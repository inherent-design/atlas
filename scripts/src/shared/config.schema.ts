/**
 * Atlas Configuration Schema (Draft)
 *
 * Zod-validated configuration with capability-based backend selection.
 * Supports provider-level defaults with model-specific overrides.
 *
 * @example atlas.config.ts
 * ```ts
 * import { defineConfig } from './src/shared/config.schema'
 *
 * export default defineConfig({
 *   backends: {
 *     'text-embedding': 'voyage',           // Provider default
 *     'code-embedding': 'voyage:voyage-code-3',  // Specific model
 *     'qntm-generation': 'claude-code:haiku',    // Specific model
 *     'text-completion': 'ollama:auto',     // Auto-select based on resources
 *   },
 *   resources: {
 *     ollama: {
 *       memoryTarget: 0.30,  // 30% of available RAM
 *       gpuLayers: 'auto',   // Auto-detect GPU
 *     }
 *   },
 *   logging: {
 *     level: 'info',
 *     modules: 'ingest:debug,qntm/*:trace',
 *   }
 * })
 * ```
 */

import { z } from 'zod'

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
 */
export const TaskCapabilitySchema = z.enum([
  'qntm-generation',    // QNTM semantic key generation
  'consolidation',      // Chunk consolidation/summarization
  'reranking',          // Search result reranking
])

export type TaskCapability = z.infer<typeof TaskCapabilitySchema>

/**
 * All capabilities that can be configured
 */
export const CapabilitySchema = z.union([
  LLMCapabilitySchema,
  EmbeddingCapabilitySchema,
  TaskCapabilitySchema,
])

export type Capability = z.infer<typeof CapabilitySchema>

// ============================================
// Provider Identifiers
// ============================================

/**
 * Known providers with their model patterns
 */
export const ProviderSchema = z.enum([
  'anthropic',      // Direct Anthropic API (requires ANTHROPIC_API_KEY)
  'claude-code',    // Claude Code CLI (claude -p)
  'openai',         // OpenAI API
  'ollama',         // Local Ollama
  'voyage',         // Voyage AI embeddings
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
    return ['anthropic', 'claude-code', 'openai', 'ollama', 'voyage'].includes(provider ?? '')
  },
  { message: 'Invalid provider. Use: anthropic, claude-code, openai, ollama, or voyage' }
)

export type BackendSpecifier = z.infer<typeof BackendSpecifierSchema>

// ============================================
// Resource Configuration
// ============================================

/**
 * Ollama resource management
 */
export const OllamaResourceConfigSchema = z.object({
  /**
   * Target memory usage as fraction of available RAM (0.0 - 1.0)
   * Default: 0.30 (30%)
   */
  memoryTarget: z.number().min(0.1).max(0.9).default(0.30),

  /**
   * GPU layer configuration
   * - 'auto': Auto-detect based on VRAM
   * - 'none': CPU only
   * - number: Explicit layer count
   */
  gpuLayers: z.union([z.literal('auto'), z.literal('none'), z.number()]).default('auto'),

  /**
   * Prefer quantization level when auto-selecting
   * Lower = smaller/faster, higher = better quality
   */
  preferredQuantization: z.enum(['q4', 'q5', 'q8', 'fp16']).optional(),
}).partial()

export type OllamaResourceConfig = z.infer<typeof OllamaResourceConfigSchema>

/**
 * All resource configurations
 */
export const ResourceConfigSchema = z.object({
  ollama: OllamaResourceConfigSchema.optional(),
}).partial()

export type ResourceConfig = z.infer<typeof ResourceConfigSchema>

// ============================================
// Logging Configuration
// ============================================

export const LogLevelSchema = z.enum(['trace', 'debug', 'info', 'warn', 'error'])

export type LogLevel = z.infer<typeof LogLevelSchema>

export const LoggingConfigSchema = z.object({
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
}).partial()

export type LoggingConfig = z.infer<typeof LoggingConfigSchema>

// ============================================
// Backend Capability Mapping
// ============================================

/**
 * Maps capabilities to backend specifiers
 */
export const BackendMappingSchema = z.record(
  z.string(),
  BackendSpecifierSchema
).optional()

export type BackendMapping = z.infer<typeof BackendMappingSchema>

// ============================================
// Domain Configuration Schemas
// ============================================

/**
 * Ingestion configuration
 */
