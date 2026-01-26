---
name: Project Analysis Chain
description: This skill should be used when the user asks to "analyze project", "deep analysis of codebase", "research chain", "run observers on project", "connector-observers pattern", or needs comprehensive multi-phase analysis of a project using the connector→observers→connector pattern with systematic documentation.
version: 0.1.0
---

# Project Analysis Chain

Execute comprehensive multi-phase analysis of codebases using the connector→observers→connector pattern. This skill automates the systematic decomposition of research work into chains of agents that produce spec-like integrator documents and intermediary connector/observer documents following .atlas organization standards.

## When to Use This Skill

Use this skill when conducting deep analysis of any project that requires:
- Multiple perspective examination (types, logging, platform, infrastructure)
- Systematic documentation following .atlas/AGENT-FILE-ORGANIZATION-GUIDE.md
- Connector-driven workgroup decomposition
- Parallel observer execution
- Final synthesis into comprehensive reports

## Core Workflow

### Phase 1: Initial Connector (Workgroup Decomposition)

Launch a single connector agent to:
1. Analyze the project structure (codebase + relevant docs)
2. Identify focus areas based on user requirements
3. Decompose work into N observer workgroups
4. Output clustering report with observer recommendations

**Connector Output:** `~/.atlas/connector/analysis/{project}/phase1-connector-{focus}-{timestamp}.md`

**Key Responsibilities:**
- Survey project directories (project-root, docs paths)
- Cluster findings into coherent analysis domains
- Recommend observer count (auto-determined based on project size and complexity)
- Define observer roles and scope

### Phase 2: Parallel Observers (Deep Analysis)

Launch N observers in parallel based on Phase 1 recommendations:
- Each observer writes exhaustive analysis to `~/.atlas/observer/analysis/{project}/phase2-observer-{letter}-{focus}-{timestamp}.md`
- Observers run silently without intermediate updates
- All observers must complete before Phase 3

**Observer Responsibilities:**
- Exhaustive examination within assigned scope
- File-by-file or category-by-category analysis
- Evidence collection with file:line citations
- No cross-observer communication

**Naming Convention:** Phase 2 files use letter suffixes (A, B, C, ...) to distinguish parallel observers.

### Phase 3: Final Connector (Synthesis)

Launch a single connector agent to:
1. Read all Phase 2 observer outputs (verification: check file existence, note missing observers)
2. Synthesize findings into comprehensive reports
3. Output integrator-level specifications to `~/.atlas/integrator/specs/{project}/`

**Synthesis Outputs:**
- Timeline documents (if temporal analysis requested)
- Status maps (current implementation state)
- Comparison matrices (e.g., entry points, type mismatches)
- Specification documents (golden path + deviations)

**Key Principle:** Do not read Phase 2 outputs during Phase 2 execution (pass to Phase 3 after verifying existence and location only).

## Usage Parameters

### Required Parameters

**--project** (REQUIRED)
- Project name (atlas, empack, logo-designer, etc.)
- Used to determine project root and organize outputs
- Example: `--project=atlas`

**--focus** (REQUIRED)
- Comma-separated list of analysis areas
- Examples: `types`, `logging`, `platform`, `infrastructure`, `entry-points`, `db-patterns`
- Determines what aspects to analyze
- Example: `--focus=types,logging`

### Optional Parameters

**--project-root** (optional)
- Override default project root path
- Defaults to `~/production/{project}`
- Example: `--project-root=/custom/path/to/project`

**--thoroughness** (optional)
- Analysis depth: `quick`, `medium`, `thorough`
- Defaults to `thorough`
- `quick`: High-level patterns only
- `medium`: Representative samples with patterns
- `thorough`: Exhaustive file-by-file analysis

## Execution Pattern

### Silent Between Links

Execute each phase silently until completion:
1. Launch Phase 1 connector → wait for completion
2. Immediately launch Phase 2 observers (all N in parallel) → wait for all completions
3. Immediately launch Phase 3 connector → wait for completion
4. Report final results to user

**No intermediate status updates** between phases (agents run autonomously).

### Timestamp Format

