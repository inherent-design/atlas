/**
 * Cache Backend Interface and Valkey/Redis Implementation
 *
 * Purpose: Hot data caching layer for QNTM keys, chunk metadata, and collection stats.
 * Technology: Valkey (Redis-compatible), using Bun's native RedisClient.
 *
 * Design principles:
 * - Graceful degradation: Cache failures should not crash the app (return null)
 * - TTL-based expiration: Keys expire automatically based on config
 * - Key prefixing: All keys prefixed with 'atlas:' for namespace isolation
 * - Serialization: JSON for complex objects
 *
 * Key patterns:
 * - atlas:qntm_keys → JSON array of all QNTM keys
 * - atlas:chunk:{id} → JSON object of ChunkMetadata
 * - atlas:stats → JSON object of CollectionStats
 *
 * @module services/storage/backends/cache
 */

import Redis from 'ioredis'
import type { ChunkPayload } from '../../../shared/types.js'
import { createLogger } from '../../../shared/logger.js'

const log = createLogger('storage:cache')

// ============================================
// Type Definitions
// ============================================

/**
 * Chunk metadata (same as ChunkPayload but for caching context)
 */
export type ChunkMetadata = ChunkPayload

/**
 * Collection statistics (cached)
 */
export interface CollectionStats {
  totalChunks: number
  totalFiles: number
  totalChars: number
  avgChunkSize: number
  lastUpdated: Date
}

/**
 * Cache Backend Interface
 *
 * Provides caching for:
 * - QNTM keys (hot read, invalidate on new keys)
 * - Chunk metadata (hot read, write-through)
 * - Collection stats (hot read, invalidate on writes)
 */
export interface CacheBackend {
  // ============================================
  // QNTM Key Caching
  // ============================================

  /**
   * Get all QNTM keys from cache
   *
   * @returns Array of QNTM keys, or null if cache miss
   */
  getAllQNTMKeys(): Promise<string[] | null>

  /**
   * Set all QNTM keys in cache
   *
   * @param keys - Array of QNTM keys to cache
   */
  setQNTMKeys(keys: string[]): Promise<void>

  /**
   * Invalidate QNTM keys cache
   *
   * Called when new QNTM keys are added.
   */
  invalidateQNTMKeys(): Promise<void>

  // ============================================
  // Chunk Caching (Hot Data)
  // ============================================

  /**
   * Get chunk metadata from cache
   *
   * @param id - Chunk ID
   * @returns Chunk metadata, or null if cache miss
   */
  getChunk(id: string): Promise<ChunkMetadata | null>

  /**
   * Set chunk metadata in cache
   *
   * @param id - Chunk ID
   * @param chunk - Chunk metadata to cache
   */
  setChunk(id: string, chunk: ChunkMetadata): Promise<void>

  /**
   * Invalidate chunk metadata cache
   *
   * @param id - Chunk ID to invalidate
   */
  invalidateChunk(id: string): Promise<void>

  // ============================================
  // Stats Caching
  // ============================================

  /**
   * Get collection stats from cache
   *
   * @returns Collection stats, or null if cache miss
   */
  getStats(): Promise<CollectionStats | null>

  /**
   * Set collection stats in cache
   *
   * @param stats - Collection stats to cache
   */
  setStats(stats: CollectionStats): Promise<void>

  /**
   * Invalidate collection stats cache
   *
   * Called when chunks are added/removed/modified.
   */
  invalidateStats(): Promise<void>

  // ============================================
  // Bulk Operations
  // ============================================

  /**
   * Get multiple chunks from cache
   *
   * @param ids - Array of chunk IDs
   * @returns Array of chunk metadata (null for cache misses)
   */
  mgetChunks(ids: string[]): Promise<(ChunkMetadata | null)[]>

  /**
   * Set multiple chunks in cache
   *
   * @param chunks - Array of { id, chunk } to cache
   */
  msetChunks(chunks: Array<{ id: string; chunk: ChunkMetadata }>): Promise<void>

  // ============================================
  // Health Check
  // ============================================

