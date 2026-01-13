/**
 * Anthropic Message Adapter
 *
 * Converts between unified message format and Anthropic SDK types.
 *
 * Key mappings:
 * - Content is ALWAYS array in Anthropic responses
 * - Thinking blocks collapse to text
 * - tool_use and tool_result map directly
 * - Images use source.data format
 */

import type Anthropic from '@anthropic-ai/sdk'
import type {
  UnifiedRequest,
  UnifiedResponse,
  UnifiedMessage,
  UnifiedContent,
  ToolDefinition,
} from '../message.js'

/**
 * Message adapter for Anthropic SDK
 */
export class AnthropicAdapter {
  /**
   * Convert unified request to Anthropic SDK format
   */
  toNativeRequest(request: UnifiedRequest): Anthropic.Messages.MessageCreateParamsNonStreaming {
    // Convert messages
    const messages = request.messages.map((msg) => this.toNativeMessage(msg))

    // Convert tools
    const tools = request.tools?.map((tool) => this.toNativeTool(tool))

    return {
      model: request.model ?? 'claude-sonnet-4-5-20250929',
      max_tokens: request.maxTokens ?? 4096,
      temperature: request.temperature,
      stop_sequences: request.stopSequences,
      messages,
      tools,
    }
  }

  /**
   * Convert unified message to Anthropic MessageParam
   */
  private toNativeMessage(message: UnifiedMessage): Anthropic.Messages.MessageParam {
    // System messages must be handled separately in Anthropic
    // (they go in a separate 'system' parameter)
    if (message.role === 'system') {
      throw new Error(
        'System messages should be extracted and passed via system parameter, not in messages array'
      )
    }

    // Tool role maps to 'user' in Anthropic
    const role = message.role === 'tool' ? 'user' : message.role

    // Convert content blocks
    const content = message.content.map((block) => this.toNativeContent(block))

    return {
      role: role as 'user' | 'assistant',
      content,
    }
  }

  /**
   * Convert unified content to Anthropic ContentBlockParam
   */
  private toNativeContent(content: UnifiedContent): Anthropic.Messages.ContentBlockParam {
    switch (content.type) {
      case 'text':
        return {
          type: 'text',
          text: content.text,
        }

      case 'image':
        return {
          type: 'image',
          source: {
            type: 'base64',
            media_type: content.mimeType as 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp',
            data: content.data,
          },
        }

      case 'tool_use':
        return {
          type: 'tool_use',
          id: content.id,
          name: content.name,
          input: content.input,
        }

      case 'tool_result':
        return {
          type: 'tool_result',
          tool_use_id: content.toolUseId,
          content: content.content,
          is_error: content.isError,
        }
    }
  }

  /**
   * Convert unified tool to Anthropic ToolParam
   */
  private toNativeTool(tool: ToolDefinition): Anthropic.Messages.Tool {
    return {
      name: tool.name,
      description: tool.description,
      input_schema: {
        type: 'object',
        ...tool.inputSchema,
      } as Anthropic.Messages.Tool.InputSchema,
    }
  }

  /**
   * Convert Anthropic response to unified format
   */
  fromNativeResponse(response: Anthropic.Messages.Message): UnifiedResponse {
    // Convert content blocks (collapse thinking to text)
    const content = response.content.map((block) => this.fromNativeContent(block))

    // Map stop reason
    const stopReason = this.mapStopReason(response.stop_reason)

    return {
      message: {
        role: 'assistant',
        content,
      },
      stopReason,
      usage: {
        inputTokens: response.usage.input_tokens,
        outputTokens: response.usage.output_tokens,
      },
      model: response.model,
    }
  }

  /**
   * Convert Anthropic ContentBlock to unified content
   * Collapses thinking blocks to text per design decision
   */
  private fromNativeContent(block: Anthropic.Messages.ContentBlock): UnifiedContent {
    switch (block.type) {
      case 'text':
        return {
          type: 'text',
          text: block.text,
        }

      case 'thinking':
        // Collapse thinking to text
        return {
          type: 'text',
          text: block.thinking,
        }

      case 'tool_use':
        return {
          type: 'tool_use',
          id: block.id,
          name: block.name,
          input: block.input as Record<string, unknown>,
        }

      default:
        // Fallback for unknown block types
        return {
          type: 'text',
          text: JSON.stringify(block),
        }
    }
  }

  /**
   * Map Anthropic stop reason to unified format
   */
  private mapStopReason(
    reason:
      | 'end_turn'
      | 'max_tokens'
      | 'stop_sequence'
      | 'tool_use'
      | 'pause_turn'
      | 'refusal'
      | null
  ): 'end_turn' | 'max_tokens' | 'tool_use' | 'stop_sequence' | 'error' {
    if (!reason) return 'end_turn'

    // Map Anthropic-specific reasons to unified format
    if (reason === 'pause_turn' || reason === 'refusal') return 'end_turn'

    return reason
  }

  /**
   * Extract system message from unified messages array
   * Anthropic requires system prompts in separate parameter
   *
   * @returns Tuple of [systemPrompt, nonSystemMessages]
   */
  static extractSystemMessage(messages: UnifiedMessage[]): [string | undefined, UnifiedMessage[]] {
    const systemMessages = messages.filter((m) => m.role === 'system')
    const nonSystemMessages = messages.filter((m) => m.role !== 'system')

    // Concatenate all system messages
    const systemPrompt = systemMessages.length
      ? systemMessages
          .map((m) => m.content.map((c) => (c.type === 'text' ? c.text : '')).join(''))
          .join('\n\n')
      : undefined

    return [systemPrompt, nonSystemMessages]
  }
}
