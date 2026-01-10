/**
 * Integration tests for daemon RPC enhancement (Phase 4)
 *
 * Tests full RPC flow across all phases:
 * - Phase 1: RPC methods (concurrent ingestion, consolidation lock, QNTM, timeline)
 * - Phase 2: Hook enhancements (tested manually via Claude Code)
 * - Phase 3: Project bootstrap skill (tested manually via Claude Code)
 */

import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import { AtlasConnection } from '../../client'
import { isDaemonRunning } from '../index'
import { writeFileSync, mkdirSync, rmSync } from 'fs'
import { join } from 'path'
import type {
  IngestStartResult,
  IngestStatusResult,
  ConsolidateStartResult,
  ConsolidateStatusResult,
  QntmGenerateResult,
  TimelineResult,
} from '../protocol'

const TEST_DIR = '/tmp/atlas-integration-test'
const TEST_FILES = [
  {
    path: 'doc1.md',
    content: 'Vector databases enable semantic search through high-dimensional embeddings.',
  },
  {
    path: 'doc2.md',
    content: 'QNTM protocol provides semantic quantization for knowledge representation.',
  },
  {
    path: 'nested/doc3.md',
    content: 'Consolidation merges similar chunks to optimize storage and retrieval.',
  },
]

describe('Integration Tests - Phase 4', () => {
  let connection: AtlasConnection

  beforeAll(async () => {
    // Skip all tests if daemon not running
    if (!isDaemonRunning()) {
      console.warn('⚠️  Daemon not running - skipping integration tests')
      console.warn('   Start daemon: cd packages/core && bun run daemon')
      return
    }

    // Create test directory and files
    mkdirSync(TEST_DIR, { recursive: true })
    mkdirSync(join(TEST_DIR, 'nested'), { recursive: true })

    for (const file of TEST_FILES) {
      writeFileSync(join(TEST_DIR, file.path), file.content, 'utf-8')
    }

    // Connect to daemon
    connection = new AtlasConnection()
    await connection.connect()
  })

  afterAll(async () => {
    if (connection) {
      connection.disconnect()
    }

    // Cleanup test directory
    try {
      rmSync(TEST_DIR, { recursive: true, force: true })
    } catch {
      // Ignore cleanup errors
    }
  })

  describe('Concurrent Ingestion Flow', () => {
    test.skipIf(!isDaemonRunning())('should start concurrent ingestion tasks', async () => {
      // Start first ingestion (non-watching)
      const result1 = await connection.request('atlas.ingest.start' as any, {
        paths: [join(TEST_DIR, 'doc1.md')],
        recursive: false,
        watch: false,
      })

      expect(result1).toBeDefined()
      const task1 = result1 as IngestStartResult
      expect(task1.taskId).toBeDefined()
      expect(task1.watching).toBe(false)
      expect(task1.message).toContain('Ingestion started')

      // Start second ingestion (watching)
      const result2 = await connection.request('atlas.ingest.start' as any, {
        paths: [join(TEST_DIR, 'doc2.md')],
        recursive: false,
        watch: true,
      })

      const task2 = result2 as IngestStartResult
      expect(task2.taskId).toBeDefined()
      expect(task2.taskId).not.toBe(task1.taskId) // Different task IDs
      expect(task2.watching).toBe(true)

      // Wait briefly for ingestion to process
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Check status of all tasks
      const statusResult = await connection.request('atlas.ingest.status' as any, {})
      const status = statusResult as IngestStatusResult

      expect(status.tasks).toBeDefined()
      expect(status.tasks.length).toBeGreaterThanOrEqual(2)

      // Find our specific tasks
      const foundTask1 = status.tasks.find((t) => t.id === task1.taskId)
      const foundTask2 = status.tasks.find((t) => t.id === task2.taskId)

      expect(foundTask1).toBeDefined()
      expect(foundTask2).toBeDefined()
      expect(foundTask1?.watching).toBe(false)
      expect(foundTask2?.watching).toBe(true)
    })

    test.skipIf(!isDaemonRunning())('should get status for specific task', async () => {
      // Start ingestion
      const startResult = await connection.request('atlas.ingest.start' as any, {
        paths: [join(TEST_DIR, 'nested/doc3.md')],
        recursive: false,
        watch: false,
      })

      const task = startResult as IngestStartResult

      // Wait for processing
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Get specific task status
      const statusResult = await connection.request('atlas.ingest.status' as any, {
        taskId: task.taskId,
      })

      const status = statusResult as IngestStatusResult
      expect(status.tasks).toHaveLength(1)
      expect(status.tasks[0].id).toBe(task.taskId)
      expect(status.tasks[0].status).toMatch(/running|completed/)
    })

    test.skipIf(!isDaemonRunning())('should stop ingestion task', async () => {
      // Start ingestion
      const startResult = await connection.request('atlas.ingest.start' as any, {
        paths: [join(TEST_DIR, 'doc1.md')],
        recursive: false,
        watch: false,
      })

      const task = startResult as IngestStartResult

      // Stop task immediately (before completion)
      const stopResult = await connection.request('atlas.ingest.stop' as any, {
        taskId: task.taskId,
      })

      expect(stopResult).toBeDefined()
      expect((stopResult as any).stopped).toBe(true)
      expect((stopResult as any).final.status).toBe('stopped')
      expect((stopResult as any).final.completedAt).toBeDefined()
    })
  })

  describe('Consolidation Lock', () => {
    test.skipIf(!isDaemonRunning())('should acquire consolidation lock', async () => {
      const result = await connection.request('atlas.consolidate.start' as any, {
        dryRun: true, // Don't actually consolidate in tests
        threshold: 0.9,
      })

      const started = result as ConsolidateStartResult
      expect(started.locked).toBe(true)
      expect(started.taskId).toBeDefined()
      expect(started.message).toContain('started')

      // Release lock by stopping (since it's async and may still be running)
      try {
        await connection.request('atlas.consolidate.stop' as any, {
          taskId: started.taskId,
        })
      } catch {
        // May have already completed
      }
    })

    test.skipIf(!isDaemonRunning())('should reject concurrent consolidation attempts', async () => {
      // Start first consolidation
      const result1 = await connection.request('atlas.consolidate.start' as any, {
        dryRun: true,
      })

      const task1 = result1 as ConsolidateStartResult
      expect(task1.locked).toBe(true)
      const firstTaskId = task1.taskId

      // Try to start second consolidation (should be rejected)
      const result2 = await connection.request('atlas.consolidate.start' as any, {
        dryRun: true,
      })

      const task2 = result2 as ConsolidateStartResult
      expect(task2.locked).toBe(false)
      expect(task2.taskId).toBe(firstTaskId) // Returns existing task ID
      expect(task2.message).toContain('already running')

      // Cleanup - stop consolidation
      try {
        await connection.request('atlas.consolidate.stop' as any, {
          taskId: firstTaskId,
        })
      } catch {
        // May have already completed
      }
    })

    test.skipIf(!isDaemonRunning())('should check consolidation status', async () => {
      // Check status when no consolidation running
      const status1 = (await connection.request(
        'atlas.consolidate.status' as any,
        {}
      )) as ConsolidateStatusResult

      expect(status1.running).toBe(false)
      expect(status1.taskId).toBeUndefined()

      // Start consolidation
      const startResult = await connection.request('atlas.consolidate.start' as any, {
        dryRun: true,
      })

      const started = startResult as ConsolidateStartResult
      expect(started.locked).toBe(true)

      // Check status while running
      const status2 = (await connection.request(
        'atlas.consolidate.status' as any,
        {}
      )) as ConsolidateStatusResult

      expect(status2.running).toBe(true)
      expect(status2.taskId).toBe(started.taskId)
      expect(status2.startedAt).toBeDefined()

      // Cleanup
      try {
        await connection.request('atlas.consolidate.stop' as any, {
          taskId: started.taskId,
        })
      } catch {
        // May have already completed
      }
    })
  })

  describe('QNTM Generation', () => {
    test.skipIf(!isDaemonRunning())('should generate QNTM keys for sample text', async () => {
      const result = await connection.request('atlas.qntm.generate' as any, {
        text: 'Vector databases enable semantic search through high-dimensional embeddings and similarity metrics.',
        maxKeys: 5,
      })

      const qntm = result as QntmGenerateResult
      expect(qntm.keys).toBeDefined()
      expect(Array.isArray(qntm.keys)).toBe(true)
      expect(qntm.keys.length).toBeGreaterThan(0)
      expect(qntm.keys.length).toBeLessThanOrEqual(5)

      // Keys should follow QNTM format (roughly)
      for (const key of qntm.keys) {
        expect(typeof key).toBe('string')
        expect(key.length).toBeGreaterThan(0)
      }
    })

    test.skipIf(!isDaemonRunning())('should respect maxKeys parameter', async () => {
      const result = await connection.request('atlas.qntm.generate' as any, {
        text: 'Consolidation merges similar knowledge chunks to optimize storage and retrieval performance.',
        maxKeys: 2,
      })

      const qntm = result as QntmGenerateResult
      expect(qntm.keys.length).toBeLessThanOrEqual(2)
    })
  })

  describe('Timeline Queries', () => {
    test.skipIf(!isDaemonRunning())('should query timeline with default params', async () => {
      // Ingest some test data first
      await connection.request('atlas.ingest' as any, {
        paths: [TEST_DIR],
        recursive: true,
      })

      // Wait for ingestion
      await new Promise((resolve) => setTimeout(resolve, 2000))

      // Query timeline
      const result = await connection.request('atlas.timeline' as any, {
        limit: 10,
      })

      const timeline = result as TimelineResult
      expect(timeline.chunks).toBeDefined()
      expect(Array.isArray(timeline.chunks)).toBe(true)
      expect(timeline.total).toBeDefined()
      expect(timeline.total).toBeGreaterThanOrEqual(0)

      // If we have results, check structure
      if (timeline.chunks.length > 0) {
        const chunk = timeline.chunks[0]
        expect(chunk.id).toBeDefined()
        expect(chunk.text).toBeDefined()
        expect(chunk.filePath).toBeDefined()
        expect(chunk.createdAt).toBeDefined()
        expect(Array.isArray(chunk.qntmKeys)).toBe(true)
      }
    })

    test.skipIf(!isDaemonRunning())('should filter timeline by date', async () => {
      const sinceDate = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() // 24h ago

      const result = await connection.request('atlas.timeline' as any, {
        since: sinceDate,
        limit: 5,
      })

      const timeline = result as TimelineResult
      expect(timeline.chunks).toBeDefined()

      // All chunks should be after the filter date
      for (const chunk of timeline.chunks) {
        if (chunk.createdAt) {
          const chunkDate = new Date(chunk.createdAt)
          expect(chunkDate.getTime()).toBeGreaterThanOrEqual(new Date(sinceDate).getTime())
        }
      }
    })

    test.skipIf(!isDaemonRunning())('should sort timeline by date descending', async () => {
      const result = await connection.request('atlas.timeline' as any, {
        limit: 10,
      })

      const timeline = result as TimelineResult

      // If we have multiple chunks, verify they're sorted newest first
      if (timeline.chunks.length > 1) {
        for (let i = 0; i < timeline.chunks.length - 1; i++) {
          const current = new Date(timeline.chunks[i].createdAt).getTime()
          const next = new Date(timeline.chunks[i + 1].createdAt).getTime()
          expect(current).toBeGreaterThanOrEqual(next)
        }
      }
    })
  })

  describe('Full Stack Integration', () => {
    test.skipIf(!isDaemonRunning())(
      'should handle complete workflow: ingest → search → consolidate → timeline',
      async () => {
        // 1. Start ingestion
        const ingestResult = await connection.request('atlas.ingest.start' as any, {
          paths: [TEST_DIR],
          recursive: true,
          watch: false,
        })

        const ingestTask = ingestResult as IngestStartResult
        expect(ingestTask.taskId).toBeDefined()

        // 2. Wait for ingestion to complete
        await new Promise((resolve) => setTimeout(resolve, 2000))

        // 3. Check ingestion status
        const statusResult = await connection.request('atlas.ingest.status' as any, {
          taskId: ingestTask.taskId,
        })

        const status = statusResult as IngestStatusResult
        expect(status.tasks[0].status).toMatch(/completed|running/)

        // 4. Search for content
        const searchResult = await connection.request('atlas.search' as any, {
          query: 'vector database semantic search',
          limit: 5,
        })

        expect(Array.isArray(searchResult)).toBe(true)
        expect((searchResult as any).length).toBeGreaterThan(0)

        // 5. Generate QNTM keys from search result
        if ((searchResult as any).length > 0) {
          const firstResult = (searchResult as any)[0]
          const qntmResult = await connection.request('atlas.qntm.generate' as any, {
            text: firstResult.text,
            maxKeys: 3,
          })

          const qntm = qntmResult as QntmGenerateResult
          expect(qntm.keys.length).toBeGreaterThan(0)
        }

        // 6. Start consolidation (dry run)
        const consolidateResult = await connection.request('atlas.consolidate.start' as any, {
          dryRun: true,
        })

        const consolidateTask = consolidateResult as ConsolidateStartResult
        expect(consolidateTask.locked).toBe(true)

        // 7. Query timeline
        const timelineResult = await connection.request('atlas.timeline' as any, {
          limit: 10,
        })

        const timeline = timelineResult as TimelineResult
        expect(timeline.chunks).toBeDefined()
        expect(timeline.total).toBeGreaterThanOrEqual(0)

        // 8. Cleanup - stop consolidation
        try {
          await connection.request('atlas.consolidate.stop' as any, {
            taskId: consolidateTask.taskId,
          })
        } catch {
          // May have already completed
        }
      }
    )
  })
})
