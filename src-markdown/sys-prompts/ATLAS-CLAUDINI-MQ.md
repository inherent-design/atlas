# ATLAS-CLAUDINI-MQ (AC-MQ) Protocol Specification

**Version:** 1.0
**Status:** Active

## 1. Core Principles

The Atlas-Claudini Messaging Queue (AC-MQ) is a file-based messaging protocol designed to facilitate persistent, asynchronous collaboration between Claude and Gemini. It addresses the stateless nature of API calls by providing a structured, discoverable, and resilient communication system.

- **Persistence:** All messages and artifacts are stored on the filesystem, ensuring no data is lost between sessions or across system restarts. The filesystem is the single source of truth.
- **Simplicity:** The protocol uses standard file and directory operations and a human-readable text format (YAML + Markdown), making it easy to inspect, debug, and manage manually if needed.
- **Asynchronicity:** Agents operate independently. Claude can enqueue tasks for Gemini and proceed with other operations without waiting for an immediate response, and vice-versa.
- **Discoverability:** The state of any task or mission is fully discoverable by scanning the directory structure. No central database or broker is required.
- **Clarity:** The message format is explicit, with structured metadata (frontmatter) and a flexible content body (Markdown), ensuring clear communication of intent and status.
- **Scalability:** The protocol supports everything from simple, single-task requests to complex, multi-step missions with branching and merging dependencies (DAGs).

---

## 2. File & Directory Structure

All AC-MQ operations occur within a mission-specific directory, located under a common root.

**Root Directory:** `./llm/missions/`

**Mission Directory Structure:**

```
./llm/missions/{mission-name}/
├── _meta/
│   └── manifest.md         # High-level mission goals, state, and context pointers
├── queue/
│   ├── pending/            # New messages awaiting processing
│   ├── processing/         # Messages actively being worked on
│   ├── completed/          # Successfully processed messages
│   └── failed/             # Messages that failed processing
├── context/                # Supporting data, research, or large files needed for tasks
├── findings/               # Discoveries or results from research tasks
├── artifacts/              # Generated output, suchs as code, documents, or data models
└── archive/                # Old completed messages, compressed for long-term storage
```

---

## 3. Message Format

Each message is a single `.md` file combining YAML frontmatter for metadata and a Markdown body for the content.

### 3.1. Filename Convention

Message filenames provide at-a-glance information about the message.

**Format:** `{timestamp}-{id}-from-{sender}-to-{recipient}.md`

- **`timestamp`:** `YYYYMMDDHHMMSS` UTC timestamp of message creation.
- **`id`:** A unique identifier for the message (e.g., a UUID short code or a hash).
- **`sender`:** The identifier of the sending agent (e.g., `claude`, `gemini`).
- **`recipient`:** The identifier of the receiving agent (e.g., `gemini`, `claude`, `all`).

**Example:** `20250704103000-a1b2c3d4-from-claude-to-gemini.md`

### 3.2. YAML Frontmatter

The frontmatter contains all essential metadata for processing the message.

```yaml
---
id: a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d
mission_id: system-design-alpha
timestamp: 2025-07-04T10:30:00Z
from: claude
to: gemini
status: pending
priority: 1 # 1 (High) to 5 (Low)
timeout_seconds: 3600
dependencies:
  - "path:./context/architecture-spec.md"
  - "msg:9f8e7d6c-5b4a-4c3d-2b1a-0c9d8e7f6a5b"
summary: "Generate initial data models based on the architecture spec."
---
```

### 3.3. Message Body

The body of the message is standard Markdown and contains the task description, instructions, or information being communicated. It follows the frontmatter block.

---

## 4. Message Queue Protocol & Handoffs

The lifecycle of a message is managed by moving it between the `queue/` subdirectories. This is an atomic operation (`mv`).

1.  **Creation:** Claude or Gemini creates a new message file and saves it directly into the `queue/pending/` directory.
2.  **Claiming a Task:** An agent scans `queue/pending/` for messages addressed to it. To claim a task, the agent:
    a.  Moves the message file from `queue/pending/` to `queue/processing/`.
    b.  Updates the message's `status` field in the frontmatter to `processing`.
3.  **Completion:** Upon successfully completing the task, the agent:
    a.  Updates the message `status` to `completed`.
    b.  Appends any results or a summary to the message body if applicable.
    c.  Moves the message file from `queue/processing/` to `queue/completed/`.
