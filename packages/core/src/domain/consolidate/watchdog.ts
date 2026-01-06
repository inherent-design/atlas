/**
 * Consolidation Watchdog
 *
 * Monitors ingestion rate and triggers consolidation when threshold reached.
 * Pauses ingestion during consolidation to ensure clean segment state.
 *
 * Flow:
 * 1. Poll every 30s to check documents ingested since last consolidation
 * 2. At threshold (500 chunks): set pause flag → wait for in-flight → consolidate → resume
 * 3. Qdrant's vacuum optimizer handles soft-deleted chunks automatically
 */

import {
  QDRANT_COLLECTION_NAME,
  BATCH_HNSW_THRESHOLD,
  CONSOLIDATION_BASE_THRESHOLD,
  CONSOLIDATION_SCALE_FACTOR,
  CONSOLIDATION_SIMILARITY_THRESHOLD,
} from '../../shared/config'
import { getConfig } from '../../shared/config.loader'
import { consolidate } from '.'
import { createLogger } from '../../shared/logger'
import { PollingScheduler } from '../../core/scheduler'
import { getStorageBackend, withHNSWDisabled } from '../../services/storage'

const log = createLogger('consolidation-watchdog')

export interface ConsolidationWatchdogConfig {
  baseThreshold?: number // Base threshold (default: CONSOLIDATION_BASE_THRESHOLD)
  scaleFactor?: number // Scale factor for dynamic threshold (default: CONSOLIDATION_SCALE_FACTOR)
  pollIntervalMs?: number
  similarityThreshold?: number
  useHNSWToggle?: boolean // Enable HNSW disable/enable during consolidation
}

/**
 * Ingest pause controller
 * Shared state between consolidation watchdog and ingest pipeline
 */
class IngestPauseController {
  private paused = false
  private inFlightCount = 0
  private waitResolvers: Array<() => void> = []
  private resumeResolvers: Array<() => void> = []

  /**
   * Check if ingestion is currently paused
   */
  isPaused(): boolean {
    return this.paused
  }

  /**
   * Pause ingestion (called by consolidation watchdog)
   */
  pause(): void {
    this.paused = true
    log.info('Ingestion paused for consolidation')
  }

  /**
   * Resume ingestion (called by consolidation watchdog)
   */
  resume(): void {
    this.paused = false
    // Notify all waiters that we've resumed
    for (const resolve of this.resumeResolvers) {
      resolve()
    }
    this.resumeResolvers = []
    log.info('Ingestion resumed')
  }

  /**
   * Wait for ingestion to resume (called by ingest when paused)
   */
  async waitForResume(): Promise<void> {
    if (!this.paused) {
      return
    }

    log.debug('Waiting for consolidation to complete')

    return new Promise((resolve) => {
      this.resumeResolvers.push(resolve)
    })
  }

  /**
   * Register an in-flight ingest operation
   */
  registerInFlight(): void {
    this.inFlightCount++
  }

  /**
   * Complete an in-flight ingest operation
   */
  completeInFlight(): void {
    this.inFlightCount--
    if (this.inFlightCount === 0) {
      // Notify waiters
      for (const resolve of this.waitResolvers) {
        resolve()
      }
      this.waitResolvers = []
    }
  }

  /**
   * Wait for all in-flight operations to complete
   */
  async waitForInFlight(): Promise<void> {
    if (this.inFlightCount === 0) {
      return
    }

    log.debug('Waiting for in-flight ingests', { count: this.inFlightCount })

    return new Promise((resolve) => {
      this.waitResolvers.push(resolve)
    })
  }

  /**
   * Get current state
   */
  getState() {
    return {
      paused: this.paused,
      inFlightCount: this.inFlightCount,
    }
  }

  /**
   * Reset state (for testing)
   */
  reset(): void {
    this.paused = false
    this.inFlightCount = 0
    this.waitResolvers = []
    this.resumeResolvers = []
  }
}

