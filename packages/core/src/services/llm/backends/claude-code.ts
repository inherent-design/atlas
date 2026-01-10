/**
 * Claude Code Backend
 *
 * Uses `claude -p` CLI for completions.
 * Requires Claude Code installed, NOT an API key.
 *
 * This backend preserves the original behavior from providers.ts
 * for users who have Claude Code but no ANTHROPIC_API_KEY.
 */

import type {
  LLMBackend,
  CanComplete,
  CanCompleteJSON,
  CanUseTool,
  CompletionResult,
  CompletionOptions,
  ToolDefinition,
  ToolUseResult,
} from '../types'
import type { LLMCapability } from '../../../shared/capabilities'
import type { LatencyClass } from '../../../shared/capabilities'
import { createLogger, startTimer } from '../../../shared/logger'
import { ClaudeCodeAdapter } from '../adapters/claude-code'
import type { UnifiedRequest, UnifiedResponse } from '../message'

const log = createLogger('llm:claude-code')

/**
 * Claude Code backend using `claude -p` CLI.
 * Default Anthropic pathway for users without API key.
 */
export class ClaudeCodeBackend implements LLMBackend, CanComplete, CanCompleteJSON, CanUseTool {
  readonly name: string
  readonly modelId: string
  readonly contextWindow = 200_000
  readonly maxOutputTokens = 64_000
  readonly latency: LatencyClass = 'fast'
  readonly capabilities: ReadonlySet<LLMCapability>

  /** Message adapter for unified format conversion */
  readonly adapter = new ClaudeCodeAdapter()

