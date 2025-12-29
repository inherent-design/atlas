/**
 * QNTM Key Cache using Bun SQLite
 *
 * Global cache for all QNTM keys across collections.
 * Enables key reuse during generation.
 */

import { Database } from 'bun:sqlite'
import { mkdirSync } from 'fs'
import { join } from 'path'
import { createLogger } from '../logger'

const log = createLogger('qntm/cache')

const DB_PATH = join(process.cwd(), 'data', 'qntm-cache.db')

let db: Database | null = null

/**
 * Initialize QNTM cache database
 */
export function initQNTMCache(): Database {
  log.debug('initQNTMCache called', { dbExists: !!db, dbPath: DB_PATH, cwd: process.cwd() })

  if (db) {
    log.debug('Returning existing database instance')
    return db
  }

  // Ensure data directory exists
  const dataDir = join(process.cwd(), 'data')
  log.debug('Creating data directory', { dataDir })

  try {
    mkdirSync(dataDir, { recursive: true })
    log.debug('Data directory created/exists')
  } catch (error) {
    log.warn('Failed to create data directory', { error })
    // Ignore if already exists
  }

  log.debug('Creating Database instance', { path: DB_PATH, create: true })

  try {
    db = new Database(DB_PATH, { create: true })
    log.debug('Database instance created', {
      dbType: typeof db,
      dbNull: db === null,
      dbUndefined: db === undefined,
    })
  } catch (error) {
    log.error('Failed to create Database instance', error as Error)
    throw error
  }

  if (!db) {
    const error = new Error('Database creation returned null/undefined')
    log.error('Database is null/undefined after creation', { db, dbType: typeof db })
    throw error
  }

  // Create qntm_keys table
  try {
    log.debug('Creating qntm_keys table')
    db.exec(`
      CREATE TABLE IF NOT EXISTS qntm_keys (
        key TEXT PRIMARY KEY,
        created_at INTEGER NOT NULL,
        usage_count INTEGER DEFAULT 1
      )
    `)
    log.debug('qntm_keys table created')
  } catch (error) {
    log.error('Failed to create qntm_keys table', error as Error)
    throw error
  }

  // Create index for faster lookups
  try {
    log.debug('Creating index on qntm_keys')
    db.exec(`
      CREATE INDEX IF NOT EXISTS idx_created_at ON qntm_keys(created_at)
    `)
    log.debug('Index created')
  } catch (error) {
    log.error('Failed to create index', error as Error)
    throw error
  }

  log.info('QNTM cache initialized successfully', { path: DB_PATH })

  if (!db) {
    throw new Error('Database is null/undefined before return!')
  }

  return db
}

/**
 * Get all existing QNTM keys from cache
 */
export function getCachedQNTMKeys(): string[] {
  const database = initQNTMCache()

  const stmt = database.prepare('SELECT key FROM qntm_keys ORDER BY usage_count DESC')
  const rows = stmt.all() as Array<{ key: string }>

  log.debug('Fetched cached QNTM keys', { count: rows.length })
  return rows.map((row) => row.key)
}

/**
 * Add new QNTM keys to cache
 */
export function cacheQNTMKeys(keys: string[]): void {
  log.debug('cacheQNTMKeys called', { keyCount: keys.length })

  const database = initQNTMCache()

  log.debug('Database returned from initQNTMCache', {
    dbType: typeof database,
    dbNull: database === null,
    dbUndefined: database === undefined,
    dbTruthy: !!database,
  })

  if (!database) {
    const error = new Error('initQNTMCache returned null/undefined!')
    log.error('Database is null/undefined in cacheQNTMKeys', { database })
    throw error
  }

  const timestamp = Date.now()

  const stmt = database.prepare(`
    INSERT INTO qntm_keys (key, created_at, usage_count)
    VALUES (?, ?, 1)
    ON CONFLICT(key) DO UPDATE SET usage_count = usage_count + 1
  `)

  for (const key of keys) {
    try {
      stmt.run(key, timestamp)
      log.trace('Cached QNTM key', { key })
    } catch (error) {
      log.warn('Failed to cache QNTM key', { key, error })
    }
  }

  log.debug('Cached QNTM keys', { count: keys.length })
}

/**
 * Get cache statistics
 */
export function getQNTMCacheStats(): {
  totalKeys: number
  mostUsedKeys: Array<{ key: string; usage_count: number }>
} {
  const database = initQNTMCache()

  const totalStmt = database.prepare('SELECT COUNT(*) as count FROM qntm_keys')
  const totalRow = totalStmt.get() as { count: number }

  const mostUsedStmt = database.prepare(
    'SELECT key, usage_count FROM qntm_keys ORDER BY usage_count DESC LIMIT 10'
  )
  const mostUsedRows = mostUsedStmt.all() as Array<{ key: string; usage_count: number }>

  return {
    totalKeys: totalRow.count,
    mostUsedKeys: mostUsedRows,
  }
}

/**
 * Close database connection
 */
export function closeQNTMCache(): void {
  if (db) {
    db.close()
    db = null
    log.debug('QNTM cache closed')
  }
}
