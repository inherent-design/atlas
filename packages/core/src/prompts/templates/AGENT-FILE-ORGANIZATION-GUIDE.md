# Agent File Organization Guide

**Version:** 1.0
**Last Updated:** 2025-12-22
**Status:** Active Standard

---

## Quick Reference

**Standard Path Format:**

```
~/production/.atlas/{agent-type}/{output-type}/{project}/{task-name-YYYY-MM-DD}.md
```

**Example:**

```
~/production/.atlas/connector/analysis/logo-designer/token-system-inventory-2025-12-21.md
```

---

## The Hierarchy

### Level 1: Agent Type

**Purpose:** Identify which agent created the file

**Options:**

- `observer/` - Raw sensory data, observations
- `connector/` - Pattern recognition outputs
- `explainer/` - Causal hypotheses, explanations
- `challenger/` - Validation reports, falsification experiments
- `integrator/` - Synthesis, strategic plans
- `orchestrator/` - Multi-agent workflow coordination
- `base/` - Main agent or unattributed work

**Rule:** Use the agent type that **created** the file, not who might read it later.

---

### Level 2: Output Type

**Purpose:** Classify the nature of the content

**Options:**

#### `analysis/`

- Pattern discoveries
- Observations
- Research findings
- Data analysis
- Inventory/audit results

**Examples:**

- Token pattern analysis
- Component inventory
- Semantic layer audit

---

#### `plans/`

- Implementation strategies
- Design specifications
- Roadmaps
- Architecture proposals
- Migration plans

**Examples:**

- Token system redesign plan
- Component refactoring strategy
- Phase-based implementation roadmap

---

#### `validation/`

- Falsification experiments
- Test results
- Verification reports
- Compliance checks
- Quality audits

**Examples:**

- Hypothesis validation
- Token compliance check
- Component correctness verification

---

#### `reports/`

- Final deliverables
- Synthesis documents
- Executive summaries
- Multi-agent workflow outcomes
- Completion reports

**Examples:**

- Orchestrator synthesis
- Project completion report
- Multi-phase workflow summary

---

#### `coordination/`

- Agent handoffs
- Shared context
- Progress tracking
- Checkpoints
- Cross-agent state

**Examples:**

- Phase checkpoints
- Workflow state tracking
- Agent-to-agent context passing

---

### Level 3: Project

**Purpose:** Group files by the problem domain or initiative

**Options:**

#### Active Projects

- `logo-designer/` - Logo designer application work
- `empack/` - Empack Minecraft packaging tool
- `{your-project-name}/` - Other active projects

#### Meta Categories (for non-project work)

- `meta/` - Agent system analysis, framework improvements
- `research/` - Exploratory work, technology assessments
- `experiments/` - POCs, prototypes, one-off explorations

**Rule:**

- If tied to a specific codebase/product → use project name
- If exploratory/one-off → use `research/` or `experiments/`
- If about the agent system itself → use `meta/`

**When to create new project:**

- You're working on a distinct codebase
- The work will span multiple files/sessions
- It's not a one-off exploration

---

### Level 4: Task Name + Date

**Purpose:** Unique, descriptive filename with timestamp

**Format:** `{descriptive-task-name}-YYYY-MM-DD.md`

**Rules:**

1. **Descriptive:** Name should explain what's in the file
2. **Kebab-case:** Use hyphens, lowercase
3. **Date:** Always include ISO date (YYYY-MM-DD)
4. **Unique:** Different from other files in same directory

**Good Examples:**

- `token-system-inventory-2025-12-21.md`
- `aggressive-optimization-discovery-2025-12-21.md`
- `phase-1-token-completion-2025-12-21.md`

**Bad Examples:**

- `analysis.md` ❌ (not descriptive)
- `Token_System_Analysis_12-21-25.md` ❌ (wrong case, wrong date format)
- `report-v2.md` ❌ (no date)

**Iterations:** For updated versions, use `-v2`, `-v3`, etc.:

