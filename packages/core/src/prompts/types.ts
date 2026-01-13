/**
 * Prompt Registry Types
 *
 * LLM-specific prompt variants with capability-aware selection.
 * Enables optimized prompts per model family while maintaining fallbacks.
 *
 * Key concepts:
 * - PromptTarget: Which model/provider a variant is optimized for
 * - PromptVariant: A specific prompt template for a target
 * - PromptDefinition: A prompt with multiple variants
 * - PromptRegistry: Selects best variant for a given backend
 */

import type { LLMCapability } from '../shared/capabilities.js'

// ============================================
// Target Specification
// ============================================

/**
 * Prompt target specification.
 *
 * Hierarchy (most to least specific):
 * - 'anthropic:haiku' - Specific model family
 * - 'anthropic' - Provider (all Claude models)
 * - 'ollama:qwen3' - Specific Ollama model
 * - 'ollama' - All Ollama models
 * - '*' - Universal fallback
 *
 * Extensible for future providers (google, openai, etc.)
 */
export type PromptTarget =
  | '*' // Universal fallback
  | 'anthropic' // All Claude models
  | 'anthropic:opus' // Claude Opus family
  | 'anthropic:sonnet' // Claude Sonnet family
  | 'anthropic:haiku' // Claude Haiku family
  | 'ollama' // All Ollama models
  | `ollama:${string}` // Specific Ollama model (e.g., 'ollama:qwen3')
  | 'google' // Gemini (future)
  | `google:${string}` // Specific Gemini model
  | 'openai' // OpenAI (future)
  | `openai:${string}` // Specific OpenAI model
  | string // Extensible

/**
 * Parse a prompt target into provider and model components.
 */
export function parsePromptTarget(target: PromptTarget): {
  provider: string
  model?: string
} {
  if (target === '*') return { provider: '*' }

  const [provider, model] = target.split(':')
  return { provider: provider!, model }
}

/**
 * Calculate specificity score for a target (higher = more specific).
 * Used for variant selection priority.
 */
export function getTargetSpecificity(target: PromptTarget): number {
  if (target === '*') return 0
  if (target.includes(':')) return 2 // Provider + model
  return 1 // Provider only
}

// ============================================
// Prompt Variant
// ============================================

/**
 * A single prompt variant optimized for a specific target.
 */
export interface PromptVariant {
  /** Target model/provider this variant is optimized for */
  target: PromptTarget

  /** The prompt template with {{placeholders}} */
  template: string

  /**
   * Priority when multiple variants match (higher = preferred).
   * Use to prefer certain variants over others at same specificity level.
   *
   * Suggested ranges:
   * - 0-9: Fallback variants
   * - 10-19: Provider-level optimizations
   * - 20-29: Model-family optimizations
   * - 30+: Highly specialized variants
   */
  priority: number

  /**
   * Optional: Capabilities required to use this variant.
   * Variant is skipped if backend doesn't support all required capabilities.
   *
   * @example ['extended-thinking'] - Only for models with thinking
   * @example ['vision'] - Only for multimodal models
   */
  requiredCapabilities?: LLMCapability[]

  /**
   * Optional: Description of why this variant exists.
   * Useful for debugging and prompt engineering.
   */
  description?: string

  /**
   * Optional: Version string for tracking prompt iterations.
   */
  version?: string
}

// ============================================
// Prompt Definition
// ============================================

/**
 * A complete prompt definition with all its variants.
 */
export interface PromptDefinition {
  /** Unique identifier (e.g., 'qntm-generation', 'consolidation-classify') */
  id: string

  /** Human-readable description of what this prompt does */
  description: string

  /**
   * All variants for this prompt.
   * At minimum, should include a universal ('*') fallback.
   */
  variants: PromptVariant[]

  /**
   * Variable names expected in the template.
   * Used for validation and documentation.
   */
  variables?: string[]

  /**
   * Optional: Category for organization (e.g., 'qntm', 'consolidation', 'classification')
   */
  category?: string
}

// ============================================
// Rendered Prompt
// ============================================

