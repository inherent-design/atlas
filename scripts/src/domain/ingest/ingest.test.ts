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
}))

// Setup mocks - hoisted but now have access to hoisted mock functions
vi.mock('../../services/storage', () => ({
  getQdrantClient: () => ({
    getCollection: mockQdrantGet,
    createCollection: mockQdrantCreate,
    upsert: mockQdrantUpsert,
  }),
}))

vi.mock('../../services/embedding', () => ({
  getVoyageClient: () => ({
    embed: mockVoyageEmbed,
  }),
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
    sanitizeQNTMKey: actual.sanitizeQNTMKey,
    fetchExistingQNTMKeys: () => Promise.resolve([]),
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

    // Should have called voyage.embed
    expect(mockVoyageEmbed).toHaveBeenCalled()

    // Should have called qdrant.upsert (2 chunks × 2 keys = 4 upserts)
    expect(mockQdrantUpsert).toHaveBeenCalled()

    const firstUpsertCall = mockQdrantUpsert.mock.calls[0]
    const point = firstUpsertCall[1].points[0]

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

    // Collect all points from all upsert calls (multi-collection indexing)
    const allPoints = mockQdrantUpsert.mock.calls.flatMap((call: any) => call[1].points)
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
    const qntmKeys1 = call1[1].points[0].payload.qntm_keys

    mockQdrantUpsert.mockClear()
    mockGenerateQNTMKeysBatch.mockClear()

    await ingestFile(testFile2, testDir)
    const call2 = mockQdrantUpsert.mock.calls[0]
    const qntmKeys2 = call2[1].points[0].payload.qntm_keys

    expect(qntmKeys1).toEqual(qntmKeys2)
  })

  test('sets metadata correctly', async () => {
    const testFile = join(testDir, 'test.md')
    writeFileSync(testFile, '# Test')

    await ingestFile(testFile, testDir)

    const upsertCall = mockQdrantUpsert.mock.calls[0]
    const payload = upsertCall[1].points[0].payload

    expect(payload.file_name).toBe('test.md')
    expect(payload.file_type).toBe('.md')
    expect(payload.importance).toBe('normal')
    expect(payload.consolidated).toBe(false)
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
    writeFileSync(join(testDir, 'file1.md'), '# File 1\n\nContent 1')
    writeFileSync(join(testDir, 'file2.md'), '# File 2\n\nContent 2')

    const result = await ingest({
      paths: [join(testDir, 'file1.md'), join(testDir, 'file2.md')],
      recursive: false,
      rootDir: testDir,
    })

    expect(result.filesProcessed).toBe(2)
    // Each file batch upserts all chunks to unified collection = 1 upsert per file = 2 total
    expect(mockQdrantUpsert).toHaveBeenCalledTimes(2)
  })

  test('expands directories without recursion', async () => {
    writeFileSync(join(testDir, 'file1.md'), '# File 1')
    writeFileSync(join(testDir, 'file2.md'), '# File 2')

    mkdirSync(join(testDir, 'subdir'))
    writeFileSync(join(testDir, 'subdir', 'file3.md'), '# File 3')

    const result = await ingest({ paths: [testDir], recursive: false, rootDir: testDir })

    expect(result.filesProcessed).toBe(2) // Only top-level files
  })

  test('expands directories with recursion', async () => {
    writeFileSync(join(testDir, 'file1.md'), '# File 1')

    mkdirSync(join(testDir, 'subdir'))
    writeFileSync(join(testDir, 'subdir', 'file2.md'), '# File 2')

    const result = await ingest({ paths: [testDir], recursive: true, rootDir: testDir })

    expect(result.filesProcessed).toBe(2) // All files including subdirectory
  })

  test('ensures collection exists before ingesting', async () => {
    writeFileSync(join(testDir, 'test.md'), '# Test')

    await ingest({ paths: [join(testDir, 'test.md')], recursive: false, rootDir: testDir })

    // Should have attempted to get collection
    expect(mockQdrantGet).toHaveBeenCalled()

    // Should have created collection (since get failed)
    expect(mockQdrantCreate).toHaveBeenCalled()
  })

  test('returns count of ingested files', async () => {
    writeFileSync(join(testDir, 'file1.md'), 'content')
    writeFileSync(join(testDir, 'file2.md'), 'content')
    writeFileSync(join(testDir, 'file3.md'), 'content')

    const result = await ingest({ paths: [testDir], recursive: false, rootDir: testDir })

    expect(result.filesProcessed).toBe(3)
  })
})

afterEach(() => {
  rmSync(testDir, { recursive: true, force: true })
})
