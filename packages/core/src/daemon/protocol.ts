/**
 * JSON-RPC 2.0 protocol for Atlas daemon communication
 */

import type { AtlasEvent } from './events'

// ============================================
// JSON-RPC Base Types
// ============================================

export interface JsonRpcRequest {
  jsonrpc: '2.0'
  id: string | number
  method: string
  params?: Record<string, unknown>
}

export interface JsonRpcResponse {
  jsonrpc: '2.0'
  id: string | number
  result?: unknown
  error?: JsonRpcError
}

export interface JsonRpcError {
  code: number
  message: string
  data?: unknown
}

export interface JsonRpcNotification {
  jsonrpc: '2.0'
  method: 'event'
  params: AtlasEvent
}

// ============================================
// JSON-RPC Error Codes
// ============================================

export const JsonRpcErrorCode = {
  // Standard JSON-RPC errors
  ParseError: -32700,
  InvalidRequest: -32600,
  MethodNotFound: -32601,
  InvalidParams: -32602,
  InternalError: -32603,

  // Atlas-specific errors
  DependencyMissing: -32000,
  CollectionNotFound: -32001,
  BackendUnavailable: -32002,
  FileNotFound: -32003,
  IngestionFailed: -32004,
  SearchFailed: -32005,
} as const

// ============================================
// Method Schemas
// ============================================

/**
 * atlas.ingest - Ingest files into vector database
 */
export interface IngestParams {
  paths: string[]
  recursive?: boolean
  verbose?: boolean
}

export interface IngestResult {
  filesProcessed: number
  chunksStored: number
  errors: Array<{ file: string; error: string }>
}

/**
 * atlas.search - Semantic search
 */
export interface SearchParams {
  query: string
  limit?: number
  since?: string // ISO 8601
  qntmKey?: string
  rerank?: boolean
  sessionId?: string
  consolidationLevel?: 0 | 1 | 2 | 3
  expandQuery?: boolean
}

export interface SearchResult {
  text: string
  filePath: string
  chunkIndex: number
  score: number
  createdAt: string
  qntmKey: string
  rerankScore?: number
}

/**
 * atlas.consolidate - Consolidate similar chunks
 */
export interface ConsolidateParams {
  dryRun?: boolean
  threshold?: number
}

export interface ConsolidateResult {
  candidatesFound: number
  consolidated: number
  deleted: number
  rounds: number
  maxLevel: number
  levelStats: Record<number, number>
}

/**
 * atlas.subscribe - Subscribe to event types
 */
export interface SubscribeParams {
  events: string[] // Event type patterns (e.g., "ingest.*", "search.completed")
}

export interface SubscribeResult {
  subscribed: string[]
}

/**
 * atlas.unsubscribe - Unsubscribe from event types
 */
export interface UnsubscribeParams {
  events: string[]
}

export interface UnsubscribeResult {
  unsubscribed: string[]
}

/**
 * atlas.health - Check all dependencies
 */
export interface HealthParams {
  // No params
}

export interface HealthResult {
  qdrant: { available: boolean; url: string; error?: string }
  ollama: { available: boolean; url: string; error?: string }
  voyage: { available: boolean; hasKey: boolean; error?: string }
  overall: 'healthy' | 'degraded' | 'unhealthy'
}

/**
 * atlas.status - Get daemon status
 */
export interface StatusParams {
  // No params
}

export interface StatusResult {
  pid: number
  uptime: number // seconds
  socket: string
  clients: number
  version: string
}

/**
 * atlas.session_event - Forward session lifecycle events from Claude Code
 */
export interface SessionEventParams {
  type: 'session.compacting' | 'session.ended'
  data: {
    sessionId: string
    transcriptPath: string
    trigger?: 'manual' | 'auto' // For compacting
    reason?: string // For ended
    cwd?: string
  }
}

export interface SessionEventResult {
  status: 'queued' | 'skipped'
  reason?: string
}

/**
 * atlas.execute_work - Execute multi-agent work graph
 */
export interface ExecuteWorkParams {
  /** Work graph to execute */
  work: unknown // WorkNode type (will be validated at runtime)
  /** Project name for artifact paths */
  project?: string
  /** Initial context variables */
  variables?: Record<string, unknown>
}

export interface ExecuteWorkResult {
  /** Agent results in execution order */
  agents: Array<{
    role: string
    task: string
    output: string
    artifacts: string[]
    status: string
    took: number
  }>
  /** Total execution time */
  took: number
  /** Status */
  status: 'success' | 'error' | 'partial'
  /** Error if failed */
  error?: string
}

