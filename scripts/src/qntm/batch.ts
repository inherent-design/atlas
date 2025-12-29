/**
 * Batch QNTM Generation with Adaptive Concurrency
 *
 * Processes multiple chunks concurrently with dynamic concurrency adjustment.
 * Watchdog monitors system pressure and scales workers up/down during long-running batches.
 */

import pRetry from 'p-retry'
import {
  generateQNTMKeys,
  getQNTMProvider,
  type QNTMGenerationInput,
  type QNTMGenerationResult,
} from '.'
import { createLogger } from '../logger'
import { assessSystemCapacity, getRecommendedConcurrency } from '../system'
import { AdaptiveConcurrencyController } from '../watchdog'

const log = createLogger('qntm/batch')

// Retry configuration
const RETRY_OPTIONS = {
  retries: 3,
  factor: 2, // Exponential backoff multiplier
  minTimeout: 1000, // 1 second base delay
  maxTimeout: 8000, // Cap at 8 seconds
  onFailedAttempt: (context: { error: Error; attemptNumber: number; retriesLeft: number }) => {
    log.warn('QNTM generation attempt failed, retrying...', {
      attemptNumber: context.attemptNumber,
      retriesLeft: context.retriesLeft,
      error: context.error.message,
    })
  },
}

/**
 * Get concurrency limit for batch processing
 * System-aware: Adapts to CPU/memory pressure, respects explicit overrides
 * Can be overridden via QNTM_CONCURRENCY environment variable or --jobs CLI flag
 */
async function getConcurrency(): Promise<number> {
  // Check for explicit override (set by CLI --jobs flag)
  const override = process.env.QNTM_CONCURRENCY
  if (override) {
    const parsed = parseInt(override, 10)
    if (!isNaN(parsed) && parsed > 0) {
      log.info('Using explicit concurrency override', {
        concurrency: parsed,
        source: 'QNTM_CONCURRENCY',
      })
      return parsed
    }
  }

  // Calculate static baseline: 60% of CPU cores, capped at 10
  const cpuCount = require('os').cpus().length
  const staticLimit = Math.min(Math.max(2, Math.floor(cpuCount * 0.6)), 10)

  // Adjust based on system pressure
  const recommended = await getRecommendedConcurrency(staticLimit, 2, 10)

  log.debug('Determined batch concurrency', {
    cpuCount,
    staticLimit,
    recommended,
    override: 'Use --jobs <n> to override',
  })

  return recommended
}

/**
 * Generate QNTM keys for multiple chunks concurrently
 *
 * @param inputs - Array of chunk inputs to process
 * @returns Array of QNTM generation results (same order as inputs)
 */
export async function generateQNTMKeysBatch(
  inputs: QNTMGenerationInput[]
): Promise<QNTMGenerationResult[]> {
  if (inputs.length === 0) return []

  // Assess system capacity before starting batch work
  const capacity = await assessSystemCapacity()
  log.info('System capacity assessed', {
    pressureLevel: capacity.pressureLevel,
    cpuUtilization: capacity.cpuUtilization.toFixed(1),
    memoryUtilization: capacity.memoryUtilization.toFixed(1),
    canSpawnWorker: capacity.canSpawnWorker,
  })

  if (capacity.pressureLevel === 'critical') {
    log.warn('Critical system pressure detected, batch processing may be slow', {
      availableMemoryGB: (capacity.details.availableMemory / 1024 / 1024 / 1024).toFixed(2),
      swapUsageGB: (capacity.details.swapUsage / 1024 / 1024 / 1024).toFixed(2),
    })
  }

  const concurrency = await getConcurrency()
  const providerConfig = getQNTMProvider()

  log.info('Starting batch QNTM generation', {
    totalInputs: inputs.length,
    concurrency,
    provider: providerConfig.provider,
    model: providerConfig.model,
    systemPressure: capacity.pressureLevel,
  })

  // Ensure Ollama model is pulled ONCE before batch work starts
  if (providerConfig.provider === 'ollama') {
    log.debug('Ensuring Ollama model before batch processing', {
      model: providerConfig.model,
    })

    const { ensureModel } = await import('../ollama')
    await ensureModel(providerConfig.model, providerConfig.ollamaHost)

    log.debug('Ollama model ready', { model: providerConfig.model })
  }

  // Create adaptive concurrency controller with watchdog
  const controller = new AdaptiveConcurrencyController(concurrency, 1, 10)
  controller.startWatchdog(10000) // Poll every 10 seconds

  try {
    // Track failures for reporting
    const failures: Array<{ index: number; error: Error }> = []

    // Create promise array with adaptive concurrency limiting and retries
    const promises = inputs.map((input, index) =>
      controller.run(async () => {
        const state = controller.getState()
        log.trace('Processing chunk in batch', {
          index,
          chunkLength: input.chunk.length,
          activeCount: state.activeWorkers,
          pendingCount: state.pendingTasks,
          currentConcurrency: state.currentConcurrency,
        })

        try {
          const result = await pRetry(() => generateQNTMKeys(input), RETRY_OPTIONS)

          log.debug('Batch chunk complete', {
            index,
            keyCount: result.keys.length,
            activeCount: controller.getState().activeWorkers,
            pendingCount: controller.getState().pendingTasks,
          })

          return result
        } catch (error) {
          const err = error as Error
          log.error(`Failed to generate QNTM keys for chunk ${index} after retries`, err)
          failures.push({ index, error: err })

          // Return empty result to maintain array order
          return {
            keys: [],
            reasoning: `Failed after ${RETRY_OPTIONS.retries} retries: ${err.message}`,
          }
        }
      })
    )

    // Wait for all to complete (including failures)
    const results = await Promise.all(promises)

    const successCount = results.filter((r) => r.keys.length > 0).length
    const failureCount = failures.length

    log.info('Batch QNTM generation complete', {
      totalProcessed: inputs.length,
      successCount,
      failureCount,
      totalKeys: results.reduce((sum, r) => sum + r.keys.length, 0),
    })

    if (failures.length > 0) {
      log.warn('Some chunks failed QNTM generation', {
        failureCount: failures.length,
        failedIndices: failures.map((f) => f.index),
      })
    }

    return results
  } finally {
    // Always cleanup watchdog, even if batch fails
    controller.stopWatchdog()
  }
}
