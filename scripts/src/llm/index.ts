/**
 * LLM Service Layer - Public API
 *
 * Unified interface for LLM completions across providers:
 * - anthropic: Claude via CLI
 * - ollama: Local inference
 *
 * Features:
 * - Single completions (complete, completeJSON)
 * - Batched completions with pressure-aware concurrency
 * - Provider auto-detection
 */

import { OLLAMA_URL } from '../config'
import { createLogger } from '../logger'

const log = createLogger('llm')

// Re-export types and functions
export type { BatchResult } from './batch'
export type { CompletionResult, LLMConfig, LLMProvider } from './providers'

export { checkOllamaAvailable, complete, completeJSON, detectProvider } from './providers'

export { completeBatch } from './batch'

// Global LLM configuration
import type { LLMConfig } from './providers'

let globalConfig: LLMConfig = {
  provider: 'ollama',
  model: 'ministral-3:3b',
  ollamaHost: OLLAMA_URL,
  temperature: 0.1,
}

/**
 * Set global LLM configuration
 */
export function setLLMConfig(config: Partial<LLMConfig>): void {
  globalConfig = { ...globalConfig, ...config }
  log.info('LLM config updated', globalConfig)
}

/**
 * Get current LLM configuration
 */
export function getLLMConfig(): LLMConfig {
  return { ...globalConfig }
}

/**
 * Initialize LLM with auto-detected provider
 */
export async function initLLM(overrides?: Partial<LLMConfig>): Promise<LLMConfig> {
  const { detectProvider } = await import('./providers')

  const provider = overrides?.provider || (await detectProvider(overrides?.ollamaHost))

  const config: LLMConfig = {
    provider,
    model: overrides?.model || (provider === 'ollama' ? 'ministral-3:3b' : 'haiku'),
    ollamaHost: overrides?.ollamaHost || OLLAMA_URL,
    temperature: overrides?.temperature ?? 0.1,
    maxTokens: overrides?.maxTokens,
  }

  setLLMConfig(config)
  return config
}
