/**
 * Mock storage backend for testing
 *
 * In-memory vector storage using Map.
 * Implements full StorageBackend interface for testing.
 *
 * IMPORTANT: Payload structure matches live data captured in __fixtures__/live-data/.
 * See loader.ts for real production payload examples with fields like:
 * - qntm_keys: string[]
 * - consolidation_level: number
 * - embedding_model: string
 * - embedding_strategy: string
 * - vectors_present: string[]
 * - parents: string[] (for consolidated chunks)
 * - occurrences: string[] (timestamps)
 * - consolidation_type/direction/reasoning
 */

import type {
  StorageBackend,
  VectorPoint,
  SearchParams,
  SearchResult,
  ScrollOptions,
  ScrollResult,
  CollectionConfig,
  StorageFilter,
  NamedVectors,
} from '../services/storage/types.js'
import type { ChunkPayload } from '../shared/types.js'
import { cosineSimilarity } from '../__fixtures__/embeddings.js'

/**
 * Configuration for MockStorageBackend
 */
export interface MockStorageConfig {
  /** Delay in ms to simulate network latency */
  delay?: number
  /** Error to throw (for error testing) */
  throwError?: Error
}

/**
 * In-memory collection storage
 */
interface Collection {
  config: CollectionConfig
  points: Map<string, VectorPoint<ChunkPayload>>
}

/**
 * Mock storage backend with in-memory Map
 */
export class MockStorageBackend implements StorageBackend {
  readonly name = 'mock-storage'
  readonly capabilities = new Set(['vector-storage'] as const)
  readonly dimensions: number
  readonly distance: 'cosine' | 'dot' | 'euclidean'
  readonly latency = 'fastest' as const

  private collections: Map<string, Collection> = new Map()
  private config: MockStorageConfig
  private calls: Array<{ method: string; args: any[]; timestamp: number }> = []

  constructor(
    config: MockStorageConfig = {},
    dimensions = 1024,
    distance: 'cosine' | 'dot' | 'euclidean' = 'cosine'
  ) {
    this.config = config
    this.dimensions = dimensions
    this.distance = distance
  }

  /**
   * Check if backend is available
   */
  async isAvailable(): Promise<boolean> {
    return true // Mock is always available
  }

  /**
   * Check if backend supports a capability
   */
  supports(capability: string): boolean {
    return this.capabilities.has(capability as any)
  }

  /**
   * Check if collection exists
   */
  async collectionExists(collection: string): Promise<boolean> {
    this.recordCall('collectionExists', [collection])
    await this.maybeDelay()
    return this.collections.has(collection)
  }

  /**
   * Create a new collection
   */
  async createCollection(collection: string, config: CollectionConfig): Promise<void> {
    this.recordCall('createCollection', [collection, config])
    await this.maybeDelay()
    this.maybeThrow()

    if (this.collections.has(collection)) {
      throw new Error(`Collection '${collection}' already exists`)
    }

    this.collections.set(collection, {
      config,
      points: new Map(),
    })
  }

  /**
   * Delete a collection
   */
  async deleteCollection(collection: string): Promise<void> {
    this.recordCall('deleteCollection', [collection])
    await this.maybeDelay()
    this.maybeThrow()

    if (!this.collections.has(collection)) {
      throw new Error(`Collection '${collection}' does not exist`)
    }

    this.collections.delete(collection)
  }

  /**
   * Get collection information
   */
  async getCollectionInfo(collection: string): Promise<{
    points_count: number
    vector_dimensions?: number | Record<string, number>
    segments_count?: number
  }> {
    this.recordCall('getCollectionInfo', [collection])
    await this.maybeDelay()
    this.maybeThrow()

    const coll = this.getCollection(collection)

    return {
      points_count: coll.points.size,
      vector_dimensions: coll.config.dimensions,
      segments_count: 1,
    }
  }

  /**
   * Upsert points into collection
   */
  async upsert(collection: string, points: VectorPoint<ChunkPayload>[]): Promise<void> {
    this.recordCall('upsert', [collection, points])
    await this.maybeDelay()
    this.maybeThrow()

    const coll = this.getCollection(collection)

    for (const point of points) {
      coll.points.set(point.id, point)
    }
  }

