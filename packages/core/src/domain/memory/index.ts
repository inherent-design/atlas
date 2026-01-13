/**
 * Atlas Memory Management
 *
 * Ephemeral working memory and multi-level activation.
 */

// Working Memory (session-scoped conversation buffer)
export {
  WorkingMemoryManager,
  getWorkingMemory,
  removeWorkingMemory,
  getActiveSessions,
  cleanupStaleSessions,
} from './working.js'

export type { ConversationTurn, CompactedMemory, WorkingMemoryConfig } from './working.js'

// Activation Layer (multi-level memory retrieval)
export { activate, formatActivatedMemory } from './activation.js'
export type { ActivationOptions, ActivatedMemory } from './activation.js'
