#!/usr/bin/env node
/**
 * Atlas CLI Entrypoint
 *
 * Thin wrapper over ApplicationService - delegates all operations.
 */

import { Command } from 'commander'
import {
  loadConfig,
  createLogger,
  setLogLevel,
  setModuleRules,
  registerPrompts,
  getApplicationService,
  getStorageService,
  CONSOLIDATION_SIMILARITY_THRESHOLD,
  DEFAULT_SEARCH_LIMIT,
  OLLAMA_URL,
  type AtlasConfig,
} from '@inherent.design/atlas-core'

const log = createLogger('cli')

/**
 * Build config overrides from CLI options
 */
function buildConfigFromOptions(globalOpts: any, commandOpts: any = {}): Partial<AtlasConfig> {
  const overrides: any = {}

  // Qdrant URL (merge with existing storage config, don't replace it)
  if (globalOpts.qdrantUrl) {
    if (!overrides.storage) overrides.storage = {}
    overrides.storage.qdrant = { url: globalOpts.qdrantUrl }
  }

  // Backend overrides
  if (commandOpts.embedding || commandOpts.llm || commandOpts.reranker) {
    overrides.backends = {}

    if (commandOpts.embedding) {
      overrides.backends['text-embedding'] = commandOpts.embedding
      overrides.backends['code-embedding'] = commandOpts.embedding
      overrides.backends['contextualized-embedding'] = commandOpts.embedding
    }

    if (commandOpts.llm) {
      overrides.backends['text-completion'] = commandOpts.llm
      overrides.backends['json-completion'] = commandOpts.llm
    }

    if (commandOpts.reranker) {
      overrides.backends['reranking'] = commandOpts.reranker
    }
  }

  // Logging level
  if (globalOpts.logLevel) {
    overrides.logging = { level: globalOpts.logLevel }
  }

  return overrides
}

