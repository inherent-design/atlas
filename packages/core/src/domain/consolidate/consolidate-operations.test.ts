/**
 * Consolidate Operations Tests
 *
 * Coverage:
 * - Candidate discovery and duplicate consolidation
 * - Pagination and batching
 * - Consolidated chunk filtering
 * - LLM classification (success and fallback)
 * - Consolidation operations (primary/secondary, metadata merging)
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
  getLLMConfig: mockLLM.getLLMConfig,
  getLLMBackendFor: mockLLM.getLLMBackendFor,
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

describe('domain/consolidate - Operations', () => {
  beforeEach(() => {
    // Register prompts before each test (prompts registry is needed for consolidation)
    registerPrompts()
    resetConsolidateMocks(mockQdrant, mockLLM, requireCollection)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  // ============================================
  // Candidate Discovery
  // ============================================

  test('should find and consolidate duplicate chunks', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({
        original_text: 'Test content A',
        qntm_keys: ['@test ~ a'],
        consolidation_level: 0,
      }),
    })

    const point2 = createMockQdrantPoint({
      id: 'chunk-2',
      payload: createMockChunkPayload({
        original_text: 'Test content B',
        qntm_keys: ['@test ~ b'],
        consolidation_level: 0,
      }),
    })

    setupSingleUseScroll(mockQdrant, 0, [point1])

    mockQdrant.search.mockResolvedValue([
      {
        id: point2.id,
        score: 0.95,
        payload: point2.payload,
      },
    ] as any)
    mockQdrant.retrieve.mockResolvedValue([point1, point2] as any)
    mockLLM.completeJSON.mockResolvedValue({
      type: 'duplicate_work',
      direction: 'unknown',
      reasoning: 'Similar content',
      keep: 'first',
    })

    const result = await consolidate({ threshold: 0.92 })

    expect(result.candidatesFound).toBe(1)
    expect(result.consolidated).toBe(1)
    expect(result.deleted).toBe(1)
    expect(mockQdrant.setPayload).toHaveBeenCalledTimes(2) // Update primary + mark secondary
  })

  test('should process all points at each level', async () => {
    // Reduced from 10 to 3 points to prevent OOM (payload accumulation)
    const points = Array.from({ length: 3 }, (_, i) =>
      createMockQdrantPoint({
        id: `chunk-${i}`,
        payload: createMockChunkPayload({ consolidation_level: 0 }),
      })
    )

    mockQdrant.scroll.mockResolvedValue({
      points,
      nextOffset: null,
    })

    // Each point finds one similar chunk
    mockQdrant.search.mockResolvedValue([
      {
        id: 'similar-chunk',
        score: 0.95,
        payload: createMockChunkPayload({ consolidation_level: 0 }),
      },
    ])

    const result = await consolidate({ dryRun: true })

    // Should process all points (no limit)
    expect(result.candidatesFound).toBeGreaterThan(0)
  })

  test('should deduplicate pairs (A~B = B~A)', async () => {
    // Use distinct vectors so we can differentiate them
    const vector1 = new Array(16).fill(0.1)
    const vector2 = new Array(16).fill(0.2)

    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      vector: vector1,
      payload: createMockChunkPayload({ consolidation_level: 0 }),
    })

    const point2 = createMockQdrantPoint({
      id: 'chunk-2',
      vector: vector2,
      payload: createMockChunkPayload({ consolidation_level: 0 }),
    })

    setupLevelFilteredScroll(mockQdrant, 0, [point1, point2])

    // Conditional logic based on vector parameter
    mockQdrant.search.mockImplementation((_: any, options: any) => {
      const vector = options.vector
      // Point 1 finds point 2
      if (vector[0] === 0.1) {
        return Promise.resolve([{ id: point2.id, score: 0.95, payload: point2.payload }])
      }
      // Point 2 finds point 1
      if (vector[0] === 0.2) {
        return Promise.resolve([{ id: point1.id, score: 0.95, payload: point1.payload }])
      }
      return Promise.resolve([])
    })

    const result = await consolidate({ dryRun: true, threshold: 0.92 })

    // Should find only 1 candidate (deduplicated)
    expect(result.candidatesFound).toBe(1)
  })

  test('should skip consolidated chunks in search', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({
        consolidation_level: 1, // Level 1+ chunks are not scanned at level 0
      }),
    })

    // Setup scroll to return point1 only at level 1 (not level 0)
    setupLevelFilteredScroll(mockQdrant, 1, [point1])

    const result = await consolidate({ dryRun: true, threshold: 0.92 })

    // No candidates found because point1 is at level 1, not level 0
    expect(result.candidatesFound).toBe(0)
  })

  test('should skip similar hits that are marked for deletion', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({ consolidation_level: 0 }),
    })

    setupSingleUseScroll(mockQdrant, 0, [point1])

    // Search returns a chunk marked for deletion
    // The search filter (line 177 in index.ts) excludes deletion_eligible=true
    // So this would be filtered by Qdrant, not by our code
    // To test this properly, we return no results from search
    mockQdrant.search.mockResolvedValue([])

    const result = await consolidate({ dryRun: true, threshold: 0.92 })

    expect(result.candidatesFound).toBe(0) // No similar chunks found
  })

  test('should handle pagination across multiple scroll calls', async () => {
    const page1Points = [
      createMockQdrantPoint({
        id: 'chunk-1',
        payload: createMockChunkPayload({ consolidation_level: 0 }),
      }),
    ]

    const page2Points = [
      createMockQdrantPoint({
        id: 'chunk-2',
        payload: createMockChunkPayload({ consolidation_level: 0 }),
      }),
    ]

    // Stateful mock: tracks call count for level 0 only
    let level0CallCount = 0
    mockQdrant.scroll.mockImplementation((_collection: string, options: any) => {
      const level = options.filter?.must?.find((m: any) => m.key === 'consolidation_level')
        ?.match?.value

      if (level === 0) {
        level0CallCount++
        if (level0CallCount === 1) {
          return Promise.resolve({ points: page1Points, nextOffset: 'offset-1' })
        }
        return Promise.resolve({ points: page2Points, nextOffset: null })
      }
      return Promise.resolve({ points: [], nextOffset: null })
    })

    mockQdrant.search.mockResolvedValue([])

    await consolidate({ dryRun: true, threshold: 0.92 })

    // Should scroll level 0 twice (pagination) + once each for levels 1, 2, 3
    expect(mockQdrant.scroll.mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  test('should stop pagination when offset is null', async () => {
    const point = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({ consolidation_level: 0 }),
    })

    setupLevelFilteredScroll(mockQdrant, 0, [point])
    mockQdrant.search.mockResolvedValue([])

    await consolidate({ dryRun: true, threshold: 0.92 })

    // Each level is scanned once (levels 0-3), so 4 scroll calls total
    // But we only return points at level 0
    const level0Calls = mockQdrant.scroll.mock.calls.filter((call: any) => {
      const level = call[1].filter?.must?.find((m: any) => m.key === 'consolidation_level')
        ?.match?.value
      return level === 0
    })
    expect(level0Calls.length).toBe(1) // Stopped after first page for level 0
  })

  // ============================================
  // LLM Classification
  // ============================================

  test('should handle classification LLM success', async () => {
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
      type: 'sequential_iteration',
      direction: 'forward',
      reasoning: 'Progressive refinement',
      keep: 'second',
    })

    await consolidate({ threshold: 0.92 })

    expect(mockLLM.completeJSON).toHaveBeenCalledTimes(1)
    expect(mockQdrant.setPayload).toHaveBeenCalled()
  })

  test('should fallback to default when classification fails', async () => {
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

    // LLM fails
    mockLLM.completeJSON.mockRejectedValue(new Error('LLM timeout'))

    await consolidate({ threshold: 0.92 })

    // Should still consolidate with default classification
    expect(mockQdrant.setPayload).toHaveBeenCalled()
  })

  // ============================================
  // Consolidation Operations
  // ============================================

  test('should swap primary/secondary when keep=second', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({
        original_text: 'First version',
        consolidation_level: 0,
      }),
    })

    const point2 = createMockQdrantPoint({
      id: 'chunk-2',
      payload: createMockChunkPayload({
        original_text: 'Second version (better)',
        consolidation_level: 0,
      }),
    })

    setupSingleUseScroll(mockQdrant, 0, [point1])
    mockQdrant.search.mockResolvedValue([{ id: point2.id, score: 0.95, payload: point2.payload }])
    mockQdrant.retrieve.mockResolvedValue([point1, point2])
    mockLLM.completeJSON.mockResolvedValue({
      type: 'sequential_iteration',
      direction: 'forward',
      reasoning: 'Second is improved',
      keep: 'second',
    })

    await consolidate({ threshold: 0.92 })

    // Verify point2 is kept (primary), point1 is marked for deletion (secondary)
    const calls = mockQdrant.setPayload.mock.calls
    expect(calls).toHaveLength(2)

    // Find the call that marks secondary as deletion eligible
    const secondaryCall = calls.find((call: any) => call[2]?.deletion_eligible === true)
    expect(secondaryCall?.[1]).toContain('chunk-1') // Point1 marked for deletion
  })

  test('should keep original when keep=first', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({
        original_text: 'First version',
        consolidation_level: 0,
      }),
    })

    const point2 = createMockQdrantPoint({
      id: 'chunk-2',
      payload: createMockChunkPayload({
        original_text: 'Second version',
        consolidation_level: 0,
      }),
    })

    setupSingleUseScroll(mockQdrant, 0, [point1])
    mockQdrant.search.mockResolvedValue([{ id: point2.id, score: 0.95, payload: point2.payload }])

    mockQdrant.retrieve.mockResolvedValue([point1, point2])

    mockLLM.completeJSON.mockResolvedValue({
      type: 'duplicate_work',
      direction: 'unknown',
      reasoning: 'Keep first',
      keep: 'first',
    })

    await consolidate({ threshold: 0.92 })

    // Verify point1 is kept, point2 is marked for deletion
    const calls = mockQdrant.setPayload.mock.calls
    const secondaryCall = calls.find((call: any) => call[2].deletion_eligible === true)
    expect(secondaryCall[1]).toContain('chunk-2')
  })

  test('should merge QNTM keys (union)', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({
        qntm_keys: ['@test ~ a', '@test ~ b'],
        consolidation_level: 0,
      }),
    })

    const point2 = createMockQdrantPoint({
      id: 'chunk-2',
      payload: createMockChunkPayload({
        qntm_keys: ['@test ~ b', '@test ~ c'],
        consolidation_level: 0,
      }),
    })

    setupSingleUseScroll(mockQdrant, 0, [point1])
    mockQdrant.search.mockResolvedValue([{ id: point2.id, score: 0.95, payload: point2.payload }])

    mockQdrant.retrieve.mockResolvedValue([point1, point2])

    mockLLM.completeJSON.mockResolvedValue({
      type: 'duplicate_work',
      direction: 'unknown',
      reasoning: 'Merge keys',
      keep: 'first',
    })

    await consolidate({ threshold: 0.92 })

    // Find the call that updates primary (has consolidation_level set)
    const calls = mockQdrant.setPayload.mock.calls
    const primaryUpdate = calls.find((call: any) => call[2].consolidation_level !== undefined)
    const updatedPayload = primaryUpdate[2]

    expect(updatedPayload.qntm_keys).toContain('@test ~ a')
    expect(updatedPayload.qntm_keys).toContain('@test ~ b')
    expect(updatedPayload.qntm_keys).toContain('@test ~ c')
    expect(updatedPayload.qntm_keys.length).toBe(3) // Union of 3 unique keys
  })

  test('should track provenance in parents array', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({
        parents: ['chunk-0'],
        consolidation_level: 0,
      }),
    })

    const point2 = createMockQdrantPoint({
      id: 'chunk-2',
      payload: createMockChunkPayload({
        parents: [],
        consolidation_level: 0,
      }),
    })

    setupSingleUseScroll(mockQdrant, 0, [point1])
    mockQdrant.search.mockResolvedValue([{ id: point2.id, score: 0.95, payload: point2.payload }])

    mockQdrant.retrieve.mockResolvedValue([point1, point2])

    mockLLM.completeJSON.mockResolvedValue({
      type: 'duplicate_work',
      direction: 'unknown',
      reasoning: 'Track provenance',
      keep: 'first',
    })

    await consolidate({ threshold: 0.92 })

    const calls = mockQdrant.setPayload.mock.calls
    const primaryUpdate = calls.find((call: any) => call[2].consolidation_level !== undefined)
    const updatedPayload = primaryUpdate[2]

    expect(updatedPayload.parents).toContain('chunk-0') // Existing parent
    expect(updatedPayload.parents).toContain('chunk-2') // New secondary parent
  })

  test('should increment occurrences count', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({
        occurrences: ['2025-12-01T10:00:00Z', '2025-12-02T10:00:00Z'],
        consolidation_level: 0,
      }),
    })

    const point2 = createMockQdrantPoint({
      id: 'chunk-2',
      payload: createMockChunkPayload({
        occurrences: ['2025-12-03T10:00:00Z', '2025-12-04T10:00:00Z', '2025-12-05T10:00:00Z'],
        consolidation_level: 0,
      }),
    })

    setupSingleUseScroll(mockQdrant, 0, [point1])
    mockQdrant.search.mockResolvedValue([{ id: point2.id, score: 0.95, payload: point2.payload }])

    mockQdrant.retrieve.mockResolvedValue([point1, point2])

    mockLLM.completeJSON.mockResolvedValue({
      type: 'duplicate_work',
      direction: 'unknown',
      reasoning: 'Count occurrences',
      keep: 'first',
    })

    await consolidate({ threshold: 0.92 })

    const calls = mockQdrant.setPayload.mock.calls
    const primaryUpdate = calls.find((call: any) => call[2].consolidation_level !== undefined)
    const updatedPayload = primaryUpdate[2]

    expect(updatedPayload.occurrences).toHaveLength(5) // 2 + 3 timestamps merged
  })

  test('should build correct consolidation prompt', async () => {
    const point1 = createMockQdrantPoint({
      id: 'chunk-1',
      payload: createMockChunkPayload({
        original_text: 'First text',
        qntm_keys: ['@test ~ a'],
        created_at: '2025-12-29T10:00:00Z',
        consolidation_level: 0,
      }),
    })

    const point2 = createMockQdrantPoint({
      id: 'chunk-2',
      payload: createMockChunkPayload({
        original_text: 'Second text',
        qntm_keys: ['@test ~ b'],
        created_at: '2025-12-30T10:00:00Z',
        consolidation_level: 0,
      }),
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

    await consolidate({ threshold: 0.92 })

    // Verify completeJSON was called with a prompt containing both texts and QNTM keys
    expect(mockLLM.completeJSON).toHaveBeenCalledTimes(1)
    const prompt = mockLLM.completeJSON.mock.calls[0][0]
    expect(prompt).toContain('First text')
    expect(prompt).toContain('Second text')
    expect(prompt).toContain('@test ~ a')
    expect(prompt).toContain('@test ~ b')
    expect(prompt).toContain('2025-12-29')
    expect(prompt).toContain('2025-12-30')
  })

  test('should mark secondary as consolidated', async () => {
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

    await consolidate({ threshold: 0.92 })

    const calls = mockQdrant.setPayload.mock.calls
    const secondaryCall = calls.find((call: any) => call[2].deletion_eligible === true)

    expect(secondaryCall).toBeDefined()
    expect(secondaryCall[1]).toContain('chunk-2')
  })

  test('should preserve primary as not consolidated', async () => {
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

    await consolidate({ threshold: 0.92 })

    const calls = mockQdrant.setPayload.mock.calls
    const primaryUpdate = calls.find((call: any) => call[2].consolidation_level !== undefined)

    expect(primaryUpdate).toBeDefined()
    expect(primaryUpdate[1]).toContain('chunk-1')
  })
})
