/**
 * Atlas Doctor - Environment Diagnostics
 *
 * Checks system configuration, service availability, and backend readiness.
 * Used by `atlas doctor` CLI command.
 */

import { createLogger } from '../../shared/logger.js'
import { QDRANT_URL, OLLAMA_URL, VOYAGE_API_KEY } from '../../shared/config.js'
import { getPrimaryCollectionName } from '../../shared/utils.js'
import { getFileTracker } from '../tracking/index.js'
import { getStorageService } from '../storage/index.js'
import { getConfig } from '../../shared/config.loader.js'

const log = createLogger('doctor')

// ============================================
// Types
// ============================================

export type CheckStatus = 'ok' | 'warning' | 'error' | 'not_configured'

export interface EnvironmentCheck {
  name: string
  status: CheckStatus
  value?: string
  message?: string
}

export interface ServiceCheck {
  name: string
  status: CheckStatus
  details?: string
  version?: string
  extra?: Record<string, unknown>
}

export interface ModelCheck {
  name: string
  status: CheckStatus
  available: boolean
  configured: boolean
}

export interface DiagnosticReport {
  environment: EnvironmentCheck[]
  services: ServiceCheck[]
  models: {
    ollama: {
      available: string[]
      missing: string[]
    }
  }
  tracking: {
    path: string
    sources: number
    activeChunks: number
    supersededChunks: number
  } | null
  configuration: {
    path: string | null
    valid: boolean
    error?: string
  }
  summary: {
    ok: number
    warning: number
    error: number
    notConfigured: number
  }
}

// ============================================
// Environment Checks
// ============================================

async function checkEnvironment(): Promise<EnvironmentCheck[]> {
  const checks: EnvironmentCheck[] = []

  // VOYAGE_API_KEY
  checks.push({
    name: 'VOYAGE_API_KEY',
    status: VOYAGE_API_KEY ? 'ok' : 'not_configured',
    value: VOYAGE_API_KEY ? 'set' : 'not set',
  })

  // ANTHROPIC_API_KEY
  const anthropicKey = process.env.ANTHROPIC_API_KEY
  checks.push({
    name: 'ANTHROPIC_API_KEY',
    status: anthropicKey ? 'ok' : 'not_configured',
    value: anthropicKey ? 'set' : 'not set',
  })

  // QDRANT_URL
  checks.push({
    name: 'QDRANT_URL',
    status: 'ok',
    value: QDRANT_URL,
  })

  // OLLAMA_URL
  checks.push({
    name: 'OLLAMA_URL',
    status: 'ok',
    value: OLLAMA_URL,
  })

  return checks
}

// ============================================
// Service Checks
// ============================================

async function checkQdrant(): Promise<ServiceCheck> {
  try {
    const response = await fetch(`${QDRANT_URL}/cluster`, {
      signal: AbortSignal.timeout(3000),
    })

    if (!response.ok) {
      return {
        name: 'Qdrant',
        status: 'error',
        details: `HTTP ${response.status}: ${response.statusText}`,
      }
    }

    const data = (await response.json()) as { version?: string }

    // Check if collection exists
    const collectionResponse = await fetch(`${QDRANT_URL}/collections/${getPrimaryCollectionName()}`, {
      signal: AbortSignal.timeout(3000),
    })

    if (collectionResponse.ok) {
      const collectionData = (await collectionResponse.json()) as {
        result?: {
          points_count?: number
          vectors_count?: number
        }
      }

      return {
        name: 'Qdrant',
        status: 'ok',
        version: data.version,
        details: `collection '${getPrimaryCollectionName()}' exists`,
        extra: {
          points: collectionData.result?.points_count ?? 0,
        },
      }
    }

    return {
      name: 'Qdrant',
      status: 'warning',
      version: data.version,
      details: `collection '${getPrimaryCollectionName()}' does not exist`,
    }
  } catch (error) {
    return {
      name: 'Qdrant',
      status: 'error',
      details: (error as Error).message,
    }
  }
}

async function checkOllama(): Promise<ServiceCheck> {
  try {
    const response = await fetch(`${OLLAMA_URL}/api/tags`, {
      signal: AbortSignal.timeout(3000),
    })

    if (!response.ok) {
      return {
        name: 'Ollama',
        status: 'error',
        details: `HTTP ${response.status}: ${response.statusText}`,
      }
    }

    const data = (await response.json()) as { models?: Array<{ name: string }> }
    const modelCount = data.models?.length ?? 0

    return {
      name: 'Ollama',
      status: 'ok',
      details: `${modelCount} models available`,
      extra: {
        models: data.models?.map((m) => m.name) ?? [],
      },
    }
  } catch (error) {
    return {
      name: 'Ollama',
      status: 'error',
      details: (error as Error).message,
    }
  }
}

async function checkVoyage(): Promise<ServiceCheck> {
  if (!VOYAGE_API_KEY) {
    return {
      name: 'Voyage',
      status: 'not_configured',
      details: 'VOYAGE_API_KEY not set',
    }
  }

  try {
    // Use the VoyageSnippetBackend's isAvailable method
    const { VoyageSnippetBackend } = await import('../embedding/backends/voyage')
    const backend = new VoyageSnippetBackend()
    const available = await backend.isAvailable()

    if (available) {
      return {
        name: 'Voyage',
        status: 'ok',
        details: 'API key valid',
      }
    }

    return {
      name: 'Voyage',
      status: 'error',
      details: 'API key invalid or service unavailable',
    }
  } catch (error) {
    return {
      name: 'Voyage',
      status: 'error',
      details: (error as Error).message,
    }
  }
}

