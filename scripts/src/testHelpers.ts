/**
 * Shared test utilities and mocks for Atlas tests
 */

import { mock } from 'bun:test'
import { mkdirSync, rmSync } from 'fs'

/**
 * Create mock functions for testing
 */
export function createTestMocks() {
  return {
    mockVoyageEmbed: mock((input: any) => {
      // Return one embedding per chunk
      const chunks = Array.isArray(input.input) ? input.input : [input.input]
      return Promise.resolve({
        data: chunks.map(() => ({
          embedding: new Array(1024).fill(0.1), // Mock 1024-dim embedding
        })),
      })
    }),
    mockQdrantGet: mock(() => Promise.reject(new Error('Collection not found'))),
    mockQdrantCreate: mock(() => Promise.resolve()),
    mockQdrantUpsert: mock(() => Promise.resolve({ status: 'acknowledged' })),
    mockQdrantSearch: mock(() => Promise.resolve([])),
    mockQdrantScroll: mock(() => Promise.resolve({ points: [] })),
    mockGenerateQNTMKeys: mock(() =>
      Promise.resolve({
        keys: ['@test ~ content', '@mock ~ data'],
        reasoning: 'Test content semantic keys',
      })
    ),
  }
}

/**
 * Setup mock modules for ingestion tests
 */
export async function setupIngestMocks(mocks: ReturnType<typeof createTestMocks>) {
  const {
    mockVoyageEmbed,
    mockQdrantGet,
    mockQdrantCreate,
    mockQdrantUpsert,
    mockGenerateQNTMKeys,
  } = mocks

  // Import real sanitizeQNTMKey to avoid mock conflicts across test files
  const { sanitizeQNTMKey: realSanitize } = await import('./qntm')

  mock.module('./clients', () => ({
    getVoyageClient: () => ({
      embed: mockVoyageEmbed,
    }),
    getQdrantClient: () => ({
      getCollection: mockQdrantGet,
      createCollection: mockQdrantCreate,
      upsert: mockQdrantUpsert,
    }),
    getTextSplitter: () => ({
      splitText: async (text: string) => {
        // Simple mock: split by paragraphs
        return text.split('\n\n').filter((chunk) => chunk.trim().length > 0)
      },
    }),
  }))

  mock.module('./qntm', () => ({
    generateQNTMKeys: mockGenerateQNTMKeys,
    sanitizeQNTMKey: realSanitize, // Use real implementation
    fetchExistingQNTMKeys: () => Promise.resolve([]),
  }))

  mock.module('./qntm/cache', () => ({
    getCachedQNTMKeys: () => [],
    cacheQNTMKeys: () => {},
  }))
}

/**
 * Setup mock modules for search tests
 */
export function setupSearchMocks(mocks: ReturnType<typeof createTestMocks>) {
  const { mockVoyageEmbed, mockQdrantSearch, mockQdrantScroll } = mocks

  mock.module('./clients', () => ({
    getVoyageClient: () => ({
      embed: mockVoyageEmbed,
    }),
    getQdrantClient: () => ({
      search: mockQdrantSearch,
      scroll: mockQdrantScroll,
    }),
  }))
}

/**
 * Test directory helpers
 */
export function setupTestDir(dirPath: string) {
  rmSync(dirPath, { recursive: true, force: true })
  mkdirSync(dirPath, { recursive: true })
}

export function cleanupTestDir(dirPath: string) {
  rmSync(dirPath, { recursive: true, force: true })
}

/**
 * Reset all mocks in the collection
 */
export function resetMocks(mocks: ReturnType<typeof createTestMocks>) {
  Object.values(mocks).forEach((mockFn) => {
    if (mockFn && typeof mockFn.mockClear === 'function') {
      mockFn.mockClear()
    }
  })
}

/**
 * Default mock payloads for testing
 */
export const mockSearchPayloads = {
  memoryChunk: {
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
  sleepChunk: {
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
}
