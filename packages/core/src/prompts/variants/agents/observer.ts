/**
 * Observer Agent Prompt (6-role model)
 *
 * Pure perception agent with Answer First format.
 * Templates loaded from external .md files at runtime.
 */

import type { PromptDefinition } from '../../types.js'
import { loadTemplate } from '../../template-loader.js'

export const observerPrompt: PromptDefinition = {
  id: 'agent-observer',
  description: 'Observer: Pure perception agent with Answer First format',
  category: 'agent',
  variables: ['task', 'context'],
  variants: [
    {
      target: '*',
      priority: 0,
      get template() {
        return loadTemplate(
          'agents/AGENT-OBSERVER.md',
          '# Observer (MOCK)\n\nRole: Observe facts without interpretation.\n\nTask: {{task}}\nContext: {{context}}'
        )
      },
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      get template() {
        return loadTemplate(
          'agents/AGENT-OBSERVER-OLLAMA.md',
          '# Observer (MOCK)\n\nObserve facts.\n\nTask: {{task}}\nContext: {{context}}'
        )
      },
    },
  ],
}
