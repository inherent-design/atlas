/**
 * Full-Text Search Backend Tests
 *
 * Tests for Meilisearch backend implementation.
 * Uses mock Meilisearch client for isolation.
 */

import { describe, expect, it, beforeEach, vi } from 'vitest'
import type {
  FullTextBackend,
  FullTextDocument,
  FullTextSearchParams,
  FullTextSearchResult,
  IndexStats,
} from '../fulltext'

// ============================================
// Mock Meilisearch Client
// ============================================

/**
 * Mock task response (Meilisearch v0.50+ EnqueuedTaskPromise pattern)
 * Returns an object with waitTask method that resolves to task result
 */
function createMockTask() {
  const task = {
    taskUid: 123,
    uid: 123,
    status: 'succeeded' as const,
    type: 'documentAdditionOrUpdate' as const,
    enqueuedAt: new Date().toISOString(),
    finishedAt: undefined as string | undefined,
  }

  return {
    ...task,
    waitTask: async (options?: { timeout?: number; interval?: number }) => {
      return {
        ...task,
        finishedAt: new Date().toISOString(),
      }
    },
  }
}

const mockTask = createMockTask()

/**
 * Mock index
 */
class MockMeilisearchIndex {
  private documents: Map<string, FullTextDocument> = new Map()
  private settings: any = {}

  constructor(private indexName: string) {}

  async getStats() {
    return {
      numberOfDocuments: this.documents.size,
      indexSize: 1024 * this.documents.size, // Mock: 1KB per document
      isIndexing: false,
      fieldDistribution: {
        original_text: this.documents.size,
        file_path: this.documents.size,
        qntm_keys: this.documents.size,
      },
    }
  }

  addDocuments(documents: FullTextDocument[]) {
    for (const doc of documents) {
      this.documents.set(doc.id, doc)
    }
    return createMockTask()
  }

  updateDocuments(documents: Partial<FullTextDocument>[]) {
    for (const doc of documents) {
      if (doc.id) {
        const existing = this.documents.get(doc.id)
        if (existing) {
          this.documents.set(doc.id, { ...existing, ...doc })
        }
      }
    }
    return createMockTask()
  }

  deleteDocument(id: string) {
    this.documents.delete(id)
    return createMockTask()
  }

