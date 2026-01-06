/**
 * File tracking service for change detection and chunk management
 */

import { createHash } from 'crypto'
import { statSync, readFileSync } from 'fs'
import { getDatabase } from './db'
import { createLogger } from '../../shared/logger'
import type { Database } from 'bun:sqlite'

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
 * File tracker for change detection
 */
export class FileTracker {
  db: Database

  constructor(dbPath?: string) {
    this.db = getDatabase(dbPath)
  }

  /**
   * Compute SHA-256 hash of file content
   */
  private computeContentHash(content: string): string {
    return createHash('sha256').update(content, 'utf-8').digest('hex')
  }

  /**
   * Compute SHA-256 hash of chunk content
   */
  private computeChunkHash(chunk: string): string {
    return createHash('sha256').update(chunk, 'utf-8').digest('hex')
  }

  /**
   * Check if file needs ingestion
   */
  async needsIngestion(path: string): Promise<NeedsIngestionResult> {
    try {
      // Get file stats
      const stats = statSync(path)
      const content = readFileSync(path, 'utf-8')
      const contentHash = this.computeContentHash(content)

      // Check if file exists in tracking database
      const source = this.db
        .prepare(
          `
        SELECT id, content_hash, file_mtime, status
        FROM sources
        WHERE path = ?
      `
        )
        .get(path) as
        | {
            id: string
            content_hash: string
            file_mtime: string
            status: string
          }
        | undefined

      if (!source) {
        // New file
        log.debug('File not tracked, needs ingestion', { path })
        return {
          needsIngest: true,
          reason: 'new',
        }
      }

      // Check if file was deleted and is now back
      if (source.status === 'deleted') {
        log.debug('File was deleted, now back, needs ingestion', { path })
        return {
          needsIngest: true,
          reason: 'modified',
        }
      }

      // Check if content changed
      if (source.content_hash !== contentHash) {
        log.debug('File content changed, needs ingestion', {
          path,
          oldHash: source.content_hash.slice(0, 8),
          newHash: contentHash.slice(0, 8),
        })

        // Get existing chunks for potential cleanup
        const existingChunks = this.db
          .prepare(
            `
          SELECT qdrant_point_id
          FROM source_chunks
          WHERE source_id = ? AND superseded_at IS NULL
        `
          )
          .all(source.id) as { qdrant_point_id: string }[]

        return {
          needsIngest: true,
          reason: 'modified',
          existingChunks: existingChunks.map((c) => c.qdrant_point_id),
        }
      }

      // File unchanged
      log.debug('File unchanged, skipping ingestion', { path })
      return {
        needsIngest: false,
        reason: 'unchanged',
      }
    } catch (error) {
      // File read error, treat as needs ingestion (will fail later with better error)
      log.warn('Error checking file, assuming needs ingestion', { path, error })
      return {
        needsIngest: true,
        reason: 'new',
      }
    }
  }

  /**
   * Record successful ingestion of a file
   */
  async recordIngestion(path: string, chunks: ChunkRecord[]): Promise<void> {
    try {
      const stats = statSync(path)
      const content = readFileSync(path, 'utf-8')
      const contentHash = this.computeContentHash(content)
      const now = new Date().toISOString()

      // Check if source already exists
      const existing = this.db
        .prepare('SELECT id, ingest_count FROM sources WHERE path = ?')
        .get(path) as { id: string; ingest_count: number } | undefined

      let sourceId: string

      if (existing) {
        // Update existing source
        sourceId = existing.id
        this.db
          .prepare(
            `
          UPDATE sources
          SET content_hash = ?,
              file_size = ?,
              file_mtime = ?,
              last_ingested_at = ?,
              ingest_count = ?,
              status = 'active'
          WHERE id = ?
        `
          )
          .run(
            contentHash,
            stats.size,
            stats.mtime.toISOString(),
            now,
            existing.ingest_count + 1,
            sourceId
          )

        // Mark old chunks as superseded
        this.db
          .prepare(
            `
          UPDATE source_chunks
          SET superseded_at = ?, superseded_by = 'reingest'
          WHERE source_id = ? AND superseded_at IS NULL
        `
          )
          .run(now, sourceId)

        log.debug('Updated source record', {
          path,
          sourceId,
          ingestCount: existing.ingest_count + 1,
        })
      } else {
        // Create new source
        sourceId = this.generateId()
        this.db
          .prepare(
            `
          INSERT INTO sources (id, path, content_hash, file_size, file_mtime, first_ingested_at, last_ingested_at, ingest_count, status)
          VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'active')
        `
          )
          .run(sourceId, path, contentHash, stats.size, stats.mtime.toISOString(), now, now)

        log.debug('Created source record', { path, sourceId })
      }

      // Insert chunk records
      const insertChunk = this.db.prepare(`
        INSERT INTO source_chunks (id, source_id, chunk_index, content_hash, qdrant_point_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
      `)

      for (const chunk of chunks) {
        const chunkId = this.generateId()
        insertChunk.run(chunkId, sourceId, chunk.index, chunk.contentHash, chunk.qdrantPointId, now)
      }

      log.info('Recorded ingestion', { path, chunks: chunks.length, sourceId })
    } catch (error) {
      log.error('Failed to record ingestion', { path, error })
      throw error
    }
  }

