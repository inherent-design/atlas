/**
 * Storage Backend Types
 *
 * Abstracts vector database operations for multi-backend support.
 */

import type { BackendDescriptor, LatencyClass } from '../../shared/capabilities'
import type { ChunkPayload } from '../../shared/types'

// ============================================
// Capability Types
// ============================================

/**
 * Storage capability (single capability for now)
 * Future: could add capabilities like 'scalar-quantization', 'product-quantization', etc.
 */
export type StorageCapability = 'vector-storage'

/**
 * Storage backend descriptor.
 * Extends base descriptor with storage-specific metadata and capabilities.
 */
export interface StorageBackend extends BackendDescriptor<StorageCapability>, CanStoreVectors {
  /** Vector dimensions supported by this backend */
  readonly dimensions: number
  /** Distance metric used */
  readonly distance: 'cosine' | 'dot' | 'euclidean'
  /** Relative latency classification */
  readonly latency: LatencyClass
}

// ============================================
// Vector Point Types
// ============================================

/**
 * Named vector identifier (corresponds to collection vector names)
 */
export type VectorName = 'text' | 'code' | 'media'

/**
 * Named vectors structure for multi-vector points.
 * Each point can have multiple named vectors (e.g., text + code).
 *
 * Index signature satisfies Qdrant SDK's VectorStruct type.
 */
export interface NamedVectors {
  text?: number[]
  code?: number[]
  media?: number[]
  [key: string]: number[] | undefined
}

/**
 * Point structure for upsert/search operations.
 * Generic payload type for flexibility.
 */
export interface VectorPoint<P = ChunkPayload> {
  /** Unique identifier for this point */
  id: string
  /** Named vectors (replaces single vector field) */
  vector: NamedVectors
  /** Attached metadata */
  payload: P
}

// ============================================
// Search Types
// ============================================

/**
 * Parameters for vector search
 */
export interface SearchParams {
  /** Which named vector to search (default: 'text') */
  vectorName?: VectorName
  /** Query vector */
  vector: number[]
  /** Maximum number of results */
  limit: number
  /** Filter conditions */
  filter?: StorageFilter
  /** Minimum similarity score threshold (0.0-1.0) */
  scoreThreshold?: number
  /** Include payload in results (default: true) */
  withPayload?: boolean
  /** Include vector in results (default: false) */
  withVector?: boolean
}

/**
 * Search result item
 */
export interface SearchResult<P = ChunkPayload> {
  /** Point ID */
  id: string
  /** Similarity score */
  score: number
  /** Payload data */
  payload: P
  /** Vector (if withVector: true) */
  vector?: number[]
}

// ============================================
// Filter Types
// ============================================

/**
 * Typed filter structure (replaces :any from Qdrant SDK)
 *
 * Supports standard filter operations:
 * - must: all conditions must match (AND)
 * - must_not: no conditions can match (NOT)
 * - should: at least one condition must match (OR)
 */
export interface StorageFilter {
  must?: FilterCondition[]
  must_not?: FilterCondition[]
  should?: FilterCondition[]
}

/**
 * Individual filter condition
 * Maps to Qdrant filter conditions:
 * - match.value → MatchValue
 * - match.any → MatchAny
 * - match.except → MatchExcept (excludes listed values)
 * - range → Range condition
 * - has_id → HasIdCondition
 * - is_null → IsNullCondition (true = field is null)
 * - is_empty → IsEmptyCondition (true = field is null or empty)
 */
export type FilterCondition =
  | { key: string; match: { value: string | number | boolean } }
  | { key: string; match: { any: string[] } }
  | { key: string; match: { except: string[] } } // Note: null not valid here, use is_null instead
  | {
      key: string
      range: { gte?: string | number; lte?: string | number; lt?: number; gt?: number }
    }
  | { has_id: string[] }
  | { is_null: string } // Field name - condition passes if field IS null
  | { is_empty: string } // Field name - condition passes if field IS null or empty array

// ============================================
// Scroll Types
// ============================================

/**
 * Options for scrolling through points
 */
