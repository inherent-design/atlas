/**
 * Prompts Service
 *
 * Centralized prompt management with LLM-specific variants.
 */

// Types
export * from './types.js'

// Registry
export { promptRegistry, renderPrompt } from './registry.js'

// Sections (composable prompt sections)
export { loadSection, sections } from './sections.js'

// Builders (high-level prompt construction)
export { buildAgentPrompt, buildTaskPrompt, buildArtifactPath } from './builders.js'
export type { BuildAgentPromptOptions, BuildTaskPromptOptions, TaskType } from './builders.js'

// Prompt registration (MUST be called explicitly at application startup)
export { registerPrompts } from './variants/index.js'
