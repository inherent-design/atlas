/**
 * Consolidate Edge Cases Tests
 *
 * Coverage:
 * - Error handling (missing points, consolidation failures)
 * - Edge cases (missing occurrences field)
 */

import {
  createMockChunkPayload,
  createMockQdrantPoint,
  createMockQdrantClient,
  createMockLLMService,
} from '../../shared/testHelpers'

import {
  resetConsolidateMocks,
  setupLevelFilteredScroll,
  setupSingleUseScroll,
} from './__tests__/helpers'

// Mock modules BEFORE importing the module under test
const mockQdrant = createMockQdrantClient()
const mockLLM = createMockLLMService()

vi.mock('../../services/storage', () => ({
  getStorageBackend: () => ({
    name: 'qdrant',
    scroll: mockQdrant.scroll,
    search: mockQdrant.search,
    retrieve: mockQdrant.retrieve,
    setPayload: mockQdrant.setPayload,
  }),
}))

vi.mock('../../services/llm', () => ({
  completeJSON: mockLLM.completeJSON,
  getLLMBackendFor: mockLLM.getLLMBackendFor,
}))

vi.mock('../../services/embedding', () => ({
  getEmbeddingBackend: () => ({
    name: 'voyage',
    dimensions: 1024,
    capabilities: new Set(['text-embedding']),
  }),
  getEmbeddingDimensions: () => 1024,
}))

vi.mock('../../shared/utils', async (importOriginal) => {
  const actual = (await importOriginal()) as Record<string, any>
  return {
    ...actual,
    requireCollection: vi.fn(() => Promise.resolve()),
  }
})

// Then import
const { consolidate } = await import('./index')
const { requireCollection } = await import('../../shared/utils')
const { registerPrompts } = await import('../../prompts/variants')

describe('domain/consolidate - Edge Cases', () => {
  beforeEach(() => {
    // Register prompts before each test (prompts registry is needed for consolidation)
    registerPrompts()
    resetConsolidateMocks(mockQdrant, mockLLM, requireCollection)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  // ============================================
  // Error Handling
  // ============================================

  test('should handle missing points gracefully', async () => {
    const point1 = createMockQdrantPoint({ id: 'chunk-1' })

    mockQdrant.scroll.mockResolvedValue({
      points: [point1],
      nextOffset: null,
    })

    mockQdrant.search.mockResolvedValue([
      { id: 'chunk-2', score: 0.95, payload: createMockChunkPayload() },
    ])

    // Retrieve returns only 1 point (chunk-2 missing)
    mockQdrant.retrieve.mockResolvedValue([point1])

    const result = await consolidate({ threshold: 0.92 })

    expect(result.consolidated).toBe(0) // Skipped
    expect(mockQdrant.setPayload).not.toHaveBeenCalled()
  })

  test('should handle consolidation errors gracefully', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({ consolidation_level: 0 }),
    })
    const point2 = createMockQdrantPoint({
      id: 'chunk-2',
      payload: createMockChunkPayload({ consolidation_level: 0 }),
    })

    setupSingleUseScroll(mockQdrant, 0, [point1])
    mockQdrant.search.mockResolvedValue([{ id: point2.id, score: 0.95, payload: point2.payload }])
    mockQdrant.retrieve.mockResolvedValue([point1, point2])
    mockLLM.completeJSON.mockResolvedValue({
      type: 'duplicate_work',
      direction: 'unknown',
      reasoning: 'Test',
      keep: 'first',
    })

    // setPayload fails
    mockQdrant.setPayload.mockRejectedValue(new Error('Qdrant error'))

    const result = await consolidate({ threshold: 0.92 })

    // Should continue gracefully
    expect(result.consolidated).toBe(0) // Failed to consolidate
    expect(result.candidatesFound).toBe(1) // But found candidates
  })

  // ============================================
  // Edge Cases
  // ============================================

  test('should handle points with no existing occurrences', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({
        created_at: '2025-12-29T10:00:00Z',
        consolidation_level: 0,
      }), // No occurrences field
    })

    const point2 = createMockQdrantPoint({
      id: 'chunk-2',
      payload: createMockChunkPayload({
        created_at: '2025-12-30T10:00:00Z',
        consolidation_level: 0,
      }), // No occurrences field
    })

    setupSingleUseScroll(mockQdrant, 0, [point1])
    mockQdrant.search.mockResolvedValue([{ id: point2.id, score: 0.95, payload: point2.payload }])
    mockQdrant.retrieve.mockResolvedValue([point1, point2])
    mockLLM.completeJSON.mockResolvedValue({
      type: 'duplicate_work',
      direction: 'unknown',
      reasoning: 'Default occurrences',
      keep: 'first',
    })

    await consolidate({ threshold: 0.92 })

    const calls = mockQdrant.setPayload.mock.calls
    const primaryUpdate = calls.find((call: any) => call[2].consolidation_level !== undefined)
    const updatedPayload = primaryUpdate[2]

    expect(updatedPayload.occurrences).toHaveLength(2) // 2 timestamps (created_at from both chunks)
  })
})
