/**
 * Analytics Backend Interface and DuckDB Implementation
 *
 * Provides OLAP analytics capabilities:
 * - Timeline aggregation queries
 * - Parquet export for archival/analysis
 * - Direct Parquet querying (no ingestion needed)
 * - Efficient aggregations over large datasets
 *
 * DuckDB is embedded (in-process), requires no service deployment.
 */

import { DuckDBInstance, DuckDBConnection } from '@duckdb/node-api'
import { createLogger } from '../../../shared/logger.js'
import { join } from 'path'
import { homedir } from 'os'
import { mkdirSync, existsSync } from 'fs'
import type { TimelineParams, TimelineData, TimelinePeriod } from '../../../shared/types.js'

const logger = createLogger('storage:analytics')

// ============================================
// Type Definitions
// ============================================

/**
 * Aggregate query parameters
 */
export interface AggregateQuery {
  /** SQL query to execute */
  sql: string
  /** Query parameters (positional) */
  params?: any[]
}

/**
 * Aggregate query result
 */
export interface AggregateResult {
  /** Result rows */
  rows: any[]
  /** Row count */
  rowCount: number
  /** Query execution time (milliseconds) */
  durationMs: number
}

/**
 * Export parameters
 */
export interface ExportParams {
  /** Export data since this date (optional) */
  since?: Date
  /** Export data until this date (optional) */
  until?: Date
  /** Output directory for export files */
  outputDir: string
  /** Export format */
  format?: 'parquet' | 'csv' | 'json'
}

/**
 * Export result
 */
export interface ExportResult {
  /** Exported file paths */
  files: string[]
  /** Total rows exported */
  rowCount: number
  /** Export execution time (milliseconds) */
  durationMs: number
}

/**
 * Metadata backend interface (for import)
 */
export interface MetadataBackend {
  /** Get all chunks with metadata */
  getAllChunks(): Promise<ChunkMetadata[]>
}

/**
 * Chunk metadata from metadata backend
 */
export interface ChunkMetadata {
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
}

// ============================================
// Analytics Backend Interface
// ============================================

/**
 * Analytics backend interface
 *
 * Provides OLAP analytics capabilities over chunk metadata.
 */
export interface AnalyticsBackend {
  /**
   * Query timeline aggregations
   *
   * @param params - Timeline query parameters
   * @returns Aggregated timeline data
   */
  queryTimeline(params: TimelineParams): Promise<TimelineData>

  /**
   * Execute custom aggregate queries
   *
   * @param query - Aggregate query with SQL and params
   * @returns Query results
   */
  queryAggregates(query: AggregateQuery): Promise<AggregateResult>

  /**
   * Export chunk analytics to Parquet/CSV/JSON
   *
   * @param params - Export parameters
   * @returns Export result with file paths
   */
  exportToParquet(params: ExportParams): Promise<ExportResult>

  /**
   * Query Parquet files directly
   *
   * @param parquetPath - Path to Parquet file (or glob pattern)
   * @param sql - SQL query to execute on Parquet
   * @returns Query results
   */
  queryParquet(parquetPath: string, sql: string): Promise<any[]>

  /**
   * Import chunk metadata from metadata backend
   *
   * Syncs chunk_analytics table with metadata backend.
   *
   * @param metadata - Metadata backend to import from
   */
  importFromMetadata(metadata: MetadataBackend): Promise<void>

  /**
   * Health check
   *
   * @throws Error if database is not accessible
   */
  healthCheck(): Promise<void>

  /**
   * Close database connection
   */
  close(): Promise<void>
}

// ============================================
// DuckDB Backend Implementation
// ============================================

/**
 * DuckDB analytics backend
 *
 * Embedded, in-process OLAP database with Parquet-native queries.
 */
export class DuckDBBackend implements AnalyticsBackend {
  private instance: DuckDBInstance | null = null
  private conn: DuckDBConnection | null = null
  private dbPath: string

