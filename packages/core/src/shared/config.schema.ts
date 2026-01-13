/**
 * Atlas Configuration Schema (Draft)
 *
 * Zod-validated configuration with capability-based backend selection.
 * Supports provider-level defaults with model-specific overrides.
 *
 * @example atlas.config.ts
 * ```ts
 * import { defineConfig } from './src/shared/config.schema.js'
 *
 * export default defineConfig({
 *   backends: {
 *     'text-embedding': 'voyage',              // Provider default
 *     'code-embedding': 'voyage:voyage-code-3', // Specific model
 *     'json-completion': 'anthropic:haiku',    // Used for QNTM, consolidation
 *     'text-completion': 'ollama:ministral-3:3b',
 *   },
 *   logging: {
 *     level: 'info',
 *     modules: 'ingest:debug,llm:*:trace',
 *   }
 * })
 * ```
 */

import { z } from 'zod'
import {
  CONSOLIDATION_BASE_THRESHOLD,
  CONSOLIDATION_SCALE_FACTOR,
  CONSOLIDATION_SIMILARITY_THRESHOLD,
  CONSOLIDATION_POLL_INTERVAL_MS,
} from './config.js'

// ============================================
// Capability Identifiers
// ============================================

/**
 * LLM Capabilities - what the model can do
 */
export const LLMCapabilitySchema = z.enum([
  'text-completion',
  'json-completion',
  'code-completion',
  'extended-thinking',
  'vision',
  'tool-use',
  'streaming',
])

export type LLMCapability = z.infer<typeof LLMCapabilitySchema>

/**
 * Domain-specific capabilities - task types that use LLM capabilities
 * but may benefit from different backend selection
 */
export const DomainCapabilitySchema = z.enum([
  'qntm-generation', // QNTM key generation (uses json-completion)
  'consolidation', // Chunk consolidation classification (uses json-completion)
  'compaction', // Working memory compaction (uses json-completion)
  'query-expansion', // Search query expansion (uses json-completion)
])

export type DomainCapability = z.infer<typeof DomainCapabilitySchema>

/**
 * Embedding Capabilities
 */
export const EmbeddingCapabilitySchema = z.enum([
  'text-embedding',
  'code-embedding',
  'contextualized-embedding',
  'multimodal-embedding',
])

export type EmbeddingCapability = z.infer<typeof EmbeddingCapabilitySchema>

/**
 * Atlas-specific task capabilities
 *
 * Note: QNTM generation and consolidation use 'json-completion' capability.
 * They're just task-specific prompts, not separate capabilities.
 */
export const TaskCapabilitySchema = z.enum([
  'reranking', // Search result reranking (distinct capability with its own backends)
])

export type TaskCapability = z.infer<typeof TaskCapabilitySchema>

/**
 * All capabilities that can be configured
 */
export const CapabilitySchema = z.union([
  LLMCapabilitySchema,
  EmbeddingCapabilitySchema,
  TaskCapabilitySchema,
  DomainCapabilitySchema,
])

export type Capability = z.infer<typeof CapabilitySchema>

// ============================================
// Provider Identifiers
// ============================================

/**
 * Known providers with their model patterns
 */
export const ProviderSchema = z.enum([
  'anthropic', // Direct Anthropic API (requires ANTHROPIC_API_KEY)
  'claude-code', // Claude Code CLI (claude -p)
  'openai', // OpenAI API
  'ollama', // Local Ollama
  'voyage', // Voyage AI embeddings
])

export type Provider = z.infer<typeof ProviderSchema>

/**
 * Backend specifier patterns:
 * - "anthropic" - Provider default (auto-select model)
 * - "anthropic:sonnet" - Provider with model class
 * - "claude-code:haiku" - Specific model
 * - "ollama:auto" - Auto-select based on resources
 * - "ollama:mistral:7b" - Specific Ollama model
 * - "voyage:voyage-code-3" - Specific Voyage model
 */
export const BackendSpecifierSchema = z.string().refine(
  (val) => {
    const parts = val.split(':')
    const provider = parts[0]
    return ['anthropic', 'claude-code', 'ollama', 'voyage'].includes(provider ?? '')
  },
  { message: 'Invalid provider. Use: anthropic, claude-code, openai, ollama, or voyage' }
)

export type BackendSpecifier = z.infer<typeof BackendSpecifierSchema>

// ============================================
// Logging Configuration
// ============================================