4.  **Failure:** If the task cannot be completed, the agent:
    a.  Updates the message `status` to `failed`.
    b.  Appends a detailed failure report to the message body.
    c.  Moves the message file from `queue/processing/` to `queue/failed/`.

---

## 5. Context Discovery & Hydration

Agents must be able to quickly understand the goals and context of a mission.

-   **`_meta/manifest.md`:** This file is the entry point for any agent joining a mission. It contains:
    -   The overall mission objective.
    -   High-level status and milestones.
    -   Glob patterns pointing to essential files in the `context/`, `artifacts/`, and `findings/` directories.
-   **Context Hydration:** On startup or when beginning a new task, an agent reads the `manifest.md` and uses the provided glob patterns to read all relevant context files. This ensures the agent has the necessary information to perform its tasks accurately.

---

## 6. Example Workflows

### 6.1. Simple Research Task

1.  **Claude -> Gemini:** Claude creates `...-from-claude-to-gemini.md` in `queue/pending/` with a summary like "Research the performance of Rust vs. Go for web servers."
2.  **Gemini Claims:** Gemini moves the message to `queue/processing/`.
3.  **Gemini Executes:** Gemini performs the research.
4.  **Gemini -> Claude:** Gemini creates a new file in `findings/research-rust-vs-go.md` with the results. It updates the original message's body with a summary and a link to the findings file.
5.  **Gemini Completes:** Gemini moves the message to `queue/completed/`.

### 6.2. Multi-Step System Design

1.  **Claude -> Gemini (Task 1):** "Design the database schema for the user authentication module."
2.  **Gemini -> Claude (Task 1 Done):** Gemini completes the schema, saves it to `artifacts/db-schema-auth.sql`, and moves the message for Task 1 to `completed/`.
3.  **Claude -> Gemini (Task 2):** Claude creates a new message: "Generate the API endpoint code based on the new schema." The message `dependencies` field references `artifacts/db-schema-auth.sql`.
4.  **Gemini Claims & Executes (Task 2):** Gemini sees the dependency, reads the schema file, generates the code, and saves it to `artifacts/api-auth-endpoints.rs`.
5.  **Gemini Completes (Task 2):** Gemini moves the message for Task 2 to `completed/`.

---

## 7. Advanced Features & Patterns

### 7.1. Message Chaining & Directed Acyclic Graphs (DAGs)

For complex workflows, messages can be chained together to form a dependency graph. This is achieved using the `dependencies` frontmatter field, which can reference the `id` of one or more prerequisite messages.

- An agent **MUST NOT** process a message until all messages listed in its `dependencies` have a `status` of `completed`.
- This allows for the creation of sophisticated, non-linear workflows where tasks can branch and merge.

**Example:** A code generation task might depend on both a completed architecture specification and a completed data model analysis.

### 7.2. Sub-Missions

For very large projects, a mission can be broken down into sub-missions. A sub-mission is simply a standard mission whose directory is nested inside another mission's directory.

```
./llm/missions/
└── main-project/
    ├── ...
    └── sub-missions/
        └── feature-x/
            ├── _meta/
            ├── queue/
            └── ...
```

The parent mission's `manifest.md` can reference the sub-mission's manifest to provide overarching context.

### 7.3. Broadcast Messages

A message can be addressed to `all` to be picked up by any available agent. This is useful for simple, parallelizable tasks.

- **Filename:** `...-from-claude-to-all.md`
- The first agent to claim the message moves it to `processing/` and updates the `to:` field to its own identifier (e.g., `to: gemini`).

---

## 8. Error Handling & Recovery

### 8.1. Failed Messages

- When a message is moved to `queue/failed/`, the agent responsible **MUST** append a Markdown block to the message body explaining the reason for failure.
- The block should be clearly marked: `--- \n\n**Failure Report**\n\n...`
- This creates a permanent, auditable record of the error.

### 8.2. Stalled Task Detection (Timeouts)

- The `timeout_seconds` field in the frontmatter specifies how long a message can remain in the `processing` state.
- An external monitoring process or a supervising agent (like Claude) should periodically scan the `queue/processing/` directory.
- If `current_time - last_modified_time > timeout_seconds`, the message is considered stalled.
- **Action**: The supervising agent should move the stalled message to `queue/failed/` and create a new high-priority message to investigate the stall.

### 8.3. Idempotency

All operations should be designed to be idempotent. For example, if an agent attempts to move a file that has already been moved, the operation should not fail. This prevents errors during recovery scenarios where an operation might be retried.

