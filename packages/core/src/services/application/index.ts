/**
 * Application Service - Unified Entry Point
 *
 * Single entry point for all Atlas operations.
 * Both CLI and daemon delegate to this service.
 *
 * Design principles:
 * - Pure functions: No hidden state, all dependencies injected
 * - Async by default: All methods return Promises
 * - Event-driven: Optional emit() for progress updates
 * - Type-safe: Zod-validated parameters and results
 */

import { createLogger } from '../../shared/logger.js'
import type {
  ApplicationService,
  IngestParams,
  IngestResult,
  SearchParams,
  SearchResult,
  ConsolidateParams,
  ConsolidateResult,
  TimelineParams,
  QNTMGenerateParams,
  QNTMGenerateResult,
  HealthStatus,
  StatusResult,
} from '../../shared/types.js'
import type { AtlasConfig } from '../../shared/config.schema.js'
import { getConfig, applyRuntimeOverrides } from '../../shared/config.loader.js'
import { initializeLLMBackends } from '../llm/index.js'
import { initializeEmbeddingBackends } from '../embedding/index.js'
import { getStorageService } from '../storage/index.js'
import { OLLAMA_URL } from '../../shared/config.js'
import { getPrimaryCollectionName } from '../../shared/utils.js'

const logger = createLogger('application')

/**
 * Default ApplicationService implementation
 *
 * Unified entry point for all Atlas operations.
 * Both CLI and daemon delegate to this service.
 */
export class DefaultApplicationService implements ApplicationService {
  private config: AtlasConfig
  private initialized: boolean = false
  private consolidationState = {
    chunksIngested: 0,
    threshold: 500,
  }
  private fileWatchers: Map<string, any> = new Map()

  constructor(config?: AtlasConfig) {
    this.config = config || getConfig()
    logger.info('ApplicationService created')
  }

  async initialize(): Promise<void> {
    if (this.initialized) {
      logger.debug('ApplicationService already initialized')
      return
    }

    logger.info('Initializing ApplicationService')

    try {
      // Initialize LLM backends
      initializeLLMBackends()
      logger.debug('LLM backends initialized')

      // Initialize embedding backends
      initializeEmbeddingBackends()
      logger.debug('Embedding backends initialized')

      // Initialize storage service (Qdrant)
      const storageService = getStorageService(this.config)
      logger.debug('Storage service initialized')

      this.initialized = true
      logger.info('ApplicationService initialized successfully')
    } catch (error) {
      logger.error('Failed to initialize ApplicationService', error as Error)
      throw new Error(`ApplicationService initialization failed: ${(error as Error).message}`)
    }
  }

  async shutdown(): Promise<void> {
    if (!this.initialized) {
      logger.debug('ApplicationService not initialized, nothing to shut down')
      return
    }

    logger.info('Shutting down ApplicationService')

    try {
      // Stop all file watchers
      await this.stopWatching()

      // Shutdown storage service (closes all backend connections)
      const storageService = getStorageService(this.config)
      await storageService.shutdown()

      // Mark as uninitialized
      this.initialized = false
      logger.info('ApplicationService shut down successfully')
    } catch (error) {
      logger.error('Error during ApplicationService shutdown', error as Error)
      throw new Error(`ApplicationService shutdown failed: ${(error as Error).message}`)
    }
  }

  private async stopWatching(path?: string): Promise<void> {
    if (path) {
      const watcher = this.fileWatchers.get(path)
      if (watcher) {
        await watcher.close()
        this.fileWatchers.delete(path)
        logger.info('Stopped watching path', { path })
      }
    } else {
      // Stop all watchers
      for (const [watchPath, watcher] of this.fileWatchers) {
        await watcher.close()
        logger.info('Stopped watching path', { path: watchPath })
      }
      this.fileWatchers.clear()
    }
  }

