/**
 * Chunk Lifecycle Management
 *
 * Handles stability scoring and grace period enforcement for chunk deletion.
 *
 * Stability Score Formula:
 *   stability = (consolidation_weight + access_weight + age_weight) / 3
 *
 *   consolidation_weight = consolidation_level / 3  (0.0 - 1.0)
 *   access_weight = min(access_count / 10, 1.0)     (caps at 10 accesses)
 *   age_weight = min(age_days / 30, 1.0)            (caps at 30 days)
 *
 * Grace Period:
 *   Chunks marked with deletion_eligible = true must wait 14 days
 *   before being hard deleted.
 */

import { getStorageBackend } from '../../services/storage'
import {
  QDRANT_COLLECTION_NAME,
  DELETION_GRACE_PERIOD_DAYS,
  STABILITY_SCORE_THRESHOLD,
} from '../../shared/config'
import { createLogger, startTimer } from '../../shared/logger'
import type { ChunkPayload, ConsolidationLevel } from '../../shared/types'

const log = createLogger('lifecycle')

/**
 * Calculate stability score for a chunk
 *
 * Higher score = more stable/frozen = less likely to change
 * Score >= 0.95 indicates chunk is ready for potential archival
 */
export function calculateStabilityScore(payload: ChunkPayload): number {
  const now = new Date()

  // Consolidation weight: higher level = more stable
  const consolidationLevel = payload.consolidation_level ?? 0
  const consolidationWeight = consolidationLevel / 3

  // Access weight: more accesses = more valuable = keep longer
  const accessCount = payload.access_count ?? 0
  const accessWeight = Math.min(accessCount / 10, 1.0)

  // Age weight: older content = more stable (assumes it's been validated over time)
  const createdAt = new Date(payload.created_at)
  const ageDays = (now.getTime() - createdAt.getTime()) / (1000 * 60 * 60 * 24)
  const ageWeight = Math.min(ageDays / 30, 1.0)

  // Average of all weights
  const stability = (consolidationWeight + accessWeight + ageWeight) / 3

  return Math.round(stability * 100) / 100 // Round to 2 decimal places
}

/**
 * Check if chunk is past grace period and ready for hard delete
 */
export function isPastGracePeriod(payload: ChunkPayload): boolean {
  if (!payload.deletion_eligible || !payload.deletion_marked_at) {
    return false
  }

  const markedAt = new Date(payload.deletion_marked_at)
  const now = new Date()
  const daysSinceMarked = (now.getTime() - markedAt.getTime()) / (1000 * 60 * 60 * 24)

  return daysSinceMarked >= DELETION_GRACE_PERIOD_DAYS
}

export interface VacuumResult {
  scanned: number
  deleted: number
  stabilityUpdated: number
  errors: number
}

/**
 * Vacuum eligible chunks past grace period
 *
 * 1. Finds all deletion_eligible chunks
 * 2. Checks if grace period has passed
 * 3. Hard deletes those past grace period
 * 4. Updates stability scores for remaining chunks
 */
export async function vacuumEligibleChunks(options: {
  dryRun?: boolean
  limit?: number
  updateStability?: boolean
}): Promise<VacuumResult> {
  const { dryRun = false, limit = 1000, updateStability = true } = options
  const endTimer = startTimer('vacuumEligibleChunks')

  const storage = getStorageBackend()
  if (!storage) {
    throw new Error('No storage backend available')
  }

  const result: VacuumResult = {
    scanned: 0,
    deleted: 0,
    stabilityUpdated: 0,
    errors: 0,
  }

  log.info('Starting vacuum pass', { dryRun, limit, updateStability })

  try {
    // Find deletion_eligible chunks
    const scrollResult = await storage.scroll(QDRANT_COLLECTION_NAME, {
      filter: {
        must: [{ key: 'deletion_eligible', match: { value: true } }],
      },
      limit,
      withPayload: true,
      withVector: false,
    })

    result.scanned = scrollResult.points.length
    log.debug('Found deletion candidates', { count: result.scanned })

    const toDelete: string[] = []

    for (const point of scrollResult.points) {
      const payload = point.payload as ChunkPayload

      if (isPastGracePeriod(payload)) {
        toDelete.push(point.id as string)
      }
    }

    log.info('Chunks past grace period', {
      total: result.scanned,
      pastGracePeriod: toDelete.length,
      gracePeriodDays: DELETION_GRACE_PERIOD_DAYS,
    })

    // Hard delete
    if (toDelete.length > 0 && !dryRun) {
      try {
        await storage.delete(QDRANT_COLLECTION_NAME, toDelete)
        result.deleted = toDelete.length
        log.info('Hard deleted chunks', { count: result.deleted })
      } catch (error) {
        result.errors++
        log.error('Failed to delete chunks', {
          error: (error as Error).message,
          count: toDelete.length,
        })
      }
    } else if (dryRun && toDelete.length > 0) {
      log.info('Dry run: would delete', { count: toDelete.length, ids: toDelete.slice(0, 5) })
      result.deleted = toDelete.length // Report what would be deleted
    }
  } catch (error) {
    result.errors++
    log.error('Vacuum scan failed', { error: (error as Error).message })
  }

  // Optionally update stability scores for non-deleted chunks
  if (updateStability) {
    const stabilityResult = await updateStabilityScores({ dryRun, limit })
    result.stabilityUpdated = stabilityResult.updated
    result.errors += stabilityResult.errors
  }

  log.info('Vacuum pass complete', result)
  endTimer()
  return result
}