/**
 * atlas.get_agent_context - Get RAG context for spawning agent
 */
export interface GetAgentContextParams {
  /** QNTM keys to search for */
  qntmKeys: string[]
  /** Limit results per key */
  limit?: number
  /** Consolidation level filter */
  consolidationLevel?: 0 | 1 | 2 | 3
}

export interface GetAgentContextResult {
  /** Context chunks from RAG */
  context: string[]
  /** Total chunks returned */
  total: number
}

// ============================================
// Method Registry
// ============================================

export type AtlasMethod =
  | 'atlas.ingest'
  | 'atlas.search'
  | 'atlas.consolidate'
  | 'atlas.subscribe'
  | 'atlas.unsubscribe'
  | 'atlas.health'
  | 'atlas.status'
  | 'atlas.session_event'
  | 'atlas.execute_work'
  | 'atlas.get_agent_context'

export type MethodParams<M extends AtlasMethod> = M extends 'atlas.ingest'
  ? IngestParams
  : M extends 'atlas.search'
    ? SearchParams
    : M extends 'atlas.consolidate'
      ? ConsolidateParams
      : M extends 'atlas.subscribe'
        ? SubscribeParams
        : M extends 'atlas.unsubscribe'
          ? UnsubscribeParams
          : M extends 'atlas.health'
            ? HealthParams
            : M extends 'atlas.status'
              ? StatusParams
              : M extends 'atlas.session_event'
                ? SessionEventParams
                : M extends 'atlas.execute_work'
                  ? ExecuteWorkParams
                  : M extends 'atlas.get_agent_context'
                    ? GetAgentContextParams
                    : never

export type MethodResult<M extends AtlasMethod> = M extends 'atlas.ingest'
  ? IngestResult
  : M extends 'atlas.search'
    ? SearchResult[]
    : M extends 'atlas.consolidate'
      ? ConsolidateResult
      : M extends 'atlas.subscribe'
        ? SubscribeResult
        : M extends 'atlas.unsubscribe'
          ? UnsubscribeResult
          : M extends 'atlas.health'
            ? HealthResult
            : M extends 'atlas.status'
              ? StatusResult
              : M extends 'atlas.session_event'
                ? SessionEventResult
                : M extends 'atlas.execute_work'
                  ? ExecuteWorkResult
                  : M extends 'atlas.get_agent_context'
                    ? GetAgentContextResult
                    : never

// ============================================
// Utilities
// ============================================

/**
 * Create JSON-RPC request
 */
export function createRequest<M extends AtlasMethod>(
  id: string | number,
  method: M,
  params?: MethodParams<M>
): JsonRpcRequest {
  return {
    jsonrpc: '2.0',
    id,
    method,
    params: params as Record<string, unknown>,
  }
}

/**
 * Create JSON-RPC success response
 */
export function createResponse<M extends AtlasMethod>(
  id: string | number,
  result: MethodResult<M>
): JsonRpcResponse {
  return {
    jsonrpc: '2.0',
    id,
    result,
  }
}

/**
 * Create JSON-RPC error response
 */
export function createErrorResponse(
  id: string | number,
  code: number,
  message: string,
  data?: unknown
): JsonRpcResponse {
  return {
    jsonrpc: '2.0',
    id,
    error: {
      code,
      message,
      data,
    },
  }
}

/**
 * Create JSON-RPC notification
 */
export function createNotification(event: AtlasEvent): JsonRpcNotification {
  return {
    jsonrpc: '2.0',
    method: 'event',
    params: event,
  }
}

/**
 * Parse JSON-RPC message from string
 */
export function parseMessage(
  message: string
): JsonRpcRequest | JsonRpcResponse | JsonRpcNotification {
  try {
    const parsed = JSON.parse(message)

    // Validate JSON-RPC 2.0 format
    if (parsed.jsonrpc !== '2.0') {
      throw new Error('Invalid JSON-RPC version')
    }

    // Distinguish between request, response, and notification
    if ('method' in parsed) {
      if ('id' in parsed) {
        // Request
        return parsed as JsonRpcRequest
      } else {
        // Notification
        return parsed as JsonRpcNotification
      }
    } else if ('id' in parsed) {
      // Response
      return parsed as JsonRpcResponse
    } else {
      throw new Error('Invalid JSON-RPC message format')
    }
  } catch (error) {
    throw new Error(`Failed to parse JSON-RPC message: ${(error as Error).message}`)
  }
}

/**
 * Serialize JSON-RPC message to string
 */
export function serializeMessage(
  message: JsonRpcRequest | JsonRpcResponse | JsonRpcNotification
): string {
  return JSON.stringify(message)
}