  constructor(config: { dbPath?: string } = {}) {
    // Expand tilde in path
    this.dbPath =
      config.dbPath?.replace('~', homedir()) ||
      join(homedir(), '.atlas', 'analytics', 'atlas.duckdb')

    // Create directory if needed
    const dbDir = this.dbPath.substring(0, this.dbPath.lastIndexOf('/'))
    if (!existsSync(dbDir)) {
      mkdirSync(dbDir, { recursive: true })
      logger.debug(`Created analytics directory: ${dbDir}`)
    }

    logger.info(`Initializing DuckDB at ${this.dbPath}`)
  }

  /**
   * Initialize database connection
   */
  private async initialize(): Promise<void> {
    if (this.instance) {
      return // Already initialized
    }

    try {
      this.instance = await DuckDBInstance.create(this.dbPath)
      this.conn = await this.instance.connect()
      logger.debug('DuckDB connection established')

      // Create schema
      await this.createSchema()
    } catch (err) {
      logger.error('Failed to initialize DuckDB', { error: (err as Error).message })
      throw err
    }
  }

  /**
   * Create analytics tables
   */
  private async createSchema(): Promise<void> {
    const sql = `
      CREATE TABLE IF NOT EXISTS chunk_analytics (
        chunk_id VARCHAR PRIMARY KEY,
        file_path VARCHAR NOT NULL,
        chunk_index INTEGER NOT NULL,
        total_chunks INTEGER NOT NULL,
        char_count INTEGER NOT NULL,
        qntm_keys VARCHAR[],
        embedding_model VARCHAR,
        embedding_strategy VARCHAR,
        content_type VARCHAR,
        consolidation_level INTEGER NOT NULL,
        created_at TIMESTAMP NOT NULL
      );

      CREATE INDEX IF NOT EXISTS idx_chunk_analytics_created_at ON chunk_analytics(created_at);
      CREATE INDEX IF NOT EXISTS idx_chunk_analytics_file_path ON chunk_analytics(file_path);
      CREATE INDEX IF NOT EXISTS idx_chunk_analytics_consolidation_level ON chunk_analytics(consolidation_level);
    `

    await this.run(sql)
    logger.debug('Analytics schema created')
  }

  /**
   * Execute SQL statement (no results)
   */
  private async run(sql: string, params: any[] = []): Promise<void> {
    await this.initialize()

    try {
      // New API: connection.run() returns a result, we just don't need it here
      if (params.length > 0) {
        await this.conn!.run(sql, params)
      } else {
        await this.conn!.run(sql)
      }
    } catch (err) {
      logger.error('SQL execution failed', { sql, error: (err as Error).message })
      throw err
    }
  }

  /**
   * Execute SQL query (with results)
   */
  private async all<T = any>(sql: string, params: any[] = []): Promise<T[]> {
    await this.initialize()

    try {
      // New API: runAndReadAll returns a reader with all rows already read
      const reader = params.length > 0
        ? await this.conn!.runAndReadAll(sql, params)
        : await this.conn!.runAndReadAll(sql)

      // Get rows as objects (with column names as keys)
      const rows = reader.getRowObjects() as T[]

      // Convert BigInt to number for JavaScript compatibility
      const converted = (rows || []).map((row) => this.convertBigInts(row))
      return converted
    } catch (err) {
      logger.error('SQL query failed', { sql, error: (err as Error).message })
      throw err
    }
  }

