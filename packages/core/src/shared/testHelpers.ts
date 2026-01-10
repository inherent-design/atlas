/**
 * Shared test utilities and mocks for Atlas tests
 *
 * Includes:
 * - PlatformSimulator: Mock macOS/Linux system commands for cross-platform testing
 * - TimeController: Deterministic time control for cache/TTL testing
 * - Fixture factories: ChunkPayload, ConsolidateCandidate, etc.
 * - Legacy mocks: createTestMocks, setupIngestMocks, etc.
 */

import { mkdirSync, rmSync } from 'fs'
import type { ChunkPayload } from './types'

// ============================================
// Platform Simulation (validated via experiments)
// ============================================

/**
 * Platform simulator for cross-platform system tests.
 * Mocks Bun.spawnSync and process.platform for deterministic testing.
 *
 * Usage:
 * ```typescript
 * const platform = new PlatformSimulator()
 * platform.simulateMacOS(45) // 45% free memory
 * // ... run tests ...
 * platform.restore()
 * ```
 */
export class PlatformSimulator {
  private originalPlatform: NodeJS.Platform
  private spawnSpy: ReturnType<typeof vi.spyOn> | null = null
  private restored = false

  constructor() {
    this.originalPlatform = process.platform
  }

  /**
   * Simulate macOS environment with configurable memory pressure
   */
  simulateMacOS(
    memoryFreePercent: number,
    options?: {
      loadAvg?: [number, number, number]
      cpuCount?: number
      swapIns?: number
      swapOuts?: number
    }
  ): void {
    const loadAvg = options?.loadAvg ?? [2.5, 2.0, 1.8]
    const cpuCount = options?.cpuCount ?? 8
    const swapIns = options?.swapIns ?? 0
    const swapOuts = options?.swapOuts ?? 0

    Object.defineProperty(process, 'platform', {
      value: 'darwin',
      configurable: true,
    })

    this.spawnSpy = vi.spyOn(Bun, 'spawnSync')
    this.spawnSpy.mockImplementation((cmd: string[]) => {
      const cmdStr = cmd.join(' ')

      if (cmdStr.includes('hw.memsize')) {
        return { success: true, stdout: Buffer.from('17179869184'), stderr: Buffer.from('') }
      }
      if (cmdStr.includes('memory_pressure')) {
        return {
          success: true,
          stdout: Buffer.from(
            `System-wide memory free percentage: ${memoryFreePercent}%\n` +
              `Swapins: ${swapIns}\nSwapouts: ${swapOuts}`
          ),
          stderr: Buffer.from(''),
        }
      }
      if (cmdStr.includes('vm.loadavg')) {
        return {
          success: true,
          stdout: Buffer.from(`{ ${loadAvg[0]} ${loadAvg[1]} ${loadAvg[2]} }`),
          stderr: Buffer.from(''),
        }
      }
      if (cmdStr.includes('hw.ncpu')) {
        return { success: true, stdout: Buffer.from(String(cpuCount)), stderr: Buffer.from('') }
      }

      // Default: command not found
      return { success: false, stdout: Buffer.from(''), stderr: Buffer.from('command not found') }
    })
  }

  /**
   * Simulate Linux environment with configurable memory usage
   */
  simulateLinux(
    memUsedPercent: number,
    options?: {
      loadAvg?: [number, number, number]
      cpuCount?: number
      swapUsedPercent?: number
    }
  ): void {
    const loadAvg = options?.loadAvg ?? [2.5, 2.0, 1.8]
    const cpuCount = options?.cpuCount ?? 8
    const swapUsedPercent = options?.swapUsedPercent ?? 5

    const totalMem = 16000000 // kB
    const availMem = Math.floor((totalMem * (100 - memUsedPercent)) / 100)
    const swapTotal = 4000000 // kB
    const swapFree = Math.floor((swapTotal * (100 - swapUsedPercent)) / 100)

    Object.defineProperty(process, 'platform', {
      value: 'linux',
      configurable: true,
    })

    this.spawnSpy = vi.spyOn(Bun, 'spawnSync')
    this.spawnSpy.mockImplementation((cmd: string[]) => {
      const cmdStr = cmd.join(' ')

      if (cmdStr.includes('/proc/meminfo')) {
        return {
          success: true,
          stdout: Buffer.from(
            `MemTotal:       ${totalMem} kB\n` +
              `MemAvailable:   ${availMem} kB\n` +
              `SwapTotal:      ${swapTotal} kB\n` +
              `SwapFree:       ${swapFree} kB`
          ),
          stderr: Buffer.from(''),
        }
      }
      if (cmdStr.includes('/proc/loadavg')) {
        return {
          success: true,
          stdout: Buffer.from(`${loadAvg[0]} ${loadAvg[1]} ${loadAvg[2]} 1/100 12345`),
          stderr: Buffer.from(''),
        }
      }
      if (cmdStr.includes('nproc')) {
        return { success: true, stdout: Buffer.from(String(cpuCount)), stderr: Buffer.from('') }
      }

      return { success: false, stdout: Buffer.from(''), stderr: Buffer.from('command not found') }
    })
  }

