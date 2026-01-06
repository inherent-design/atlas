/**
 * Atlas Context Search Library
 *
 * Pure business logic for searching ingested context with Voyage + Qdrant.
 * CLI interface is in index.ts.
 *
 * Access Tracking:
 * - Increments access_count on retrieved chunks
 * - Updates last_accessed_at timestamp
 * - Filters out deletion_eligible and superseded_by chunks
 */

import { getEmbeddingBackend } from '../../services/embedding'
import { getStorageBackend } from '../../services/storage'
import { getRerankerBackendFor } from '../../services/reranker'
import { generateQueryQNTMKeys, fetchExistingQNTMKeys } from '../../services/llm'
import type { StorageFilter } from '../../services/storage'
import {
  QDRANT_COLLECTION_NAME,
  DEFAULT_SEARCH_LIMIT,
  DEFAULT_HNSW_EF,
  DEFAULT_QUANTIZATION_RESCORE,
  DEFAULT_QUANTIZATION_OVERSAMPLING,
} from '../../shared/config'
import { createLogger, startTimer } from '../../shared/logger'
import type { SearchOptions, SearchResult, ChunkPayload } from '../../shared/types'

const log = createLogger('search')

/**
 * Update access tracking for retrieved chunks
 * Increments access_count and sets last_accessed_at
 * Follows supersession chains to credit the current version
 */
async function updateAccessTracking(pointIds: string[]): Promise<void> {
  if (pointIds.length === 0) return

  const storageBackend = getStorageBackend('vector-storage')
  if (!storageBackend) {
    log.warn('No storage backend available for access tracking')
    return
  }

  const now = new Date().toISOString()

  try {
    // Retrieve points to check for supersession
    const points = await storageBackend.retrieve(QDRANT_COLLECTION_NAME, pointIds)

    // Build map of target IDs (follow supersession chains)
    const targetUpdates = new Map<string, number>()

    for (const point of points) {
      const payload = point.payload as ChunkPayload
      let targetId = point.id
      let targetPayload = payload

      // Follow supersession chain to current version
      while (targetPayload.superseded_by) {
        try {
          const successor = await storageBackend.retrieve(QDRANT_COLLECTION_NAME, [
            targetPayload.superseded_by,
          ])
          if (successor.length === 0) break
          targetId = successor[0]!.id
          targetPayload = successor[0]!.payload as ChunkPayload
        } catch {
          break // Chain broken, use last valid target
        }
      }

      // Accumulate access counts per target (in case multiple accessed chunks point to same current version)
      targetUpdates.set(targetId, (targetUpdates.get(targetId) ?? 0) + 1)
    }

    // Update each target's access tracking
    for (const [targetId, incrementBy] of targetUpdates) {
      const target = await storageBackend.retrieve(QDRANT_COLLECTION_NAME, [targetId])
      if (target.length === 0) continue

      const currentPayload = target[0]!.payload as ChunkPayload
      await storageBackend.setPayload(QDRANT_COLLECTION_NAME, [targetId], {
        access_count: (currentPayload.access_count ?? 0) + incrementBy,
        last_accessed_at: now,
      })
    }

    log.debug('Updated access tracking', {
      requested: pointIds.length,
      targets: targetUpdates.size,
      timestamp: now,
    })
  } catch (error) {
    // Non-fatal: log warning but don't fail the search
    log.warn('Failed to update access tracking', {
      error: (error as Error).message,
      pointCount: pointIds.length,
    })
  }
}

