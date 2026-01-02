/**
 * QNTM Generation Providers
 *
 * Domain-specific prompt building for QNTM key generation.
 * Uses llm/ module for actual LLM completions.
 */

import pRetry from 'p-retry'
import type { QNTMGenerationInput, QNTMGenerationResult } from '.'
import { getLLMBackendFor, type LLMConfig } from '.'
import { createLogger } from '../../shared/logger'

const log = createLogger('qntm/providers')

// Retry configuration for QNTM generation
const RETRY_OPTIONS = {
  retries: 3,
  factor: 2,
  minTimeout: 1000,
  maxTimeout: 8000,
  onFailedAttempt: (context: { error: Error; attemptNumber: number; retriesLeft: number }) => {
    log.warn('QNTM generation attempt failed, retrying...', {
      attemptNumber: context.attemptNumber,
      retriesLeft: context.retriesLeft,
      error: context.error.message,
    })
  },
}

// Re-export types for backwards compatibility
export type { LLMConfig as ProviderConfig, LLMProvider as QNTMProvider } from '.'

/**
 * Build QNTM generation prompt
 *
 * Uses QNTM language spec (EBNF) to ensure proper ternary relationship format.
 */
export function buildQNTMPrompt(input: QNTMGenerationInput): string {
  const { chunk, existingKeys, context } = input

  return `# QNTM Semantic Key Generation

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
${existingKeys.length > 0 ? existingKeys.map((k) => `- ${k}`).join('\n') : '(none yet)'}

${
  context?.fileName
    ? `## Context
File: ${context.fileName} (chunk ${context.chunkIndex}/${context.totalChunks})
`
    : ''
}## Chunk Text
\`\`\`
${chunk}
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
✗ Don't use vague predicates like "about" or "has"`
}

/**
 * Generate QNTM keys using specified provider
 */
export async function generateQNTMKeysWithProvider(
  input: QNTMGenerationInput,
  config: LLMConfig
): Promise<QNTMGenerationResult> {
  const prompt = buildQNTMPrompt(input)

  log.debug('Generating QNTM keys', {
    provider: config.provider,
    model: config.model,
    chunkLength: input.chunk.length,
    existingKeyCount: input.existingKeys.length,
  })

  // Get JSON-capable LLM backend from registry
  const backend = getLLMBackendFor('json-completion')
  if (!backend) {
    throw new Error('No JSON-capable LLM backend available for QNTM generation')
  }

  // Type-safe check for JSON completion capability
  if (!('completeJSON' in backend)) {
    throw new Error('Backend does not implement JSON completion')
  }

  log.debug('Using LLM backend for QNTM generation', { backend: backend.name })

  const result = await pRetry(
    () => backend.completeJSON<QNTMGenerationResult>(prompt),
    RETRY_OPTIONS
  )

  log.trace('QNTM generation result', { backend: backend.name, result })

  return result
}
