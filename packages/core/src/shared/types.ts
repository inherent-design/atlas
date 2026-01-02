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
export const ConsolidationDirectionSchema = z.enum([
  'forward',
  'backward',
  'convergent',
  'unknown',
])
export type ConsolidationDirection = z.infer<typeof ConsolidationDirectionSchema>

/**
 * Consolidation level hierarchy (vertical abstraction)
 * 0 = Raw chunk (fresh ingestion, no consolidation)
 * 1 = Deduplicated (merged with near-duplicates)
 * 2 = Topic summary (aggregated multiple level-1 chunks)
 * 3 = Domain knowledge (abstract patterns across topics)
 */
export const ConsolidationLevelSchema = z.union([
  z.literal(0),
  z.literal(1),
  z.literal(2),
  z.literal(3),
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
export const InferredBySchema = z.enum([
  'consolidator',
  'explainer',
  'user',
  'heuristic',
])
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
// Search Types
// ============================================

/**
 * Search options for semantic queries
 */
export const SearchOptionsSchema = z.object({
  /** Search query string */
  query: z.string().min(1, 'Query cannot be empty'),
  /** Maximum results to return */
  limit: z.number().int().min(1).max(100).optional(),
  /** ISO 8601 datetime for temporal filtering */
  since: z.string().datetime({ offset: true }).optional(),
  /** Filter by specific QNTM key */
  qntmKey: z.string().optional(),
  /** Enable reranking with cross-encoder */
  rerank: z.boolean().default(false),
  /** How many candidates to rerank (default: 3x limit) */
  rerankTopK: z.number().int().min(1).max(1000).optional(),
})
export type SearchOptions = z.infer<typeof SearchOptionsSchema>

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
    /** Consolidation level (0=raw, 1=deduped, 2=topic, 3=domain) */
    consolidation_level: ConsolidationLevelSchema,
    /** Abstraction score (0.0-1.0, higher = more abstract) */
    abstraction_score: z.number().min(0).max(1).optional(),
    /** Type of consolidation performed */
    consolidation_type: ConsolidationTypeSchema.optional(),
    /** Direction of consolidation relationship */
    consolidation_direction: ConsolidationDirectionSchema.optional(),
    /** LLM-provided explanation of consolidation */
    consolidation_reasoning: z.string().optional(),

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
// Ingest Types
// ============================================

/**
 * Configuration for ingestion
 */
export const IngestOptionsSchema = z.object({
  /** File or directory paths to ingest */
  paths: z.array(z.string()).min(1, 'At least one path required'),
  /** Recursively process directories */
  recursive: z.boolean().default(false),
  /** Root directory for relative paths */
  rootDir: z.string().optional(),
  /** Enable verbose logging */
  verbose: z.boolean().default(true),
  /** Pre-fetched QNTM keys for reuse */
  existingKeys: z.array(z.string()).optional(),
  /** Disable HNSW during batch ingestion (auto based on file count if undefined) */
  useHNSWToggle: z.boolean().optional(),
})
export type IngestOptions = z.infer<typeof IngestOptionsSchema>

/**
 * Result of ingestion operation
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
})
export type IngestResult = z.infer<typeof IngestResultSchema>

// ============================================
// Timeline Types
// ============================================

/**
 * Options for timeline queries
 */
export const TimelineOptionsSchema = z.object({
  /** Starting date (ISO 8601) */
  since: z.string().datetime({ offset: true }),
  /** Maximum results to return */
  limit: z.number().int().min(1).max(100).default(20),
})
export type TimelineOptions = z.infer<typeof TimelineOptionsSchema>
