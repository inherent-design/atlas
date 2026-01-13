/**
 * Full-Text Search Backend Interface and Implementations
 *
 * Provides keyword search, typo tolerance, and faceted filtering
 * using Meilisearch or compatible search engines.
 *
 * @example Meilisearch Backend
 * ```typescript
 * const backend = new MeilisearchBackend({
 *   url: 'http://localhost:7700',
 *   masterKey: 'your-master-key',
 *   indexName: 'atlas_chunks',
 * })
 *
 * await backend.createIndex()
 * await backend.index([
 *   {
 *     id: 'chunk-1',
 *     original_text: 'User authentication with JWT tokens',
 *     file_path: '/docs/auth.md',
 *     file_name: 'auth.md',
 *     qntm_keys: ['@auth ~ jwt', '@security ~ tokens'],
 *     file_type: '.md',
 *     consolidation_level: 0,
 *   },
 * ])
 *
 * const results = await backend.search({
 *   query: 'authentication',
 *   limit: 10,
 * })
 * ```
 */

import { MeiliSearch, Index, type Task, ErrorStatusCode } from 'meilisearch'
import { createLogger } from '../../../shared/logger.js'
import type { MeilisearchConfig } from '../../../shared/config.schema.js'

const logger = createLogger('storage:fulltext')

// ============================================
// Full-Text Document Schema
// ============================================

/**
 * Document indexed for full-text search
 *
 * Maps ChunkPayload to search-optimized schema.
 * Includes filterable metadata and searchable text.
 */
export interface FullTextDocument {
  /** Unique document ID (matches chunk ID) */
  id: string
  /** Original chunk text (searchable) */
  original_text: string
  /** File path (searchable + filterable) */
  file_path: string
  /** File name (searchable) */
  file_name: string
  /** QNTM semantic keys (searchable) */
  qntm_keys: string[]

  // Filterable fields
  /** File extension (e.g., '.ts', '.md') */
  file_type?: string
  /** Consolidation level (0-4) */
  consolidation_level?: number
  /** Content type classification */
  content_type?: string
  /** ISO 8601 creation timestamp */
  created_at?: string
  /** Importance classification */
  importance?: string
  /** Memory type classification */
  memory_type?: string
}

// ============================================
// Search Parameters
// ============================================

/**
 * Full-text search parameters
 */
export interface FullTextSearchParams {
  /** Search query string */
  query: string
  /** Maximum results to return (default: 20) */
  limit?: number
  /** Filter expression (Meilisearch syntax) */
  filter?: string | string[]
  /** Attributes to retrieve (default: all) */
  attributesToRetrieve?: string[]
  /** Attributes to highlight (default: ['original_text']) */
  attributesToHighlight?: string[]
  /** Highlight pre-tag (default: '<em>') */
  highlightPreTag?: string
  /** Highlight post-tag (default: '</em>') */
  highlightPostTag?: string
}

/**
 * Search result from full-text backend
 */
export interface FullTextSearchResult {
  /** Document ID */
  id: string
  /** Original text (with highlights if enabled) */
  original_text: string
  /** File path */
  file_path: string
  /** Relevance score (0-1, normalized from Meilisearch ranking) */
  score: number
  /** Highlighted text snippets */
  _formatted?: Record<string, string>
}

/**
 * Index statistics
 */
export interface IndexStats {
  /** Total documents indexed */
  numberOfDocuments: number
  /** Is indexing in progress */
  isIndexing: boolean
  /** Field distribution (field name → document count) */
  fieldDistribution?: Record<string, number>
}

// ============================================
// Full-Text Backend Interface
// ============================================

/**
 * Full-text search backend interface
 *
 * Provides keyword search, typo tolerance, and faceted filtering.
 * Implementations: Meilisearch, Elasticsearch, etc.
 */
export interface FullTextBackend {
  // ============================================
  // Indexing Operations
  // ============================================

  /**
   * Index multiple documents (batch operation)
   *
   * @param documents - Documents to index
   * @throws Error if indexing fails
   *
   * @example
   * ```typescript
   * await backend.index([
   *   { id: '1', original_text: 'foo', file_path: '/a.md', ... },
   *   { id: '2', original_text: 'bar', file_path: '/b.md', ... },
   * ])
   * ```
   */
  index(documents: FullTextDocument[]): Promise<void>

