# Atlas

Persistent semantic memory for AI agents. Ingest, search, and consolidate context across sessions using Voyage embeddings + Qdrant vector storage.

## Quick Start

### Prerequisites

```bash
# Start Qdrant
docker compose up -d

# Set API keys
export VOYAGE_API_KEY="your-key"       # Required for embeddings
export ANTHROPIC_API_KEY="your-key"    # Optional, for Anthropic LLM
```

### Basic Usage

```bash
# Ingest documentation
bun run --filter @inherent.design/atlas atlas ingest ./docs -r

# Search semantically
bun run --filter @inherent.design/atlas atlas search "authentication patterns" --limit 10

# Search with reranking
bun run --filter @inherent.design/atlas atlas search "error handling" --rerank

# Timeline view
bun run --filter @inherent.design/atlas atlas timeline --since "2025-12-01"

# Consolidate memories
bun run --filter @inherent.design/atlas atlas consolidate --dry-run
```

## Structure

```
atlas/
├── packages/
│   ├── core/           # @inherent.design/atlas-core
│   │   └── src/
│   │       ├── domain/     # ingest, search, consolidate
│   │       ├── services/   # embedding, llm, storage, reranker
│   │       └── shared/     # config, logger, types
│   ├── cli/            # @inherent.design/atlas
│   │   └── src/index.ts
│   └── mcp/            # @inherent.design/atlas-mcp
│       └── src/            # MCP server for Claude Code
├── docs/
│   └── architecture.md
├── skill/
│   └── SKILL.md            # Claude Code skill wrapper
├── atlas.config.example.ts
├── docker-compose.yml
└── .env.local.example
```

## Packages

| Package                       | Description                                |
| ----------------------------- | ------------------------------------------ |
| `@inherent.design/atlas-core` | Core library (embeddings, storage, search) |
| `@inherent.design/atlas`      | CLI                                        |
| `@inherent.design/atlas-mcp`  | MCP server for Claude Code                 |

## Configuration

Copy the example config and customize:

```bash
cp atlas.config.example.ts atlas.config.ts
```

```typescript
import { defineConfig } from '@inherent.design/atlas-core'

export default defineConfig({
  backends: {
    'text-embedding': 'voyage:voyage-3-large',
    'code-embedding': 'voyage:voyage-code-3',
    'qntm-generation': 'ollama:ministral-3:3b',
    reranking: 'voyage:rerank-2.5',
  },
  qdrant: {
    url: 'http://localhost:6333',
    collection: 'atlas',
  },
  ingestion: {
    batchSize: 50,
    qntmConcurrency: 8,
  },
})
```

## Development

```bash
# Install dependencies
bun install

# Run tests
bun run --filter @inherent.design/atlas-core test

# Type check
bun run --filter @inherent.design/atlas-core typecheck
```

## Requirements

- **Runtime:** Bun >= 1.2.15
- **Services:** Qdrant (vector DB), Ollama (optional, for local LLM)
- **API Keys:** `VOYAGE_API_KEY` (required), `ANTHROPIC_API_KEY` (optional)

## Documentation

- [Architecture](docs/architecture.md) - Technical architecture and data flow

## License

MIT
