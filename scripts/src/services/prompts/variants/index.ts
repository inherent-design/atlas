/**
 * Prompt Variants Index
 *
 * Register all prompt definitions here.
 */

import { promptRegistry } from '../registry'
import { qntmGenerationPrompt } from './qntm-generation'
import { consolidationClassificationPrompt } from './consolidation-classification'

// Register all prompts
export function registerPrompts(): void {
  promptRegistry.register(qntmGenerationPrompt)
  promptRegistry.register(consolidationClassificationPrompt)
}

// Auto-register on import
registerPrompts()

// Re-export for direct access
export { qntmGenerationPrompt, consolidationClassificationPrompt }
