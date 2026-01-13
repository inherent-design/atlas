/**
 * JSON-RPC 2.0 protocol for Atlas daemon communication
 */

import { z } from 'zod'
import type { AtlasEvent } from './events.js'
import type {
  IngestParams,
  IngestResult as DomainIngestResult,
  SearchParams,
  SearchResult as DomainSearchResult,
  ConsolidateParams,
  ConsolidateResult as DomainConsolidateResult,
  QNTMGenerateParams,
  QNTMGenerateResult as DomainQNTMGenerateResult,
  TimelineParams,
} from '../shared/types.js'

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
 *
 * Uses canonical IngestParams (already camelCase, no transformation needed)
 * Re-exported from ../shared/types via import above
 */
export type { IngestParams }

/**
 * IngestResultDTO: camelCase RPC layer
 * Transforms domain IngestResult (snake_case) to camelCase for JSON-RPC
 */
export interface IngestResultDTO {
  filesProcessed: number
  chunksStored: number
  errors: Array<{ file: string; error: string }>
  durationMs?: number
  peakMemoryBytes?: number
  skippedFiles?: number
}

// Legacy alias (backwards compatibility)
export type IngestResult = IngestResultDTO

/**
 * atlas.search - Semantic search
 *
 * Uses canonical SearchParams (already camelCase, no transformation needed)
 * Re-exported from ../shared/types via import above
 */
export type { SearchParams }

/**
 * Search result DTO for JSON-RPC protocol (camelCase for JSON convention)
 * Note: Different from domain SearchResult which uses snake_case for DB
 */