  /**
   * Simulate unsupported platform (Windows or unknown)
   */
  simulateUnsupportedPlatform(platform: string = 'win32'): void {
    Object.defineProperty(process, 'platform', {
      value: platform,
      configurable: true,
    })

    this.spawnSpy = vi.spyOn(Bun, 'spawnSync')
    this.spawnSpy.mockImplementation(() => ({
      success: false,
      stdout: Buffer.from(''),
      stderr: Buffer.from('not supported'),
    }))
  }

  /**
   * Simulate command failures for error path testing
   */
  simulateCommandFailure(): void {
    this.spawnSpy = vi.spyOn(Bun, 'spawnSync')
    this.spawnSpy.mockImplementation(() => ({
      success: false,
      stdout: Buffer.from(''),
      stderr: Buffer.from('command failed'),
    }))
  }

  /**
   * Restore original platform and mocks
   */
  restore(): void {
    if (this.restored) return
    this.restored = true

    Object.defineProperty(process, 'platform', {
      value: this.originalPlatform,
      configurable: true,
    })

    if (this.spawnSpy) {
      this.spawnSpy.mockRestore()
      this.spawnSpy = null
    }
  }
}

// ============================================
// Time Control
// ============================================

/**
 * Deterministic time controller for cache/TTL testing.
 * Overrides Date.now() to allow manual time advancement.
 *
 * Usage:
 * ```typescript
 * const time = new TimeController()
 * time.install()
 * // Date.now() returns controlled time
 * time.advance(1001) // Advance 1001ms
 * time.restore()
 * ```
 */
export class TimeController {
  private _now: number
  private originalDateNow: typeof Date.now
  private installed = false

  constructor(startTime: number = Date.now()) {
    this._now = startTime
    this.originalDateNow = Date.now
  }

  install(): void {
    if (this.installed) return
    this.installed = true
    Date.now = () => this._now
  }

  advance(ms: number): void {
    this._now += ms
  }

  setTime(timestamp: number): void {
    this._now = timestamp
  }

  getTime(): number {
    return this._now
  }

  restore(): void {
    if (!this.installed) return
    this.installed = false
    Date.now = this.originalDateNow
  }
}

// ============================================
// Fixture Factories
// ============================================

/**
 * Create a mock ChunkPayload for testing
 */
export function createMockChunkPayload(overrides?: Partial<ChunkPayload>): ChunkPayload {
  return {
    original_text: 'Test chunk content for testing purposes.',
    file_path: '/test/docs/test-file.md',
    file_name: 'test-file.md',
    file_type: '.md',
    chunk_index: 0,
    total_chunks: 1,
    char_count: 42,
    qntm_keys: ['@test ~ content'],
    created_at: '2025-12-30T00:00:00Z',
    importance: 'normal',
    consolidation_level: 0,
    ...overrides,
  }
}

/**
 * Create a mock Qdrant point for testing
 */
export function createMockQdrantPoint(overrides?: {
  id?: string
  vector?: number[] | { text?: number[]; code?: number[] }
  payload?: Partial<ChunkPayload>
}) {
  const defaultVector = new Array(16).fill(0.1)

  // Support both flat vectors (legacy) and named vectors (current)
  const vector = overrides?.vector
    ? Array.isArray(overrides.vector)
      ? { text: overrides.vector } // Convert flat to named
      : overrides.vector // Already named
    : { text: defaultVector } // Default named vector

  return {
    id: overrides?.id ?? `point-${Math.random().toString(36).slice(2, 8)}`,
    vector,
    payload: createMockChunkPayload(overrides?.payload),
  }
}

/**
 * Create a mock consolidation candidate
 */
export function createMockConsolidateCandidate(overrides?: {
  id?: string
  pairId?: string
  similarity?: number
  text?: string
  qntmKeys?: string[]
}) {
  return {
    id: overrides?.id ?? `chunk-${Math.random().toString(36).slice(2, 8)}`,
    pair_id: overrides?.pairId ?? `chunk-${Math.random().toString(36).slice(2, 8)}`,
    similarity: overrides?.similarity ?? 0.95,
    text_preview: (overrides?.text ?? 'Test chunk content...').slice(0, 50),
    qntm_keys: overrides?.qntmKeys ?? ['@test ~ content'],
    file_path: '/test/docs/test.md',
    created_at: '2025-12-30T00:00:00Z',
  }
}

/**
 * Create mock Qdrant client for service mocking
 */
export function createMockQdrantClient() {
  return {
    getCollection: vi.fn(() => Promise.resolve({ status: 'green' })) as any,
    createCollection: vi.fn(() => Promise.resolve()) as any,
    upsert: vi.fn(() => Promise.resolve({ status: 'acknowledged' })) as any,
    search: vi.fn(() => Promise.resolve([])) as any,
    scroll: vi.fn(() => Promise.resolve({ points: [], nextOffset: null })) as any,
    retrieve: vi.fn(() => Promise.resolve([])) as any,
    setPayload: vi.fn(() => Promise.resolve()) as any,
    createPayloadIndex: vi.fn(() => Promise.resolve()) as any,
  }
}

