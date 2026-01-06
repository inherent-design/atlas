/**
 * Atlas Working Memory Manager
 *
 * Ephemeral, session-scoped memory buffer for conversation turns.
 * Implements automatic compaction when buffer overflows.
 *
 * Memory gradient:
 * Working Memory (ephemeral) → L0 (episodic) → L1-L2 (semantic) → L3 (crystallized)
 *
 * Key behaviors:
 * - Ring buffer: Oldest turns fall off when capacity exceeded
 * - Auto-compaction: When buffer full, compact and promote to L0
 * - Session-scoped: Each session has isolated working memory
 * - TTL-based: Optionally expire stale sessions
 */

import { createLogger } from '../../shared/logger'
import { getLLMBackendFor } from '../../services/llm'
import { buildCompactionPrompt } from '../../services/llm/prompts'
import { ingest } from '../ingest'
import type { IngestResult } from '../../shared/types'

const log = createLogger('memory:working')

// ============================================
// Types
// ============================================

export interface ConversationTurn {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

export interface CompactedMemory {
  summary: string
  completed: string[]
  in_progress: string[]
  next_steps: string[]
  decisions: string[]
  context: {
    files_involved: string[]
    key_concepts: string[]
    user_preferences: string[]
  }
  verbatim_quotes: string[]
}

export interface WorkingMemoryConfig {
  /** Maximum turns before auto-compaction (default: 20) */
  maxTurns?: number
  /** Session TTL in milliseconds (default: 1 hour) */
  sessionTTL?: number
  /** Auto-compact when buffer full (default: true) */
  autoCompact?: boolean
  /** User ID for scoping (optional) */
  userId?: string
}

// ============================================
// Working Memory Manager
// ============================================

export class WorkingMemoryManager {
  private buffer: ConversationTurn[] = []
  private sessionId: string
  private userId?: string
  private maxTurns: number
  private sessionTTL: number
  private autoCompact: boolean
  private lastActivity: number
  private compactionHistory: Array<{ timestamp: string; turnCount: number }> = []

  constructor(sessionId: string, config: WorkingMemoryConfig = {}) {
    this.sessionId = sessionId
    this.userId = config.userId
    this.maxTurns = config.maxTurns ?? 20
    this.sessionTTL = config.sessionTTL ?? 60 * 60 * 1000 // 1 hour
    this.autoCompact = config.autoCompact ?? true
    this.lastActivity = Date.now()

    log.debug('Working memory initialized', {
      sessionId,
      userId: this.userId,
      maxTurns: this.maxTurns,
      autoCompact: this.autoCompact,
    })
  }

  /**
   * Add a conversation turn to working memory.
   * Triggers auto-compaction if buffer exceeds capacity.
   */
  async addTurn(turn: Omit<ConversationTurn, 'timestamp'>): Promise<void> {
    this.lastActivity = Date.now()

    const fullTurn: ConversationTurn = {
      ...turn,
      timestamp: new Date().toISOString(),
    }

    this.buffer.push(fullTurn)

    log.trace('Turn added to working memory', {
      sessionId: this.sessionId,
      role: turn.role,
      contentLength: turn.content.length,
      bufferSize: this.buffer.length,
    })

    // Check if we need to compact
    if (this.autoCompact && this.buffer.length >= this.maxTurns) {
      log.info('Working memory buffer full, triggering auto-compaction', {
        sessionId: this.sessionId,
        bufferSize: this.buffer.length,
        maxTurns: this.maxTurns,
      })
      await this.compactAndPromote()
    }
  }

  /**
   * Add multiple turns at once.
   */
  async addTurns(turns: Array<Omit<ConversationTurn, 'timestamp'>>): Promise<void> {
    for (const turn of turns) {
      await this.addTurn(turn)
    }
  }

  /**
   * Get current buffer contents.
   */
  getBuffer(): ConversationTurn[] {
    return [...this.buffer]
  }