export interface SearchResultDTO {
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
 *
 * Uses canonical ConsolidateParams (already camelCase, no transformation needed)
 * Re-exported from ../shared/types via import above
 */
export type { ConsolidateParams }

/**
 * ConsolidateResultDTO: camelCase RPC layer
 * Aligns with canonical ConsolidateResult fields (no fake data)
 */
export interface ConsolidateResultDTO {
  consolidationsPerformed: number
  chunksAbsorbed: number
  candidatesEvaluated: number
  typeBreakdown?: {
    duplicate_work: number
    sequential_iteration: number
    contextual_convergence: number
  }
  durationMs?: number
  preview?: Array<{
    primary_id: string
    secondary_id: string
    similarity: number
    consolidation_type: 'duplicate_work' | 'sequential_iteration' | 'contextual_convergence'
    reasoning: string
  }>
}

// Legacy alias (backwards compatibility)
export type ConsolidateResult = ConsolidateResultDTO

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

/**
 * Zod schema for WorkNode runtime validation.
 * Validates work graph structure before execution.
 */
const BaseWorkNodeSchema = z.object({
  type: z.enum(['agent', 'sequence', 'parallel', 'conditional', 'loop']),
  id: z.string().optional(),
})

const AgentConfigSchema = z.object({
  role: z.enum(['observer', 'connector', 'explainer', 'challenger', 'integrator']),
  task: z.string(),
  project: z.string().optional(),
  context: z.array(z.string()).optional(),
  qntmKeys: z.array(z.string()).optional(),
  consolidationLevel: z.union([z.literal(0), z.literal(1), z.literal(2), z.literal(3)]).optional(),
  maxTurns: z.number().optional(),
  temperature: z.number().optional(),
  maxTokens: z.number().optional(),
  writeArtifacts: z.boolean().optional(),
})

// Forward declare WorkNode for recursive types
type WorkNodeType = z.infer<typeof BaseWorkNodeSchema> & {
  config?: z.infer<typeof AgentConfigSchema>
  children?: WorkNodeType[]
  child?: WorkNodeType
  then?: WorkNodeType
  else?: WorkNodeType
  condition?: string
  passContext?: boolean
  maxConcurrency?: number
  loopType?: 'count' | 'condition' | 'infinite' | 'adaptive'
  iterations?: number
  continueWhile?: string
  loopContext?: Record<string, unknown>
  conditionContext?: Record<string, unknown>
  adaptiveConfig?: {
    evaluatorRole?: string
    maxIterations?: number
  }
}

// Use simpler approach: validate discriminated union with unknown for recursive parts
const WorkNodeSchema: z.ZodSchema = z.union([
  // AgentNode
  BaseWorkNodeSchema.extend({
    type: z.literal('agent'),
    config: AgentConfigSchema,
  }),
  // SequenceNode
  BaseWorkNodeSchema.extend({
    type: z.literal('sequence'),
    children: z.array(z.any()), // Validated recursively at runtime
    passContext: z.boolean().optional(),
  }),
  // ParallelNode
  BaseWorkNodeSchema.extend({
    type: z.literal('parallel'),
    children: z.array(z.any()), // Validated recursively at runtime
    maxConcurrency: z.number().optional(),
  }),
  // ConditionalNode
  BaseWorkNodeSchema.extend({
    type: z.literal('conditional'),
    condition: z.string(),
    then: z.any(), // Validated recursively at runtime
    else: z.any().optional(), // Validated recursively at runtime
    conditionContext: z.record(z.string(), z.unknown()).optional(),
  }),
  // LoopNode
  BaseWorkNodeSchema.extend({
    type: z.literal('loop'),
    loopType: z.enum(['count', 'condition', 'infinite', 'adaptive']),
    child: z.any(), // Validated recursively at runtime
    iterations: z.number().optional(),
    continueWhile: z.string().optional(),
    loopContext: z.record(z.string(), z.unknown()).optional(),
    adaptiveConfig: z
      .object({
        evaluatorRole: z.string().optional(),
        maxIterations: z.number().optional(),
      })
      .optional(),
  }),
])

/**
 * Recursively validate WorkNode structure.
 * Validates top-level first, then validates nested nodes.
 */
function validateWorkNodeRecursive(node: unknown, path: string = 'work'): void {
  // Parse top-level structure
  const parsed = WorkNodeSchema.parse(node) as any

  // Recursively validate children based on type
  switch (parsed.type) {
    case 'sequence':
    case 'parallel':
      if (parsed.children) {
        parsed.children.forEach((child: unknown, i: number) => {
          validateWorkNodeRecursive(child, `${path}.children[${i}]`)
        })
      }
      break
    case 'conditional':
      if (parsed.then) {
        validateWorkNodeRecursive(parsed.then, `${path}.then`)
      }
      if (parsed.else) {
        validateWorkNodeRecursive(parsed.else, `${path}.else`)
      }
      break
    case 'loop':
      if (parsed.child) {
        validateWorkNodeRecursive(parsed.child, `${path}.child`)
      }
      break
    // 'agent' has no nested nodes
  }
}

/**
 * Validate ExecuteWorkParams at runtime.
 * Throws if work graph is malformed.
 */
export function validateExecuteWorkParams(params: ExecuteWorkParams): void {
  try {
    validateWorkNodeRecursive(params.work)
  } catch (error) {
    if (error instanceof z.ZodError) {
      const issues = error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join(', ')
      throw new Error(`Invalid work graph: ${issues}`)
    }
    throw error
  }
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

/**
 * atlas.ingest.start - Start async ingestion task
 */
export interface IngestStartParams {
  paths: string[]
  recursive?: boolean
  watch?: boolean // Auto-reingest on file changes
}

export interface IngestStartResult {
  taskId: string
  message: string
  watching: boolean
}

/**
 * atlas.ingest.status - Get ingestion task status
 */
export interface IngestStatusParams {
  taskId?: string // If omitted, return all tasks
}

export interface IngestionTask {
  id: string
  paths: string[]
  status: 'running' | 'completed' | 'failed' | 'stopped'
  watching: boolean
  filesProcessed: number
  chunksStored: number
  errors: Array<{ file: string; error: string }>
  startedAt: string
  completedAt?: string
}

export interface IngestStatusResult {
  tasks: IngestionTask[]
}

/**
 * atlas.ingest.stop - Stop ingestion task
 */
export interface IngestStopParams {
  taskId: string
}

export interface IngestStopResult {
  stopped: boolean
  final: IngestionTask
}

/**
 * atlas.consolidate.start - Start async consolidation
 */
export interface ConsolidateStartParams {
  threshold?: number
  dryRun?: boolean
}

export interface ConsolidateStartResult {
  taskId: string
  locked: boolean // false if already running
  message: string
}

/**
 * atlas.consolidate.status - Get consolidation status
 */
export interface ConsolidateStatusParams {
  // No params
}

export interface ConsolidateStatusResult {
  running: boolean
  taskId?: string
  progress?: {
    candidatesFound: number
    consolidated: number
    deleted: number
    currentLevel: number
  }
  startedAt?: string
}

/**
 * atlas.consolidate.stop - Stop consolidation
 */
export interface ConsolidateStopParams {
  taskId: string
}

export interface ConsolidateStopResult {
  stopped: boolean
  final?: ConsolidateResult
}

/**
 * atlas.qntm.generate - Generate QNTM keys for text
 *
 * Uses canonical QNTMGenerateParams (already camelCase, no transformation needed)
 * Re-exported from ../shared/types via import above
 */
export type { QNTMGenerateParams }

/**
 * QntmGenerateResultDTO: camelCase RPC layer
 * Matches canonical QNTMGenerateResult (already camelCase)
 */
export interface QntmGenerateResultDTO {
  keys: string[]
  reasoning?: string
}

// Legacy alias (backwards compatibility)
export type QntmGenerateResult = QntmGenerateResultDTO

/**
 * atlas.timeline - Query timeline with filters
 *
 * Uses canonical TimelineParams (already camelCase, no transformation needed)
 * Re-exported from ../shared/types via import above
 */
export type { TimelineParams }

export interface TimelineResult {
  chunks: Array<{
    id: string
    text: string
    filePath: string
    createdAt: string
    qntmKeys: string[]
  }>
  total: number
}

// ============================================
// Method Registry
// ============================================

export type AtlasMethod =
  | 'atlas.ingest'
  | 'atlas.ingest.start'
  | 'atlas.ingest.status'
  | 'atlas.ingest.stop'
  | 'atlas.search'
  | 'atlas.consolidate'
  | 'atlas.consolidate.start'
  | 'atlas.consolidate.status'
  | 'atlas.consolidate.stop'
  | 'atlas.qntm.generate'
  | 'atlas.timeline'
  | 'atlas.subscribe'
  | 'atlas.unsubscribe'
  | 'atlas.health'
  | 'atlas.status'
  | 'atlas.session_event'
  | 'atlas.execute_work'
  | 'atlas.get_agent_context'

export type MethodParams<M extends AtlasMethod> = M extends 'atlas.ingest'
  ? IngestParams
  : M extends 'atlas.ingest.start'
    ? IngestStartParams
    : M extends 'atlas.ingest.status'
      ? IngestStatusParams
      : M extends 'atlas.ingest.stop'
        ? IngestStopParams
        : M extends 'atlas.search'
          ? SearchParams
          : M extends 'atlas.consolidate'
            ? ConsolidateParams
            : M extends 'atlas.consolidate.start'
              ? ConsolidateStartParams
              : M extends 'atlas.consolidate.status'
                ? ConsolidateStatusParams
                : M extends 'atlas.consolidate.stop'
                  ? ConsolidateStopParams
                  : M extends 'atlas.qntm.generate'
                    ? QNTMGenerateParams
                    : M extends 'atlas.timeline'
                      ? TimelineParams
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
  : M extends 'atlas.ingest.start'
    ? IngestStartResult
    : M extends 'atlas.ingest.status'
      ? IngestStatusResult
      : M extends 'atlas.ingest.stop'
        ? IngestStopResult
        : M extends 'atlas.search'
          ? SearchResultDTO[]
          : M extends 'atlas.consolidate'
            ? ConsolidateResult
            : M extends 'atlas.consolidate.start'
              ? ConsolidateStartResult
              : M extends 'atlas.consolidate.status'
                ? ConsolidateStatusResult
                : M extends 'atlas.consolidate.stop'
                  ? ConsolidateStopResult
                  : M extends 'atlas.qntm.generate'
                    ? QntmGenerateResult
                    : M extends 'atlas.timeline'
                      ? TimelineResult
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
