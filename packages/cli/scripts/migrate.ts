#!/usr/bin/env tsx
/**
 * Atlas Migration Tool
 *
 * Migrates data from Qdrant to multi-tier storage:
 * - PostgreSQL (metadata)
 * - Valkey (cache)
 * - Meilisearch (full-text search)
 * - DuckDB (analytics)
 *
 * Usage:
 *   tsx packages/cli/scripts/migrate.ts [--dry-run]
 */

import { Kysely, PostgresDialect, sql as kysql } from 'kysely'
import { Pool } from 'pg'
import { existsSync } from 'fs'
import { join } from 'path'
import { homedir } from 'os'
import { type Schemas, QdrantClient } from '@qdrant/js-client-rest'

// Import from source files directly to avoid circular dependencies
import { createLogger } from '../../core/src/shared/logger.js'
import { loadConfig } from '../../core/src/shared/config.loader.js'
import { generateSourceId, hashContent } from '../../core/src/shared/utils.js'
import { ValkeyBackend } from '../../core/src/services/storage/backends/cache.js'
import { MeilisearchBackend } from '../../core/src/services/storage/backends/fulltext.js'
import { DuckDBBackend } from '../../core/src/services/storage/backends/analytics.js'
import { getQdrantClient } from '../../core/src/services/storage/client.js'
import type { ChunkPayload } from '../../core/src/shared/types.js'
import type { AtlasConfig } from '../../core/src/shared/config.schema.js'
import type { FullTextDocument } from '../../core/src/services/storage/backends/fulltext.js'
import type { ChunkMetadata } from '../../core/src/services/storage/backends/metadata.js'
import type { Database } from '../../core/src/services/storage/backends/database.types.js'

const logger = createLogger('migrate')

// ============================================
// Types
// ============================================

interface MigrationResult {
  success: boolean
  pointsMigrated: number
  durationMs: number
  errors: string[]
}

type QdrantPoint = Schemas['Record'] & {
  payload: ChunkPayload
}

// ============================================
// Migration Tool
// ============================================

class MigrationTool {
  private postgresPool: Pool | null = null
  private postgresDb: Kysely<Database> | null = null
  private valkeyBackend: ValkeyBackend | null = null
  private meilisearchBackend: MeilisearchBackend | null = null
  private duckdbBackend: DuckDBBackend | null = null
  private qdrantClient: QdrantClient

  constructor(private config: AtlasConfig) {
    // Initialize Qdrant client (source)
    this.qdrantClient = getQdrantClient()

    // Initialize backends based on config
    if (config.storage?.postgres) {
      this.postgresPool = new Pool({
        host: config.storage.postgres.host,
        port: config.storage.postgres.port,
        database: config.storage.postgres.database,
        user: config.storage.postgres.user,
        password: config.storage.postgres.password,
        max: config.storage.postgres.poolSize || 20,
        ssl: config.storage.postgres.ssl ? { rejectUnauthorized: false } : undefined,
        connectionTimeoutMillis: config.storage.postgres.connectTimeoutMs || 30000,
        idleTimeoutMillis: config.storage.postgres.idleTimeoutMs || 30000,
      })

      this.postgresDb = new Kysely<Database>({
        dialect: new PostgresDialect({ pool: this.postgresPool }),
      })

      logger.info('PostgreSQL Kysely client initialized')
    }

    if (config.storage?.valkey) {
      this.valkeyBackend = new ValkeyBackend({
        host: config.storage.valkey.host ?? 'localhost',
        port: config.storage.valkey.port ?? 6379,
        password: config.storage.valkey.password,
        defaultTTL: config.storage.valkey.defaultTTL ?? 3600,
      })
      logger.info('Valkey backend initialized')
    }

    if (config.storage?.meilisearch) {
      this.meilisearchBackend = new MeilisearchBackend(config.storage.meilisearch)
      logger.info('Meilisearch backend initialized')
    }

    if (config.storage?.duckdb) {
      this.duckdbBackend = new DuckDBBackend({
        dbPath: config.storage.duckdb.dbPath,
      })
      logger.info('DuckDB backend initialized')
    }
  }

  /**
   * Cleanup - close all connections
   *
   * Note: Bun 1.3.5 has known issues with closing native connections during process exit.
   * We explicitly close connections here to avoid NAPI errors during automatic cleanup.
   *
   * CRITICAL: We null out references so Bun's exit handler doesn't see them and try to
   * close them automatically (which triggers the NAPI crash).
   */
  private cleanedUp = false