```
token-audit-2025-12-21.md
token-audit-2025-12-21-v2.md
token-audit-2025-12-21-v3.md
```

---

## Decision Tree

**Use this flowchart to determine the path:**

```
1. Which agent am I?
   ├─ observer → observer/
   ├─ connector → connector/
   ├─ explainer → explainer/
   ├─ challenger → challenger/
   ├─ integrator → integrator/
   ├─ orchestrator → orchestrator/
   └─ main/unknown → base/

2. What type of output is this?
   ├─ Raw findings/patterns → analysis/
   ├─ Strategy/design → plans/
   ├─ Testing/verification → validation/
   ├─ Final deliverable → reports/
   └─ Agent coordination → coordination/

3. What project is this for?
   ├─ Logo designer → logo-designer/
   ├─ Empack → empack/
   ├─ Agent system → meta/
   ├─ Technology research → research/
   ├─ One-off exploration → experiments/
   └─ New codebase → create new project/

4. Descriptive name + date
   → {task-name}-YYYY-MM-DD.md
```

---

## Agent-Specific Guidelines

### Observer

**Typical outputs:** Raw observations, sensor readings, data collection

**Common paths:**

```
observer/analysis/{project}/{observation-topic-YYYY-MM-DD}.md
observer/coordination/{project}/{checkpoint-name-YYYY-MM-DD}.md
```

**Example:**

```
observer/analysis/logo-designer/colorpicker-rendering-2025-12-21.md
```

---

### Connector

**Typical outputs:** Pattern discoveries, similarity analysis, clustering

**Common paths:**

```
connector/analysis/{project}/{pattern-analysis-YYYY-MM-DD}.md
connector/reports/{project}/{pattern-synthesis-YYYY-MM-DD}.md
```

**Example:**

```
connector/analysis/logo-designer/token-system-pattern-analysis-2025-12-21.md
```

---

### Explainer

**Typical outputs:** Causal hypotheses, rationale, WHY explanations

**Common paths:**

```
explainer/analysis/{project}/{hypothesis-topic-YYYY-MM-DD}.md
explainer/reports/{project}/{explanation-synthesis-YYYY-MM-DD}.md
```

**Example:**

```
explainer/analysis/logo-designer/base-wrapper-hypothesis-2025-12-21.md
```

---

### Challenger

**Typical outputs:** Validation reports, falsification experiments, test results

**Common paths:**

```
challenger/validation/{project}/{validation-topic-YYYY-MM-DD}.md
challenger/reports/{project}/{validation-summary-YYYY-MM-DD}.md
```

**Example:**

```
challenger/validation/logo-designer/token-system-audit-validation-2025-12-21.md
```

---

### Integrator

**Typical outputs:** Strategic plans, synthesis, implementation specs

**Common paths:**

```
integrator/plans/{project}/{implementation-plan-YYYY-MM-DD}.md
integrator/reports/{project}/{synthesis-report-YYYY-MM-DD}.md
```

**Example:**

```
integrator/plans/logo-designer/base-ui-theming-strategy-2025-12-21.md
```

---

### Orchestrator

**Typical outputs:** Multi-agent workflow reports, phase coordination

**Common paths:**

```
orchestrator/coordination/{project}/{workflow-state-YYYY-MM-DD}.md
orchestrator/reports/{project}/{workflow-synthesis-YYYY-MM-DD}.md
```

**Example:**

```
orchestrator/reports/logo-designer/token-system-complete-rebuild-2025-12-21.md
```

---

### Base Agent (Main Claude)

**Typical outputs:** Mixed work, high-level coordination, user-facing deliverables

**Common paths:**

```
base/plans/{project}/{feature-plan-YYYY-MM-DD}.md
base/reports/{project}/{project-status-YYYY-MM-DD}.md
base/coordination/{project}/{checkpoint-YYYY-MM-DD}.md
```

**Example:**

```
base/plans/logo-designer/ui-primitive-component-progression.md
```

---

## Special Directories

### signals/ - Meta-Learning System