---

## 9. State Management Strategies

### 9.1. State Reconciliation

The filesystem is the single source of truth. An agent starting up or recovering from a crash **MUST** reconcile its internal state by:
1. Scanning all `queue/` subdirectories to rebuild its view of the task landscape.
2. Reading the `_meta/manifest.md` to understand the mission's high-level state.
3. Checking for any messages in `processing/` that are assigned to it, and determining if they are stalled.

### 9.2. Archival

The `queue/completed/` directory can grow large over time. A periodic maintenance task should:
1. Move messages older than a defined threshold (e.g., 7 days) from `completed/` to the `archive/` directory.
2. The `archive/` directory can be compressed or stored in a less expensive storage tier.

---

## 10. Performance Considerations

### 10.1. Filesystem Performance

- The protocol's performance is bound by the underlying filesystem's I/O capabilities.
- For high-throughput scenarios, using an SSD is recommended.
- Avoid placing mission directories on network-mounted drives if latency is a concern.

### 10.2. Message Size

- While the protocol can handle large message bodies, it is more efficient to pass large data blobs by reference.
- Store large files (e.g., datasets, models) in the `context/` or `artifacts/` directories and reference their paths in the message `dependencies`.

---

## 11. Security & Access Control

### 11.1. Filesystem Permissions

Standard filesystem permissions are the primary mechanism for access control. The user account running the agent processes should have appropriate read/write permissions on the `llm/missions/` directory.

### 11.2. Sanitization

Agents **MUST** treat all data read from message files as untrusted input.
- When a message body contains instructions that could lead to dangerous actions (e.g., executing shell commands), the receiving agent must have a strict validation and sandboxing policy.
- Claude, as the orchestrator, is responsible for ensuring that directives sent to Gemini do not contain malicious or unintended commands.

---

## 12. CLI Operations & Utilities

A simple command-line utility could be developed to manage the AC-MQ.

### Example Commands:

- `acmq status {mission-name}`: Displays a summary of messages in each queue.
- `acmq create-mission {mission-name}`: Scaffolds a new mission directory structure.
- `acmq send {mission-name} --to {recipient} --file message.md`: Enqueues a new message from a file.
- `acmq list {mission-name} --queue pending`: Lists the messages in a specific queue.
- `acmq find-stalled {mission-name}`: Finds and reports any messages that have exceeded their timeout in the processing queue.
---
id: a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d
mission_id: system-design-alpha
timestamp: 2025-07-04T10:30:00Z
from: claude
to: gemini
status: pending
priority: 1 # 1 (High) to 5 (Low)
timeout_seconds: 3600
dependencies:
  - "path:./context/architecture-spec.md"
  - "msg:9f8e7d6c-5b4a-4c3d-2b1a-0c9d8e7f6a5b"
summary: "Generate initial data models based on the architecture spec."
---

## 13. Dynamic Event Coalescing and Bus Documents

The AC-MQ protocol extends beyond simple message passing by incorporating dynamic strategies for grouping and summarizing related events. This is achieved through the creation of **Message Bus Documents**, which provide a consolidated, in-memory-friendly view of complex message streams.

### 13.1. The Message Bus Document

A Message Bus Document is a dynamically generated Markdown file that aggregates and summarizes a collection of related AC-MQ messages. These documents live in the `findings/` directory and serve as a higher-level abstraction over individual message files.

**Structure of a Bus Document:**

-   **Header:** Contains metadata about the bus document itself, including the query that generated it and the timestamp of its creation.
-   **Summary Table:** A tabular representation of the messages included in the bus, with key metadata for each message.
-   **Thematic Summaries:** AI-generated summaries of the key themes, findings, and outcomes from the aggregated messages.
-   **Full Message Log:** A concatenated log of the full content of each message included in the bus.

### 13.2. Adaptive Coalescing Strategies

The system uses adaptive, content-aware strategies to determine when and how to create bus documents. This is not a static, time-based process but rather a dynamic one driven by the flow of the mission.

**Coalescing Triggers:**

1.  **Semantic Similarity:** The system uses embedding-based similarity searches to identify clusters of messages discussing similar topics. When a cluster reaches a configurable size, a bus document is generated.
2.  **Dependency Graph Analysis:** By analyzing the `dependencies` field in messages, the system can identify chains or sub-graphs of related tasks. Completed chains are automatically summarized in a bus document.
3.  **Mission Milestone Completion:** When a significant milestone is reached in the `_meta/manifest.md`, the system can be triggered to create a bus document of all messages that contributed to that milestone.
4.  **Agent Request:** An agent can explicitly request the creation of a bus document with a specific query (e.g., "summarize all messages related to database performance").

