# Atlas Codebase Pattern Clusters - 2025-12-29

**STATUS**: Complete
**PROGRESS**: Detected 5 major pattern clusters from Observer findings
**BLOCKERS**: None
**QUESTIONS**: None
**NEXT**: N/A (task complete)

---

## Executive Summary

Analyzed Observer's findings from Atlas TypeScript codebase. Clustered 189/196 passing tests with 7 failures, ~143 lines of duplicated batch processing code, coverage gaps in consolidate.ts (396 lines, 0%), and 78 import statements across 23 files.

**Key Patterns Identified**:
1. **TEST FIXES** - 7 failures in qntm/providers.test.ts due to stale mocks after LLM extraction refactoring
2. **DEDUPLICATION** - 90% identical code in llm/batch.ts and qntm/batch.ts (~143 lines duplicated)
3. **COVERAGE PRIORITIES** - consolidate.ts (0%), llm/providers.ts (low), clients/*.ts (no tests)
4. **ORGANIZATION** - Singleton pattern with reset() methods, circular system.ts ↔ watchdog.ts concern
5. **IMPLEMENTATION PLAN** - Ordered execution sequence with dependency tracking

---

## CLUSTER 1: TEST FIXES

### Pattern Description
All 7 failing tests in `qntm/providers.test.ts` share same root cause: stale mocks after LLM extraction refactoring. Tests mock `./providers` module at global scope, but when `llm/batch.test.ts` runs first in test suite, its mocks pollute the module cache affecting downstream tests.

**Similarity**: Mock isolation failures when running full suite (not when running file in isolation)

**Confidence**: 0.95

**Cluster size**: 7 test failures

### Files Affected
- `src/qntm/providers.test.ts` (350 lines) - All 7 failures
- `src/llm/batch.test.ts` (675 lines) - Source of mock pollution

### Test Failures
```
1. qntm-providers > generateQNTMKeysWithProvider > anthropic provider > generates keys via Claude API
   - Error: expect() mismatch on result.keys
   - Line: 51-62

2. qntm-providers > generateQNTMKeysWithProvider > anthropic provider > includes existing keys in prompt
   - Error: capturedPrompt undefined
   - Line: 64-102

3. qntm-providers > generateQNTMKeysWithProvider > ollama provider > generates keys via Ollama API
   - Error: expect() mismatch on result.keys
   - Line: 106-143

4. qntm-providers > generateQNTMKeysWithProvider > ollama provider > uses correct Ollama request format
   - Error: capturedBody undefined
   - Line: 145-172

5. qntm-providers > generateQNTMKeysWithProvider > ollama provider > handles Ollama API errors
   - Error: expect().rejects not throwing
   - Line: 174-190

6. qntm-providers > generateQNTMKeysWithProvider > throws on unknown provider
   - Error: expect().rejects not throwing
   - Line: 193-199

7. qntm-providers > generateQNTMKeysWithProvider > includes context in prompt when provided
   - Error: capturedPrompt undefined
   - Line: 201-227
```

### Root Cause Analysis

**Before refactoring**: `qntm/providers.ts` contained direct LLM implementation
**After refactoring**: `qntm/providers.ts` imports from `llm/providers.ts` (line 9)

**Mock conflict**:
```typescript
// llm/batch.test.ts:36-47
mock.module('./providers', () => ({
  completeJSON: mockCompleteJSON,
}))

// qntm/providers.test.ts uses same global mock registry
// When llm/batch.test.ts runs first, its mock persists
```

**Why tests fail in suite but pass in isolation**:
- Bun's `mock.module()` uses global module cache
- First test file to mock a module "wins" for entire suite
- qntm/providers.test.ts mocks get ignored when llm/batch.test.ts runs first

### Concrete Fixes Needed

**Option A: Scoped mocks (recommended)**
```typescript
// qntm/providers.test.ts
beforeEach(() => {
  mock.module('../llm/providers', () => ({
    completeJSON: mockCompleteJSON,
    checkOllamaAvailable: mockCheckOllama,
    detectProvider: mockDetectProvider,
  }))
})

afterEach(() => {
  // Reset module mocks between tests
  mock.restore()
})
```

**Option B: Mock at higher level**
```typescript
// Mock llm/providers instead of qntm/providers
// Since qntm/providers is now a thin wrapper
import { completeJSON } from '../llm'
// Mock '../llm' module instead
```

**Option C: Use dependency injection**
```typescript
// Pass completeJSON as parameter instead of importing
export async function generateQNTMKeysWithProvider(
  input: QNTMGenerationInput,
  config: LLMConfig,
  completeFn = completeJSON  // Injectable for testing
): Promise<QNTMGenerationResult>
```

### Estimated Changes
- **Files**: 2 (qntm/providers.test.ts, possibly qntm/providers.ts)
- **Lines**: 20-30 lines (add beforeEach/afterEach hooks, update mock paths)
- **Complexity**: Low (mock refactoring, no logic changes)

---

## CLUSTER 2: DEDUPLICATION

### Pattern Description
`llm/batch.ts` and `qntm/batch.ts` implement identical pressure-aware batch processing with adaptive concurrency. Only differences: domain-specific prompt building and default result handling. 90% code overlap (~143 lines duplicated).

**Similarity**: Exact structural match - same imports, same retry config, same getConcurrency(), same system assessment, same AdaptiveConcurrencyController usage

**Confidence**: 0.98

**Cluster size**: 2 files

### Code Comparison

**Identical sections**:
```
Lines 10-32:  Imports (pRetry, system, watchdog, logger)
Lines 20-32:  RETRY_OPTIONS configuration
Lines 34-42:  BatchResult<T> interface
Lines 48-72:  getConcurrency() function (near-identical)
Lines 96-109: System capacity assessment
Lines 111-130: AdaptiveConcurrencyController setup
Lines 132-161: Batch processing loop with controller.run()
Lines 168-180: Success/failure counting and logging
Lines 188-192: finally { controller.stopWatchdog() }
```

**Only differences**:
```typescript
// llm/batch.ts
completeBatch<I, O>(
  inputs: I[],
  buildPrompt: (input: I, index: number) => string,  // Generic prompt builder
  config: LLMConfig,
  defaultResult: (input: I, error: Error) => O
)

// qntm/batch.ts
generateQNTMKeysBatch(
  inputs: QNTMGenerationInput[]  // Domain-specific input type
): Promise<QNTMGenerationResult[]>
// Uses generateQNTMKeys() internally
```

### Single Source of Truth Proposal

**Extract to**: `src/batch.ts` (new file)

```typescript
/**
 * Generic batch processor with adaptive concurrency
 * Core infrastructure for pressure-aware LLM batching
 */

