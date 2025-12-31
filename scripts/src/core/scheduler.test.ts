/**
 * Tests for PollingScheduler
 */

import { PollingScheduler } from './scheduler'

describe('PollingScheduler', () => {
  let scheduler: PollingScheduler | null = null

  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    // Cleanup scheduler if test didn't
    if (scheduler) {
      scheduler.stop()
      scheduler = null
    }
    vi.useRealTimers()
  })

  describe('initialization', () => {
    test('initializes with correct name and state', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test-scheduler',
        tick,
      })

      const state = scheduler.getState()
      expect(state.name).toBe('test-scheduler')
      expect(state.isRunning).toBe(false)
      expect(state.isBusy).toBe(false)
      expect(state.isShuttingDown).toBe(false)
    })

    test('accepts custom logger', () => {
      const customLog = {
        debug: vi.fn(() => {}),
        info: vi.fn(() => {}),
        warn: vi.fn(() => {}),
        error: vi.fn(() => {}),
      }

      scheduler = new PollingScheduler({
        name: 'test',
        tick: async () => {},
        logger: customLog,
      })

      // Should not throw
      expect(scheduler).toBeDefined()
    })
  })

  describe('start/stop lifecycle', () => {
    test('starts scheduler successfully', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      scheduler.start(100)

      expect(scheduler.isRunning()).toBe(true)
      expect(scheduler.getState().isShuttingDown).toBe(false)
    })

    test('stops scheduler successfully', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      scheduler.start(100)
      expect(scheduler.isRunning()).toBe(true)

      scheduler.stop()
      expect(scheduler.isRunning()).toBe(false)
    })

    test('prevents duplicate start', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      scheduler.start(100)
      const state1 = scheduler.getState()

      // Try to start again
      scheduler.start(100)
      const state2 = scheduler.getState()

      // Should still be running, but not double-started
      expect(state1.isRunning).toBe(true)
      expect(state2.isRunning).toBe(true)
      expect(tick).not.toHaveBeenCalled() // Interval hasn't fired yet
    })

    test('handles stop when not running', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      // Should not throw
      scheduler.stop()
      expect(scheduler.isRunning()).toBe(false)
    })

    test('resets shutdown flag on restart', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      scheduler.start(100)
      scheduler.stop()

      expect(scheduler.getState().isShuttingDown).toBe(true)

      scheduler.start(100)
      expect(scheduler.getState().isShuttingDown).toBe(false)
    })
  })

  describe('tick execution', () => {
    test('executes tick at interval', async () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      scheduler.start(50) // 50ms interval

      // Advance time for 2+ ticks
      await vi.advanceTimersByTimeAsync(120)

      scheduler.stop()

      // Should have been called at least twice
      expect(tick.mock.calls.length).toBeGreaterThanOrEqual(2)
    })

    test('skips tick when already in progress', async () => {
      let tickCount = 0
      const tick = vi.fn(async () => {
        tickCount++
        // Long-running tick - use real delay simulation
        await new Promise((resolve) => setTimeout(resolve, 100))
      })

      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      scheduler.start(30) // Interval shorter than tick duration

      // Advance time for multiple intervals
      await vi.advanceTimersByTimeAsync(150)

      scheduler.stop()

      // Should not have overlapping ticks
      // With 30ms interval and 100ms tick, we'd expect only 1-2 ticks
      expect(tickCount).toBeLessThanOrEqual(2)
    })

    test('skips tick when shutting down', async () => {
      const tick = vi.fn(async () => {
        await new Promise((resolve) => setTimeout(resolve, 10))
      })

      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      scheduler.start(20)

      // Let one tick execute
      await vi.advanceTimersByTimeAsync(25)

      // Stop immediately
      scheduler.stop()

      const callsAfterStop = tick.mock.calls.length

      // Advance more time
      await vi.advanceTimersByTimeAsync(50)

      // Should not have increased
      expect(tick.mock.calls.length).toBe(callsAfterStop)
    })

    test('handles tick errors gracefully', async () => {
      let callCount = 0
      const tick = vi.fn(async () => {
        callCount++
        if (callCount === 1) {
          throw new Error('Tick failed')
        }
      })

      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      scheduler.start(50)

      // Advance time for multiple ticks
      await vi.advanceTimersByTimeAsync(150)

      scheduler.stop()

      // Should continue executing after error
      expect(callCount).toBeGreaterThanOrEqual(2)
    })

    test('resets busy flag after tick error', async () => {
      const tick = vi.fn(async () => {
        throw new Error('Test error')
      })

      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      scheduler.start(50)

      // Wait for tick to execute and fail
      await vi.advanceTimersByTimeAsync(70)

      // Should not be busy after error
      expect(scheduler.isBusy()).toBe(false)

      scheduler.stop()
    })
  })

  describe('state queries', () => {
    test('isRunning returns correct state', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      expect(scheduler.isRunning()).toBe(false)

      scheduler.start(100)
      expect(scheduler.isRunning()).toBe(true)

      scheduler.stop()
      expect(scheduler.isRunning()).toBe(false)
    })

    test('isBusy returns false when no tick in progress', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      expect(scheduler.isBusy()).toBe(false)
    })

    test('isBusy returns true during tick execution', async () => {
      let busyDuringTick = false
      const tick = vi.fn(async () => {
        if (scheduler) {
          busyDuringTick = scheduler.isBusy()
        }
        await new Promise((resolve) => setTimeout(resolve, 30))
      })

      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      // Use triggerTick for synchronous control
      const tickPromise = scheduler.triggerTick()

      // Advance time for tick to complete
      await vi.advanceTimersByTimeAsync(50)
      await tickPromise

      // Busy flag should have been true inside tick
      expect(busyDuringTick).toBe(true)
      // Should not be busy now
      expect(scheduler.isBusy()).toBe(false)
    })

    test('getState returns complete state', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test-name',
        tick,
      })

      const state = scheduler.getState()

      expect(state).toHaveProperty('name')
      expect(state).toHaveProperty('isRunning')
      expect(state).toHaveProperty('isBusy')
      expect(state).toHaveProperty('isShuttingDown')

      expect(state.name).toBe('test-name')
    })
  })

  describe('triggerTick', () => {
    test('executes tick manually', async () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      await scheduler.triggerTick()

      expect(tick).toHaveBeenCalledTimes(1)
    })

    test('sets busy flag during manual tick', async () => {
      let busyDuringTick = false
      const tick = vi.fn(async () => {
        if (scheduler) {
          busyDuringTick = scheduler.isBusy()
        }
        await new Promise((resolve) => setTimeout(resolve, 10))
      })

      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      const tickPromise = scheduler.triggerTick()
      await vi.advanceTimersByTimeAsync(20)
      await tickPromise

      expect(busyDuringTick).toBe(true)
      expect(scheduler.isBusy()).toBe(false) // Should be reset after
    })

    test('skips manual trigger when tick in progress', async () => {
      let tickCount = 0
      const tick = vi.fn(async () => {
        tickCount++
        await new Promise((resolve) => setTimeout(resolve, 50))
      })

      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      // Start two manual ticks simultaneously
      const promise1 = scheduler.triggerTick()
      const promise2 = scheduler.triggerTick() // Should be skipped

      await vi.advanceTimersByTimeAsync(100)
      await Promise.all([promise1, promise2])

      expect(tickCount).toBe(1) // Only one should have executed
    })

    test('resets busy flag after manual tick error', async () => {
      const tick = vi.fn(async () => {
        throw new Error('Manual tick error')
      })

      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      // triggerTick re-throws errors (unlike start() which catches them)
      try {
        await scheduler.triggerTick()
      } catch {
        // Expected - triggerTick propagates errors
      }

      // Busy flag should still be reset despite error
      expect(scheduler.isBusy()).toBe(false)
    })

    test('works without starting scheduler', async () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      // Don't call start()
      await scheduler.triggerTick()

      expect(tick).toHaveBeenCalledTimes(1)
      expect(scheduler.isRunning()).toBe(false)
    })
  })

  describe('edge cases', () => {
    test('handles rapid start/stop cycles', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      for (let i = 0; i < 5; i++) {
        scheduler.start(100)
        scheduler.stop()
      }

      expect(scheduler.isRunning()).toBe(false)
    })

    test('clamps interval to minimum 10ms', async () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      // Start with zero interval (should be clamped to 10ms)
      scheduler.start(0)

      await vi.advanceTimersByTimeAsync(50)

      scheduler.stop()

      // With 10ms interval over 50ms, expect ~5 ticks
      expect(tick.mock.calls.length).toBeGreaterThanOrEqual(4)
      expect(tick.mock.calls.length).toBeLessThanOrEqual(6)
    })

    test('handles very long interval', () => {
      const tick = vi.fn(async () => {})
      scheduler = new PollingScheduler({
        name: 'test',
        tick,
      })

      // Start with very long interval
      scheduler.start(3600000) // 1 hour

      expect(scheduler.isRunning()).toBe(true)

      scheduler.stop()
    })
  })
})