/**
 * Create mock LLM service for testing
 */
export function createMockLLMService() {
  const mockCompleteJSON = vi.fn(() =>
    Promise.resolve({
      type: 'duplicate_work',
      direction: 'unknown',
      reasoning: 'Test classification',
      keep: 'first',
    })
  ) as any

  return {
    completeJSON: mockCompleteJSON,
    getLLMConfig: vi.fn(() => ({
      provider: 'ollama' as const,
      model: 'test-model',
      temperature: 0.1,
    })) as any,
    complete: vi.fn(() => Promise.resolve({ content: '{}', usage: {} })) as any,
    getLLMBackendFor: vi.fn(() => ({
      name: 'test-backend',
      capabilities: new Set(['json-completion']),
      supports: (cap: string) => cap === 'json-completion',
      completeJSON: mockCompleteJSON,
    })),
  }
}

// ============================================
// Legacy Mocks (preserved for compatibility)
// ============================================

/**
 * Create mock functions for testing
 */
export function createTestMocks() {
  return {
    mockVoyageEmbed: vi.fn((input: any) => {
      // Return one embedding per chunk
      const chunks = Array.isArray(input.input) ? input.input : [input.input]
      return Promise.resolve({
        data: chunks.map(() => ({
          embedding: new Array(1024).fill(0.1), // Mock 1024-dim embedding
        })),
      })
    }),
    mockQdrantGet: vi.fn(() => Promise.reject(new Error('Collection not found'))),
    mockQdrantCreate: vi.fn(() => Promise.resolve()),
    mockQdrantUpsert: vi.fn(() => Promise.resolve({ status: 'acknowledged' })),
    mockQdrantSearch: vi.fn(() => Promise.resolve([])),
    mockQdrantScroll: vi.fn(() => Promise.resolve({ points: [] })),
    mockGenerateQNTMKeys: vi.fn(() =>
      Promise.resolve({
        keys: ['@test ~ content', '@mock ~ data'],
        reasoning: 'Test content semantic keys',
      })
    ),
  }
}

/**
 * Setup mock modules for ingestion tests
 * NOTE: Legacy function - references modules that may not exist.
 * Kept for backward compatibility but not used in current tests.
 */
export async function setupIngestMocks(mocks: ReturnType<typeof createTestMocks>) {
  const {
    mockVoyageEmbed,
    mockQdrantGet,
    mockQdrantCreate,
    mockQdrantUpsert,
    mockGenerateQNTMKeys,
  } = mocks

  // Note: This function references './clients' and './qntm' which may not exist
  // If you need this function, ensure those modules exist first
  console.warn('setupIngestMocks: This is a legacy function that may reference missing modules')
}

/**
 * Setup mock modules for search tests
 * NOTE: Legacy function - references modules that may not exist.
 * Kept for backward compatibility but not used in current tests.
 */
export function setupSearchMocks(mocks: ReturnType<typeof createTestMocks>) {
  const { mockVoyageEmbed, mockQdrantSearch, mockQdrantScroll } = mocks

  // Note: This function references './clients' which may not exist
  // If you need this function, ensure that module exists first
  console.warn('setupSearchMocks: This is a legacy function that may reference missing modules')
}

/**
 * Test directory helpers
 */
export function setupTestDir(dirPath: string) {
  rmSync(dirPath, { recursive: true, force: true })
  mkdirSync(dirPath, { recursive: true })
}

export function cleanupTestDir(dirPath: string) {
  rmSync(dirPath, { recursive: true, force: true })
}

/**
 * Reset all mocks in the collection
 */
export function resetMocks(mocks: ReturnType<typeof createTestMocks>) {
  Object.values(mocks).forEach((mockFn) => {
    if (mockFn && typeof mockFn.mockClear === 'function') {
      mockFn.mockClear()
    }
  })
}

/**
 * Default mock payloads for testing
 */
export const mockSearchPayloads = {
  memoryChunk: {
    id: 'chunk1',
    score: 0.95,
    payload: {
      original_text: 'This is about memory consolidation patterns in neural networks.',
      file_path: 'docs/memory.md',
      chunk_index: 0,
      created_at: '2025-12-25T10:00:00Z',
      qntm_keys: ['@memory ~ consolidation', '@neural ~ patterns'],
    },
  },
  sleepChunk: {
    id: 'chunk2',
    score: 0.87,
    payload: {
      original_text: 'Sleep patterns enable episodic to semantic transformation.',
      file_path: 'docs/sleep.md',
      chunk_index: 1,
      created_at: '2025-12-26T11:00:00Z',
      qntm_keys: ['@sleep ~ patterns', '@episodic ~ semantic'],
    },
  },
}
