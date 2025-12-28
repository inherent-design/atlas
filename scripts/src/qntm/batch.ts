/**
 * Batch QNTM Generation with CPU-Aware Concurrency
 *
 * Processes multiple chunks concurrently using p-limit for concurrency control.
 * Adapts to system CPU count to avoid overwhelming the system while maximizing throughput.
 */

import pLimit from 'p-limit'
import {
  generateQNTMKeys,
  getQNTMProvider,
  type QNTMGenerationInput,
  type QNTMGenerationResult,
} from '.'
import { log } from '../logger'

// CPU-aware concurrency: 75% of available cores, capped at 10 to avoid rate limits
// Can be overridden via QNTM_CONCURRENCY environment variable or --jobs CLI flag
const CONCURRENCY = (() => {
  // Check for explicit override
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

  log.info('Auto-detected batch concurrency', {
    cpuCount,
    computed75Percent: computed,
    finalConcurrency: capped,
    override: 'Use --jobs <n> to override',
  })

  return capped
})()

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

  const limit = pLimit(CONCURRENCY)
  const providerConfig = getQNTMProvider()

  log.info('Starting batch QNTM generation', {
    totalInputs: inputs.length,
    concurrency: CONCURRENCY,
    provider: providerConfig.provider,
    model: providerConfig.model,
  })

  // Create promise array with concurrency limiting
  const promises = inputs.map((input, index) =>
    limit(async () => {
      log.trace('Processing chunk in batch', {
        index,
        chunkLength: input.chunk.length,
        activeCount: limit.activeCount,
        pendingCount: limit.pendingCount,
      })

      try {
        const result = await generateQNTMKeys(input)

        log.debug('Batch chunk complete', {
          index,
          keyCount: result.keys.length,
          activeCount: limit.activeCount,
          pendingCount: limit.pendingCount,
        })

        return result
      } catch (error) {
        log.error(`Failed to generate QNTM keys for chunk ${index}`, error as Error)
        throw error
      }
    })
  )

  // Wait for all to complete
  const results = await Promise.all(promises)

  log.info('Batch QNTM generation complete', {
    totalProcessed: results.length,
    totalKeys: results.reduce((sum, r) => sum + r.keys.length, 0),
  })

  return results
}