// Semantic search with optional temporal filtering
export async function search(options: SearchOptions): Promise<SearchResult[]> {
  const endTimer = startTimer('search')
  const startTime = Date.now()

  // Emit search.started event
  options.emit?.({
    type: 'search.started',
    data: {
      query: options.query,
      sessionId: undefined, // Could be passed in options if needed
      limit: options.limit ?? DEFAULT_SEARCH_LIMIT,
    },
  })

  try {
    // Get backends from registries
    const embeddingBackend = getEmbeddingBackend('text-embedding')
    if (!embeddingBackend) {
      throw new Error('No text embedding backend available')
    }

    const storageBackend = getStorageBackend('vector-storage')
    if (!storageBackend) {
      throw new Error('No vector storage backend available')
    }

    const { query, limit = DEFAULT_SEARCH_LIMIT, since, qntmKey } = options

    log.debug('Starting search', { query, limit, since, qntmKey })

    // Query expansion (optional)
    let expandedKeys: string[] = []
    if (options.expandQuery) {
      const existingKeys = await fetchExistingQNTMKeys()
      const expansion = await generateQueryQNTMKeys(query, existingKeys.slice(0, 30))
      expandedKeys = expansion.keys

      log.debug('Query expanded with QNTM keys', {
        original: query,
        expansion: expandedKeys,
      })
    }

    // Embed query using backend
    const embedStart = startTimer('embed query')

    log.trace('Embedding request', { query, backend: embeddingBackend.name })

    const embedResult = await embeddingBackend.embedText!(query)

    log.trace('Embedding response', {
      embeddingCount: embedResult.embeddings.length,
      embeddingDim: embedResult.embeddings[0]?.length,
      usage: embedResult.usage,
    })

    embedStart()

    // Safety check for embedding
    const queryVector = embedResult.embeddings[0]
    if (!queryVector) {
      throw new Error('Failed to generate query embedding')
    }

    // Build typed filter for temporal/semantic constraints
    const filter: StorageFilter = {
      // Always exclude deleted chunks
      must_not: [{ key: 'deletion_eligible', match: { value: true } }],
      // Only include chunks where superseded_by is null (not superseded)
      must: [{ is_null: 'superseded_by' }],
    }

    // Add temporal filter
    if (since) {
      filter.must = filter.must || []
      filter.must.push({
        key: 'created_at',
        range: {
          gte: since,
        },
      })
    }

    // Add QNTM key filter
    if (qntmKey) {
      filter.must = filter.must || []
      filter.must.push({
        key: 'qntm_keys',
        match: { any: [qntmKey] },
      })
    }

    // Add consolidation level filter
    if (options.consolidationLevel !== undefined) {
      filter.must = filter.must || []
      filter.must.push({
        key: 'consolidation_level',
        match: { value: options.consolidationLevel },
      })
    }

    // Add QNTM key expansion boost (optional)
    if (expandedKeys.length > 0) {
      filter.should = filter.should || []
      filter.should.push({
        key: 'qntm_keys',
        match: { any: expandedKeys },
      })
    }

    // Search using backend
    // Default to 'text' vector, future: add CLI flag to search 'code' vector
    const searchStart = startTimer('storage search')

    log.trace('Storage search request', {
      collection: QDRANT_COLLECTION_NAME,
      vectorName: 'text',
      vectorDim: queryVector.length,
      limit,
      hasFilter:
        Object.keys(filter.must_not || []).length > 0 || Object.keys(filter.must || []).length > 0,
      backend: storageBackend.name,
    })

    let results: Array<
      import('../../services/storage').SearchResult<ChunkPayload> & { rerank_score?: number }
    > = await storageBackend.search(QDRANT_COLLECTION_NAME, {
      vectorName: 'text', // Phase 2: Default to text vector
      vector: queryVector,
      limit,
      filter:
        Object.keys(filter.must_not || []).length > 0 || Object.keys(filter.must || []).length > 0
          ? filter
          : undefined,
    })

    log.trace('Storage search response', {
      collection: QDRANT_COLLECTION_NAME,
      resultCount: results.length,
      topScore: results[0]?.score,
    })

    searchStart()

    log.info('Search complete', { resultsFound: results.length })

    // Rerank results automatically if Voyage reranker available (unless explicitly disabled)
    const shouldRerank = options.rerank !== false && results.length > 0
    if (shouldRerank) {
      const rerankStart = startTimer('reranker')
      const reranker = getRerankerBackendFor('text-reranking')

      if (reranker && 'rerank' in reranker) {
        const rerankTopK = options.rerankTopK ?? limit * 3

        // Get more candidates for reranking (up to rerankTopK, but don't exceed results)
        const candidateCount = Math.min(rerankTopK, results.length)
        const candidates = results.slice(0, candidateCount)
        const documents = candidates.map((hit) => (hit.payload as ChunkPayload).original_text)

        log.debug('Reranking results', {
          candidates: candidates.length,
          finalLimit: limit,
          backend: reranker.name,
        })

        try {
          const reranked = await (reranker as any).rerank(query, documents, { topK: limit })

          // Reorder results by rerank score (reranker returns sorted by relevance)
          results = reranked.results.map((r: any) => {
            const originalHit = candidates[r.index]
            return {
              ...originalHit,
              rerank_score: r.relevance_score,
            }
          })

          log.debug('Reranking complete', {
            results: results.length,
            topRerankScore: results[0]?.rerank_score,
          })
        } catch (error) {
          log.warn('Reranking failed, using vector search results', {
            error: (error as Error).message,
          })
        }

        rerankStart()
      } else {
        log.debug('Reranker not available, using vector search results only')
      }
    }

    // Extract point IDs for access tracking
    const pointIds = results.map((hit) => hit.id)

    // Update access tracking (non-blocking, fire-and-forget)
    updateAccessTracking(pointIds).catch((err) => {
      log.warn('Access tracking update failed', { error: err.message })
    })

    // Format results
    const formatted = results.map((hit) => {
      const payload = hit.payload as ChunkPayload
      return {
        text: payload.original_text,
        file_path: payload.file_path,
        chunk_index: payload.chunk_index,
        score: hit.score,
        created_at: payload.created_at,
        qntm_key: payload.qntm_keys[0] || 'unknown', // Use first key for display
        rerank_score: (hit as any).rerank_score, // Preserve rerank score if present
      }
    })

    // Emit search.completed event
    const reranker = getRerankerBackendFor('text-reranking')
    const wasReranked = shouldRerank && reranker && 'rerank' in reranker
    options.emit?.({
      type: 'search.completed',
      data: {
        results: formatted.length,
        took: Date.now() - startTime,
        reranked: wasReranked,
      },
    })

    endTimer()
    return formatted
  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error))

    // Emit search.error event
    options.emit?.({
      type: 'search.error',
      data: {
        query: options.query,
        error: err.message,
        phase: 'search', // Could be 'embed', 'search', or 'rerank' depending on where it failed
      },
    })

    // Re-throw error
    throw error
  }
}