// Singleton pause controller
export const ingestPauseController = new IngestPauseController()

/**
 * Consolidation Watchdog
 *
 * Monitors document count and triggers consolidation at dynamic threshold.
 * Threshold formula: baseThreshold + (scaleFactor × point_count)
 * Default: 100 + (0.05 × point_count)
 */
export class ConsolidationWatchdog {
  readonly name = 'consolidation-watchdog'
  private scheduler: PollingScheduler
  private lastConsolidationCount = 0
  private currentCount = 0
  private baseThreshold: number
  private scaleFactor: number
  private similarityThreshold: number
  private useHNSWToggle: boolean
  private isConsolidating = false
  private consecutiveFailures = 0
  private readonly MAX_CONSECUTIVE_FAILURES = 3

  constructor(config: ConsolidationWatchdogConfig = {}) {
    const atlasConfig = getConfig()
    const consolidationConfig = atlasConfig.consolidation

    this.baseThreshold =
      config.baseThreshold ?? consolidationConfig?.baseThreshold ?? CONSOLIDATION_BASE_THRESHOLD
    this.scaleFactor =
      config.scaleFactor ?? consolidationConfig?.scaleFactor ?? CONSOLIDATION_SCALE_FACTOR
    this.similarityThreshold =
      config.similarityThreshold ??
      consolidationConfig?.similarityThreshold ??
      CONSOLIDATION_SIMILARITY_THRESHOLD
    this.useHNSWToggle = config.useHNSWToggle ?? true

    this.scheduler = new PollingScheduler({
      name: 'consolidation',
      tick: () => this.checkAndConsolidate(),
    })

    log.debug('ConsolidationWatchdog initialized', {
      baseThreshold: this.baseThreshold,
      scaleFactor: this.scaleFactor,
      similarityThreshold: this.similarityThreshold,
      useHNSWToggle: this.useHNSWToggle,
    })
  }

  /**
   * Calculate dynamic threshold based on collection size
   * Formula: baseThreshold + (scaleFactor × point_count)
   */
  private async calculateDynamicThreshold(): Promise<number> {
    try {
      const backend = getStorageBackend()
      if (!backend) {
        return this.baseThreshold
      }
      const info = await backend.getCollectionInfo(QDRANT_COLLECTION_NAME)
      const pointCount = info.points_count ?? 0
      const threshold = Math.floor(this.baseThreshold + this.scaleFactor * pointCount)
      log.debug('Dynamic threshold calculated', { pointCount, threshold })
      return threshold
    } catch {
      // Fall back to base threshold if collection doesn't exist
      return this.baseThreshold
    }
  }

  /**
   * Start the consolidation watchdog
   */
  start(pollIntervalMs?: number): void {
    const atlasConfig = getConfig()
    const defaultInterval = atlasConfig.consolidation?.pollIntervalMs ?? 30000
    const interval = pollIntervalMs ?? defaultInterval

    log.info('Starting consolidation watchdog', {
      pollIntervalMs: interval,
      baseThreshold: this.baseThreshold,
      scaleFactor: this.scaleFactor,
    })
    this.scheduler.start(interval)
  }

  /**
   * Stop the consolidation watchdog
   */
  stop(): void {
    this.scheduler.stop()
    log.info('Consolidation watchdog stopped', {
      documentsProcessed: this.currentCount - this.lastConsolidationCount,
      consecutiveFailures: this.consecutiveFailures,
    })
  }

  /**
   * Increment document counter (called by ingest pipeline)
   */
  recordIngestion(count = 1): void {
    this.currentCount += count
  }

  /**
   * Get current state
   */
  getState() {
    return {
      isRunning: this.scheduler.isRunning(),
      isConsolidating: this.isConsolidating,
      currentCount: this.currentCount,
      lastConsolidationCount: this.lastConsolidationCount,
      documentsSinceLastConsolidation: this.currentCount - this.lastConsolidationCount,
      baseThreshold: this.baseThreshold,
      scaleFactor: this.scaleFactor,
      consecutiveFailures: this.consecutiveFailures,
      circuitBreakerOpen: this.consecutiveFailures >= this.MAX_CONSECUTIVE_FAILURES,
    }
  }

