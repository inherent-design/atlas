/**
 * Unit tests for Atlas utility functions
 */

import { generateQNTMKey, generateChunkId, expandPaths } from './utils'
import { writeFileSync, mkdirSync, rmSync } from 'fs'
import { join } from 'path'

describe('generateQNTMKey', () => {
  test('generates consistent keys for same content', () => {
    const text = 'This is a test document about memory consolidation.'
    const key1 = generateQNTMKey(text)
    const key2 = generateQNTMKey(text)

    expect(key1).toBe(key2)
    expect(key1).toMatch(/^atlas_/)
  })

  test('generates different keys for different content', () => {
    const text1 = 'Document about memory consolidation.'
    const text2 = 'Document about semantic search.'

    const key1 = generateQNTMKey(text1)
    const key2 = generateQNTMKey(text2)

    expect(key1).not.toBe(key2)
  })

  test('handles long text by using first 500 chars', () => {
    const longText = 'A'.repeat(1000)
    const key = generateQNTMKey(longText)

    expect(key).toMatch(/^atlas_/)
    expect(key.length).toBe(14) // 'atlas_' + 8 char hash
  })

  test('handles empty string', () => {
    const key = generateQNTMKey('')
    expect(key).toMatch(/^atlas_/)
  })
})

describe('generateChunkId', () => {
  test('generates consistent IDs for same file/chunk', () => {
    const id1 = generateChunkId('docs/readme.md', 0)
    const id2 = generateChunkId('docs/readme.md', 0)

    expect(id1).toBe(id2)
  })

  test('generates different IDs for different chunks of same file', () => {
    const id1 = generateChunkId('docs/readme.md', 0)
    const id2 = generateChunkId('docs/readme.md', 1)

    expect(id1).not.toBe(id2)
  })

  test('generates different IDs for different files', () => {
    const id1 = generateChunkId('docs/readme.md', 0)
    const id2 = generateChunkId('docs/guide.md', 0)

    expect(id1).not.toBe(id2)
  })

  test('generates valid UUID format', () => {
    const id = generateChunkId('test.md', 0)
    // UUID format: 8-4-4-4-12 hex chars with hyphens
    expect(id).toMatch(/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/)
  })
})

describe('expandPaths', () => {
  const testDir = '/tmp/atlas-test-expand'

  // Setup test directory structure
  function setupTestDir() {
    rmSync(testDir, { recursive: true, force: true })
    mkdirSync(testDir, { recursive: true })

    // Create test files
    writeFileSync(join(testDir, 'file1.md'), 'content 1')
    writeFileSync(join(testDir, 'file2.ts'), 'content 2')
    writeFileSync(join(testDir, 'file3.txt'), 'content 3')
    writeFileSync(join(testDir, 'ignored.pdf'), 'binary') // Should be ignored

    // Create subdirectory
    mkdirSync(join(testDir, 'subdir'))
    writeFileSync(join(testDir, 'subdir', 'file4.md'), 'content 4')
    writeFileSync(join(testDir, 'subdir', 'file5.js'), 'content 5')

    // Create ignored directory
    mkdirSync(join(testDir, 'node_modules'))
    writeFileSync(join(testDir, 'node_modules', 'file6.md'), 'should ignore')
  }

  test('expands single file path', () => {
    setupTestDir()
    const file = join(testDir, 'file1.md')
    const files = expandPaths([file], false)

    expect(files).toEqual([file])
  })

  test('expands directory without recursion', () => {
    setupTestDir()
    const files = expandPaths([testDir], false)

    // Should get top-level files only (not subdirectory)
    expect(files).toHaveLength(3) // file1.md, file2.ts, file3.txt
    expect(files.some((f) => f.includes('file1.md'))).toBe(true)
    expect(files.some((f) => f.includes('file4.md'))).toBe(false) // in subdir
  })

  test('expands directory with recursion', () => {
    setupTestDir()
    const files = expandPaths([testDir], true)

    // Should get all files including subdirectory
    expect(files).toHaveLength(5) // file1-5 (excluding .pdf and node_modules)
    expect(files.some((f) => f.includes('file4.md'))).toBe(true)
    expect(files.some((f) => f.includes('file5.js'))).toBe(true)
  })

  test('ignores node_modules even with recursion', () => {
    setupTestDir()
    const files = expandPaths([testDir], true)

    expect(files.some((f) => f.includes('node_modules'))).toBe(false)
  })

  test('filters by supported file extensions', () => {
    setupTestDir()
    const files = expandPaths([testDir], true)

    // Should have .md, .ts, .txt, .js
    expect(files.every((f) => /\.(md|ts|txt|js)$/.test(f))).toBe(true)

    // Should not have .pdf
    expect(files.some((f) => f.endsWith('.pdf'))).toBe(false)
  })

  test('handles multiple paths', () => {
    setupTestDir()
    const file1 = join(testDir, 'file1.md')
    const file2 = join(testDir, 'file2.ts')
    const files = expandPaths([file1, file2], false)

    expect(files).toHaveLength(2)
    expect(files).toContain(file1)
    expect(files).toContain(file2)
  })

  test('handles mixed files and directories', () => {
    setupTestDir()
    const file = join(testDir, 'file1.md')
    const dir = join(testDir, 'subdir')
    const files = expandPaths([file, dir], false)

    // Should have file1.md + files from subdir
    expect(files).toHaveLength(3) // file1.md, file4.md, file5.js
    expect(files).toContain(file)
  })

  // Cleanup happens in global afterEach
})
