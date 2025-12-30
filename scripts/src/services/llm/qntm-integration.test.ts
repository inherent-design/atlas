/**
 * Unit tests for QNTM orchestration layer
 */

import { describe, expect, test } from 'bun:test'
import { getQNTMProvider, sanitizeQNTMKey, setQNTMProvider } from '.'

describe('qntm orchestration', () => {
  describe('provider configuration', () => {
    test('setQNTMProvider updates configuration', () => {
      setQNTMProvider({
        provider: 'anthropic',
        model: 'sonnet',
        ollamaHost: 'http://custom:11434',
      })

      const config = getQNTMProvider()

      expect(config.provider).toBe('anthropic')
      expect(config.model).toBe('sonnet')
      expect(config.ollamaHost).toBe('http://custom:11434')
    })

    test('getQNTMProvider returns current configuration', () => {
      setQNTMProvider({
        provider: 'ollama',
        model: 'ministral-3:3b',
      })

      const config = getQNTMProvider()

      expect(config.provider).toBe('ollama')
      expect(config.model).toBe('ministral-3:3b')
    })

    test('provider config persists across calls', () => {
      setQNTMProvider({ provider: 'anthropic', model: 'opus' })

      const config1 = getQNTMProvider()
      const config2 = getQNTMProvider()

      expect(config1).toEqual(config2)
    })
  })

  // Note: generateQNTMKeys is tested via integration tests in ingest.test.ts
  // Direct unit testing requires complex mocking that causes conflicts with other test files

  describe('sanitizeQNTMKey', () => {
    test('removes @ prefix', () => {
      const sanitized = sanitizeQNTMKey('@memory ~ consolidation')
      expect(sanitized).not.toContain('@')
    })

    test('replaces ~ with underscore', () => {
      const sanitized = sanitizeQNTMKey('@memory ~ consolidation')
      expect(sanitized).toContain('_')
      expect(sanitized).not.toContain('~')
    })

    test('replaces spaces with underscore', () => {
      const sanitized = sanitizeQNTMKey('@memory consolidation patterns')
      expect(sanitized).not.toContain(' ')
      expect(sanitized).toContain('_')
    })

    test('converts to lowercase', () => {
      const sanitized = sanitizeQNTMKey('@Memory ~ CONSOLIDATION')
      expect(sanitized).toBe('memory___consolidation')
    })

    test('removes invalid characters', () => {
      const input = '@test!@#$%^&*()key'
      const sanitized = sanitizeQNTMKey(input)

      // Should only contain lowercase alphanumeric, underscore, and hyphen
      expect(sanitized).toMatch(/^[a-z0-9_-]+$/)
      expect(sanitized).toBe('testkey')
    })

    test('handles complex QNTM keys', () => {
      const complex = '@consciousness ~ emergence ~ self_reference'
      const sanitized = sanitizeQNTMKey(complex)

      expect(sanitized).toBe('consciousness___emergence___self_reference')
    })

    test('handles empty string', () => {
      const sanitized = sanitizeQNTMKey('')
      expect(sanitized).toBe('')
    })

    test('preserves hyphens and underscores', () => {
      const sanitized = sanitizeQNTMKey('@test-key_name')
      expect(sanitized).toContain('-')
      expect(sanitized).toContain('_')
    })
  })

  // Note: fetchExistingQNTMKeys and integration workflows are tested via ingest.test.ts
  // These require Qdrant client mocking which conflicts with other test file mocks

  describe('integration scenarios', () => {
    test('key sanitization matches collection naming', () => {
      const qntmKey = '@memory ~ consolidation ~ episodic'
      const sanitized = sanitizeQNTMKey(qntmKey)

      // Should be valid Qdrant collection name
      expect(sanitized).toMatch(/^[a-z0-9_-]+$/)
      expect(sanitized.length).toBeGreaterThan(0)
    })
  })
})
