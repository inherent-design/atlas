/**
 * Tests for System Monitoring and Capacity Assessment
 *
 * Vitest's pool: 'forks' provides process isolation, eliminating mock pollution.
 */

import { PlatformSimulator } from '../shared/testHelpers'
import {
  assessSystemCapacity,
  getGPUCapabilities,
  getRecommendedConcurrency,
  _resetCapacityCache,
} from './system'

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
      // Use PlatformSimulator to get deterministic results in test environment
      const platform = new PlatformSimulator()
      platform.simulateMacOS(45)

      const capacity = await assessSystemCapacity()

      expect(capacity.details).toHaveProperty('availableMemory')
      expect(capacity.details).toHaveProperty('swapUsage')
      expect(capacity.details).toHaveProperty('currentLoad')
      expect(capacity.details).toHaveProperty('totalMemory')
      expect(capacity.details).toHaveProperty('usedMemory')

      expect(capacity.details.totalMemory).toBeGreaterThan(0)
      expect(capacity.details.availableMemory).toBeGreaterThanOrEqual(0)
      expect(capacity.details.swapUsage).toBeGreaterThanOrEqual(0)

      platform.restore()
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

  // ============================================
  // New tests for uncovered code paths
  // ============================================

  describe('cache behavior', () => {
    let platform: PlatformSimulator

    beforeEach(() => {
      _resetCapacityCache() // Clear any cached data from previous tests
    })

    afterEach(() => {
      platform?.restore()
      _resetCapacityCache()
    })

    test('should use cached capacity within TTL', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(45)

      const capacity1 = await assessSystemCapacity()
      const capacity2 = await assessSystemCapacity()

      // Second call should return exact same object (cached)
      expect(capacity2).toBe(capacity1)

      platform.restore()
    })

    test('should refresh cache after manual reset', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(45)

      await assessSystemCapacity()
      _resetCapacityCache()

      // Should trigger new assessment
      const capacity = await assessSystemCapacity()
      expect(capacity.pressureLevel).toBe('nominal')

      platform.restore()
    })
  })

  describe('platform-specific parsing - macOS', () => {
    let platform: PlatformSimulator

    beforeEach(() => {
      _resetCapacityCache()
    })

    afterEach(() => {
      platform?.restore()
      _resetCapacityCache()
    })

    test('should parse macOS memory with nominal pressure', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(45) // 45% free

      const capacity = await assessSystemCapacity()

      expect(capacity.pressureLevel).toBe('nominal')
      expect(capacity.canSpawnWorker).toBe(true)
      expect(capacity.details.totalMemory).toBeGreaterThan(0)

      platform.restore()
    })

    test('should parse macOS memory with warning pressure', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(15) // 15% free (< 20%)

      const capacity = await assessSystemCapacity()

      expect(capacity.pressureLevel).toBe('warning')

      platform.restore()
    })

    test('should parse macOS memory with critical pressure', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(3) // 3% free (< 5%)

      const capacity = await assessSystemCapacity()

      expect(capacity.pressureLevel).toBe('critical')
      expect(capacity.canSpawnWorker).toBe(false)

      platform.restore()
    })

    test('should detect swap activity on macOS', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(45, { swapIns: 1000, swapOuts: 500 })

      const capacity = await assessSystemCapacity()

      // Swap activity detected (binary indicator)
      expect(capacity.details.swapUsage).toBeGreaterThan(0)

      platform.restore()
    })

    test('should detect no swap activity on macOS', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(45, { swapIns: 0, swapOuts: 0 })

      const capacity = await assessSystemCapacity()

      expect(capacity.details.swapUsage).toBe(0)

      platform.restore()
    })

    test('should calculate CPU utilization correctly on macOS', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(45, { loadAvg: [4.0, 3.5, 3.0], cpuCount: 8 })

      const capacity = await assessSystemCapacity()

      // 4.0 / 8 = 50% utilization
      expect(capacity.cpuUtilization).toBeCloseTo(50, 1)
      expect(capacity.details.currentLoad).toBe(4.0)

      platform.restore()
    })

    test('should cap CPU utilization at 100% when overloaded', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(45, { loadAvg: [16.0, 14.0, 12.0], cpuCount: 8 })

      const capacity = await assessSystemCapacity()

      // 16.0 / 8 = 200% -> capped at 100%
      expect(capacity.cpuUtilization).toBe(100)

      platform.restore()
    })
  })

  describe('platform-specific parsing - Linux', () => {
    let platform: PlatformSimulator

    beforeEach(() => {
      _resetCapacityCache()
    })

    afterEach(() => {
      platform?.restore()
      _resetCapacityCache()
    })

    test('should parse Linux memory with nominal pressure', async () => {
      platform = new PlatformSimulator()
      platform.simulateLinux(50) // 50% used

      const capacity = await assessSystemCapacity()

      expect(capacity.pressureLevel).toBe('nominal')
      expect(capacity.canSpawnWorker).toBe(true)
      expect(capacity.details.totalMemory).toBeGreaterThan(0)

      platform.restore()
    })

    test('should parse Linux memory with warning pressure from high memory', async () => {
      platform = new PlatformSimulator()
      platform.simulateLinux(90) // 90% used (> 85%)

      const capacity = await assessSystemCapacity()

      expect(capacity.pressureLevel).toBe('warning')

      platform.restore()
    })

    test('should parse Linux memory with critical pressure from high swap', async () => {
      platform = new PlatformSimulator()
      platform.simulateLinux(70, { swapUsedPercent: 80 }) // 80% swap used (> 75%)

      const capacity = await assessSystemCapacity()

      expect(capacity.pressureLevel).toBe('critical')
      expect(capacity.canSpawnWorker).toBe(false)

      platform.restore()
    })

    test('should convert Linux memory from kB to bytes', async () => {
      platform = new PlatformSimulator()
      platform.simulateLinux(50)

      const capacity = await assessSystemCapacity()

      // Total should be 16000000 kB * 1024 = 16384000000 bytes
      expect(capacity.details.totalMemory).toBe(16000000 * 1024)

      platform.restore()
    })
  })

  describe('unsupported platform', () => {
    let platform: PlatformSimulator

    beforeEach(() => {
      _resetCapacityCache()
    })

    afterEach(() => {
      platform?.restore()
      _resetCapacityCache()
    })

    test('should fail open when platform unsupported', async () => {
      platform = new PlatformSimulator()
      platform.simulateUnsupportedPlatform('win32')

      const capacity = await assessSystemCapacity()

      // Fail open: allow workers when monitoring unavailable
      expect(capacity.canSpawnWorker).toBe(true)
      expect(capacity.pressureLevel).toBe('nominal')
      expect(capacity.cpuUtilization).toBe(0)
      expect(capacity.memoryUtilization).toBe(0)

      platform.restore()
    })
  })

  describe('command failure handling', () => {
    let platform: PlatformSimulator

    beforeEach(() => {
      _resetCapacityCache()
    })

    afterEach(() => {
      platform?.restore()
      _resetCapacityCache()
    })

    test('should handle command failures gracefully', async () => {
      platform = new PlatformSimulator()
      platform.simulateCommandFailure()

      const capacity = await assessSystemCapacity()

      // Should fail open
      expect(capacity.canSpawnWorker).toBe(true)
      expect(capacity.pressureLevel).toBe('nominal')

      platform.restore()
    })
  })

  describe('worker spawn composite conditions', () => {
    let platform: PlatformSimulator

    beforeEach(() => {
      _resetCapacityCache()
    })

    afterEach(() => {
      platform?.restore()
      _resetCapacityCache()
    })

    test('should allow worker spawn when all conditions met', async () => {
      platform = new PlatformSimulator()
      // Nominal: CPU < 70%, available > 15%, swap < 40%, not critical
      platform.simulateMacOS(45, { loadAvg: [3.0, 2.5, 2.0], cpuCount: 8 })

      const capacity = await assessSystemCapacity()

      expect(capacity.canSpawnWorker).toBe(true)

      platform.restore()
    })

    test('should block worker spawn on high CPU', async () => {
      platform = new PlatformSimulator()
      // CPU: 7.5 / 8 = 93.75% > 70%
      platform.simulateMacOS(45, { loadAvg: [7.5, 7.0, 6.5], cpuCount: 8 })

      const capacity = await assessSystemCapacity()

      expect(capacity.canSpawnWorker).toBe(false)
      expect(capacity.cpuUtilization).toBeGreaterThan(70)

      platform.restore()
    })

    test('should block worker spawn on low available memory', async () => {
      platform = new PlatformSimulator()
      // 10% free = 90% used, available = 10% < 15%
      platform.simulateMacOS(10, { loadAvg: [2.0, 2.0, 2.0], cpuCount: 8 })

      const capacity = await assessSystemCapacity()

      expect(capacity.canSpawnWorker).toBe(false)

      platform.restore()
    })

    test('should block worker spawn on critical pressure', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(3) // Critical pressure (< 5% free)

      const capacity = await assessSystemCapacity()

      expect(capacity.pressureLevel).toBe('critical')
      expect(capacity.canSpawnWorker).toBe(false)

      platform.restore()
    })
  })

  describe('getRecommendedConcurrency with pressure', () => {
    let platform: PlatformSimulator

    beforeEach(() => {
      _resetCapacityCache()
    })

    afterEach(() => {
      platform?.restore()
      _resetCapacityCache()
    })

    test('should return minimum on critical pressure', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(3) // Critical pressure

      const concurrency = await getRecommendedConcurrency(10, 1, 20)

      expect(concurrency).toBe(1) // minWorkers

      platform.restore()
    })

    test('should reduce concurrency by 50% on warning', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(15) // Warning pressure (< 20%)

      const concurrency = await getRecommendedConcurrency(10, 1, 20)

      expect(concurrency).toBe(5) // 10 * 0.5

      platform.restore()
    })

    test('should use static limit on nominal pressure', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(45) // Nominal pressure

      const concurrency = await getRecommendedConcurrency(8, 1, 20)

      expect(concurrency).toBe(8) // staticLimit

      platform.restore()
    })

    test('should cap at maxWorkers', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(45) // Nominal

      const concurrency = await getRecommendedConcurrency(100, 1, 10)

      expect(concurrency).toBe(10) // maxWorkers

      platform.restore()
    })

    test('should respect minWorkers during reduction', async () => {
      platform = new PlatformSimulator()
      platform.simulateMacOS(15) // Warning

      const concurrency = await getRecommendedConcurrency(10, 8, 20)

      // 10 * 0.5 = 5, but min is 8
      expect(concurrency).toBe(8) // minWorkers

      platform.restore()
    })
  })
})
