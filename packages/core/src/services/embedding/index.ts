/**
 * Embedding Service - Voyage AI
 */

import { BackendRegistry } from '../../shared/registry'
import { VoyageSnippetBackend, VoyageCodeBackend } from './backends/voyage'
import { VoyageContextBackend } from './backends/voyage-context'
import { VoyageMultimodalBackend } from './backends/voyage-multimodal'
import { OllamaEmbeddingBackend, getOllamaDimensions } from './backends/ollama'
import { getConfig } from '../../shared/config.loader'
import { parseBackendSpecifier } from '../../shared/config.schema'
import { createLogger } from '../../shared/logger'
import type { EmbeddingCapability } from '../../shared/capabilities'
import type { EmbeddingBackend } from './types'

// Re-export types
export type * from './types'

const log = createLogger('embedding')

// ============================================
// Embedding Backend Registry
// ============================================

/**
 * Global embedding backend registry.
 * Lazily initialized to allow runtime config overrides.
 */
export const embeddingRegistry = new BackendRegistry<EmbeddingBackend>()

let initialized = false

/**
 * Initialize embedding backends from current config.
 * Called after CLI args are parsed and runtime overrides applied.
 * Safe to call multiple times - clears and re-registers on subsequent calls.
 */
export function initializeEmbeddingBackends(): void {
  if (initialized) {
    log.debug('Re-initializing embedding backends (clearing previous registrations)')
    embeddingRegistry.clear()
  }

  const config = getConfig()

  const textEmbedding = (config.backends?.['text-embedding'] || 'voyage:voyage-3-large') as string
  const codeEmbedding = (config.backends?.['code-embedding'] || 'voyage:voyage-code-3') as string
  const contextEmbedding = (config.backends?.['contextualized-embedding'] ||
    'voyage:voyage-context-3') as string
  const multimodalEmbedding = (config.backends?.['multimodal-embedding'] || 'voyage:voyage-multimodal-3') as string

  log.debug('Initializing embedding backends', {
    textEmbedding,
    codeEmbedding,
    contextEmbedding,
    multimodalEmbedding,
  })

  // Register embedding backends based on config
  // Voyage backends (when VOYAGE_API_KEY present)
  if (parseBackendSpecifier(textEmbedding).provider === 'voyage') {
    embeddingRegistry.register(new VoyageSnippetBackend())
  }

  if (parseBackendSpecifier(codeEmbedding).provider === 'voyage') {
    embeddingRegistry.register(new VoyageCodeBackend())
  }

  if (parseBackendSpecifier(contextEmbedding).provider === 'voyage') {
    embeddingRegistry.register(new VoyageContextBackend())
  }

  if (parseBackendSpecifier(multimodalEmbedding).provider === 'voyage') {
    embeddingRegistry.register(new VoyageMultimodalBackend())
  }

  // Ollama backends (fallback when VOYAGE_API_KEY not present)
  if (parseBackendSpecifier(textEmbedding).provider === 'ollama') {
    const model = parseBackendSpecifier(textEmbedding).model || 'nomic-embed-text'
    const dimensions = getOllamaDimensions(model)
    embeddingRegistry.register(new OllamaEmbeddingBackend(model, { dimensions }))
  }

  initialized = true

  log.debug('Embedding backends initialized', {
    backends: embeddingRegistry.getAll().map((b) => b.name),
  })
}

// Auto-initialize at module load for backward compatibility
// (CLI will call initializeEmbeddingBackends() after applying runtime overrides)
initializeEmbeddingBackends()

/**
 * Get an embedding backend by capability.
 *
 * @param capability - Embedding capability to look for
 * @returns Embedding backend or undefined
 *
 * @example
 * const backend = getEmbeddingBackend('code-embedding')
 * if (backend && backend.supports('code-embedding')) {
 *   await backend.embedCode(['function main() {}'])
 * }
 */
export function getEmbeddingBackend(capability: EmbeddingCapability): EmbeddingBackend | undefined {
  return embeddingRegistry.getFor(capability)
}

/**
 * Get embedding dimensions from configured text-embedding backend.
 * Used for dynamic collection configuration.
 *
 * @returns Dimensions from configured backend, or 1024 (Voyage default) if no backend available
 */
export function getEmbeddingDimensions(): number {
  const backend = getEmbeddingBackend('text-embedding')
  if (backend) {
    return backend.dimensions
  }
  // Fallback to Voyage default (1024)
  return 1024
}
