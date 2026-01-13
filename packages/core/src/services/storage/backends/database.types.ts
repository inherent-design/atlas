/**
 * Kysely database schema types
 *
 * Type-safe database schema for PostgreSQL backend.
 * Generated from existing PostgreSQL schema in metadata.ts migrations.
 */

import type { ChunkPayload } from '../../../shared/types.js'
import type { ColumnType } from 'kysely'

/**
 * Sources table
 */
export interface SourcesTable {
  id: string
  path: string
  content_hash: string
  file_mtime: ColumnType<Date, Date | string, Date | string>
  status: 'active' | 'deleted'
  created_at: ColumnType<Date, Date | string | undefined, never>
  updated_at: ColumnType<Date, Date | string | undefined, Date | string | undefined>
}

/**
 * Chunks table
 */
export interface ChunksTable {
  id: string
  source_id: string
  chunk_index: number
  total_chunks: number
  char_count: number
  payload: ColumnType<ChunkPayload, ChunkPayload, ChunkPayload>

  // Embedding metadata
  embedding_model: string | null
  embedding_strategy: string | null
  content_type: string | null

  // Consolidation state
  consolidation_level: number
  consolidation_type: string | null
  consolidation_direction: string | null

  // Lifecycle
  stability_score: number | null
  access_count: number
  last_accessed_at: ColumnType<Date | null, Date | string | null, Date | string | null>
  superseded_by: string | null
  deletion_eligible: boolean
  deletion_marked_at: ColumnType<Date | null, Date | string | null, Date | string | null>

  created_at: ColumnType<Date, Date | string, never>
}

/**
 * QNTM keys table
 */
export interface QntmKeysTable {
  key: string
  first_seen_at: ColumnType<Date, Date | string | undefined, Date | string | undefined>
  last_seen_at: ColumnType<Date, Date | string | undefined, Date | string | undefined>
  usage_count: number
  last_used_in_chunk_id: string | null
}

/**
 * Chunk-QNTM mapping table
 */
export interface ChunkQntmKeysTable {
  chunk_id: string
  qntm_key: string
}

/**
 * Collection stats table
 */
export interface CollectionStatsTable {
  collection_name: string
  total_chunks: number
  total_files: number
  total_chars: number
  last_updated: ColumnType<Date, Date | string | undefined, Date | string | undefined>
}

/**
 * File stats table
 */
export interface FileStatsTable {
  file_path: string
  chunk_count: number
  char_count: number
  qntm_key_count: number
  embedding_model: string | null
  last_ingested: ColumnType<Date, Date | string | undefined, Date | string | undefined>
}

/**
 * Complete database schema
 */
export interface Database {
  sources: SourcesTable
  chunks: ChunksTable
  qntm_keys: QntmKeysTable
  chunk_qntm_keys: ChunkQntmKeysTable
  collection_stats: CollectionStatsTable
  file_stats: FileStatsTable
}
