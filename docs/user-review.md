# Atlas User Review: Problem Decomposition

**Date**: 2026-01-25
**Status**: Active problem breakdown
**Purpose**: Organize unfinished ideas, track decisions, maintain clarity

---

## Executive Summary

Atlas has ~6 distinct problems that have become entangled. This document separates them, tracks their state, and helps sequence decisions.

**The meta-problem**: Infrastructure was built before the problem was fully defined. The storage layer works; the consumption and collection layers don't exist.

---

## Problem Registry

### P1: Vector Growth Management

**Goal**: Keep a "complete map" of encountered content without storing every chunk forever.

**Your instinct**: Chunk similarity merging reduces storage while preserving semantic coverage.

**Current state**:
- Consolidation finds similar chunks (cosine > threshold)
- LLM classifies relationship type
- "Merging" keeps one chunk, soft-deletes others, combines QNTM keys
- This doesn't actually reduce vector count in a meaningful way

**Questions to answer**:
- [ ] What's actual vector count growth rate per day/week of usage?
- [ ] Does similarity threshold (0.85) make sense? Too aggressive? Too conservative?
- [ ] Is the goal dedup (remove redundant), summarization (compress), or indexing (organize)?
- [ ] Would a different approach work: just let duplicates exist, rely on search to find best match?

**Blockers**: Unclear what "success" looks like.

---

### P2: Meilisearch Role

**Goal**: Unclear. "Perfect layer for something."

**Your instinct**: Meilisearch + Qdrant together solve a problem neither solves alone.

**Current state**:
- Deployed, running
- Hybrid search code references it
- Unclear if it's being populated during ingestion
- Unclear what queries would use it

**Questions to answer**:
- [ ] Is Meilisearch populated during ingestion? (Verify in code)
- [ ] What query would use full-text that vectors can't handle?
  - "Find all chunks mentioning `SessionStart`" (exact keyword)
  - "Find all chunks from file X" (metadata filter)
  - "Find typo-tolerant matches for `sesion`"
- [ ] Should Meilisearch index same content as Qdrant, or different?
- [ ] Is Meilisearch for search, or for something else (faceting, filtering)?

**Blockers**: Don't know what it's for yet.

---

### P3: Temporal Transactions (PostgreSQL + TimescaleDB)

**Goal**: "Git for reality" - query historical state of files, sessions, events.

**Your instinct**: TimescaleDB can represent temporal transactions: file updates, agent sessions, user interactions, world events.

**Current state**:
- FileTracker writes to PostgreSQL (moved from SQLite)
- TimescaleDB extension installed but not used as hypertable
- No temporal queries implemented
- 00-events layer conceptually captures events, but in files not DB

**Questions to answer**:
- [ ] What temporal queries do you actually need?
  - "What did file X contain on date Y"?
  - "What happened in session Z"?
  - "What changed between dates A and B"?
  - "How many chunks were ingested per hour"?
- [ ] Is PostgreSQL the source of truth for file state, or filesystem?
- [ ] Should 00-events be in TimescaleDB instead of/in addition to files?
- [ ] What's the relationship between DB temporal data and ~/.atlas/memory/00-events/?

**Blockers**: Don't know what temporal queries matter.

---

### P4: Mental Snapshot (Daemon → Reality)

**Goal**: Daemon queries DBs → maintains a "mental snapshot" of reality/head-of-files.

**Your instinct**: This snapshot becomes a file that feeds back into Qdrant.

**Current state**:
- Daemon scaffolded but not running
- No "snapshot" generation implemented
- No loop from DB query → file generation → re-ingestion

**Questions to answer**:
- [ ] What IS the mental snapshot?
  - A summary of "what Atlas knows"?
  - A list of "files that exist and their status"?
  - A semantic map of "concepts and their relationships"?
- [ ] When does the snapshot get generated? (On schedule? On demand? On change?)
- [ ] Who consumes the snapshot? (CC sessions? Web UI? User directly?)
- [ ] What format? (Single file? Multiple files? DB view?)

**Blockers**: "Mental snapshot" is a metaphor without implementation spec.

---

### P5: Consumption Path (CC Gets Context)

**Goal**: When CC runs, relevant context from Atlas appears automatically.

