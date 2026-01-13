/**
 * Claude Code CLI Adapter
 *
 * Converts between unified message format and Claude CLI format.
 *
 * Key limitations:
 * - Single-turn only (no multi-turn conversations)
 * - Text in/out only (structured content not exposed)
 * - Result wrapped in { result: string }
 * - No tool_use, thinking, or content block details
 */

import type { UnifiedRequest, UnifiedResponse, UnifiedMessage } from '../message.js'

/**
 * Claude Code CLI wrapper response
 */
export interface ClaudeCodeResponse {
  result: string
}

/**
 * Message adapter for Claude Code CLI
 */
export class ClaudeCodeAdapter {
  /**
   * Convert unified request to Claude Code prompt string
   * Only uses the last user message (single-turn limitation)
   */
  toNativeRequest(request: UnifiedRequest): string {
    // Find last user message
    const lastUserMessage = [...request.messages].reverse().find((m) => m.role === 'user')

    if (!lastUserMessage) {
      throw new Error('No user message found in request')
    }

    // Extract text from content blocks
    const text = this.extractText(lastUserMessage)

    return text
  }

  /**
   * Extract text from unified message
   */
  private extractText(message: UnifiedMessage): string {
    return message.content
      .filter((c) => c.type === 'text')
      .map((c) => (c.type === 'text' ? c.text : ''))
      .join('\n')
  }

  /**
   * Convert Claude Code response to unified format
   */
  fromNativeResponse(response: ClaudeCodeResponse, model: string): UnifiedResponse {
    return {
      message: {
        role: 'assistant',
        content: [
          {
            type: 'text',
            text: response.result,
          },
        ],
      },
      stopReason: 'end_turn', // CLI always completes or errors
      model,
    }
  }

  /**
   * Parse raw CLI output to extract result
   * Handles markdown code fences and JSON wrapper
   */
  parseRawOutput(output: string): ClaudeCodeResponse {
    // Try to parse as JSON first
    try {
      const parsed = JSON.parse(output.trim())
      if (parsed.result) {
        return parsed
      }
    } catch {
      // Not JSON, treat as raw text
    }

    // Strip markdown code fences if present
    const codeBlockMatch = output.match(/```(?:json)?\s*\n([\s\S]*?)\n```/)
    if (codeBlockMatch && codeBlockMatch[1]) {
      return { result: codeBlockMatch[1] }
    }

    // Return raw output
    return { result: output }
  }
}
