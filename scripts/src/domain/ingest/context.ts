/**
 * Ingest Context
 *
 * Lazy-cached resolution of backends and capabilities.
 * Eliminates repeated checks like "Contextualized backend not available" per-file.
 *
 * Pattern: Resolve once on context creation, cache for duration of ingest operation.
 */

import { getEmbeddingBackend } from '../../services/embedding'
import { getStorageBackend } from '../../services/storage'
import { getLLMBackend } from '../../services/llm'
import { createLogger } from '../../shared/logger'
import type { EmbeddingBackend } from '../../services/embedding/types'
import type { StorageBackend } from '../../services/storage'
import type { LLMBackend, CanCompleteJSON } from '../../services/llm/types'
import type { IngestConfig } from './index'

const log = createLogger('ingest:context')

/**
 * Ingest context with lazy-cached backend resolution.
 * Capabilities computed once, cached for operation duration.
 */
export interface IngestContext {
  // Lazy-cached backends (resolved on first access)
  getEmbeddingBackend(): Promise<EmbeddingBackend>
  getCodeEmbeddingBackend(): Promise<EmbeddingBackend | null>
  getContextualizedEmbeddingBackend(): Promise<EmbeddingBackend | null>
  getStorageBackend(): Promise<StorageBackend>
  getLLMBackend(): Promise<LLMBackend & CanCompleteJSON>

  // Flags (computed once from config)
  readonly contextualizedAvailable: boolean
  readonly codeEmbeddingAvailable: boolean
  readonly dimensions: number
  readonly rootDir: string
  readonly existingQNTMKeys: string[]
}

/**
 * Create ingest context with lazy backend resolution.
 *
 * Backends are resolved once on first access and cached.
 * Flags are computed eagerly to enable fast capability checks.
 */
export async function createIngestContext(config: IngestConfig): Promise<IngestContext> {
  const rootDir = config.rootDir || process.cwd()
  const existingQNTMKeys = config.existingKeys || []

  // Eagerly check backend availability for flags
  const textBackend = getEmbeddingBackend('text-embedding')
  if (!textBackend) {
    throw new Error('No text embedding backend available')
  }

  const contextBackend = getEmbeddingBackend('contextualized-embedding')
  const codeBackend = getEmbeddingBackend('code-embedding')

  // Check if backends support their respective capabilities
  const contextualizedAvailable = !!(
    contextBackend && 'embedContextualized' in contextBackend
  )
  const codeEmbeddingAvailable = !!(codeBackend && 'embedCode' in codeBackend)

  // Get dimensions from text backend
  const dimensions =
    'dimensions' in textBackend && typeof textBackend.dimensions === 'number'
      ? textBackend.dimensions
      : 1024

  log.debug('Created ingest context', {
    rootDir,
    dimensions,
    contextualizedAvailable,
    codeEmbeddingAvailable,
    existingQNTMKeys: existingQNTMKeys.length,
  })

  // Lazy caches (null until first access)
  let embeddingBackendCache: EmbeddingBackend | null = null
  let codeBackendCache: EmbeddingBackend | null = null
  let contextBackendCache: EmbeddingBackend | null = null
  let storageBackendCache: StorageBackend | null = null
  let llmBackendCache: (LLMBackend & CanCompleteJSON) | null = null

  return {
    // Lazy getters with caching
    async getEmbeddingBackend() {
      if (!embeddingBackendCache) {
        const backend = getEmbeddingBackend('text-embedding')
        if (!backend) {
          throw new Error('No text embedding backend available')
        }

        // Ensure Ollama models are pulled
        if ('ensureAvailable' in backend && typeof backend.ensureAvailable === 'function') {
          const ready = await backend.ensureAvailable()
          if (!ready) {
            throw new Error(`Embedding backend not available: ${backend.name}`)
          }
        }

        embeddingBackendCache = backend
        log.trace('Cached text embedding backend', { backend: backend.name })
      }
      return embeddingBackendCache
    },

    async getCodeEmbeddingBackend() {
      if (!codeEmbeddingAvailable) {
        return null
      }

      if (!codeBackendCache) {
        const backend = getEmbeddingBackend('code-embedding')
        if (!backend) {
          return null
        }

        // Ensure Ollama code models are pulled
        if ('ensureAvailable' in backend && typeof backend.ensureAvailable === 'function') {
          const ready = await backend.ensureAvailable()
          if (!ready) {
            log.warn('Code embedding backend not available after pull attempt', {
              backend: backend.name,
            })
            return null
          }
        }

        codeBackendCache = backend
        log.trace('Cached code embedding backend', { backend: backend.name })
      }
      return codeBackendCache
    },

    async getContextualizedEmbeddingBackend() {
      if (!contextualizedAvailable) {
        return null
      }

      if (!contextBackendCache) {
        const backend = getEmbeddingBackend('contextualized-embedding')
        if (!backend) {
          return null
        }

        // Ensure Ollama contextualized models are pulled
        if ('ensureAvailable' in backend && typeof backend.ensureAvailable === 'function') {
          const ready = await backend.ensureAvailable()
          if (!ready) {
            log.warn('Contextualized embedding backend not available after pull attempt', {
              backend: backend.name,
            })
            return null
          }
        }

        contextBackendCache = backend
        log.trace('Cached contextualized embedding backend', { backend: backend.name })
      }
      return contextBackendCache
    },

    async getStorageBackend() {
      if (!storageBackendCache) {
        const backend = getStorageBackend('vector-storage')
        if (!backend) {
          throw new Error('No vector storage backend available')
        }
        storageBackendCache = backend
        log.trace('Cached storage backend', { backend: backend.name })
      }
      return storageBackendCache
    },

    async getLLMBackend() {
      if (!llmBackendCache) {
        const backend = getLLMBackend('json-completion')
        if (!backend || !('completeJSON' in backend)) {
          throw new Error('No JSON-capable LLM backend available')
        }
        llmBackendCache = backend as LLMBackend & CanCompleteJSON
        log.trace('Cached LLM backend', { backend: backend.name })
      }
      return llmBackendCache
    },

    // Flags (eager, computed once)
    contextualizedAvailable,
    codeEmbeddingAvailable,
    dimensions,
    rootDir,
    existingQNTMKeys,
  }
}