**Purpose:** Capture agent failures, extract lessons, improve agent performance over time

**When this was created:**signals/ directory was added 2026-01-08, inspired by Daniel Miessler's Personal AI Infrastructure (PAI) signal-based learning loops.

**Structure:**

```
signals/
├── failures/         [HOT] New error reports when agents block/fail
├── learnings/        [WARM] Extracted lessons (human-reviewed before ingestion)
│   ├── observer/
│   ├── connector/
│   ├── explainer/
│   ├── challenger/
│   └── integrator/
├── consolidated/     [COLD] Cross-agent patterns (3+ agents affected)
└── archive/          [COLD] Processed signals
    └── YYYY-MM/
```

**When to use signals/failures/:**

- Agent reports `STATUS: Blocked`
- Agent errors or times out
- Agent produces incorrect output (caught by validation)
- Agent takes excessive time/tokens (performance issue)

**When NOT to use signals/:**

- Agent completes successfully (→ use normal `{agent}/{output-type}/{project}/`)
- Agent finds zero results (that's valid, not a failure)
- User changes requirements mid-task (not agent failure)

**Workflow:**

1. **Capture:** Write failure to `signals/failures/{agent}-{issue}-{date}.md`
2. **Auto-ingest:** Daemon watches and ingests to Qdrant with `content_type: signal`
3. **Pattern detection:** When 3+ similar failures detected, trigger learning extraction
4. **Extract:** LLM analyzes failures → generates lesson → writes to `signals/learnings/{agent}/`
5. **Human review:** Review learning before it's ingested to Qdrant
6. **Apply:** Next agent spawn queries Qdrant for recent learnings for that role

**Example paths:**

```
signals/failures/observer-grep-pattern-miss-2026-01-08.md
signals/learnings/observer/regex-pattern-variants.md
```

**Templates:** See `integrator/plans/meta/substrate-pai-implementation-templates-2026-01-08.md`

---

### bootstrap/ - Project Contexts

**Purpose:** Standardized project context for agent spawns (Telos-style)

**Structure:** `bootstrap/{project}.md`

**Contents:**

- Mission (what/who/why)
- Goals (measurable outcomes)
- Problems (current issues + approaches)
- KPIs (metrics with targets)
- Technical infrastructure (stack, constraints)
- Strategic approaches (how we work)

**When to create:**

- Starting new project
- Major project milestone
- Quarterly context updates

**Usage:** Read on agent spawn to inject full project context in <1k tokens

**Example:** `bootstrap/logo-designer.md`

---

### evidence/ - Curated Facts

**Purpose:** High-confidence findings worth preserving separately (Substrate-style)

**Structure:** `evidence/{project}/{fact-name-date}.md`

**Criteria for evidence files:**

- Confidence ≥ 0.95 (Very High)
- Referenced frequently
- Baseline for future work
- Worth curating separately

**When to use:**

- Challenger validation with very high confidence
- Audit results (e.g., "token compliance: 73%")
- Performance benchmarks
- Architecture decisions

**Example:** `evidence/logo-designer/token-audit-2025-12-21.md`

---

### daemon/ - Runtime Files

**Purpose:** Daemon process state and runtime files (NOT ingested to Qdrant)

**Structure:**

```
daemon/
├── atlas.sock      # Unix domain socket (daemon IPC)
├── atlas.pid       # Process ID file
├── atlas.db        # SQLite database (file tracking, hashes)
└── daemon.log      # Daemon process logs (optional)
```

**Managed by:** Atlas daemon automatically (DO NOT manually edit)

**When created:** Automatically when daemon starts

**Ignored by:** File watcher (these are not semantic knowledge)

---

## Archive Strategy

**Current approach:** No separate archive directory. Old work stays in place.

**Rationale:**

- Qdrant already handles semantic deduplication via consolidation
- File age tracked via `created_at` and `last_accessed_at` metadata
- Temperature tiers (hot/warm/cold) distinguish recent from stale
- Can filter by date in searches: `--since 2025-01-01`

**If you must archive:**

- Add prefix to filename: `ARCHIVED-{original-name}.md`
- Or move to subdirectory within project: `{project}/archive-2024/`
- File watcher will still ingest (but marked with old timestamp)

---

## Finding Files

### By Agent Type

```bash
# All connector outputs across all projects
ls .atlas/connector/analysis/*/

# All challenger validations for logo-designer
ls .atlas/challenger/validation/logo-designer/
```

### By Project

```bash
# All logo-designer work across all agents
find .atlas -path "*/logo-designer/*" -name "*.md"

# All token-related work
find .atlas -name "*token*" -name "*.md"
```

### By Output Type

```bash
# All analysis outputs
find .atlas -path "*/analysis/*" -name "*.md"

# All validation reports
find .atlas -path "*/validation/*" -name "*.md"
```

### By Date

```bash
# All work from 2025-12-21
find .atlas -name "*2025-12-21.md"

# Recent work (last 7 days)
find .atlas -name "*.md" -mtime -7
```

---

## Cross-References

**When referencing other files in your output:**

Use relative paths from .atlas root:

```markdown
See connector analysis: `connector/analysis/logo-designer/token-patterns-2025-12-21.md`
Previous validation: `challenger/validation/logo-designer/token-audit-2025-12-20.md`
```

**When reading files in prompts:**

```
Read previous connector output:
~/production/.atlas/connector/analysis/logo-designer/token-patterns-2025-12-21.md
```

---

## Migration Notes

**For existing files (during migration):**

1. Identify agent type, output type, project
2. Create directory structure if needed:
   ```bash
   mkdir -p .atlas/{agent}/{output-type}/{project}
   ```
3. Move file to new location
4. Update any references in other files
5. Add redirect note in old location (optional)

**Redirect note template:**

```markdown
# MOVED

This file has been relocated to:
`{new-path}`

Date moved: 2025-12-22
```

---

## Special Cases

### Multi-Agent Workflows

If a file is the result of multiple agents (orchestrator coordinating connector + integrator):

- Primary agent: orchestrator
- Output type: reports (final deliverable)
- Note in file metadata which agents contributed

### Temporary Working Files

For ephemeral coordination:

- Use `coordination/` output type
- Clean up after workflow completes
- Or archive when no longer needed

### Large Multi-Phase Projects

For projects with many phases/checkpoints:

- Use descriptive phase names in filename
- Example: `phase-1-token-completion-2025-12-21.md`
- Keep all phases in same project directory

---

## File Metadata

**Recommended frontmatter for all files:**

```markdown
---
agent: connector
output_type: analysis
project: logo-designer
task: token-system-pattern-analysis
date: 2025-12-21
iteration: 1
related_files:
  - observer/analysis/logo-designer/token-inventory-2025-12-20.md
  - challenger/validation/logo-designer/token-audit-2025-12-21.md
---

# Token System Pattern Analysis

...
```

**Benefits:**

- Programmatic file discovery
- Easier to track workflows
- Clear provenance

---

## Validation Checklist

Before saving a file, verify:

- [ ] Path follows `{agent}/{output-type}/{project}/{name-YYYY-MM-DD}.md`
- [ ] Agent type matches who created it
- [ ] Output type matches content nature
- [ ] Project is correct (or meta/research/experiments)
- [ ] Filename is descriptive + has date
- [ ] Directory structure exists (create if needed)
- [ ] File doesn't duplicate an existing file
- [ ] Frontmatter metadata is present (optional but recommended)

---

## Examples by Use Case

### Use Case: Token System Audit

**Workflow:** observer → connector → integrator → challenger

**Files created:**

```
observer/analysis/logo-designer/token-usage-observations-2025-12-21.md
connector/analysis/logo-designer/token-pattern-clusters-2025-12-21.md
integrator/plans/logo-designer/token-remediation-strategy-2025-12-21.md
challenger/validation/logo-designer/token-compliance-check-2025-12-21.md
orchestrator/reports/logo-designer/token-audit-complete-2025-12-21.md
```

---

### Use Case: Component Refactoring

**Workflow:** connector → integrator → challenger

**Files created:**

```
connector/analysis/logo-designer/component-deduplication-patterns-2025-12-21.md
integrator/plans/logo-designer/recipe-consolidation-plan-2025-12-21.md
challenger/validation/logo-designer/refactor-correctness-check-2025-12-21.md
```

---

### Use Case: Technology Research

**Workflow:** observer (web research) → integrator (synthesis)

**Files created:**

```
observer/analysis/research/shadcn-component-patterns-2025-12-20.md
integrator/reports/research/ui-library-comparison-2025-12-20.md
```

---

### Use Case: Exploratory POC

**Single agent:** integrator

**Files created:**

```
integrator/reports/experiments/color-harmony-musical-ratios-2025-12-21.md
```

---

## Common Mistakes to Avoid

❌ **Mixing output types in filename**

```
connector-validation-report-2025-12-21.md
```

Use output-type directory instead.

---

❌ **Creating files at wrong level**

```
.atlas/logo-designer-token-analysis.md  # Wrong: at root
```

Should be:

```
.atlas/connector/analysis/logo-designer/token-analysis-2025-12-21.md
```

---

❌ **Vague project names**

```
.atlas/connector/analysis/project1/...
```

Use descriptive project names.

---

❌ **Missing dates**

```
token-analysis.md  # Can't tell when created
```

Always include: `token-analysis-2025-12-21.md`

---

❌ **Wrong agent attribution**

```
# Created by connector, but saved to integrator/
```

Use the agent that created it, not the intended reader.

---

## Questions?

**Q: What if I can't determine the project?**
A: Use `meta/` if it's about the agent system, `research/` if exploratory, or `experiments/` for one-offs.

**Q: Can I create subdirectories within project/?**
A: Yes, for large projects with many files:

```
.atlas/connector/analysis/logo-designer/tokens/...
.atlas/connector/analysis/logo-designer/components/...
```

**Q: What about non-markdown files?**
A: Follow same hierarchy, adjust extension:

```
.atlas/connector/analysis/logo-designer/data-export-2025-12-21.json
```

**Q: Should I update this guide?**
A: Yes! This is a living document. Propose changes via pull request or agent collaboration.

---

## Summary

**The Golden Rule:**

> Every file should have ONE clear agent, ONE clear output type, ONE clear project, and ONE clear purpose.

**Path Templates:**

**Regular agent outputs:**

```
.atlas/{agent}/{output-type}/{project}/{descriptive-name-YYYY-MM-DD}.md
```

**Special directories:**

```
.atlas/signals/failures/{agent}-{issue}-{date}.md          # Error captures
.atlas/signals/learnings/{agent}/{pattern-name}.md         # Extracted lessons
.atlas/bootstrap/{project}.md                              # Project contexts
.atlas/evidence/{project}/{fact-name-date}.md              # Curated facts
.atlas/daemon/                                             # Runtime files (auto-managed)
```

**When in doubt:**

1. Ask: "Is this a failure/error?" → `signals/failures/`
2. Ask: "Is this a systematic lesson?" → `signals/learnings/{agent}/`
3. Ask: "Is this project context?" → `bootstrap/`
4. Ask: "Is this a curated fact?" → `evidence/`
5. Otherwise: "Who created this?" → agent type
6. Ask: "What is this?" → output type
7. Ask: "What project?" → project name
8. Describe it clearly + add date → filename

**Quick decision tree:**

```
Is it a failure/blocker? → signals/failures/
  └─ No
     Is it a learned pattern? → signals/learnings/
       └─ No
          Is it project context? → bootstrap/
            └─ No
               Is it high-confidence fact? → evidence/
                 └─ No
                    Regular output → {agent}/{output-type}/{project}/
```

---

**End of Guide**
**Last Updated:** 2026-01-08
**Changes:** Added signals/, bootstrap/, evidence/, daemon/ directories; removed archive/; migrated old files to proper structure