  /**
   * Get buffer size.
   */
  size(): number {
    return this.buffer.length
  }

  /**
   * Check if session is stale (exceeded TTL).
   */
  isStale(): boolean {
    return Date.now() - this.lastActivity > this.sessionTTL
  }

  /**
   * Compact working memory using LLM summarization.
   * Does NOT promote to L0 - just returns the compacted memory.
   */
  async compact(): Promise<CompactedMemory> {
    if (this.buffer.length === 0) {
      log.debug('Nothing to compact, buffer empty', { sessionId: this.sessionId })
      return {
        summary: '',
        completed: [],
        in_progress: [],
        next_steps: [],
        decisions: [],
        context: {
          files_involved: [],
          key_concepts: [],
          user_preferences: [],
        },
        verbatim_quotes: [],
      }
    }

    log.info('Compacting working memory', {
      sessionId: this.sessionId,
      turnCount: this.buffer.length,
    })

    // Build compaction prompt
    const conversation = this.buffer.map((turn) => ({
      role: turn.role,
      content: turn.content,
    }))
    const prompt = buildCompactionPrompt(conversation)

    // Get LLM backend
    const backend = getLLMBackendFor('json-completion')
    if (!backend || !('completeJSON' in backend)) {
      throw new Error('No JSON-capable LLM backend available for compaction')
    }

    // Run compaction (type assertion: we verified completeJSON exists)
    const result = await (
      backend as { completeJSON<T>(prompt: string): Promise<T> }
    ).completeJSON<CompactedMemory>(prompt)

    log.debug('Compaction complete', {
      sessionId: this.sessionId,
      summaryLength: result.summary.length,
      completedCount: result.completed.length,
      inProgressCount: result.in_progress.length,
    })

    return result
  }

  /**
   * Compact working memory and promote to L0 (Qdrant).
   * Clears buffer after successful promotion.
   */
  async compactAndPromote(): Promise<IngestResult> {
    const compacted = await this.compact()

    if (!compacted.summary && compacted.completed.length === 0) {
      log.debug('Nothing meaningful to promote', { sessionId: this.sessionId })
      return { filesProcessed: 0, chunksStored: 0, errors: [] }
    }

    // Format compacted memory as structured text for ingestion
    const content = this.formatCompactedMemory(compacted)

    // Create temporary file-like structure for ingestion
    const tempPath = `/tmp/atlas-working-memory-${this.sessionId}-${Date.now()}.md`

    // Write to temp file (will be cleaned up by OS)
    const { writeFileSync } = await import('fs')
    writeFileSync(tempPath, content)

    log.info('Promoting compacted memory to L0', {
      sessionId: this.sessionId,
      contentLength: content.length,
    })

    // Ingest with memory-specific metadata
    const result = await ingest({
      paths: [tempPath],
      rootDir: '/tmp',
      verbose: false,
      recursive: false,
    })

    // Record compaction in history
    this.compactionHistory.push({
      timestamp: new Date().toISOString(),
      turnCount: this.buffer.length,
    })

    // Clear buffer after successful promotion
    const promotedTurnCount = this.buffer.length
    this.buffer = []

    log.info('Working memory promoted to L0', {
      sessionId: this.sessionId,
      promotedTurns: promotedTurnCount,
      chunksStored: result.chunksStored,
    })

    // Cleanup temp file
    try {
      const { unlinkSync } = await import('fs')
      unlinkSync(tempPath)
    } catch {
      // Ignore cleanup errors
    }

    return result
  }

