/**
 * Ollama Embedding Backend
 *
 * Fallback embedding provider for users without VOYAGE_API_KEY.
 * Uses Ollama's /api/embeddings endpoint with models like nomic-embed-text.
 *
 * Key features:
 * - Local, self-hosted embeddings
 * - 768-dimension vectors (nomic-embed-text default)
 * - No API key required
 */

import { OLLAMA_URL } from '../../../shared/config'
import { createLogger } from '../../../shared/logger'
import type { EmbeddingBackend, CanEmbedText, BatchEmbeddingResult } from '../types'
import type { EmbeddingCapability, LatencyClass } from '../../../shared/capabilities'

const log = createLogger('embedding:ollama')

/**
 * Ollama embedding model dimension mapping
 * Maps model names to their output dimensions
 */
const OLLAMA_EMBEDDING_DIMENSIONS: Record<string, number> = {
  'nomic-embed-text': 768,
  'all-minilm': 384,
  'all-minilm:l6-v2': 384,
  'snowflake-arctic-embed': 1024,
  'snowflake-arctic-embed:xs': 384,
  'snowflake-arctic-embed:s': 384,
  'snowflake-arctic-embed:m': 768,
  'snowflake-arctic-embed:l': 1024,
  'mxbai-embed-large': 1024,
  'bge-m3': 1024,
  'bge-large': 1024,
  'granite-embedding:30m': 384,
  'qwen3-embedding:0.6b': 1024,
  'qwen3-embedding:4b': 1024,
  'qwen3-embedding:8b': 1024,
}

/**
 * Get dimensions for an Ollama embedding model
 * @param model - Model name (e.g., 'nomic-embed-text', 'snowflake-arctic-embed:xs')
 * @returns Dimension count, defaulting to 768 if unknown
 */
export function getOllamaDimensions(model: string): number {
  return OLLAMA_EMBEDDING_DIMENSIONS[model] ?? 768 // Default to nomic-embed-text dimensions
}

/**
 * Ollama embedding backend.
 * Supports text-embedding via /api/embeddings.
 */
export class OllamaEmbeddingBackend implements EmbeddingBackend, CanEmbedText {
  readonly name: string
  readonly capabilities: ReadonlySet<EmbeddingCapability> = new Set(['text-embedding'])
  readonly dimensions: number
  readonly maxTokens: number
  readonly model: string
  readonly latency: LatencyClass = 'moderate'
  readonly pricing = { input: 0, output: 0 } // Free (self-hosted)

  private host: string

  constructor(
    modelName: string = 'nomic-embed-text',
    config?: {
      host?: string
      dimensions?: number
      maxTokens?: number
    }
  ) {
    this.model = modelName
    this.name = `ollama:${modelName}`
    this.host = config?.host ?? OLLAMA_URL
    // Use dimension mapping if not explicitly configured
    this.dimensions = config?.dimensions ?? getOllamaDimensions(modelName)
    this.maxTokens = config?.maxTokens ?? 8192

    log.debug('OllamaEmbeddingBackend initialized', {
      name: this.name,
      host: this.host,
      dimensions: this.dimensions,
      model: this.model,
    })
  }

  /**
   * Check if backend is available (Ollama server running and model pulled)
   */
  async isAvailable(): Promise<boolean> {
    try {
      // Check if Ollama server is reachable
      const healthResponse = await fetch(`${this.host}/api/tags`, {
        signal: AbortSignal.timeout(2000),
      })

      if (!healthResponse.ok) {
        return false
      }

      // Check if model is pulled
      const models = (await healthResponse.json()) as { models: Array<{ name: string }> }
      const modelExists = models.models.some((m) => m.name.startsWith(this.model))

      return modelExists
    } catch (error) {
      log.debug('Ollama not available', {
        host: this.host,
        error: (error as Error).message,
      })
      return false
    }
  }

  /**
   * Pull model if not available
   */
  async pullModel(): Promise<void> {
    log.info('Pulling Ollama embedding model', { model: this.model, host: this.host })

    try {
      const response = await fetch(`${this.host}/api/pull`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: this.model,
          stream: false, // Don't stream for simplicity
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to pull model: ${response.statusText}`)
      }

      log.info('Embedding model pulled successfully', { model: this.model })
    } catch (error) {
      log.error('Failed to pull embedding model', error as Error)
      throw new Error(`Failed to pull ${this.model}: ${(error as Error).message}`)
    }
  }

  /**
   * Ensure model is available (pull if needed)
   */
  async ensureModel(): Promise<void> {
    const available = await this.isAvailable()

    if (available) {
      log.debug('Embedding model already available', { model: this.model })
      return
    }

    log.info('Embedding model not found, pulling...', { model: this.model })
    await this.pullModel()
  }

  /**
   * Ensure backend is available and ready to use
   * @returns true if model is ready, false if pull failed
   */
  async ensureAvailable(): Promise<boolean> {
    const available = await this.isAvailable()
    if (available) return true

    log.info('Model not available, attempting to pull...', { model: this.model })
    try {
      await this.pullModel()
      return true
    } catch (error) {
      log.error('Failed to pull model', { model: this.model, error })
      return false
    }
  }

  /**
   * Check if backend supports a capability
   */
  supports(cap: EmbeddingCapability): boolean {
    return this.capabilities.has(cap)
  }

  /**
   * Embed text using Ollama /api/embeddings
   *
   * @param input - Single string or array of strings
   * @returns Batch embedding result with all vectors
   */
  async embedText(input: string | string[]): Promise<BatchEmbeddingResult> {
    const inputs = Array.isArray(input) ? input : [input]

    log.debug('Embedding text with Ollama', {
      model: this.model,
      count: inputs.length,
      totalChars: inputs.reduce((sum, text) => sum + text.length, 0),
    })

    // Ollama /api/embeddings processes one prompt at a time
    // We need to make multiple requests for batching
    const embeddings: number[][] = []
    let totalTokens = 0
    let totalDurationNs = 0

    for (const text of inputs) {
      const response = await fetch(`${this.host}/api/embeddings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: this.model,
          prompt: text,
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(
          `Ollama embedding failed: ${response.status} ${response.statusText}\n${errorText}`
        )
      }

      const data = (await response.json()) as {
        embedding: number[]
        prompt_eval_count?: number
        total_duration?: number
      }

      if (!data.embedding || !Array.isArray(data.embedding)) {
        throw new Error('Ollama embedding response missing embedding array')
      }

      embeddings.push(data.embedding)
      totalTokens += data.prompt_eval_count ?? 0
      totalDurationNs += data.total_duration ?? 0
    }

    const dimensions = embeddings[0]?.length ?? this.dimensions

    log.debug('Ollama embeddings complete', {
      count: embeddings.length,
      dimensions,
    })

    return {
      embeddings,
      model: this.model,
      strategy: 'snippet',
      dimensions,
      usage:
        totalTokens > 0
          ? {
              inputTokens: totalTokens,
              durationMs: totalDurationNs > 0 ? Math.round(totalDurationNs / 1_000_000) : undefined,
            }
          : undefined,
    }
  }
}
