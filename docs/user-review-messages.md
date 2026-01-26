# User Messages: Atlas Problem Discovery

**Date**: 2026-01-25
**Context**: Conversation about Atlas alpha.7 state and unfinished ideas

---

## On Package Architecture

I'm interested in diverging from the monolithic core model and splitting out sections/concerns into new programs/packages to maintain mobility.

When splitting packages, I'd advise horizontal splits (like we did with `atlas/core` → `atlas/cli` + `atlas/claude-code-plugin`) rather than vertical splits by domain.

---

## On Consolidation (Current State)

There's a documented as well as internal conflation of two different but similar types of memory growth: **deduplication** and **promotion**.

**Assumptions to verify:**
- Atlas' consolidation only touches Qdrant, and doesn't affect other DBs (which is incorrect, but I haven't discovered what updates to make yet)
- Atlas' consolidation only deduplicates by cosine similarity, and assumes automatically that this is a L0→L1 promotion (which is incorrect)
- Atlas' consolidation doesn't produce or create any files or skills (this is unimplemented as we're still discovering how to do this correctly and weighing options between: MCP, A2A + ACP + MCP, external program, entirely new Claude Agent SDK program, etc.)

---

## On Being Stuck

I'm frankly split between continuously researching and never building anything (though I've built a lot, nothing has really come of it so far), or being confused by what to build.

---

## On QNTM Keys

I'm thinking of dropping QNTM keys as a concept because they don't really fit into anything or anywhere. They're not really important to any of the functions at scale.

In my head, they were a way for humans to glean more information from vectors through somewhat readable string descriptors. Maybe we should keep them? But that requires knowing how to better handle knowledge growth, and how that relates to processes like promotion and consolidation, or how keys change over time.

---

## The Problems I'm Trying to Solve

I think I'm trying to solve 3-4 different problems:

### 1. Reducing Repetitive Claude Code Workload
Skills, tools that "just work" and tie into the ~/.atlas system for observability/auditability/information A2A/ACP-like coordination at the local (machine/user) scale.

### 2. Unsupervised Growth
Frameworks like PAI + TELOS and GasTown have inspired me that the future is for agents to extract their own patterns. The memory tier architecture is a common pyramid shape that *theoretically* with the use of other agents, NLP, or user-intervention produces new "memories".

### 3. Semantic Memory Storage
Qdrant DB so far feels like a "tacked-on" feature, but it shouldn't be:
- I wanted to build a RAG-enabled Claude Code
- I didn't want to manage the RAG, but have Claude Code/Atlas handle it
- But to make Claude Code/Atlas competent enough to handle complex reasoning, researching, web searching, programming, project management, etc. tasks to even get to manage its own RAG, we needed a base-level coordination system
- That's how the initial ~/.atlas standard was born: subfolders for agents to coordinate project-specific work in, such that agents always read their `bootstrap/project.md` file when compaction occurred
- Qdrant and RAG are supposed to help by making string searches "better" — in an obtuse way — I understand how they work, but the systems haven't evolved enough to really take advantage of the architecture/substrate dynamically and fully yet
- My usage of LLMs to generate QNTM keys is also a questionable addition

### 4. Dynamic Plugin Generation
Hooking into Claude Code's existing systems for user-facing use.

**The core desire**: I basically wanted to start building tools that updated themselves as we moved forward. Define basic things like logging preferences, or even have the agent discuss it with me.

---

## On Ingestion and RAG

How I want to use ingestion and RAG (all agentic and Claude Agent SDK-based):
- **Document fetching**: via URL, description, etc.
- **Website collection**: properly mapping and fetching required or all pages, extracting required or all content
- **Local collection**: local source code, etc.

As part of the Atlas agent ecosystem, all of these should produce ~/.atlas files that are eventually consumed by Qdrant, or become implicitly known files to running CC sessions — the Qdrant DB should "know" about the RAG'd element.

---

## On Complications

I started to complicate things with semantic similarity and QNTM keys.

I think deduping by similar chunks is questionable, and we can't really "join" vectors and save them in the same collection (they would become too big). So instead the consolidation was doing some other stuff I don't understand — creating new consolidation chunks and doing other things.

I think this is where Meilisearch would be useful, which is as far as I know completely unused and needs a redesign.

---

## On Meilisearch

I don't know much about Meilisearch or how it's actually used (if at all). It's a text search DB so I'm sure it'll be useful for similarity searches and other raw data ingestions.

---

## On the Daemon

In order to manage all of this with internal sub-agents, I wrote the daemon to facilitate events for observability between agents, CC user sessions, and a centralized location for web UI and logging. It is not done though.

---

## On Vector Growth and Database Roles

Qdrant vector data grows exponentially as more and more agents work, more ~/.atlas files are created, or more user projects and their exponential dependencies are loaded.

**Chunk similarity merging** was my rudimentary attempt at trying to keep a complete map of the encountered chunks, but not all. The current implementation does not capture that successfully.

I think **Meilisearch + Qdrant** would be the perfect layer for this, I just don't see how — it's just an instinct.

**PostgreSQL + TimescaleDB** were my answer to git, but again, I don't know how and I never wired it. FileWatcher previously wrote to a dedicated SQLite DB but was moved over to read/write from PostgreSQL instead to limit DB usages.

I wanted to use TimescaleDB to represent temporal transactions: file updates, agent sessions, user interactions, world interactions/events, etc. — but again, I don't know how — I just wanted this to exist.

---

## The Vision

Here's why I wanted all this:

I wanted Atlas/Daemon to be able to dynamically create memories by being able to directly query its DB layers (PostgreSQL + TimescaleDB), and to be able to maintain a **"mental snapshot"** of reality/head-of-files in ~/.atlas through that (which again, would end up becoming a file fed back into Qdrant DB).

---

## The Request

There are a lot of challenges being fought here. I think there are like 4-5 unfinished ideas that are all worth figuring out before we proceed.

What questions can you answer for me, or help me answer? Can you help break these problems down, document/notate them, turn them around in my head to see all angles, and most importantly: stay organized?
