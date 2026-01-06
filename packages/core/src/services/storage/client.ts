/**
 * Qdrant Client
 */

import { QdrantClient } from '@qdrant/js-client-rest'
import { getQdrantURL } from '../../shared/config'
import { createLogger } from '../../shared/logger'
import { createSingleton } from '../../shared/utils'

const log = createLogger('clients:qdrant')

function createQdrantClient(): QdrantClient {
  const url = getQdrantURL()
  log.trace('Creating Qdrant client', { url })
  return new QdrantClient({ url })
}

const qdrantSingleton = createSingleton(createQdrantClient, 'qdrant')

export const getQdrantClient = qdrantSingleton.get
export const resetQdrantClient = qdrantSingleton.reset
