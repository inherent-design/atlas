/**
 * Shared TypeScript types for Atlas
 *
 * Schema Version: 2.0 (2025-12-30)
 * Breaking changes from v1:
 * - occurrences: number → string[] (timestamps array)
 * - consolidated: boolean → removed (use consolidation_level instead)
 * - consolidated_from: string[] → removed (absorbed into parents)
 */

// Consolidation types
export type ConsolidationType = 'duplicate_work' | 'sequential_iteration' | 'contextual_convergence'
export type ConsolidationDirection = 'forward' | 'backward' | 'convergent' | 'unknown'

/**
 * Consolidation level hierarchy (vertical abstraction)
 * 0 = Raw chunk (fresh ingestion, no consolidation)
 * 1 = Deduplicated (merged with near-duplicates)
 * 2 = Topic summary (aggregated multiple level-1 chunks)
 * 3 = Domain knowledge (abstract patterns across topics)
 */
export type ConsolidationLevel = 0 | 1 | 2 | 3

/**
 * Causal relationship between chunks (timeline building)
 */
export interface CausalLink {
  target_id: string // Point ID of related chunk
  relation: 'supersedes' | 'references' | 'derived_from' | 'contradicts' | 'extends'
  confidence: number // 0.0-1.0
  inferred_by: 'consolidator' | 'explainer' | 'user' | 'heuristic'
}

export interface SearchOptions {
  query: string
  limit?: number
  since?: string // ISO 8601 datetime for temporal filtering
  qntmKey?: string // Filter by specific QNTM key
}

export interface SearchResult {
  text: string
  file_path: string
  chunk_index: number
  score: number
  created_at: string
  qntm_key: string
}

export interface ChunkPayload {
  // === Core identity ===
  original_text: string
  file_path: string
  file_name: string
  file_type: string
  chunk_index: number
  total_chunks: number
  char_count: number
  qntm_keys: string[] // Multiple semantic addresses (tag-based)
  created_at: string // ISO 8601
  importance: 'normal' | 'high' | 'low'

  // === Vertical consolidation (abstraction levels) ===
  consolidation_level: ConsolidationLevel // 0=raw, 1=deduped, 2=topic, 3=domain
  abstraction_score?: number // 0.0-1.0, higher = more abstract
  consolidation_type?: ConsolidationType
  consolidation_direction?: ConsolidationDirection
  consolidation_reasoning?: string // LLM-provided explanation

  // === Provenance DAG ===
  parents?: string[] // Point IDs this was consolidated from (absorbs old consolidated_from)
  occurrences?: string[] // ISO 8601 timestamps of all instances (BREAKING: was number)

  // === Horizontal re-consolidation (cross-time clustering) ===
  last_reprocessed_at?: string // ISO 8601, when last re-evaluated for consolidation
  reprocess_count?: number // How many times this chunk has been re-consolidated
  similarity_anchors?: string[] // Point IDs of similar chunks (cluster representatives)

  // === Timeline building (causal sequences) ===
  timeline_id?: string // Timeline this chunk belongs to (e.g., project, conversation)
  timeline_position?: number // Sequence position within timeline
  causal_links?: CausalLink[] // Relationships to other chunks

  // === Stability and deletion ===
  stability_score?: number // 0.0-1.0, how stable/frozen this chunk is
  access_count?: number // Number of times retrieved in searches
  last_accessed_at?: string // ISO 8601, last retrieval time
  deletion_eligible?: boolean // Marked for deletion after grace period
  superseded_by?: string // Point ID of replacement chunk
  deletion_marked_at?: string // ISO 8601, when deletion_eligible was set

  /**
   * Index signature for Qdrant payload compatibility.
   * Qdrant accepts arbitrary key-value pairs in payloads, and this signature
   * allows ChunkPayload to satisfy that contract without type errors.
   * Future: StorageInterface abstraction will remove this leaky abstraction.
   */
  [key: string]: unknown
}

export interface QdrantPoint {
  id: string
  vector: number[]
  payload: ChunkPayload
}
