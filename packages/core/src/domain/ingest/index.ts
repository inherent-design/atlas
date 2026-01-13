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
import { getStorageBackend, withHNSWDisabled } from '../../services/storage/index.js'
import { getEmbeddingBackend } from '../../services/embedding/index.js'
import { getTextSplitter } from '../../services/chunking/index.js'
import { CHUNK_MIN_CHARS, BATCH_HNSW_THRESHOLD } from '../../shared/config.js'
import { getConfig } from '../../shared/config.loader.js'
import { createLogger, startTimer } from '../../shared/logger.js'
import { fetchExistingQNTMKeys, generateQNTMKeys } from '../../services/llm/index.js'
import type { ChunkPayload, IngestResult, IngestParams } from '../../shared/types.js'
import type { VectorPoint, NamedVectors } from '../../services/storage/index.js'
import {
  ensureCollection,
  expandPaths,
  generateChunkId,
  hashContent,
  getPrimaryCollectionName,
} from '../../shared/utils.js'
import {
  detectContentType,
  getRequiredVectors,
  TEXT_EXTENSIONS,
} from '../../services/embedding/types.js'
import type { CanEmbedContextualized } from '../../services/embedding/types.js'
import { parallel, batch } from '../../core/pipeline.js'
import { adaptiveParallel } from '../../core/adaptive-parallel.js'
import { createIngestContext } from './context.js'
import type { IngestContext } from './context.js'
import type { ChunkWithContext, EmbeddedChunk, KeyedChunk } from './types.js'
import type { QNTMGenerationInput } from '../../services/llm/index.js'
import { getFileTracker } from '../../services/tracking/index.js'
import {
  splitIntoDocumentsFast,
  estimateTotalTokens,
  VOYAGE_SAFE_LIMIT,
} from '../../services/tokenization/index.js'

const log = createLogger('ingest')

/**
 * Cache for contextualized embeddings to avoid duplicate API calls.
 * Key: filePath, Value: Promise<ContextualizedEmbeddingResult[][]>
 */
const contextualizedEmbeddingCache = new Map<string, Promise<any>>()

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
  // Use contextualized for text documents with 3+ chunks (context matters)
  return TEXT_EXTENSIONS.includes(ext as any) && chunkCount >= 3
}

// ============================================
// Streaming Pipeline Implementation
// ============================================

/**
 * Stream chunks from a single file with context.
 * Output: ChunkWithContext
 *
 * Integrates file tracker to skip unchanged files.
 */
async function* streamChunks(
  filePath: string,
  ctx: IngestContext
): AsyncGenerator<ChunkWithContext> {
  const splitter = getTextSplitter()
  const relativePath = relative(ctx.rootDir, filePath)

  // Check if file needs ingestion (file tracker)
  const db = ctx.getDatabase()
  const tracker = getFileTracker(db)
  const trackResult = await tracker.needsIngestion(filePath)

  if (!trackResult.needsIngest) {
    // Emit skip event
    ctx.emit?.({
      type: 'ingest.file.skipped',
      data: {
        path: relativePath,
        reason: trackResult.reason,
      },
    })
    log.debug('File unchanged, skipping', { file: relativePath })
    return // Don't yield any chunks for this file
  }

  // Emit file started event
  const content = readFileSync(filePath, 'utf-8')
  const contentType = detectContentType(filePath)

  log.debug('Reading file', { file: relativePath, sizeBytes: content.length })

  // Chunk text
  const rawChunks = await splitter.splitText(content)
  const chunks = rawChunks.filter((chunk) => chunk.trim().length >= CHUNK_MIN_CHARS)

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

  ctx.emit?.({
    type: 'ingest.file.started',
    data: {
      path: relativePath,
      chunkCount: chunks.length,
    },
  })

  // Check if document exceeds context window and needs splitting
  const estimatedTokens = estimateTotalTokens(chunks)
  const needsSplit = estimatedTokens > VOYAGE_SAFE_LIMIT

  if (needsSplit) {
    // Split into sub-documents for contextualized embedding
    const subDocuments = splitIntoDocumentsFast(chunks, VOYAGE_SAFE_LIMIT)
    log.info('Large document split for contextualized embedding', {
      file: relativePath,
      originalChunks: chunks.length,
      estimatedTokens,
      subDocuments: subDocuments.length,
    })

    // Track global chunk index across splits
    let globalChunkIndex = 0

    for (let splitIndex = 0; splitIndex < subDocuments.length; splitIndex++) {
      const subDoc = subDocuments[splitIndex]!

      for (let localIndex = 0; localIndex < subDoc.length; localIndex++) {
        yield {
          chunk: subDoc[localIndex]!,
          context: {
            filePath: relativePath,
            fileName: basename(filePath),
            fileType: extname(filePath),
            chunkIndex: localIndex, // Local index within sub-document
            totalChunks: subDoc.length, // Chunks in this sub-document
            contentType,
            allChunks: subDoc, // Only this sub-document's chunks
            // Split metadata
            splitIndex,
            splitTotal: subDocuments.length,
            chunkIndexGlobal: globalChunkIndex,
          },
        }
        globalChunkIndex++
      }
    }
  } else {
    // Normal case: document fits in context window
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
          allChunks: chunks, // Pass all chunks for contextualized embedding
        },
      }
    }
  }
}

