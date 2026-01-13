/**
 * Atlas daemon socket server
 *
 * Provides Unix domain socket (macOS/Linux) and named pipe (Windows) support
 * for JSON-RPC communication.
 */

import { createServer, Server as NetServer, Socket } from 'net'
import { unlinkSync, existsSync, mkdirSync } from 'fs'
import { join } from 'path'
import { homedir, platform } from 'os'
import { createLogger } from '../shared/logger.js'
import type { JsonRpcRequest, JsonRpcResponse, JsonRpcNotification } from './protocol.js'
import { parseMessage, serializeMessage, createErrorResponse, JsonRpcErrorCode } from './protocol.js'
import type { EventRouter } from './router.js'

const log = createLogger('daemon:server')

/**
 * Get daemon runtime directory path
 */
export function getDaemonDir(): string {
  return join(homedir(), '.atlas', 'daemon')
}

/**
 * Get socket path for platform
 */
export function getSocketPath(): string {
  const isWindows = platform() === 'win32'

  if (isWindows) {
    // Windows named pipe
    return '\\\\.\\pipe\\atlas'
  } else {
    // Unix domain socket
    return join(getDaemonDir(), 'atlas.sock')
  }
}

/**
 * Get PID file path
 */
export function getPidFilePath(): string {
  return join(getDaemonDir(), 'atlas.pid')
}

/**
 * Client connection state
 */
interface ClientConnection {
  socket: Socket
  id: string
  subscriptions: Set<string> // Event type patterns
}

/**
 * Atlas daemon server
 */
export class AtlasDaemonServer {
  private server: NetServer
  private clients: Map<string, ClientConnection> = new Map()
  private socketPath: string
  private router: EventRouter
  private nextClientId = 1

  constructor(router: EventRouter, socketPath?: string) {
    this.socketPath = socketPath || getSocketPath()
    this.router = router
    this.server = createServer((socket) => this.handleConnection(socket))
  }

  /**
   * Start the server
   */
  async start(): Promise<void> {
    // Ensure daemon directory exists
    const daemonDir = getDaemonDir()
    if (!existsSync(daemonDir)) {
      mkdirSync(daemonDir, { recursive: true })
      log.info('Created daemon directory', { path: daemonDir })
    }

    // Clean up existing socket file (Unix only)
    if (platform() !== 'win32' && existsSync(this.socketPath)) {
      try {
        unlinkSync(this.socketPath)
        log.debug('Removed existing socket file', { path: this.socketPath })
      } catch (error) {
        log.warn('Failed to remove existing socket', { path: this.socketPath, error })
      }
    }

    return new Promise((resolve, reject) => {
      this.server.on('error', (error) => {
        log.error('Server error', { error })
        reject(error)
      })

      this.server.listen(this.socketPath, () => {
        log.info('Daemon server started', { socket: this.socketPath, pid: process.pid })
        resolve()
      })
    })
  }

  /**
   * Stop the server
   */
  async stop(): Promise<void> {
    return new Promise((resolve, reject) => {
      // Close all client connections
      for (const client of this.clients.values()) {
        client.socket.end()
      }
      this.clients.clear()

      this.server.close((error) => {
        if (error) {
          log.error('Error closing server', { error })
          reject(error)
        } else {
          log.info('Daemon server stopped')
          resolve()
        }
      })

      // Clean up socket file (Unix only)
      if (platform() !== 'win32' && existsSync(this.socketPath)) {
        try {
          unlinkSync(this.socketPath)
        } catch (error) {
          log.warn('Failed to remove socket file', { path: this.socketPath, error })
        }
      }
    })
  }