export interface BatchProcessor<I, O> {
  process: (input: I, index: number) => Promise<O>
  defaultResult?: (input: I, error: Error) => O
}

export async function processBatch<I, O>(
  inputs: I[],
  processor: BatchProcessor<I, O>,
  options?: {
    concurrencyEnvVar?: string
    modelProvider?: 'ollama' | 'anthropic'
    modelName?: string
    ollamaHost?: string
  }
): Promise<BatchResult<O>>
```

**Usage after refactoring**:
```typescript
// llm/batch.ts - becomes thin wrapper
export async function completeBatch<I, O>(
  inputs: I[],
  buildPrompt: (input: I, index: number) => string,
  config: LLMConfig,
  defaultResult: (input: I, error: Error) => O
): Promise<BatchResult<O>> {
  return processBatch(inputs, {
    process: async (input, index) => {
      const prompt = buildPrompt(input, index)
      return await completeJSON<O>(prompt, config)
    },
    defaultResult,
  }, {
    concurrencyEnvVar: 'LLM_CONCURRENCY',
    modelProvider: config.provider,
    modelName: config.model,
    ollamaHost: config.ollamaHost,
  })
}

// qntm/batch.ts - becomes thin wrapper
export async function generateQNTMKeysBatch(
  inputs: QNTMGenerationInput[]
): Promise<QNTMGenerationResult[]> {
  return processBatch(inputs, {
    process: (input) => generateQNTMKeys(input),
    defaultResult: (input, error) => ({
      keys: [],
      reasoning: `Failed after retries: ${error.message}`,
    }),
  }, {
    concurrencyEnvVar: 'QNTM_CONCURRENCY',
    modelProvider: getLLMConfig().provider,
    modelName: getLLMConfig().model,
  })
}
```

### Files Affected
- `src/batch.ts` (NEW) - 150 lines (extracted common logic)
- `src/llm/batch.ts` (MODIFY) - Reduce from 194 to ~40 lines (wrapper)
- `src/qntm/batch.ts` (MODIFY) - Reduce from 193 to ~35 lines (wrapper)
- `src/llm/batch.test.ts` (MODIFY) - Update to test wrapper behavior
- `src/qntm/batch.test.ts` (NEW) - Add tests for QNTM batch wrapper
- `src/batch.test.ts` (NEW) - Test core batch processing logic

### Estimated Changes
- **Net lines**: +150 (new batch.ts) - 143 (deduplication) - 10 (test updates) = -3 lines
- **Files created**: 2 (batch.ts, batch.test.ts)
- **Files modified**: 3 (llm/batch.ts, qntm/batch.ts, llm/batch.test.ts)
- **Complexity**: Medium (requires careful abstraction to preserve behavior)

---

## CLUSTER 3: COVERAGE PRIORITIES

### Pattern Description
Modules with core business logic have 0% or low test coverage. These require dedicated test suites to reach 70%+ threshold.

**Similarity**: Untested or under-tested modules with complex logic (not thin wrappers)

**Confidence**: 0.92

**Cluster size**: 4 high-priority modules

### High Priority (Core Logic, 0% Coverage)

**1. consolidate.ts (396 lines)**
```
Functions needing tests:
- buildConsolidationPrompt(text1, text2, keys1, keys2, created1, created2): string
  Line 55-110 (prompt building logic)