  /**
   * Update a single document
   *
   * @param id - Document ID
   * @param document - Partial document update
   * @throws Error if update fails
   *
   * @example
   * ```typescript
   * await backend.updateDocument('chunk-1', {
   *   consolidation_level: 1,
   *   importance: 'high',
   * })
   * ```
   */
  updateDocument(id: string, document: Partial<FullTextDocument>): Promise<void>

  /**
   * Delete a document by ID
   *
   * @param id - Document ID
   * @throws Error if deletion fails
   *
   * @example
   * ```typescript
   * await backend.deleteDocument('chunk-1')
   * ```
   */
  deleteDocument(id: string): Promise<void>

  // ============================================
  // Search Operations
  // ============================================

  /**
   * Search for documents
   *
   * @param params - Search parameters (query, filters, limit)
   * @returns Array of search results sorted by relevance
   *
   * @example
   * ```typescript
   * const results = await backend.search({
   *   query: 'authentication',
   *   limit: 10,
   *   filter: 'file_type = .ts',
   * })
   * ```
   */
  search(params: FullTextSearchParams): Promise<FullTextSearchResult[]>

  // ============================================
  // Index Management
  // ============================================

  /**
   * Create search index (idempotent)
   *
   * @throws Error if index creation fails
   *
   * @example
   * ```typescript
   * await backend.createIndex()
   * ```
   */
  createIndex(): Promise<void>

  /**
   * Delete search index
   *
   * @throws Error if index deletion fails
   *
   * @example
   * ```typescript
   * await backend.deleteIndex()
   * ```
   */
  deleteIndex(): Promise<void>

  /**
   * Get index statistics
   *
   * @returns Index stats (document count, size, field distribution)
   *
   * @example
   * ```typescript
   * const stats = await backend.getIndexStats()
   * console.log(`Indexed: ${stats.numberOfDocuments} documents`)
   * ```
   */
  getIndexStats(): Promise<IndexStats>

  // ============================================
  // Health Check
  // ============================================

  /**
   * Health check (verify connection)
   *
   * @throws Error if unhealthy
   *
   * @example
   * ```typescript
   * await backend.healthCheck()
   * ```
   */
  healthCheck(): Promise<void>
}

// ============================================
// Meilisearch Backend Implementation
// ============================================

/**
 * Meilisearch full-text search backend
 *
 * Features:
 * - 7× faster indexing than Elasticsearch
 * - Typo tolerance (up to 2 typos)
 * - Prefix matching
 * - Faceted filtering
 * - <50ms query latency
 *
 * Architecture:
 * - Uses Meilisearch npm package
 * - Configurable searchable/filterable attributes
 * - Configurable ranking rules
 * - Batch indexing (up to 1000 documents)
 *
 * @example
 * ```typescript
 * const backend = new MeilisearchBackend({
 *   url: 'http://localhost:7700',
 *   masterKey: 'atlas_dev_master_key',
 *   indexName: 'atlas_chunks',
 * })
 *
 * await backend.createIndex()
 * await backend.index(documents)
 * const results = await backend.search({ query: 'auth' })
 * ```
 */
export class MeilisearchBackend implements FullTextBackend {
  private client: MeiliSearch
  private indexName: string
  private indexInstance: Index | null = null

  // Configuration
  private searchableAttributes: string[]
  private filterableAttributes: string[]
  private rankingRules: string[]

  constructor(config: MeilisearchConfig) {
    const url = config.url ?? 'http://localhost:7700'
    const masterKey = config.masterKey
    this.indexName = config.indexName ?? 'atlas_chunks'

    if (!masterKey) {
      throw new Error('Meilisearch masterKey is required in config.storage.meilisearch')
    }

    this.client = new MeiliSearch({ host: url, apiKey: masterKey })

    // Configuration from schema (with defaults)
    this.searchableAttributes = config.searchableAttributes ?? [
      'original_text',
      'file_path',
      'qntm_keys',
    ]

    this.filterableAttributes = config.filterableAttributes ?? [
      'file_type',
      'consolidation_level',
      'content_type',
      'created_at',
      'importance',
      'memory_type',
    ]

    this.rankingRules = config.rankingRules ?? [
      'words',
      'typo',
      'proximity',
      'attribute',
      'sort',
      'exactness',
    ]

    logger.debug('MeilisearchBackend initialized', {
      url,
      indexName: this.indexName,
      searchableAttributes: this.searchableAttributes,
      filterableAttributes: this.filterableAttributes,
    })
  }

