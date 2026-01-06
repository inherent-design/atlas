/**
 * Test fixtures for Atlas
 *
 * Centralized exports for all test fixtures.
 *
 * Usage:
 * ```typescript
 * import { CHUNKS, EMBEDDINGS, createChunkPayload } from './__fixtures__'
 * ```
 */

// Chunk fixtures
export {
  createChunkPayload,
  CHUNKS,
  CHUNK_BATCH,
  createChunkSequence,
} from './chunks'

// Embedding fixtures
export {
  generateEmbedding,
  generateNamedVectors,
  EMBEDDINGS,
  EMBEDDING_BATCH,
  cosineSimilarity,
} from './embeddings'

// File content fixtures
export {
  MARKDOWN_FILE,
  TYPESCRIPT_FILE,
  PYTHON_FILE,
  JSON_FILE,
  YAML_FILE,
  LOG_FILE,
  SHELL_FILE,
  FILE_CONTENT_BY_TYPE,
  getSampleContent,
  createTestFilePath,
  TEST_FILES,
} from './files'

// Search fixtures
export {
  createSearchOptions,
  createSearchResult,
  SEARCH_OPTIONS,
  SEARCH_RESULTS,
  createSearchResultBatch,
  MOCK_SEARCH_RESPONSE,
  EMPTY_SEARCH_RESPONSE,
} from './search'

// Ingestion fixtures
export {
  createIngestOptions,
  createIngestResult,
  INGEST_OPTIONS,
  INGEST_RESULTS,
  INGEST_FILE_PATHS,
  createMockFileTree,
  flattenFileTree,
} from './ingest'

// Factory builders
export {
  ChunkPayloadBuilder,
  VectorPointBuilder,
  SearchResultBuilder,
  Builders,
  generateVectorPointBatch,
  generateSearchResults,
  generateConsolidationHierarchy,
} from './factories'
