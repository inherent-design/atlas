/**
 * Mock reranker backend for testing
 *
 * Returns configurable reranking results.
 * Tracks all calls for test assertions.
 */

import type {
  RerankerBackend,
  RerankResponse,
  RerankResult,
  RerankOptions,
} from '../services/reranker/types'

/**
 * Reranking strategy for mock
 */
export type RerankStrategy =
  | 'preserve-order' // Keep original order
  | 'reverse-order' // Reverse the order
  | 'by-length' // Rank by document length (longer = higher score)
  | 'by-query-overlap' // Rank by word overlap with query
  | 'custom' // Use custom scoring function

/**
 * Configuration for MockRerankerBackend
 */
export interface MockRerankerConfig {
  /** Model name to report */
  model?: string
  /** Reranking strategy */
  strategy?: RerankStrategy
  /** Custom scoring function (for 'custom' strategy) */
  scoreFn?: (query: string, document: string, index: number) => number
  /** Fixed scores for specific documents */
  fixedScores?: Record<string, number>
  /** Delay in ms to simulate network latency */
  delay?: number
  /** Error to throw */
  throwError?: Error
}

/**
 * Mock reranker backend
 */
export class MockRerankerBackend implements RerankerBackend {
  readonly name = 'mock-reranker'
  readonly capabilities = new Set(['text-reranking'] as const)
  readonly model: string
  readonly maxQueryTokens = 8000
  readonly maxDocumentTokens = 8000
  readonly maxTotalTokens = 600_000
  readonly maxDocuments = 1000
  readonly latency = 'fast' as const
  readonly supportsInstructions = true

  private config: MockRerankerConfig
  private calls: Array<{
    method: string
    query: string
    documents: string[]
    options?: RerankOptions
    timestamp: number
  }> = []

  constructor(config: MockRerankerConfig = {}) {
    this.config = config
    this.model = config.model || 'mock-rerank-1.0'
  }

  /**
   * Check if backend is available
   */
  async isAvailable(): Promise<boolean> {
    return true // Mock is always available
  }

  /**
   * Check if backend supports a capability
   */
  supports(capability: string): boolean {
    return this.capabilities.has(capability as any)
  }

  /**
   * Rerank documents by relevance
   */
  async rerank(
    query: string,
    documents: string[],
    options?: RerankOptions
  ): Promise<RerankResponse> {
    this.recordCall('rerank', query, documents, options)
    await this.maybeDelay()
    this.maybeThrow()

    // Calculate scores based on strategy
    const results: RerankResult[] = documents.map((document, index) => ({
      index,
      score: this.calculateScore(query, document, index),
      document,
    }))

    // Sort by score descending
    results.sort((a, b) => b.score - a.score)

    // Apply topK limit
    const topK = options?.topK || documents.length
    const limitedResults = results.slice(0, topK)

    // Remove documents if requested
    if (options?.returnDocuments === false) {
      for (const result of limitedResults) {
        ;(result as any).document = undefined
      }
    }

    return {
      results: limitedResults,
      model: this.model,
      usage: {
        totalTokens: this.estimateTokens(query, documents),
      },
    }
  }

  // === Helper Methods ===

  /**
   * Calculate score based on strategy
   */
  private calculateScore(query: string, document: string, index: number): number {
    // Check for fixed score
    if (this.config.fixedScores?.[document]) {
      return this.config.fixedScores[document]
    }

    const strategy = this.config.strategy || 'preserve-order'

    switch (strategy) {
      case 'preserve-order':
        // Higher score for earlier documents
        return 1.0 - index * 0.05

      case 'reverse-order':
        // Higher score for later documents
        return 0.5 + index * 0.05

      case 'by-length':
        // Longer documents get higher scores
        return Math.min(1.0, document.length / 1000)

      case 'by-query-overlap': {
        // Score by word overlap with query
        const queryWords = new Set(query.toLowerCase().split(/\s+/))
        const docWords = document.toLowerCase().split(/\s+/)
        const overlap = docWords.filter((word) => queryWords.has(word)).length
        return Math.min(1.0, overlap / queryWords.size)
      }

      case 'custom':
        if (this.config.scoreFn) {
          return this.config.scoreFn(query, document, index)
        }
        return 0.5

      default:
        return 0.5
    }
  }

  /**
   * Estimate total tokens
   */
  private estimateTokens(query: string, documents: string[]): number {
    const queryTokens = Math.ceil(query.split(/\s+/).length * 1.3)
    const docTokens = documents.reduce(
      (sum, doc) => sum + Math.ceil(doc.split(/\s+/).length * 1.3),
      0
    )
    return queryTokens + docTokens
  }

  /**
   * Maybe delay
   */
  private async maybeDelay(): Promise<void> {
    if (this.config.delay) {
      await new Promise((resolve) => setTimeout(resolve, this.config.delay))
    }
  }

  /**
   * Maybe throw error
   */
  private maybeThrow(): void {
    if (this.config.throwError) {
      throw this.config.throwError
    }
  }

  /**
   * Record call
   */
  private recordCall(
    method: string,
    query: string,
    documents: string[],
    options?: RerankOptions
  ): void {
    this.calls.push({
      method,
      query,
      documents,
      options,
      timestamp: Date.now(),
    })
  }

  // === Test Utilities ===

  /**
   * Get all calls
   */
  getCalls(): Array<{
    method: string
    query: string
    documents: string[]
    options?: RerankOptions
    timestamp: number
  }> {
    return [...this.calls]
  }

  /**
   * Get calls for method
   */
  getCallsFor(method: string): Array<{
    method: string
    query: string
    documents: string[]
    options?: RerankOptions
    timestamp: number
  }> {
    return this.calls.filter((call) => call.method === method)
  }

  /**
   * Get call count
   */
  getCallCount(method?: string): number {
    if (method) {
      return this.calls.filter((call) => call.method === method).length
    }
    return this.calls.length
  }

  /**
   * Clear calls
   */
  clearCalls(): void {
    this.calls = []
  }

  /**
   * Set fixed score for document
   */
  setFixedScore(document: string, score: number): void {
    if (!this.config.fixedScores) {
      this.config.fixedScores = {}
    }
    this.config.fixedScores[document] = score
  }

  /**
   * Set reranking strategy
   */
  setStrategy(strategy: RerankStrategy): void {
    this.config.strategy = strategy
  }

  /**
   * Set custom scoring function
   */
  setScoringFunction(fn: (query: string, document: string, index: number) => number): void {
    this.config.strategy = 'custom'
    this.config.scoreFn = fn
  }

  /**
   * Set error
   */
  setError(error: Error): void {
    this.config.throwError = error
  }

  /**
   * Clear error
   */
  clearError(): void {
    this.config.throwError = undefined
  }

  /**
   * Set delay
   */
  setDelay(ms: number): void {
    this.config.delay = ms
  }
}

/**
 * Create mock reranker backend
 */
export function createMockRerankerBackend(config?: MockRerankerConfig): MockRerankerBackend {
  return new MockRerankerBackend(config)
}
