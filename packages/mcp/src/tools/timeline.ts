/**
 * Atlas Timeline Tool
 *
 * MCP tool for getting chronological timeline of ingested context.
 * Uses Zod schemas for input validation.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { zodToJsonSchema } from 'zod-to-json-schema'
import { timeline, loadConfig, TimelineOptionsSchema } from '@inherent.design/atlas-core'

/**
 * MCP-specific timeline input schema
 * Based on TimelineOptionsSchema with MCP-appropriate defaults
 */
const MCPTimelineInputSchema = z.object({
  /** Starting date (ISO 8601) */
  since: z.string().min(1, 'Since date is required'),
  /** Maximum results to return */
  limit: z.number().int().min(1).max(100).default(20),
})

export function registerTimelineTool(server: McpServer) {
  // Generate JSON Schema from Zod schema for MCP
  const inputSchema = zodToJsonSchema(MCPTimelineInputSchema as any, {
    $refStrategy: 'none',
    target: 'jsonSchema7',
  })

  server.tool(
    'atlas_timeline',
    'Get chronological timeline of ingested context',
    inputSchema as Record<string, unknown>,
    async (args) => {
      // Validate input with Zod
      const parseResult = MCPTimelineInputSchema.safeParse(args)
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

      const { since, limit } = parseResult.data

      await loadConfig()

      const results = await timeline(since, limit)

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              results.map((r) => ({
                filePath: r.file_path,
                text: r.text,
                createdAt: r.created_at,
                qntmKey: r.qntm_key,
              }))
            ),
          },
        ],
      }
    }
  )
}
