/**
 * Shared utility functions for Atlas
 */

import { createHash } from 'crypto'
import { readdirSync, statSync } from 'fs'
import { dirname, extname, join, resolve } from 'path'
import {
  QDRANT_COLLECTION_NAME,
  IGNORE_PATTERNS,
  QDRANT_COLLECTION_CONFIG,
  TEXT_FILE_EXTENSIONS,
  buildCollectionConfig,
} from './config'

// ============================================
// Singleton Factory
// ============================================

/**
 * Creates a lazy singleton with test reset capability.
 * Prevents code duplication across service clients.
 *
 * @param factory - Function that creates the instance
 * @param name - Debug name for logging (optional)
 * @returns Object with get() and reset() methods
 */
export function createSingleton<T>(
  factory: () => T,
  name?: string
): {
  get: () => T
  reset: () => void
} {
  let instance: T | null = null
  return {
    get: () => {
      if (!instance) {
        instance = factory()
        // Lazy import logger to avoid circular dependencies
        if (name) {
          import('./logger').then(({ createLogger }) => {
            const log = createLogger('utils')
            log.trace('Singleton created', { name })
          })
        }
      }
      return instance
    },
    reset: () => {
      instance = null
      if (name) {
        import('./logger').then(({ createLogger }) => {
          const log = createLogger('utils')
          log.trace('Singleton reset', { name })
        })
      }
    },
  }
}

// Import logger after singleton factory
import { createLogger } from './logger'
const log = createLogger('utils')

// Import storage backend via registry (abstracted interface)
import { getStorageBackend } from '../services/storage'

// ============================================
// Hash Generation
// ============================================

// Generate QNTM semantic key via content hash
// TODO: Replace with LLM-based QNTM generation for better semantic stability
export function generateQNTMKey(text: string): string {
  const hash = createHash('md5').update(text.substring(0, 500)).digest('hex').substring(0, 8)
  return `atlas_${hash}`
}

// Generate stable ID for chunk
export function generateChunkId(filePath: string, chunkIndex: number): string {
  const hash = createHash('md5').update(`${filePath}:${chunkIndex}`).digest('hex')
  return hash
}

// Payload index definitions for filtered queries
const PAYLOAD_INDEXES = [
  { field: 'qntm_keys', schema: 'keyword' as const },
  { field: 'created_at', schema: 'datetime' as const },
  { field: 'consolidated', schema: 'bool' as const },
]

// Ensure collection exists with Step 3 production config
export async function ensureCollection(collectionName?: string): Promise<void> {
  const backend = getStorageBackend()
  if (!backend) {
    throw new Error('No storage backend available')
  }
  const name = collectionName || QDRANT_COLLECTION_NAME

  // Get embedding dimensions from configured backend
  const { getEmbeddingDimensions } = await import('../services/embedding')
  const expectedDimensions = getEmbeddingDimensions()

  const exists = await backend.collectionExists(name)
  if (exists) {
    log.debug('Collection exists, validating dimensions', { collection: name })

    // Validate dimensions match expected
    const collectionInfo = await backend.getCollectionInfo(name)
    if (collectionInfo.vector_dimensions) {
      const textVectorDims = collectionInfo.vector_dimensions.text
      const codeVectorDims = collectionInfo.vector_dimensions.code

      if (textVectorDims && textVectorDims !== expectedDimensions) {
        const errorMsg = `Collection '${name}' dimension mismatch: collection has ${textVectorDims} dimensions but configured embedding model outputs ${expectedDimensions}.\nEither:\n1. Change embedding.backend in config to match existing collection\n2. Run 'atlas qdrant drop --yes' to recreate collection with new dimensions`
        log.error(errorMsg)
        throw new Error(errorMsg)
      }

      if (codeVectorDims && codeVectorDims !== expectedDimensions) {
        const errorMsg = `Collection '${name}' dimension mismatch: collection code vector has ${codeVectorDims} dimensions but configured embedding model outputs ${expectedDimensions}.\nEither:\n1. Change embedding.backend in config to match existing collection\n2. Run 'atlas qdrant drop --yes' to recreate collection with new dimensions`
        log.error(errorMsg)
        throw new Error(errorMsg)
      }

      log.debug('Collection dimensions validated', {
        collection: name,
        dimensions: expectedDimensions
      })
    }
  } else {
    log.info('Creating collection with production config', {
      collection: name,
      dimensions: expectedDimensions
    })
    const collectionConfig = buildCollectionConfig(expectedDimensions)
    await backend.createCollection(name, collectionConfig)
    log.info('Collection created', {
      collection: name,
      dimensions: expectedDimensions,
      config: 'HNSW + int8 quantization',
    })

    // Create payload indexes for filtered queries
    await ensurePayloadIndexes(name)
  }
}

