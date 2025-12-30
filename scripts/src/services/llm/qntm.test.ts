/**
 * Unit tests for QNTM provider abstraction
 *
 * Note: Uses dynamic imports to ensure mocks are set up before module loading.
 * This prevents mock pollution from other test files (e.g., llm/batch.test.ts).
 */

import { afterEach, beforeEach, describe, expect, mock, test } from 'bun:test'
import type { QNTMGenerationInput } from '.'

// Store original globals for restoration
const originalFetch = global.fetch
const originalSpawn = Bun.spawn

// Mock completeJSON from llm/ module BEFORE importing qntm/providers
const mockCompleteJSON = mock(async () => ({
  keys: ['@memory ~ consolidation', '@patterns ~ neural'],
  reasoning: 'Test reasoning',
}))

const mockCheckOllamaAvailable = mock(async () => true)
const mockDetectProvider = mock(async () => 'ollama' as const)

// Set up module mocks before any imports that use them
mock.module('./providers', () => ({
  completeJSON: mockCompleteJSON,
  checkOllamaAvailable: mockCheckOllamaAvailable,
  detectProvider: mockDetectProvider,
  complete: mock(async () => ({ content: '{}', usage: {} })),
}))

mock.module('.', () => ({
  completeJSON: mockCompleteJSON,
  checkOllamaAvailable: mockCheckOllamaAvailable,
  detectProvider: mockDetectProvider,
}))

// Now dynamically import the module under test
const { generateQNTMKeysWithProvider, checkOllamaAvailable, detectProvider, buildQNTMPrompt } =
  await import('./qntm')

describe('qntm-providers', () => {
  beforeEach(() => {
    // Reset mocks between tests
    mockCompleteJSON.mockClear()
    mockCheckOllamaAvailable.mockClear()
    mockDetectProvider.mockClear()

    // Restore globals
    global.fetch = originalFetch
    ;(Bun as any).spawn = originalSpawn
  })

  afterEach(() => {
    // Ensure globals are restored
    global.fetch = originalFetch
    ;(Bun as any).spawn = originalSpawn
  })

  describe('buildQNTMPrompt', () => {
    test('includes chunk text in prompt', () => {
      const input: QNTMGenerationInput = {
        chunk: 'Test chunk content',
        existingKeys: [],
      }

      const prompt = buildQNTMPrompt(input)

      expect(prompt).toContain('Test chunk content')
    })

    test('includes existing keys in prompt', () => {
      const input: QNTMGenerationInput = {
        chunk: 'Test chunk',
        existingKeys: ['@memory ~ type ~ episodic', '@database ~ strategy ~ indexing'],
      }

      const prompt = buildQNTMPrompt(input)

      expect(prompt).toContain('@memory ~ type ~ episodic')
      expect(prompt).toContain('@database ~ strategy ~ indexing')
    })

    test('includes context when provided', () => {
      const input: QNTMGenerationInput = {
        chunk: 'Test chunk',
        existingKeys: [],
        context: {
          fileName: 'test.md',
          chunkIndex: 2,
          totalChunks: 5,
        },
      }

      const prompt = buildQNTMPrompt(input)

      expect(prompt).toContain('test.md')
      expect(prompt).toContain('chunk 2/5')
    })

    test('shows (none yet) when no existing keys', () => {
      const input: QNTMGenerationInput = {
        chunk: 'Test chunk',
        existingKeys: [],
      }

      const prompt = buildQNTMPrompt(input)

      expect(prompt).toContain('(none yet)')
    })
  })

  describe('generateQNTMKeysWithProvider', () => {
    const mockInput: QNTMGenerationInput = {
      chunk: 'This is a test chunk about memory consolidation patterns.',
      existingKeys: ['@existing ~ key ~ value'],
      context: {
        fileName: 'test.md',
        chunkIndex: 0,
        totalChunks: 1,
      },
    }

    describe('with mocked LLM layer', () => {
      test('generates keys via completeJSON', async () => {
        const result = await generateQNTMKeysWithProvider(mockInput, {
          provider: 'anthropic',
          model: 'haiku',
        })

        expect(result.keys).toHaveLength(2)
        expect(result.keys).toContain('@memory ~ consolidation')
        expect(result.reasoning).toBe('Test reasoning')
        expect(mockCompleteJSON).toHaveBeenCalled()
      })

      test('passes config to completeJSON', async () => {
        await generateQNTMKeysWithProvider(mockInput, {
          provider: 'ollama',
          model: 'ministral-3:3b',
          ollamaHost: 'http://localhost:11434',
        })

        expect(mockCompleteJSON).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            provider: 'ollama',
            model: 'ministral-3:3b',
            ollamaHost: 'http://localhost:11434',
          })
        )
      })

      test('includes existing keys in prompt sent to LLM', async () => {
        await generateQNTMKeysWithProvider(mockInput, {
          provider: 'anthropic',
          model: 'haiku',
        })

        const promptArg = mockCompleteJSON.mock.calls[0]?.[0] as string
        expect(promptArg).toContain('@existing ~ key ~ value')
      })

      test('includes context in prompt when provided', async () => {
        await generateQNTMKeysWithProvider(mockInput, {
          provider: 'ollama',
          model: 'ministral-3:3b',
        })

        const promptArg = mockCompleteJSON.mock.calls[0]?.[0] as string
        expect(promptArg).toContain('test.md')
        expect(promptArg).toContain('chunk 0/1')
      })

      test('handles LLM errors', async () => {
        mockCompleteJSON.mockImplementationOnce(async () => {
          throw new Error('LLM API error')
        })

        await expect(
          generateQNTMKeysWithProvider(mockInput, {
            provider: 'anthropic',
            model: 'haiku',
          })
        ).rejects.toThrow('LLM API error')
      })
    })
  })

  describe('checkOllamaAvailable', () => {
    test('returns result from LLM module', async () => {
      mockCheckOllamaAvailable.mockResolvedValueOnce(true)

      const available = await checkOllamaAvailable('http://localhost:11434')
      expect(available).toBe(true)
    })

    test('returns false when unavailable', async () => {
      mockCheckOllamaAvailable.mockResolvedValueOnce(false)

      const available = await checkOllamaAvailable('http://localhost:11434')
      expect(available).toBe(false)
    })
  })

  describe('detectProvider', () => {
    test('returns detected provider', async () => {
      mockDetectProvider.mockResolvedValueOnce('ollama')

      const provider = await detectProvider()
      expect(provider).toBe('ollama')
    })

    test('returns anthropic when detected', async () => {
      mockDetectProvider.mockResolvedValueOnce('anthropic')

      const provider = await detectProvider()
      expect(provider).toBe('anthropic')
    })
  })
})
