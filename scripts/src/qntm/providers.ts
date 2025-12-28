/**
 * QNTM Generation Providers
 *
 * Abstraction for QNTM generation via different LLM providers:
 * - claude: Anthropic Claude API (haiku, sonnet, opus)
 * - ollama: Local Ollama inference
 */

import type { QNTMGenerationInput, QNTMGenerationResult } from '.'
import { log, startTimer } from '../logger'

export type QNTMProvider = 'anthropic' | 'ollama'

export interface ProviderConfig {
  provider: QNTMProvider
  model?: string // e.g., "haiku", "sonnet" for claude; "qwen2.5:7b" for ollama
  ollamaHost?: string // Default: http://localhost:11434
}

const DEFAULT_OLLAMA_HOST = 'http://localhost:11434'

/**
 * Build QNTM generation prompt
 */
function buildQNTMPrompt(input: QNTMGenerationInput): string {
  const { chunk, existingKeys, context } = input

  return `# QNTM Semantic Key Generation

Generate stable semantic addresses (QNTM keys) for this chunk. Each key represents a semantic neighborhood this chunk belongs to.

## Existing Keys in System
${existingKeys.length > 0 ? existingKeys.map((k) => `- ${k}`).join('\n') : '(none yet)'}

${context?.fileName ? `## Context\nFile: ${context.fileName} (chunk ${context.chunkIndex}/${context.totalChunks})\n` : ''}
## Chunk
\`\`\`
${chunk}
\`\`\`

## Instructions
1. Identify 1-3 core semantic concepts in this chunk
2. For each concept, check if existing keys already capture it - REUSE if possible
3. Generate new keys ONLY if concept not covered by existing keys
4. Format: @concept ~ relationship ~ concept (simple, stable across rephrasing)
5. Return ONLY valid JSON (no markdown, no explanation outside JSON)

## Output (JSON only)
{
  "keys": ["@concept1 ~ relation", "@concept2 ~ relation ~ concept3"],
  "reasoning": "Brief explanation"
}`
}

/**
 * Generate QNTM keys via Anthropic API (using claude CLI)
 */
async function generateViaAnthropicAPI(
  prompt: string,
  model: string = 'haiku'
): Promise<QNTMGenerationResult> {
  const endTimer = startTimer(`claude -p --model ${model}`)

  log.trace('Anthropic API request', { model, promptLength: prompt.length })

  try {
    // Use stdin piping to avoid shell escaping issues
    const process = Bun.spawn(
      [
        'claude',
        '-p',
        '--model',
        model,
        '--output-format',
        'json',
        '--tools',
        '',
        '--max-turns',
        '1',
      ],
      {
        stdin: 'pipe',
        stdout: 'pipe',
        stderr: 'pipe',
      }
    )

    log.trace('Claude CLI process spawned', {
      args: [
        'claude',
        '-p',
        '--model',
        model,
        '--output-format',
        'json',
        '--tools',
        '',
        '--max-turns',
        '1',
      ],
    })

    // Write prompt to stdin
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

    // Extract result from Claude CLI wrapper
    let resultText = wrapper.result || output
    log.trace('Extracted result text', {
      resultTextLength: resultText.length,
      resultTextPreview: resultText.substring(0, 500),
    })

    // Strip markdown code fences if present (Claude CLI sometimes wraps in ```json...```)
    const codeBlockMatch = resultText.match(/```(?:json)?\s*\n([\s\S]*?)\n```/)
    if (codeBlockMatch) {
      resultText = codeBlockMatch[1]
      log.trace('Stripped markdown code fences', {
        strippedTextLength: resultText.length,
        strippedTextPreview: resultText.substring(0, 500),
      })
    }

    // Parse the actual QNTM response
    const result = JSON.parse(resultText)
    log.trace('Parsed QNTM result', { result })

    endTimer()
    return result
  } catch (error) {
    log.error('Anthorpic QNTM generation failed', error as Error)
    throw new Error(`Anthorpic QNTM generation failed: ${error}`)
  }
}

/**
 * Generate QNTM keys via Ollama API
 */
async function generateViaOllama(
  prompt: string,
  model: string = 'qwen2.5:7b',
  ollamaHost: string = DEFAULT_OLLAMA_HOST
): Promise<QNTMGenerationResult> {
  // Ensure model is available (pull if needed)
  const { ensureModel } = await import('../ollama')
  await ensureModel(model, ollamaHost)

  const endTimer = startTimer(`ollama ${model}`)

  log.trace('Ollama API request', { model, ollamaHost, promptLength: prompt.length })

  try {
    const requestBody = {
      model,
      prompt,
      stream: false,
      format: 'json',
      options: {
        temperature: 0.1, // Low temperature for consistency
        num_predict: 256, // Limit output tokens
      },
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
      headers: Object.fromEntries(response.headers.entries()),
    })

    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.statusText}`)
    }

    const data = (await response.json()) as { response: string }
    log.trace('Ollama raw response', {
      dataKeys: Object.keys(data),
      responseLength: data.response.length,
      responsePreview: data.response.substring(0, 500),
    })

    const result = JSON.parse(data.response) as QNTMGenerationResult
    log.trace('Parsed QNTM result', { result })

    endTimer()
    return result
  } catch (error) {
    log.error('Ollama QNTM generation failed', error as Error)
    throw new Error(`Ollama QNTM generation failed: ${error}`)
  }
}

/**
 * Generate QNTM keys using specified provider
 */
export async function generateQNTMKeysWithProvider(
  input: QNTMGenerationInput,
  config: ProviderConfig
): Promise<QNTMGenerationResult> {
  const prompt = buildQNTMPrompt(input)

  log.debug('Generating QNTM keys', {
    provider: config.provider,
    model: config.model,
    chunkLength: input.chunk.length,
    existingKeyCount: input.existingKeys.length,
  })

  if (config.provider === 'anthropic') {
    return generateViaAnthropicAPI(prompt, config.model)
  } else if (config.provider === 'ollama') {
    return generateViaOllama(prompt, config.model, config.ollamaHost)
  }

  throw new Error(`Unknown provider: ${config.provider}`)
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
      signal: AbortSignal.timeout(2000), // 2s timeout
    })
    return response.ok
  } catch {
    return false
  }
}

/**
 * Auto-detect best available provider
 */
export async function detectProvider(): Promise<QNTMProvider> {
  // Try Ollama first
  if (await checkOllamaAvailable()) {
    log.info('Auto-detected Ollama as QNTM provider')
    return 'ollama'
  }

  // Fallback to Anthropic if ANTHROPIC_API_KEY exists
  if (process.env.ANTHROPIC_API_KEY) {
    log.info('Auto-detected Anthropic as QNTM provider')
    return 'anthropic'
  }

  log.warn('No QNTM provider available, defaulting to ollama (may fail)')
  return 'ollama'
}
