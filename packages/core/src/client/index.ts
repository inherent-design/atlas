/**
 * Atlas client library
 *
 * Provides programmatic access to Atlas daemon via JSON-RPC.
 */

export * from './connection.js'

import { AtlasConnection } from './connection.js'
import type {
  IngestParams,
  SearchParams,
  ConsolidateParams,
  HealthResult,
  StatusResult,
} from '../daemon/protocol.js'
import type { AtlasEvent } from '../daemon/events.js'

/**
 * Atlas client
 */
export class AtlasClient {
  private connection: AtlasConnection

  constructor(socketPath?: string) {
    this.connection = new AtlasConnection(socketPath)
  }

  /**
   * Connect to daemon
   */
  async connect(): Promise<void> {
    await this.connection.connect()
  }

  /**
   * Disconnect from daemon
   */
  disconnect(): void {
    this.connection.disconnect()
  }

  /**
   * Ingest files
   */
  async ingest(params: IngestParams) {
    return this.connection.request('atlas.ingest', params)
  }

  /**
   * Search
   */
  async search(params: SearchParams) {
    return this.connection.request('atlas.search', params)
  }

  /**
   * Consolidate
   */
  async consolidate(params: ConsolidateParams) {
    return this.connection.request('atlas.consolidate', params)
  }

  /**
   * Health check
   */
  async health(): Promise<HealthResult> {
    return this.connection.request('atlas.health', {})
  }

  /**
   * Get status
   */
  async status(): Promise<StatusResult> {
    return this.connection.request('atlas.status', {})
  }

  /**
   * Subscribe to events
   */
  async subscribe(patterns: string[]): Promise<void> {
    await this.connection.subscribe(patterns)
  }

  /**
   * Unsubscribe from events
   */
  async unsubscribe(patterns: string[]): Promise<void> {
    await this.connection.unsubscribe(patterns)
  }

  /**
   * Add event handler
   */
  on(handler: (event: AtlasEvent) => void): void {
    this.connection.onEvent(handler)
  }

  /**
   * Remove event handler
   */
  off(handler: (event: AtlasEvent) => void): void {
    this.connection.offEvent(handler)
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connection.isConnected()
  }
}

/**
 * Create client and connect
 */
export async function createClient(socketPath?: string): Promise<AtlasClient> {
  const client = new AtlasClient(socketPath)
  await client.connect()
  return client
}