- classifyConsolidation(payload1, payload2): Promise<ConsolidationClassification>
  Line 115-149 (LLM-based classification with fallback)

- findCandidates(threshold, limit): Promise<ConsolidateCandidate[]>
  Line 157-235 (vector similarity search with deduplication)

- performConsolidation(candidates): Promise<{consolidated, deleted}>
  Line 246-347 (QNTM key merging, payload updates)

- consolidate(config): Promise<ConsolidateResult>
  Line 352-395 (main orchestration)
```

**Coverage gaps**:
- Prompt template correctness (line 63-109)
- LLM classification fallback logic (line 138-148)
- Pair deduplication algorithm (line 208-210)
- QNTM key union logic (line 295-297)
- Soft delete vs hard delete behavior (line 322-325)

**Test file**: `src/consolidate.test.ts` (NEW)
**Estimated lines**: 450-550 lines (comprehensive test suite)

**2. llm/providers.ts (283 lines)**
```
Functions needing tests:
- completeViaAnthropic(prompt, model, jsonMode): Promise<CompletionResult>
  Line 38-109 (Bun.spawn, stdin/stdout handling, markdown stripping)

- completeViaOllama(prompt, model, host, jsonMode, temp, maxTokens): Promise<CompletionResult>
  Line 114-181 (fetch API, error handling, usage tracking)

- complete(prompt, config): Promise<CompletionResult>
  Line 186-209 (router logic)

- completeJSON<T>(prompt, config): Promise<T>
  Line 214-249 (JSON parsing with error handling)

- checkOllamaAvailable(host): Promise<boolean>
  Line 254-264 (already partially tested)

- detectProvider(host): Promise<LLMProvider>
  Line 269-282 (already partially tested)
