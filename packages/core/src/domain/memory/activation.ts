/**
 * Atlas Activation Layer
 *
 * Multi-level memory retrieval combining:
 * - Working memory (ephemeral session buffer)
 * - L0 (Episodic: recent specific events)
 * - L1 (Topic: deduplicated content)
 * - L2 (Concept: summarized knowledge)
 * - L3 (Principle: abstract patterns)
 *
 * Uses QNTM query expansion to bridge vocabulary gaps.
 */

import { createLogger } from '../../shared/logger'
import { search } from '../search'
import { generateQueryQNTMKeys, fetchExistingQNTMKeys } from '../../services/llm'
import { getWorkingMemory } from './working'
import type { ConversationTurn } from './working'
import type { SearchResult } from '../../shared/types'

const log = createLogger('memory/activation')

export interface ActivationOptions {
  query: string
  agentId?: string
  sessionId?: string
  limit?: number
  levelWeights?: {
    L0?: number
    L1?: number
    L2?: number
    L3?: number
  }
}

export interface ActivatedMemory {
  working: ConversationTurn[]
  L0: SearchResult[]
  L1: SearchResult[]
  L2: SearchResult[]
  L3: SearchResult[]
  totalResults: number
  queryExpansion: string[]
}

const DEFAULT_WEIGHTS = { L0: 0.4, L1: 0.3, L2: 0.2, L3: 0.1 }

/**
 * Activate multi-level memory for a query.
 *
 * Retrieves relevant context from:
 * 1. Working memory (ephemeral conversation buffer for session)
 * 2. L0-L3 consolidated memories (episodic → semantic → crystallized)
 *
 * Uses QNTM query expansion to bridge vocabulary gap between
 * query language and stored content.
 *
 * @param options - Query, session context, and level weights
 * @returns Activated memories from all levels
 */
export async function activate(options: ActivationOptions): Promise<ActivatedMemory> {
  const {
    query,
    agentId,
    sessionId,
    limit = 20,
    levelWeights = DEFAULT_WEIGHTS,
  } = options

  log.info('Activating memory', { query, agentId, sessionId, limit })

  // 1. Get working memory buffer
  let working: ConversationTurn[] = []
  if (sessionId) {
    const session = getWorkingMemory(sessionId)
    working = session.getBuffer()
    log.debug('Working memory retrieved', { sessionId, turns: working.length })
  }

  // 2. Generate QNTM query expansion
  const existingKeys = await fetchExistingQNTMKeys()
  const expansion = await generateQueryQNTMKeys(query, existingKeys.slice(0, 30))
  const queryExpansion = expansion.keys
  log.debug('Query expanded', { keys: queryExpansion })

  // 3. Calculate per-level limits based on weights
  const totalWeight =
    (levelWeights.L0 || 0) +
    (levelWeights.L1 || 0) +
    (levelWeights.L2 || 0) +
    (levelWeights.L3 || 0)

  const l0Limit = Math.ceil((limit * (levelWeights.L0 || DEFAULT_WEIGHTS.L0)) / totalWeight)
  const l1Limit = Math.ceil((limit * (levelWeights.L1 || DEFAULT_WEIGHTS.L1)) / totalWeight)
  const l2Limit = Math.ceil((limit * (levelWeights.L2 || DEFAULT_WEIGHTS.L2)) / totalWeight)
  const l3Limit = Math.ceil((limit * (levelWeights.L3 || DEFAULT_WEIGHTS.L3)) / totalWeight)

  // 4. Multi-level search (parallel)
  const [L0, L1, L2, L3] = await Promise.all([
    search({ query, limit: l0Limit, consolidationLevel: 0 }),
    search({ query, limit: l1Limit, consolidationLevel: 1 }),
    search({ query, limit: l2Limit, consolidationLevel: 2 }),
    search({ query, limit: l3Limit, consolidationLevel: 3 }),
  ])

  const totalResults = L0.length + L1.length + L2.length + L3.length

  log.info('Activation complete', {
    working: working.length,
    L0: L0.length,
    L1: L1.length,
    L2: L2.length,
    L3: L3.length,
    total: totalResults,
  })

  return { working, L0, L1, L2, L3, totalResults, queryExpansion }
}

/**
 * Format activated memory as structured text for LLM context.
 *
 * @param activated - Activated memory from all levels
 * @returns Formatted string ready for LLM context window
 */
export function formatActivatedMemory(activated: ActivatedMemory): string {
  const sections: string[] = []

  if (activated.working.length > 0) {
    sections.push('## Current Session')
    for (const turn of activated.working) {
      sections.push(`[${turn.role.toUpperCase()}] ${turn.content}`)
    }
  }

  if (activated.L0.length > 0) {
    sections.push('## Recent Context (L0)')
    for (const r of activated.L0) {
      sections.push(`- ${r.text.slice(0, 200)}...`)
    }
  }

  if (activated.L1.length > 0) {
    sections.push('## Deduplicated Topics (L1)')
    for (const r of activated.L1) {
      sections.push(`- ${r.text.slice(0, 200)}...`)
    }
  }

  if (activated.L2.length > 0) {
    sections.push('## Relevant Knowledge (L2)')
    for (const r of activated.L2) {
      sections.push(`- ${r.text.slice(0, 200)}...`)
    }
  }

  if (activated.L3.length > 0) {
    sections.push('## Applicable Patterns (L3)')
    for (const r of activated.L3) {
      sections.push(`- ${r.text.slice(0, 200)}...`)
    }
  }

  return sections.join('\n\n')
}
