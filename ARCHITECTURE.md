# Atlas Architecture - Technical Reference

Complete architectural overview based on .atlas research (Steps 1-4 + Sleep Patterns).

## System Overview

Atlas is a persistent semantic memory layer for Claude Code, enabling context to survive across sessions through Voyage embeddings + Qdrant vector storage.

```
┌─────────────────────────────────────────────┐
│ User Input (Files, Questions)               │
└────────────────┬────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ↓                 ↓
  [INGESTION]       [RETRIEVAL]
        │                 │
        ↓                 │
┌───────────────┐         │
│ Chunking      │         │
│ 768 tokens    │         │
│ 13% overlap   │         │
└───────┬───────┘         │
        │                 │
        ↓                 │
┌───────────────┐         │
│ Voyage API    │         │
│ 1024-dim      │         │
│ embeddings    │         │
└───────┬───────┘         │
        │                 │
        ↓                 │
┌───────────────┐         │
│ Qdrant Store  │         │
│ HNSW + int8   │<────────┘
│ quantization  │
└───────────────┘
```

## Data Flow

### Ingestion Pipeline

1. **File Reading** → Raw text extraction
2. **Chunking** (RecursiveCharacterTextSplitter)
   - 768 tokens per chunk (conservative for quality)
   - 100 token overlap (13%, maintains context across boundaries)
   - Hierarchical separators: `\n\n` → `\n` → `. ` → ` `
3. **QNTM Key Generation** (semantic addressing)
   - Currently: Content-based MD5 hash
   - Future: LLM-generated semantic key (`@memory ~ consolidation ~ episodic`)
4. **Embedding** (Voyage-3-large via API)
   - Batch processing for efficiency
   - 1024-dim normalized vectors
5. **Storage** (Qdrant upsert)
   - Dual-indexing: QNTM key + datetime timestamp
   - Original text preserved in payload
   - Metadata: file path, chunk index, importance, etc.

### Retrieval Pipeline

1. **Query Embedding** (Voyage-3-large)
   - Same model as ingestion ensures compatibility
2. **Vector Search** (Qdrant HNSW)
   - Approximate nearest neighbors (O(log N))
   - int8 quantization with rescoring (0.99 accuracy)
   - Optional temporal filtering via payload
3. **Result Ranking**
   - Dot product similarity (Voyage pre-normalizes)
   - Metadata attribution (file path, chunk index, timestamp)
4. **Context Assembly**
   - Original text from payload
   - Source attribution for traceability

## Memory Layers

### Layer 1: Working Memory (Future: mem0)
- **Purpose**: Short-term agent task context
- **Technology**: mem0 (not yet implemented)
- **Persistence**: Thread-based, ephemeral
- **Embeddings**: OpenAI text-embedding-3-small (cheap)

### Layer 2: Long-term Memory (Current: Qdrant)
- **Purpose**: Persistent knowledge base across sessions
- **Technology**: Qdrant + Voyage-3-large
- **Persistence**: Permanent collections
- **Embeddings**: Voyage-3-large (1024-dim, quality)

### Layer 3: Conversation State (Future: LangGraph)
- **Purpose**: Thread continuity and agent coordination
- **Technology**: LangGraph Checkpointers
- **Persistence**: SQLite/PostgreSQL
- **Data**: State metadata, not embeddings

## Dual-Indexing Pattern

From Sleep Patterns research - enables both semantic and temporal access:

### Semantic Index (QNTM Keys)
- **Purpose**: Content-based addressing
- **Mechanism**: LLM-generated semantic tokens
- **Example**: `@memory ~ consolidation ~ episodic`
- **Access**: Qdrant collection names or payload filtering

### Temporal Index (Datetime Payloads)
- **Purpose**: Chronological queries and timelines
- **Mechanism**: RFC 3339 timestamps in payload
- **Example**: `2025-12-28T12:34:56.789Z`
- **Access**: Qdrant scroll API with `order_by: created_at`

### Combined Queries
```typescript
// Semantic similarity + temporal constraint
qdrant.search(collection, {
  vector: queryEmbedding,
  filter: {
    must: [{
      key: 'created_at',
      range: { gte: '2025-12-01T00:00:00Z' }
    }]
  }
});
```

## Qdrant Configuration (Production)

From Step 3 research - optimized for quality + efficiency:

```typescript
{
  vectors: {
    size: 1024,           // Voyage-3-large dimension
    distance: 'Dot',      // Faster than cosine (Voyage pre-normalizes)
    on_disk: true         // Full vectors on disk for rescoring
  },
  hnsw_config: {
    m: 16,                // Balanced accuracy/memory
    ef_construct: 100,    // Build-time quality
    on_disk: false        // HNSW graph in RAM for speed
  },
  quantization_config: {
    scalar: {
      type: 'int8',       // 4x compression
      quantile: 0.99,     // 0.99 accuracy retention
      always_ram: true    // Quantized vectors in RAM
    }
  }
}
```

**Performance** (per 1M vectors):
- Recall@10: >0.98
- Latency: 10-50ms (p95)
- Throughput: 100-500 RPS (single node)
- Memory: 1.4GB RAM + 5GB disk

## Chunking Strategy (Step 2)

RecursiveCharacterTextSplitter with hierarchical separators:

```typescript
{
  chunkSize: 768,                           // Conservative for quality
  chunkOverlap: 100,                        // 13% overlap
  separators: ['\n\n', '\n', '. ', ' ', ''] // Semantic boundaries
}
```

**Rationale**:
- 768 tokens fits comfortably in Voyage's 32k context
- 13% overlap maintains semantic continuity across chunks
- Hierarchical separators respect document structure (paragraphs → sentences → words)

## Future Enhancements (From Sleep Patterns Research)

### 1. Episodic → Semantic Consolidation
- LLM batch processing of similar memories
- Abstraction from detailed episodes to general patterns
- Scheduled sleep cycles (consolidation daemon)

### 2. Importance-Based Retention
- Protect salient memories from deduplication
- Tag high-importance items for permanent storage
- Adaptive TTL based on access frequency

### 3. Semantic Deduplication
- SemDeDup algorithm (cluster + threshold + representative selection)
- Preserve temporal metadata while removing redundancy
- Order-preserving fingerprinting

### 4. LLM-Based QNTM Generation
- Replace content hashing with LLM semantic key generation
- Stable addressing: similar concepts → same QNTM key
- Enables semantic URL-style addressing

### 5. Causal Inference
- Multi-expert LLM framework
- Temporal precedence filtering (A before B required for A causes B)
- Event knowledge graph construction

## Technology Stack

**Current**:
- Bun runtime (TypeScript-native, fast)
- Voyage AI SDK (`voyageai` npm package)
- Qdrant JS client (`@qdrant/js-client-rest`)
- LangChain text splitters (`@langchain/textsplitters`)

**Future**:
- mem0 (working memory layer)
- LangGraph (multi-agent orchestration)
- Three.js + UMAP (3D visualization via embedding-atlas)

## Research Foundation

This architecture is built on comprehensive .atlas research:

- **Step 1**: QNTM Integration Strategy
- **Step 2**: Chunking Strategies
- **Step 3**: Embeddings Mechanics & Storage
- **Step 4**: Stack Architecture Synthesis
- **Sleep Patterns**: Natural process-inspired consolidation

All research artifacts available in: `/Users/zer0cell/production/.atlas/`
