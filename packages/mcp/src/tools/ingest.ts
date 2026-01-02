/**
 * Atlas Ingest Tool
 *
 * MCP tool for ingesting files into Atlas semantic memory.
 * Uses Zod schemas for input validation.
 */

import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { zodToJsonSchema } from 'zod-to-json-schema'
import { ingest, loadConfig, IngestOptionsSchema } from '@inherent.design/atlas-core'

/**
 * MCP-specific ingest input schema
 * Subset of IngestOptionsSchema with only MCP-relevant fields
 */
const MCPIngestInputSchema = z.object({
  /** File or directory paths to ingest */
  paths: z.array(z.string()).min(1, 'At least one path required'),
  /** Recursively process directories */
  recursive: z.boolean().default(false),
})

export function registerIngestTool(server: McpServer) {
  // Generate JSON Schema from Zod schema for MCP
  const inputSchema = zodToJsonSchema(MCPIngestInputSchema, {
    $refStrategy: 'none',
    target: 'jsonSchema7',
  })

  server.tool(
    'atlas_ingest',
    'Ingest files into Atlas semantic memory',
    inputSchema as Record<string, unknown>,
    async (args) => {
      // Validate input with Zod
      const parseResult = MCPIngestInputSchema.safeParse(args)
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

      const { paths, recursive } = parseResult.data

      await loadConfig()

      const result = await ingest({
        paths,
        recursive,
        verbose: false,
      })

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              filesProcessed: result.filesProcessed,
              chunksStored: result.chunksStored,
              errors: result.errors.map((e) => ({ file: e.file, error: e.error })),
            }),
          },
        ],
      }
    }
  )
}
