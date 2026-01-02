/**
 * Integration tests for Atlas ingestion
 */

import { mkdirSync, rmSync, writeFileSync } from 'fs'
import { join } from 'path'

// Use vi.hoisted() to define mocks that will be available when vi.mock() factories run
const {
  mockVoyageEmbed,
  mockQdrantGet,
  mockQdrantCreate,
  mockQdrantUpsert,
  mockGenerateQNTMKeysBatch,
  mockCollectionExists,
} = vi.hoisted(() => ({
  mockVoyageEmbed: vi.fn((input: any) => {
    // Return one embedding per chunk
    const chunks = Array.isArray(input.input) ? input.input : [input.input]
    return Promise.resolve({
      data: chunks.map(() => ({
        embedding: new Array(1024).fill(0.1), // Mock 1024-dim embedding
      })),
    })
  }),
  mockQdrantGet: vi.fn(() => Promise.reject(new Error('Collection not found'))),
  mockQdrantCreate: vi.fn(() => Promise.resolve()),
  mockQdrantUpsert: vi.fn(() => Promise.resolve({ status: 'acknowledged' })),
  mockGenerateQNTMKeysBatch: vi.fn((inputs: any[]) =>
    Promise.resolve(
      inputs.map(() => ({
        keys: ['@test ~ content', '@mock ~ data'],
        reasoning: 'Test content semantic keys',
      }))
    )
  ),
  mockCollectionExists: vi.fn(async () => true), // Default: collection exists
}))

// Setup mocks - hoisted but now have access to hoisted mock functions
vi.mock('../../services/storage/client', () => ({
  getQdrantClient: () => ({
    getCollection: mockQdrantGet,
    createCollection: mockQdrantCreate,
    createPayloadIndex: vi.fn(() => Promise.resolve()),
    upsert: mockQdrantUpsert,
  }),
}))

vi.mock('../../services/storage', () => ({
  getStorageBackend: () => ({
    name: 'qdrant',
    upsert: mockQdrantUpsert,
    collectionExists: mockCollectionExists, // Use tracked mock
    createCollection: mockQdrantCreate,
    getCollectionInfo: vi.fn(() => Promise.resolve({
      points_count: 0,
      vector_dimensions: { text: 1024, code: 1024 }
    })),
  }),
  withHNSWDisabled: async (fn: () => Promise<any>) => fn(),
}))

vi.mock('../../services/embedding', () => ({
  getVoyageClient: () => ({
    embed: mockVoyageEmbed,
  }),
  getEmbeddingBackend: () => ({
    name: 'voyage:text',
    embedText: async (input: string | string[]) => {
      const inputs = Array.isArray(input) ? input : [input]
      return {
        embeddings: inputs.map(() => new Array(1024).fill(0.1)),
        model: 'voyage-3-large',
        strategy: 'snippet' as const,
        dimensions: 1024,
        usage: { inputTokens: inputs.length * 10 },
      }
    },
  }),
  getEmbeddingDimensions: () => 1024, // Mock dimension retrieval
}))

vi.mock('../../services/chunking', () => ({
  getTextSplitter: () => ({
    splitText: async (text: string) => {
      // Simple mock: split by paragraphs
      return text.split('\n\n').filter((chunk) => chunk.trim().length > 0)
    },
  }),
}))

// Mock LLM service with sanitizeQNTMKey preserved
vi.mock('../../services/llm', async () => {
  const actual = await vi.importActual<typeof import('../../services/llm')>('../../services/llm')
  return {
    generateQNTMKeysBatch: mockGenerateQNTMKeysBatch,
    generateQNTMKeys: vi.fn((input: any) => Promise.resolve({
      keys: ['@test ~ content', '@mock ~ data'],
      reasoning: 'Test content semantic keys',
    })),
    sanitizeQNTMKey: actual.sanitizeQNTMKey,
    fetchExistingQNTMKeys: () => Promise.resolve([]),
    getLLMBackendFor: vi.fn(() => ({
      name: 'test-backend',
      capabilities: new Set(['json-completion']),
      supports: (cap: string) => cap === 'json-completion',
      completeJSON: vi.fn((prompt: string) => {
        return Promise.resolve({
          keys: ['@test ~ content', '@mock ~ data'],
          reasoning: 'Test content semantic keys',
        })
      }),
    })),
  }
})

// Import after mocks are set up
import { ingest, ingestFile } from '.'

const testDir = '/tmp/atlas-test-ingest'

