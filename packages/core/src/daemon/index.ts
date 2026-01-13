/**
 * Atlas daemon entry point
 *
 * Exports daemon components and provides main daemon start function.
 */

export * from './events.js'
export * from './protocol.js'
export * from './server.js'
export * from './router.js'

import { EventRouter } from './router.js'
import { AtlasDaemonServer, getSocketPath, getPidFilePath } from './server.js'
import { writeFileSync, existsSync, readFileSync, unlinkSync } from 'fs'
import { createLogger } from '../shared/logger.js'
import { schedulerManager } from '../core/scheduler-manager.js'
import { getSystemPressureMonitor } from '../core/system-pressure-monitor.js'
import { getFileWatcher } from '../core/file-watcher.js'
import { getConfig } from '../shared/config.loader.js'
import { ensureCollection } from '../shared/utils.js'
import { registerPrompts } from '../prompts/index.js'
import { getStorageService } from '../services/storage/index.js'
import { getFileTracker } from '../services/tracking/tracker.js'

const log = createLogger('daemon')

/**
 * Global daemon instance
 */
let daemonInstance: AtlasDaemon | null = null

/**
 * Daemon configuration
 */
export interface DaemonConfig {
  socketPath?: string
  detach?: boolean
  tcpPort?: number
  /** Enable file watcher (overrides config file setting) */
  enableFileWatcher?: boolean
}

/**
 * Atlas daemon
 */
export class AtlasDaemon {
  private router: EventRouter
  private server: AtlasDaemonServer
  private config: DaemonConfig

  constructor(config: DaemonConfig = {}) {
    this.config = config
    this.router = new EventRouter()
    this.server = new AtlasDaemonServer(this.router, config.socketPath)
    this.router.setServer(this.server)
  }

  /**
   * Register schedulers with the scheduler manager
   */
  private registerSchedulers(): void {
    const atlasConfig = getConfig()
    const autoStart = atlasConfig.daemon?.autoStart ?? {
      systemPressureMonitor: true,
      fileWatcher: true,
    }

    // Always register system pressure monitor (required by adaptive parallel)
    if (autoStart.systemPressureMonitor !== false) {
      schedulerManager.register(getSystemPressureMonitor())
      log.debug('Registered SystemPressureMonitor')
    }

    // Register FileWatcher if enabled (watches ~/.atlas by default)
    if (autoStart.fileWatcher !== false) {
      schedulerManager.register(getFileWatcher())
      log.debug('Registered FileWatcher')
    }
  }

  /**
   * Start the daemon
   */
  async start(): Promise<void> {
    // Check if daemon is already running
    if (this.isDaemonRunning()) {
      throw new Error('Daemon is already running')
    }

    // Clean up stale socket file
    this.cleanupStaleSocket()

    // Initialize ApplicationService (including storage service)
    await this.router.initialize()
    log.debug('ApplicationService initialized')

    // Initialize FileTracker with database instance (BEFORE starting schedulers)
    const storageService = getStorageService()
    const db = storageService.getDatabase()
    getFileTracker(db)
    log.debug('FileTracker initialized with database')

    // Ensure collection exists before any operations
    await ensureCollection()
    log.debug('Collection ensured')

    // Write PID file
    this.writePidFile()

    // Set up signal handlers
    this.setupSignalHandlers()

    // Register and start schedulers
    this.registerSchedulers()

    // Start server
    await this.server.start()

    // Start all registered schedulers
    schedulerManager.startAll()

    // Emit started event
    this.router.emit({
      type: 'daemon.started',
      data: {
        pid: process.pid,
        socket: getSocketPath(),
      },
    })

    log.info('Atlas daemon started', { pid: process.pid })

    // If detached, print ssh-agent style output
    if (!this.config.detach) {
      this.printStartupCommands()
    }
  }

  /**
   * Stop the daemon
   */
  async stop(): Promise<void> {
    log.info('Stopping daemon...')

    // Emit stopping event
    this.router.emit({
      type: 'daemon.stopping',
      data: {
        reason: 'manual',
      },
    })

    // Stop all schedulers before stopping server
    schedulerManager.stopAll()

    // Stop server
    await this.server.stop()

    // Remove PID file
    this.removePidFile()

    log.info('Daemon stopped')
  }

  /**
   * Check if daemon is running
   */
  private isDaemonRunning(): boolean {
    const pidFile = getPidFilePath()
    if (!existsSync(pidFile)) {
      return false
    }

    try {
      const pid = parseInt(readFileSync(pidFile, 'utf-8').trim(), 10)

      // Check if process exists
      try {
        process.kill(pid, 0) // Signal 0 checks existence without killing
        return true
      } catch {
        // Process doesn't exist, clean up stale PID file
        unlinkSync(pidFile)
        return false
      }
    } catch {
      return false
    }
  }

