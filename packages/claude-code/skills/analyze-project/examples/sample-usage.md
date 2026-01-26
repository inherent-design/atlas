# Sample Usage - analyze-project Skill

## Basic Usage

```
User: Analyze the Atlas project focusing on types and logging

Claude: I'll execute a comprehensive analysis chain for Atlas.

[Executes silently:]
Phase 1: Connector analyzes project, determines 4 observers needed
Phase 2: Launches 4 observers in parallel (types-a, types-b, logging-a, logging-b)
Phase 3: Connector synthesizes findings into specifications

Completed! Analysis outputs:

Phase 1 Connector:
- ~/.atlas/connector/analysis/atlas/phase1-connector-types-logging-2026-01-13-18-30.md

Phase 2 Observers (4):
- ~/.atlas/observer/analysis/atlas/phase2-observer-a-types-2026-01-13-18-30.md
- ~/.atlas/observer/analysis/atlas/phase2-observer-b-types-2026-01-13-18-30.md
- ~/.atlas/observer/analysis/atlas/phase2-observer-c-logging-2026-01-13-18-30.md
- ~/.atlas/observer/analysis/atlas/phase2-observer-d-logging-2026-01-13-18-30.md

Phase 3 Synthesis:
- ~/.atlas/integrator/specs/atlas/type-system-overview-2026-01-13-18-30.md
- ~/.atlas/integrator/specs/atlas/type-mismatches-detailed-2026-01-13-18-30.md
- ~/.atlas/integrator/specs/atlas/logging-infrastructure-overview-2026-01-13-18-30.md
- ~/.atlas/integrator/specs/atlas/logging-api-mismatches-detailed-2026-01-13-18-30.md

Key Findings:
- 23 type duplications found across services layer
- Inconsistent logger module naming (47 variations)
- 5 infrastructure components analyzed (watchdog, scheduler active)
```

## Advanced Usage with Custom Path

```
User: Run deep analysis on my custom project at /opt/myproject, focusing on platform

Claude: [Executes analysis with custom path]

Completed! Analysis outputs for custom project:
- Phase 1: ~/.atlas/connector/analysis/myproject/phase1-connector-platform-2026-01-13-19-15.md
- Phase 2: 3 observers completed
- Phase 3: ~/.atlas/integrator/specs/myproject/application-platform-overview-2026-01-13-19-15.md
```

## Quick Analysis

```
User: Quick analysis of empack focusing on types only

Claude: [Executes with thoroughness=quick]

Completed! Quick analysis:
- Phase 1: Identified 2 observer scopes (type definitions, type usage)
- Phase 2: 2 observers completed high-level pattern analysis
- Phase 3: ~/.atlas/integrator/specs/empack/type-system-overview-2026-01-13-20-00.md

Note: Quick analysis provides pattern-level insights without exhaustive file-by-file examination.
```

## Multiple Focus Areas

```
User: Analyze Atlas: types, logging, platform, infrastructure

Claude: [Executes comprehensive multi-domain analysis]

Completed! Multi-domain analysis:
Phase 1: Determined 6 observers needed
Phase 2: 6 observers (2 types, 2 logging, 1 platform, 1 infrastructure)
Phase 3: 8 specification documents generated

All outputs in ~/.atlas/ following standard organization.
```

## Expected Timeline

- **Small project** (< 50 files): 5-10 minutes
- **Medium project** (50-200 files): 10-20 minutes
- **Large project** (200+ files): 20-40 minutes

Times vary based on thoroughness setting and focus area complexity.

## Parameter Syntax

All parameters can be specified in natural language:

```
"Analyze atlas focusing on types"
→ --project=atlas --focus=types

"Deep analysis of empack: types, logging, and platform"
→ --project=empack --focus=types,logging,platform --thoroughness=thorough

"Quick look at logo-designer types"
→ --project=logo-designer --focus=types --thoroughness=quick

"Analyze my project at /custom/path focusing on infrastructure"
→ --project=myproject --project-root=/custom/path --focus=infrastructure
```

## Output File Naming

All outputs follow strict naming conventions:

**Phase 1:** `phase1-connector-{focus}-{timestamp}.md`
- Example: `phase1-connector-types-logging-2026-01-13-18-30.md`

**Phase 2:** `phase2-observer-{letter}-{focus}-{timestamp}.md`
- Example: `phase2-observer-a-types-2026-01-13-18-30.md`

**Phase 3:** `{focus}-{type}-{timestamp}.md`
- Example: `type-mismatches-detailed-2026-01-13-18-30.md`
- Example: `logging-infrastructure-overview-2026-01-13-18-30.md`

Timestamps ensure multiple runs don't conflict and preserve analysis history.
