/**
 * HNSW Index Controller
 *
 * Manages HNSW indexing state for batch operations.
 * Disabling HNSW (m=0) during bulk inserts/updates improves throughput 5-10x.
 * Re-enabling (m=16) triggers a single-pass index rebuild.
 *
 * Usage:
 *   await disableHNSW()
 *   try {
 *     // bulk operations
 *   } finally {
 *     await enableHNSW()
 *   }
 */

import { getQdrantClient } from '.'
import {
  QDRANT_COLLECTION_NAME,
  HNSW_M_DEFAULT,
  HNSW_M_DISABLED,
} from '../../shared/config'
import { createLogger } from '../../shared/logger'

const log = createLogger('hnsw')

let hnswDisabled = false

/**
 * Disable HNSW indexing for batch operations
 * Vectors are stored but remain unindexed until re-enabled
 */
export async function disableHNSW(): Promise<void> {
  if (hnswDisabled) {
    log.debug('HNSW already disabled, skipping')
    return
  }

  const qdrant = getQdrantClient()

  log.info('Disabling HNSW indexing for batch mode')

  await qdrant.updateCollection(QDRANT_COLLECTION_NAME, {
    hnsw_config: { m: HNSW_M_DISABLED },
  })

  hnswDisabled = true
  log.debug('HNSW indexing disabled', { m: HNSW_M_DISABLED })
}

/**
 * Re-enable HNSW indexing after batch operations
 * Triggers index rebuild in background
 */
export async function enableHNSW(): Promise<void> {
  if (!hnswDisabled) {
    log.debug('HNSW already enabled, skipping')
    return
  }

  const qdrant = getQdrantClient()

  log.info('Re-enabling HNSW indexing, triggering rebuild')

  await qdrant.updateCollection(QDRANT_COLLECTION_NAME, {
    hnsw_config: { m: HNSW_M_DEFAULT },
  })

  hnswDisabled = false
  log.debug('HNSW indexing enabled', { m: HNSW_M_DEFAULT })
}

/**
 * Check if HNSW is currently disabled
 */
export function isHNSWDisabled(): boolean {
  return hnswDisabled
}

/**
 * Wrap a batch operation with HNSW disable/enable
 * Ensures HNSW is re-enabled even if operation fails
 */
export async function withHNSWDisabled<T>(operation: () => Promise<T>): Promise<T> {
  await disableHNSW()
  try {
    return await operation()
  } finally {
    await enableHNSW()
  }
}
