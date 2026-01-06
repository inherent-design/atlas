/**
 * Atlas Prompt Registry
 *
 * Centralized prompts for LLM operations across Atlas.
 * Each prompt is designed for a specific abstraction level or task.
 */

// ============================================
// QNTM Key Generation Prompts (by abstraction level)
// ============================================

/**
 * QNTM abstraction levels:
 * - L0 (Instance): Specific events, exact references, temporal anchors
 * - L1 (Topic): Deduplicated content, topic-level concepts
 * - L2 (Concept): Summarized knowledge, decontextualized facts
 * - L3 (Principle): Abstract patterns, transferable insights
 */
export type QNTMAbstractionLevel = 0 | 1 | 2 | 3

/**
 * Level-specific instructions for QNTM key generation.
 * Each level targets a different abstraction granularity.
 */
export const QNTM_LEVEL_INSTRUCTIONS: Record<QNTMAbstractionLevel, string> = {
  0: `## Abstraction Level: L0 (Instance)
Generate SPECIFIC, instance-level keys that anchor to concrete events or references.
- Include temporal markers when relevant (dates, versions, sessions)
- Reference specific files, functions, or entities by name
- Capture the "what happened" not the "what it means"

Examples:
  conversation ~ instance ~ "2026-01-02_auth_discussion"
  file ~ modified ~ "src/auth/login.ts"
  decision ~ made ~ "use_jwt_over_sessions"
  error ~ encountered ~ "qdrant_connection_timeout"`,

  1: `## Abstraction Level: L1 (Topic)
Generate TOPIC-level keys that group related instances without specific details.
- Abstract away timestamps and specific identifiers
- Focus on the subject matter, not the specific occurrence
- Suitable for "what topics does this cover?"

Examples:
  memory ~ topic ~ authentication_patterns
  codebase ~ area ~ user_management
  discussion ~ subject ~ database_architecture
  work ~ category ~ bug_fixes`,

  2: `## Abstraction Level: L2 (Concept)
Generate CONCEPT-level keys that capture decontextualized knowledge.
- Remove all temporal and instance-specific references
- Focus on transferable facts and relationships
- Suitable for "what do I know about X?"

Examples:
  security ~ concept ~ defense_in_depth
  architecture ~ pattern ~ event_sourcing
  memory ~ strategy ~ hierarchical_consolidation
  retrieval ~ method ~ hybrid_search`,

  3: `## Abstraction Level: L3 (Principle)
Generate PRINCIPLE-level keys that capture abstract, transferable insights.
- Maximum abstraction: domain-agnostic patterns
- Focus on "lessons learned" and generalizable rules
- Suitable for "what patterns apply here?"

Examples:
  design ~ principle ~ separation_of_concerns
  optimization ~ tradeoff ~ latency_vs_throughput
  system ~ invariant ~ eventual_consistency
  learning ~ insight ~ constraints_drive_innovation`,
}

/**
 * Build QNTM generation prompt for a specific abstraction level.
 */
export function buildQNTMPrompt(
  chunk: string,
  existingKeys: string[],
  level: QNTMAbstractionLevel,
  context?: {
    fileName?: string
    chunkIndex?: number
    totalChunks?: number
  }
): string {
  return `# QNTM Semantic Key Generation

Generate stable semantic addresses (QNTM keys) using the QNTM relationship language.
Each key is a ternary relationship: subject ~ predicate ~ object

## QNTM Syntax (EBNF)
relationship = expression, "~", expression, "~", expression
expression   = concept | collection
concept      = identifier [ ":" value ]
collection   = "[" expression_list "]"

${QNTM_LEVEL_INSTRUCTIONS[level]}

## Existing Keys (REUSE when semantically close)
${
  existingKeys.length > 0
    ? existingKeys
        .slice(-50)
        .map((k) => `- ${k}`)
        .join('\n')
    : '(none yet)'
}

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
1. **Identify 1-3 semantic concepts** appropriate for L${level} abstraction
2. **Check existing keys** - REUSE if semantically similar (don't create duplicates)
3. **Format as ternary relationships**: Always 3 parts separated by " ~ "
   - Subject: Core concept (e.g., "memory", "architecture", "design")
   - Predicate: Relationship type (e.g., "type", "pattern", "principle")
   - Object: Classification/value appropriate for this abstraction level
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
✓ Keys match L${level} abstraction (${['instance', 'topic', 'concept', 'principle'][level]}-level)
✓ Reused existing keys when concepts overlap
✗ Don't create near-duplicates of existing keys
✗ Don't use vague predicates like "about" or "has"`
}

