/**
 * Tests for AdaptiveConcurrencyController
 */

import { describe, expect, test, beforeEach, afterEach } from 'bun:test'
import { AdaptiveConcurrencyController } from './watchdog'

describe('AdaptiveConcurrencyController', () => {
  let controller: AdaptiveConcurrencyController

  afterEach(() => {
    // Cleanup watchdog if test didn't
    if (controller) {
      controller.stopWatchdog()
    }
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

    // Check state after a small delay
    await new Promise((resolve) => setTimeout(resolve, 10))
    const state = controller.getState()

    // With concurrency 2 and 5 tasks, should have 2 active and 3 pending
    expect(state.activeWorkers).toBe(2)
    expect(state.pendingTasks).toBe(3)

    // Wait for completion
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
})
