#!/usr/bin/env python3
"""
Hybrid Retrieval Example (12_hybrid_retrieval.py)

This example demonstrates hybrid retrieval combining semantic and keyword search:
1. Pure semantic search (embedding-based)
2. Pure keyword search (BM25)
3. Hybrid search with weighted combination
4. Results comparison between methods

The example shows how different search strategies can complement each other,
with semantic search capturing conceptual relevance and keyword search ensuring
key terms are matched.
"""

import argparse
import os
import sys
import time
from typing import Any, Dict, List, Set, Tuple

# Import common utilities for Atlas examples
from common import (
    ensure_example_data,
    handle_example_error,
    print_example_footer,
    print_example_header,
    setup_example,
)
from tabulate import tabulate

from atlas.core import logging
from atlas.knowledge.hybrid_search import HybridSearchEngine

# Import atlas modules
from atlas.knowledge.retrieval import KnowledgeBase, RetrievalFilter, RetrievalResult
from atlas.knowledge.settings import RetrievalSettings


def add_example_arguments(parser):
    """Add example-specific arguments to the parser."""
    parser.add_argument(
        "--semantic-weight",
        type=float,
        default=0.7,
        help="Weight for semantic search results (default: 0.7)",
    )
    parser.add_argument(
        "--keyword-weight",
        type=float,
        default=0.3,
        help="Weight for keyword search results (default: 0.3)",
    )
    parser.add_argument(
        "--query", type=str, help="Specific query to use instead of example queries"
    )
    parser.add_argument(
        "--n-results", type=int, default=5, help="Number of results to return (default: 5)"
    )
    parser.add_argument(
        "--merge-strategy",
        type=str,
        default="weighted_score",
        choices=["weighted_score", "score_add", "score_multiply", "rank_fusion"],
        help="Strategy for merging results (default: weighted_score)",
    )


def format_result(result: RetrievalResult, index: int) -> str:
    """Format a retrieval result for display.

    Args:
        result: The retrieval result.
        index: Result number for display.

    Returns:
        Formatted string with result information.
    """
    source = result.metadata.get("source", "Unknown")
    # Clean up source path to just show filename
    source = os.path.basename(source) if source != "Unknown" else source

    # Truncate content for display
    content_snippet = result.content[:100].replace("\n", " ")
    if len(result.content) > 100:
        content_snippet += "..."

    return f"{index+1}. {source} (score: {result.relevance_score:.4f})\n" f"   {content_snippet}\n"


def print_result_overlap(
    semantic_results: List[RetrievalResult],
    keyword_results: List[RetrievalResult],
    hybrid_results: List[RetrievalResult],
) -> None:
    """Print analysis of the overlap between different search methods.

    Args:
        semantic_results: Results from semantic search.
        keyword_results: Results from keyword search.
        hybrid_results: Results from hybrid search.
    """

    # Get document IDs for each result set
    def get_ids(results: List[RetrievalResult]) -> Set[str]:
        return {
            result.metadata.get("id", result.metadata.get("simple_id", hash(result.content)))
            for result in results
        }

    semantic_ids = get_ids(semantic_results)
    keyword_ids = get_ids(keyword_results)
    hybrid_ids = get_ids(hybrid_results)

    # Calculate overlaps
    semantic_keyword_overlap = len(semantic_ids.intersection(keyword_ids))
    semantic_hybrid_overlap = len(semantic_ids.intersection(hybrid_ids))
    keyword_hybrid_overlap = len(keyword_ids.intersection(hybrid_ids))
    all_overlap = len(semantic_ids.intersection(keyword_ids).intersection(hybrid_ids))

    # Calculate unique results
    semantic_unique = len(semantic_ids - keyword_ids - hybrid_ids)
    keyword_unique = len(keyword_ids - semantic_ids - hybrid_ids)
    hybrid_unique = len(hybrid_ids - semantic_ids - keyword_ids)

    # Calculate total unique documents across all methods
    total_unique = len(semantic_ids.union(keyword_ids).union(hybrid_ids))

    # Print analysis
    print("\n🔍 Result Overlap Analysis 🔍")
    print("--------------------------")

    table = [
        ["Overlap Type", "Count", "Percentage"],
        [
            "Semantic & Keyword",
            semantic_keyword_overlap,
            f"{100 * semantic_keyword_overlap / max(1, total_unique):.1f}%",
        ],
        [
            "Semantic & Hybrid",
            semantic_hybrid_overlap,
            f"{100 * semantic_hybrid_overlap / max(1, total_unique):.1f}%",
        ],
        [
            "Keyword & Hybrid",
            keyword_hybrid_overlap,
            f"{100 * keyword_hybrid_overlap / max(1, total_unique):.1f}%",
        ],
        ["All Methods", all_overlap, f"{100 * all_overlap / max(1, total_unique):.1f}%"],
        ["Semantic Only", semantic_unique, f"{100 * semantic_unique / max(1, total_unique):.1f}%"],
        ["Keyword Only", keyword_unique, f"{100 * keyword_unique / max(1, total_unique):.1f}%"],
        ["Hybrid Only", hybrid_unique, f"{100 * hybrid_unique / max(1, total_unique):.1f}%"],
        ["Total Unique Documents", total_unique, "100.0%"],
    ]

    print(tabulate(table, headers="firstrow", tablefmt="pretty"))
    print()


