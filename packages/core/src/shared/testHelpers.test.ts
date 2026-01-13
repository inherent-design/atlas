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

// REMOVED: PlatformSimulator tests - requires spying on spawnSync which doesn't work in ESM

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

// REMOVED: _resetCapacityCache test - requires PlatformSimulator

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
