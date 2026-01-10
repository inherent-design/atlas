/**
 * Tests for shared test helpers
 */
import {
  PlatformSimulator,
  TimeController,
  createMockChunkPayload,
  createMockQdrantPoint,
  createMockQdrantClient,
} from './testHelpers'
import { assessSystemCapacity, _resetCapacityCache } from '../core/system'

describe('PlatformSimulator', () => {
  let platform: PlatformSimulator

  beforeEach(() => {
    _resetCapacityCache()
  })

  afterEach(() => {
    platform?.restore()
    _resetCapacityCache()
  })

  test('simulateMacOS returns nominal pressure for high free memory', async () => {
    platform = new PlatformSimulator()
    platform.simulateMacOS(45) // 45% free

    const capacity = await assessSystemCapacity()

    expect(capacity.pressureLevel).toBe('nominal')
    expect(capacity.canSpawnWorker).toBe(true)
  })

  test('simulateMacOS returns warning pressure for low free memory', async () => {
    platform = new PlatformSimulator()
    platform.simulateMacOS(15) // 15% free (< 20%)

    const capacity = await assessSystemCapacity()

    expect(capacity.pressureLevel).toBe('warning')
  })

  test('simulateMacOS returns critical pressure for very low free memory', async () => {
    platform = new PlatformSimulator()
    platform.simulateMacOS(3) // 3% free (< 5%)

    const capacity = await assessSystemCapacity()

    expect(capacity.pressureLevel).toBe('critical')
    expect(capacity.canSpawnWorker).toBe(false)
  })

  test('simulateLinux returns nominal pressure', async () => {
    platform = new PlatformSimulator()
    platform.simulateLinux(50) // 50% used

    const capacity = await assessSystemCapacity()

    expect(capacity.pressureLevel).toBe('nominal')
  })

  test('simulateLinux returns warning pressure for high usage', async () => {
    platform = new PlatformSimulator()
    platform.simulateLinux(90) // 90% used (> 85%)

    const capacity = await assessSystemCapacity()

    expect(capacity.pressureLevel).toBe('warning')
  })

  test('restore reverts to original platform', () => {
    const originalPlatform = process.platform
    platform = new PlatformSimulator()
    platform.simulateMacOS(50)

    expect(process.platform).toBe('darwin')

    platform.restore()

    expect(process.platform).toBe(originalPlatform)
  })
})

describe('TimeController', () => {
  let time: TimeController

  afterEach(() => {
    time?.restore()
  })

  test('install overrides Date.now', () => {
    const startTime = 1000000
    time = new TimeController(startTime)
    time.install()

    expect(Date.now()).toBe(startTime)
  })

  test('advance moves time forward', () => {
    time = new TimeController(1000000)
    time.install()

    time.advance(500)
    expect(Date.now()).toBe(1000500)

    time.advance(500)
    expect(Date.now()).toBe(1001000)
  })

  test('restore reverts Date.now', () => {
    const realNow = Date.now()
    time = new TimeController(0)
    time.install()

    expect(Date.now()).toBe(0)

    time.restore()

    // Should be close to real time now
    expect(Date.now()).toBeGreaterThanOrEqual(realNow)
  })
})

describe('_resetCapacityCache', () => {
  let platform: PlatformSimulator

  beforeEach(() => {
    _resetCapacityCache()
  })

  afterEach(() => {
    platform?.restore()
    _resetCapacityCache()
  })

  test('allows immediate cache refresh', async () => {
    platform = new PlatformSimulator()
    platform.simulateMacOS(50)

    // First call
    const result1 = await assessSystemCapacity()
    expect(result1.pressureLevel).toBe('nominal')

    // Change mock but don't reset cache
    platform.restore()
    platform = new PlatformSimulator()
    platform.simulateMacOS(3) // Critical

    // Without reset, would return cached nominal
    const result2 = await assessSystemCapacity()
    expect(result2.pressureLevel).toBe('nominal') // Still cached

    // Reset cache
    _resetCapacityCache()

    // Now should get critical
    const result3 = await assessSystemCapacity()
    expect(result3.pressureLevel).toBe('critical')
  })
})

describe('Fixture Factories', () => {
  test('createMockChunkPayload returns valid payload', () => {
    const payload = createMockChunkPayload()

    expect(payload.original_text).toBeDefined()
    expect(payload.file_path).toBeDefined()
    expect(payload.qntm_keys).toBeInstanceOf(Array)
    expect(payload.consolidation_level).toBe(0)
  })

  test('createMockChunkPayload accepts overrides', () => {
    const payload = createMockChunkPayload({
      original_text: 'Custom text',
      consolidated: true,
    })

    expect(payload.original_text).toBe('Custom text')
    expect(payload.consolidated).toBe(true)
  })

  test('createMockQdrantPoint returns point with payload', () => {
    const point = createMockQdrantPoint({ id: 'test-123' })

    expect(point.id).toBe('test-123')
    expect(point.vector.text).toHaveLength(16) // Mock uses 16-dim vectors for efficiency
    expect(point.payload.original_text).toBeDefined()
  })

  test('createMockQdrantClient returns all methods', () => {
    const client = createMockQdrantClient()

    expect(client.getCollection).toBeDefined()
    expect(client.search).toBeDefined()
    expect(client.scroll).toBeDefined()
    expect(client.upsert).toBeDefined()
    expect(client.retrieve).toBeDefined()
    expect(client.setPayload).toBeDefined()
  })
})
