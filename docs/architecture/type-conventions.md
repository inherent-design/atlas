# Atlas Type Conventions

**Date:** 2026-01-12
**Status:** Implemented

## Overview

Atlas uses a hybrid naming convention to balance developer experience (TypeScript camelCase) with database schema alignment (SQL snake_case).

## Convention Rules

### Input Parameters (camelCase)

All operation parameters use **camelCase** following TypeScript/JavaScript conventions:

```typescript
interface IngestParams {
  paths: string[]
  recursive?: boolean
  rootDir?: string              // camelCase
  allowConsolidation?: boolean  // camelCase
}
```

**Rationale:**
- Developer-facing API (CLI, RPC)
- TypeScript/JavaScript convention
- Better IDE autocomplete experience

### Output Results (snake_case in domain)

Domain operation results use **snake_case** matching database schemas:

```typescript
interface SearchResult {
  text: string
  file_path: string      // snake_case (matches DB)
  chunk_index: number    // snake_case (matches DB)
  created_at: string     // snake_case (matches DB)
  qntm_key: string       // snake_case (matches DB)
}
```

**Rationale:**
- Aligns with PostgreSQL/Qdrant payload schemas
- No transformation needed when reading from DB
- Preserves database naming conventions

### RPC Protocol (camelCase via DTOs)

RPC JSON-RPC protocol returns **camelCase** via transformation:

```typescript
interface SearchResultDTO {
  text: string
  filePath: string       // transformed from file_path
  chunkIndex: number     // transformed from chunk_index
  createdAt: string      // transformed from created_at
  qntmKey: string        // transformed from qntm_key
}
```

**Rationale:**
- JSON-RPC convention favors camelCase
- External API consistency
- Transformation happens at protocol boundary (router.ts)

## Implementation

### Canonical Types (types.ts)

- **Params**: camelCase (IngestParams, SearchParams, etc.)
- **Results**: snake_case (SearchResult, ConsolidateResult, etc.)

### RPC Protocol (protocol.ts)

- **Params**: Import directly from types.ts (no DTOs needed)
- **Results**: Define DTOs with camelCase transformation

```typescript
// Import param types (no duplication)
import type { IngestParams, SearchParams } from '../../shared/types'

// Define result DTOs (transformation layer)
export interface SearchResultDTO {
  filePath: string  // snake_case → camelCase
  // ...
}
```

### Router (router.ts)

- **Params**: Pass through with spread operator
- **Results**: Map snake_case → camelCase

```typescript
private async handleSearch(params: SearchParams): Promise<SearchResultDTO[]> {
  const results = await this.app.search({ ...params, emit })

  return results.map((r) => ({
    filePath: r.file_path,  // Transform
    // ...
  }))
}
```

## Why This Hybrid Approach?

### Rejected Alternative 1: All camelCase
- **Problem**: Breaks alignment with DB schema
- **Impact**: Requires transformation at storage layer
- **Cost**: Performance overhead, more code

### Rejected Alternative 2: All snake_case
- **Problem**: Violates TypeScript/JavaScript conventions
- **Impact**: Poor developer experience
- **Cost**: Fights against ecosystem tooling

### Chosen Alternative: Hybrid
- **Benefit**: Aligns with conventions at each layer
- **Tradeoff**: Transformation at RPC boundary only
- **Cost**: Minimal (~50 LOC for result DTOs)

## Migration from Previous State

Before this decision, protocol.ts duplicated ALL param types from types.ts with zero transformation. This was pure duplication (~200 LOC) with no benefit.

**Removed:** IngestParamsDTO, SearchParamsDTO, ConsolidateParamsDTO (duplicates)
**Kept:** SearchResultDTO, ConsolidateResultDTO (legitimate transformations)

## References

- Type architecture audit: `~/.atlas/integrator/analysis/atlas/type-architecture-mapping-2026-01-12.md`
- Canonical types: `packages/core/src/shared/types.ts`
- RPC protocol: `packages/core/src/daemon/protocol.ts`
- Router mappings: `packages/core/src/daemon/router.ts`
