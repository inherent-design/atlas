/**
 * Atlas Context Ingestion Library
 *
 * Pure business logic for ingesting files into Qdrant with Voyage embeddings.
 * CLI interface is in index.ts.
 */

import { readFileSync } from 'fs'
import { basename, extname, relative } from 'path'
import { getQdrantClient, getTextSplitter, getVoyageClient } from './clients'
import { QDRANT_COLLECTION_NAME, VOYAGE_MODEL } from './config'
import { getConsolidationWatchdog, ingestPauseController } from './consolidation-watchdog'
import { createLogger, startTimer } from './logger'

const log = createLogger('ingest')
import { fetchExistingQNTMKeys, generateQNTMKeysBatch } from './qntm'
import type { ChunkPayload } from './types'
import { ensureCollection, expandPaths, generateChunkId } from './utils'

export interface IngestConfig {
  paths: string[]
  recursive?: boolean
  rootDir?: string
  verbose?: boolean
  existingKeys?: string[] // Pre-fetched keys for reuse
}

export interface IngestResult {
  filesProcessed: number
  chunksStored: number
  errors: Array<{ file: string; error: Error }>
}

// Ingest a single file into unified 'atlas' collection
export async function ingestFile(
  filePath: string,
  rootDir: string,
  options: { verbose?: boolean; existingKeys?: string[] } = {}
): Promise<number> {
  // Check if ingestion is paused for consolidation
  if (ingestPauseController.isPaused()) {
    log.debug('Ingestion paused, waiting for consolidation', { file: filePath })
    // Wait would block here - instead just skip with warning
    log.warn('Skipping file during consolidation pause', { file: filePath })
    return 0
  }

  // Register in-flight operation
  ingestPauseController.registerInFlight()

  try {
    return await ingestFileInternal(filePath, rootDir, options)
  } finally {
    // Complete in-flight operation
    ingestPauseController.completeInFlight()
  }
}

// Internal ingest logic (wrapped by pause controller)
async function ingestFileInternal(
  filePath: string,
  rootDir: string,
  options: { verbose?: boolean; existingKeys?: string[] } = {}
): Promise<number> {
  const { verbose = true, existingKeys = [] } = options
  const endTimer = startTimer(`ingestFile: ${filePath}`)

  const voyage = getVoyageClient()
  const qdrant = getQdrantClient()
  const splitter = getTextSplitter()

  const content = readFileSync(filePath, 'utf-8')
  const relativePath = relative(rootDir, filePath)

  log.debug('Reading file', { file: relativePath, sizeBytes: content.length })

  // Chunk text using Step 2 config
  const chunks = await splitter.splitText(content)
  log.debug('Chunked text', { file: relativePath, chunks: chunks.length })

  if (verbose) {
    log.info(`Ingesting: ${relativePath}`, { chunks: chunks.length })
  }

  // Embed all chunks in batch
  const embedStart = startTimer(`embed: ${relativePath}`)

  log.trace('Voyage embed request (batch)', {
    file: relativePath,
    chunkCount: chunks.length,
    model: VOYAGE_MODEL,
  })

  const embeddings = await voyage.embed({
    input: chunks,
    model: VOYAGE_MODEL,
  })

  log.trace('Voyage embed response (batch)', {
    file: relativePath,
    dataLength: embeddings.data?.length,
    embeddingDim: embeddings.data?.[0]?.embedding?.length,
    usage: embeddings.usage,
  })

  embedStart()

  const timestamp = new Date().toISOString()

  // Batch generate QNTM keys for all chunks concurrently
  log.debug('Batch generating QNTM keys', {
    file: relativePath,
    chunks: chunks.length,
  })

  const qntmInputs = chunks.map((chunk, i) => ({
    chunk,
    existingKeys,
    context: {
      fileName: basename(filePath),
      chunkIndex: i,
      totalChunks: chunks.length,
    },
  }))

  const qntmResults = await generateQNTMKeysBatch(qntmInputs)

  // Build all points for batch upsert
  const points: Array<{ id: string; vector: number[]; payload: ChunkPayload }> = []

  for (let i = 0; i < chunks.length; i++) {
    const chunk = chunks[i]
    if (!chunk) continue

    const qntmResult = qntmResults[i]
    if (!qntmResult) {
      log.warn('Missing QNTM result for chunk', { file: relativePath, chunk: i })
      continue
    }

    const chunkId = generateChunkId(relativePath, i)

    // Safety check for embeddings
    const embedding = embeddings.data?.[i]?.embedding
    if (!embedding) {
      log.warn('Missing embedding for chunk', { file: relativePath, chunk: i })
      continue
    }

    const payload: ChunkPayload = {
      original_text: chunk,
      file_path: relativePath,
      file_name: basename(filePath),
      file_type: extname(filePath),
      chunk_index: i,
      total_chunks: chunks.length,
      char_count: chunk.length,
      qntm_keys: qntmResult.keys, // QNTM keys as metadata tags
      created_at: timestamp,
      importance: 'normal',
      consolidated: false,
    }

    points.push({
      id: chunkId,
      vector: embedding,
      payload,
    })

    if (verbose && i % 10 === 0) {
      log.debug(`Prepared chunk ${i + 1}/${chunks.length}`, {
        file: relativePath,
        qntmKeys: qntmResult.keys,
      })
    }
  }

  // Batch upsert all chunks to unified collection
  if (points.length > 0) {
    log.trace('Qdrant batch upsert request', {
      collection: QDRANT_COLLECTION_NAME,
      pointCount: points.length,
    })

    await qdrant.upsert(QDRANT_COLLECTION_NAME, {
      points,
      wait: true,
    })

    log.trace('Qdrant batch upsert complete', {
      collection: QDRANT_COLLECTION_NAME,
      pointCount: points.length,
    })
  }

  if (verbose) {
    log.info(`Stored ${points.length} chunks`, { file: relativePath })
  }

  // Record ingestion for consolidation watchdog threshold tracking
  if (points.length > 0) {
    getConsolidationWatchdog().recordIngestion(points.length)
  }

  endTimer()
  return points.length
}

// Main ingestion function
export async function ingest(config: IngestConfig): Promise<IngestResult> {
  const { paths, recursive = false, rootDir = process.cwd(), verbose = true } = config
  const endTimer = startTimer('ingest (total)')

  log.debug('Starting ingestion', { paths, recursive, rootDir })

  // Ensure collection exists ONCE before any file processing
  await ensureCollection(QDRANT_COLLECTION_NAME)

  // Fetch existing QNTM keys for reuse
  const existingKeys = config.existingKeys || (await fetchExistingQNTMKeys())
  log.info('Fetched existing QNTM keys', { count: existingKeys.length })

  const filesToIngest = expandPaths(paths, recursive)
  log.info('Files to ingest', { count: filesToIngest.length })

  const errors: Array<{ file: string; error: Error }> = []
  let chunksStored = 0

  for (const file of filesToIngest) {
    try {
      const chunks = await ingestFile(file, rootDir, { verbose, existingKeys })
      chunksStored += chunks
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error))
      errors.push({ file, error: err })
      log.error(`Failed to ingest ${file}`, err)
    }
  }

  const result = {
    filesProcessed: filesToIngest.length - errors.length,
    chunksStored,
    errors,
  }

  log.info('Ingestion complete', {
    filesProcessed: result.filesProcessed,
    chunksStored: result.chunksStored,
    errorCount: errors.length,
  })

  if (errors.length > 0) {
    log.warn('Some files failed to ingest', { errorCount: errors.length })
  }

  endTimer()
  return result
}
