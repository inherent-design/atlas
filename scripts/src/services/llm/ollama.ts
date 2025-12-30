/**
 * Ollama Model Management
 *
 * Dynamically pull and manage Ollama models via API
 */

import { createLogger } from '../../shared/logger'
import { OLLAMA_URL } from '../../shared/config'

const log = createLogger('ollama')

export interface PullProgress {
  status: string
  digest?: string
  total?: number
  completed?: number
}

/**
 * Pull a model from Ollama registry
 */
export async function pullModel(model: string, ollamaHost: string = OLLAMA_URL): Promise<void> {
  log.info('Pulling Ollama model', { model, ollamaHost })

  try {
    const response = await fetch(`${ollamaHost}/api/pull`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        stream: true, // Stream progress updates
      }),
    })

    if (!response.ok) {
      throw new Error(`Failed to pull model: ${response.statusText}`)
    }

    // Stream NDJSON progress updates
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.trim()) continue

        const event: PullProgress = JSON.parse(line)

        // Log progress
        if (event.total && event.completed) {
          const percent = ((event.completed / event.total) * 100).toFixed(1)
          log.debug('Pull progress', {
            model,
            status: event.status,
            percent: `${percent}%`,
            completed: event.completed,
            total: event.total,
          })
        } else {
          log.debug('Pull status', { model, status: event.status })
        }
      }
    }

    log.info('Model pulled successfully', { model })
  } catch (error) {
    log.error('Failed to pull model', error as Error)
    throw new Error(`Failed to pull ${model}: ${error}`)
  }
}

/**
 * List available models
 */
export async function listModels(ollamaHost: string = OLLAMA_URL): Promise<string[]> {
  try {
    const response = await fetch(`${ollamaHost}/api/tags`)
    if (!response.ok) {
      throw new Error(`Failed to list models: ${response.statusText}`)
    }

    const data = (await response.json()) as { models: Array<{ name: string }> }
    return data.models.map((m) => m.name)
  } catch (error) {
    log.warn('Failed to list models', error as Error)
    return []
  }
}

/**
 * Ensure model is available (pull if needed)
 */
export async function ensureModel(model: string, ollamaHost: string = OLLAMA_URL): Promise<void> {
  const models = await listModels(ollamaHost)

  if (models.includes(model)) {
    log.debug('Model already available', { model })
    return
  }

  log.info('Model not found, pulling...', { model })
  await pullModel(model, ollamaHost)
}
