/**
 * Atlas Context Ingestion Library
 *
 * Streaming pipeline architecture for concurrent ingestion.
 * Pipeline: Read+Chunk → Embed → QNTM → Upsert (with backpressure)
 *
 * CLI interface is in index.ts.
 */

import { readFileSync } from 'fs'
import { basename, extname, relative } from 'path'
import { getStorageBackend, withHNSWDisabled } from '../../services/storage'
import { getEmbeddingBackend } from '../../services/embedding'
import { getTextSplitter } from '../../services/chunking'
import { QDRANT_COLLECTION_NAME, BATCH_HNSW_THRESHOLD, CHUNK_MIN_CHARS } from '../../shared/config'
import { getConfig } from '../../shared/config.loader'
import { getConsolidationWatchdog, ingestPauseController } from '../consolidate/watchdog'
import { createLogger, startTimer } from '../../shared/logger'
import { fetchExistingQNTMKeys, generateQNTMKeys } from '../../services/llm'
import type { ChunkPayload } from '../../shared/types'
import type { VectorPoint, NamedVectors } from '../../services/storage'
import { ensureCollection, expandPaths, generateChunkId } from '../../shared/utils'
import { detectContentType, getRequiredVectors, DOCUMENT_EXTENSIONS } from '../../services/embedding/types'
import type { CanEmbedContextualized } from '../../services/embedding/types'
import { parallel, batch } from '../../core/pipeline'
import { adaptiveParallel } from '../../core/adaptive-parallel'
import { createIngestContext } from './context'
import type { IngestContext } from './context'
import type { ChunkWithContext, EmbeddedChunk, KeyedChunk } from './types'
import type { QNTMGenerationInput } from '../../services/llm'

const log = createLogger('ingest')

/**
 * Determine if a file should use contextualized embeddings.
 *
 * Uses contextualized for documents with 3+ chunks where context matters.
 * Threshold: 3 chunks ensures there's meaningful context to leverage.
 *
 * @param filePath - File path (for extension check)
 * @param chunkCount - Number of chunks in the document
 * @returns true if contextualized embeddings should be used
 */
function shouldUseContextualized(filePath: string, chunkCount: number): boolean {
  const ext = filePath.slice(filePath.lastIndexOf('.')).toLowerCase()
  // Use contextualized for documents with 3+ chunks (context matters)
  return DOCUMENT_EXTENSIONS.includes(ext as any) && chunkCount >= 3
}

export interface IngestConfig {
  paths: string[]
  recursive?: boolean
  rootDir?: string
  verbose?: boolean
  existingKeys?: string[] // Pre-fetched keys for reuse
  useHNSWToggle?: boolean // Disable HNSW during batch ingestion (default: auto based on file count)
}

export interface IngestResult {
  filesProcessed: number
  chunksStored: number
  errors: Array<{ file: string; error: Error }>
}

// ============================================
// Streaming Pipeline Implementation
// ============================================

/**
 * Stream chunks from a single file with context.
 * Output: ChunkWithContext
 */
async function* streamChunks(
  filePath: string,
  ctx: IngestContext
): AsyncGenerator<ChunkWithContext> {
  const splitter = getTextSplitter()
  const content = readFileSync(filePath, 'utf-8')
  const relativePath = relative(ctx.rootDir, filePath)
  const contentType = detectContentType(filePath)

  log.debug('Reading file', { file: relativePath, sizeBytes: content.length })

  // Chunk text
  const rawChunks = await splitter.splitText(content)
  const chunks = rawChunks.filter(chunk => chunk.trim().length >= CHUNK_MIN_CHARS)

  if (rawChunks.length !== chunks.length) {
    log.debug('Filtered tiny chunks', {
      file: relativePath,
      original: rawChunks.length,
      filtered: chunks.length,
      removed: rawChunks.length - chunks.length,
    })
  }

  log.debug('Chunked text', { file: relativePath, chunks: chunks.length })
  log.info(`Ingesting: ${relativePath}`, { chunks: chunks.length, contentType })

  // Yield each chunk with context
  for (let i = 0; i < chunks.length; i++) {
    yield {
      chunk: chunks[i]!,
      context: {
        filePath: relativePath,
        fileName: basename(filePath),
        fileType: extname(filePath),
        chunkIndex: i,
        totalChunks: chunks.length,
        contentType,
      },
    }
  }
}

/**
 * Embed a single chunk (snippet or contextualized).
 * Pure transform: ChunkWithContext → EmbeddedChunk
 */
