---
name: atlas
description: Persistent semantic memory for AI agents. Ingest, search, consolidate context across sessions. Manages Qdrant + Ollama infrastructure and background daemon.
allowed-tools: Bash(docker:*), Bash(docker-compose:*), Bash(bun:*), Bash(curl:*), Bash(cd:*)
---

# Atlas - Persistent Semantic Memory

Atlas solves context overflow by storing knowledge persistently across sessions using Voyage embeddings + Qdrant vector storage.

---

## Infrastructure Setup

### Start Services

```bash
cd ~/production/atlas
docker compose up -d
```

Starts:
- **Qdrant** (port 6333) - Vector database with HNSW index
- **Ollama** (port 11434) - Local LLM for QNTM generation (optional)

### Verify Services

```bash
# Qdrant health
curl http://localhost:6333/health

# Qdrant collection info
curl http://localhost:6333/collections/atlas

# Ollama models
curl http://localhost:11434/api/tags
```

### Stop Services

```bash
cd ~/production/atlas
docker compose down
```

### Pull Ollama Model (if needed)

```bash
docker exec -it atlas-ollama ollama pull ministral:3b
```

---

## Environment

```bash
# Required for Voyage embeddings
export VOYAGE_API_KEY="your-key"

# Optional: enables Anthropic LLM instead of Ollama
export ANTHROPIC_API_KEY="your-key"
```

Without API keys, Atlas falls back to Ollama for all operations.

---

## CLI Commands

All commands run from atlas root:

```bash
cd ~/production/atlas
```

### Ingest

Store files in persistent memory:

```bash
# Single file
bun run --filter @inherent.design/atlas atlas ingest /path/to/file.md

# Directory (recursive)
bun run --filter @inherent.design/atlas atlas ingest ./docs -r

# Multiple paths
bun run --filter @inherent.design/atlas atlas ingest README.md src/ docs/ -r

# Verbose output
bun run --filter @inherent.design/atlas atlas ingest ./src -r --verbose
```

**Supported formats:** `.md`, `.ts`, `.tsx`, `.js`, `.jsx`, `.json`, `.yaml`, `.rs`, `.go`, `.py`, `.sh`, `.css`, `.html`, `.qntm`

**Ignored:** `node_modules`, `.git`, `dist`, `build`, `coverage`

### Search

Semantic search across stored context:

```bash
# Basic search
bun run --filter @inherent.design/atlas atlas search "authentication patterns"

# With limit
bun run --filter @inherent.design/atlas atlas search "error handling" --limit 10

# With reranking (higher quality, slower)
bun run --filter @inherent.design/atlas atlas search "memory consolidation" --rerank

# Temporal filter
bun run --filter @inherent.design/atlas atlas search "api design" --since "2025-12-01"
```

### Timeline

Chronological view of stored context:

```bash
# Recent entries
bun run --filter @inherent.design/atlas atlas timeline

# Since date
bun run --filter @inherent.design/atlas atlas timeline --since "2025-12-15"

# Limit results
bun run --filter @inherent.design/atlas atlas timeline --limit 50
```

### Consolidate

Merge similar chunks to reduce redundancy:

```bash
# Dry run (preview only)
bun run --filter @inherent.design/atlas atlas consolidate --dry-run

# Execute consolidation
bun run --filter @inherent.design/atlas atlas consolidate

# With verbose output
bun run --filter @inherent.design/atlas atlas consolidate --verbose
```

### Doctor

Diagnose system health:

```bash
bun run --filter @inherent.design/atlas atlas doctor
```

Checks:
- Environment variables (API keys)
- Service connectivity (Qdrant, Ollama, Voyage, Anthropic)
- Ollama model availability
- Configuration validation
- Tracking database stats

### Qdrant Management

```bash
# Drop collection (destructive!)
bun run --filter @inherent.design/atlas atlas qdrant drop --yes

# Disable HNSW (for batch ingestion - faster writes)
bun run --filter @inherent.design/atlas atlas qdrant hnsw off

# Enable HNSW (after batch ingestion - enables search)
bun run --filter @inherent.design/atlas atlas qdrant hnsw on
```

---

## Daemon

Background service for file watching and auto-ingestion.

### Start Daemon

```bash
cd ~/production/atlas/packages/core
bun run daemon
```

Or via CLI:

```bash
cd ~/production/atlas
bun run --filter @inherent.design/atlas atlas daemon start
```

The daemon:
- Watches `~/.atlas/` for new files (recursive)
- Auto-ingests files matching embeddable extensions
- Runs consolidation watchdog
- Monitors system pressure (CPU/memory)

### Stop Daemon

```bash
bun run --filter @inherent.design/atlas atlas daemon stop
```

### Check Status

```bash
bun run --filter @inherent.design/atlas atlas daemon status
```

---

## Development

```bash
cd ~/production/atlas/packages/core

# Run tests (296 tests)
bun run test

# Type check
bunx tsc --noEmit

# Watch mode
bun run test:watch
```

---

## When to Use This Skill

**Trigger phrases:**
- "Remember this across sessions"
- "Store this in memory"
- "Search previous work"
- "What did we decide about..."
- "Find all mentions of..."
- "Ingest the documentation"
- "Start the atlas daemon"
- "Check atlas health"

**Use cases:**
- Project context too large for single session
- Building on previous research/decisions
- Documentation needs to be queryable
- Persistent knowledge base for codebase
- Auto-ingestion of evolving docs

---

## Architecture Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| Embeddings | Voyage-3-large (1024d) | Semantic vectors |
| Vector DB | Qdrant (HNSW, int8) | Storage + search |
| LLM | Anthropic/Ollama | QNTM key generation |
| Reranker | Voyage rerank-2.5 | Result quality boost |
| Daemon | Unix socket server | Background processing |

**Performance:**
- Recall@10: >0.98
- Latency: 10-50ms (p95)
- Compression: 4x via int8 quantization

---

## Quick Recovery

If things break:

```bash
# 1. Restart services
cd ~/production/atlas
docker compose restart

# 2. Verify health
curl http://localhost:6333/health
curl http://localhost:11434/api/tags

# 3. Run diagnostics
bun run --filter @inherent.design/atlas atlas doctor

# 4. Nuclear option: drop and re-ingest
bun run --filter @inherent.design/atlas atlas qdrant drop --yes
bun run --filter @inherent.design/atlas atlas ingest ~/.atlas -r
```

---

## Packages

| Package | npm | Description |
|---------|-----|-------------|
| `@inherent.design/atlas-core` | Core | Embeddings, storage, search |
| `@inherent.design/atlas` | CLI | Command-line interface |
| `@inherent.design/atlas-mcp` | MCP | Claude Code integration |