export const LogLevelSchema = z.enum(['trace', 'debug', 'info', 'warn', 'error'])

export type LogLevel = z.infer<typeof LogLevelSchema>

export const LoggingConfigSchema = z
  .object({
    /**
     * Global log level fallback
     */
    level: LogLevelSchema.default('info'),

    /**
     * Module-specific log rules
     * Format: "module:level,module/*:level"
     * Example: "ingest:debug,qntm/*:trace,llm/batch:warn"
     */
    modules: z.string().optional(),
  })
  .partial()

export type LoggingConfig = z.infer<typeof LoggingConfigSchema>

// ============================================
// Backend Capability Mapping
// ============================================

/**
 * Maps capabilities to backend specifiers
 */
export const BackendMappingSchema = z.record(z.string(), BackendSpecifierSchema).optional()

export type BackendMapping = z.infer<typeof BackendMappingSchema>

// ============================================
// Domain Configuration Schemas
// ============================================

/**
 * Ingestion configuration
 */
export const IngestionConfigSchema = z
  .object({
    /**
     * Embedding strategy selection
     * - 'auto': Auto-detect based on content type and document length
     * - 'snippet': Always use snippet embeddings
     * - 'contextualized': Always use contextualized embeddings
     */
    embeddingStrategy: z.enum(['auto', 'snippet', 'contextualized']).default('auto'),

    /**
     * Upsert batch size (chunks per upsert call)
     * Higher = fewer API calls, but more memory usage
     */
    batchSize: z.number().min(1).max(500).default(50),

    /**
     * Upsert batch timeout (milliseconds)
     * Flush batch if no new chunks arrive within this time
     */
    batchTimeoutMs: z.number().min(1000).max(60000).default(15000),

    /**
     * Adaptive concurrency monitoring interval (milliseconds)
     * How often to check system pressure and adjust concurrency
     */
    monitoringIntervalMs: z.number().min(5000).max(120000).default(30000),

    /**
     * Initial QNTM generation concurrency
     * Adjusted at runtime based on system pressure
     */
    qntmConcurrency: z.number().min(1).max(32).default(8),

    /**
     * Minimum QNTM concurrency (floor during pressure)
     */
    qntmConcurrencyMin: z.number().min(1).max(16).default(2),

    /**
     * Maximum QNTM concurrency (ceiling when nominal)
     */
    qntmConcurrencyMax: z.number().min(2).max(64).default(16),
  })
  .partial()

export type IngestionConfig = z.infer<typeof IngestionConfigSchema>

/**
 * Search configuration
 */
export const SearchConfigSchema = z
  .object({
    /**
     * Rerank candidate multiplier (default: 3)
     * When reranking enabled, retrieves (limit × multiplier) candidates before reranking.
     * Higher = better recall but more expensive.
     */
    rerankCandidateMultiplier: z.number().min(1).max(10).default(3),
  })
  .partial()

export type SearchConfig = z.infer<typeof SearchConfigSchema>

/**
 * Consolidation configuration
 */
export const ConsolidationConfigSchema = z
  .object({
    /**
     * Similarity threshold for consolidation candidates (0-1)
     * Higher = more strict (only very similar chunks consolidated)
     */
    similarityThreshold: z.number().min(0).max(1).default(CONSOLIDATION_SIMILARITY_THRESHOLD),

    /**
     * Base threshold for triggering consolidation (chunks ingested)
     */
    baseThreshold: z.number().min(1).default(CONSOLIDATION_BASE_THRESHOLD),

    /**
     * Scale factor for dynamic threshold calculation
     * Formula: baseThreshold + (scaleFactor × collection_size)
     */
    scaleFactor: z.number().min(0).max(1).default(CONSOLIDATION_SCALE_FACTOR),

    /**
     * Poll interval for consolidation watchdog (milliseconds)
     */
    pollIntervalMs: z.number().min(1000).default(CONSOLIDATION_POLL_INTERVAL_MS),
  })
  .partial()

export type ConsolidationConfig = z.infer<typeof ConsolidationConfigSchema>

/**
 * Daemon configuration
 */
