/**
 * Shared test helpers for consolidate tests
 *
 * Extracted from index.test.ts to enable test file splitting without duplication.
 * Each test file imports these helpers and runs in separate Vitest worker for memory isolation.
 *
 * NOTE: Module mocking (vi.mock) must be done inline in each test file before imports,
 * as vi.mock is hoisted to top of file and can't reference external variables.
 */

/**
 * Reset all mocks to default state (called in beforeEach)
 */
export function resetConsolidateMocks(mockQdrant: any, mockLLM: any, requireCollection: any) {
  // Reset all mocks (clears implementation + call history)
  mockQdrant.scroll.mockReset()
  mockQdrant.search.mockReset()
  mockQdrant.retrieve.mockReset()
  mockQdrant.setPayload.mockReset()
  mockLLM.completeJSON.mockReset()
  ;(requireCollection as any).mockReset()

  // Restore default implementations
  // IMPORTANT: scroll must return nextOffset: null to prevent infinite loops
  ;(requireCollection as any).mockResolvedValue(undefined)
  mockQdrant.setPayload.mockResolvedValue({} as any)

  // Default scroll: empty results that terminate pagination
  mockQdrant.scroll.mockImplementation(() => Promise.resolve({ points: [], nextOffset: null }))

  mockQdrant.search.mockResolvedValue([])
  mockQdrant.retrieve.mockResolvedValue([])
}

/**
 * Setup scroll mock to return points only at specific consolidation level
 *
 * This prevents the consolidate() function from finding candidates at all 4 levels (0-3)
 * when tests only expect candidates at level 0.
 *
 * @param mockQdrant - Mock Qdrant client
 * @param level - Consolidation level to return points at
 * @param points - Points to return at that level
 */
export function setupLevelFilteredScroll(mockQdrant: any, level: number, points: any[]) {
  mockQdrant.scroll.mockImplementation((_collection: string, options: any) => {
    const requestedLevel = options.filter?.must?.find((m: any) => m.key === 'consolidation_level')
      ?.match?.value

    if (requestedLevel === level) {
      return Promise.resolve({ points, nextOffset: null })
    }
    return Promise.resolve({ points: [], nextOffset: null })
  })
}

/**
 * Setup scroll mock with single-use behavior (returns points once, then empty)
 *
 * This simulates consolidation promoting points to next level. After first scroll,
 * the point is "promoted" so subsequent scrolls return empty.
 *
 * @param mockQdrant - Mock Qdrant client
 * @param level - Consolidation level to return points at
 * @param points - Points to return on first call
 */
export function setupSingleUseScroll(mockQdrant: any, level: number, points: any[]) {
  let callCount = 0
  mockQdrant.scroll.mockImplementation((_collection: string, options: any) => {
    const requestedLevel = options.filter?.must?.find((m: any) => m.key === 'consolidation_level')
      ?.match?.value

    if (requestedLevel === level) {
      callCount++
      if (callCount === 1) {
        return Promise.resolve({ points, nextOffset: null })
      }
    }
    return Promise.resolve({ points: [], nextOffset: null })
  })
}
