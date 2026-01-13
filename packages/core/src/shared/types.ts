/**
 * Shared TypeScript types for Atlas
 *
 * Schema Version: 3.0 (2026-01-02)
 * - Zod schema validation added for all types
 * - Export both Schema (runtime validation) and Type (static typing)
 *
 * Breaking changes from v2:
 * - Types now derived from Zod schemas via z.infer<>
 *
 * Breaking changes from v1:
 * - occurrences: number -> string[] (timestamps array)
 * - consolidated: boolean -> removed (use consolidation_level instead)
 * - consolidated_from: string[] -> removed (absorbed into parents)
 *
 * NAMING CONVENTIONS:
 * - API types (SearchOptions, IngestOptions): camelCase fields (TypeScript convention)
 * - Storage types (ChunkPayload): snake_case fields (matches PostgreSQL/Qdrant storage layer)
 * - Protocol types (daemon/protocol): camelCase (JSON-RPC convention)
 *
 * This is intentional to match respective layer conventions.
 */

import { z } from 'zod'

// ============================================
// Consolidation Enums
// ============================================

/**
 * Type of consolidation that occurred
 */
export const ConsolidationTypeSchema = z.enum([
  'duplicate_work',
  'sequential_iteration',
  'contextual_convergence',
])
export type ConsolidationType = z.infer<typeof ConsolidationTypeSchema>

/**
 * Direction of consolidation relationship
 */
export const ConsolidationDirectionSchema = z.enum(['forward', 'backward', 'convergent', 'unknown'])
export type ConsolidationDirection = z.infer<typeof ConsolidationDirectionSchema>

/**
 * Consolidation level hierarchy (vertical abstraction)
 * 0 = Raw chunk (fresh ingestion, no consolidation)
 * 1 = Deduplicated (merged with near-duplicates)
 * 2 = Topic summary (aggregated multiple level-1 chunks)
 * 3 = Domain knowledge (abstract patterns across topics)
 * 4 = Meta-knowledge (cross-domain synthesis)
 */
export const ConsolidationLevelSchema = z.union([
  z.literal(0),
  z.literal(1),
  z.literal(2),
  z.literal(3),
  z.literal(4),
])
export type ConsolidationLevel = z.infer<typeof ConsolidationLevelSchema>

// ============================================
// Causal Links
// ============================================

/**
 * Relationship types between chunks
 */
export const CausalRelationSchema = z.enum([
  'supersedes',
  'references',
  'derived_from',
  'contradicts',
  'extends',
])
export type CausalRelation = z.infer<typeof CausalRelationSchema>

/**
 * Inference source for causal relationships
 */
export const InferredBySchema = z.enum(['consolidator', 'explainer', 'user', 'heuristic'])
export type InferredBy = z.infer<typeof InferredBySchema>

/**
 * Causal relationship between chunks (timeline building)
 */
export const CausalLinkSchema = z.object({
  /** Point ID of related chunk */
  target_id: z.string().min(1),
  /** Relationship type */
  relation: CausalRelationSchema,
  /** Confidence score (0.0-1.0) */
  confidence: z.number().min(0).max(1),
  /** How this relationship was determined */
  inferred_by: InferredBySchema,
})
export type CausalLink = z.infer<typeof CausalLinkSchema>

// ============================================
// Search Result (moved to Unified types below)
// ============================================

/**
 * Single search result
 */
export const SearchResultSchema = z.object({
  /** Chunk text content */
  text: z.string(),
  /** File path relative to root */
  file_path: z.string(),
  /** Index of chunk within file */
  chunk_index: z.number().int().min(0),
  /** Similarity score (0.0-1.0) */
  score: z.number().min(0).max(1),
  /** ISO 8601 creation timestamp */
  created_at: z.string().datetime({ offset: true }),
  /** Primary QNTM semantic key */
  qntm_key: z.string(),
  /** Cross-encoder relevance score (if reranking enabled) */
  rerank_score: z.number().min(0).max(1).optional(),
})
export type SearchResult = z.infer<typeof SearchResultSchema>

