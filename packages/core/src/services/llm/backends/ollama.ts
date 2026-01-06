/**
 * Ollama LLM Backend
 *
 * Dynamic capability discovery via /api/show endpoint.
 * Supports any Ollama model without hardcoding capabilities.
 *
 * Key features:
 * - Runtime capability detection (vision, tools, etc.)
 * - Extended thinking for compatible models (qwen3, deepseek-r1, etc.)
 * - Auto-model pulling if not available
 */

import type {
  LLMBackend,
  CanComplete,
  CanCompleteJSON,
  CompletionResult,
  CompletionOptions,
  OllamaModelDetails,
} from '../types'
import { mapOllamaCapabilities, ollamaSupportsThinking } from '../types'
import type { LLMCapability, LatencyClass } from '../../../shared/capabilities'
import { createLogger } from '../../../shared/logger'
import { OLLAMA_URL } from '../../../shared/config'
import { OllamaAdapter } from '../adapters/ollama'
import type { UnifiedRequest, UnifiedResponse } from '../message'

const log = createLogger('llm:ollama')

/**
 * Ollama backend with dynamic capability discovery.
 */
export class OllamaLLMBackend implements LLMBackend, CanComplete, CanCompleteJSON {
  readonly name: string
  readonly modelId: string
  readonly contextWindow: number
  readonly maxOutputTokens: number
  readonly latency: LatencyClass
  readonly capabilities: ReadonlySet<LLMCapability>

  /** Message adapter for unified format conversion */
  readonly adapter = new OllamaAdapter()

  private host: string
  private discovered: boolean = false
  private discoveryPromise: Promise<void> | null = null

  constructor(
    modelName: string,
    config?: {
      host?: string
      contextWindow?: number
      maxOutputTokens?: number
    }
  ) {
    this.modelId = modelName
    this.name = `ollama:${modelName}`
    this.host = config?.host ?? OLLAMA_URL

    // Default values (will be updated after discovery)
    this.contextWindow = config?.contextWindow ?? 8192 // Conservative default
    this.maxOutputTokens = config?.maxOutputTokens ?? 4096
    this.latency = 'moderate' // Ollama is generally moderate-to-slow

    // Initialize with minimal capabilities (will be discovered)
    this.capabilities = new Set<LLMCapability>(['text-completion', 'json-completion', 'streaming'])

    log.debug('OllamaLLMBackend initialized', {
      name: this.name,
      host: this.host,
      capabilities: [...this.capabilities],
    })
  }

  /**
   * Check if backend supports a capability
   */
  supports(cap: LLMCapability): boolean {
    return this.capabilities.has(cap)
  }

  /**
   * Discover model capabilities via /api/show
   * Uses promise lock to prevent concurrent discovery calls
   */
  private async discover(): Promise<void> {
    if (this.discovered) return

    // Serialize concurrent calls - only first caller does actual work
    if (this.discoveryPromise) {
      return this.discoveryPromise
    }

    this.discoveryPromise = this.doDiscover()
    try {
      await this.discoveryPromise
    } finally {
      this.discoveryPromise = null
    }
  }

