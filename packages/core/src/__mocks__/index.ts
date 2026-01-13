/**
 * Mock backends for Atlas testing
 *
 * Centralized exports for all mock implementations.
 *
 * Usage:
 * ```typescript
 * import { createMockEmbeddingBackend, createMockStorageBackend } from './__mocks__.js'
 * ```
 */

// Embedding backend
export {
  MockEmbeddingBackend,
  createMockEmbeddingBackend,
  type MockEmbeddingConfig,
} from './MockEmbeddingBackend.js'

// Storage backend
export {
  MockStorageBackend,
  createMockStorageBackend,
  type MockStorageConfig,
} from './MockStorageBackend.js'

// LLM backend
export {
  MockLLMBackend,
  createMockLLMBackend,
  CONSOLIDATION_RESPONSES,
  type MockLLMConfig,
} from './MockLLMBackend.js'

// Reranker backend
export {
  MockRerankerBackend,
  createMockRerankerBackend,
  type MockRerankerConfig,
  type RerankStrategy,
} from './MockRerankerBackend.js'
