/**
 * Event router - Thin RPC layer delegating to ApplicationService
 *
 * Routes JSON-RPC requests to ApplicationService methods and manages:
 * - Request validation and error handling
 * - Event emission for progress updates
 * - Client subscription management
 * - Background task coordination (async ingest/consolidate)
 */

import type { JsonRpcRequest, JsonRpcResponse, AtlasMethod } from './protocol.js'
import {
  createResponse,
  createErrorResponse,
  JsonRpcErrorCode,
  validateExecuteWorkParams,
  type IngestParams,
  type IngestResult,
  type IngestStartParams,
  type IngestStartResult,
  type IngestStatusParams,
  type IngestStatusResult,
  type IngestStopParams,
  type IngestStopResult,
  type SearchParams,
  type SearchResultDTO,
  type ConsolidateParams,
  type ConsolidateResult,
  type ConsolidateStartParams,
  type ConsolidateStartResult,
  type ConsolidateStatusParams,
  type ConsolidateStatusResult,
  type ConsolidateStopParams,
  type ConsolidateStopResult,
  type QNTMGenerateParams,
  type QntmGenerateResult,
  type TimelineParams,
  type TimelineResult,
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
} from './protocol.js'
import { createLogger } from '../shared/logger.js'
import type { AtlasDaemonServer } from './server.js'
import type { AtlasEvent } from './events.js'
import { daemonState } from './state.js'
import { v4 as uuid } from 'uuid'
import { DefaultApplicationService } from '../services/application/index.js'
import type { AtlasConfig } from '../shared/config.schema.js'
import { getConfig } from '../shared/config.loader.js'

const log = createLogger('daemon:router')

/**
 * Method handler function
 */
type MethodHandler<P = unknown, R = unknown> = (params: P, clientId: string) => Promise<R>

/**
 * Event router - Delegates to ApplicationService
 */
export class EventRouter {
  private handlers: Map<AtlasMethod, MethodHandler<any, any>> = new Map()
  private server: AtlasDaemonServer | null = null
  private eventListeners: Set<(event: AtlasEvent) => void> = new Set()
  private startTime: number
  private app: DefaultApplicationService
  private config: AtlasConfig

  constructor(config?: AtlasConfig) {
    this.startTime = Date.now()
    this.config = config || getConfig()
    this.app = new DefaultApplicationService(this.config)
    this.registerDefaultHandlers()
    log.info('EventRouter created')
  }

