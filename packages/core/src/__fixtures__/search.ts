/**
 * Search-related fixtures for testing
 *
 * Provides SearchOptions and SearchResult fixtures.
 */

import type { SearchOptions, SearchResult } from '../shared/types'
import { CHUNKS } from './chunks'

/**
 * Create SearchOptions with sensible defaults
 *
 * @param overrides - Partial options to merge with defaults
 * @returns Complete SearchOptions
 */
export function createSearchOptions(overrides?: Partial<SearchOptions>): SearchOptions {
  return {
    query: 'test query',
    limit: 10,
    ...overrides,
  }
}

/**
 * Create a SearchResult from a ChunkPayload
 *
 * @param payload - Source chunk payload
 * @param score - Similarity score (0.0-1.0)
 * @param rerankScore - Optional rerank score
 * @returns SearchResult
 */
export function createSearchResult(
  payload: typeof CHUNKS[keyof typeof CHUNKS],
  score: number,
  rerankScore?: number
): SearchResult {
  return {
    text: payload.original_text,
    file_path: payload.file_path,
    chunk_index: payload.chunk_index,
    score,
    created_at: payload.created_at,
    qntm_key: payload.qntm_keys[0] || '',
    rerank_score: rerankScore,
  }
}

/**
 * Common search option presets
 */
export const SEARCH_OPTIONS = {
  /** Basic search */
  basic: createSearchOptions({
    query: 'memory consolidation',
    limit: 10,
  }),

  /** Search with temporal filter */
  temporal: createSearchOptions({
    query: 'recent changes',
    limit: 5,
    since: '2025-12-28T00:00:00Z',
  }),

  /** Search with QNTM key filter */
  filtered: createSearchOptions({
    query: 'architecture patterns',
    limit: 10,
    qntmKey: '@architecture ~ design',
  }),

  /** Search with reranking */
  reranked: createSearchOptions({
    query: 'consolidation algorithm',
    limit: 5,
    rerank: true,
    rerankTopK: 15,
  }),

  /** Search with query expansion */
  expanded: createSearchOptions({
    query: 'sleep memory',
    limit: 10,
    expandQuery: true,
  }),

  /** Search for raw chunks only */
  rawOnly: createSearchOptions({
    query: 'test content',
    limit: 10,
    consolidationLevel: 0,
  }),

  /** Search for topic summaries */
  topicSummaries: createSearchOptions({
    query: 'overview summary',
    limit: 5,
    consolidationLevel: 2,
  }),
} as const

/**
 * Common search results for testing
 */
export const SEARCH_RESULTS = {
  /** Memory-related result */
  memory: createSearchResult(CHUNKS.markdown, 0.92),

  /** Code-related result */
  code: createSearchResult(CHUNKS.typescript, 0.88),

  /** Consolidated result */
  consolidated: createSearchResult(CHUNKS.consolidated, 0.85),

  /** High importance result */
  important: createSearchResult(CHUNKS.important, 0.78),

  /** Topic summary result */
  topicSummary: createSearchResult(CHUNKS.topicSummary, 0.95),

  /** Reranked result (with rerank score) */
  reranked: createSearchResult(CHUNKS.markdown, 0.87, 0.94),
} as const

/**
 * Create a batch of search results with descending scores
 *
 * @param count - Number of results to generate
 * @param baseScore - Starting score (default: 0.95)
 * @param scoreDecrement - Amount to decrease each score (default: 0.05)
 * @returns Array of SearchResults
 */
export function createSearchResultBatch(
  count: number,
  baseScore = 0.95,
  scoreDecrement = 0.05
): SearchResult[] {
  const results: SearchResult[] = []

  for (let i = 0; i < count; i++) {
    const score = Math.max(0.1, baseScore - i * scoreDecrement)
    results.push({
      text: `Result ${i + 1}: Test content for search result testing.`,
      file_path: `/test/results/result-${i}.md`,
      chunk_index: i,
      score,
      created_at: new Date(Date.UTC(2025, 11, 30, 12, i)).toISOString(),
      qntm_key: `@test ~ result-${i}`,
    })
  }

  return results
}

/**
 * Mock search response with typical result distribution
 */
export const MOCK_SEARCH_RESPONSE = {
  results: [
    SEARCH_RESULTS.memory, // High relevance
    SEARCH_RESULTS.consolidated, // Medium-high relevance
    SEARCH_RESULTS.code, // Medium relevance
    SEARCH_RESULTS.important, // Lower relevance but high importance
    createSearchResult(CHUNKS.conversation, 0.72), // Low relevance
  ],
  query: 'memory consolidation',
  totalResults: 5,
}

/**
 * Empty search response (no results)
 */
export const EMPTY_SEARCH_RESPONSE = {
  results: [],
  query: 'nonexistent query that matches nothing',
  totalResults: 0,
}
