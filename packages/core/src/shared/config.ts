/**
 * Atlas Configuration
 * Based on .atlas research (Steps 1-4 + Sleep Patterns)
 *
 * Note: This file contains legacy constants. New code should use
 * config.loader.ts and config.schema.ts for configuration.
 */

import {
  CODE_EXTENSIONS,
  getAllEmbeddableExtensions,
  MEDIA_EXTENSIONS,
  TEXT_EXTENSIONS,
} from '../services/embedding/types'
import { createLogger } from './logger'

const log = createLogger('config')

// Collection name - hardcoded for now, will be dynamic for colpali support
export const QDRANT_COLLECTION_NAME = 'atlas'

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
    media: {
      size: EMBEDDING_DIM,
      distance: 'Dot' as const,
      on_disk: true,
      hnsw_config: {
        m: 16, // Balanced for multimodal content
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
      media: {
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
    },
  }
}

// ============================================
// Extension Re-exports (for backwards compatibility)
// ============================================

/**
 * Re-export extension constants from embedding/types.ts
 * Use these for consistent file type detection across the codebase.
 */
export { CODE_EXTENSIONS, getAllEmbeddableExtensions, MEDIA_EXTENSIONS, TEXT_EXTENSIONS }

/**
 * Legacy alias for backwards compatibility.
 * @deprecated Use TEXT_EXTENSIONS and CODE_EXTENSIONS directly instead
 */
export const TEXT_FILE_EXTENSIONS = [...TEXT_EXTENSIONS, ...CODE_EXTENSIONS] as const

/**
 * Directory and file patterns to ignore during recursive file operations.
 * Used by expandPaths() in utils.ts for file discovery and file watcher.
 *
 * Based on architectural decisions (2026-01-08):
 * - Ignore all build artifacts (generated code, not source of truth)
 * - Ignore all dependencies (third-party code, massive token cost)
 * - Ignore secrets (.env files without .example/.template suffix)
 * - Ignore editor/IDE metadata and OS files (no semantic value)
 *
 * Rationale: Focus on source code and documentation that represents
 * actual project knowledge. Build output and dependencies are noise.
 */
export const IGNORE_PATTERNS = [
  // === Dependencies (massive, third-party code) ===
  'node_modules',
  'jspm_packages',
  'bower_components',
  'vendor',
  '.pnp',
  '.pnp.js',

  // === Build Artifacts (generated, not source) ===
  'dist',
  'build',
  'out',
  '.next',
  '.nuxt',
  '.cache',
  '.parcel-cache',
  '.svelte-kit',
  '.docusaurus',
  'coverage',
  '.nyc_output',
  'target',
  'prev',
  '.bun',

  // === Version Control ===
  '.git',
  '.svn',
  '.hg',

  // === Editor/IDE Files ===
  '.vscode',
  '.idea',
  '.vs',
  '*.sublime-workspace',
  '*.swp',
  '*.swo',
  '*.swn',
  '.netrwhist',

  // === OS Metadata ===
  '.DS_Store',
  'Thumbs.db',
  'desktop.ini',
  '.Spotlight-V100',
  '.Trashes',
  '._*',

  // === Logs and Runtime Files ===
  'logs',
  '*.log',
  '*.pid',
  '*.seed',
  '*.pid.lock',

  // === Test Artifacts ===
  '.pytest_cache',
  '.tox',
  '__pycache__',
  '*.pyc',

  // === Temporary Files ===
  '*.tmp',
  '*.temp',
  '*.bak',
  '*~',

  // === Secrets (but allow templates) ===
  // Note: Files matching .env.example or .env.template are NOT ignored
  '.env',
  '.env.local',
  '.env.development',
  '.env.test',
  '.env.production',
  'credentials.json',
  'secrets.json',
  '*.key',
  '*.pem',
  '*.p12',
  '*.pfx',

  // === Atlas Runtime (daemon files) ===
  'daemon',
  '**/*.sock',
  '**/*.db',
  '**/*.db-shm',
  '**/*.db-wal',
]

// Ollama config
export const OLLAMA_URL = process.env.OLLAMA_URL || 'http://localhost:11434'

// Qdrant URL - from env or default
export const QDRANT_URL = process.env.QDRANT_URL || 'http://localhost:6333'

// Getter for consistency with other config (just returns the constant for now)
export function getQdrantURL(): string {
  return QDRANT_URL
}

export const VOYAGE_API_KEY = process.env.VOYAGE_API_KEY

// Consolidation config
export const CONSOLIDATION_BASE_THRESHOLD = 500 // chunks/points, not files
export const CONSOLIDATION_SCALE_FACTOR = 0.05
export const CONSOLIDATION_SIMILARITY_THRESHOLD = 0.8
export const CONSOLIDATION_POLL_INTERVAL_MS = 30000 // 30 seconds

// Deletion config
export const DELETION_GRACE_PERIOD_DAYS = 14
export const STABILITY_SCORE_THRESHOLD = 0.95

// HNSW batch mode config
export const HNSW_M_DEFAULT = 16
export const HNSW_M_DISABLED = 0
export const BATCH_HNSW_THRESHOLD = 20 // Disable HNSW if batch size > this