  /**
   * Mark file as deleted (soft delete chunks)
   */
  async markDeleted(path: string): Promise<MarkDeletedResult> {
    try {
      const now = new Date().toISOString()

      // Get source ID
      const source = this.db.prepare('SELECT id FROM sources WHERE path = ?').get(path) as
        | { id: string }
        | undefined

      if (!source) {
        log.debug('File not tracked, nothing to mark as deleted', { path })
        return { supersededChunks: [] }
      }

      // Get active chunks
      const chunks = this.db
        .prepare(
          `
        SELECT qdrant_point_id
        FROM source_chunks
        WHERE source_id = ? AND superseded_at IS NULL
      `
        )
        .all(source.id) as { qdrant_point_id: string }[]

      // Mark source as deleted
      this.db
        .prepare(
          `
        UPDATE sources
        SET status = 'deleted', last_ingested_at = ?
        WHERE id = ?
      `
        )
        .run(now, source.id)

      // Mark chunks as superseded
      this.db
        .prepare(
          `
        UPDATE source_chunks
        SET superseded_at = ?, superseded_by = 'file_deleted'
        WHERE source_id = ? AND superseded_at IS NULL
      `
        )
        .run(now, source.id)

      log.info('Marked file as deleted', { path, chunks: chunks.length })

      return {
        supersededChunks: chunks.map((c) => c.qdrant_point_id),
      }
    } catch (error) {
      log.error('Failed to mark file as deleted', { path, error })
      throw error
    }
  }

  /**
   * Find chunk by content hash (for deduplication)
   */
  async findChunkByContentHash(contentHash: string): Promise<ChunkByHash | null> {
    try {
      const chunk = this.db
        .prepare(
          `
        SELECT qdrant_point_id
        FROM source_chunks
        WHERE content_hash = ? AND superseded_at IS NULL
        LIMIT 1
      `
        )
        .get(contentHash) as { qdrant_point_id: string } | undefined

      if (!chunk) {
        return null
      }

      // Note: We don't store embeddings in SQLite, would need to fetch from Qdrant
      return {
        qdrantPointId: chunk.qdrant_point_id,
      }
    } catch (error) {
      log.error('Failed to find chunk by content hash', {
        contentHash: contentHash.slice(0, 8),
        error,
      })
      return null
    }
  }

  /**
   * Clean up orphaned records (e.g., chunks whose source is deleted)
   */
  async vacuum(): Promise<{ removed: number }> {
    try {
      // Delete chunks that were superseded more than 14 days ago
      const cutoff = new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString()

      const result = this.db
        .prepare(
          `
        DELETE FROM source_chunks
        WHERE superseded_at IS NOT NULL AND superseded_at < ?
      `
        )
        .run(cutoff)

      log.info('Vacuumed old chunk records', { removed: result.changes })

      return { removed: result.changes }
    } catch (error) {
      log.error('Failed to vacuum', { error })
      throw error
    }
  }

  /**
   * Generate a UUID v4
   */
  private generateId(): string {
    return crypto.randomUUID()
  }

  /**
   * Get statistics
   */
  getStats(): {
    sources: number
    activeChunks: number
    supersededChunks: number
  } {
    const sources = (
      this.db.prepare("SELECT COUNT(*) as count FROM sources WHERE status = 'active'").get() as {
        count: number
      }
    ).count

    const activeChunks = (
      this.db
        .prepare('SELECT COUNT(*) as count FROM source_chunks WHERE superseded_at IS NULL')
        .get() as {
        count: number
      }
    ).count

    const supersededChunks = (
      this.db
        .prepare('SELECT COUNT(*) as count FROM source_chunks WHERE superseded_at IS NOT NULL')
        .get() as {
        count: number
      }
    ).count

    return { sources, activeChunks, supersededChunks }
  }
}

/**
 * Singleton tracker instance
 */
let trackerInstance: FileTracker | null = null

/**
 * Get file tracker instance
 */
export function getFileTracker(dbPath?: string): FileTracker {
  if (!trackerInstance) {
    trackerInstance = new FileTracker(dbPath)
  }
  return trackerInstance
}
