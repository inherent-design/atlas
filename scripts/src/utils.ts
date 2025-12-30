/**
 * Shared utility functions for Atlas
 */

import { createHash } from 'crypto'
import { readdirSync, statSync } from 'fs'
import { extname, join } from 'path'
import { getQdrantClient } from './clients'
import {
  QDRANT_COLLECTION_NAME,
  IGNORE_PATTERNS,
  QDRANT_COLLECTION_CONFIG,
  TEXT_FILE_EXTENSIONS,
} from './config'
import { createLogger } from './logger'

const log = createLogger('utils')

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
  const qdrant = getQdrantClient()
  const name = collectionName || QDRANT_COLLECTION_NAME

  try {
    await qdrant.getCollection(name)
    log.debug('Collection exists', { collection: name })
  } catch {
    log.info('Creating collection with production config', { collection: name })
    await qdrant.createCollection(name, QDRANT_COLLECTION_CONFIG)
    log.info('Collection created', {
      collection: name,
      config: 'HNSW + int8 quantization',
    })

    // Create payload indexes for filtered queries
    await ensurePayloadIndexes(name)
  }
}

// Ensure payload indexes exist (idempotent)
export async function ensurePayloadIndexes(collectionName?: string): Promise<void> {
  const qdrant = getQdrantClient()
  const name = collectionName || QDRANT_COLLECTION_NAME

  for (const { field, schema } of PAYLOAD_INDEXES) {
    try {
      await qdrant.createPayloadIndex(name, {
        field_name: field,
        field_schema: schema,
        wait: true,
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
