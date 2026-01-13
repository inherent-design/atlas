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

import { getEmbeddingBackend } from '../../services/embedding/index.js'
import { getStorageBackend } from '../../services/storage/index.js'
import { getStorageService } from '../../services/storage/index.js'
import { getRerankerBackendFor } from '../../services/reranker/index.js'
import { generateQueryQNTMKeys, fetchExistingQNTMKeys } from '../../services/llm/index.js'
import type { StorageFilter } from '../../services/storage/index.js'
import {
  DEFAULT_SEARCH_LIMIT,
  DEFAULT_HNSW_EF,
  DEFAULT_QUANTIZATION_RESCORE,
  DEFAULT_QUANTIZATION_OVERSAMPLING,
} from '../../shared/config.js'
import { getPrimaryCollectionName } from '../../shared/utils.js'
import { createLogger, startTimer } from '../../shared/logger.js'
import type { SearchParams, SearchResult, ChunkPayload } from '../../shared/types.js'

const log = createLogger('search')

/**
 * Build Meilisearch filter string from SearchParams
 */
function buildMeilisearchFilters(options: SearchParams): string {
  const filters = []

  if (options.since) {
    // Convert ISO datetime to Unix timestamp (seconds)
    filters.push(`created_at >= ${new Date(options.since).getTime() / 1000}`)
  }

  if (options.qntmKey) {
    filters.push(`qntm_keys = "${options.qntmKey}"`)
  }

  if (options.consolidationLevel !== undefined) {
    filters.push(`consolidation_level = ${options.consolidationLevel}`)
  }

  if (options.contentType) {
    filters.push(`content_type = "${options.contentType}"`)
  }

  return filters.join(' AND ')
}

/**
 * Hybrid search: Combines vector search (Qdrant) with keyword search (Meilisearch)
 * Uses reciprocal rank fusion (RRF) to merge results
 */
async function hybridSearch(query: string, options: SearchParams): Promise<SearchResult[]> {
  const endTimer = startTimer('hybrid-search')
  const storageService = getStorageService()
  const limit = options.limit || DEFAULT_SEARCH_LIMIT
  const k = 60 // RRF constant (standard value)

  log.debug('Starting hybrid search', { query, limit })

  // 1. Vector search (semantic similarity) - fetch 3x limit for better recall
  const vectorResults = await search({
    ...options,
    limit: limit * 3,
  })

  log.debug('Vector search complete', { results: vectorResults.length })

  // 2. Keyword search (full-text) - fetch 3x limit for better recall
  const filters = buildMeilisearchFilters(options)
  const keywordResults = await storageService.fullTextSearch(query, {
    limit: limit * 3,
    filters: filters || undefined,
  })

  log.debug('Keyword search complete', { results: keywordResults.length })

  // 3. Reciprocal Rank Fusion (RRF)
  interface HitWithScore {
    hit: SearchResult
    score: number
  }

  const scoreMap = new Map<string, HitWithScore>()

  // Score vector results by rank position
  vectorResults.forEach((result, index) => {
    const rrfScore = 1 / (k + index + 1)

    // Create search result from vector search result
    scoreMap.set(result.file_path + ':' + result.chunk_index, {
      hit: result,
      score: rrfScore,
    })
  })

  // Add keyword results by rank position
  keywordResults.forEach((hit, index) => {
    const rrfScore = 1 / (k + index + 1)
    const key = hit.payload.file_path + ':' + hit.payload.chunk_index

    const existing = scoreMap.get(key)

    if (existing) {
      // Combine scores (appears in both result sets)
      existing.score += rrfScore
    } else {
      // Add new result (only in keyword results)
      scoreMap.set(key, {
        hit: {
          text: hit.payload.original_text,
          file_path: hit.payload.file_path,
          chunk_index: hit.payload.chunk_index,
          score: 0, // No vector score
          created_at: hit.payload.created_at,
          qntm_key: hit.payload.qntm_keys[0] || 'unknown',
        },
        score: rrfScore,
      })
    }
  })

  // 4. Sort by combined RRF score and return top-k
  const hybridResults = Array.from(scoreMap.values())
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(({ hit, score }) => ({
      ...hit,
      // Store RRF score in rerank_score field for display
      rerank_score: score,
    }))

  log.info('Hybrid search complete', {
    vectorResults: vectorResults.length,
    keywordResults: keywordResults.length,
    hybridResults: hybridResults.length,
  })

  endTimer()
  return hybridResults
}