  /**
   * Reset circuit breaker (for recovery)
   */
  resetCircuitBreaker(): void {
    this.consecutiveFailures = 0
    log.info('Circuit breaker reset')
  }

  /**
   * Check if threshold reached and trigger consolidation
   */
  private async checkAndConsolidate(): Promise<void> {
    // Circuit breaker: stop after consecutive failures
    if (this.consecutiveFailures >= this.MAX_CONSECUTIVE_FAILURES) {
      log.warn('Circuit breaker open: too many consecutive failures', {
        failures: this.consecutiveFailures,
        maxFailures: this.MAX_CONSECUTIVE_FAILURES,
      })
      return
    }

    const documentsSinceConsolidation = this.currentCount - this.lastConsolidationCount
    const dynamicThreshold = await this.calculateDynamicThreshold()

    log.debug('Consolidation check', {
      documentsSinceConsolidation,
      dynamicThreshold,
      isConsolidating: this.isConsolidating,
    })

    if (documentsSinceConsolidation < dynamicThreshold) {
      return
    }

    if (this.isConsolidating) {
      log.debug('Consolidation already in progress, skipping')
      return
    }

    await this.runConsolidation()
  }

  /**
   * Run consolidation with pause/resume and HNSW toggle
   */
  private async runConsolidation(): Promise<void> {
    this.isConsolidating = true

    try {
      // 1. Pause ingestion
      ingestPauseController.pause()

      // 2. Wait for in-flight ingests to complete
      await ingestPauseController.waitForInFlight()

      log.info('Starting consolidation pass', {
        documentsSinceLastConsolidation: this.currentCount - this.lastConsolidationCount,
        useHNSWToggle: this.useHNSWToggle,
      })

      // 3. Run consolidation (with HNSW toggle if enabled)
      const consolidationTask = async () => {
        return consolidate({
          threshold: this.similarityThreshold,
          limit: 50, // Process up to 50 pairs per pass
        })
      }

      const result = this.useHNSWToggle
        ? await withHNSWDisabled(consolidationTask)
        : await consolidationTask()

      log.info('Consolidation pass complete', {
        candidatesFound: result.candidatesFound,
        consolidated: result.consolidated,
        deleted: result.deleted,
      })

      // 4. Update counter and reset failure count
      this.lastConsolidationCount = this.currentCount
      this.consecutiveFailures = 0
    } catch (error) {
      this.consecutiveFailures++
      log.error('Consolidation failed', {
        error: (error as Error).message,
        consecutiveFailures: this.consecutiveFailures,
        maxFailures: this.MAX_CONSECUTIVE_FAILURES,
      })
    } finally {
      // 5. Resume ingestion
      ingestPauseController.resume()
      this.isConsolidating = false
    }
  }

  /**
   * Force a consolidation pass (for manual trigger)
   */
  async forceConsolidation(): Promise<void> {
    if (this.isConsolidating) {
      log.warn('Consolidation already in progress')
      return
    }

    await this.runConsolidation()
  }
}

// Singleton watchdog instance
let watchdogInstance: ConsolidationWatchdog | null = null

/**
 * Get or create the consolidation watchdog singleton
 */
export function getConsolidationWatchdog(
  config?: ConsolidationWatchdogConfig
): ConsolidationWatchdog {
  if (!watchdogInstance) {
    watchdogInstance = new ConsolidationWatchdog(config)
  }
  return watchdogInstance
}

/**
 * Reset the singleton (for testing)
 */
export function resetConsolidationWatchdog(): void {
  if (watchdogInstance) {
    watchdogInstance.stop()
    watchdogInstance = null
  }
}