  /**
   * Health check (verify connection)
   *
   * @throws Error if unhealthy
   */
  healthCheck(): Promise<void>

  // ============================================
  // Cleanup
  // ============================================

  /**
   * Flush all cached data
   *
   * WARNING: This clears ALL cached data. Use with caution.
   */
  flushAll(): Promise<void>
}

// ============================================
// Valkey/Redis Backend Implementation
// ============================================

/**
 * Valkey/Redis cache backend
 *
 * Uses ioredis client for Node.js compatibility.
 * Compatible with both Valkey and Redis (identical protocol).
 *
 * Configuration via ValkeyConfig:
 * - host: Valkey/Redis server host
 * - port: Valkey/Redis server port
 * - password: Optional password for authentication
 * - defaultTTL: Key expiration time (seconds)
 *
 * Error handling:
 * - Connection errors → log warning, return null (graceful degradation)
 * - Operation errors → log warning, return null
 * - Never crash the application
 */
export class ValkeyBackend implements CacheBackend {
  private client: Redis
  private connected: boolean = false
  private readonly keyPrefix = 'atlas:'
  private readonly ttl: number

  // Key patterns
  private readonly QNTM_KEYS_KEY = `${this.keyPrefix}qntm_keys`
  private readonly STATS_KEY = `${this.keyPrefix}stats`

  /**
   * Create Valkey backend instance
   *
   * @param config - Valkey configuration
   */
  constructor(
    private readonly config: {
      host: string
      port: number
      password?: string
      defaultTTL: number
    }
  ) {
    this.ttl = config.defaultTTL

    // Initialize ioredis client
    this.client = new Redis({
      host: config.host,
      port: config.port,
      password: config.password,
      retryStrategy: (times) => {
        // Exponential backoff with max 3s
        const delay = Math.min(times * 50, 3000)
        return delay
      },
      maxRetriesPerRequest: 3,
      lazyConnect: true, // Don't auto-connect, we'll do it in connect()
    })

    // Listen for connection events
    this.client.on('error', (err) => {
      log.warn('Redis connection error', { error: err.message })
      this.connected = false
    })

    this.client.on('close', () => {
      log.debug('Redis connection closed')
      this.connected = false
    })
  }

  /**
   * Initialize connection to Valkey/Redis
   *
   * Uses ioredis client with lazy connection.
   */
  private async connect(): Promise<void> {
    if (this.connected) return

    try {
      await this.client.connect()
      const pong = await this.client.ping()
      if (pong !== 'PONG') {
        throw new Error(`Unexpected PING response: ${pong}`)
      }
      this.connected = true
      log.info('Cache backend initialized', {
        host: this.config.host,
        port: this.config.port,
        ttl: this.ttl,
      })
    } catch (error) {
      log.warn('Failed to connect to Redis/Valkey, cache disabled', {
        error: error instanceof Error ? error.message : String(error),
        host: this.config.host,
        port: this.config.port,
      })
      this.connected = false
    }
  }

  /**
   * Ensure connection is established before operations
   */
  private async ensureConnected(): Promise<boolean> {
    if (!this.connected) {
      await this.connect()
    }
    return this.connected
  }

  // ============================================
  // QNTM Key Caching
  // ============================================

  async getAllQNTMKeys(): Promise<string[] | null> {
    try {
      if (!(await this.ensureConnected())) return null

      const cached = await this.client.get(this.QNTM_KEYS_KEY)
      if (!cached) {
        log.debug('QNTM keys cache miss')
        return null
      }

      const keys = JSON.parse(cached) as string[]
      log.debug('QNTM keys cache hit', { count: keys.length })
      return keys
    } catch (error) {
      log.warn('Failed to get QNTM keys from cache', {
        error: error instanceof Error ? error.message : String(error),
      })
      return null
    }
  }

