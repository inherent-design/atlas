/**
 * Batch QNTM Generation
 *
 * Uses llm/batch.ts for generic batch processing, provides QNTM-specific:
 * - Prompt building via buildQNTMPrompt
 * - Result typing via QNTMGenerationResult
 */

import type { QNTMGenerationInput, QNTMGenerationResult } from '.'
import { getLLMConfig } from '.'
import { completeBatch, type BatchResult } from './batch'
import { createLogger } from '../../shared/logger'
import { buildQNTMPrompt } from './qntm'

const log = createLogger('qntm/batch')

/**
 * Generate QNTM keys for multiple chunks concurrently
 *
 * Delegates to llm/batch.completeBatch with QNTM-specific prompt builder.
 *
 * @param inputs - Array of chunk inputs to process
 * @returns Array of QNTM generation results (same order as inputs)
 */
export async function generateQNTMKeysBatch(
  inputs: QNTMGenerationInput[]
): Promise<QNTMGenerationResult[]> {
  if (inputs.length === 0) return []

  const config = getLLMConfig()

  log.info('Starting batch QNTM generation', {
    totalInputs: inputs.length,
    provider: config.provider,
    model: config.model,
  })

  const batchResult: BatchResult<QNTMGenerationResult> = await completeBatch(
    inputs,
    (input, _index) => buildQNTMPrompt(input),
    config,
    (_input, error) => ({
      keys: [],
      reasoning: `Failed: ${error.message}`,
    })
  )

  const totalKeys = batchResult.results.reduce((sum, r) => sum + r.keys.length, 0)

  log.info('Batch QNTM generation complete', {
    totalProcessed: inputs.length,
    successCount: batchResult.stats.success,
    failureCount: batchResult.stats.failed,
    totalKeys,
  })

  if (batchResult.failures.length > 0) {
    log.warn('Some chunks failed QNTM generation', {
      failureCount: batchResult.failures.length,
      failedIndices: batchResult.failures.map((f) => f.index),
    })
  }

  return batchResult.results
}