// ============================================
// Importance Levels
// ============================================

/**
 * Importance classification for chunks
 */
export const ImportanceSchema = z.enum(['normal', 'high', 'low'])
export type Importance = z.infer<typeof ImportanceSchema>

// ============================================
// Content Types
// ============================================

/**
 * Content type classification
 */
export const ContentTypeSchema = z.enum(['text', 'code', 'media'])
export type ContentType = z.infer<typeof ContentTypeSchema>

/**
 * Named vectors that can exist for a point
 */
export const VectorNameSchema = z.enum(['text', 'code', 'media'])
export type VectorName = z.infer<typeof VectorNameSchema>

// ============================================
// Chunk Payload
// ============================================

/**
 * Full chunk payload stored in Qdrant
 * Comprehensive schema with all metadata fields
 */
export const ChunkPayloadSchema = z
  .object({
    // === Core identity ===
    /** Original text content */
    original_text: z.string().min(1),
    /** File path relative to root directory */
    file_path: z.string().min(1),
    /** File name with extension */
    file_name: z.string().min(1),
    /** File extension (e.g., '.ts', '.md') */
    file_type: z.string(),
    /** Index of this chunk within the file (0-based) */
    chunk_index: z.number().int().min(0),
    /** Total number of chunks from this file */
    total_chunks: z.number().int().min(1),
    /** Character count of original_text */
    char_count: z.number().int().min(0),
    /** Multiple semantic addresses (tag-based QNTM keys) */
    qntm_keys: z.array(z.string()).min(1),
    /** ISO 8601 creation timestamp */
    created_at: z.string().datetime({ offset: true }),
    /** Importance classification */
    importance: ImportanceSchema,

    // === Embedding metadata (Phase 2: Named Vectors) ===
    /** Embedding model used (e.g., 'voyage-3-large', 'voyage-code-3') */
    embedding_model: z.string().optional(),
    /** Embedding strategy (snippet, contextualized, multimodal) */
    embedding_strategy: z.enum(['snippet', 'contextualized', 'multimodal']).optional(),
    /** Content classification */
    content_type: ContentTypeSchema.optional(),
    /** Which named vectors exist for this point */
    vectors_present: z.array(VectorNameSchema).optional(),

    // === Vertical consolidation (abstraction levels) ===
    /** Consolidation level (0=raw, 1=deduped, 2=topic, 3=domain, 4=meta) */
    consolidation_level: ConsolidationLevelSchema,
    /** Abstraction score (0.0-1.0, higher = more abstract) */
    abstraction_score: z.number().min(0).max(1).optional(),
    /** Type of consolidation performed */
    consolidation_type: ConsolidationTypeSchema.optional(),
    /** Direction of consolidation relationship */
    consolidation_direction: ConsolidationDirectionSchema.optional(),
    /** LLM-provided explanation of consolidation */
    consolidation_reasoning: z.string().optional(),

    // === Memory Integration ===
    /** Memory type classification */
    memory_type: z.enum(['file', 'conversation', 'compacted', 'consolidated']).optional(),
    /** Session ID for working memory compactions */
    session_id: z.string().optional(),
    /** Entity that sourced this chunk (user_id, agent_id, etc.) */
    source_entity: z.string().optional(),

    // === Document Split Metadata (for large documents exceeding context window) ===
    /** Index of sub-document this chunk belongs to (0-based) */
    split_index: z.number().int().min(0).optional(),
    /** Total number of sub-documents the original was split into */
    split_total: z.number().int().min(1).optional(),
    /** Original chunk index before splitting (for retrieval context) */
    chunk_index_global: z.number().int().min(0).optional(),

    // === Provenance DAG ===
    /** Point IDs this was consolidated from (absorbs old consolidated_from) */
    parents: z.array(z.string()).optional(),
    /** ISO 8601 timestamps of all instances (BREAKING: was number in v1) */
    occurrences: z.array(z.string().datetime({ offset: true })).optional(),

    // === Horizontal re-consolidation (cross-time clustering) ===
    /** ISO 8601 timestamp of last re-evaluation for consolidation */
    last_reprocessed_at: z.string().datetime({ offset: true }).optional(),
    /** How many times this chunk has been re-consolidated */
    reprocess_count: z.number().int().min(0).optional(),
    /** Point IDs of similar chunks (cluster representatives) */
    similarity_anchors: z.array(z.string()).optional(),

    // === Timeline building (causal sequences) ===
    /** Timeline this chunk belongs to (e.g., project, conversation) */
    timeline_id: z.string().optional(),
    /** Sequence position within timeline */
    timeline_position: z.number().int().min(0).optional(),
    /** Relationships to other chunks */
    causal_links: z.array(CausalLinkSchema).optional(),

    // === Stability and deletion ===
    /** Stability score (0.0-1.0, how stable/frozen this chunk is) */
    stability_score: z.number().min(0).max(1).optional(),
    /** Number of times retrieved in searches */
    access_count: z.number().int().min(0).optional(),
    /** ISO 8601 timestamp of last retrieval */
    last_accessed_at: z.string().datetime({ offset: true }).optional(),
    /** Marked for deletion after grace period */
    deletion_eligible: z.boolean().optional(),
    /** Point ID of replacement chunk */
    superseded_by: z.string().optional(),
    /** ISO 8601 timestamp when deletion_eligible was set */
    deletion_marked_at: z.string().datetime({ offset: true }).optional(),
  })
  .passthrough() // Allow additional properties for Qdrant compatibility

