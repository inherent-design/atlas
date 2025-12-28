/**
 * Qdrant Client
 */

import { QdrantClient } from '@qdrant/js-client-rest'
import { QDRANT_URL } from '../config'
import { log } from '../logger'

export function createQdrantClient(): QdrantClient {
  log.trace('Creating Qdrant client', { url: QDRANT_URL })

  return new QdrantClient({
    url: QDRANT_URL,
  })
}

// Singleton instance (lazy initialization)
let qdrantClientInstance: QdrantClient | null = null

export function getQdrantClient(): QdrantClient {
  if (!qdrantClientInstance) {
    qdrantClientInstance = createQdrantClient()
  }
  return qdrantClientInstance
}

// For testing: reset singleton
export function resetQdrantClient(): void {
  qdrantClientInstance = null
}