  async setQNTMKeys(keys: string[]): Promise<void> {
    try {
      if (!(await this.ensureConnected())) return

      await this.client.setex(this.QNTM_KEYS_KEY, this.ttl, JSON.stringify(keys))
      log.debug('QNTM keys cached', { count: keys.length, ttl: this.ttl })
    } catch (error) {
      log.warn('Failed to cache QNTM keys', {
        error: error instanceof Error ? error.message : String(error),
      })
    }
  }

  async invalidateQNTMKeys(): Promise<void> {
    try {
      if (!(await this.ensureConnected())) return

      await this.client.del(this.QNTM_KEYS_KEY)
      log.debug('QNTM keys cache invalidated')
    } catch (error) {
      log.warn('Failed to invalidate QNTM keys cache', {
        error: error instanceof Error ? error.message : String(error),
      })
    }
  }

  // ============================================
  // Chunk Caching
  // ============================================

  async getChunk(id: string): Promise<ChunkMetadata | null> {
    try {
      if (!(await this.ensureConnected())) return null

      const key = this.getChunkKey(id)
      const cached = await this.client.get(key)
      if (!cached) {
        log.debug('Chunk cache miss', { id })
        return null
      }

      const chunk = JSON.parse(cached) as ChunkMetadata
      log.debug('Chunk cache hit', { id })
      return chunk
    } catch (error) {
      log.warn('Failed to get chunk from cache', {
        id,
        error: error instanceof Error ? error.message : String(error),
      })
      return null
    }
  }

  async setChunk(id: string, chunk: ChunkMetadata): Promise<void> {
    try {
      if (!(await this.ensureConnected())) return

      const key = this.getChunkKey(id)
      await this.client.setex(key, this.ttl, JSON.stringify(chunk))
      log.debug('Chunk cached', { id, ttl: this.ttl })
    } catch (error) {
      log.warn('Failed to cache chunk', {
        id,
        error: error instanceof Error ? error.message : String(error),
      })
    }
  }

  async invalidateChunk(id: string): Promise<void> {
    try {
      if (!(await this.ensureConnected())) return

      const key = this.getChunkKey(id)
      await this.client.del(key)
      log.debug('Chunk cache invalidated', { id })
    } catch (error) {
      log.warn('Failed to invalidate chunk cache', {
        id,
        error: error instanceof Error ? error.message : String(error),
      })
    }
  }

  // ============================================
  // Stats Caching
  // ============================================

  async getStats(): Promise<CollectionStats | null> {
    try {
      if (!(await this.ensureConnected())) return null

      const cached = await this.client.get(this.STATS_KEY)
      if (!cached) {
        log.debug('Stats cache miss')
        return null
      }

      const stats = JSON.parse(cached) as CollectionStats
      // Deserialize Date
      stats.lastUpdated = new Date(stats.lastUpdated)
      log.debug('Stats cache hit')
      return stats
    } catch (error) {
      log.warn('Failed to get stats from cache', {
        error: error instanceof Error ? error.message : String(error),
      })
      return null
    }
  }

  async setStats(stats: CollectionStats): Promise<void> {
    try {
      if (!(await this.ensureConnected())) return

      await this.client.setex(this.STATS_KEY, this.ttl, JSON.stringify(stats))
      log.debug('Stats cached', { ttl: this.ttl })
    } catch (error) {
      log.warn('Failed to cache stats', {
        error: error instanceof Error ? error.message : String(error),
      })
    }
  }

  async invalidateStats(): Promise<void> {
    try {
      if (!(await this.ensureConnected())) return

      await this.client.del(this.STATS_KEY)
      log.debug('Stats cache invalidated')
    } catch (error) {
      log.warn('Failed to invalidate stats cache', {
        error: error instanceof Error ? error.message : String(error),
      })
    }
  }

  // ============================================
  // Bulk Operations
  // ============================================

