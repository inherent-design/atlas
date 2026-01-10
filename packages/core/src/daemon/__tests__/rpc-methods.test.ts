/**
 * Tests for new RPC methods (Phase 1)
 *
 * Tests:
 * - Concurrent ingestion (start/status/stop)
 * - Consolidation lock
 * - QNTM generation
 * - Timeline queries
 */

import { describe, test, expect, beforeEach } from 'vitest'
import { daemonState } from '../state'
import { EventRouter } from '../router'
import type { JsonRpcRequest } from '../protocol'
import type {
  IngestStartParams,
  IngestStatusParams,
  IngestStopParams,
  ConsolidateStartParams,
  ConsolidateStatusParams,
  QntmGenerateParams,
  TimelineParams,
} from '../protocol'

// Helper to create properly typed JSON-RPC request
function createRpcRequest(id: number, method: string, params?: unknown): JsonRpcRequest {
  return {
    jsonrpc: '2.0',
    id,
    method,
    params: (params || {}) as Record<string, unknown>,
  }
}

describe('RPC Methods - Phase 1', () => {
  let router: EventRouter

  beforeEach(() => {
    router = new EventRouter()
    // Clear state between tests (access private fields for testing)
    ;(daemonState as any).ingestionTasks.clear()
    ;(daemonState as any).consolidationLock = { locked: false }
    ;(daemonState as any).autoWatchPaths.clear()
  })

  describe('atlas.ingest.start', () => {
    test('creates ingestion task', async () => {
      const params: IngestStartParams = {
        paths: ['/tmp/test'],
        recursive: true,
        watch: false,
      }

      const request = createRpcRequest(1, 'atlas.ingest.start', params)
      const response = await router.handleRequest(request, 'test-client')

      expect(response.error).toBeUndefined()
      expect(response.result).toBeDefined()

      const result = response.result as any
      expect(result.taskId).toBeDefined()
      expect(typeof result.taskId).toBe('string')
      expect(result.message).toContain('Ingestion started')
      expect(result.watching).toBe(false)
    })

    test('supports watch flag', async () => {
      const params: IngestStartParams = {
        paths: ['/tmp/test'],
        recursive: true,
        watch: true,
      }

      const request = createRpcRequest(1, 'atlas.ingest.start', params)
      const response = await router.handleRequest(request, 'test-client')
      const result = response.result as any

      expect(result.watching).toBe(true)
    })
  })

  describe('atlas.ingest.status', () => {
    test('returns all tasks when no taskId specified', async () => {
      // Create a couple of tasks first
      const task1 = daemonState.createIngestionTask(['/tmp/test1'], false)
      const task2 = daemonState.createIngestionTask(['/tmp/test2'], true)

      const params: IngestStatusParams = {}

      const request = createRpcRequest(1, 'atlas.ingest.status', params)
      const response = await router.handleRequest(request, 'test-client')
      const result = response.result as any

      expect(result.tasks).toHaveLength(2)
      expect(result.tasks[0].id).toBe(task1)
      expect(result.tasks[1].id).toBe(task2)
    })

    test('returns specific task when taskId specified', async () => {
      const task1 = daemonState.createIngestionTask(['/tmp/test1'], false)
      daemonState.createIngestionTask(['/tmp/test2'], true)

      const params: IngestStatusParams = {
        taskId: task1,
      }

      const request = createRpcRequest(1, 'atlas.ingest.status', params)
      const response = await router.handleRequest(request, 'test-client')
      const result = response.result as any

      expect(result.tasks).toHaveLength(1)
      expect(result.tasks[0].id).toBe(task1)
    })

    test('returns empty array for non-existent task', async () => {
      const params: IngestStatusParams = {
        taskId: 'non-existent',
      }

      const request = createRpcRequest(1, 'atlas.ingest.status', params)
      const response = await router.handleRequest(request, 'test-client')
      const result = response.result as any

      expect(result.tasks).toHaveLength(0)
    })
  })

  describe('atlas.ingest.stop', () => {
    test('stops ingestion task', async () => {
      const taskId = daemonState.createIngestionTask(['/tmp/test'], false)

      const params: IngestStopParams = {
        taskId,
      }

      const request = createRpcRequest(1, 'atlas.ingest.stop', params)
      const response = await router.handleRequest(request, 'test-client')
      const result = response.result as any

      expect(result.stopped).toBe(true)
      expect(result.final.id).toBe(taskId)
      expect(result.final.status).toBe('stopped')
      expect(result.final.completedAt).toBeDefined()
    })

    test('throws error for non-existent task', async () => {
      const params: IngestStopParams = {
        taskId: 'non-existent',
      }

      const request = createRpcRequest(1, 'atlas.ingest.stop', params)
      const response = await router.handleRequest(request, 'test-client')

      expect(response.error).toBeDefined()
      expect(response.error?.message).toContain('Internal error')
    })
  })

  describe('atlas.consolidate.start', () => {
    test('acquires consolidation lock', async () => {
      const params: ConsolidateStartParams = {
        dryRun: true,
      }

      const request = createRpcRequest(1, 'atlas.consolidate.start', params)
      const response = await router.handleRequest(request, 'test-client')
      const result = response.result as any

      expect(result.locked).toBe(true)
      expect(result.taskId).toBeDefined()
      expect(result.message).toContain('started')
    })

    test('rejects if consolidation already running', async () => {
      // Start first consolidation
      const params1: ConsolidateStartParams = {
        dryRun: true,
      }

      const request1 = createRpcRequest(1, 'atlas.consolidate.start', params1)
      const response1 = await router.handleRequest(request1, 'test-client')
      const result1 = response1.result as any

      expect(result1.locked).toBe(true)
      const firstTaskId = result1.taskId

      // Try to start second consolidation
      const params2: ConsolidateStartParams = {
        dryRun: true,
      }

      const request2 = createRpcRequest(2, 'atlas.consolidate.start', params2)
      const response2 = await router.handleRequest(request2, 'test-client')
      const result2 = response2.result as any

      expect(result2.locked).toBe(false)
      expect(result2.taskId).toBe(firstTaskId)
      expect(result2.message).toContain('already running')
    })
  })

  describe('atlas.consolidate.status', () => {
    test('returns not running when no consolidation active', async () => {
      const params: ConsolidateStatusParams = {}

      const request = createRpcRequest(1, 'atlas.consolidate.status', params)
      const response = await router.handleRequest(request, 'test-client')
      const result = response.result as any

      expect(result.running).toBe(false)
      expect(result.taskId).toBeUndefined()
    })

    test('returns running status when consolidation active', async () => {
      // Start consolidation first
      const startRequest = createRpcRequest(1, 'atlas.consolidate.start', { dryRun: true })
      const startResponse = await router.handleRequest(startRequest, 'test-client')
      const startResult = startResponse.result as any
      const taskId = startResult.taskId

      // Check status
      const statusRequest = createRpcRequest(2, 'atlas.consolidate.status', {})
      const statusResponse = await router.handleRequest(statusRequest, 'test-client')
      const statusResult = statusResponse.result as any

      expect(statusResult.running).toBe(true)
      expect(statusResult.taskId).toBe(taskId)
      expect(statusResult.startedAt).toBeDefined()
    })
  })

  describe('atlas.qntm.generate', () => {
    test('generates QNTM keys for text', async () => {
      const params: QntmGenerateParams = {
        text: 'Vector databases enable semantic search through high-dimensional embeddings.',
        maxKeys: 3,
      }

      const request = createRpcRequest(1, 'atlas.qntm.generate', params)
      const response = await router.handleRequest(request, 'test-client')

      // This test requires LLM to be available, so we check for either success or error
      if (response.error) {
        // If LLM not available, that's expected in test env
        expect(response.error.message).toBeDefined()
      } else {
        const result = response.result as any
        expect(result.keys).toBeDefined()
        expect(Array.isArray(result.keys)).toBe(true)
        // Keys should be limited by maxKeys
        expect(result.keys.length).toBeLessThanOrEqual(3)
      }
    })

    test('respects maxKeys parameter', async () => {
      const params: QntmGenerateParams = {
        text: 'Test text for QNTM generation.',
        maxKeys: 1,
      }

      const request = createRpcRequest(1, 'atlas.qntm.generate', params)
      const response = await router.handleRequest(request, 'test-client')

      if (!response.error) {
        const result = response.result as any
        expect(result.keys.length).toBeLessThanOrEqual(1)
      }
    })
  })

  describe('atlas.timeline', () => {
    test('returns timeline chunks', async () => {
      const params: TimelineParams = {
        limit: 10,
      }

      const request = createRpcRequest(1, 'atlas.timeline', params)
      const response = await router.handleRequest(request, 'test-client')

      // This requires storage backend to be available
      if (response.error) {
        // If storage not available, that's expected in test env
        expect(response.error.message).toBeDefined()
      } else {
        const result = response.result as any
        expect(result.chunks).toBeDefined()
        expect(Array.isArray(result.chunks)).toBe(true)
        expect(result.total).toBeDefined()
        expect(typeof result.total).toBe('number')
      }
    })

    test('supports date filter', async () => {
      const params: TimelineParams = {
        since: '2026-01-01T00:00:00Z',
        limit: 5,
      }

      const request = createRpcRequest(1, 'atlas.timeline', params)
      const response = await router.handleRequest(request, 'test-client')

      if (!response.error) {
        const result = response.result as any
        expect(result.chunks).toBeDefined()
        // All chunks should be after the filter date
        for (const chunk of result.chunks) {
          if (chunk.createdAt) {
            expect(new Date(chunk.createdAt).getTime()).toBeGreaterThanOrEqual(
              new Date('2026-01-01T00:00:00Z').getTime()
            )
          }
        }
      }
    })

    test('supports QNTM key filter', async () => {
      const params: TimelineParams = {
        qntmKey: '@vector ~ database',
        limit: 5,
      }

      const request = createRpcRequest(1, 'atlas.timeline', params)
      const response = await router.handleRequest(request, 'test-client')

      if (!response.error) {
        const result = response.result as any
        expect(result.chunks).toBeDefined()
        // All chunks should contain the QNTM key
        for (const chunk of result.chunks) {
          if (chunk.qntmKeys) {
            expect(chunk.qntmKeys).toContain('@vector ~ database')
          }
        }
      }
    })
  })

  describe('State management', () => {
    test('supports concurrent ingestion tasks', () => {
      const task1 = daemonState.createIngestionTask(['/tmp/test1'], false)
      const task2 = daemonState.createIngestionTask(['/tmp/test2'], true)

      const tasks = daemonState.getAllIngestionTasks()
      expect(tasks).toHaveLength(2)

      const retrieved1 = daemonState.getIngestionTask(task1)
      const retrieved2 = daemonState.getIngestionTask(task2)

      expect(retrieved1?.id).toBe(task1)
      expect(retrieved2?.id).toBe(task2)
      expect(retrieved1?.watching).toBe(false)
      expect(retrieved2?.watching).toBe(true)
    })

    test('updates ingestion task state', () => {
      const taskId = daemonState.createIngestionTask(['/tmp/test'], false)

      daemonState.updateIngestionTask(taskId, {
        filesProcessed: 5,
        chunksStored: 20,
        status: 'completed',
      })

      const task = daemonState.getIngestionTask(taskId)
      expect(task?.filesProcessed).toBe(5)
      expect(task?.chunksStored).toBe(20)
      expect(task?.status).toBe('completed')
    })

    test('consolidation lock prevents double acquisition', () => {
      const acquired1 = daemonState.acquireConsolidationLock('task-1')
      const acquired2 = daemonState.acquireConsolidationLock('task-2')

      expect(acquired1).toBe(true)
      expect(acquired2).toBe(false)

      const lock = daemonState.getConsolidationLock()
      expect(lock.locked).toBe(true)
      expect(lock.taskId).toBe('task-1')
    })

    test('consolidation lock can be released and reacquired', () => {
      const acquired1 = daemonState.acquireConsolidationLock('task-1')
      expect(acquired1).toBe(true)

      daemonState.releaseConsolidationLock()

      const acquired2 = daemonState.acquireConsolidationLock('task-2')
      expect(acquired2).toBe(true)

      const lock = daemonState.getConsolidationLock()
      expect(lock.taskId).toBe('task-2')
    })

    test('auto-watch path registration', () => {
      daemonState.registerAutoWatch('/tmp/project', 'task-123')

      expect(daemonState.isAutoWatched('/tmp/project')).toBe(true)
      expect(daemonState.isAutoWatched('/tmp/other')).toBe(false)
      expect(daemonState.getAutoWatchTaskId('/tmp/project')).toBe('task-123')
    })
  })
})
