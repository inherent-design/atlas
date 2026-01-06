/**
 * Embedding fixtures for testing
 *
 * Provides deterministic embedding vectors for consistent test results.
 */

/**
 * Generate a deterministic 1024-dimensional embedding from a seed.
 *
 * Uses simple hash function to create reproducible vectors.
 * Same seed always produces same vector.
 *
 * @param seed - String seed for reproducibility
 * @returns 1024-dimensional vector
 */
export function generateEmbedding(seed: string): number[] {
  const vector: number[] = []
  let hash = 0

  // Simple string hash
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i)
    hash = hash & hash // Convert to 32-bit integer
  }

  // Generate 1024 values using hash as seed
  for (let i = 0; i < 1024; i++) {
    // Linear congruential generator for deterministic pseudorandom values
    hash = (hash * 1103515245 + 12345) & 0x7fffffff
    vector.push((hash / 0x7fffffff) * 2 - 1) // Normalize to [-1, 1]
  }

  return vector
}

/**
 * Generate named vectors for a point.
 * Creates text, code, and media vectors from different seeds.
 *
 * @param baseSeed - Base seed for vector generation
 * @returns Object with text, code, and media vectors
 */
export function generateNamedVectors(baseSeed: string): {
  text: number[]
  code: number[]
  media: number[]
} {
  return {
    text: generateEmbedding(`${baseSeed}:text`),
    code: generateEmbedding(`${baseSeed}:code`),
    media: generateEmbedding(`${baseSeed}:media`),
  }
}

/**
 * Common embedding fixtures for testing
 */
export const EMBEDDINGS = {
  /** Default test embedding */
  default: generateEmbedding('default'),
  /** Zero vector (rare but useful for edge cases) */
  zero: new Array(1024).fill(0),
  /** Unit vector (all components equal) */
  unit: new Array(1024).fill(1 / Math.sqrt(1024)),
  /** Memory-related content */
  memory: generateEmbedding('memory consolidation neural patterns'),
  /** Sleep-related content */
  sleep: generateEmbedding('sleep patterns episodic semantic'),
  /** Code-related content */
  code: generateEmbedding('typescript function implementation'),
  /** Documentation content */
  docs: generateEmbedding('architecture documentation systems'),
} as const

/**
 * Batch of diverse embeddings for multi-result tests
 */
export const EMBEDDING_BATCH = [
  generateEmbedding('test-chunk-0'),
  generateEmbedding('test-chunk-1'),
  generateEmbedding('test-chunk-2'),
  generateEmbedding('test-chunk-3'),
  generateEmbedding('test-chunk-4'),
] as const

/**
 * Calculate cosine similarity between two vectors.
 * Useful for verifying search result ordering.
 *
 * @param a - First vector
 * @param b - Second vector
 * @returns Similarity score (0.0-1.0)
 */
export function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) {
    throw new Error('Vectors must have same dimensions')
  }

  let dotProduct = 0
  let normA = 0
  let normB = 0

  for (let i = 0; i < a.length; i++) {
    const ai = a[i]!
    const bi = b[i]!
    dotProduct += ai * bi
    normA += ai * ai
    normB += bi * bi
  }

  const magnitude = Math.sqrt(normA) * Math.sqrt(normB)
  if (magnitude === 0) return 0

  return dotProduct / magnitude
}
