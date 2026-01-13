/**
 * Challenger Agent Prompt (6-role model)
 *
 * Hypothesis falsification via adversarial testing with uncertainty tracking.
 */

import type { PromptDefinition } from '../../types.js'
import { loadTemplate } from '../../template-loader.js'

export const challengerPrompt: PromptDefinition = {
  id: 'agent-challenger',
  description: 'Challenger: Hypothesis falsification with uncertainty bounds',
  category: 'agent',
  variables: ['task', 'context'],
  variants: [
    {
      target: '*',
      priority: 0,
      get template() {
        return loadTemplate(
          'agents/AGENT-CHALLENGER.md',
          'Test hypotheses via adversarial experiments to REFUTE predictions.'
        )
      },
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      get template() {
        return loadTemplate(
          'agents/AGENT-CHALLENGER-OLLAMA.md',
          'Test hypotheses to REFUTE them. Report VALIDATED|REFUTED|INCONCLUSIVE.'
        )
      },
    },
  ],
}
