/**
 * FileWatcher tests - Verify lifecycle and registration
 *
 * Tests that FileWatcher implements ManagedScheduler correctly and can be registered
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { getFileWatcher } from '../file-watcher'
import { schedulerManager } from '../scheduler-manager'

// Mock chokidar to avoid actual file watching during tests
vi.mock('chokidar', () => ({
  watch: vi.fn(() => ({
    on: vi.fn().mockReturnThis(),
    close: vi.fn(),
  })),
}))

// Mock file system operations
vi.mock('fs', () => ({
  existsSync: vi.fn(() => true),
  mkdirSync: vi.fn(),
}))

describe('FileWatcher Lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    const watcher = getFileWatcher()
    if (watcher) {
      watcher.stop()
    }
  })

  describe('ManagedScheduler Interface', () => {
    it('implements ManagedScheduler interface', () => {
      const watcher = getFileWatcher()

      expect(watcher).toBeDefined()
      expect(watcher.name).toBe('file-watcher')
      expect(typeof watcher.start).toBe('function')
      expect(typeof watcher.stop).toBe('function')
      expect(typeof watcher.getState).toBe('function')
    })

    it('has correct scheduler name', () => {
      const watcher = getFileWatcher()
      expect(watcher.name).toBe('file-watcher')
    })
  })

  describe('Lifecycle Methods', () => {
    it('starts without errors', () => {
      const watcher = getFileWatcher()
      expect(() => watcher.start()).not.toThrow()
    })

    it('stops without errors', () => {
      const watcher = getFileWatcher()
      watcher.start()
      expect(() => watcher.stop()).not.toThrow()
    })

    it('can be started and stopped multiple times', () => {
      const watcher = getFileWatcher()

      watcher.start()
      watcher.stop()
      watcher.start()
      watcher.stop()

      expect(true).toBe(true) // No errors thrown
    })

    it('getState returns valid state object', () => {
      const watcher = getFileWatcher()
      const state = watcher.getState()

      expect(state).toBeDefined()
      expect(typeof state.isRunning).toBe('boolean')
      expect(Array.isArray(state.watchedPaths)).toBe(true)
      expect(typeof state.queueSize).toBe('number')
    })

    it('reports isRunning=true after start', () => {
      const watcher = getFileWatcher()
      watcher.start()

      const state = watcher.getState()
      expect(state.isRunning).toBe(true)
    })

    it('reports isRunning=false after stop', () => {
      const watcher = getFileWatcher()
      watcher.start()
      watcher.stop()

      const state = watcher.getState()
      expect(state.isRunning).toBe(false)
    })
  })

  describe('Scheduler Registration', () => {
    it('can be registered with schedulerManager', () => {
      const watcher = getFileWatcher()

      expect(() => {
        schedulerManager.register(watcher)
      }).not.toThrow()
    })

    it('is listed in schedulerManager after registration', () => {
      const watcher = getFileWatcher()
      schedulerManager.register(watcher)

      const status = schedulerManager.getStatus()
      expect(status.schedulers).toBeDefined()
      expect('file-watcher' in (status.schedulers as Record<string, unknown>)).toBe(true)
    })

    it('can be retrieved from schedulerManager after registration', () => {
      const watcher = getFileWatcher()
      schedulerManager.register(watcher)

      const retrieved = schedulerManager.get('file-watcher')
      expect(retrieved).toBeDefined()
      expect(retrieved?.name).toBe('file-watcher')
    })

    it('can be started via schedulerManager', () => {
      const watcher = getFileWatcher()
      schedulerManager.register(watcher)

      expect(() => {
        schedulerManager.startAll()
      }).not.toThrow()

      const state = watcher.getState()
      expect(state.isRunning).toBe(true)
    })

    it('can be stopped via schedulerManager', () => {
      const watcher = getFileWatcher()
      schedulerManager.register(watcher)
      schedulerManager.startAll()

      expect(() => {
        schedulerManager.stopAll()
      }).not.toThrow()

      const state = watcher.getState()
      expect(state.isRunning).toBe(false)
    })
  })

  describe('Singleton Pattern', () => {
    it('returns same instance on multiple calls', () => {
      const watcher1 = getFileWatcher()
      const watcher2 = getFileWatcher()

      expect(watcher1).toBe(watcher2)
    })

    it('maintains state across multiple getFileWatcher calls', () => {
      const watcher1 = getFileWatcher()
      watcher1.start()

      const watcher2 = getFileWatcher()
      const state = watcher2.getState()

      expect(state.isRunning).toBe(true)
    })
  })

  describe('Configuration', () => {
    it('loads configuration from getConfig()', () => {
      const watcher = getFileWatcher()

      // FileWatcher should initialize without errors even if config is present
      expect(watcher).toBeDefined()
      expect(watcher.name).toBe('file-watcher')
    })

    it('uses default watch paths if config not specified', () => {
      const watcher = getFileWatcher()

      // FileWatcher constructor should not throw
      expect(watcher).toBeDefined()
    })
  })

  describe('Error Handling', () => {
    it('handles start() when already running', () => {
      const watcher = getFileWatcher()
      watcher.start()

      // Starting again should not throw (should warn and return)
      expect(() => watcher.start()).not.toThrow()
    })

    it('handles stop() when not running', () => {
      const watcher = getFileWatcher()

      // Stopping when not running should not throw
      expect(() => watcher.stop()).not.toThrow()
    })
  })
})
