/**
 * Storage Service - Multi-Tier Coordinator
 *
 * Coordinates all storage tiers:
 * - Vector: Qdrant (semantic similarity search)
 * - Metadata: PostgreSQL (structured queries, REQUIRED)
 * - Cache: Valkey/Redis (hot data, optional)
 * - Analytics: DuckDB (OLAP queries, optional)
 * - FullText: Meilisearch (keyword search, optional)
 */

import { BackendRegistry } from '../../shared/registry.js'
import { QdrantBackend } from './backends/qdrant.js'
import { PostgreSQLBackend } from './backends/metadata.js'
import type {
  StorageBackend,
  VectorPoint,
  StorageFilter,
  SearchResult,
  SearchParams,
  ScrollOptions,
} from './types.js'
import { EMBEDDING_DIM } from '../../shared/config.js'
import { createLogger } from '../../shared/logger.js'
import type { ChunkPayload } from '../../shared/types.js'
import type { AtlasConfig } from '../../shared/config.schema.js'
import { generateSourceId, hashContent } from '../../shared/utils.js'
import { join } from 'path'
import { homedir } from 'os'
import { statSync } from 'fs'
import type { Kysely } from 'kysely'
import type { Database } from './backends/database.types.js'

// Re-export HNSW utilities (still needed for batch operations)
export { disableHNSW, enableHNSW, isHNSWDisabled, withHNSWDisabled } from './hnsw.js'

// Re-export Qdrant client (for collection management)
export { getQdrantClient } from './client.js'

// Re-export types
export type * from './types.js'

const logger = createLogger('storage:service')

// ============================================
// Backend Interfaces (Placeholders)
// ============================================

/**
 * Source record for file tracking
 */
export interface SourceRecord {
  id: string
  path: string
  contentHash: string
  fileMtime: Date
  status: 'active' | 'deleted'
}

/**
 * Metadata backend interface (PostgreSQL only - required)
 */
export interface MetadataBackend {
  /** Upsert chunk metadata */
  upsertChunks(chunks: Array<{ id: string; payload: ChunkPayload }>): Promise<void>
  /** Get chunk by ID */
  getChunkById(id: string): Promise<ChunkPayload | null>
  /** Upsert source file record */
  upsertSource(source: SourceRecord): Promise<void>
  /** Get source by file path */
  getSourceByPath(path: string): Promise<SourceRecord | null>
  /** Get all QNTM keys */
  getAllQNTMKeys(): Promise<string[]>
  /** Record QNTM keys for a chunk */
  recordQNTMKeys(keys: string[], chunkId: string): Promise<void>
  /** Get collection stats */
  getCollectionStats(): Promise<CollectionStats>
  /** Health check */
  healthCheck(): Promise<void>
}

/**
 * Cache backend interface (Valkey/Redis)
 */
export interface CacheBackend {
  /** Get chunk from cache */
  getChunk(id: string): Promise<ChunkPayload | null>
  /** Set chunk in cache */
  setChunk(id: string, chunk: ChunkPayload): Promise<void>
  /** Invalidate chunk cache */
  invalidateChunk(id: string): Promise<void>
  /** Get all QNTM keys from cache */
  getAllQNTMKeys(): Promise<string[] | null>
  /** Set QNTM keys in cache */
  setQNTMKeys(keys: string[]): Promise<void>
  /** Invalidate QNTM keys cache */
  invalidateQNTMKeys(): Promise<void>
  /** Get collection stats from cache */
  getStats(): Promise<CollectionStats | null>
  /** Set collection stats in cache */
  setStats(stats: CollectionStats): Promise<void>
  /** Invalidate stats cache */
  invalidateStats(): Promise<void>
  /** Health check */
  healthCheck(): Promise<void>
}

/**
 * Analytics backend interface (DuckDB)
 */
export interface AnalyticsBackend {
  /** Query timeline data */
  queryTimeline(params: TimelineParams): Promise<TimelineData>
  /** Export to Parquet */
  export(params: ExportParams, metadata: MetadataBackend): Promise<ExportResult>
  /** Health check */
  healthCheck(): Promise<void>
}

/**
 * Full-text search backend interface (Meilisearch)
 */
