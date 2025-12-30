/**
 * QNTM Semantic Key Generation - Public API
 *
 * LLM-based semantic compression generating stable addresses for chunks.
 * Uses llm/ module for completions, provides QNTM-specific prompt building.
 */

import { createLogger } from '../logger'
import { getLLMConfig, setLLMConfig, type LLMConfig } from '../llm'
import { generateQNTMKeysWithProvider } from './providers'

const log = createLogger('qntm')

// Re-export batch functionality
export { generateQNTMKeysBatch } from './batch'

// Re-export types (using LLM types with QNTM aliases for compatibility)
export type { LLMConfig as ProviderConfig, LLMProvider as QNTMProvider } from '../llm'

export interface QNTMGenerationInput {
  chunk: string
  existingKeys: string[]
  context?: {
    fileName?: string
    chunkIndex?: number
    totalChunks?: number
  }
}

export interface QNTMGenerationResult {
  keys: string[]
  reasoning?: string
}

/**
 * Set QNTM provider configuration
 * (Delegates to llm/ module)
 */
export function setQNTMProvider(config: Partial<LLMConfig>): void {
  setLLMConfig(config)
  log.info('QNTM provider configured', config)
}

/**
 * Get current QNTM provider configuration
 */
export function getQNTMProvider(): LLMConfig {
  return getLLMConfig()
}

/**
 * Generate QNTM semantic keys for a chunk
 *
 * @param input - Chunk text, existing keys for reuse, optional context
 * @returns Array of QNTM keys (1-3 semantic addresses)
 */
export async function generateQNTMKeys(input: QNTMGenerationInput): Promise<QNTMGenerationResult> {
  const config = getLLMConfig()
  const result = await generateQNTMKeysWithProvider(input, config)

  log.info('QNTM keys generated', {
    provider: config.provider,
    model: config.model,
    keyCount: result.keys.length,
    keys: result.keys,
  })

  return result
}

/**
 * Sanitize QNTM key for use as Qdrant collection name
 *
 * Converts: @memory ~ consolidation → memory_consolidation
 */
export function sanitizeQNTMKey(key: string): string {
  return key
    .replace(/@/g, '') // Remove @
    .replace(/~/g, '_') // Replace ~ with _
    .replace(/\s+/g, '_') // Replace spaces with _
    .replace(/[^a-zA-Z0-9_-]/g, '') // Remove invalid chars
    .toLowerCase()
}

/**
 * Fetch all existing QNTM keys from unified atlas collection
 *
 * Scrolls through collection to collect unique qntm_keys from payloads.
 * Used for key reuse during QNTM generation (avoid near-duplicates).
 *
 * @returns Array of unique QNTM keys
 */
export async function fetchExistingQNTMKeys(): Promise<string[]> {
  const { getQdrantClient } = await import('../clients')
  const { QDRANT_COLLECTION_NAME } = await import('../config')
  const qdrant = getQdrantClient()

  try {
    // Check if collection exists
    try {
      await qdrant.getCollection(QDRANT_COLLECTION_NAME)
    } catch {
      log.debug('Collection does not exist yet, no existing keys')
      return []
    }

    // Scroll through collection to collect unique keys
    const uniqueKeys = new Set<string>()
    let offset: string | number | null | undefined = undefined
    const SCROLL_LIMIT = 100

    do {
      const result = await qdrant.scroll(QDRANT_COLLECTION_NAME, {
        limit: SCROLL_LIMIT,
        offset,
        with_payload: { include: ['qntm_keys'] },
        with_vector: false,
      })

      for (const point of result.points) {
        const keys = (point.payload as any)?.qntm_keys as string[] | undefined
        if (keys) {
          for (const key of keys) {
            uniqueKeys.add(key)
          }
        }
      }

      offset = result.next_page_offset
    } while (offset !== null && offset !== undefined)

    const keysArray = Array.from(uniqueKeys)

    log.debug('Fetched existing QNTM keys from unified collection', {
      total: keysArray.length,
    })

    return keysArray
  } catch (error) {
    log.error('Failed to fetch QNTM keys from Qdrant', error as Error)
    return []
  }
}
