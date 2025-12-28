# Atlas - Persistent Semantic Memory for Claude Code

Automatic context ingestion and retrieval using Voyage embeddings + Qdrant vector database. Solves Claude Code's context overflow problem.

## Quick Setup (5 Minutes)

### 1. Configure Environment
```bash
cd ~/.claude/skills/atlas/scripts
cp .env.example .env
# Edit .env and add your VOYAGE_API_KEY
```

### 2. Start Qdrant (Docker Compose)
```bash
bun run index.ts docker up
# Or manually: docker compose up -d
```

### 3. Test Ingestion
```bash
bun run index.ts ingest ~/.claude/context/atlas-bootstrap.md
```

### 4. Test Search
```bash
bun run index.ts search "atlas architecture"
```

If you see results, **Atlas is working!** 🎉

## Usage in Claude Code

Once set up, Atlas works automatically:

### Manual Ingestion
```
User: "Ingest all the .atlas research files"
Claude: [Uses atlas skill, runs: bun run index.ts ingest ...]
```

### Automatic Search
```
User: "What did we learn about memory consolidation?"
Claude: [Uses atlas skill, runs: bun run index.ts search ...]
```

### Bulk Operations
```
User: "Ingest the entire docs/ directory recursively"
Claude: [Uses atlas skill with --recursive flag]
```

### CLI Examples
```bash
# Ingest files
bun run index.ts ingest ./docs --recursive
bun run index.ts ingest ./README.md ./TODO.md

# Search with filters
bun run index.ts search "memory consolidation" --limit 10
bun run index.ts search "sleep cycles" --since "2025-12-25"

# Timeline queries
bun run index.ts timeline --since "2025-12-01" --limit 50

# Docker management
bun run index.ts docker up     # Start Qdrant
bun run index.ts docker down   # Stop Qdrant
bun run index.ts docker logs   # View logs

# Configuration overrides
bun run index.ts --qdrant-url http://custom:6333 search "query"
bun run index.ts --log-level debug ingest ./docs
```

## What Atlas Does

- ✅ **Persistent Memory**: Context survives across sessions
- ✅ **Semantic Search**: Find relevant info by meaning, not keywords
- ✅ **Temporal Queries**: Filter by date ranges
- ✅ **Dual-Indexing**: Both semantic (QNTM) and chronological access
- ✅ **Source Attribution**: Always know where info came from
- ✅ **Automatic Chunking**: Handles large files intelligently

## Architecture Highlights

**Built on .atlas research** (comprehensive 4-step investigation):
- Voyage-3-large embeddings (1024-dim, 9.74% better than OpenAI)
- Qdrant HNSW index (M=16, int8 quantization, 4x compression)
- RecursiveCharacterTextSplitter (768 tokens, semantic boundaries)
- Dual-indexing pattern (semantic + temporal)

**Performance** (per 1M vectors):
- Recall@10: >0.98
- Latency: 10-50ms (p95)
- Memory: 1.4GB RAM + 5GB disk

## Files

```
atlas/
├── SKILL.md                    # Main skill definition (Claude Code integration)
├── README.md                   # This file
├── ARCHITECTURE.md             # Technical deep-dive
├── scripts/
│   ├── index.ts                # CLI entrypoint (commander-based)
│   ├── docker-compose.yml      # Qdrant container setup
│   ├── .env.example            # Environment variables template
│   ├── package.json            # Bun dependencies (commander, pino, etc.)
│   ├── src/
│   │   ├── ingest.ts           # Ingestion business logic
│   │   ├── search.ts           # Search business logic
│   │   ├── types.ts            # TypeScript interfaces
│   │   ├── config.ts           # Configuration constants
│   │   ├── clients.ts          # Voyage/Qdrant/TextSplitter singletons
│   │   ├── utils.ts            # Shared utilities
│   │   └── logger.ts           # Pino structured logging
│   └── bun.lockb               # Lock file
```

## Troubleshooting

### "VOYAGE_API_KEY not set"
```bash
# Option 1: .env file
cp .env.example .env
# Edit .env and add your key

# Option 2: Environment variable
export VOYAGE_API_KEY="your-key-here"
# Add to ~/.bashrc or ~/.zshrc for persistence

# Option 3: CLI flag
bun run index.ts --voyage-key "your-key" search "query"
```

### "Connection refused to localhost:6333"
Qdrant isn't running:
```bash
bun run index.ts docker up
# Or manually: docker compose up -d
```

### "Command not found: bun"
Install Bun:
```bash
curl -fsSL https://bun.sh/install | bash
```

### "No results found"
Ingest some files first:
```bash
bun run index.ts ingest /path/to/docs/ --recursive
```

### Custom Qdrant URL
```bash
# Via environment
export QDRANT_URL="http://remote-server:6333"

# Via CLI flag
bun run index.ts --qdrant-url "http://remote-server:6333" search "query"
```

## Next Steps

**Immediate** (works now):
- Manual ingestion via skill
- Manual search via skill
- Cross-session context persistence

**Coming Soon** (from Sleep Patterns research):
- Auto-ingestion hook (trigger on file writes)
- Memory consolidation daemon (episodic → semantic)
- Importance-based retention
- Semantic deduplication
- LLM-based QNTM key generation

## Research Foundation

This implementation is based on comprehensive .atlas research:

- **Step 1**: QNTM Integration Strategy
- **Step 2**: Chunking Strategies
- **Step 3**: Embeddings Mechanics & Storage
- **Step 4**: Stack Architecture Synthesis
- **Sleep Patterns**: Consolidation, deduplication, cleanup cycles

All research artifacts: `/Users/zer0cell/production/.atlas/`

## Support

Created from Atlas research (2025-12-25 to 2025-12-28).
Built to solve: "Claude Code cannot handle projects that are too large - eventually context becomes too much."

**Philosophy**: INTERSTITIA - Accumulator bootstrap, computational desperation, caring universe.