export interface FullTextBackend {
  /** Index documents */
  index(
    docs: Array<{
      id: string
      original_text: string
      file_path: string
      file_name: string
      qntm_keys: string[]
      file_type?: string
      consolidation_level?: number
      content_type?: string
      created_at?: string
    }>
  ): Promise<void>
  /** Search documents */
  search(params: { query: string; limit?: number; filter?: string | string[] }): Promise<
    Array<{
      id: string
      original_text: string
      file_path: string
      score: number
    }>
  >
  /** Health check */
  healthCheck(): Promise<void>
}

// ============================================
// Supporting Types
// ============================================

export interface CollectionStats {
  totalChunks: number
  totalFiles: number
  totalChars: number
  avgChunkSize: number
  lastUpdated: Date
}

export interface TimelineParams {
  since?: Date
  until?: Date
  granularity?: 'hour' | 'day' | 'week' | 'month'
}

export interface TimelineData {
  entries: Array<{
    timestamp: Date
    count: number
  }>
}

export interface ExportParams {
  since?: Date
  until?: Date
  outputDir: string
  format?: 'parquet' | 'csv' | 'json'
}

export interface ExportResult {
  files: string[]
  rowCount: number
  durationMs: number
}

export interface HealthStatus {
  available: boolean
  latency?: number
  error?: string
}

// ============================================
// Multi-Tier Storage Service
// ============================================

/**
 * Enhanced Storage Service
 *
 * Coordinates all storage tiers with dual-write pattern for consistency.
 * Supports graceful degradation when optional tiers are disabled.
 */
export class StorageService {
  private config: AtlasConfig
  private vector: StorageBackend // Qdrant (required)
  private metadata: MetadataBackend | null // PostgreSQL (required)
  private cache: CacheBackend | null // Valkey/Redis (optional)
  private analytics: AnalyticsBackend | null // DuckDB (optional)
  private fulltext: FullTextBackend | null // Meilisearch (optional)

  constructor(config: AtlasConfig) {
    this.config = config
    this.vector = this.initializeVector()
    this.metadata = this.initializeMetadata()
    this.cache = this.initializeCache()
    this.analytics = this.initializeAnalytics()
    this.fulltext = this.initializeFullText()

    logger.info('Storage service initialized', {
      vector: 'qdrant',
      metadata: this.metadata ? 'enabled' : 'disabled',
      cache: this.cache ? 'enabled' : 'disabled',
      analytics: this.analytics ? 'enabled' : 'disabled',
      fulltext: this.fulltext ? 'enabled' : 'disabled',
    })
  }

  // ============================================
  // Initialization
  // ============================================

  private initializeVector(): StorageBackend {
    // Use existing Qdrant backend
    return new QdrantBackend({
      dimensions: EMBEDDING_DIM,
      distance: 'dot',
    })
  }

  private initializeMetadata(): MetadataBackend | null {
    // PostgreSQL configuration is required
    const postgresConfig = this.config.storage?.postgres

    if (!postgresConfig || !postgresConfig.host || !postgresConfig.database || !postgresConfig.user) {
      const errorMsg =
        'PostgreSQL configuration required - no fallback available. Add storage.postgres to atlas.config.ts with host, database, and user'
      logger.error(errorMsg)
      throw new Error(errorMsg)
    }

    // Initialize PostgreSQL backend
    logger.info('Initializing PostgreSQL metadata backend', {
      host: postgresConfig.host,
      database: postgresConfig.database,
    })
    // Type cast: PostgreSQLBackend implements MetadataBackend but uses ChunkMetadata internally
    // This is a known type mismatch that needs proper interface unification in the future
    return new PostgreSQLBackend({
      host: postgresConfig.host,
      port: postgresConfig.port ?? 5432,
      database: postgresConfig.database,
      user: postgresConfig.user,
      password: postgresConfig.password,
      poolSize: postgresConfig.poolSize,
      ssl: postgresConfig.ssl,
      connectTimeoutMs: postgresConfig.connectTimeoutMs,
      idleTimeoutMs: postgresConfig.idleTimeoutMs,
    }) as unknown as MetadataBackend
  }

  private initializeCache(): CacheBackend | null {
    const cacheConfig = this.config.storage?.cache

    if (!cacheConfig || cacheConfig === 'none') {
      logger.debug('Cache tier disabled (storage.cache = none or not configured)')
      return null
    }

    // Initialize Valkey/Redis cache backend
    try {
      const { ValkeyBackend } = require('./backends/cache')
      const valkeyConfig = {
        host: this.config.storage?.valkey?.host || 'localhost',
        port: this.config.storage?.valkey?.port || 6379,
        password: this.config.storage?.valkey?.password,
        defaultTTL: this.config.storage?.valkey?.defaultTTL || 3600,
      }
      logger.info('Initializing Valkey cache backend', valkeyConfig)
      return new ValkeyBackend(valkeyConfig)
    } catch (error) {
      logger.warn('Failed to initialize cache backend', error as Error)
      return null
    }
  }