/**
 * Require collection to exist, throw if it doesn't
 *
 * Use this for operations that should NOT create the collection (e.g., consolidation).
 * Throws an error with actionable message if collection is missing.
 */
export async function requireCollection(collectionName?: string): Promise<void> {
  const backend = getStorageBackend()
  if (!backend) {
    throw new Error('No storage backend available')
  }
  const name = collectionName || QDRANT_COLLECTION_NAME

  const exists = await backend.collectionExists(name)
  if (!exists) {
    const msg = `Collection '${name}' does not exist. Run 'bun atlas ingest' first to create it.`
    log.error(msg)
    throw new Error(msg)
  }
  log.debug('Collection verified', { collection: name })
}

/**
 * Check if collection exists (non-throwing)
 */
export async function collectionExists(collectionName?: string): Promise<boolean> {
  const backend = getStorageBackend()
  if (!backend) {
    return false
  }
  const name = collectionName || QDRANT_COLLECTION_NAME
  return backend.collectionExists(name)
}

// Ensure payload indexes exist (idempotent)
export async function ensurePayloadIndexes(collectionName?: string): Promise<void> {
  const backend = getStorageBackend()
  if (!backend) {
    throw new Error('No storage backend available')
  }
  const name = collectionName || QDRANT_COLLECTION_NAME

  // createPayloadIndex is optional (Qdrant-specific)
  if (!backend.createPayloadIndex) {
    log.debug('Backend does not support payload indexes, skipping', { backend: backend.name })
    return
  }

  for (const { field, schema } of PAYLOAD_INDEXES) {
    try {
      await backend.createPayloadIndex(name, {
        field_name: field,
        field_schema: schema,
      })
      log.debug('Payload index created', { collection: name, field, schema })
    } catch (error) {
      // Index may already exist - that's fine
      const msg = (error as Error).message
      if (!msg.includes('already exists')) {
        log.warn('Failed to create payload index', { field, error: msg })
      }
    }
  }

  log.info('Payload indexes ensured', {
    collection: name,
    indexes: PAYLOAD_INDEXES.map((i) => i.field),
  })
}

// Recursively find all text files
export function findFiles(dirPath: string, recursive = false): string[] {
  const files: string[] = []

  function walk(dir: string) {
    const entries = readdirSync(dir, { withFileTypes: true })

    for (const entry of entries) {
      const fullPath = join(dir, entry.name)

      // Skip ignored directories
      if (IGNORE_PATTERNS.some((pattern) => entry.name.includes(pattern))) {
        continue
      }

      if (entry.isDirectory() && recursive) {
        walk(fullPath)
      } else if (entry.isFile()) {
        const ext = extname(entry.name)
        if (TEXT_FILE_EXTENSIONS.includes(ext)) {
          files.push(fullPath)
        }
      }
    }
  }

  walk(dirPath)
  return files
}

// Expand paths to files (directories → file list)
export function expandPaths(paths: string[], recursive = false): string[] {
  const files: string[] = []

  for (const path of paths) {
    const stat = statSync(path)

    if (stat.isDirectory()) {
      files.push(...findFiles(path, recursive))
    } else if (stat.isFile()) {
      files.push(path)
    }
  }

  return files
}

/**
 * Compute the root directory for relative path calculation.
 *
 * Uses user-provided input paths as the base, not CWD.
 * This ensures stored file_path reflects user intent, not program detail.
 *
 * @param inputPaths - Original paths from CLI (before expansion)
 * @returns Root directory for relative path calculation
 *
 * @example
 * // Single directory: use it as root
 * computeRootDir(['/Users/me/docs']) // → '/Users/me/docs'
 *
 * // Single file: use parent directory
 * computeRootDir(['/Users/me/docs/file.md']) // → '/Users/me/docs'
 *
 * // Multiple paths: find common ancestor
 * computeRootDir(['/Users/me/docs/a', '/Users/me/docs/b']) // → '/Users/me/docs'
 */
export function computeRootDir(inputPaths: string[]): string {
  if (inputPaths.length === 0) {
    return process.cwd()
  }

  // Resolve all paths to absolute
  const absolutePaths = inputPaths.map((p) => resolve(p))

  if (absolutePaths.length === 1) {
    const path = absolutePaths[0]!
    try {
      const stat = statSync(path)
      return stat.isDirectory() ? path : dirname(path)
    } catch {
      return dirname(path)
    }
  }

  // Multiple paths: find common ancestor
  const segments = absolutePaths.map((p) => p.split('/').filter(Boolean))
  const minLength = Math.min(...segments.map((s) => s.length))

  let commonDepth = 0
  for (let i = 0; i < minLength; i++) {
    const segment = segments[0]![i]
    if (segments.every((s) => s[i] === segment)) {
      commonDepth = i + 1
    } else {
      break
    }
  }

  const commonPath = '/' + segments[0]!.slice(0, commonDepth).join('/')
  return commonPath
}