  /**
   * Search for similar vectors
   */
  async search(collection: string, params: SearchParams): Promise<SearchResult<ChunkPayload>[]> {
    this.recordCall('search', [collection, params])
    await this.maybeDelay()
    this.maybeThrow()

    const coll = this.getCollection(collection)
    const vectorName = params.vectorName || 'text'
    const results: SearchResult<ChunkPayload>[] = []

    // Calculate similarity for all points
    for (const [id, point] of coll.points) {
      // Apply filter if provided
      if (params.filter && !this.matchesFilter(point.payload, params.filter)) {
        continue
      }

      // Get named vector
      const pointVector = point.vector[vectorName]
      if (!pointVector) continue

      // Calculate similarity
      const score = this.calculateSimilarity(params.vector, pointVector)

      // Apply score threshold
      if (params.scoreThreshold && score < params.scoreThreshold) {
        continue
      }

      results.push({
        id,
        score,
        payload: point.payload,
        vector: params.withVector ? pointVector : undefined,
      })
    }

    // Sort by score descending
    results.sort((a, b) => b.score - a.score)

    // Apply limit
    return results.slice(0, params.limit)
  }

  /**
   * Retrieve specific points by ID
   */
  async retrieve(collection: string, ids: string[]): Promise<VectorPoint<ChunkPayload>[]> {
    this.recordCall('retrieve', [collection, ids])
    await this.maybeDelay()
    this.maybeThrow()

    const coll = this.getCollection(collection)
    const points: VectorPoint<ChunkPayload>[] = []

    for (const id of ids) {
      const point = coll.points.get(id)
      if (point) {
        points.push(point)
      }
    }

    return points
  }

  /**
   * Delete points by ID
   */
  async delete(collection: string, ids: string[]): Promise<void> {
    this.recordCall('delete', [collection, ids])
    await this.maybeDelay()
    this.maybeThrow()

    const coll = this.getCollection(collection)

    for (const id of ids) {
      coll.points.delete(id)
    }
  }

  /**
   * Scroll through all points
   */
  async scroll(collection: string, options: ScrollOptions): Promise<ScrollResult<ChunkPayload>> {
    this.recordCall('scroll', [collection, options])
    await this.maybeDelay()
    this.maybeThrow()

    const coll = this.getCollection(collection)
    const allPoints = Array.from(coll.points.values())

    // Apply filter
    const filtered = options.filter
      ? allPoints.filter((point) => this.matchesFilter(point.payload, options.filter!))
      : allPoints

    // Parse offset
    const offset = options.offset ? parseInt(options.offset, 10) : 0

    // Slice for pagination
    const points = filtered.slice(offset, offset + options.limit)
    const nextOffset =
      offset + options.limit < filtered.length ? String(offset + options.limit) : null

    return {
      points,
      nextOffset,
    }
  }

  /**
   * Update payload for points
   */
  async setPayload(
    collection: string,
    ids: string[],
    payload: Partial<ChunkPayload>
  ): Promise<void> {
    this.recordCall('setPayload', [collection, ids, payload])
    await this.maybeDelay()
    this.maybeThrow()

    const coll = this.getCollection(collection)

    for (const id of ids) {
      const point = coll.points.get(id)
      if (point) {
        point.payload = { ...point.payload, ...payload }
      }
    }
  }

  /**
   * Create payload index (no-op for in-memory)
   */
  async createPayloadIndex(
    collection: string,
    config: {
      field_name: string
      field_schema: 'keyword' | 'integer' | 'float' | 'bool' | 'datetime'
    }
  ): Promise<void> {
    this.recordCall('createPayloadIndex', [collection, config])
    await this.maybeDelay()
    // No-op for in-memory mock
  }

  // === Helper Methods ===

  /**
   * Get collection or throw error
   */
  private getCollection(name: string): Collection {
    const coll = this.collections.get(name)
    if (!coll) {
      throw new Error(`Collection '${name}' does not exist`)
    }
    return coll
  }

  /**
   * Calculate similarity based on distance metric
   */
  private calculateSimilarity(a: number[], b: number[]): number {
    switch (this.distance) {
      case 'cosine':
        return cosineSimilarity(a, b)
      case 'dot': {
        let sum = 0
        for (let i = 0; i < a.length; i++) {
          sum += a[i]! * b[i]!
        }
        return sum
      }
      case 'euclidean': {
        let sum = 0
        for (let i = 0; i < a.length; i++) {
          const diff = a[i]! - b[i]!
          sum += diff * diff
        }
        return 1 / (1 + Math.sqrt(sum)) // Convert distance to similarity
      }
    }
  }

