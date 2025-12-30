/**
 * Structured logging with Pino
 *
 * Pattern-based module logging with specificity ordering:
 * - LOG_LEVEL: Global fallback level (trace|debug|info|warn|error), default: info
 * - LOG_MODULES: Pattern:level pairs, comma-separated, with glob support
 *
 * Pattern format: "pattern:level" where pattern supports globs
 * Specificity: exact match > more segments > glob patterns
 *
 * Usage:
 *   const log = createLogger('qntm/providers')
 *   log.debug('message', { key: 'value' })
 *
 * Examples:
 *   LOG_MODULES="qntm/providers:error,qntm/*:debug,watchdog:debug"
 *     -> qntm/providers at error, other qntm/* at debug, watchdog at debug
 *   LOG_MODULES="*:trace"
 *     -> trace for all modules
 *   LOG_LEVEL=warn LOG_MODULES="ingest:debug"
 *     -> debug for ingest, warn for everything else
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

type LogLevel = keyof typeof LEVELS

/** Logger interface returned by createLogger */
export interface Logger {
  trace: (msg: string, data?: object) => void
  debug: (msg: string, data?: object) => void
  info: (msg: string, data?: object) => void
  warn: (msg: string, data?: object) => void
  error: (msg: string, error?: Error | object) => void
}

/** Parsed log rule with specificity for ordering */
interface LogRule {
  pattern: string
  level: LogLevel
  specificity: number
  glob: Glob
}

/**
 * Calculate specificity score for pattern ordering
 * Higher = more specific, gets matched first
 */
function calculateSpecificity(pattern: string): number {
  const segments = pattern.split('/').length
  const hasGlob = pattern.includes('*')
  const isWildcardOnly = pattern === '*'

  // Wildcard-only is least specific
  if (isWildcardOnly) return 0

  // Base: 10 points per segment
  // Bonus: +5 for exact match (no glob)
  return segments * 10 + (hasGlob ? 0 : 5)
}

/**
 * Parse LOG_MODULES config into sorted rules
 * Format: "pattern:level,pattern:level,..."
 */
function parseLogModules(config: string | undefined): LogRule[] {
  if (!config) return []

  return config
    .split(',')
    .map((rule) => rule.trim())
    .filter((rule) => rule.length > 0)
    .map((rule) => {
      const colonIdx = rule.lastIndexOf(':')
      let pattern: string
      let level: LogLevel

      if (colonIdx === -1) {
        // No level specified, default to debug
        pattern = rule
        level = 'debug'
      } else {
        pattern = rule.slice(0, colonIdx)
        const levelStr = rule.slice(colonIdx + 1).toLowerCase()
        level = (LEVELS[levelStr] !== undefined ? levelStr : 'debug') as LogLevel
      }

      return {
        pattern,
        level,
        specificity: calculateSpecificity(pattern),
        glob: new Glob(pattern),
      }
    })
    .sort((a, b) => b.specificity - a.specificity) // Most specific first
}

// Mutable state (updated by CLI or setLogLevel)
let globalLogLevel: LogLevel = (process.env.LOG_LEVEL as LogLevel) || 'info'
let moduleRules: LogRule[] = parseLogModules(process.env.LOG_MODULES)

/**
 * Get effective log level for a module
 * Checks rules in specificity order, falls back to global level
 */
function getEffectiveLevel(module?: string): number {
  if (!module || moduleRules.length === 0) {
    return LEVELS[globalLogLevel]
  }

  // Find first matching rule (already sorted by specificity)
  for (const rule of moduleRules) {
    if (rule.glob.match(module)) {
      return LEVELS[rule.level]
    }
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
 * Update global log level dynamically (called by CLI)
 * NOTE: Keep Pino at 'trace' - filtering happens at application level
 */
export function setLogLevel(level: LogLevel): void {
  globalLogLevel = level
}

/**
 * Update module rules dynamically
 * Format: "pattern:level,pattern:level,..."
 */
export function setModuleRules(config: string): void {
  moduleRules = parseLogModules(config)
}

/**
 * Get current logging configuration (for debugging)
 */
export function getLogConfig(): { globalLevel: LogLevel; rules: Array<{ pattern: string; level: LogLevel; specificity: number }> } {
  return {
    globalLevel: globalLogLevel,
    rules: moduleRules.map((r) => ({ pattern: r.pattern, level: r.level, specificity: r.specificity })),
  }
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
