/**
 * File tracking service for change detection and chunk management
 *
 * PostgreSQL-based tracker using Kysely for type-safe queries.
 * Tracks file ingestion state via sources table and chunk metadata.
 */

import { statSync, readFileSync, existsSync } from 'fs'
import { sql as kysql } from 'kysely'
import type { Kysely } from 'kysely'
import { createLogger } from '../../shared/logger.js'
import { generateSourceId, hashContent, generateChunkId } from '../../shared/utils.js'
import type { Database } from '../storage/backends/database.types.js'

const log = createLogger('tracking:tracker')

/**
 * Chunk record for tracking ingestion
 */
export interface ChunkRecord {
  index: number
  contentHash: string
  qdrantPointId: string
}

/**
 * Result of checking if file needs ingestion
 */
export interface NeedsIngestionResult {
  needsIngest: boolean
  reason: 'new' | 'modified' | 'unchanged'
  existingChunks?: string[] // Qdrant point IDs that can be reused
}

/**
 * Result of marking file as deleted
 */
export interface MarkDeletedResult {
  supersededChunks: string[] // Qdrant point IDs to mark as deleted
}

/**
 * Chunk found by content hash
 */
export interface ChunkByHash {
  qdrantPointId: string
  embedding?: number[] // Could reuse embedding if available
}

/**
 * PostgreSQL-based file tracker
 *
 * Uses existing sources and chunks tables to track file ingestion state.
 * Provides change detection via content hash and file modification time.
 */
export class FileTracker {
  constructor(private db: Kysely<Database>) {
    log.debug('FileTracker initialized with PostgreSQL backend')
  }

  /**
   * Check if file needs ingestion
   *
   * Compares file modification time and content hash against stored record.
   * Returns needsIngest=false only if file is unchanged since last ingestion.
   */
  async needsIngestion(path: string): Promise<NeedsIngestionResult> {
    try {
      // Check if file exists
      if (!existsSync(path)) {
        log.warn('File does not exist', { path })
        return {
          needsIngest: false,
          reason: 'unchanged',
        }
      }

      // Get file stats
      const stats = statSync(path)
      const fileMtime = stats.mtime

      // Compute current content hash
      const content = readFileSync(path, 'utf-8')
      const currentHash = hashContent(content)

      // Look up source record
      const source = await this.db
        .selectFrom('sources')
        .select(['id', 'path', 'content_hash', 'file_mtime', 'status'])
        .where('path', '=', path)
        .executeTakeFirst()

      // New file (no source record)
      if (!source) {
        log.debug('File is new', { path })
        return {
          needsIngest: true,
          reason: 'new',
        }
      }

      // Compare content hash and mtime
      const storedMtime = new Date(source.file_mtime)
      const hashChanged = source.content_hash !== currentHash
      const mtimeChanged = fileMtime > storedMtime

      if (hashChanged || mtimeChanged) {
        log.debug('File modified', {
          path,
          hashChanged,
          mtimeChanged,
          currentHash: currentHash.slice(0, 8),
          storedHash: source.content_hash.slice(0, 8),
        })

        // Fetch existing chunk IDs for potential reuse
        const chunks = await this.db
          .selectFrom('chunks')
          .select('id')
          .where('source_id', '=', source.id)
          .execute()

        return {
          needsIngest: true,
          reason: 'modified',
          existingChunks: chunks.map((c) => c.id),
        }
      }

      // File unchanged
      log.debug('File unchanged', { path })
      return {
        needsIngest: false,
        reason: 'unchanged',
      }
    } catch (error) {
      // On error (DB unavailable, file read error), default to ingestion
      log.warn('Error checking file ingestion status, defaulting to ingest', {
        path,
        error: error instanceof Error ? error.message : String(error),
      })
      return {
        needsIngest: true,
        reason: 'new',
      }
    }
  }

  /**
   * Record file ingestion
   *
   * Updates sources table and stores chunk tracking information.
   */
  async recordIngestion(filePath: string, chunks: ChunkRecord[]): Promise<void> {
    try {
      // Get file stats
      const stats = statSync(filePath)
      const fileMtime = stats.mtime

      // Compute content hash
      const content = readFileSync(filePath, 'utf-8')
      const contentHash = hashContent(content)

      // Generate source ID
      const sourceId = generateSourceId(filePath)

      // Upsert source record
      await this.db
        .insertInto('sources')
        .values({
          id: sourceId,
          path: filePath,
          content_hash: contentHash,
          file_mtime: fileMtime,
          status: 'active',
        })
        .onConflict((oc) =>
          oc.column('path').doUpdateSet({
            content_hash: contentHash,
            file_mtime: fileMtime,
            status: 'active',
            updated_at: kysql`NOW()`,
          })
        )
        .execute()

      log.debug('Recorded ingestion', {
        path: filePath,
        sourceId,
        chunkCount: chunks.length,
      })
    } catch (error) {
      log.error('Failed to record ingestion', {
        path: filePath,
        error: error instanceof Error ? error.message : String(error),
      })
      // Don't throw - tracking is best-effort
    }
  }