describe('ingestFile', () => {
  beforeEach(() => {
    // Reset mocks
    mockVoyageEmbed.mockClear()
    mockQdrantGet.mockClear()
    mockQdrantCreate.mockClear()
    mockQdrantUpsert.mockClear()
    mockGenerateQNTMKeysBatch.mockClear()

    // Setup test directory
    rmSync(testDir, { recursive: true, force: true })
    mkdirSync(testDir, { recursive: true })
  })

  test('ingests single file successfully', async () => {
    const testFile = join(testDir, 'test.md')
    writeFileSync(testFile, '# Test\n\nThis is a test document.\n\nWith multiple paragraphs.')

    await ingestFile(testFile, testDir)

    // Should have called backend.upsert
    expect(mockQdrantUpsert).toHaveBeenCalled()

    const firstUpsertCall = mockQdrantUpsert.mock.calls[0]
    const points = firstUpsertCall[1] // Second argument is the points array
    const point = points[0]

    // Each point should have correct structure
    expect(point).toHaveProperty('id')
    expect(point).toHaveProperty('vector')
    expect(point).toHaveProperty('payload')
    expect(point.payload).toHaveProperty('original_text')
    expect(point.payload).toHaveProperty('file_path')
    expect(point.payload).toHaveProperty('qntm_keys')
    expect(point.payload.qntm_keys).toEqual(['@test ~ content', '@mock ~ data'])
    expect(point.payload).toHaveProperty('created_at')
  })

  test('handles file read errors gracefully', async () => {
    const nonExistentFile = join(testDir, 'does-not-exist.md')

    await expect(ingestFile(nonExistentFile, testDir)).rejects.toThrow()
  })

  test('preserves original text in payload', async () => {
    const testFile = join(testDir, 'test.md')
    const content = '# Test\n\nThis is important content that must be preserved.'
    writeFileSync(testFile, content)

    await ingestFile(testFile, testDir)

    // Collect all points from all upsert calls
    const allPoints = mockQdrantUpsert.mock.calls.flatMap((call: any) => call[1]) // Second argument is points array
    const texts = allPoints.map((p: any) => p.payload.original_text)

    // Should have both chunks
    expect(texts.some((t: string) => t.includes('important content'))).toBe(true)
  })

  test('generates consistent QNTM keys for same content', async () => {
    const testFile1 = join(testDir, 'test1.md')
    const testFile2 = join(testDir, 'test2.md')
    const content = '# Same Content\n\nIdentical text.'

    writeFileSync(testFile1, content)
    writeFileSync(testFile2, content)

    await ingestFile(testFile1, testDir)
    const call1 = mockQdrantUpsert.mock.calls[0]
    const qntmKeys1 = call1[1][0].payload.qntm_keys // Second arg is points array

    mockQdrantUpsert.mockClear()
    mockGenerateQNTMKeysBatch.mockClear()

    await ingestFile(testFile2, testDir)
    const call2 = mockQdrantUpsert.mock.calls[0]
    const qntmKeys2 = call2[1][0].payload.qntm_keys // Second arg is points array

    expect(qntmKeys1).toEqual(qntmKeys2)
  })

  test('sets metadata correctly', async () => {
    const testFile = join(testDir, 'test.md')
    writeFileSync(testFile, '# Test Document Title')

    await ingestFile(testFile, testDir)

    const upsertCall = mockQdrantUpsert.mock.calls[0]
    const payload = upsertCall[1][0].payload // Second arg is points array

    expect(payload.file_name).toBe('test.md')
    expect(payload.file_type).toBe('.md')
    expect(payload.importance).toBe('normal')
    expect(payload.consolidation_level).toBe(0)
    expect(payload.created_at).toMatch(/^\d{4}-\d{2}-\d{2}T/) // ISO 8601 timestamp
  })
})

describe('ingest', () => {
  beforeEach(() => {
    rmSync(testDir, { recursive: true, force: true })
    mkdirSync(testDir, { recursive: true })

    // Reset mocks
    mockVoyageEmbed.mockClear()
    mockQdrantGet.mockClear()
    mockQdrantCreate.mockClear()
    mockQdrantUpsert.mockClear()
    mockGenerateQNTMKeysBatch.mockClear()
  })

  test('ingests multiple files', async () => {
    writeFileSync(join(testDir, 'file1.md'), '# File One Title\n\nContent for file one')
    writeFileSync(join(testDir, 'file2.md'), '# File Two Title\n\nContent for file two')

    const result = await ingest({
      paths: [join(testDir, 'file1.md'), join(testDir, 'file2.md')],
      recursive: false,
      rootDir: testDir,
    })

    expect(result.filesProcessed).toBe(2)
    // Streaming pipeline batches chunks across files for efficiency
    // With batch size of 50, small files are combined into single upsert
    expect(mockQdrantUpsert).toHaveBeenCalledTimes(1)
  })

  test('expands directories without recursion', async () => {
    writeFileSync(join(testDir, 'file1.md'), '# File One Title')
    writeFileSync(join(testDir, 'file2.md'), '# File Two Title')

    mkdirSync(join(testDir, 'subdir'))
    writeFileSync(join(testDir, 'subdir', 'file3.md'), '# File Three Title')

    const result = await ingest({ paths: [testDir], recursive: false, rootDir: testDir })

    expect(result.filesProcessed).toBe(2) // Only top-level files
  })

  test('expands directories with recursion', async () => {
    writeFileSync(join(testDir, 'file1.md'), '# File One Title')

    mkdirSync(join(testDir, 'subdir'))
    writeFileSync(join(testDir, 'subdir', 'file2.md'), '# File Two Title')

    const result = await ingest({ paths: [testDir], recursive: true, rootDir: testDir })

    expect(result.filesProcessed).toBe(2) // All files including subdirectory
  })

  test('ensures collection exists before ingesting', async () => {
    // Override mock to return false (collection doesn't exist)
    mockCollectionExists.mockResolvedValueOnce(false)

    writeFileSync(join(testDir, 'test.md'), '# Test Document Title')

    await ingest({ paths: [join(testDir, 'test.md')], recursive: false, rootDir: testDir })

    // Should have checked if collection exists
    expect(mockCollectionExists).toHaveBeenCalled()

    // Should have created collection (since collectionExists returned false)
    expect(mockQdrantCreate).toHaveBeenCalled()
  })

  test('returns count of ingested files', async () => {
    writeFileSync(join(testDir, 'file1.md'), 'content for test one')
    writeFileSync(join(testDir, 'file2.md'), 'content for test two')
    writeFileSync(join(testDir, 'file3.md'), 'content for test three')

    const result = await ingest({ paths: [testDir], recursive: false, rootDir: testDir })

    expect(result.filesProcessed).toBe(3)
  })
})

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true })
})
