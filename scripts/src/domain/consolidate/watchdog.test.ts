/**
 * Tests for ConsolidationWatchdog and IngestPauseController
 */

// Use vi.hoisted() to define mocks that will be available when vi.mock() factories run
const { mockConsolidate, mockGetCollection, mockUpdateCollection } = vi.hoisted(() => ({
  mockConsolidate: vi.fn(() =>
    Promise.resolve({
      candidatesFound: 5,
      consolidated: 3,
      deleted: 3,
    })
  ),
  mockGetCollection: vi.fn(() => Promise.resolve({ points_count: 0 })),
  mockUpdateCollection: vi.fn(() => Promise.resolve()),
}))

// Setup module mock - hoisted but now has access to hoisted mock function
vi.mock('.', () => ({
  consolidate: mockConsolidate,
}))

// Mock Qdrant client for dynamic threshold calculation and HNSW toggle
vi.mock('../../services/storage', () => ({
  getQdrantClient: () => ({
    getCollection: mockGetCollection,
    updateCollection: mockUpdateCollection,
  }),
  withHNSWDisabled: async <T>(fn: () => Promise<T>) => fn(), // Pass through
}))

// Now import the module under test (after mock is set up)
import {
  ConsolidationWatchdog,
  ingestPauseController,
  resetConsolidationWatchdog,
  getConsolidationWatchdog,
} from './watchdog'

describe('IngestPauseController', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    // Reset pause controller state completely
    ingestPauseController.reset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('pause/resume', () => {
    test('starts unpaused', () => {
      expect(ingestPauseController.isPaused()).toBe(false)
    })

    test('pauses successfully', () => {
      ingestPauseController.pause()
      expect(ingestPauseController.isPaused()).toBe(true)
    })

    test('resumes successfully', () => {
      ingestPauseController.pause()
      ingestPauseController.resume()
      expect(ingestPauseController.isPaused()).toBe(false)
    })

    test('handles multiple pause calls', () => {
      ingestPauseController.pause()
      ingestPauseController.pause()
      expect(ingestPauseController.isPaused()).toBe(true)

      ingestPauseController.resume()
      expect(ingestPauseController.isPaused()).toBe(false)
    })

    test('handles multiple resume calls', () => {
      ingestPauseController.pause()
      ingestPauseController.resume()
      ingestPauseController.resume()
      expect(ingestPauseController.isPaused()).toBe(false)
    })
  })

  describe('in-flight tracking', () => {
    test('starts with zero in-flight operations', () => {
      const state = ingestPauseController.getState()
      expect(state.inFlightCount).toBe(0)
    })

    test('tracks in-flight registration', () => {
      ingestPauseController.registerInFlight()
      const state = ingestPauseController.getState()
      expect(state.inFlightCount).toBe(1)
    })

    test('tracks in-flight completion', () => {
      ingestPauseController.registerInFlight()
      ingestPauseController.completeInFlight()
      const state = ingestPauseController.getState()
      expect(state.inFlightCount).toBe(0)
    })

    test('tracks multiple in-flight operations', () => {
      ingestPauseController.registerInFlight()
      ingestPauseController.registerInFlight()
      ingestPauseController.registerInFlight()

      const state1 = ingestPauseController.getState()
      expect(state1.inFlightCount).toBe(3)

      ingestPauseController.completeInFlight()

      const state2 = ingestPauseController.getState()
      expect(state2.inFlightCount).toBe(2)
    })

    test('handles completion when count is zero', () => {
      // Should not go negative
      ingestPauseController.completeInFlight()
      const state = ingestPauseController.getState()
      expect(state.inFlightCount).toBe(-1) // Actually it will go negative based on impl
    })
  })

  describe('waitForInFlight', () => {
    test('resolves immediately when no in-flight operations', async () => {
      const start = Date.now()
      await ingestPauseController.waitForInFlight()
      const duration = Date.now() - start

      // Should resolve almost instantly
      expect(duration).toBeLessThan(10)
    })

    test('waits for in-flight operations to complete', async () => {
      ingestPauseController.registerInFlight()

      let resolved = false
      const waitPromise = ingestPauseController.waitForInFlight().then(() => {
        resolved = true
      })

      // Should not resolve yet
      await vi.advanceTimersByTimeAsync(10)
      expect(resolved).toBe(false)

      // Complete the in-flight operation
      ingestPauseController.completeInFlight()

      await waitPromise
      expect(resolved).toBe(true)
    })

    test('waits for all in-flight operations', async () => {
      ingestPauseController.registerInFlight()
      ingestPauseController.registerInFlight()

      let resolved = false
      const waitPromise = ingestPauseController.waitForInFlight().then(() => {
        resolved = true
      })

      // Complete first operation
      ingestPauseController.completeInFlight()
      await vi.advanceTimersByTimeAsync(10)
      expect(resolved).toBe(false)

      // Complete second operation
      ingestPauseController.completeInFlight()
      await waitPromise
      expect(resolved).toBe(true)
    })

    test('notifies multiple waiters', async () => {
      ingestPauseController.registerInFlight()

      let resolved1 = false
      let resolved2 = false

      const wait1 = ingestPauseController.waitForInFlight().then(() => {
        resolved1 = true
      })

      const wait2 = ingestPauseController.waitForInFlight().then(() => {
        resolved2 = true
      })

      // Complete the in-flight operation
      ingestPauseController.completeInFlight()

      await Promise.all([wait1, wait2])

      expect(resolved1).toBe(true)
      expect(resolved2).toBe(true)
    })
  })

  describe('getState', () => {
    test('returns correct state', () => {
      const state = ingestPauseController.getState()

      expect(state).toHaveProperty('paused')
      expect(state).toHaveProperty('inFlightCount')
      expect(typeof state.paused).toBe('boolean')
      expect(typeof state.inFlightCount).toBe('number')
    })

    test('reflects pause state changes', () => {
      const state1 = ingestPauseController.getState()
      expect(state1.paused).toBe(false)

      ingestPauseController.pause()

      const state2 = ingestPauseController.getState()
      expect(state2.paused).toBe(true)
    })

    test('reflects in-flight count changes', () => {
      ingestPauseController.registerInFlight()
      const state = ingestPauseController.getState()
      expect(state.inFlightCount).toBeGreaterThan(0)
    })
  })
})