export const IngestionConfigSchema = z.object({
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
}).partial()

export type IngestionConfig = z.infer<typeof IngestionConfigSchema>

/**
 * Search configuration
 */
export const SearchConfigSchema = z.object({
  /**
   * Rerank candidate multiplier (default: 3)
   * When reranking enabled, retrieves (limit × multiplier) candidates before reranking.
   * Higher = better recall but more expensive.
   */
  rerankCandidateMultiplier: z.number().min(1).max(10).default(3),
}).partial()

export type SearchConfig = z.infer<typeof SearchConfigSchema>

/**
 * Consolidation configuration
 */
export const ConsolidationConfigSchema = z.object({
  /**
   * Similarity threshold for consolidation candidates (0-1)
   * Higher = more strict (only very similar chunks consolidated)
   */
  similarityThreshold: z.number().min(0).max(1).default(0.95),

  /**
   * Base threshold for triggering consolidation (documents ingested)
   */
  baseThreshold: z.number().min(1).default(100),

  /**
   * Scale factor for dynamic threshold calculation
   * Formula: baseThreshold + (scaleFactor × collection_size)
   */
  scaleFactor: z.number().min(0).max(1).default(0.05),

  /**
   * Poll interval for consolidation watchdog (milliseconds)
   * Default: 180000 (3 minutes)
   */
  pollIntervalMs: z.number().min(1000).default(180000),
}).partial()

