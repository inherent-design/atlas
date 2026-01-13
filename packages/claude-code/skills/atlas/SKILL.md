---
name: atlas
description: Persistent semantic memory for AI agents. Ingest, search, consolidate context across sessions. Manages Qdrant + Ollama infrastructure and background daemon.
allowed-tools: Bash(docker:*), Bash(docker-compose:*), Bash(pnpm:*), Bash(curl:*), Bash(cd:*)
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
pnpm --filter @inherent.design/atlas-cli atlas ingest /path/to/file.md

# Directory (recursive)
pnpm --filter @inherent.design/atlas-cli atlas ingest ./docs -r

# Multiple paths
pnpm --filter @inherent.design/atlas-cli atlas ingest README.md src/ docs/ -r

# Verbose output
pnpm --filter @inherent.design/atlas-cli atlas ingest ./src -r --verbose
```

**Supported formats:** `.md`, `.ts`, `.tsx`, `.js`, `.jsx`, `.json`, `.yaml`, `.rs`, `.go`, `.py`, `.sh`, `.css`, `.html`, `.qntm`

**Ignored:** `node_modules`, `.git`, `dist`, `build`, `coverage`

### Search

Semantic search across stored context:

```bash
# Basic search
pnpm --filter @inherent.design/atlas-cli atlas search "authentication patterns"

# With limit
pnpm --filter @inherent.design/atlas-cli atlas search "error handling" --limit 10

# With reranking (higher quality, slower)
pnpm --filter @inherent.design/atlas-cli atlas search "memory consolidation" --rerank

# Temporal filter
pnpm --filter @inherent.design/atlas-cli atlas search "api design" --since "2025-12-01"
```

### Timeline

Chronological view of stored context:

```bash
# Recent entries
pnpm --filter @inherent.design/atlas-cli atlas timeline

# Since date
pnpm --filter @inherent.design/atlas-cli atlas timeline --since "2025-12-15"

# Limit results
pnpm --filter @inherent.design/atlas-cli atlas timeline --limit 50
```

### Consolidate

Merge similar chunks to reduce redundancy:

```bash
# Dry run (preview only)
pnpm --filter @inherent.design/atlas-cli atlas consolidate --dry-run

# Execute consolidation
pnpm --filter @inherent.design/atlas-cli atlas consolidate

# With verbose output
pnpm --filter @inherent.design/atlas-cli atlas consolidate --verbose
```

### Doctor

Diagnose system health:

```bash
pnpm --filter @inherent.design/atlas-cli atlas doctor
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
pnpm --filter @inherent.design/atlas-cli atlas qdrant drop --yes

# Disable HNSW (for batch ingestion - faster writes)
pnpm --filter @inherent.design/atlas-cli atlas qdrant hnsw off

# Enable HNSW (after batch ingestion - enables search)
pnpm --filter @inherent.design/atlas-cli atlas qdrant hnsw on
```

---

## Daemon

Background service for file watching and auto-ingestion.

### Start Daemon

```bash
cd ~/production/atlas/packages/core
pnpm daemon
```

Or via CLI:

```bash
cd ~/production/atlas
pnpm --filter @inherent.design/atlas-cli atlas daemon start
```

The daemon:

- Watches `~/.atlas/` for new files (recursive)
- Auto-ingests files matching embeddable extensions
- Runs consolidation watchdog
- Monitors system pressure (CPU/memory)

### Stop Daemon

```bash
pnpm --filter @inherent.design/atlas-cli atlas daemon stop
```

### Check Status

```bash
pnpm --filter @inherent.design/atlas-cli atlas daemon status
```

---

## Development

```bash
cd ~/production/atlas/packages/core

# Run tests (298 tests)
pnpm test

# Type check
pnpm exec tsc --noEmit

# Watch mode
pnpm test:watch
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

| Component  | Technology             | Purpose               |
| ---------- | ---------------------- | --------------------- |
| Embeddings | Voyage-3-large (1024d) | Semantic vectors      |
| Vector DB  | Qdrant (HNSW, int8)    | Storage + search      |
| LLM        | Anthropic/Ollama       | QNTM key generation   |
| Reranker   | Voyage rerank-2.5      | Result quality boost  |
| Daemon     | Unix socket server     | Background processing |

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
pnpm --filter @inherent.design/atlas-cli atlas doctor

# 4. Nuclear option: drop and re-ingest
pnpm --filter @inherent.design/atlas-cli atlas qdrant drop --yes
pnpm --filter @inherent.design/atlas-cli atlas ingest ~/.atlas -r
```

---

## Packages

| Package                       | Description                                |
| ----------------------------- | ------------------------------------------ |
| `@inherent.design/atlas-core` | Core library (embeddings, storage, search) |
| `@inherent.design/atlas-cli`  | Command-line interface                     |
| `@inherent.design/atlas-mcp`  | MCP server for Claude Code                 |
