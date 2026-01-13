/**
 * Metadata backend interface and implementations
 *
 * Provides structured storage for chunk metadata, QNTM keys, and analytics.
 * PostgreSQL is required - no SQLite fallback.
 */

import { Kysely, PostgresDialect, sql as kysql } from 'kysely'
import { Pool } from 'pg'
import { createLogger } from '../../../shared/logger.js'
import type { ChunkPayload } from '../../../shared/types.js'
import { generateSourceId } from '../../../shared/utils.js'
import type { Database } from './database.types.js'

const postgresLog = createLogger('storage:postgres')

// ============================================
// Type Definitions
// ============================================

/**
 * Chunk metadata (without vector)
 */
export interface ChunkMetadata {
  id: string
  payload: ChunkPayload
}

/**
 * Metadata filter for querying chunks
 */
export interface MetadataFilter {
  /** Filter by file path pattern (SQL LIKE) */
  filePath?: string
  /** Filter by consolidation level */
  consolidationLevel?: number
  /** Filter by content type */
  contentType?: 'text' | 'code' | 'media'
  /** Filter by created after (ISO 8601) */
  createdAfter?: string
  /** Filter by created before (ISO 8601) */
  createdBefore?: string
  /** Limit results */
  limit?: number
  /** Offset for pagination */
  offset?: number
}

/**
 * QNTM key statistics
 */
export interface QNTMKeyStats {
  /** Total unique keys */
  totalKeys: number
  /** Most frequently used keys */
  topKeys: Array<{
    key: string
    usageCount: number
    lastSeenAt: string
  }>
  /** Least frequently used keys */
  leastUsedKeys: Array<{
    key: string
    usageCount: number
    lastSeenAt: string
  }>
}

/**
 * Collection statistics
 */
export interface CollectionStats {
  totalChunks: number
  totalFiles: number
  totalChars: number
  avgChunkSize: number
  lastUpdated: Date
}

/**
 * File statistics query parameters
 */
export interface FileStatsQuery {
  /** Limit results */
  limit?: number
  /** Order by field */
  orderBy?: 'chunk_count' | 'char_count' | 'last_ingested'
  /** Order direction */
  orderDir?: 'asc' | 'desc'
}

/**
 * File statistics
 */
export interface FileStats {
  filePath: string
  chunkCount: number
  charCount: number
  qntmKeyCount: number
  embeddingModel: string | null
  lastIngested: string
}

/**
 * Timeline parameters
 */
export interface TimelineParams {
  since?: Date
  until?: Date
  granularity?: 'hour' | 'day' | 'week' | 'month'
  limit?: number
}

/**
 * Timeline data point
 */
export interface TimelineDataPoint {
  timestamp: string
  chunkCount: number
  fileCount: number
  charCount: number
}

/**
 * Timeline data
 */
export interface TimelineData {
  points: TimelineDataPoint[]
  granularity: 'hour' | 'day' | 'week' | 'month'
  since: Date
  until: Date
}

// ============================================
// MetadataBackend Interface
// ============================================

/**
 * Metadata backend interface
 *
 * Provides structured storage for chunk metadata, QNTM keys, and analytics.
 */
export interface MetadataBackend {
  // Chunk operations
  upsertChunks(chunks: ChunkMetadata[]): Promise<void>
  getChunkById(id: string): Promise<ChunkMetadata | null>
  queryChunks(filter: MetadataFilter): Promise<ChunkMetadata[]>

  // QNTM key operations
  getAllQNTMKeys(): Promise<string[]>
  recordQNTMKeys(keys: string[], chunkId: string): Promise<void>
  getQNTMKeyStats(): Promise<QNTMKeyStats>

  // Analytics operations
  getCollectionStats(): Promise<CollectionStats>
  getFileStats(params?: FileStatsQuery): Promise<FileStats[]>
  getIngestionTimeline(params: TimelineParams): Promise<TimelineData>

  // Health check
  healthCheck(): Promise<void>
}

// ============================================
// PostgreSQLBackend Implementation
// ============================================

/**
 * PostgreSQL metadata backend
 *
 * For 100k+ chunks. Server-based, concurrent writes, advanced queries.
 * Uses Kysely with node-postgres driver.
 */
export class PostgreSQLBackend implements MetadataBackend {
  private config: PostgreSQLConfig
  private db: Kysely<Database>
  private pool: Pool

