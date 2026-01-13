/**
 * @inherent.design/atlas-core
 *
 * Core library for Atlas context management with RAG (Voyage + Qdrant)
 */

// Domain exports (explicit to avoid conflicts with daemon/protocol.ts)
export { ingest } from './domain/ingest/index.js'
export { search, timeline, formatResults } from './domain/search/index.js'
export { consolidate, type ConsolidateConfig, type ConsolidateResult } from './domain/consolidate/index.js'
export * from './domain/memory/index.js'

// Service exports (functions and main types)
export {
  getEmbeddingBackend,
  getEmbeddingDimensions,
  initializeEmbeddingBackends,
} from './services/embedding/index.js'
export {
  getLLMBackend,
  getLLMBackendFor,
  initializeLLMBackends,
  generateQNTMKeys,
  fetchExistingQNTMKeys,
  type CompletionResult,
} from './services/llm/index.js'
export {
  getStorageBackend,
  getStorageService,
  getQdrantClient,
  enableHNSW,
  disableHNSW,
} from './services/storage/index.js'
export { getRerankerBackendFor } from './services/reranker/index.js'
export { createTextSplitter, getTextSplitter, resetTextSplitter } from './services/chunking/index.js'
export {
  getApplicationService,
  resetApplicationService,
  DefaultApplicationService,
} from './services/application/index.js'

// Shared utilities and types (prefer shared/types.ts for domain types)
export * from './shared/config.js'
export * from './shared/config.loader.js'
export * from './shared/config.schema.js'
export * from './shared/logger.js'
export * from './shared/types.js' // Includes IngestOptions, SearchOptions, IngestResult, SearchResult
export * from './shared/utils.js'

// Core pipeline utilities
export * from './core/pipeline.js'
export * from './core/adaptive-parallel.js'
export * from './core/system.js'
export * from './core/scheduler-manager.js'
export * from './core/system-pressure-monitor.js'
export * from './core/file-watcher.js'

// Daemon and client (exclude conflicting types from daemon/protocol)
export { startDaemon, stopDaemon, isDaemonRunning, getDaemonPid, killDaemon } from './daemon/index.js'
export * from './client/index.js'

// Tracking service
export * from './services/tracking/index.js'

// Doctor service
export * from './services/doctor/index.js'

// Prompts service (includes registerPrompts for lazy initialization)
export { registerPrompts } from './prompts/index.js'
