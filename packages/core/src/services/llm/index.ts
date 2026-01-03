/**
 * LLM Service Layer - Public API
 *
 * Unified interface for LLM completions across providers:
 * - anthropic: Claude via SDK
 * - ollama: Local inference
 *
 * Features:
 * - Backend registry with capability-based lookup
 * - Single completions (complete, completeJSON)
 * - Batched completions with pressure-aware concurrency
 * - Provider auto-detection
 * - QNTM semantic key generation
 */

import { OLLAMA_URL, QDRANT_COLLECTION_NAME } from '../../shared/config'
import { createLogger } from '../../shared/logger'
import { BackendRegistry } from '../../shared/registry'
import { getConfig } from '../../shared/config.loader'
import type { LLMBackend } from './types'

const log = createLogger('llm')

// ============================================
// Backend Registry
// ============================================

import { OllamaLLMBackend } from './backends/ollama'
import { getClaudeCodeBackend } from './backends/claude-code'

/**
 * Global LLM backend registry.
 * Lazily initialized to allow runtime config overrides.
 */
export const llmRegistry = new BackendRegistry<LLMBackend>()

let initialized = false

/**
 * Initialize LLM backends from current config.
 * Called after CLI args are parsed and runtime overrides applied.
 * Safe to call multiple times - clears and re-registers on subsequent calls.
 */
export function initializeLLMBackends(): void {
  if (initialized) {
    log.debug('Re-initializing LLM backends (clearing previous registrations)')
    llmRegistry.clear()
  }

  const config = getConfig()

  log.debug('Initializing LLM backends', {
    textCompletion: config.backends?.['text-completion'],
    jsonCompletion: config.backends?.['json-completion'],
    qntmGeneration: config.backends?.['qntm-generation'],
  })

  // Always register Claude Code backends (uses CLI, no API key needed)
  llmRegistry.register(getClaudeCodeBackend('haiku'))
  llmRegistry.register(getClaudeCodeBackend('sonnet'))
  llmRegistry.register(getClaudeCodeBackend('opus'))

  // Register Anthropic API backends (when ANTHROPIC_API_KEY present and SDK installed)
  // Note: Requires @anthropic-ai/sdk package (not installed by default)
  // Skip registration if SDK not available (graceful degradation)
  try {
    if (process.env.ANTHROPIC_API_KEY) {
      // This will throw if @anthropic-ai/sdk is not installed
      const { AnthropicBackend } = require('./backends/anthropic')
      llmRegistry.register(new AnthropicBackend('haiku'))
      llmRegistry.register(new AnthropicBackend('sonnet'))
      llmRegistry.register(new AnthropicBackend('opus'))
      log.debug('Anthropic API backends registered')
    }
  } catch (error) {
    // SDK not installed or import failed - skip Anthropic backends
    log.debug('Anthropic SDK not available, skipping Anthropic API backends', {
      error: (error as Error).message,
    })
  }

  // Always register Ollama backends (local, commonly used)
  const ollamaModel = (config.backends?.['text-completion'] || 'ollama:ministral-3:3b').split(':').slice(1).join(':') || 'ministral-3:3b'
  llmRegistry.register(new OllamaLLMBackend(ollamaModel))

  initialized = true

  log.debug('LLM backends initialized', {
    backends: llmRegistry.getAll().map(b => b.name),
    capabilities: llmRegistry.getCapabilities(),
  })
}

// Auto-initialize at module load for backward compatibility
// (CLI will call initializeLLMBackends() after applying runtime overrides)
initializeLLMBackends()

/**
 * Get an LLM backend by name.
 *
 * @param name - Backend name (e.g., 'anthropic:haiku', 'ollama:ministral')
 * @returns Backend or undefined if not found
 */
export function getLLMBackend(name: string): LLMBackend | undefined {
  return llmRegistry.get(name)
}

/**
 * Get LLM backend for a capability, respecting config preferences.
 *
 * Lookup order:
 * 1. Config-specified backend for this capability (e.g., backends['json-completion'])
 * 2. First registered backend with this capability (fallback)
 *
 * @param capability - LLM capability to look for
 * @returns Backend or undefined if none support it
 */
export function getLLMBackendFor(capability: string): LLMBackend | undefined {
  const config = getConfig()

  // Check if config specifies a backend for this capability
  const configuredBackend = config.backends?.[capability as keyof typeof config.backends]
  if (configuredBackend) {
    const backend = llmRegistry.get(configuredBackend)
    if (backend) {
      log.trace('Using configured backend for capability', { capability, backend: backend.name })
      return backend
    }
    log.debug('Configured backend not found in registry, falling back', {
      capability,
      configured: configuredBackend,
    })
  }

  // Fallback: first backend with capability
  return llmRegistry.getFor(capability)
}