// ============================================
// Working Memory Compaction Prompt
// ============================================

/**
 * Prompt for compacting working memory (conversation) into episodic chunks.
 * Inspired by Claude Code's /compact and similar tools.
 *
 * Key insight from research: All tools converge on:
 * completed work → current state → next steps → constraints/decisions
 */
export const WORKING_MEMORY_COMPACTION_PROMPT = `# Working Memory Compaction

You are compacting a conversation into structured episodic memories for long-term storage.
This compacted memory will be the ONLY context available when the conversation continues.

## Your Task
Extract the essential information that would allow an agent to:
1. Understand what was accomplished
2. Know the current state of any work in progress
3. Identify clear next steps
4. Remember key decisions, constraints, and user preferences

## Input Format
You will receive raw conversation turns (user/assistant messages).

## Output Format
Return a JSON object with structured memories:

{
  "summary": "1-2 sentence overview of what this conversation was about",
  "completed": [
    "Specific accomplishment #1",
    "Specific accomplishment #2"
  ],
  "in_progress": [
    "Work item currently underway (with current state)"
  ],
  "next_steps": [
    "Clear, actionable next step"
  ],
  "decisions": [
    "Key decision: chose X over Y because Z"
  ],
  "context": {
    "files_involved": ["path/to/file.ts"],
    "key_concepts": ["concept1", "concept2"],
    "user_preferences": ["preference expressed by user"]
  },
  "verbatim_quotes": [
    "Any critical direct quotes that must be preserved exactly"
  ]
}

## Guidelines
- Be CONCISE but COMPLETE - this is the only record
- Preserve critical information, not every detail
- Focus on ACTIONABLE information
- Include specific file paths, function names, error messages
- Preserve user preferences and constraints VERBATIM
- If work is in progress, capture the CURRENT STATE precisely

## Anti-patterns
✗ Don't include pleasantries or conversation filler
✗ Don't summarize to the point of losing actionable detail
✗ Don't lose specific technical details (versions, configs, etc.)
✗ Don't omit user-stated constraints or preferences`

/**
 * Build working memory compaction prompt with conversation.
 */
export function buildCompactionPrompt(
  conversation: Array<{ role: string; content: string }>
): string {
  const formattedConversation = conversation
    .map((turn) => `[${turn.role.toUpperCase()}]\n${turn.content}`)
    .join('\n\n---\n\n')

  return `${WORKING_MEMORY_COMPACTION_PROMPT}

## Conversation to Compact

${formattedConversation}

## Output
Return ONLY valid JSON matching the format above.`
}

// ============================================
// Consolidation Classification Prompt
// ============================================

/**
 * Prompt for classifying relationship between two chunks during consolidation.
 * Used in consolidate/index.ts
 */
export function buildConsolidationPrompt(
  text1: string,
  text2: string,
  keys1: string[],
  keys2: string[],
  created1: string,
  created2: string,
  level1: number,
  level2: number
): string {
  return `# Chunk Consolidation Classification

You are analyzing two similar text chunks to determine their relationship and how to consolidate them.

## Chunk 1 (level: L${level1}, created: ${created1})
QNTM Keys: ${keys1.join(', ')}
\`\`\`
${text1}
\`\`\`

## Chunk 2 (level: L${level2}, created: ${created2})
QNTM Keys: ${keys2.join(', ')}
\`\`\`
${text2}
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
  "keep": "first" | "second" | "merge",
  "merged_summary": "If keep=merge, provide a summary that combines both (optional)"
}`
}

// ============================================
// Query Expansion Prompt (for search-time QNTM)
// ============================================

/**
 * Prompt for generating QNTM keys from a search query.
 * Used to bridge vocabulary gap between query and stored content.
 */
export function buildQueryExpansionPrompt(query: string, existingKeys: string[]): string {
  return `# Query Semantic Expansion

Generate QNTM keys that would match content relevant to this query.
Think about what semantic concepts the user is trying to find.

## Query
"${query}"

## Existing Keys in Knowledge Base (sample)
${existingKeys
  .slice(0, 30)
  .map((k) => `- ${k}`)
  .join('\n')}

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
Keys: ["decision ~ topic ~ database", "architecture ~ choice ~ storage", "discussion ~ subject ~ persistence"]`
}
