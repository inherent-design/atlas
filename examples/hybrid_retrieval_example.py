"""
Hybrid Retrieval Example for Atlas Knowledge System

This example demonstrates how to use the hybrid retrieval features in Atlas,
which combines semantic vector search with keyword-based search for more robust 
document retrieval from your knowledge base.

Usage:
    python examples/hybrid_retrieval_example.py [--directory DIRECTORY] [--query QUERY]
"""

import os
import sys
import argparse
from typing import List, Dict, Any, Optional

# Add the project root to the path so we can import atlas modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from atlas.knowledge.retrieval import KnowledgeBase, RetrievalFilter, RetrievalResult
from atlas.knowledge.settings import RetrievalSettings
from atlas.knowledge.embedding import EmbeddingStrategyFactory
from atlas.knowledge.ingest import DocumentProcessor


def print_retrieval_results(results: List[RetrievalResult], title: str) -> None:
    """Print retrieval results with formatting.
    
    Args:
        results: List of retrieval results to print.
        title: Title to display above results.
    """
    print("\n" + "=" * 80)
    print(f"{title} ({len(results)} results)")
    print("=" * 80)
    
    for i, result in enumerate(results):
        # Get a content preview
        content_preview = result.content.strip()
        if len(content_preview) > 300:
            content_preview = content_preview[:300] + "..."
        
        print(f"\n{i+1}. Score: {result.relevance_score:.4f}")
        print(f"   Source: {result.source}")
        if result.section_title:
            print(f"   Section: {result.section_title}")
        print(f"   Content: {content_preview}")
        print("-" * 40)


def main():
    """Run the hybrid retrieval example."""
    parser = argparse.ArgumentParser(description="Atlas Hybrid Retrieval Example")
    parser.add_argument(
        "--directory", 
        help="Directory to ingest (if not using existing collection)",
        default=None
    )
    parser.add_argument(
        "--query", 
        help="The query to search for",
        default="How does the chunking strategy work with semantic boundaries?"
    )
    parser.add_argument(
        "--collection", 
        help="Collection name", 
        default="atlas_knowledge_base"
    )
    parser.add_argument(
        "--embedding", 
        help="Embedding strategy to use (default, anthropic, hybrid)", 
        default="default"
    )
    
    args = parser.parse_args()
    
    # If a directory is provided, ingest it first
    if args.directory:
        print(f"Ingesting documents from {args.directory}...")
        processor = DocumentProcessor(
            collection_name=args.collection,
            embedding_strategy=args.embedding,
            enable_deduplication=True,
        )
        processor.process_directory(args.directory)
    
    # Initialize knowledge base
    kb = KnowledgeBase(
        collection_name=args.collection,
        embedding_strategy=args.embedding,
    )
    
    print(f"\nPerforming searches for query: '{args.query}'")
    
    # Create an optional filter (for example, to filter by file type)
    # For now, we'll use a simple filter as there seems to be a format issue
    # with multiple filter conditions in ChromaDB
    filter = RetrievalFilter.from_metadata(
        file_type="md",  # Only markdown files
        exclude_duplicates=False,  # Don't exclude duplicates for now to avoid query issues
    )
    
    # Execute standard semantic search
    semantic_settings = RetrievalSettings(
        use_hybrid_search=False,
        rerank_results=True,
        num_results=5
    )
    
    semantic_results = kb.retrieve(
        query=args.query,
        filter=filter,
        settings=semantic_settings
    )
    
    # Print semantic search results
    print_retrieval_results(semantic_results, "Semantic Search Results")
    
    # Execute hybrid search (combining semantic and keyword search)
    hybrid_settings = RetrievalSettings(
        use_hybrid_search=True,
        semantic_weight=0.7,  # Weight for semantic search (70%)
        keyword_weight=0.3,   # Weight for keyword search (30%)
        num_results=5
    )
    
    hybrid_results = kb.retrieve(
        query=args.query,
        filter=filter,
        settings=hybrid_settings
    )
    
    # Print hybrid search results
    print_retrieval_results(hybrid_results, "Hybrid Search Results")
    
    # Compare the differences between semantic and hybrid search
    print("\n" + "=" * 80)
    print("COMPARISON ANALYSIS")
    print("=" * 80)
    
    semantic_ids = {result.metadata.get("id", id(result)): i for i, result in enumerate(semantic_results)}
    hybrid_ids = {result.metadata.get("id", id(result)): i for i, result in enumerate(hybrid_results)}
    
    # Identify unique results in hybrid that weren't in semantic top results
    unique_to_hybrid = [
        (i, result) for i, result in enumerate(hybrid_results) 
        if result.metadata.get("id", id(result)) not in semantic_ids
    ]
    
    if unique_to_hybrid:
        print(f"\nHybrid search found {len(unique_to_hybrid)} results that weren't in the top semantic results:")
        for rank, (i, result) in enumerate(unique_to_hybrid):
            print(f"  - Result #{i+1}: {result.source} (score: {result.relevance_score:.4f})")
    else:
        print("\nBoth search methods returned the same documents (possibly in different order)")
    
    # Compare ranking differences
    common_ids = set(semantic_ids.keys()) & set(hybrid_ids.keys())
    if common_ids:
        rank_changes = []
        for doc_id in common_ids:
            semantic_rank = semantic_ids[doc_id] + 1  # Convert to 1-based
            hybrid_rank = hybrid_ids[doc_id] + 1      # Convert to 1-based
            rank_change = semantic_rank - hybrid_rank
            if rank_change != 0:
                rank_changes.append((doc_id, semantic_rank, hybrid_rank, rank_change))
        
        if rank_changes:
            print("\nRanking changes between semantic and hybrid search:")
            for doc_id, semantic_rank, hybrid_rank, change in sorted(rank_changes, key=lambda x: abs(x[3]), reverse=True):
                hybrid_result = hybrid_results[hybrid_rank-1]  # Convert back to 0-based
                direction = "higher" if change > 0 else "lower"
                print(f"  - {hybrid_result.source} ranked {abs(change)} positions {direction} in hybrid search")
    
    # Example of exploring metadata fields
    print("\n" + "=" * 80)
    print("AVAILABLE METADATA FIELDS")
    print("=" * 80)
    metadata_fields = kb.get_metadata_fields()
    print(f"Available metadata fields: {', '.join(metadata_fields)}")
    
    # Example of searching by metadata
    if "file_type" in metadata_fields:
        file_types = kb.search_by_metadata("file_type", "")
        print(f"\nAvailable file types: {', '.join(file_types)}")
    
    if "version" in metadata_fields:
        versions = kb.get_versions()
        print(f"\nAvailable versions: {', '.join(versions)}")


if __name__ == "__main__":
    main()