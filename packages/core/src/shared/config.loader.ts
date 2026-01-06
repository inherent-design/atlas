/**
 * Atlas Config Loader
 *
 * Loads atlas.config.ts from project root, merges with defaults.
 * Validates with Zod schema.
 */

import { existsSync } from 'node:fs'
import { join } from 'node:path'
import {
  AtlasConfigSchema,
  defaultConfig,
  type AtlasConfig,
  parseBackendSpecifier,
  validateProviderCapability,
  type Capability,
} from './config.schema'
import { createLogger } from './logger'

const log = createLogger('config-loader')

// Singleton config instance
let globalConfig: AtlasConfig | null = null

/**
 * Try to load user config from atlas.config.ts
 *
 * Search order:
 * 1. Explicit configPath (if provided via -c flag)
 * 2. Current working directory
 * 3. User's home directory (~/.atlas/config.ts) - system-wide config
 */
async function tryLoadUserConfig(configPath?: string): Promise<Partial<AtlasConfig>> {
  const homedir = require('os').homedir()

  // Resolve config path - check multiple locations
  const paths = [
    configPath,
    join(process.cwd(), 'atlas.config.ts'),
    join(process.cwd(), 'atlas.config.js'),
    // System-wide config in ~/.atlas/
    join(homedir, '.atlas', 'config.ts'),
    join(homedir, '.atlas', 'config.js'),
  ].filter(Boolean) as string[]

  for (const path of paths) {
    if (existsSync(path)) {
      try {
        log.debug('Loading config from', { path })

        // Dynamic import (supports both .ts and .js)
        const module = await import(path)
        const userConfig = module.default || module

        // Only log if config has keys (not empty object)
        const keys = Object.keys(userConfig)
        if (keys.length > 0) {
          log.info('User config loaded', { path, keys })
        } else {
          log.debug('Empty config file found', { path })
        }
        return userConfig
      } catch (error) {
        log.warn('Failed to load config file', { path, error: (error as Error).message })
      }
    }
  }

  log.debug('No user config found, using defaults')
  return {}
}

/**
 * Detect environment-based provider defaults
 * Check for API keys to enable providers
 */
function getEnvironmentDefaults(): Partial<AtlasConfig> {
  const envDefaults: Partial<AtlasConfig> = { backends: {} }

  // Check for Voyage API key → enable Voyage backends
  if (process.env.VOYAGE_API_KEY) {
    log.debug('VOYAGE_API_KEY detected, enabling Voyage backends')
    envDefaults.backends = {
      ...envDefaults.backends,
      'text-embedding': 'voyage:voyage-3-large',
      'code-embedding': 'voyage:voyage-code-3',
      'contextualized-embedding': 'voyage:voyage-context-3',
      reranking: 'voyage:rerank-2.5',
    }
  } else {
    log.debug('VOYAGE_API_KEY not found, using Ollama for embeddings')
    envDefaults.backends = {
      ...envDefaults.backends,
      'text-embedding': 'ollama:nomic-embed-text',
      'code-embedding': 'ollama:nomic-embed-text',
      'contextualized-embedding': 'ollama:nomic-embed-text',
    }
  }

  // Check for Anthropic API key → enable Anthropic API backend
  if (process.env.ANTHROPIC_API_KEY) {
    log.debug('ANTHROPIC_API_KEY detected, enabling Anthropic API LLM')
    envDefaults.backends = {
      ...envDefaults.backends,
      'text-completion': 'anthropic:haiku',
      'json-completion': 'anthropic:haiku',
    }
  } else {
    log.debug('ANTHROPIC_API_KEY not found, using Ollama for LLM')
    envDefaults.backends = {
      ...envDefaults.backends,
      'text-completion': 'ollama:ministral-3:3b',
      'json-completion': 'ollama:ministral-3:3b',
    }
  }

  return envDefaults
}

/**
 * Merge user config with defaults
 * Precedence: User config > Environment-detected providers > Default config
 */
