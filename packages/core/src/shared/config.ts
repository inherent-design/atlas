/**
 * Atlas Configuration
 * Based on .atlas research (Steps 1-4 + Sleep Patterns)
 *
 * Note: This file contains legacy constants. New code should use
 * config.loader.ts and config.schema.ts for configuration.
 */

import { createLogger } from './logger'
import { getConfig } from './config.loader'

const log = createLogger('config')

// Get config (will use defaults if not loaded)
const atlasConfig = getConfig()

// Collection config
export const QDRANT_COLLECTION_NAME = atlasConfig.qdrant?.collection || 'atlas'

// Voyage AI config (Step 3)
export const VOYAGE_MODEL = 'voyage-3-large' as const
export const EMBEDDING_DIM = 1024

// Chunking config (Step 2)
export const CHUNK_SIZE = 768 // tokens (conservative for quality)
export const CHUNK_OVERLAP = 100 // 13% overlap
export const CHUNK_MIN_CHARS = 10 // Skip chunks smaller than this
export const CHUNK_SEPARATORS = ['\n\n', '\n', '. ', ' ', ''] // Hierarchical semantic boundaries

// Search defaults
export const DEFAULT_SEARCH_LIMIT = 5
export const DEFAULT_HNSW_EF = 50 // From Step 3 production config
export const DEFAULT_QUANTIZATION_RESCORE = true
export const DEFAULT_QUANTIZATION_OVERSAMPLING = 3.0

// Qdrant collection config (Step 3 production)
// Named vectors: single collection with multiple vector types
export const QDRANT_COLLECTION_CONFIG = {
  vectors: {
    text: {
      size: EMBEDDING_DIM,
      distance: 'Dot' as const, // Voyage normalizes vectors, dot = cosine
      on_disk: true, // Full vectors on disk
      hnsw_config: {
        m: 16, // Balanced accuracy/memory
        ef_construct: 100,
        on_disk: false, // HNSW graph in RAM for speed
      },
      quantization_config: {
        scalar: {
          type: 'int8' as const, // 4x compression, 0.99 accuracy
          quantile: 0.99,
          always_ram: true,
        },
      },
    },
    code: {
      size: EMBEDDING_DIM,
      distance: 'Dot' as const,
      on_disk: true,
      hnsw_config: {
        m: 20, // Higher connectivity for code structure
        ef_construct: 120, // More build effort for better code retrieval
        on_disk: false,
      },
      quantization_config: {
        scalar: {
          type: 'int8' as const,
          quantile: 0.99,
          always_ram: true,
        },
      },
    },
    // Future: media vector (voyage-multimodal-3.5)
  },
}

/**
 * Build Qdrant collection config with dynamic dimensions.
 * Use this instead of QDRANT_COLLECTION_CONFIG for dimension-aware collection creation.
 *
 * @param dimensions - Vector dimensions from embedding backend
 * @returns Collection config compatible with Qdrant createCollection()
 */
export function buildCollectionConfig(dimensions: number) {
  return {
    vectors: {
      text: {
        size: dimensions,
        distance: 'Dot' as const,
        on_disk: true,
        hnsw_config: {
          m: 16,
          ef_construct: 100,
          on_disk: false,
        },
        quantization_config: {
          scalar: {
            type: 'int8' as const,
            quantile: 0.99,
            always_ram: true,
          },
        },
      },
      code: {
        size: dimensions,
        distance: 'Dot' as const,
        on_disk: true,
        hnsw_config: {
          m: 20,
          ef_construct: 120,
          on_disk: false,
        },
        quantization_config: {
          scalar: {
            type: 'int8' as const,
            quantile: 0.99,
            always_ram: true,
          },
        },
      },
    },
  }
}

// File patterns
export const TEXT_FILE_EXTENSIONS = [
  '.md',
  '.txt',
  '.ts',
  '.tsx',
  '.js',
  '.jsx',
  '.json',
  '.yaml',
  '.yml',
  '.toml',
  '.qntm',
  '.rs',
  '.go',
  '.py',
  '.sh',
  '.css',
  '.html',
]

export const IGNORE_PATTERNS = [
  'node_modules',
  '.git',
  'dist',
  'build',
  '.next',
  'coverage',
  '.atlas',
  'prev',
  'target',
  '.bun',
]

// Ollama config
export const OLLAMA_URL = process.env.OLLAMA_URL || 'http://localhost:11434'

// Environment - use getters to allow runtime config updates
export function getQdrantURL(): string {
  const config = getConfig()
  return config.qdrant?.url || process.env.QDRANT_URL || 'http://localhost:6333'
}

// Legacy export for backwards compatibility (reads dynamically)
export const QDRANT_URL = getQdrantURL()

export const VOYAGE_API_KEY = process.env.VOYAGE_API_KEY

// Consolidation config
export const CONSOLIDATION_BASE_THRESHOLD = 500 // chunks, not files
export const CONSOLIDATION_SCALE_FACTOR = 0.05
export const CONSOLIDATION_SIMILARITY_THRESHOLD = 0.80
export const CONSOLIDATION_POLL_INTERVAL_MS = 30000 // 30 seconds

// Deletion config
export const DELETION_GRACE_PERIOD_DAYS = 14
export const STABILITY_SCORE_THRESHOLD = 0.95

// HNSW batch mode config
export const HNSW_M_DEFAULT = 16
export const HNSW_M_DISABLED = 0
export const BATCH_HNSW_THRESHOLD = 50 // Disable HNSW if batch size > this