export type ChunkPayload = z.infer<typeof ChunkPayloadSchema>

// ============================================
// Qdrant Point
// ============================================

/**
 * A vector point with payload for Qdrant storage
 */
export const QdrantPointSchema = z.object({
  /** Unique point identifier */
  id: z.string().min(1),
  /** Embedding vector */
  vector: z.array(z.number()),
  /** Chunk payload */
  payload: ChunkPayloadSchema,
})
export type QdrantPoint = z.infer<typeof QdrantPointSchema>

// ============================================
// Unified Parameter Types (Phase 1.2)
// ============================================

/**
 * Unified ingest parameters
 * Used by: CLI, daemon, ApplicationService
 *
 * NOTE: All fields are optional to maintain backwards compatibility.
 * Defaults are applied at runtime, not in the schema.
 */
export const IngestParamsSchema = z.object({
  /** File or directory paths to ingest */
  paths: z.array(z.string()).min(1, 'At least one path required'),
  /** Recursively process directories (default: false) */
  recursive: z.boolean().optional(),
  /** Root directory for relative paths */
  rootDir: z.string().optional(),
  /** Enable verbose logging (default: false) */
  verbose: z.boolean().optional(),
  /** Pre-fetched QNTM keys for reuse (optimization) */
  existingKeys: z.array(z.string()).optional(),
  /** Disable HNSW during batch ingestion (auto if undefined) */
  useHNSWToggle: z.boolean().optional(),
  /** Enable watch mode (auto-reingest on file changes, default: false) */
  watch: z.boolean().optional(),
  /** Allow auto-consolidation after ingest (default: true) */
  allowConsolidation: z.boolean().optional(),
  /** Chunks threshold before triggering consolidation (default: 500) */
  consolidationThreshold: z.number().int().min(1).optional(),
})
export type IngestParams = z.infer<typeof IngestParamsSchema> & {
  /** Event emitter function (opt-in, for daemon mode) */
  emit?: (event: any) => void
}

/**
 * Unified search parameters
 * Used by: CLI, daemon, ApplicationService
 *
 * NOTE: All fields except query are optional to maintain backwards compatibility.
 * Defaults are applied at runtime, not in the schema.
 */