export type ConsolidationConfig = z.infer<typeof ConsolidationConfigSchema>

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
   *   'qntm-generation': 'claude-code:haiku',
   *   'text-completion': 'ollama:auto',
   * }
   * ```
   */
  backends: BackendMappingSchema.optional(),

  /**
   * Resource constraints and auto-selection behavior
   */
  resources: ResourceConfigSchema.optional(),

  /**
   * Logging configuration
   */
  logging: LoggingConfigSchema.optional(),

  /**
   * Qdrant configuration
   */
  qdrant: z.object({
    url: z.string().url().default('http://localhost:6333'),
    collection: z.string().default('atlas'),
  }).partial().optional(),

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
    'qntm-generation': 'ollama:ministral-3:3b',
    'reranking': 'voyage:rerank-2.5',
  },
  resources: {
    ollama: {
      memoryTarget: 0.30,
      gpuLayers: 'auto',
    },
  },
  logging: {
    level: 'info',
  },
}

// ============================================
// Model Recommendations by VRAM Tier
// ============================================

/**
 * VRAM tier definitions for Ollama model auto-selection.
 * Based on research of Q4_K_M quantization requirements.
 *
 * Formula: VRAM (GB) ≈ Parameters (B) × 0.57 (Q4_K_M)
 */
export const vramTiers = {
  /**
   * Tier 1: Ultra-lightweight (<1GB VRAM)
   * Best for: Classification, QNTM key generation, embedded systems
   */
  tier1: {
    minVram: 0,
    maxVram: 1,
    llmModels: ['qwen2.5-coder:0.5b', 'tinyllama:1.1b', 'smollm2:360m'],
    embeddingModels: ['all-minilm:l6-v2', 'snowflake-arctic-embed:xs'],
    recommended: {
      'json-completion': 'qwen2.5-coder:0.5b', // 398MB
      'qntm-generation': 'qwen2.5-coder:0.5b',
      'text-embedding': 'all-minilm:l6-v2', // 46MB
    },
  },

  /**
   * Tier 2: Small (1-4GB VRAM)
   * Best for: General text, edge deployment
   */
  tier2: {
    minVram: 1,
    maxVram: 4,
    llmModels: ['ministral-3:3b', 'phi3:3.8b', 'gemma2:2b'],
    embeddingModels: ['nomic-embed-text', 'granite-embedding:30m'],
    recommended: {
      'text-completion': 'ministral-3:3b', // 1.8GB
      'json-completion': 'ministral-3:3b',
      'qntm-generation': 'ministral-3:3b',
      'text-embedding': 'nomic-embed-text', // 262MB
    },
  },

  /**
   * Tier 3: Medium (4-8GB VRAM)
   * Best for: Code generation, general purpose
   */
  tier3: {
    minVram: 4,
    maxVram: 8,
    llmModels: ['mistral:7b', 'qwen2.5-coder:7b', 'deepseek-r1:8b', 'llama3.1:8b'],
    embeddingModels: ['mxbai-embed-large', 'bge-large'],
    recommended: {
      'text-completion': 'llama3.1:8b', // 4.1GB
      'code-completion': 'qwen2.5-coder:7b', // 4.7GB
      'json-completion': 'mistral:7b', // 4.4GB
      'qntm-generation': 'mistral:7b',
      'text-embedding': 'mxbai-embed-large', // 670MB, MTEB 64.68
    },
  },

  /**
   * Tier 4: Large (8-16GB VRAM)
   * Best for: Complex reasoning, production code
   */
  tier4: {
    minVram: 8,
    maxVram: 16,
    llmModels: ['deepseek-r1:14b', 'phi4:14b', 'qwen2.5-coder:14b'],
    embeddingModels: ['bge-m3', 'qwen3-embedding:0.6b'],
    recommended: {
      'text-completion': 'deepseek-r1:14b', // 8GB, strong reasoning
      'code-completion': 'qwen2.5-coder:14b', // 9GB
      'extended-thinking': 'deepseek-r1:14b',
      'text-embedding': 'bge-m3', // 1.06GB, 8192 context
    },
  },

  /**
   * Tier 5: XL (16-32GB VRAM)
   * Best for: Maximum quality, complex codebases
   */
  tier5: {
    minVram: 16,
    maxVram: 32,
    llmModels: ['qwen2.5-coder:32b', 'codellama:34b', 'deepseek-r1:32b'],
    embeddingModels: ['qwen3-embedding:4b'],
    recommended: {
      'code-completion': 'qwen2.5-coder:32b', // 20GB
      'extended-thinking': 'deepseek-r1:32b', // 18GB
      'text-embedding': 'qwen3-embedding:4b', // 8GB, 32K context
    },
  },

  /**
   * Tier 6: XXL (32GB+ VRAM)
   * Best for: Frontier capability, research
   */
  tier6: {
    minVram: 32,
    maxVram: Infinity,
    llmModels: ['llama3.3:70b', 'qwen3:70b', 'deepseek-r1:70b'],
    embeddingModels: ['qwen3-embedding:8b'],
    recommended: {
      'text-completion': 'llama3.3:70b', // 43GB
      'code-completion': 'qwen3:70b', // 40GB
      'extended-thinking': 'deepseek-r1:70b', // 40GB
      'text-embedding': 'qwen3-embedding:8b', // 16GB, MTEB #1 multilingual
    },
  },
} as const

export type VramTier = keyof typeof vramTiers

/**
 * Get recommended Ollama model for a capability given available VRAM
 */
export function getRecommendedOllamaModel(
  capability: Capability,
  availableVramGB: number
): string | undefined {
  // Find highest tier that fits in available VRAM
  const tiers = [
    vramTiers.tier6,
    vramTiers.tier5,
    vramTiers.tier4,
    vramTiers.tier3,
    vramTiers.tier2,
    vramTiers.tier1,
  ]

  for (const tier of tiers) {
    if (availableVramGB >= (tier.minVram ?? 0)) {
      return tier.recommended[capability as keyof typeof tier.recommended]
    }
  }

  return undefined
}

// ============================================
// Capability → Provider Compatibility
// ============================================

/**
 * Which providers support which capabilities
 * Used for validation when user specifies backend
 */
export const providerCapabilities: Record<Provider, Capability[]> = {
  anthropic: [
    'text-completion', 'json-completion', 'code-completion',
    'extended-thinking', 'vision', 'tool-use', 'streaming',
    'qntm-generation', 'consolidation',
  ],
  'claude-code': [
    'text-completion', 'json-completion', 'code-completion',
    'vision', 'tool-use', 'streaming',
    'qntm-generation', 'consolidation',
  ],
  openai: [
    'text-completion', 'json-completion', 'code-completion',
    'vision', 'tool-use', 'streaming',
    'qntm-generation', 'consolidation',
  ],
  ollama: [
    'text-completion', 'json-completion', 'code-completion',
    'extended-thinking', 'streaming',
    'text-embedding', 'code-embedding', 'contextualized-embedding',
    'qntm-generation', 'consolidation',
  ],
  voyage: [
    'text-embedding', 'code-embedding', 'contextualized-embedding',
    'reranking',
  ],
}

/**
 * Validate that a provider supports a capability
 */
export function validateProviderCapability(
  provider: Provider,
  capability: Capability
): boolean {
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