def print_top_results(results: List[RetrievalResult], method_name: str) -> None:
    """Print the top results from a search method.

    Args:
        results: The search results.
        method_name: Name of the search method.
    """
    print(f"\n📊 {method_name} Results 📊")
    print("-" * (len(method_name) + 20))

    # Print the top results
    if not results:
        print("No results found.")
        return

    table_data = []
    for i, result in enumerate(results):
        source = result.metadata.get("source", "Unknown")
        source = os.path.basename(source) if source != "Unknown" else source

        # Truncate content for display and clean newlines
        content_snippet = result.content[:80].replace("\n", " ")
        if len(result.content) > 80:
            content_snippet += "..."

        table_data.append([i + 1, source, f"{result.relevance_score:.4f}", content_snippet])

    headers = ["#", "Source", "Score", "Content Preview"]
    print(tabulate(table_data, headers=headers, tablefmt="pretty"))
    print()


def main():
    """Run the hybrid retrieval example."""
    # Set up the example with standardized logging and argument parsing
    args = setup_example("Atlas Hybrid Retrieval Example", add_example_arguments)
    logger = logging.get_logger(__name__)

    # Print example header
    print_example_header("Hybrid Retrieval Example")

    # Ensure we have example data
    was_ingested, document_count = ensure_example_data(args)
    if was_ingested:
        logger.info("Example data was ingested automatically")
        print("Example data was ingested automatically for this example")

    if document_count == 0:
        print("\n⚠️ No documents in the knowledge base!")
        print("Please ingest some documents before running this example.")
        print("You can do so with: python main.py ingest -d /path/to/documents")
        return

    try:
        # Initialize the knowledge base
        logger.info("Initializing knowledge base")
        start_time = time.time()
        kb = KnowledgeBase(collection_name=args.collection, db_path=args.db_path)
        logger.info(f"Knowledge base initialized in {time.time() - start_time:.2f}s")

        # Initialize the hybrid search engine
        hybrid_engine = HybridSearchEngine(
            kb,
            semantic_weight=args.semantic_weight,
            keyword_weight=args.keyword_weight,
            merge_strategy=args.merge_strategy,
        )

        # Index documents for keyword search
        logger.info("Indexing documents for BM25 search")
        start_time = time.time()
        hybrid_engine.index_documents()
        logger.info(f"Documents indexed in {time.time() - start_time:.2f}s")

        # Choose query
        query = args.query or "How does Atlas handle knowledge retrieval?"
        print(f'\n🔎 Query: "{query}"')

        # Perform different retrieval methods
        logger.info(f"Performing retrieval with query: {query}")
        print("\nRetrieving documents using semantic, keyword, and hybrid methods...")

        # 1. Pure semantic search
        semantic_settings = RetrievalSettings(use_hybrid_search=False, num_results=args.n_results)
        semantic_results = kb.retrieve(query, settings=semantic_settings)

        # 2. Pure keyword search
        start_time = time.time()
        keyword_results = hybrid_engine.search(
            query, n_results=args.n_results, semantic_only=False, keyword_only=True
        )
        logger.info(f"Keyword search completed in {time.time() - start_time:.2f}s")

        # 3. Hybrid search
        start_time = time.time()
        hybrid_results = hybrid_engine.search(
            query,
            n_results=args.n_results,
            semantic_weight=args.semantic_weight,
            keyword_weight=args.keyword_weight,
        )
        logger.info(f"Hybrid search completed in {time.time() - start_time:.2f}s")

        # Print retrieval summary
        print("\n📋 Retrieval Summary 📋")
        print("---------------------")
        print(f'Query: "{query}"')
        print(f"Semantic weight: {args.semantic_weight}, Keyword weight: {args.keyword_weight}")
        print(f"Merge strategy: {args.merge_strategy}")
        print(
            f"Retrieved: {len(semantic_results)} semantic, {len(keyword_results)} keyword, and {len(hybrid_results)} hybrid results"
        )

        # Print results from each method
        print_top_results(semantic_results, "Semantic Search")
        print_top_results(keyword_results, "Keyword Search")
        print_top_results(hybrid_results, "Hybrid Search")

        # Print result overlap analysis
        print_result_overlap(semantic_results, keyword_results, hybrid_results)

        # Print usage guidance
        print("\n🔮 When to Use Each Method 🔮")
        print("---------------------------")
        print(
            "🔹 Semantic Search: Best for conceptual queries where exact keywords might not appear"
        )
        print("   Example: 'How does the system organize knowledge?'")
        print()
        print("🔹 Keyword Search: Best for specific term queries or when you need exact matches")
        print("   Example: 'BM25 implementation details'")
        print()
        print(
            "🔹 Hybrid Search: Best general-purpose approach that combines strengths of both methods"
        )
        print(
            "   Example: Any query where both semantic understanding and keyword matching are valuable"
        )
        print()
        print("💡 Tip: Adjust weights based on your specific use case. Higher semantic weight for")
        print("   conceptual queries, higher keyword weight for specific technical terms.")

    except Exception as e:
        handle_example_error(logger, e, "Error during hybrid retrieval")

    # Print footer
    print_example_footer()


if __name__ == "__main__":
    main()