All outputs use timestamp format: `YYYY-MM-DD-HH-MM`
- Enables multiple analysis runs without conflicts
- Preserves analysis history
- Example: `phase1-connector-types-2026-01-13-17-45.md`

### Output Organization

Follow `~/.atlas/AGENT-FILE-ORGANIZATION-GUIDE.md` patterns:

```
~/.atlas/
├── connector/analysis/{project}/
│   ├── phase1-connector-{focus}-{timestamp}.md
│   └── phase3-connector-{focus}-{timestamp}.md
├── observer/analysis/{project}/
│   ├── phase2-observer-a-{focus}-{timestamp}.md
│   ├── phase2-observer-b-{focus}-{timestamp}.md
│   └── ... (N observers)
└── integrator/specs/{project}/
    ├── {focus}-overview-{timestamp}.md
    ├── {focus}-detailed-{timestamp}.md
    └── ... (synthesis outputs)
```

## Implementation Steps

### Step 1: Parse User Request

Extract parameters from user query:
- Project name (required)
- Focus areas (required, comma-separated)
- Project root (optional, default: `~/production/{project}`)
- Thoroughness (optional, default: `thorough`)

### Step 2: Validate Paths

Verify paths exist:
- Project root directory
- .atlas workspace directory
- Bootstrap file (if exists): `~/.atlas/bootstrap/{project}.md`

### Step 3: Execute Phase 1 Connector

Launch connector agent with task:
```
Analyze {project} focusing on {focus areas}.
Project root: {project-root}
Thoroughness: {thoroughness}

Decompose analysis into N observer workgroups.
Output clustering report to:
~/.atlas/connector/analysis/{project}/phase1-connector-{focus}-{timestamp}.md

Include:
- Identified patterns requiring examination
- Observer count recommendation (N)
- Observer role definitions
- Scope boundaries for each observer
```

Wait for Phase 1 completion.

### Step 4: Execute Phase 2 Observers (Parallel)

Launch N observers in parallel (where N determined by Phase 1 connector):
```
Observer {Letter} Task:
Analyze {specific scope from Phase 1}.
Project root: {project-root}
Thoroughness: {thoroughness}

Output exhaustive analysis to:
~/.atlas/observer/analysis/{project}/phase2-observer-{letter}-{focus}-{timestamp}.md

Do not communicate with other observers.
Do not synthesize across observations (Phase 3 task).
```

Wait for all N observers to complete.

### Step 5: Verify Phase 2 Outputs

Check Phase 2 completion:
- Glob pattern: `~/.atlas/observer/analysis/{project}/phase2-observer-*-{focus}-{timestamp}.md`
- Count files (should be N)
- Note any missing observers
- Do NOT read file contents (pass paths to Phase 3)

### Step 6: Execute Phase 3 Connector

Launch connector agent with task:
```
Synthesize findings from Phase 2 observers.

Observer outputs:
- {list all Phase 2 file paths}

Missing observers (if any): {list}

Output synthesis to:
~/.atlas/integrator/specs/{project}/

Create comprehensive reports:
- Overview documents (high-level synthesis)
- Detailed documents (function-level traces)
- Comparison matrices (entry points, patterns)
- Golden path specifications (ideal + deviations)

Use format based on focus areas:
- types: type-mismatches-{timestamp}.md, type-duplications-{timestamp}.md
- logging: logging-infrastructure-{timestamp}.md, logging-api-mismatches-{timestamp}.md
- platform: application-platform-{timestamp}.md
- infrastructure: watchdog-scheduler-{timestamp}.md
```

Wait for Phase 3 completion.

### Step 7: Report Results

Inform user of completion:
- Phase 1 connector output location
- Phase 2 observer output count and locations
- Phase 3 synthesis output locations
- Summary of findings (high-level only)

## Focus Area Templates

### Types Analysis

**Observer Scopes:**
- Type definitions (interfaces, types, enums)
- Type usage patterns (imports, exports)
- Type mismatches (any, unknown, duplicates)
- Type inference points

