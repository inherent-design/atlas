/**
 * ChunkPayload fixtures for testing
 *
 * Provides sample chunk payloads covering common scenarios.
 */

import type { ChunkPayload } from '../shared/types'
import { generateEmbedding } from './embeddings'

/**
 * Create a ChunkPayload with sensible defaults and optional overrides.
 *
 * @param overrides - Partial payload to merge with defaults
 * @returns Complete ChunkPayload
 */
export function createChunkPayload(overrides?: Partial<ChunkPayload>): ChunkPayload {
  const defaults: ChunkPayload = {
    original_text: 'This is a test chunk for Atlas semantic memory testing.',
    file_path: '/test/docs/sample.md',
    file_name: 'sample.md',
    file_type: '.md',
    chunk_index: 0,
    total_chunks: 1,
    char_count: 56,
    qntm_keys: ['@test ~ content', '@sample ~ data'],
    created_at: '2025-12-30T00:00:00Z',
    importance: 'normal',
    consolidation_level: 0,
  }

  return { ...defaults, ...overrides }
}

/**
 * Common chunk fixtures for various test scenarios
 */
export const CHUNKS = {
  /** Basic markdown chunk (level 0 raw) */
  markdown: createChunkPayload({
    original_text: 'Memory consolidation occurs during sleep, transforming episodic memories into semantic knowledge.',
    file_path: '/docs/memory/consolidation.md',
    file_name: 'consolidation.md',
    file_type: '.md',
    qntm_keys: ['@memory ~ consolidation', '@episodic ~ semantic'],
    char_count: 106,
  }),

  /** TypeScript code chunk */
  typescript: createChunkPayload({
    original_text: 'export function embedText(input: string): Promise<number[]> {\n  return voyage.embed(input)\n}',
    file_path: '/src/services/embedding.ts',
    file_name: 'embedding.ts',
    file_type: '.ts',
    qntm_keys: ['@embedding ~ service', '@typescript ~ function'],
    content_type: 'code',
    embedding_model: 'voyage-code-3',
    vectors_present: ['text', 'code'],
    char_count: 92,
  }),

  /** Consolidated chunk (level 1 deduped) */
  consolidated: createChunkPayload({
    original_text: 'Sleep consolidation: Episodic memories are replayed and integrated into semantic networks during sleep.',
    file_path: '/docs/memory/sleep-consolidation.md',
    file_name: 'sleep-consolidation.md',
    file_type: '.md',
    qntm_keys: ['@sleep ~ consolidation', '@memory ~ integration'],
    consolidation_level: 1,
    consolidation_type: 'duplicate_work',
    consolidation_direction: 'forward',
    parents: ['chunk-abc123', 'chunk-def456'],
    occurrences: ['2025-12-28T10:00:00Z', '2025-12-29T15:30:00Z'],
    char_count: 105,
  }),

  /** High importance chunk */
  important: createChunkPayload({
    original_text: 'CRITICAL: Memory corruption detected in consolidation pipeline. Requires immediate investigation.',
    file_path: '/logs/errors/2025-12-30.log',
    file_name: '2025-12-30.log',
    file_type: '.log',
    qntm_keys: ['@error ~ critical', '@memory ~ corruption'],
    importance: 'high',
    char_count: 98,
  }),

  /** Topic summary (level 2) */
  topicSummary: createChunkPayload({
    original_text: 'Memory consolidation research shows that sleep plays a crucial role in transforming short-term episodic memories into long-term semantic knowledge through repeated replay and integration.',
    file_path: '/summaries/memory-consolidation-overview.md',
    file_name: 'memory-consolidation-overview.md',
    file_type: '.md',
    qntm_keys: ['@memory ~ consolidation', '@research ~ summary'],
    consolidation_level: 2,
    consolidation_type: 'contextual_convergence',
    abstraction_score: 0.75,
    parents: ['chunk-consolidated-1', 'chunk-consolidated-2', 'chunk-consolidated-3'],
    char_count: 186,
  }),

  /** Conversation chunk */
  conversation: createChunkPayload({
    original_text: 'User: How does Atlas handle consolidation?\nAssistant: Atlas uses hierarchical consolidation with 4 levels (raw, deduped, topic, domain).',
    file_path: '/conversations/2025-12-30-atlas-qa.md',
    file_name: '2025-12-30-atlas-qa.md',
    file_type: '.md',
    qntm_keys: ['@atlas ~ consolidation', '@conversation ~ qa'],
    memory_type: 'conversation',
    session_id: 'session-20251230-001',
    char_count: 148,
  }),

  /** Old chunk eligible for deletion */
  deletionEligible: createChunkPayload({
    original_text: 'Outdated approach: Use single-vector storage for all content types.',
    file_path: '/docs/legacy/old-architecture.md',
    file_name: 'old-architecture.md',
    file_type: '.md',
    qntm_keys: ['@legacy ~ architecture', '@outdated ~ approach'],
    deletion_eligible: true,
    superseded_by: 'chunk-new-architecture',
    deletion_marked_at: '2025-12-25T00:00:00Z',
    char_count: 68,
  }),

  /** Chunk with causal links */
  withCausalLinks: createChunkPayload({
    original_text: 'Named vectors implementation allows separate embeddings for text, code, and media content.',
    file_path: '/docs/architecture/named-vectors.md',
    file_name: 'named-vectors.md',
    file_type: '.md',
    qntm_keys: ['@architecture ~ named-vectors', '@implementation ~ design'],
    causal_links: [
      {
        target_id: 'chunk-old-architecture',
        relation: 'supersedes',
        confidence: 0.95,
        inferred_by: 'consolidator',
      },
      {
        target_id: 'chunk-multimodal-support',
        relation: 'extends',
        confidence: 0.85,
        inferred_by: 'explainer',
      },
    ],
    timeline_id: 'architecture-evolution',
    timeline_position: 5,
    char_count: 92,
  }),
} as const

/**
 * Batch of chunks for multi-document tests
 */
export const CHUNK_BATCH = [
  CHUNKS.markdown,
  CHUNKS.typescript,
  CHUNKS.consolidated,
  CHUNKS.important,
  CHUNKS.topicSummary,
] as const

/**
 * Create a sequence of related chunks (for timeline/consolidation tests)
 */
export function createChunkSequence(count: number, basePath = '/docs/sequence'): ChunkPayload[] {
  return Array.from({ length: count }, (_, i) =>
    createChunkPayload({
      original_text: `Chunk ${i + 1} of ${count}: Sequential content for testing.`,
      file_path: `${basePath}/chunk-${i}.md`,
      file_name: `chunk-${i}.md`,
      chunk_index: i,
      total_chunks: count,
      qntm_keys: [`@sequence ~ ${i}`, '@test ~ data'],
      created_at: new Date(Date.UTC(2025, 11, 30, 12, i)).toISOString(),
      timeline_position: i,
    })
  )
}
