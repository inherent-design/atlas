/**
 * Event router with multi-lane architecture
 *
 * Routes JSON-RPC requests to appropriate handlers and manages event lanes:
 * - Ingest Lane: embed, qntm, upsert operations
 * - Search Lane: activate, format operations
 * - Consolidate Lane: background consolidation
 * - Watch Lane: file watcher operations
 * - Admin Lane: health checks, dependencies
 */

import type { JsonRpcRequest, JsonRpcResponse, AtlasMethod } from './protocol'
import {
  createResponse,
  createErrorResponse,
  JsonRpcErrorCode,
  type IngestParams,
  type IngestResult,
  type SearchParams,
  type SearchResult,
  type ConsolidateParams,
  type ConsolidateResult,
  type SubscribeParams,
  type SubscribeResult,
  type UnsubscribeParams,
  type UnsubscribeResult,
  type HealthParams,
  type HealthResult,
  type StatusParams,
  type StatusResult,
  type SessionEventParams,
  type SessionEventResult,
  type ExecuteWorkParams,
  type ExecuteWorkResult,
  type GetAgentContextParams,
  type GetAgentContextResult,
} from './protocol'
import { createLogger } from '../shared/logger'
import type { AtlasDaemonServer } from './server'
import type { AtlasEvent } from './events'

const log = createLogger('daemon:router')

/**
 * Method handler function
 */
type MethodHandler<P = unknown, R = unknown> = (params: P, clientId: string) => Promise<R>

/**
 * Event router
 */
export class EventRouter {
  private handlers: Map<AtlasMethod, MethodHandler<any, any>> = new Map()
  private server: AtlasDaemonServer | null = null
  private eventListeners: Set<(event: AtlasEvent) => void> = new Set()
  private startTime: number

  constructor() {
    this.startTime = Date.now()
    this.registerDefaultHandlers()
  }

  /**
   * Set the server instance (for subscriptions)
   */
  setServer(server: AtlasDaemonServer): void {
    this.server = server
  }

  /**
   * Register default method handlers
   */
  private registerDefaultHandlers(): void {
    this.registerHandler('atlas.ingest', this.handleIngest.bind(this))
    this.registerHandler('atlas.search', this.handleSearch.bind(this))
    this.registerHandler('atlas.consolidate', this.handleConsolidate.bind(this))
    this.registerHandler('atlas.subscribe', this.handleSubscribe.bind(this))
    this.registerHandler('atlas.unsubscribe', this.handleUnsubscribe.bind(this))
    this.registerHandler('atlas.health', this.handleHealth.bind(this))
    this.registerHandler('atlas.status', this.handleStatus.bind(this))
    this.registerHandler('atlas.session_event', this.handleSessionEvent.bind(this))
    this.registerHandler('atlas.execute_work', this.handleExecuteWork.bind(this))
    this.registerHandler('atlas.get_agent_context', this.handleGetAgentContext.bind(this))
  }

  /**
   * Register a method handler
   */
  registerHandler<M extends AtlasMethod>(method: M, handler: MethodHandler<any, any>): void {
    this.handlers.set(method, handler)
    log.debug('Registered handler', { method })
  }

  /**
   * Handle JSON-RPC request
   */
  async handleRequest(request: JsonRpcRequest, clientId: string): Promise<JsonRpcResponse> {
    const { id, method, params } = request

    log.debug('Handling request', { id, method, clientId })

    // Find handler
    const handler = this.handlers.get(method as AtlasMethod)
    if (!handler) {
      return createErrorResponse(id, JsonRpcErrorCode.MethodNotFound, `Method not found: ${method}`)
    }

    try {
      // Execute handler
      const result = await handler(params || {}, clientId)

      // Return success response
      return createResponse(id, result)
    } catch (error) {
      log.error('Handler error', { id, method, error })

      return createErrorResponse(
        id,
        JsonRpcErrorCode.InternalError,
        'Internal error',
        (error as Error).message
      )
    }
  }

  /**
   * Emit event to all listeners
   */
  emit(event: AtlasEvent): void {
    // Notify all event listeners
    for (const listener of this.eventListeners) {
      try {
        listener(event)
      } catch (error) {
        log.error('Event listener error', { type: event.type, error })
      }
    }

    // Broadcast to connected clients (if server is set)
    if (this.server) {
      this.server.broadcastEvent(event)
    }
  }

  /**
   * Add event listener
   */
  addEventListener(listener: (event: AtlasEvent) => void): void {
    this.eventListeners.add(listener)
  }

  /**
   * Remove event listener
   */
  removeEventListener(listener: (event: AtlasEvent) => void): void {
    this.eventListeners.delete(listener)
  }

  // ============================================
  // Method Handlers
  // ============================================

  /**
   * Handle atlas.ingest
   */
  private async handleIngest(params: IngestParams, _clientId: string): Promise<IngestResult> {
    // Import ingest function dynamically to avoid circular dependencies
    const { ingest } = await import('../domain/ingest')

    const result = await ingest({
      paths: params.paths,
      recursive: params.recursive ?? false,
      verbose: params.verbose ?? false,
      // Pass event emitter to domain function
      emit: (event) => this.emit(event),
    })

    return {
      filesProcessed: result.filesProcessed,
      chunksStored: result.chunksStored,
      errors: result.errors,
    }
  }

