/**
 * Atlas Search Tool
 *
 * MCP tool for semantic search across ingested context.
 * Uses Zod schemas for input validation.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { zodToJsonSchema } from 'zod-to-json-schema'
import { search, loadConfig, SearchOptionsSchema } from '@inherent.design/atlas-core'

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
})

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

      const { query, limit, since, qntmKey, rerank } = parseResult.data

      await loadConfig()

      const results = await search({
        query,
        limit,
        since,
        qntmKey,
        rerank,
      })

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              results.map((r) => ({
                filePath: r.file_path,
                text: r.text,
                score: r.score,
                rerankScore: r.rerank_score,
                qntmKey: r.qntm_key,
                createdAt: r.created_at,
              }))
            ),
          },
        ],
      }
    }
  )
}
