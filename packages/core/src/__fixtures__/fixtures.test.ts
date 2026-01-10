/**
 * Test fixtures verification
 *
 * Ensures all fixtures and mocks work correctly.
 */

import { describe, test, expect } from 'vitest'
import {
  CHUNKS,
  EMBEDDINGS,
  createChunkPayload,
  generateEmbedding,
  cosineSimilarity,
  ChunkPayloadBuilder,
  generateVectorPointBatch,
  SEARCH_OPTIONS,
  createSearchResult,
} from './index'
import {
  createMockEmbeddingBackend,
  createMockStorageBackend,
  createMockLLMBackend,
  createMockRerankerBackend,
} from '../__mocks__'
import { createTestContext, withMockedBackends } from './utils'

describe('Fixtures', () => {
  describe('Chunks', () => {
    test('should provide predefined chunks', () => {
      expect(CHUNKS.markdown).toBeDefined()
      expect(CHUNKS.typescript).toBeDefined()
      expect(CHUNKS.consolidated).toBeDefined()
      expect(CHUNKS.markdown.original_text).toBeTruthy()
      expect(CHUNKS.markdown.qntm_keys.length).toBeGreaterThan(0)
    })

    test('should create custom chunks', () => {
      const chunk = createChunkPayload({
        original_text: 'Custom test',
        qntm_keys: ['@test ~ custom'],
      })
      expect(chunk.original_text).toBe('Custom test')
      expect(chunk.qntm_keys).toContain('@test ~ custom')
    })

    test('should build chunks with builder', () => {
      const chunk = new ChunkPayloadBuilder()
        .withText('Builder test')
        .withFilePath('/test/builder.md')
        .withQntmKeys('@builder ~ test')
        .withConsolidationLevel(1)
        .build()

      expect(chunk.original_text).toBe('Builder test')
      expect(chunk.file_path).toBe('/test/builder.md')
      expect(chunk.consolidation_level).toBe(1)
    })
  })

  describe('Embeddings', () => {
    test('should generate deterministic embeddings', () => {
      const v1 = generateEmbedding('test-seed')
      const v2 = generateEmbedding('test-seed')

      expect(v1).toHaveLength(16)
      expect(v1).toEqual(v2) // Same seed = same vector
    })

    test('should provide predefined embeddings', () => {
      expect(EMBEDDINGS.default).toHaveLength(16)
      expect(EMBEDDINGS.memory).toHaveLength(16)
      expect(EMBEDDINGS.code).toHaveLength(16)
    })

    test('should calculate cosine similarity', () => {
      const v1 = generateEmbedding('test1')
      const v2 = generateEmbedding('test2')
      const sim = cosineSimilarity(v1, v2)

      expect(sim).toBeGreaterThanOrEqual(-1)
      expect(sim).toBeLessThanOrEqual(1)
    })

    test('should have perfect similarity for same vector', () => {
      const v1 = generateEmbedding('identical')
      const sim = cosineSimilarity(v1, v1)

      expect(sim).toBeCloseTo(1.0, 5)
    })
  })

  describe('Search', () => {
    test('should provide search options', () => {
      expect(SEARCH_OPTIONS.basic).toBeDefined()
      expect(SEARCH_OPTIONS.reranked).toBeDefined()
      expect(SEARCH_OPTIONS.basic.query).toBeTruthy()
    })

    test('should create search results', () => {
      const result = createSearchResult(CHUNKS.markdown, 0.92)

      expect(result.text).toBe(CHUNKS.markdown.original_text)
      expect(result.score).toBe(0.92)
      expect(result.file_path).toBe(CHUNKS.markdown.file_path)
    })
  })

  describe('Factories', () => {
    test('should generate vector point batch', () => {
      const points = generateVectorPointBatch(5, 'test', 'text')

      expect(points).toHaveLength(5)
      expect(points[0]!.id).toContain('test')
      expect(points[0]!.vector.text).toBeDefined()
      expect(points[0]!.vector.text).toHaveLength(16)
    })
  })
})