async function checkAnthropic(): Promise<ServiceCheck> {
  const apiKey = process.env.ANTHROPIC_API_KEY

  if (!apiKey) {
    return {
      name: 'Anthropic',
      status: 'not_configured',
      details: 'ANTHROPIC_API_KEY not set',
    }
  }

  try {
    // Try to import and check availability
    const { AnthropicBackend } = await import('../llm/backends/anthropic')
    const backend = new AnthropicBackend('haiku-4.5')
    const available = await backend.isAvailable()

    if (available) {
      return {
        name: 'Anthropic',
        status: 'ok',
        details: 'API key valid',
      }
    }

    return {
      name: 'Anthropic',
      status: 'error',
      details: 'API key invalid or service unavailable',
    }
  } catch (error) {
    return {
      name: 'Anthropic',
      status: 'error',
      details: (error as Error).message,
    }
  }
}

async function checkServices(): Promise<ServiceCheck[]> {
  const [qdrant, ollama, voyage, anthropic] = await Promise.all([
    checkQdrant(),
    checkOllama(),
    checkVoyage(),
    checkAnthropic(),
  ])

  return [qdrant, ollama, voyage, anthropic]
}

// ============================================
// Model Checks
// ============================================

async function checkOllamaModels(): Promise<{
  available: string[]
  missing: string[]
}> {
  try {
    const response = await fetch(`${OLLAMA_URL}/api/tags`, {
      signal: AbortSignal.timeout(3000),
    })

    if (!response.ok) {
      return { available: [], missing: [] }
    }

    const data = (await response.json()) as { models?: Array<{ name: string }> }
    const available = data.models?.map((m) => m.name) ?? []

    // Check configured models from config
    const { getConfig } = await import('../../shared/config.loader')
    const config = getConfig()

    const configuredModels = new Set<string>()

    // Extract Ollama models from backend config
    for (const [_cap, backend] of Object.entries(config.backends ?? {})) {
      if (backend.startsWith('ollama:')) {
        const modelName = backend.split(':').slice(1).join(':')
        if (modelName && modelName !== 'auto') {
          configuredModels.add(modelName)
        }
      }
    }

    const missing = Array.from(configuredModels).filter(
      (model) => !available.some((a) => a.startsWith(model))
    )

    return { available, missing }
  } catch (error) {
    log.warn('Failed to check Ollama models', { error: (error as Error).message })
    return { available: [], missing: [] }
  }
}

// ============================================
// Configuration Check
// ============================================

async function checkConfiguration(): Promise<{
  path: string | null
  valid: boolean
  error?: string
}> {
  try {
    const { getConfig, getConfigPath } = await import('../../shared/config.loader')
    const configPath = getConfigPath()
    const config = getConfig()

    // Config is already validated by Zod during load
    return {
      path: configPath,
      valid: true,
    }
  } catch (error) {
    return {
      path: null,
      valid: false,
      error: (error as Error).message,
    }
  }
}

// ============================================
// Tracking Database Check
// ============================================

async function checkTracking(): Promise<{
  path: string
  sources: number
  activeChunks: number
  supersededChunks: number
} | null> {
  try {
    const atlasConfig = getConfig()
    const storageService = getStorageService(atlasConfig)
    const db = storageService.getDatabase()
    const tracker = getFileTracker(db)
    const stats = await tracker.getStats()

    // PostgreSQL database info
    const dbPath = atlasConfig.storage?.postgres
      ? `postgresql://${atlasConfig.storage.postgres.host}:${atlasConfig.storage.postgres.port}/${atlasConfig.storage.postgres.database}`
      : 'PostgreSQL (not configured)'

    return {
      path: dbPath,
      sources: stats.totalFiles,
      activeChunks: stats.totalChunks,
      supersededChunks: stats.deletedFiles,
    }
  } catch (error) {
    log.warn('Failed to check tracking database', { error: (error as Error).message })
    return null
  }
}

// ============================================
// Main Diagnostic Function
// ============================================

export async function runDiagnostics(): Promise<DiagnosticReport> {
  log.debug('Running diagnostics...')

  const [environment, services, models, configuration, tracking] = await Promise.all([
    checkEnvironment(),
    checkServices(),
    checkOllamaModels(),
    checkConfiguration(),
    checkTracking(),
  ])

  // Calculate summary
  const allChecks = [...environment, ...services]
  const summary = {
    ok: allChecks.filter((c) => c.status === 'ok').length,
    warning: allChecks.filter((c) => c.status === 'warning').length,
    error: allChecks.filter((c) => c.status === 'error').length,
    notConfigured: allChecks.filter((c) => c.status === 'not_configured').length,
  }

  return {
    environment,
    services,
    models: {
      ollama: models,
    },
    tracking,
    configuration,
    summary,
  }
}