  constructor(config: PostgreSQLConfig) {
    this.config = config

    // Initialize PostgreSQL connection pool
    this.pool = new Pool({
      host: config.host,
      port: config.port,
      database: config.database,
      user: config.user,
      password: config.password,
      max: config.poolSize || 20,
      ssl: config.ssl ? { rejectUnauthorized: false } : undefined,
      connectionTimeoutMillis: config.connectTimeoutMs || 30000,
      idleTimeoutMillis: config.idleTimeoutMs || 30000,
    })

    // Initialize Kysely with PostgreSQL dialect
    this.db = new Kysely<Database>({
      dialect: new PostgresDialect({
        pool: this.pool,
      }),
    })

    postgresLog.info('Initialized PostgreSQL backend', {
      host: config.host,
      port: config.port,
      database: config.database,
      poolSize: config.poolSize || 20,
    })

    // Run migrations (async, but don't await - happens in background)
    this.runMigrations().catch((error) => {
      postgresLog.error('Migration failed', { error })
    })
  }

  /**
   * Run schema migrations
   */
  private async runMigrations(): Promise<void> {
    postgresLog.debug('Running migrations')

    try {
      // Create extension for UUID generation
      await kysql`CREATE EXTENSION IF NOT EXISTS "uuid-ossp"`.execute(this.db)

      // Create sources table
      await kysql`
        CREATE TABLE IF NOT EXISTS sources (
          id TEXT PRIMARY KEY,
          path TEXT UNIQUE NOT NULL,
          content_hash TEXT NOT NULL,
          file_mtime TIMESTAMP NOT NULL,
          status TEXT NOT NULL DEFAULT 'active',
          created_at TIMESTAMP NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
      `.execute(this.db)

      // Create chunks table
      await kysql`
        CREATE TABLE IF NOT EXISTS chunks (
          id TEXT PRIMARY KEY,
          source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
          chunk_index INTEGER NOT NULL,
          total_chunks INTEGER NOT NULL,
          char_count INTEGER NOT NULL,
          payload JSONB NOT NULL,

          embedding_model TEXT,
          embedding_strategy TEXT,
          content_type TEXT,

          consolidation_level INTEGER NOT NULL DEFAULT 0,
          consolidation_type TEXT,
          consolidation_direction TEXT,

          stability_score REAL,
          access_count INTEGER DEFAULT 0,
          last_accessed_at TIMESTAMP,
          superseded_by TEXT,
          deletion_eligible BOOLEAN DEFAULT FALSE,
          deletion_marked_at TIMESTAMP,

          created_at TIMESTAMP NOT NULL DEFAULT NOW(),
          UNIQUE(source_id, chunk_index)
        )
      `.execute(this.db)

      // Create indexes
      await kysql`CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id)`.execute(
        this.db
      )
      await kysql`CREATE INDEX IF NOT EXISTS idx_chunks_level ON chunks(consolidation_level)`.execute(
        this.db
      )
      await kysql`CREATE INDEX IF NOT EXISTS idx_chunks_created ON chunks(created_at DESC)`.execute(
        this.db
      )
      await kysql`CREATE INDEX IF NOT EXISTS idx_chunks_content_type ON chunks(content_type)`.execute(
        this.db
      )
      await kysql`CREATE INDEX IF NOT EXISTS idx_chunks_payload_gin ON chunks USING GIN(payload)`.execute(
        this.db
      )

      // QNTM keys table
      await kysql`
        CREATE TABLE IF NOT EXISTS qntm_keys (
          key TEXT PRIMARY KEY,
          first_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
          last_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
          usage_count INTEGER DEFAULT 1,
          last_used_in_chunk_id TEXT
        )
      `.execute(this.db)

      await kysql`CREATE INDEX IF NOT EXISTS idx_qntm_keys_usage ON qntm_keys(usage_count DESC)`.execute(
        this.db
      )
      await kysql`CREATE INDEX IF NOT EXISTS idx_qntm_keys_last_seen ON qntm_keys(last_seen_at DESC)`.execute(
        this.db
      )

      // Chunk-QNTM mapping
      await kysql`
        CREATE TABLE IF NOT EXISTS chunk_qntm_keys (
          chunk_id TEXT NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
          qntm_key TEXT NOT NULL REFERENCES qntm_keys(key) ON DELETE CASCADE,
          PRIMARY KEY (chunk_id, qntm_key)
        )
      `.execute(this.db)

      await kysql`CREATE INDEX IF NOT EXISTS idx_chunk_qntm_keys_key ON chunk_qntm_keys(qntm_key)`.execute(
        this.db
      )

      // Collection stats table
      await kysql`
        CREATE TABLE IF NOT EXISTS collection_stats (
          collection_name TEXT PRIMARY KEY,
          total_chunks INTEGER DEFAULT 0,
          total_files INTEGER DEFAULT 0,
          total_chars BIGINT DEFAULT 0,
          last_updated TIMESTAMP NOT NULL DEFAULT NOW()
        )
      `.execute(this.db)

      // File stats table
      await kysql`
        CREATE TABLE IF NOT EXISTS file_stats (
          file_path TEXT PRIMARY KEY,
          chunk_count INTEGER DEFAULT 0,
          char_count BIGINT DEFAULT 0,
          qntm_key_count INTEGER DEFAULT 0,
          embedding_model TEXT,
          last_ingested TIMESTAMP NOT NULL DEFAULT NOW()
        )
      `.execute(this.db)

      await kysql`CREATE INDEX IF NOT EXISTS idx_file_stats_last_ingested ON file_stats(last_ingested DESC)`.execute(
        this.db
      )

      // Enable TimescaleDB hypertables (if extension is available)
      try {
        // Check if TimescaleDB extension exists
        const extResult = await kysql`
          SELECT COUNT(*) as count FROM pg_extension WHERE extname = 'timescaledb'
        `.execute(this.db)

        const hasTimescale = (extResult.rows[0] as { count: string } | undefined)?.count
          ? Number((extResult.rows[0] as { count: string }).count) > 0
          : false

        if (hasTimescale) {
          // Check if chunks is already a hypertable
          const hypertableCheck = await kysql`
            SELECT COUNT(*) as count FROM timescaledb_information.hypertables
            WHERE hypertable_name = 'chunks'
          `.execute(this.db)

          const hypertableCount = (hypertableCheck.rows[0] as { count: string } | undefined)?.count
            ? Number((hypertableCheck.rows[0] as { count: string }).count)
            : 0

          if (hypertableCount === 0) {
            // Only try to create hypertable if table is empty
            const countResult = await kysql`SELECT COUNT(*) as count FROM chunks`.execute(this.db)
            const rowCount = (countResult.rows[0] as { count: string } | undefined)?.count
              ? Number((countResult.rows[0] as { count: string }).count)
              : 0

            if (rowCount === 0) {
              await kysql`SELECT create_hypertable('chunks', 'created_at')`.execute(this.db)
              postgresLog.info('TimescaleDB hypertable created for chunks')
            } else {
              postgresLog.debug(
                'Skipping hypertable conversion - table not empty. Use standard table for now.',
                { rowCount }
              )
            }
          } else {
            postgresLog.debug('TimescaleDB hypertable already exists for chunks')
          }
        } else {
          postgresLog.debug('TimescaleDB extension not installed, using standard table')
        }
      } catch (error) {
        const errMsg = error instanceof Error ? error.message : String(error)
        postgresLog.debug('TimescaleDB check failed, using standard table', { error: errMsg })
      }

      postgresLog.debug('Migrations complete')
    } catch (error) {
      postgresLog.error('Migration error', { error })
      throw error
    }
  }

