/**
 * SQLite schema for Atlas file tracking and event persistence
 */

export const SCHEMA_VERSION = 1

/**
 * SQL statements for creating all tables
 */
export const CREATE_TABLES = `
-- File tracking for change detection
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  content_hash TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  file_mtime TEXT NOT NULL,
  first_ingested_at TEXT NOT NULL,
  last_ingested_at TEXT NOT NULL,
  ingest_count INTEGER DEFAULT 1,
  status TEXT DEFAULT 'active' CHECK(status IN ('active', 'deleted', 'ignored'))
);

-- Chunk tracking (maps source → Qdrant points)
CREATE TABLE IF NOT EXISTS source_chunks (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  content_hash TEXT NOT NULL,
  qdrant_point_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  superseded_at TEXT,
  superseded_by TEXT,
  UNIQUE(source_id, chunk_index)
);

-- Event log (optional persistence for replay/debugging)
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL,
  data TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  client_id TEXT
);

-- Watch paths (file watcher config)
CREATE TABLE IF NOT EXISTS watch_paths (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  recursive INTEGER DEFAULT 1,
  include_patterns TEXT,
  exclude_patterns TEXT,
  auto_ingest INTEGER DEFAULT 1,
  created_at TEXT NOT NULL
);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_info (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_sources_path ON sources(path);
CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);
CREATE INDEX IF NOT EXISTS idx_source_chunks_source ON source_chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_source_chunks_content ON source_chunks(content_hash);
CREATE INDEX IF NOT EXISTS idx_source_chunks_qdrant ON source_chunks(qdrant_point_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_watch_paths_path ON watch_paths(path);
`

/**
 * Initial schema version insert
 */
export const SET_SCHEMA_VERSION = `
INSERT OR REPLACE INTO schema_info (key, value)
VALUES ('schema_version', '${SCHEMA_VERSION}');
`

/**
 * Get current schema version
 */
export const GET_SCHEMA_VERSION = `
SELECT value FROM schema_info WHERE key = 'schema_version';
`
