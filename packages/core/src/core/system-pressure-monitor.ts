/**
 * SystemPressureMonitor - Global system pressure polling
 *
 * Replaces per-adaptiveParallel polling with shared state.
 * Subscribers get notified when pressure level changes.
 */

import { createLogger } from '../shared/logger'
import { getConfig } from '../shared/config.loader'
import { PollingScheduler } from './scheduler'
import { assessSystemCapacity, type PressureLevel, type SystemCapacity } from './system'
import type { ManagedScheduler } from './scheduler-manager'

const log = createLogger('system-pressure-monitor')

/**
 * Callback for pressure changes
 */
export interface PressureSubscriber {
  (pressure: PressureLevel, capacity: SystemCapacity): void
}

/**
 * System pressure monitor
 * Polls system pressure and notifies subscribers of changes
 */
class SystemPressureMonitor implements ManagedScheduler {
  readonly name = 'system-pressure'
  private scheduler: PollingScheduler
  private subscribers = new Set<PressureSubscriber>()
  private currentPressure: PressureLevel = 'nominal'
  private currentCapacity: SystemCapacity | null = null
  private intervalMs: number

  constructor() {
    const config = getConfig()
    this.intervalMs = config.daemon?.pressureMonitorIntervalMs ?? 30000

    this.scheduler = new PollingScheduler({
      name: 'system-pressure-monitor',
      tick: async () => {
        await this.checkPressure()
      },
    })

    log.debug('SystemPressureMonitor initialized', { intervalMs: this.intervalMs })
  }

  /**
   * Subscribe to pressure changes
   * Returns unsubscribe function
   */
  subscribe(fn: PressureSubscriber): () => void {
    this.subscribers.add(fn)
    log.debug('Pressure subscriber added', { subscriberCount: this.subscribers.size })

    // If we already have capacity data, notify immediately
    if (this.currentCapacity) {
      try {
        fn(this.currentPressure, this.currentCapacity)
      } catch (error) {
        log.error('Subscriber notification failed', error as Error)
      }
    }

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(fn)
      log.debug('Pressure subscriber removed', { subscriberCount: this.subscribers.size })
    }
  }

  /**
   * Get current pressure level
   */
  getCurrentPressure(): PressureLevel {
    return this.currentPressure
  }

  /**
   * Get current capacity snapshot
   */
  getCurrentCapacity(): SystemCapacity | null {
    return this.currentCapacity
  }

  /**
   * Check system pressure and notify subscribers if changed
   */
  private async checkPressure(): Promise<void> {
    try {
      const capacity = await assessSystemCapacity()
      const previousPressure = this.currentPressure
      const newPressure = capacity.pressureLevel

      this.currentCapacity = capacity
      this.currentPressure = newPressure

      // Log pressure level changes
      if (previousPressure !== newPressure) {
        log.info('System pressure level changed', {
          from: previousPressure,
          to: newPressure,
          cpuUtilization: capacity.cpuUtilization.toFixed(1),
          memoryUtilization: capacity.memoryUtilization.toFixed(1),
          subscriberCount: this.subscribers.size,
        })
      } else {
        log.trace('System pressure checked', {
          pressure: newPressure,
          cpuUtilization: capacity.cpuUtilization.toFixed(1),
          memoryUtilization: capacity.memoryUtilization.toFixed(1),
        })
      }

      // Notify all subscribers
      for (const subscriber of this.subscribers) {
        try {
          subscriber(newPressure, capacity)
        } catch (error) {
          log.error('Subscriber notification failed', error as Error)
        }
      }
    } catch (error) {
      log.error('Failed to check system pressure', error as Error)
    }
  }

  /**
   * Start monitoring (ManagedScheduler interface)
   */
  start(): void {
    if (this.scheduler.isRunning()) {
      log.warn('SystemPressureMonitor already running, ignoring duplicate start')
      return
    }

    log.info('Starting system pressure monitoring', { intervalMs: this.intervalMs })
    this.scheduler.start(this.intervalMs)
  }

  /**
   * Stop monitoring (ManagedScheduler interface)
   */
  stop(): void {
    if (!this.scheduler.isRunning()) {
      log.debug('SystemPressureMonitor not running, nothing to stop')
      return
    }

    log.info('Stopping system pressure monitoring')
    this.scheduler.stop()
  }

  /**
   * Get state (ManagedScheduler interface)
   */
  getState(): { isRunning: boolean; pressure: PressureLevel; subscribers: number } {
    return {
      isRunning: this.scheduler.isRunning(),
      pressure: this.currentPressure,
      subscribers: this.subscribers.size,
    }
  }
}

// Singleton instance
let instance: SystemPressureMonitor | null = null

/**
 * Get the global system pressure monitor
 */
export function getSystemPressureMonitor(): SystemPressureMonitor {
  if (!instance) {
    instance = new SystemPressureMonitor()
  }
  return instance
}

/**
 * Reset the singleton (for testing)
 */
export function resetSystemPressureMonitor(): void {
  if (instance) {
    instance.stop()
    instance = null
  }
}
