/**
 * Router tests - Verify field forwarding from RPC to ApplicationService
 *
 * Tests that router forwards ALL fields from DTOs to ApplicationService (no information loss)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { EventRouter } from '../router'
import type {
  IngestParams,
  SearchParams,
  ConsolidateParams,
  QNTMGenerateParams,
  TimelineParams,
} from '../protocol'

// Mock ApplicationService
const mockIngest = vi.fn()
const mockSearch = vi.fn()
const mockConsolidate = vi.fn()
const mockGenerateQNTM = vi.fn()
const mockTimeline = vi.fn()

vi.mock('../../services/application', () => ({
  DefaultApplicationService: class MockApplicationService {
    async initialize() {}
    ingest = mockIngest
    search = mockSearch
    consolidate = mockConsolidate
    generateQNTM = mockGenerateQNTM
    timeline = mockTimeline
  },
}))

describe('EventRouter Field Forwarding', () => {
  let router: EventRouter

  beforeEach(() => {
    router = new EventRouter()
    vi.clearAllMocks()
  })

  describe('handleIngest', () => {
    it('forwards ALL IngestParams fields to ApplicationService', async () => {
      const params: IngestParams = {
        paths: ['/test/path'],
        recursive: true,
        rootDir: '/root',
        verbose: true,
        existingKeys: ['key1', 'key2'],
        useHNSWToggle: false,
        watch: true,
        allowConsolidation: false,
        consolidationThreshold: 200,
      }

      mockIngest.mockResolvedValue({
        filesProcessed: 1,
        chunksStored: 10,
        errors: [],
        durationMs: 1000,
        peakMemoryBytes: 1024,
        skippedFiles: 0,
      })

      const request = {
        jsonrpc: '2.0' as const,
        id: 1,
        method: 'atlas.ingest',
        params,
      }

      await router.handleRequest(request, 'test-client')

      // Verify all fields were forwarded
      expect(mockIngest).toHaveBeenCalledWith(
        expect.objectContaining({
          paths: ['/test/path'],
          recursive: true,
          rootDir: '/root',
          verbose: true,
          existingKeys: ['key1', 'key2'],
          useHNSWToggle: false,
          watch: true,
          allowConsolidation: false,
          consolidationThreshold: 200,
          emit: expect.any(Function),
        })
      )
    })

    it('forwards watch field specifically (regression test)', async () => {
      const params: IngestParams = {
        paths: ['/watch/test'],
        watch: true,
      }

      mockIngest.mockResolvedValue({
        filesProcessed: 0,
        chunksStored: 0,
        errors: [],
      })

      const request = {
        jsonrpc: '2.0' as const,
        id: 2,
        method: 'atlas.ingest',
        params,
      }

      await router.handleRequest(request, 'test-client')

      expect(mockIngest).toHaveBeenCalledWith(
        expect.objectContaining({
          watch: true,
        })
      )
    })

    it('returns all IngestResult fields including metrics', async () => {
      const params: IngestParams = { paths: ['/test'] }

      mockIngest.mockResolvedValue({
        filesProcessed: 5,
        chunksStored: 25,
        errors: [{ file: '/test/fail.txt', error: 'Read error' }],
        durationMs: 2500,
        peakMemoryBytes: 2048,
        skippedFiles: 1,
      })

      const request = {
        jsonrpc: '2.0' as const,
        id: 3,
        method: 'atlas.ingest',
        params,
      }

      const response = await router.handleRequest(request, 'test-client')

      expect(response.result).toEqual({
        filesProcessed: 5,
        chunksStored: 25,
        errors: [{ file: '/test/fail.txt', error: 'Read error' }],
        durationMs: 2500,
        peakMemoryBytes: 2048,
        skippedFiles: 1,
      })
    })
  })

  describe('handleSearch', () => {
    it('forwards ALL SearchParams fields to ApplicationService', async () => {
      const params: SearchParams = {
        query: 'test query',
        limit: 20,
        since: '2026-01-01T00:00:00Z',
        qntmKey: 'test-key',
        rerank: true,
        rerankTopK: 60,
        expandQuery: true,
        hybridSearch: true,
        consolidationLevel: 2,
        contentType: 'code',
        agentRole: 'observer',
        temperature: 'hot',
      }

      mockSearch.mockResolvedValue([])

      const request = {
        jsonrpc: '2.0' as const,
        id: 4,
        method: 'atlas.search',
        params,
      }

      await router.handleRequest(request, 'test-client')

      // Verify all fields were forwarded
      expect(mockSearch).toHaveBeenCalledWith(
        expect.objectContaining({
          query: 'test query',
          limit: 20,
          since: '2026-01-01T00:00:00Z',
          qntmKey: 'test-key',
          rerank: true,
          rerankTopK: 60,
          expandQuery: true,
          hybridSearch: true,
          consolidationLevel: 2,
          contentType: 'code',
          agentRole: 'observer',
          temperature: 'hot',
          emit: expect.any(Function),
        })
      )
    })

    it('forwards advanced search features (regression test)', async () => {
      const params: SearchParams = {
        query: 'test',
        rerankTopK: 100,
        expandQuery: true,
        hybridSearch: true,
      }

      mockSearch.mockResolvedValue([])

      const request = {
        jsonrpc: '2.0' as const,
        id: 5,
        method: 'atlas.search',
        params,
      }

      await router.handleRequest(request, 'test-client')

      expect(mockSearch).toHaveBeenCalledWith(
        expect.objectContaining({
          rerankTopK: 100,
          expandQuery: true,
          hybridSearch: true,
        })
      )
    })
  })

  describe('handleConsolidate', () => {
    it('forwards ALL ConsolidateParams fields to ApplicationService', async () => {
      const params: ConsolidateParams = {
        dryRun: true,
        threshold: 0.85,
        batchSize: 75,
        limit: 500,
        qntmKeyFilter: 'test.*',
        consolidationLevel: 1,
        continuous: false,
        pollIntervalMs: 45000,
      }

      mockConsolidate.mockResolvedValue({
        consolidationsPerformed: 10,
        chunksAbsorbed: 20,
        candidatesEvaluated: 50,
      })

      const request = {
        jsonrpc: '2.0' as const,
        id: 6,
        method: 'atlas.consolidate',
        params,
      }

      await router.handleRequest(request, 'test-client')

      // Verify all fields were forwarded
      expect(mockConsolidate).toHaveBeenCalledWith(
        expect.objectContaining({
          dryRun: true,
          threshold: 0.85,
          batchSize: 75,
          limit: 500,
          qntmKeyFilter: 'test.*',
          consolidationLevel: 1,
          continuous: false,
          pollIntervalMs: 45000,
          emit: expect.any(Function),
        })
      )
    })

    it('returns ConsolidateResult with NO fake data', async () => {
      const params: ConsolidateParams = { dryRun: false }

      mockConsolidate.mockResolvedValue({
        consolidationsPerformed: 5,
        chunksAbsorbed: 10,
        candidatesEvaluated: 25,
        typeBreakdown: {
          duplicate_work: 3,
          sequential_iteration: 1,
          contextual_convergence: 1,
        },
        durationMs: 3000,
      })

      const request = {
        jsonrpc: '2.0' as const,
        id: 7,
        method: 'atlas.consolidate',
        params,
      }

      const response = await router.handleRequest(request, 'test-client')

      // Verify result matches canonical schema (no fake rounds/maxLevel)
      expect(response.result).toEqual({
        consolidationsPerformed: 5,
        chunksAbsorbed: 10,
        candidatesEvaluated: 25,
        typeBreakdown: {
          duplicate_work: 3,
          sequential_iteration: 1,
          contextual_convergence: 1,
        },
        durationMs: 3000,
        preview: undefined,
      })

      // Ensure NO fake data
      expect((response.result as any).rounds).toBeUndefined()
      expect((response.result as any).maxLevel).toBeUndefined()
      expect((response.result as any).levelStats).toBeUndefined()
    })
  })

  describe('handleQntmGenerate', () => {
    it('forwards ALL QNTMGenerateParams fields to ApplicationService', async () => {
      const params: QNTMGenerateParams = {
        text: 'Test text for QNTM generation',
        existingKeys: ['key1', 'key2'],
        context: {
          fileName: 'test.ts',
          chunkIndex: 0,
          totalChunks: 5,
        },
        level: 'abstract',
      }

      mockGenerateQNTM.mockResolvedValue({
        keys: ['gen1', 'gen2', 'gen3'],
        reasoning: 'Test reasoning',
      })

      const request = {
        jsonrpc: '2.0' as const,
        id: 8,
        method: 'atlas.qntm.generate',
        params,
      }

      await router.handleRequest(request, 'test-client')

      // Verify all fields were forwarded
      expect(mockGenerateQNTM).toHaveBeenCalledWith(
        expect.objectContaining({
          text: 'Test text for QNTM generation',
          existingKeys: ['key1', 'key2'],
          context: {
            fileName: 'test.ts',
            chunkIndex: 0,
            totalChunks: 5,
          },
          level: 'abstract',
        })
      )
    })
  })

  describe('handleTimeline', () => {
    it('forwards ALL TimelineParams fields to ApplicationService', async () => {
      const params: TimelineParams = {
        since: '2026-01-01T00:00:00Z',
        until: '2026-01-12T00:00:00Z',
        limit: 200,
        timelineId: 'test-timeline',
        includeCausalLinks: true,
        granularity: 'hour',
      }

      mockTimeline.mockResolvedValue([])

      const request = {
        jsonrpc: '2.0' as const,
        id: 9,
        method: 'atlas.timeline',
        params,
      }

      await router.handleRequest(request, 'test-client')

      // Verify all fields were forwarded
      expect(mockTimeline).toHaveBeenCalledWith(
        expect.objectContaining({
          since: '2026-01-01T00:00:00Z',
          until: '2026-01-12T00:00:00Z',
          limit: 200,
          timelineId: 'test-timeline',
          includeCausalLinks: true,
          granularity: 'hour',
        })
      )
    })
  })
})
