/**
 * Anthropic LLM Backend
 *
 * Claude API integration via @anthropic-ai/sdk.
 * Supports all Claude 4.5 models (Opus, Sonnet, Haiku).
 *
 * Capabilities:
 * - text-completion, json-completion (all models)
 * - extended-thinking (all 4.5 models)
 * - vision, tool-use, streaming (all models)
 * - long-context (sonnet-4.5 only with beta header)
 */

import Anthropic from '@anthropic-ai/sdk'
import type {
  LLMBackend,
  CanComplete,
  CanCompleteJSON,
  CompletionResult,
  CompletionOptions,
  ClaudeModelKey,
} from '../types.js'
import { CLAUDE_MODELS } from '../types.js'
import type { LLMCapability, LatencyClass, PricingInfo } from '../../../shared/capabilities.js'
import { createLogger } from '../../../shared/logger.js'
import { AnthropicAdapter } from '../adapters/anthropic.js'
import type { UnifiedRequest, UnifiedResponse } from '../message.js'

const log = createLogger('llm:anthropic')

/**
 * Get Anthropic API key from environment
 */
function getAnthropicAPIKey(): string {
  const key = process.env.ANTHROPIC_API_KEY
  if (!key) {
    throw new Error('ANTHROPIC_API_KEY environment variable is not set')
  }
  return key
}

/**
 * Anthropic backend for Claude models.
 * Implements text-completion and json-completion capabilities.
 */
export class AnthropicBackend implements LLMBackend, CanComplete, CanCompleteJSON {
  readonly name: string
  readonly modelId: string
  readonly contextWindow: number
  readonly maxOutputTokens: number
  readonly latency: LatencyClass
  readonly pricing?: PricingInfo
  readonly capabilities: ReadonlySet<LLMCapability>

  /** Message adapter for unified format conversion */
  readonly adapter = new AnthropicAdapter()

  private client: Anthropic
  private modelKey: ClaudeModelKey

