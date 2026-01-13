/**
 * Working Memory Compaction Prompt
 *
 * Compacts conversation into structured episodic memories.
 */

import type { PromptDefinition } from '../../types.js'

export const compactionPrompt: PromptDefinition = {
  id: 'compaction',
  description: 'Compact working memory (conversation) into episodic chunks',
  category: 'memory',
  variables: ['conversation'],
  variants: [
    {
      target: '*',
      priority: 0,
      template: `# Working Memory Compaction

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
✗ Don't omit user-stated constraints or preferences

## Conversation to Compact

{{conversation}}`,
    },
    {
      target: 'ollama',
      priority: 10,
      description: 'Ollama-optimized (shorter)',
      template: `# Compact Conversation

Extract essential information:

Output JSON:
{
  "summary": "...",
  "completed": ["..."],
  "in_progress": ["..."],
  "next_steps": ["..."],
  "decisions": ["..."],
  "context": { "files_involved": [], "key_concepts": [], "user_preferences": [] }
}

Guidelines:
- Concise but complete
- Preserve actionable details
- Include specific paths/names/errors
- Preserve user preferences verbatim

Conversation:
{{conversation}}`,
    },
  ],
}