  async ingest(params: IngestParams): Promise<IngestResult> {
    this.ensureInitialized()
    logger.info('Starting ingest')

    try {
      // Delegate to domain/ingest
      const { ingest } = await import('../../domain/ingest')
      const { computeRootDir } = await import('../../shared/utils')

      const result = await ingest({
        paths: params.paths,
        recursive: params.recursive ?? false,
        rootDir: params.rootDir || computeRootDir(params.paths),
        verbose: params.verbose ?? false,
        watch: params.watch ?? false,
        emit: params.emit,
      })

      logger.info('Ingest complete', {
        filesProcessed: result.filesProcessed,
        chunksStored: result.chunksStored,
        errors: result.errors.length,
      })

      // Track consolidation stats (always)
      this.consolidationState.chunksIngested += result.chunksStored

      // Auto-consolidate if allowed and threshold reached
      const threshold = params.consolidationThreshold || this.consolidationState.threshold
      const allowConsolidation = params.allowConsolidation ?? true // Default: true

      if (allowConsolidation && this.consolidationState.chunksIngested >= threshold) {
        logger.info('Auto-triggering consolidation (threshold reached)', {
          chunksIngested: this.consolidationState.chunksIngested,
          threshold,
        })

        await this.consolidate({ dryRun: false })
        this.consolidationState.chunksIngested = 0
      }

      // Start watching if requested
      if (params.watch) {
        await this.startWatching(params.paths, params.recursive ?? false)
      }

      return result
    } catch (error) {
      logger.error('Ingest failed', error as Error)
      throw new Error(`Ingest failed: ${(error as Error).message}`)
    }
  }

  private async startWatching(paths: string[], recursive: boolean): Promise<void> {
    const { watch } = await import('chokidar')
    const { join } = await import('path')

    for (const path of paths) {
      if (this.fileWatchers.has(path)) {
        logger.debug('Already watching path', { path })
        continue
      }

      logger.info('Starting file watcher', { path, recursive })
      const watcher = watch(path, { ignoreInitial: true })

      watcher.on('change', async (changedPath: string) => {
        logger.info('File changed, re-ingesting', { path: changedPath })
        try {
          await this.ingest({ paths: [changedPath], recursive: false })
        } catch (error) {
          logger.error('Failed to re-ingest changed file', error as Error)
        }
      })

      this.fileWatchers.set(path, watcher)
    }
  }

  async search(params: SearchParams): Promise<SearchResult[]> {
    this.ensureInitialized()
    logger.info('Starting search')

    try {
      // Delegate to domain/search
      const { search } = await import('../../domain/search')

      const results = await search({
        query: params.query,
        limit: params.limit,
        since: params.since,
        qntmKey: params.qntmKey,
        rerank: params.rerank ?? false,
        consolidationLevel: params.consolidationLevel,
        contentType: params.contentType,
        agentRole: params.agentRole,
        temperature: params.temperature,
        expandQuery: params.expandQuery ?? false,
        emit: params.emit,
      })

      logger.info('Search complete', { count: results.length, query: params.query })
      return results
    } catch (error) {
      logger.error('Search failed', error as Error)
      throw new Error(`Search failed: ${(error as Error).message}`)
    }
  }

  async consolidate(params: ConsolidateParams): Promise<ConsolidateResult> {
    this.ensureInitialized()
    logger.info('Starting consolidate')

    try {
      // Delegate to domain/consolidate
      const { consolidate } = await import('../../domain/consolidate')

      const domainResult = await consolidate({
        dryRun: params.dryRun ?? false,
        threshold: params.threshold,
        emit: params.emit,
      })

      // Map domain result to ApplicationService result type
      const result: ConsolidateResult = {
        consolidationsPerformed: domainResult.consolidated,
        chunksAbsorbed: domainResult.deleted,
        candidatesEvaluated: domainResult.candidatesFound,
      }

      logger.info('Consolidate complete', {
        consolidationsPerformed: result.consolidationsPerformed,
        chunksAbsorbed: result.chunksAbsorbed,
        candidatesEvaluated: result.candidatesEvaluated,
      })

      return result
    } catch (error) {
      logger.error('Consolidate failed', error as Error)
      throw new Error(`Consolidate failed: ${(error as Error).message}`)
    }
  }