// Main async function
async function main() {
  // Load config first
  await loadConfig()

  // Register prompts
  registerPrompts()

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

      // Set environment variables that aren't in config
      if (opts.voyageKey) process.env.VOYAGE_API_KEY = opts.voyageKey
      if (opts.jobs) process.env.QNTM_CONCURRENCY = String(opts.jobs)

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
    .option('--no-consolidation', 'Disable auto-consolidation after ingest', false)
    .option('--consolidation-threshold <n>', 'Chunks threshold for consolidation', parseInt, 500)
    .option('-w, --watch', 'Watch for file changes and re-ingest', false)
    .option('--embedding <backend>', 'Override embedding backend (e.g., voyage:voyage-3-large)')
    .option('--llm <backend>', 'Override LLM backend (e.g., claude-code:haiku)')
    .action(async (paths: string[], options, command) => {
      const globalOpts = command.parent?.opts() || {}

      try {
        // Build config overrides from CLI options
        const configOverrides = buildConfigFromOptions(globalOpts, options)

        // Get ApplicationService with config
        const app = getApplicationService()
        if (Object.keys(configOverrides).length > 0) {
          app.applyOverrides(configOverrides)
        }
        await app.initialize()

        // Delegate to ApplicationService
        const result = await app.ingest({
          paths,
          recursive: options.recursive,
          verbose: !options.quiet,
          allowConsolidation: !options.noConsolidation,
          consolidationThreshold: options.consolidationThreshold,
          watch: options.watch,
        })

        // Format output
        if (result.errors.length > 0) {
          log.error(`${result.errors.length} file(s) failed to ingest`)
          for (const { file, error } of result.errors) {
            log.error(`  ${file}`, new Error(error))
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
    .option('--consolidation-level <level>', 'Filter by consolidation level (0-4)', parseInt)
    .option(
      '--content-type <type>',
      'Filter by content type (code, document, conversation, signal, learning, axiom, evidence)'
    )
    .option(
      '--agent-role <role>',
      'Filter by agent role (observer, connector, explainer, challenger, integrator, meta)'
    )
    .option('--temperature <tier>', 'Filter by temperature tier (hot, warm, cold)')
    .option('--embedding <backend>', 'Override embedding backend (e.g., voyage:voyage-3-large)')
    .option('--reranker <backend>', 'Override reranker backend (e.g., voyage:rerank-2.5)')
    .action(async (query: string, options, command) => {
      const globalOpts = command.parent?.opts() || {}

      try {
        // Build config overrides from CLI options
        const configOverrides = buildConfigFromOptions(globalOpts, options)

        // Get ApplicationService with config
        const app = getApplicationService()
        if (Object.keys(configOverrides).length > 0) {
          app.applyOverrides(configOverrides)
        }
        await app.initialize()

        // Delegate to ApplicationService
        const results = await app.search({
          query,
          limit: options.limit,
          since: options.since,
          qntmKey: options.qntm,
          rerank: options.rerank,
          consolidationLevel: options.consolidationLevel,
          contentType: options.contentType,
          agentRole: options.agentRole,
          temperature: options.temperature,
        })

        // Format output
        const { formatResults } = await import('@inherent.design/atlas-core')
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

      try {
        // Build config overrides from CLI options
        const configOverrides = buildConfigFromOptions(globalOpts, options)

        // Get ApplicationService with config
        const app = getApplicationService()
        if (Object.keys(configOverrides).length > 0) {
          app.applyOverrides(configOverrides)
        }
        await app.initialize()

        // Delegate to ApplicationService
        const results = await app.timeline({
          since: options.since,
          limit: options.limit || 20,
          includeCausalLinks: false,
          granularity: 'day',
        })

        // Format output
        const { formatResults } = await import('@inherent.design/atlas-core')
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
    .option('--llm <backend>', 'Override LLM backend (e.g., claude-code:haiku)')
    .action(async (options, command) => {
      const globalOpts = command.parent?.opts() || {}

      try {
        // Build config overrides from CLI options
        const configOverrides = buildConfigFromOptions(globalOpts, options)

        // Get ApplicationService with config
        const app = getApplicationService()
        if (Object.keys(configOverrides).length > 0) {
          app.applyOverrides(configOverrides)
        }
        await app.initialize()

        // Delegate to ApplicationService
        const result = await app.consolidate({
          dryRun: options.dryRun,
          threshold: options.threshold,
        })

        // Format output
        if (options.dryRun) {
          log.info(`Dry run: found ${result.candidatesEvaluated} consolidation candidates`)
        } else {
          log.info(
            `Consolidation complete: ${result.consolidationsPerformed} chunks merged (${result.chunksAbsorbed} removed)`
          )
        }
      } catch (error) {
        log.error('Consolidation failed', error as Error)
        process.exit(1)
      }
    })

  // (Old qdrant command removed - consolidated into dimension-based version below)

  // Daemon command - start daemon (ssh-agent style output)
  program
    .command('daemon')
    .description('Start Atlas daemon for event-driven operation')
    .option('--detach', 'Run daemon in background', false)
    .option('--watch', 'Enable file watcher for auto-ingestion', false)
    .option('--tcp <port>', 'Also listen on TCP port', parseInt)
    .action(async (options) => {
      try {
        const { startDaemon } = await import('@inherent.design/atlas-core')
        await startDaemon({
          detach: options.detach,
          enableFileWatcher: options.watch,
          tcpPort: options.tcp,
        })
      } catch (error) {
        log.error('Failed to start daemon', error as Error)
        process.exit(1)
      }
    })

  // Daemon stop command
  program
    .command('daemon:stop')
    .description('Stop Atlas daemon')
    .action(async () => {
      try {
        const { isDaemonRunning, killDaemon } = await import('@inherent.design/atlas-core')

        if (!isDaemonRunning()) {
          console.log('Atlas daemon is not running')
          return
        }

        await killDaemon()
        console.log('Atlas daemon stopped')
      } catch (error) {
        log.error('Failed to stop daemon', error as Error)
        process.exit(1)
      }
    })

  // Daemon status command
  program
    .command('daemon:status')
    .description('Check Atlas daemon status')
    .action(async () => {
      try {
        const { isDaemonRunning, getDaemonPid } = await import('@inherent.design/atlas-core')

        if (isDaemonRunning()) {
          const pid = getDaemonPid()
          console.log(`Atlas daemon running (PID ${pid})`)
          // Could also connect and get full status via JSON-RPC
          console.log('Use atlas client to get detailed status')
        } else {
          console.log('Atlas daemon is not running')
        }
      } catch (error) {
        log.error('Failed to check daemon status', error as Error)
        process.exit(1)
      }
    })

  // Doctor command - diagnose environment
  program
    .command('doctor')
    .description('Diagnose Atlas environment and service availability')
    .action(async () => {
      try {
        // Get ApplicationService
        const app = getApplicationService()
        await app.initialize()

        // Get health status
        const health = await app.health()

        // Print header
        console.log('Atlas Doctor')
        console.log('============\n')

        // Overall status
        console.log(`Overall: ${health.overall}`)
        console.log(`Timestamp: ${health.timestamp}\n`)

        // Vector service
        console.log('Vector Storage:')
        console.log(`  ${health.services.vector.name.padEnd(20)} ${health.services.vector.status}`)
        if (health.services.vector.error) {
          console.log(`  Error: ${health.services.vector.error}`)
        }
        console.log('')

        // Metadata service
        console.log('Metadata Storage:')
        console.log(
          `  ${health.services.metadata.name.padEnd(20)} ${health.services.metadata.status}`
        )
        if (health.services.metadata.error) {
          console.log(`  Error: ${health.services.metadata.error}`)
        }
        console.log('')

        // Embedding backends
        if (health.services.embedding.backends.length > 0) {
          console.log('Embedding Backends:')
          for (const backend of health.services.embedding.backends) {
            console.log(`  ${backend.name.padEnd(20)} ${backend.status}`)
          }
          console.log(
            `  Total: ${health.services.embedding.available}/${health.services.embedding.total}`
          )
          console.log('')
        }

        // LLM backends
        if (health.services.llm.backends.length > 0) {
          console.log('LLM Backends:')
          for (const backend of health.services.llm.backends) {
            console.log(`  ${backend.name.padEnd(20)} ${backend.status}`)
          }
          console.log(`  Total: ${health.services.llm.available}/${health.services.llm.total}`)
          console.log('')
        }

        // Reranker backends
        if (health.services.reranker.backends.length > 0) {
          console.log('Reranker Backends:')
          for (const backend of health.services.reranker.backends) {
            console.log(`  ${backend.name.padEnd(20)} ${backend.status}`)
          }
          console.log(
            `  Total: ${health.services.reranker.available}/${health.services.reranker.total}`
          )
          console.log('')
        }

        // Exit code based on health
        if (health.overall === 'unhealthy') {
          process.exit(1)
        }
      } catch (error) {
        log.error('Doctor failed', error as Error)
        process.exit(1)
      }
    })

  // Qdrant management commands
  const qdrantCmd = program
    .command('qdrant')
    .description('Qdrant collection management commands')

  // List collections
  qdrantCmd
    .command('list')
    .description('List all atlas_* collections with active status')
    .action(async () => {
      try {
        const { getQdrantClient, getPrimaryCollectionName, getStorageService, loadConfig } =
          await import('@inherent.design/atlas-core')

        // Initialize storage service
        const config = await loadConfig()
        getStorageService(config)

        const client = getQdrantClient()
        const response = await client.getCollections()
        const allCollections = response.collections.map((c) => c.name)
        const atlasCollections = allCollections.filter((name) => name.startsWith('atlas'))

        if (atlasCollections.length === 0) {
          console.log('No atlas collections found.')
          console.log('Run "atlas ingest" to create the first collection.')
          return
        }

        const activeCollection = getPrimaryCollectionName()

        console.log('Atlas Collections:')
        for (const name of atlasCollections) {
          const isActive = name === activeCollection
          const marker = isActive ? ' (active)' : ''
          console.log(`  ${name}${marker}`)
        }
        console.log(`\nActive collection: ${activeCollection}`)
      } catch (error) {
        log.error('Failed to list collections', error as Error)
        process.exit(1)
      }
    })

  // Rename collection
  qdrantCmd
    .command('rename')
    .description('Rename a collection')
    .argument('<old-name>', 'Current collection name')
    .argument('<new-name>', 'New collection name')
    .action(async (oldName: string, newName: string) => {
      try {
        const { getStorageBackend, getStorageService, loadConfig } = await import(
          '@inherent.design/atlas-core'
        )

        // Initialize storage service
        const config = await loadConfig()
        getStorageService(config)

        const storage = getStorageBackend()
        if (!storage) {
          log.error('No storage backend available')
          process.exit(1)
        }

        // Check if old collection exists
        const exists = await storage.collectionExists(oldName)
        if (!exists) {
          log.error(`Collection '${oldName}' does not exist`)
          process.exit(1)
        }

        // Check if new name already exists
        const newExists = await storage.collectionExists(newName)
        if (newExists) {
          log.error(`Collection '${newName}' already exists`)
          process.exit(1)
        }

        // Rename via Qdrant client (create alias or manual migration)
        const { getQdrantClient } = await import('@inherent.design/atlas-core')
        const qdrant = getQdrantClient()

        // Create collection alias as rename mechanism
        await qdrant.updateCollectionAliases({
          actions: [
            {
              create_alias: {
                collection_name: oldName,
                alias_name: newName,
              },
            },
          ],
        })

        console.log(`Collection renamed: ${oldName} → ${newName}`)
        console.log(
          `Note: This creates an alias. To fully migrate, use Qdrant's snapshot feature.`
        )
      } catch (error) {
        log.error('Failed to rename collection', error as Error)
        process.exit(1)
      }
    })

  // Drop collection
  qdrantCmd
    .command('drop')
    .description('Delete a collection (CAUTION: irreversible)')
    .argument('[collection-name]', 'Collection name to drop (defaults to active collection)')
    .option('--yes', 'Skip confirmation prompt')
    .action(async (collectionName: string | undefined, options) => {
      try {
        const { getStorageBackend, getPrimaryCollectionName, getStorageService, loadConfig } =
          await import('@inherent.design/atlas-core')

        // Initialize storage service
        const config = await loadConfig()
        getStorageService(config)

        const storage = getStorageBackend()
        if (!storage) {
          log.error('No storage backend available')
          process.exit(1)
        }

        const targetCollection = collectionName || getPrimaryCollectionName()

        // Check if collection exists
        const exists = await storage.collectionExists(targetCollection)
        if (!exists) {
          log.error(`Collection '${targetCollection}' does not exist`)
          process.exit(1)
        }

        // Confirm deletion unless --yes flag
        if (!options.yes) {
          const readline = await import('readline/promises')
          const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
          })

          const answer = await rl.question(
            `Are you sure you want to delete collection '${targetCollection}'? [y/N] `
          )
          rl.close()

          if (answer.toLowerCase() !== 'y' && answer.toLowerCase() !== 'yes') {
            console.log('Deletion cancelled')
            return
          }
        }

        // Delete collection
        await storage.deleteCollection(targetCollection)
        console.log(`Collection '${targetCollection}' deleted`)
      } catch (error) {
        log.error('Failed to delete collection', error as Error)
        process.exit(1)
      }
    })

  // Collection doctor command
  qdrantCmd
    .command('doctor')
    .description('Diagnose collection issues and suggest fixes')
    .action(async () => {
      try {
        const {
          getQdrantClient,
          getPrimaryCollectionName,
          parseDimensionsFromCollection,
          getStorageService,
          loadConfig,
        } = await import('@inherent.design/atlas-core')

        // Initialize storage service
        const config = await loadConfig()
        getStorageService(config)

        console.log('Atlas Collection Doctor')
        console.log('=======================\n')

        // Get all collections
        const client = getQdrantClient()
        const response = await client.getCollections()
        const allCollections = response.collections.map((c) => c.name)
        const atlasCollections = allCollections.filter((name) => name.startsWith('atlas'))

        // Check for legacy 'atlas' collection
        const hasLegacy = atlasCollections.includes('atlas')
        if (hasLegacy) {
          console.log('⚠️  Legacy Collection Detected')
          console.log('  Found: atlas (old naming convention)')
          console.log(
            '  Action: Rename to dimension-based format (e.g., atlas_1024, atlas_768, atlas_384)'
          )
          console.log('  Command: atlas qdrant rename atlas atlas_<dimension>')
          console.log('')
        }

        // List all atlas collections with dimensions
        const activeCollection = getPrimaryCollectionName()
        console.log('Current Collections:')
        for (const name of atlasCollections) {
          const dims = parseDimensionsFromCollection(name)
          const isActive = name === activeCollection
          const marker = isActive ? ' (active)' : ''
          const dimInfo = dims ? ` [${dims} dimensions]` : ' [unknown format]'
          console.log(`  ${name}${dimInfo}${marker}`)
        }
        console.log(`\nActive collection: ${activeCollection}`)
        console.log('')

        // Check for dimension mismatches
        const { getEmbeddingDimensions } = await import('@inherent.design/atlas-core')
        const configDims = getEmbeddingDimensions()
        const activeDims = parseDimensionsFromCollection(activeCollection)

        if (activeDims !== configDims) {
          console.log('⚠️  Dimension Mismatch')
          console.log(`  Config expects: ${configDims} dimensions`)
          console.log(`  Active collection: ${activeDims} dimensions`)
          console.log('  Action: Update config or recreate collection')
          console.log(`  Command: atlas qdrant drop ${activeCollection} --yes`)
          console.log('')
        } else {
          console.log('✅ Active collection dimensions match config')
          console.log('')
        }
      } catch (error) {
        log.error('Collection doctor failed', error as Error)
        process.exit(1)
      }
    })

  // Status command - show current status
  program
    .command('status')
    .description('Show current Atlas status')
    .action(async () => {
      try {
        // Get ApplicationService
        const app = getApplicationService()
        await app.initialize()

        // Get status
        const status = await app.status()

        // Print header
        console.log('Atlas Status')
        console.log('============\n')

        // Collection stats
        console.log('Collection:')
        console.log(`  Name:         ${status.collection.name}`)
        console.log(`  Total chunks: ${status.collection.totalChunks}`)
        console.log(`  Total files:  ${status.collection.totalFiles}`)
        console.log(`  QNTM keys:    ${status.collection.totalQNTMKeys}`)
        console.log('')

        // Storage config
        console.log('Storage:')
        console.log(`  Vector:    ${status.backends.storage}`)
        console.log(`  Metadata:  ${status.storage.metadata}`)
        console.log(`  Cache:     ${status.storage.cache}`)
        console.log(`  Fulltext:  ${status.storage.fulltext}`)
        console.log(`  Analytics: ${status.storage.analytics}`)
        console.log('')

        // Backends
        console.log('Backends:')
        console.log(`  Embedding: ${status.backends.embedding.join(', ')}`)
        console.log(`  LLM:       ${status.backends.llm.join(', ')}`)
        if (status.backends.reranker.length > 0) {
          console.log(`  Reranker:  ${status.backends.reranker.join(', ')}`)
        }
        console.log('')
      } catch (error) {
        log.error('Status failed', error as Error)
        process.exit(1)
      }
    })

  // Export command - export analytics data
  program
    .command('export')
    .description('Export analytics data to Parquet format')
    .option('-o, --output <path>', 'Output directory', './exports')
    .option('-f, --format <format>', 'Export format (parquet|csv|json)', 'parquet')
    .option('--since <date>', 'Export data since this date (ISO 8601)')
    .option('--until <date>', 'Export data until this date (ISO 8601)')
    .action(async (options) => {
      try {
        // Get ApplicationService
        const app = getApplicationService()
        await app.initialize()

        const storageService = getStorageService(app.getConfig())

        if (!storageService.hasAnalytics()) {
          log.error('Analytics backend not configured. Enable DuckDB in atlas.config.ts')
          process.exit(1)
        }

        log.info('Exporting analytics data...')

        const result = await storageService.exportAnalytics({
          outputDir: options.output,
          format: options.format,
          since: options.since ? new Date(options.since) : undefined,
          until: options.until ? new Date(options.until) : undefined,
        })

        log.info('Export complete', {
          files: result.files,
          rows: result.rowCount,
          durationMs: result.durationMs,
        })

        console.log(`\nExported ${result.rowCount} rows to:`)
        for (const file of result.files) {
          console.log(`  ${file}`)
        }
      } catch (error) {
        log.error('Export failed', error as Error)
        process.exit(1)
      }
    })

  // Watch command - manual file watching
  program
    .command('watch')
    .description('Watch directories for new files to ingest')
    .option('--path <paths...>', 'Directories to watch (default: ~/.atlas/inbox)')
    .option('--pattern <patterns...>', 'File patterns (default: *.md, *.txt)')
    .action(async (options) => {
      try {
        const { getFileWatcher } = await import('@inherent.design/atlas-core')

        const watcher = getFileWatcher()

        log.info('Starting file watcher...')
        log.info('Press Ctrl+C to stop')

        watcher.start()

        // Keep process alive
        process.on('SIGINT', () => {
          log.info('Stopping file watcher...')
          watcher.stop()
          process.exit(0)
        })

        // Prevent exit
        await new Promise(() => {})
      } catch (error) {
        log.error('Watch failed', error as Error)
        process.exit(1)
      }
    })

  // Tracking subcommand group
  const trackingCommand = program
    .command('tracking')
    .description('File tracking database management')

  trackingCommand
    .command('status')
    .description('Show tracking database statistics')
    .action(async () => {
      try {
        const { getFileTracker, getStorageService } = await import('@inherent.design/atlas-core')
        const { loadConfig } = await import('@inherent.design/atlas-core')
        const config = await loadConfig()
        const storageService = getStorageService(config)
        const db = storageService.getDatabase()
        const tracker = getFileTracker(db)
        const stats = await tracker.getStats()

        console.log('Tracking Database Status')
        console.log('========================')
        console.log(`Total sources:       ${stats.totalFiles}`)
        console.log(`Active sources:      ${stats.activeFiles}`)
        console.log(`Deleted sources:     ${stats.deletedFiles}`)
        console.log(`Total chunks:        ${stats.totalChunks}`)
      } catch (error) {
        log.error('Failed to get tracking status', error as Error)
        process.exit(1)
      }
    })

  trackingCommand
    .command('vacuum')
    .description('Clean up old deleted source records (PostgreSQL)')
    .option('-n, --dry-run', 'Preview what would be removed')
    .action(async (options) => {
      try {
        const { getFileTracker, getStorageService } = await import('@inherent.design/atlas-core')
        const { loadConfig } = await import('@inherent.design/atlas-core')
        const config = await loadConfig()
        const storageService = getStorageService(config)
        const db = storageService.getDatabase()
        const tracker = getFileTracker(db)
        const stats = await tracker.getStats()

        if (options.dryRun) {
          console.log(`Would clean up: ${stats.deletedFiles} deleted source records`)
          return
        }

        console.log('Note: PostgreSQL automatically cleans up via ON DELETE CASCADE.')
        console.log(`Currently tracking: ${stats.deletedFiles} deleted sources`)
      } catch (error) {
        log.error('Vacuum failed', error as Error)
        process.exit(1)
      }
    })

  trackingCommand
    .command('check')
    .description('Check if a file needs ingestion')
    .argument('<path>', 'File path to check')
    .action(async (filePath: string) => {
      try {
        const { resolve } = await import('path')
        const { getFileTracker, getStorageService } = await import('@inherent.design/atlas-core')
        const { loadConfig } = await import('@inherent.design/atlas-core')
        const config = await loadConfig()
        const storageService = getStorageService(config)
        const db = storageService.getDatabase()

        const absolutePath = resolve(filePath)
        const tracker = getFileTracker(db)
        const result = await tracker.needsIngestion(absolutePath)

        console.log(`File: ${absolutePath}`)
        console.log(`Needs ingestion: ${result.needsIngest}`)
        console.log(`Reason: ${result.reason}`)
        if (result.existingChunks) {
          console.log(`Existing chunks: ${result.existingChunks.length}`)
        }
      } catch (error) {
        log.error('Check failed', error as Error)
        process.exit(1)
      }
    })

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
