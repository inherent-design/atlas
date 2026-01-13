---
name: atlas-project
description: Create Atlas project bootstrap for persistent memory tracking. Analyzes conversation and directory structure to generate ~/.atlas/bootstrap/<project>.md and start auto-ingestion.
use_when: User wants to start tracking a new project, research area, codebase, or knowledge domain in Atlas persistent memory.
allowed-tools: Bash(tree:*), Bash(ls:*), Bash(git:*), Read, Task(subagent_type:integrator)
---

# Atlas Project Bootstrap Creator

Creates a persistent memory foundation for a project by:

1. Analyzing conversation context + directory structure
2. Generating project-specific bootstrap map at `~/.atlas/bootstrap/<project>.md`
3. Starting auto-ingestion with file watching

---

## When to Use

**Trigger phrases:**

- "Let's start tracking this project in Atlas"
- "Create an Atlas bootstrap for this codebase"
- "Set up persistent memory for this research"
- "/atlas-project <name> <path>"

**Use cases:**

- Starting work on a new codebase
- Research project that will span multiple sessions
- Client project requiring context persistence
- Any work that exceeds single-session context window

---

## Usage

```bash
# Option 1: Let skill detect from conversation
User: "Let's track this Rust project in Atlas"
Claude: [Creates bootstrap from current context]

# Option 2: Explicit path
User: "/atlas-project my-app ~/projects/my-app"
Claude: [Analyzes directory and creates bootstrap]
```

---

## What It Creates

**File:** `~/.atlas/bootstrap/<project>.md`

**Contents:**

- Project identity (name, type, root path)
- Entry points (main files, CLIs, servers)
- Directory structure (navigational snapshot)
- Key commands (build, test, run)
- Tech stack
- Current status

**Plus:** Starts auto-ingestion of project directory (recursive, file-watched)

---

## Implementation Flow

1. Gather context:
   - Full conversation history
   - `tree -L 3 <path>` output
   - `git log --oneline -5` (if git repo)
   - `package.json` / `Cargo.toml` / etc. (if present)

2. Spawn Integrator sub-agent with prompt:
   - "Detect project type from conversation and directory"
   - "Verify folder matches user intent"
   - "Generate ~/.atlas/bootstrap/<project>.md"

3. Write bootstrap file

4. Start ingestion:

   ```typescript
   await connection.request('atlas.ingest.start', {
     paths: [projectPath],
     recursive: true,
     watch: true,
   })
   ```

5. Return taskId and bootstrap path

---

## Examples

**Monorepo (TypeScript):**

````markdown
# MyApp Bootstrap

**Version:** 1.0 | **Type:** Monorepo (Bun) | **Root:** `/Users/mannie/projects/myapp`

## Packages

- `packages/core` - Core library
- `packages/cli` - Command-line interface
- `packages/web` - Web frontend

## Commands

```bash
pnpm install
pnpm test
pnpm dev
```
````

````

**Rust CLI:**
```markdown
# MyTool Bootstrap

**Version:** 0.1.0 | **Type:** Rust CLI | **Root:** `/Users/mannie/projects/mytool`

## Entry Points
- `src/main.rs` - CLI entrypoint
- `src/lib.rs` - Core library

## Commands
```bash
cargo build
cargo test
cargo run -- --help
````

````

---

## Notes

- Bootstrap file is a **navigational snapshot**, not documentation
- Focuses on "how to orient and operate" for cold-start agents
- Auto-updates when file watcher detects changes
- Can have multiple projects tracked simultaneously

---

## Behind the Scenes

The skill runs `/packages/claude-code/scripts/project-create.ts`:

1. **Context gathering**: Collects conversation history, directory tree, git log, package manifests
2. **LLM analysis**: Calls daemon to generate bootstrap content via Integrator agent
3. **File creation**: Writes `~/.atlas/bootstrap/<project>.md`
4. **Auto-ingestion**: Registers project path for continuous memory updates via `atlas.ingest.start`

**Daemon dependency**: Requires Atlas daemon running (`pnpm daemon` in `packages/core`)

---

## Error Recovery

If bootstrap creation fails:

```bash
# 1. Check daemon is running
cd ~/production/atlas/packages/core
pnpm daemon

# 2. Verify services are up
curl http://localhost:6333/health  # Qdrant

# 3. Check ingestion status
pnpm --filter @inherent.design/atlas-cli atlas ingest.status

# 4. Manually create bootstrap if needed
# Edit: ~/.atlas/bootstrap/<project>.md
# Then: pnpm --filter @inherent.design/atlas-cli atlas ingest.start <path> -r --watch
````

---

## Performance

- **Context gathering**: ~500ms (tree, git log, file reads)
- **LLM generation**: ~2-5s (Haiku via daemon)
- **File write**: <10ms
- **Ingestion start**: <100ms (async, runs in background)

**Total latency**: ~3-6 seconds for full bootstrap creation

---

## Integration with PreTaskSpawn

Once a project has a bootstrap file:

1. `PreTaskSpawn` hook automatically detects it
2. Injects full bootstrap content into sub-agent context
3. Also injects relevant semantic chunks from Atlas
4. Enables "cold-start recovery" for agents working on project tasks

**Flow:**

```
User spawns task → PreTaskSpawn hook
  ↓
Finds bootstrap for current cwd
  ↓
Searches Atlas for task-relevant chunks
  ↓
Injects both into sub-agent context
  ↓
Sub-agent starts with full project awareness
```
