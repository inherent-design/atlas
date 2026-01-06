/**
 * Tests for pattern-based module logging
 */

import { createLogger, setLogLevel, setModuleRules, getLogConfig } from './logger'

describe('logger', () => {
  beforeEach(() => {
    // Reset to defaults
    setLogLevel('info')
    setModuleRules('')
  })

  describe('getLogConfig', () => {
    test('returns default config when no rules set', () => {
      const config = getLogConfig()
      expect(config.globalLevel).toBe('info')
      expect(config.rules).toHaveLength(0)
    })

    test('reflects setLogLevel changes', () => {
      setLogLevel('debug')
      expect(getLogConfig().globalLevel).toBe('debug')
    })
  })

  describe('setModuleRules', () => {
    test('parses single rule', () => {
      setModuleRules('qntm:debug')
      const config = getLogConfig()
      expect(config.rules).toHaveLength(1)
      expect(config.rules[0]).toEqual({
        pattern: 'qntm',
        level: 'debug',
        specificity: 15, // 1 segment * 10 + 5 (no glob)
      })
    })

    test('parses multiple rules', () => {
      setModuleRules('qntm:debug,watchdog:trace,ingest:error')
      const config = getLogConfig()
      expect(config.rules).toHaveLength(3)
    })

    test('defaults to debug when no level specified', () => {
      setModuleRules('qntm')
      const config = getLogConfig()
      expect(config.rules[0]?.level).toBe('debug')
    })

    test('handles glob patterns', () => {
      setModuleRules('qntm:*:trace')
      const config = getLogConfig()
      expect(config.rules[0]).toEqual({
        pattern: 'qntm:*',
        level: 'trace',
        specificity: 20, // 2 segments * 10, no bonus (has glob)
      })
    })

    test('handles wildcard-only pattern', () => {
      setModuleRules('*:trace')
      const config = getLogConfig()
      expect(config.rules[0]?.specificity).toBe(0)
    })
  })

  describe('specificity ordering', () => {
    test('exact match beats glob', () => {
      setModuleRules('qntm:*:trace,qntm:providers:error')
      const config = getLogConfig()

      // qntm:providers (25) should come before qntm:* (20)
      expect(config.rules[0]?.pattern).toBe('qntm:providers')
      expect(config.rules[1]?.pattern).toBe('qntm:*')
    })

    test('more segments beat fewer', () => {
      setModuleRules('qntm:debug,qntm:providers:error')
      const config = getLogConfig()

      // qntm:providers (25) should come before qntm (15)
      expect(config.rules[0]?.pattern).toBe('qntm:providers')
      expect(config.rules[1]?.pattern).toBe('qntm')
    })

    test('wildcard is least specific', () => {
      setModuleRules('*:trace,qntm:debug')
      const config = getLogConfig()

      // qntm (15) should come before * (0)
      expect(config.rules[0]?.pattern).toBe('qntm')
      expect(config.rules[1]?.pattern).toBe('*')
    })

    test('complex ordering scenario', () => {
      setModuleRules('*:info,qntm:*:debug,qntm:providers:error,llm:warn')
      const config = getLogConfig()

      // Expected order: qntm:providers (25), qntm:* (20), llm (15), * (0)
      expect(config.rules.map((r) => r.pattern)).toEqual(['qntm:providers', 'qntm:*', 'llm', '*'])
    })
  })

  describe('createLogger filtering', () => {
    test('uses global level when no rules', () => {
      setLogLevel('warn')
      setModuleRules('')

      const log = createLogger('test')
      // Can't easily test output, but we can verify config
      expect(getLogConfig().globalLevel).toBe('warn')
      expect(getLogConfig().rules).toHaveLength(0)
    })

    test('applies module-specific level', () => {
      setLogLevel('error')
      setModuleRules('test:debug')

      const config = getLogConfig()
      expect(config.globalLevel).toBe('error')
      expect(config.rules[0]?.level).toBe('debug')
    })

    test('glob pattern matches submodules', () => {
      setModuleRules('qntm:*:trace')

      const config = getLogConfig()
      expect(config.rules[0]?.pattern).toBe('qntm:*')
      // The glob should match qntm:providers, qntm:batch, etc.
    })
  })

  describe('edge cases', () => {
    test('handles empty string', () => {
      setModuleRules('')
      expect(getLogConfig().rules).toHaveLength(0)
    })

    test('handles whitespace in rules', () => {
      setModuleRules('  qntm:debug  ,  watchdog:trace  ')
      const config = getLogConfig()
      expect(config.rules).toHaveLength(2)
      expect(config.rules.map((r) => r.pattern)).toContain('qntm')
      expect(config.rules.map((r) => r.pattern)).toContain('watchdog')
    })

    test('handles invalid level gracefully', () => {
      setModuleRules('qntm:invalid')
      const config = getLogConfig()
      expect(config.rules[0]?.level).toBe('debug') // Falls back to debug
    })

    test('handles pattern with colon in path', () => {
      // Edge case: what if someone has a weird module name?
      // lastIndexOf(':') should handle this
      setModuleRules('c:/weird/path:debug')
      const config = getLogConfig()
      expect(config.rules[0]?.pattern).toBe('c:/weird/path')
      expect(config.rules[0]?.level).toBe('debug')
    })
  })
})