// Get chronological timeline (temporal-only query)
export async function timeline(since: string, limit = 20): Promise<SearchResult[]> {
  const endTimer = startTimer('timeline')

  const storageBackend = getStorageBackend('vector-storage')
  if (!storageBackend) {
    throw new Error('No vector storage backend available')
  }

  log.debug('Fetching timeline', { since, limit })

  const filter: StorageFilter = {
    must: [
      {
        key: 'created_at',
        range: { gte: since },
      },
      // Only include chunks where superseded_by is null (not superseded)
      { is_null: 'superseded_by' },
    ],
    // Exclude deleted chunks
    must_not: [{ key: 'deletion_eligible', match: { value: true } }],
  }

  log.trace('Storage scroll request', {
    collection: QDRANT_COLLECTION_NAME,
    filter,
    backend: storageBackend.name,
  })

  const results = await storageBackend.scroll(QDRANT_COLLECTION_NAME, {
    filter,
    limit,
  })

  log.trace('Storage scroll response', {
    collection: QDRANT_COLLECTION_NAME,
    pointCount: results.points.length,
    nextPageOffset: results.nextOffset,
  })

  log.info('Timeline complete', { pointsFound: results.points.length })

  const formatted = results.points.map((point) => {
    const payload = point.payload as ChunkPayload
    return {
      text: payload.original_text,
      file_path: payload.file_path,
      chunk_index: payload.chunk_index,
      score: 1.0, // Timeline queries don't have similarity scores
      created_at: payload.created_at,
      qntm_key: payload.qntm_keys[0] || 'unknown', // Use first key for display
    }
  })

  endTimer()
  return formatted
}

// Format results for display
export function formatResults(results: SearchResult[]): string {
  if (results.length === 0) {
    return 'No results found.'
  }

  return results
    .map((result, i) => {
      const scoreDisplay =
        result.rerank_score !== undefined
          ? `Vector: ${result.score.toFixed(3)} | Rerank: ${result.rerank_score.toFixed(3)}`
          : `Score: ${result.score.toFixed(3)}`
      const header = `[${i + 1}] ${result.file_path} (chunk ${result.chunk_index}) - ${scoreDisplay}`
      const meta = `QNTM: ${result.qntm_key} | Created: ${result.created_at}`
      const divider = '─'.repeat(80)
      return `${header}\n${meta}\n${divider}\n${result.text}\n`
    })
    .join('\n')
}
