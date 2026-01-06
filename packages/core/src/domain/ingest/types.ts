/**
 * Chunk-Level Pipeline Types
 *
 * Progressive enrichment pattern:
 * ChunkWithContext → EmbeddedChunk → KeyedChunk → VectorPoint
 *
 * Each stage adds information without mutation (pure transforms).
 */

/**
 * Base chunk with file context.
 * Output of chunking stage, input to embedding stage.
 */
export interface ChunkWithContext {
  chunk: string
  context: {
    filePath: string // Relative to rootDir (user intent, not CWD)
    fileName: string
    fileType: string
    chunkIndex: number
    totalChunks: number
    contentType: 'text' | 'code' | 'media'
    // All chunks from this file (for contextualized embedding)
    allChunks?: string[]
    // Split metadata (for large documents exceeding context window)
    splitIndex?: number // Which sub-document (0-based)
    splitTotal?: number // Total sub-documents
    chunkIndexGlobal?: number // Original position before splitting
  }
}

/**
 * Chunk with embeddings added.
 * Output of embedding stage, input to QNTM key generation.
 */
export interface EmbeddedChunk extends ChunkWithContext {
  embedding: number[]
  embeddingModel: string
  embeddingStrategy: 'snippet' | 'contextualized'
  // Optional code embedding (if content_type = 'code')
  codeEmbedding?: number[]
}

/**
 * Chunk with QNTM keys added.
 * Output of key generation stage, input to upsert.
 */
export interface KeyedChunk extends EmbeddedChunk {
  qntmKeys: string[]
}
