/**
 * Voyage AI Embedding Backends
 *
 * Implements EmbeddingBackend + capability mixins for Voyage AI models:
 * - VoyageSnippetBackend (voyage-3-large): text-embedding
 * - VoyageCodeBackend (voyage-code-3): text-embedding, code-embedding
 */

import { VoyageAIClient } from 'voyageai'
import { VOYAGE_API_KEY } from '../../../shared/config'
import { createLogger } from '../../../shared/logger'
import { createSingleton } from '../../../shared/utils'
import type {
  EmbeddingBackend,
  EmbeddingCapability,
  CanEmbedText,
  CanEmbedCode,
  BatchEmbeddingResult,
} from '../types'

const log = createLogger('embedding/voyage')

// Singleton Voyage client
function createVoyageClient(): VoyageAIClient {
  if (!VOYAGE_API_KEY) {
    throw new Error('VOYAGE_API_KEY environment variable not set')
  }
  return new VoyageAIClient({ apiKey: VOYAGE_API_KEY })
}

const voyageSingleton = createSingleton(createVoyageClient, 'voyage')

/**
 * Voyage Snippet Backend (voyage-3-large)
 *
 * Capabilities: text-embedding
 * Use for: General prose, documents, snippets
 */
export class VoyageSnippetBackend implements EmbeddingBackend, CanEmbedText {
  readonly name = 'voyage:text'
  readonly capabilities: ReadonlySet<EmbeddingCapability> = new Set(['text-embedding'])
  readonly dimensions = 1024
  readonly maxTokens = 32000
  readonly model = 'voyage-3-large'
  readonly latency = 'moderate' as const
  readonly pricing = { input: 0.08, output: 0 }

  private client: VoyageAIClient

  constructor() {
    this.client = voyageSingleton.get()
  }

  async isAvailable(): Promise<boolean> {
    try {
      // Test with minimal request
      await this.client.embed({
        input: ['test'],
        model: this.model,
      })
      return true
    } catch (error) {
      log.warn('Voyage availability check failed', { error: (error as Error).message })
      return false
    }
  }

  supports(cap: EmbeddingCapability): boolean {
    return this.capabilities.has(cap)
  }

  async embedText(input: string | string[]): Promise<BatchEmbeddingResult> {
    const inputs = Array.isArray(input) ? input : [input]

    const response = await this.client.embed({
      input: inputs,
      model: this.model,
      input_type: 'document',
    })

    return {
      embeddings: response.data.map((item) => item.embedding ?? []),
      model: this.model,
      strategy: 'snippet',
      dimensions: this.dimensions,
      usage: response.usage?.totalTokens
        ? { inputTokens: response.usage.totalTokens }
        : undefined,
    }
  }
}

/**
 * Voyage Code Backend (voyage-code-3)
 *
 * Capabilities: text-embedding, code-embedding
 * Use for: Code files, technical documentation
 */
export class VoyageCodeBackend implements EmbeddingBackend, CanEmbedText, CanEmbedCode {
  readonly name = 'voyage:code'
  readonly capabilities: ReadonlySet<EmbeddingCapability> = new Set([
    'text-embedding',
    'code-embedding',
  ])
  readonly dimensions = 1024
  readonly maxTokens = 32000
  readonly model = 'voyage-code-3'
  readonly latency = 'moderate' as const
  readonly pricing = { input: 0.08, output: 0 }

  private client: VoyageAIClient

  constructor() {
    this.client = voyageSingleton.get()
  }

  async isAvailable(): Promise<boolean> {
    try {
      await this.client.embed({
        input: ['test'],
        model: this.model,
      })
      return true
    } catch (error) {
      log.warn('Voyage code availability check failed', { error: (error as Error).message })
      return false
    }
  }

  supports(cap: EmbeddingCapability): boolean {
    return this.capabilities.has(cap)
  }

  async embedText(input: string | string[]): Promise<BatchEmbeddingResult> {
    const inputs = Array.isArray(input) ? input : [input]

    const response = await this.client.embed({
      input: inputs,
      model: this.model,
      input_type: 'document',
    })

    return {
      embeddings: response.data.map((item) => item.embedding ?? []),
      model: this.model,
      strategy: 'snippet',
      dimensions: this.dimensions,
      usage: response.usage?.totalTokens
        ? { inputTokens: response.usage.totalTokens }
        : undefined,
    }
  }

  async embedCode(input: string | string[], _language?: string): Promise<BatchEmbeddingResult> {
    const inputs = Array.isArray(input) ? input : [input]

    // voyage-code-3 doesn't need explicit language parameter
    const response = await this.client.embed({
      input: inputs,
      model: this.model,
      input_type: 'document',
    })

    return {
      embeddings: response.data.map((item) => item.embedding ?? []),
      model: this.model,
      strategy: 'code',
      dimensions: this.dimensions,
      usage: response.usage?.totalTokens
        ? { inputTokens: response.usage.totalTokens }
        : undefined,
    }
  }
}
