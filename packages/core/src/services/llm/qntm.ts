/**
 * QNTM Generation Providers
 *
 * Domain-specific prompt building for QNTM key generation.
 * Uses llm/ module for actual LLM completions.
 *
 * Supports abstraction levels:
 * - L0 (Instance): Specific events, exact references
 * - L1 (Topic): Deduplicated, topic-level concepts
 * - L2 (Concept): Summarized, decontextualized facts
 * - L3 (Principle): Abstract patterns, transferable insights
 */

import pRetry from 'p-retry'
import type { QNTMGenerationInput, QNTMGenerationResult } from '.'
import { getLLMBackendFor, type LLMConfig } from '.'
import { createLogger } from '../../shared/logger'
import { buildTaskPrompt } from '../../prompts/builders'
import type { QNTMAbstractionLevel } from '../../prompts/types'

const log = createLogger('qntm:providers')

// Retry configuration for QNTM generation
const RETRY_OPTIONS = {
  retries: 3,
  factor: 2,
  minTimeout: 1000,
  maxTimeout: 8000,
  onFailedAttempt: (context: { error: Error; attemptNumber: number; retriesLeft: number }) => {
    log.warn('QNTM generation attempt failed, retrying...', {
      attemptNumber: context.attemptNumber,
      retriesLeft: context.retriesLeft,
      error: context.error.message,
    })
  },
}

// Re-export types for backwards compatibility
export type { LLMConfig as ProviderConfig, LLMProvider as QNTMProvider } from '.'
export type { QNTMAbstractionLevel } from '../../prompts/types'

/**
 * Extended QNTM generation input with abstraction level.
 */
export interface QNTMGenerationInputWithLevel extends QNTMGenerationInput {
  level?: QNTMAbstractionLevel
}

/**
 * Build QNTM generation prompt
 *
 * Uses QNTM language spec (EBNF) to ensure proper ternary relationship format.
 * Supports abstraction levels for consolidation pipeline.
 *
 * @param input - Chunk text, existing keys, context, and abstraction level
 * @returns Prompt string for LLM
 */
export async function buildQNTMPrompt(input: QNTMGenerationInputWithLevel): Promise<string> {
  const { chunk, existingKeys, context, level = 0 } = input

  // Format existing keys
  const formattedKeys = existingKeys.slice(-50).map(k => `- ${k}`).join('\n') || '(none yet)'

  // Format context if provided
  let contextFileName = ''
  let contextChunkIndex = ''
  let contextTotalChunks = ''

  if (context?.fileName) {
    contextFileName = `## Context\nFile: ${context.fileName}\n`
    if (context.chunkIndex !== undefined && context.totalChunks !== undefined) {
      contextChunkIndex = `Chunk: ${context.chunkIndex}`
      contextTotalChunks = `Total: ${context.totalChunks}`
    }
  }

  // Use the new prompt registry
  return await buildTaskPrompt('qntm-generation', {
    chunk,
    existingKeys: formattedKeys,
    contextFileName,
    contextChunkIndex,
    contextTotalChunks,
  })
}

/**
 * Generate QNTM keys using specified provider
 *
 * @param input - Chunk text, existing keys, context, and optional abstraction level
 * @param config - LLM provider configuration
 * @returns Generated QNTM keys with reasoning
 */
export async function generateQNTMKeysWithProvider(
  input: QNTMGenerationInputWithLevel,
  config: LLMConfig
): Promise<QNTMGenerationResult> {
  const prompt = await buildQNTMPrompt(input)

  log.debug('Generating QNTM keys', {
    provider: config.provider,
    model: config.model,
    chunkLength: input.chunk.length,
    existingKeyCount: input.existingKeys.length,
    level: input.level ?? 0,
  })

  // Get JSON-capable LLM backend
  const backend = getLLMBackendFor('json-completion')
  if (!backend) {
    throw new Error('No JSON-capable LLM backend available for QNTM generation')
  }

  // Verify backend has JSON completion method
  if (!('completeJSON' in backend)) {
    throw new Error('Backend does not implement JSON completion')
  }

  log.debug('Using LLM backend for QNTM generation', { backend: backend.name })

  const result = await pRetry(
    () => (backend as import('./types').CanCompleteJSON).completeJSON<QNTMGenerationResult>(prompt),
    RETRY_OPTIONS
  )

  log.trace('QNTM generation result', { backend: backend.name, result })

  return result
}

/**
 * Generate QNTM keys for a search query (query-time expansion).
 * Bridges vocabulary gap between user query and stored content.
 *
 * @param query - User's search query
 * @param existingKeys - Sample of existing keys in knowledge base
 * @returns Generated QNTM keys that would match relevant content
 */
export async function generateQueryQNTMKeys(
  query: string,
  existingKeys: string[]
): Promise<QNTMGenerationResult> {
  // Format existing keys
  const formattedKeys = existingKeys.slice(-50).map(k => `- ${k}`).join('\n') || '(none)'

  const prompt = await buildTaskPrompt('query-expansion', {
    query,
    existingKeys: formattedKeys,
  })

  log.debug('Generating query QNTM keys', {
    queryLength: query.length,
    existingKeyCount: existingKeys.length,
  })

  // Get JSON-capable LLM backend
  const backend = getLLMBackendFor('json-completion')
  if (!backend) {
    throw new Error('No JSON-capable LLM backend available for query expansion')
  }

  if (!('completeJSON' in backend)) {
    throw new Error('Backend does not implement JSON completion')
  }

  log.debug('Using LLM backend for query expansion', { backend: backend.name })

  const result = await pRetry(
    () => (backend as import('./types').CanCompleteJSON).completeJSON<QNTMGenerationResult>(prompt),
    RETRY_OPTIONS
  )

  log.trace('Query QNTM keys generated', { backend: backend.name, keys: result.keys })

  return result
}