  /**
   * Handle new client connection
   */
  private handleConnection(socket: Socket): void {
    const clientId = `client-${this.nextClientId++}`
    const client: ClientConnection = {
      socket,
      id: clientId,
      subscriptions: new Set(),
    }

    this.clients.set(clientId, client)
    log.debug('Client connected', { clientId, total: this.clients.size })

    // Set up data buffering for JSON-RPC messages
    let buffer = ''

    socket.on('data', (chunk) => {
      buffer += chunk.toString()

      // Process complete messages (newline-delimited)
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete message in buffer

      for (const line of lines) {
        if (line.trim()) {
          this.handleMessage(client, line.trim())
        }
      }
    })

    socket.on('end', () => {
      this.clients.delete(clientId)
      log.debug('Client disconnected', { clientId, total: this.clients.size })
    })

    socket.on('error', (error) => {
      log.error('Client socket error', { clientId, error })
      this.clients.delete(clientId)
    })
  }

  /**
   * Handle JSON-RPC message from client
   */
  private async handleMessage(client: ClientConnection, message: string): Promise<void> {
    try {
      const parsed = parseMessage(message)

      // Only handle requests (not responses or notifications from clients)
      if ('method' in parsed && 'id' in parsed) {
        const request = parsed as JsonRpcRequest
        const response = await this.router.handleRequest(request, client.id)
        this.sendMessage(client, response)
      }
    } catch (error) {
      log.error('Failed to handle message', { clientId: client.id, error })

      // Send parse error response (if we can extract an ID)
      try {
        const parsed = JSON.parse(message)
        const id = parsed.id || 0
        const errorResponse = createErrorResponse(
          id,
          JsonRpcErrorCode.ParseError,
          'Failed to parse JSON-RPC message',
          (error as Error).message
        )
        this.sendMessage(client, errorResponse)
      } catch {
        // Can't even parse to get ID, ignore
      }
    }
  }

  /**
   * Send message to client
   */
  private sendMessage(
    client: ClientConnection,
    message: JsonRpcResponse | JsonRpcNotification
  ): void {
    try {
      const serialized = serializeMessage(message)
      client.socket.write(serialized + '\n')
    } catch (error) {
      log.error('Failed to send message', { clientId: client.id, error })
    }
  }

  /**
   * Broadcast event to subscribed clients
   */
  broadcastEvent(event: import('./events').AtlasEvent): void {
    for (const client of this.clients.values()) {
      // Check if client is subscribed to this event type
      if (this.isSubscribed(client, event.type)) {
        const notification: JsonRpcNotification = {
          jsonrpc: '2.0',
          method: 'event',
          params: event,
        }
        this.sendMessage(client, notification)
      }
    }
  }

  /**
   * Check if client is subscribed to event type
   */
  private isSubscribed(client: ClientConnection, eventType: string): boolean {
    for (const pattern of client.subscriptions) {
      if (this.matchesPattern(eventType, pattern)) {
        return true
      }
    }
    return false
  }

  /**
   * Match event type against subscription pattern
   * Supports wildcards: "ingest.*" matches "ingest.started", "ingest.completed", etc.
   */
  private matchesPattern(eventType: string, pattern: string): boolean {
    if (pattern === '*') return true
    if (pattern === eventType) return true

    // Convert glob pattern to regex
    const regexPattern = pattern.replace(/\./g, '\\.').replace(/\*/g, '.*')
    const regex = new RegExp(`^${regexPattern}$`)
    return regex.test(eventType)
  }

  /**
   * Add subscription for client
   */
  subscribe(clientId: string, patterns: string[]): void {
    const client = this.clients.get(clientId)
    if (client) {
      for (const pattern of patterns) {
        client.subscriptions.add(pattern)
      }
      log.debug('Client subscribed', { clientId, patterns, total: client.subscriptions.size })
    }
  }

  /**
   * Remove subscription for client
   */
  unsubscribe(clientId: string, patterns: string[]): void {
    const client = this.clients.get(clientId)
    if (client) {
      for (const pattern of patterns) {
        client.subscriptions.delete(pattern)
      }
      log.debug('Client unsubscribed', { clientId, patterns, remaining: client.subscriptions.size })
    }
  }

  /**
   * Get server status
   */
  getStatus(): {
    clients: number
    uptime: number
    socket: string
  } {
    return {
      clients: this.clients.size,
      uptime: process.uptime(),
      socket: this.socketPath,
    }
  }
}
