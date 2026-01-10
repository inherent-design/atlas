/**
 * Prompts Service
 *
 * Centralized prompt management with LLM-specific variants.
 */

// Types
export * from './types'

// Registry
export { promptRegistry, renderPrompt } from './registry'

// Sections (composable prompt sections)
export { loadSection, sections } from './sections'

// Builders (high-level prompt construction)
export { buildAgentPrompt, buildTaskPrompt, buildArtifactPath, buildFrontmatter } from './builders'
export type { BuildAgentPromptOptions, BuildTaskPromptOptions, TaskType } from './builders'

// Prompt registration (MUST be called explicitly at application startup)
export { registerPrompts } from './variants'
