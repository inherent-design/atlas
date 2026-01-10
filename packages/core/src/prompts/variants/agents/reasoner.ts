/**
 * Reasoner Agent Prompt
 *
 * Consolidated from Explainer + Challenger roles.
 * - Explainer: Generate causal hypotheses ("X BECAUSE Y")
 * - Challenger: Falsification via adversarial testing
 *
 * Type 2 cognition: Hypothesize → Test → Refine
 */

import type { PromptDefinition } from '../../types'
import { loadTemplate } from '../../template-loader'

export const reasonerPrompt: PromptDefinition = {
  id: 'agent-reasoner',
  description: 'Reasoner agent: hypothesis generation and adversarial testing',
  category: 'agent',
  variables: ['task', 'context', 'observations', 'constraints'],
  variants: [
    {
      target: '*',
      priority: 0,
      description: 'Universal fallback',
      get template() {
        return loadTemplate(
          'agents/AGENT-REASONER.md',
          'Generate competing hypotheses, derive predictions, test via REFUTATION attempts.'
        )
      },
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      get template() {
        return loadTemplate(
          'agents/AGENT-REASONER-OLLAMA.md',
          'Hypothesize → Test to REFUTE → Report VALIDATED|REFUTED|INCONCLUSIVE.'
        )
      },
    },
  ],
}
