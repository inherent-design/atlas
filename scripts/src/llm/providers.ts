/**
 * LLM Provider Implementations
 *
 * Core completion logic for different LLM backends:
 * - anthropic: Claude via `claude -p` CLI
 * - ollama: Local inference via Ollama API
 */

import { createLogger, startTimer } from '../logger'

const log = createLogger('llm/providers')

export type LLMProvider = 'anthropic' | 'ollama'

export interface LLMConfig {
  provider: LLMProvider
  model?: string
  temperature?: number
  maxTokens?: number
  ollamaHost?: string
}

export interface CompletionResult {
  text: string
  usage?: {
    promptTokens?: number
    completionTokens?: number
  }
}

const DEFAULT_OLLAMA_HOST = 'http://localhost:11434'
const DEFAULT_OLLAMA_MODEL = 'ministral-3:3b'
const DEFAULT_ANTHROPIC_MODEL = 'haiku'

/**
 * Complete via Anthropic API (using claude CLI)
 */
async function completeViaAnthropic(
  prompt: string,
  model: string = DEFAULT_ANTHROPIC_MODEL,
  jsonMode: boolean = false
): Promise<CompletionResult> {
  const endTimer = startTimer(`claude -p --model ${model}`)

  log.trace('Anthropic completion request', { model, promptLength: prompt.length, jsonMode })

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

    const process = Bun.spawn(args, {
      stdin: 'pipe',
      stdout: 'pipe',
      stderr: 'pipe',
    })

    log.trace('Claude CLI process spawned', { args })

    process.stdin.write(prompt)
    process.stdin.end()

    log.trace('Prompt written to stdin', { promptPreview: prompt.substring(0, 200) })

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
    return { text: resultText }
  } catch (error) {
    log.error('Anthropic completion failed', error as Error)
    throw new Error(`Anthropic completion failed: ${error}`)
  }
}

/**
 * Complete via Ollama API
 */
async function completeViaOllama(
  prompt: string,
  model: string = DEFAULT_OLLAMA_MODEL,
  ollamaHost: string = DEFAULT_OLLAMA_HOST,
  jsonMode: boolean = false,
  temperature: number = 0.1,
  maxTokens: number = 512
): Promise<CompletionResult> {
  const endTimer = startTimer(`ollama ${model}`)

  log.trace('Ollama completion request', {
    model,
    ollamaHost,
    promptLength: prompt.length,
    jsonMode,
  })

  try {
    const requestBody: Record<string, unknown> = {
      model,
      prompt,
      stream: false,
      options: {
        temperature,
        num_predict: maxTokens,
      },
    }

    if (jsonMode) {
      requestBody.format = 'json'
    }

    log.trace('Ollama request body', { requestBody })

    const response = await fetch(`${ollamaHost}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })

    log.trace('Ollama HTTP response', {
      status: response.status,
      statusText: response.statusText,
    })

    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.statusText}`)
    }

    const data = (await response.json()) as {
      response: string
      prompt_eval_count?: number
      eval_count?: number
    }

    log.trace('Ollama raw response', {
      responseLength: data.response.length,
      responsePreview: data.response.substring(0, 500),
    })

    endTimer()
    return {
      text: data.response,
      usage: {
        promptTokens: data.prompt_eval_count,
        completionTokens: data.eval_count,
      },
    }
  } catch (error) {
    log.error('Ollama completion failed', error as Error)
    throw new Error(`Ollama completion failed: ${error}`)
  }
}

/**
 * Complete a prompt using the configured provider
 */
export async function complete(prompt: string, config: LLMConfig): Promise<CompletionResult> {
  const { provider, model, ollamaHost } = config

  log.debug('LLM completion', {
    provider,
    model,
    promptLength: prompt.length,
  })

  if (provider === 'anthropic') {
    return completeViaAnthropic(prompt, model || DEFAULT_ANTHROPIC_MODEL)
  } else if (provider === 'ollama') {
    return completeViaOllama(
      prompt,
      model || DEFAULT_OLLAMA_MODEL,
      ollamaHost || DEFAULT_OLLAMA_HOST,
      false,
      config.temperature ?? 0.1,
      config.maxTokens ?? 512
    )
  }

  throw new Error(`Unknown provider: ${provider}`)
}

/**
 * Complete a prompt expecting JSON output
 */
export async function completeJSON<T>(prompt: string, config: LLMConfig): Promise<T> {
  const { provider, model, ollamaHost } = config

  log.debug('LLM JSON completion', {
    provider,
    model,
    promptLength: prompt.length,
  })

  let result: CompletionResult

  if (provider === 'anthropic') {
    result = await completeViaAnthropic(prompt, model || DEFAULT_ANTHROPIC_MODEL, true)
  } else if (provider === 'ollama') {
    result = await completeViaOllama(
      prompt,
      model || DEFAULT_OLLAMA_MODEL,
      ollamaHost || DEFAULT_OLLAMA_HOST,
      true,
      config.temperature ?? 0.1,
      config.maxTokens ?? 512
    )
  } else {
    throw new Error(`Unknown provider: ${provider}`)
  }

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

/**
 * Check if Ollama is available
 */
export async function checkOllamaAvailable(
  ollamaHost: string = DEFAULT_OLLAMA_HOST
): Promise<boolean> {
  try {
    const response = await fetch(`${ollamaHost}/api/tags`, {
      method: 'GET',
      signal: AbortSignal.timeout(2000),
    })
    return response.ok
  } catch {
    return false
  }
}

/**
 * Auto-detect best available provider
 */
export async function detectProvider(ollamaHost?: string): Promise<LLMProvider> {
  if (await checkOllamaAvailable(ollamaHost)) {
    log.info('Auto-detected Ollama as LLM provider')
    return 'ollama'
  }

  if (process.env.ANTHROPIC_API_KEY) {
    log.info('Auto-detected Anthropic as LLM provider')
    return 'anthropic'
  }

  log.warn('No LLM provider available, defaulting to ollama (may fail)')
  return 'ollama'
}
