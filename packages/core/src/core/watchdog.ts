/**
 * Adaptive Concurrency Watchdog Controller
 *
 * Dynamically adjusts concurrency based on system pressure during long-running batch operations.
 * Polls system capacity at regular intervals and scales workers up/down to match available resources.
 *
 * Design:
 * - Can't adjust p-limit mid-flight, but can create new instances
 * - Active tasks complete under old limit, new tasks use adjusted limit
 * - Gradual scale-up (conservative), rapid scale-down (protective)
 */

import pLimit from 'p-limit'
import { createLogger } from '../shared/logger'
import { PollingScheduler } from './scheduler'
import { assessSystemCapacity, type PressureLevel } from './system'

const log = createLogger('watchdog')

export class AdaptiveConcurrencyController {
  private limit: ReturnType<typeof pLimit>
  private currentConcurrency: number
  private minWorkers: number
  private maxWorkers: number
  private scheduler: PollingScheduler
  private lastLoggedState: {
    activeWorkers: number
    pendingTasks: number
    concurrency: number
  } | null = null

  constructor(initialConcurrency: number, min = 1, max = 10) {
    this.currentConcurrency = Math.max(min, Math.min(initialConcurrency, max))
    this.minWorkers = min
    this.maxWorkers = max
    this.limit = pLimit(this.currentConcurrency)

    this.scheduler = new PollingScheduler({
      name: 'concurrency',
      tick: () => this.checkAndAdjust(),
      logger: log,
    })

    log.debug('AdaptiveConcurrencyController initialized', {
      initialConcurrency: this.currentConcurrency,
      minWorkers: this.minWorkers,
      maxWorkers: this.maxWorkers,
    })
  }

  /**
   * Start watchdog monitoring
   * Polls system capacity at regular intervals and adjusts concurrency dynamically
   *
   * @param intervalMs - Poll interval in milliseconds (default: 10000ms = 10s)
   */
  startWatchdog(intervalMs = 10000): void {
    log.info('Starting watchdog monitor', {
      intervalMs,
      currentConcurrency: this.currentConcurrency,
    })
    this.scheduler.start(intervalMs)
  }

  /**
   * Stop watchdog monitoring
   * Should be called when batch processing completes (use try/finally)
   */
  stopWatchdog(): void {
    this.scheduler.stop()
    log.info('Watchdog stopped', {
      finalConcurrency: this.currentConcurrency,
      activeWorkers: this.limit.activeCount,
      pendingTasks: this.limit.pendingCount,
    })
  }

  /**
   * Wrap task with concurrency limiting
   * Uses current limit instance (may change over watchdog lifetime)
   */
  async run<T>(task: () => Promise<T>): Promise<T> {
    return this.limit(task)
  }

  /**
   * Get current controller state (for testing/debugging)
   */
  getState() {
    return {
      currentConcurrency: this.currentConcurrency,
      activeWorkers: this.limit.activeCount,
      pendingTasks: this.limit.pendingCount,
      isWatchdogRunning: this.scheduler.isRunning(),
    }
  }

  /**
   * Internal: Check system capacity and adjust concurrency if needed
   */
  private async checkAndAdjust(): Promise<void> {
    const capacity = await assessSystemCapacity()
    const state = this.getState()

    // Only log when state changes or when there's actual work
    const hasWork = state.activeWorkers > 0 || state.pendingTasks > 0
    const stateChanged =
      !this.lastLoggedState ||
      this.lastLoggedState.activeWorkers !== state.activeWorkers ||
      this.lastLoggedState.pendingTasks !== state.pendingTasks ||
      this.lastLoggedState.concurrency !== state.currentConcurrency

    if (hasWork && stateChanged) {
      log.debug('Watchdog check', {
        currentConcurrency: state.currentConcurrency,
        activeWorkers: state.activeWorkers,
        pendingTasks: state.pendingTasks,
        systemPressure: capacity.pressureLevel,
        cpuUtilization: capacity.cpuUtilization.toFixed(1),
        memoryUtilization: capacity.memoryUtilization.toFixed(1),
      })
      this.lastLoggedState = {
        activeWorkers: state.activeWorkers,
        pendingTasks: state.pendingTasks,
        concurrency: state.currentConcurrency,
      }
    }

    const newConcurrency = this.calculateTargetConcurrency(capacity.pressureLevel)

    if (newConcurrency !== this.currentConcurrency) {
      this.adjustConcurrency(newConcurrency, capacity.pressureLevel)
    }
  }

  /**
   * Internal: Calculate target concurrency based on pressure level
   */
  private calculateTargetConcurrency(pressureLevel: PressureLevel): number {
    switch (pressureLevel) {
      case 'critical':
        // Emergency: drop to minimum immediately
        return this.minWorkers

      case 'warning':
        // Reduce by 30% (multiply by 0.7), but respect minimum
        return Math.max(this.minWorkers, Math.floor(this.currentConcurrency * 0.7))

      case 'nominal':
        // Gradually increase back to max (+1 per check)
        // Conservative scale-up prevents oscillation
        return Math.min(this.maxWorkers, this.currentConcurrency + 1)

      default:
        return this.currentConcurrency
    }
  }

  /**
   * Internal: Adjust concurrency by creating new p-limit instance
   * Active tasks continue under old limit, new tasks use new limit
   */
  private adjustConcurrency(newConcurrency: number, pressureLevel: PressureLevel): void {
    const oldConcurrency = this.currentConcurrency
    const oldActiveCount = this.limit.activeCount
    const oldPendingCount = this.limit.pendingCount

    // Create new limit instance with updated concurrency
    this.currentConcurrency = newConcurrency
    this.limit = pLimit(newConcurrency)

    const logLevel = pressureLevel === 'critical' ? 'warn' : 'info'
    const logMethod = log[logLevel].bind(log)

    logMethod('Concurrency adjusted', {
      from: oldConcurrency,
      to: newConcurrency,
      pressureLevel,
      oldActiveWorkers: oldActiveCount,
      oldPendingTasks: oldPendingCount,
      reason: this.getAdjustmentReason(pressureLevel),
    })
  }

  /**
   * Internal: Get human-readable reason for adjustment
   */
  private getAdjustmentReason(pressureLevel: PressureLevel): string {
    switch (pressureLevel) {
      case 'critical':
        return 'Critical pressure: reducing to minimum workers'
      case 'warning':
        return 'Warning pressure: reducing by 30%'
      case 'nominal':
        return 'Nominal pressure: gradually increasing capacity'
      default:
        return 'Unknown pressure level'
    }
  }
}