  /**
   * Handle atlas.search
   */
  private async handleSearch(params: SearchParams, _clientId: string): Promise<SearchResult[]> {
    // Import search function dynamically
    const { search } = await import('../domain/search')

    const results = await search({
      query: params.query,
      limit: params.limit,
      since: params.since,
      qntmKey: params.qntmKey,
      rerank: params.rerank ?? false,
      consolidationLevel: params.consolidationLevel,
      expandQuery: params.expandQuery ?? false,
      // Pass event emitter to domain function
      emit: (event) => this.emit(event),
    })

    return results.map((r) => ({
      text: r.text,
      filePath: r.file_path,
      chunkIndex: r.chunk_index,
      score: r.score,
      createdAt: r.created_at,
      qntmKey: r.qntm_key,
      rerankScore: r.rerank_score,
    }))
  }

  /**
   * Handle atlas.consolidate
   */
  private async handleConsolidate(
    params: ConsolidateParams,
    _clientId: string
  ): Promise<ConsolidateResult> {
    // Import consolidate function dynamically
    const { consolidate } = await import('../domain/consolidate')

    const result = await consolidate({
      dryRun: params.dryRun,
      threshold: params.threshold,
      // Pass event emitter to domain function
      emit: (event) => this.emit(event),
    })

    return {
      candidatesFound: result.candidatesFound,
      consolidated: result.consolidated,
      deleted: result.deleted,
      rounds: result.rounds,
      maxLevel: result.maxLevel,
      levelStats: result.levelStats,
    }
  }

  /**
   * Handle atlas.subscribe
   */
  private async handleSubscribe(
    params: SubscribeParams,
    clientId: string
  ): Promise<SubscribeResult> {
    if (!this.server) {
      throw new Error('Server not initialized')
    }

    this.server.subscribe(clientId, params.events)

    return {
      subscribed: params.events,
    }
  }

  /**
   * Handle atlas.unsubscribe
   */
  private async handleUnsubscribe(
    params: UnsubscribeParams,
    clientId: string
  ): Promise<UnsubscribeResult> {
    if (!this.server) {
      throw new Error('Server not initialized')
    }

    this.server.unsubscribe(clientId, params.events)

    return {
      unsubscribed: params.events,
    }
  }

  /**
   * Handle atlas.health
   */
  private async handleHealth(_params: HealthParams, _clientId: string): Promise<HealthResult> {
    // Check Qdrant
    let qdrant = { available: false, url: '', error: '' }
    try {
      const { getStorageBackend } = await import('../services/storage')
      const storage = getStorageBackend()
      if (storage) {
        qdrant = { available: true, url: 'http://localhost:6333', error: '' }
      }
    } catch (error) {
      qdrant.error = (error as Error).message
    }

    // Check Ollama
    let ollama = { available: false, url: '', error: '' }
    try {
      const { OLLAMA_URL } = await import('../shared/config')
      const response = await fetch(`${OLLAMA_URL}/api/tags`)
      ollama = { available: response.ok, url: OLLAMA_URL, error: '' }
    } catch (error) {
      ollama.error = (error as Error).message
    }

    // Check Voyage
    const voyage = {
      available: !!process.env.VOYAGE_API_KEY,
      hasKey: !!process.env.VOYAGE_API_KEY,
      error: !process.env.VOYAGE_API_KEY ? 'VOYAGE_API_KEY not set' : undefined,
    }

    // Determine overall health
    let overall: 'healthy' | 'degraded' | 'unhealthy'
    if (qdrant.available && (voyage.available || ollama.available)) {
      overall = 'healthy'
    } else if (qdrant.available) {
      overall = 'degraded'
    } else {
      overall = 'unhealthy'
    }

    return { qdrant, ollama, voyage, overall }
  }

  /**
   * Handle atlas.status
   */
  private async handleStatus(_params: StatusParams, _clientId: string): Promise<StatusResult> {
    const status = this.server?.getStatus() || { clients: 0, uptime: 0, socket: '' }

    return {
      pid: process.pid,
      uptime: Math.floor((Date.now() - this.startTime) / 1000),
      socket: status.socket,
      clients: status.clients,
      version: '0.1.0',
    }
  }

  /**
   * Handle atlas.session_event - forward session lifecycle events from Claude Code
   */
  private async handleSessionEvent(
    params: SessionEventParams,
    _clientId: string
  ): Promise<SessionEventResult> {
    const { type, data } = params

    log.info('Received session event', { type, sessionId: data.sessionId })

    // Emit internal event for subscribers
    if (type === 'session.compacting') {
      this.emit({
        type: 'session.compacting',
        data: {
          sessionId: data.sessionId,
          transcriptPath: data.transcriptPath,
          trigger: data.trigger || 'auto',
          cwd: data.cwd,
        },
      })
    } else if (type === 'session.ended') {
      this.emit({
        type: 'session.ended',
        data: {
          sessionId: data.sessionId,
          transcriptPath: data.transcriptPath,
          reason: data.reason,
          cwd: data.cwd,
        },
      })
    }

    // Queue background task to ingest transcript (fire and forget)
    this.processSessionTranscript(data.transcriptPath, data.sessionId, type).catch((err) =>
      log.error('Failed to process session transcript', { error: (err as Error).message })
    )

    return { status: 'queued' }
  }

