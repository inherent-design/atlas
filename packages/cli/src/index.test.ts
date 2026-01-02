/**
 * CLI Smoke Tests
 *
 * Tests CLI command parsing and help output.
 * Does not test actual backend operations (those are tested in core).
 */

import { describe, it, expect, beforeAll } from 'vitest'
import { execSync, spawnSync } from 'child_process'
import { resolve } from 'path'

const CLI_PATH = resolve(__dirname, 'index.ts')
const ROOT_DIR = resolve(__dirname, '../../..')

// Helper to run CLI command and capture output
function runCLI(args: string[], options?: { cwd?: string }): { stdout: string; stderr: string; status: number | null } {
  const result = spawnSync('bun', ['run', CLI_PATH, ...args], {
    cwd: options?.cwd || ROOT_DIR,
    encoding: 'utf-8',
    timeout: 10000,
  })

  return {
    stdout: result.stdout || '',
    stderr: result.stderr || '',
    status: result.status,
  }
}

describe('CLI', () => {
  describe('help', () => {
    it('displays help with --help flag', () => {
      const result = runCLI(['--help'])

      expect(result.status).toBe(0)
      expect(result.stdout).toContain('atlas')
      expect(result.stdout).toContain('Persistent Context Management')
    })

    it('displays version with --version flag', () => {
      const result = runCLI(['--version'])

      expect(result.status).toBe(0)
      expect(result.stdout).toMatch(/\d+\.\d+\.\d+/)
    })
  })

  describe('ingest command', () => {
    it('shows help for ingest command', () => {
      const result = runCLI(['ingest', '--help'])

      expect(result.status).toBe(0)
      expect(result.stdout).toContain('Ingest files/directories')
      expect(result.stdout).toContain('--recursive')
      expect(result.stdout).toContain('--embedding')
      expect(result.stdout).toContain('--llm')
    })

    it('requires at least one path argument', () => {
      const result = runCLI(['ingest'])

      expect(result.status).not.toBe(0)
      expect(result.stderr).toContain("missing required argument 'paths'")
    })
  })

  describe('search command', () => {
    it('shows help for search command', () => {
      const result = runCLI(['search', '--help'])

      expect(result.status).toBe(0)
      expect(result.stdout).toContain('Semantic search')
      expect(result.stdout).toContain('--limit')
      expect(result.stdout).toContain('--since')
      expect(result.stdout).toContain('--rerank')
    })

    it('requires query argument', () => {
      const result = runCLI(['search'])

      expect(result.status).not.toBe(0)
      expect(result.stderr).toContain("missing required argument 'query'")
    })
  })

  describe('timeline command', () => {
    it('shows help for timeline command', () => {
      const result = runCLI(['timeline', '--help'])

      expect(result.status).toBe(0)
      expect(result.stdout).toContain('chronological timeline')
      expect(result.stdout).toContain('--since')
      expect(result.stdout).toContain('--limit')
    })

    it('requires --since option', () => {
      const result = runCLI(['timeline'])

      expect(result.status).not.toBe(0)
      expect(result.stderr).toContain("required option '--since <date>'")
    })
  })

  describe('consolidate command', () => {
    it('shows help for consolidate command', () => {
      const result = runCLI(['consolidate', '--help'])

      expect(result.status).toBe(0)
      expect(result.stdout).toContain('consolidate similar chunks')
      expect(result.stdout).toContain('--dry-run')
      expect(result.stdout).toContain('--threshold')
    })
  })

  describe('qdrant subcommands', () => {
    it('shows help for qdrant command', () => {
      const result = runCLI(['qdrant', '--help'])

      expect(result.status).toBe(0)
      expect(result.stdout).toContain('Qdrant database management')
      expect(result.stdout).toContain('drop')
      expect(result.stdout).toContain('hnsw')
      expect(result.stdout).toContain('vacuum')
    })

    it('qdrant drop requires --yes flag', () => {
      const result = runCLI(['qdrant', 'drop'])

      // Should exit non-zero without --yes flag
      expect(result.status).not.toBe(0)
    })

    it('qdrant hnsw requires state argument', () => {
      const result = runCLI(['qdrant', 'hnsw'])

      expect(result.status).not.toBe(0)
      expect(result.stderr).toContain("missing required argument 'state'")
    })
  })

  describe('global options', () => {
    it('accepts --qdrant-url option', () => {
      const result = runCLI(['--qdrant-url', 'http://custom:6333', '--help'])

      expect(result.status).toBe(0)
      expect(result.stdout).toContain('--qdrant-url')
    })

    it('accepts --log-level option', () => {
      const result = runCLI(['--log-level', 'debug', '--help'])

      expect(result.status).toBe(0)
      expect(result.stdout).toContain('--log-level')
    })

    it('accepts --jobs option', () => {
      const result = runCLI(['--jobs', '4', '--help'])

      expect(result.status).toBe(0)
      expect(result.stdout).toContain('--jobs')
    })
  })
})
