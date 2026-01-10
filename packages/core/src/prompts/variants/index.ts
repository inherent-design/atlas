/**
 * Prompt Variants Index
 *
 * Register all prompt definitions here.
 */

import { promptRegistry } from '../registry'

// Import all agent prompts
import {
  observerPrompt,
  connectorPrompt,
  explainerPrompt,
  challengerPrompt,
  integrator6RolePrompt,
  metaPrompt,
  sensorPrompt,
  reasonerPrompt,
  integratorPrompt,
} from './agents'

// Import all task prompts
import {
  qntmGenerationPrompt,
  queryExpansionPrompt,
  consolidationClassificationPrompt,
  compactionPrompt,
} from './tasks'

// Lazy registration flag
let registered = false

// Register all prompts (called explicitly by production entry points)
export function registerPrompts(): void {
  // Guard against double registration
  if (registered) {
    return
  }

  // 6-role agent prompts
  promptRegistry.register(observerPrompt)
  promptRegistry.register(connectorPrompt)
  promptRegistry.register(explainerPrompt)
  promptRegistry.register(challengerPrompt)
  promptRegistry.register(integrator6RolePrompt)
  promptRegistry.register(metaPrompt)

  // 3-role agent prompts
  promptRegistry.register(sensorPrompt)
  promptRegistry.register(reasonerPrompt)
  promptRegistry.register(integratorPrompt)

  // Task prompts
  promptRegistry.register(qntmGenerationPrompt)
  promptRegistry.register(queryExpansionPrompt)
  promptRegistry.register(consolidationClassificationPrompt)
  promptRegistry.register(compactionPrompt)

  registered = true
}

// REMOVED: Auto-register on import
// Previously this line caused 1.5GB heap allocation per Vitest worker
// Now consumers must call registerPrompts() explicitly at startup

// Re-export for direct access
export * from './agents'
export * from './tasks'
