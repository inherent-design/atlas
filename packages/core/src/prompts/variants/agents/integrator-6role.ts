/**
 * Integrator Agent Prompt (6-role model)
 *
 * Task execution and synthesis. Cannot spawn sub-agents (flat hierarchy).
 */

import type { PromptDefinition } from '../../types.js'
import { loadTemplate } from '../../template-loader.js'

export const integrator6RolePrompt: PromptDefinition = {
  id: 'agent-integrator-6role',
  description: 'Integrator: Task executor (6-role, flat hierarchy terminal node)',
  category: 'agent',
  variables: ['task', 'context'],
  variants: [
    {
      target: '*',
      priority: 0,
      get template() {
        return loadTemplate(
          'agents/AGENT-INTEGRATOR-6ROLE.md',
          'Terminal-node task executor: analyze → plan → execute → validate → report (U4 protocol).'
        )
      },
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      get template() {
        return loadTemplate(
          'agents/AGENT-INTEGRATOR-6ROLE-OLLAMA.md',
          'Execute systematically. Terminal node. Never spawn sub-agents.'
        )
      },
    },
  ],
}
