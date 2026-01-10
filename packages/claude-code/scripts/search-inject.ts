#!/usr/bin/env bun
/**
 * UserPromptSubmit hook: Search Atlas and inject relevant context
 *
 * Input (stdin): { prompt: string, session_id: string, transcript_path: string, cwd: string }
 * Output (stdout): { hookSpecificOutput: { hookEventName: "UserPromptSubmit", additionalContext: string } }
 *
 * Routes through daemon when available (pull methodology), falls back to direct.
 */

import {
  AtlasConnection,
  isDaemonRunning,
  search,
  loadConfig,
} from '@inherent.design/atlas-core'
import { existsSync, readdirSync, readFileSync } from 'fs'
import { join } from 'path'

interface HookInput {
  prompt: string
  session_id: string
  transcript_path: string
  cwd: string
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

  // Skip if prompt is too short (trivial like "hi", "ok") or a slash command
  if (!input.prompt || input.prompt.length < 3 || input.prompt.startsWith('/')) {
    process.exit(0)
  }

  try {
    let results: SearchResult[] = []

    // Try daemon first (pull methodology)
    if (isDaemonRunning()) {
      try {
        const connection = new AtlasConnection()
        await connection.connect()

        const daemonResults = (await connection.request('atlas.search' as any, {
          query: input.prompt,
          limit: 3,
          rerank: false,
          sessionId: input.session_id,
        })) as SearchResult[]

        connection.disconnect()

        results = daemonResults
      } catch {
        // Daemon connection failed, fall through to direct
      }
    }

    // Fallback: direct search (daemon not running or failed)
    if (results.length === 0) {
      await loadConfig()

      const directResults = await search({
        query: input.prompt,
        limit: 3,
        rerank: false,
      })

      results = directResults.map((r) => ({
        text: r.text,
        filePath: r.file_path,
        score: r.score,
      }))
    }

    if (results.length === 0) {
      process.exit(0) // No context to inject
    }

    // Pack results within token budget (2000 tokens ~= 8000 chars)
    const TOKEN_BUDGET = 2000
    const CHARS_PER_TOKEN = 4
    const MAX_CHARS = TOKEN_BUDGET * CHARS_PER_TOKEN

    const packedResults: SearchResult[] = []
    let totalChars = 0

    for (const result of results) {
      const resultChars = result.text.length + result.filePath.length + 50 // +50 for formatting
      if (totalChars + resultChars > MAX_CHARS) {
        break // Budget exhausted
      }
      packedResults.push(result)
      totalChars += resultChars
    }

    // Format packed results as context
    const context = packedResults
      .map((r, i) => `[Atlas Memory ${i + 1}] (${r.filePath}):\n${r.text}`)
      .join('\n\n---\n\n')

    // Auto-detection: Check if cwd has bootstrap and start auto-watch if needed
    try {
      const bootstrapDir = join(process.env.HOME!, '.atlas', 'bootstrap')
      if (existsSync(bootstrapDir)) {
        const files = readdirSync(bootstrapDir).filter((f) => f.endsWith('.md'))
        for (const file of files) {
          const content = readFileSync(join(bootstrapDir, file), 'utf-8')
          if (content.includes(input.cwd)) {
            // Found bootstrap for current project
            // Check if already watching via daemon
            if (isDaemonRunning()) {
              try {
                const connection = new AtlasConnection()
                await connection.connect()

                const status = (await connection.request(
                  'atlas.ingest.status' as any,
                  {}
                )) as any

                // Check if any task is watching this cwd
                const watching = status.tasks.some(
                  (t: any) => t.watching && t.paths.includes(input.cwd)
                )

                if (!watching) {
                  // Start auto-watch
                  await connection.request('atlas.ingest.start' as any, {
                    paths: [input.cwd],
                    recursive: true,
                    watch: true,
                  })
                }

                connection.disconnect()
              } catch {
                // Silently fail
              }
            }
            break
          }
        }
      }
    } catch {
      // Silently fail - don't block search injection
    }

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