  /**
   * Mark file as deleted
   *
   * Updates source status to 'deleted' and returns chunk IDs to supersede.
   */
  async markDeleted(filePath: string): Promise<MarkDeletedResult> {
    try {
      const sourceId = generateSourceId(filePath)

      // Get existing chunks for this source
      const chunks = await this.db
        .selectFrom('chunks')
        .select('id')
        .where('source_id', '=', sourceId)
        .execute()

      // Update source status to deleted
      await this.db
        .updateTable('sources')
        .set({
          status: 'deleted',
          updated_at: kysql`NOW()`,
        })
        .where('id', '=', sourceId)
        .execute()

      log.debug('Marked file as deleted', {
        path: filePath,
        sourceId,
        supersededChunks: chunks.length,
      })

      return {
        supersededChunks: chunks.map((c) => c.id),
      }
    } catch (error) {
      log.error('Failed to mark file as deleted', {
        path: filePath,
        error: error instanceof Error ? error.message : String(error),
      })
      return {
        supersededChunks: [],
      }
    }
  }

  /**
   * Find chunk by content hash
   *
   * Searches for a chunk with matching content hash in payload.
   * Note: This requires JSONB querying which may be slow without proper indexes.
   */
  async findChunkByHash(contentHash: string): Promise<ChunkByHash | null> {
    try {
      // Query chunks where payload contains matching content hash
      // This is a slow operation without specialized indexes
      const result = await this.db
        .selectFrom('chunks')
        .select(['id'])
        .where(kysql`payload->>'original_text'`, '=', contentHash)
        .executeTakeFirst()

      if (!result) {
        return null
      }

      return {
        qdrantPointId: result.id,
      }
    } catch (error) {
      log.error('Failed to find chunk by hash', {
        error: error instanceof Error ? error.message : String(error),
      })
      return null
    }
  }

  /**
   * Get all tracked files
   *
   * Returns list of all files in sources table with their status.
   */
  async getAllFiles(): Promise<
    Array<{
      path: string
      status: string
      lastIngested: string
      contentHash: string
    }>
  > {
    try {
      const sources = await this.db
        .selectFrom('sources')
        .select(['path', 'status', 'updated_at', 'content_hash'])
        .orderBy('updated_at', 'desc')
        .execute()

      return sources.map((s) => ({
        path: s.path,
        status: s.status,
        lastIngested: new Date(s.updated_at).toISOString(),
        contentHash: s.content_hash,
      }))
    } catch (error) {
      log.error('Failed to get all files', {
        error: error instanceof Error ? error.message : String(error),
      })
      return []
    }
  }

  /**
   * Get chunks for a file
   *
   * Returns chunk tracking records for a specific file.
   * Note: We don't store contentHash per chunk currently, so we use chunk ID.
   */
  async getFileChunks(filePath: string): Promise<ChunkRecord[]> {
    try {
      const sourceId = generateSourceId(filePath)

      const chunks = await this.db
        .selectFrom('chunks')
        .select(['id', 'chunk_index'])
        .where('source_id', '=', sourceId)
        .orderBy('chunk_index', 'asc')
        .execute()

      return chunks.map((c) => ({
        index: c.chunk_index,
        contentHash: '', // Not stored per-chunk, would need to extract from payload
        qdrantPointId: c.id,
      }))
    } catch (error) {
      log.error('Failed to get file chunks', {
        path: filePath,
        error: error instanceof Error ? error.message : String(error),
      })
      return []
    }
  }

  /**
   * Get statistics
   *
   * Returns aggregate statistics about tracked files and chunks.
   */
  async getStats(): Promise<{
    totalFiles: number
    totalChunks: number
    activeFiles: number
    deletedFiles: number
  }> {
    try {
      // Count sources by status
      const sourceCounts = await this.db
        .selectFrom('sources')
        .select([
          kysql<number>`COUNT(*)`.as('total'),
          kysql<number>`COUNT(*) FILTER (WHERE status = 'active')`.as('active'),
          kysql<number>`COUNT(*) FILTER (WHERE status = 'deleted')`.as('deleted'),
        ])
        .executeTakeFirstOrThrow()

      // Count total chunks
      const chunkCount = await this.db
        .selectFrom('chunks')
        .select(kysql<number>`COUNT(*)`.as('count'))
        .executeTakeFirstOrThrow()

      return {
        totalFiles: Number(sourceCounts.total),
        totalChunks: Number(chunkCount.count),
        activeFiles: Number(sourceCounts.active),
        deletedFiles: Number(sourceCounts.deleted),
      }
    } catch (error) {
      log.error('Failed to get stats', {
        error: error instanceof Error ? error.message : String(error),
      })
      return {
        totalFiles: 0,
        totalChunks: 0,
        activeFiles: 0,
        deletedFiles: 0,
      }
    }
  }
}

/**
 * Singleton tracker instance
 */
let trackerInstance: FileTracker | null = null

/**
 * Get the singleton FileTracker instance
 *
 * @param db - Kysely database instance (required on first call)
 * @returns FileTracker instance
 */
export function getFileTracker(db?: Kysely<Database>): FileTracker {
  if (!trackerInstance) {
    if (!db) {
      throw new Error('FileTracker requires Kysely database instance on first initialization')
    }
    trackerInstance = new FileTracker(db)
  }
  return trackerInstance
}