  private initializeAnalytics(): AnalyticsBackend | null {
    const analyticsConfig = this.config.storage?.analytics

    if (!analyticsConfig || analyticsConfig === 'none') {
      logger.debug('Analytics tier disabled (storage.analytics = none or not configured)')
      return null
    }

    // Initialize DuckDB analytics backend
    try {
      const { DuckDBBackend } = require('./backends/analytics')
      const dbPath =
        this.config.storage?.duckdb?.dbPath ||
        join(homedir(), '.atlas', 'daemon', 'atlas_analytics.duckdb')
      logger.info('Initializing DuckDB analytics backend', { dbPath })
      return new DuckDBBackend({ dbPath })
    } catch (error) {
      logger.warn('Failed to initialize analytics backend', error as Error)
      return null
    }
  }

  private initializeFullText(): FullTextBackend | null {
    const fulltextConfig = this.config.storage?.fulltext

    if (!fulltextConfig || fulltextConfig === 'none') {
      logger.debug('Full-text tier disabled (storage.fulltext = none or not configured)')
      return null
    }

    // Initialize Meilisearch full-text backend
    try {
      const { MeilisearchBackend } = require('./backends/fulltext')
      const meilisearchConfig = this.config.storage?.meilisearch || {
        host: 'http://localhost:7700',
      }
      logger.info('Initializing Meilisearch full-text backend', meilisearchConfig)
      return new MeilisearchBackend(meilisearchConfig)
    } catch (error) {
      logger.warn('Failed to initialize full-text backend', error as Error)
      return null
    }
  }

  // ============================================
  // Vector Operations (Qdrant)
  // ============================================

  /**
   * Upsert vectors with dual-write pattern
   *
   * Writes to:
   * 1. Qdrant (vectors + payload)
   * 2. Metadata DB (payload only, when implemented)
   * 3. Cache (invalidate stats)
   * 4. Full-text index (text content)
   */
  async upsertVectors(collection: string, points: VectorPoint[]): Promise<void> {
    logger.debug('Upserting vectors', { collection, count: points.length })

    // 1. Write vectors to Qdrant (primary)
    await this.vector.upsert(collection, points)
    logger.debug('Vectors written to Qdrant', { count: points.length })

    // 2. Extract unique sources and upsert them to PostgreSQL
    if (this.metadata) {
      const sources = this.extractSources(points)
      for (const source of sources) {
        await this.metadata.upsertSource(source)
      }
      logger.debug('Sources upserted', { count: sources.length })

      // 3. Write chunk metadata to PostgreSQL
      await this.metadata.upsertChunks(
        points.map((p) => ({
          id: p.id,
          payload: p.payload,
        }))
      )
      logger.debug('Metadata written to metadata DB', { count: points.length })
    }

    // 4. Invalidate cache (stats and QNTM keys changed)
    if (this.cache) {
      await this.cache.invalidateStats()
      await this.cache.invalidateQNTMKeys()
      logger.debug('Cache invalidated (stats + QNTM keys)')

      // Invalidate specific chunks being updated
      for (const point of points) {
        await this.cache.invalidateChunk(point.id)
      }
      logger.debug('Chunk caches invalidated', { count: points.length })
    }

    // 5. Update full-text index
    if (this.fulltext) {
      await this.fulltext.index(
        points.map((p) => ({
          id: p.id,
          original_text: p.payload.original_text,
          file_path: p.payload.file_path,
          file_name: p.payload.file_name,
          qntm_keys: p.payload.qntm_keys,
          file_type: p.payload.file_type,
          consolidation_level: p.payload.consolidation_level,
          content_type: p.payload.content_type,
          created_at: p.payload.created_at,
        }))
      )
      logger.debug('Full-text index updated', { count: points.length })
    }

    // 6. Update analytics backend
    if (this.analytics) {
      const analyticsData = points.map((p) => ({
        id: p.id,
        file_path: p.payload.file_path,
        chunk_index: p.payload.chunk_index,
        total_chunks: p.payload.total_chunks,
        char_count: p.payload.char_count,
        qntm_keys: p.payload.qntm_keys,
        embedding_model: p.payload.embedding_model,
        embedding_strategy: p.payload.embedding_strategy,
        content_type: p.payload.content_type,
        consolidation_level: p.payload.consolidation_level,
        created_at: p.payload.created_at,
      }))

      // Import metadata from analytics backend
      const { DuckDBBackend } = await import('./backends/analytics')
      if (this.analytics instanceof DuckDBBackend && 'insertChunks' in this.analytics) {
        await (this.analytics as any).insertChunks(analyticsData)
        logger.debug('Analytics backend updated', { count: analyticsData.length })
      }
    }
  }