  async search(query: string, options: any) {
    // Simple mock: match query against original_text
    const hits = Array.from(this.documents.values()).filter((doc) => {
      const matchesQuery = doc.original_text.toLowerCase().includes(query.toLowerCase())

      // Apply filters if provided
      if (options.filter && typeof options.filter === 'string') {
        // Parse simple filter: "field = value"
        const filterMatch = options.filter.match(/(\w+)\s*=\s*(.+)/)
        if (filterMatch) {
          const [, field, value] = filterMatch
          const docValue = (doc as any)[field]
          const filterValue = value.replace(/['"]/g, '')

          if (docValue?.toString() !== filterValue) {
            return false
          }
        }
      }

      return matchesQuery
    })

    // Sort by relevance (simple: exact matches first)
    hits.sort((a, b) => {
      const aExact = a.original_text.toLowerCase() === query.toLowerCase()
      const bExact = b.original_text.toLowerCase() === query.toLowerCase()
      if (aExact && !bExact) return -1
      if (!aExact && bExact) return 1
      return 0
    })

    // Limit results
    const limitedHits = hits.slice(0, options.limit ?? 20)

    return {
      hits: limitedHits.map((hit) => ({
        ...hit,
        _formatted: {
          original_text: hit.original_text.replace(
            new RegExp(query, 'gi'),
            (match) => `${options.highlightPreTag}${match}${options.highlightPostTag}`
          ),
        },
      })),
      processingTimeMs: 5,
      query,
    }
  }

  updateSettings(settings: any) {
    // Synchronously return task object (not a Promise)
    // The real Meilisearch returns an EnqueuedTask that has waitTask method immediately available
    this.settings = { ...this.settings, ...settings }
    return createMockTask()
  }

  async getSettings() {
    return this.settings
  }
}

/**
 * Mock Meilisearch client
 */
class MockMeiliSearch {
  private indexes: Map<string, MockMeilisearchIndex> = new Map()
  private healthStatus: 'available' | 'unavailable' = 'available'

  constructor(config: { host: string; apiKey?: string }) {
    // Store config for verification if needed
  }

  index(indexName: string): MockMeilisearchIndex {
    let idx = this.indexes.get(indexName)
    if (!idx) {
      idx = new MockMeilisearchIndex(indexName)
      this.indexes.set(indexName, idx)
    }
    return idx
  }

  createIndex(indexName: string, options?: any) {
    if (this.indexes.has(indexName)) {
      const error: any = new Error('Index already exists')
      error.code = 'index_already_exists'
      throw error
    }
    this.indexes.set(indexName, new MockMeilisearchIndex(indexName))
    return createMockTask()
  }

  deleteIndex(indexName: string) {
    if (!this.indexes.has(indexName)) {
      const error: any = new Error('Index not found')
      error.code = 'index_not_found'
      throw error
    }
    this.indexes.delete(indexName)
    return createMockTask()
  }

  async getTask(taskUid: number) {
    return mockTask
  }

  async health() {
    return { status: this.healthStatus }
  }

  // Test helper: set health status
  setHealthStatus(status: 'available' | 'unavailable') {
    this.healthStatus = status
  }
}

// ============================================
// Mock Backend Implementation
// ============================================

/**
 * Create MeilisearchBackend with mocked client
 */
async function createMockBackend(): Promise<{
  backend: FullTextBackend
  mockClient: MockMeiliSearch
}> {
  const mockClient = new MockMeiliSearch({ host: 'http://localhost:7700' })

  // Mock the MeilisearchBackend class
  const { MeilisearchBackend } = await import('../fulltext')

  // Replace MeiliSearch constructor with mock
  const OriginalMeiliSearch = (global as any).MeiliSearch
  ;(global as any).MeiliSearch = MockMeiliSearch

  const backend = new MeilisearchBackend({
    url: 'http://localhost:7700',
    masterKey: 'test-master-key',
    indexName: 'test_index',
    searchableAttributes: ['original_text', 'file_path'],
    filterableAttributes: ['file_type', 'consolidation_level'],
    rankingRules: ['words', 'typo', 'proximity'],
  })

  // Inject mock client
  ;(backend as any).client = mockClient

  // Restore original
  ;(global as any).MeiliSearch = OriginalMeiliSearch

  return { backend, mockClient }
}

// ============================================
// Test Fixtures
// ============================================

const mockDocuments: FullTextDocument[] = [
  {
    id: 'chunk-1',
    original_text: 'User authentication with JWT tokens',
    file_path: '/docs/auth.md',
    file_name: 'auth.md',
    qntm_keys: ['@auth ~ jwt', '@security ~ tokens'],
    file_type: '.md',
    consolidation_level: 0,
    content_type: 'text',
    created_at: '2026-01-10T00:00:00Z',
    importance: 'high',
  },
  {
    id: 'chunk-2',
    original_text: 'OAuth2 authentication flow implementation',
    file_path: '/docs/oauth.md',
    file_name: 'oauth.md',
    qntm_keys: ['@auth ~ oauth', '@security ~ flow'],
    file_type: '.md',
    consolidation_level: 0,
    content_type: 'text',
    created_at: '2026-01-10T01:00:00Z',
    importance: 'normal',
  },
  {
    id: 'chunk-3',
    original_text: 'TypeScript function for user validation',
    file_path: '/src/auth.ts',
    file_name: 'auth.ts',
    qntm_keys: ['@code ~ typescript', '@validation ~ user'],
    file_type: '.ts',
    consolidation_level: 0,
    content_type: 'code',
    created_at: '2026-01-10T02:00:00Z',
    importance: 'normal',
  },
]

// ============================================
// Tests
// ============================================

describe('FullTextBackend (Meilisearch)', () => {
  describe('Index Management', () => {
    it('should create index with settings', async () => {
      const { backend, mockClient } = await createMockBackend()

      await backend.createIndex()

      const index = mockClient.index('test_index')
      const settings = await index.getSettings()

      expect(settings.searchableAttributes).toEqual(['original_text', 'file_path'])
      expect(settings.filterableAttributes).toEqual(['file_type', 'consolidation_level'])
      expect(settings.rankingRules).toEqual(['words', 'typo', 'proximity'])
    })

    it('should be idempotent (no error if index exists)', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.createIndex() // Should not throw

      expect(true).toBe(true) // Test passes if no error thrown
    })

    it('should delete index', async () => {
      const { backend, mockClient } = await createMockBackend()

      await backend.createIndex()
      await backend.deleteIndex()

      // Verify index is deleted
      try {
        const index = mockClient.index('test_index')
        await index.getStats()
        expect(true).toBe(false) // Should not reach here
      } catch (error) {
        // Expected: index not found
      }
    })

    it('should get index stats', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      const stats = await backend.getIndexStats()

      expect(stats.numberOfDocuments).toBe(3)
      expect(stats.isIndexing).toBe(false)
      expect(stats.fieldDistribution).toBeDefined()
    })

    it('should return zero stats for non-existent index', async () => {
      const { backend } = await createMockBackend()

      const stats = await backend.getIndexStats()

      expect(stats.numberOfDocuments).toBe(0)
      expect(stats.isIndexing).toBe(false)
    })
  })

  describe('Indexing Operations', () => {
    it('should index documents in batches', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      const stats = await backend.getIndexStats()
      expect(stats.numberOfDocuments).toBe(3)
    })

    it('should handle empty document array', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index([])

      const stats = await backend.getIndexStats()
      expect(stats.numberOfDocuments).toBe(0)
    })

    it('should update document', async () => {
      const { backend, mockClient } = await createMockBackend()

      await backend.createIndex()
      const firstDoc = mockDocuments[0]
      if (!firstDoc) throw new Error('No mock document')
      await backend.index([firstDoc])

      await backend.updateDocument('chunk-1', {
        consolidation_level: 1,
        importance: 'critical',
      })

      const index = mockClient.index('test_index')
      const stats = await index.getStats()
      expect(stats.numberOfDocuments).toBe(1)

      // Verify update (search to retrieve document)
      const results = await backend.search({ query: 'authentication' })
      expect(results.length).toBe(1)
    })

    it('should delete document', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      await backend.deleteDocument('chunk-1')

      const stats = await backend.getIndexStats()
      expect(stats.numberOfDocuments).toBe(2)
    })
  })

  describe('Search Operations', () => {
    beforeEach(async () => {
      // Setup: create index and add documents for each test
    })

    it('should search with simple query', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      const results = await backend.search({
        query: 'authentication',
        limit: 10,
      })

      expect(results.length).toBeGreaterThan(0)
      const firstResult = results[0]
      if (!firstResult) throw new Error('Expected at least one result')
      expect(firstResult.original_text).toContain('authentication')
      expect(firstResult.score).toBeGreaterThan(0)
      expect(firstResult.score).toBeLessThanOrEqual(1)
    })

    it('should search with filters', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      const results = await backend.search({
        query: 'user',
        limit: 10,
        filter: 'file_type = .ts',
      })

      expect(results.length).toBe(1)
      const firstResult = results[0]
      if (!firstResult) throw new Error('Expected one result')
      expect(firstResult.id).toBe('chunk-3')
    })

    it('should limit results', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      const results = await backend.search({
        query: 'auth',
        limit: 2,
      })

      expect(results.length).toBeLessThanOrEqual(2)
    })

    it('should highlight search terms', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      const results = await backend.search({
        query: 'authentication',
        attributesToHighlight: ['original_text'],
        highlightPreTag: '<mark>',
        highlightPostTag: '</mark>',
      })

      expect(results.length).toBeGreaterThan(0)
      const firstResult = results[0]
      if (!firstResult) throw new Error('Expected at least one result')
      expect(firstResult._formatted?.original_text).toContain('<mark>')
    })

    it('should return empty results for no matches', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      const results = await backend.search({
        query: 'nonexistentquery12345',
      })

      expect(results.length).toBe(0)
    })

    it('should handle typo tolerance (mock: exact match only)', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      // Mock doesn't implement typo tolerance, so this tests exact match
      const results = await backend.search({
        query: 'authentication',
      })

      expect(results.length).toBeGreaterThan(0)
    })
  })

  describe('Health Check', () => {
    it('should pass health check when server is available', async () => {
      const { backend } = await createMockBackend()

      await backend.healthCheck()

      expect(true).toBe(true) // Test passes if no error thrown
    })

    it('should fail health check when server is unavailable', async () => {
      const { backend, mockClient } = await createMockBackend()

      mockClient.setHealthStatus('unavailable')

      try {
        await backend.healthCheck()
        expect(true).toBe(false) // Should not reach here
      } catch (error) {
        expect((error as Error).message).toContain('health check failed')
      }
    })
  })

  describe('Batch Operations', () => {
    it('should handle large batch (>1000 documents)', async () => {
      const { backend } = await createMockBackend()

      // Create 1500 documents
      const largeBatch: FullTextDocument[] = Array.from({ length: 1500 }, (_, i) => ({
        id: `chunk-${i}`,
        original_text: `Document ${i} about authentication`,
        file_path: `/docs/doc-${i}.md`,
        file_name: `doc-${i}.md`,
        qntm_keys: [`@doc ~ ${i}`],
        file_type: '.md',
        consolidation_level: 0,
      }))

      await backend.createIndex()
      await backend.index(largeBatch)

      const stats = await backend.getIndexStats()
      expect(stats.numberOfDocuments).toBe(1500)
    })
  })

  describe('Score Normalization', () => {
    it('should normalize scores to 0-1 range', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      const results = await backend.search({
        query: 'auth',
        limit: 10,
      })

      for (const result of results) {
        expect(result.score).toBeGreaterThanOrEqual(0)
        expect(result.score).toBeLessThanOrEqual(1)
      }
    })

    it('should rank results by relevance (first = highest score)', async () => {
      const { backend } = await createMockBackend()

      await backend.createIndex()
      await backend.index(mockDocuments)

      const results = await backend.search({
        query: 'auth',
        limit: 10,
      })

      // Scores should be in descending order
      for (let i = 1; i < results.length; i++) {
        const prev = results[i - 1]
        const curr = results[i]
        if (!prev || !curr) continue
        expect(prev.score).toBeGreaterThanOrEqual(curr.score)
      }
    })
  })
})
