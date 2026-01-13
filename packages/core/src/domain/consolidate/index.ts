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

import { getStorageBackend } from '../../services/storage/index.js'
import { getEmbeddingBackend } from '../../services/embedding/index.js'
import {
  VOYAGE_MODEL,
  CONSOLIDATION_SIMILARITY_THRESHOLD,
} from '../../shared/config.js'
import { getConfig } from '../../shared/config.loader.js'
import { getPrimaryCollectionName, requireCollection } from '../../shared/utils.js'
import { getLLMBackendFor } from '../../services/llm/index.js'
import { buildTaskPrompt } from '../../prompts/builders.js'
import { createLogger, startTimer } from '../../shared/logger.js'
import type { ChunkPayload, ConsolidationType, ConsolidationDirection } from '../../shared/types.js'
import type { NamedVectors } from '../../services/storage/index.js'

const log = createLogger('consolidate')

export interface ConsolidateConfig {
  dryRun?: boolean
  threshold?: number // Similarity threshold (0-1)
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
  rounds: number
  maxLevel: number
  levelStats: Record<number, number> // level -> count consolidated to that level
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
  // Get JSON-capable LLM backend (with domain-specific override)
  const backend = getLLMBackendFor('json-completion', 'consolidation')
  if (!backend) {
    throw new Error('No JSON-capable LLM backend available for consolidation')
  }

  // Verify backend has JSON completion method
  if (!('completeJSON' in backend)) {
    throw new Error('Backend does not implement JSON completion')
  }