  async mgetChunks(ids: string[]): Promise<(ChunkMetadata | null)[]> {
    try {
      if (!(await this.ensureConnected())) {
        return ids.map(() => null)
      }

      const keys = ids.map((id) => this.getChunkKey(id))
      const cached = await this.client.mget(...keys)

      const chunks = cached.map((value: string | null, index: number): ChunkMetadata | null => {
        if (!value) {
          log.debug('Chunk cache miss (bulk)', { id: ids[index] })
          return null
        }
        try {
          return JSON.parse(value) as ChunkMetadata
        } catch {
          log.warn('Failed to parse cached chunk', { id: ids[index] })
          return null
        }
      })

      const hits = chunks.filter((c: ChunkMetadata | null) => c !== null).length
      log.debug('Bulk chunk cache lookup', { total: ids.length, hits, misses: ids.length - hits })

      return chunks
    } catch (error) {
      log.warn('Failed to get chunks from cache (bulk)', {
        error: error instanceof Error ? error.message : String(error),
      })
      return ids.map(() => null)
    }
  }

  async msetChunks(chunks: Array<{ id: string; chunk: ChunkMetadata }>): Promise<void> {
    try {
      if (!(await this.ensureConnected())) return

      // Parallel operations with Promise.all
      await Promise.all(
        chunks.map(async ({ id, chunk }) => {
          const key = this.getChunkKey(id)
          await this.client.set(key, JSON.stringify(chunk))
          await this.client.expire(key, this.ttl)
        })
      )

      log.debug('Bulk chunks cached', { count: chunks.length, ttl: this.ttl })
    } catch (error) {
      log.warn('Failed to cache chunks (bulk)', {
        error: error instanceof Error ? error.message : String(error),
      })
    }
  }

  // ============================================
  // Health Check
  // ============================================

  async healthCheck(): Promise<void> {
    try {
      if (!(await this.ensureConnected())) {
        throw new Error('Not connected to Redis/Valkey')
      }

      const pong = await this.client.ping()
      if (pong !== 'PONG') {
        throw new Error('PING failed: unexpected response')
      }
    } catch (error) {
      throw new Error(
        `Cache health check failed: ${error instanceof Error ? error.message : String(error)}`
      )
    }
  }

  // ============================================
  // Cleanup
  // ============================================

  async flushAll(): Promise<void> {
    try {
      if (!(await this.ensureConnected())) return

      // Only flush keys with our prefix (atlas:*)
      const keys = await this.client.keys(`${this.keyPrefix}*`)
      if (keys.length > 0) {
        await this.client.del(...keys)
        log.info('Cache flushed', { keysDeleted: keys.length })
      } else {
        log.info('Cache already empty')
      }
    } catch (error) {
      log.warn('Failed to flush cache', {
        error: error instanceof Error ? error.message : String(error),
      })
    }
  }

  /**
   * Close Redis connection
   *
   * Call this when shutting down to properly cleanup the connection.
   * Uses graceful quit() for clean shutdown with Node.js.
   */
  async close(): Promise<void> {
    try {
      if (this.connected) {
        await this.client.quit()
        this.connected = false
        log.debug('Redis connection closed')
      }
    } catch (error) {
      log.warn('Error closing Redis connection', {
        error: error instanceof Error ? error.message : String(error),
      })
      // Force disconnect if graceful quit fails
      this.client.disconnect()
    }
  }

  // ============================================
  // Helper Methods
  // ============================================

  /**
   * Generate chunk cache key
   */
  private getChunkKey(id: string): string {
    return `${this.keyPrefix}chunk:${id}`
  }
}

// ============================================
// Factory Function
// ============================================

/**
 * Create a Valkey/Redis cache backend
 *
 * @param config - Valkey configuration
 * @returns CacheBackend instance
 *
 * @example
 * ```typescript
 * import { createValkeyBackend } from './backends/cache.js'
 *
 * const cache = createValkeyBackend({
 *   host: 'localhost',
 *   port: 6379,
 *   password: undefined,
 *   defaultTTL: 3600, // 1 hour
 * })
 *
 * await cache.healthCheck()
 * const keys = await cache.getAllQNTMKeys()
 * ```
 */
export function createValkeyBackend(config: {
  host: string
  port: number
  password?: string
  defaultTTL: number
}): CacheBackend {
  return new ValkeyBackend(config)
}