**Synthesis Outputs:**
- `type-system-overview-{timestamp}.md`: Overall type architecture
- `type-mismatches-detailed-{timestamp}.md`: Mismatch catalog with fix priorities
- `type-duplications-detailed-{timestamp}.md`: Duplicate type definitions

### Logging Analysis

**Observer Scopes:**
- Logger initialization patterns
- Module name conventions
- Log level usage
- Infrastructure (watchdog, schedulers, OTEL)

**Synthesis Outputs:**
- `logging-infrastructure-overview-{timestamp}.md`: Infrastructure status
- `logging-api-mismatches-detailed-{timestamp}.md`: Inconsistent logger usage
- `logging-module-names-detailed-{timestamp}.md`: Module naming patterns

### Platform Analysis

**Observer Scopes:**
- Runtime environment (Node.js, Bun, etc.)
- Platform-specific code
- Dependency analysis
- Build system configuration

**Synthesis Outputs:**
- `application-platform-overview-{timestamp}.md`: Platform architecture
- `platform-compatibility-detailed-{timestamp}.md`: Platform-specific issues

### Infrastructure Analysis

**Observer Scopes:**
- Watchdog implementation
- Scheduler usage
- OTEL integration
- System monitoring

**Synthesis Outputs:**
- `infrastructure-overview-{timestamp}.md`: Infrastructure status
- `watchdog-scheduler-detailed-{timestamp}.md`: Component analysis

## Auto-Determined Observer Count

Phase 1 connector determines observer count based on:
- Project size (file count, LOC)
- Focus area complexity
- Thoroughness setting
- Available analysis dimensions

**Typical observer counts:**
- Small project (< 50 files): 2-3 observers
- Medium project (50-200 files): 3-5 observers
- Large project (200+ files): 5-8 observers

**Never hardcode observer count** - let connector adapt to project characteristics.

## Quality Standards

### Phase 1 Output

- Must include N (observer count recommendation)
- Must define clear scope boundaries
- Must identify patterns requiring examination
- Must follow connector naming convention

### Phase 2 Outputs

- All N observers must complete
- Each output must follow observer naming convention
- Each output must be exhaustive within scope
- Each output must include file:line citations

### Phase 3 Outputs

- Must synthesize ALL Phase 2 findings
- Must follow integrator naming convention
- Must include golden path specifications
- Must note deviations from ideal state

## Error Handling

### Missing Observer Outputs

If observer fails:
- Note in Phase 3 synthesis
- Continue with available observers
- Report incomplete analysis to user

### Invalid Focus Areas

If focus area not recognized:
- Ask user to clarify
- Suggest valid focus areas
- Do not proceed until clarified

### Path Validation Failures

If project-root doesn't exist:
- Ask user to verify path
- Suggest common locations
- Do not proceed until validated

## Examples

See `examples/` directory for sample invocations and expected outputs.

## Best Practices

1. **Always use timestamps** - Enables history preservation
2. **Silent execution** - No intermediate updates between phases
3. **Parallel observers** - Launch all Phase 2 observers simultaneously
4. **Auto-determine observer count** - Trust Phase 1 connector recommendations
5. **Follow .atlas organization** - Respect AGENT-FILE-ORGANIZATION-GUIDE.md patterns
6. **Golden path documentation** - Always specify ideal state + current deviations
7. **Evidence-based** - All claims must cite file:line sources

## Additional Resources

### Related Files

- `~/.atlas/AGENT-FILE-ORGANIZATION-GUIDE.md` - File organization standards
- `~/.atlas/bootstrap/{project}.md` - Project bootstrap context

### Example Outputs

- `examples/phase1-connector-sample.md` - Sample Phase 1 output
- `examples/phase2-observer-sample.md` - Sample Phase 2 output
- `examples/phase3-synthesis-sample.md` - Sample Phase 3 output

## Success Criteria

Analysis considered successful when:
- All 3 phases complete without errors
- Phase 2 produces N observer outputs (where N from Phase 1)
- Phase 3 synthesis covers all focus areas
- Outputs follow .atlas organization standards
- User can reference specifications for future work

Focus on systematic decomposition, parallel execution, and comprehensive synthesis for effective project analysis.
