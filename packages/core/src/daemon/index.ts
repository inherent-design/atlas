/**
 * Atlas daemon entry point
 *
 * Exports daemon components and provides main daemon start function.
 */

export * from './events'
export * from './protocol'
export * from './server'
export * from './router'

import { EventRouter } from './router'
import { AtlasDaemonServer, getSocketPath, getPidFilePath } from './server'
import { writeFileSync, existsSync, readFileSync, unlinkSync } from 'fs'
import { createLogger } from '../shared/logger'
import { schedulerManager } from '../core/scheduler-manager'
import { getConsolidationWatchdog } from '../domain/consolidate/watchdog'
import { getSystemPressureMonitor } from '../core/system-pressure-monitor'
import { getFileWatcher } from '../core/file-watcher'
import { getConfig } from '../shared/config.loader'

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
      consolidationWatchdog: true,
      systemPressureMonitor: true,
      fileWatcher: false,
    }

    // Always register system pressure monitor (required by adaptive parallel)
    if (autoStart.systemPressureMonitor !== false) {
      schedulerManager.register(getSystemPressureMonitor())
      log.debug('Registered SystemPressureMonitor')
    }

    // Register consolidation watchdog if enabled
    if (autoStart.consolidationWatchdog !== false) {
      schedulerManager.register(getConsolidationWatchdog())
      log.debug('Registered ConsolidationWatchdog')
    }

    // Register file watcher if enabled via config or CLI flag
    if (this.config.enableFileWatcher === true || autoStart.fileWatcher === true) {
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
   * Set up signal handlers
   */
  private setupSignalHandlers(): void {
    const handleSignal = (signal: string) => {
      log.info('Received signal, stopping daemon', { signal })
      this.router.emit({
        type: 'daemon.stopping',
        data: {
          reason: 'signal',
        },
      })
      this.stop().then(() => {
        process.exit(0)
      })
    }

    process.on('SIGINT', () => handleSignal('SIGINT'))
    process.on('SIGTERM', () => handleSignal('SIGTERM'))
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
