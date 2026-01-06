/**
 * Integration tests for Atlas search
 */

import type { SearchResult } from '../../shared/types'

// Use vi.hoisted() to define mocks that will be available when vi.mock() factories run
const { mockVoyageEmbed, mockQdrantSearch, mockQdrantScroll } = vi.hoisted(() => ({
  mockVoyageEmbed: vi.fn((input: any) => {
    // Return one embedding per input
    const chunks = Array.isArray(input.input) ? input.input : [input.input]
    return Promise.resolve({
      data: chunks.map(() => ({
        embedding: new Array(1024).fill(0.1),
      })),
    })
  }),
  mockQdrantSearch: vi.fn(() =>
    Promise.resolve([
      {
        id: 'chunk1',
        score: 0.95,
        payload: {
          original_text: 'This is about memory consolidation patterns in neural networks.',
          file_path: 'docs/memory.md',
          chunk_index: 0,
          created_at: '2025-12-25T10:00:00Z',
          qntm_keys: ['@memory ~ consolidation', '@neural ~ patterns'],
        },
      },
      {
        id: 'chunk2',
        score: 0.87,
        payload: {
          original_text: 'Sleep patterns enable episodic to semantic transformation.',
          file_path: 'docs/sleep.md',
          chunk_index: 1,
          created_at: '2025-12-26T11:00:00Z',
          qntm_keys: ['@sleep ~ patterns', '@episodic ~ semantic'],
        },
      },
    ])
  ),
  mockQdrantScroll: vi.fn(() =>
    Promise.resolve({
      points: [
        {
          id: 'chunk1',
          payload: {
            original_text: 'First document chronologically.',
            file_path: 'docs/first.md',
            chunk_index: 0,
            created_at: '2025-12-01T00:00:00Z',
            qntm_keys: ['@first ~ doc'],
          },
        },
        {
          id: 'chunk2',
          payload: {
            original_text: 'Second document chronologically.',
            file_path: 'docs/second.md',
            chunk_index: 0,
            created_at: '2025-12-02T00:00:00Z',
            qntm_keys: ['@second ~ doc'],
          },
        },
      ],
    })
  ),
}))

// Setup mocks - hoisted but now have access to hoisted mock functions
vi.mock('../../services/embedding', () => ({
  getVoyageClient: () => ({
    embed: mockVoyageEmbed,
  }),
  getEmbeddingBackend: () => ({
    name: 'voyage:text',
    embedText: async (input: string | string[]) => {
      const inputs = Array.isArray(input) ? input : [input]
      return {
        embeddings: inputs.map(() => new Array(1024).fill(0.1)),
        model: 'voyage-3-large',
        strategy: 'snippet' as const,
        dimensions: 1024,
        usage: { inputTokens: inputs.length * 10 },
      }
    },
  }),
}))

vi.mock('../../services/storage', () => ({
  getStorageBackend: () => ({
    name: 'qdrant',
    search: mockQdrantSearch,
    scroll: mockQdrantScroll,
    retrieve: vi.fn(() => Promise.resolve([])),
    setPayload: vi.fn(() => Promise.resolve()),
  }),
}))

// Import after mocks
import { formatResults, search, timeline } from '.'

describe('search', () => {
  beforeEach(() => {
    mockVoyageEmbed.mockClear()
    mockQdrantSearch.mockClear()
  })

  test('performs basic semantic search', async () => {
    const results = await search({
      query: 'memory consolidation',
      limit: 5,
    })

    // Should have called backend.search
    expect(mockQdrantSearch).toHaveBeenCalled()

    // Should return formatted results
    expect(results).toHaveLength(2)
    expect(results[0]?.text).toContain('memory consolidation')
    expect(results[0]?.score).toBe(0.95)
  })

  test('applies limit parameter', async () => {
    await search({
      query: 'test query',
      limit: 10,
    })

    const searchCall = (mockQdrantSearch.mock.calls as any[][])[0]
    expect(searchCall).toBeDefined()
    expect(searchCall![1].limit).toBe(10)
  })

  test('filters by temporal constraint (since)', async () => {
    await search({
      query: 'test query',
      since: '2025-12-01T00:00:00Z',
    })

    const searchCall = (mockQdrantSearch.mock.calls as any[][])[0]
    expect(searchCall).toBeDefined()
    const filter = searchCall![1].filter

    expect(filter).toBeDefined()
    expect(filter!.must).toBeDefined()
    // Find the temporal filter (not positional - default filters may exist)
    const temporalFilter = filter!.must!.find((f: any) => f.key === 'created_at')
    expect(temporalFilter).toBeDefined()
    expect(temporalFilter.range.gte).toBe('2025-12-01T00:00:00Z')
  })

  test('filters by QNTM key', async () => {
    await search({
      query: 'test query',
      qntmKey: 'atlas_specific',
    })

    const searchCall = (mockQdrantSearch.mock.calls as any[][])[0]
    expect(searchCall).toBeDefined()
    const filter = searchCall![1].filter

    expect(filter).toBeDefined()
    expect(filter!.must).toBeDefined()
    const qntmFilter = filter!.must!.find((f: any) => f.key === 'qntm_keys')
    expect(qntmFilter).toBeDefined()
    expect(qntmFilter.match.any).toEqual(['atlas_specific'])
  })

  test('combines semantic and temporal filtering', async () => {
    await search({
      query: 'test query',
      since: '2025-12-01T00:00:00Z',
      qntmKey: 'atlas_specific',
    })

    const searchCall = (mockQdrantSearch.mock.calls as any[][])[0]
    expect(searchCall).toBeDefined()
    const filter = searchCall![1].filter

    // Should have temporal + qntm filters (plus default is_null filter)
    const temporalFilter = filter!.must!.find((f: any) => f.key === 'created_at')
    const qntmFilter = filter!.must!.find((f: any) => f.key === 'qntm_keys')
    expect(temporalFilter).toBeDefined()
    expect(qntmFilter).toBeDefined()
  })

  test('calls backend search with correct parameters', async () => {
    await search({ query: 'test' })

    const searchCall = (mockQdrantSearch.mock.calls as any[][])[0]
    expect(searchCall).toBeDefined()
    const params = searchCall![1]

    expect(params.vector).toHaveLength(1024)
    expect(params.limit).toBeGreaterThan(0)
  })

  test('returns results with correct structure', async () => {
    const results = await search({ query: 'test' })

    results.forEach((result) => {
      expect(result).toHaveProperty('text')
      expect(result).toHaveProperty('file_path')
      expect(result).toHaveProperty('chunk_index')
      expect(result).toHaveProperty('score')
      expect(result).toHaveProperty('created_at')
      expect(result).toHaveProperty('qntm_key')
    })
  })
})