async function embedChunk(
  chunkWithContext: ChunkWithContext,
  ctx: IngestContext,
  allChunks?: string[] // For contextualized embedding (all chunks from same file)
): Promise<EmbeddedChunk> {
  const { chunk, context } = chunkWithContext
  const requiredVectors = getRequiredVectors(context.contentType)

  // Determine if we should use contextualized
  const useContextualized =
    shouldUseContextualized(context.filePath, context.totalChunks) &&
    ctx.contextualizedAvailable

  let embedding: number[]
  let embeddingModel: string
  let embeddingStrategy: 'snippet' | 'contextualized'
  let codeEmbedding: number[] | undefined

  // Text embedding (always present)
  if (requiredVectors.includes('text')) {
    if (useContextualized) {
      // Use contextualized embeddings
      const contextBackend = await ctx.getContextualizedEmbeddingBackend()
      if (contextBackend && 'embedContextualized' in contextBackend) {
        // Need all chunks for contextualized embedding
        if (!allChunks) {
          throw new Error('Contextualized embedding requires all chunks from file')
        }

        log.trace('Embedding request (contextualized)', {
          file: context.filePath,
          chunkIndex: context.chunkIndex,
          backend: contextBackend.name,
        })

        const contextResult = await (contextBackend as CanEmbedContextualized).embedContextualized(
          [allChunks]
        )
        // Get this chunk's embedding from the batch
        embedding = contextResult[0][context.chunkIndex]!.embedding
        embeddingModel = (contextBackend as any).model ?? 'voyage-context-3'
        embeddingStrategy = 'contextualized'

        log.trace('Embedding response (contextualized)', {
          file: context.filePath,
          chunkIndex: context.chunkIndex,
          embeddingDim: embedding.length,
          model: embeddingModel,
        })
      } else {
        // Fallback to snippet
        log.warn('Contextualized backend not available, falling back to snippet', {
          file: context.filePath,
        })
        const textBackend = await ctx.getEmbeddingBackend()
        const textResult = await textBackend.embedText([chunk])
        embedding = textResult.embeddings[0]!
        embeddingModel = textResult.model
        embeddingStrategy = 'snippet'
      }
    } else {
      // Use snippet embeddings
      const textBackend = await ctx.getEmbeddingBackend()

      log.trace('Embedding request (snippet)', {
        file: context.filePath,
        chunkIndex: context.chunkIndex,
        backend: textBackend.name,
      })

      const textResult = await textBackend.embedText([chunk])
      embedding = textResult.embeddings[0]!
      embeddingModel = textResult.model
      embeddingStrategy = 'snippet'

      log.trace('Embedding response (snippet)', {
        file: context.filePath,
        chunkIndex: context.chunkIndex,
        embeddingDim: textResult.dimensions,
        model: textResult.model,
      })
    }
  } else {
    throw new Error('Text vector required but not in requiredVectors')
  }

  // Code embedding (code files only)
  if (requiredVectors.includes('code') && ctx.codeEmbeddingAvailable) {
    const codeBackend = await ctx.getCodeEmbeddingBackend()
    if (codeBackend) {
      log.trace('Embedding request (code)', {
        file: context.filePath,
        chunkIndex: context.chunkIndex,
        backend: codeBackend.name,
      })

      const codeResult = await codeBackend.embedCode([chunk])
      codeEmbedding = codeResult.embeddings[0]

      log.trace('Embedding response (code)', {
        file: context.filePath,
        chunkIndex: context.chunkIndex,
        embeddingDim: codeResult.dimensions,
      })
    } else {
      log.warn('Code embedding backend not available, skipping code vector', {
        file: context.filePath,
      })
    }
  }

  return {
    ...chunkWithContext,
    embedding,
    embeddingModel,
    embeddingStrategy,
    codeEmbedding,
  }
}

/**
 * Generate QNTM keys for a chunk.
 * Pure transform: EmbeddedChunk → KeyedChunk
 */
async function generateKeysForChunk(
  embeddedChunk: EmbeddedChunk,
  ctx: IngestContext
): Promise<KeyedChunk> {
  const { chunk, context } = embeddedChunk

  log.trace('Generating QNTM keys', {
    file: context.filePath,
    chunkIndex: context.chunkIndex,
  })

  const qntmInput: QNTMGenerationInput = {
    chunk,
    existingKeys: ctx.existingQNTMKeys,
    context: {
      fileName: context.fileName,
      chunkIndex: context.chunkIndex,
      totalChunks: context.totalChunks,
    },
  }

  // Call generateQNTMKeys which uses backend registry
  const qntmResult = await generateQNTMKeys(qntmInput)

  log.trace('Generated QNTM keys', {
    file: context.filePath,
    chunkIndex: context.chunkIndex,
    keys: qntmResult.keys,
  })

  return {
    ...embeddedChunk,
    qntmKeys: qntmResult.keys,
  }
}

