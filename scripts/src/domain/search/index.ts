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

import { getVoyageClient } from '../../services/embedding'
import { getQdrantClient } from '../../services/storage'
import {
  QDRANT_COLLECTION_NAME,
  VOYAGE_MODEL,
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
 */
async function updateAccessTracking(pointIds: string[]): Promise<void> {
  if (pointIds.length === 0) return

  const qdrant = getQdrantClient()
  const now = new Date().toISOString()

  try {
    // Fetch current access counts
    const points = await qdrant.retrieve(QDRANT_COLLECTION_NAME, {
      ids: pointIds,
      with_payload: true,
      with_vector: false,
    })

    // Update each point with incremented access count
    for (const point of points) {
      const payload = point.payload as ChunkPayload
      const currentCount = payload.access_count ?? 0

      await qdrant.setPayload(QDRANT_COLLECTION_NAME, {
        payload: {
          access_count: currentCount + 1,
          last_accessed_at: now,
        },
        points: [point.id as string],
      })
    }

    log.debug('Updated access tracking', {
      pointCount: pointIds.length,
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
  const voyage = getVoyageClient()
  const qdrant = getQdrantClient()

  const { query, limit = DEFAULT_SEARCH_LIMIT, since, qntmKey } = options

  log.debug('Starting search', { query, limit, since, qntmKey })

  // Embed query using Voyage
  const embedStart = startTimer('embed query')

  log.trace('Voyage embed request', { query, model: VOYAGE_MODEL })

  const embedding = await voyage.embed({
    input: query,
    model: VOYAGE_MODEL,
  })

  log.trace('Voyage embed response', {
    dataLength: embedding.data?.length,
    embeddingDim: embedding.data?.[0]?.embedding?.length,
    usage: embedding.usage,
  })

  embedStart()

  // Safety check for embedding
  const queryVector = embedding.data?.[0]?.embedding
  if (!queryVector) {
    throw new Error('Failed to generate query embedding')
  }

  // Build Qdrant filter for temporal/semantic constraints
  const filter: any = {
    // Always exclude deleted and superseded chunks
    must_not: [
      { key: 'deletion_eligible', match: { value: true } },
      { key: 'superseded_by', match: { except: [null] } }, // Exclude if superseded_by is set
    ],
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

  // Search with HNSW + rescoring (from Step 3 config)
  const qdrantStart = startTimer('qdrant search')

  const searchParams = {
    vector: queryVector,
    limit,
    filter: Object.keys(filter).length > 0 ? filter : undefined,
    with_payload: true,
    with_vector: false,
    params: {
      quantization: {
        rescore: DEFAULT_QUANTIZATION_RESCORE,
        oversampling: DEFAULT_QUANTIZATION_OVERSAMPLING,
      },
      hnsw_ef: DEFAULT_HNSW_EF,
      exact: false,
    },
  }

  log.trace('Qdrant search request', {
    collection: QDRANT_COLLECTION_NAME,
    vectorDim: queryVector.length,
    limit,
    hasFilter: !!searchParams.filter,
    filter: searchParams.filter,
  })

  const results = await qdrant.search(QDRANT_COLLECTION_NAME, searchParams)

  log.trace('Qdrant search response', {
    collection: QDRANT_COLLECTION_NAME,
    resultCount: results.length,
    topScore: results[0]?.score,
  })

  qdrantStart()

  log.info('Search complete', { resultsFound: results.length })

  // Extract point IDs for access tracking
  const pointIds = results.map((hit: any) => hit.id as string)

  // Update access tracking (non-blocking, fire-and-forget)
  updateAccessTracking(pointIds).catch((err) => {
    log.warn('Access tracking update failed', { error: err.message })
  })

  // Format results
  const formatted = results.map((hit: any) => ({
    text: hit.payload.original_text,
    file_path: hit.payload.file_path,
    chunk_index: hit.payload.chunk_index,
    score: hit.score,
    created_at: hit.payload.created_at,
    qntm_key: hit.payload.qntm_keys[0] || 'unknown', // Use first key for display
  }))

  endTimer()
  return formatted
}

// Get chronological timeline (temporal-only query)
export async function timeline(since: string, limit = 20): Promise<SearchResult[]> {
  const endTimer = startTimer('timeline')
  const qdrant = getQdrantClient()

  log.debug('Fetching timeline', { since, limit })

  const scrollParams = {
    filter: {
      must: [
        {
          key: 'created_at',
          range: { gte: since },
        },
      ],
      // Exclude deleted and superseded chunks
      must_not: [
        { key: 'deletion_eligible', match: { value: true } },
        { key: 'superseded_by', match: { except: [null] } },
      ],
    },
    limit,
    with_payload: true,
    with_vector: false,
    order_by: {
      key: 'created_at',
      direction: 'asc' as const, // Chronological order
    },
  }

  log.trace('Qdrant scroll request', {
    collection: QDRANT_COLLECTION_NAME,
    params: scrollParams,
  })

  const results = await qdrant.scroll(QDRANT_COLLECTION_NAME, scrollParams)

  log.trace('Qdrant scroll response', {
    collection: QDRANT_COLLECTION_NAME,
    pointCount: results.points.length,
    nextPageOffset: results.next_page_offset,
  })

  log.info('Timeline complete', { pointsFound: results.points.length })

  const formatted = results.points.map((point: any) => ({
    text: point.payload.original_text,
    file_path: point.payload.file_path,
    chunk_index: point.payload.chunk_index,
    score: 1.0, // Timeline queries don't have similarity scores
    created_at: point.payload.created_at,
    qntm_key: point.payload.qntm_keys[0] || 'unknown', // Use first key for display
  }))

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
      const header = `[${i + 1}] ${result.file_path} (chunk ${result.chunk_index}) - Score: ${result.score.toFixed(3)}`
      const meta = `QNTM: ${result.qntm_key} | Created: ${result.created_at}`
      const divider = '─'.repeat(80)
      return `${header}\n${meta}\n${divider}\n${result.text}\n`
    })
    .join('\n')
}