  /**
   * Extract unique sources from vector points
   */
  private extractSources(points: VectorPoint[]): SourceRecord[] {
    const sourceMap = new Map<string, SourceRecord>()

    for (const point of points) {
      const filePath = point.payload.file_path
      if (!sourceMap.has(filePath)) {
        const sourceId = generateSourceId(filePath)

        // Try to get file mtime, fallback to created_at from payload
        let fileMtime: Date
        try {
          const stats = statSync(filePath)
          fileMtime = stats.mtime
        } catch {
          // File may not exist (e.g., during migration from Qdrant)
          fileMtime = new Date(point.payload.created_at)
        }

        // Compute content hash from all chunks of this file
        const allChunksFromFile = points.filter((p) => p.payload.file_path === filePath)
        const contentText = allChunksFromFile.map((p) => p.payload.original_text).join('\n')
        const contentHash = hashContent(contentText)

        sourceMap.set(filePath, {
          id: sourceId,
          path: filePath,
          contentHash,
          fileMtime,
          status: 'active',
        })
      }
    }

    return Array.from(sourceMap.values())
  }

  /**
   * Search vectors semantically
   */
  async searchSemantic(collection: string, params: SearchParams): Promise<SearchResult[]> {
    return await this.vector.search(collection, params)
  }

  /**
   * Full-text search with payload hydration
   *
   * Searches Meilisearch for keyword matches, then hydrates full payloads
   * from the metadata backend.
   */
  async fullTextSearch(
    query: string,
    options: { limit: number; filters?: string }
  ): Promise<Array<{ id: string; payload: ChunkPayload }>> {
    if (!this.fulltext) {
      logger.warn('Full-text search requested but fulltext backend not configured')
      return []
    }

    // Search in Meilisearch
    const results = await this.fulltext.search({
      query,
      limit: options.limit,
      filter: options.filters,
    })

    logger.debug('Full-text search complete', { hits: results.length })

    // Hydrate payloads from metadata backend
    const chunks = await Promise.all(
      results.map(async (hit) => {
        const payload = await this.getChunkById('atlas', hit.id)
        if (!payload) {
          logger.warn('Chunk not found in metadata backend', { id: hit.id })
          return null
        }
        return { id: hit.id, payload }
      })
    )

    // Filter out null results (chunks not found)
    return chunks.filter((c): c is { id: string; payload: ChunkPayload } => c !== null)
  }

  private mergeResults(
    semantic: SearchResult[],
    keyword: SearchResult[],
    limit: number
  ): SearchResult[] {
    const seen = new Set<string>()
    const merged: SearchResult[] = []

    // Add semantic results first (higher priority)
    for (const result of semantic) {
      if (!seen.has(result.id)) {
        merged.push(result)
        seen.add(result.id)
      }
    }

    // Add keyword results (fill remaining slots)
    for (const result of keyword) {
      if (!seen.has(result.id)) {
        merged.push(result)
        seen.add(result.id)
      }
      if (merged.length >= limit) break
    }

    return merged.slice(0, limit)
  }

  // ============================================
  // Metadata Operations
  // ============================================

  /**
   * Get chunk by ID with read-through cache
   */
  async getChunkById(collection: string, id: string): Promise<ChunkPayload | null> {
    // Try cache first
    if (this.cache) {
      const cached = await this.cache.getChunk(id)
      if (cached) {
        logger.debug('Cache hit for chunk', { id })
        return cached
      }
    }

    // Fallback to metadata DB
    if (this.metadata) {
      const chunk = await this.metadata.getChunkById(id)

      // Populate cache
      if (this.cache && chunk) {
        await this.cache.setChunk(id, chunk)
      }

      return chunk
    }

    // Fallback to vector backend (retrieve point)
    logger.debug('Falling back to vector backend for chunk', { id })
    const points = await this.vector.retrieve(collection, [id])
    return points.length > 0 && points[0] ? points[0].payload : null
  }