  async timeline(params: TimelineParams): Promise<SearchResult[]> {
    this.ensureInitialized()
    logger.info('Starting timeline query')

    try {
      // Delegate to domain/search timeline function
      const { timeline } = await import('../../domain/search')

      const results = await timeline(params.since, params.limit)

      logger.info('Timeline query complete', { count: results.length, since: params.since })
      return results
    } catch (error) {
      logger.error('Timeline query failed', error as Error)
      throw new Error(`Timeline query failed: ${(error as Error).message}`)
    }
  }

  async health(): Promise<HealthStatus> {
    logger.debug('Checking health')

    const timestamp = new Date().toISOString()
    let overall: 'healthy' | 'degraded' | 'unhealthy' = 'unhealthy'

    const services: HealthStatus['services'] = {
      vector: { name: 'qdrant', status: 'unhealthy' },
      metadata: { name: 'metadata', status: 'unhealthy' },
      embedding: { total: 0, available: 0, backends: [] },
      llm: { total: 0, available: 0, backends: [] },
      reranker: { total: 0, available: 0, backends: [] },
    }

    try {
      // Check Qdrant
      try {
        const storageService = getStorageService(this.config)
        const storage = storageService.getVectorBackend()
        const exists = await storage.collectionExists(getPrimaryCollectionName())
        services.vector = {
          name: 'qdrant',
          status: exists ? 'healthy' : 'degraded',
        }
      } catch (error) {
        services.vector = {
          name: 'qdrant',
          status: 'unhealthy',
          error: (error as Error).message,
        }
      }

      // Check metadata backend (placeholder - always healthy for now)
      services.metadata = {
        name: 'metadata',
        status: 'healthy',
      }

      // Check embedding backends
      const embeddingBackends = [
        this.config.backends?.['text-embedding'],
        this.config.backends?.['code-embedding'],
        this.config.backends?.['contextualized-embedding'],
      ].filter((b): b is string => !!b)

      services.embedding = {
        total: embeddingBackends.length,
        available: embeddingBackends.length, // Assume all available
        backends: embeddingBackends.map((b) => ({
          name: b,
          status: 'healthy' as const,
        })),
      }

      // Check LLM backends
      const llmBackends = [
        this.config.backends?.['text-completion'],
        this.config.backends?.['json-completion'],
      ].filter((b): b is string => !!b)

      services.llm = {
        total: llmBackends.length,
        available: llmBackends.length, // Assume all available
        backends: llmBackends.map((b) => ({
          name: b,
          status: 'healthy' as const,
        })),
      }

      // Check reranker backends
      const rerankerBackends = [this.config.backends?.['reranking']].filter((b): b is string => !!b)

      services.reranker = {
        total: rerankerBackends.length,
        available: rerankerBackends.length,
        backends: rerankerBackends.map((b) => ({
          name: b,
          status: 'healthy' as const,
        })),
      }

      // Determine overall health
      const vectorHealthy = services.vector.status === 'healthy'
      const metadataHealthy = services.metadata.status === 'healthy'
      const embeddingHealthy = services.embedding.available > 0
      const llmHealthy = services.llm.available > 0

      if (vectorHealthy && metadataHealthy && embeddingHealthy && llmHealthy) {
        overall = 'healthy'
      } else if (vectorHealthy || metadataHealthy) {
        overall = 'degraded'
      } else {
        overall = 'unhealthy'
      }

      logger.debug('Health check complete', { overall })
      return { overall, timestamp, services }
    } catch (error) {
      logger.error('Health check failed', error as Error)
      return {
        overall: 'unhealthy',
        timestamp,
        services: {
          vector: { name: 'qdrant', status: 'unhealthy', error: 'Health check failed' },
          metadata: { name: 'metadata', status: 'unhealthy', error: 'Health check failed' },
          embedding: { total: 0, available: 0, backends: [] },
          llm: { total: 0, available: 0, backends: [] },
          reranker: { total: 0, available: 0, backends: [] },
        },
      }
    }
  }

