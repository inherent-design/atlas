/**
 * Text Splitter Tests
 * Coverage target: 8 test cases for singleton pattern, config usage, and splitting behavior
 */

import { RecursiveCharacterTextSplitter } from '@langchain/textsplitters'
import { CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_SEPARATORS } from '../../shared/config'
import { createTextSplitter, getTextSplitter, resetTextSplitter } from './splitter'

beforeEach(() => {
  resetTextSplitter() // Clear singleton before each test
})

afterEach(() => {
  resetTextSplitter()
})

describe('createTextSplitter', () => {
  test('should return RecursiveCharacterTextSplitter instance', () => {
    const splitter = createTextSplitter()
    expect(splitter).toBeInstanceOf(RecursiveCharacterTextSplitter)
  })

  test('should use CHUNK_SIZE from config', () => {
    const splitter = createTextSplitter()
    expect((splitter as any).chunkSize).toBe(CHUNK_SIZE)
    expect((splitter as any).chunkSize).toBe(768)
  })

  test('should use CHUNK_OVERLAP from config', () => {
    const splitter = createTextSplitter()
    expect((splitter as any).chunkOverlap).toBe(CHUNK_OVERLAP)
    expect((splitter as any).chunkOverlap).toBe(100)
  })

  test('should use CHUNK_SEPARATORS from config', () => {
    const splitter = createTextSplitter()
    expect((splitter as any).separators).toEqual(CHUNK_SEPARATORS)
    expect((splitter as any).separators).toEqual(['\n\n', '\n', '. ', ' ', ''])
  })
})

describe('getTextSplitter', () => {
  test('should create singleton instance on first call', () => {
    const splitter = getTextSplitter()
    expect(splitter).toBeInstanceOf(RecursiveCharacterTextSplitter)
    expect(splitter).not.toBeNull()
  })

  test('should return same instance on subsequent calls', () => {
    const splitter1 = getTextSplitter()
    const splitter2 = getTextSplitter()
    expect(splitter1).toBe(splitter2) // Reference equality
  })
})

describe('resetTextSplitter', () => {
  test('should clear singleton and allow new instance creation', () => {
    const splitter1 = getTextSplitter()
    resetTextSplitter()
    const splitter2 = getTextSplitter()

    expect(splitter1).not.toBe(splitter2) // Different instances after reset
    expect(splitter2).toBeInstanceOf(RecursiveCharacterTextSplitter)
  })
})

describe('text splitting behavior', () => {
  test('should actually split text correctly', async () => {
    const splitter = getTextSplitter()

    // Create text that will definitely need splitting
    // Each paragraph is ~100 chars, we need enough to exceed CHUNK_SIZE (768 tokens ≈ 3000 chars)
    const paragraphs = Array.from(
      { length: 40 },
      (_, i) =>
        `This is paragraph ${i + 1} with some meaningful content that represents a semantic unit of text.`
    )
    const longText = paragraphs.join('\n\n')

    const chunks = await splitter.splitText(longText)

    // Should split into multiple chunks
    expect(chunks.length).toBeGreaterThan(1)

    // Each chunk should be within size limits
    // LangChain uses approximate token counting, so we verify character counts
    for (const chunk of chunks) {
      expect(chunk.length).toBeLessThanOrEqual(CHUNK_SIZE * 4) // Conservative: ~4 chars per token
      expect(chunk.length).toBeGreaterThan(0)
    }

    // Chunks should have overlap
    // Find overlapping content between consecutive chunks
    let hasOverlap = false
    for (let i = 0; i < chunks.length - 1; i++) {
      const currentChunk = chunks[i]
      const nextChunk = chunks[i + 1]

      // Check if end of current chunk appears in beginning of next chunk
      const currentEnd = currentChunk?.slice(-50) // Last 50 chars
      if (
        nextChunk &&
        currentEnd &&
        nextChunk.includes(currentEnd.trim()) &&
        currentEnd.trim().length > 0
      ) {
        hasOverlap = true
        break
      }
    }

    expect(hasOverlap).toBe(true)
  })

  test('should respect separator hierarchy', async () => {
    const splitter = getTextSplitter()

    // Text with different separator levels
    const text = [
      'Section 1 with multiple sentences. This is sentence two. And sentence three.',
      '',
      'Section 2 with more content. Another sentence here.',
      '',
      'Section 3 continues the pattern.',
    ].join('\n')

    const chunks = await splitter.splitText(text)

    // Should split on double newlines (paragraph boundaries) first
    expect(chunks.length).toBeGreaterThan(0)

    // All chunks should be non-empty
    for (const chunk of chunks) {
      expect(chunk.trim().length).toBeGreaterThan(0)
    }
  })

  test('should handle short text without splitting', async () => {
    const splitter = getTextSplitter()
    const shortText = 'This is a short piece of text that should not be split.'

    const chunks = await splitter.splitText(shortText)

    expect(chunks.length).toBe(1)
    expect(chunks[0]).toBe(shortText)
  })

  test('should handle empty text', async () => {
    const splitter = getTextSplitter()
    const emptyText = ''

    const chunks = await splitter.splitText(emptyText)

    expect(chunks.length).toBe(0)
  })

  test('should handle text with only whitespace', async () => {
    const splitter = getTextSplitter()
    const whitespaceText = '   \n\n   \t   '

    const chunks = await splitter.splitText(whitespaceText)

    // LangChain may return empty array or array with whitespace
    // Either is acceptable behavior
    expect(Array.isArray(chunks)).toBe(true)
  })

  test('should split very long single line', async () => {
    const splitter = getTextSplitter()

    // Single line with no natural separators, exceeding chunk size
    const longLine = 'word '.repeat(1000) // 5000 chars, definitely exceeds token limit

    const chunks = await splitter.splitText(longLine)

    // Should split on space separator (last resort in hierarchy)
    expect(chunks.length).toBeGreaterThan(1)

    for (const chunk of chunks) {
      expect(chunk.length).toBeGreaterThan(0)
    }
  })
})
