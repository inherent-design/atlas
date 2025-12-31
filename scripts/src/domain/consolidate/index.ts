/**
 * Atlas Chunk Consolidation
 *
 * Finds and merges similar chunks in the unified atlas collection.
 * Uses vector similarity to identify candidates, then LLM to classify
 * the relationship and generate a consolidated summary.
 *
 * Consolidation types:
 * - duplicate_work: Same content created independently
 * - sequential_iteration: Progressive refinement of same concept
 * - contextual_convergence: Different paths arriving at similar insight
 */

import { getQdrantClient } from '../../services/storage'
import { getVoyageClient } from '../../services/embedding'
import { QDRANT_COLLECTION_NAME, VOYAGE_MODEL } from '../../shared/config'
import { completeJSON, getLLMConfig } from '../../services/llm'
import { createLogger, startTimer } from '../../shared/logger'
import type { ChunkPayload, ConsolidationType, ConsolidationDirection } from '../../shared/types'

const log = createLogger('consolidate')

export interface ConsolidateConfig {
  dryRun?: boolean
  threshold?: number // Similarity threshold (0-1)
  limit?: number // Max candidates to process
}

export interface ConsolidateCandidate {
  id: string
  file_path: string
  similarity: number
  text_preview: string
  qntm_keys: string[]
  created_at: string
  pair_id: string // ID of the similar chunk
}

export interface ConsolidateResult {
  candidatesFound: number
  consolidated: number
  deleted: number
  candidates?: ConsolidateCandidate[]
}

interface ConsolidationClassification {
  type: ConsolidationType
  direction: ConsolidationDirection
  reasoning: string
  keep: 'first' | 'second' | 'merge'
}

/**
 * Build prompt for consolidation classification
 */
function buildConsolidationPrompt(
  text1: string,
  text2: string,
  keys1: string[],
  keys2: string[],
  created1: string,
  created2: string
): string {
  return `# Chunk Consolidation Classification

You are analyzing two similar text chunks to determine their relationship and how to consolidate them.

## Chunk 1 (created: ${created1})
QNTM Keys: ${keys1.join(', ')}
\`\`\`
${text1}
\`\`\`

## Chunk 2 (created: ${created2})
QNTM Keys: ${keys2.join(', ')}
\`\`\`
${text2}
\`\`\`

## Classification Types

1. **duplicate_work**: Same or nearly identical content created independently
   - Keep the more recent/complete version
   - Example: Same code snippet saved twice

2. **sequential_iteration**: Progressive refinement of the same concept
   - Shows evolution of an idea over time
   - Direction matters: forward (improvement) or backward (regression)
   - Example: Draft → revised → final versions

3. **contextual_convergence**: Different approaches arriving at similar insight
   - Different contexts but overlapping conclusions
   - Both perspectives may be valuable
   - Example: Same technique discovered in different projects

## Instructions

1. Compare the semantic content of both chunks
2. Consider timestamps to understand temporal relationship
3. Classify the relationship type
4. Determine which to keep or if they should be merged
5. Return ONLY valid JSON

## Output Format
{
  "type": "duplicate_work" | "sequential_iteration" | "contextual_convergence",
  "direction": "forward" | "backward" | "convergent" | "unknown",
  "reasoning": "1-2 sentence explanation",
  "keep": "first" | "second" | "merge"
}`
}

/**
 * Classify the relationship between two chunks using LLM
 */
async function classifyConsolidation(
  payload1: ChunkPayload,
  payload2: ChunkPayload
): Promise<ConsolidationClassification> {
  const config = getLLMConfig()

  const prompt = buildConsolidationPrompt(
    payload1.original_text,
    payload2.original_text,
    payload1.qntm_keys,
    payload2.qntm_keys,
    payload1.created_at,
    payload2.created_at
  )

  try {
    const result = await completeJSON<ConsolidationClassification>(prompt, config)
    log.debug('Consolidation classified', {
      type: result.type,
      direction: result.direction,
      keep: result.keep,
    })
    return result
  } catch (error) {
    log.warn('Failed to classify consolidation, using default', {
      error: (error as Error).message,
    })
    return {
      type: 'duplicate_work',
      direction: 'unknown',
      reasoning: 'Classification failed, defaulting to duplicate_work',
      keep: 'first',
    }
  }
}

/**
 * Find consolidation candidates via self-similarity search
 *
 * For each chunk, finds other chunks with similarity > threshold.
 * Returns deduplicated pairs (A~B and B~A are same pair).
 */