export const DaemonConfigSchema = z
  .object({
    /**
     * Auto-start schedulers when daemon starts
     */
    autoStart: z
      .object({
        consolidationWatchdog: z.boolean().default(true),
        systemPressureMonitor: z.boolean().default(true),
        fileWatcher: z.boolean().default(true), // Watches ~/.atlas by default
      })
      .partial()
      .default({
        consolidationWatchdog: true,
        systemPressureMonitor: true,
        fileWatcher: true,
      }),

    /**
     * File watcher configuration
     * Uses whitelist approach: only files with embeddable extensions are watched.
     */
    fileWatcher: z
      .object({
        /**
         * Directories to watch for new files.
         * Default: ['~/.atlas'] (changed from ~/.atlas/inbox to watch entire Atlas directory)
         */
        paths: z.array(z.string()).default(['~/.atlas']),
        /**
         * File patterns to watch (e.g., ['*.md', '*.ts']).
         * If not specified, defaults to all embeddable extensions from getAllEmbeddableExtensions().
         * Whitelist approach: only specified patterns are watched.
         */
        patterns: z.array(z.string()).optional(),
        /**
         * Patterns to ignore (e.g., ['*.tmp', '*.log']).
         * Empty by default - whitelist handles filtering.
         */
        ignorePatterns: z.array(z.string()).default([]),
      })
      .partial()
      .default({
        paths: ['~/.atlas'],
        ignorePatterns: [],
      }),

    /**
     * System pressure monitor interval (milliseconds)
     * Default: 30000 (30 seconds)
     */
    pressureMonitorIntervalMs: z.number().min(5000).default(30000),
  })
  .partial()

export type DaemonConfig = z.infer<typeof DaemonConfigSchema>

// ============================================
// Storage Tier Configuration
// ============================================

/**
 * PostgreSQL configuration (Metadata + Time-Series)
 *
 * REQUIRED - PostgreSQL is the only supported metadata backend.
 * Configure connection details here.
 */
export const PostgreSQLConfigSchema = z
  .object({
    /** PostgreSQL host */
    host: z.string().default('localhost'),
    /** PostgreSQL port */
    port: z.number().int().min(1).max(65535).default(5432),
    /** Database name */
    database: z.string().default('atlas'),
    /** Database user */
    user: z.string().default('atlas'),
    /** Database password (REQUIRED) */
    password: z.string().describe('Required - set via env or config'),
    /** Connection pool size */
    poolSize: z.number().int().min(1).max(100).default(20),
    /** Enable SSL/TLS */
    ssl: z.boolean().default(false),
    /** Connection timeout (milliseconds) */
    connectTimeoutMs: z.number().int().min(1000).default(30000),
    /** Idle connection timeout (milliseconds) */
    idleTimeoutMs: z.number().int().min(1000).default(30000),
  })
  .partial()

export type PostgreSQLConfig = z.infer<typeof PostgreSQLConfigSchema>

/**
 * TimescaleDB configuration (PostgreSQL extension)
 */
export const TimescaleDBConfigSchema = z
  .object({
    /** Enable TimescaleDB extension */
    enabled: z.boolean().default(true),
    /** Chunk time interval for hypertables (e.g., '1 day', '7 days') */
    chunkTimeInterval: z.string().default('1 day'),
    /** Compression policy after N days (0 = disabled) */
    compressionAfterDays: z.number().int().min(0).default(7),
    /** Retention policy in days (0 = disabled) */
    retentionDays: z.number().int().min(0).default(0),
  })
  .partial()

export type TimescaleDBConfig = z.infer<typeof TimescaleDBConfigSchema>

/**
 * Valkey/Redis configuration (Hot Data Cache)
 */
export const ValkeyConfigSchema = z
  .object({
    /** Valkey/Redis host */
    host: z.string().default('localhost'),
    /** Valkey/Redis port */
    port: z.number().int().min(1).max(65535).default(6379),
    /** Valkey/Redis password (optional for local dev) */
    password: z.string().optional(),
    /** Maximum memory (e.g., '2gb', '512mb') */
    maxMemory: z.string().default('2gb'),
    /** Eviction policy when maxMemory reached */
    evictionPolicy: z
      .enum(['allkeys-lru', 'volatile-lru', 'allkeys-lfu', 'volatile-lfu'])
      .default('allkeys-lru'),
    /** Key TTL for cached data (seconds, 0 = no expiration) */
    defaultTTL: z.number().int().min(0).default(3600),
  })
  .partial()

export type ValkeyConfig = z.infer<typeof ValkeyConfigSchema>

/**
 * Meilisearch configuration (Full-Text Search)
 */