/**
 * Stream all chunks from all files.
 * Output: ChunkWithContext
 */
async function* streamAllFiles(
  filePaths: string[],
  ctx: IngestContext
): AsyncGenerator<ChunkWithContext> {
  for (const filePath of filePaths) {
    try {
      // Wait if ingestion is paused for consolidation
      if (ingestPauseController.isPaused()) {
        log.debug('Ingestion paused, waiting for consolidation to complete', { file: filePath })
        await ingestPauseController.waitForResume()
        log.debug('Consolidation complete, resuming ingestion', { file: filePath })
      }

      // Register in-flight operation
      ingestPauseController.registerInFlight()

      try {
        for await (const chunk of streamChunks(filePath, ctx)) {
          yield chunk
        }
      } finally {
        // Complete in-flight operation
        ingestPauseController.completeInFlight()
      }
    } catch (error) {
      log.error(`Failed to stream chunks from ${filePath}`, error as Error)
      // Continue with next file
    }
  }
}

/**
 * Upsert chunks in batches.
 * Consumes: AsyncIterable<KeyedChunk>
 * Returns: Total chunks stored
 */
async function upsertChunks(
  chunks: AsyncIterable<KeyedChunk>,
  ctx: IngestContext,
  batchSize: number,
  timeoutMs: number
): Promise<number> {
  const storageBackend = await ctx.getStorageBackend()
  const timestamp = new Date().toISOString()
  let totalStored = 0

  // Batch chunks for efficient upsert
  const batches = batch(chunks, { maxSize: batchSize, timeoutMs })

  for await (const chunkBatch of batches) {
    const points: VectorPoint<ChunkPayload>[] = []

    for (const keyedChunk of chunkBatch) {
      const { chunk, context, embedding, codeEmbedding, embeddingModel, embeddingStrategy, qntmKeys } =
        keyedChunk

      const chunkId = generateChunkId(context.filePath, context.chunkIndex)

      // Build named vectors structure
      const namedVectors: NamedVectors = {
        text: embedding,
      }

      if (codeEmbedding) {
        namedVectors.code = codeEmbedding
      }

      const requiredVectors = getRequiredVectors(context.contentType)
      const vectorsPresent = requiredVectors.filter(v =>
        v === 'text' ? namedVectors.text : v === 'code' ? namedVectors.code : false
      ) as ('text' | 'code' | 'media')[]

      const payload: ChunkPayload = {
        original_text: chunk,
        file_path: context.filePath,
        file_name: context.fileName,
        file_type: context.fileType,
        chunk_index: context.chunkIndex,
        total_chunks: context.totalChunks,
        char_count: chunk.length,
        qntm_keys: qntmKeys,
        created_at: timestamp,
        importance: 'normal',
        consolidation_level: 0, // Raw chunk, no consolidation yet

        // Embedding metadata
        embedding_model: embeddingModel,
        embedding_strategy: embeddingStrategy,
        content_type: context.contentType,
        vectors_present: vectorsPresent,
      }

      points.push({
        id: chunkId,
        vector: namedVectors,
        payload,
      })
    }

    if (points.length > 0) {
      log.trace('Storage batch upsert request', {
        collection: QDRANT_COLLECTION_NAME,
        pointCount: points.length,
        backend: storageBackend.name,
      })

      await storageBackend.upsert(QDRANT_COLLECTION_NAME, points)

      log.trace('Storage batch upsert complete', {
        collection: QDRANT_COLLECTION_NAME,
        pointCount: points.length,
      })

      totalStored += points.length

      // Record ingestion for consolidation watchdog
      getConsolidationWatchdog().recordIngestion(points.length)

      log.debug(`Stored batch of ${points.length} chunks`, { totalStored })
    }
  }

  return totalStored
}

// ============================================
// Backward-Compatible API
// ============================================

/**
 * Ingest a single file into unified 'atlas' collection.
 * Uses streaming pipeline internally for consistency.
 */
