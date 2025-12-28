/**
 * Atlas Context Ingestion Library
 *
 * Pure business logic for ingesting files into Qdrant with Voyage embeddings.
 * CLI interface is in index.ts.
 */

import { readFileSync } from 'fs'
import { basename, extname, relative } from 'path'
import { getQdrantClient, getTextSplitter, getVoyageClient } from './clients'
import { VOYAGE_MODEL } from './config'
import { log, startTimer } from './logger'
import { fetchExistingQNTMKeys, generateQNTMKeysBatch, sanitizeQNTMKey } from './qntm'
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

// Ingest a single file with QNTM multi-collection indexing
export async function ingestFile(
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
  let totalUpserts = 0

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

  // Process each chunk: upsert to multiple collections
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
      qntm_keys: qntmResult.keys, // Store all keys in payload
      created_at: timestamp,
      importance: 'normal',
      consolidated: false,
    }

    const point = {
      id: chunkId,
      vector: embedding,
      payload,
    }

    // Upsert same chunk to multiple collections (one per QNTM key)
    for (const qntmKey of qntmResult.keys) {
      const collectionName = sanitizeQNTMKey(qntmKey)

      // Ensure collection exists
      await ensureCollection(collectionName)

      log.trace('Qdrant upsert request', {
        collection: collectionName,
        pointId: point.id,
        vectorDim: point.vector.length,
        payloadKeys: Object.keys(point.payload),
      })

      // Upsert chunk to this semantic neighborhood
      await qdrant.upsert(collectionName, {
        points: [point],
        wait: true,
      })

      log.trace('Qdrant upsert complete', {
        collection: collectionName,
        pointId: point.id,
      })

      totalUpserts++
    }

    if (verbose && i % 10 === 0) {
      log.debug(`Processed chunk ${i + 1}/${chunks.length}`, {
        file: relativePath,
        qntmKeys: qntmResult.keys,
      })
    }
  }

  if (verbose) {
    log.info(`Stored ${chunks.length} chunks in ${totalUpserts} collection upserts`, {
      file: relativePath,
    })
  }

  endTimer()
  return chunks.length
}

// Main ingestion function
export async function ingest(config: IngestConfig): Promise<IngestResult> {
  const { paths, recursive = false, rootDir = process.cwd(), verbose = true } = config
  const endTimer = startTimer('ingest (total)')

  log.debug('Starting ingestion', { paths, recursive, rootDir })

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