  /**
   * Initialize ApplicationService
   */
  async initialize(): Promise<void> {
    await this.app.initialize()
    log.info('EventRouter initialized')
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
    this.registerHandler('atlas.ingest.start', this.handleIngestStart.bind(this))
    this.registerHandler('atlas.ingest.status', this.handleIngestStatus.bind(this))
    this.registerHandler('atlas.ingest.stop', this.handleIngestStop.bind(this))
    this.registerHandler('atlas.search', this.handleSearch.bind(this))
    this.registerHandler('atlas.consolidate', this.handleConsolidate.bind(this))
    this.registerHandler('atlas.consolidate.start', this.handleConsolidateStart.bind(this))
    this.registerHandler('atlas.consolidate.status', this.handleConsolidateStatus.bind(this))
    this.registerHandler('atlas.consolidate.stop', this.handleConsolidateStop.bind(this))
    this.registerHandler('atlas.qntm.generate', this.handleQntmGenerate.bind(this))
    this.registerHandler('atlas.timeline', this.handleTimeline.bind(this))
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
   * Handle atlas.ingest - Delegate to ApplicationService
   * Forward ALL IngestParams fields (no information loss)
   */
  private async handleIngest(params: IngestParams, _clientId: string): Promise<IngestResult> {
    const result = await this.app.ingest({
      ...params,
      emit: (event) => this.emit(event),
    })

    return {
      filesProcessed: result.filesProcessed,
      chunksStored: result.chunksStored,
      errors: result.errors,
      durationMs: result.durationMs,
      peakMemoryBytes: result.peakMemoryBytes,
      skippedFiles: result.skippedFiles,
    }
  }

  /**
   * Handle atlas.search - Delegate to ApplicationService
   * Forward ALL SearchParams fields (no information loss)
   */
  private async handleSearch(params: SearchParams, _clientId: string): Promise<SearchResultDTO[]> {
    const results = await this.app.search({
      ...params,
      emit: (event) => this.emit(event),
    })

    // Map to DTO format (snake_case → camelCase)
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
   * Handle atlas.consolidate - Delegate to ApplicationService
   * Forward ALL ConsolidateParams fields (no information loss)
   * Return ConsolidateResult with NO fake data (aligned with canonical schema)
   */
  private async handleConsolidate(
    params: ConsolidateParams,
    _clientId: string
  ): Promise<ConsolidateResult> {
    const domainResult = await this.app.consolidate({
      ...params,
      emit: (event) => this.emit(event),
    })

    // Map ApplicationService result to daemon protocol format (aligned with canonical)
    return {
      consolidationsPerformed: domainResult.consolidationsPerformed,
      chunksAbsorbed: domainResult.chunksAbsorbed,
      candidatesEvaluated: domainResult.candidatesEvaluated,
      typeBreakdown: domainResult.typeBreakdown,
      durationMs: domainResult.durationMs,
      preview: domainResult.preview,
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
   * Handle atlas.health - Delegate to ApplicationService
   */
  private async handleHealth(_params: HealthParams, _clientId: string): Promise<HealthResult> {
    const healthStatus = await this.app.health()

    // Map HealthStatus to daemon protocol HealthResult (simplified format)
    const vectorService = healthStatus.services.vector
    const qdrant = {
      available: vectorService.status === 'healthy',
      url: this.config.storage?.qdrant?.url || 'http://localhost:6333',
      error: vectorService.error || '',
    }

    // Check Ollama backend health
    const ollamaBackend = healthStatus.services.llm.backends.find((b) => b.name.includes('ollama'))
    const ollama = {
      available: ollamaBackend?.status === 'healthy',
      url: 'http://localhost:11434',
      error: ollamaBackend?.error || '',
    }

    // Check Voyage backend health
    const voyageBackend = healthStatus.services.embedding.backends.find((b) =>
      b.name.includes('voyage')
    )
    const voyage = {
      available: voyageBackend?.status === 'healthy',
      hasKey: !!process.env.VOYAGE_API_KEY,
      error: voyageBackend?.error,
    }

    return { qdrant, ollama, voyage, overall: healthStatus.overall }
  }

  /**
   * Handle atlas.status - Mix ApplicationService + daemon-specific info
   */
  private async handleStatus(_params: StatusParams, _clientId: string): Promise<StatusResult> {
    const serverStatus = this.server?.getStatus() || { clients: 0, uptime: 0, socket: '' }

    return {
      pid: process.pid,
      uptime: Math.floor((Date.now() - this.startTime) / 1000),
      socket: serverStatus.socket,
      clients: serverStatus.clients,
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
        log.debug('Insufficient content to ingest from session', {
          sessionId,
          length: relevantContent?.length || 0,
        })
        return
      }

      // Create temp file with session content
      const tempPath = `/tmp/atlas-session-${sessionId}.md`
      const sessionHeader = `# Claude Code Session ${sessionId}\n\nEvent: ${eventType}\nTimestamp: ${new Date().toISOString()}\n\n`
      await fs.writeFile(tempPath, sessionHeader + relevantContent, 'utf-8')

      // Ingest the session content via ApplicationService
      const result = await this.app.ingest({
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

      log.info('Session transcript ingested', {
        sessionId,
        eventType,
        chunks: result.chunksStored,
        took,
      })
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
    const { executeWork, buildWorkContext } = await import('../domain/agents')

    log.info('Executing work graph', { project: params.project })

    // Validate work graph structure before execution
    validateExecuteWorkParams(params)

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
   * Delegate to ApplicationService's search
   */
  private async handleGetAgentContext(
    params: GetAgentContextParams,
    _clientId: string
  ): Promise<GetAgentContextResult> {
    log.debug('Getting agent context', {
      qntmKeys: params.qntmKeys,
      limit: params.limit,
    })

    const context: string[] = []

    for (const key of params.qntmKeys) {
      const results = await this.app.search({
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

  // ============================================
  // New RPC Method Handlers (Phase 1)
  // ============================================

  /**
   * Handle atlas.ingest.start - Start async ingestion task
   */
  private async handleIngestStart(
    params: IngestStartParams,
    _clientId: string
  ): Promise<IngestStartResult> {
    const { paths, recursive = false, watch = false } = params

    // Create task
    const taskId = daemonState.createIngestionTask(paths, watch)

    // Start ingestion in background
    this.runIngestionTask(taskId, paths, recursive, watch).catch((error) => {
      daemonState.updateIngestionTask(taskId, {
        status: 'failed',
        completedAt: new Date().toISOString(),
      })
      log.error('Ingestion task failed', { taskId, error })
    })

    return {
      taskId,
      message: `Ingestion started for ${paths.length} path(s)`,
      watching: watch,
    }
  }

  /**
   * Background ingestion runner - Delegate to ApplicationService
   */
  private async runIngestionTask(
    taskId: string,
    paths: string[],
    recursive: boolean,
    watch: boolean
  ): Promise<void> {
    const result = await this.app.ingest({
      paths,
      recursive,
      emit: (event) => {
        // Update task progress from events
        if (event.type === 'ingest.file.complete') {
          const task = daemonState.getIngestionTask(taskId)
          if (task) {
            daemonState.updateIngestionTask(taskId, {
              filesProcessed: task.filesProcessed + 1,
              chunksStored: task.chunksStored + (event.data.chunks || 0),
            })
          }
        }
        this.emit(event)
      },
    })

    daemonState.updateIngestionTask(taskId, {
      status: 'completed',
      filesProcessed: result.filesProcessed,
      chunksStored: result.chunksStored,
      errors: result.errors,
      completedAt: new Date().toISOString(),
    })

    // If watch=true, register with auto-watch
    if (watch) {
      for (const path of paths) {
        daemonState.registerAutoWatch(path, taskId)
      }
      // TODO: Integrate with existing file watcher
    }
  }

  /**
   * Handle atlas.ingest.status - Get ingestion task status
   */
  private async handleIngestStatus(
    params: IngestStatusParams,
    _clientId: string
  ): Promise<IngestStatusResult> {
    const { taskId } = params

    if (taskId) {
      const task = daemonState.getIngestionTask(taskId)
      return { tasks: task ? [task] : [] }
    }

    return { tasks: daemonState.getAllIngestionTasks() }
  }

  /**
   * Handle atlas.ingest.stop - Stop ingestion task
   */
  private async handleIngestStop(
    params: IngestStopParams,
    _clientId: string
  ): Promise<IngestStopResult> {
    const { taskId } = params
    const task = daemonState.getIngestionTask(taskId)

    if (!task) {
      throw new Error(`Task ${taskId} not found`)
    }

    // TODO: Implement task cancellation (requires ingest to support abort signal)
    daemonState.updateIngestionTask(taskId, {
      status: 'stopped',
      completedAt: new Date().toISOString(),
    })

    return { stopped: true, final: task }
  }

  /**
   * Handle atlas.consolidate.start - Start async consolidation
   */
  private async handleConsolidateStart(
    params: ConsolidateStartParams,
    _clientId: string
  ): Promise<ConsolidateStartResult> {
    const { threshold, dryRun = false } = params
    const taskId = uuid()

    // Try to acquire lock
    const acquired = daemonState.acquireConsolidationLock(taskId)

    if (!acquired) {
      const lock = daemonState.getConsolidationLock()
      return {
        taskId: lock.taskId!,
        locked: false,
        message: 'Consolidation already running',
      }
    }

    // Start consolidation in background
    this.runConsolidationTask(taskId, threshold, dryRun).catch((error) => {
      daemonState.releaseConsolidationLock()
      log.error('Consolidation task failed', { taskId, error })
    })

    return {
      taskId,
      locked: true,
      message: 'Consolidation started',
    }
  }

  /**
   * Background consolidation runner - Delegate to ApplicationService
   */
  private async runConsolidationTask(
    taskId: string,
    threshold?: number,
    dryRun?: boolean
  ): Promise<void> {
    try {
      await this.app.consolidate({
        threshold,
        dryRun,
        emit: (event) => {
          // TODO: Track progress events in state
          this.emit(event)
        },
      })
    } finally {
      daemonState.releaseConsolidationLock()
    }
  }

  /**
   * Handle atlas.consolidate.status - Get consolidation status
   */
  private async handleConsolidateStatus(
    _params: ConsolidateStatusParams,
    _clientId: string
  ): Promise<ConsolidateStatusResult> {
    const lock = daemonState.getConsolidationLock()

    return {
      running: lock.locked,
      taskId: lock.taskId,
      startedAt: lock.startedAt?.toISOString(),
      // TODO: Add progress tracking
    }
  }

  /**
   * Handle atlas.consolidate.stop - Stop consolidation
   */
  private async handleConsolidateStop(
    params: ConsolidateStopParams,
    _clientId: string
  ): Promise<ConsolidateStopResult> {
    const { taskId } = params
    const lock = daemonState.getConsolidationLock()

    if (!lock.locked || lock.taskId !== taskId) {
      throw new Error(`Task ${taskId} not running`)
    }

    // TODO: Implement graceful stop (requires consolidate to support abort signal)
    daemonState.releaseConsolidationLock()

    return { stopped: true }
  }

  /**
   * Handle atlas.qntm.generate - Delegate to ApplicationService
   * Forward ALL QntmGenerateParams fields (no information loss)
   */
  private async handleQntmGenerate(
    params: QNTMGenerateParams,
    _clientId: string
  ): Promise<QntmGenerateResult> {
    const result = await this.app.generateQNTM({
      text: params.text,
      existingKeys: params.existingKeys ?? [],
      level: params.level ?? 'concrete',
      context: params.context ?? {
        fileName: '<manual>',
      },
    })

    return {
      keys: result.keys,
      reasoning: result.reasoning,
    }
  }

  /**
   * Handle atlas.timeline - Delegate to ApplicationService
   * Forward ALL TimelineParams fields (no information loss)
   */
  private async handleTimeline(params: TimelineParams, _clientId: string): Promise<TimelineResult> {
    const results = await this.app.timeline({
      since: params.since,
      until: params.until,
      limit: params.limit ?? 50,
      timelineId: params.timelineId,
      includeCausalLinks: params.includeCausalLinks ?? false,
      granularity: params.granularity ?? 'day',
    })

    // Map to timeline result format
    const chunks = results.map((r) => ({
      id: '', // TODO: Add chunk ID to SearchResult
      text: r.text,
      filePath: r.file_path,
      createdAt: r.created_at,
      qntmKeys: [r.qntm_key],
    }))

    // Sort by created_at descending (most recent first)
    chunks.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())

    return {
      chunks,
      total: chunks.length,
    }
  }
}