  // ============================================
  // Chunk Operations
  // ============================================

  async upsertChunks(chunks: ChunkMetadata[]): Promise<void> {
    if (chunks.length === 0) return

    try {
      // Use PostgreSQL UPSERT (INSERT ... ON CONFLICT DO UPDATE)
      for (const chunk of chunks) {
        const p = chunk.payload

        // Generate source_id from file_path (deterministic UUID)
        const sourceId = generateSourceId(p.file_path)

        // Kysely properly handles JSONB - no need for Bun.SQL workarounds
        // Payload is stored as proper JSONB object type
        await this.db
          .insertInto('chunks')
          .values({
            id: chunk.id,
            source_id: sourceId,
            chunk_index: p.chunk_index,
            total_chunks: p.total_chunks,
            char_count: p.char_count,
            payload: JSON.stringify(chunk.payload) as any, // Cast to JSONB
            embedding_model: p.embedding_model || null,
            embedding_strategy: p.embedding_strategy || null,
            content_type: p.content_type || null,
            consolidation_level: p.consolidation_level,
            consolidation_type: p.consolidation_type || null,
            consolidation_direction: p.consolidation_direction || null,
            stability_score: p.stability_score || null,
            access_count: p.access_count || 0,
            last_accessed_at: p.last_accessed_at || null,
            superseded_by: p.superseded_by || null,
            deletion_eligible: p.deletion_eligible || false,
            deletion_marked_at: p.deletion_marked_at || null,
            created_at: p.created_at,
          })
          .onConflict((oc) =>
            oc.column('id').doUpdateSet({
              source_id: sourceId,
              chunk_index: p.chunk_index,
              total_chunks: p.total_chunks,
              char_count: p.char_count,
              payload: JSON.stringify(chunk.payload) as any,
              embedding_model: p.embedding_model || null,
              embedding_strategy: p.embedding_strategy || null,
              content_type: p.content_type || null,
              consolidation_level: p.consolidation_level,
              consolidation_type: p.consolidation_type || null,
              consolidation_direction: p.consolidation_direction || null,
              stability_score: p.stability_score || null,
              access_count: p.access_count || 0,
              last_accessed_at: p.last_accessed_at || null,
              superseded_by: p.superseded_by || null,
              deletion_eligible: p.deletion_eligible || false,
              deletion_marked_at: p.deletion_marked_at || null,
            })
          )
          .execute()
      }

      postgresLog.debug('Upserted chunks', { count: chunks.length })

      // Invalidate collection stats
      await this.invalidateCollectionStats()
    } catch (error) {
      postgresLog.error('Failed to upsert chunks', { error })
      throw error
    }
  }

