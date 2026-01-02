/**
 * Voyage Reranker Backend
 *
 * Reranking service via Voyage AI API.
 * Supports rerank-2.5 and rerank-2.5-lite models.
 *
 * Features:
 * - Instruction-following (v2.5+)
 * - Multilingual support (lite model)
 * - High document capacity (1000 docs, 600K total tokens)
 */

import type {
  RerankerBackend,
  CanRerankText,
  RerankResponse,
  RerankOptions,
  InstructedRerankOptions,
  VoyageRerankerModel,
} from '../types'
import { VOYAGE_RERANKER_MODELS, formatInstructedQuery } from '../types'
import type { RerankerCapability, LatencyClass, PricingInfo } from '../../../shared/capabilities'
import { createLogger } from '../../../shared/logger'

const log = createLogger('reranker/voyage')

/**
 * Get Voyage API key from environment
 */
function getVoyageAPIKey(): string {
  const key = process.env.VOYAGE_API_KEY
  if (!key) {
    throw new Error('VOYAGE_API_KEY environment variable is not set')
  }
  return key
}

/**
 * Voyage reranker backend.
 * Implements text-reranking capability.
 */
export class VoyageRerankerBackend implements RerankerBackend, CanRerankText {
  readonly name: string
  readonly model: string
  readonly maxQueryTokens: number
  readonly maxDocumentTokens: number
  readonly maxTotalTokens: number
  readonly maxDocuments: number
  readonly latency: LatencyClass
  readonly pricing?: PricingInfo
  readonly supportsInstructions: boolean
  readonly capabilities: ReadonlySet<RerankerCapability>

  private apiKey: string
  private baseUrl: string

  constructor(modelKey: VoyageRerankerModel) {
    const spec = VOYAGE_RERANKER_MODELS[modelKey]

    this.name = `voyage:${spec.model}`
    this.model = spec.model
    this.maxQueryTokens = spec.maxQueryTokens
    this.maxDocumentTokens = spec.maxDocumentTokens
    this.maxTotalTokens = spec.maxTotalTokens
    this.maxDocuments = spec.maxDocuments
    this.latency = spec.latency
    this.supportsInstructions = spec.supportsInstructions
    this.capabilities = spec.capabilities

    this.baseUrl = 'https://api.voyageai.com/v1'

    try {
      this.apiKey = getVoyageAPIKey()
    } catch (error) {
      log.warn('Failed to get Voyage API key', {
        error: (error as Error).message,
      })
      this.apiKey = ''
    }

    log.debug('VoyageRerankerBackend initialized', {
      name: this.name,
      model: this.model,
      capabilities: [...this.capabilities],
      supportsInstructions: this.supportsInstructions,
    })
  }

  /**
   * Check if backend supports a capability
   */
  supports(cap: RerankerCapability): boolean {
    return this.capabilities.has(cap)
  }

  /**
   * Check if Voyage API is available
   */
  async isAvailable(): Promise<boolean> {
    if (!this.apiKey) {
      return false
    }

    // No health check endpoint, assume available if API key exists
    return true
  }

  /**
   * Rerank documents by relevance to query
   */
  async rerank(
    query: string,
    documents: string[],
    options?: RerankOptions | InstructedRerankOptions
  ): Promise<RerankResponse> {
    if (!this.apiKey) {
      throw new Error('Voyage API key not configured')
    }

    // Handle instruction-following if supported and provided
    let finalQuery = query
    if (this.supportsInstructions && options && 'instructions' in options && options.instructions) {
      finalQuery = formatInstructedQuery(query, options.instructions)
    }

    const topK = options?.topK ?? documents.length
    const returnDocuments = options?.returnDocuments ?? true
    // Note: Voyage API doesn't support truncate parameter (removed)

    log.debug('Voyage rerank request', {
      model: this.model,
      query: finalQuery.substring(0, 100),
      documentCount: documents.length,
      topK,
    })

    try {
      const response = await fetch(`${this.baseUrl}/rerank`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({
          model: this.model,
          query: finalQuery,
          documents,
          top_k: topK,
          return_documents: returnDocuments,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Voyage API error (${response.status}): ${errorText}`)
      }

      const data = (await response.json()) as {
        data: Array<{
          index: number
          relevance_score: number
          document?: string
        }>
        usage?: {
          total_tokens: number
        }
      }

      const result: RerankResponse = {
        results: data.data.map((item) => ({
          index: item.index,
          score: item.relevance_score,
          document: item.document ?? documents[item.index],
        })),
        model: this.model,
        usage: data.usage
          ? {
              totalTokens: data.usage.total_tokens,
            }
          : undefined,
      }

      log.debug('Voyage rerank success', {
        model: this.model,
        resultCount: result.results.length,
        topScore: result.results[0]?.score,
      })

      return result
    } catch (error) {
      log.error('Voyage rerank failed', error as Error)
      throw new Error(`Voyage rerank failed: ${(error as Error).message}`)
    }
  }
}

/**
 * Create singleton instances for Voyage reranker models
 */
let rerank25Instance: VoyageRerankerBackend | undefined
let rerank25LiteInstance: VoyageRerankerBackend | undefined

export function getVoyageRerank25(): VoyageRerankerBackend {
  if (!rerank25Instance) {
    rerank25Instance = new VoyageRerankerBackend('rerank-2.5')
  }
  return rerank25Instance
}

export function getVoyageRerank25Lite(): VoyageRerankerBackend {
  if (!rerank25LiteInstance) {
    rerank25LiteInstance = new VoyageRerankerBackend('rerank-2.5-lite')
  }
  return rerank25LiteInstance
}
