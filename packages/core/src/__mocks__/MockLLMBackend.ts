/**
 * Mock LLM backend for testing
 *
 * Returns canned JSON responses.
 * Tracks all calls for test assertions.
 */

import type {
  LLMBackend,
  CompletionResult,
  CompletionOptions,
  ThinkingResult,
  ThinkingOptions,
  ToolUseResult,
  ImageInput,
} from '../services/llm/types.js'
import type { ToolDefinition, UnifiedRequest, UnifiedResponse } from '../services/llm/message.js'

/**
 * Configuration for MockLLMBackend
 */
export interface MockLLMConfig {
  /** Model ID to report */
  modelId?: string
  /** Default JSON response */
  defaultJSON?: any
  /** Fixed responses for specific prompts */
  responses?: Record<string, any>
  /** Delay in ms to simulate network latency */
  delay?: number
  /** Error to throw */
  throwError?: Error
}

/**
 * Mock LLM backend with canned responses
 */
export class MockLLMBackend implements LLMBackend {
  readonly name = 'mock-llm'
  readonly capabilities = new Set([
    'text-completion',
    'json-completion',
    'extended-thinking',
    'vision',
    'tool-use',
    'streaming',
  ] as const)
  readonly modelId: string
  readonly contextWindow = 100_000
  readonly maxOutputTokens = 4_000
  readonly latency = 'fast' as const

  private config: MockLLMConfig
  private calls: Array<{ method: string; prompt: string; options?: any; timestamp: number }> = []