  /**
   * Check if payload matches filter
   */
  private matchesFilter(payload: ChunkPayload, filter: StorageFilter): boolean {
    // Must conditions (AND)
    if (filter.must) {
      for (const condition of filter.must) {
        if (!this.matchesCondition(payload, condition)) {
          return false
        }
      }
    }

    // Must not conditions (NOT)
    if (filter.must_not) {
      for (const condition of filter.must_not) {
        if (this.matchesCondition(payload, condition)) {
          return false
        }
      }
    }

    // Should conditions (OR) - at least one must match
    if (filter.should && filter.should.length > 0) {
      const anyMatch = filter.should.some((condition) => this.matchesCondition(payload, condition))
      if (!anyMatch) {
        return false
      }
    }

    return true
  }

  /**
   * Check if payload matches a single condition
   */
  private matchesCondition(payload: any, condition: any): boolean {
    if ('key' in condition) {
      const value = payload[condition.key]

      if ('match' in condition) {
        if ('value' in condition.match) {
          return value === condition.match.value
        }
        if ('any' in condition.match) {
          return condition.match.any.includes(value)
        }
        if ('except' in condition.match) {
          return !condition.match.except.includes(value)
        }
      }

      if ('range' in condition) {
        const { gte, lte, gt, lt } = condition.range
        if (gte !== undefined && value < gte) return false
        if (lte !== undefined && value > lte) return false
        if (gt !== undefined && value <= gt) return false
        if (lt !== undefined && value >= lt) return false
        return true
      }
    }

    // Handle special condition types without 'key' field
    if ('has_id' in condition) {
      // has_id: Check if point ID is in array
      return condition.has_id.includes((payload as any).id || '')
    }

    if ('is_null' in condition) {
      // is_null: Check if field is null/undefined
      const value = payload[condition.is_null]
      return value === null || value === undefined
    }

    if ('is_empty' in condition) {
      // is_empty: Check if array/string field is empty
      const value = payload[condition.is_empty]
      if (Array.isArray(value)) return value.length === 0
      if (typeof value === 'string') return value === ''
      return false
    }

    return false
  }

  /**
   * Maybe delay based on config
   */
  private async maybeDelay(): Promise<void> {
    if (this.config.delay) {
      await new Promise((resolve) => setTimeout(resolve, this.config.delay))
    }
  }

  /**
   * Maybe throw error based on config
   */
  private maybeThrow(): void {
    if (this.config.throwError) {
      throw this.config.throwError
    }
  }

  /**
   * Record method call
   */
  private recordCall(method: string, args: any[]): void {
    this.calls.push({
      method,
      args,
      timestamp: Date.now(),
    })
  }

  // === Test Utilities ===

  /**
   * Get all recorded calls
   */
  getCalls(): Array<{ method: string; args: any[]; timestamp: number }> {
    return [...this.calls]
  }

  /**
   * Get calls for specific method
   */
  getCallsFor(method: string): Array<{ method: string; args: any[]; timestamp: number }> {
    return this.calls.filter((call) => call.method === method)
  }

  /**
   * Get call count
   */
  getCallCount(method?: string): number {
    if (method) {
      return this.calls.filter((call) => call.method === method).length
    }
    return this.calls.length
  }

  /**
   * Clear call history
   */
  clearCalls(): void {
    this.calls = []
  }

  /**
   * Set error to throw
   */
  setError(error: Error): void {
    this.config.throwError = error
  }

  /**
   * Clear error
   */
  clearError(): void {
    this.config.throwError = undefined
  }

  /**
   * Set delay
   */
  setDelay(ms: number): void {
    this.config.delay = ms
  }

  /**
   * Get all points in a collection (test utility)
   */
  getAllPoints(collection: string): VectorPoint<ChunkPayload>[] {
    const coll = this.collections.get(collection)
    if (!coll) return []
    return Array.from(coll.points.values())
  }

  /**
   * Clear all collections
   */
  clearAll(): void {
    this.collections.clear()
    this.calls = []
  }
}

/**
 * Create a mock storage backend
 */
export function createMockStorageBackend(config?: MockStorageConfig): MockStorageBackend {
  return new MockStorageBackend(config)
}