function mergeConfig(defaults: AtlasConfig, user: Partial<AtlasConfig>): AtlasConfig {
  // Get environment-based defaults
  const envDefaults = getEnvironmentDefaults()

  // Merge in order: defaults → env-detected → user (user takes precedence)
  const merged: AtlasConfig = {
    backends: {
      ...defaults.backends,
      ...envDefaults.backends,
      ...user.backends,
    },
    logging: {
      ...defaults.logging,
      ...envDefaults.logging,
      ...user.logging,
    },
  }

  // Validate merged config
  try {
    const validated = AtlasConfigSchema.parse(merged)

    // Cross-check provider-capability assignments
    if (validated.backends) {
      for (const [capability, specifier] of Object.entries(validated.backends)) {
        const { provider } = parseBackendSpecifier(specifier)
        if (!validateProviderCapability(provider, capability as Capability)) {
          throw new Error(
            `Invalid config: Provider '${provider}' does not support capability '${capability}'. ` +
              `Valid capabilities for ${provider}: ${require('./config.schema').providerCapabilities[provider]?.join(', ')}`
          )
        }
      }
      log.debug('Provider-capability validation passed')
    }

    return validated
  } catch (error) {
    log.error('Invalid config after merge', { error: (error as Error).message })
    throw new Error(`Config validation failed: ${(error as Error).message}`)
  }
}

/**
 * Load config from atlas.config.ts or use defaults
 */
export async function loadConfig(configPath?: string): Promise<AtlasConfig> {
  if (globalConfig) {
    log.debug('Returning cached config')
    return globalConfig
  }

  // Try to load user config
  const userConfig = await tryLoadUserConfig(configPath)

  // Merge with defaults (user config takes precedence)
  globalConfig = mergeConfig(defaultConfig, userConfig)

  log.info('Config loaded', {
    backends: Object.keys(globalConfig.backends || {}),
    logLevel: globalConfig.logging?.level,
  })

  return globalConfig
}

/**
 * Get current config (must call loadConfig first)
 * Returns defaults if not loaded yet
 */
export function getConfig(): AtlasConfig {
  if (!globalConfig) {
    log.debug('Config not loaded, returning defaults')
    return defaultConfig
  }
  return globalConfig
}

/**
 * Get resolved config file path (or null if not found)
 */
export function getConfigPath(): string | null {
  const paths = [join(process.cwd(), 'atlas.config.ts'), join(process.cwd(), 'atlas.config.js')]

  for (const path of paths) {
    if (existsSync(path)) {
      return path
    }
  }

  return null
}

/**
 * Apply runtime overrides to config (for CLI flags)
 * Creates a new config object instead of mutating global
 */
export function applyRuntimeOverrides(overrides: Partial<AtlasConfig>): void {
  if (!globalConfig) {
    log.warn('Cannot apply overrides: config not loaded yet')
    return
  }

  // Create new config with deep merge of overrides
  const merged: AtlasConfig = {
    backends: {
      ...globalConfig.backends,
      ...overrides.backends,
    },
    logging: {
      ...globalConfig.logging,
      ...overrides.logging,
    },
  }

  // Validate provider-capability assignments for new backends
  if (overrides.backends) {
    for (const [capability, specifier] of Object.entries(overrides.backends)) {
      const { provider } = parseBackendSpecifier(specifier)
      if (!validateProviderCapability(provider, capability as Capability)) {
        throw new Error(
          `Invalid runtime override: Provider '${provider}' does not support capability '${capability}'`
        )
      }
    }
  }

  // Log config diff at debug level
  log.debug('Applying runtime overrides', { overrides })
  if (overrides.backends) {
    for (const [capability, newValue] of Object.entries(overrides.backends)) {
      const oldValue = globalConfig.backends?.[capability as Capability]
      if (oldValue !== newValue) {
        log.debug(`Backend override: ${capability}`, { from: oldValue, to: newValue })
      }
    }
  }

  // Replace global config (immutable pattern)
  globalConfig = merged
  log.debug('Runtime overrides applied')
}

/**
 * Reset config (for testing)
 */
export function _resetConfig(): void {
  globalConfig = null
  log.debug('Config reset')
}
