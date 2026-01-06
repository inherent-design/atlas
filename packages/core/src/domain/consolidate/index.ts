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

import { getStorageBackend } from '../../services/storage'
import { getEmbeddingBackend } from '../../services/embedding'
import { QDRANT_COLLECTION_NAME, VOYAGE_MODEL } from '../../shared/config'
import { getConfig } from '../../shared/config.loader'
import { getLLMBackendFor } from '../../services/llm'
import { buildConsolidationPrompt } from '../../services/llm/prompts'
import { createLogger, startTimer } from '../../shared/logger'
import type { ChunkPayload, ConsolidationType, ConsolidationDirection } from '../../shared/types'
import type { NamedVectors } from '../../services/storage'

const log = createLogger('consolidate')

export interface ConsolidateConfig {
  dryRun?: boolean
  threshold?: number // Similarity threshold (0-1)
  limit?: number // Max candidates to process
  emit?: (event: any) => void // Event emitter (opt-in, for daemon mode)
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
 * Classify the relationship between two chunks using LLM
 */
async function classifyConsolidation(
  payload1: ChunkPayload,
  payload2: ChunkPayload
): Promise<ConsolidationClassification> {
  // Get JSON-capable LLM backend
  const backend = getLLMBackendFor('json-completion')
  if (!backend) {
    throw new Error('No JSON-capable LLM backend available for consolidation')
  }

  // Verify backend has JSON completion method
  if (!('completeJSON' in backend)) {
    throw new Error('Backend does not implement JSON completion')
  }

  const prompt = buildConsolidationPrompt(
    payload1.original_text,
    payload2.original_text,
    payload1.qntm_keys,
    payload2.qntm_keys,
    payload1.created_at,
    payload2.created_at,
    payload1.consolidation_level,
    payload2.consolidation_level
  )

  try {
    // Type assertion: we verified completeJSON exists
    const result = await (
      backend as { completeJSON<T>(prompt: string): Promise<T> }
    ).completeJSON<ConsolidationClassification>(prompt)
    log.debug('Consolidation classified', {
      backend: backend.name,
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
  const storage = getStorageBackend()
  if (!storage) {
    throw new Error('No storage backend available')
  }

  log.info('Scanning for consolidation candidates', { threshold, limit })

  // Get all points from collection
  const candidates: ConsolidateCandidate[] = []
  const seenPairs = new Set<string>() // Track A~B pairs to avoid duplicates

  let offset: string | number | null | undefined = undefined
  const SCROLL_LIMIT = 50

  do {
    const result = await storage.scroll(QDRANT_COLLECTION_NAME, {
      limit: SCROLL_LIMIT,
      offset,
      withPayload: true,
      withVector: true,
    })

    // For each point, search for similar points
    for (const point of result.points) {
      const payload = point.payload as ChunkPayload
      const namedVectors = point.vector as NamedVectors
      const textVector = namedVectors.text

      if (!textVector || payload.consolidated) continue

      // Search for similar points
      const similar = await storage.search(QDRANT_COLLECTION_NAME, {
        vectorName: 'text',
        vector: textVector,
        limit: 5, // Top 5 similar
        scoreThreshold: threshold,
        withPayload: true,
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

    offset = result.nextOffset
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
  candidates: ConsolidateCandidate[],
  emit?: (event: any) => void
): Promise<{ consolidated: number; deleted: number }> {
  const endTimer = startTimer('performConsolidation')
  const storage = getStorageBackend()
  if (!storage) {
    throw new Error('No storage backend available')
  }

  let consolidated = 0
  let deleted = 0

  // Process candidates
  for (const candidate of candidates) {
    try {
      // Fetch both points
      const points = await storage.retrieve(QDRANT_COLLECTION_NAME, [
        candidate.id,
        candidate.pair_id,
      ])

      if (points.length !== 2) {
        log.warn('Could not fetch both points for consolidation', {
          id: candidate.id,
          pair_id: candidate.pair_id,
        })
        continue
      }

      const [point1, point2] = points
      const payload1 = point1!.payload as ChunkPayload
      const payload2 = point2!.payload as ChunkPayload

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

      // Merge occurrences (timestamps array)
      const primaryOccurrences = primaryPayload.occurrences || [primaryPayload.created_at]
      const secondaryOccurrences = secondaryPayload.occurrences || [secondaryPayload.created_at]
      const mergedOccurrences = [
        ...new Set([...primaryOccurrences, ...secondaryOccurrences]),
      ].sort()

      // Update primary with consolidation metadata
      const updatedPayload: ChunkPayload = {
        ...primaryPayload,
        qntm_keys: mergedKeys,
        consolidation_level: Math.max(primaryPayload.consolidation_level, 1) as 0 | 1 | 2 | 3, // At least level 1 after consolidation
        occurrences: mergedOccurrences, // Array of ISO timestamps
        parents: [...(primaryPayload.parents || []), secondary!.id as string], // Absorbs consolidated_from
        consolidation_type: classification.type,
        consolidation_direction: classification.direction,
        consolidation_reasoning: classification.reasoning,
      }

      // Update primary point
      await storage.setPayload(QDRANT_COLLECTION_NAME, [primary!.id as string], updatedPayload)

      // Mark secondary as superseded (soft delete with provenance)
      await storage.setPayload(QDRANT_COLLECTION_NAME, [secondary!.id as string], {
        consolidation_level: Math.max(secondaryPayload.consolidation_level, 1) as 0 | 1 | 2 | 3,
        superseded_by: primary!.id as string,
        deletion_eligible: true,
        deletion_marked_at: new Date().toISOString(),
      })

      consolidated++
      deleted++

      // Emit consolidate.pair.merged event
      emit?.({
        type: 'consolidate.pair.merged',
        data: {
          primary: primary!.id as string,
          secondary: secondary!.id as string,
          type: classification.type,
        },
      })

      log.debug('Consolidated pair', {
        primary: primary!.id,
        secondary: secondary!.id,
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
  const atlasConfig = getConfig()
  const defaultThreshold = atlasConfig.consolidation?.similarityThreshold ?? 0.95

  const { dryRun = false, threshold = defaultThreshold, limit = Infinity, emit } = config
  const endTimer = startTimer('consolidate')
  const startTime = Date.now()

  log.info('Starting consolidation', { dryRun, threshold, limit })

  // Emit consolidate.triggered event
  emit?.({
    type: 'consolidate.triggered',
    data: {
      reason: 'manual', // Could be 'threshold' if triggered by watchdog
      l0Count: 0, // Would need to query this from Qdrant if needed
    },
  })

  try {
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

    // Perform consolidation (pass emit function)
    const { consolidated, deleted } = await performConsolidation(candidates, emit)

    log.info('Consolidation complete', {
      candidatesFound: candidates.length,
      consolidated,
      deleted,
    })

    // Emit consolidate.completed event
    emit?.({
      type: 'consolidate.completed',
      data: {
        merged: consolidated,
        deleted,
        took: Date.now() - startTime,
      },
    })

    endTimer()
    return {
      candidatesFound: candidates.length,
      consolidated,
      deleted,
    }
  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error))

    // Emit consolidate.error event
    emit?.({
      type: 'consolidate.error',
      data: {
        error: err.message,
        phase: 'find', // Could be 'find', 'classify', or 'merge'
      },
    })

    throw error
  }
}