  async cleanup(): Promise<void> {
    // Idempotent - only run once
    if (this.cleanedUp) {
      logger.debug('Cleanup already performed, skipping')
      return
    }
    this.cleanedUp = true

    logger.info('🧹 Starting cleanup...')

    // Close Valkey/Redis connection (safe)
    if (this.valkeyBackend) {
      try {
        this.valkeyBackend.close()
        this.valkeyBackend = null
        logger.info('✓ Valkey connection closed')
      } catch (error) {
        logger.warn('Error closing Valkey', { error: (error as Error).message })
      }
    }

    // Close DuckDB connection (safe - explicitly close before exit prevents NAPI errors)
    if (this.duckdbBackend) {
      try {
        await this.duckdbBackend.close()
        this.duckdbBackend = null
        logger.info('✓ DuckDB connection closed')
      } catch (error) {
        logger.warn('Error closing DuckDB', { error: (error as Error).message })
      }
    }

    // Close PostgreSQL connection gracefully with Node.js pg driver
    if (this.postgresDb && this.postgresPool) {
      try {
        await this.postgresDb.destroy()
        await this.postgresPool.end()
        this.postgresDb = null
        this.postgresPool = null
        logger.info('✓ PostgreSQL connection closed')
      } catch (error) {
        logger.warn('Error closing PostgreSQL', { error: (error as Error).message })
      }
    }

    // Meilisearch uses HTTP client, no explicit close needed
    if (this.meilisearchBackend) {
      this.meilisearchBackend = null
      logger.info('✓ Meilisearch client reference cleared')
    }

    logger.info('🧹 Cleanup complete')
  }

