/**
 * Reranker Service Types
 *
 * Capability interfaces for reranker backends.
 * Rerankers are cross-encoders that jointly process query-document pairs
 * for more accurate relevance scoring than embedding similarity alone.
 *
 * Backend implementations:
 * - VoyageReranker (rerank-2.5, rerank-2.5-lite): text-reranking, multilingual
 * - Future: Jina Reranker v2, Qwen3 Reranking, Cohere Rerank
 */

import type { BackendDescriptor, LatencyClass, PricingInfo, RerankerCapability } from '../../shared/capabilities'

// ============================================
// Result Types
// ============================================

/**
 * Single reranking result for a document
 */
export interface RerankResult {
  /** Original index of the document in the input array */
  index: number
  /** Relevance score (0.0-1.0, higher = more relevant) */
  score: number
  /** The document text (returned for convenience) */
  document: string
}

/**
 * Full reranking response
 */
export interface RerankResponse {
  /** Reranked results, sorted by score descending */
  results: RerankResult[]
  /** Model used for reranking */
  model: string
  /** Token usage (if reported) */
  usage?: {
    totalTokens: number
  }
}

// ============================================
// Backend Descriptor
// ============================================

/**
 * Reranker backend descriptor.
 * Extends base descriptor with reranker-specific metadata.
 */
export interface RerankerBackend extends BackendDescriptor<RerankerCapability> {
  /** Model identifier (e.g., 'rerank-2.5') */
  readonly model: string

  /** Maximum tokens per query */
  readonly maxQueryTokens: number

  /** Maximum tokens per document */
  readonly maxDocumentTokens: number

  /** Maximum total tokens (query + all documents) */
  readonly maxTotalTokens: number

  /** Maximum documents per request */
  readonly maxDocuments: number

  /** Relative latency classification */
  readonly latency: LatencyClass

  /** Pricing information (if metered) */
  readonly pricing?: PricingInfo

  /** Whether this reranker supports instruction-following */
  readonly supportsInstructions: boolean
}

// ============================================
// Capability Interfaces (Mixins)
// ============================================

/**
 * Basic text reranking capability.
 * All rerankers implement this.
 */
export interface CanRerankText {
  /**
   * Rerank documents by relevance to a query.
   *
   * @param query - The search query
   * @param documents - Array of documents to rerank
   * @param options - Reranking options
   * @returns Reranked results sorted by score
   */
  rerank(query: string, documents: string[], options?: RerankOptions): Promise<RerankResponse>
}

/**
 * Code-optimized reranking capability.
 * Uses models trained on code structure and semantics.
 *
 * Supported by: Jina Reranker v2, Qwen3 Reranking
 * NOT supported by: Voyage rerankers
 */
export interface CanRerankCode {
  /**
   * Rerank code documents with code-aware model.
   *
   * @param query - The search query (can be natural language or code)
   * @param documents - Array of code documents to rerank
   * @param options - Reranking options
   * @returns Reranked results sorted by score
   */
  rerankCode(query: string, documents: string[], options?: RerankOptions): Promise<RerankResponse>
}

/**
 * Multilingual reranking capability.
 * Handles queries and documents in multiple languages.
 *
 * Supported by: Voyage rerank-2.5-lite, Jina v2, Qwen3
 */
export interface CanRerankMultilingual {
  /**
   * Rerank with multilingual support.
   * Same interface as rerank(), but explicitly multilingual-aware.
   *
   * @param query - Query in any supported language
   * @param documents - Documents in any supported languages
   * @param options - Reranking options
   * @returns Reranked results
   */
  rerankMultilingual(
    query: string,
    documents: string[],
    options?: RerankOptions
  ): Promise<RerankResponse>

  /** List of supported language codes */
  readonly supportedLanguages: string[]
}

// ============================================
// Capability Map (for type narrowing)
// ============================================

/**
 * Maps capability strings to their interface types.
 */