**Your instinct**: This was the original RAG goal.

**Current state**:
- SessionStart hook scaffolded
- Hook → Daemon RPC designed
- Daemon → Qdrant query designed
- **Nothing is wired**. Hooks don't call daemon. Daemon doesn't inject context.

**Questions to answer**:
- [ ] What's the minimum viable consumption path?
  - SessionStart → query Qdrant → inject top-K chunks?
  - UserPromptSubmit → query based on prompt → inject relevant context?
- [ ] How much context is "right"? (Token budget, relevance threshold)
- [ ] Does this need the daemon, or could hooks query Qdrant directly?
- [ ] What proves this works? (User notices relevant context appearing)

**Blockers**: Just needs to be wired. This is implementation, not design.

---

### P6: Collection Sources (URLs, Websites, Local)

**Goal**: Ingest content from multiple sources: URLs, websites, local files.

**Your instinct**: All sources should produce ~/.atlas files that feed into Qdrant.

**Current state**:
- Local files: Implemented (ingestion pipeline works)
- URLs: Not implemented
- Websites (crawl + map): Not implemented

**Questions to answer**:
- [ ] Which collection source matters most right now?
- [ ] Can URL/website collection be a separate tool/program?
  - Tool outputs ~/.atlas files → file watcher ingests → done
- [ ] Does collection need to understand content (smart extraction) or just fetch (dump raw)?
- [ ] How does collection relate to the "mental snapshot" (P4)?

**Blockers**: Sequencing. Local works; others are separate projects.

---

## Entanglement Map

How these problems connect:

```
P6 (Collection) → produces files
        │
        ▼
P3 (Temporal/PG) ← tracks file changes
        │
        ▼
P1 (Vector Growth) ← managed by consolidation
        │
        ├──► P2 (Meilisearch) ← unclear role
        │
        ▼
P4 (Mental Snapshot) ← generated from DB state
        │
        ▼
P5 (Consumption) → CC gets context
```

**Key insight**: P5 (Consumption) is the END of the chain. It's the only one that produces user-visible value. Everything else is infrastructure.

---

## QNTM Keys: Keep or Drop?

**Current role**:
- Generated during ingestion via LLM (1 call per chunk)
- Merged during consolidation
- Used as filter criteria in search
- Human-readable semantic tags

**Cost**: LLM call per chunk during ingestion. Adds latency and API cost.

**Value**:
- [ ] Do you ever filter by QNTM key?
- [ ] Do QNTM keys improve search results?
- [ ] Are they useful for the "mental snapshot" (P4)?

**Options**:
1. **Keep as-is**: Accept cost, hope for future value
2. **Generate lazily**: Only generate on first access
3. **Drop entirely**: Let vectors do semantic work
4. **Replace**: Use Meilisearch keywords instead of LLM-generated keys

**Recommendation**: Drop for now. Re-add if you find a use case.

---

## Sequencing Recommendation

Based on "what produces user-visible value soonest":

**Phase 0: Prove RAG works**
- Wire P5 (Consumption): SessionStart → Qdrant → inject context
- Use existing local ingestion (P6 local already works)
- Skip P1-P4 until RAG is proven

**Phase 1: Understand usage patterns**
- With RAG working, observe: What queries happen? What context helps?
- This informs P1 (growth), P2 (Meilisearch role), P4 (snapshot)

**Phase 2: Add collection sources**
- P6: URL fetching → ~/.atlas files → ingestion
- Keep it simple: separate tool, outputs files, done

**Phase 3: Revisit infrastructure**
- P1, P2, P3, P4 become clearer after real usage

---

## Decision Log

| Date       | Decision                      | Rationale                              |
| ---------- | ----------------------------- | -------------------------------------- |
| 2026-01-25 | Created problem decomposition | Needed clarity on 6 entangled problems |
|            |                               |                                        |

---

## Open Questions (For User)

1. Which of P1-P6 feels most urgent to YOU right now?
2. What would "RAG working" look like? What's the test case?
3. Is there existing content you want to query? (A specific project, docs, etc.)
4. How much are you willing to simplify to get something working?

---

*This document is a living artifact. Update as decisions are made.*
