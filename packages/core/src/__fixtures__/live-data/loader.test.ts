/**
 * Tests for live data fixture loader
 */

import { describe, it, expect } from 'vitest'
import { liveFixtures } from './loader'

describe('liveFixtures', () => {
  describe('qdrant', () => {
    it('should load Qdrant points', () => {
      expect(liveFixtures.qdrant.points).toHaveLength(10)
      expect(liveFixtures.qdrant.points[0]).toHaveProperty('id')
      expect(liveFixtures.qdrant.points[0]).toHaveProperty('payload')
    })

    it('should have realistic payload structure', () => {
      const firstPoint = liveFixtures.qdrant.points[0]
      expect(firstPoint).toBeDefined()
      const { payload } = firstPoint!

      // Check required fields from live data
      expect(payload).toHaveProperty('original_text')
      expect(payload).toHaveProperty('file_path')
      expect(payload).toHaveProperty('file_name')
      expect(payload).toHaveProperty('file_type')
      expect(payload).toHaveProperty('chunk_index')
      expect(payload).toHaveProperty('total_chunks')
      expect(payload).toHaveProperty('char_count')
      expect(payload).toHaveProperty('qntm_keys')
      expect(payload).toHaveProperty('created_at')
      expect(payload).toHaveProperty('importance')
      expect(payload).toHaveProperty('consolidation_level')
      expect(payload).toHaveProperty('embedding_model')
      expect(payload).toHaveProperty('embedding_strategy')
      expect(payload).toHaveProperty('content_type')
      expect(payload).toHaveProperty('vectors_present')
    })

    it('should have QNTM keys without @ prefix', () => {
      const firstPoint = liveFixtures.qdrant.points[0]
      expect(firstPoint).toBeDefined()
      const qntmKeys = firstPoint!.payload.qntm_keys as string[]

      expect(Array.isArray(qntmKeys)).toBe(true)
      expect(qntmKeys.length).toBeGreaterThan(0)

      // Verify no @ prefix (live data uses "key ~ value" format)
      qntmKeys.forEach((key: string) => {
        expect(key).not.toMatch(/^@/)
      })
    })

    it('should find point by ID', () => {
      const firstPoint = liveFixtures.qdrant.points[0]
      expect(firstPoint).toBeDefined()
      const firstId = firstPoint!.id
      const found = liveFixtures.qdrant.getPoint(firstId)

      expect(found).toBeDefined()
      expect(found?.id).toBe(firstId)
    })

    it('should filter points by file path', () => {
      const firstPoint = liveFixtures.qdrant.points[0]
      expect(firstPoint).toBeDefined()
      const filePath = firstPoint!.payload.file_path as string

      const filtered = liveFixtures.qdrant.getPointsByFile(filePath)

      expect(filtered.length).toBeGreaterThan(0)
      filtered.forEach(point => {
        expect(point.payload.file_path).toBe(filePath)
      })
    })

    it('should have consolidation metadata where present', () => {
      const pointsWithConsolidation = liveFixtures.qdrant.points.filter(
        p => p.payload.consolidation_type
      )

      if (pointsWithConsolidation.length > 0) {
        const consolidated = pointsWithConsolidation[0]
        expect(consolidated).toBeDefined()
        expect(consolidated!.payload).toHaveProperty('consolidation_type')
        expect(consolidated!.payload).toHaveProperty('consolidation_direction')
        expect(consolidated!.payload).toHaveProperty('consolidation_reasoning')
        expect(consolidated!.payload).toHaveProperty('parents')
        expect(Array.isArray(consolidated!.payload.parents)).toBe(true)
      }
    })
  })

  describe('postgres', () => {
    it('should load PostgreSQL sources', () => {
      expect(liveFixtures.postgres.sources).toHaveLength(10)
      expect(liveFixtures.postgres.sources[0]).toHaveProperty('id')
      expect(liveFixtures.postgres.sources[0]).toHaveProperty('path')
      expect(liveFixtures.postgres.sources[0]).toHaveProperty('content_hash')
      expect(liveFixtures.postgres.sources[0]).toHaveProperty('status')
    })

    it('should load PostgreSQL chunks', () => {
      expect(liveFixtures.postgres.chunks).toHaveLength(10)
      expect(liveFixtures.postgres.chunks[0]).toHaveProperty('id')
      expect(liveFixtures.postgres.chunks[0]).toHaveProperty('source_id')
      expect(liveFixtures.postgres.chunks[0]).toHaveProperty('chunk_index')
      expect(liveFixtures.postgres.chunks[0]).toHaveProperty('payload')
    })

    it('should find source by ID', () => {
      const firstSource = liveFixtures.postgres.sources[0]
      expect(firstSource).toBeDefined()
      const firstId = firstSource!.id
      const found = liveFixtures.postgres.getSource(firstId)

      expect(found).toBeDefined()
      expect(found?.id).toBe(firstId)
    })

    it('should filter chunks by source ID', () => {
      const firstChunk = liveFixtures.postgres.chunks[0]
      expect(firstChunk).toBeDefined()
      const sourceId = firstChunk!.source_id

      const filtered = liveFixtures.postgres.getChunksBySource(sourceId)

      expect(filtered.length).toBeGreaterThan(0)
      filtered.forEach(chunk => {
        expect(chunk.source_id).toBe(sourceId)
      })
    })

    it('should have matching chunk payloads with Qdrant', () => {
      // Verify that PostgreSQL chunk payload structure matches Qdrant
      const pgChunk = liveFixtures.postgres.chunks[0]
      expect(pgChunk).toBeDefined()
      const pgPayload = pgChunk!.payload

      // Should have same fields as Qdrant payload
      expect(pgPayload).toHaveProperty('original_text')
      expect(pgPayload).toHaveProperty('file_path')
      expect(pgPayload).toHaveProperty('qntm_keys')
      expect(pgPayload).toHaveProperty('consolidation_level')
    })
  })
})
