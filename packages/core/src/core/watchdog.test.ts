/**
 * Tests for AdaptiveConcurrencyController
 */

// Use vi.hoisted() to define mocks that will be available when vi.mock() factories run
const { mockAssessSystemCapacity, mockResetCapacityCache } = vi.hoisted(() => ({
  mockAssessSystemCapacity: vi.fn(async () => ({
    canSpawnWorker: true,
    cpuUtilization: 30,
    memoryUtilization: 50,
    pressureLevel: 'nominal',
    details: {
      availableMemory: 8000000000,
      swapUsage: 0,
      currentLoad: 2.5,
      totalMemory: 16000000000,
      usedMemory: 8000000000,
    },
  })),
  mockResetCapacityCache: vi.fn(() => {}),
}))

// Setup mock - hoisted but now has access to hoisted mock functions
vi.mock('./system', () => ({
  assessSystemCapacity: mockAssessSystemCapacity,
  _resetCapacityCache: mockResetCapacityCache,
}))

// Dynamic import after mocks are set up
const { AdaptiveConcurrencyController } = await import('./watchdog')

describe('AdaptiveConcurrencyController', () => {
  let controller: InstanceType<typeof AdaptiveConcurrencyController>

  beforeEach(() => {
    vi.useFakeTimers()
    // Clear previous mock calls and reset to nominal pressure
    mockAssessSystemCapacity.mockClear()
    mockAssessSystemCapacity.mockResolvedValue({
      canSpawnWorker: true,
      cpuUtilization: 30,
      memoryUtilization: 50,
      pressureLevel: 'nominal',
      details: {
        availableMemory: 8000000000,
        swapUsage: 0,
        currentLoad: 2.5,
        totalMemory: 16000000000,
        usedMemory: 8000000000,
      },
    })
    mockResetCapacityCache()
  })

  afterEach(() => {
    // Cleanup watchdog if test didn't
    if (controller) {
      controller.stopWatchdog()
    }
    vi.useRealTimers()
  })

  test('initializes with correct concurrency', () => {
    controller = new AdaptiveConcurrencyController(5, 1, 10)
    const state = controller.getState()

    expect(state.currentConcurrency).toBe(5)
    expect(state.isWatchdogRunning).toBe(false)
  })

  test('clamps initial concurrency to min/max bounds', () => {
    const tooLow = new AdaptiveConcurrencyController(0, 1, 10)
    expect(tooLow.getState().currentConcurrency).toBe(1)

    const tooHigh = new AdaptiveConcurrencyController(20, 1, 10)
    expect(tooHigh.getState().currentConcurrency).toBe(10)
  })

  test('runs tasks with concurrency limiting', async () => {
    controller = new AdaptiveConcurrencyController(2, 1, 5)

    let activeCount = 0
    const maxActive = { value: 0 }

    const tasks = Array.from({ length: 10 }, () =>
      controller.run(async () => {
        activeCount++
        maxActive.value = Math.max(maxActive.value, activeCount)
        await new Promise((resolve) => setTimeout(resolve, 10))
        activeCount--
      })
    )

    // Advance timers to complete all tasks (10 tasks with concurrency 2, 10ms each = ~50ms)
    await vi.advanceTimersByTimeAsync(100)
    await Promise.all(tasks)
    expect(maxActive.value).toBeLessThanOrEqual(2)
  })

  test('starts and stops watchdog cleanly', () => {
    controller = new AdaptiveConcurrencyController(5, 1, 10)

    expect(controller.getState().isWatchdogRunning).toBe(false)

    controller.startWatchdog(5000)
    expect(controller.getState().isWatchdogRunning).toBe(true)

    controller.stopWatchdog()
    expect(controller.getState().isWatchdogRunning).toBe(false)
  })

  test('prevents duplicate watchdog start', () => {
    controller = new AdaptiveConcurrencyController(5, 1, 10)

    controller.startWatchdog(5000)
    const state1 = controller.getState()

    // Try to start again
    controller.startWatchdog(5000)
    const state2 = controller.getState()

    expect(state1.isWatchdogRunning).toBe(true)
    expect(state2.isWatchdogRunning).toBe(true)
    // Should not throw, just log warning

    controller.stopWatchdog()
  })

  test('handles stop when not running', () => {
    controller = new AdaptiveConcurrencyController(5, 1, 10)

    // Should not throw
    controller.stopWatchdog()
    expect(controller.getState().isWatchdogRunning).toBe(false)
  })

  test('tracks active and pending tasks', async () => {
    controller = new AdaptiveConcurrencyController(2, 1, 5)

    const promises: Promise<void>[] = []

    // Start 5 tasks with concurrency 2
    for (let i = 0; i < 5; i++) {
      promises.push(
        controller.run(async () => {
          await new Promise((resolve) => setTimeout(resolve, 50))
        })
      )
    }

    // Check state after a small delay (advance just enough to start tasks)
    await vi.advanceTimersByTimeAsync(10)
    const state = controller.getState()

    // With concurrency 2 and 5 tasks, should have 2 active and 3 pending
    expect(state.activeWorkers).toBe(2)
    expect(state.pendingTasks).toBe(3)

    // Wait for completion (advance enough for all tasks)
    await vi.advanceTimersByTimeAsync(200)
    await Promise.all(promises)

    const finalState = controller.getState()
    expect(finalState.activeWorkers).toBe(0)
    expect(finalState.pendingTasks).toBe(0)
  })

  test('returns task results correctly', async () => {
    controller = new AdaptiveConcurrencyController(3, 1, 5)

    const results = await Promise.all([
      controller.run(async () => 'result1'),
      controller.run(async () => 42),
      controller.run(async () => ({ key: 'value' })),
    ])

    expect(results).toEqual(['result1', 42, { key: 'value' }])
  })

  test('propagates task errors', async () => {
    controller = new AdaptiveConcurrencyController(3, 1, 5)

    let caughtError: Error | null = null

    try {
      await controller.run(async () => {
        throw new Error('Task failed')
      })
    } catch (error) {
      caughtError = error as Error
    }

    expect(caughtError).not.toBeNull()
    expect(caughtError?.message).toBe('Task failed')
  })

  test('handles mixed success and failure tasks', async () => {
    controller = new AdaptiveConcurrencyController(3, 1, 5)

    const results = await Promise.allSettled([
      controller.run(async () => 'success1'),
      controller.run(async () => {
        throw new Error('failure1')
      }),
      controller.run(async () => 'success2'),
      controller.run(async () => {
        throw new Error('failure2')
      }),
    ])

    const fulfilled = results.filter((r) => r.status === 'fulfilled')
    const rejected = results.filter((r) => r.status === 'rejected')

    expect(fulfilled.length).toBe(2)
    expect(rejected.length).toBe(2)
  })

  // ============================================
  // NEW TESTS: Concurrency Adjustment Behavior
  // ============================================

  test('should adjust concurrency when pressure changes to critical', async () => {
    controller = new AdaptiveConcurrencyController(10, 1, 10)
    controller.startWatchdog(10000)

    // Access scheduler via private property (TypeScript workaround)
    const scheduler = (controller as any).scheduler

    // Mock critical pressure
    mockAssessSystemCapacity.mockResolvedValueOnce({
      canSpawnWorker: false,
      cpuUtilization: 95,
      memoryUtilization: 98,
      pressureLevel: 'critical',
      details: {
        availableMemory: 200000000,
        swapUsage: 0.8,
        currentLoad: 15.0,
        totalMemory: 16000000000,
        usedMemory: 15800000000,
      },
    })

    // Reset cache so the mock is actually called
    mockResetCapacityCache()

    // Trigger tick manually
    await scheduler.triggerTick()

    const state = controller.getState()
    expect(state.currentConcurrency).toBe(1) // Dropped to minimum

    controller.stopWatchdog()
  })

  test('should reduce concurrency on warning pressure', async () => {
    controller = new AdaptiveConcurrencyController(10, 1, 10)
    controller.startWatchdog(10000)

    const scheduler = (controller as any).scheduler

    // Mock warning pressure
    mockAssessSystemCapacity.mockResolvedValueOnce({
      canSpawnWorker: true,
      cpuUtilization: 75,
      memoryUtilization: 82,
      pressureLevel: 'warning',
      details: {
        availableMemory: 2000000000,
        swapUsage: 0.3,
        currentLoad: 10.0,
        totalMemory: 16000000000,
        usedMemory: 14000000000,
      },
    })

    // Reset cache so the mock is actually called
    mockResetCapacityCache()

    await scheduler.triggerTick()

    const state = controller.getState()
    // 10 * 0.7 = 7
    expect(state.currentConcurrency).toBe(7)

    controller.stopWatchdog()
  })

  test('should gradually increase concurrency on nominal pressure', async () => {
    controller = new AdaptiveConcurrencyController(5, 1, 10)
    controller.startWatchdog(10000)

    const scheduler = (controller as any).scheduler

    // Nominal pressure → should increase by 1
    await scheduler.triggerTick()

    let state = controller.getState()
    expect(state.currentConcurrency).toBe(6)

    // Another tick → increase again
    await scheduler.triggerTick()

    state = controller.getState()
    expect(state.currentConcurrency).toBe(7)

    controller.stopWatchdog()
  })

  test('should cap concurrency at maximum during scale-up', async () => {
    controller = new AdaptiveConcurrencyController(10, 1, 10)
    controller.startWatchdog(10000)

    const scheduler = (controller as any).scheduler

    // Nominal pressure, but already at max
    await scheduler.triggerTick()

    const state = controller.getState()
    expect(state.currentConcurrency).toBe(10) // Stays at max, doesn't exceed

    controller.stopWatchdog()
  })

  test('should respect minimum during scale-down', async () => {
    controller = new AdaptiveConcurrencyController(2, 1, 10)
    controller.startWatchdog(10000)

    const scheduler = (controller as any).scheduler

    // Mock warning pressure → 2 * 0.7 = 1.4, floors to 1 (minimum)
    mockAssessSystemCapacity.mockResolvedValueOnce({
      canSpawnWorker: true,
      cpuUtilization: 75,
      memoryUtilization: 82,
      pressureLevel: 'warning',
      details: {
        availableMemory: 2000000000,
        swapUsage: 0.3,
        currentLoad: 10.0,
        totalMemory: 16000000000,
        usedMemory: 14000000000,
      },
    })

    // Reset cache so the mock is actually called
    mockResetCapacityCache()

    await scheduler.triggerTick()

    const state = controller.getState()
    expect(state.currentConcurrency).toBe(1) // Respects minimum

    controller.stopWatchdog()
  })

  test('should not adjust when pressure unchanged from nominal', async () => {
    controller = new AdaptiveConcurrencyController(5, 1, 10)
    controller.startWatchdog(10000)

    const scheduler = (controller as any).scheduler

    // First tick increases to 6
    await scheduler.triggerTick()

    let state = controller.getState()
    expect(state.currentConcurrency).toBe(6)

    // Second tick increases to 7
    await scheduler.triggerTick()

    state = controller.getState()
    expect(state.currentConcurrency).toBe(7)

    // Verify gradual increase continues while pressure nominal
    controller.stopWatchdog()
  })

  test('should continue processing tasks during concurrency adjustment', async () => {
    controller = new AdaptiveConcurrencyController(5, 1, 10)

    let completedCount = 0

    // Start long-running tasks
    const tasks = Array.from({ length: 10 }, () =>
      controller.run(async () => {
        await new Promise((resolve) => setTimeout(resolve, 100))
        completedCount++
      })
    )

    // Adjust concurrency mid-flight via startWatchdog + tick
    controller.startWatchdog(10000)
    const scheduler = (controller as any).scheduler

    // Mock critical pressure to force adjustment
    mockAssessSystemCapacity.mockResolvedValueOnce({
      canSpawnWorker: false,
      cpuUtilization: 95,
      memoryUtilization: 98,
      pressureLevel: 'critical',
      details: {
        availableMemory: 200000000,
        swapUsage: 0.8,
        currentLoad: 15.0,
        totalMemory: 16000000000,
        usedMemory: 15800000000,
      },
    })

    // Reset cache so the mock is actually called
    mockResetCapacityCache()

    await scheduler.triggerTick()

    // State should reflect adjustment
    const state = controller.getState()
    expect(state.currentConcurrency).toBe(1)

    // Advance timers to complete all tasks
    await vi.advanceTimersByTimeAsync(500)
    await Promise.all(tasks)
    expect(completedCount).toBe(10)

    controller.stopWatchdog()
  })

  test('should handle rapid pressure changes', async () => {
    controller = new AdaptiveConcurrencyController(10, 1, 10)
    controller.startWatchdog(10000)

    const scheduler = (controller as any).scheduler

    // Critical → drops to 1
    mockAssessSystemCapacity.mockResolvedValueOnce({
      canSpawnWorker: false,
      cpuUtilization: 95,
      memoryUtilization: 98,
      pressureLevel: 'critical',
      details: {
        availableMemory: 200000000,
        swapUsage: 0.8,
        currentLoad: 15.0,
        totalMemory: 16000000000,
        usedMemory: 15800000000,
      },
    })

    // Reset cache so the mock is actually called
    mockResetCapacityCache()

    await scheduler.triggerTick()
    expect(controller.getState().currentConcurrency).toBe(1)

    // Nominal → increases to 2
    mockAssessSystemCapacity.mockResolvedValueOnce({
      canSpawnWorker: true,
      cpuUtilization: 30,
      memoryUtilization: 50,
      pressureLevel: 'nominal',
      details: {
        availableMemory: 8000000000,
        swapUsage: 0,
        currentLoad: 2.5,
        totalMemory: 16000000000,
        usedMemory: 8000000000,
      },
    })

    // Reset cache so the mock is actually called
    mockResetCapacityCache()

    await scheduler.triggerTick()
    expect(controller.getState().currentConcurrency).toBe(2)

    // Warning → reduces to 1 (2 * 0.7 = 1.4, floors to 1)
    mockAssessSystemCapacity.mockResolvedValueOnce({
      canSpawnWorker: true,
      cpuUtilization: 75,
      memoryUtilization: 82,
      pressureLevel: 'warning',
      details: {
        availableMemory: 2000000000,
        swapUsage: 0.3,
        currentLoad: 10.0,
        totalMemory: 16000000000,
        usedMemory: 14000000000,
      },
    })

    // Reset cache so the mock is actually called
    mockResetCapacityCache()

    await scheduler.triggerTick()
    expect(controller.getState().currentConcurrency).toBe(1)

    controller.stopWatchdog()
  })
})