  async getChunkById(id: string): Promise<ChunkMetadata | null> {
    try {
      const result = await this.db
        .selectFrom('chunks')
        .select(['id', 'payload'])
        .where('id', '=', id)
        .executeTakeFirst()

      if (!result) return null

      return {
        id: result.id,
        payload: result.payload,
      }
    } catch (error) {
      postgresLog.error('Failed to get chunk by ID', { id, error })
      throw error
    }
  }

  async queryChunks(filter: MetadataFilter): Promise<ChunkMetadata[]> {
    try {
      const limit = filter.limit || 100
      const offset = filter.offset || 0

      // Build query with Kysely
      let query = this.db.selectFrom('chunks').select(['id', 'payload'])

      // Apply filters
      if (filter.filePath) {
        // Use JSONB operators for file_path filtering
        query = query.where(kysql`payload->>'file_path'`, 'like', filter.filePath)
      }

      if (filter.consolidationLevel !== undefined) {
        query = query.where('consolidation_level', '=', filter.consolidationLevel)
      }

      if (filter.contentType) {
        query = query.where('content_type', '=', filter.contentType)
      }

      if (filter.createdAfter) {
        query = query.where('created_at', '>=', new Date(filter.createdAfter))
      }

      if (filter.createdBefore) {
        query = query.where('created_at', '<=', new Date(filter.createdBefore))
      }

      // Execute query with ordering and pagination
      const result = await query.orderBy('created_at', 'desc').limit(limit).offset(offset).execute()

      return result.map((row) => ({
        id: row.id,
        payload: row.payload,
      }))
    } catch (error) {
      postgresLog.error('Failed to query chunks', { filter, error })
      throw error
    }
  }

  // ============================================
  // Source Operations
  // ============================================

  async upsertSource(source: {
    id: string
    path: string
    contentHash: string
    fileMtime: Date
    status: 'active' | 'deleted'
  }): Promise<void> {
    try {
      await this.db
        .insertInto('sources')
        .values({
          id: source.id,
          path: source.path,
          content_hash: source.contentHash,
          file_mtime: source.fileMtime,
          status: source.status,
        })
        .onConflict((oc) =>
          oc.column('path').doUpdateSet((eb) => ({
            content_hash: source.contentHash,
            file_mtime: source.fileMtime,
            status: source.status,
          }))
        )
        .execute()

      postgresLog.debug('Upserted source', { path: source.path, id: source.id })
    } catch (error) {
      postgresLog.error('Failed to upsert source', { source, error })
      throw error
    }
  }

  async getSourceByPath(path: string): Promise<{
    id: string
    path: string
    contentHash: string
    fileMtime: Date
    status: 'active' | 'deleted'
  } | null> {
    try {
      const result = await this.db
        .selectFrom('sources')
        .select(['id', 'path', 'content_hash', 'file_mtime', 'status'])
        .where('path', '=', path)
        .executeTakeFirst()

      if (!result) return null

      return {
        id: result.id,
        path: result.path,
        contentHash: result.content_hash,
        fileMtime: new Date(result.file_mtime),
        status: result.status,
      }
    } catch (error) {
      postgresLog.error('Failed to get source by path', { path, error })
      throw error
    }
  }