  constructor(model: string = 'haiku') {
    this.modelId = model
    this.name = `claude-code:${model}`
    this.capabilities = new Set([
      'text-completion',
      'json-completion',
      'streaming',
      'vision',
      'tool-use',
    ])

    log.debug('ClaudeCodeBackend initialized', {
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
   * Check if claude CLI is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      const proc = Bun.spawn(['which', 'claude'], {
        stdout: 'pipe',
        stderr: 'pipe',
      })
      await proc.exited
      return proc.exitCode === 0
    } catch {
      return false
    }
  }

  /**
   * Generate a text completion via claude CLI.
   * Preserves exact behavior from providers.ts lines 38-109.
   */
  async complete(prompt: string, options?: CompletionOptions): Promise<CompletionResult> {
    const model = this.modelId
    const endTimer = startTimer(`claude -p --model ${model}`)

    log.trace('Claude Code completion request', {
      model,
      promptLength: prompt.length,
    })

    try {
      const args = [
        'claude',
        '-p',
        '--model',
        model,
        '--output-format',
        'json',
        '--tools',
        '""',
        '--strict-mcp-config',
        '--max-turns',
        '1',
      ]

      log.trace('Claude CLI process spawned', { args })

      const process = Bun.spawn(args, {
        stdin: 'pipe',
        stdout: 'pipe',
        stderr: 'pipe',
      })

      process.stdin.write(prompt)
      process.stdin.end()

      log.trace('Prompt written to stdin', {
        promptPreview: prompt.substring(0, 200),
      })

      const output = await new Response(process.stdout).text()
      const stderr = await new Response(process.stderr).text()

      log.trace('Claude CLI raw output', {
        outputLength: output.length,
        outputPreview: output.substring(0, 500),
        stderrLength: stderr.length,
        stderr: stderr.substring(0, 500),
      })

      const wrapper = JSON.parse(output.trim())
      log.trace('Parsed CLI wrapper', { wrapper })

      let resultText = wrapper.result || output
      log.trace('Extracted result text', {
        resultTextLength: resultText.length,
        resultTextPreview: resultText.substring(0, 500),
      })

      // Strip markdown code fences if present
      const codeBlockMatch = resultText.match(/```(?:json)?\s*\n([\s\S]*?)\n```/)
      if (codeBlockMatch) {
        resultText = codeBlockMatch[1]
        log.trace('Stripped markdown code fences', {
          strippedTextLength: resultText.length,
        })
      }

      endTimer()
      return {
        text: resultText,
        model,
      }
    } catch (error) {
      log.error('Claude Code completion failed', error as Error)
      throw new Error(`Claude Code completion failed: ${error}`)
    }
  }

  /**
   * Generate a JSON completion.
   * Expects prompt to be wrapped with wrapForJSON() from prompts.ts.
   */
  async completeJSON<T>(prompt: string, options?: CompletionOptions): Promise<T> {
    const result = await this.complete(prompt, options)

    // Try to extract JSON if there's any preamble (fallback for non-compliant responses)
    let textToParse = result.text.trim()

    // If response doesn't start with JSON, try to extract it
    if (!textToParse.startsWith('{') && !textToParse.startsWith('[')) {
      const jsonMatch = textToParse.match(/(\{[\s\S]*\}|\[[\s\S]*\])/)
      if (jsonMatch) {
        log.warn('Extracted JSON from response with preamble', {
          originalLength: textToParse.length,
          extractedLength: jsonMatch[0].length,
        })
        textToParse = jsonMatch[0]
      }
    }

    try {
      return JSON.parse(textToParse) as T
    } catch (error) {
      log.error('Failed to parse JSON response', {
        text: result.text.substring(0, 500),
        error: (error as Error).message,
      })
      throw new Error(`Failed to parse JSON response: ${error}`)
    }
  }

  /**
   * Generate a completion using unified message format
   * Uses the message adapter for format conversion
   */
  async completeWithMessages(request: UnifiedRequest): Promise<UnifiedResponse> {
    const model = request.model ?? this.modelId
    const endTimer = startTimer(`claude -p --model ${model} (unified)`)

    log.debug('Claude Code unified message request', {
      model,
      messageCount: request.messages.length,
    })

    try {
      // Convert to prompt string (extracts last user message)
      const prompt = this.adapter.toNativeRequest(request)

      const args = [
        'claude',
        '-p',
        '--model',
        model,
        '--output-format',
        'json',
        '--tools',
        '""',
        '--strict-mcp-config',
        '--max-turns',
        '1',
      ]

      log.trace('Claude CLI process spawned (unified)', { args })

      const process = Bun.spawn(args, {
        stdin: 'pipe',
        stdout: 'pipe',
        stderr: 'pipe',
      })

      process.stdin.write(prompt)
      process.stdin.end()

      const output = await new Response(process.stdout).text()
      const stderr = await new Response(process.stderr).text()

      log.trace('Claude CLI raw output (unified)', {
        outputLength: output.length,
        stderrLength: stderr.length,
      })

      // Parse raw output using adapter
      const parsedResponse = this.adapter.parseRawOutput(output)

      // Convert to unified response
      const unifiedResponse = this.adapter.fromNativeResponse(parsedResponse, model)

      log.debug('Claude Code unified message response', {
        model: unifiedResponse.model,
        stopReason: unifiedResponse.stopReason,
      })

      endTimer()
      return unifiedResponse
    } catch (error) {
      log.error('Claude Code unified message completion failed', error as Error)
      throw new Error(`Claude Code completion failed: ${error}`)
    }
  }

  /**
   * Generate completion with tool definitions
   * Uses claude CLI with --tools parameter
   */
  async completeWithTools(
    prompt: string,
    tools: ToolDefinition[],
    options?: CompletionOptions
  ): Promise<ToolUseResult> {
    const model = this.modelId
    const endTimer = startTimer(`claude -p --model ${model} (with tools)`)

    log.trace('Claude Code tool completion request', {
      model,
      promptLength: prompt.length,
      toolCount: tools.length,
    })

    try {
      // Format tools for Claude CLI
      // Claude CLI expects JSON-formatted tool definitions
      const toolsJson = JSON.stringify(
        tools.map((t) => ({
          name: t.name,
          description: t.description,
          input_schema: t.inputSchema,
        }))
      )

      const args = [
        'claude',
        '-p',
        '--model',
        model,
        '--output-format',
        'json',
        '--tools',
        toolsJson,
        '--strict-mcp-config',
        '--max-turns',
        '1',
      ]

      log.trace('Claude CLI process spawned (with tools)', { args: args.slice(0, -2) })

      const process = Bun.spawn(args, {
        stdin: 'pipe',
        stdout: 'pipe',
        stderr: 'pipe',
      })

      process.stdin.write(prompt)
      process.stdin.end()

      const output = await new Response(process.stdout).text()
      const stderr = await new Response(process.stderr).text()

      log.trace('Claude CLI raw output (with tools)', {
        outputLength: output.length,
        stderrLength: stderr.length,
      })

      // Parse response
      const wrapper = JSON.parse(output.trim())
      const result = wrapper.result || output

      // Check if response contains tool calls
      // Claude CLI returns tool calls in the response
      let toolCalls: Array<{ id: string; name: string; input: Record<string, unknown> }> = []
      let text = ''

      try {
        const parsed = typeof result === 'string' ? JSON.parse(result) : result

        // Claude Code format: { type: 'tool_use', id, name, input }
        if (Array.isArray(parsed)) {
          for (const item of parsed) {
            if (item.type === 'tool_use') {
              toolCalls.push({
                id: item.id || `tool_${Date.now()}`,
                name: item.name,
                input: item.input || {},
              })
            } else if (item.type === 'text') {
              text += item.text || ''
            }
          }
        } else if (parsed.type === 'tool_use') {
          toolCalls.push({
            id: parsed.id || `tool_${Date.now()}`,
            name: parsed.name,
            input: parsed.input || {},
          })
        } else {
          // Plain text response
          text = typeof result === 'string' ? result : JSON.stringify(result)
        }
      } catch {
        // If parsing fails, treat as plain text
        text = result
      }

      endTimer()

      return {
        text,
        toolCalls,
        model,
        stopReason: toolCalls.length > 0 ? 'tool_use' : 'end_turn',
      }
    } catch (error) {
      log.error('Claude Code tool completion failed', error as Error)
      throw new Error(`Claude Code tool completion failed: ${error}`)
    }
  }
}

/**
 * Create singleton instance for ClaudeCode backend
 */
let instance: ClaudeCodeBackend | undefined

export function getClaudeCodeBackend(model: string = 'haiku'): ClaudeCodeBackend {
  if (!instance || instance.modelId !== model) {
    instance = new ClaudeCodeBackend(model)
  }
  return instance
}
