/**
 * Consolidate Validation Tests
 *
 * Coverage:
 * - Collection existence validation
 * - Configuration defaults and custom values
 * - Dry-run mode
 * - Result structure validation
 */

import {
  createMockChunkPayload,
  createMockQdrantPoint,
  createMockQdrantClient,
  createMockLLMService,
} from '../../shared/testHelpers'

import { resetConsolidateMocks, setupLevelFilteredScroll } from './__tests__/helpers'

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

describe('domain/consolidate - Validation', () => {
  beforeEach(() => {
    resetConsolidateMocks(mockQdrant, mockLLM, requireCollection)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  // ============================================
  // Collection Validation
  // ============================================

  test('should throw when collection missing', async () => {
    ;(requireCollection as any).mockImplementation(() => {
      throw new Error('Collection atlas_1024 does not exist')
    })

    await expect(consolidate({ threshold: 0.92 })).rejects.toThrow(
      'Collection atlas_1024 does not exist'
    )
  })

  // ============================================
  // Configuration
  // ============================================

  test('should use default config values', async () => {
    mockQdrant.scroll.mockResolvedValue({
      points: [],
      nextOffset: null,
    })

    await consolidate({})

    expect(mockQdrant.scroll).toHaveBeenCalled()
    // Verify defaults by checking that no errors occur
  })

  test('should respect custom threshold', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({ consolidation_level: 0 }),
    })

    mockQdrant.scroll.mockResolvedValue({
      points: [point1],
      nextOffset: null,
    })

    mockQdrant.search.mockResolvedValue([])

    await consolidate({ threshold: 0.95 })

    // Verify search was called with custom threshold
    expect(mockQdrant.search).toHaveBeenCalledWith(
      'atlas_1024',
      expect.objectContaining({ scoreThreshold: 0.95 })
    )
  })

  // ============================================
  // Dry-Run Mode
  // ============================================

  test('should return candidates in dry-run mode without modifying', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({ consolidation_level: 0 }),
    })

    setupLevelFilteredScroll(mockQdrant, 0, [point1])
    mockQdrant.search.mockResolvedValue([
      {
        id: 'chunk-2',
        score: 0.95,
        payload: createMockChunkPayload({ consolidation_level: 0 }),
      },
    ])

    const result = await consolidate({ dryRun: true, threshold: 0.92 })

    expect(result.candidatesFound).toBe(1)
    expect(result.consolidated).toBe(0)
    expect(result.deleted).toBe(0)
    expect(result.candidates).toBeDefined()
    expect(result.candidates!.length).toBe(1)
    expect(mockQdrant.setPayload).not.toHaveBeenCalled()
  })

  // ============================================
  // Result Structure
  // ============================================

  test('should return correct result structure', async () => {
    const point1 = createMockQdrantPoint({ id: 'chunk-1' })
    const point2 = createMockQdrantPoint({ id: 'chunk-2' })
    const point3 = createMockQdrantPoint({ id: 'chunk-3' })

    mockQdrant.scroll.mockResolvedValue({
      points: [point1],
      nextOffset: null,
    })

    // Return 2 similar chunks
    mockQdrant.search.mockResolvedValue([
      { id: point2.id, score: 0.95, payload: point2.payload },
      { id: point3.id, score: 0.93, payload: point3.payload },
    ])

    mockQdrant.retrieve.mockResolvedValue([point1, point2])

    mockLLM.completeJSON.mockResolvedValue({
      type: 'duplicate_work',
      direction: 'unknown',
      reasoning: 'Test',
      keep: 'first',
    })

    const result = await consolidate({ threshold: 0.92 })

    expect(result).toHaveProperty('candidatesFound')
    expect(result).toHaveProperty('consolidated')
    expect(result).toHaveProperty('deleted')
    expect(result.candidatesFound).toBeGreaterThan(0)
    expect(typeof result.consolidated).toBe('number')
    expect(typeof result.deleted).toBe('number')
  })
})
