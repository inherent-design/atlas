/**
 * @inherent.design/atlas-core
 *
 * Core library for Atlas context management with RAG (Voyage + Qdrant)
 */

// Domain exports
export * from './domain/ingest'
export * from './domain/search'
export * from './domain/consolidate'
export * from './domain/memory'

// Service exports
export * from './services/embedding'
export * from './services/llm'
export * from './services/storage'
export * from './services/reranker'
export * from './services/chunking'

// Shared utilities
export * from './shared/config'
export * from './shared/config.loader'
export * from './shared/config.schema'
export * from './shared/logger'
export * from './shared/types'
export * from './shared/utils'

// Core pipeline utilities
export * from './core/pipeline'
export * from './core/adaptive-parallel'
export * from './core/system'
