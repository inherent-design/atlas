/**
 * Mock backends for Atlas testing
 *
 * Centralized exports for all mock implementations.
 *
 * Usage:
 * ```typescript
 * import { createMockEmbeddingBackend, createMockStorageBackend } from './__mocks__'
 * ```
 */

// Embedding backend
export {
  MockEmbeddingBackend,
  createMockEmbeddingBackend,
  type MockEmbeddingConfig,
} from './MockEmbeddingBackend'

// Storage backend
export {
  MockStorageBackend,
  createMockStorageBackend,
  type MockStorageConfig,
} from './MockStorageBackend'

// LLM backend
export {
  MockLLMBackend,
  createMockLLMBackend,
  CONSOLIDATION_RESPONSES,
  type MockLLMConfig,
} from './MockLLMBackend'

// Reranker backend
export {
  MockRerankerBackend,
  createMockRerankerBackend,
  type MockRerankerConfig,
  type RerankStrategy,
} from './MockRerankerBackend'
