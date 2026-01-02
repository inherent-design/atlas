/**
 * Consolidation Classification Prompt
 *
 * Classifies the relationship between two similar chunks and determines
 * which to keep during consolidation.
 */

import type { PromptDefinition } from '../types'

export const consolidationClassificationPrompt: PromptDefinition = {
  id: 'consolidation-classify',
  description: 'Classify relationship between similar chunks for consolidation',
  category: 'consolidation',
  variables: ['text1', 'text2', 'keys1', 'keys2', 'created1', 'created2'],
  variants: [
    {
      target: '*',
      priority: 0,
      description: 'Universal fallback',
      template: `# Chunk Consolidation Classification

You are analyzing two similar text chunks to determine their relationship and how to consolidate them.

## Chunk 1 (created: {{created1}})
QNTM Keys: {{keys1}}
\`\`\`
{{text1}}
\`\`\`

## Chunk 2 (created: {{created2}})
QNTM Keys: {{keys2}}
\`\`\`
{{text2}}
\`\`\`

## Classification Types

1. **duplicate_work**: Same or nearly identical content created independently
   - Keep the more recent/complete version
   - Example: Same code snippet saved twice

2. **sequential_iteration**: Progressive refinement of the same concept
   - Shows evolution of an idea over time
   - Direction matters: forward (improvement) or backward (regression)
   - Example: Draft → revised → final versions

3. **contextual_convergence**: Different approaches arriving at similar insight
   - Different contexts but overlapping conclusions
   - Both perspectives may be valuable
   - Example: Same technique discovered in different projects

## Instructions

1. Compare the semantic content of both chunks
2. Consider timestamps to understand temporal relationship
3. Classify the relationship type
4. Determine which to keep or if they should be merged
5. Return ONLY valid JSON

## Output Format
{
  "type": "duplicate_work" | "sequential_iteration" | "contextual_convergence",
  "direction": "forward" | "backward" | "convergent" | "unknown",
  "reasoning": "1-2 sentence explanation",
  "keep": "first" | "second" | "merge"
}`,
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter context)',
      template: `Compare two text chunks and classify their relationship:

Chunk 1 ({{created1}}):
{{text1}}

Chunk 2 ({{created2}}):
{{text2}}

Types:
- duplicate_work: Same content, keep one
- sequential_iteration: Evolution over time (forward/backward)
- contextual_convergence: Different paths, similar insight

Return JSON:
{
  "type": "duplicate_work" | "sequential_iteration" | "contextual_convergence",
  "direction": "forward" | "backward" | "convergent" | "unknown",
  "reasoning": "brief explanation",
  "keep": "first" | "second" | "merge"
}`,
    },
  ],
}