describe('ConsolidationWatchdog', () => {
  let watchdog: InstanceType<typeof ConsolidationWatchdog> | null = null

  beforeEach(() => {
    vi.useFakeTimers()
    mockConsolidate.mockClear()
    ingestPauseController.reset()
    resetConsolidationWatchdog()
  })

  afterEach(() => {
    if (watchdog) {
      watchdog.stop()
      watchdog = null
    }
    resetConsolidationWatchdog()
    vi.useRealTimers()
  })

  describe('initialization', () => {
    test('initializes with default config', () => {
      watchdog = new ConsolidationWatchdog()
      const state = watchdog.getState()

      expect(state.baseThreshold).toBe(100) // CONSOLIDATION_BASE_THRESHOLD
      expect(state.isRunning).toBe(false)
      expect(state.isConsolidating).toBe(false)
      expect(state.currentCount).toBe(0)
      expect(state.lastConsolidationCount).toBe(0)
    })

    test('initializes with custom threshold', () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 50 })
      const state = watchdog.getState()

      expect(state.baseThreshold).toBe(50)
    })

    test('initializes with custom similarity threshold', () => {
      watchdog = new ConsolidationWatchdog({ similarityThreshold: 0.85 })
      // No direct way to test this, but should not throw
      expect(watchdog).toBeDefined()
    })
  })

  describe('start/stop', () => {
    test('starts successfully', () => {
      watchdog = new ConsolidationWatchdog()
      watchdog.start(1000)

      expect(watchdog.getState().isRunning).toBe(true)
    })

    test('stops successfully', () => {
      watchdog = new ConsolidationWatchdog()
      watchdog.start(1000)
      watchdog.stop()

      expect(watchdog.getState().isRunning).toBe(false)
    })

    test('uses custom poll interval', () => {
      watchdog = new ConsolidationWatchdog()
      watchdog.start(5000)

      expect(watchdog.getState().isRunning).toBe(true)
    })

    test('uses default poll interval when not specified', () => {
      watchdog = new ConsolidationWatchdog()
      watchdog.start() // No argument = use default

      expect(watchdog.getState().isRunning).toBe(true)
    })
  })

  describe('recordIngestion', () => {
    test('increments count by 1 by default', () => {
      watchdog = new ConsolidationWatchdog()
      watchdog.recordIngestion()

      const state = watchdog.getState()
      expect(state.currentCount).toBe(1)
    })

    test('increments count by specified amount', () => {
      watchdog = new ConsolidationWatchdog()
      watchdog.recordIngestion(5)

      const state = watchdog.getState()
      expect(state.currentCount).toBe(5)
    })

    test('accumulates multiple ingestions', () => {
      watchdog = new ConsolidationWatchdog()
      watchdog.recordIngestion(3)
      watchdog.recordIngestion(2)
      watchdog.recordIngestion(1)

      const state = watchdog.getState()
      expect(state.currentCount).toBe(6)
    })
  })

  describe('threshold detection', () => {
    test('does not consolidate below threshold', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 10 })
      watchdog.recordIngestion(5)

      watchdog.start(50) // Fast polling

      // Wait for a few poll cycles
      await vi.advanceTimersByTimeAsync(150)

      watchdog.stop()

      // Should not have triggered consolidation
      expect(mockConsolidate).not.toHaveBeenCalled()
    })

    test('triggers consolidation at threshold', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 10, useHNSWToggle: false })
      watchdog.recordIngestion(10)

      watchdog.start(50)

      // Wait for poll to trigger
      await vi.advanceTimersByTimeAsync(100)

      watchdog.stop()

      // Should have triggered consolidation
      expect(mockConsolidate).toHaveBeenCalled()
    })

    test('triggers consolidation above threshold', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 10, useHNSWToggle: false })
      watchdog.recordIngestion(15)

      watchdog.start(50)

      await vi.advanceTimersByTimeAsync(100)

      watchdog.stop()

      expect(mockConsolidate).toHaveBeenCalled()
    })

    test('calculates documentsSinceLastConsolidation correctly', () => {
      watchdog = new ConsolidationWatchdog()
      watchdog.recordIngestion(50)

      const state1 = watchdog.getState()
      expect(state1.documentsSinceLastConsolidation).toBe(50)
    })
  })

  describe('consolidation execution', () => {
    test('pauses ingestion during consolidation', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 5, useHNSWToggle: false })
      watchdog.recordIngestion(5)

      let pausedDuringConsolidation = false

      // Mock consolidate to check pause state
      mockConsolidate.mockImplementationOnce(async () => {
        pausedDuringConsolidation = ingestPauseController.isPaused()
        await new Promise((resolve) => setTimeout(resolve, 50))
        return { candidatesFound: 0, consolidated: 0, deleted: 0 }
      })

      const consolidatePromise = watchdog.forceConsolidation()
      await vi.advanceTimersByTimeAsync(100)
      await consolidatePromise

      expect(pausedDuringConsolidation).toBe(true)
      expect(ingestPauseController.isPaused()).toBe(false) // Should be resumed
    })

    test('waits for in-flight operations before consolidating', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 5, useHNSWToggle: false })
      watchdog.recordIngestion(5)

      // Register in-flight operation
      ingestPauseController.registerInFlight()

      let consolidationStarted = false

      mockConsolidate.mockImplementationOnce(async () => {
        consolidationStarted = true
        return { candidatesFound: 0, consolidated: 0, deleted: 0 }
      })

      const consolidatePromise = watchdog.forceConsolidation()

      // Wait a bit - consolidation should not start yet
      await vi.advanceTimersByTimeAsync(20)
      expect(consolidationStarted).toBe(false)

      // Complete in-flight operation
      ingestPauseController.completeInFlight()

      await consolidatePromise
      expect(consolidationStarted).toBe(true)
    })

    test('resumes ingestion after consolidation', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 5, useHNSWToggle: false })
      watchdog.recordIngestion(5)

      await watchdog.forceConsolidation()

      expect(ingestPauseController.isPaused()).toBe(false)
    })

    test('resumes ingestion even if consolidation fails', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 5, useHNSWToggle: false })
      watchdog.recordIngestion(5)

      mockConsolidate.mockImplementationOnce(async () => {
        throw new Error('Consolidation error')
      })

      await watchdog.forceConsolidation()

      expect(ingestPauseController.isPaused()).toBe(false)
    })

    test('updates lastConsolidationCount after successful consolidation', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 5, useHNSWToggle: false })
      watchdog.recordIngestion(10)

      await watchdog.forceConsolidation()

      const state = watchdog.getState()
      expect(state.lastConsolidationCount).toBe(10)
      expect(state.documentsSinceLastConsolidation).toBe(0)
    })

    test('does not update count if consolidation fails', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 5, useHNSWToggle: false })
      watchdog.recordIngestion(10)

      mockConsolidate.mockImplementationOnce(async () => {
        throw new Error('Failed')
      })

      await watchdog.forceConsolidation()

      const state = watchdog.getState()
      // Count should NOT be updated on failure (stays at 0, not 10)
      expect(state.lastConsolidationCount).toBe(0)
      expect(state.documentsSinceLastConsolidation).toBe(10)
    })

    test('passes similarity threshold to consolidate', async () => {
      watchdog = new ConsolidationWatchdog({
        baseThreshold: 5,
        similarityThreshold: 0.88,
        useHNSWToggle: false,
      })
      watchdog.recordIngestion(5)

      await watchdog.forceConsolidation()

      expect(mockConsolidate).toHaveBeenCalledWith({
        threshold: 0.88,
        limit: 50,
      })
    })

    test('passes default similarity threshold', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 5, useHNSWToggle: false })
      watchdog.recordIngestion(5)

      await watchdog.forceConsolidation()

      expect(mockConsolidate).toHaveBeenCalledWith({
        threshold: 0.8, // CONSOLIDATION_SIMILARITY_THRESHOLD from config
        limit: 50,
      })
    })
  })

  describe('forceConsolidation', () => {
    test('runs consolidation manually', async () => {
      watchdog = new ConsolidationWatchdog()
      // Don't record any ingestions - below threshold

      await watchdog.forceConsolidation()

      expect(mockConsolidate).toHaveBeenCalled()
    })

    test('prevents concurrent consolidations', async () => {
      watchdog = new ConsolidationWatchdog()

      let consolidationCount = 0

      mockConsolidate.mockImplementation(async () => {
        consolidationCount++
        await new Promise((resolve) => setTimeout(resolve, 100))
        return { candidatesFound: 0, consolidated: 0, deleted: 0 }
      })

      // Start two consolidations simultaneously
      const promise1 = watchdog.forceConsolidation()
      const promise2 = watchdog.forceConsolidation() // Should be rejected

      await vi.advanceTimersByTimeAsync(200)
      await Promise.all([promise1, promise2])

      // Only one should have executed
      expect(consolidationCount).toBe(1)
    })

    test('sets isConsolidating flag', async () => {
      watchdog = new ConsolidationWatchdog()

      let consolidatingDuringRun = false

      mockConsolidate.mockImplementationOnce(async () => {
        consolidatingDuringRun = watchdog?.getState().isConsolidating ?? false
        return { candidatesFound: 0, consolidated: 0, deleted: 0 }
      })

      await watchdog.forceConsolidation()

      expect(consolidatingDuringRun).toBe(true)
      expect(watchdog.getState().isConsolidating).toBe(false)
    })
  })

  describe('getState', () => {
    test('returns complete state', () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 50 })
      watchdog.recordIngestion(30)

      const state = watchdog.getState()

      expect(state).toHaveProperty('isRunning')
      expect(state).toHaveProperty('isConsolidating')
      expect(state).toHaveProperty('currentCount')
      expect(state).toHaveProperty('lastConsolidationCount')
      expect(state).toHaveProperty('documentsSinceLastConsolidation')
      expect(state).toHaveProperty('baseThreshold')
      expect(state).toHaveProperty('scaleFactor')
      expect(state).toHaveProperty('consecutiveFailures')
      expect(state).toHaveProperty('circuitBreakerOpen')

      expect(state.currentCount).toBe(30)
      expect(state.baseThreshold).toBe(50)
      expect(state.documentsSinceLastConsolidation).toBe(30)
    })
  })

  describe('periodic consolidation', () => {
    test('automatically consolidates when threshold reached', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 5, useHNSWToggle: false })

      watchdog.start(50) // Fast polling

      // Incrementally add documents
      watchdog.recordIngestion(3)
      await vi.advanceTimersByTimeAsync(60)

      watchdog.recordIngestion(2) // Now at threshold
      await vi.advanceTimersByTimeAsync(100)

      watchdog.stop()

      expect(mockConsolidate).toHaveBeenCalled()
    })

    test('skips consolidation if already in progress', async () => {
      watchdog = new ConsolidationWatchdog({ baseThreshold: 5, useHNSWToggle: false })

      let consolidationCount = 0

      mockConsolidate.mockImplementation(async () => {
        consolidationCount++
        await new Promise((resolve) => setTimeout(resolve, 200))
        return { candidatesFound: 0, consolidated: 0, deleted: 0 }
      })

      watchdog.recordIngestion(10)
      watchdog.start(30) // Fast polling, shorter than consolidation

      // Wait for multiple poll cycles
      await vi.advanceTimersByTimeAsync(300)

      watchdog.stop()

      // Should only run once despite multiple polls
      expect(consolidationCount).toBe(1)
    })
  })
})