```

**Coverage gaps**:
- Markdown code fence stripping (line 95-101)
- Ollama format: 'json' in request body (line 137-139)
- JSON parse failure error messages (line 240-248)
- Claude CLI stderr handling (line 76, 82)

**Note**: Some coverage exists from `qntm/providers.test.ts` (tests imported functions), but direct provider tests missing

**Test file**: `src/llm/providers.test.ts` (NEW)
**Estimated lines**: 400-500 lines

### Medium Priority (Partial Coverage)

**3. qntm/batch.ts (193 lines)**
**Current coverage**: Indirectly tested via integration tests, no dedicated unit tests

**Test file**: `src/qntm/batch.test.ts` (NEW) - After deduplication
**Estimated lines**: 150-200 lines (test wrapper behavior)

### Low Priority (Thin Wrappers)

**4. clients/*.ts (Total: 70 lines across 3 files)**
```
src/clients/qdrant.ts    - 33 lines (singleton wrapper)
src/clients/voyage.ts    - 37 lines (singleton wrapper)
src/clients/splitter.ts  - Similar pattern
src/clients/index.ts     - 29 lines (re-exports + resetClients())
```

**Coverage gaps**:
- Singleton initialization (already trivial)
- reset() methods (used in existing tests)
- Error handling (VOYAGE_API_KEY missing - line 12-14)

**Test priority**: LOW (simple wrappers, high-value tests elsewhere)

**If tested**:
- `src/clients/clients.test.ts` (NEW)
- Estimated lines: 100-150 lines (singleton behavior, reset(), error paths)

### Coverage Summary

| Module | Lines | Current | Target | Tests Needed |
|--------|-------|---------|--------|--------------|
| consolidate.ts | 396 | 0% | 70%+ | 450-550 lines |
| llm/providers.ts | 283 | Low | 70%+ | 400-500 lines |
| qntm/batch.ts | 193 | Indirect | 70%+ | 150-200 lines |
| clients/*.ts | 70 | 0% | 50%+ | 100-150 lines (LOW priority) |

**Total estimated test lines**: 1,100-1,400 lines across 4 new test files

---

## CLUSTER 4: ORGANIZATION

### Pattern Description
Structural patterns requiring attention: singleton management, import organization, circular dependency risk.

**Similarity**: Architectural patterns that affect testability, maintainability, and module boundaries

**Confidence**: 0.88

**Cluster size**: 3 organizational patterns

### 4.1 Singleton Pattern with reset() Methods

**Files using pattern**:
```
src/clients/qdrant.ts:20-32    - qdrantClientInstance + resetQdrantClient()
src/clients/voyage.ts:24-36    - voyageClientInstance + resetVoyageClient()
src/clients/splitter.ts        - Similar pattern (unverified)
src/clients/index.ts:20-28     - Unified resetClients()
```

**Pattern structure**:
```typescript
let clientInstance: ClientType | null = null

export function getClient(): ClientType {
  if (!clientInstance) {
    clientInstance = createClient()
  }
  return clientInstance
}

export function resetClient(): void {
  clientInstance = null
}
```

**Why this matters**:
- 6 singleton patterns across codebase (Observer finding)
- All have reset() methods for testing
- Unified reset in clients/index.ts (line 20-28)

**Current state**: GOOD (consistent pattern, testable, centralized reset)

**Improvement opportunities**:
- Document singleton usage pattern (why lazy initialization?)
- Consider dependency injection for better testability
- Ensure all singletons registered in resetClients()

**Estimated changes**: 0 lines (pattern already consistent)

### 4.2 Import Organization

**Total**: 78 import statements across 23 files

**Heaviest importers** (from grep analysis):
```
src/consolidate.ts:14-18       - 5 imports
src/ingest.ts:8-18             - 11 imports (heaviest)
src/search.ts:8-20             - 4 imports
src/llm/batch.ts:10-15         - 6 imports
src/qntm/batch.ts:8-17         - 10 imports
```

**Import pattern analysis**:
- **Internal modules**: Most imports from './clients', './config', './logger'
- **External deps**: pRetry, systeminformation, voyageai, @qdrant/js-client-rest
- **Type imports**: Consistent use of `import type` for type-only imports
- **Re-exports**: clients/index.ts, llm/index.ts, qntm/index.ts use barrel pattern

**Current state**: GOOD (organized, barrel exports, type imports)

**Potential issue**: Deep import chains
```
qntm/batch.ts imports:
  → qntm/index.ts (generateQNTMKeys)
    → qntm/providers.ts
      → llm/providers.ts (completeJSON)
        → logger.ts
```

**Improvement opportunities**:
- None critical (imports are well-organized)
- Consider import cost analysis if build time becomes issue

**Estimated changes**: 0 lines (acceptable as-is)

### 4.3 Circular Dependency Risk

**Observed concern**: system.ts ↔ watchdog.ts

**Investigation**:
```typescript
// src/system.ts imports watchdog?
grep "import.*watchdog" src/system.ts
// Result: No direct import found in grep