  /**
   * Write PID file
   */
  private writePidFile(): void {
    const pidFile = getPidFilePath()
    writeFileSync(pidFile, process.pid.toString(), 'utf-8')
    log.debug('Wrote PID file', { pid: process.pid, file: pidFile })
  }

  /**
   * Remove PID file
   */
  private removePidFile(): void {
    const pidFile = getPidFilePath()
    if (existsSync(pidFile)) {
      unlinkSync(pidFile)
      log.debug('Removed PID file', { file: pidFile })
    }
  }

  /**
   * Clean up stale socket file
   */
  private cleanupStaleSocket(): void {
    const socketPath = getSocketPath()
    if (existsSync(socketPath)) {
      try {
        unlinkSync(socketPath)
        log.debug('Removed stale socket', { path: socketPath })
      } catch (error) {
        log.warn('Failed to remove stale socket', { path: socketPath, error })
      }
    }
  }

  /**
   * Set up signal handlers
   */
  private setupSignalHandlers(): void {
    let isShuttingDown = false

    const handleSignal = (signal: string) => {
      if (isShuttingDown) {
        log.warn('Already shutting down, ignoring signal', { signal })
        return
      }
      isShuttingDown = true

      log.info('Received signal, stopping daemon', { signal })
      this.router.emit({
        type: 'daemon.stopping',
        data: {
          reason: 'signal',
        },
      })

      this.stop()
        .then(() => {
          log.info('Daemon stopped gracefully')
          process.exit(0)
        })
        .catch((error) => {
          log.error('Error during shutdown', error as Error)
          process.exit(1)
        })
    }

    const handleException = (error: Error, type: string) => {
      if (isShuttingDown) {
        return
      }
      isShuttingDown = true

      log.error(`Unhandled ${type}, shutting down`, error)
      this.router.emit({
        type: 'daemon.stopping',
        data: {
          reason: 'error',
        },
      })

      this.stop()
        .then(() => process.exit(1))
        .catch(() => process.exit(1))
    }

    // Graceful shutdown signals
    process.on('SIGINT', () => handleSignal('SIGINT'))
    process.on('SIGTERM', () => handleSignal('SIGTERM'))
    process.on('SIGHUP', () => handleSignal('SIGHUP'))

    // Crash handlers
    process.on('uncaughtException', (error) => handleException(error, 'exception'))
    process.on('unhandledRejection', (reason) => {
      const error = reason instanceof Error ? reason : new Error(String(reason))
      handleException(error, 'rejection')
    })

    // Normal exit cleanup
    process.on('beforeExit', () => {
      if (!isShuttingDown) {
        log.debug('Process exiting normally')
        this.removePidFile()
      }
    })
  }

  /**
   * Print startup commands (ssh-agent style)
   */
  private printStartupCommands(): void {
    const socketPath = this.config.socketPath || getSocketPath()
    console.log(`ATLAS_SOCK=${socketPath}; export ATLAS_SOCK;`)
    console.log(`echo Atlas daemon pid ${process.pid};`)
  }

  /**
   * Get router instance
   */
  getRouter(): EventRouter {
    return this.router
  }

  /**
   * Get server instance
   */
  getServer(): AtlasDaemonServer {
    return this.server
  }
}

/**
 * Start daemon
 */
export async function startDaemon(config: DaemonConfig = {}): Promise<AtlasDaemon> {
  if (daemonInstance) {
    throw new Error('Daemon already started')
  }

  // Register prompts before starting daemon (required for consolidation, etc.)
  registerPrompts()
  log.debug('Prompts registered for daemon')

  daemonInstance = new AtlasDaemon(config)
  await daemonInstance.start()

  return daemonInstance
}

/**
 * Stop daemon
 */
export async function stopDaemon(): Promise<void> {
  if (!daemonInstance) {
    throw new Error('Daemon not running')
  }

  await daemonInstance.stop()
  daemonInstance = null
}

/**
 * Get daemon instance
 */
export function getDaemon(): AtlasDaemon | null {
  return daemonInstance
}

/**
 * Check if daemon is running (by PID file)
 */
export function isDaemonRunning(): boolean {
  const pidFile = getPidFilePath()
  if (!existsSync(pidFile)) {
    return false
  }

  try {
    const pid = parseInt(readFileSync(pidFile, 'utf-8').trim(), 10)
    process.kill(pid, 0)
    return true
  } catch {
    return false
  }
}

/**
 * Get daemon PID
 */
export function getDaemonPid(): number | null {
  const pidFile = getPidFilePath()
  if (!existsSync(pidFile)) {
    return null
  }

  try {
    return parseInt(readFileSync(pidFile, 'utf-8').trim(), 10)
  } catch {
    return null
  }
}

/**
 * Kill daemon process
 */
export function killDaemon(): boolean {
  const pid = getDaemonPid()
  if (!pid) {
    return false
  }

  try {
    process.kill(pid, 'SIGTERM')
    return true
  } catch {
    return false
  }
}
