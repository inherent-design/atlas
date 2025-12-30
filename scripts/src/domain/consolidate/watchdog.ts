/**
 * Consolidation Watchdog
 *
 * Monitors ingestion rate and triggers consolidation when threshold reached.
 * Pauses ingestion during consolidation to ensure clean segment state.
 *
 * Flow:
 * 1. Poll every 30s to check documents ingested since last consolidation
 * 2. At threshold (100 docs): set pause flag → wait for in-flight → consolidate → resume
 * 3. Qdrant's vacuum optimizer handles soft-deleted chunks automatically
 */

import { QDRANT_COLLECTION_NAME } from '../../shared/config'
import { consolidate } from '.'
import { createLogger } from '../../shared/logger'
import { PollingScheduler } from '../../core/scheduler'

const log = createLogger('consolidation-watchdog')

// Configuration
const DEFAULT_THRESHOLD = 100 // Documents before triggering consolidation
const DEFAULT_POLL_INTERVAL_MS = 30000 // 30 seconds
const DEFAULT_SIMILARITY_THRESHOLD = 0.92

export interface ConsolidationWatchdogConfig {
  threshold?: number
  pollIntervalMs?: number
  similarityThreshold?: number
}

/**
 * Ingest pause controller
 * Shared state between consolidation watchdog and ingest pipeline
 */
class IngestPauseController {
  private paused = false
  private inFlightCount = 0
  private waitResolvers: Array<() => void> = []

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
    log.info('Ingestion resumed')
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
  }
}

// Singleton pause controller
export const ingestPauseController = new IngestPauseController()

/**
 * Consolidation Watchdog
 *
 * Monitors document count and triggers consolidation at threshold.
 */
export class ConsolidationWatchdog {
  private scheduler: PollingScheduler
  private lastConsolidationCount = 0
  private currentCount = 0
  private threshold: number
  private similarityThreshold: number
  private isConsolidating = false

  constructor(config: ConsolidationWatchdogConfig = {}) {
    this.threshold = config.threshold ?? DEFAULT_THRESHOLD
    this.similarityThreshold = config.similarityThreshold ?? DEFAULT_SIMILARITY_THRESHOLD

    this.scheduler = new PollingScheduler({
      name: 'consolidation',
      tick: () => this.checkAndConsolidate(),
    })

    log.debug('ConsolidationWatchdog initialized', {
      threshold: this.threshold,
      similarityThreshold: this.similarityThreshold,
    })
  }

  /**
   * Start the consolidation watchdog
   */
  start(pollIntervalMs = DEFAULT_POLL_INTERVAL_MS): void {
    log.info('Starting consolidation watchdog', {
      pollIntervalMs,
      threshold: this.threshold,
    })
    this.scheduler.start(pollIntervalMs)
  }

  /**
   * Stop the consolidation watchdog
   */
  stop(): void {
    this.scheduler.stop()
    log.info('Consolidation watchdog stopped', {
      documentsProcessed: this.currentCount - this.lastConsolidationCount,
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
      threshold: this.threshold,
    }
  }

  /**
   * Check if threshold reached and trigger consolidation
   */
  private async checkAndConsolidate(): Promise<void> {
    const documentsSinceConsolidation = this.currentCount - this.lastConsolidationCount

    log.debug('Consolidation check', {
      documentsSinceConsolidation,
      threshold: this.threshold,
      isConsolidating: this.isConsolidating,
    })

    if (documentsSinceConsolidation < this.threshold) {
      return
    }

    if (this.isConsolidating) {
      log.debug('Consolidation already in progress, skipping')
      return
    }

    await this.runConsolidation()
  }

  /**
   * Run consolidation with pause/resume
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
      })

      // 3. Run consolidation
      const result = await consolidate({
        threshold: this.similarityThreshold,
        limit: 50, // Process up to 50 pairs per pass
      })

      log.info('Consolidation pass complete', {
        candidatesFound: result.candidatesFound,
        consolidated: result.consolidated,
        deleted: result.deleted,
      })

      // 4. Update counter
      this.lastConsolidationCount = this.currentCount
    } catch (error) {
      log.error('Consolidation failed', error as Error)
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
export function getConsolidationWatchdog(config?: ConsolidationWatchdogConfig): ConsolidationWatchdog {
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