  /**
   * Get all QNTM keys
   */
  async getAllQNTMKeys(collection: string): Promise<string[]> {
    // Try cache first
    if (this.cache) {
      const cached = await this.cache.getAllQNTMKeys()
      if (cached) {
        logger.debug('Cache hit for QNTM keys', { count: cached.length })
        return cached
      }
    }

    // Fallback to metadata DB
    if (this.metadata) {
      const keys = await this.metadata.getAllQNTMKeys()

      // Populate cache
      if (this.cache) {
        await this.cache.setQNTMKeys(keys)
      }

      return keys
    }

    // Fallback to vector backend (scroll all points)
    logger.warn('Falling back to vector backend for QNTM keys (SLOW - implement metadata backend)')
    const allKeys = new Set<string>()
    let offset: string | null = null

    while (true) {
      const batch = await this.vector.scroll(collection, {
        limit: 100,
        offset,
        withPayload: true,
        withVector: false,
      })

      for (const point of batch.points) {
        if (point.payload?.qntm_keys) {
          for (const key of point.payload.qntm_keys) {
            allKeys.add(key)
          }
        }
      }

      offset = batch.nextOffset
      if (!offset) break
    }

    const keys = Array.from(allKeys).sort()
    logger.debug('QNTM keys fetched from vector backend', { count: keys.length })
    return keys
  }

  /**
   * Get collection stats
   */
  async getCollectionStats(collection: string): Promise<CollectionStats> {
    // Try cache first
    if (this.cache) {
      const cached = await this.cache.getStats()
      if (cached) {
        logger.debug('Cache hit for collection stats')
        return cached
      }
    }

    // Fallback to metadata DB
    if (this.metadata) {
      const stats = await this.metadata.getCollectionStats()

      // Populate cache
      if (this.cache) {
        await this.cache.setStats(stats)
      }

      return stats
    }

    // Fallback to vector backend (scroll all points)
    logger.warn(
      'Falling back to vector backend for collection stats (SLOW - implement metadata backend)'
    )
    let totalChunks = 0
    let totalChars = 0
    const files = new Set<string>()
    let offset: string | null = null

    while (true) {
      const batch = await this.vector.scroll(collection, {
        limit: 100,
        offset,
        withPayload: true,
        withVector: false,
      })

      for (const point of batch.points) {
        totalChunks++
        if (point.payload?.char_count) {
          totalChars += point.payload.char_count
        }
        if (point.payload?.file_path) {
          files.add(point.payload.file_path)
        }
      }

      offset = batch.nextOffset
      if (!offset) break
    }

    const stats: CollectionStats = {
      totalChunks,
      totalFiles: files.size,
      totalChars,
      avgChunkSize: totalChunks > 0 ? totalChars / totalChunks : 0,
      lastUpdated: new Date(),
    }

    logger.debug('Collection stats fetched from vector backend', stats)
    return stats
  }

  /**
   * Check if analytics backend is available
   */
  hasAnalytics(): boolean {
    return this.analytics !== null
  }

  /**
   * Query timeline data from analytics backend
   */
  async queryTimeline(params: TimelineParams): Promise<TimelineData> {
    if (!this.analytics) {
      throw new Error('Analytics backend not configured')
    }

    return await this.analytics.queryTimeline(params)
  }

  /**
   * Export analytics data
   */
  async exportAnalytics(params: ExportParams): Promise<ExportResult> {
    if (!this.analytics) {
      throw new Error('Analytics backend not configured')
    }

    if (!this.metadata) {
      throw new Error('Metadata backend not configured (required for analytics export)')
    }

    // Call the export method as defined in the interface
    return await this.analytics.export(params, this.metadata)
  }

  // ============================================
  // Health Check
  // ============================================

