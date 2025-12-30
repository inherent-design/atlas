/**
 * Tests for System Monitoring and Capacity Assessment
 */

import { describe, expect, test } from 'bun:test'
import { assessSystemCapacity, getGPUCapabilities, getRecommendedConcurrency } from './system'

describe('system monitoring', () => {
  describe('assessSystemCapacity', () => {
    test('returns valid capacity assessment', async () => {
      const capacity = await assessSystemCapacity()

      expect(capacity).toHaveProperty('canSpawnWorker')
      expect(capacity).toHaveProperty('cpuUtilization')
      expect(capacity).toHaveProperty('memoryUtilization')
      expect(capacity).toHaveProperty('pressureLevel')
      expect(capacity).toHaveProperty('details')

      expect(typeof capacity.canSpawnWorker).toBe('boolean')
      expect(typeof capacity.cpuUtilization).toBe('number')
      expect(typeof capacity.memoryUtilization).toBe('number')
      expect(['nominal', 'warning', 'critical']).toContain(capacity.pressureLevel)

      expect(capacity.cpuUtilization).toBeGreaterThanOrEqual(0)
      expect(capacity.cpuUtilization).toBeLessThanOrEqual(100)
      expect(capacity.memoryUtilization).toBeGreaterThanOrEqual(0)
      expect(capacity.memoryUtilization).toBeLessThanOrEqual(100)
    })

    test('provides detailed metrics', async () => {
      const capacity = await assessSystemCapacity()

      expect(capacity.details).toHaveProperty('availableMemory')
      expect(capacity.details).toHaveProperty('swapUsage')
      expect(capacity.details).toHaveProperty('currentLoad')
      expect(capacity.details).toHaveProperty('totalMemory')
      expect(capacity.details).toHaveProperty('usedMemory')

      expect(capacity.details.totalMemory).toBeGreaterThan(0)
      expect(capacity.details.availableMemory).toBeGreaterThanOrEqual(0)
      expect(capacity.details.swapUsage).toBeGreaterThanOrEqual(0)
    })
  })

  describe('getGPUCapabilities', () => {
    test('returns GPU capability status', async () => {
      const gpu = await getGPUCapabilities()

      expect(gpu).toHaveProperty('available')
      expect(typeof gpu.available).toBe('boolean')

      if (gpu.available) {
        expect(gpu).toHaveProperty('maxBufferSize')
        expect(gpu).toHaveProperty('maxTextureDimension2D')
        expect(typeof gpu.maxBufferSize).toBe('number')
        expect(typeof gpu.maxTextureDimension2D).toBe('number')
      } else {
        expect(gpu).toHaveProperty('error')
        expect(typeof gpu.error).toBe('string')
      }
    })
  })

  describe('getRecommendedConcurrency', () => {
    test('returns concurrency within bounds', async () => {
      const staticLimit = 8
      const minWorkers = 2
      const maxWorkers = 10

      const concurrency = await getRecommendedConcurrency(staticLimit, minWorkers, maxWorkers)

      expect(concurrency).toBeGreaterThanOrEqual(minWorkers)
      expect(concurrency).toBeLessThanOrEqual(maxWorkers)
      expect(typeof concurrency).toBe('number')
    })

    test('respects minimum workers even under pressure', async () => {
      const staticLimit = 8
      const minWorkers = 1
      const maxWorkers = 10

      const concurrency = await getRecommendedConcurrency(staticLimit, minWorkers, maxWorkers)

      expect(concurrency).toBeGreaterThanOrEqual(minWorkers)
    })

    test('caps at maximum workers', async () => {
      const staticLimit = 100 // Request way more than max
      const minWorkers = 2
      const maxWorkers = 10

      const concurrency = await getRecommendedConcurrency(staticLimit, minWorkers, maxWorkers)

      expect(concurrency).toBeLessThanOrEqual(maxWorkers)
    })
  })

  describe('pressure level classification', () => {
    test('nominal pressure allows worker spawning', async () => {
      const capacity = await assessSystemCapacity()

      // On a healthy system, should typically be nominal
      if (capacity.pressureLevel === 'nominal') {
        expect(capacity.canSpawnWorker).toBe(true)
      }
    })

    test('critical pressure prevents worker spawning', async () => {
      const capacity = await assessSystemCapacity()

      // If pressure is critical, must block worker spawn
      if (capacity.pressureLevel === 'critical') {
        expect(capacity.canSpawnWorker).toBe(false)
      }
    })
  })
})
