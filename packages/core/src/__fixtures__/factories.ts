/**
 * Factory functions for dynamic fixture generation
 *
 * Provides builders and generators for test data.
 * Structure matches live production data in __fixtures__/live-data/.
 */

import type { ChunkPayload, SearchResult } from '../shared/types.js'
import type { NamedVectors, VectorPoint } from '../services/storage/types.js'
import { generateEmbedding, generateNamedVectors } from './embeddings.js'
import { createChunkPayload } from './chunks.js'

/**
 * ChunkPayload builder with fluent interface
 */
export class ChunkPayloadBuilder {
  private payload: Partial<ChunkPayload> = {}

  /** Set original text */
  withText(text: string): this {
    this.payload.original_text = text
    this.payload.char_count = text.length
    return this
  }

  /** Set file path */
  withFilePath(path: string): this {
    this.payload.file_path = path
    const fileName = path.split('/').pop() || 'unknown'
    this.payload.file_name = fileName
    const fileType = fileName.slice(fileName.lastIndexOf('.'))
    this.payload.file_type = fileType
    return this
  }

  /** Set QNTM keys */
  withQntmKeys(...keys: string[]): this {
    this.payload.qntm_keys = keys
    return this
  }

  /** Set consolidation level */
  withConsolidationLevel(level: 0 | 1 | 2 | 3): this {
    this.payload.consolidation_level = level
    return this
  }

  /** Set importance */
  withImportance(importance: 'low' | 'normal' | 'high'): this {
    this.payload.importance = importance
    return this
  }

  /** Set creation timestamp */
  withCreatedAt(timestamp: string): this {
    this.payload.created_at = timestamp
    return this
  }

  /** Set chunk index and total */
  withChunkInfo(index: number, total: number): this {
    this.payload.chunk_index = index
    this.payload.total_chunks = total
    return this
  }

  /** Set parents (for consolidated chunks) */
  withParents(...parentIds: string[]): this {
    this.payload.parents = parentIds
    return this
  }

  /** Set content type and vectors */
  withContentType(
    contentType: 'text' | 'code' | 'media',
    vectorsPresent?: ('text' | 'code' | 'media')[]
  ): this {
    this.payload.content_type = contentType
    this.payload.vectors_present = vectorsPresent
    return this
  }

  /** Build final ChunkPayload */
  build(): ChunkPayload {
    return createChunkPayload(this.payload)
  }
}

/**
 * VectorPoint builder with fluent interface
 */
export class VectorPointBuilder {
  private id: string = `point-${Date.now()}`
  private vector: NamedVectors = {}
  private payload: Partial<ChunkPayload> = {}

  /** Set point ID */
  withId(id: string): this {
    this.id = id
    return this
  }

  /** Set text vector */
  withTextVector(vector?: number[]): this {
    this.vector.text = vector || generateEmbedding(`${this.id}:text`)
    return this
  }

  /** Set code vector */
  withCodeVector(vector?: number[]): this {
    this.vector.code = vector || generateEmbedding(`${this.id}:code`)
    return this
  }

  /** Set media vector */
  withMediaVector(vector?: number[]): this {
    this.vector.media = vector || generateEmbedding(`${this.id}:media`)
    return this
  }

  /** Set all named vectors from seed */
  withNamedVectors(seed: string): this {
    const vectors = generateNamedVectors(seed)
    this.vector = vectors
    return this
  }

  /** Set payload */
  withPayload(payload: Partial<ChunkPayload>): this {
    this.payload = payload
    return this
  }

  /** Build final VectorPoint */
  build(): VectorPoint {
    return {
      id: this.id,
      vector: this.vector,
      payload: createChunkPayload(this.payload),
    }
  }
}

/**
 * SearchResult builder with fluent interface
 */
export class SearchResultBuilder {
  private result: Partial<SearchResult> = {
    chunk_index: 0,
    score: 0.9,
    created_at: new Date().toISOString(),
  }

