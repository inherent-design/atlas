/**
 * Config Loader Tests
 *
 * Tests for config loading, merging, validation, and environment detection.
 */

describe('Config Loader', () => {
  // Save original env vars
  const originalEnv = { ...process.env }

  beforeEach(() => {
    // Reset module cache to force fresh imports
    vi.resetModules()

    // Override HOME to prevent loading system-wide config from ~/.atlas/
    process.env.HOME = '/tmp/atlas-test-home-nonexistent'
  })

  afterEach(() => {
    // Restore original environment
    process.env = { ...originalEnv }
  })

  describe('Default Configuration', () => {
    it('should return default config when no user config found', async () => {
      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig('/nonexistent/path/atlas.config.ts')

      expect(config).toBeDefined()
      expect(config.backends).toBeDefined()
      expect(config.logging?.level).toBe('info')
    })

    it('should cache config after first load', async () => {
      const { loadConfig } = await import('./config.loader')
      const config1 = await loadConfig()
      const config2 = await loadConfig()

      expect(config1).toBe(config2) // Same instance
    })

    it('should return cached config with getConfig()', async () => {
      const { loadConfig, getConfig } = await import('./config.loader')
      await loadConfig()
      const config = getConfig()

      expect(config).toBeDefined()
      expect(config.backends).toBeDefined()
    })

    it('should reset config cache when _resetConfig() called', async () => {
      const { loadConfig, _resetConfig } = await import('./config.loader')
      const config1 = await loadConfig()
      _resetConfig()
      const config2 = await loadConfig()

      // Should be different instances after reset
      expect(config1).not.toBe(config2)
    })
  })

  describe('Environment-Based Provider Detection', () => {
    it('should enable Voyage backends when VOYAGE_API_KEY present', async () => {
      process.env.VOYAGE_API_KEY = 'test-key'

      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      expect(config.backends?.['text-embedding']).toBe('voyage:voyage-3-large')
      expect(config.backends?.['code-embedding']).toBe('voyage:voyage-code-3')
      expect(config.backends?.['contextualized-embedding']).toBe('voyage:voyage-context-3')
      expect(config.backends?.['reranking']).toBe('voyage:rerank-2.5')
    })

    it('should enable Anthropic API backends when ANTHROPIC_API_KEY present', async () => {
      process.env.ANTHROPIC_API_KEY = 'test-key'

      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      expect(config.backends?.['text-completion']).toBe('anthropic:haiku')
      expect(config.backends?.['json-completion']).toBe('anthropic:haiku')
      // Note: qntm-generation removed - uses json-completion capability instead
    })

    it('should use Ollama fallback when neither API key present', async () => {
      delete process.env.VOYAGE_API_KEY
      delete process.env.ANTHROPIC_API_KEY

      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      expect(config.backends?.['text-embedding']).toBe('ollama:nomic-embed-text')
      expect(config.backends?.['text-completion']).toBe('ollama:ministral-3:3b')
    })

    it('should enable both Voyage and Anthropic when both keys present', async () => {
      process.env.VOYAGE_API_KEY = 'test-voyage-key'
      process.env.ANTHROPIC_API_KEY = 'test-anthropic-key'

      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      expect(config.backends?.['text-embedding']).toBe('voyage:voyage-3-large')
      expect(config.backends?.['text-completion']).toBe('anthropic:haiku')
    })
  })

  describe('Config Merge Precedence', () => {
    it('should apply default config at lowest precedence', async () => {
      delete process.env.VOYAGE_API_KEY
      delete process.env.ANTHROPIC_API_KEY

      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      // Should have defaults from config.schema.ts
      expect(config.logging?.level).toBe('info')
    })

    it('should apply environment-detected providers at medium precedence', async () => {
      process.env.VOYAGE_API_KEY = 'test-key'

      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      // Environment detection should override defaults
      expect(config.backends?.['text-embedding']).toBe('voyage:voyage-3-large')
    })

    // Note: User config testing would require creating a temp config file
    // which is complex in Vitest. Skipping for now - tested via integration.
  })

  describe('Config Validation', () => {
    it('should accept valid config without errors', async () => {
      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      // Should not throw
      expect(config).toBeDefined()
      expect(config.backends).toBeDefined()
    })

    it('should have all required backend capabilities defined', async () => {
      process.env.VOYAGE_API_KEY = 'test-key'
      process.env.ANTHROPIC_API_KEY = 'test-key'

      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      // Check all required capabilities (from capabilities.ts)
      // Embedding
      expect(config.backends?.['text-embedding']).toBeDefined()
      expect(config.backends?.['code-embedding']).toBeDefined()
      expect(config.backends?.['contextualized-embedding']).toBeDefined()
      // LLM (json-completion used for QNTM generation, consolidation)
      expect(config.backends?.['text-completion']).toBeDefined()
      expect(config.backends?.['json-completion']).toBeDefined()
      // Reranker
      expect(config.backends?.['reranking']).toBeDefined()
    })

    it('should validate backend specifier format', async () => {
      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      // All backends should follow provider:model pattern
      Object.values(config.backends || {}).forEach((backend) => {
        expect(backend).toMatch(/^[a-z-]+:[a-z0-9-:.]+$/)
      })
    })
  })

  describe('Logging Configuration', () => {
    it('should default to info log level', async () => {
      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      expect(config.logging?.level).toBe('info')
    })
  })

  describe('Backend Specifier Parsing', () => {
    it('should handle voyage backend specifiers', async () => {
      process.env.VOYAGE_API_KEY = 'test-key'

      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      expect(config.backends?.['text-embedding']).toContain('voyage:')
      expect(config.backends?.['reranking']).toContain('voyage:')
    })

    it('should handle ollama backend specifiers', async () => {
      delete process.env.VOYAGE_API_KEY
      delete process.env.ANTHROPIC_API_KEY

      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      expect(config.backends?.['text-embedding']).toContain('ollama:')
      expect(config.backends?.['text-completion']).toContain('ollama:')
    })

    it('should handle anthropic backend specifiers', async () => {
      process.env.ANTHROPIC_API_KEY = 'test-key'

      const { loadConfig } = await import('./config.loader')
      const config = await loadConfig()

      expect(config.backends?.['text-completion']).toContain('anthropic:')
    })
  })
})
