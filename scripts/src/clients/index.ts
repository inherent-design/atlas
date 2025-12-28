/**
 * Client Providers - Public API
 *
 * Centralized client initialization for external services:
 * - Voyage AI (embeddings)
 * - Qdrant (vector database)
 * - LangChain Text Splitter (chunking)
 */

// Voyage AI
export { createVoyageClient, getVoyageClient, resetVoyageClient } from './voyage'

// Qdrant
export { createQdrantClient, getQdrantClient, resetQdrantClient } from './qdrant'

// Text Splitter
export { createTextSplitter, getTextSplitter, resetTextSplitter } from './splitter'

// Unified reset for testing
export function resetClients(): void {
  const { resetVoyageClient } = require('./voyage')
  const { resetQdrantClient } = require('./qdrant')
  const { resetTextSplitter } = require('./splitter')

  resetVoyageClient()
  resetQdrantClient()
  resetTextSplitter()
}
