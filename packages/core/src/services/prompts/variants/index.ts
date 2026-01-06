/**
 * Prompt Variants Index
 *
 * Register all prompt definitions here.
 */

import { promptRegistry } from '../registry'
import { qntmGenerationPrompt } from './qntm-generation'
import { consolidationClassificationPrompt } from './consolidation-classification'
import { sensorPrompt } from './sensor'
import { reasonerPrompt } from './reasoner'
import { integratorPrompt } from './integrator'

// Register all prompts
export function registerPrompts(): void {
  // Task prompts
  promptRegistry.register(qntmGenerationPrompt)
  promptRegistry.register(consolidationClassificationPrompt)

  // Agent prompts
  promptRegistry.register(sensorPrompt)
  promptRegistry.register(reasonerPrompt)
  promptRegistry.register(integratorPrompt)
}

// Auto-register on import
registerPrompts()

// Re-export for direct access
export { qntmGenerationPrompt, consolidationClassificationPrompt }
export { sensorPrompt, reasonerPrompt, integratorPrompt }