  /**
   * Insert or update chunk analytics
   */
  async insertChunks(chunks: ChunkMetadata[]): Promise<void> {
    if (chunks.length === 0) {
      return
    }

    // Batch insert with UPSERT logic
    const batchSize = 1000
    for (let i = 0; i < chunks.length; i += batchSize) {
      const batch = chunks.slice(i, i + batchSize)

      const values = batch
        .map(() => `(?, ?, ?, ?, ?, CAST(? AS VARCHAR[]), ?, ?, ?, ?, ?)`)
        .join(', ')

      const sql = `
        INSERT INTO chunk_analytics (
          chunk_id, file_path, chunk_index, total_chunks, char_count,
          qntm_keys, embedding_model, embedding_strategy, content_type,
          consolidation_level, created_at
        ) VALUES ${values}
        ON CONFLICT (chunk_id) DO UPDATE SET
          consolidation_level = EXCLUDED.consolidation_level,
          created_at = EXCLUDED.created_at
      `

      const params = batch.flatMap((c) => [
        c.id,
        c.file_path,
        c.chunk_index,
        c.total_chunks,
        c.char_count,
        JSON.stringify(c.qntm_keys), // DuckDB array literal
        c.embedding_model,
        c.embedding_strategy,
        c.content_type,
        c.consolidation_level,
        c.created_at,
      ])

      await this.run(sql, params)
    }

    logger.debug('Analytics chunks inserted/updated', { count: chunks.length })
  }

  /**
   * Convert BigInt values to numbers recursively
   */
  private convertBigInts(obj: any): any {
    if (obj === null || obj === undefined) {
      return obj
    }

    if (typeof obj === 'bigint') {
      return Number(obj)
    }

    if (Array.isArray(obj)) {
      return obj.map((item) => this.convertBigInts(item))
    }

    if (typeof obj === 'object') {
      const result: any = {}
      for (const key in obj) {
        result[key] = this.convertBigInts(obj[key])
      }
      return result
    }

    return obj
  }

  /**
   * Query timeline aggregations
   */
  async queryTimeline(params: TimelineParams): Promise<TimelineData> {
    const start = Date.now()

    // Default until to now
    const until = params.until || new Date().toISOString()
    const granularity = params.granularity || 'day'

    // Map granularity to DuckDB date_trunc interval
    const interval =
      granularity === 'hour'
        ? 'hour'
        : granularity === 'week'
          ? 'week'
          : granularity === 'month'
            ? 'month'
            : 'day'

    const sql = `
      SELECT
        date_trunc('${interval}', created_at) AS period,
        COUNT(*) AS chunk_count,
        COUNT(DISTINCT file_path) AS file_count,
        SUM(char_count) AS char_count,
        ROUND(AVG(char_count), 2) AS avg_chunk_size
      FROM chunk_analytics
      WHERE created_at >= ? AND created_at < ?
      GROUP BY period
      ORDER BY period ASC
    `

    const rows = await this.all<{
      period: string
      chunk_count: number
      file_count: number
      char_count: number
      avg_chunk_size: number
    }>(sql, [params.since, until])

    // Calculate totals
    const totalChunks = rows.reduce((sum, r) => sum + r.chunk_count, 0)
    const totalFiles = rows.reduce((sum, r) => sum + r.file_count, 0)

    const durationMs = Date.now() - start

    logger.debug('Timeline query completed', {
      since: params.since,
      until,
      granularity,
      periods: rows.length,
      totalChunks,
      durationMs,
    })

    return {
      periods: rows.map((r) => ({
        period: r.period,
        chunkCount: r.chunk_count,
        fileCount: r.file_count,
        charCount: r.char_count,
        avgChunkSize: r.avg_chunk_size,
      })),
      totalChunks,
      totalFiles,
      durationMs,
    }
  }

  /**
   * Execute custom aggregate queries
   */
  async queryAggregates(query: AggregateQuery): Promise<AggregateResult> {
    const start = Date.now()

    const rows = await this.all(query.sql, query.params || [])
    const durationMs = Date.now() - start

    logger.debug('Aggregate query completed', {
      rowCount: rows.length,
      durationMs,
    })

    return {
      rows,
      rowCount: rows.length,
      durationMs,
    }
  }

