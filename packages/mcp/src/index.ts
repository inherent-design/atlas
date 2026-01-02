#!/usr/bin/env bun
/**
 * @inherent.design/atlas-mcp - MCP Server for Atlas
 *
 * Exposes Atlas functionality via Model Context Protocol
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'

// Import tools
import { registerIngestTool } from './tools/ingest.js'
import { registerSearchTool } from './tools/search.js'
import { registerTimelineTool } from './tools/timeline.js'

const server = new McpServer({
  name: 'atlas',
  version: '1.0.0',
})

// Register all tools
registerIngestTool(server)
registerSearchTool(server)
registerTimelineTool(server)

// Start server
async function main() {
  const transport = new StdioServerTransport()
  await server.connect(transport)
  console.error('Atlas MCP server running on stdio')
}

main().catch(console.error)
