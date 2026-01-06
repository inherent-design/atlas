#!/usr/bin/env bun
/**
 * UserPromptSubmit hook: Search Atlas and inject relevant context
 *
 * Input (stdin): { prompt: string, session_id: string, transcript_path: string, cwd: string }
 * Output (stdout): { hookSpecificOutput: { hookEventName: "UserPromptSubmit", additionalContext: string } }
 *
 * Uses atlas-core directly to search for relevant context.
 */

import { search, loadConfig } from '@inherent.design/atlas-core'

interface HookInput {
  prompt: string
  session_id: string
  transcript_path: string
  cwd: string
}

async function main() {
  // Read input from stdin using Bun's native API
  let input: HookInput
  try {
    const data = await Bun.readableStreamToText(Bun.stdin.stream())
    input = JSON.parse(data)
  } catch {
    // Invalid input, exit silently
    process.exit(0)
  }

  // Skip if prompt is too short (trivial like "hi", "ok") or a slash command
  if (!input.prompt || input.prompt.length < 3 || input.prompt.startsWith('/')) {
    process.exit(0)
  }

  try {
    await loadConfig()

    // Search Atlas with the user's prompt
    const results = await search({
      query: input.prompt,
      limit: 3,
      rerank: false, // Keep it fast
    })

    if (results.length === 0) {
      process.exit(0) // No context to inject
    }

    // Format results as context
    const context = results
      .map((r, i) => `[Atlas Memory ${i + 1}] (${r.file_path}):\n${r.text}`)
      .join('\n\n---\n\n')

    // Output structured response
    const output = {
      hookSpecificOutput: {
        hookEventName: 'UserPromptSubmit',
        additionalContext: `\n\n<atlas-context>\nRelevant context from Atlas semantic memory:\n\n${context}\n</atlas-context>`,
      },
    }

    console.log(JSON.stringify(output))
  } catch (error) {
    // Silently fail - don't block user prompts
    // Could log to stderr for debugging: console.error(`Atlas search failed: ${error}`)
    process.exit(0)
  }
}

main()