export async function ingestFile(
  filePath: string,
  rootDir: string,
  options: { verbose?: boolean; existingKeys?: string[] } = {}
): Promise<number> {
  const { verbose = true, existingKeys = [] } = options
  const endTimer = startTimer(`ingestFile: ${filePath}`)

  // Create context
  const ctx = await createIngestContext({
    paths: [filePath],
    rootDir,
    existingKeys,
  })

  // Wait if ingestion is paused for consolidation
  if (ingestPauseController.isPaused()) {
    log.debug('Ingestion paused, waiting for consolidation to complete', { file: filePath })
    await ingestPauseController.waitForResume()
    log.debug('Consolidation complete, resuming ingestion', { file: filePath })
  }

  // Register in-flight operation
  ingestPauseController.registerInFlight()

  try {
    // Stream chunks from file
    const chunks = streamChunks(filePath, ctx)

    // Embed chunks (concurrency: 3 for API rate limits)
    const embedded = parallel(chunks, chunk => embedChunk(chunk, ctx), 3)

    // Get ingestion config for tuning parameters
    const atlasConfig = getConfig()
    const ingestionConfig = atlasConfig.ingestion ?? {}

    // Generate QNTM keys (adaptive concurrency based on config + system pressure)
    const keyed = adaptiveParallel(embedded, chunk => generateKeysForChunk(chunk, ctx), {
      initialConcurrency: ingestionConfig.qntmConcurrency ?? 8,
      min: ingestionConfig.qntmConcurrencyMin ?? 2,
      max: ingestionConfig.qntmConcurrencyMax ?? 16,
      monitoringIntervalMs: ingestionConfig.monitoringIntervalMs ?? 30000,
    })

    // Upsert in batches (config-driven batch size and timeout)
    const stored = await upsertChunks(
      keyed,
      ctx,
      ingestionConfig.batchSize ?? 50,
      ingestionConfig.batchTimeoutMs ?? 15000
    )

    if (verbose) {
      const relativePath = relative(rootDir, filePath)
      log.info(`Stored ${stored} chunks`, { file: relativePath })
    }

    endTimer()
    return stored
  } finally {
    // Complete in-flight operation
    ingestPauseController.completeInFlight()
  }
}

/**
 * Main ingestion function - streaming pipeline for all files.
 */
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

  // Determine if we should use HNSW toggle (auto: based on file count threshold)
  const shouldToggleHNSW =
    config.useHNSWToggle ?? filesToIngest.length >= BATCH_HNSW_THRESHOLD

  if (shouldToggleHNSW) {
    log.info('Batch mode: HNSW indexing will be disabled during ingestion', {
      fileCount: filesToIngest.length,
      threshold: BATCH_HNSW_THRESHOLD,
    })
  }

  // Start consolidation watchdog to monitor ingestion and trigger consolidation
  const consolidationWatchdog = getConsolidationWatchdog()
  consolidationWatchdog.start()

  // Create ingest context
  const ctx = await createIngestContext({
    ...config,
    rootDir,
    existingKeys,
  })

  // Core ingestion logic
  const ingestBatch = async (): Promise<IngestResult> => {
    const errors: Array<{ file: string; error: Error }> = []
    let chunksStored = 0

    try {
      // Stream all files through unified pipeline
      const allChunks = streamAllFiles(filesToIngest, ctx)

      // Get ingestion config for tuning parameters
      const atlasConfig = getConfig()
      const ingestionConfig = atlasConfig.ingestion ?? {}

      // Embed chunks (concurrency: 3 for API rate limits)
      const embedded = parallel(allChunks, chunk => embedChunk(chunk, ctx), 3)

      // Generate QNTM keys (adaptive concurrency based on config + system pressure)
      const keyed = adaptiveParallel(embedded, chunk => generateKeysForChunk(chunk, ctx), {
        initialConcurrency: ingestionConfig.qntmConcurrency ?? 8,
        min: ingestionConfig.qntmConcurrencyMin ?? 2,
        max: ingestionConfig.qntmConcurrencyMax ?? 16,
        monitoringIntervalMs: ingestionConfig.monitoringIntervalMs ?? 30000,
      })

      // Upsert in batches (config-driven batch size and timeout)
      chunksStored = await upsertChunks(
        keyed,
        ctx,
        ingestionConfig.batchSize ?? 50,
        ingestionConfig.batchTimeoutMs ?? 15000
      )
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error))
      log.error('Pipeline error', err)
      errors.push({ file: '<pipeline>', error: err })
    }

    return {
      filesProcessed: filesToIngest.length - errors.length,
      chunksStored,
      errors,
    }
  }

  let result: IngestResult

  try {
    // Run with or without HNSW toggle
    result = shouldToggleHNSW ? await withHNSWDisabled(ingestBatch) : await ingestBatch()
  } finally {
    // Stop consolidation watchdog
    consolidationWatchdog.stop()
  }

  log.info('Ingestion complete', {
    filesProcessed: result.filesProcessed,
    chunksStored: result.chunksStored,
    errorCount: result.errors.length,
    usedHNSWToggle: shouldToggleHNSW,
  })

  if (result.errors.length > 0) {
    log.warn('Some files failed to ingest', { errorCount: result.errors.length })
  }

  endTimer()
  return result
}