export const SearchParamsSchema = z.object({
  /** Search query string */
  query: z.string().min(1, 'Query cannot be empty'),
  /** Maximum results to return (default: 5) */
  limit: z.number().int().min(1).max(100).optional(),
  /** ISO 8601 datetime for temporal filtering */
  since: z.string().datetime({ offset: true }).optional(),
  /** Filter by specific QNTM key */
  qntmKey: z.string().optional(),
  /** Enable reranking with cross-encoder (default: false) */
  rerank: z.boolean().optional(),
  /** How many candidates to rerank (default: 3x limit) */
  rerankTopK: z.number().int().min(1).max(1000).optional(),
  /** Enable QNTM query expansion (vocabulary bridging, default: false) */
  expandQuery: z.boolean().optional(),
  /** Enable hybrid search (vector + keyword with RRF, default: false) */
  hybridSearch: z.boolean().optional(),
  /** Filter by consolidation level (0=raw, 1=deduped, 2=topic, 3=domain, 4=meta) */
  consolidationLevel: z
    .union([z.literal(0), z.literal(1), z.literal(2), z.literal(3), z.literal(4)])
    .optional(),
  /** Filter by content type */
  contentType: z
    .enum(['code', 'document', 'conversation', 'signal', 'learning', 'axiom', 'evidence'])
    .optional(),
  /** Filter by agent role */
  agentRole: z
    .enum(['observer', 'connector', 'explainer', 'challenger', 'integrator', 'meta'])
    .optional(),
  /** Filter by temperature tier */
  temperature: z.enum(['hot', 'warm', 'cold']).optional(),
})
export type SearchParams = z.infer<typeof SearchParamsSchema> & {
  /** Event emitter function (opt-in, for daemon mode) */
  emit?: (event: any) => void
}

/**
 * Unified consolidate parameters
 * Used by: CLI, daemon, ApplicationService
 *
 * NOTE: All fields are optional to maintain backwards compatibility.
 * Defaults are applied at runtime, not in the schema.
 */
export const ConsolidateParamsSchema = z.object({
  /** Dry run (preview without executing, default: false) */
  dryRun: z.boolean().optional(),
  /** Similarity threshold for consolidation candidates (0-1, default: 0.8) */
  threshold: z.number().min(0).max(1).optional(),
  /** Batch size for processing chunks (default: 100) */
  batchSize: z.number().int().min(10).max(1000).optional(),
  /** Maximum chunks to consolidate (0 = no limit, default: 0) */
  limit: z.number().int().min(0).optional(),
  /** Filter by QNTM key pattern (regex) */
  qntmKeyFilter: z.string().optional(),
  /** Only consolidate chunks at this level */
  consolidationLevel: z
    .union([z.literal(0), z.literal(1), z.literal(2), z.literal(3), z.literal(4)])
    .optional(),
  /** Continuous consolidation mode (run as background task, default: false) */
  continuous: z.boolean().optional(),
  /** Poll interval for continuous mode (ms, default: 30000) */
  pollIntervalMs: z.number().int().min(1000).optional(),
})
export type ConsolidateParams = z.infer<typeof ConsolidateParamsSchema> & {
  /** Event emitter function (opt-in, for daemon mode) */
  emit?: (event: any) => void
}

/**
 * Unified timeline parameters
 * Used by: CLI, daemon, ApplicationService
 */
export const TimelineParamsSchema = z.object({
  /** Starting date (ISO 8601) */
  since: z.string().datetime({ offset: true }),
  /** Ending date (ISO 8601, optional = now) */
  until: z.string().datetime({ offset: true }).optional(),
  /** Maximum results to return */
  limit: z.number().int().min(1).max(1000).optional().default(100),
  /** Timeline ID filter (e.g., project name, conversation ID) */
  timelineId: z.string().optional(),
  /** Include causal links in results */
  includeCausalLinks: z.boolean().optional().default(false),
  /** Granularity for timeline grouping */
  granularity: z.enum(['hour', 'day', 'week', 'month']).optional().default('day'),
})
export type TimelineParams = z.infer<typeof TimelineParamsSchema>

