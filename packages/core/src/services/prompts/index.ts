/**
 * Prompts Service
 *
 * Centralized prompt management with LLM-specific variants.
 */

// Types
export * from './types'

// Registry
export { promptRegistry, renderPrompt } from './registry'

// Variants (auto-registers on import)
export * from './variants'
