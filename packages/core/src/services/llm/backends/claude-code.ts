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
  LLMCapability,
  CanComplete,
  CanCompleteJSON,
  CompletionResult,
  CompletionOptions,
} from '../types'
import type { LatencyClass } from '../../../shared/capabilities'
import { createLogger, startTimer } from '../../../shared/logger'

const log = createLogger('llm/claude-code')

/**
 * Claude Code backend using `claude -p` CLI.
 * Default Anthropic pathway for users without API key.
 */
export class ClaudeCodeBackend implements LLMBackend, CanComplete, CanCompleteJSON {
  readonly name: string
  readonly modelId: string
  readonly contextWindow = 200_000
  readonly maxOutputTokens = 64_000
  readonly latency: LatencyClass = 'fast'
  readonly capabilities: ReadonlySet<LLMCapability>

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
    const model = options?.model ?? this.modelId
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
   * Generate a JSON completion
   */
  async completeJSON<T>(prompt: string, options?: CompletionOptions): Promise<T> {
    const result = await this.complete(prompt, options)

    try {
      return JSON.parse(result.text) as T
    } catch (error) {
      log.error('Failed to parse JSON response', {
        text: result.text.substring(0, 500),
        error: (error as Error).message,
      })
      throw new Error(`Failed to parse JSON response: ${error}`)
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
