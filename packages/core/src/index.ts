/**
 * @inherent.design/atlas-core
 *
 * Core library for Atlas context management with RAG (Voyage + Qdrant)
 */

// Domain exports (explicit to avoid conflicts with daemon/protocol.ts)
export { ingest } from './domain/ingest'
export { search, timeline, formatResults } from './domain/search'
export { consolidate, type ConsolidateConfig, type ConsolidateResult } from './domain/consolidate'
export * from './domain/memory'

// Service exports (functions and main types)
export {
  getEmbeddingBackend,
  getEmbeddingDimensions,
  initializeEmbeddingBackends,
} from './services/embedding'
export {
  getLLMBackend,
  getLLMBackendFor,
  initializeLLMBackends,
  setQNTMProvider,
  generateQNTMKeys,
  fetchExistingQNTMKeys,
  type LLMProvider,
  type CompletionResult,
} from './services/llm'
export { getStorageBackend, enableHNSW, disableHNSW } from './services/storage'
export { getRerankerBackendFor } from './services/reranker'
export { createTextSplitter, getTextSplitter, resetTextSplitter } from './services/chunking'

// Shared utilities and types (prefer shared/types.ts for domain types)
export * from './shared/config'
export * from './shared/config.loader'
export * from './shared/config.schema'
export * from './shared/logger'
export * from './shared/types' // Includes IngestOptions, SearchOptions, IngestResult, SearchResult
export * from './shared/utils'

// Core pipeline utilities
export * from './core/pipeline'
export * from './core/adaptive-parallel'
export * from './core/system'
export * from './core/scheduler-manager'
export * from './core/system-pressure-monitor'
export * from './core/file-watcher'

// Daemon and client (exclude conflicting types from daemon/protocol)
export { startDaemon, stopDaemon, isDaemonRunning, getDaemonPid, killDaemon } from './daemon'
export * from './client'

// Tracking service
export * from './services/tracking'

// Doctor service
export * from './services/doctor'