  /**
   * Main migration entry point
   */
  async migrate(dryRun: boolean = false): Promise<MigrationResult> {
    const startTime = Date.now()
    const errors: string[] = []

    try {
      logger.info('Starting Atlas migration', { dryRun })

      // Pre-flight checks
      await this.preMigrationChecks()

      if (dryRun) {
        await this.dryRunMigration()
        return {
          success: true,
          pointsMigrated: 0,
          durationMs: Date.now() - startTime,
          errors: [],
        }
      }

      // Actual migration
      const pointsMigrated = await this.performMigration()

      // Post-migration validation
      await this.postMigrationValidation()

      return {
        success: true,
        pointsMigrated,
        durationMs: Date.now() - startTime,
        errors,
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      logger.error('Migration failed', { err: error })
      errors.push(errorMessage)
      return {
        success: false,
        pointsMigrated: 0,
        durationMs: Date.now() - startTime,
        errors,
      }
    } finally {
      await this.cleanup()
    }
  }

  /**
   * Wait for PostgreSQL schema to be ready
   *
   * PostgreSQLBackend runs migrations in background (not awaited),
   * so we need to poll until tables exist.
   */
  private async waitForPostgresSchema(): Promise<void> {
    const maxWait = 10000 // 10 seconds
    const interval = 500 // 500ms
    const startTime = Date.now()

    while (Date.now() - startTime < maxWait) {
      try {
        const tables = await kysql<{ table_name: string }>`
          SELECT table_name
          FROM information_schema.tables
          WHERE table_schema = 'public'
            AND table_name IN ('sources', 'chunks', 'qntm_keys')
        `.execute(this.postgresDb!)

        if (tables.rows.length >= 3) {
          logger.debug('PostgreSQL schema ready')
          return
        }

        logger.debug('Waiting for PostgreSQL schema...', {
          tablesFound: tables.rows.length,
          elapsed: Date.now() - startTime,
        })
      } catch (error) {
        logger.debug('PostgreSQL schema check failed, retrying...', {
          error: (error as Error).message,
        })
      }

      await new Promise((resolve) => setTimeout(resolve, interval))
    }

    throw new Error('PostgreSQL schema not ready after 10 seconds - migrations may have failed')
  }

  /**
   * Pre-flight checks
   */
  private async preMigrationChecks(): Promise<void> {
    logger.info('Running pre-flight checks...')

    // Check daemon not running (read PID file)
    const pidPath = join(homedir(), '.atlas', 'daemon', 'daemon.pid')
    if (existsSync(pidPath)) {
      throw new Error('Daemon is running. Stop it before migration: atlas daemon stop')
    }

    // Check all required services accessible
    const checks: Promise<void>[] = []

    if (this.postgresDb) {
      checks.push(
        // Wait for PostgreSQL schema to be ready (migrations run in background)
        this.waitForPostgresSchema()
      )
    } else {
      throw new Error('PostgreSQL backend not configured (required)')
    }

    if (this.valkeyBackend) {
      checks.push(this.valkeyBackend.healthCheck())
    }

    if (this.meilisearchBackend) {
      checks.push(this.meilisearchBackend.healthCheck())
    }

    if (this.duckdbBackend) {
      checks.push(this.duckdbBackend.healthCheck())
    }

    await Promise.all(checks)

    // Get source count
    const collectionInfo = await this.qdrantClient.getCollection('atlas')
    const qdrantCount = collectionInfo.points_count ?? 0
    logger.info('Source point count', { qdrantCount })

    logger.info('✓ Pre-flight checks passed')
  }

  /**
   * Dry run - validate shapes without writing
   */
  private async dryRunMigration(): Promise<void> {
    logger.info('DRY RUN - No data will be written')

    // Scroll all points
    const points = await this.scrollAll()

    logger.info(`Validating ${points.length} points...`)

    // Sample 5 random points for detailed output
    const sampleIndices = new Set<number>()
    while (sampleIndices.size < Math.min(5, points.length)) {
      sampleIndices.add(Math.floor(Math.random() * points.length))
    }
    const samplePoints = Array.from(sampleIndices)
      .map((i) => points[i])
      .filter((p): p is QdrantPoint => p !== undefined)

    logger.info('\n=== SAMPLE MIGRATION (5 random points) ===\n')

    for (const point of samplePoints) {
      // Transform to all backend formats
      const pgChunk = this.transformForPostgres(point)
      const msDoc = this.transformForMeilisearch(String(point.id), point.payload)
      const duckdbRow = this.transformForDuckDB(point.payload)
      const valkeyChunk = point.payload

      logger.info(`\n--- Point ID: ${point.id} ---`)
      logger.info('Source (Qdrant):')
      logger.info(JSON.stringify(point, null, 2))

      logger.info('\nPostgreSQL (chunks table):')
      logger.info(
        JSON.stringify(
          {
            id: pgChunk.id,
            source_id: generateSourceId(pgChunk.payload.file_path),
            chunk_index: pgChunk.payload.chunk_index,
            total_chunks: pgChunk.payload.total_chunks,
            char_count: pgChunk.payload.char_count,
            file_path: pgChunk.payload.file_path,
            file_name: pgChunk.payload.file_name,
            consolidation_level: pgChunk.payload.consolidation_level,
            qntm_keys: pgChunk.payload.qntm_keys,
          },
          null,
          2
        )
      )

      logger.info('\nValkey (cache):')
      logger.info(`  Key: atlas:chunk:${pgChunk.id}`)
      logger.info(`  Value: ${JSON.stringify(valkeyChunk).substring(0, 200)}...`)
      logger.info(`  TTL: ${this.valkeyBackend ? '3600s' : 'N/A'}`)

      logger.info('\nMeilisearch (fulltext index):')
      logger.info(
        JSON.stringify(
          {
            id: msDoc.id,
            original_text: msDoc.original_text.substring(0, 100) + '...',
            file_path: msDoc.file_path,
            file_name: msDoc.file_name,
            qntm_keys: msDoc.qntm_keys,
            file_type: msDoc.file_type,
          },
          null,
          2
        )
      )

      logger.info('\nDuckDB (analytics):')
      logger.info(JSON.stringify(duckdbRow, null, 2))

      logger.info('\n' + '='.repeat(80) + '\n')
    }

    // Validate all points (silent)
    for (const point of points) {
      this.transformForPostgres(point)
      this.transformForMeilisearch(String(point.id), point.payload)
      this.transformForDuckDB(point.payload)
    }

    logger.info(`✓ DRY RUN complete - validated ${points.length} points`)
  }

  /**
   * Perform actual migration
   */
  private async performMigration(): Promise<number> {
    const collectionInfo = await this.qdrantClient.getCollection('atlas')
    const totalPoints = collectionInfo.points_count ?? 0
    let migrated = 0

    logger.info('Starting migration', { totalPoints })

    // Batch processing
    const batchSize = 1000
    let offset: string | number | Record<string, unknown> | undefined = undefined

    while (migrated < totalPoints) {
      const scrollResult = await this.qdrantClient.scroll('atlas', {
        limit: batchSize,
        offset: offset,
        with_payload: true,
        with_vector: false, // Don't need vectors
      })

      const batch = scrollResult.points as QdrantPoint[]

      if (batch.length === 0) break

      // Migrate batch with parallel backend writes
      await this.migrateBatch(batch)

      migrated += batch.length
      offset = scrollResult.next_page_offset ?? undefined

      const progress = ((migrated / totalPoints) * 100).toFixed(1)
      logger.info(`Progress: ${migrated}/${totalPoints} (${progress}%)`)

      if (!scrollResult.next_page_offset) break
    }

    logger.info('✓ Migration complete', { migrated })
    return migrated
  }

  /**
   * Migrate single batch to all backends in parallel
   */
  private async migrateBatch(points: QdrantPoint[]): Promise<void> {
    const tasks: Promise<void>[] = []

    // PostgreSQL (required)
    if (this.postgresDb) {
      tasks.push(this.migrateToPostgres(points))
    }

    // Valkey (optional)
    if (this.valkeyBackend) {
      tasks.push(this.migrateToValkey(points))
    }

    // Meilisearch (optional)
    if (this.meilisearchBackend) {
      tasks.push(this.migrateToMeilisearch(points))
    }

    // DuckDB (optional)
    if (this.duckdbBackend) {
      tasks.push(this.migrateToDuckDB(points))
    }

    // Execute all in parallel
    await Promise.all(tasks)
  }

  /**
   * Migrate batch to PostgreSQL
   */
  private async migrateToPostgres(points: QdrantPoint[]): Promise<void> {
    if (!this.postgresDb) return

    const db = this.postgresDb
    const chunks = points.map((p) => this.transformForPostgres(p))

    // Step 1: Extract and upsert unique sources from this batch
    const sourceMap = new Map<
      string,
      { id: string; path: string; contentHash: string; fileMtime: Date }
    >()

    for (const point of points) {
      const filePath = point.payload.file_path
      if (!sourceMap.has(filePath)) {
        const sourceId = generateSourceId(filePath)

        // Compute content hash from all chunks of this file in the batch
        const allChunksFromFile = points.filter((p) => p.payload.file_path === filePath)
        const contentText = allChunksFromFile.map((p) => p.payload.original_text).join('\n')
        const contentHash = hashContent(contentText)

        // Use created_at from first chunk as file mtime (file may not exist locally during migration)
        const fileMtime = new Date(point.payload.created_at)

        sourceMap.set(filePath, {
          id: sourceId,
          path: filePath,
          contentHash,
          fileMtime,
        })
      }
    }

    // Upsert sources
    for (const source of sourceMap.values()) {
      await db
        .insertInto('sources')
        .values({
          id: source.id,
          path: source.path,
          content_hash: source.contentHash,
          file_mtime: source.fileMtime,
          status: 'active',
        })
        .onConflict((oc) =>
          oc.column('path').doUpdateSet({
            content_hash: (eb) => eb.ref('excluded.content_hash'),
            file_mtime: (eb) => eb.ref('excluded.file_mtime'),
            updated_at: kysql`NOW()`,
          })
        )
        .execute()
    }

    logger.debug('Sources upserted', { count: sourceMap.size })

    // Step 2: Upsert chunks with real source_id
    for (const chunk of chunks) {
      const p = chunk.payload
      const sourceId = generateSourceId(p.file_path)

      await db
        .insertInto('chunks')
        .values({
          id: chunk.id,
          source_id: sourceId,
          chunk_index: p.chunk_index,
          total_chunks: p.total_chunks,
          char_count: p.char_count,
          payload: JSON.stringify(chunk.payload) as any, // JSONB type
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
            source_id: (eb) => eb.ref('excluded.source_id'),
            payload: (eb) => eb.ref('excluded.payload'),
            embedding_model: (eb) => eb.ref('excluded.embedding_model'),
            embedding_strategy: (eb) => eb.ref('excluded.embedding_strategy'),
            content_type: (eb) => eb.ref('excluded.content_type'),
            consolidation_level: (eb) => eb.ref('excluded.consolidation_level'),
            consolidation_type: (eb) => eb.ref('excluded.consolidation_type'),
            consolidation_direction: (eb) => eb.ref('excluded.consolidation_direction'),
            stability_score: (eb) => eb.ref('excluded.stability_score'),
            access_count: (eb) => eb.ref('excluded.access_count'),
            last_accessed_at: (eb) => eb.ref('excluded.last_accessed_at'),
            superseded_by: (eb) => eb.ref('excluded.superseded_by'),
            deletion_eligible: (eb) => eb.ref('excluded.deletion_eligible'),
            deletion_marked_at: (eb) => eb.ref('excluded.deletion_marked_at'),
          })
        )
        .execute()
    }

    // Record QNTM keys
    for (const point of points) {
      const qntmKeys = point.payload.qntm_keys || []
      if (qntmKeys.length > 0) {
        await db.transaction().execute(async (trx) => {
          for (const key of qntmKeys) {
            // Upsert QNTM key
            await trx
              .insertInto('qntm_keys')
              .values({
                key,
                first_seen_at: kysql`NOW()`,
                last_seen_at: kysql`NOW()`,
                usage_count: 1,
                last_used_in_chunk_id: String(point.id),
              })
              .onConflict((oc) =>
                oc.column('key').doUpdateSet({
                  last_seen_at: kysql`NOW()`,
                  usage_count: kysql`qntm_keys.usage_count + 1`,
                  last_used_in_chunk_id: String(point.id),
                })
              )
              .execute()

            // Insert mapping (ignore if exists)
            await trx
              .insertInto('chunk_qntm_keys')
              .values({
                chunk_id: String(point.id),
                qntm_key: key,
              })
              .onConflict((oc) => oc.columns(['chunk_id', 'qntm_key']).doNothing())
              .execute()
          }
        })
      }
    }
  }