  constructor(config: MockLLMConfig = {}) {
    this.config = config
    this.modelId = config.modelId || 'mock-llm-1.0'
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
   * Generate text completion
   */
  async complete(prompt: string, options?: CompletionOptions): Promise<CompletionResult> {
    this.recordCall('complete', prompt, options)
    await this.maybeDelay()
    this.maybeThrow()

    const response = this.getResponse(prompt) || 'Mock completion response'

    return {
      text: typeof response === 'string' ? response : JSON.stringify(response),
      model: this.modelId,
      usage: {
        inputTokens: this.estimateTokens(prompt),
        outputTokens: this.estimateTokens(response),
      },
      stopReason: 'end_turn',
    }
  }

  /**
   * Generate JSON completion
   */
  async completeJSON<T>(prompt: string, options?: CompletionOptions): Promise<T> {
    this.recordCall('completeJSON', prompt, options)
    await this.maybeDelay()
    this.maybeThrow()

    const response = this.getResponse(prompt) || this.config.defaultJSON || {}
    return response as T
  }

  /**
   * Generate completion with extended thinking
   */
  async think(prompt: string, options?: ThinkingOptions): Promise<ThinkingResult> {
    this.recordCall('think', prompt, options)
    await this.maybeDelay()
    this.maybeThrow()

    const response = this.getResponse(prompt) || 'Mock thinking response'

    return {
      text: typeof response === 'string' ? response : JSON.stringify(response),
      model: this.modelId,
      thinking: 'Step 1: Analyze prompt\nStep 2: Generate response\nStep 3: Verify output',
      thinkingSummary: 'Analyzed prompt and generated appropriate response',
      usage: {
        inputTokens: this.estimateTokens(prompt),
        outputTokens: this.estimateTokens(response),
        thinkingTokens: 150,
      },
      stopReason: 'end_turn',
    }
  }

  /**
   * Generate completion with images
   */
  async completeWithImages(
    prompt: string,
    images: ImageInput[],
    options?: CompletionOptions
  ): Promise<CompletionResult> {
    this.recordCall('completeWithImages', prompt, { images, ...options })
    await this.maybeDelay()
    this.maybeThrow()

    const response =
      this.getResponse(prompt) || `Mock vision response for ${images.length} image(s)`

    return {
      text: response,
      model: this.modelId,
      usage: {
        inputTokens: this.estimateTokens(prompt) + images.length * 1000,
        outputTokens: this.estimateTokens(response),
      },
      stopReason: 'end_turn',
    }
  }

  /**
   * Generate completion with tools
   */
  async completeWithTools(
    prompt: string,
    tools: ToolDefinition[],
    options?: CompletionOptions
  ): Promise<ToolUseResult> {
    this.recordCall('completeWithTools', prompt, { tools, ...options })
    await this.maybeDelay()
    this.maybeThrow()

    // Mock tool call
    const toolCalls = [
      {
        id: 'call-123',
        name: tools[0]?.name || 'mock_tool',
        input: { param: 'value' },
      },
    ]

    return {
      text: 'Mock tool use response',
      model: this.modelId,
      toolCalls,
      usage: {
        inputTokens: this.estimateTokens(prompt),
        outputTokens: 50,
      },
      stopReason: 'tool_use',
    }
  }

  /**
   * Stream completion (mock returns async iterator)
   */
  async *stream(prompt: string, options?: CompletionOptions): AsyncIterable<string> {
    this.recordCall('stream', prompt, options)
    await this.maybeDelay()
    this.maybeThrow()

    const response = this.getResponse(prompt) || 'Mock streaming response'
    const chunks = response.split(' ')

    for (const chunk of chunks) {
      yield chunk + ' '
      await new Promise((resolve) => setTimeout(resolve, 10))
    }
  }

  /**
   * Generate completion using unified message format
   */
  async completeWithMessages(request: UnifiedRequest): Promise<UnifiedResponse> {
    const lastMessage = request.messages[request.messages.length - 1]
    const prompt = lastMessage
      ? lastMessage.content.map((c) => (c.type === 'text' ? c.text : '[non-text]')).join('\n')
      : 'No messages'

    this.recordCall('completeWithMessages', prompt, request)
    await this.maybeDelay()
    this.maybeThrow()

    const response = this.getResponse(prompt) || 'Mock unified response'

    return {
      message: {
        role: 'assistant',
        content: [{ type: 'text', text: response }],
      },
      stopReason: 'end_turn',
      usage: {
        inputTokens: this.estimateTokens(prompt),
        outputTokens: this.estimateTokens(response),
      },
      model: request.model || this.modelId,
    }
  }

  // === Helper Methods ===

  /**
   * Get response for prompt (from config or default)
   */
  private getResponse(prompt: string): any {
    // Check for exact match
    if (this.config.responses?.[prompt]) {
      return this.config.responses[prompt]
    }

    // Check for partial match
    if (this.config.responses) {
      for (const [key, value] of Object.entries(this.config.responses)) {
        if (prompt.includes(key)) {
          return value
        }
      }
    }

    return null
  }

  /**
   * Estimate tokens (simple word count * 1.3)
   */
  private estimateTokens(text: string | any): number {
    const str = typeof text === 'string' ? text : JSON.stringify(text)
    return Math.ceil(str.split(/\s+/).length * 1.3)
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
  private recordCall(method: string, prompt: string, options?: any): void {
    this.calls.push({
      method,
      prompt,
      options,
      timestamp: Date.now(),
    })
  }

  // === Test Utilities ===

  /**
   * Get all calls
   */
  getCalls(): Array<{ method: string; prompt: string; options?: any; timestamp: number }> {
    return [...this.calls]
  }

  /**
   * Get calls for method
   */
  getCallsFor(
    method: string
  ): Array<{ method: string; prompt: string; options?: any; timestamp: number }> {
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
   * Set response for prompt
   */
  setResponse(prompt: string, response: any): void {
    if (!this.config.responses) {
      this.config.responses = {}
    }
    this.config.responses[prompt] = response
  }

  /**
   * Set default JSON response
   */
  setDefaultJSON(json: any): void {
    this.config.defaultJSON = json
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
 * Create mock LLM backend
 */
export function createMockLLMBackend(config?: MockLLMConfig): MockLLMBackend {
  return new MockLLMBackend(config)
}

/**
 * Common canned responses for consolidation
 */
export const CONSOLIDATION_RESPONSES = {
  duplicate_work: {
    type: 'duplicate_work',
    direction: 'forward',
    reasoning: 'Both chunks describe the same concept with minor wording differences',
    keep: 'second',
  },
  sequential_iteration: {
    type: 'sequential_iteration',
    direction: 'forward',
    reasoning: 'Second chunk is an updated version of the first',
    keep: 'second',
  },
  contextual_convergence: {
    type: 'contextual_convergence',
    direction: 'convergent',
    reasoning: 'Chunks discuss related aspects of the same topic',
    keep: 'both',
  },
  unrelated: {
    type: 'unrelated',
    direction: 'unknown',
    reasoning: 'Chunks discuss completely different topics',
    keep: 'both',
  },
} as const
