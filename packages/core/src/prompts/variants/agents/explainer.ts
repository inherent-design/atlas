/**
 * Explainer Agent Prompt (6-role model)
 *
 * Causal hypothesis generator building "X BECAUSE Y" explanations.
 * Templates loaded from external .md files at runtime.
 */

import type { PromptDefinition } from '../../types'
import { loadTemplate } from '../../template-loader'

export const explainerPrompt: PromptDefinition = {
  id: 'agent-explainer',
  description: 'Explainer: Hypothesis generation with falsifiable predictions',
  category: 'agent',
  variables: ['task', 'context'],
  variants: [
    {
      target: '*',
      priority: 0,
      get template() {
        return loadTemplate(
          'agents/AGENT-EXPLAINER.md',
          '# Explainer (MOCK)\n\nGenerate 2-3 competing hypotheses.\n\nTask: {{task}}\nContext: {{context}}'
        )
      },
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      get template() {
        return loadTemplate(
          'agents/AGENT-EXPLAINER-OLLAMA.md',
          '# Explainer (MOCK)\n\nGenerate hypotheses.\n\nTask: {{task}}\nContext: {{context}}'
        )
      },
    },
  ],
}
