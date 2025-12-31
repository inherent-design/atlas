/**
 * Unit tests for QNTM provider abstraction
 *
 * Note: Integration tests with actual LLM calls are in qntm-integration.test.ts
 * These tests focus on the prompt building and utility functions that don't require mocking.
 */

import type { QNTMGenerationInput } from '.'
import { buildQNTMPrompt } from './qntm'

describe('qntm-providers', () => {
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

  // Note: generateQNTMKeysWithProvider, checkOllamaAvailable, and detectProvider
  // require complex mocking scenarios that are tested via integration tests.
  // With Vitest's process isolation, mocking the LLM layer is straightforward
  // and these tests don't need the dynamic import workarounds from bun:test.
})
