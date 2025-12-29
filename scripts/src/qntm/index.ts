/**
 * QNTM Semantic Key Generation - Public API
 *
 * LLM-based semantic compression generating stable addresses for chunks.
 * Based on Step 1 research: parallel post-chunking workflow with key reuse.
 */

import { createLogger } from '../logger'

const log = createLogger('qntm')
import { cacheQNTMKeys, getCachedQNTMKeys } from './cache'
import { generateQNTMKeysWithProvider, type ProviderConfig } from './providers'

// Re-export batch functionality
export { generateQNTMKeysBatch } from './batch'

// Re-export types
export type { ProviderConfig, QNTMProvider } from './providers'

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

// Global provider config (set via CLI or auto-detect)
let providerConfig: ProviderConfig = {
  provider: 'ollama',
  model: 'qwen2.5:7b',
}

/**
 * Set QNTM provider configuration
 */
export function setQNTMProvider(config: ProviderConfig): void {
  providerConfig = config
  log.info('QNTM provider configured', config)
}

/**
 * Get current QNTM provider configuration
 */
export function getQNTMProvider(): ProviderConfig {
  return providerConfig
}

/**
 * Generate QNTM semantic keys for a chunk
 *
 * @param input - Chunk text, existing keys for reuse, optional context
 * @returns Array of QNTM keys (1-3 semantic addresses)
 */
export async function generateQNTMKeys(input: QNTMGenerationInput): Promise<QNTMGenerationResult> {
  const result = await generateQNTMKeysWithProvider(input, providerConfig)

  // Cache generated keys for future reuse
  cacheQNTMKeys(result.keys)

  log.info('QNTM keys generated', {
    provider: providerConfig.provider,
    model: providerConfig.model,
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
 * Fetch all existing QNTM keys (from cache + Qdrant collections)
 *
 * @returns Array of all QNTM keys (deduplicated)
 */
export async function fetchExistingQNTMKeys(): Promise<string[]> {
  // Get cached keys first (faster)
  const cachedKeys = getCachedQNTMKeys()

  // Also fetch from Qdrant collections as fallback/validation
  const { getQdrantClient } = await import('../clients')
  const qdrant = getQdrantClient()

  try {
    const collections = await qdrant.getCollections()
    const qdrantKeys = collections.collections
      .map((c) => c.name)
      .filter((name) => !name.startsWith('atlas_')) // Skip non-QNTM collections

    // Cache any Qdrant keys that aren't already cached (hydration)
    const newKeys = qdrantKeys.filter((k) => !cachedKeys.includes(k))
    if (newKeys.length > 0) {
      cacheQNTMKeys(newKeys)
      log.debug('Hydrated cache from Qdrant collections', { newKeysCached: newKeys.length })
    }

    // Merge and deduplicate
    const allKeys = Array.from(new Set([...cachedKeys, ...qdrantKeys]))

    log.debug('Fetched existing QNTM keys', {
      cached: cachedKeys.length,
      qdrant: qdrantKeys.length,
      total: allKeys.length,
    })

    return allKeys
  } catch (error) {
    log.warn('Failed to fetch Qdrant QNTM keys, using cache only', error as Error)
    return cachedKeys
  }
}
