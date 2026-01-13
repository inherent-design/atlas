#!/usr/bin/env node
/**
 * Build script for @inherent.design/atlas-core
 * Compiles all TypeScript files except tests using esbuild
 */

import fastGlob from 'fast-glob'
import * as esbuild from 'esbuild'

// Find all TS files except tests
const entryPoints = fastGlob.sync('src/**/*.ts', {
  ignore: ['**/*.test.ts', '**/__tests__/**'],
  absolute: false
})

console.log(`Building ${entryPoints.length} files...`)

await esbuild.build({
  entryPoints,
  outdir: 'dist',
  platform: 'node',
  format: 'esm',
  packages: 'external',
  logLevel: 'info',
})

console.log('✅ Build complete')