### 13.3. Example Bus Document

**Filename:** `findings/bus-document-auth-module-20250705120000.md`

```markdown
# Message Bus: Authentication Module Analysis

**Generated:** 2025-07-05T12:00:00Z
**Query:** Dependency graph traversal from message `...-task-1.md`
**Messages Included:** 5

## Summary Table

| Timestamp | From | To | Summary | Status |
| --- | --- | --- | --- | --- |
| 20250704103000 | claude | gemini | Design the database schema for the user auth module. | completed |
| 20250704140000 | gemini | claude | Generated API endpoint code for auth. | completed |
| ... | ... | ... | ... | ... |

## Thematic Summary

The primary focus of this message cluster was the development of the user authentication module. Key outcomes include the finalization of the database schema, the generation of corresponding API endpoints, and the resolution of a performance issue related to password hashing.

## Full Message Log

---
**File:** `...-from-claude-to-gemini.md`

... (full content of the first message) ...

---
**File:** `...-from-gemini-to-claude.md`

... (full content of the second message) ...
```

## 14. Adaptive Queue Merging and State Snapshots

To manage the growth of the `queue/` directories and provide a historical record of mission state, the protocol includes a mechanism for adaptive queue merging.

### 14.1. Queue State Snapshots

A Queue State Snapshot is a tabular summary of a queue (`pending/`, `completed/`, `failed/`) at a specific point in time. These snapshots are stored as Markdown files in the `artifacts/queue-snapshots/` directory.

### 14.2. Adaptive Merging Engine

The system learns the optimal frequency and granularity for creating snapshots based on mission velocity.

-   **High-Velocity Missions:** In missions with a high volume of messages, snapshots are created more frequently but may be less detailed (e.g., only including message summaries).
-   **Low-Velocity Missions:** In slower-paced missions, snapshots are created less frequently but can be more comprehensive, including full message bodies.

The merging engine uses a simple feedback loop: if the number of files in a queue directory exceeds a dynamic threshold (which is adjusted based on the rate of message creation), a merge operation is triggered.

## 15. Self-Organizing Context and Knowledge Bases

The `context/` directory is designed to evolve from a simple file repository into a self-organizing knowledge base. This is an application of the **Self-Organizing Architecture** and **Neocortical Competition** principles from the Atlas bio-computational framework.

### 15.1. Context Clusters

As the number of files in the `context/` directory grows, the system will automatically identify clusters of related documents based on their content. These clusters are then moved into subdirectories, and a `README.md` file is generated at the root of the cluster.

This `README.md` acts as a "bus document" for the context cluster, providing a summary of the documents within it and explaining their relationships.

### 15.2. Example Context Cluster

```
context/
└── database-performance/
    ├── README.md
    ├── analysis-of-query-plans.md
    ├── indexing-strategy.md
    └── benchmark-results.csv
```

The `README.md` in this cluster would contain summaries of the three documents and explain how they relate to the overall topic of database performance.

## 16. Trimodal Reporting and Mission Synthesis

The AC-MQ system can generate three different types of mission reports, corresponding to the **Trimodal Methodology** (Bottom-Up, Top-Down, Holistic). These reports provide different levels of abstraction and are designed for different audiences and purposes.

### 16.1. Bottom-Up: The Detailed Log

-   **Content:** A complete, chronological log of every message in the mission, typically generated as a single, large bus document.
-   **Purpose:** Auditing, debugging, and detailed analysis.
-   **Audience:** Developers, system administrators.

### 16.2. Top-Down: The Executive Summary

-   **Content:** A high-level summary of the mission's progress, key findings, and major artifacts. This report is generated by an AI agent that has been tasked with reading the `_meta/manifest.md` and all major bus documents.
-   **Purpose:** Status updates, strategic review.
-   **Audience:** Project managers, stakeholders.

### 16.3. Holistic: The Integrated Synthesis

-   **Content:** A narrative report that weaves together information from `findings/`, `artifacts/`, and the message queues to tell the story of the mission. It connects the "why" (from the manifest) with the "what" (from the artifacts) and the "how" (from the message logs).
-   **Purpose:** Deep understanding, knowledge transfer, and mission archival.
-   **Audience:** Future agents joining the project, historians.
