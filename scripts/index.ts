#!/usr/bin/env bun
/**
 * Atlas CLI Entrypoint
 *
 * Unified command-line interface for Atlas context ingestion and search.
 */

import { loadConfig, getConfig, applyRuntimeOverrides } from './src/shared/config.loader'
import { parseBackendSpecifier } from './src/shared/config.schema'
import { Command } from 'commander'
import {
  CONSOLIDATION_SIMILARITY_THRESHOLD,
  DEFAULT_SEARCH_LIMIT,
  OLLAMA_URL,
} from './src/shared/config'
import { createLogger, setLogLevel, setModuleRules } from './src/shared/logger'

const log = createLogger('app')

// Main async function to load config before importing services
async function main() {
  // Load config first (services call getConfig() at module load)
  await loadConfig()

  // Dynamic imports AFTER config is loaded
  const { ingest } = await import('./src/domain/ingest')
  const { setQNTMProvider } = await import('./src/services/llm')
  const { formatResults, search, timeline } = await import('./src/domain/search')
  const { computeRootDir } = await import('./src/shared/utils')

  const program = new Command()

  program
    .name('atlas')
    .description('Persistent Context Management with RAG (Voyage + Qdrant)')
    .version('1.0.0')
    .option(
      '--qdrant-url <url>',
      'Qdrant server URL',
      process.env.QDRANT_URL || 'http://localhost:6333'
    )
    .option('--voyage-key <key>', 'Voyage AI API key', process.env.VOYAGE_API_KEY)
    .option(
      '--log-level <level>',
      'Global log level fallback (trace, debug, info, warn, error)',
      process.env.LOG_LEVEL || 'info'
    )
    .option(
      '--log-modules <rules>',
      'Module logging rules (e.g., "qntm/*:debug,ingest:trace")',
      process.env.LOG_MODULES
    )
    .option('--ollama-url <url>', 'Ollama server URL', OLLAMA_URL)
    .option(
      '-j, --jobs <n>',
      'Concurrent QNTM generation jobs (default: 60% of CPU cores, max 10)',
      parseInt
    )
    .hook('preAction', (thisCommand) => {
      const opts = thisCommand.opts()

      // Apply logging configuration early
      if (opts.logLevel) {
        setLogLevel(opts.logLevel)
      }
      if (opts.logModules) {
        setModuleRules(opts.logModules)
      }

      log.debug('CLI options parsed', {
        jobs: opts.jobs,
        logLevel: opts.logLevel,
        logModules: opts.logModules,
      })
    })

  // Ingest command
  program
    .command('ingest')
    .description('Ingest files/directories into Atlas vector database')
    .argument('<paths...>', 'Files or directories to ingest')
    .option('-r, --recursive', 'Recursively ingest directories', false)
    .option('-q, --quiet', 'Suppress verbose output', false)
    .option('--embedding <backend>', 'Override embedding backend (e.g., voyage:voyage-3-large)')
    .option('--llm <backend>', 'Override LLM backend (e.g., claude-code:haiku)')
    .action(async (paths: string[], options, command) => {
      const globalOpts = command.parent?.opts() || {}

      // Apply runtime config overrides (immutable pattern)
      const overrides: any = {}

      if (globalOpts.qdrantUrl) {
        overrides.qdrant = { url: globalOpts.qdrantUrl }
      }

      if (options.embedding || options.llm) {
        overrides.backends = {}

        if (options.embedding) {
          log.debug('Overriding embedding backend', { backend: options.embedding })
          overrides.backends['text-embedding'] = options.embedding
          overrides.backends['code-embedding'] = options.embedding
          overrides.backends['contextualized-embedding'] = options.embedding
        }

        if (options.llm) {
          log.debug('Overriding LLM backend', { backend: options.llm })
          overrides.backends['text-completion'] = options.llm
          overrides.backends['json-completion'] = options.llm
          overrides.backends['qntm-generation'] = options.llm
        }
      }

      // Apply overrides to config (validates provider-capability compatibility)
      if (Object.keys(overrides).length > 0) {
        applyRuntimeOverrides(overrides)
      }

      // Re-initialize backends after applying runtime overrides
      const { initializeEmbeddingBackends } = await import('./src/services/embedding')
      const { initializeLLMBackends } = await import('./src/services/llm')
      initializeEmbeddingBackends()
      initializeLLMBackends()

      // Set env vars that aren't in config (API keys)
      if (globalOpts.voyageKey) process.env.VOYAGE_API_KEY = globalOpts.voyageKey

      // Configure QNTM concurrency
      if (globalOpts.jobs) {
        process.env.QNTM_CONCURRENCY = String(globalOpts.jobs)
        log.debug('QNTM concurrency configured', { jobs: globalOpts.jobs })
      }

      // Configure QNTM provider (from --llm flag or config)
      if (options.llm) {
        const parsed = parseBackendSpecifier(options.llm)
        const provider = parsed.provider
        const model =
          parsed.model ||
          (provider === 'anthropic'
            ? 'haiku'
            : provider === 'claude-code'
              ? 'haiku'
              : 'ministral-3:3b')

        log.debug('Configuring QNTM provider from --llm flag', { provider, model })
        setQNTMProvider({
          provider,
          model,
          ollamaHost: globalOpts.ollamaUrl,
        })
      } else {
        // Use config defaults (already set via config.loader)
        const config = getConfig()
        const llmBackend = config.backends?.['qntm-generation'] || 'ollama:ministral-3:3b'
        const parsed = parseBackendSpecifier(llmBackend)
        const provider = parsed.provider
        const model = parsed.model || 'ministral-3:3b'

        log.debug('Configuring QNTM provider from config', { provider, model })
        setQNTMProvider({
          provider,
          model,
          ollamaHost: globalOpts.ollamaUrl,
        })
      }

      try {
        const result = await ingest({
          paths,
          recursive: options.recursive,
          rootDir: computeRootDir(paths),
          verbose: !options.quiet,
        })

        if (result.errors.length > 0) {
          log.error(`${result.errors.length} file(s) failed to ingest`)
          for (const { file, error } of result.errors) {
            log.error(`  ${file}`, error)
          }
        }

        if (!options.quiet) {
          log.info(
            `Ingestion complete: ${result.filesProcessed} files, ${result.chunksStored} chunks`
          )
        }
      } catch (error) {
        log.error('Ingestion failed', error as Error)
        process.exit(1)
      }
    })

  // Search command
  program
    .command('search')
    .description('Semantic search across ingested context')
    .argument('<query>', 'Search query')
    .option('-l, --limit <n>', 'Number of results', parseInt, DEFAULT_SEARCH_LIMIT)
    .option('--since <date>', 'Filter by creation date (ISO 8601)')
    .option('--qntm <key>', 'Filter by QNTM semantic key')
    .option('--rerank', 'Rerank results using Voyage cross-encoder')
    .option('--embedding <backend>', 'Override embedding backend (e.g., voyage:voyage-3-large)')
    .option('--reranker <backend>', 'Override reranker backend (e.g., voyage:rerank-2.5)')
    .action(async (query: string, options, command) => {
      const globalOpts = command.parent?.opts() || {}

      // Apply runtime config overrides (immutable pattern)
      const overrides: any = {}

      if (globalOpts.qdrantUrl) {
        overrides.qdrant = { url: globalOpts.qdrantUrl }
      }

      if (options.embedding || options.reranker) {
        overrides.backends = {}

        if (options.embedding) {
          log.debug('Overriding embedding backend', { backend: options.embedding })
          overrides.backends['text-embedding'] = options.embedding
          overrides.backends['code-embedding'] = options.embedding
          overrides.backends['contextualized-embedding'] = options.embedding
        }

        if (options.reranker) {
          log.debug('Overriding reranker backend', { backend: options.reranker })
          overrides.backends['reranking'] = options.reranker
        }
      }

      // Apply overrides to config (validates provider-capability compatibility)
      if (Object.keys(overrides).length > 0) {
        applyRuntimeOverrides(overrides)
      }

      // Re-initialize backends after applying runtime overrides
      const { initializeEmbeddingBackends } = await import('./src/services/embedding')
      const { initializeLLMBackends } = await import('./src/services/llm')
      initializeEmbeddingBackends()
      initializeLLMBackends()

      // Set env vars that aren't in config (API keys)
      if (globalOpts.voyageKey) process.env.VOYAGE_API_KEY = globalOpts.voyageKey

      try {
        log.info('Starting search', { query, limit: options.limit, rerank: options.rerank })
        const results = await search({
          query,
          limit: options.limit,
          since: options.since,
          qntmKey: options.qntm,
          rerank: options.rerank,
        })
        log.debug('Search complete', { resultCount: results.length })
        console.log(formatResults(results))
      } catch (error) {
        log.error('Search failed', error as Error)
        process.exit(1)
      }
    })

  // Timeline command
  program
    .command('timeline')
    .description('Show chronological timeline of ingested context')
    .requiredOption('--since <date>', 'Starting date (ISO 8601)')
    .option('-l, --limit <n>', 'Number of results', parseInt, 20)
    .option('--embedding <backend>', 'Override embedding backend (e.g., voyage:voyage-3-large)')
    .action(async (options, command) => {
      const globalOpts = command.parent?.opts() || {}

      // Apply runtime config overrides (immutable pattern)
      const overrides: any = {}

      if (globalOpts.qdrantUrl) {
        overrides.qdrant = { url: globalOpts.qdrantUrl }
      }

      if (options.embedding) {
        log.debug('Overriding embedding backend', { backend: options.embedding })
        overrides.backends = {
          'text-embedding': options.embedding,
          'code-embedding': options.embedding,
          'contextualized-embedding': options.embedding,
        }
      }

      // Apply overrides to config (validates provider-capability compatibility)
      if (Object.keys(overrides).length > 0) {
        applyRuntimeOverrides(overrides)
      }

      // Re-initialize backends after applying runtime overrides
      const { initializeEmbeddingBackends } = await import('./src/services/embedding')
      const { initializeLLMBackends } = await import('./src/services/llm')
      initializeEmbeddingBackends()
      initializeLLMBackends()

      // Set env vars that aren't in config (API keys)
      if (globalOpts.voyageKey) process.env.VOYAGE_API_KEY = globalOpts.voyageKey

      try {
        log.info('Starting timeline query', { since: options.since, limit: options.limit })
        const results = await timeline(options.since, options.limit)
        log.debug('Timeline complete', { resultCount: results.length })
        console.log(formatResults(results))
      } catch (error) {
        log.error('Timeline failed', error as Error)
        process.exit(1)
      }
    })

  // Consolidate command
  program
    .command('consolidate')
    .description('Find and consolidate similar chunks in the atlas collection')
    .option('--dry-run', 'Preview consolidation candidates without modifying', false)
    .option(
      '--threshold <n>',
      'Similarity threshold (0-1)',
      parseFloat,
      CONSOLIDATION_SIMILARITY_THRESHOLD
    )
    .option('-l, --limit <n>', 'Max candidates to process (default: unlimited)', parseInt)
    .option('--llm <backend>', 'Override LLM backend (e.g., claude-code:haiku)')
    .action(async (options, command) => {
      const globalOpts = command.parent?.opts() || {}

      // Apply runtime config overrides (immutable pattern)
      const overrides: any = {}

      if (globalOpts.qdrantUrl) {
        overrides.qdrant = { url: globalOpts.qdrantUrl }
      }

      if (options.llm) {
        log.debug('Overriding LLM backend', { backend: options.llm })
        overrides.backends = {
          'text-completion': options.llm,
          'json-completion': options.llm,
          'qntm-generation': options.llm,
        }

        // Also update legacy QNTM provider
        const parsed = parseBackendSpecifier(options.llm)
        const model =
          parsed.model ||
          (parsed.provider === 'anthropic'
            ? 'haiku'
            : parsed.provider === 'claude-code'
              ? 'haiku'
              : 'ministral-3:3b')
        setQNTMProvider({ provider: parsed.provider, model })
      }

      // Apply overrides to config (validates provider-capability compatibility)
      if (Object.keys(overrides).length > 0) {
        applyRuntimeOverrides(overrides)
      }

      // Re-initialize backends after applying runtime overrides
      const { initializeEmbeddingBackends } = await import('./src/services/embedding')
      const { initializeLLMBackends } = await import('./src/services/llm')
      initializeEmbeddingBackends()
      initializeLLMBackends()

      // Set env vars that aren't in config (API keys)
      if (globalOpts.voyageKey) process.env.VOYAGE_API_KEY = globalOpts.voyageKey

      try {
        const { consolidate } = await import('./src/domain/consolidate')
        const result = await consolidate({
          dryRun: options.dryRun,
          threshold: options.threshold,
          limit: options.limit,
        })

        if (options.dryRun) {
          log.info(`Dry run: found ${result.candidatesFound} consolidation candidates`)
          if (result.candidates && result.candidates.length > 0) {
            for (const candidate of result.candidates.slice(0, 10)) {
              console.log(
                `  - ${candidate.file_path} (similarity: ${candidate.similarity.toFixed(3)})`
              )
            }
            if (result.candidates.length > 10) {
              console.log(`  ... and ${result.candidates.length - 10} more`)
            }
          }
        } else {
          log.info(
            `Consolidation complete: ${result.consolidated} chunks merged, ${result.deleted} removed`
          )
        }
      } catch (error) {
        log.error('Consolidation failed', error as Error)
        process.exit(1)
      }
    })

  // Qdrant management command
  program
    .command('qdrant')
    .description('Qdrant database management commands')
    .addCommand(
      new Command('drop')
        .description('Drop atlas collection (DESTRUCTIVE)')
        .option('-y, --yes', 'Confirm deletion without prompt')
        .action(async (options, command) => {
          const globalOpts = command.parent?.parent?.opts() || {}

          // Apply runtime config overrides (immutable pattern)
          if (globalOpts.qdrantUrl) {
            applyRuntimeOverrides({ qdrant: { url: globalOpts.qdrantUrl } })
          }

          if (!options.yes) {
            log.error('DESTRUCTIVE OPERATION: This will delete all ingested data.')
            log.error('Use --yes flag to confirm: atlas qdrant drop --yes')
            process.exit(1)
          }

          try {
            const { getStorageBackend } = await import('./src/services/storage')
            const { QDRANT_COLLECTION_NAME } = await import('./src/shared/config')

            const storage = getStorageBackend()
            if (!storage) {
              log.error('No storage backend available')
              process.exit(1)
            }

            // Check if collection exists
            const exists = await storage.collectionExists(QDRANT_COLLECTION_NAME)
            if (!exists) {
              log.warn(`Collection '${QDRANT_COLLECTION_NAME}' does not exist`)
              return
            }

            // Get collection info before deletion
            const info = await storage.getCollectionInfo(QDRANT_COLLECTION_NAME)
            log.warn('Dropping collection', {
              collection: QDRANT_COLLECTION_NAME,
              points: info.points_count,
              dimensions: info.vector_dimensions
            })

            // Perform deletion
            await storage.deleteCollection(QDRANT_COLLECTION_NAME)
            log.info(`Collection '${QDRANT_COLLECTION_NAME}' dropped successfully`)
          } catch (error) {
            log.error('Drop collection failed', error as Error)
            process.exit(1)
          }
        })
    )
    .addCommand(
      new Command('hnsw')
        .description('Toggle HNSW indexing (on|off)')
        .argument('<state>', 'on or off')
        .action(async (state: string, options, command) => {
          const globalOpts = command.parent?.parent?.opts() || {}

          // Apply runtime config overrides (immutable pattern)
          if (globalOpts.qdrantUrl) {
            applyRuntimeOverrides({ qdrant: { url: globalOpts.qdrantUrl } })
          }
          if (globalOpts.voyageKey) {
            process.env.VOYAGE_API_KEY = globalOpts.voyageKey
          }

          const validStates = ['on', 'off']
          if (!validStates.includes(state)) {
            log.error(`Invalid state: ${state}. Use: on or off`)
            process.exit(1)
          }

          try {
            const { enableHNSW, disableHNSW, isHNSWDisabled } =
              await import('./src/services/storage')

            if (state === 'on') {
              await enableHNSW()
              log.info('HNSW indexing enabled (m=16)')
            } else {
              await disableHNSW()
              log.info('HNSW indexing disabled (m=0)')
            }
          } catch (error) {
            log.error('HNSW toggle failed', error as Error)
            process.exit(1)
          }
        })
    )
    .addCommand(
      new Command('vacuum')
        .description('Hard-delete chunks past grace period (14 days default)')
        .option('-f, --force', 'Bypass grace period and delete immediately')
        .option('-n, --dry-run', 'Show what would be deleted without deleting')
        .option('-l, --limit <n>', 'Max chunks to process', '1000')
        .action(async (options, command) => {
          const globalOpts = command.parent?.parent?.opts() || {}

          // Apply runtime config overrides (immutable pattern)
          if (globalOpts.qdrantUrl) {
            applyRuntimeOverrides({ qdrant: { url: globalOpts.qdrantUrl } })
          }

          try {
            const { getStorageBackend } = await import('./src/services/storage')
            const { QDRANT_COLLECTION_NAME, DELETION_GRACE_PERIOD_DAYS } =
              await import('./src/shared/config')

            const storage = getStorageBackend()
            if (!storage) {
              log.error('No storage backend available')
              process.exit(1)
            }

            const limit = parseInt(options.limit, 10)
            const dryRun = options.dryRun || false
            const force = options.force || false

            // Get collection stats first
            const collectionInfo = await storage.getCollectionInfo(QDRANT_COLLECTION_NAME)
            log.info('Collection stats before vacuum', {
              totalPoints: collectionInfo.points_count,
              segments: collectionInfo.segments_count,
            })

            // Find deletion-eligible chunks
            const scrollResult = await storage.scroll(QDRANT_COLLECTION_NAME, {
              filter: {
                must: [{ key: 'deletion_eligible', match: { value: true } }],
              },
              limit,
              withPayload: true,
              withVector: false,
            })

            const eligibleCount = scrollResult.points.length

            if (eligibleCount === 0) {
              log.info('No chunks marked for deletion')
              return
            }

            // Filter by grace period unless --force
            const now = new Date()
            const toDelete: string[] = []
            let skippedGracePeriod = 0

            for (const point of scrollResult.points) {
              const payload = point.payload as { deletion_marked_at?: string }
              const markedAt = payload.deletion_marked_at
                ? new Date(payload.deletion_marked_at)
                : null

              if (force || !markedAt) {
                // Force delete or no timestamp (legacy)
                toDelete.push(point.id as string)
              } else {
                const daysSinceMarked =
                  (now.getTime() - markedAt.getTime()) / (1000 * 60 * 60 * 24)
                if (daysSinceMarked >= DELETION_GRACE_PERIOD_DAYS) {
                  toDelete.push(point.id as string)
                } else {
                  skippedGracePeriod++
                }
              }
            }

            log.info('Vacuum candidates', {
              markedForDeletion: eligibleCount,
              pastGracePeriod: toDelete.length,
              withinGracePeriod: skippedGracePeriod,
              gracePeriodDays: force ? 'BYPASSED' : DELETION_GRACE_PERIOD_DAYS,
            })

            if (toDelete.length === 0) {
              log.info('No chunks past grace period. Use --force to bypass.')
              return
            }

            if (dryRun) {
              log.info('Dry run: would delete', {
                count: toDelete.length,
                sampleIds: toDelete.slice(0, 5),
              })
              return
            }

            // Perform hard delete
            await storage.delete(QDRANT_COLLECTION_NAME, toDelete)
            log.info('Hard deleted chunks', { count: toDelete.length })

            // Get updated stats
            const afterInfo = await storage.getCollectionInfo(QDRANT_COLLECTION_NAME)
            log.info('Collection stats after vacuum', {
              totalPoints: afterInfo.points_count,
              segments: afterInfo.segments_count,
              pointsRemoved: collectionInfo.points_count - afterInfo.points_count,
            })
          } catch (error) {
            log.error('Vacuum failed', error as Error)
            process.exit(1)
          }
        })
    )

  // Docker helper command
  program
    .command('docker')
    .description('Docker setup commands')
    .addCommand(
      new Command('up').description('Start Atlas services (Qdrant + Ollama)').action(() => {
        log.info('Starting Atlas services...')
        const { execSync } = require('child_process')
        execSync('docker compose up -d', { stdio: 'inherit' })
        log.info('Qdrant started at http://localhost:6333')
        log.info('Ollama started at http://localhost:11434')
      })
    )
    .addCommand(
      new Command('down').description('Stop Atlas services').action(() => {
        const { execSync } = require('child_process')
        execSync('docker compose down', { stdio: 'inherit' })
        log.info('Atlas services stopped')
      })
    )
    .addCommand(
      new Command('restart').description('Restart Atlas services').action(() => {
        log.info('Restarting Atlas services...')
        const { execSync } = require('child_process')
        execSync('docker compose restart', { stdio: 'inherit' })
        log.info('Atlas services restarted')
      })
    )
    .addCommand(
      new Command('logs')
        .description('View Docker service logs (qdrant|ollama|all)')
        .argument('[service]', 'Service to view logs for (qdrant, ollama, or all)', 'all')
        .action((service: string) => {
          const { execSync } = require('child_process')
          const validServices = ['qdrant', 'ollama', 'all']

          if (!validServices.includes(service)) {
            log.error(`Invalid service: ${service}. Use: qdrant, ollama, or all`)
            process.exit(1)
          }

          const cmd =
            service === 'all' ? 'docker compose logs -f' : `docker compose logs -f ${service}`

          log.info(`Viewing ${service} logs (Ctrl+C to exit)...`)
          execSync(cmd, { stdio: 'inherit' })
        })
    )

  // Run CLI
  program.parse()
}

// Execute main function
if (import.meta.main) {
  main().catch((error) => {
    log.error('Fatal error', error as Error)
    process.exit(1)
  })
}
