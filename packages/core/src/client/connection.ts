/**
 * Atlas daemon client connection
 *
 * Provides socket-based JSON-RPC communication with the Atlas daemon.
 */

import { Socket } from 'net'
import { getSocketPath } from '../daemon/server'
import { createLogger } from '../shared/logger'
import type {
  JsonRpcRequest,
  JsonRpcResponse,
  JsonRpcNotification,
  AtlasMethod,
  MethodParams,
  MethodResult,
} from '../daemon/protocol'
import { createRequest, parseMessage, serializeMessage } from '../daemon/protocol'
import type { AtlasEvent } from '../daemon/events'

const log = createLogger('client:connection')

/**
 * Connection state
 */
type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'closed'

/**
 * Atlas daemon connection
 */
export class AtlasConnection {
  private socket: Socket | null = null
  private state: ConnectionState = 'disconnected'
  private socketPath: string
  private buffer = ''
  private pendingRequests = new Map<
    string | number,
    {
      resolve: (result: unknown) => void
      reject: (error: Error) => void
    }
  >()
  private nextRequestId = 1
  private eventHandlers: Set<(event: AtlasEvent) => void> = new Set()

  constructor(socketPath?: string) {
    this.socketPath = socketPath || getSocketPath()
  }

  /**
   * Connect to daemon
   */
  async connect(): Promise<void> {
    if (this.state === 'connected') {
      return
    }

    if (this.state === 'connecting') {
      throw new Error('Connection already in progress')
    }

    this.state = 'connecting'

    return new Promise((resolve, reject) => {
      this.socket = new Socket()

      this.socket.on('connect', () => {
        this.state = 'connected'
        log.debug('Connected to daemon', { socket: this.socketPath })
        resolve()
      })

      this.socket.on('data', (chunk) => {
        this.handleData(chunk)
      })

      this.socket.on('end', () => {
        log.debug('Connection ended')
        this.state = 'closed'
      })

      this.socket.on('error', (error) => {
        log.error('Socket error', { error })
        if (this.state === 'connecting') {
          this.state = 'disconnected'
          reject(error)
        }
      })

      this.socket.connect(this.socketPath)
    })
  }

  /**
   * Disconnect from daemon
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.end()
      this.socket = null
    }
    this.state = 'disconnected'
  }

  /**
   * Send request and wait for response
   */
  async request<M extends AtlasMethod>(
    method: M,
    params?: MethodParams<M>
  ): Promise<MethodResult<M>> {
    if (this.state !== 'connected') {
      throw new Error('Not connected to daemon')
    }

    const id = this.nextRequestId++
    const request = createRequest(id, method, params)

    // Create promise for response
    const responsePromise = new Promise<MethodResult<M>>((resolve, reject) => {
      this.pendingRequests.set(id, { resolve: resolve as (result: unknown) => void, reject })
    })

    // Send request
    this.send(request)

    return responsePromise
  }

  /**
   * Subscribe to events
   */
  async subscribe(patterns: string[]): Promise<void> {
    await this.request('atlas.subscribe', { events: patterns })
  }

  /**
   * Unsubscribe from events
   */
  async unsubscribe(patterns: string[]): Promise<void> {
    await this.request('atlas.unsubscribe', { events: patterns })
  }

  /**
   * Add event handler
   */
  onEvent(handler: (event: AtlasEvent) => void): void {
    this.eventHandlers.add(handler)
  }

  /**
   * Remove event handler
   */
  offEvent(handler: (event: AtlasEvent) => void): void {
    this.eventHandlers.delete(handler)
  }

  /**
   * Handle incoming data
   */
  private handleData(chunk: Buffer): void {
    this.buffer += chunk.toString()

    // Process complete messages (newline-delimited)
    const lines = this.buffer.split('\n')
    this.buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.trim()) {
        this.handleMessage(line.trim())
      }
    }
  }

  /**
   * Handle parsed message
   */
  private handleMessage(message: string): void {
    try {
      const parsed = parseMessage(message)

      if ('result' in parsed || 'error' in parsed) {
        // Response
        this.handleResponse(parsed as JsonRpcResponse)
      } else if ('method' in parsed && parsed.method === 'event') {
        // Event notification
        this.handleEvent(parsed as JsonRpcNotification)
      }
    } catch (error) {
      log.error('Failed to parse message', { error })
    }
  }

  /**
   * Handle response
   */
  private handleResponse(response: JsonRpcResponse): void {
    const pending = this.pendingRequests.get(response.id)
    if (!pending) {
      log.warn('Received response for unknown request', { id: response.id })
      return
    }

    this.pendingRequests.delete(response.id)

    if (response.error) {
      pending.reject(new Error(response.error.message))
    } else {
      pending.resolve(response.result)
    }
  }

  /**
   * Handle event notification
   */
  private handleEvent(notification: JsonRpcNotification): void {
    const event = notification.params as AtlasEvent

    for (const handler of this.eventHandlers) {
      try {
        handler(event)
      } catch (error) {
        log.error('Event handler error', { type: event.type, error })
      }
    }
  }

  /**
   * Send message
   */
  private send(message: JsonRpcRequest): void {
    if (!this.socket) {
      throw new Error('Socket not initialized')
    }

    const serialized = serializeMessage(message)
    this.socket.write(serialized + '\n')
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.state === 'connected'
  }
}