  async status(): Promise<StatusResult> {
    logger.debug('Getting status')

    try {
      const storageService = getStorageService(this.config)
      const storage = storageService.getVectorBackend()

      // Get collection info
      const collectionInfo = await storage.getCollectionInfo(getPrimaryCollectionName())

      // Get unique embedding backends
      const embeddingBackends = [
        this.config.backends?.['text-embedding'],
        this.config.backends?.['code-embedding'],
        this.config.backends?.['contextualized-embedding'],
      ].filter((b): b is string => !!b)

      // Get unique LLM backends
      const llmBackends = [
        this.config.backends?.['text-completion'],
        this.config.backends?.['json-completion'],
      ].filter((b): b is string => !!b)

      // Get reranker backends
      const rerankerBackends = [this.config.backends?.['reranking']].filter((b): b is string => !!b)

      const result: StatusResult = {
        collection: {
          name: getPrimaryCollectionName(),
          totalChunks: collectionInfo.points_count || 0,
          totalFiles: 0, // TODO: Get from metadata backend
          totalQNTMKeys: 0, // TODO: Get from metadata backend
          avgChunkSize: 0, // TODO: Calculate from metadata
        },
        storage: {
          metadata: 'postgresql', // PostgreSQL is now required
          cache: this.config.storage?.cache || 'none',
          fulltext: this.config.storage?.fulltext || 'none',
          analytics: this.config.storage?.analytics || 'none',
        },
        backends: {
          embedding: [...new Set(embeddingBackends)],
          llm: [...new Set(llmBackends)],
          reranker: rerankerBackends,
          storage: this.config.storage?.qdrant?.url || 'http://localhost:6333',
        },
      }

      logger.debug('Status retrieved')
      return result
    } catch (error) {
      logger.error('Failed to get status', error as Error)
      throw new Error(`Status retrieval failed: ${(error as Error).message}`)
    }
  }

  async generateQNTM(params: QNTMGenerateParams): Promise<QNTMGenerateResult> {
    this.ensureInitialized()
    logger.info('Generating QNTM keys')

    try {
      const { generateQNTMKeys } = await import('../llm')

      const result = await generateQNTMKeys({
        chunk: params.text,
        existingKeys: params.existingKeys || [],
        context: params.context || { fileName: '<manual>' },
      })

      logger.info('QNTM keys generated', { keyCount: result.keys.length })
      return {
        keys: result.keys,
        reasoning: result.reasoning,
      }
    } catch (error) {
      logger.error('QNTM generation failed', error as Error)
      throw new Error(`QNTM generation failed: ${(error as Error).message}`)
    }
  }

  getConfig(): AtlasConfig {
    return this.config
  }

  applyOverrides(overrides: Partial<AtlasConfig>): void {
    logger.info('Applying configuration overrides')

    try {
      // Apply overrides to config (validates provider-capability compatibility)
      applyRuntimeOverrides(overrides)

      // Update internal config reference
      this.config = getConfig()

      // Re-initialize backends if already initialized
      if (this.initialized) {
        logger.debug('Re-initializing backends after config override')
        initializeLLMBackends()
        initializeEmbeddingBackends()
      }

      logger.info('Configuration overrides applied successfully')
    } catch (error) {
      logger.error('Failed to apply configuration overrides', error as Error)
      throw new Error(`Config override failed: ${(error as Error).message}`)
    }
  }

  private ensureInitialized(): void {
    if (!this.initialized) {
      throw new Error('ApplicationService not initialized. Call initialize() first.')
    }
  }
}

// ============================================
// Singleton Instance (Optional)
// ============================================

let defaultInstance: DefaultApplicationService | null = null

/**
 * Get or create the default ApplicationService singleton
 *
 * @param config - Configuration (required for first call)
 * @returns ApplicationService instance
 */
export function getApplicationService(config?: AtlasConfig): DefaultApplicationService {
  if (!defaultInstance) {
    if (!config) {
      // Use current global config if none provided
      config = getConfig()
    }
    defaultInstance = new DefaultApplicationService(config)
  }
  return defaultInstance
}

/**
 * Reset the singleton instance (for testing)
 */
export function resetApplicationService(): void {
  defaultInstance = null
}
