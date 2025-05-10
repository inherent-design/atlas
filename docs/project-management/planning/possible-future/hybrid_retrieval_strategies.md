# Hybrid Retrieval Strategies

**NOTE: The approaches outlined in this document are design proposals and are not yet implemented in Atlas.**

This document outlines potential implementation strategies for hybrid search in Atlas, combining semantic (vector) and lexical (keyword) retrieval approaches to maximize search effectiveness.

## Strategy Overview

Hybrid retrieval aims to combine the strengths of two complementary approaches:

1. **Semantic (Vector) Search**
   - Based on embedding similarity
   - Captures meaning even when exact terms aren't present
   - Better for conceptual matching and understanding intent
   - May miss exact terminology or specialized vocabulary

2. **Lexical (Keyword) Search**
   - Based on exact term matching or statistical methods like BM25
   - Precise for specific terms, identifiers, or technical vocabulary
   - Better for finding exact matches and specific details
   - Misses conceptual similarity when different terms are used

## Proposed Implementation Approaches

### 1. Parallel Combination (Recommended First Implementation)

```
Query
  ├─> Semantic Search ──> Semantic Results with Scores
  └─> Keyword Search ───> Keyword Results with Scores
                               │
                               ▼
                        Score Normalization
                               │
                               ▼
                         Result Merging
                               │
                               ▼
                          Final Results
```

**Implementation Details:**
- Run both search types independently with the same query
- Normalize scores from both approaches to a common scale (0-1)
- Combine results with configurable weights (default: 70% semantic, 30% keyword)
- Rerank the combined results based on weighted scores
- Remove duplicates, prioritizing results found by both methods

**Advantages:**
- Simplest to implement
- Gives most control over the balance between approaches
- Easy to tune for different content types
- Can be made transparent to users for debugging

**Code Structure:**
```python
def retrieve_hybrid(
    self,
    query: str,
    n_results: int = 10,
    filter: Optional[RetrievalFilter] = None,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3,
) -> List[RetrievalResult]:
    """Retrieve documents using hybrid semantic and keyword search."""
    # Get semantic search results
    semantic_results = self.retrieve(
        query, 
        n_results=n_results*2,  # Get more results to allow for merging
        filter=filter
    )
    
    # Get keyword search results (e.g., using BM25 or simple term matching)
    keyword_results = self.retrieve_keywords(
        query,
        n_results=n_results*2,
        filter=filter
    )
    
    # Merge results with appropriate weights
    merged_results = self._merge_results(
        semantic_results, 
        keyword_results,
        semantic_weight=semantic_weight,
        keyword_weight=keyword_weight,
        deduplicate=True
    )
    
    # Return top N results after merging
    return merged_results[:n_results]
```

### 2. Sequential Filtering

```
Query
  │
  ▼
Semantic Search (broader pool)
  │
  ▼
Filter Results by Keyword Match
  │
  ▼
Rerank Based on Combined Scores
  │
  ▼
Final Results
```

**Implementation Details:**
- Start with semantic search to get a candidate pool (e.g., top 100 results)
- Apply keyword filtering to narrow down candidates
- Rerank results based on combined semantic and keyword relevance
- Can be more efficient for very large document collections

**Advantages:**
- Potentially more efficient for large collections
- Useful when keyword filtering is very specific
- Can handle more complex queries with both conceptual and specific needs

### 3. BM25 + Vector Hybrid

```
Query
  ├─> Vector Embedding ───> Vector Search
  └─> Term Processing ────> BM25 Search
                                │
                                ▼
                         Score Combination
                                │
                                ▼
                            Final Results
```

**Implementation Details:**
- Implement BM25 scoring alongside vector search
- BM25 parameters (k1, b) can be tuned for different content types
- Combine BM25 scores with vector similarity scores using learned weights
- Often outperforms either method alone in information retrieval benchmarks

**Advantages:**
- More sophisticated lexical matching than simple keyword search
- Better handling of term frequency and document length
- Industry-standard approach used in systems like Elasticsearch

