/**
 * Structured logging with Pino
 *
 * Module-scoped logging with application-level filtering:
 * - LOG_LEVEL: Global minimum level (trace|debug|info|warn|error)
 * - LOG_MODULES: Comma-separated glob patterns to enable (e.g., "qntm,ollama")
 * - LOG_MODULE_LEVEL: Override level for matched modules (default: trace)
 *
 * Usage:
 *   const log = createLogger('qntm/providers')
 *   log.trace('verbose details', { key: 'value' })
 *
 * Examples:
 *   LOG_LEVEL=info LOG_MODULES=qntm LOG_MODULE_LEVEL=trace
 *     -> trace for qntm modules, info for everything else
 *   LOG_MODULES="qntm,ollama"
 *     -> enable qntm and ollama modules (including qntm/*, ollama/*)
 *   LOG_MODULES="*"
 *     -> enable all modules
 */

import { Glob } from 'bun'
import pino from 'pino'

const IS_DEV = process.env.NODE_ENV !== 'production'

// Level ordering for comparison
const LEVELS: Record<string, number> = {
  trace: 10,
  debug: 20,
  info: 30,
  warn: 40,
  error: 50,
}

// Mutable state (updated by CLI or setLogLevel)
let globalLogLevel = process.env.LOG_LEVEL || 'info'
let moduleLogLevel = process.env.LOG_MODULE_LEVEL || 'trace'
let modulePatterns = process.env.LOG_MODULES
  ? process.env.LOG_MODULES.split(',').map((m) => m.trim())
  : null

/**
 * Check if a module should be logged based on module filter patterns
 * Uses Bun's native glob matching for pattern support
 */
function shouldLogModule(module?: string): boolean {
  if (!modulePatterns || !module) return true

  return modulePatterns.some((pattern) => {
    // Use Bun's native Glob for pattern matching
    // Check both exact match and hierarchical match (qntm matches qntm/providers)
    const exactGlob = new Glob(pattern)
    const hierarchicalGlob = new Glob(`${pattern}/*`)
    return exactGlob.match(module) || hierarchicalGlob.match(module)
  })
}

/**
 * Get effective log level for a module (reads from mutable state)
 */
function getEffectiveLevel(module?: string): number {
  if (module && shouldLogModule(module) && modulePatterns) {
    // Module is explicitly enabled, use module-specific level
    return LEVELS[moduleLogLevel] || LEVELS[globalLogLevel]
  }
  return LEVELS[globalLogLevel]
}

export const logger = pino({
  level: 'trace', // Set to lowest, filtering happens per-module
  transport: IS_DEV
    ? {
        target: 'pino-pretty',
        options: {
          colorize: true,
          translateTime: 'HH:MM:ss',
          ignore: 'pid,hostname',
          messageFormat: '{module} {msg}',
        },
      }
    : undefined,
})

// Root logger (backward compatibility - no module filtering)
export const log = {
  trace: (msg: string, data?: object) => {
    if (LEVELS[globalLogLevel] <= LEVELS.trace) {
      logger.trace(data || {}, msg)
    }
  },
  debug: (msg: string, data?: object) => {
    if (LEVELS[globalLogLevel] <= LEVELS.debug) {
      logger.debug(data || {}, msg)
    }
  },
  info: (msg: string, data?: object) => {
    if (LEVELS[globalLogLevel] <= LEVELS.info) {
      logger.info(data || {}, msg)
    }
  },
  warn: (msg: string, data?: object) => {
    if (LEVELS[globalLogLevel] <= LEVELS.warn) {
      logger.warn(data || {}, msg)
    }
  },
  error: (msg: string, error?: Error | object) => {
    if (LEVELS[globalLogLevel] <= LEVELS.error) {
      if (error instanceof Error) {
        logger.error({ err: error }, msg)
      } else {
        logger.error(error || {}, msg)
      }
    }
  },
}

/**
 * Create a module-scoped logger with filtering
 */
export function createLogger(module: string) {
  const child = logger.child({ module })

  return {
    trace: (msg: string, data?: object) => {
      if (getEffectiveLevel(module) <= LEVELS.trace) {
        child.trace(data || {}, msg)
      }
    },
    debug: (msg: string, data?: object) => {
      if (getEffectiveLevel(module) <= LEVELS.debug) {
        child.debug(data || {}, msg)
      }
    },
    info: (msg: string, data?: object) => {
      if (getEffectiveLevel(module) <= LEVELS.info) {
        child.info(data || {}, msg)
      }
    },
    warn: (msg: string, data?: object) => {
      if (getEffectiveLevel(module) <= LEVELS.warn) {
        child.warn(data || {}, msg)
      }
    },
    error: (msg: string, error?: Error | object) => {
      if (getEffectiveLevel(module) <= LEVELS.error) {
        if (error instanceof Error) {
          child.error({ err: error }, msg)
        } else {
          child.error(error || {}, msg)
        }
      }
    },
  }
}

/**
 * Update log level dynamically (called by CLI)
 * NOTE: Keep Pino at 'trace' - filtering happens at application level
 */
export function setLogLevel(level: 'trace' | 'debug' | 'info' | 'warn' | 'error'): void {
  globalLogLevel = level
  // Don't lower Pino's level - we filter at application level per-module
  // logger.level = level
}

// Timing utilities for performance tracing
export function startTimer(label: string): () => void {
  const start = performance.now()
  log.trace(`[START] ${label}`)

  return () => {
    const durationMs = performance.now() - start
    log.debug(`[END] ${label}`, { durationMs, durationSec: (durationMs / 1000).toFixed(2) })
  }
}

export function timeAsync<T>(label: string, fn: () => Promise<T>): Promise<T> {
  const end = startTimer(label)
  return fn().finally(end)
}
