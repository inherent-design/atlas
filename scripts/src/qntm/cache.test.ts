/**
 * Unit tests for QNTM cache (Bun SQLite)
 */

import { afterEach, beforeEach, describe, expect, test } from 'bun:test'
import { rmSync } from 'fs'
import { join } from 'path'
import {
  cacheQNTMKeys,
  closeQNTMCache,
  getCachedQNTMKeys,
  getQNTMCacheStats,
  initQNTMCache,
} from './cache'

const testCachePath = join(process.cwd(), 'data', 'qntm-cache.db')

describe('qntm-cache', () => {
  beforeEach(() => {
    // Clean up any existing cache
    closeQNTMCache()
    try {
      rmSync(testCachePath, { force: true })
    } catch {
      // Ignore if doesn't exist
    }
  })

  afterEach(() => {
    closeQNTMCache()
    try {
      rmSync(testCachePath, { force: true })
    } catch {
      // Ignore cleanup errors
    }
  })

  describe('initQNTMCache', () => {
    test('creates database and tables', () => {
      const db = initQNTMCache()

      expect(db).toBeDefined()

      // Verify table exists
      const tables = db
        .prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='qntm_keys'")
        .all()
      expect(tables).toHaveLength(1)
    })

    test('creates index on created_at', () => {
      const db = initQNTMCache()

      const indexes = db
        .prepare("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_created_at'")
        .all()
      expect(indexes).toHaveLength(1)
    })

    test('returns same instance on multiple calls (singleton)', () => {
      const db1 = initQNTMCache()
      const db2 = initQNTMCache()

      expect(db1).toBe(db2)
    })
  })

  describe('getCachedQNTMKeys', () => {
    test('returns empty array for new cache', () => {
      initQNTMCache()
      const keys = getCachedQNTMKeys()

      expect(keys).toEqual([])
    })

    test('returns cached keys in usage order', () => {
      initQNTMCache()

      // Cache some keys with different usage counts
      cacheQNTMKeys(['@memory ~ consolidation'])
      cacheQNTMKeys(['@sleep ~ patterns'])
      cacheQNTMKeys(['@memory ~ consolidation']) // Increment usage

      const keys = getCachedQNTMKeys()

      expect(keys).toHaveLength(2)
      // @memory should be first (usage_count = 2)
      expect(keys[0]).toBe('@memory ~ consolidation')
      expect(keys[1]).toBe('@sleep ~ patterns')
    })
  })

  describe('cacheQNTMKeys', () => {
    test('inserts new keys', () => {
      initQNTMCache()

      cacheQNTMKeys(['@test ~ key1', '@test ~ key2'])

      const keys = getCachedQNTMKeys()
      expect(keys).toHaveLength(2)
      expect(keys).toContain('@test ~ key1')
      expect(keys).toContain('@test ~ key2')
    })

    test('increments usage_count on duplicate keys', () => {
      const db = initQNTMCache()

      cacheQNTMKeys(['@memory ~ consolidation'])
      cacheQNTMKeys(['@memory ~ consolidation'])
      cacheQNTMKeys(['@memory ~ consolidation'])

      const result = db
        .prepare('SELECT usage_count FROM qntm_keys WHERE key = ?')
        .get('@memory ~ consolidation') as { usage_count: number }

      expect(result.usage_count).toBe(3)
    })

    test('handles empty array gracefully', () => {
      initQNTMCache()

      cacheQNTMKeys([])

      const keys = getCachedQNTMKeys()
      expect(keys).toEqual([])
    })

    test('stores created_at timestamp', () => {
      const db = initQNTMCache()
      const beforeTime = Date.now()

      cacheQNTMKeys(['@test ~ timestamp'])

      const afterTime = Date.now()

      const result = db
        .prepare('SELECT created_at FROM qntm_keys WHERE key = ?')
        .get('@test ~ timestamp') as { created_at: number }

      expect(result.created_at).toBeGreaterThanOrEqual(beforeTime)
      expect(result.created_at).toBeLessThanOrEqual(afterTime)
    })
  })

  describe('getQNTMCacheStats', () => {
    test('returns zero stats for empty cache', () => {
      initQNTMCache()

      const stats = getQNTMCacheStats()

      expect(stats.totalKeys).toBe(0)
      expect(stats.mostUsedKeys).toEqual([])
    })

    test('returns total key count', () => {
      initQNTMCache()

      cacheQNTMKeys(['@key1', '@key2', '@key3'])

      const stats = getQNTMCacheStats()
      expect(stats.totalKeys).toBe(3)
    })

    test('returns most used keys with usage counts', () => {
      initQNTMCache()

      // Create keys with different usage patterns
      cacheQNTMKeys(['@popular'])
      cacheQNTMKeys(['@popular'])
      cacheQNTMKeys(['@popular'])
      cacheQNTMKeys(['@moderate'])
      cacheQNTMKeys(['@moderate'])
      cacheQNTMKeys(['@rare'])

      const stats = getQNTMCacheStats()

      expect(stats.mostUsedKeys).toHaveLength(3)
      expect(stats.mostUsedKeys[0].key).toBe('@popular')
      expect(stats.mostUsedKeys[0].usage_count).toBe(3)
      expect(stats.mostUsedKeys[1].key).toBe('@moderate')
      expect(stats.mostUsedKeys[1].usage_count).toBe(2)
      expect(stats.mostUsedKeys[2].key).toBe('@rare')
      expect(stats.mostUsedKeys[2].usage_count).toBe(1)
    })

    test('limits most used keys to 10', () => {
      initQNTMCache()

      // Create 15 keys
      for (let i = 0; i < 15; i++) {
        cacheQNTMKeys([`@key${i}`])
      }

      const stats = getQNTMCacheStats()

      expect(stats.totalKeys).toBe(15)
      expect(stats.mostUsedKeys.length).toBeLessThanOrEqual(10)
    })
  })

  describe('closeQNTMCache', () => {
    test('closes database connection', () => {
      initQNTMCache()

      closeQNTMCache()

      // After closing, next init should create new instance
      const db = initQNTMCache()
      expect(db).toBeDefined()
    })

    test('handles closing already closed connection', () => {
      initQNTMCache()

      closeQNTMCache()
      closeQNTMCache() // Should not throw

      expect(true).toBe(true) // If we get here, no error thrown
    })

    test('handles closing without init', () => {
      closeQNTMCache() // Should not throw
      expect(true).toBe(true)
    })
  })

  describe('integration scenarios', () => {
    test('typical workflow: cache, retrieve, update usage', () => {
      initQNTMCache()

      // Initial cache
      cacheQNTMKeys(['@memory ~ consolidation', '@sleep ~ patterns'])

      let keys = getCachedQNTMKeys()
      expect(keys).toHaveLength(2)

      // Reuse a key (increments usage)
      cacheQNTMKeys(['@memory ~ consolidation'])

      keys = getCachedQNTMKeys()
      expect(keys[0]).toBe('@memory ~ consolidation') // Should be first now

      const stats = getQNTMCacheStats()
      expect(stats.totalKeys).toBe(2)
      expect(stats.mostUsedKeys[0].usage_count).toBe(2)
    })

    test('persistence across close/reopen', () => {
      initQNTMCache()
      cacheQNTMKeys(['@persistent ~ key'])
      closeQNTMCache()

      // Reopen
      initQNTMCache()
      const keys = getCachedQNTMKeys()

      expect(keys).toContain('@persistent ~ key')
    })

    test('handles special characters in keys', () => {
      initQNTMCache()

      const specialKeys = [
        "@memory ~ consolidation's test",
        '@key ~ with "quotes"',
        '@key ~ with\nnewline',
      ]

      cacheQNTMKeys(specialKeys)

      const keys = getCachedQNTMKeys()
      expect(keys).toHaveLength(3)
    })
  })
})
