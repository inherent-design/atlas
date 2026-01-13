/**
 * Ollama Message Adapter
 *
 * Converts between unified message format and Ollama API format.
 *
 * Key mappings:
 * - Content is ALWAYS a string (not array)
 * - Images are in separate images[] field
 * - tool_calls is separate field (not in content)
 * - role: 'tool' for tool results (with tool_name field)
 * - Thinking is optional raw string field
 */

import type { UnifiedRequest, UnifiedResponse, UnifiedMessage, UnifiedContent } from '../message.js'

/**
 * Ollama API message format
 */
export interface OllamaMessage {
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  images?: string[] // Base64-encoded images
  tool_calls?: Array<{
    function: {
      name: string
      arguments: Record<string, unknown>
    }
  }>
  tool_name?: string // For tool responses only
  thinking?: string // For thinking models
}

/**
 * Ollama chat request format
 */
export interface OllamaChatRequest {
  model: string
  messages: OllamaMessage[]
  stream?: boolean
  format?: 'json' // Enable JSON mode
  tools?: Array<{
    type: 'function'
    function: {
      name: string
      description: string
      parameters: Record<string, unknown>
    }
  }>
  options?: {
    temperature?: number
    num_predict?: number // max tokens
    stop?: string[]
  }
}

/**
 * Ollama chat response format
 */
export interface OllamaChatResponse {
  message: OllamaMessage
  model: string
  created_at: string
  done: boolean
  done_reason?: string
  total_duration?: number
  load_duration?: number
  prompt_eval_count?: number
  eval_count?: number
}

/**
 * Message adapter for Ollama API
 */
export class OllamaAdapter {
  /**
   * Convert unified request to Ollama chat format
   */
  toNativeRequest(request: UnifiedRequest): OllamaChatRequest {
    return {
      model: request.model ?? 'llama3.2',
      messages: request.messages.map((msg) => this.toNativeMessage(msg)),
      stream: false,
      tools: request.tools?.map((tool) => ({
        type: 'function' as const,
        function: {
          name: tool.name,
          description: tool.description,
          parameters: tool.inputSchema,
        },
      })),
      options: {
        temperature: request.temperature,
        num_predict: request.maxTokens,
        stop: request.stopSequences,
      },
    }
  }

  /**
   * Convert unified message to Ollama message format
   */
  private toNativeMessage(message: UnifiedMessage): OllamaMessage {
    // Separate content by type
    const textBlocks = message.content.filter((c) => c.type === 'text')
    const imageBlocks = message.content.filter((c) => c.type === 'image')
    const toolUseBlocks = message.content.filter((c) => c.type === 'tool_use')
    const toolResultBlocks = message.content.filter((c) => c.type === 'tool_result')

    // Concatenate all text
    const content = textBlocks.map((b) => (b.type === 'text' ? b.text : '')).join('\n')

    // Extract images (base64 data only)
    const images =
      imageBlocks.length > 0
        ? imageBlocks.map((b) => (b.type === 'image' ? b.data : ''))
        : undefined

    // Convert tool_use blocks to tool_calls format
    const tool_calls =
      toolUseBlocks.length > 0
        ? toolUseBlocks.map((b) =>
            b.type === 'tool_use'
              ? {
                  function: {
                    name: b.name,
                    arguments: b.input,
                  },
                }
              : { function: { name: '', arguments: {} } }
          )
        : undefined

    // Handle tool results (role: 'tool')
    if (toolResultBlocks.length > 0 && message.role === 'tool') {
      const toolResult = toolResultBlocks[0]
      if (toolResult && toolResult.type === 'tool_result') {
        return {
          role: 'tool',
          content: toolResult.content,
          tool_name: toolResult.toolUseId,
        }
      }
    }

    return {
      role: message.role === 'tool' ? 'user' : message.role,
      content,
      images,
      tool_calls,
    }
  }

  /**
   * Convert Ollama response to unified format
   */
  fromNativeResponse(response: OllamaChatResponse): UnifiedResponse {
    const message = this.fromNativeMessage(response.message)

    // Map stop reason
    const stopReason = this.mapStopReason(response.done_reason)

    return {
      message,
      stopReason,
      usage: {
        inputTokens: response.prompt_eval_count ?? 0,
        outputTokens: response.eval_count ?? 0,
      },
      model: response.model,
    }
  }

  /**
   * Convert Ollama message to unified message
   */
  private fromNativeMessage(message: OllamaMessage): UnifiedMessage {
    const content: UnifiedContent[] = []

    // Add text content (if any)
    if (message.content) {
      content.push({
        type: 'text',
        text: message.content,
      })
    }

    // Add thinking content (collapse to text)
    if (message.thinking) {
      content.push({
        type: 'text',
        text: message.thinking,
      })
    }

    // Add images (if any)
    if (message.images) {
      for (const imageData of message.images) {
        content.push({
          type: 'image',
          data: imageData,
          mimeType: 'image/png', // Ollama doesn't specify, assume PNG
        })
      }
    }

    // Add tool calls (if any)
    if (message.tool_calls) {
      for (const toolCall of message.tool_calls) {
        content.push({
          type: 'tool_use',
          id: `${toolCall.function.name}_${Date.now()}`, // Ollama doesn't provide IDs
          name: toolCall.function.name,
          input: toolCall.function.arguments,
        })
      }
    }

    // Handle tool results
    if (message.role === 'tool' && message.tool_name) {
      content.push({
        type: 'tool_result',
        toolUseId: message.tool_name,
        content: message.content,
      })
    }

    return {
      role: message.role,
      content,
    }
  }

  /**
   * Map Ollama done_reason to unified stop reason
   */
  private mapStopReason(
    reason?: string
  ): 'end_turn' | 'max_tokens' | 'tool_use' | 'stop_sequence' | 'error' {
    if (!reason) return 'end_turn'

    switch (reason) {
      case 'stop':
        return 'end_turn'
      case 'length':
        return 'max_tokens'
      case 'tool_calls':
        return 'tool_use'
      default:
        return 'end_turn'
    }
  }
}