export const MeilisearchConfigSchema = z
  .object({
    /** Meilisearch server URL */
    url: z.string().url().default('http://localhost:7700'),
    /** Master API key */
    masterKey: z.string().optional(),
    /** Index name for chunks */
    indexName: z.string().default('atlas_chunks'),
    /** Searchable attributes (field names) */
    searchableAttributes: z.array(z.string()).default(['original_text', 'file_path', 'qntm_keys']),
    /** Filterable attributes (for faceted search) */
    filterableAttributes: z
      .array(z.string())
      .default([
        'file_type',
        'consolidation_level',
        'content_type',
        'created_at',
        'importance',
        'memory_type',
      ]),
    /** Ranking rules */
    rankingRules: z
      .array(z.string())
      .default(['words', 'typo', 'proximity', 'attribute', 'sort', 'exactness']),
  })
  .partial()

export type MeilisearchConfig = z.infer<typeof MeilisearchConfigSchema>

/**
 * DuckDB configuration (Analytics + Parquet Export)
 */
export const DuckDBConfigSchema = z
  .object({
    /** Database file path (embedded, not a service) */
    dbPath: z.string().default('~/.atlas/daemon/atlas_analytics.duckdb'),
    /** Enable analytics queries */
    enableAnalytics: z.boolean().default(true),
    /** Enable Parquet export */
    enableParquetExport: z.boolean().default(true),
    /** Parquet export directory */
    parquetExportDir: z.string().default('~/.atlas/exports'),
    /** Memory limit for queries (e.g., '4GB') */
    memoryLimit: z.string().default('2GB'),
    /** Number of threads for parallel queries */
    threads: z.number().int().min(1).default(4),
  })
  .partial()

export type DuckDBConfig = z.infer<typeof DuckDBConfigSchema>

/**
 * Qdrant configuration (Vector Search)
 */
export const QdrantConfigSchema = z
  .object({
    /** Qdrant server URL */
    url: z.string().url().default('http://localhost:6333'),
    /** Qdrant API key (optional, for Qdrant Cloud) */
    apiKey: z.string().optional(),
    /** Collection name */
    collection: z.string().default('atlas'),
    /** Enable HNSW index (disable for batch ingestion) */
    enableHNSW: z.boolean().default(true),
    /** Timeout for API requests (milliseconds) */
    timeout: z.number().int().min(1000).default(30000),
  })
  .partial()

export type QdrantConfig = z.infer<typeof QdrantConfigSchema>

/**
 * Storage tier configuration
 */
export const StorageConfigSchema = z
  .object({
    /** PostgreSQL configuration (REQUIRED - no SQLite fallback) */
    postgres: PostgreSQLConfigSchema,
    /** TimescaleDB configuration (requires PostgreSQL) */
    timescale: TimescaleDBConfigSchema.optional(),
    /** Cache backend ('none', 'redis', 'valkey') */
    cache: z.enum(['none', 'redis', 'valkey']).default('none'),
    /** Valkey/Redis configuration (used when cache = 'redis' or 'valkey') */
    valkey: ValkeyConfigSchema.optional(),
    /** Analytics backend ('none', 'duckdb') */
    analytics: z.enum(['none', 'duckdb']).default('none'),
    /** DuckDB configuration (used when analytics = 'duckdb') */
    duckdb: DuckDBConfigSchema.optional(),
    /** Full-text search backend ('none', 'meilisearch') */
    fulltext: z.enum(['none', 'meilisearch']).default('none'),
    /** Meilisearch configuration (used when fulltext = 'meilisearch') */
    meilisearch: MeilisearchConfigSchema.optional(),
    /** Vector search configuration (Qdrant) */
    qdrant: QdrantConfigSchema,
  })
  .partial()
  .refine(
    (config) => {
      // PostgreSQL config required (always)
      if (!config.postgres?.password) {
        return false
      }
      return true
    },
    { message: 'PostgreSQL configuration required - add storage.postgres to atlas.config.ts' }
  )
  .refine(
    (config) => {
      // Valkey config required if cache is redis/valkey
      if ((config.cache === 'redis' || config.cache === 'valkey') && !config.valkey?.host) {
        return false
      }
      return true
    },
    { message: 'Valkey configuration required when cache backend is enabled' }
  )
  .refine(
    (config) => {
      // Meilisearch config required if fulltext = 'meilisearch'
      if (config.fulltext === 'meilisearch' && !config.meilisearch?.masterKey) {
        return false
      }
      return true
    },
    { message: 'Meilisearch configuration required when fulltext backend is meilisearch' }
  )

export type StorageConfig = z.infer<typeof StorageConfigSchema>