  // ============================================
  // Index Management
  // ============================================

  /**
   * Get or create index
   */
  private async getIndex(): Promise<Index> {
    if (this.indexInstance) {
      return this.indexInstance
    }

    try {
      this.indexInstance = this.client.index(this.indexName)
      // Verify index exists by fetching stats
      await this.indexInstance.getStats()
      logger.debug('Connected to existing index', { indexName: this.indexName })
      return this.indexInstance
    } catch (error: any) {
      if (error.code === ErrorStatusCode.INDEX_NOT_FOUND) {
        // Index doesn't exist - will be created by createIndex()
        logger.debug('Index not found, will create on first index()', { indexName: this.indexName })
        this.indexInstance = this.client.index(this.indexName)
        return this.indexInstance
      }
      throw error
    }
  }

  async createIndex(): Promise<void> {
    try {
      // Check if index already exists first
      try {
        const index = await this.getIndex()
        await index.getStats()
        logger.debug('Index already exists, updating settings', { indexName: this.indexName })

        // Update settings (in case they changed)
        await index
          .updateSettings({
            searchableAttributes: this.searchableAttributes,
            filterableAttributes: this.filterableAttributes,
            rankingRules: this.rankingRules,
          })
          .waitTask({ timeout: 30000, interval: 100 })

        logger.info('Index settings configured', {
          indexName: this.indexName,
          searchableAttributes: this.searchableAttributes,
          filterableAttributes: this.filterableAttributes,
          rankingRules: this.rankingRules,
        })
        return
      } catch (checkError: any) {
        if (checkError.code !== ErrorStatusCode.INDEX_NOT_FOUND) {
          throw checkError
        }
        // Index doesn't exist, proceed to create it
        logger.debug('Index not found, creating new index', { indexName: this.indexName })
      }

      // Create index (only if it doesn't exist)
      await this.client
        .createIndex(this.indexName, { primaryKey: 'id' })
        .waitTask({ timeout: 30000, interval: 100 })

      logger.info('Index created', { indexName: this.indexName })

      // Get index reference
      const index = await this.getIndex()

      // Update settings (searchable attributes, filterable attributes, ranking rules)
      await index
        .updateSettings({
          searchableAttributes: this.searchableAttributes,
          filterableAttributes: this.filterableAttributes,
          rankingRules: this.rankingRules,
        })
        .waitTask({ timeout: 30000, interval: 100 })

      logger.info('Index settings configured', {
        indexName: this.indexName,
        searchableAttributes: this.searchableAttributes,
        filterableAttributes: this.filterableAttributes,
        rankingRules: this.rankingRules,
      })
    } catch (error: any) {
      logger.error('Failed to create index', { error: error.message, indexName: this.indexName })
      throw new Error(`Failed to create Meilisearch index: ${error.message}`)
    }
  }

  async deleteIndex(): Promise<void> {
    try {
      await this.client.deleteIndex(this.indexName).waitTask({ timeout: 30000, interval: 100 })

      this.indexInstance = null
      logger.info('Index deleted', { indexName: this.indexName })
    } catch (error: any) {
      if (error.code === ErrorStatusCode.INDEX_NOT_FOUND) {
        logger.debug('Index already deleted', { indexName: this.indexName })
        return
      }

      logger.error('Failed to delete index', { error: error.message, indexName: this.indexName })
      throw new Error(`Failed to delete Meilisearch index: ${error.message}`)
    }
  }

  async getIndexStats(): Promise<IndexStats> {
    try {
      const index = await this.getIndex()
      const stats = await index.getStats()

      return {
        numberOfDocuments: stats.numberOfDocuments,
        isIndexing: stats.isIndexing,
        fieldDistribution: stats.fieldDistribution,
      }
    } catch (error: any) {
      if (error.code === ErrorStatusCode.INDEX_NOT_FOUND) {
        return {
          numberOfDocuments: 0,
          isIndexing: false,
        }
      }

      logger.error('Failed to get index stats', { error: error.message, indexName: this.indexName })
      throw new Error(`Failed to get Meilisearch index stats: ${error.message}`)
    }
  }

