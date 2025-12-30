/**
 * Voyage AI Client
 */

import { VoyageAIClient } from 'voyageai'
import { VOYAGE_API_KEY } from '../../shared/config'
import { createLogger } from '../../shared/logger'

const log = createLogger('clients/voyage')

export function createVoyageClient(): VoyageAIClient {
  if (!VOYAGE_API_KEY) {
    throw new Error('VOYAGE_API_KEY environment variable not set')
  }

  log.trace('Creating Voyage AI client', { apiKeySet: !!VOYAGE_API_KEY })

  return new VoyageAIClient({
    apiKey: VOYAGE_API_KEY,
  })
}

// Singleton instance (lazy initialization)
let voyageClientInstance: VoyageAIClient | null = null

export function getVoyageClient(): VoyageAIClient {
  if (!voyageClientInstance) {
    voyageClientInstance = createVoyageClient()
  }
  return voyageClientInstance
}

// For testing: reset singleton
export function resetVoyageClient(): void {
  voyageClientInstance = null
}