  // ============================================
  // QNTM Key Operations
  // ============================================

  async getAllQNTMKeys(): Promise<string[]> {
    try {
      const result = await this.db.selectFrom('qntm_keys').select('key').orderBy('key').execute()
      return result.map((r) => r.key)
    } catch (error) {
      postgresLog.error('Failed to get all QNTM keys', { error })
      throw error
    }
  }

  async recordQNTMKeys(keys: string[], chunkId: string): Promise<void> {
    if (keys.length === 0) return

    try {
      // Use transaction for atomic operations
      await this.db.transaction().execute(async (trx) => {
        for (const key of keys) {
          // Upsert QNTM key
          await trx
            .insertInto('qntm_keys')
            .values({
              key,
              last_used_in_chunk_id: chunkId,
              usage_count: 1,
            })
            .onConflict((oc) =>
              oc.column('key').doUpdateSet((eb) => ({
                usage_count: kysql`qntm_keys.usage_count + 1` as any,
                last_used_in_chunk_id: chunkId,
              }))
            )
            .execute()

          // Insert mapping (ignore if exists)
          await trx
            .insertInto('chunk_qntm_keys')
            .values({
              chunk_id: chunkId,
              qntm_key: key,
            })
            .onConflict((oc) => oc.columns(['chunk_id', 'qntm_key']).doNothing())
            .execute()
        }
      })

      postgresLog.debug('Recorded QNTM keys', { count: keys.length, chunkId })
    } catch (error) {
      postgresLog.error('Failed to record QNTM keys', { error })
      throw error
    }
  }

  async getQNTMKeyStats(): Promise<QNTMKeyStats> {
    try {
      const totalResult = await this.db
        .selectFrom('qntm_keys')
        .select(kysql<number>`COUNT(*)`.as('count'))
        .executeTakeFirstOrThrow()

      const topKeysResult = await this.db
        .selectFrom('qntm_keys')
        .select(['key', 'usage_count', 'last_seen_at'])
        .orderBy('usage_count', 'desc')
        .limit(10)
        .execute()

      const leastUsedKeysResult = await this.db
        .selectFrom('qntm_keys')
        .select(['key', 'usage_count', 'last_seen_at'])
        .orderBy('usage_count', 'asc')
        .limit(10)
        .execute()

      return {
        totalKeys: Number(totalResult.count),
        topKeys: topKeysResult.map((k) => ({
          key: k.key,
          usageCount: k.usage_count,
          lastSeenAt: k.last_seen_at.toISOString(),
        })),
        leastUsedKeys: leastUsedKeysResult.map((k) => ({
          key: k.key,
          usageCount: k.usage_count,
          lastSeenAt: k.last_seen_at.toISOString(),
        })),
      }
    } catch (error) {
      postgresLog.error('Failed to get QNTM key stats', { error })
      throw error
    }
  }

  // ============================================
  // Analytics Operations
  // ============================================

  async getCollectionStats(): Promise<CollectionStats> {
    try {
      // Try cached stats first
      const cachedResult = await this.db
        .selectFrom('collection_stats')
        .select(['total_chunks', 'total_files', 'total_chars', 'last_updated'])
        .where('collection_name', '=', 'atlas')
        .executeTakeFirst()

      if (cachedResult) {
        return {
          totalChunks: cachedResult.total_chunks,
          totalFiles: cachedResult.total_files,
          totalChars: cachedResult.total_chars,
          avgChunkSize:
            cachedResult.total_chunks > 0
              ? cachedResult.total_chars / cachedResult.total_chunks
              : 0,
          lastUpdated: new Date(cachedResult.last_updated),
        }
      }

      // Compute stats
      const statsResult = await this.db
        .selectFrom('chunks')
        .select([
          kysql<number>`COUNT(*)`.as('total_chunks'),
          kysql<number>`COUNT(DISTINCT source_id)`.as('total_files'),
          kysql<number>`COALESCE(SUM(char_count), 0)`.as('total_chars'),
        ])
        .executeTakeFirstOrThrow()

      const totalChunks = Number(statsResult.total_chunks)
      const totalFiles = Number(statsResult.total_files)
      const totalChars = Number(statsResult.total_chars)

      // Cache stats
      await this.cacheCollectionStats({
        totalChunks,
        totalFiles,
        totalChars,
        avgChunkSize: totalChunks > 0 ? totalChars / totalChunks : 0,
        lastUpdated: new Date(),
      })

      return {
        totalChunks,
        totalFiles,
        totalChars,
        avgChunkSize: totalChunks > 0 ? totalChars / totalChunks : 0,
        lastUpdated: new Date(),
      }
    } catch (error) {
      postgresLog.error('Failed to get collection stats', { error })
      throw error
    }
  }