/**
 * Embed a single chunk (snippet or contextualized).
 * Pure transform: ChunkWithContext → EmbeddedChunk
 */
async function embedChunk(
  chunkWithContext: ChunkWithContext,
  ctx: IngestContext
): Promise<EmbeddedChunk> {
  const { chunk, context } = chunkWithContext
  const requiredVectors = getRequiredVectors(context.contentType)

  // Determine if we should use contextualized
  const useContextualized =
    shouldUseContextualized(context.filePath, context.totalChunks) && ctx.contextualizedAvailable

  let embedding: number[]
  let embeddingModel: string
  let embeddingStrategy: 'snippet' | 'contextualized'
  let codeEmbedding: number[] | undefined

  // Text embedding (always present)
  if (requiredVectors.includes('text')) {
    if (useContextualized && context.allChunks) {
      // Use contextualized embeddings (allChunks provided in context)
      const contextBackend = await ctx.getContextualizedEmbeddingBackend()
      if (contextBackend && 'embedContextualized' in contextBackend) {
        // Check cache first (avoid duplicate API calls for same file/split)
        // Include split index in cache key for large documents split into sub-documents
        const splitSuffix = context.splitIndex !== undefined ? `:split${context.splitIndex}` : ''
        const cacheKey = `${context.filePath}${splitSuffix}`
        if (!contextualizedEmbeddingCache.has(cacheKey)) {
          log.trace('Embedding request (contextualized)', {
            file: context.filePath,
            backend: contextBackend.name,
            totalChunks: context.totalChunks,
            splitIndex: context.splitIndex,
            splitTotal: context.splitTotal,
          })

          // Cache the promise (so concurrent chunks await the same call)
          const embedPromise = (contextBackend as CanEmbedContextualized).embedContextualized([
            context.allChunks,
          ])
          contextualizedEmbeddingCache.set(cacheKey, embedPromise)
        } else {
          log.trace('Using cached contextualized embeddings', {
            file: context.filePath,
            chunkIndex: context.chunkIndex,
            splitIndex: context.splitIndex,
          })
        }

        const contextResult = await contextualizedEmbeddingCache.get(cacheKey)!
        // Get this chunk's embedding from the batch
        embedding = contextResult[0]![context.chunkIndex]!.embedding
        embeddingModel = (contextBackend as any).model ?? 'voyage-context-3'
        embeddingStrategy = 'contextualized'

        log.trace('Embedding response (contextualized)', {
          file: context.filePath,
          chunkIndex: context.chunkIndex,
          splitIndex: context.splitIndex,
          embeddingDim: embedding.length,
          model: embeddingModel,
        })
      } else {
        // Fallback to snippet (backend not available)
        log.debug('Contextualized backend not available, falling back to snippet', {
          file: context.filePath,
        })
        const textBackend = await ctx.getEmbeddingBackend()
        const textResult = await textBackend.embedText!([chunk])
        embedding = textResult.embeddings[0]!
        embeddingModel = textResult.model
        embeddingStrategy = 'snippet'
      }
    } else if (useContextualized && !context.allChunks) {
      // Fallback to snippet (allChunks not provided)
      log.debug('Contextualized embedding skipped (no allChunks), using snippet embedding', {
        file: context.filePath,
        chunkIndex: context.chunkIndex,
      })
      const textBackend = await ctx.getEmbeddingBackend()
      const textResult = await textBackend.embedText!([chunk])
      embedding = textResult.embeddings[0]!
      embeddingModel = textResult.model
      embeddingStrategy = 'snippet'
    } else {
      // Use snippet embeddings
      const textBackend = await ctx.getEmbeddingBackend()

      log.trace('Embedding request (snippet)', {
        file: context.filePath,
        chunkIndex: context.chunkIndex,
        backend: textBackend.name,
      })

      const textResult = await textBackend.embedText!([chunk])
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

      const codeResult = await codeBackend.embedCode!([chunk])
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

  // Emit chunk embedded event
  ctx.emit?.({
    type: 'ingest.chunk.embedded',
    data: {
      path: context.filePath,
      index: context.chunkIndex,
      strategy: embeddingStrategy,
    },
  })

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
      for await (const chunk of streamChunks(filePath, ctx)) {
        yield chunk
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
 *
 * Also records ingestion in file tracker.
 */
async function upsertChunks(
  chunks: AsyncIterable<KeyedChunk>,
  ctx: IngestContext,
  batchSize: number,
  timeoutMs: number
): Promise<number> {
  const storageService = ctx.getStorageService()
  const db = ctx.getDatabase()
  const tracker = getFileTracker(db)
  const timestamp = new Date().toISOString()
  let totalStored = 0

  // Group chunks by file for tracker recording
  const fileChunksMap = new Map<string, { chunks: any[]; filePath: string }>()

  // Batch chunks for efficient upsert
  const batches = batch(chunks, { maxSize: batchSize, timeoutMs })

  for await (const chunkBatch of batches) {
    const points: VectorPoint<ChunkPayload>[] = []

    for (const keyedChunk of chunkBatch) {
      const {
        chunk,
        context,
        embedding,
        codeEmbedding,
        embeddingModel,
        embeddingStrategy,
        qntmKeys,
      } = keyedChunk

      const chunkId = generateChunkId(context.filePath, context.chunkIndex)

      // Build named vectors structure
      const namedVectors: NamedVectors = {
        text: embedding,
      }

      if (codeEmbedding) {
        namedVectors.code = codeEmbedding
      }

      const requiredVectors = getRequiredVectors(context.contentType)
      const vectorsPresent = requiredVectors.filter((v) =>
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

        // Split metadata (for large documents exceeding context window)
        ...(context.splitIndex !== undefined && {
          split_index: context.splitIndex,
          split_total: context.splitTotal,
          chunk_index_global: context.chunkIndexGlobal,
        }),
      }

      points.push({
        id: chunkId,
        vector: namedVectors,
        payload,
      })

      // Track chunks by file for later recording
      const absolutePath = `${ctx.rootDir}/${context.filePath}`.replace(/\/\//g, '/')
      if (!fileChunksMap.has(absolutePath)) {
        fileChunksMap.set(absolutePath, { chunks: [], filePath: absolutePath })
      }
      fileChunksMap.get(absolutePath)!.chunks.push({
        index: context.chunkIndex,
        contentHash: hashContent(chunk),
        qdrantPointId: chunkId,
      })

      // Emit chunk stored event
      ctx.emit?.({
        type: 'ingest.chunk.stored',
        data: {
          path: context.filePath,
          index: context.chunkIndex,
          id: chunkId,
        },
      })
    }

    if (points.length > 0) {
      const collectionName = getPrimaryCollectionName()

      log.trace('Storage batch upsert request (multi-tier)', {
        collection: collectionName,
        pointCount: points.length,
      })

      // Dual-write to Qdrant + PostgreSQL + Meilisearch (if enabled)
      await storageService.upsertVectors(collectionName, points)

      log.trace('Storage batch upsert complete (multi-tier)', {
        collection: collectionName,
        pointCount: points.length,
      })

      totalStored += points.length

      log.debug(`Stored batch of ${points.length} chunks`, { totalStored })
    }
  }

  // Record ingestion in file tracker (after all batches complete)
  for (const [filePath, { chunks: fileChunks }] of fileChunksMap) {
    try {
      await tracker.recordIngestion(filePath, fileChunks)

      // Emit file completed event
      const relativePath = relative(ctx.rootDir, filePath)
      ctx.emit?.({
        type: 'ingest.file.completed',
        data: {
          path: relativePath,
          chunks: fileChunks.length,
        },
      })
    } catch (error) {
      log.error('Failed to record ingestion in file tracker', {
        filePath,
        error: (error as Error).message,
      })
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
    recursive: false,
    verbose,
  })

  try {
    // Stream chunks from file
    const chunks = streamChunks(filePath, ctx)

    // Embed chunks (concurrency: 3 for API rate limits)
    const embedded = parallel(chunks, (chunk) => embedChunk(chunk, ctx), 3)

    // Get ingestion config for tuning parameters
    const atlasConfig = getConfig()
    const ingestionConfig = atlasConfig.ingestion ?? {}

    // Generate QNTM keys (adaptive concurrency based on config + system pressure)
    const keyed = adaptiveParallel(embedded, (chunk) => generateKeysForChunk(chunk, ctx), {
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
    // Clear contextualized embedding cache
    contextualizedEmbeddingCache.clear()
  }
}

/**
 * Main ingestion function - streaming pipeline for all files.
 */
export async function ingest(config: IngestParams): Promise<IngestResult> {
  const { paths, recursive = false, rootDir = process.cwd(), verbose = true } = config
  const endTimer = startTimer('ingest (total)')

  log.debug('Starting ingestion', { paths, recursive, rootDir })

  // Ensure collection exists ONCE before any file processing (uses dimension-based naming)
  await ensureCollection()

  // Fetch existing QNTM keys for reuse
  const existingKeys = config.existingKeys || (await fetchExistingQNTMKeys())
  log.info('Fetched existing QNTM keys', { count: existingKeys.length })

  const filesToIngest = expandPaths(paths, recursive)
  log.info('Files to ingest', { count: filesToIngest.length })

  // Emit ingest.started event
  config.emit?.({
    type: 'ingest.started',
    data: {
      paths,
      fileCount: filesToIngest.length,
    },
  })

  // Determine if we should use HNSW toggle (auto: based on file count threshold)
  const shouldToggleHNSW = config.useHNSWToggle ?? filesToIngest.length >= BATCH_HNSW_THRESHOLD

  if (shouldToggleHNSW) {
    log.info('Batch mode: HNSW indexing will be disabled during ingestion', {
      fileCount: filesToIngest.length,
      threshold: BATCH_HNSW_THRESHOLD,
    })
  }

  // Create ingest context
  const ctx = await createIngestContext({
    ...config,
    rootDir,
    existingKeys,
  })

  // Core ingestion logic
  const ingestBatch = async (): Promise<IngestResult> => {
    const errors: Array<{ file: string; error: string }> = []
    let chunksStored = 0
    let skippedCount = 0

    try {
      // Stream all files through unified pipeline
      const allChunks = streamAllFiles(filesToIngest, ctx)

      // Get ingestion config for tuning parameters
      const atlasConfig = getConfig()
      const ingestionConfig = atlasConfig.ingestion ?? {}

      // Embed chunks (concurrency: 3 for API rate limits)
      const embedded = parallel(allChunks, (chunk) => embedChunk(chunk, ctx), 3)

      // Generate QNTM keys (adaptive concurrency based on config + system pressure)
      const keyed = adaptiveParallel(embedded, (chunk) => generateKeysForChunk(chunk, ctx), {
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
      errors.push({ file: '<pipeline>', error: err.message })

      // Emit error event
      config.emit?.({
        type: 'ingest.error',
        data: {
          error: err.message,
          phase: 'store',
        },
      })
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
  } catch (error) {
    // Emit error event for outer exception
    const err = error instanceof Error ? error : new Error(String(error))
    config.emit?.({
      type: 'ingest.error',
      data: {
        error: err.message,
        phase: 'store',
      },
    })
    throw error
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

  // Emit ingest.completed event
  config.emit?.({
    type: 'ingest.completed',
    data: {
      files: result.filesProcessed,
      chunks: result.chunksStored,
      skipped: 0, // Note: we'd need to track this separately if needed
      errors: result.errors.length,
    },
  })

  endTimer()

  // Clear contextualized embedding cache
  contextualizedEmbeddingCache.clear()

  return result
}
