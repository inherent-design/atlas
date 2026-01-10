/**
 * Integrator Agent Prompt
 *
 * Primary task executor and decision synthesizer.
 * Handles ANY task type through systematic decomposition.
 *
 * Terminal node: Cannot spawn sub-agents (flat hierarchy).
 */

import type { PromptDefinition } from '../../types'
import { loadTemplate } from '../../template-loader'

export const integratorPrompt: PromptDefinition = {
  id: 'agent-integrator',
  description: 'Integrator agent: task execution and synthesis',
  category: 'agent',
  variables: ['task', 'context', 'hypotheses', 'constraints'],
  variants: [
    {
      target: '*',
      priority: 0,
      description: 'Universal fallback',
      get template() {
        return loadTemplate(
          'agents/AGENT-INTEGRATOR.md',
          'Execute tasks systematically: analyze → plan → execute → validate → report.'
        )
      },
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      get template() {
        return loadTemplate(
          'agents/AGENT-INTEGRATOR-OLLAMA.md',
          'Execute tasks step-by-step, validate before claiming done.'
        )
      },
    },
  ],
}