export interface ScrollOptions {
  /** Number of points to return */
  limit: number
  /** Pagination offset (from previous scroll) */
  offset?: string | null
  /** Filter conditions */
  filter?: StorageFilter
  /** Include payload in results (default: true) */
  withPayload?: boolean
  /** Include vector in results (default: false) */
  withVector?: boolean
}

/**
 * Scroll result with pagination
 */
export interface ScrollResult<P = ChunkPayload> {
  /** Points returned in this page */
  points: VectorPoint<P>[]
  /** Offset for next page (null if no more results) */
  nextOffset: string | null
}

// ============================================
// Collection Types
// ============================================

/**
 * Configuration for creating a collection
 */
export interface CollectionConfig {
  /** Vector dimensions */
  dimensions: number
  /** Distance metric */
  distance: 'cosine' | 'dot' | 'euclidean'
  /** Store vectors on disk (vs in-memory) */
  onDisk?: boolean
  /** HNSW graph M parameter (edges per node) */
  hnswM?: number
  /** HNSW graph ef_construct parameter (search depth during build) */
  hnswEfConstruct?: number
  /** Quantization type (compression) */
  quantization?: 'int8' | 'float16' | null
}

// ============================================
// Capability Interface
// ============================================

/**
 * Vector storage capability interface.
 * Backends that implement this can store and retrieve vectors.
 */
export interface CanStoreVectors {
  /**
   * Insert or update points in a collection
   *
   * @param collection - Collection name
   * @param points - Points to upsert
   */
  upsert(collection: string, points: VectorPoint[]): Promise<void>

  /**
   * Search for similar vectors
   *
   * @param collection - Collection name
   * @param params - Search parameters
   * @returns Array of search results, sorted by score (descending)
   */
  search(collection: string, params: SearchParams): Promise<SearchResult[]>

  /**
   * Retrieve specific points by ID
   *
   * @param collection - Collection name
   * @param ids - Point IDs to retrieve
   * @returns Array of points (may be fewer than requested if some IDs don't exist)
   */
  retrieve(collection: string, ids: string[]): Promise<VectorPoint[]>

  /**
   * Delete points by ID
   *
   * @param collection - Collection name
   * @param ids - Point IDs to delete
   */
  delete(collection: string, ids: string[]): Promise<void>

  /**
   * Scroll through all points in a collection
   *
   * @param collection - Collection name
   * @param options - Scroll options (limit, offset, filter)
   * @returns Scroll result with points and next offset
   */
  scroll(collection: string, options: ScrollOptions): Promise<ScrollResult>

  /**
   * Update payload for specific points
   *
   * @param collection - Collection name
   * @param ids - Point IDs to update
   * @param payload - Partial payload to merge
   */
  setPayload(collection: string, ids: string[], payload: Partial<ChunkPayload>): Promise<void>

  // === Collection Management ===

  /**
   * Check if a collection exists
   *
   * @param collection - Collection name
   * @returns true if collection exists
   */
  collectionExists(collection: string): Promise<boolean>

  /**
   * Create a new collection
   *
   * @param collection - Collection name
   * @param config - Collection configuration
   */
  createCollection(collection: string, config: CollectionConfig): Promise<void>

  /**
   * Delete a collection
   *
   * @param collection - Collection name
   */
  deleteCollection(collection: string): Promise<void>

  /**
   * Get collection information (point count, status, etc.)
   *
   * @param collection - Collection name
   * @returns Collection info including points_count, vector_dimensions, and segments_count
   */
  getCollectionInfo(collection: string): Promise<{
    points_count: number
    vector_dimensions?: number | Record<string, number>
    segments_count?: number
  }>

  /**
   * Create a payload index for filtered queries (Qdrant-specific).
   * Optional method - backends may skip if indexing is automatic.
   *
   * @param collection - Collection name
   * @param config - Index configuration
   */
  createPayloadIndex?(
    collection: string,
    config: {
      field_name: string
      field_schema: 'keyword' | 'integer' | 'float' | 'bool' | 'datetime'
    }
  ): Promise<void>
}