export type RerankerCapabilityMap = {
  'text-reranking': CanRerankText
  'code-reranking': CanRerankCode
  'multilingual-reranking': CanRerankMultilingual
}

// ============================================
// Options Types
// ============================================

/**
 * Options for reranking operations
 */
export interface RerankOptions {
  /** Number of top results to return (default: all) */
  topK?: number
  /** Return documents in response (default: true) */
  returnDocuments?: boolean
  /** Truncate documents that exceed max tokens (default: true) */
  truncate?: boolean
}

/**
 * Options for instruction-following rerankers
 */
export interface InstructedRerankOptions extends RerankOptions {
  /**
   * Instructions to guide relevance scoring.
   * Prepended to query for instruction-following models.
   *
   * @example "Prioritize peer-reviewed sources over forums"
   * @example "Focus on recent content from the last 12 months"
   */
  instructions?: string
}

// ============================================
// Configuration Types
// ============================================

/**
 * Configuration for initializing a reranker backend
 */
export interface RerankerBackendConfig {
  /** Model identifier */
  model: string
  /** API key (if required) */
  apiKey?: string
  /** Base URL for API (for self-hosted) */
  baseUrl?: string
  /** Request timeout in milliseconds */
  timeout?: number
}

// ============================================
// Voyage Reranker Specifications
// ============================================

/**
 * Voyage reranker model specifications (from docs, Dec 2025)
 */
export const VOYAGE_RERANKER_MODELS = {
  'rerank-2.5': {
    model: 'rerank-2.5',
    maxQueryTokens: 8000,
    maxDocumentTokens: 8000,
    maxTotalTokens: 600_000,
    maxDocuments: 1000,
    latency: 'moderate' as const,
    supportsInstructions: true,
    capabilities: new Set<RerankerCapability>(['text-reranking']),
    description: 'Generalist reranker optimized for quality with instruction-following',
  },
  'rerank-2.5-lite': {
    model: 'rerank-2.5-lite',
    maxQueryTokens: 8000,
    maxDocumentTokens: 8000,
    maxTotalTokens: 600_000,
    maxDocuments: 1000,
    latency: 'fast' as const,
    supportsInstructions: true,
    capabilities: new Set<RerankerCapability>(['text-reranking', 'multilingual-reranking']),
    description: 'Optimized for latency and quality with multilingual support',
  },
  // Legacy models
  'rerank-2': {
    model: 'rerank-2',
    maxQueryTokens: 4000,
    maxDocumentTokens: 4000,
    maxTotalTokens: 300_000,
    maxDocuments: 1000,
    latency: 'moderate' as const,
    supportsInstructions: false,
    capabilities: new Set<RerankerCapability>(['text-reranking']),
    description: 'Previous generation reranker',
  },
  'rerank-2-lite': {
    model: 'rerank-2-lite',
    maxQueryTokens: 2000,
    maxDocumentTokens: 2000,
    maxTotalTokens: 150_000,
    maxDocuments: 1000,
    latency: 'fast' as const,
    supportsInstructions: false,
    capabilities: new Set<RerankerCapability>(['text-reranking']),
    description: 'Previous generation lite reranker',
  },
} as const

export type VoyageRerankerModel = keyof typeof VOYAGE_RERANKER_MODELS

// ============================================
// Utility Functions
// ============================================

/**
 * Format query with instructions for instruction-following rerankers.
 * Instructions are prepended to the query.
 *
 * @param query - The original search query
 * @param instructions - Optional instructions to guide relevance
 * @returns Formatted query string
 *
 * @example
 * formatInstructedQuery(
 *   "best treatment for headaches",
 *   "Prioritize peer-reviewed journals over forums"
 * )
 * // Returns: "Prioritize peer-reviewed journals over forums\nQuery: best treatment for headaches"
 */
export function formatInstructedQuery(query: string, instructions?: string): string {
  if (!instructions) return query
  return `${instructions}\nQuery: ${query}`
}
