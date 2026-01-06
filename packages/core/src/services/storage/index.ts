/**
 * Storage Service - Qdrant Vector Database
 */

import { BackendRegistry } from '../../shared/registry'
import { QdrantBackend } from './backends/qdrant'
import type { StorageBackend } from './types'
import { EMBEDDING_DIM } from '../../shared/config'

// Re-export HNSW utilities (still needed for batch operations)
export { disableHNSW, enableHNSW, isHNSWDisabled, withHNSWDisabled } from './hnsw'

// Re-export types
export type * from './types'

// ============================================
// Storage Backend Registry
// ============================================

/**
 * Global storage backend registry.
 * Initialized with Qdrant backend by default.
 */
export const storageRegistry = new BackendRegistry<StorageBackend>()

// Register default Qdrant backend
storageRegistry.register(
  new QdrantBackend({
    dimensions: EMBEDDING_DIM,
    distance: 'dot',
  })
)

/**
 * Get a storage backend by capability.
 * Currently only 'vector-storage' is supported.
 *
 * @param capability - Storage capability to look for
 * @returns Storage backend or undefined
 */
export function getStorageBackend(
  capability: 'vector-storage' = 'vector-storage'
): StorageBackend | undefined {
  return storageRegistry.getFor(capability)
}
