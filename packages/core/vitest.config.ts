import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: {
      // Mock Bun runtime for Vitest compatibility
      bun: fileURLToPath(new URL('./test-bun-shim.ts', import.meta.url)),
      // Mock bun-webgpu (GPU detection not needed in tests)
      'bun-webgpu': fileURLToPath(new URL('./test-bun-shim.ts', import.meta.url)),
      // Mock bun:sqlite using better-sqlite3 (for test compatibility)
      'bun:sqlite': fileURLToPath(new URL('./test-bun-sqlite-shim.ts', import.meta.url)),
    },
  },
  test: {
    // Process-level isolation: each test file runs in separate child process
    // This prevents mock.module() leaks between files (the core issue with bun:test)
    pool: 'forks',

    // DOM environment for future React SSR testing
    environment: 'happy-dom',

    // Auto-restore mocks after each test
    restoreMocks: true,
    mockReset: true,
    clearMocks: true,

    // Global APIs (describe, test, expect, vi) without imports
    globals: true,

    // Test file patterns (unit tests only)
    include: ['src/**/*.test.ts'],
    exclude: ['node_modules', 'dist', 'src/**/*.e2e.test.ts', 'src/__tests__/e2e/**'],

    // Timeouts
    testTimeout: 10000,
    hookTimeout: 10000,

    // Coverage (when running with --coverage)
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['src/**/*.ts'],
      exclude: ['src/**/*.test.ts', 'src/**/*.d.ts'],
    },
  },
})
