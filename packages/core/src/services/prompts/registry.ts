/**
 * Prompt Registry
 *
 * Centralized prompt management with variant selection.
 */

import type {
  PromptDefinition,
  PromptVariant,
  PromptBackendInfo,
  RenderedPrompt,
  RenderOptions,
} from './types'
import { scoreVariant, compareVariantMatches, renderTemplate, validateVariables } from './types'
import { createLogger } from '../../shared/logger'

const log = createLogger('prompts:registry')

class PromptRegistry {
  private prompts = new Map<string, PromptDefinition>()

  register(definition: PromptDefinition): void {
    if (this.prompts.has(definition.id)) {
      log.warn('Overwriting prompt definition', { id: definition.id })
    }
    this.prompts.set(definition.id, definition)
    log.trace('Prompt registered', { id: definition.id, variants: definition.variants.length })
  }

  get(id: string): PromptDefinition | undefined {
    return this.prompts.get(id)
  }

  selectVariant(
    id: string,
    backend: PromptBackendInfo,
    options?: RenderOptions
  ): PromptVariant | undefined {
    const definition = this.prompts.get(id)
    if (!definition) {
      log.error('Prompt not found', { id })
      return undefined
    }

    // Force specific target if requested
    if (options?.forceTarget) {
      return definition.variants.find((v) => v.target === options.forceTarget)
    }

    // Score and sort variants
    const matches = definition.variants
      .map((v) => scoreVariant(v, backend, options))
      .filter((m): m is NonNullable<typeof m> => m !== null)
      .sort(compareVariantMatches)

    if (matches.length === 0) {
      log.warn('No matching variant found', { id, backend: backend.name })
      return undefined
    }

    return matches[0]!.variant
  }

  render(
    id: string,
    variables: Record<string, string>,
    backend: PromptBackendInfo,
    options?: RenderOptions
  ): RenderedPrompt | undefined {
    const variant = this.selectVariant(id, backend, options)
    if (!variant) return undefined

    // Validate variables if requested
    if (options?.validateVariables !== false) {
      const missing = validateVariables(variant.template, variables)
      if (missing.length > 0) {
        log.error('Missing template variables', { id, missing })
        return undefined
      }
    }

    const text = renderTemplate(variant.template, variables)

    return {
      text,
      variant,
      promptId: id,
      variables,
    }
  }

  list(): string[] {
    return Array.from(this.prompts.keys())
  }
}

// Global registry instance
export const promptRegistry = new PromptRegistry()

// Convenience function for rendering
export function renderPrompt(
  id: string,
  variables: Record<string, string>,
  backend: PromptBackendInfo,
  options?: RenderOptions
): string | undefined {
  return promptRegistry.render(id, variables, backend, options)?.text
}
