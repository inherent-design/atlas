/**
 * Cache Backend Tests
 *
 * Tests for ValkeyBackend implementation with graceful error handling.
 *
 * Test strategy:
 * - Mock Redis client (no actual Redis connection required)
 * - Test all CacheBackend interface methods
 * - Test error handling (connection failures, operation failures)
 * - Test TTL expiration behavior
 * - Test bulk operations
 *
 * @module services/storage/backends/__tests__/cache.test
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ValkeyBackend } from '../cache'
import type { ChunkMetadata, CollectionStats } from '../cache'
import type { ChunkPayload } from '../../../../shared/types'

// ============================================
// Mock Redis Client
// ============================================

/**
 * Mock Redis client for testing
 *
 * Simulates Redis operations with in-memory storage.
 */
class MockRedisClient {
  private store: Map<string, { value: string; expiresAt?: number }> = new Map()
  private connected: boolean = true

  // Simulate connection state
  setConnected(connected: boolean): void {
    this.connected = connected
  }

  async ping(): Promise<string> {
    if (!this.connected) {
      throw new Error('Connection refused')
    }
    return 'PONG'
  }

  async get(key: string): Promise<string | null> {
    if (!this.connected) {
      throw new Error('Connection refused')
    }

    const entry = this.store.get(key)
    if (!entry) return null

    // Check expiration
    if (entry.expiresAt && Date.now() > entry.expiresAt) {
      this.store.delete(key)
      return null
    }

    return entry.value
  }

  async set(key: string, value: string): Promise<'OK'> {
    if (!this.connected) {
      throw new Error('Connection refused')
    }

    this.store.set(key, { value })
    return 'OK'
  }

  async setex(key: string, ttl: number, value: string): Promise<'OK'> {
    if (!this.connected) {
      throw new Error('Connection refused')
    }

    const expiresAt = Date.now() + ttl * 1000
    this.store.set(key, { value, expiresAt })
    return 'OK'
  }

  async expire(key: string, ttl: number): Promise<number> {
    if (!this.connected) {
      throw new Error('Connection refused')
    }

    const entry = this.store.get(key)
    if (!entry) return 0

    const expiresAt = Date.now() + ttl * 1000
    this.store.set(key, { ...entry, expiresAt })
    return 1
  }

  async del(...keys: string[]): Promise<number> {
    if (!this.connected) {
      throw new Error('Connection refused')
    }

    let deleted = 0
    for (const key of keys) {
      if (this.store.delete(key)) {
        deleted++
      }
    }
    return deleted
  }

  async mget(...keys: string[]): Promise<(string | null)[]> {
    if (!this.connected) {
      throw new Error('Connection refused')
    }

    return keys.map((key) => {
      const entry = this.store.get(key)
      if (!entry) return null

      // Check expiration
      if (entry.expiresAt && Date.now() > entry.expiresAt) {
        this.store.delete(key)
        return null
      }

      return entry.value
    })
  }

  async keys(pattern: string): Promise<string[]> {
    if (!this.connected) {
      throw new Error('Connection refused')
    }

    // Simple pattern matching (only supports 'atlas:*')
    const prefix = pattern.replace('*', '')
    return Array.from(this.store.keys()).filter((key) => key.startsWith(prefix))
  }

  // Mock pipeline for ioredis compatibility
  pipeline(): MockRedisPipeline {
    return new MockRedisPipeline(this)
  }

  // Clear all data (for test cleanup)
  clear(): void {
    this.store.clear()
  }
}

/**
 * Mock Redis pipeline for bulk operations
 */
class MockRedisPipeline {
  private commands: Array<{ method: string; args: any[] }> = []

  constructor(private client: MockRedisClient) {}

  setex(key: string, ttl: number, value: string): this {
    this.commands.push({ method: 'setex', args: [key, ttl, value] })
    return this
  }

  async exec(): Promise<any[]> {
    const results = []
    for (const cmd of this.commands) {
      if (cmd.method === 'setex') {
        const result = await this.client.setex(cmd.args[0], cmd.args[1], cmd.args[2])
        results.push([null, result])
      }
    }
    return results
  }
}

// ============================================
// Test Setup
// ============================================

