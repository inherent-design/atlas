#!/usr/bin/env tsx
/**
 * PreToolUse hook: Inject project bootstrap and relevant context for Task spawns
 *
 * Input (stdin): PreToolUse format with tool_name: "Task"
 * Output (stdout): { hookSpecificOutput: { hookEventName: "PreToolUse", additionalContext: string } }
 *
 * Injects both project bootstrap file and semantically relevant chunks from Atlas.
 */

import {
  AtlasConnection,
  isDaemonRunning,
  loadConfig,
  getApplicationService,
} from '@inherent.design/atlas-core'
import { existsSync, readFileSync, readdirSync } from 'fs'
import { join } from 'path'

interface HookInput {
  session_id: string
  transcript_path: string
  cwd: string
  permission_mode: string
  hook_event_name: string
  tool_name: string
  tool_input: {
    description?: string
    prompt: string
    subagent_type?: string
  }
  tool_use_id: string
}

interface SearchResult {
  text: string
  filePath: string
  score: number
}

/** Read stdin using Node.js streams */
async function readStdin(): Promise<string> {
  const chunks: Buffer[] = []
  for await (const chunk of process.stdin) {
    chunks.push(chunk)
  }
  return Buffer.concat(chunks).toString('utf-8')
}

async function main() {
  // Read input from stdin
  let input: HookInput
  try {
    const data = await readStdin()
    input = JSON.parse(data)
  } catch {
    // Invalid input, exit silently
    process.exit(0)
  }

  // Only run for Task tool
  if (input.tool_name !== 'Task') {
    process.exit(0)
  }

  // Extract task description from prompt and description
  const taskDescription = input.tool_input.description
    ? `${input.tool_input.description}\n\n${input.tool_input.prompt}`
    : input.tool_input.prompt

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
  let searchResults: SearchResult[] = []

  // Try daemon first
  if (isDaemonRunning()) {
    try {
      const connection = new AtlasConnection()
      await connection.connect()

      searchResults = (await connection.request('atlas.search' as any, {
        query: taskDescription,
        limit: 5,
        rerank: false,
      })) as SearchResult[]

      connection.disconnect()
    } catch {
      // Silently fail - will try direct search
    }
  }

  // Fallback: direct search (daemon not running or failed)
  if (searchResults.length === 0) {
    try {
      // Load config
      const config = await loadConfig()

      // Get ApplicationService singleton
      const app = getApplicationService(config)

      // Initialize storage and backends (matches CLI pattern)
      await app.initialize()

      // Search via ApplicationService
      const directResults = await app.search({
        query: taskDescription,
        limit: 5,
        rerank: false,
      })

      searchResults = directResults.map((r: any) => ({
        text: r.text,
        filePath: r.file_path,
        score: r.score,
      }))
    } catch {
      // Silently fail - don't block task spawn
    }
  }

  // Pack results within token budget if we got any
  if (searchResults.length > 0) {
    // Pack within token budget (2000 tokens ~= 8000 chars)
    const TOKEN_BUDGET = 2000
    const CHARS_PER_TOKEN = 4
    const MAX_CHARS = TOKEN_BUDGET * CHARS_PER_TOKEN

    const packed: SearchResult[] = []
    let totalChars = 0

    for (const r of searchResults) {
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
        hookEventName: 'PreToolUse',
        additionalContext: context,
      },
    }
    console.log(JSON.stringify(output))
  }

  process.exit(0)
}

main()
