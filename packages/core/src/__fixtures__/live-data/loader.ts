/**
 * Live Data Fixture Loader
 *
 * Loads real service data captured from live Atlas instance.
 * Use these fixtures in tests to ensure mocks match production reality.
 */

import qdrantPointsDataRaw from './qdrant-points.json' with { type: 'json' }
import postgresSourcesDataRaw from './postgres-sources.json' with { type: 'json' }
import postgresChunksDataRaw from './postgres-chunks.json' with { type: 'json' }
import meilisearchDocumentsDataRaw from './meilisearch-documents.json' with { type: 'json' }
import meilisearchSettingsDataRaw from './meilisearch-settings.json' with { type: 'json' }
import meilisearchStatsDataRaw from './meilisearch-stats.json' with { type: 'json' }

export interface QdrantPoint {
  id: string
  payload: Record<string, any>
}

export interface PostgresSource {
  id: string
  path: string
  content_hash: string
  status: string
  file_mtime: string
  created_at: string
}

export interface PostgresChunk {
  id: string
  source_id: string
  chunk_index: number
  payload: Record<string, any>
  created_at: string
}

export interface MeilisearchDocument {
  id: string
  original_text: string
  file_path: string
  file_name: string
  qntm_keys: string[]
  file_type: string
  consolidation_level: number
  content_type: string
  created_at: string
  importance: string
}

export interface MeilisearchSettings {
  searchableAttributes: string[]
  filterableAttributes: string[]
  sortableAttributes: string[]
  rankingRules: string[]
  stopWords: string[]
  synonyms: Record<string, string[]>
  distinctAttribute: string | null
  typoTolerance: any
  faceting: any
  pagination: any
}

// Type the JSON imports properly
const qdrantPointsData = qdrantPointsDataRaw as { points: QdrantPoint[] }
const postgresSourcesData = postgresSourcesDataRaw as PostgresSource[]
// PostgresChunk payload is stringified in JSON export, needs parsing
interface PostgresChunkRaw extends Omit<PostgresChunk, 'payload'> {
  payload: string | Record<string, any>
}
const postgresChunksData = postgresChunksDataRaw as PostgresChunkRaw[]
const meilisearchDocumentsData = meilisearchDocumentsDataRaw as { hits: MeilisearchDocument[] }
const meilisearchSettingsData = meilisearchSettingsDataRaw as MeilisearchSettings
const meilisearchStatsData = meilisearchStatsDataRaw as Record<string, unknown>

// Parse stringified payloads from PostgreSQL JSON export
const parsedPostgresChunks: PostgresChunk[] = postgresChunksData.map((chunk) => ({
  ...chunk,
  payload: typeof chunk.payload === 'string' ? JSON.parse(chunk.payload) : chunk.payload,
}))

export const liveFixtures = {
  qdrant: {
    points: qdrantPointsData.points,
    getPoint: (id: string) => qdrantPointsData.points.find(p => p.id === id),
    getPointsByFile: (filePath: string) =>
      qdrantPointsData.points.filter(p => p.payload.file_path === filePath),
  },
  postgres: {
    sources: postgresSourcesData,
    chunks: parsedPostgresChunks,
    getSource: (id: string) => postgresSourcesData.find(s => s.id === id),
    getChunksBySource: (sourceId: string) =>
      parsedPostgresChunks.filter(c => c.source_id === sourceId),
  },
  meilisearch: {
    documents: meilisearchDocumentsData.hits as MeilisearchDocument[],
    settings: meilisearchSettingsData as MeilisearchSettings,
    stats: meilisearchStatsData,
    search: (query: string, limit = 20) =>
      meilisearchDocumentsData.hits.filter((doc: any) =>
        doc.original_text.toLowerCase().includes(query.toLowerCase())
      ).slice(0, limit),
    getDocument: (id: string) =>
      meilisearchDocumentsData.hits.find((doc: any) => doc.id === id),
  },
}

export default liveFixtures