async function findCandidates(threshold: number, limit: number): Promise<ConsolidateCandidate[]> {
  const endTimer = startTimer('findCandidates')
  const qdrant = getQdrantClient()

  log.info('Scanning for consolidation candidates', { threshold, limit })

  // Get all points from collection
  const candidates: ConsolidateCandidate[] = []
  const seenPairs = new Set<string>() // Track A~B pairs to avoid duplicates

  let offset: string | number | null | undefined = undefined
  const SCROLL_LIMIT = 50

  do {
    const result = await qdrant.scroll(QDRANT_COLLECTION_NAME, {
      limit: SCROLL_LIMIT,
      offset,
      with_payload: true,
      with_vector: true,
    })

    // For each point, search for similar points
    for (const point of result.points) {
      const payload = point.payload as ChunkPayload
      const vector = point.vector as number[]

      if (!vector || payload.consolidated) continue

      // Search for similar points
      const similar = await qdrant.search(QDRANT_COLLECTION_NAME, {
        vector,
        limit: 5, // Top 5 similar
        score_threshold: threshold,
        with_payload: true,
        filter: {
          must_not: [
            { has_id: [point.id] }, // Exclude self
          ],
        },
      })

      for (const hit of similar) {
        const hitPayload = hit.payload as ChunkPayload

        // Skip already consolidated chunks
        if (hitPayload.consolidated) continue

        // Create canonical pair ID (sorted to dedupe A~B and B~A)
        const pairKey = [point.id, hit.id].sort().join('~')
        if (seenPairs.has(pairKey)) continue
        seenPairs.add(pairKey)

        candidates.push({
          id: point.id as string,
          file_path: payload.file_path,
          similarity: hit.score,
          text_preview: payload.original_text.substring(0, 100),
          qntm_keys: payload.qntm_keys,
          created_at: payload.created_at,
          pair_id: hit.id as string,
        })

        if (candidates.length >= limit) break
      }

      if (candidates.length >= limit) break
    }

    offset = result.next_page_offset
  } while (offset !== null && offset !== undefined && candidates.length < limit)

  log.info('Found consolidation candidates', { count: candidates.length })

  endTimer()
  return candidates
}

/**
 * Consolidate similar chunks
 *
 * For each candidate pair:
 * 1. Fetch both chunks
 * 2. Use LLM to classify relationship and determine which to keep
 * 3. Update kept chunk with provenance metadata
 * 4. Mark other chunk as consolidated (soft delete)
 */
async function performConsolidation(
  candidates: ConsolidateCandidate[]
): Promise<{ consolidated: number; deleted: number }> {
  const endTimer = startTimer('performConsolidation')
  const qdrant = getQdrantClient()

  let consolidated = 0
  let deleted = 0

  // Process candidates
  for (const candidate of candidates) {
    try {
      // Fetch both points
      const points = await qdrant.retrieve(QDRANT_COLLECTION_NAME, {
        ids: [candidate.id, candidate.pair_id],
        with_payload: true,
        with_vector: true,
      })

      if (points.length !== 2) {
        log.warn('Could not fetch both points for consolidation', {
          id: candidate.id,
          pair_id: candidate.pair_id,
        })
        continue
      }

      const [point1, point2] = points
      const payload1 = point1.payload as ChunkPayload
      const payload2 = point2.payload as ChunkPayload

      // Classify the relationship using LLM
      const classification = await classifyConsolidation(payload1, payload2)

      // Determine primary and secondary based on classification
      let primary = point1
      let secondary = point2
      let primaryPayload = payload1
      let secondaryPayload = payload2

      if (classification.keep === 'second') {
        primary = point2
        secondary = point1
        primaryPayload = payload2
        secondaryPayload = payload1
      }
      // For 'merge' or 'first', keep point1 as primary

      // Merge QNTM keys (union)
      const mergedKeys = Array.from(
        new Set([...primaryPayload.qntm_keys, ...secondaryPayload.qntm_keys])
      )

      // Update primary with consolidation metadata
      const updatedPayload: ChunkPayload = {
        ...primaryPayload,
        qntm_keys: mergedKeys,
        consolidated: false, // Primary stays active
        occurrences: (primaryPayload.occurrences || 1) + (secondaryPayload.occurrences || 1),
        parents: [...(primaryPayload.parents || []), secondary.id as string],
        consolidated_from: [...(primaryPayload.consolidated_from || []), secondary.id as string],
        consolidation_type: classification.type,
        consolidation_direction: classification.direction,
        consolidation_reasoning: classification.reasoning,
      }

      // Update primary point
      await qdrant.setPayload(QDRANT_COLLECTION_NAME, {
        payload: updatedPayload,
        points: [primary.id as string],
      })

      // Mark secondary as consolidated (soft delete)
      await qdrant.setPayload(QDRANT_COLLECTION_NAME, {
        payload: { consolidated: true },
        points: [secondary.id as string],
      })

      consolidated++
      deleted++

      log.debug('Consolidated pair', {
        primary: primary.id,
        secondary: secondary.id,
        type: classification.type,
        mergedKeys: mergedKeys.length,
      })
    } catch (error) {
      log.error('Failed to consolidate pair', {
        id: candidate.id,
        pair_id: candidate.pair_id,
        error: (error as Error).message,
      })
    }
  }

  endTimer()
  return { consolidated, deleted }
}

/**
 * Main consolidation function
 */
export async function consolidate(config: ConsolidateConfig): Promise<ConsolidateResult> {
  const { dryRun = false, threshold = 0.92, limit = 100 } = config
  const endTimer = startTimer('consolidate')

  log.info('Starting consolidation', { dryRun, threshold, limit })

  // Require collection to exist - fail if not (don't auto-create)
  const { requireCollection } = await import('../../shared/utils')
  await requireCollection(QDRANT_COLLECTION_NAME)

  // Find candidates
  const candidates = await findCandidates(threshold, limit)

  if (dryRun) {
    endTimer()
    return {
      candidatesFound: candidates.length,
      consolidated: 0,
      deleted: 0,
      candidates,
    }
  }

  // Perform consolidation
  const { consolidated, deleted } = await performConsolidation(candidates)

  log.info('Consolidation complete', {
    candidatesFound: candidates.length,
    consolidated,
    deleted,
  })

  endTimer()
  return {
    candidatesFound: candidates.length,
    consolidated,
    deleted,
  }
}