describe('ValkeyBackend', () => {
  let backend: ValkeyBackend
  let mockClient: MockRedisClient

  beforeEach(() => {
    mockClient = new MockRedisClient()

    // Create backend and inject mock client
    backend = new ValkeyBackend({
      host: 'localhost',
      port: 6379,
      password: undefined,
      defaultTTL: 3600,
    })

    // Inject mock client via private property
    ;(backend as any).client = mockClient
    ;(backend as any).connected = true
  })

  afterEach(() => {
    mockClient.clear()
  })

  // ============================================
  // QNTM Key Caching Tests
  // ============================================

  describe('QNTM Key Caching', () => {
    it('should cache and retrieve QNTM keys', async () => {
      const keys = ['@memory ~ consolidation', '@atlas ~ architecture', '@llm ~ generation']

      // Set keys
      await backend.setQNTMKeys(keys)

      // Get keys
      const cached = await backend.getAllQNTMKeys()
      expect(cached).toEqual(keys)
    })

    it('should return null on cache miss', async () => {
      const cached = await backend.getAllQNTMKeys()
      expect(cached).toBeNull()
    })

    it('should invalidate QNTM keys cache', async () => {
      const keys = ['@memory ~ consolidation']
      await backend.setQNTMKeys(keys)

      // Verify cached
      let cached = await backend.getAllQNTMKeys()
      expect(cached).toEqual(keys)

      // Invalidate
      await backend.invalidateQNTMKeys()

      // Verify cache miss
      cached = await backend.getAllQNTMKeys()
      expect(cached).toBeNull()
    })

    it('should handle connection errors gracefully (QNTM keys)', async () => {
      mockClient.setConnected(false)

      // Should return null, not throw
      const cached = await backend.getAllQNTMKeys()
      expect(cached).toBeNull()

      // Should not throw on write
      await expect(backend.setQNTMKeys(['@test'])).resolves.toBeUndefined()
    })
  })

  // ============================================
  // Chunk Caching Tests
  // ============================================

  describe('Chunk Caching', () => {
    it('should cache and retrieve chunk metadata', async () => {
      const chunk: ChunkMetadata = {
        id: 'chunk-123',
        original_text: 'Test chunk content',
        file_path: '/test/file.md',
        file_name: 'file.md',
        file_type: '.md',
        chunk_index: 0,
        total_chunks: 1,
        char_count: 100,
        qntm_keys: ['@test ~ content'],
        created_at: new Date().toISOString(),
        importance: 'normal',
        consolidation_level: 0,
      } as any

      // Set chunk
      await backend.setChunk('chunk-123', chunk)

      // Get chunk
      const cached = await backend.getChunk('chunk-123')
      expect(cached).toEqual(chunk)
    })

    it('should return null on chunk cache miss', async () => {
      const cached = await backend.getChunk('nonexistent')
      expect(cached).toBeNull()
    })

    it('should invalidate chunk cache', async () => {
      const chunk: ChunkMetadata = {
        id: 'chunk-123',
        original_text: 'Test',
      } as any

      await backend.setChunk('chunk-123', chunk)

      // Verify cached
      let cached = await backend.getChunk('chunk-123')
      expect(cached).toEqual(chunk)

      // Invalidate
      await backend.invalidateChunk('chunk-123')

      // Verify cache miss
      cached = await backend.getChunk('chunk-123')
      expect(cached).toBeNull()
    })

    it('should handle connection errors gracefully (chunks)', async () => {
      mockClient.setConnected(false)

      // Should return null, not throw
      const cached = await backend.getChunk('chunk-123')
      expect(cached).toBeNull()

      // Should not throw on write
      await expect(backend.setChunk('chunk-123', {} as any)).resolves.toBeUndefined()
    })
  })

  // ============================================
  // Stats Caching Tests
  // ============================================

  describe('Stats Caching', () => {
    it('should cache and retrieve collection stats', async () => {
      const stats: CollectionStats = {
        totalChunks: 100,
        totalFiles: 10,
        totalChars: 50000,
        avgChunkSize: 500,
        lastUpdated: new Date(),
      }

      // Set stats
      await backend.setStats(stats)

      // Get stats
      const cached = await backend.getStats()
      expect(cached).not.toBeNull()
      expect(cached!.totalChunks).toBe(100)
      expect(cached!.totalFiles).toBe(10)
      expect(cached!.lastUpdated).toBeInstanceOf(Date)
    })

    it('should return null on stats cache miss', async () => {
      const cached = await backend.getStats()
      expect(cached).toBeNull()
    })

    it('should invalidate stats cache', async () => {
      const stats: CollectionStats = {
        totalChunks: 100,
        totalFiles: 10,
        totalChars: 50000,
        avgChunkSize: 500,
        lastUpdated: new Date(),
      }

      await backend.setStats(stats)

      // Verify cached
      let cached = await backend.getStats()
      expect(cached).not.toBeNull()

      // Invalidate
      await backend.invalidateStats()

      // Verify cache miss
      cached = await backend.getStats()
      expect(cached).toBeNull()
    })

    it('should handle connection errors gracefully (stats)', async () => {
      mockClient.setConnected(false)

      // Should return null, not throw
      const cached = await backend.getStats()
      expect(cached).toBeNull()

      // Should not throw on write
      await expect(backend.setStats({} as any)).resolves.toBeUndefined()
    })
  })

  // ============================================
  // Bulk Operations Tests
  // ============================================

  describe('Bulk Operations', () => {
    it('should get multiple chunks (mget)', async () => {
      const mockPayload1: ChunkPayload = {
        original_text: 'Chunk 1',
        file_path: '/test/file1.ts',
        file_name: 'file1.ts',
        file_type: '.ts',
        chunk_index: 0,
        total_chunks: 1,
        char_count: 7,
        qntm_keys: ['test_key'],
        created_at: new Date().toISOString(),
        importance: 'normal',
        consolidation_level: 0,
      }
      const mockPayload2: ChunkPayload = {
        ...mockPayload1,
        original_text: 'Chunk 2',
        file_path: '/test/file2.ts',
        file_name: 'file2.ts',
      }
      const mockPayload3: ChunkPayload = {
        ...mockPayload1,
        original_text: 'Chunk 3',
        file_path: '/test/file3.ts',
        file_name: 'file3.ts',
      }

      const chunks = [
        { id: 'chunk-1', chunk: mockPayload1 },
        { id: 'chunk-2', chunk: mockPayload2 },
        { id: 'chunk-3', chunk: mockPayload3 },
      ]

      // Set chunks individually
      for (const { id, chunk } of chunks) {
        await backend.setChunk(id, chunk)
      }

      // Get all chunks
      const cached = await backend.mgetChunks(['chunk-1', 'chunk-2', 'chunk-3'])
      expect(cached).toHaveLength(3)
      expect(cached[0]?.original_text).toBe('Chunk 1')
      expect(cached[1]?.original_text).toBe('Chunk 2')
      expect(cached[2]?.original_text).toBe('Chunk 3')
    })

    it('should return null for cache misses in mget', async () => {
      const mockPayload: ChunkPayload = {
        original_text: 'Chunk 1',
        file_path: '/test/file.ts',
        file_name: 'file.ts',
        file_type: '.ts',
        chunk_index: 0,
        total_chunks: 1,
        char_count: 7,
        qntm_keys: ['test_key'],
        created_at: new Date().toISOString(),
        importance: 'normal',
        consolidation_level: 0,
      }

      await backend.setChunk('chunk-1', mockPayload)

      const cached = await backend.mgetChunks(['chunk-1', 'nonexistent', 'chunk-3'])
      expect(cached).toHaveLength(3)
      expect(cached[0]?.original_text).toBe('Chunk 1')
      expect(cached[1]).toBeNull()
      expect(cached[2]).toBeNull()
    })

    it('should set multiple chunks (mset)', async () => {
      const mockPayload1: ChunkPayload = {
        original_text: 'Chunk 1',
        file_path: '/test/file1.ts',
        file_name: 'file1.ts',
        file_type: '.ts',
        chunk_index: 0,
        total_chunks: 1,
        char_count: 7,
        qntm_keys: ['test_key'],
        created_at: new Date().toISOString(),
        importance: 'normal',
        consolidation_level: 0,
      }
      const mockPayload2: ChunkPayload = {
        ...mockPayload1,
        original_text: 'Chunk 2',
        file_path: '/test/file2.ts',
        file_name: 'file2.ts',
      }

      const chunks = [
        { id: 'chunk-1', chunk: mockPayload1 },
        { id: 'chunk-2', chunk: mockPayload2 },
      ]

      // Set all chunks
      await backend.msetChunks(chunks)

      // Verify all cached
      const cached1 = await backend.getChunk('chunk-1')
      const cached2 = await backend.getChunk('chunk-2')

      expect(cached1?.original_text).toBe('Chunk 1')
      expect(cached1?.file_path).toBe('/test/file1.ts')
      expect(cached2?.original_text).toBe('Chunk 2')
      expect(cached2?.file_path).toBe('/test/file2.ts')
    })

    it('should handle connection errors gracefully (bulk)', async () => {
      mockClient.setConnected(false)

      // Should return all nulls, not throw
      const cached = await backend.mgetChunks(['chunk-1', 'chunk-2'])
      expect(cached).toEqual([null, null])

      // Should not throw on write
      await expect(
        backend.msetChunks([{ id: 'chunk-1', chunk: {} as any }])
      ).resolves.toBeUndefined()
    })
  })

  // ============================================
  // Health Check Tests
  // ============================================

  describe('Health Check', () => {
    it('should pass health check when connected', async () => {
      await expect(backend.healthCheck()).resolves.toBeUndefined()
    })

    it('should fail health check when disconnected', async () => {
      mockClient.setConnected(false)

      await expect(backend.healthCheck()).rejects.toThrow('Cache health check failed')
    })
  })

  // ============================================
  // Cleanup Tests
  // ============================================

  describe('Cleanup', () => {
    it('should flush all cached data', async () => {
      // Add some data
      await backend.setQNTMKeys(['@test ~ key'])
      await backend.setChunk('chunk-1', { id: 'chunk-1' } as any)
      await backend.setStats({ totalChunks: 100 } as any)

      // Verify data exists
      let keys = await backend.getAllQNTMKeys()
      expect(keys).not.toBeNull()

      // Flush all
      await backend.flushAll()

      // Verify all data cleared
      keys = await backend.getAllQNTMKeys()
      const chunk = await backend.getChunk('chunk-1')
      const stats = await backend.getStats()

      expect(keys).toBeNull()
      expect(chunk).toBeNull()
      expect(stats).toBeNull()
    })

    it('should handle flush errors gracefully', async () => {
      mockClient.setConnected(false)

      // Should not throw
      await expect(backend.flushAll()).resolves.toBeUndefined()
    })
  })

  // ============================================
  // TTL Expiration Tests
  // ============================================

  describe('TTL Expiration', () => {
    it('should respect TTL for QNTM keys', async () => {
      // Create backend with short TTL
      const shortTTLBackend = new ValkeyBackend({
        host: 'localhost',
        port: 6379,
        password: undefined,
        defaultTTL: 1, // 1 second
      })
      ;(shortTTLBackend as any).client = mockClient
      ;(shortTTLBackend as any).connected = true

      // Set keys
      await shortTTLBackend.setQNTMKeys(['@test ~ key'])

      // Verify cached
      let cached = await shortTTLBackend.getAllQNTMKeys()
      expect(cached).not.toBeNull()

      // Wait for expiration (simulate)
      await new Promise((resolve) => setTimeout(resolve, 1100))

      // Verify expired (should be null)
      cached = await shortTTLBackend.getAllQNTMKeys()
      expect(cached).toBeNull()
    })

    it('should respect TTL for chunks', async () => {
      const shortTTLBackend = new ValkeyBackend({
        host: 'localhost',
        port: 6379,
        password: undefined,
        defaultTTL: 1,
      })
      ;(shortTTLBackend as any).client = mockClient
      ;(shortTTLBackend as any).connected = true

      await shortTTLBackend.setChunk('chunk-1', { id: 'chunk-1' } as any)

      // Verify cached
      let cached = await shortTTLBackend.getChunk('chunk-1')
      expect(cached).not.toBeNull()

      // Wait for expiration
      await new Promise((resolve) => setTimeout(resolve, 1100))

      // Verify expired
      cached = await shortTTLBackend.getChunk('chunk-1')
      expect(cached).toBeNull()
    })
  })

  // ============================================
  // Key Prefix Tests
  // ============================================

  describe('Key Prefix', () => {
    it('should use atlas: prefix for all keys', async () => {
      await backend.setQNTMKeys(['@test'])
      await backend.setChunk('chunk-1', { id: 'chunk-1' } as any)
      await backend.setStats({ totalChunks: 100 } as any)

      // Get all keys
      const keys = await mockClient.keys('atlas:*')

      // Should have 3 keys: qntm_keys, chunk:chunk-1, stats
      expect(keys.length).toBe(3)
      expect(keys).toContain('atlas:qntm_keys')
      expect(keys).toContain('atlas:chunk:chunk-1')
      expect(keys).toContain('atlas:stats')
    })
  })

  // ============================================
  // Error Recovery Tests
  // ============================================

  describe('Error Recovery', () => {
    it('should recover after connection loss', async () => {
      // Set data while connected
      await backend.setQNTMKeys(['@test ~ key'])

      // Disconnect
      mockClient.setConnected(false)
      ;(backend as any).connected = false

      // Operations should fail gracefully
      let cached = await backend.getAllQNTMKeys()
      expect(cached).toBeNull()

      // Reconnect mock client
      mockClient.setConnected(true)

      // Reconnect backend (simulates ensureConnected() succeeding)
      ;(backend as any).connected = true

      // Operations should work again
      await backend.setQNTMKeys(['@test ~ key'])
      cached = await backend.getAllQNTMKeys()
      expect(cached).toEqual(['@test ~ key'])
    })

    it('should handle JSON parse errors gracefully', async () => {
      // Manually set invalid JSON
      await mockClient.setex('atlas:chunk:invalid', 3600, '{invalid json}')

      // Should return null, not throw
      const cached = await backend.getChunk('invalid')
      expect(cached).toBeNull()
    })
  })
})
