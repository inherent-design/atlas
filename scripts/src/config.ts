/**
 * Atlas Configuration
 * Based on .atlas research (Steps 1-4 + Sleep Patterns)
 */

// Collection config
export const COLLECTION_NAME = 'atlas_context' as const

// Voyage AI config (Step 3)
export const VOYAGE_MODEL = 'voyage-3-large' as const
export const EMBEDDING_DIM = 1024

// Chunking config (Step 2)
export const CHUNK_SIZE = 768 // tokens (conservative for quality)
export const CHUNK_OVERLAP = 100 // 13% overlap
export const CHUNK_SEPARATORS = ['\n\n', '\n', '. ', ' ', ''] // Hierarchical semantic boundaries

// Search defaults
export const DEFAULT_SEARCH_LIMIT = 5
export const DEFAULT_HNSW_EF = 50 // From Step 3 production config
export const DEFAULT_QUANTIZATION_RESCORE = true
export const DEFAULT_QUANTIZATION_OVERSAMPLING = 3.0

// Qdrant collection config (Step 3 production)
export const QDRANT_COLLECTION_CONFIG = {
  vectors: {
    size: EMBEDDING_DIM,
    distance: 'Dot' as const, // Voyage normalizes vectors, dot = cosine
    on_disk: true, // Full vectors on disk
  },
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

// QNTM generation config
export const DEFAULT_QNTM_PROVIDER = 'ollama' as const
export const DEFAULT_QNTM_MODEL_OLLAMA = 'qwen2.5:7b' as const
export const DEFAULT_QNTM_MODEL_ANTHROPIC = 'haiku' as const
export const OLLAMA_URL = process.env.OLLAMA_URL || 'http://localhost:11434'

// Environment
export const QDRANT_URL = process.env.QDRANT_URL || 'http://localhost:6333'
export const VOYAGE_API_KEY = process.env.VOYAGE_API_KEY
