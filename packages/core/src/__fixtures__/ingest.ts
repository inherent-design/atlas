/**
 * Ingestion-related fixtures for testing
 *
 * Provides IngestParams and IngestResult fixtures.
 */

import type { IngestParams, IngestResult } from '../shared/types.js'
import { TEST_FILES } from './files.js'

/**
 * Create IngestParams with sensible defaults
 *
 * @param overrides - Partial options to merge with defaults
 * @returns Complete IngestParams
 */
export function createIngestParams(overrides?: Partial<IngestParams>): IngestParams {
  return {
    paths: ['/test/docs'],
    recursive: true,
    rootDir: '/test',
    verbose: false,
    ...overrides,
  }
}

/**
 * Common ingest option presets
 */
export const INGEST_OPTIONS = {
  /** Single file ingestion */
  singleFile: createIngestParams({
    paths: [TEST_FILES.markdown],
    recursive: false,
  }),

  /** Directory ingestion (recursive) */
  directory: createIngestParams({
    paths: ['/test/docs'],
    recursive: true,
    rootDir: '/test',
  }),

  /** Multiple files */
  multipleFiles: createIngestParams({
    paths: [TEST_FILES.markdown, TEST_FILES.typescript, TEST_FILES.python],
    recursive: false,
  }),

  /** With verbose logging */
  verbose: createIngestParams({
    paths: ['/test/docs'],
    recursive: true,
    verbose: true,
  }),

  /** With pre-fetched QNTM keys (optimization) */
  withKeys: createIngestParams({
    paths: ['/test/docs'],
    existingKeys: ['@memory ~ consolidation', '@architecture ~ design', '@test ~ data'],
  }),

  /** Disable HNSW for batch ingestion */
  batchOptimized: createIngestParams({
    paths: ['/test/docs'],
    recursive: true,
    useHNSWToggle: false,
  }),
} as const

/**
 * Create IngestResult with sensible defaults
 *
 * @param overrides - Partial result to merge with defaults
 * @returns Complete IngestResult
 */
export function createIngestResult(overrides?: Partial<IngestResult>): IngestResult {
  return {
    filesProcessed: 0,
    chunksStored: 0,
    errors: [],
    ...overrides,
  }
}

/**
 * Common ingest result presets
 */
export const INGEST_RESULTS = {
  /** Successful single file ingestion */
  singleFileSuccess: createIngestResult({
    filesProcessed: 1,
    chunksStored: 3,
    errors: [],
  }),

  /** Successful directory ingestion */
  directorySuccess: createIngestResult({
    filesProcessed: 12,
    chunksStored: 48,
    errors: [],
  }),

  /** Partial failure (some files succeeded) */
  partialFailure: createIngestResult({
    filesProcessed: 8,
    chunksStored: 32,
    errors: [
      {
        file: '/test/docs/corrupted.md',
        error: 'Failed to read file: invalid UTF-8',
      },
      {
        file: '/test/docs/binary.dat',
        error: 'Unsupported file type: .dat',
      },
    ],
  }),

  /** Complete failure (all files failed) */
  completeFailure: createIngestResult({
    filesProcessed: 0,
    chunksStored: 0,
    errors: [
      {
        file: '/test/docs/file1.md',
        error: 'Embedding service unavailable',
      },
      {
        file: '/test/docs/file2.md',
        error: 'Embedding service unavailable',
      },
    ],
  }),

  /** Empty directory (no files found) */
  empty: createIngestResult({
    filesProcessed: 0,
    chunksStored: 0,
    errors: [],
  }),
} as const

/**
 * Sample file paths for ingestion tests
 */
export const INGEST_FILE_PATHS = {
  /** Single markdown file */
  singleMd: [TEST_FILES.markdown],

  /** Multiple code files */
  codeFiles: [TEST_FILES.typescript, TEST_FILES.python],

  /** Mixed file types */
  mixed: [
    TEST_FILES.markdown,
    TEST_FILES.typescript,
    TEST_FILES.python,
    TEST_FILES.json,
    TEST_FILES.yaml,
  ],

  /** Config files only */
  configFiles: [TEST_FILES.json, TEST_FILES.yaml],

  /** Log files */
  logFiles: [TEST_FILES.log],
} as const

/**
 * Create a mock file tree structure for testing
 */
export function createMockFileTree(): Record<string, string[]> {
  return {
    '/test/docs': [
      '/test/docs/README.md',
      '/test/docs/architecture.md',
      '/test/docs/memory-consolidation.md',
    ],
    '/test/docs/guides': ['/test/docs/guides/quickstart.md', '/test/docs/guides/configuration.md'],
    '/test/src': [
      '/test/src/index.ts',
      '/test/src/embedding.ts',
      '/test/src/storage.ts',
      '/test/src/consolidation.ts',
    ],
    '/test/config': ['/test/config/atlas.json', '/test/config/atlas.yaml'],
    '/test/logs': [
      '/test/logs/2025-12-28.log',
      '/test/logs/2025-12-29.log',
      '/test/logs/2025-12-30.log',
    ],
  }
}

/**
 * Flatten file tree into array of all file paths
 */
export function flattenFileTree(tree: Record<string, string[]>): string[] {
  return Object.values(tree).flat()
}
