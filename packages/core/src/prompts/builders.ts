/**
 * Prompt Builders
 *
 * High-level functions for building agent and task prompts.
 */

import { promptRegistry } from './registry'
import { loadSection, sections } from './sections'
import { renderTemplate as renderTemplateSync } from './types'
import type { AgentRole, PromptBackendInfo } from './types'

// NOTE: Prompt registration is now lazy (no module-level side effect).
// Consumers must call registerPrompts() explicitly at application startup.
// See: variants/index.ts for registration function.

/**
 * Async version of renderTemplate that supports section loading.
 * Replaces {{SECTION_NAME}} with loaded section content.
 * Replaces {{variable}} with provided variables.
 */
async function renderTemplate(
  template: string,
  variables: Record<string, string>
): Promise<string> {
  let rendered = template

  // 1. Replace special sections {{ALL_CAPS}}
  const sectionMatches = [...template.matchAll(/\{\{([A-Z_]+)\}\}/g)]
  for (const match of sectionMatches) {
    const sectionName = match[1]!
    if (sections[sectionName]) {
      const content = await loadSection(sectionName)
      rendered = rendered.replace(match[0], content)
    }
  }

  // 2. Replace regular variables {{lowercase_or_camelCase}}
  rendered = renderTemplateSync(rendered, variables)

  return rendered
}

/**
 * Options for building agent prompts
 */
export interface BuildAgentPromptOptions {
  /** Context strings to include */
  context?: string[]
  /** Include file organization guidance (default: true) */
  includeFileOrg?: boolean
  /** Include Atlas identity (default: false, only for orchestrators) */
  includeAtlasIdentity?: boolean
  /** Include signal system guidance (default: true) */
  includeSignalSystem?: boolean
  /** Backend for variant selection */
  backend?: PromptBackendInfo
}

/**
 * Build agent prompt with context and sections.
 *
 * @param role - Agent role (observer, sensor, integrator, etc.)
 * @param task - Task description
 * @param options - Build options
 * @returns Rendered prompt string
 */
export async function buildAgentPrompt(
  role: AgentRole,
  task: string,
  options?: BuildAgentPromptOptions | string[] // Support old signature (string[])
): Promise<string> {
  // Handle backward compatibility (old signature: context as string[])
  let opts: BuildAgentPromptOptions
  if (Array.isArray(options)) {
    opts = { context: options }
  } else {
    opts = options ?? {}
  }

  const {
    context = [],
    includeFileOrg = true,
    includeAtlasIdentity = false,
    includeSignalSystem = true,
    backend,
  } = opts

  // Get default backend if not provided
  const effectiveBackend = backend ?? getDefaultBackend()

  // Map role to prompt ID
  const promptId = getAgentPromptId(role)

  // Select variant
  const variant = promptRegistry.selectVariant(promptId, effectiveBackend)
  if (!variant) {
    throw new Error(`No prompt variant found for role: ${role}`)
  }

  // Build variables
  const variables: Record<string, string> = {
    task,
    context: context.join('\n\n---\n\n'),
  }

  // Render template (handles {{SECTION_NAME}} placeholders)
  let prompt = await renderTemplate(variant.template, variables)

  // Inject optional sections if not already in template
  if (includeFileOrg && !prompt.includes('{{FILE_ORG_CONTEXT}}')) {
    const fileOrg = await loadSection('FILE_ORG_CONTEXT')
    prompt = `${prompt}\n\n---\n\n## File Organization\n\n${fileOrg}`
  }

  if (includeAtlasIdentity && !prompt.includes('{{CLAUDE_SYS}}')) {
    const identity = await loadSection('CLAUDE_SYS')
    prompt = `${prompt}\n\n---\n\n## Atlas Identity\n\n${identity}`
  }

  if (includeSignalSystem && !prompt.includes('{{SIGNAL_SYSTEM}}')) {
    const signals = await loadSection('SIGNAL_SYSTEM')
    prompt = `${prompt}\n\n---\n\n## Learning from Failures\n\n${signals}`
  }

  return prompt
}

/**
 * Options for building task prompts
 */
export interface BuildTaskPromptOptions {
  /** Backend for variant selection */
  backend?: PromptBackendInfo
  /** Wrap prompt for JSON output (default: true) */
  wrapJSON?: boolean
}

/**
 * Task types available in the registry
 */
export type TaskType =
  | 'qntm-generation'
  | 'consolidation-classify'
  | 'compaction'
  | 'query-expansion'

/**
 * Build task prompt (QNTM, consolidation, etc.)
 *
 * @param taskType - Type of task prompt
 * @param variables - Template variables
 * @param options - Build options
 * @returns Rendered prompt string
 */
export async function buildTaskPrompt(
  taskType: TaskType,
  variables: Record<string, string>,
  options?: BuildTaskPromptOptions
): Promise<string> {
  const { backend, wrapJSON = true } = options ?? {}

  const effectiveBackend = backend ?? getDefaultBackend()

  const variant = promptRegistry.selectVariant(taskType, effectiveBackend)
  if (!variant) {
    throw new Error(`No prompt variant found for task: ${taskType}`)
  }

  let prompt = await renderTemplate(variant.template, variables)

  if (wrapJSON) {
    prompt = wrapForJSON(prompt)
  }

  return prompt
}

/**
 * Build artifact file path for agent output.
 *
 * @param role - Agent role
 * @param outputType - Type of output (analysis, reports, validation, etc.)
 * @param project - Project name
 * @param taskName - Task name
 * @returns Absolute file path
 */
export function buildArtifactPath(
  role: AgentRole,
  outputType: string,
  project: string,
  taskName: string
): string {
  const timestamp = new Date().toISOString().split('T')[0] // YYYY-MM-DD
  const homeDir = process.env.HOME || '/tmp'
  const filename = `${taskName}-${timestamp}.md`
  return `${homeDir}/.atlas/${role}/${outputType}/${project}/${filename}`
}

/**
 * Build frontmatter for .atlas files.
 *
 * @param role - Agent role
 * @param outputType - Type of output
 * @param project - Project name
 * @param task - Task name
 * @returns YAML frontmatter string (with trailing newlines)
 */
export function buildFrontmatter(
  role: AgentRole,
  outputType: string,
  project: string,
  task: string
): string {
  const date = new Date().toISOString().split('T')[0]
  return `---
agent: ${role}
output_type: ${outputType}
project: ${project}
task: ${task}
date: ${date}
---

`
}

/**
 * Map agent role to prompt ID.
 * Handles both 3-role and 6-role models.
 */
function getAgentPromptId(role: AgentRole): string {
  // Map role directly to prompt ID
  // 3-role: sensor, reasoner, integrator
  // 6-role: observer, connector, explainer, challenger, integrator-6role, meta
  return `agent-${role}`
}

/**
 * Get default backend for prompt selection.
 * Falls back to universal variant if no backend specified.
 */
function getDefaultBackend(): PromptBackendInfo {
  return {
    name: '*',
    capabilities: new Set(),
  }
}

/**
 * Wrap prompt for JSON output enforcement.
 * Used for task prompts that expect structured JSON responses.
 */
function wrapForJSON(prompt: string): string {
  return `${prompt}

CRITICAL: You MUST respond with valid JSON only. No markdown, no explanations, no code blocks.
Just the raw JSON object.`
}
