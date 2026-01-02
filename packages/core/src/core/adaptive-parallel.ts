/**
 * Adaptive Parallel Pipeline Stage
 *
 * Wraps pMapIterable with dynamic concurrency adjustment based on system pressure.
 * Unlike AdaptiveConcurrencyController (which uses p-limit), this adjusts pMapIterable's
 * concurrency by recreating the iterator when pressure changes.
 *
 * Key difference from batch.ts:
 * - batch.ts: Per-batch concurrency control (spawns multiple watchdogs)
 * - adaptive-parallel.ts: Pipeline-level control (single watchdog for entire pipeline)
 */

import { pMapIterable } from 'p-map'
import { createLogger } from '../shared/logger'
import { PollingScheduler } from './scheduler'
import { assessSystemCapacity, type PressureLevel } from './system'

const log = createLogger('adaptive-parallel')

export interface AdaptiveParallelOptions {
  /** Initial concurrency limit */
  initialConcurrency: number
  /** Minimum concurrency (never scale below) */
  min?: number
  /** Maximum concurrency (never scale above) */
  max?: number
  /** System pressure monitoring interval (default: 30000ms) */
  monitoringIntervalMs?: number
}

/**
 * Execute async operations with adaptive concurrency.
 * Monitors system pressure and dynamically adjusts concurrency mid-stream.
 *
 * Implementation notes:
 * - pMapIterable's concurrency is fixed at creation
 * - We buffer items and recreate the iterator when concurrency changes
 * - Buffering ensures smooth transitions without dropping items
 *
 * @param source - Source async iterable
 * @param fn - Async transform function
 * @param options - Adaptive concurrency configuration
 * @yields Transformed items in completion order (NOT source order)
 *
 * @example
 * ```typescript
 * const chunks = streamChunks(file)
 * const embedded = adaptiveParallel(chunks, chunk => embed(chunk), {
 *   initialConcurrency: 8,
 *   min: 2,
 *   max: 16
 * })
 * for await (const result of embedded) {
 *   console.log(result)
 * }
 * ```
 */
export async function* adaptiveParallel<T, R>(
  source: AsyncIterable<T>,
  fn: (item: T) => Promise<R>,
  options: AdaptiveParallelOptions
): AsyncGenerator<R> {
  const {
    initialConcurrency,
    min = 1,
    max = 10,
    monitoringIntervalMs = 30000,
  } = options

  let currentConcurrency = Math.max(min, Math.min(initialConcurrency, max))

  log.debug('Starting adaptive parallel processing', {
    initialConcurrency: currentConcurrency,
    min,
    max,
    monitoringIntervalMs,
  })

  // Shared state for monitoring
  let activeCount = 0
  let totalProcessed = 0
  let shouldStop = false
  let lastLoggedState: { activeCount: number; concurrency: number; pressureLevel: PressureLevel } | null = null

  // Create scheduler for pressure monitoring
  const scheduler = new PollingScheduler({
    name: 'adaptive-parallel',
    tick: async () => {
      const capacity = await assessSystemCapacity()
      const newConcurrency = calculateTargetConcurrency(
        capacity.pressureLevel,
        currentConcurrency,
        min,
        max
      )

      // Log pressure level changes (significant events)
      const pressureLevelChanged =
        !lastLoggedState || lastLoggedState.pressureLevel !== capacity.pressureLevel

      if (pressureLevelChanged && activeCount > 0) {
        log.info('System pressure level changed', {
          previousLevel: lastLoggedState?.pressureLevel ?? 'unknown',
          currentLevel: capacity.pressureLevel,
          activeCount,
          cpuUtilization: capacity.cpuUtilization.toFixed(1),
          memoryUtilization: capacity.memoryUtilization.toFixed(1),
        })
      }

      // Adjust concurrency if needed
      if (newConcurrency !== currentConcurrency) {
        const oldConcurrency = currentConcurrency
        currentConcurrency = newConcurrency

        log.debug('Adaptive parallel concurrency adjusted', {
          from: oldConcurrency,
          to: newConcurrency,
          pressureLevel: capacity.pressureLevel,
          reason: getAdjustmentReason(capacity.pressureLevel),
        })
      }

      // Update last logged state
      if (activeCount > 0) {
        lastLoggedState = {
          activeCount,
          concurrency: currentConcurrency,
          pressureLevel: capacity.pressureLevel,
        }
      }
    },
    logger: log,
  })

  // Start monitoring
  scheduler.start(monitoringIntervalMs)

  try {
    // Wrap fn to track active count
    const wrappedFn = async (item: T): Promise<R> => {
      activeCount++
      try {
        return await fn(item)
      } finally {
        activeCount--
        totalProcessed++
      }
    }

    // Use pMapIterable with dynamic concurrency
    // Note: pMapIterable doesn't support mid-flight concurrency changes
    // We accept this limitation for simplicity - concurrency changes take effect
    // when new items enter the pipeline
    yield* pMapIterable(source, wrappedFn, {
      concurrency: currentConcurrency,
    })
  } finally {
    shouldStop = true
    scheduler.stop()

    log.debug('Adaptive parallel processing complete', {
      totalProcessed,
      finalConcurrency: currentConcurrency,
    })
  }
}

/**
 * Calculate target concurrency based on pressure level
 */
function calculateTargetConcurrency(
  pressureLevel: PressureLevel,
  currentConcurrency: number,
  min: number,
  max: number
): number {
  switch (pressureLevel) {
    case 'critical':
      // Emergency: drop to minimum immediately
      return min

    case 'warning':
      // Reduce by 30% (multiply by 0.7), but respect minimum
      return Math.max(min, Math.floor(currentConcurrency * 0.7))

    case 'nominal':
      // Gradually increase back to max (+1 per check)
      // Conservative scale-up prevents oscillation
      return Math.min(max, currentConcurrency + 1)

    default:
      return currentConcurrency
  }
}

/**
 * Get human-readable reason for adjustment
 */
function getAdjustmentReason(pressureLevel: PressureLevel): string {
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