/**
 * Timeline period with aggregated metrics
 */
export const TimelinePeriodSchema = z.object({
  /** Period start timestamp (ISO 8601) */
  period: z.string(),
  /** Number of chunks ingested in this period */
  chunkCount: z.number().int().min(0),
  /** Number of files ingested in this period */
  fileCount: z.number().int().min(0),
  /** Total characters ingested in this period */
  charCount: z.number().int().min(0),
  /** Average chunk size in this period */
  avgChunkSize: z.number().min(0),
})
export type TimelinePeriod = z.infer<typeof TimelinePeriodSchema>

/**
 * Timeline data with aggregated metrics
 * Used by: CLI timeline, daemon analytics, DuckDB backend
 */
export const TimelineDataSchema = z.object({
  /** Timeline periods with aggregated metrics */
  periods: z.array(TimelinePeriodSchema),
  /** Total chunks across all periods */
  totalChunks: z.number().int().min(0),
  /** Total files across all periods */
  totalFiles: z.number().int().min(0),
  /** Query execution time (milliseconds) */
  durationMs: z.number().int().min(0),
})
export type TimelineData = z.infer<typeof TimelineDataSchema>

/**
 * QNTM generation parameters
 */
export const QNTMGenerateParamsSchema = z.object({
  /** Text to generate QNTM keys for */
  text: z.string().min(1),
  /** Existing QNTM keys for context */
  existingKeys: z.array(z.string()).default([]),
  /** Context for generation (file path, chunk index, etc.) */
  context: z
    .object({
      fileName: z.string().optional(),
      chunkIndex: z.number().int().min(0).optional(),
      totalChunks: z.number().int().min(1).optional(),
    })
    .optional(),
  /** Abstraction level for keys */
  level: z.enum(['concrete', 'abstract', 'meta']).default('concrete'),
})
export type QNTMGenerateParams = z.infer<typeof QNTMGenerateParamsSchema>

// ============================================
// Unified Result Types (Phase 1.2)
// ============================================

/**
 * Enhanced result of ingestion operation
 * Used by: CLI, daemon, ApplicationService
 */
export const IngestResultSchema = z.object({
  /** Number of files successfully processed */
  filesProcessed: z.number().int().min(0),
  /** Number of chunks stored */
  chunksStored: z.number().int().min(0),
  /** Errors encountered during ingestion */
  errors: z.array(
    z.object({
      /** File that failed */
      file: z.string(),
      /** Error message */
      error: z.string(),
    })
  ),
  /** Time taken (milliseconds) - NEW in Phase 1.2 */
  durationMs: z.number().int().min(0).optional(),
  /** Peak memory usage (bytes) - NEW in Phase 1.2 */
  peakMemoryBytes: z.number().int().min(0).optional(),
  /** Files skipped (already up to date) - NEW in Phase 1.2 */
  skippedFiles: z.number().int().min(0).optional(),
})
export type IngestResult = z.infer<typeof IngestResultSchema>

/**
 * Result of consolidation operation
 * Used by: CLI, daemon, ApplicationService
 */