  constructor(modelKey: ClaudeModelKey) {
    const spec = CLAUDE_MODELS[modelKey]

    this.modelKey = modelKey
    this.name = `anthropic:${spec.family}`
    this.modelId = spec.id
    this.contextWindow = spec.contextWindow
    this.maxOutputTokens = spec.maxOutputTokens
    this.latency = spec.latency
    this.pricing = spec.pricing
    this.capabilities = spec.capabilities

    // Initialize Anthropic client
    try {
      this.client = new Anthropic({
        apiKey: getAnthropicAPIKey(),
      })
    } catch (error) {
      log.warn('Failed to initialize Anthropic client', {
        error: (error as Error).message,
      })
      // Client will be undefined, isAvailable() will return false
      this.client = null as any
    }

    log.debug('AnthropicBackend initialized', {
      name: this.name,
      modelId: this.modelId,
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
   * Check if Anthropic API is available
   */
  async isAvailable(): Promise<boolean> {
    if (!this.client) {
      return false
    }

    try {
      // Quick health check: list models (lightweight operation)
      // This validates API key without making a completion
      await this.client.models.list({ limit: 1 })
      return true
    } catch (error) {
      log.debug('Anthropic not available', {
        error: (error as Error).message,
      })
      return false
    }
  }

  /**
   * Generate a text completion
   */
  async complete(prompt: string, options?: CompletionOptions): Promise<CompletionResult> {
    if (!this.client) {
      throw new Error('Anthropic client not initialized (missing API key)')
    }

    const maxTokens = options?.maxTokens ?? 4096
    const temperature = options?.temperature ?? 0.7

    log.debug('Anthropic completion request', {
      model: this.modelId,
      promptLength: prompt.length,
      maxTokens,
      temperature,
    })

    try {
      const response = await this.client.messages.create({
        model: this.modelId,
        max_tokens: maxTokens,
        temperature,
        messages: [
          {
            role: 'user',
            content: prompt,
          },
        ],
        // Add beta header for long-context if sonnet-4.5
        ...(this.modelKey === 'sonnet-4.5'
          ? {
              headers: {
                'anthropic-beta': 'max-tokens-3-5-sonnet-2024-07-15',
              },
            }
          : {}),
      })

      // Extract text from content blocks
      const text = response.content
        .filter((block) => block.type === 'text')
        .map((block) => (block as { type: 'text'; text: string }).text)
        .join('')

      const result: CompletionResult = {
        text,
        model: this.modelId,
        stopReason: response.stop_reason ?? undefined,
        usage: {
          inputTokens: response.usage.input_tokens,
          outputTokens: response.usage.output_tokens,
        },
      }

      log.debug('Anthropic completion success', {
        model: this.modelId,
        outputLength: text.length,
        usage: result.usage,
      })

      return result
    } catch (error) {
      log.error('Anthropic completion failed', error as Error)
      throw new Error(`Anthropic completion failed: ${(error as Error).message}`)
    }
  }

  /**
   * Generate a JSON completion
   */
  async completeJSON<T>(prompt: string, options?: CompletionOptions): Promise<T> {
    if (!this.client) {
      throw new Error('Anthropic client not initialized (missing API key)')
    }

    // Ensure prompt requests JSON format
    const jsonPrompt = prompt.includes('JSON')
      ? prompt
      : `${prompt}\n\nRespond with valid JSON only.`

    const result = await this.complete(jsonPrompt, options)

    // Extract JSON from response (handle markdown code fences)
    let jsonText = result.text.trim()

    // Strip markdown code fences if present
    const codeBlockMatch = jsonText.match(/```(?:json)?\s*\n([\s\S]*?)\n```/)
    if (codeBlockMatch && codeBlockMatch[1]) {
      jsonText = codeBlockMatch[1]
    }

    try {
      return JSON.parse(jsonText) as T
    } catch (error) {
      log.error('Failed to parse JSON response', {
        text: jsonText.substring(0, 500),
        error: (error as Error).message,
      })
      throw new Error(`Failed to parse JSON response: ${(error as Error).message}`)
    }
  }

  /**
   * Generate a completion using unified message format
   * Uses the message adapter for format conversion
   */
  async completeWithMessages(request: UnifiedRequest): Promise<UnifiedResponse> {
    if (!this.client) {
      throw new Error('Anthropic client not initialized (missing API key)')
    }

    log.debug('Anthropic unified message request', {
      model: request.model ?? this.modelId,
      messageCount: request.messages.length,
    })

    try {
      // Extract system messages (Anthropic requires separate parameter)
      const [systemPrompt, messages] = AnthropicAdapter.extractSystemMessage(request.messages)

      // Convert to native format
      const nativeRequest = this.adapter.toNativeRequest({
        ...request,
        messages, // Use filtered messages without system
        model: request.model ?? this.modelId,
      })

      // Add system prompt if present
      const requestWithSystem = systemPrompt
        ? { ...nativeRequest, system: systemPrompt }
        : nativeRequest

      // Call Anthropic API
      const response = await this.client.messages.create(requestWithSystem)

      // Convert response to unified format
      const unifiedResponse = this.adapter.fromNativeResponse(response)

      log.debug('Anthropic unified message response', {
        model: unifiedResponse.model,
        stopReason: unifiedResponse.stopReason,
        usage: unifiedResponse.usage,
      })

      return unifiedResponse
    } catch (error) {
      log.error('Anthropic unified message completion failed', error as Error)
      throw new Error(`Anthropic completion failed: ${(error as Error).message}`)
    }
  }
}

/**
 * Backend lifecycle management:
 * Backends are managed by the registry in services/llm/index.ts.
 * Use llmRegistry.get('anthropic:haiku') to retrieve instances.
 *
 * Singleton pattern removed in favor of registry-managed lifecycle.
 */
