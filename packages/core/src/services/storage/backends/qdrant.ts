/**
 * Qdrant Storage Backend
 *
 * Implements StorageBackend + CanStoreVectors for Qdrant vector database.
 * Wraps QdrantClient with capability-first interface.
 */

import type { QdrantClient as QdrantClientType } from '@qdrant/js-client-rest'
import { getQdrantClient } from '../client.js'
import { createLogger } from '../../../shared/logger.js'
import type {
  StorageBackend,
  StorageCapability,
  CanStoreVectors,
  VectorPoint,
  SearchParams,
  SearchResult,
  ScrollOptions,
  ScrollResult,
  CollectionConfig,
} from '../types.js'
import type { ChunkPayload } from '../../../shared/types.js'
import type { StorageFilter, FilterCondition } from '../types.js'

const log = createLogger('storage:qdrant')

/**
 * Translate StorageFilter to Qdrant SDK filter format.
 * Handles is_null/is_empty conditions that need special structure.
 */
function translateFilter(filter: StorageFilter | undefined): Record<string, FilterCondition[]> | undefined {
  if (!filter) return undefined

  const translateCondition = (cond: FilterCondition): FilterCondition => {
    // is_null condition → { is_null: { key: "field" } }
    if ('is_null' in cond) {
      return { is_null: { key: cond.is_null } } as FilterCondition
    }
    // is_empty condition → { is_empty: { key: "field" } }
    if ('is_empty' in cond) {
      return { is_empty: { key: cond.is_empty } } as FilterCondition
    }
    // has_id, match, range conditions → pass through (already correct format)
    return cond
  }

  // Only include non-empty filter arrays to avoid JSON null serialization
  const result: Record<string, FilterCondition[]> = {}

  if (filter.must?.length) {
    result.must = filter.must.map(translateCondition)
  }
  if (filter.must_not?.length) {
    result.must_not = filter.must_not.map(translateCondition)
  }
  if (filter.should?.length) {
    result.should = filter.should.map(translateCondition)
  }

  return Object.keys(result).length > 0 ? result : undefined
}

/**
 * Qdrant backend implementation.
 * Provides vector storage via Qdrant REST API.
 */
export class QdrantBackend implements StorageBackend, CanStoreVectors {
  readonly name = 'qdrant'
  readonly capabilities: ReadonlySet<StorageCapability> = new Set(['vector-storage'])
  readonly dimensions: number
  readonly distance: 'cosine' | 'dot' | 'euclidean'
  readonly latency = 'fast' as const

  private client: QdrantClientType

  constructor(config: { dimensions: number; distance?: 'cosine' | 'dot' | 'euclidean' }) {
    this.dimensions = config.dimensions
    this.distance = config.distance ?? 'dot'
    this.client = getQdrantClient()
  }

  /**
   * Check if Qdrant is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      await this.client.getCollections()
      return true
    } catch (error) {
      log.warn('Qdrant availability check failed', { error: (error as Error).message })
      return false
    }
  }

  /**
   * Check if backend supports a capability
   */
  supports(cap: StorageCapability): boolean {
    return this.capabilities.has(cap)
  }

  // ============================================
  // Collection Management
  // ============================================

  async collectionExists(collection: string): Promise<boolean> {
    try {
      await this.client.getCollection(collection)
      return true
    } catch {
      return false
    }
  }

  async createCollection(collection: string, config: CollectionConfig | any): Promise<void> {
    // Support both old single-vector and new named-vector configs
    // If config has 'dimensions', it's old format - convert to named vector
    // If config has 'vectors' object, use directly (named vector format)

    let qdrantConfig: any

    if ('dimensions' in config) {
      // Old format: single vector (backward compatibility)
      const qdrantDistance =
        config.distance === 'cosine' ? 'Cosine' : config.distance === 'euclidean' ? 'Euclid' : 'Dot'

      qdrantConfig = {
        vectors: {
          size: config.dimensions,
          distance: qdrantDistance,
          on_disk: config.onDisk ?? true,
        },
      }

      // Add HNSW config if specified
      if (config.hnswM || config.hnswEfConstruct) {
        qdrantConfig.vectors.hnsw_config = {
          m: config.hnswM ?? 16,
          ef_construct: config.hnswEfConstruct ?? 100,
        }
      }

      // Add quantization if specified
      if (config.quantization === 'int8') {
        qdrantConfig.vectors.quantization_config = {
          scalar: {
            type: 'int8',
            quantile: 0.99,
            always_ram: true,
          },
        }
      } else if (config.quantization === 'float16') {
        qdrantConfig.vectors.quantization_config = {
          scalar: {
            type: 'float16',
          },
        }
      }
    } else {
      // New format: named vectors (from QDRANT_COLLECTION_CONFIG)
      qdrantConfig = config
    }

    await this.client.createCollection(collection, qdrantConfig)
    log.info('Collection created', { collection })
  }