// ============================================
// Backward-Compatible Exports
// ============================================

// Re-export types
export type { CompletionResult } from './types'

// ============================================
// Legacy Configuration Types
// ============================================

/**
 * Legacy LLM configuration type.
 * Used for backward compatibility with QNTM code.
 * New code should use backend registry directly.
 */
export type LLMProvider = 'anthropic' | 'ollama'

export interface LLMConfig {
  provider: LLMProvider
  model?: string
  temperature?: number
  maxTokens?: number
  ollamaHost?: string
}

const defaultConfig: LLMConfig = {
  provider: 'ollama',
  model: 'ministral-3:3b',
  ollamaHost: OLLAMA_URL,
  temperature: 0.1,
}

let globalConfig: LLMConfig = { ...defaultConfig }

/**
 * Reset LLM config to defaults (for testing)
 * @internal Test-only export
 */
export function _resetLLMConfig(): void {
  globalConfig = { ...defaultConfig }
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

// ============================================
// QNTM Semantic Key Generation
// ============================================

import { generateQNTMKeysWithProvider, generateQueryQNTMKeys } from './qntm'
export { generateQueryQNTMKeys } from './qntm'
export type { QNTMAbstractionLevel, QNTMGenerationInputWithLevel } from './qntm'

export interface QNTMGenerationInput {
  chunk: string
  existingKeys: string[]
  context?: {
    fileName?: string
    chunkIndex?: number
    totalChunks?: number
  }
}

export interface QNTMGenerationResult {
  keys: string[]
  reasoning?: string
}

/**
 * Set QNTM provider configuration
 * (Delegates to LLM config)
 */
export function setQNTMProvider(config: Partial<LLMConfig>): void {
  setLLMConfig(config)
  log.info('QNTM provider configured', config)
}

/**
 * Get current QNTM provider configuration
 */
export function getQNTMProvider(): LLMConfig {
  return getLLMConfig()
}

/**
 * Generate QNTM semantic keys for a chunk
 *
 * @param input - Chunk text, existing keys for reuse, optional context
 * @returns Array of QNTM keys (1-3 semantic addresses)
 */
export async function generateQNTMKeys(input: QNTMGenerationInput): Promise<QNTMGenerationResult> {
  const config = getLLMConfig()
  const result = await generateQNTMKeysWithProvider(input, config)

  log.debug('QNTM keys generated', {
    provider: config.provider,
    model: config.model,
    keyCount: result.keys.length,
  })

  log.trace('QNTM keys', { keys: result.keys })

  return result
}

/**
 * Sanitize QNTM key for use as Qdrant collection name
 *
 * Converts: @memory ~ consolidation → memory_consolidation
 */
export function sanitizeQNTMKey(key: string): string {
  return key
    .replace(/@/g, '') // Remove @
    .replace(/~/g, '_') // Replace ~ with _
    .replace(/\s+/g, '_') // Replace spaces with _
    .replace(/[^a-zA-Z0-9_-]/g, '') // Remove invalid chars
    .toLowerCase()
}

/**
 * Fetch all existing QNTM keys from unified atlas collection
 *
 * Scrolls through collection to collect unique qntm_keys from payloads.
 * Used for key reuse during QNTM generation (avoid near-duplicates).
 *
 * @returns Array of unique QNTM keys
 */
export async function fetchExistingQNTMKeys(): Promise<string[]> {
  const { getStorageBackend } = await import('../storage')
  const storage = getStorageBackend()
  if (!storage) {
    log.debug('No storage backend available')
    return []
  }

  try {
    // Check if collection exists
    const exists = await storage.collectionExists(QDRANT_COLLECTION_NAME)
    if (!exists) {
      log.debug('Collection does not exist yet, no existing keys')
      return []
    }

    // Scroll through collection to collect unique keys
    const uniqueKeys = new Set<string>()
    let offset: string | number | null | undefined = undefined
    const SCROLL_LIMIT = 100

    do {
      const result = await storage.scroll(QDRANT_COLLECTION_NAME, {
        limit: SCROLL_LIMIT,
        offset,
        withPayload: true,
        withVector: false,
      })

      for (const point of result.points) {
        const keys = (point.payload as any)?.qntm_keys as string[] | undefined
        if (keys) {
          for (const key of keys) {
            uniqueKeys.add(key)
          }
        }
      }

      offset = result.nextOffset
    } while (offset !== null && offset !== undefined)

    const keysArray = Array.from(uniqueKeys)

    log.debug('Fetched existing QNTM keys from unified collection', {
      total: keysArray.length,
    })

    return keysArray
  } catch (error) {
    log.error('Failed to fetch QNTM keys from Qdrant', error as Error)
    return []
  }
}
