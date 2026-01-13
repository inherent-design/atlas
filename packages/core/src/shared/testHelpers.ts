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
import type { ChunkPayload } from './types.js'

// ============================================
// Platform Simulation
// ============================================

/**
 * Platform simulator for cross-platform system tests.
 * Mocks process.platform for deterministic testing.
 *
 * NOTE: This does NOT spy on child_process.spawnSync anymore due to ESM limitations.
 * Tests that need to mock spawnSync should use vi.mock('child_process') at the test file level.
 *
 * Usage:
 * ```typescript
 * const platform = new PlatformSimulator()
 * platform.simulateMacOS() // only sets process.platform
 * // ... run tests ...
 * platform.restore()
 * ```
 */
export class PlatformSimulator {
  private originalPlatform: NodeJS.Platform
  private restored = false

  constructor() {
    this.originalPlatform = process.platform
  }

  /**
   * Simulate macOS environment (only sets process.platform)
   */
  simulateMacOS(
    _memoryFreePercent?: number,
    _options?: {
      loadAvg?: [number, number, number]
      cpuCount?: number
      swapIns?: number
      swapOuts?: number
    }
  ): void {
    Object.defineProperty(process, 'platform', {
      value: 'darwin',
      configurable: true,
    })
  }

  /**
   * Simulate Linux environment (only sets process.platform)
   */
  simulateLinux(
    _memUsedPercent?: number,
    _options?: {
      loadAvg?: [number, number, number]
      cpuCount?: number
      swapUsedPercent?: number
    }
  ): void {
    Object.defineProperty(process, 'platform', {
      value: 'linux',
      configurable: true,
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
  }

  /**
   * Restore original platform
   */
  restore(): void {
    if (this.restored) return
    this.restored = true

    Object.defineProperty(process, 'platform', {
      value: this.originalPlatform,
      configurable: true,
    })
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
