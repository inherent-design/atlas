/**
 * Reranker Service Layer - Public API
 *
 * Cross-encoder reranking for improved relevance scoring.
 * Complements embedding-based search with query-document interaction.
 *
 * Features:
 * - Backend registry with capability-based lookup
 * - Instruction-following for guided relevance
 * - Multilingual support
 */

import { createLogger } from '../../shared/logger'
import { BackendRegistry } from '../../shared/registry'
import { getConfig } from '../../shared/config.loader'
import { parseBackendSpecifier } from '../../shared/config.schema'
import type { RerankerBackend, RerankResponse, RerankOptions } from './types'

const log = createLogger('reranker')

// ============================================
// Backend Registry
// ============================================

/**
 * Global reranker backend registry.
 * Backends are registered lazily via ensureRerankerBackend().
 */
export const rerankerRegistry = new BackendRegistry<RerankerBackend>()

/**
 * Lazy initialization flag
 */
let initialized = false

/**
 * Ensure reranker backend is registered.
 * Registers backend on first call, subsequent calls are no-op.
 */
async function ensureRerankerBackend(): Promise<void> {
  if (initialized) return

  const config = getConfig()
  const rerankingBackend = (config.backends?.['reranking'] || 'voyage:rerank-2.5') as string

  // Register Voyage reranker if configured
  if (parseBackendSpecifier(rerankingBackend).provider === 'voyage') {
    // Parse model from specifier
    const { model } = parseBackendSpecifier(rerankingBackend)
    const modelKey = model || 'rerank-2.5' // Default to rerank-2.5 if no model specified

    // Dynamic import to avoid circular dependencies
    const { getVoyageRerank25, getVoyageRerank25Lite } = await import('./backends/voyage')
    try {
      // Select appropriate factory based on model
      const voyageBackend =
        modelKey === 'rerank-2.5-lite' ? getVoyageRerank25Lite() : getVoyageRerank25()

      if (await voyageBackend.isAvailable()) {
        rerankerRegistry.register(voyageBackend)
        log.debug('Registered Voyage reranker from config', {
          backend: rerankingBackend,
          model: voyageBackend.model,
        })
      }
    } catch (error) {
      log.debug('Voyage reranker not available', { error: (error as Error).message })
    }
  }

  initialized = true
}

/**
 * Get a reranker backend by name.
 *
 * @param name - Backend name (e.g., 'voyage:rerank-2.5')
 * @returns Backend or undefined if not found
 */
export function getRerankerBackend(name: string): RerankerBackend | undefined {
  return rerankerRegistry.get(name)
}

/**
 * Get first reranker backend that supports a capability.
 *
 * @param capability - Reranker capability to look for
 * @returns Backend or undefined if none support it
 */
export function getRerankerBackendFor(capability: string): RerankerBackend | undefined {
  return rerankerRegistry.getFor(capability)
}

// ============================================
// Convenience Functions
// ============================================

/**
 * Rerank documents using first available backend.
 *
 * @param query - Search query
 * @param documents - Documents to rerank
 * @param options - Reranking options
 * @returns Reranked results sorted by relevance
 */
export async function rerank(
  query: string,
  documents: string[],
  options?: RerankOptions
): Promise<RerankResponse> {
  // Ensure backend is registered (lazy init)
  await ensureRerankerBackend()

  const backend = rerankerRegistry.getFor('text-reranking')
  if (!backend) {
    throw new Error('No reranker backend available')
  }

  // Type-safe check for text-reranking capability
  if (!('rerank' in backend)) {
    throw new Error('Backend does not implement text-reranking')
  }

  return (backend as import('./types').CanRerankText).rerank(query, documents, options)
}

// ============================================
// Re-exports
// ============================================

export type {
  RerankerBackend,
  CanRerankText,
  CanRerankCode,
  CanRerankMultilingual,
  RerankResponse,
  RerankResult,
  RerankOptions,
  InstructedRerankOptions,
} from './types'
