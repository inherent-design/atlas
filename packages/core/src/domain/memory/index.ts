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
} from './working'

export type { ConversationTurn, CompactedMemory, WorkingMemoryConfig } from './working'

// Activation Layer (multi-level memory retrieval)
export { activate, formatActivatedMemory } from './activation'
export type { ActivationOptions, ActivatedMemory } from './activation'