/**
 * Update access tracking for retrieved chunks
 * Increments access_count and sets last_accessed_at
 * Follows supersession chains to credit the current version
 */
async function updateAccessTracking(pointIds: string[]): Promise<void> {
  if (pointIds.length === 0) return

  const storageBackend = getStorageBackend()
  if (!storageBackend) {
    log.warn('No storage backend available for access tracking')
    return
  }

  const now = new Date().toISOString()

  try {
    // Retrieve points to check for supersession
    const points = await storageBackend.retrieve(getPrimaryCollectionName(), pointIds)

    // Build map of target IDs (follow supersession chains)
    const targetUpdates = new Map<string, number>()

    for (const point of points) {
      const payload = point.payload as ChunkPayload
      let targetId = point.id
      let targetPayload = payload

      // Follow supersession chain to current version
      while (targetPayload.superseded_by) {
        try {
          const successor = await storageBackend.retrieve(getPrimaryCollectionName(), [
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
      const target = await storageBackend.retrieve(getPrimaryCollectionName(), [targetId])
      if (target.length === 0) continue

      const currentPayload = target[0]!.payload as ChunkPayload
      await storageBackend.setPayload(getPrimaryCollectionName(), [targetId], {
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
export async function search(options: SearchParams): Promise<SearchResult[]> {
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
    // Route to hybrid search if enabled
    if (options.hybridSearch) {
      log.info('Routing to hybrid search (vector + keyword with RRF)')
      const results = await hybridSearch(options.query, options)

      // Emit search.completed event
      options.emit?.({
        type: 'search.completed',
        data: {
          results: results.length,
          took: Date.now() - startTime,
          reranked: false, // Hybrid search uses RRF, not reranking
        },
      })

      endTimer()
      return results
    }

    // Get backends from registries
    const embeddingBackend = getEmbeddingBackend('text-embedding')
    if (!embeddingBackend) {
      throw new Error('No text embedding backend available')
    }

    const storageBackend = getStorageBackend()
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
      // Note: No need to filter superseded_by - chunks without the field are implicitly not superseded
      // (Qdrant's is_null only matches when field exists with null value, not when field is absent)
      must: [], // Initialize empty array for dynamic filters below
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

    // Add content type filter
    if (options.contentType) {
      filter.must = filter.must || []
      filter.must.push({
        key: 'content_type',
        match: { value: options.contentType },
      })
    }

    // Add agent role filter
    if (options.agentRole) {
      filter.must = filter.must || []
      filter.must.push({
        key: 'agent_role',
        match: { value: options.agentRole },
      })
    }

    // Add temperature filter
    if (options.temperature) {
      filter.must = filter.must || []
      filter.must.push({
        key: 'temperature',
        match: { value: options.temperature },
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
      collection: getPrimaryCollectionName(),
      vectorName: 'text',
      vectorDim: queryVector.length,
      limit,
      hasFilter:
        Object.keys(filter.must_not || []).length > 0 || Object.keys(filter.must || []).length > 0,
      backend: storageBackend.name,
    })

    let results: Array<
      import('../../services/storage').SearchResult<ChunkPayload> & { rerank_score?: number }
    > = await storageBackend.search(getPrimaryCollectionName(), {
      vectorName: 'text', // Phase 2: Default to text vector
      vector: queryVector,
      limit,
      filter:
        (filter.must_not && filter.must_not.length > 0) ||
        (filter.must && filter.must.length > 0) ||
        (filter.should && filter.should.length > 0)
          ? filter
          : undefined,
    })

    log.trace('Storage search response', {
      collection: getPrimaryCollectionName(),
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

  const storageBackend = getStorageBackend()
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
    collection: getPrimaryCollectionName(),
    filter,
    backend: storageBackend.name,
  })

  const results = await storageBackend.scroll(getPrimaryCollectionName(), {
    filter,
    limit,
  })

  log.trace('Storage scroll response', {
    collection: getPrimaryCollectionName(),
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
