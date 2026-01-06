/**
 * Atlas Search Tool
 *
 * MCP tool for semantic search across ingested context.
 * Routes through daemon when available for coordinated access.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { zodToJsonSchema } from 'zod-to-json-schema'
import { search, loadConfig, createClient, type AtlasClient } from '@inherent.design/atlas-core'

/** Search result type from daemon (matches daemon/protocol.ts) */
interface DaemonSearchResult {
  text: string
  filePath: string
  chunkIndex: number
  score: number
  createdAt: string
  qntmKey: string
  rerankScore?: number
}

/**
 * MCP-specific search input schema
 * Based on SearchOptionsSchema with MCP-appropriate defaults
 */
const MCPSearchInputSchema = z.object({
  /** Search query string */
  query: z.string().min(1, 'Query cannot be empty'),
  /** Maximum results to return */
  limit: z.number().int().min(1).max(100).default(5),
  /** ISO 8601 datetime for temporal filtering */
  since: z.string().optional(),
  /** Filter by specific QNTM key */
  qntmKey: z.string().optional(),
  /** Enable reranking with cross-encoder */
  rerank: z.boolean().default(false),
  /** Expand query with QNTM keys */
  expandQuery: z.boolean().default(false),
})

/** Cached daemon client (lazy initialized) */
let daemonClient: AtlasClient | null = null

/**
 * Try to connect to daemon, return null if unavailable
 */
async function getDaemonClient(): Promise<AtlasClient | null> {
  if (daemonClient?.isConnected()) {
    return daemonClient
  }

  try {
    daemonClient = await createClient()
    return daemonClient
  } catch {
    // Daemon not running, fall back to direct
    daemonClient = null
    return null
  }
}

export function registerSearchTool(server: McpServer) {
  // Generate JSON Schema from Zod schema for MCP
  const inputSchema = zodToJsonSchema(MCPSearchInputSchema as any, {
    $refStrategy: 'none',
    target: 'jsonSchema7',
  })

  server.tool(
    'atlas_search',
    'Semantic search across ingested context',
    inputSchema as Record<string, unknown>,
    async (args) => {
      // Validate input with Zod
      const parseResult = MCPSearchInputSchema.safeParse(args)
      if (!parseResult.success) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                error: 'Invalid input',
                details: parseResult.error.issues,
              }),
            },
          ],
          isError: true,
        }
      }

      const { query, limit, since, qntmKey, rerank, expandQuery } = parseResult.data

      // Try daemon first (pull methodology)
      const client = await getDaemonClient()

      let results: Array<{
        filePath: string
        text: string
        score: number
        rerankScore?: number
        qntmKey: string
        createdAt: string
      }>

      if (client) {
        // Route through daemon
        const daemonResults = (await client.search({
          query,
          limit,
          since,
          qntmKey,
          rerank,
          expandQuery,
        })) as DaemonSearchResult[]

        results = daemonResults.map((r) => ({
          filePath: r.filePath,
          text: r.text,
          score: r.score,
          rerankScore: r.rerankScore,
          qntmKey: r.qntmKey,
          createdAt: r.createdAt,
        }))
      } else {
        // Fallback: direct call (daemon not running)
        await loadConfig()

        const directResults = await search({
          query,
          limit,
          since,
          qntmKey,
          rerank,
          expandQuery,
        })

        results = directResults.map((r) => ({
          filePath: r.file_path,
          text: r.text,
          score: r.score,
          rerankScore: r.rerank_score,
          qntmKey: r.qntm_key,
          createdAt: r.created_at,
        }))
      }

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results),
          },
        ],
      }
    }
  )
}
