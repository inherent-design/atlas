/**
 * SQLite database connection management for Atlas tracking
 */

import { Database } from 'bun:sqlite'
import { join } from 'path'
import { existsSync, mkdirSync } from 'fs'
import { homedir } from 'os'
import { CREATE_TABLES, SET_SCHEMA_VERSION, GET_SCHEMA_VERSION, SCHEMA_VERSION } from './schema'
import { createLogger } from '../../shared/logger'

const log = createLogger('tracking:db')

/**
 * Get the Atlas data directory path
 */
export function getAtlasDataDir(): string {
  return join(homedir(), '.atlas')
}

/**
 * Get the daemon runtime directory path
 */
export function getDaemonDir(): string {
  return join(getAtlasDataDir(), 'daemon')
}

/**
 * Get the default database path
 */
export function getDefaultDbPath(): string {
  return join(getDaemonDir(), 'atlas.db')
}

/**
 * Ensure Atlas data directory exists
 */
function ensureDataDir(): void {
  const dataDir = getAtlasDataDir()
  if (!existsSync(dataDir)) {
    mkdirSync(dataDir, { recursive: true })
    log.info('Created Atlas data directory', { path: dataDir })
  }

  // Ensure daemon directory exists
  const daemonDir = getDaemonDir()
  if (!existsSync(daemonDir)) {
    mkdirSync(daemonDir, { recursive: true })
    log.info('Created daemon directory', { path: daemonDir })
  }
}

/**
 * Singleton database instance
 */
let dbInstance: Database | null = null

/**
 * Get or create database connection
 */
export function getDatabase(path?: string): Database {
  if (dbInstance) {
    return dbInstance
  }

  ensureDataDir()

  const dbPath = path || getDefaultDbPath()
  const isNew = !existsSync(dbPath)

  log.debug('Opening database', { path: dbPath, isNew })

  const db = new Database(dbPath)

  // Enable foreign keys
  db.exec('PRAGMA foreign_keys = ON')

  // Enable WAL mode for better concurrency
  db.exec('PRAGMA journal_mode = WAL')

  // Set reasonable timeouts
  db.exec('PRAGMA busy_timeout = 5000')

  // Initialize schema if new database
  if (isNew) {
    log.info('Initializing new database', { path: dbPath })
    initializeSchema(db)
  } else {
    // Check and migrate schema if needed
    const currentVersion = getCurrentSchemaVersion(db)
    if (currentVersion < SCHEMA_VERSION) {
      log.info('Migrating database schema', { from: currentVersion, to: SCHEMA_VERSION })
      migrateSchema(db, currentVersion)
    }
  }

  dbInstance = db
  return db
}

/**
 * Initialize database schema
 */
function initializeSchema(db: Database): void {
  // Create all tables
  db.exec(CREATE_TABLES)

  // Set schema version
  db.exec(SET_SCHEMA_VERSION)

  log.info('Database schema initialized', { version: SCHEMA_VERSION })
}

/**
 * Get current schema version from database
 */
function getCurrentSchemaVersion(db: Database): number {
  try {
    const result = db.prepare(GET_SCHEMA_VERSION).get() as { value: string } | undefined
    return result ? parseInt(result.value, 10) : 0
  } catch (error) {
    // Schema table doesn't exist, treat as version 0
    return 0
  }
}

/**
 * Migrate database schema from one version to another
 */
function migrateSchema(db: Database, fromVersion: number): void {
  // Future migrations will go here
  // For now, just recreate if version 0 (fresh start)
  if (fromVersion === 0) {
    initializeSchema(db)
    return
  }

  // Add version-specific migrations here
  // Example:
  // if (fromVersion < 2) {
  //   db.exec('ALTER TABLE sources ADD COLUMN new_field TEXT')
  //   db.exec("UPDATE schema_info SET value = '2' WHERE key = 'schema_version'")
  // }
}

/**
 * Close database connection
 */
export function closeDatabase(): void {
  if (dbInstance) {
    log.debug('Closing database connection')
    dbInstance.close()
    dbInstance = null
  }
}

/**
 * Reset database instance (for testing)
 */
export function resetDatabase(): void {
  closeDatabase()
}