  async deleteCollection(collection: string): Promise<void> {
    await this.client.deleteCollection(collection)
    log.info('Collection deleted', { collection })
  }

  async getCollectionInfo(collection: string): Promise<{
    points_count: number
    vector_dimensions?: Record<string, number>
  }> {
    const info = await this.client.getCollection(collection)

    // Extract dimensions from named vectors config
    const vectorDimensions: Record<string, number> = {}
    if (info.config?.params?.vectors && typeof info.config.params.vectors === 'object') {
      for (const [name, config] of Object.entries(info.config.params.vectors)) {
        if (config && typeof config === 'object' && 'size' in config) {
          vectorDimensions[name] = (config as any).size
        }
      }
    }

    return {
      points_count: info.points_count ?? 0,
      vector_dimensions: Object.keys(vectorDimensions).length > 0 ? vectorDimensions : undefined,
    }
  }

  async createPayloadIndex(
    collection: string,
    config: {
      field_name: string
      field_schema: 'keyword' | 'integer' | 'float' | 'bool' | 'datetime'
    }
  ): Promise<void> {
    await this.client.createPayloadIndex(collection, {
      field_name: config.field_name,
      field_schema: config.field_schema,
      wait: true,
    })
    log.debug('Payload index created', { collection, field: config.field_name })
  }

  // ============================================
  // Point Operations
  // ============================================

  async upsert(collection: string, points: VectorPoint[]): Promise<void> {
    const qdrantPoints = points.map((p) => ({
      id: p.id,
      vector: p.vector,
      payload: p.payload,
    }))

    await this.client.upsert(collection, {
      wait: true,
      points: qdrantPoints,
    })

    log.trace('Points upserted', { collection, count: points.length })
  }

  async search(collection: string, params: SearchParams): Promise<SearchResult[]> {
    const vectorName = params.vectorName ?? 'text' // Default to text vector

    const response = await this.client.search(collection, {
      vector: {
        name: vectorName,
        vector: params.vector,
      },
      limit: params.limit,
      filter: translateFilter(params.filter),
      score_threshold: params.scoreThreshold,
      with_payload: params.withPayload ?? true,
      with_vector: params.withVector ?? false,
    })

    return response.map((hit: any) => ({
      id: hit.id as string,
      score: hit.score,
      payload: hit.payload as ChunkPayload,
      vector: hit.vector as number[] | undefined,
    }))
  }

  async retrieve(collection: string, ids: string[]): Promise<VectorPoint[]> {
    const response = await this.client.retrieve(collection, {
      ids,
      with_payload: true,
      with_vector: true,
    })

    return response.map((point: any) => ({
      id: point.id as string,
      vector: point.vector as any, // NamedVectors or number[] (backward compatible)
      payload: point.payload as ChunkPayload,
    }))
  }

  async delete(collection: string, ids: string[]): Promise<void> {
    await this.client.delete(collection, {
      wait: true,
      points: ids,
    })

    log.trace('Points deleted', { collection, count: ids.length })
  }

  async scroll(collection: string, options: ScrollOptions): Promise<ScrollResult> {
    const response = await this.client.scroll(collection, {
      limit: options.limit,
      offset: options.offset ?? undefined,
      filter: translateFilter(options.filter),
      with_payload: options.withPayload ?? true,
      with_vector: options.withVector ?? false,
    })

    return {
      points: response.points.map((p: any) => ({
        id: p.id as string,
        vector: p.vector as any, // NamedVectors or number[] (backward compatible)
        payload: p.payload as ChunkPayload,
      })),
      nextOffset: (response.next_page_offset as string | null) ?? null,
    }
  }

  async setPayload(
    collection: string,
    ids: string[],
    payload: Partial<ChunkPayload>
  ): Promise<void> {
    await this.client.setPayload(collection, {
      wait: true,
      points: ids,
      payload: payload as Record<string, any>,
    })

    log.trace('Payload updated', { collection, count: ids.length })
  }
}
