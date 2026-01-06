/**
 * SchedulerManager - Global registry for daemon-managed schedulers
 *
 * Pattern: Register at module load, daemon controls lifecycle
 * Decouples watchdogs from ingest lifecycle and enables daemon-managed background tasks.
 */

import { createLogger } from '../shared/logger'

const log = createLogger('scheduler-manager')

/**
 * Interface for schedulers managed by the daemon
 */
export interface ManagedScheduler {
  name: string
  start: () => void
  stop: () => void
  getState: () => { isRunning: boolean; [key: string]: unknown }
}

/**
 * Global scheduler registry
 * Daemon controls lifecycle of all registered schedulers
 */
class SchedulerManager {
  private schedulers = new Map<string, ManagedScheduler>()
  private started = false

  /**
   * Register a scheduler for daemon management
   */
  register(scheduler: ManagedScheduler): void {
    if (this.schedulers.has(scheduler.name)) {
      log.warn('Scheduler already registered, skipping', { name: scheduler.name })
      return
    }

    this.schedulers.set(scheduler.name, scheduler)
    log.debug('Scheduler registered', { name: scheduler.name })

    // If daemon already started, start this scheduler immediately
    if (this.started) {
      log.info('Daemon already running, starting scheduler immediately', { name: scheduler.name })
      scheduler.start()
    }
  }

  /**
   * Unregister a scheduler
   */
  unregister(name: string): void {
    const scheduler = this.schedulers.get(name)
    if (!scheduler) {
      log.debug('Scheduler not found, nothing to unregister', { name })
      return
    }

    // Stop if running
    if (this.started) {
      scheduler.stop()
    }

    this.schedulers.delete(name)
    log.debug('Scheduler unregistered', { name })
  }

  /**
   * Start all registered schedulers
   * Called by daemon on start
   */
  startAll(): void {
    if (this.started) {
      log.warn('Schedulers already started, ignoring duplicate start')
      return
    }

    this.started = true
    log.info('Starting all schedulers', { count: this.schedulers.size })

    for (const [name, scheduler] of this.schedulers) {
      try {
        scheduler.start()
        log.debug('Scheduler started', { name })
      } catch (error) {
        log.error('Failed to start scheduler', {
          name,
          error: (error as Error).message,
        })
      }
    }

    log.info('All schedulers started')
  }

  /**
   * Stop all registered schedulers
   * Called by daemon on stop
   */
  stopAll(): void {
    if (!this.started) {
      log.debug('Schedulers not started, nothing to stop')
      return
    }

    log.info('Stopping all schedulers', { count: this.schedulers.size })

    for (const [name, scheduler] of this.schedulers) {
      try {
        scheduler.stop()
        log.debug('Scheduler stopped', { name })
      } catch (error) {
        log.error('Failed to stop scheduler', {
          name,
          error: (error as Error).message,
        })
      }
    }

    this.started = false
    log.info('All schedulers stopped')
  }

  /**
   * Get status of all schedulers
   */
  getStatus(): Record<string, unknown> {
    const schedulerStates: Record<string, unknown> = {}

    for (const [name, scheduler] of this.schedulers) {
      try {
        schedulerStates[name] = scheduler.getState()
      } catch (error) {
        schedulerStates[name] = {
          error: (error as Error).message,
        }
      }
    }

    return {
      managerStarted: this.started,
      schedulerCount: this.schedulers.size,
      schedulers: schedulerStates,
    }
  }

  /**
   * Check if manager has started
   */
  isStarted(): boolean {
    return this.started
  }

  /**
   * Get scheduler by name
   */
  get(name: string): ManagedScheduler | undefined {
    return this.schedulers.get(name)
  }

  /**
   * Reset manager (for testing)
   */
  reset(): void {
    this.stopAll()
    this.schedulers.clear()
    this.started = false
    log.debug('SchedulerManager reset')
  }
}

// Singleton instance
export const schedulerManager = new SchedulerManager()
