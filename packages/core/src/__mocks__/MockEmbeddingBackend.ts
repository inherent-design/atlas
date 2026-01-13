/**
 * Mock embedding backend for testing
 *
 * Returns deterministic embeddings based on input text.
 * Tracks all calls for test assertions.
 */

import type {
  EmbeddingBackend,
  BatchEmbeddingResult,
  ContextualizedEmbeddingResult,
  MultimodalEmbeddingResult,
} from '../services/embedding/types.js'
import { generateEmbedding } from '../__fixtures__/embeddings.js'

/**
 * Configuration for MockEmbeddingBackend
 */
export interface MockEmbeddingConfig {
  /** Model name to report */
  model?: string
  /** Vector dimensions */
  dimensions?: number
  /** Fixed embeddings to return (for predictable tests) */
  fixedEmbeddings?: Record<string, number[]>
  /** Delay in ms to simulate network latency */
  delay?: number
  /** Error to throw (for error testing) */
  throwError?: Error
}

/**
 * Mock embedding backend with deterministic output
 */
export class MockEmbeddingBackend implements EmbeddingBackend {
  readonly name = 'mock-embedding'
  readonly capabilities = new Set([
    'text-embedding',
    'code-embedding',
    'multimodal-embedding',
  ] as const)
  readonly dimensions: number
  readonly maxTokens = 8000
  readonly model: string
  readonly latency = 'fast' as const
  readonly maxBatchSize = 32

  private config: MockEmbeddingConfig
  private calls: Array<{ method: string; input: any; timestamp: number }> = []

  constructor(config: MockEmbeddingConfig = {}) {
    this.config = config
    this.model = config.model || 'mock-embedding-1024'
    this.dimensions = config.dimensions || 1024
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
   * Embed text content
   */
  async embedText(input: string | string[]): Promise<BatchEmbeddingResult> {
    this.recordCall('embedText', input)

    if (this.config.delay) {
      await this.sleep(this.config.delay)
    }

    if (this.config.throwError) {
      throw this.config.throwError
    }

    const inputs = Array.isArray(input) ? input : [input]
    const embeddings = inputs.map((text) => this.getEmbedding(text))

    return {
      embeddings,
      model: this.model,
      strategy: 'snippet',
      dimensions: this.dimensions,
      usage: {
        inputTokens: inputs.reduce((sum, text) => sum + this.estimateTokens(text), 0),
      },
    }
  }

  /**
   * Embed code content (same as embedText for mock)
   */
  async embedCode(input: string | string[], _language?: string): Promise<BatchEmbeddingResult> {
    this.recordCall('embedCode', input)

    if (this.config.delay) {
      await this.sleep(this.config.delay)
    }

    if (this.config.throwError) {
      throw this.config.throwError
    }

    const inputs = Array.isArray(input) ? input : [input]
    const embeddings = inputs.map((text) => this.getEmbedding(text, ':code'))

    return {
      embeddings,
      model: this.model,
      strategy: 'snippet',
      dimensions: this.dimensions,
      usage: {
        inputTokens: inputs.reduce((sum, text) => sum + this.estimateTokens(text), 0),
      },
    }
  }

  /**
   * Embed with document context
   */
  async embedContextualized(documents: string[][]): Promise<ContextualizedEmbeddingResult[][]> {
    this.recordCall('embedContextualized', documents)

    if (this.config.delay) {
      await this.sleep(this.config.delay)
    }

    if (this.config.throwError) {
      throw this.config.throwError
    }

    return documents.map((chunks, docIndex) =>
      chunks.map((chunk, chunkIndex) => ({
        embedding: this.getEmbedding(chunk, `:ctx:${docIndex}:${chunkIndex}`),
        model: this.model,
        strategy: 'contextualized' as const,
        dimensions: this.dimensions,
        documentIndex: docIndex,
        chunkIndex,
      }))
    )
  }

  /**
   * Embed multimodal content
   */
  async embedMultimodal(input: Buffer, mimeType: string): Promise<MultimodalEmbeddingResult> {
    this.recordCall('embedMultimodal', { bufferSize: input.length, mimeType })

    if (this.config.delay) {
      await this.sleep(this.config.delay)
    }

    if (this.config.throwError) {
      throw this.config.throwError
    }

    // Use buffer hash as seed for deterministic embedding
    const seed = `multimodal:${mimeType}:${input.length}`

    return {
      embedding: this.getEmbedding(seed),
      model: this.model,
      strategy: 'multimodal',
      dimensions: this.dimensions,
      mimeType,
      extractedText: `[Extracted text from ${mimeType}]`,
    }
  }

  /**
   * Check if MIME type is supported
   */
  supportsMimeType(_mimeType: string): boolean {
    return true // Mock supports all MIME types
  }

  /**
   * Get deterministic embedding for input
   */
  private getEmbedding(text: string, suffix = ''): number[] {
    const key = text + suffix

    // Return fixed embedding if configured
    if (this.config.fixedEmbeddings?.[key]) {
      return this.config.fixedEmbeddings[key]
    }

    // Generate deterministic embedding from text
    return generateEmbedding(key)
  }

  /**
   * Simple token estimation (whitespace split)
   */
  private estimateTokens(text: string): number {
    return Math.ceil(text.split(/\s+/).length * 1.3)
  }

  /**
   * Sleep for testing delay
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  /**
   * Record method call for assertions
   */
  private recordCall(method: string, input: any): void {
    this.calls.push({
      method,
      input,
      timestamp: Date.now(),
    })
  }

  // === Test Utilities ===

  /**
   * Get all recorded calls
   */
  getCalls(): Array<{ method: string; input: any; timestamp: number }> {
    return [...this.calls]
  }

  /**
   * Get calls for a specific method
   */
  getCallsFor(method: string): Array<{ method: string; input: any; timestamp: number }> {
    return this.calls.filter((call) => call.method === method)
  }

  /**
   * Get call count for a method
   */
  getCallCount(method?: string): number {
    if (method) {
      return this.calls.filter((call) => call.method === method).length
    }
    return this.calls.length
  }

  /**
   * Clear call history
   */
  clearCalls(): void {
    this.calls = []
  }

  /**
   * Set fixed embedding for a specific input
   */
  setFixedEmbedding(input: string, embedding: number[]): void {
    if (!this.config.fixedEmbeddings) {
      this.config.fixedEmbeddings = {}
    }
    this.config.fixedEmbeddings[input] = embedding
  }

  /**
   * Configure to throw error on next call
   */
  setError(error: Error): void {
    this.config.throwError = error
  }

  /**
   * Clear error configuration
   */
  clearError(): void {
    this.config.throwError = undefined
  }

  /**
   * Set artificial delay
   */
  setDelay(ms: number): void {
    this.config.delay = ms
  }
}

/**
 * Create a mock embedding backend with optional config
 */
export function createMockEmbeddingBackend(config?: MockEmbeddingConfig): MockEmbeddingBackend {
  return new MockEmbeddingBackend(config)
}
