/**
 * Unified Message Type System
 *
 * Provides a single message format that works across all LLM providers:
 * - Anthropic (via @anthropic-ai/sdk)
 * - Ollama (via HTTP API)
 * - Claude Code (via CLI)
 *
 * Design principles:
 * - Separate request/response types (response includes usage, stopReason)
 * - Discriminated union content blocks (type-safe)
 * - Provider adapters handle conversion at backend boundary
 * - Full conversation fidelity (includes tool_use, tool_result)
 * - Thinking blocks collapse to text
 */

// ============================================
// Core Message Types
// ============================================

/**
 * Message role
 * Superset of all provider roles
 */
export type MessageRole = 'user' | 'assistant' | 'system' | 'tool'

/**
 * Content block types (discriminated union)
 * Normalized across all providers
 */
export type UnifiedContent =
  | { type: 'text'; text: string }
  | { type: 'image'; data: string; mimeType: string }
  | { type: 'tool_use'; id: string; name: string; input: Record<string, unknown> }
  | { type: 'tool_result'; toolUseId: string; content: string; isError?: boolean }

/**
 * A single message in a conversation
 */
export interface UnifiedMessage {
  role: MessageRole
  content: UnifiedContent[]
}

// ============================================
// Request/Response Types
// ============================================

/**
 * Request to an LLM (what you send)
 */
export interface UnifiedRequest {
  /** Conversation messages */
  messages: UnifiedMessage[]
  /** Model identifier (optional - backend may have default) */
  model?: string
  /** Maximum tokens to generate */
  maxTokens?: number
  /** Sampling temperature (0.0-1.0) */
  temperature?: number
  /** Stop sequences */
  stopSequences?: string[]
  /** Tool definitions (for tool-using models) */
  tools?: ToolDefinition[]
}

/**
 * Response from an LLM (what you get back)
 */
export interface UnifiedResponse {
  /** Generated message */
  message: UnifiedMessage
  /** Why generation stopped */
  stopReason: 'end_turn' | 'max_tokens' | 'tool_use' | 'stop_sequence' | 'error'
  /** Token usage (if available) */
  usage?: {
    inputTokens: number
    outputTokens: number
  }
  /** Model that generated this response */
  model: string
}

// ============================================
// Tool Definitions
// ============================================

/**
 * Tool/function definition for tool-using models
 */
export interface ToolDefinition {
  /** Tool name */
  name: string
  /** Human-readable description */
  description: string
  /** JSON schema for input parameters */
  inputSchema: Record<string, unknown>
}

// ============================================
// Convenience Helpers
// ============================================

/**
 * Create a text message
 * @param role - Message role
 * @param text - Text content
 * @returns Unified message with text content
 *
 * @example
 * ```ts
 * const userMsg = textMessage('user', 'What is 2+2?')
 * const assistantMsg = textMessage('assistant', 'The answer is 4.')
 * ```
 */
export function textMessage(role: MessageRole, text: string): UnifiedMessage {
  return {
    role,
    content: [{ type: 'text', text }],
  }
}

/**
 * Create a message with image content
 * @param role - Message role (typically 'user')
 * @param text - Text prompt
 * @param images - Array of base64-encoded images with MIME types
 * @returns Unified message with text and image content
 *
 * @example
 * ```ts
 * const msg = imageMessage('user', 'Describe this image', [
 *   { data: 'base64...', mimeType: 'image/png' }
 * ])
 * ```
 */
export function imageMessage(
  role: MessageRole,
  text: string,
  images: Array<{ data: string; mimeType: string }>
): UnifiedMessage {
  return {
    role,
    content: [{ type: 'text', text }, ...images.map((img) => ({ type: 'image' as const, ...img }))],
  }
}

/**
 * Create a tool use message (from assistant)
 * @param toolCalls - Array of tool calls
 * @returns Unified message with tool_use content
 *
 * @example
 * ```ts
 * const msg = toolUseMessage([
 *   { id: 'call_1', name: 'get_weather', input: { city: 'Tokyo' } }
 * ])
 * ```
 */
export function toolUseMessage(
  toolCalls: Array<{ id: string; name: string; input: Record<string, unknown> }>
): UnifiedMessage {
  return {
    role: 'assistant',
    content: toolCalls.map((call) => ({
      type: 'tool_use' as const,
      id: call.id,
      name: call.name,
      input: call.input,
    })),
  }
}

/**
 * Create a tool result message (from tool execution)
 * @param toolUseId - ID of the tool call this is responding to
 * @param content - Result content (as string)
 * @param isError - Whether this is an error result
 * @returns Unified message with tool_result content
 *
 * @example
 * ```ts
 * const msg = toolResultMessage('call_1', '{"temp": 11, "unit": "C"}')
 * const errorMsg = toolResultMessage('call_2', 'City not found', true)
 * ```
 */
export function toolResultMessage(
  toolUseId: string,
  content: string,
  isError?: boolean
): UnifiedMessage {
  return {
    role: 'tool',
    content: [
      {
        type: 'tool_result',
        toolUseId,
        content,
        isError,
      },
    ],
  }
}

/**
 * Create a system message
 * @param text - System prompt text
 * @returns Unified message with system role
 *
 * @example
 * ```ts
 * const msg = systemMessage('You are a helpful assistant.')
 * ```
 */
export function systemMessage(text: string): UnifiedMessage {
  return textMessage('system', text)
}

// ============================================
// Type Guards
// ============================================

/**
 * Check if content is a text block
 */
export function isTextContent(content: UnifiedContent): content is { type: 'text'; text: string } {
  return content.type === 'text'
}

/**
 * Check if content is an image block
 */
export function isImageContent(
  content: UnifiedContent
): content is { type: 'image'; data: string; mimeType: string } {
  return content.type === 'image'
}

/**
 * Check if content is a tool_use block
 */
export function isToolUseContent(
  content: UnifiedContent
): content is { type: 'tool_use'; id: string; name: string; input: Record<string, unknown> } {
  return content.type === 'tool_use'
}

/**
 * Check if content is a tool_result block
 */
export function isToolResultContent(
  content: UnifiedContent
): content is { type: 'tool_result'; toolUseId: string; content: string; isError?: boolean } {
  return content.type === 'tool_result'
}

// ============================================
// Utility Functions
// ============================================

/**
 * Extract all text from a message's content blocks
 * @param message - Message to extract text from
 * @returns Concatenated text from all text blocks
 *
 * @example
 * ```ts
 * const msg = textMessage('user', 'Hello world')
 * extractText(msg) // => 'Hello world'
 * ```
 */
export function extractText(message: UnifiedMessage): string {
  return message.content.filter(isTextContent).map((block) => block.text).join('')
}

/**
 * Check if a message contains any tool use
 * @param message - Message to check
 * @returns true if message contains tool_use blocks
 */
export function hasToolUse(message: UnifiedMessage): boolean {
  return message.content.some(isToolUseContent)
}

/**
 * Extract all tool calls from a message
 * @param message - Message to extract from
 * @returns Array of tool calls
 */
export function extractToolCalls(message: UnifiedMessage): Array<{
  id: string
  name: string
  input: Record<string, unknown>
}> {
  return message.content.filter(isToolUseContent).map((block) => ({
    id: block.id,
    name: block.name,
    input: block.input,
  }))
}
