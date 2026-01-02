import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['src/**/*.test.ts'],
    testTimeout: 15000, // CLI tests may need more time
  },
})