describe('timeline', () => {
  beforeEach(() => {
    mockQdrantScroll.mockClear()
  })

  test('retrieves chronological timeline', async () => {
    const results = await timeline('2025-12-01T00:00:00Z', 20)

    // Should have called backend.scroll
    expect(mockQdrantScroll).toHaveBeenCalled()

    const scrollCall = (mockQdrantScroll.mock.calls as any[][])[0]
    expect(scrollCall).toBeDefined()

    // Should have temporal filter
    expect((scrollCall![1] as any).filter!.must![0].key).toBe('created_at')
    expect((scrollCall![1] as any).filter!.must![0].range.gte).toBe('2025-12-01T00:00:00Z')

    // Should return results
    expect(results).toHaveLength(2)
  })

  test('applies limit parameter', async () => {
    await timeline('2025-12-01T00:00:00Z', 10)

    const scrollCall = (mockQdrantScroll.mock.calls as any[][])[0]
    expect(scrollCall).toBeDefined()
    expect(scrollCall![1].limit).toBe(10)
  })

  test('returns results with score 1.0 (no similarity)', async () => {
    const results = await timeline('2025-12-01T00:00:00Z')

    results.forEach((result) => {
      expect(result.score).toBe(1.0)
    })
  })

  test('preserves chronological order', async () => {
    const results = await timeline('2025-12-01T00:00:00Z')

    // Results should be in order (assuming mock returns them ordered)
    const date1 = new Date(results[0]!.created_at).getTime()
    const date2 = new Date(results[1]!.created_at).getTime()
    expect(date1).toBeLessThan(date2)
  })
})

describe('formatResults', () => {
  const mockResults: SearchResult[] = [
    {
      text: 'This is the content of the first result.',
      file_path: 'docs/test.md',
      chunk_index: 0,
      score: 0.95,
      created_at: '2025-12-25T10:00:00Z',
      qntm_key: '@memory ~ consolidation',
    },
    {
      text: 'This is the content of the second result.',
      file_path: 'docs/another.md',
      chunk_index: 1,
      score: 0.87,
      created_at: '2025-12-26T11:00:00Z',
      qntm_key: '@sleep ~ patterns',
    },
  ]

  test('formats results with headers and metadata', () => {
    const formatted = formatResults(mockResults)

    expect(formatted).toContain('[1] docs/test.md')
    expect(formatted).toContain('Score: 0.950')
    expect(formatted).toContain('QNTM: @memory ~ consolidation')
    expect(formatted).toContain('Created: 2025-12-25T10:00:00Z')
    expect(formatted).toContain('first result')
  })

  test('includes all results', () => {
    const formatted = formatResults(mockResults)

    expect(formatted).toContain('[1]')
    expect(formatted).toContain('[2]')
    expect(formatted).toContain('docs/test.md')
    expect(formatted).toContain('docs/another.md')
  })

  test('handles empty results', () => {
    const formatted = formatResults([])

    expect(formatted).toBe('No results found.')
  })

  test('includes divider lines', () => {
    const formatted = formatResults(mockResults)

    // Should have dividers (80 dashes)
    expect(formatted).toContain('─'.repeat(80))
  })

  test('formats scores with 3 decimal places', () => {
    const formatted = formatResults(mockResults)

    expect(formatted).toContain('Score: 0.950')
    expect(formatted).toContain('Score: 0.870')
  })

  test('preserves original text content', () => {
    const formatted = formatResults(mockResults)

    expect(formatted).toContain('This is the content of the first result.')
    expect(formatted).toContain('This is the content of the second result.')
  })
})