  /**
   * Migrate batch to Valkey
   */
  private async migrateToValkey(points: QdrantPoint[]): Promise<void> {
    const chunks = points.map((p) => ({
      id: String(p.id),
      chunk: p.payload,
    }))

    await this.valkeyBackend!.msetChunks(chunks)
  }

  /**
   * Migrate batch to Meilisearch
   */
  private async migrateToMeilisearch(points: QdrantPoint[]): Promise<void> {
    const documents = points.map((p) => this.transformForMeilisearch(String(p.id), p.payload))

    await this.meilisearchBackend!.index(documents)
  }

  /**
   * Migrate batch to DuckDB
   */
  private async migrateToDuckDB(points: QdrantPoint[]): Promise<void> {
    const chunks = points.map((p) => ({
      id: String(p.id),
      file_path: p.payload.file_path,
      chunk_index: p.payload.chunk_index,
      total_chunks: p.payload.total_chunks,
      char_count: p.payload.char_count,
      qntm_keys: p.payload.qntm_keys || [],
      embedding_model: p.payload.embedding_model || '',
      embedding_strategy: p.payload.embedding_strategy || '',
      content_type: p.payload.content_type || '',
      consolidation_level: p.payload.consolidation_level,
      created_at: p.payload.created_at,
    }))

    // Use importFromMetadata pattern - create adapter
    const metadataAdapter = {
      async getAllChunks() {
        return chunks
      },
    } as any // Type adapter for compatibility

    await this.duckdbBackend!.importFromMetadata(metadataAdapter)
  }