  const prompt = await buildTaskPrompt('consolidation-classify', {
    text1: payload1.original_text,
    text2: payload2.original_text,
    keys1: payload1.qntm_keys.join(', '),
    keys2: payload2.qntm_keys.join(', '),
    created1: payload1.created_at,
    created2: payload2.created_at,
  })

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
 * Find consolidation candidates at a specific consolidation level
 *
 * Searches for similar chunks at the same level to consolidate into the next level.
 * Returns deduplicated pairs (A~B and B~A are same pair).
 */
async function findCandidatesAtLevel(
  level: number,
  threshold: number
): Promise<ConsolidateCandidate[]> {
  const endTimer = startTimer(`findCandidatesAtLevel:${level}`)
  const storage = getStorageBackend()
  if (!storage) {
    throw new Error('No storage backend available')
  }

  log.info('Scanning for consolidation candidates', { level, threshold })

  const candidates: ConsolidateCandidate[] = []
  const seenPairs = new Set<string>() // Track A~B pairs to avoid duplicates

  // Scroll through ALL points at this level (no limit)
  let offset: string | number | null | undefined = undefined
  const SCROLL_LIMIT = 100 // Increased from 50

  do {
    const result = await storage.scroll(getPrimaryCollectionName(), {
      limit: SCROLL_LIMIT,
      offset,
      withPayload: true,
      withVector: true,
      filter: {
        must: [{ key: 'consolidation_level', match: { value: level } }],
        must_not: [
          { key: 'deletion_eligible', match: { value: true } }, // Not marked for deletion
        ],
      },
    })

    // For each point at this level, search for similar points AT SAME LEVEL
    for (const point of result.points) {
      const payload = point.payload as ChunkPayload
      const namedVectors = point.vector as NamedVectors
      const textVector = namedVectors.text

      if (!textVector) continue

      // Search for similar points at same level
      const similar = await storage.search(getPrimaryCollectionName(), {
        vectorName: 'text',
        vector: textVector,
        limit: 10, // Top 10 similar candidates
        scoreThreshold: threshold,
        withPayload: true,
        filter: {
          must: [{ key: 'consolidation_level', match: { value: level } }],
          must_not: [
            { has_id: [point.id] }, // Exclude self
            { key: 'deletion_eligible', match: { value: true } }, // Not marked for deletion
          ],
        },
      })

      for (const hit of similar) {
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
      }
    }

    offset = result.nextOffset
  } while (offset !== null && offset !== undefined)

  log.info('Found consolidation candidates', { level, count: candidates.length })

  endTimer()
  return candidates
}

/**
 * Consolidate similar chunks
 *
 * For each candidate pair:
 * 1. Fetch both chunks
 * 2. Use LLM to classify relationship and determine which to keep
 * 3. Update kept chunk with provenance metadata and promote to targetLevel
 * 4. Mark other chunk as consolidated (soft delete)
 */
async function performConsolidation(
  candidates: ConsolidateCandidate[],
  targetLevel: number,
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
      const points = await storage.retrieve(getPrimaryCollectionName(), [
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

      // Update primary with consolidation metadata and promote to target level
      const updatedPayload: ChunkPayload = {
        ...primaryPayload,
        qntm_keys: mergedKeys,
        consolidation_level: targetLevel as 0 | 1 | 2 | 3 | 4,
        occurrences: mergedOccurrences, // Array of ISO timestamps
        parents: [...(primaryPayload.parents || []), secondary!.id as string], // Absorbs consolidated_from
        consolidation_type: classification.type,
        consolidation_direction: classification.direction,
        consolidation_reasoning: classification.reasoning,
      }

      // Update primary point
      await storage.setPayload(getPrimaryCollectionName(), [primary!.id as string], updatedPayload)

      // Mark secondary as superseded (soft delete with provenance)
      await storage.setPayload(getPrimaryCollectionName(), [secondary!.id as string], {
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
  const defaultThreshold =
    atlasConfig.consolidation?.similarityThreshold ?? CONSOLIDATION_SIMILARITY_THRESHOLD

  const { dryRun = false, threshold = defaultThreshold, emit } = config
  const endTimer = startTimer('consolidate')
  const startTime = Date.now()

  log.info('Starting consolidation', { dryRun, threshold })

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
    await requireCollection(getPrimaryCollectionName())

    let totalCandidatesFound = 0
    let totalConsolidated = 0
    let totalDeleted = 0
    let rounds = 0
    let maxLevel = 0
    const levelStats: Record<number, number> = {}
    const allCandidates: ConsolidateCandidate[] = []

    const MAX_LEVEL = 4

    // Process each level until stable, then move to next
    for (let currentLevel = 0; currentLevel < MAX_LEVEL; currentLevel++) {
      const targetLevel = currentLevel + 1
      let levelStable = false

      // Keep processing this level until stable (no new consolidations)
      while (!levelStable) {
        rounds++
        log.info('Starting consolidation round', {
          round: rounds,
          currentLevel,
          targetLevel,
        })

        // Find candidates at current level
        const candidates = await findCandidatesAtLevel(currentLevel, threshold)
        totalCandidatesFound += candidates.length

        if (dryRun) {
          allCandidates.push(...candidates)
        }

        if (candidates.length === 0) {
          log.info('Level is stable (no candidates)', { level: currentLevel })
          levelStable = true
          break
        }

        if (!dryRun) {
          // Perform consolidation to next level
          const { consolidated, deleted } = await performConsolidation(
            candidates,
            targetLevel,
            emit
          )

          totalConsolidated += consolidated
          totalDeleted += deleted

          if (consolidated > 0) {
            levelStats[targetLevel] = (levelStats[targetLevel] || 0) + consolidated
            maxLevel = Math.max(maxLevel, targetLevel)
          }

          log.info('Round complete', {
            round: rounds,
            level: currentLevel,
            candidates: candidates.length,
            consolidated,
            deleted,
          })

          // If we didn't consolidate anything, level is stable
          if (consolidated === 0) {
            levelStable = true
          }
          // Otherwise, continue scanning this level for more candidates
        } else {
          // In dry run, only scan each level once
          levelStable = true
        }
      }
    }

    if (dryRun) {
      endTimer()
      return {
        candidatesFound: totalCandidatesFound,
        consolidated: 0,
        deleted: 0,
        rounds,
        maxLevel: 0,
        levelStats: {},
        candidates: allCandidates,
      }
    }

    log.info('Consolidation complete', {
      rounds,
      candidatesFound: totalCandidatesFound,
      consolidated: totalConsolidated,
      deleted: totalDeleted,
      maxLevel,
      levelStats,
    })

    // Emit consolidate.completed event
    emit?.({
      type: 'consolidate.completed',
      data: {
        merged: totalConsolidated,
        deleted: totalDeleted,
        took: Date.now() - startTime,
      },
    })

    endTimer()
    return {
      candidatesFound: totalCandidatesFound,
      consolidated: totalConsolidated,
      deleted: totalDeleted,
      rounds,
      maxLevel,
      levelStats,
    }
  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error))

    // Emit consolidate.error event
    emit?.({
      type: 'consolidate.error',
      data: {
        error: err.message,
        phase: 'consolidate',
      },
    })

    throw error
  }
}