### 4. Feedback Loop Method

```
Query
  │
  ▼
Semantic Search
  │
  ▼
Extract Key Terms from Top Results
  │
  ▼
Expanded Keyword Search
  │
  ▼
Combine and Rerank
  │
  ▼
Final Results
```

**Implementation Details:**
- Start with semantic search to understand the query intent
- Extract important keywords/entities from top semantic results
- Use these terms to enhance a keyword search query
- Combine original semantic results with the enhanced keyword results
- More complex but can handle ambiguous queries better

**Advantages:**
- Can improve handling of ambiguous queries
- Uses initial semantic results to inform keyword search
- Potentially better recall for complex informational needs

## Configuration and Tuning

The hybrid retrieval system should allow for extensive configuration:

### Global Configuration

- Default weights for semantic vs. keyword search (e.g., 70/30)
- Score normalization method (min-max, softmax, etc.)
- Result merging strategy (linear combination, rank fusion, etc.)
- Default number of candidates to consider from each approach

### Query-Level Configuration

- Per-query adjustments to weights based on query characteristics
- Content type hints to favor one approach over another
- Specificity detection to adjust weights automatically
- Query expansion settings for enhancing keyword search

### Document Type Configuration

- Different weight presets for code vs. documentation vs. general content
- Custom scoring functions for specialized content types
- Field weighting for structured documents

## Performance Considerations

Hybrid search adds computational overhead that should be managed:

1. **Caching Layer**
   - Cache common queries with their hybrid results
   - Cache intermediate results from each approach
   - Expiration policy based on knowledge base updates

2. **Lazy Evaluation**
   - Only run the second approach if results from first aren't sufficient
   - Short-circuit expensive operations when high-confidence matches are found
   - Progressively enhance results as needed

3. **Asynchronous Processing**
   - Run approaches in parallel for better performance
   - Return initial results quickly while enhancing in background
   - Support for streaming incremental improvements

## Evaluation and Feedback

To continuously improve hybrid search, consider:

1. **Relevance Metrics**
   - Track precision/recall for different query types
   - Measure mean reciprocal rank (MRR) and normalized discounted cumulative gain (nDCG)
   - Compare performance against each approach individually

2. **User Feedback Mechanisms**
   - Allow users to rate search result relevance
   - Track which results are actually used vs. ignored
   - Use feedback to auto-adjust weights over time

3. **A/B Testing**
   - Test different hybrid configurations against each other
   - Identify query patterns that favor different approaches
   - Refine algorithms based on performance data

## When to Use Different Approaches

### Content Type Considerations

| Content Type | Recommended Approach | Weight Balance |
|--------------|----------------------|----------------|
| General documentation | Parallel Combination | 70% semantic, 30% keyword |
| Code repositories | BM25 + Vector Hybrid | 40% semantic, 60% keyword |
| Technical specifications | Sequential Filtering | 50% semantic, 50% keyword |
| Conceptual content | Parallel with emphasis on semantic | 85% semantic, 15% keyword |
| Mixed content | Feedback Loop | Dynamic based on query |

### Query Type Considerations

| Query Type | Example | Recommended Approach |
|------------|---------|----------------------|
| Conceptual | "How does knowledge embedding work?" | Emphasize semantic search |
| Specific | "APIError in authentication module" | Emphasize keyword search |
| Mixed | "How to handle authentication errors in login flow" | Balanced hybrid approach |
| Ambiguous | "Atlas architecture overview" | Feedback loop approach |
| Technical terms | "ChromaDB metadata filtering syntax" | BM25 + Vector hybrid |

## Conclusion

Hybrid retrieval represents a significant enhancement to Atlas' knowledge capabilities, combining the strengths of semantic understanding with precise keyword matching. While more complex than either approach alone, the benefits in retrieval quality justify the implementation effort.

The recommended implementation path is to start with the Parallel Combination approach due to its simplicity and explicit control, then evolve toward more sophisticated approaches based on performance data and specific use cases.

**NOTE: These strategies are design proposals and not yet implemented in Atlas.**