  // ============================================
  // Indexing Operations
  // ============================================

  async index(documents: FullTextDocument[]): Promise<void> {
    if (documents.length === 0) {
      logger.debug('No documents to index')
      return
    }

    try {
      // Ensure index exists with proper settings (idempotent)
      await this.createIndex()

      // Get index reference
      const index = await this.getIndex()

      // Batch size limit: 1000 documents per request
      const batchSize = 1000
      const batches = []

      for (let i = 0; i < documents.length; i += batchSize) {
        batches.push(documents.slice(i, i + batchSize))
      }

      logger.debug('Indexing documents', { total: documents.length, batches: batches.length })

      // Process batches sequentially (Meilisearch handles queueing)
      for (const batch of batches) {
        const task = await index.addDocuments(batch).waitTask({ timeout: 30000, interval: 100 })
        logger.debug('Batch indexed', { count: batch.length, taskUid: task.uid })
      }

      logger.info('Documents indexed successfully', { count: documents.length })
    } catch (error: any) {
      logger.error('Failed to index documents', { error: error.message, count: documents.length })
      throw new Error(`Failed to index documents in Meilisearch: ${error.message}`)
    }
  }

  async updateDocument(id: string, document: Partial<FullTextDocument>): Promise<void> {
    try {
      const index = await this.getIndex()

      // Meilisearch requires full document ID for updates
      const updateDoc = { id, ...document }

      const task = await index
        .updateDocuments([updateDoc])
        .waitTask({ timeout: 30000, interval: 100 })

      logger.debug('Document updated', { id, taskUid: task.uid })
    } catch (error: any) {
      logger.error('Failed to update document', { error: error.message, id })
      throw new Error(`Failed to update document in Meilisearch: ${error.message}`)
    }
  }

  async deleteDocument(id: string): Promise<void> {
    try {
      const index = await this.getIndex()

      const task = await index.deleteDocument(id).waitTask({ timeout: 30000, interval: 100 })

      logger.debug('Document deleted', { id, taskUid: task.uid })
    } catch (error: any) {
      logger.error('Failed to delete document', { error: error.message, id })
      throw new Error(`Failed to delete document from Meilisearch: ${error.message}`)
    }
  }

  // ============================================
  // Search Operations
  // ============================================

  async search(params: FullTextSearchParams): Promise<FullTextSearchResult[]> {
    try {
      const index = await this.getIndex()

      const results = await index.search(params.query, {
        limit: params.limit ?? 20,
        filter: params.filter,
        attributesToRetrieve: params.attributesToRetrieve ?? ['*'],
        attributesToHighlight: params.attributesToHighlight ?? ['original_text'],
        highlightPreTag: params.highlightPreTag ?? '<em>',
        highlightPostTag: params.highlightPostTag ?? '</em>',
      })

      logger.debug('Search completed', {
        query: params.query,
        hits: results.hits.length,
        processingTimeMs: results.processingTimeMs,
      })

      // Map Meilisearch results to FullTextSearchResult
      return results.hits.map((hit: any, index: number) => ({
        id: hit.id,
        original_text: hit.original_text,
        file_path: hit.file_path,
        // Normalize score: Meilisearch ranks by relevance (first = best)
        // Map position to score: 1.0 for first result, decaying
        score: 1.0 - index / (results.hits.length + 1),
        _formatted: hit._formatted,
      }))
    } catch (error: any) {
      logger.error('Search failed', { error: error.message, query: params.query })
      throw new Error(`Meilisearch search failed: ${error.message}`)
    }
  }

  // ============================================
  // Health Check
  // ============================================

  async healthCheck(): Promise<void> {
    try {
      // Check if server is reachable
      const health = await this.client.health()

      if (health.status !== 'available') {
        throw new Error(`Meilisearch status: ${health.status}`)
      }

      logger.debug('Health check passed', { status: health.status })
    } catch (error: any) {
      logger.error('Health check failed', { error: error.message })
      throw new Error(`Meilisearch health check failed: ${error.message}`)
    }
  }
}
