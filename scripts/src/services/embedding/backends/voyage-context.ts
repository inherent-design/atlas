/**
 * Voyage AI Contextualized Embedding Backend
 *
 * Implements EmbeddingBackend + CanEmbedText + CanEmbedContextualized for voyage-context-3.
 * This backend provides document-aware embeddings where each chunk is embedded with
 * awareness of its neighboring chunks, improving retrieval for context-dependent content.
 *
 * @see https://docs.voyageai.com/docs/embeddings#voyage-context-3
 */

import { VoyageAIClient } from 'voyageai'
import { VOYAGE_API_KEY } from '../../../shared/config'
import { createLogger } from '../../../shared/logger'
import { createSingleton } from '../../../shared/utils'
import type {
  EmbeddingBackend,
  EmbeddingCapability,
  CanEmbedText,
  CanEmbedContextualized,
  BatchEmbeddingResult,
  ContextualizedEmbeddingResult,
} from '../types'

const log = createLogger('embedding/voyage-context')

// Singleton Voyage client (shared with other Voyage backends)
function createVoyageClient(): VoyageAIClient {
  if (!VOYAGE_API_KEY) {
    throw new Error('VOYAGE_API_KEY environment variable not set')
  }
  return new VoyageAIClient({ apiKey: VOYAGE_API_KEY })
}

const voyageSingleton = createSingleton(createVoyageClient, 'voyage')

/**
 * Voyage Context Backend (voyage-context-3)
 *
 * Capabilities: text-embedding, contextualized-embedding
 * Use for: Long documents with semantic flow (prose, articles, documentation)
 *
 * Key features:
 * - Document-aware chunk embeddings
 * - 32K context window
 * - 1024-dim output (default)
 * - Supports 256, 512, 1024, 2048 dimensions
 *
 * API Limits:
 * - Max 1,000 documents per request
 * - Max 16,000 chunks total
 * - Max 120K tokens total
 */
export class VoyageContextBackend implements EmbeddingBackend, CanEmbedText, CanEmbedContextualized {
  readonly name = 'voyage:context'
  readonly capabilities: ReadonlySet<EmbeddingCapability> = new Set([
    'text-embedding',
    'contextualized-embedding',
  ])
  readonly dimensions = 1024
  readonly maxTokens = 32000
  readonly model = 'voyage-context-3'
  readonly latency = 'moderate' as const
  readonly pricing = { input: 0.08, output: 0 }

  private client: VoyageAIClient

  constructor() {
    this.client = voyageSingleton.get()
  }

  async isAvailable(): Promise<boolean> {
    try {
      // Test with minimal contextualized request
      await this.client.contextualizedEmbed({
        inputs: [['test']],
        model: this.model,
      })
      return true
    } catch (error) {
      log.warn('Voyage context availability check failed', { error: (error as Error).message })
      return false
    }
  }

  supports(cap: EmbeddingCapability): boolean {
    return this.capabilities.has(cap)
  }

  /**
   * Embed text using contextualized embeddings API.
   *
   * For single strings or simple arrays, wraps inputs as single-element documents.
   * For true document-aware embeddings, use embedContextualized() directly.
   *
   * @param input - Single string or array of strings
   * @returns Batch embedding result with all vectors
   */
  async embedText(input: string | string[]): Promise<BatchEmbeddingResult> {
    const inputs = Array.isArray(input) ? input : [input]

    // Wrap each input as a single-chunk document
    const documents = inputs.map((text) => [text])

    const response = await this.client.contextualizedEmbed({
      inputs: documents,
      model: this.model,
      inputType: 'document',
    })

    // Flatten: each document has one chunk, extract that chunk's embedding
    const embeddings: number[][] = []
    for (const docItem of response.data ?? []) {
      const chunkItem = docItem.data?.[0]
      if (chunkItem?.embedding) {
        embeddings.push(chunkItem.embedding)
      }
    }

    return {
      embeddings,
      model: this.model,
      strategy: 'snippet',
      dimensions: this.dimensions,
      usage: response.usage?.totalTokens
        ? { inputTokens: response.usage.totalTokens }
        : undefined,
    }
  }

  /**
   * Embed chunks with document context awareness.
   *
   * Each chunk is embedded with knowledge of its neighboring chunks in the document,
   * improving retrieval accuracy for content where context matters.
   *
   * @param documents - Array of documents, each document is array of chunks
   * @returns 2D array: results[docIndex][chunkIndex]
   *
   * @example
   * const docs = [
   *   ["Chapter 1: Introduction", "The story begins...", "And then..."],
   *   ["Chapter 2: Conflict", "The hero faces...", "Meanwhile..."]
   * ]
   * const results = await backend.embedContextualized(docs)
   * // results[0][1] = embedding for "The story begins..." with Chapter 1 context
   */
  async embedContextualized(documents: string[][]): Promise<ContextualizedEmbeddingResult[][]> {
    if (documents.length === 0) {
      return []
    }

    // Validate limits
    const totalChunks = documents.reduce((sum, doc) => sum + doc.length, 0)
    if (documents.length > 1000) {
      throw new Error(`Too many documents: ${documents.length} (max 1,000)`)
    }
    if (totalChunks > 16000) {
      throw new Error(`Too many chunks: ${totalChunks} (max 16,000)`)
    }

    const response = await this.client.contextualizedEmbed({
      inputs: documents,
      model: this.model,
      inputType: 'document',
    })

    // Parse response into 2D array structure
    const results: ContextualizedEmbeddingResult[][] = []

    for (const docItem of response.data ?? []) {
      const docIndex = docItem.index ?? results.length
      const docResults: ContextualizedEmbeddingResult[] = []

      for (const chunkItem of docItem.data ?? []) {
        if (chunkItem.embedding) {
          docResults.push({
            embedding: chunkItem.embedding,
            model: this.model,
            strategy: 'contextualized' as const,
            dimensions: this.dimensions,
            documentIndex: docIndex,
            chunkIndex: chunkItem.index ?? docResults.length,
          })
        }
      }

      results[docIndex] = docResults
    }

    return results
  }
}
