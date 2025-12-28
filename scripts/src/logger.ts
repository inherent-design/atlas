/**
 * Structured logging with Pino
 */

import pino from 'pino'

const LOG_LEVEL = process.env.LOG_LEVEL || 'info'
const IS_DEV = process.env.NODE_ENV !== 'production'

export const logger = pino({
  level: LOG_LEVEL,
  transport: IS_DEV
    ? {
        target: 'pino-pretty',
        options: {
          colorize: true,
          translateTime: 'HH:MM:ss',
          ignore: 'pid,hostname',
        },
      }
    : undefined,
})

// Convenience methods
export const log = {
  trace: (msg: string, data?: object) => logger.trace(data || {}, msg),
  debug: (msg: string, data?: object) => logger.debug(data || {}, msg),
  info: (msg: string, data?: object) => logger.info(data || {}, msg),
  warn: (msg: string, data?: object) => logger.warn(data || {}, msg),
  error: (msg: string, error?: Error | object) => {
    if (error instanceof Error) {
      logger.error({ err: error }, msg)
    } else {
      logger.error(error || {}, msg)
    }
  },
}

/**
 * Update log level dynamically
 */
export function setLogLevel(level: 'trace' | 'debug' | 'info' | 'warn' | 'error'): void {
  logger.level = level
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
