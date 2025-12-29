/**
 * Batch QNTM Generation with CPU-Aware Concurrency
 *
 * Processes multiple chunks concurrently using p-limit for concurrency control.
 * Adapts to system CPU count to avoid overwhelming the system while maximizing throughput.
 */

import pLimit from 'p-limit'
import pRetry from 'p-retry'
import {
  generateQNTMKeys,
  getQNTMProvider,
  type QNTMGenerationInput,
  type QNTMGenerationResult,
} from '.'
import { createLogger } from '../logger'

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
 * CPU-aware: 60% of available cores, capped at 10 to avoid rate limits
 * Can be overridden via QNTM_CONCURRENCY environment variable or --jobs CLI flag
 */
function getConcurrency(): number {
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

  // Auto-detect based on CPU count
  const cpuCount = require('os').cpus().length
  const computed = Math.max(2, Math.floor(cpuCount * 0.6))
  const capped = Math.min(computed, 10)

  log.debug('Auto-detected batch concurrency', {
    cpuCount,
    computed60Percent: computed,
    finalConcurrency: capped,
    override: 'Use --jobs <n> to override',
  })

  return capped
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

  const concurrency = getConcurrency()
  const limit = pLimit(concurrency)
  const providerConfig = getQNTMProvider()

  log.info('Starting batch QNTM generation', {
    totalInputs: inputs.length,
    concurrency,
    provider: providerConfig.provider,
    model: providerConfig.model,
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

  // Track failures for reporting
  const failures: Array<{ index: number; error: Error }> = []

  // Create promise array with concurrency limiting and retries
  const promises = inputs.map((input, index) =>
    limit(async () => {
      log.trace('Processing chunk in batch', {
        index,
        chunkLength: input.chunk.length,
        activeCount: limit.activeCount,
        pendingCount: limit.pendingCount,
      })

      try {
        const result = await pRetry(() => generateQNTMKeys(input), RETRY_OPTIONS)

        log.debug('Batch chunk complete', {
          index,
          keyCount: result.keys.length,
          activeCount: limit.activeCount,
          pendingCount: limit.pendingCount,
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
}