/**
 * Result of rendering a prompt with variables.
 */
export interface RenderedPrompt {
  /** The final rendered prompt text */
  text: string

  /** Which variant was selected */
  variant: PromptVariant

  /** The prompt definition ID */
  promptId: string

  /** Variables that were substituted */
  variables: Record<string, string>
}

// ============================================
// Registry Types
// ============================================

/**
 * Backend info needed for variant selection.
 * Minimal interface to avoid tight coupling to LLMBackend.
 */
export interface PromptBackendInfo {
  /** Backend name (e.g., 'anthropic:haiku', 'ollama:qwen3') */
  name: string

  /** Capabilities this backend supports */
  capabilities: ReadonlySet<LLMCapability>
}

/**
 * Options for variant selection
 */
export interface VariantSelectionOptions {
  /**
   * Prefer variants with specific capabilities even if lower priority.
   * Useful when you want to leverage a capability if available.
   */
  preferCapabilities?: LLMCapability[]

  /**
   * Force a specific target (bypass automatic selection).
   * Useful for testing specific variants.
   */
  forceTarget?: PromptTarget
}

/**
 * Options for prompt rendering
 */
export interface RenderOptions extends VariantSelectionOptions {
  /**
   * Validate that all expected variables are provided.
   * Throws if a variable in the template is not in the variables object.
   * Default: true
   */
  validateVariables?: boolean

  /**
   * Allow extra variables not defined in template.
   * Default: true
   */
  allowExtraVariables?: boolean
}

// ============================================
// Template Utilities
// ============================================

/**
 * Extract variable names from a template.
 * Variables are in {{name}} format.
 *
 * @example extractVariables('Hello {{name}}, your score is {{score}}')
 * // Returns: ['name', 'score']
 */
export function extractVariables(template: string): string[] {
  const matches = template.match(/\{\{(\w+)\}\}/g)
  if (!matches) return []
  return [...new Set(matches.map((m) => m.slice(2, -2)))]
}

/**
 * Render a template with variables and special sections.
 * Replaces {{name}} with the corresponding value.
 * Supports {{SECTION_NAME}} for dynamic section loading (loaded via sections module).
 *
 * Note: This is synchronous. For async section loading, use the builders module.
 *
 * @param template - The template string
 * @param variables - Key-value pairs to substitute
 * @returns Rendered string
 *
 * @example renderTemplate('Hello {{name}}!', { name: 'World' })
 * // Returns: 'Hello World!'
 */
export function renderTemplate(template: string, variables: Record<string, string>): string {
  return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    return key in variables ? variables[key]! : match
  })
}

/**
 * Validate that all required variables are provided.
 *
 * @param template - The template string
 * @param variables - Provided variables
 * @returns Array of missing variable names (empty if all provided)
 */
export function validateVariables(template: string, variables: Record<string, string>): string[] {
  const required = extractVariables(template)
  return required.filter((v) => !(v in variables))
}

// ============================================
// Variant Selection Logic
// ============================================

/**
 * Match score for variant selection.
 * Higher is better.
 */
export interface VariantMatch {
  variant: PromptVariant
  /** Specificity of target match (0=universal, 1=provider, 2=model) */
  specificity: number
  /** User-defined priority from variant */
  priority: number
  /** Whether all required capabilities are met */
  capabilitiesMet: boolean
  /** Number of preferred capabilities matched (if preferCapabilities specified) */
  preferredCapabilityMatches: number
}

/**
 * Check if a variant's target matches a backend.
 *
 * @param target - Variant's target specification
 * @param backendName - Backend name (e.g., 'anthropic:haiku')
 * @returns true if target matches backend
 */
export function targetMatchesBackend(target: PromptTarget, backendName: string): boolean {
  if (target === '*') return true

  const { provider: targetProvider, model: targetModel } = parsePromptTarget(target)
  const [backendProvider, backendModel] = backendName.split(':')

  // Provider must match
  if (targetProvider !== backendProvider) return false

  // If target specifies model, it must match
  if (targetModel && backendModel) {
    return backendModel.toLowerCase().includes(targetModel.toLowerCase())
  }

  // Provider-only target matches any model of that provider
  return true
}