export interface StabilityUpdateResult {
  scanned: number
  updated: number
  errors: number
}

/**
 * Update stability scores for active chunks
 *
 * Scans chunks without recent stability updates and recalculates scores.
 * Chunks with stability >= threshold may be marked for archival.
 */
export async function updateStabilityScores(options: {
  dryRun?: boolean
  limit?: number
}): Promise<StabilityUpdateResult> {
  const { dryRun = false, limit = 500 } = options
  const endTimer = startTimer('updateStabilityScores')

  const storage = getStorageBackend()
  if (!storage) {
    throw new Error('No storage backend available')
  }

  const result: StabilityUpdateResult = {
    scanned: 0,
    updated: 0,
    errors: 0,
  }

  log.debug('Updating stability scores', { dryRun, limit })

  try {
    // Find active (non-deleted) chunks
    const scrollResult = await storage.scroll(QDRANT_COLLECTION_NAME, {
      filter: {
        must_not: [{ key: 'deletion_eligible', match: { value: true } }],
      },
      limit,
      withPayload: true,
      withVector: false,
    })

    result.scanned = scrollResult.points.length

    for (const point of scrollResult.points) {
      const payload = point.payload as ChunkPayload
      const newScore = calculateStabilityScore(payload)
      const currentScore = payload.stability_score ?? 0

      // Only update if score changed significantly (avoid unnecessary writes)
      if (Math.abs(newScore - currentScore) >= 0.05) {
        if (!dryRun) {
          try {
            await storage.setPayload(QDRANT_COLLECTION_NAME, [point.id as string], {
              stability_score: newScore,
            })
            result.updated++
          } catch (error) {
            result.errors++
            log.warn('Failed to update stability score', {
              pointId: point.id,
              error: (error as Error).message,
            })
          }
        } else {
          result.updated++
          log.debug('Dry run: would update stability', {
            pointId: point.id,
            from: currentScore,
            to: newScore,
          })
        }
      }
    }

    log.debug('Stability update complete', result)
  } catch (error) {
    result.errors++
    log.error('Stability scan failed', { error: (error as Error).message })
  }

  endTimer()
  return result
}

/**
 * Mark a chunk for deletion with grace period
 */
export async function markForDeletion(pointId: string, supersededBy?: string): Promise<void> {
  const storage = getStorageBackend()
  if (!storage) {
    throw new Error('No storage backend available')
  }

  const now = new Date().toISOString()

  await storage.setPayload(QDRANT_COLLECTION_NAME, [pointId], {
    deletion_eligible: true,
    deletion_marked_at: now,
    ...(supersededBy && { superseded_by: supersededBy }),
  })

  log.debug('Marked chunk for deletion', {
    pointId,
    supersededBy,
    gracePeriodDays: DELETION_GRACE_PERIOD_DAYS,
  })
}

/**
 * Unmark a chunk from deletion (rescue before grace period expires)
 */
export async function unmarkFromDeletion(pointId: string): Promise<void> {
  const storage = getStorageBackend()
  if (!storage) {
    throw new Error('No storage backend available')
  }

  await storage.setPayload(QDRANT_COLLECTION_NAME, [pointId], {
    deletion_eligible: false,
    deletion_marked_at: undefined,
    superseded_by: undefined,
  })

  log.debug('Unmarked chunk from deletion', { pointId })
}