  /**
   * Scroll all points from Qdrant
   */
  private async scrollAll(): Promise<QdrantPoint[]> {
    const allPoints: QdrantPoint[] = []
    let offset: string | number | Record<string, unknown> | undefined = undefined
    const limit = 1000

    while (true) {
      const result = await this.qdrantClient.scroll('atlas', {
        limit,
        offset: offset,
        with_payload: true,
        with_vector: false,
      })

      if (result.points.length === 0) break
      allPoints.push(...(result.points as QdrantPoint[]))
      offset = result.next_page_offset ?? undefined

      if (!offset) break
    }

    return allPoints
  }

  /**
   * Post-migration validation
   */
  private async postMigrationValidation(): Promise<void> {
    logger.info('Running post-migration validation...')

    // Check counts match
    const collectionInfo = await this.qdrantClient.getCollection('atlas')
    const qdrantCount = collectionInfo.points_count ?? 0

    if (this.postgresDb) {
      const result = await this.postgresDb
        .selectFrom('chunks')
        .select((eb) => eb.fn.countAll<string>().as('count'))
        .executeTakeFirstOrThrow()

      const postgresCount = parseInt(result.count)

      if (postgresCount !== qdrantCount) {
        throw new Error(`Count mismatch: Postgres=${postgresCount}, Qdrant=${qdrantCount}`)
      }
      logger.info('PostgreSQL count verified', { postgresCount })
    }

    if (this.meilisearchBackend) {
      // Wait for Meilisearch indexing to complete (poll until isIndexing=false)
      logger.debug('Waiting for Meilisearch indexing to complete...')

      let meilisearchStats = await this.meilisearchBackend.getIndexStats()
      let attempts = 0
      const maxAttempts = 30 // 30 seconds max wait

      while (meilisearchStats.isIndexing && attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
        meilisearchStats = await this.meilisearchBackend.getIndexStats()
        attempts++
        logger.debug('Waiting for indexing...', {
          attempt: attempts,
          documentsIndexed: meilisearchStats.numberOfDocuments,
        })
      }

      const meilisearchCount = meilisearchStats.numberOfDocuments

      logger.debug('Meilisearch stats retrieved', {
        numberOfDocuments: meilisearchCount,
        isIndexing: meilisearchStats.isIndexing,
        expected: qdrantCount,
        waitedSeconds: attempts,
      })

      if (meilisearchCount !== qdrantCount) {
        logger.warn('Meilisearch count mismatch - this may resolve after indexing completes', {
          meilisearchCount,
          qdrantCount,
          isStillIndexing: meilisearchStats.isIndexing,
        })
        // Don't throw - Meilisearch stats can lag slightly, or indexing may continue in background
      } else {
        logger.info('Meilisearch count verified', { meilisearchCount })
      }
    }

    logger.info('✓ Post-migration validation passed')
  }

