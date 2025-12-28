/**
 * Shared TypeScript types for Atlas
 */

export interface SearchOptions {
  query: string
  limit?: number
  since?: string // ISO 8601 datetime for temporal filtering
  qntmKey?: string // Filter by specific QNTM key
}

export interface SearchResult {
  text: string
  file_path: string
  chunk_index: number
  score: number
  created_at: string
  qntm_key: string
}

export interface ChunkPayload {
  original_text: string
  file_path: string
  file_name: string
  file_type: string
  chunk_index: number
  total_chunks: number
  char_count: number
  qntm_keys: string[] // Multiple semantic addresses (tag-based)
  created_at: string
  importance: 'normal' | 'high' | 'low'
  consolidated: boolean
  [key: string]: unknown // Index signature for Qdrant compatibility
}

export interface QdrantPoint {
  id: string
  vector: number[]
  payload: ChunkPayload
}
