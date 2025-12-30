/**
 * PollingScheduler - Base class for interval-based background tasks
 *
 * Provides common lifecycle management for watchdogs and schedulers:
 * - Start/stop with duplicate prevention
 * - Graceful shutdown (completes in-flight tick)
 * - Error handling with logging
 * - State introspection
 */

import { createLogger, type Logger } from '../shared/logger'

export interface PollingSchedulerOptions {
  name: string
  tick: () => Promise<void>
  intervalMs?: number
  logger?: Logger
}

export class PollingScheduler {
  private interval: Timer | null = null
  private isShuttingDown = false
  private tickInProgress = false
  private readonly name: string
  private readonly tick: () => Promise<void>
  private readonly log: Logger

  constructor(options: PollingSchedulerOptions) {
    this.name = options.name
    this.tick = options.tick
    this.log = options.logger || createLogger(`scheduler/${options.name}`)
  }

  /**
   * Start polling at the specified interval
   */
  start(intervalMs: number): void {
    if (this.interval !== null) {
      this.log.warn('Scheduler already running, ignoring duplicate start')
      return
    }

    this.isShuttingDown = false

    this.log.info('Scheduler started', { intervalMs })

    this.interval = setInterval(async () => {
      if (this.isShuttingDown || this.tickInProgress) {
        return
      }

      this.tickInProgress = true
      try {
        await this.tick()
      } catch (error) {
        this.log.error('Scheduler tick failed', error as Error)
      } finally {
        this.tickInProgress = false
      }
    }, intervalMs)
  }

  /**
   * Stop polling gracefully
   * In-flight tick will complete before full stop
   */
  stop(): void {
    if (this.interval === null) {
      this.log.debug('Scheduler not running, nothing to stop')
      return
    }

    this.isShuttingDown = true
    clearInterval(this.interval)
    this.interval = null

    this.log.info('Scheduler stopped')
  }

  /**
   * Check if scheduler is currently running
   */
  isRunning(): boolean {
    return this.interval !== null && !this.isShuttingDown
  }

  /**
   * Check if a tick is currently in progress
   */
  isBusy(): boolean {
    return this.tickInProgress
  }

  /**
   * Get scheduler state for debugging
   */
  getState() {
    return {
      name: this.name,
      isRunning: this.isRunning(),
      isBusy: this.isBusy(),
      isShuttingDown: this.isShuttingDown,
    }
  }

  /**
   * Trigger a single tick manually (for testing)
   */
  async triggerTick(): Promise<void> {
    if (this.tickInProgress) {
      this.log.warn('Tick already in progress, skipping manual trigger')
      return
    }

    this.tickInProgress = true
    try {
      await this.tick()
    } finally {
      this.tickInProgress = false
    }
  }
}
