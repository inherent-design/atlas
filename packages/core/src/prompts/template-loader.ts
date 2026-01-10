/**
 * Template Loader - Runtime file loading for prompt content
 *
 * Loads prompt templates from external .md files at runtime instead of
 * embedding them in TypeScript source. This prevents heap OOM during
 * parallel test execution by avoiding large string allocation at module load.
 */

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join, dirname } from 'node:path'

// Detect test environment
const IS_TEST =
  typeof process !== 'undefined' &&
  (process.env.VITEST === 'true' || process.env.NODE_ENV === 'test')

// Cache for loaded templates (production only)
const templateCache = new Map<string, string>()

/**
 * Load template from file system.
 * Caches after first load in production.
 * Returns mock content in test environment.
 *
 * @param filename - Template filename in templates/ directory
 * @param mockContent - Content to return in test environment
 * @returns Template content
 */
export function loadTemplate(filename: string, mockContent: string): string {
  // Test environment: return mock immediately
  if (IS_TEST) {
    return mockContent
  }

  // Check cache first
  if (templateCache.has(filename)) {
    return templateCache.get(filename)!
  }

  // Load from filesystem
  const __filename = fileURLToPath(import.meta.url)
  const __dirname = dirname(__filename)
  const templatePath = join(__dirname, 'templates', filename)

  const content = readFileSync(templatePath, 'utf-8')

  // Cache for future calls
  templateCache.set(filename, content)

  return content
}

/**
 * Clear template cache (for testing)
 */
export function clearTemplateCache(): void {
  templateCache.clear()
}