  /**
   * Export chunk analytics to Parquet/CSV/JSON
   */
  async exportToParquet(params: ExportParams): Promise<ExportResult> {
    const start = Date.now()

    // Ensure output directory exists
    const outputDir = params.outputDir.replace('~', homedir())
    if (!existsSync(outputDir)) {
      mkdirSync(outputDir, { recursive: true })
    }

    const format = params.format || 'parquet'
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const outputPath = join(outputDir, `chunk_analytics_${timestamp}.${format}`)

    // Build WHERE clause
    const whereClauses: string[] = []
    const queryParams: any[] = []

    if (params.since) {
      whereClauses.push('created_at >= ?')
      queryParams.push(params.since.toISOString())
    }

    if (params.until) {
      whereClauses.push('created_at < ?')
      queryParams.push(params.until.toISOString())
    }

    const whereClause = whereClauses.length > 0 ? `WHERE ${whereClauses.join(' AND ')}` : ''

    // Export query
    const sql = `
      COPY (
        SELECT * FROM chunk_analytics
        ${whereClause}
        ORDER BY created_at
      ) TO '${outputPath}' (FORMAT ${format.toUpperCase()})
    `

    await this.run(sql, queryParams)

    // Get row count
    const countSql = `
      SELECT COUNT(*) as count FROM chunk_analytics ${whereClause}
    `
    const countResult = await this.all<{ count: number }>(countSql, queryParams)
    const rowCount = countResult[0]?.count || 0

    const durationMs = Date.now() - start

    logger.info('Export completed', {
      format,
      outputPath,
      rowCount,
      durationMs,
    })

    return {
      files: [outputPath],
      rowCount,
      durationMs,
    }
  }

  /**
   * Query Parquet files directly
   */
  async queryParquet(parquetPath: string, sql: string): Promise<any[]> {
    const expandedPath = parquetPath.replace('~', homedir())

    logger.debug('Querying Parquet file', { parquetPath: expandedPath })

    // DuckDB can query Parquet directly
    const rows = await this.all(sql.replace('chunk_analytics', `'${expandedPath}'`))

    logger.debug('Parquet query completed', { rowCount: rows.length })

    return rows
  }

  /**
   * Import chunk metadata from metadata backend
   */
  async importFromMetadata(metadata: MetadataBackend): Promise<void> {
    logger.info('Importing metadata into analytics...')
    const start = Date.now()

    // Get all chunks from metadata backend
    const chunks = await metadata.getAllChunks()

    logger.debug(`Retrieved ${chunks.length} chunks from metadata backend`)

    // Clear existing data
    await this.run('DELETE FROM chunk_analytics')

    // Batch insert
    const batchSize = 1000
    for (let i = 0; i < chunks.length; i += batchSize) {
      const batch = chunks.slice(i, i + batchSize)

      const values = batch
        .map(() => `(?, ?, ?, ?, ?, CAST(? AS VARCHAR[]), ?, ?, ?, ?, ?)`)
        .join(', ')

      const sql = `
        INSERT INTO chunk_analytics (
          chunk_id, file_path, chunk_index, total_chunks, char_count,
          qntm_keys, embedding_model, embedding_strategy, content_type,
          consolidation_level, created_at
        ) VALUES ${values}
      `

      const params = batch.flatMap((c) => [
        c.id,
        c.file_path,
        c.chunk_index,
        c.total_chunks,
        c.char_count,
        JSON.stringify(c.qntm_keys), // DuckDB array literal
        c.embedding_model,
        c.embedding_strategy,
        c.content_type,
        c.consolidation_level,
        c.created_at,
      ])

      await this.run(sql, params)

      logger.debug(`Inserted batch ${i / batchSize + 1}/${Math.ceil(chunks.length / batchSize)}`)
    }

    const durationMs = Date.now() - start

    logger.info('Metadata import completed', {
      chunksImported: chunks.length,
      durationMs,
    })
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<void> {
    await this.initialize()

    // Simple query to verify database is accessible
    await this.all('SELECT 1 as health')

    logger.debug('Health check passed')
  }

  /**
   * Close database connection
   */
  async close(): Promise<void> {
    if (this.conn) {
      this.conn.closeSync()
      this.conn = null
    }

    // Instance cleanup happens automatically
    this.instance = null

    logger.debug('DuckDB connection closed')
  }
}
