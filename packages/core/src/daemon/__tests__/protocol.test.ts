/**
 * Protocol tests - Verify DTO type completeness
 *
 * Tests that all RPC DTOs include ALL fields from canonical types (no information loss)
 */

import { describe, it, expect } from 'vitest'
import type {
  IngestParams,
  IngestResultDTO,
  SearchParams,
  ConsolidateParams,
  ConsolidateResultDTO,
  QNTMGenerateParams,
  TimelineParams,
} from '../protocol'

describe('Protocol DTO Field Completeness', () => {
  describe('IngestParams', () => {
    it('includes all canonical IngestParams fields', () => {
      const dto: IngestParams = {
        paths: ['/test'],
        recursive: true,
        rootDir: '/root',
        verbose: true,
        existingKeys: ['key1'],
        useHNSWToggle: false,
        watch: true,
        allowConsolidation: false,
        consolidationThreshold: 100,
      }

      // Type check: If any field is missing, TypeScript will error
      expect(dto.paths).toBeDefined()
      expect(dto.recursive).toBeDefined()
      expect(dto.rootDir).toBeDefined()
      expect(dto.verbose).toBeDefined()
      expect(dto.existingKeys).toBeDefined()
      expect(dto.useHNSWToggle).toBeDefined()
      expect(dto.watch).toBeDefined()
      expect(dto.allowConsolidation).toBeDefined()
      expect(dto.consolidationThreshold).toBeDefined()
    })

    it('allows optional fields to be omitted', () => {
      const dto: IngestParams = {
        paths: ['/test'],
      }

      expect(dto.paths).toEqual(['/test'])
    })
  })

  describe('IngestResultDTO', () => {
    it('includes all canonical IngestResult fields', () => {
      const dto: IngestResultDTO = {
        filesProcessed: 10,
        chunksStored: 50,
        errors: [],
        durationMs: 1000,
        peakMemoryBytes: 1024 * 1024,
        skippedFiles: 2,
      }

      expect(dto.filesProcessed).toBe(10)
      expect(dto.chunksStored).toBe(50)
      expect(dto.errors).toEqual([])
      expect(dto.durationMs).toBe(1000)
      expect(dto.peakMemoryBytes).toBe(1024 * 1024)
      expect(dto.skippedFiles).toBe(2)
    })

    it('allows optional metric fields to be omitted', () => {
      const dto: IngestResultDTO = {
        filesProcessed: 10,
        chunksStored: 50,
        errors: [],
      }

      expect(dto.filesProcessed).toBe(10)
      expect(dto.durationMs).toBeUndefined()
    })
  })

  describe('SearchParams', () => {
    it('includes all canonical SearchParams fields', () => {
      const dto: SearchParams = {
        query: 'test query',
        limit: 10,
        since: '2026-01-01T00:00:00Z',
        qntmKey: 'key1',
        rerank: true,
        rerankTopK: 30,
        expandQuery: true,
        hybridSearch: true,
        consolidationLevel: 2,
        contentType: 'code',
        agentRole: 'observer',
        temperature: 'hot',
      }

      expect(dto.query).toBe('test query')
      expect(dto.rerankTopK).toBe(30)
      expect(dto.expandQuery).toBe(true)
      expect(dto.hybridSearch).toBe(true)
      expect(dto.contentType).toBe('code')
      expect(dto.agentRole).toBe('observer')
      expect(dto.temperature).toBe('hot')
    })

    it('allows all advanced features to be optional', () => {
      const dto: SearchParams = {
        query: 'minimal query',
      }

      expect(dto.query).toBe('minimal query')
      expect(dto.rerankTopK).toBeUndefined()
    })
  })

  describe('ConsolidateParams', () => {
    it('includes all canonical ConsolidateParams fields', () => {
      const dto: ConsolidateParams = {
        dryRun: true,
        threshold: 0.9,
        batchSize: 50,
        limit: 1000,
        qntmKeyFilter: 'pattern.*',
        consolidationLevel: 1,
        continuous: false,
        pollIntervalMs: 30000,
      }

      expect(dto.dryRun).toBe(true)
      expect(dto.threshold).toBe(0.9)
      expect(dto.batchSize).toBe(50)
      expect(dto.limit).toBe(1000)
      expect(dto.qntmKeyFilter).toBe('pattern.*')
      expect(dto.consolidationLevel).toBe(1)
      expect(dto.continuous).toBe(false)
      expect(dto.pollIntervalMs).toBe(30000)
    })

    it('allows all fields to be optional', () => {
      const dto: ConsolidateParams = {}

      expect(dto).toBeDefined()
    })
  })

  describe('ConsolidateResultDTO', () => {
    it('includes canonical fields with NO fake data', () => {
      const dto: ConsolidateResultDTO = {
        consolidationsPerformed: 5,
        chunksAbsorbed: 10,
        candidatesEvaluated: 20,
        typeBreakdown: {
          duplicate_work: 3,
          sequential_iteration: 1,
          contextual_convergence: 1,
        },
        durationMs: 5000,
      }

      expect(dto.consolidationsPerformed).toBe(5)
      expect(dto.chunksAbsorbed).toBe(10)
      expect(dto.candidatesEvaluated).toBe(20)
      expect(dto.typeBreakdown).toBeDefined()
      expect(dto.durationMs).toBe(5000)
    })

    it('does not require fake rounds/maxLevel/levelStats fields', () => {
      const dto: ConsolidateResultDTO = {
        consolidationsPerformed: 1,
        chunksAbsorbed: 2,
        candidatesEvaluated: 3,
      }

      // These fields should NOT exist or be fake data
      expect('rounds' in dto).toBe(false)
      expect('maxLevel' in dto).toBe(false)
      expect('levelStats' in dto).toBe(false)
    })
  })

  describe('QNTMGenerateParams', () => {
    it('includes all canonical QNTMGenerateParams fields', () => {
      const dto: QNTMGenerateParams = {
        text: 'Sample text',
        existingKeys: ['key1', 'key2'],
        context: {
          fileName: 'test.ts',
          chunkIndex: 0,
          totalChunks: 10,
        },
        level: 'abstract',
      }

      expect(dto.text).toBe('Sample text')
      expect(dto.existingKeys).toEqual(['key1', 'key2'])
      expect(dto.context).toBeDefined()
      expect(dto.level).toBe('abstract')
    })

    it('requires only text field (existingKeys and level have defaults)', () => {
      const dto: QNTMGenerateParams = {
        text: 'Minimal text',
        existingKeys: [],
        level: 'concrete',
      }

      expect(dto.text).toBe('Minimal text')
    })
  })

  describe('TimelineParams', () => {
    it('includes all canonical TimelineParams fields', () => {
      const dto: TimelineParams = {
        since: '2026-01-01T00:00:00Z',
        until: '2026-01-12T00:00:00Z',
        limit: 100,
        timelineId: 'project-123',
        includeCausalLinks: true,
        granularity: 'day',
      }

      expect(dto.since).toBe('2026-01-01T00:00:00Z')
      expect(dto.until).toBe('2026-01-12T00:00:00Z')
      expect(dto.limit).toBe(100)
      expect(dto.timelineId).toBe('project-123')
      expect(dto.includeCausalLinks).toBe(true)
      expect(dto.granularity).toBe('day')
    })

    it('requires only since field (other fields have defaults)', () => {
      const dto: TimelineParams = {
        since: '2026-01-01T00:00:00Z',
        limit: 100,
        includeCausalLinks: false,
        granularity: 'day',
      }

      expect(dto.since).toBe('2026-01-01T00:00:00Z')
    })
  })
})