  async getFileStats(params?: FileStatsQuery): Promise<FileStats[]> {
    const limit = params?.limit || 100
    const orderBy = params?.orderBy || 'last_ingested'
    const orderDir = params?.orderDir || 'desc'

    try {
      const result = await this.db
        .selectFrom('file_stats')
        .select([
          'file_path',
          'chunk_count',
          'char_count',
          'qntm_key_count',
          'embedding_model',
          'last_ingested',
        ])
        .orderBy(orderBy, orderDir)
        .limit(limit)
        .execute()

      return result.map((r) => ({
        filePath: r.file_path,
        chunkCount: r.chunk_count,
        charCount: r.char_count,
        qntmKeyCount: r.qntm_key_count,
        embeddingModel: r.embedding_model,
        lastIngested: r.last_ingested.toISOString(),
      }))
    } catch (error) {
      postgresLog.error('Failed to get file stats', { error })
      throw error
    }
  }

  async getIngestionTimeline(params: TimelineParams): Promise<TimelineData> {
    const since = params.since || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
    const until = params.until || new Date()
    const granularity = params.granularity || 'day'
    const limit = params.limit || 1000

    try {
      const result = await this.db
        .selectFrom('chunks')
        .select([
          kysql<string>`DATE_TRUNC(${kysql.literal(granularity)}, created_at)`.as('timestamp'),
          kysql<number>`COUNT(*)`.as('chunk_count'),
          kysql<number>`COUNT(DISTINCT source_id)`.as('file_count'),
          kysql<number>`SUM(char_count)`.as('char_count'),
        ])
        .where('created_at', '>=', since)
        .where('created_at', '<=', until)
        .groupBy(kysql`DATE_TRUNC(${kysql.literal(granularity)}, created_at)`)
        .orderBy('timestamp', 'asc')
        .limit(limit)
        .execute()

      return {
        points: result.map((r) => ({
          timestamp: r.timestamp,
          chunkCount: Number(r.chunk_count),
          fileCount: Number(r.file_count),
          charCount: Number(r.char_count),
        })),
        granularity,
        since,
        until,
      }
    } catch (error) {
      postgresLog.error('Failed to get ingestion timeline', { error })
      throw error
    }
  }

  // ============================================
  // Health Check
  // ============================================

  async healthCheck(): Promise<void> {
    try {
      await kysql`SELECT 1`.execute(this.db)
    } catch (error) {
      postgresLog.error('Health check failed', { error })
      throw new Error(`PostgreSQL health check failed: ${error}`)
    }
  }

  // ============================================
  // Helper Methods
  // ============================================

  private async invalidateCollectionStats(): Promise<void> {
    try {
      await this.db.deleteFrom('collection_stats').where('collection_name', '=', 'atlas').execute()
    } catch (error) {
      // Ignore errors during invalidation
    }
  }

  private async cacheCollectionStats(stats: CollectionStats): Promise<void> {
    try {
      await this.db
        .insertInto('collection_stats')
        .values({
          collection_name: 'atlas',
          total_chunks: stats.totalChunks,
          total_files: stats.totalFiles,
          total_chars: stats.totalChars,
        })
        .onConflict((oc) =>
          oc.column('collection_name').doUpdateSet({
            total_chunks: stats.totalChunks,
            total_files: stats.totalFiles,
            total_chars: stats.totalChars,
          })
        )
        .execute()
    } catch (error) {
      // Ignore errors during caching
    }
  }

  /**
   * Get Kysely database instance
   *
   * Used by FileTracker and other services that need direct DB access.
   */
  getDatabase(): Kysely<Database> {
    return this.db
  }

  /**
   * Close PostgreSQL connection
   */
  async close(): Promise<void> {
    try {
      await this.db.destroy()
      await this.pool.end()
      postgresLog.debug('PostgreSQL connection closed')
    } catch (error) {
      postgresLog.error('Error closing PostgreSQL connection', { error })
    }
  }
}

/**
 * PostgreSQL configuration
 */
export interface PostgreSQLConfig {
  host: string
  port: number
  database: string
  user: string
  password?: string
  poolSize?: number
  ssl?: boolean
  connectTimeoutMs?: number
  idleTimeoutMs?: number
}
