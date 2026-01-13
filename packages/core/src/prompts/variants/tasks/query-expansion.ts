/**
 * Query Expansion Prompt
 *
 * Generates QNTM keys from search queries for semantic retrieval.
 */

import type { PromptDefinition } from '../../types.js'

export const queryExpansionPrompt: PromptDefinition = {
  id: 'query-expansion',
  description: 'Generate QNTM keys from search query for semantic retrieval',
  category: 'qntm',
  variables: ['query', 'existingKeys'],
  variants: [
    {
      target: '*',
      priority: 0,
      template: `# Query Semantic Expansion

Generate QNTM keys that would match content relevant to this query.
Think about what semantic concepts the user is trying to find.

## Query
"{{query}}"

## Existing Keys in Knowledge Base (sample)
{{existingKeys}}

## Instructions
1. Identify 2-4 semantic concepts the query is seeking
2. Generate QNTM keys that would MATCH stored content (not describe the query itself)
3. Consider synonyms and related concepts (vocabulary bridging)
4. Use existing key patterns when applicable

## Output Format
{
  "keys": ["subject ~ predicate ~ object", "..."],
  "reasoning": "Why these keys would help find relevant content"
}

## Examples
Query: "How do I handle authentication?"
Keys: ["security ~ pattern ~ authentication", "user ~ management ~ login", "session ~ strategy ~ jwt"]

Query: "What did we decide about the database?"
Keys: ["decision ~ topic ~ database", "architecture ~ choice ~ storage", "discussion ~ subject ~ persistence"]`,
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      template: `# Query Expansion

Query: "{{query}}"

Existing keys sample:
{{existingKeys}}

Generate 2-4 QNTM keys that would MATCH relevant content.

Output JSON:
{
  "keys": ["subject ~ predicate ~ object", "..."],
  "reasoning": "..."
}`,
    },
  ],
}