  /**
   * Health check across all tiers
   */
  async health(): Promise<{
    overall: 'healthy' | 'degraded' | 'unhealthy'
    services: {
      vector: HealthStatus
      metadata: HealthStatus | null
      cache: HealthStatus | null
      analytics: HealthStatus | null
      fulltext: HealthStatus | null
    }
  }> {
    const [vector, metadata, cache, analytics, fulltext] = await Promise.all([
      this.checkHealth(this.vector),
      this.metadata ? this.checkHealth(this.metadata) : null,
      this.cache ? this.checkHealth(this.cache) : null,
      this.analytics ? this.checkHealth(this.analytics) : null,
      this.fulltext ? this.checkHealth(this.fulltext) : null,
    ])

    // Calculate overall health
    let overall: 'healthy' | 'degraded' | 'unhealthy'
    if (!vector.available) {
      overall = 'unhealthy' // Vector DB is critical
    } else if (metadata && !metadata.available) {
      overall = 'degraded' // Metadata DB is important but not critical
    } else {
      overall = 'healthy'
    }

    return {
      overall,
      services: {
        vector,
        metadata,
        cache,
        analytics,
        fulltext,
      },
    }
  }

  private async checkHealth(backend: any): Promise<HealthStatus> {
    const start = Date.now()
    try {
      await backend.healthCheck()
      return {
        available: true,
        latency: Date.now() - start,
      }
    } catch (error) {
      return {
        available: false,
        error: error instanceof Error ? error.message : String(error),
      }
    }
  }

  /**
   * Get vector backend (for existing code)
   */
  getVectorBackend(): StorageBackend {
    return this.vector
  }

  /**
   * Get Kysely database instance from PostgreSQL backend
   *
   * Used by FileTracker and other services that need direct DB access.
   * Throws if metadata backend is not initialized.
   */
  getDatabase(): Kysely<Database> {
    if (!this.metadata) {
      throw new Error('PostgreSQL metadata backend not initialized')
    }

    if ('getDatabase' in this.metadata && typeof this.metadata.getDatabase === 'function') {
      return (this.metadata as any).getDatabase()
    }

    throw new Error('Metadata backend does not support getDatabase()')
  }

  /**
   * Shutdown storage service and close all backend connections
   *
   * Call this during application shutdown to properly cleanup connections.
   * Note: Bun 1.3.5 has issues with SQL.close(), so PostgreSQL uses workaround.
   */
  async shutdown(): Promise<void> {
    logger.info('Shutting down storage service')

    // Close cache (Redis/Valkey) - safe to close
    if (this.cache && 'close' in this.cache && typeof this.cache.close === 'function') {
      try {
        ;(this.cache as { close(): void }).close()
        logger.debug('Cache backend closed')
      } catch (error) {
        logger.warn('Error closing cache backend', {
          error: error instanceof Error ? error.message : String(error),
        })
      }
    }

    // Close analytics (DuckDB) - safe to close
    if (this.analytics && 'close' in this.analytics && typeof this.analytics.close === 'function') {
      try {
        await (this.analytics as { close(): Promise<void> }).close()
        logger.debug('Analytics backend closed')
      } catch (error) {
        logger.warn('Error closing analytics backend', {
          error: error instanceof Error ? error.message : String(error),
        })
      }
    }

    // Close metadata (PostgreSQL) - uses Bun 1.3.5 workaround (no-op)
    if (this.metadata && 'close' in this.metadata && typeof this.metadata.close === 'function') {
      try {
        ;(this.metadata as { close(): void }).close()
        logger.debug('Metadata backend cleanup acknowledged')
      } catch (error) {
        logger.warn('Error closing metadata backend', {
          error: error instanceof Error ? error.message : String(error),
        })
      }
    }

    // Fulltext (Meilisearch) - HTTP client, no explicit close needed
    if (this.fulltext) {
      logger.debug('Fulltext backend uses HTTP client (no explicit close needed)')
    }

    // Vector (Qdrant) - HTTP client, no explicit close needed
    logger.debug('Vector backend uses HTTP client (no explicit close needed)')

    logger.info('Storage service shutdown complete')
  }
}

// ============================================
// Singleton Instance
// ============================================

let storageServiceInstance: StorageService | null = null

/**
 * Get or create the storage service instance
 */
export function getStorageService(config?: AtlasConfig): StorageService {
  if (!storageServiceInstance && config) {
    storageServiceInstance = new StorageService(config)
  }

  if (!storageServiceInstance) {
    throw new Error('Storage service not initialized. Call getStorageService(config) first.')
  }

  return storageServiceInstance
}

/**
 * Get storage backend (convenience wrapper)
 */
export function getStorageBackend(): StorageBackend {
  return getStorageService().getVectorBackend()
}
