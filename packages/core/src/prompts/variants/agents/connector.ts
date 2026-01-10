/**
 * Connector Agent Prompt (6-role model)
 *
 * Pattern recognition via embedding similarity.
 * Templates loaded from external .md files at runtime.
 */

import type { PromptDefinition } from '../../types'
import { loadTemplate } from '../../template-loader'

export const connectorPrompt: PromptDefinition = {
  id: 'agent-connector',
  description: 'Connector: Pattern recognition and clustering',
  category: 'agent',
  variables: ['task', 'context'],
  variants: [
    {
      target: '*',
      priority: 0,
      get template() {
        return loadTemplate(
          'agents/AGENT-CONNECTOR.md',
          '# Connector (MOCK)\n\nFind patterns without explaining why.\n\nTask: {{task}}\nContext: {{context}}'
        )
      },
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      get template() {
        return loadTemplate(
          'agents/AGENT-CONNECTOR-OLLAMA.md',
          '# Connector (MOCK)\n\nFind patterns.\n\nTask: {{task}}\nContext: {{context}}'
        )
      },
    },
  ],
}
