#!/usr/bin/env tsx
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
  loadConfig,
  getApplicationService,
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

interface TranscriptMessage {
  role: 'user' | 'assistant'
  content: string | Array<{ type: string; text?: string; thinking?: string }>
}

/** Read stdin using Node.js streams */
async function readStdin(): Promise<string> {
  const chunks: Buffer[] = []
  for await (const chunk of process.stdin) {
    chunks.push(chunk)
  }
  return Buffer.concat(chunks).toString('utf-8')
}

/** Extract last assistant message from transcript for context */
function getLastAssistantMessage(transcriptPath: string): string | null {
  try {
    if (!existsSync(transcriptPath)) {
      return null
    }

    const transcriptContent = readFileSync(transcriptPath, 'utf-8')
    const lines = transcriptContent.trim().split('\n').filter(Boolean)

    // Parse JSONL in reverse to find last assistant message
    for (let i = lines.length - 1; i >= 0; i--) {
      try {
        const line = lines[i]
        if (!line) continue
        const entry = JSON.parse(line)

        // Look for assistant messages (skip tool results and system messages)
        if (entry.message && entry.message.role === 'assistant') {
          const content = entry.message.content

          // Extract text from content array or string
          if (Array.isArray(content)) {
            // Find text blocks (skip thinking blocks, tool uses, etc.)
            const textBlocks = content
              .filter((block: any) => block.type === 'text' && block.text)
              .map((block: any) => block.text)
              .join('\n')

            if (textBlocks.trim().length > 0) {
              // Truncate to reasonable size (max 500 chars for search context)
              return textBlocks.trim().slice(0, 500)
            }
          } else if (typeof content === 'string') {
            return content.trim().slice(0, 500)
          }
        }
      } catch {
        // Skip malformed lines
        continue
      }
    }

    return null
  } catch (error) {
    console.error('[search-inject] Failed to read transcript:', (error as Error).message)
    return null
  }
}

async function main() {
  console.error('[search-inject] Hook started')

  // Read input from stdin
  let input: HookInput
  try {
    const data = await readStdin()
    input = JSON.parse(data)
    console.error('[search-inject] Input parsed:', {
      promptLength: input.prompt?.length,
      sessionId: input.session_id,
    })
  } catch (error) {
    // Invalid input, exit silently
    console.error('[search-inject] Failed to parse input:', (error as Error).message)
    process.exit(0)
  }

  // Skip if prompt is too short (trivial like "hi", "ok") or a slash command
  if (!input.prompt || input.prompt.length < 3 || input.prompt.startsWith('/')) {
    console.error('[search-inject] Skipping:', {
      reason: input.prompt?.startsWith('/') ? 'slash command' : 'too short',
      length: input.prompt?.length,
    })
    process.exit(0)
  }

  try {
    // Extract last assistant message for context
    const lastAssistantMsg = getLastAssistantMessage(input.transcript_path)
    console.error('[search-inject] Last assistant context:', {
      hasContext: !!lastAssistantMsg,
      contextLength: lastAssistantMsg?.length ?? 0,
    })

    // Build enriched query: prepend last assistant message if available
    const enrichedQuery = lastAssistantMsg
      ? `${lastAssistantMsg}\n\nUser follow-up: ${input.prompt}`
      : input.prompt

    console.error('[search-inject] Query enrichment:', {
      originalLength: input.prompt.length,
      enrichedLength: enrichedQuery.length,
      contextAdded: !!lastAssistantMsg,
    })

    let results: SearchResult[] = []
    let searchMethod: 'daemon' | 'direct' | 'none' = 'none'

    // Try daemon first (pull methodology)
    if (isDaemonRunning()) {
      console.error('[search-inject] Daemon running, attempting connection')
      try {
        const connection = new AtlasConnection()
        await connection.connect()
        console.error('[search-inject] Daemon connected')

        const daemonResults = (await connection.request('atlas.search' as any, {
          query: enrichedQuery,
          limit: 3,
          rerank: false,
          sessionId: input.session_id,
        })) as SearchResult[]

        connection.disconnect()

        results = daemonResults
        searchMethod = 'daemon'
        console.error('[search-inject] Daemon search completed:', {
          results: daemonResults.length,
        })
      } catch (error) {
        // Daemon connection failed, fall through to direct
        console.error('[search-inject] Daemon search failed:', (error as Error).message)
      }
    } else {
      console.error('[search-inject] Daemon not running')
    }

    // Fallback: direct search (daemon not running or failed)
    if (results.length === 0) {
      console.error('[search-inject] Attempting direct search')
      try {
        // Load config
        const config = await loadConfig()

        // Get ApplicationService singleton
        const app = getApplicationService(config)

        // Initialize storage and backends (CRITICAL - matches CLI pattern)
        await app.initialize()

        // Search via ApplicationService (not domain function directly)
        const directResults = await app.search({
          query: enrichedQuery,
          limit: 3,
          rerank: false,
        })

        results = directResults.map((r: any) => ({
          text: r.text,
          filePath: r.file_path,
          score: r.score,
        }))

        searchMethod = 'direct'
        console.error('[search-inject] Direct search completed:', {
          results: directResults.length,
        })
      } catch (error) {
        console.error('[search-inject] Direct search failed:', (error as Error).message)
      }
    }

    if (results.length === 0) {
      console.error('[search-inject] No results found, exiting')
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

    console.error('[search-inject] Packed results:', {
      total: results.length,
      packed: packedResults.length,
      totalChars,
      maxChars: MAX_CHARS,
      estimatedTokens: Math.ceil(totalChars / CHARS_PER_TOKEN),
    })

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
            console.error('[search-inject] Found bootstrap for project:', {
              cwd: input.cwd,
              bootstrapFile: file,
            })
            // Found bootstrap for current project
            // Check if already watching via daemon
            if (isDaemonRunning()) {
              try {
                const connection = new AtlasConnection()
                await connection.connect()

                const status = (await connection.request('atlas.ingest.status' as any, {})) as any

                // Check if any task is watching this cwd
                const watching = status.tasks.some(
                  (t: any) => t.watching && t.paths.includes(input.cwd)
                )

                if (!watching) {
                  // Start auto-watch
                  console.error('[search-inject] Starting auto-watch for:', input.cwd)
                  await connection.request('atlas.ingest.start' as any, {
                    paths: [input.cwd],
                    recursive: true,
                    watch: true,
                  })
                } else {
                  console.error('[search-inject] Project already being watched')
                }

                connection.disconnect()
              } catch (error) {
                console.error('[search-inject] Auto-watch failed:', (error as Error).message)
              }
            }
            break
          }
        }
      }
    } catch (error) {
      console.error('[search-inject] Bootstrap check failed:', (error as Error).message)
    }

    // Output structured response
    const output = {
      hookSpecificOutput: {
        hookEventName: 'UserPromptSubmit',
        additionalContext: `\n\n<atlas-context>\nRelevant context from Atlas semantic memory:\n\n${context}\n</atlas-context>`,
      },
    }

    console.error('[search-inject] Hook completed successfully:', {
      method: searchMethod,
      contextsInjected: packedResults.length,
    })

    console.log(JSON.stringify(output))
  } catch (error) {
    // Log error details to stderr but don't block user prompts
    console.error('[search-inject] Fatal error:', (error as Error).message)
    console.error('[search-inject] Stack:', (error as Error).stack)
    process.exit(0)
  }
}

main()