export const ConsolidateResultSchema = z.object({
  /** Number of consolidation operations performed */
  consolidationsPerformed: z.number().int().min(0),
  /** Number of chunks absorbed into primary chunks */
  chunksAbsorbed: z.number().int().min(0),
  /** Number of candidate pairs evaluated */
  candidatesEvaluated: z.number().int().min(0),
  /** Consolidation type breakdown */
  typeBreakdown: z
    .object({
      duplicate_work: z.number().int().min(0).default(0),
      sequential_iteration: z.number().int().min(0).default(0),
      contextual_convergence: z.number().int().min(0).default(0),
    })
    .optional(),
  /** Time taken (milliseconds) */
  durationMs: z.number().int().min(0).optional(),
  /** Preview of consolidations (if dryRun) */
  preview: z
    .array(
      z.object({
        primary_id: z.string(),
        secondary_id: z.string(),
        similarity: z.number().min(0).max(1),
        consolidation_type: z.enum([
          'duplicate_work',
          'sequential_iteration',
          'contextual_convergence',
        ]),
        reasoning: z.string(),
      })
    )
    .optional(),
})
export type ConsolidateResult = z.infer<typeof ConsolidateResultSchema>

/**
 * QNTM generation result
 */
export const QNTMGenerateResultSchema = z.object({
  /** Generated QNTM keys */
  keys: z.array(z.string()).min(1),
  /** LLM reasoning for key generation */
  reasoning: z.string().optional(),
})
export type QNTMGenerateResult = z.infer<typeof QNTMGenerateResultSchema>

/**
 * Health status for a single service
 */
export const ServiceHealthSchema = z.object({
  /** Service name */
  name: z.string(),
  /** Service status */
  status: z.enum(['healthy', 'degraded', 'unhealthy']),
  /** Response latency (milliseconds) */
  latencyMs: z.number().int().min(0).optional(),
  /** Error message (if unhealthy) */
  error: z.string().optional(),
  /** Additional details (arbitrary key-value pairs) */
  details: z.any().optional(),
})
export type ServiceHealth = z.infer<typeof ServiceHealthSchema>

/**
 * Overall health status
 * Used by: CLI doctor, daemon health endpoint, ApplicationService
 */
export const HealthStatusSchema = z.object({
  /** Overall status */
  overall: z.enum(['healthy', 'degraded', 'unhealthy']),
  /** Timestamp of health check */
  timestamp: z.string().datetime({ offset: true }),
  /** Individual service health */
  services: z.object({
    /** Vector search (Qdrant) */
    vector: ServiceHealthSchema,
    /** Metadata storage (PostgreSQL only - required) */
    metadata: ServiceHealthSchema,
    /** Cache (Valkey/Redis, optional) */
    cache: ServiceHealthSchema.optional(),
    /** Analytics (DuckDB, optional) */
    analytics: ServiceHealthSchema.optional(),
    /** Full-text search (Meilisearch, optional) */
    fulltext: ServiceHealthSchema.optional(),
    /** Embedding backends */
    embedding: z.object({
      total: z.number().int().min(0),
      available: z.number().int().min(0),
      backends: z.array(ServiceHealthSchema),
    }),
    /** LLM backends */
    llm: z.object({
      total: z.number().int().min(0),
      available: z.number().int().min(0),
      backends: z.array(ServiceHealthSchema),
    }),
    /** Reranker backends */
    reranker: z.object({
      total: z.number().int().min(0),
      available: z.number().int().min(0),
      backends: z.array(ServiceHealthSchema),
    }),
  }),
  /** System information */
  system: z
    .object({
      /** CPU usage (0-1) */
      cpuUsage: z.number().min(0).max(1).optional(),
      /** Memory usage (bytes) */
      memoryUsage: z.number().int().min(0).optional(),
      /** Disk usage (bytes) */
      diskUsage: z.number().int().min(0).optional(),
      /** Uptime (milliseconds) */
      uptimeMs: z.number().int().min(0).optional(),
    })
    .optional(),
})
export type HealthStatus = z.infer<typeof HealthStatusSchema>

/**
 * Storage tier status
 */
export const TierStatusSchema = z.object({
  /** Metadata backend ('sqlite' or 'postgresql') */
  metadata: z.string(),
  /** Cache backend ('none', 'redis', 'valkey') */
  cache: z.string(),
  /** Analytics backend ('none', 'duckdb') */
  analytics: z.string(),
  /** Full-text search backend ('none', 'meilisearch') */
  fulltext: z.string(),
})
export type TierStatus = z.infer<typeof TierStatusSchema>