// ============================================
// Main Configuration Schema
// ============================================

export const AtlasConfigSchema = z.object({
  /**
   * Capability → Backend mapping
   *
   * Keys are capabilities (what you need done).
   * Values are backend specifiers (who does it).
   *
   * @example
   * ```ts
   * backends: {
   *   'text-embedding': 'voyage',
   *   'code-embedding': 'voyage:voyage-code-3',
   *   'json-completion': 'anthropic:haiku', // Used for QNTM, consolidation
   *   'text-completion': 'ollama:auto',
   * }
   * ```
   */
  backends: BackendMappingSchema.optional(),

  /**
   * Storage tier configuration
   */
  storage: StorageConfigSchema.optional(),

  /**
   * Logging configuration
   */
  logging: LoggingConfigSchema.optional(),

  /**
   * Ingestion configuration
   */
  ingestion: IngestionConfigSchema.optional(),

  /**
   * Search configuration
   */
  search: SearchConfigSchema.optional(),

  /**
   * Consolidation configuration
   */
  consolidation: ConsolidationConfigSchema.optional(),

  /**
   * Daemon configuration
   */
  daemon: DaemonConfigSchema.optional(),
})

export type AtlasConfig = z.infer<typeof AtlasConfigSchema>

// ============================================
// Config Helpers
// ============================================

/**
 * Define and validate an Atlas configuration
 */
export function defineConfig(config: AtlasConfig): AtlasConfig {
  return AtlasConfigSchema.parse(config)
}

/**
 * Default configuration (used when no atlas.config.ts exists)
 *
 * Research-backed defaults (2025-12-31):
 * - Embeddings: voyage-3-large outperforms OpenAI-v3-large by 9.74%
 * - Code embeddings: voyage-code-3 outperforms OpenAI-v3-large by 13.80%
 * - LLM: ministral:3b runs on 1.8GB VRAM, good for QNTM key generation
 * - Reranking: rerank-2.5 is 1.85% better than rerank-2 at same price
 */
export const defaultConfig: AtlasConfig = {
  backends: {
    'text-embedding': 'voyage:voyage-3-large',
    'code-embedding': 'voyage:voyage-code-3',
    'contextualized-embedding': 'voyage:voyage-context-3',
    'text-completion': 'ollama:ministral-3:3b',
    'json-completion': 'ollama:ministral-3:3b',
    reranking: 'voyage:rerank-2.5',
  },
  logging: {
    level: 'info',
  },
}

// ============================================
// Capability → Provider Compatibility
// ============================================

/**
 * Which providers support which capabilities
 * Used for validation when user specifies backend
 *
 * Note: QNTM generation and consolidation use 'json-completion'.
 * Configure 'json-completion' to control which backend handles these tasks.
 */
export const providerCapabilities: Record<Provider, Capability[]> = {
  anthropic: [
    'text-completion',
    'json-completion',
    'code-completion',
    'extended-thinking',
    'vision',
    'tool-use',
    'streaming',
  ],
  'claude-code': [
    'text-completion',
    'json-completion',
    'code-completion',
    'vision',
    'tool-use',
    'streaming',
  ],
  openai: [
    'text-completion',
    'json-completion',
    'code-completion',
    'vision',
    'tool-use',
    'streaming',
  ],
  ollama: [
    'text-completion',
    'json-completion',
    'code-completion',
    'extended-thinking',
    'streaming',
    'vision',
    'tool-use',
    'text-embedding',
    'code-embedding',
    'contextualized-embedding',
  ],
  voyage: ['text-embedding', 'code-embedding', 'contextualized-embedding', 'reranking'],
}

/**
 * Validate that a provider supports a capability
 */
export function validateProviderCapability(provider: Provider, capability: Capability): boolean {
  return providerCapabilities[provider]?.includes(capability) ?? false
}

/**
 * Parse a backend specifier into provider and model
 * @throws Error if provider is not recognized
 */
export function parseBackendSpecifier(specifier: BackendSpecifier): {
  provider: Provider
  model?: string
} {
  const parts = specifier.split(':')
  const provider = parts[0]

  // Validate provider
  if (!ProviderSchema.safeParse(provider).success) {
    throw new Error(
      `Invalid provider '${provider}' in backend specifier '${specifier}'. ` +
        `Valid providers: ${ProviderSchema.options.join(', ')}`
    )
  }

  const model = parts.slice(1).join(':') || undefined

  return { provider: provider as Provider, model }
}
