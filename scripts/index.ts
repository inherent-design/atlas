#!/usr/bin/env bun
/**
 * Atlas CLI Entrypoint
 *
 * Unified command-line interface for Atlas context ingestion and search.
 */

import { Command } from 'commander'
import {
  DEFAULT_QNTM_MODEL_ANTHROPIC,
  DEFAULT_QNTM_MODEL_OLLAMA,
  DEFAULT_QNTM_PROVIDER,
  DEFAULT_SEARCH_LIMIT,
  OLLAMA_URL,
} from './src/config'
import { ingest } from './src/ingest'
import { createLogger, setLogLevel, setModuleRules } from './src/logger'
import { setQNTMProvider } from './src/qntm'
import { formatResults, search, timeline } from './src/search'

const log = createLogger('app')

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
  .option(
    '--provider <provider>',
    'QNTM generation provider (anthropic|ollama)',
    DEFAULT_QNTM_PROVIDER
  )
  .option('--model <model>', 'Model for QNTM generation')
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
      provider: opts.provider,
      model: opts.model,
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
  .action(async (paths: string[], options, command) => {
    const globalOpts = command.parent?.opts() || {}

    // Set runtime config from CLI flags
    if (globalOpts.qdrantUrl) process.env.QDRANT_URL = globalOpts.qdrantUrl
    if (globalOpts.voyageKey) process.env.VOYAGE_API_KEY = globalOpts.voyageKey

    // Configure QNTM concurrency
    if (globalOpts.jobs) {
      process.env.QNTM_CONCURRENCY = String(globalOpts.jobs)
      log.debug('QNTM concurrency configured', { jobs: globalOpts.jobs })
    }

    // Configure QNTM provider
    const provider = globalOpts.provider || DEFAULT_QNTM_PROVIDER
    const model =
      globalOpts.model ||
      (provider === 'anthropic' ? DEFAULT_QNTM_MODEL_ANTHROPIC : DEFAULT_QNTM_MODEL_OLLAMA)
    log.debug('Configuring QNTM provider', { provider, model })
    setQNTMProvider({
      provider,
      model,
      ollamaHost: globalOpts.ollamaUrl,
    })

    try {
      const result = await ingest({
        paths,
        recursive: options.recursive,
        rootDir: process.cwd(),
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
  .action(async (query: string, options, command) => {
    const globalOpts = command.parent?.opts() || {}

    // Set runtime config from CLI flags
    if (globalOpts.qdrantUrl) process.env.QDRANT_URL = globalOpts.qdrantUrl
    if (globalOpts.voyageKey) process.env.VOYAGE_API_KEY = globalOpts.voyageKey

    try {
      log.info('Starting search', { query, limit: options.limit })
      const results = await search({
        query,
        limit: options.limit,
        since: options.since,
        qntmKey: options.qntm,
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
  .action(async (options, command) => {
    const globalOpts = command.parent?.opts() || {}

    // Set runtime config from CLI flags
    if (globalOpts.qdrantUrl) process.env.QDRANT_URL = globalOpts.qdrantUrl
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
  .option('--threshold <n>', 'Similarity threshold (0-1)', parseFloat, 0.92)
  .option('-l, --limit <n>', 'Max candidates to process', parseInt, 100)
  .action(async (options, command) => {
    const globalOpts = command.parent?.opts() || {}

    // Set runtime config from CLI flags
    if (globalOpts.qdrantUrl) process.env.QDRANT_URL = globalOpts.qdrantUrl
    if (globalOpts.voyageKey) process.env.VOYAGE_API_KEY = globalOpts.voyageKey

    try {
      const { consolidate } = await import('./src/consolidate')
      const result = await consolidate({
        dryRun: options.dryRun,
        threshold: options.threshold,
        limit: options.limit,
      })

      if (options.dryRun) {
        log.info(`Dry run: found ${result.candidatesFound} consolidation candidates`)
        if (result.candidates && result.candidates.length > 0) {
          for (const candidate of result.candidates.slice(0, 10)) {
            console.log(`  - ${candidate.file_path} (similarity: ${candidate.similarity.toFixed(3)})`)
          }
          if (result.candidates.length > 10) {
            console.log(`  ... and ${result.candidates.length - 10} more`)
          }
        }
      } else {
        log.info(`Consolidation complete: ${result.consolidated} chunks merged, ${result.deleted} removed`)
      }
    } catch (error) {
      log.error('Consolidation failed', error as Error)
      process.exit(1)
    }
  })

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
if (import.meta.main) {
  program.parse()
}
