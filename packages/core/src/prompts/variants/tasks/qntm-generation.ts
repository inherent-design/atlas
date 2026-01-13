/**
 * QNTM Key Generation Prompt
 *
 * Generates semantic triplet keys in format: subject ~ predicate ~ object
 */

import type { PromptDefinition } from '../../types.js'

export const qntmGenerationPrompt: PromptDefinition = {
  id: 'qntm-generation',
  description: 'Generate QNTM semantic keys for a text chunk',
  category: 'qntm',
  variables: [
    'chunk',
    'existingKeys',
    'contextFileName',
    'contextChunkIndex',
    'contextTotalChunks',
  ],
  variants: [
    {
      target: '*',
      priority: 0,
      description: 'Universal fallback',
      template: `# QNTM Semantic Key Generation

Generate stable semantic addresses (QNTM keys) using the QNTM relationship language.
Each key is a ternary relationship: subject ~ predicate ~ object

## QNTM Syntax (EBNF)
relationship = expression, "~", expression, "~", expression
expression   = concept | collection
concept      = identifier [ ":" value ]
collection   = "[" expression_list "]"

## Examples (from atlas.qntm)
memory ~ type ~ episodic
memory ~ type ~ semantic
database ~ strategy ~ indexing
database ~ property ~ persistent
retrieval ~ method ~ vector_search
content ~ domain ~ [machine_learning, systems_design]

## Existing Keys (REUSE when semantically close)
{{existingKeys}}

File: {{contextFileName}}
Chunk: {{contextChunkIndex}} of {{contextTotalChunks}}

## Chunk Text
\`\`\`
{{chunk}}
\`\`\`

## Instructions
1. **Identify 1-3 semantic concepts** in this chunk (main topics/themes)
2. **Check existing keys** - REUSE if semantically similar (don't create duplicates)
3. **Format as ternary relationships**: Always 3 parts separated by " ~ "
   - Subject: Core concept (e.g., "memory", "database", "algorithm")
   - Predicate: Relationship type (e.g., "type", "strategy", "property", "relates_to")
   - Object: Classification/value (e.g., "episodic", "indexing", "[concept1, concept2]")
4. **Use simple identifiers**: snake_case, no special chars except underscore
5. **Be stable**: Same semantic meaning → same key (invariant to rephrasing)
6. Return ONLY valid JSON

## Output Format
{
  "keys": ["subject ~ predicate ~ object", "..."],
  "reasoning": "1-2 sentence explanation of semantic choices"
}

## Quality Checks
✓ Each key has exactly 3 parts separated by " ~ "
✓ Identifiers use snake_case (no @, no spaces)
✓ Keys are semantically meaningful (not just generic)
✓ Reused existing keys when concepts overlap
✗ Don't create near-duplicates of existing keys
✗ Don't use vague predicates like "about" or "has"`,
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter context)',
      template: `Extract semantic triplets: subject ~ predicate ~ object

QNTM Syntax: relationship = subject ~ predicate ~ object
Examples:
- memory ~ type ~ episodic
- database ~ strategy ~ indexing
- retrieval ~ method ~ vector_search

Existing keys (REUSE):
{{existingKeys}}

Text:
\`\`\`
{{chunk}}
\`\`\`

Generate 1-3 QNTM keys. Return JSON:
{
  "keys": ["subject ~ predicate ~ object"],
  "reasoning": "brief explanation"
}

Rules:
- 3 parts separated by " ~ "
- snake_case identifiers
- Reuse existing keys when similar
- Be semantically specific`,
    },
  ],
}