  private async doDiscover(): Promise<void> {
    try {
      log.debug('Discovering Ollama model capabilities', {
        model: this.modelId,
        host: this.host,
      })

      const response = await fetch(`${this.host}/api/show`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: this.modelId }),
      })

      if (!response.ok) {
        log.warn('Failed to discover model capabilities', {
          model: this.modelId,
          status: response.status,
        })
        return
      }

      const details = (await response.json()) as OllamaModelDetails

      // Map Ollama capabilities to our LLMCapability type
      const discoveredCaps = mapOllamaCapabilities(details.capabilities ?? [])

      // Add thinking capability if model supports it
      if (ollamaSupportsThinking(this.modelId)) {
        discoveredCaps.add('extended-thinking')
      }

      // Update capabilities
      ;(this.capabilities as Set<LLMCapability>).clear()
      for (const cap of discoveredCaps) {
        ;(this.capabilities as Set<LLMCapability>).add(cap)
      }

      this.discovered = true

      log.info('Ollama capabilities discovered', {
        model: this.modelId,
        capabilities: [...this.capabilities],
        family: details.details?.family,
        parameterSize: details.details?.parameter_size,
      })
    } catch (error) {
      log.warn('Capability discovery failed, using defaults', {
        model: this.modelId,
        error: (error as Error).message,
      })
    }
  }

  /**
   * Check if Ollama is available and model exists
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
      const modelExists = models.models.some((m) => m.name.startsWith(this.modelId))

      if (modelExists) {
        // Discover capabilities if not already done
        await this.discover()
      }

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
   * Generate a text completion
   */
  async complete(prompt: string, options?: CompletionOptions): Promise<CompletionResult> {
    // Ensure capabilities are discovered
    if (!this.discovered) {
      await this.discover()
    }

    const maxTokens = options?.maxTokens ?? 512
    const temperature = options?.temperature ?? 0.1

    log.debug('Ollama completion request', {
      model: this.modelId,
      host: this.host,
      promptLength: prompt.length,
      maxTokens,
      temperature,
    })

    try {
      const requestBody = {
        model: this.modelId,
        prompt,
        stream: false,
        options: {
          temperature,
          num_predict: maxTokens,
          stop: options?.stopSequences,
        },
      }

      const response = await fetch(`${this.host}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.statusText}`)
      }

      const data = (await response.json()) as {
        response: string
        prompt_eval_count?: number
        eval_count?: number
      }

      const result: CompletionResult = {
        text: data.response,
        model: this.modelId,
        usage: {
          inputTokens: data.prompt_eval_count ?? 0,
          outputTokens: data.eval_count ?? 0,
        },
      }

      log.debug('Ollama completion success', {
        model: this.modelId,
        outputLength: result.text.length,
        usage: result.usage,
      })

      return result
    } catch (error) {
      log.error('Ollama completion failed', error as Error)
      throw new Error(`Ollama completion failed: ${(error as Error).message}`)
    }
  }

  /**
   * Generate a JSON completion
   */
  async completeJSON<T>(prompt: string, options?: CompletionOptions): Promise<T> {
    // Ensure capabilities are discovered
    if (!this.discovered) {
      await this.discover()
    }

    const maxTokens = options?.maxTokens ?? 512
    const temperature = options?.temperature ?? 0.1

    log.debug('Ollama JSON completion request', {
      model: this.modelId,
      promptLength: prompt.length,
    })

    try {
      const requestBody = {
        model: this.modelId,
        prompt,
        stream: false,
        format: 'json', // Enable JSON mode
        options: {
          temperature,
          num_predict: maxTokens,
          stop: options?.stopSequences,
        },
      }

      const response = await fetch(`${this.host}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.statusText}`)
      }

      const data = (await response.json()) as {
        response: string
      }

      // Parse JSON response
      const parsed = JSON.parse(data.response) as T

      log.debug('Ollama JSON completion success', {
        model: this.modelId,
      })

      return parsed
    } catch (error) {
      log.error('Ollama JSON completion failed', error as Error)
      throw new Error(`Ollama JSON completion failed: ${(error as Error).message}`)
    }
  }

  /**
   * Pull model if not available
   */
  async pullModel(): Promise<void> {
    log.info('Pulling Ollama model', { model: this.modelId, host: this.host })

    try {
      const response = await fetch(`${this.host}/api/pull`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: this.modelId,
          stream: false, // Don't stream for simplicity
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to pull model: ${response.statusText}`)
      }

      log.info('Model pulled successfully', { model: this.modelId })

      // Discover capabilities after pulling
      await this.discover()
    } catch (error) {
      log.error('Failed to pull model', error as Error)
      throw new Error(`Failed to pull ${this.modelId}: ${(error as Error).message}`)
    }
  }

  /**
   * List available models
   */
  async listModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.host}/api/tags`)
      if (!response.ok) {
        throw new Error(`Failed to list models: ${response.statusText}`)
      }

      const data = (await response.json()) as { models: Array<{ name: string }> }
      return data.models.map((m) => m.name)
    } catch (error) {
      log.warn('Failed to list models', error as Error)
      return []
    }
  }

  /**
   * Ensure model is available (pull if needed)
   */
  async ensureModel(): Promise<void> {
    const models = await this.listModels()

    if (models.includes(this.modelId)) {
      log.debug('Model already available', { model: this.modelId })
      return
    }

    log.info('Model not found, pulling...', { model: this.modelId })
    await this.pullModel()
  }

  /**
   * Ensure backend is available and ready to use
   * @returns true if model is ready, false if pull failed
   */
  async ensureAvailable(): Promise<boolean> {
    const available = await this.isAvailable()
    if (available) return true

    log.info('Model not available, attempting to pull...', { model: this.modelId })
    try {
      await this.pullModel()
      return true
    } catch (error) {
      log.error('Failed to pull model', { model: this.modelId, error })
      return false
    }
  }

  /**
   * Generate a completion using unified message format
   * Uses the message adapter for format conversion
   */
  async completeWithMessages(request: UnifiedRequest): Promise<UnifiedResponse> {
    // Ensure capabilities are discovered
    if (!this.discovered) {
      await this.discover()
    }

    log.debug('Ollama unified message request', {
      model: request.model ?? this.modelId,
      messageCount: request.messages.length,
    })

    try {
      // Convert to native Ollama format
      const nativeRequest = this.adapter.toNativeRequest({
        ...request,
        model: request.model ?? this.modelId,
      })

      // Call Ollama chat API
      const response = await fetch(`${this.host}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nativeRequest),
      })

      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.statusText}`)
      }

      const data = (await response.json()) as import('../adapters/ollama').OllamaChatResponse

      // Convert response to unified format
      const unifiedResponse = this.adapter.fromNativeResponse(data)

      log.debug('Ollama unified message response', {
        model: unifiedResponse.model,
        stopReason: unifiedResponse.stopReason,
        usage: unifiedResponse.usage,
      })

      return unifiedResponse
    } catch (error) {
      log.error('Ollama unified message completion failed', error as Error)
      throw new Error(`Ollama completion failed: ${(error as Error).message}`)
    }
  }
}

/**
 * Create an Ollama backend and ensure model is available
 */
export async function createOllamaBackend(
  modelName: string,
  options?: {
    host?: string
    autoPull?: boolean
  }
): Promise<OllamaLLMBackend> {
  const backend = new OllamaLLMBackend(modelName, {
    host: options?.host,
  })

  const available = await backend.isAvailable()

  if (!available && options?.autoPull) {
    log.info('Model not available, auto-pulling', { model: modelName })
    await backend.pullModel()
  }

  return backend
}