describe('Mocks', () => {
  describe('EmbeddingBackend', () => {
    test('should return deterministic embeddings', async () => {
      const backend = createMockEmbeddingBackend()
      const result = await backend.embedText('test input')

      expect(result.embeddings).toHaveLength(1)
      expect(result.embeddings[0]).toHaveLength(16)
      expect(result.model).toBe('mock-embedding-1024')
    })

    test('should track calls', async () => {
      const backend = createMockEmbeddingBackend()
      await backend.embedText('test1')
      await backend.embedText('test2')

      expect(backend.getCallCount('embedText')).toBe(2)
    })

    test('should support fixed embeddings', async () => {
      const backend = createMockEmbeddingBackend()
      const fixed = new Array(16).fill(0.5)
      backend.setFixedEmbedding('specific', fixed)

      const result = await backend.embedText('specific')
      expect(result.embeddings[0]).toEqual(fixed)
    })

    test('should throw configured errors', async () => {
      const backend = createMockEmbeddingBackend()
      backend.setError(new Error('Service unavailable'))

      await expect(backend.embedText('test')).rejects.toThrow('Service unavailable')
    })
  })

  describe('StorageBackend', () => {
    test('should create and manage collections', async () => {
      const backend = createMockStorageBackend()

      await backend.createCollection('test', {
        dimensions: 16,
        distance: 'cosine',
      })

      const exists = await backend.collectionExists('test')
      expect(exists).toBe(true)
    })

    test('should upsert and retrieve points', async () => {
      const backend = createMockStorageBackend()
      await backend.createCollection('test', { dimensions: 1024, distance: 'cosine' })

      const points = generateVectorPointBatch(3)
      await backend.upsert('test', points)

      const retrieved = await backend.retrieve('test', [points[0]!.id])
      expect(retrieved).toHaveLength(1)
      expect(retrieved[0]!.id).toBe(points[0]!.id)
    })

    test('should search and return sorted results', async () => {
      const backend = createMockStorageBackend()
      await backend.createCollection('test', { dimensions: 1024, distance: 'cosine' })

      const points = generateVectorPointBatch(5)
      await backend.upsert('test', points)

      const query = generateEmbedding('query')
      const results = await backend.search('test', {
        vector: query,
        limit: 3,
      })

      expect(results).toHaveLength(3)
      // Verify sorted descending
      for (let i = 1; i < results.length; i++) {
        expect(results[i]!.score).toBeLessThanOrEqual(results[i - 1]!.score)
      }
    })
  })

  describe('LLMBackend', () => {
    test('should return JSON responses', async () => {
      const backend = createMockLLMBackend({
        defaultJSON: { type: 'test', value: 42 },
      })

      const result = await backend.completeJSON('test prompt')
      expect(result).toEqual({ type: 'test', value: 42 })
    })

    test('should track calls', async () => {
      const backend = createMockLLMBackend()
      await backend.complete('test1')
      await backend.completeJSON('test2')

      expect(backend.getCallCount()).toBe(2)
      expect(backend.getCallCount('complete')).toBe(1)
      expect(backend.getCallCount('completeJSON')).toBe(1)
    })

    test('should support prompt-specific responses', async () => {
      const backend = createMockLLMBackend()
      backend.setResponse('specific prompt', { custom: 'response' })

      const result = await backend.completeJSON('specific prompt')
      expect(result).toEqual({ custom: 'response' })
    })
  })

  describe('RerankerBackend', () => {
    test('should rerank documents', async () => {
      const backend = createMockRerankerBackend()
      const docs = ['doc1', 'doc2', 'doc3']

      const result = await backend.rerank('query', docs)

      expect(result.results).toHaveLength(3)
      expect(result.model).toBe('mock-rerank-1.0')
    })

    test('should respect topK limit', async () => {
      const backend = createMockRerankerBackend()
      const docs = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']

      const result = await backend.rerank('query', docs, { topK: 2 })

      expect(result.results).toHaveLength(2)
    })

    test('should support different strategies', async () => {
      const backend = createMockRerankerBackend()
      backend.setStrategy('reverse-order')

      const docs = ['doc1', 'doc2', 'doc3']
      const result = await backend.rerank('query', docs)

      // With reverse-order, later docs should have higher scores
      expect(result.results[0]!.score).toBeGreaterThan(result.results[2]!.score)
    })
  })
})

describe('Test Utilities', () => {
  test('should create test context', () => {
    const ctx = createTestContext()

    expect(ctx.embedding).toBeDefined()
    expect(ctx.storage).toBeDefined()
    expect(ctx.llm).toBeDefined()
    expect(ctx.reranker).toBeDefined()
    expect(ctx.cleanup).toBeInstanceOf(Function)
  })

  test('should cleanup context', async () => {
    const ctx = createTestContext()
    await ctx.embedding.embedText('test')
    await ctx.storage.createCollection('test', { dimensions: 1024, distance: 'cosine' })

    ctx.cleanup()

    expect(ctx.embedding.getCallCount()).toBe(0)
    expect(ctx.storage.getCallCount()).toBe(0)
  })

  test('should work with withMockedBackends', async () => {
    const result = await withMockedBackends(async (ctx) => {
      await ctx.embedding.embedText('test')
      return ctx.embedding.getCallCount()
    })

    expect(result).toBe(1)
  })
})