  /**
   * Process session transcript in background
   * Reads the JSONL transcript file, extracts relevant content, and ingests it.
   */
  private async processSessionTranscript(
    transcriptPath: string,
    sessionId: string,
    eventType: string
  ): Promise<void> {
    const startTime = Date.now()

    try {
      // Read transcript JSONL file
      const fs = await import('fs/promises')
      const content = await fs.readFile(transcriptPath, 'utf-8')

      // Parse JSONL (each line is a message)
      const messages = content
        .split('\n')
        .filter((line) => line.trim())
        .map((line) => {
          try {
            return JSON.parse(line)
          } catch {
            return null
          }
        })
        .filter(Boolean)

      if (messages.length === 0) {
        log.debug('No messages in transcript', { sessionId })
        return
      }

      // Extract relevant content for ingestion
      // Claude Code transcripts use .type (not .role) and have different content structures:
      // - User messages: { type: 'user', content: string }
      // - Assistant messages: { type: 'assistant', message: { content: [{ type: 'text', text: '...' }] } }
      const relevantContent = messages
        .filter((m: any) => m.type === 'user' || m.type === 'assistant')
        .map((m: any) => {
          // User messages have content as string
          if (m.type === 'user' && typeof m.content === 'string') {
            return m.content
          }
          // Assistant messages have nested message.content array
          if (m.type === 'assistant' && m.message?.content) {
            const content = m.message.content
            if (Array.isArray(content)) {
              return content
                .filter((c: any) => c.type === 'text')
                .map((c: any) => c.text)
                .join('\n')
            }
            if (typeof content === 'string') return content
          }
          return ''
        })
        .filter(Boolean)
        .join('\n\n---\n\n')

      if (!relevantContent || relevantContent.length < 100) {
        log.debug('Insufficient content to ingest from session', { sessionId, length: relevantContent?.length || 0 })
        return
      }

      // Create temp file with session content
      const tempPath = `/tmp/atlas-session-${sessionId}.md`
      const sessionHeader = `# Claude Code Session ${sessionId}\n\nEvent: ${eventType}\nTimestamp: ${new Date().toISOString()}\n\n`
      await fs.writeFile(tempPath, sessionHeader + relevantContent, 'utf-8')

      // Ingest the session content
      const { ingest } = await import('../domain/ingest')
      const result = await ingest({
        paths: [tempPath],
        recursive: false,
        verbose: false,
        emit: (event) => this.emit(event),
      })

      // Clean up temp file
      await fs.unlink(tempPath).catch(() => {})

      const took = Date.now() - startTime

      // Emit completion event
      this.emit({
        type: 'session.ingested',
        data: {
          sessionId,
          chunksCreated: result.chunksStored,
          took,
        },
      })

      log.info('Session transcript ingested', { sessionId, eventType, chunks: result.chunksStored, took })
    } catch (error) {
      // Emit error event
      this.emit({
        type: 'session.error',
        data: {
          sessionId,
          error: (error as Error).message,
          phase: 'ingest',
        },
      })

      throw error
    }
  }

  /**
   * Handle atlas.execute_work - Execute multi-agent work graph
   */
  private async handleExecuteWork(
    params: ExecuteWorkParams,
    _clientId: string
  ): Promise<ExecuteWorkResult> {
    const { executeWork, buildWorkContext } = await import('../domain/agents/coordinator')

    log.info('Executing work graph', { project: params.project })

    // Build context with emit function so agents can broadcast events
    const context = buildWorkContext(
      [],
      params.project ?? 'default',
      params.variables ?? {},
      (event) => this.emit(event)
    )

    const result = await executeWork(params.work as any, context)

    return {
      agents: result.agents.map((a) => ({
        role: a.role,
        task: a.task,
        output: a.output,
        artifacts: a.artifacts,
        status: a.status,
        took: a.took,
      })),
      took: result.took,
      status: result.status,
      error: result.error,
    }
  }

  /**
   * Handle atlas.get_agent_context - Get RAG context for agent spawn
   */
  private async handleGetAgentContext(
    params: GetAgentContextParams,
    _clientId: string
  ): Promise<GetAgentContextResult> {
    const { search } = await import('../domain/search')

    log.debug('Getting agent context', {
      qntmKeys: params.qntmKeys,
      limit: params.limit,
    })

    const context: string[] = []

    for (const key of params.qntmKeys) {
      const results = await search({
        query: key,
        qntmKey: key,
        limit: params.limit ?? 5,
        consolidationLevel: params.consolidationLevel,
      })

      context.push(
        ...results.map((r) => `[${r.file_path}]\n${r.text}\n(score: ${r.score.toFixed(3)})`)
      )
    }

    return {
      context,
      total: context.length,
    }
  }
}
