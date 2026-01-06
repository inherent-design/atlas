/**
 * FileWatcher - Watch directories for new files to ingest
 *
 * Uses chokidar for cross-platform file watching.
 * Integrates with FileTracker for change detection and Ingest pipeline.
 */

import { watch, type FSWatcher } from 'chokidar'
import { resolve, relative, extname } from 'path'
import { homedir } from 'os'
import { existsSync, mkdirSync } from 'fs'
import { createLogger } from '../shared/logger'
import { getConfig } from '../shared/config.loader'
import { IGNORE_PATTERNS } from '../shared/config'
import { getFileTracker } from '../services/tracking'
import { getAllEmbeddableExtensions } from '../services/embedding/types'
import type { ManagedScheduler } from './scheduler-manager'

const log = createLogger('file-watcher')

interface FileWatcherConfig {
  paths: string[]
  patterns: string[]
  ignorePatterns: string[]
}

class FileWatcher implements ManagedScheduler {
  readonly name = 'file-watcher'
  private watcher: FSWatcher | null = null
  private config: FileWatcherConfig
  private ingestQueue: Set<string> = new Set()
  private debounceTimer: ReturnType<typeof setTimeout> | null = null
  private isProcessing = false
  private readyLogged = false

  constructor() {
    const atlasConfig = getConfig()
    const watcherConfig = atlasConfig.daemon?.fileWatcher ?? {}

    // Get embeddable extensions as glob patterns (whitelist approach)
    const defaultPatterns = getAllEmbeddableExtensions().map((ext) => `*${ext}`)

    // Expand ~ to homedir
    // Default ignore patterns include node_modules, .git, dist, etc.
    this.config = {
      paths: (watcherConfig.paths ?? ['~/.atlas']).map((p) => p.replace(/^~/, homedir())),
      patterns: watcherConfig.patterns ?? defaultPatterns,
      ignorePatterns: watcherConfig.ignorePatterns ?? IGNORE_PATTERNS,
    }

    log.debug('FileWatcher initialized', this.config)
  }

  start(): void {
    if (this.watcher) {
      log.warn('FileWatcher already running')
      return
    }

    // Ensure watch directories exist
    for (const dir of this.config.paths) {
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true })
        log.info('Created watch directory', { path: dir })
      }
    }

    // Watch directories recursively, filter by extension in handler
    log.info('Starting file watcher', {
      paths: this.config.paths,
      patterns: this.config.patterns,
    })

    this.watcher = watch(this.config.paths, {
      ignored: this.config.ignorePatterns,
      persistent: true,
      ignoreInitial: false, // Process existing files on start
      depth: 99, // Deep recursion
      awaitWriteFinish: {
        stabilityThreshold: 500,
        pollInterval: 100,
      },
    })

    this.watcher
      .on('add', (path) => this.handleFileEvent('add', path))
      .on('change', (path) => this.handleFileEvent('change', path))
      .on('unlink', (path) => this.handleFileEvent('unlink', path))
      .on('error', (error) => log.error('Watcher error', error as Error))
      .on('ready', () => {
        if (!this.readyLogged) {
          log.info('File watcher ready')
          this.readyLogged = true
        }
      })
  }

  stop(): void {
    if (!this.watcher) {
      log.debug('FileWatcher not running')
      return
    }

    log.info('Stopping file watcher')
    this.watcher.close()
    this.watcher = null
    this.readyLogged = false

    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer)
      this.debounceTimer = null
    }
  }

  getState(): { isRunning: boolean; watchedPaths: string[]; queueSize: number } {
    return {
      isRunning: this.watcher !== null,
      watchedPaths: this.config.paths,
      queueSize: this.ingestQueue.size,
    }
  }

  private handleFileEvent(event: 'add' | 'change' | 'unlink', filePath: string): void {
    // Filter by allowed extensions
    const ext = extname(filePath).toLowerCase()
    const allowedExtensions = this.config.patterns.map((p) => p.replace('*', ''))
    if (!allowedExtensions.includes(ext)) {
      return // Skip non-matching files
    }

    log.debug('File event', { event, path: filePath })

    if (event === 'unlink') {
      // Handle deletion immediately
      this.handleDeletion(filePath)
      return
    }

    // Queue file for ingestion (debounced)
    this.ingestQueue.add(filePath)
    this.scheduleProcessing()
  }

  private async handleDeletion(filePath: string): Promise<void> {
    try {
      const tracker = getFileTracker()
      const result = await tracker.markDeleted(filePath)

      if (result.supersededChunks.length > 0) {
        log.info('Marked file as deleted', {
          path: filePath,
          supersededChunks: result.supersededChunks.length,
        })

        // TODO: Optionally soft-delete chunks in Qdrant
        // For now, they'll be cleaned up by vacuum
      }
    } catch (error) {
      log.error('Failed to handle deletion', { path: filePath, error })
    }
  }

  private scheduleProcessing(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer)
    }

    // Debounce: wait 1s after last event before processing
    this.debounceTimer = setTimeout(() => {
      this.processQueue()
    }, 1000)
  }

  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.ingestQueue.size === 0) {
      return
    }

    this.isProcessing = true
    const files = Array.from(this.ingestQueue)
    this.ingestQueue.clear()

    log.info('Processing file queue', { count: files.length })

    try {
      // Dynamic import to avoid circular dependency
      const { ingest } = await import('../domain/ingest')
      const { computeRootDir } = await import('../shared/utils')

      // Filter to only files that need ingestion
      const tracker = getFileTracker()
      const filesToIngest: string[] = []

      for (const file of files) {
        const result = await tracker.needsIngestion(file)
        if (result.needsIngest) {
          filesToIngest.push(file)
        } else {
          log.debug('File unchanged, skipping', { path: file })
        }
      }

      if (filesToIngest.length === 0) {
        log.debug('No files need ingestion')
        return
      }

      log.info('Ingesting files', { count: filesToIngest.length })

      const result = await ingest({
        paths: filesToIngest,
        recursive: false,
        rootDir: computeRootDir(filesToIngest),
        verbose: false,
      })

      log.info('Ingestion complete', {
        files: result.filesProcessed,
        chunks: result.chunksStored,
        errors: result.errors.length,
      })
    } catch (error) {
      log.error('Failed to process queue', error as Error)

      // Re-queue failed files for retry
      for (const file of files) {
        this.ingestQueue.add(file)
      }
    } finally {
      this.isProcessing = false
    }
  }
}

// Singleton instance
let instance: FileWatcher | null = null

export function getFileWatcher(): FileWatcher {
  if (!instance) {
    instance = new FileWatcher()
  }
  return instance
}

export function resetFileWatcher(): void {
  if (instance) {
    instance.stop()
    instance = null
  }
}
