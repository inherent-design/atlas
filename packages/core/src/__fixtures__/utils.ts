/**
 * Test utilities and context helpers
 *
 * Provides test environment setup and assertion helpers.
 */

import type { SearchResult, IngestResult } from '../shared/types.js'
import { createMockEmbeddingBackend } from '../__mocks__/MockEmbeddingBackend.js'
import { createMockStorageBackend } from '../__mocks__/MockStorageBackend.js'
import { createMockLLMBackend } from '../__mocks__/MockLLMBackend.js'
import { createMockRerankerBackend } from '../__mocks__/MockRerankerBackend.js'

/**
 * Test context with mocked backends
 */
export interface TestContext {
  embedding: ReturnType<typeof createMockEmbeddingBackend>
  storage: ReturnType<typeof createMockStorageBackend>
  llm: ReturnType<typeof createMockLLMBackend>
  reranker: ReturnType<typeof createMockRerankerBackend>
  cleanup: () => void
}

/**
 * Create isolated test context with mocked backends
 *
 * @returns Test context with all mocks initialized
 */
export function createTestContext(): TestContext {
  const embedding = createMockEmbeddingBackend()
  const storage = createMockStorageBackend()
  const llm = createMockLLMBackend()
  const reranker = createMockRerankerBackend()

  return {
    embedding,
    storage,
    llm,
    reranker,
    cleanup: () => {
      embedding.clearCalls()
      storage.clearAll()
      llm.clearCalls()
      reranker.clearCalls()
    },
  }
}

/**
 * Execute function with mocked backends
 *
 * Automatically creates context, runs function, and cleans up.
 *
 * @param fn - Function to run with test context
 * @returns Result of function
 */
export async function withMockedBackends<T>(fn: (context: TestContext) => Promise<T>): Promise<T> {
  const context = createTestContext()
  try {
    return await fn(context)
  } finally {
    context.cleanup()
  }
}

/**
 * Assert that result follows U4 protocol
 *
 * Validates that a result has STATUS, PROGRESS, BLOCKERS, QUESTIONS, NEXT fields.
 *
 * @param result - Object to validate
 * @throws Error if validation fails
 */
export function assertU4Output(result: any): void {
  const required = ['STATUS', 'PROGRESS', 'BLOCKERS', 'QUESTIONS', 'NEXT']

  for (const field of required) {
    if (!(field in result)) {
      throw new Error(`U4 protocol violation: missing field '${field}'`)
    }
  }

  const validStatuses = ['Complete', 'In Progress', 'Blocked']
  if (!validStatuses.includes(result.STATUS)) {
    throw new Error(
      `U4 protocol violation: STATUS must be one of ${validStatuses.join(', ')}, got '${result.STATUS}'`
    )
  }

  // PROGRESS must be string or array of strings
  if (typeof result.PROGRESS !== 'string' && !Array.isArray(result.PROGRESS)) {
    throw new Error('U4 protocol violation: PROGRESS must be string or array')
  }

  // BLOCKERS must be string or array
  if (typeof result.BLOCKERS !== 'string' && !Array.isArray(result.BLOCKERS)) {
    throw new Error('U4 protocol violation: BLOCKERS must be string or array')
  }

  // QUESTIONS must be string or array
  if (typeof result.QUESTIONS !== 'string' && !Array.isArray(result.QUESTIONS)) {
    throw new Error('U4 protocol violation: QUESTIONS must be string or array')
  }

  // NEXT must be string or array
  if (typeof result.NEXT !== 'string' && !Array.isArray(result.NEXT)) {
    throw new Error('U4 protocol violation: NEXT must be string or array')
  }
}

/**
 * Assert that search results are sorted by score (descending)
 *
 * @param results - Search results to validate
 * @throws Error if not properly sorted
 */
export function assertSortedByScore(results: SearchResult[]): void {
  for (let i = 1; i < results.length; i++) {
    const curr = results[i]!
    const prev = results[i - 1]!
    if (curr.score > prev.score) {
      throw new Error(
        `Results not sorted: result[${i}].score (${curr.score}) > result[${i - 1}].score (${prev.score})`
      )
    }
  }
}

