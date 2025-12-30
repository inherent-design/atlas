/**
 * Batch LLM Completions with Adaptive Concurrency
 *
 * Generic batch processor for LLM completions with:
 * - Pressure-aware concurrency scaling
 * - Watchdog monitoring during long batches
 * - Retry with exponential backoff
 */

import pRetry from 'p-retry'
import { createLogger } from '../logger'
import { ensureModel } from '../ollama'
import { assessSystemCapacity, getRecommendedConcurrency } from '../system'
import { AdaptiveConcurrencyController } from '../watchdog'
import { completeJSON, type LLMConfig } from './providers'

const log = createLogger('llm/batch')

// Retry configuration
const RETRY_OPTIONS = {
  retries: 3,
  factor: 2,
  minTimeout: 1000,
  maxTimeout: 8000,
  onFailedAttempt: (context: { error: Error; attemptNumber: number; retriesLeft: number }) => {
    log.warn('LLM completion attempt failed, retrying...', {
      attemptNumber: context.attemptNumber,
      retriesLeft: context.retriesLeft,
      error: context.error.message,
    })
  },
}

export interface BatchResult<T> {
  results: T[]
  stats: {
    total: number
    success: number
    failed: number
  }
  failures: Array<{ index: number; error: Error }>
}

/**
 * Get concurrency limit for batch processing
 * Respects LLM_CONCURRENCY env var or CLI --jobs flag
 */
async function getConcurrency(): Promise<number> {
  const override = process.env.LLM_CONCURRENCY || process.env.QNTM_CONCURRENCY
  if (override) {
    const parsed = parseInt(override, 10)
    if (!isNaN(parsed) && parsed > 0) {
      log.info('Using explicit concurrency override', {
        concurrency: parsed,
        source: 'LLM_CONCURRENCY',
      })
      return parsed
    }
  }

  const cpuCount = require('os').cpus().length
  const staticLimit = Math.min(Math.max(2, Math.floor(cpuCount * 0.6)), 10)
  const recommended = await getRecommendedConcurrency(staticLimit, 2, 10)

  log.debug('Determined batch concurrency', {
    cpuCount,
    staticLimit,
    recommended,
  })

  return recommended
}

/**
 * Process multiple inputs through LLM with adaptive concurrency
 *
 * @param inputs - Array of inputs to process
 * @param buildPrompt - Function to build prompt from input
 * @param config - LLM configuration
 * @param defaultResult - Default result for failed items (to maintain array order)
 */
export async function completeBatch<I, O>(
  inputs: I[],
  buildPrompt: (input: I, index: number) => string,
  config: LLMConfig,
  defaultResult: (input: I, error: Error) => O
): Promise<BatchResult<O>> {
  if (inputs.length === 0) {
    return {
      results: [],
      stats: { total: 0, success: 0, failed: 0 },
      failures: [],
    }
  }

  // Assess system capacity
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
    })
  }

  const concurrency = await getConcurrency()

  log.info('Starting batch LLM completions', {
    totalInputs: inputs.length,
    concurrency,
    provider: config.provider,
    model: config.model,
    systemPressure: capacity.pressureLevel,
  })

  // Ensure Ollama model is pulled ONCE before batch
  if (config.provider === 'ollama') {
    log.debug('Ensuring Ollama model before batch', { model: config.model })
    await ensureModel(config.model || 'ministral-3:3b', config.ollamaHost)
    log.debug('Ollama model ready', { model: config.model })
  }

  // Create adaptive concurrency controller
  const controller = new AdaptiveConcurrencyController(concurrency, 1, 10)
  controller.startWatchdog(10000)

  const failures: Array<{ index: number; error: Error }> = []

  try {
    const promises = inputs.map((input, index) =>
      controller.run(async () => {
        const state = controller.getState()
        log.trace('Processing item in batch', {
          index,
          activeCount: state.activeWorkers,
          pendingCount: state.pendingTasks,
        })

        try {
          const prompt = buildPrompt(input, index)
          const result = await pRetry(() => completeJSON<O>(prompt, config), RETRY_OPTIONS)

          log.debug('Batch item complete', {
            index,
            activeCount: controller.getState().activeWorkers,
          })

          return result
        } catch (error) {
          const err = error as Error
          log.error(`Failed to process batch item ${index} after retries`, err)
          failures.push({ index, error: err })
          return defaultResult(input, err)
        }
      })
    )

    const results = await Promise.all(promises)

    const successCount = inputs.length - failures.length
    const failureCount = failures.length

    log.info('Batch LLM completions complete', {
      total: inputs.length,
      success: successCount,
      failed: failureCount,
    })

    if (failures.length > 0) {
      log.warn('Some batch items failed', {
        failureCount: failures.length,
        failedIndices: failures.map((f) => f.index),
      })
    }

    return {
      results,
      stats: {
        total: inputs.length,
        success: successCount,
        failed: failureCount,
      },
      failures,
    }
  } finally {
    controller.stopWatchdog()
  }
}
