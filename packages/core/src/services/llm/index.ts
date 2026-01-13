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

import { OLLAMA_URL } from '../../shared/config.js'
import { createLogger } from '../../shared/logger.js'
import { BackendRegistry } from '../../shared/registry.js'
import { getConfig } from '../../shared/config.loader.js'
import { getPrimaryCollectionName } from '../../shared/utils.js'
import type { LLMBackend } from './types.js'

const log = createLogger('llm')

// ============================================
// Backend Registry
// ============================================

import { OllamaLLMBackend } from './backends/ollama.js'
import { getClaudeCodeBackend } from './backends/claude-code.js'

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
  const ollamaModel =
    (config.backends?.['text-completion'] || 'ollama:ministral-3:3b')
      .split(':')
      .slice(1)
      .join(':') || 'ministral-3:3b'
  llmRegistry.register(new OllamaLLMBackend(ollamaModel))

  initialized = true

  log.debug('LLM backends initialized', {
    backends: llmRegistry.getAll().map((b) => b.name),
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
 * 1. Domain-specific backend (if domain provided, e.g., 'qntm-generation')
 * 2. Capability-level backend (e.g., 'json-completion')
 * 3. First registered backend with this capability (fallback)
 *
 * @param capability - LLM capability to look for
 * @param domain - Optional domain-specific override (e.g., 'qntm-generation', 'consolidation')
 * @returns Backend or undefined if none support it
 */
export function getLLMBackendFor(capability: string, domain?: string): LLMBackend | undefined {
  const config = getConfig()

  // Priority 1: Domain-specific backend
  if (domain) {
    const domainBackend = config.backends?.[domain as keyof typeof config.backends]
    if (domainBackend) {
      const backend = llmRegistry.get(domainBackend)
      if (backend) {
        log.trace('Using domain-specific backend', { domain, backend: backend.name })
        return backend
      }
      log.debug('Configured domain backend not found in registry', {
        domain,
        configured: domainBackend,
      })
    }
  }

  // Priority 2: Capability-level backend
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

  // Priority 3: Registry fallback
  return llmRegistry.getFor(capability)
}

// ============================================
// Backward-Compatible Exports
// ============================================

// Re-export types
export type { CompletionResult } from './types.js'
export type { ToolDefinition } from './message.js'

// ============================================
// Legacy Configuration Types - REMOVED IN v2.0
// ============================================

/**
 * MIGRATION GUIDE (v2.0 Breaking Change):
 *
 * The legacy LLMConfig/LLMProvider system has been completely removed.
 * Use the backend registry instead:
 *
 * OLD API (removed):
 *   import { setLLMConfig, getLLMConfig, setQNTMProvider, getQNTMProvider } from '@inherent.design/atlas-core'
 *   setLLMConfig({ provider: 'ollama', model: 'mistral' })
 *   const config = getLLMConfig()
 *
 * NEW API (use this):
 *   import { getLLMBackendFor } from '@inherent.design/atlas-core'
 *   const backend = getLLMBackendFor('json-completion')  // or 'text-completion', 'qntm-generation'
 *   const result = await backend.completeJSON(prompt)
 *
 * Configuration now uses config.yaml:
 *   backends:
 *     text-completion: "ollama:ministral-3:3b"
 *     json-completion: "claude-code:haiku"
 *     qntm-generation: "anthropic:opus"
 *
 * See: https://docs.inherent.design/atlas/backends for full migration guide
 */

// ============================================
// QNTM Semantic Key Generation
// ============================================

import { generateQNTMKeysWithProvider, generateQueryQNTMKeys } from './qntm.js'
export { generateQueryQNTMKeys } from './qntm.js'
export type { QNTMAbstractionLevel, QNTMGenerationInputWithLevel } from './qntm.js'

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
 * Generate QNTM semantic keys for a chunk
 *
 * @param input - Chunk text, existing keys for reuse, optional context
 * @returns Array of QNTM keys (1-3 semantic addresses)
 */
export async function generateQNTMKeys(input: QNTMGenerationInput): Promise<QNTMGenerationResult> {
  const result = await generateQNTMKeysWithProvider(input)

  log.debug('QNTM keys generated', {
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
 * Uses multi-tier caching for performance:
 * 1. Try Valkey cache (fastest, ~1ms)
 * 2. Try PostgreSQL metadata DB (fast, ~10ms)
 * 3. Fallback to Qdrant scroll (slow, ~15s for 1,188 points)
 *
 * Used for key reuse during QNTM generation (avoid near-duplicates).
 *
 * @returns Array of unique QNTM keys
 */
export async function fetchExistingQNTMKeys(): Promise<string[]> {
  try {
    // Use StorageService multi-tier pattern (cache → metadata → vector)
    const { getStorageService } = await import('../storage')
    const storageService = getStorageService()

    const keys = await storageService.getAllQNTMKeys(getPrimaryCollectionName())

    log.debug('Fetched existing QNTM keys', {
      total: keys.length,
    })

    return keys
  } catch (error) {
    log.error('Failed to fetch QNTM keys', error as Error)
    return []
  }
}