/**
 * Assert that all scores are within valid range [0, 1]
 *
 * @param results - Search results to validate
 * @throws Error if any score is out of range
 */
export function assertValidScores(results: SearchResult[]): void {
  for (let i = 0; i < results.length; i++) {
    const score = results[i]!.score
    if (score < 0 || score > 1) {
      throw new Error(`Invalid score at result[${i}]: ${score} (must be 0.0-1.0)`)
    }
  }
}

/**
 * Assert that ingest result is successful (no errors)
 *
 * @param result - Ingest result to validate
 * @throws Error if result has errors
 */
export function assertIngestSuccess(result: IngestResult): void {
  if (result.errors.length > 0) {
    const errorSummary = result.errors.map((e) => `${e.file}: ${e.error}`).join('\n')
    throw new Error(`Ingest had errors:\n${errorSummary}`)
  }

  if (result.filesProcessed === 0) {
    throw new Error('Ingest processed 0 files')
  }

  if (result.chunksStored === 0) {
    throw new Error('Ingest stored 0 chunks')
  }
}

/**
 * Wait for condition to be true (polling)
 *
 * @param condition - Function that returns true when done
 * @param timeoutMs - Maximum time to wait
 * @param intervalMs - Polling interval
 * @throws Error if timeout reached
 */
export async function waitFor(
  condition: () => boolean | Promise<boolean>,
  timeoutMs = 5000,
  intervalMs = 100
): Promise<void> {
  const start = Date.now()

  while (Date.now() - start < timeoutMs) {
    if (await condition()) {
      return
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }

  throw new Error(`waitFor timeout after ${timeoutMs}ms`)
}

/**
 * Create a spy function that tracks calls
 *
 * @returns Spy function with call tracking
 */
export function createSpy<T extends (...args: any[]) => any>(): T & {
  calls: Array<{ args: any[]; timestamp: number }>
  callCount: number
  clear: () => void
} {
  const calls: Array<{ args: any[]; timestamp: number }> = []

  const spy = ((...args: any[]) => {
    calls.push({ args, timestamp: Date.now() })
  }) as any

  spy.calls = calls
  Object.defineProperty(spy, 'callCount', {
    get: () => calls.length,
  })
  spy.clear = () => {
    calls.length = 0
  }

  return spy
}

/**
 * Generate ISO 8601 timestamp for testing
 *
 * @param offsetMinutes - Minutes offset from now (negative for past)
 * @returns ISO 8601 timestamp string
 */
export function generateTimestamp(offsetMinutes = 0): string {
  const date = new Date()
  date.setMinutes(date.getMinutes() + offsetMinutes)
  return date.toISOString()
}

/**
 * Generate unique ID for testing
 *
 * @param prefix - Optional prefix
 * @returns Unique ID string
 */
export function generateId(prefix = 'test'): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

/**
 * Sleep for testing delays
 *
 * @param ms - Milliseconds to sleep
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Assert that value is defined (TypeScript type guard)
 *
 * @param value - Value to check
 * @param message - Error message
 */
export function assertDefined<T>(
  value: T | undefined | null,
  message?: string
): asserts value is T {
  if (value === undefined || value === null) {
    throw new Error(message || 'Expected value to be defined')
  }
}

/**
 * Assert that arrays have same length
 *
 * @param actual - Actual array
 * @param expected - Expected array
 * @param message - Error message
 */
export function assertSameLength(actual: any[], expected: any[], message?: string): void {
  if (actual.length !== expected.length) {
    throw new Error(
      message || `Array length mismatch: expected ${expected.length}, got ${actual.length}`
    )
  }
}

/**
 * Assert that value is approximately equal (for floating point)
 *
 * @param actual - Actual value
 * @param expected - Expected value
 * @param epsilon - Tolerance
 * @param message - Error message
 */
export function assertApproxEqual(
  actual: number,
  expected: number,
  epsilon = 0.0001,
  message?: string
): void {
  if (Math.abs(actual - expected) > epsilon) {
    throw new Error(
      message ||
        `Values not approximately equal: expected ${expected}, got ${actual} (epsilon: ${epsilon})`
    )
  }
}