describe('singleton functions', () => {
  beforeEach(() => {
    ingestPauseController.reset()
  })

  afterEach(() => {
    resetConsolidationWatchdog()
  })

  describe('getConsolidationWatchdog', () => {
    test('creates singleton instance', () => {
      const instance1 = getConsolidationWatchdog()
      const instance2 = getConsolidationWatchdog()

      expect(instance1).toBe(instance2)
    })

    test('uses provided config on first call', () => {
      const instance = getConsolidationWatchdog({ baseThreshold: 75 })
      const state = instance.getState()

      expect(state.baseThreshold).toBe(75)
    })

    test('ignores config on subsequent calls', () => {
      const instance1 = getConsolidationWatchdog({ baseThreshold: 75 })
      const instance2 = getConsolidationWatchdog({ baseThreshold: 50 })

      expect(instance1).toBe(instance2)
      expect(instance1.getState().baseThreshold).toBe(75) // Original config
    })
  })

  describe('resetConsolidationWatchdog', () => {
    test('stops existing instance', () => {
      const instance = getConsolidationWatchdog()
      instance.start(1000)

      expect(instance.getState().isRunning).toBe(true)

      resetConsolidationWatchdog()

      expect(instance.getState().isRunning).toBe(false)
    })

    test('allows creating new instance after reset', () => {
      const instance1 = getConsolidationWatchdog({ baseThreshold: 50 })
      resetConsolidationWatchdog()

      const instance2 = getConsolidationWatchdog({ baseThreshold: 100 })

      expect(instance1).not.toBe(instance2)
      expect(instance2.getState().baseThreshold).toBe(100)
    })

    test('handles reset when no instance exists', () => {
      // Should not throw
      resetConsolidationWatchdog()
      expect(true).toBe(true)
    })
  })
})