/**
 * Score a variant for selection.
 * Used to rank variants when multiple match.
 */
export function scoreVariant(
  variant: PromptVariant,
  backend: PromptBackendInfo,
  options?: VariantSelectionOptions
): VariantMatch | null {
  // Check if target matches backend
  if (!targetMatchesBackend(variant.target, backend.name)) {
    return null
  }

  // Check required capabilities
  const capabilitiesMet =
    !variant.requiredCapabilities ||
    variant.requiredCapabilities.every((cap) => backend.capabilities.has(cap))

  if (!capabilitiesMet) {
    return null // Skip variants with unmet capability requirements
  }

  // Count preferred capability matches
  let preferredCapabilityMatches = 0
  if (options?.preferCapabilities) {
    for (const cap of options.preferCapabilities) {
      if (variant.requiredCapabilities?.includes(cap)) {
        preferredCapabilityMatches++
      }
    }
  }

  return {
    variant,
    specificity: getTargetSpecificity(variant.target),
    priority: variant.priority,
    capabilitiesMet: true,
    preferredCapabilityMatches,
  }
}

/**
 * Compare two variant matches for sorting.
 * Returns negative if a should come before b.
 */
export function compareVariantMatches(a: VariantMatch, b: VariantMatch): number {
  // First: prefer variants with more preferred capability matches
  if (a.preferredCapabilityMatches !== b.preferredCapabilityMatches) {
    return b.preferredCapabilityMatches - a.preferredCapabilityMatches
  }

  // Second: prefer more specific targets
  if (a.specificity !== b.specificity) {
    return b.specificity - a.specificity
  }

  // Third: prefer higher priority
  return b.priority - a.priority
}

// ============================================
// Known Prompt IDs (for type safety)
// ============================================

/**
 * Known prompt IDs in the Atlas system.
 * Extend as prompts are added.
 */
export type KnownPromptId =
  // Task prompts
  | 'qntm-generation' // Generate QNTM semantic keys
  | 'consolidation-classify' // Classify chunk relationships
  | 'content-classify' // Classify content type (text/code/media)
  | 'compaction' // Working memory compaction
  | 'query-expansion' // QNTM query expansion
  // 3-role agent prompts
  | 'agent-sensor' // Sensor: perception + pattern recognition
  | 'agent-reasoner' // Reasoner: hypothesis generation + testing
  | 'agent-integrator' // Integrator: task execution + synthesis
  // 6-role agent prompts
  | 'agent-observer' // Observer: pure perception
  | 'agent-connector' // Connector: pattern recognition
  | 'agent-explainer' // Explainer: hypothesis generation
  | 'agent-challenger' // Challenger: falsification testing
  | 'agent-integrator-6role' // Integrator (6-role explicit)
  | 'agent-meta' // Meta: orchestration
  | string // Extensible

/**
 * QNTM abstraction levels for consolidation pipeline.
 * - L0 (Instance): Specific events, exact references, temporal anchors
 * - L1 (Topic): Deduplicated content, topic-level concepts
 * - L2 (Concept): Summarized knowledge, decontextualized facts
 * - L3 (Principle): Abstract patterns, transferable insights
 */
export type QNTMAbstractionLevel = 0 | 1 | 2 | 3

/**
 * Agent role type (supports both 3-role and 6-role models)
 */
export type AgentRole =
  // 3-role INTERSTITIA model
  | 'sensor' // Observer + Connector (perception + pattern clustering)
  | 'reasoner' // Explainer + Challenger (hypothesis + falsification)
  | 'integrator' // Task execution + synthesis
  // 6-role specialized model
  | 'observer' // Pure perception
  | 'connector' // Pattern recognition
  | 'explainer' // Hypothesis generation
  | 'challenger' // Falsification testing
  | 'integrator-6role' // Task execution (explicit 6-role)
  | 'meta' // Orchestration
