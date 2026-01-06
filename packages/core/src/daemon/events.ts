/**
 * Atlas event type definitions
 *
 * All events flow through the daemon's event router and can be
 * subscribed to by clients via JSON-RPC.
 */

// ============================================
// Ingest Events
// ============================================

export type IngestStartedEvent = {
  type: 'ingest.started'
  data: {
    paths: string[]
    fileCount: number
  }
}

export type IngestFileStartedEvent = {
  type: 'ingest.file.started'
  data: {
    path: string
    chunkCount: number
  }
}

export type IngestFileSkippedEvent = {
  type: 'ingest.file.skipped'
  data: {
    path: string
    reason: 'unchanged' | 'ignored'
  }
}

export type IngestChunkEmbeddedEvent = {
  type: 'ingest.chunk.embedded'
  data: {
    path: string
    index: number
    strategy: 'snippet' | 'contextualized'
  }
}

export type IngestChunkStoredEvent = {
  type: 'ingest.chunk.stored'
  data: {
    path: string
    index: number
    id: string // Qdrant point ID
  }
}

export type IngestFileCompletedEvent = {
  type: 'ingest.file.completed'
  data: {
    path: string
    chunks: number
  }
}

export type IngestCompletedEvent = {
  type: 'ingest.completed'
  data: {
    files: number
    chunks: number
    skipped: number
    errors: number
  }
}

export type IngestErrorEvent = {
  type: 'ingest.error'
  data: {
    path?: string
    error: string
    phase: 'read' | 'embed' | 'qntm' | 'store'
  }
}

// ============================================
// Search Events
// ============================================

export type SearchStartedEvent = {
  type: 'search.started'
  data: {
    query: string
    sessionId?: string
    limit: number
  }
}

export type SearchActivatedEvent = {
  type: 'search.activated'
  data: {
    working: number // Working memory entries
    L0: number // Episodic
    L1: number // Topic
    L2: number // Concept
    L3: number // Principle
  }
}

export type SearchCompletedEvent = {
  type: 'search.completed'
  data: {
    results: number
    took: number // milliseconds
    reranked: boolean
  }
}

export type SearchErrorEvent = {
  type: 'search.error'
  data: {
    query: string
    error: string
    phase: 'embed' | 'search' | 'rerank'
  }
}

// ============================================
// Consolidation Events
// ============================================

export type ConsolidateTriggeredEvent = {
  type: 'consolidate.triggered'
  data: {
    reason: 'threshold' | 'manual'
    l0Count: number
  }
}

export type ConsolidatePairMergedEvent = {
  type: 'consolidate.pair.merged'
  data: {
    primary: string // Point ID
    secondary: string // Point ID
    type: 'duplicate_work' | 'sequential_iteration' | 'contextual_convergence'
  }
}

export type ConsolidateCompletedEvent = {
  type: 'consolidate.completed'
  data: {
    merged: number
    deleted: number
    took: number // milliseconds
  }
}

export type ConsolidateErrorEvent = {
  type: 'consolidate.error'
  data: {
    error: string
    phase: 'find' | 'classify' | 'merge'
  }
}

// ============================================
// Watch Events (File Watcher)
// ============================================

export type WatchFileChangedEvent = {
  type: 'watch.file.changed'
  data: {
    path: string
    changeType: 'modified' | 'created' | 'deleted'
  }
}

export type WatchIngestQueuedEvent = {
  type: 'watch.ingest.queued'
  data: {
    path: string
  }
}

// ============================================
// Session Events (Claude Code Integration)
// ============================================

export type SessionCompactingEvent = {
  type: 'session.compacting'
  data: {
    sessionId: string
    transcriptPath: string
    trigger: 'manual' | 'auto'
    cwd?: string
  }
}

export type SessionEndedEvent = {
  type: 'session.ended'
  data: {
    sessionId: string
    transcriptPath: string
    reason?: string
    cwd?: string
  }
}

export type SessionIngestedEvent = {
  type: 'session.ingested'
  data: {
    sessionId: string
    chunksCreated: number
    took: number // milliseconds
  }
}

export type SessionErrorEvent = {
  type: 'session.error'
  data: {
    sessionId: string
    error: string
    phase: 'read' | 'parse' | 'ingest'
  }
}

// ============================================
// Admin Events
// ============================================

export type HealthCheckedEvent = {
  type: 'health.checked'
  data: {
    qdrant: boolean
    ollama: boolean
    voyage: boolean
  }
}

export type DepsMissingEvent = {
  type: 'deps.missing'
  data: {
    dep: 'qdrant' | 'ollama' | 'voyage'
    available: boolean
    remedy?: string
  }
}

export type DaemonStartedEvent = {
  type: 'daemon.started'
  data: {
    pid: number
    socket: string
  }
}

export type DaemonStoppingEvent = {
  type: 'daemon.stopping'
  data: {
    reason: 'signal' | 'error' | 'manual'
  }
}

// ============================================
// Union Type
// ============================================

export type AtlasEvent =
  // Ingest
  | IngestStartedEvent
  | IngestFileStartedEvent
  | IngestFileSkippedEvent
  | IngestChunkEmbeddedEvent
  | IngestChunkStoredEvent
  | IngestFileCompletedEvent
  | IngestCompletedEvent
  | IngestErrorEvent
  // Search
  | SearchStartedEvent
  | SearchActivatedEvent
  | SearchCompletedEvent
  | SearchErrorEvent
  // Consolidation
  | ConsolidateTriggeredEvent
  | ConsolidatePairMergedEvent
  | ConsolidateCompletedEvent
  | ConsolidateErrorEvent
  // Watch
  | WatchFileChangedEvent
  | WatchIngestQueuedEvent
  // Session (Claude Code integration)
  | SessionCompactingEvent
  | SessionEndedEvent
  | SessionIngestedEvent
  | SessionErrorEvent
  // Admin
  | HealthCheckedEvent
  | DepsMissingEvent
  | DaemonStartedEvent
  | DaemonStoppingEvent

/**
 * Event emitter type
 */
export type EventEmitter = (event: AtlasEvent) => void

/**
 * Event subscriber callback
 */
export type EventSubscriber = (event: AtlasEvent) => void | Promise<void>

/**
 * Extract event data type from event type string
 */
export type EventData<T extends AtlasEvent['type']> = Extract<AtlasEvent, { type: T }>['data']