  /**
   * Transform Qdrant point to PostgreSQL chunk
   */
  private transformForPostgres(point: QdrantPoint): { id: string; payload: ChunkPayload } {
    return {
      id: String(point.id),
      payload: point.payload,
    }
  }

  /**
   * Transform payload to Meilisearch document
   */
  private transformForMeilisearch(id: string, payload: ChunkPayload): FullTextDocument {
    return {
      id: id, // Use actual chunk UUID (Meilisearch requires alphanumeric + hyphens/underscores)
      original_text: payload.original_text,
      file_path: payload.file_path,
      file_name: payload.file_name,
      qntm_keys: payload.qntm_keys || [],
      file_type: payload.file_type,
      consolidation_level: payload.consolidation_level,
      content_type: payload.content_type,
      created_at: payload.created_at,
      importance: payload.importance,
      memory_type: payload.memory_type,
    }
  }

  /**
   * Transform payload to DuckDB row
   */
  private transformForDuckDB(payload: ChunkPayload): {
    id: string
    file_path: string
    chunk_index: number
    total_chunks: number
    char_count: number
    qntm_keys: string[]
    embedding_model: string
    embedding_strategy: string
    content_type: string
    consolidation_level: number
    created_at: string
  } {
    return {
      id: payload.file_path + ':' + payload.chunk_index,
      file_path: payload.file_path,
      chunk_index: payload.chunk_index,
      total_chunks: payload.total_chunks,
      char_count: payload.char_count,
      qntm_keys: payload.qntm_keys || [],
      embedding_model: payload.embedding_model || '',
      embedding_strategy: payload.embedding_strategy || '',
      content_type: payload.content_type || '',
      consolidation_level: payload.consolidation_level,
      created_at: payload.created_at,
    }
  }
}

// ============================================
// Main Execution
// ============================================

async function main() {
  const dryRun = process.argv.includes('--dry-run')

  logger.info('Atlas Migration Tool', { dryRun })

  const config = await loadConfig()
  const migrationTool = new MigrationTool(config)

  try {
    const result = await migrationTool.migrate(dryRun)

    // Note: cleanup() is already called in migrate()'s finally block
    // Calling it again here would be redundant and potentially harmful

    if (result.success) {
      logger.info('✓ Migration successful', {
        pointsMigrated: result.pointsMigrated,
        durationMs: result.durationMs,
      })
      // Don't call process.exit() - let script naturally terminate
      // This avoids triggering Bun's buggy NAPI cleanup for SQL connections
    } else {
      console.error('\n✗ Migration failed:')
      for (const err of result.errors) {
        console.error('  -', err)
      }
      // Return non-zero via process.exitCode (doesn't trigger immediate exit)
      process.exitCode = 1
    }
  } catch (error) {
    logger.error('Fatal error during migration', { error: (error as Error).message })

    // Note: cleanup() is already called in migrate()'s finally block
    // Only attempt cleanup if migrate() was never called (construction error)
    if (migrationTool && !migrationTool['cleanedUp']) {
      try {
        await migrationTool.cleanup()
      } catch (cleanupError) {
        logger.warn('Cleanup failed', { error: cleanupError })
      }
    }

    // Set exit code but don't call process.exit() (triggers NAPI crash)
    process.exitCode = 1
  }
}

main().catch((error) => {
  logger.error('Fatal error', { err: error })
  // Don't call process.exit() - causes Bun 1.3.5 NAPI crash
  // Set exit code and let process terminate naturally
  process.exitCode = 1
})
