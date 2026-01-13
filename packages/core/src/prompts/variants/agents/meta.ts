/**
 * Meta Agent Prompt (6-role model)
 *
 * Orchestration agent coordinating multi-agent workflows.
 */

import type { PromptDefinition } from '../../types.js'
import { loadTemplate } from '../../template-loader.js'

export const metaPrompt: PromptDefinition = {
  id: 'agent-meta',
  description: 'Meta: Orchestration and workflow coordination',
  category: 'agent',
  variables: ['task', 'context'],
  variants: [
    {
      target: '*',
      priority: 0,
      get template() {
        return loadTemplate(
          'agents/AGENT-META.md',
          'Orchestrate multi-agent workflows: spawn agents, synthesize results, coordinate execution.'
        )
      },
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      get template() {
        return loadTemplate(
          'agents/AGENT-META-OLLAMA.md',
          'Coordinate agents, synthesize results. Flat hierarchy constraint.'
        )
      },
    },
  ],
}