  /**
   * Format compacted memory as markdown for ingestion.
   */
  private formatCompactedMemory(compacted: CompactedMemory): string {
    const sections: string[] = []

    // Header with session metadata
    sections.push(`# Working Memory Compaction`)
    sections.push(`Session: ${this.sessionId}`)
    if (this.userId) sections.push(`User: ${this.userId}`)
    sections.push(`Compacted: ${new Date().toISOString()}`)
    sections.push('')

    // Summary
    if (compacted.summary) {
      sections.push(`## Summary`)
      sections.push(compacted.summary)
      sections.push('')
    }

    // Completed work
    if (compacted.completed.length > 0) {
      sections.push(`## Completed`)
      for (const item of compacted.completed) {
        sections.push(`- ${item}`)
      }
      sections.push('')
    }

    // In progress
    if (compacted.in_progress.length > 0) {
      sections.push(`## In Progress`)
      for (const item of compacted.in_progress) {
        sections.push(`- ${item}`)
      }
      sections.push('')
    }

    // Next steps
    if (compacted.next_steps.length > 0) {
      sections.push(`## Next Steps`)
      for (const item of compacted.next_steps) {
        sections.push(`- ${item}`)
      }
      sections.push('')
    }

    // Decisions
    if (compacted.decisions.length > 0) {
      sections.push(`## Decisions`)
      for (const item of compacted.decisions) {
        sections.push(`- ${item}`)
      }
      sections.push('')
    }

    // Context
    if (
      compacted.context.files_involved.length > 0 ||
      compacted.context.key_concepts.length > 0 ||
      compacted.context.user_preferences.length > 0
    ) {
      sections.push(`## Context`)

      if (compacted.context.files_involved.length > 0) {
        sections.push(`### Files`)
        for (const file of compacted.context.files_involved) {
          sections.push(`- \`${file}\``)
        }
      }

      if (compacted.context.key_concepts.length > 0) {
        sections.push(`### Concepts`)
        for (const concept of compacted.context.key_concepts) {
          sections.push(`- ${concept}`)
        }
      }

      if (compacted.context.user_preferences.length > 0) {
        sections.push(`### User Preferences`)
        for (const pref of compacted.context.user_preferences) {
          sections.push(`- ${pref}`)
        }
      }
      sections.push('')
    }

    // Verbatim quotes (preserved exactly)
    if (compacted.verbatim_quotes.length > 0) {
      sections.push(`## Verbatim Quotes`)
      for (const quote of compacted.verbatim_quotes) {
        sections.push(`> ${quote}`)
      }
      sections.push('')
    }

    return sections.join('\n')
  }

  /**
   * Clear buffer without compacting.
   * Use when you want to discard working memory.
   */
  clear(): void {
    const turnCount = this.buffer.length
    this.buffer = []
    log.debug('Working memory cleared', { sessionId: this.sessionId, clearedTurns: turnCount })
  }

  /**
   * Get compaction history for this session.
   */
  getCompactionHistory(): Array<{ timestamp: string; turnCount: number }> {
    return [...this.compactionHistory]
  }
}

// ============================================
// Session Manager (for multi-session support)
// ============================================

const sessions = new Map<string, WorkingMemoryManager>()

/**
 * Get or create a working memory session.
 */
export function getWorkingMemory(
  sessionId: string,
  config?: WorkingMemoryConfig
): WorkingMemoryManager {
  let session = sessions.get(sessionId)

  if (!session || session.isStale()) {
    session = new WorkingMemoryManager(sessionId, config)
    sessions.set(sessionId, session)
  }

  return session
}

/**
 * Remove a session from the manager.
 */
export function removeWorkingMemory(sessionId: string): boolean {
  return sessions.delete(sessionId)
}

/**
 * Get all active session IDs.
 */
export function getActiveSessions(): string[] {
  return Array.from(sessions.keys()).filter((id) => {
    const session = sessions.get(id)
    return session && !session.isStale()
  })
}

/**
 * Cleanup stale sessions.
 */
export function cleanupStaleSessions(): number {
  let cleaned = 0
  for (const [id, session] of sessions) {
    if (session.isStale()) {
      sessions.delete(id)
      cleaned++
    }
  }
  if (cleaned > 0) {
    log.info('Cleaned up stale sessions', { count: cleaned })
  }
  return cleaned
}
