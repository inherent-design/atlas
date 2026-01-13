import { defineConfig } from 'tsdown'
import fastGlob from 'fast-glob'

// Get all source files excluding tests, mocks, and fixtures
const entryPoints = fastGlob.sync('src/**/*.ts', {
  ignore: [
    '**/*.test.ts',
    '**/__tests__/**',
    '**/__mocks__/**',
    '**/__fixtures__/**',
  ],
  absolute: false,
})

export default defineConfig({
  entry: entryPoints,
  format: ['esm'],
  dts: true,
  clean: true,
  platform: 'node',
  outDir: 'dist',
  // Preserve directory structure (unbundle mode)
  unbundle: true,
  // Mark all dependencies as external (don't bundle them)
  external: [/node_modules/],
})