  /** Set result text */
  withText(text: string): this {
    this.result.text = text
    return this
  }

  /** Set file path */
  withFilePath(path: string): this {
    this.result.file_path = path
    return this
  }

  /** Set similarity score */
  withScore(score: number): this {
    this.result.score = score
    return this
  }

  /** Set rerank score */
  withRerankScore(score: number): this {
    this.result.rerank_score = score
    return this
  }

  /** Set QNTM key */
  withQntmKey(key: string): this {
    this.result.qntm_key = key
    return this
  }

  /** Set chunk index */
  withChunkIndex(index: number): this {
    this.result.chunk_index = index
    return this
  }

  /** Set creation timestamp */
  withCreatedAt(timestamp: string): this {
    this.result.created_at = timestamp
    return this
  }

  /** Build final SearchResult */
  build(): SearchResult {
    return this.result as SearchResult
  }
}

/**
 * Generate a batch of VectorPoints with similar vectors
 *
 * @param count - Number of points to generate
 * @param baseSeed - Base seed for vector generation
 * @param vectorType - Which named vector to include
 * @returns Array of VectorPoints
 */
export function generateVectorPointBatch(
  count: number,
  baseSeed = 'test',
  vectorType: 'text' | 'code' | 'media' = 'text'
): VectorPoint[] {
  const points: VectorPoint[] = []

  for (let i = 0; i < count; i++) {
    const builder = new VectorPointBuilder().withId(`${baseSeed}-${i}`).withPayload({
      original_text: `Test point ${i} for batch generation`,
      file_path: `/test/batch/${i}.md`,
      qntm_keys: [`@test ~ ${baseSeed}`, `@batch ~ ${i}`],
    })

    // Add appropriate vector type
    switch (vectorType) {
      case 'text':
        builder.withTextVector()
        break
      case 'code':
        builder.withCodeVector()
        break
      case 'media':
        builder.withMediaVector()
        break
    }

    points.push(builder.build())
  }

  return points
}

/**
 * Generate search results with descending scores
 *
 * @param count - Number of results
 * @param baseScore - Starting score
 * @param decrement - Score decrease per result
 * @returns Array of SearchResults
 */
export function generateSearchResults(
  count: number,
  baseScore = 0.95,
  decrement = 0.05
): SearchResult[] {
  const results: SearchResult[] = []

  for (let i = 0; i < count; i++) {
    const score = Math.max(0.1, baseScore - i * decrement)
    results.push(
      new SearchResultBuilder()
        .withText(`Search result ${i + 1}`)
        .withFilePath(`/test/results/${i}.md`)
        .withScore(score)
        .withQntmKey(`@test ~ result-${i}`)
        .withChunkIndex(i)
        .build()
    )
  }

  return results
}

/**
 * Generate consolidated chunk hierarchy
 *
 * @param levels - Number of consolidation levels
 * @returns Array of chunks from level 0 to N
 */
export function generateConsolidationHierarchy(levels: number): ChunkPayload[] {
  const chunks: ChunkPayload[] = []
  let parentIds: string[] = []

  for (let level = 0; level <= levels; level++) {
    const id = `chunk-level-${level}`
    const chunk = new ChunkPayloadBuilder()
      .withText(`Consolidated chunk at level ${level}`)
      .withFilePath(`/test/consolidated/level-${level}.md`)
      .withConsolidationLevel(level as 0 | 1 | 2 | 3)
      .withQntmKeys(`@consolidated ~ level-${level}`)
      .build()

    // Add parents from previous level
    if (parentIds.length > 0) {
      chunk.parents = parentIds
    }

    chunks.push(chunk)
    parentIds = [id] // Next level's parent
  }

  return chunks
}

/**
 * Export builder classes for direct use
 */
export const Builders = {
  ChunkPayload: ChunkPayloadBuilder,
  VectorPoint: VectorPointBuilder,
  SearchResult: SearchResultBuilder,
}
