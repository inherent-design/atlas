/**
 * Sensor Agent Prompt
 *
 * Consolidated from Observer + Connector roles.
 * - Observer: Pure perception, exhaust sensory modality
 * - Connector: Pattern clustering via similarity
 *
 * Type 0+1 cognition: Perception → Patterns (no causation)
 * Templates loaded from external .md files at runtime.
 */

import type { PromptDefinition } from '../../types'
import { loadTemplate } from '../../template-loader'

export const sensorPrompt: PromptDefinition = {
  id: 'agent-sensor',
  description: 'Sensor agent: perception and pattern recognition without interpretation',
  category: 'agent',
  variables: ['task', 'context', 'constraints'],
  variants: [
    {
      target: '*',
      priority: 0,
      description: 'Universal fallback',
      get template() {
        return loadTemplate(
          'agents/AGENT-SENSOR.md',
          '# Sensor (MOCK)\n\nObserve and cluster patterns.\n\nTask: {{task}}\nContext: {{context}}\nConstraints: {{constraints}}'
        )
      },
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      get template() {
        return loadTemplate(
          'agents/AGENT-SENSOR-OLLAMA.md',
          '# Sensor (MOCK)\n\nObserve + cluster.\n\nTask: {{task}}\nContext: {{context}}\nConstraints: {{constraints}}'
        )
      },
    },
  ],
}