/**
 * Status result
 */
export const StatusResultSchema = z.object({
  /** Collection statistics */
  collection: z.object({
    name: z.string(),
    totalChunks: z.number().int().min(0),
    totalFiles: z.number().int().min(0),
    totalQNTMKeys: z.number().int().min(0),
    avgChunkSize: z.number().min(0),
    lastIngested: z.string().datetime({ offset: true }).optional(),
  }),
  /** Backend information */
  backends: z.object({
    embedding: z.array(z.string()),
    llm: z.array(z.string()),
    reranker: z.array(z.string()),
    storage: z.string(),
  }),
  /** Storage tier status */
  storage: TierStatusSchema,
  /** System metrics */
  system: z
    .object({
      cpuUsage: z.number().min(0).max(1).optional(),
      memoryUsage: z.number().int().min(0).optional(),
      diskUsage: z.number().int().min(0).optional(),
      uptimeMs: z.number().int().min(0).optional(),
    })
    .optional(),
})
export type StatusResult = z.infer<typeof StatusResultSchema>

// ============================================
// Application Service Interface (Phase 1.3)
// ============================================

/**
 * Unified Application Service Interface
 *
 * Single entry point for all Atlas operations.
 * Both CLI and daemon delegate to implementations of this interface.
 *
 * Design principles:
 * - Pure functions: No hidden state, all dependencies injected
 * - Async by default: All methods return Promises
 * - Event-driven: Optional emit() for progress updates
 * - Type-safe: Zod-validated parameters and results
 *
 * @example
 * ```typescript
 * // CLI usage
 * const app = new DefaultApplicationService()
 * await app.initialize()
 * const result = await app.ingest({ paths: ['./docs'], recursive: true })
 * console.log(`Ingested ${result.filesProcessed} files`)
 * await app.shutdown()
 * ```
 */
export interface ApplicationService {
  // ============================================
  // Core Operations
  // ============================================

  /**
   * Ingest files into Atlas
   *
   * Used by:
   * - CLI: `atlas ingest <paths...>`
   * - Daemon: `atlas.ingest` RPC method
   *
   * @param params - Ingestion parameters (paths, recursive, etc.)
   * @returns Ingestion result (files processed, chunks stored, errors)
   *
   * @example
   * ```typescript
   * const result = await app.ingest({
   *   paths: ['./docs'],
   *   recursive: true,
   * })
   * console.log(`Ingested ${result.filesProcessed} files`)
   * ```
   */
  ingest(params: IngestParams): Promise<IngestResult>

  /**
   * Search for semantic matches
   *
   * Used by:
   * - CLI: `atlas search <query>`
   * - Daemon: `atlas.search` RPC method
   *
   * @param params - Search parameters (query, limit, filters, etc.)
   * @returns Array of search results sorted by relevance
   *
   * @example
   * ```typescript
   * const results = await app.search({
   *   query: 'authentication implementation',
   *   limit: 10,
   *   rerank: true,
   * })
   * console.log(`Found ${results.length} results`)
   * ```
   */
  search(params: SearchParams): Promise<SearchResult[]>

  /**
   * Consolidate similar chunks
   *
   * Used by:
   * - CLI: `atlas consolidate`
   * - Daemon: `atlas.consolidate` RPC method
   *
   * @param params - Consolidation parameters (threshold, dryRun, etc.)
   * @returns Consolidation result (operations performed, chunks absorbed)
   *
   * @example
   * ```typescript
   * const result = await app.consolidate({
   *   dryRun: true,
   *   threshold: 0.85,
   * })
   * console.log(`Found ${result.candidatesEvaluated} candidates`)
   * ```
   */
  consolidate(params: ConsolidateParams): Promise<ConsolidateResult>

