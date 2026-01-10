#!/usr/bin/env bun
/**
 * PreTaskSpawn hook: Inject project bootstrap and relevant context
 *
 * Input (stdin): { task_description: string, cwd: string, session_id: string }
 * Output (stdout): { hookSpecificOutput: { hookEventName: "PreTaskSpawn", additionalContext: string } }
 *
 * Injects both project bootstrap file and semantically relevant chunks from Atlas.
 */

import { AtlasConnection, isDaemonRunning } from '@inherent.design/atlas-core'
import { existsSync, readFileSync, readdirSync } from 'fs'
import { join } from 'path'

interface HookInput {
  task_description: string
  cwd: string
  session_id: string
}

interface SearchResult {
  text: string
  filePath: string
  score: number
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

  // Detect bootstrap file matching current project
  const bootstrapDir = join(process.env.HOME!, '.atlas', 'bootstrap')
  let bootstrapContent = ''

  if (existsSync(bootstrapDir)) {
    try {
      const files = readdirSync(bootstrapDir).filter((f) => f.endsWith('.md'))
      for (const file of files) {
        const content = readFileSync(join(bootstrapDir, file), 'utf-8')
        // Simple heuristic: check if cwd appears in bootstrap
        if (content.includes(input.cwd)) {
          bootstrapContent = content
          break
        }
      }
    } catch {
      // Silently fail - don't block task spawn
    }
  }

  // Search for task-relevant chunks from Atlas
  let relevantChunks = ''

  if (isDaemonRunning()) {
    try {
      const connection = new AtlasConnection()
      await connection.connect()

      const results = (await connection.request('atlas.search' as any, {
        query: input.task_description,
        limit: 5,
        rerank: false,
      })) as SearchResult[]

      connection.disconnect()

      // Pack within token budget (2000 tokens ~= 8000 chars)
      const TOKEN_BUDGET = 2000
      const CHARS_PER_TOKEN = 4
      const MAX_CHARS = TOKEN_BUDGET * CHARS_PER_TOKEN

      const packed: SearchResult[] = []
      let totalChars = 0

      for (const r of results) {
        const chars = r.text.length + r.filePath.length + 50 // +50 for formatting
        if (totalChars + chars > MAX_CHARS) {
          break // Budget exhausted
        }
        packed.push(r)
        totalChars += chars
      }

      relevantChunks = packed
        .map((r, i) => `[${i + 1}] ${r.filePath}:\n${r.text}`)
        .join('\n\n---\n\n')
    } catch {
      // Silently fail - daemon might not be available
    }
  }

  // Build context output
  let context = ''

  if (bootstrapContent) {
    context += `<atlas-project-bootstrap>\n${bootstrapContent}\n</atlas-project-bootstrap>\n\n`
  }

  if (relevantChunks) {
    context += `<atlas-relevant-context>\n${relevantChunks}\n</atlas-relevant-context>`
  }

  // Output structured response if we have context
  if (context) {
    const output = {
      hookSpecificOutput: {
        hookEventName: 'PreTaskSpawn',
        additionalContext: context,
      },
    }
    console.log(JSON.stringify(output))
  }

  process.exit(0)
}

main()