// src/watchdog.ts:16
import { assessSystemCapacity, type PressureLevel } from './system'
```

**Actual dependency**: watchdog.ts → system.ts (one-way, SAFE)

**Why flagged as circular**:
- Observer may have detected conceptual coupling (both deal with system resources)
- AdaptiveConcurrencyController in watchdog.ts uses assessSystemCapacity()
- system.ts may log about watchdog activity (indirect reference)

**Current state**: NO CIRCULAR DEPENDENCY (grep confirms one-way import)

**Estimated changes**: 0 lines (false positive)

### Organization Summary

| Pattern | Files | Status | Action Needed |
|---------|-------|--------|---------------|
| Singleton reset() | 6 | ✅ Good | Document pattern |
| Import organization | 23 | ✅ Good | None |
| Circular dependency | 2 | ✅ Safe | None (false positive) |

**Total estimated changes**: 0 lines (organization already good)

---

## CLUSTER 5: IMPLEMENTATION PLAN

### Pattern Description
Execution order with dependency tracking to avoid breaking changes. Groups ordered by prerequisite relationships.

**Similarity**: All implementation tasks share dependency on completing previous fixes first

**Confidence**: 0.90

**Cluster size**: 5 implementation phases

### Phase 1: Test Fixes (BLOCKING - do first)

**Why first**: Broken tests prevent confident refactoring

**Tasks**:
1. Fix qntm/providers.test.ts mock isolation (Option A: scoped mocks)
2. Verify all 7 tests pass in isolation AND in suite
3. Run full test suite: `bun test`

**Dependencies**: None

**Deliverables**:
- ✅ 196/196 tests passing
- ✅ Mock isolation documented in test file comments

**Estimated effort**: 1-2 hours

**Files changed**:
- `src/qntm/providers.test.ts` (20-30 lines modified)

---

### Phase 2: Deduplication (BLOCKING - enables coverage)

**Why second**: Consolidating batch logic reduces test surface area before writing coverage tests

**Tasks**:
1. Extract common batch logic to `src/batch.ts`
2. Refactor `llm/batch.ts` to use generic processor
3. Refactor `qntm/batch.ts` to use generic processor
4. Update `llm/batch.test.ts` to test wrapper
5. Create `src/batch.test.ts` for core logic
6. Verify behavior unchanged: run all tests

**Dependencies**: Phase 1 (need passing tests to verify refactor)

**Deliverables**:
- ✅ Single source of truth for batch processing
- ✅ -143 lines of duplication removed
- ✅ All existing tests still passing
- ✅ New tests for core batch logic

**Estimated effort**: 4-6 hours

**Files changed**:
- `src/batch.ts` (NEW, 150 lines)
- `src/batch.test.ts` (NEW, 200-250 lines)
- `src/llm/batch.ts` (MODIFY, -154 lines to ~40 lines)
- `src/qntm/batch.ts` (MODIFY, -158 lines to ~35 lines)
- `src/llm/batch.test.ts` (MODIFY, update imports/assertions)

**Risks**:
- Behavioral changes in edge cases (need thorough testing)
- Performance regression (verify concurrency control still works)

---

### Phase 3: High-Priority Coverage (PARALLEL - can split work)

**Why third**: Now that test infrastructure is stable and deduplication done, add coverage

**Tasks**:
1. **Task 3A**: Write `src/consolidate.test.ts` (450-550 lines)
   - Test findCandidates() with mock Qdrant responses
   - Test classifyConsolidation() with mock LLM responses
   - Test performConsolidation() pair merging logic
   - Test consolidate() orchestration

2. **Task 3B**: Write `src/llm/providers.test.ts` (400-500 lines)
   - Test completeViaAnthropic() with mock Bun.spawn
   - Test completeViaOllama() with mock fetch
   - Test markdown code fence stripping
   - Test JSON parsing error handling

3. **Task 3C**: Write `src/qntm/batch.test.ts` (150-200 lines)
   - Test generateQNTMKeysBatch() wrapper behavior
   - Test QNTM-specific default result handling
   - Test concurrency env var override

**Dependencies**: Phase 2 (deduplication must complete first)

**Parallelization**: Tasks 3A, 3B, 3C can run in parallel (no interdependencies)

**Deliverables**:
- ✅ consolidate.ts coverage: 0% → 70%+
- ✅ llm/providers.ts coverage: low → 70%+
- ✅ qntm/batch.ts coverage: indirect → 70%+

**Estimated effort**: 8-12 hours total (2-4 hours per task if parallel)

**Files changed**:
- `src/consolidate.test.ts` (NEW, 450-550 lines)
- `src/llm/providers.test.ts` (NEW, 400-500 lines)
- `src/qntm/batch.test.ts` (NEW, 150-200 lines)

---

### Phase 4: Low-Priority Coverage (OPTIONAL)

**Why fourth**: Nice-to-have, not critical for stability

**Tasks**:
1. Write `src/clients/clients.test.ts`
   - Test singleton initialization
   - Test reset() methods
   - Test VOYAGE_API_KEY error handling

**Dependencies**: None (can run anytime)

**Deliverables**:
- ✅ clients/*.ts coverage: 0% → 50%+

**Estimated effort**: 2-3 hours

**Files changed**:
- `src/clients/clients.test.ts` (NEW, 100-150 lines)

**Priority**: LOW (defer if time-constrained)

---

### Phase 5: Organization Documentation (OPTIONAL)

**Why fifth**: No code changes, just documentation

**Tasks**:
1. Document singleton pattern rationale in clients/README.md
2. Add architecture decision record (ADR) for batch processing abstraction
3. Update CONTRIBUTING.md with testing guidelines

**Dependencies**: Phases 1-3 complete (document final state)

**Deliverables**:
- ✅ Pattern documentation in clients/README.md
- ✅ ADR for batch abstraction decision
- ✅ Testing guidelines updated

**Estimated effort**: 1-2 hours

**Files changed**:
- `src/clients/README.md` (NEW or MODIFY)
- `docs/adr/0001-batch-abstraction.md` (NEW)
- `CONTRIBUTING.md` (MODIFY)

**Priority**: LOW (defer if time-constrained)

---

### Execution Timeline

**Sequential execution** (conservative, one person):
- Phase 1: 1-2 hours
- Phase 2: 4-6 hours
- Phase 3: 8-12 hours (sequential)
- Phase 4: 2-3 hours (optional)
- Phase 5: 1-2 hours (optional)
- **Total**: 16-25 hours

**Parallel execution** (optimistic, team of 3):
- Phase 1: 1-2 hours (Person A)
- Phase 2: 4-6 hours (Person A)
- Phase 3A: 2-4 hours (Person A) ┐
- Phase 3B: 2-4 hours (Person B) ├─ Parallel
- Phase 3C: 2-4 hours (Person C) ┘
- Phase 4: 2-3 hours (Person B, optional)
- Phase 5: 1-2 hours (Person C, optional)
- **Total**: 10-17 hours (wall clock time)

---

## Dependency Graph

```
Phase 1: Test Fixes
   ↓