  /**
   * Query timeline of chunks
   *
   * Used by:
   * - CLI: `atlas timeline --since <date>`
   * - Daemon: `atlas.timeline` RPC method
   *
   * @param params - Timeline parameters (since, until, limit, etc.)
   * @returns Array of chunks sorted chronologically
   *
   * @example
   * ```typescript
   * const results = await app.timeline({
   *   since: '2026-01-01T00:00:00Z',
   *   limit: 50,
   * })
   * console.log(`Found ${results.length} chunks`)
   * ```
   */
  timeline(params: TimelineParams): Promise<SearchResult[]>

  // ============================================
  // Health & Diagnostics
  // ============================================

  /**
   * Health check across all services
   *
   * Used by:
   * - CLI: `atlas doctor`
   * - Daemon: `atlas.health` RPC method
   *
   * @returns Overall health status and individual service health
   *
   * @example
   * ```typescript
   * const health = await app.health()
   * console.log(`Overall status: ${health.overall}`)
   * console.log(`Vector DB: ${health.services.vector.status}`)
   * ```
   */
  health(): Promise<HealthStatus>

  /**
   * Get current Atlas status
   *
   * Used by:
   * - CLI: `atlas status`
   * - Daemon: `atlas.status` RPC method
   *
   * @returns Collection stats, backend info, system metrics
   *
   * @example
   * ```typescript
   * const status = await app.status()
   * console.log(`Total chunks: ${status.collection.totalChunks}`)
   * console.log(`Storage: ${status.storage.metadata}`)
   * ```
   */
  status(): Promise<StatusResult>

  // ============================================
  // QNTM Operations
  // ============================================

  /**
   * Generate QNTM keys for text
   *
   * Used by:
   * - Daemon: `atlas.qntm.generate` RPC method
   * - Internal: During ingestion
   *
   * @param params - Text and context for QNTM generation
   * @returns Generated QNTM keys and reasoning
   *
   * @example
   * ```typescript
   * const result = await app.generateQNTM({
   *   text: 'User authentication with JWT tokens',
   *   existingKeys: [],
   * })
   * console.log(`Generated keys: ${result.keys.join(', ')}`)
   * ```
   */
  generateQNTM(params: QNTMGenerateParams): Promise<QNTMGenerateResult>

  // ============================================
  // Configuration
  // ============================================

  /**
   * Get current configuration
   *
   * @returns Current Atlas configuration (resolved from file + env + overrides)
   *
   * @example
   * ```typescript
   * const config = app.getConfig()
   * console.log(`Qdrant URL: ${config.qdrant?.url}`)
   * ```
   */
  getConfig(): any // Will be AtlasConfig once storage config is added

  /**
   * Apply runtime configuration overrides
   *
   * Used by:
   * - CLI: Apply --embedding, --llm flags
   * - Daemon: Apply client-specific overrides
   *
   * @param overrides - Partial configuration to merge
   *
   * @example
   * ```typescript
   * app.applyOverrides({
   *   backends: {
   *     'text-embedding': 'voyage:voyage-3-large',
   *   },
   * })
   * ```
   */
  applyOverrides(overrides: any): void // Will be Partial<AtlasConfig> once storage config is added

  // ============================================
  // Lifecycle
  // ============================================

  /**
   * Initialize application (load config, initialize backends)
   *
   * Called once at startup (CLI or daemon).
   *
   * @example
   * ```typescript
   * const app = new DefaultApplicationService()
   * await app.initialize()
   * // Now ready to handle requests
   * ```
   */
  initialize(): Promise<void>

  /**
   * Shutdown application (cleanup resources)
   *
   * Called on graceful shutdown.
   *
   * @example
   * ```typescript
   * process.on('SIGTERM', async () => {
   *   await app.shutdown()
   *   process.exit(0)
   * })
   * ```
   */
  shutdown(): Promise<void>
}
