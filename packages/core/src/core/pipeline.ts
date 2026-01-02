/**
 * Streaming Pipeline Primitives
 *
 * Async iterator utilities for streaming, concurrent data pipelines.
 * Natural backpressure: producer pauses when consumer falls behind.
 *
 * Core pattern: AsyncGenerator → transform → AsyncGenerator → consume
 */

import { pMapIterable } from 'p-map'

/**
 * Execute async operations with bounded concurrency.
 * Natural backpressure: producer pauses when pending.length >= concurrency.
 *
 * @param source - Source async iterable
 * @param fn - Async transform function
 * @param concurrency - Maximum concurrent operations (default: 4)
 * @yields Transformed items in completion order (NOT source order)
 *
 * @example
 * ```typescript
 * const chunks = streamChunks(file)
 * const embedded = parallel(chunks, chunk => embed(chunk), 3)
 * for await (const result of embedded) {
 *   console.log(result)
 * }
 * ```
 */
export async function* parallel<T, R>(
  source: AsyncIterable<T>,
  fn: (item: T) => Promise<R>,
  concurrency = 4
): AsyncGenerator<R> {
  yield* pMapIterable(source, fn, { concurrency })
}

/**
 * Batch items with hybrid flush (count OR timeout, whichever first).
 *
 * @param source - Source async iterable
 * @param options - Batching configuration
 * @param options.maxSize - Maximum batch size (flush when reached)
 * @param options.timeoutMs - Maximum wait time (flush when exceeded)
 * @yields Batches of items
 *
 * @example
 * ```typescript
 * const chunks = streamChunks(file)
 * const batches = batch(chunks, { maxSize: 50, timeoutMs: 5000 })
 * for await (const batch of batches) {
 *   await upsert(batch)
 * }
 * ```
 */
export async function* batch<T>(
  source: AsyncIterable<T>,
  options: { maxSize: number; timeoutMs: number }
): AsyncGenerator<T[]> {
  const { maxSize, timeoutMs } = options
  let buffer: T[] = []
  let timeoutHandle: NodeJS.Timeout | null = null

  const iterator = source[Symbol.asyncIterator]()

  // Flush current buffer and reset timeout
  const flush = () => {
    if (timeoutHandle) {
      clearTimeout(timeoutHandle)
      timeoutHandle = null
    }
    const batch = buffer
    buffer = []
    return batch
  }

  // Promise that resolves when timeout expires
  let timeoutPromise: Promise<'timeout'> | null = null
  const resetTimeout = () => {
    if (timeoutHandle) {
      clearTimeout(timeoutHandle)
    }
    timeoutPromise = new Promise(resolve => {
      timeoutHandle = setTimeout(() => resolve('timeout'), timeoutMs)
    })
  }

  try {
    while (true) {
      // Start timeout if buffer has items
      if (buffer.length > 0 && !timeoutPromise) {
        resetTimeout()
      }

      // Race between next item and timeout
      const next = iterator.next()
      const result = timeoutPromise
        ? await Promise.race([next, timeoutPromise.then(() => ({ done: false, timeout: true }))])
        : await next

      // Timeout expired - flush buffer
      if ('timeout' in result && result.timeout) {
        if (buffer.length > 0) {
          yield flush()
        }
        timeoutPromise = null
        continue
      }

      const { value, done } = result as IteratorResult<T>

      // Source exhausted - flush remaining
      if (done) {
        if (buffer.length > 0) {
          yield flush()
        }
        break
      }

      // Add item to buffer
      buffer.push(value)

      // Flush if max size reached
      if (buffer.length >= maxSize) {
        yield flush()
        timeoutPromise = null
      }
    }
  } finally {
    // Cleanup timeout on exit
    if (timeoutHandle) {
      clearTimeout(timeoutHandle)
    }
  }
}

/**
 * Consume an async iterable, applying fn to each item.
 * Optionally process items concurrently.
 *
 * @param source - Source async iterable
 * @param fn - Async consumer function
 * @param concurrency - Optional concurrent processing (default: sequential)
 *
 * @example
 * ```typescript
 * const chunks = streamChunks(file)
 * await drain(chunks, chunk => console.log(chunk))
 * ```
 */
export async function drain<T>(
  source: AsyncIterable<T>,
  fn: (item: T) => Promise<void>,
  concurrency?: number
): Promise<void> {
  if (concurrency && concurrency > 1) {
    // Concurrent drain via parallel
    for await (const _ of parallel(source, fn, concurrency)) {
      // parallel() yields results, we just consume them
    }
  } else {
    // Sequential drain
    for await (const item of source) {
      await fn(item)
    }
  }
}
