/**
 * SQLite database connection management for Atlas tracking
 *
 * @deprecated This file is deprecated. FileTracker now uses PostgreSQL via MetadataBackend.
 * SQLite database at ~/.atlas/daemon/atlas.db has been archived.
 * This file is kept for reference only and will be removed in a future version.
 *
 * All exports throw errors directing users to PostgreSQL-based alternatives.
 */

import { join } from 'path'
import { homedir } from 'os'
import { createLogger } from '../../shared/logger.js'

const log = createLogger('tracking:db')

// Type stub for deprecated Database (prevents type errors without importing bun:sqlite)
interface Database {
  exec(sql: string): void
  prepare(sql: string): any
  close(): void
}

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
 * Get or create database connection
 * @deprecated Use PostgreSQL via MetadataBackend instead
 */
export function getDatabase(_path?: string): Database {
  throw new Error('getDatabase() is deprecated. Use PostgreSQL via MetadataBackend instead.')
}

/**
 * Close database connection
 * @deprecated Use PostgreSQL via MetadataBackend instead
 */
export function closeDatabase(): void {
  log.warn('closeDatabase() is deprecated and has no effect')
}

/**
 * Reset database instance (for testing)
 * @deprecated Use PostgreSQL via MetadataBackend instead
 */
export function resetDatabase(): void {
  log.warn('resetDatabase() is deprecated and has no effect')
}