Phase 2: Deduplication
   ↓
   ├─→ Phase 3A: consolidate.test.ts ──┐
   ├─→ Phase 3B: llm/providers.test.ts ├─→ Phase 5: Documentation
   └─→ Phase 3C: qntm/batch.test.ts ───┘
        ↓ (optional)
   Phase 4: clients.test.ts
```

**Critical path**: Phase 1 → Phase 2 → Phase 3 (longest path)
**Parallelizable**: Phase 3A, 3B, 3C (no interdependencies)
**Optional**: Phase 4, Phase 5

---

## Risk Assessment

**High Risk** (requires careful attention):
- Phase 2 deduplication: Behavioral changes possible in edge cases
- Phase 3 coverage: Mock complexity may cause flaky tests

**Medium Risk**:
- Phase 1 test fixes: Mock isolation may reveal other hidden issues

**Low Risk**:
- Phase 4 client tests: Simple wrappers, straightforward testing
- Phase 5 documentation: No code changes

**Mitigation strategies**:
- Run full test suite after each phase
- Use git branches for each phase (easy rollback)
- Peer review for Phase 2 (deduplication is high-impact)

---

## Output Summary

**Total patterns detected**: 5 major clusters
**Files requiring changes**: 11 files (6 new, 5 modified)
**Estimated line changes**:
- Added: ~1,900 lines (tests + batch abstraction)
- Removed: ~300 lines (duplication)
- Net: +1,600 lines (mostly test coverage)

**Coverage improvement**:
- consolidate.ts: 0% → 70%+
- llm/providers.ts: low → 70%+
- qntm/batch.ts: indirect → 70%+
- clients/*.ts: 0% → 50%+ (optional)

**Test stability**:
- Current: 189/196 passing (96.4%)
- After Phase 1: 196/196 passing (100%)
- After Phase 3: 196+ passing with 70%+ coverage

**Execution order**:
1. Phase 1: Fix tests (REQUIRED)
2. Phase 2: Deduplication (REQUIRED)
3. Phase 3: Coverage (REQUIRED for 70% target)
4. Phase 4: Clients (OPTIONAL)
5. Phase 5: Docs (OPTIONAL)

---

**Output saved to**: ~/.claude/skills/atlas/.atlas/connector/analysis/atlas/atlas-test-coverage-pattern-clusters-2025-12-29.md
