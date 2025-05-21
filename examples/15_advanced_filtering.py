#!/usr/bin/env python3
"""
Advanced Filtering Example (15_advanced_filtering.py)

This example demonstrates the advanced filtering capabilities of Atlas:
1. Metadata filtering with various operators
2. Document content filtering
3. Combined metadata and content filtering
4. Range filtering for version/date fields
5. Handling filter combinations

It shows how to use the full power of the RetrievalFilter class with
ChromaDB 1.0.8+ compatibility.
"""

import sys
from typing import Any, Dict, List

# Import common utilities for Atlas examples
from common import ensure_example_data, handle_example_error, print_example_footer, setup_example

from atlas import create_query_client
from atlas.core import logging

# Import atlas modules
from atlas.knowledge.retrieval import KnowledgeBase, RetrievalFilter, RetrievalSettings


def format_document(doc: Any, index: int) -> None:
    """Format and print a document in a readable way.

    Args:
        doc: Document object or dictionary
        index: Result number for display
    """
    # Handle both dictionary and RetrievalResult objects
    if hasattr(doc, "metadata"):
        # It's a RetrievalResult object
        source = doc.metadata.get("source", "Unknown")
        doc_id = doc.id if hasattr(doc, "id") else "Unknown"
        relevance = doc.relevance_score
        content = doc.content
        metadata = doc.metadata
    else:
        # It's a dictionary
        source = doc["metadata"].get("source", "Unknown")
        doc_id = doc.get("id", "Unknown")
        relevance = doc["relevance_score"]
        content = doc["content"]
        metadata = doc["metadata"]

    print(f"\nResult {index}:")
    print(f"- Source: {source}")
    if "section_title" in metadata:
        print(f"- Section: {metadata.get('section_title')}")
    print(f"- Relevance: {relevance:.4f}")

    # Print content preview
    print(f"- Content preview: {content[:150]}...")


def add_example_arguments(parser):
    """Add example-specific arguments to the parser."""
    # Skip database options since they're in the common parser

    # Retrieval options
    parser.add_argument(
        "--query",
        type=str,
        default="knowledge graph structure",
        help="Specific query to use instead of default",
    )
    parser.add_argument(
        "--n-results", type=int, default=5, help="Number of results to return (default: 5)"
    )


def main():
    """Run the advanced filtering example."""
    # Set up the example with standardized logging and argument parsing
    args = setup_example("Atlas Advanced Filtering Example", add_example_arguments)
    logger = logging.get_logger(__name__)

    # Ensure we have example data
    was_ingested, document_count = ensure_example_data(args)
    if was_ingested:
        logger.info("Example data was ingested automatically")
        print("Example data was ingested automatically for this example")

    # Initialize the knowledge base
    logger.info("Initializing knowledge base")
    print(f"Initializing knowledge base:")
    collection_name = args.collection
    db_path = args.db_path
    print(f"- Collection: {collection_name}")
    print(f"- Database path: {db_path}")

    try:
        # Create knowledge base
        kb = KnowledgeBase(
            collection_name=collection_name,
            db_path=db_path,
        )

        # Check collection count
        collection_count = kb.collection.count()
        if collection_count == 0:
            logger.error("No documents found in the knowledge base")
            print("\nError: No documents found in the knowledge base")
            print("Please run the document ingestion example first:")
            print("  python examples/10_document_ingestion.py")
            sys.exit(1)

        logger.info(f"Knowledge base ready with {collection_count} documents")
        print(f"\nKnowledge base ready:")
        print(f"- Collection: {kb.collection_name}")
        print(f"- Document count: {collection_count}")

        # Example 1: Basic Metadata Filtering
        print("\n" + "-" * 50)
        print("Example 1: Basic Metadata Filtering")
        print("-" * 50)

        query = args.query
        logger.info(f"Performing basic metadata filtering for query: {query}")
        print(f"\nQuery: {query}")

        # Get available metadata fields
        print(f"Checking available metadata fields...")
        metadata_fields = kb.get_metadata_fields()
        print(f"Available metadata fields: {', '.join(metadata_fields)}")

        # Create a filter for documents from components directory
        filter = RetrievalFilter()

        # Start with a known path that should exist in our example data
        filter.add_filter("source", {"$eq": "docs/components/knowledge"})

        print(f"\nFilter: source equals 'docs/components/knowledge'")
        results = kb.retrieve(query, n_results=args.n_results, filter=filter)
        print(f"\nFound {len(results)} results")

        for i, doc in enumerate(results, 1):
            format_document(doc, i)

        # Example 2: Operator-Based Filtering
        print("\n" + "-" * 50)
        print("Example 2: Operator-Based Filtering")
        print("-" * 50)

        # Create filter with comparison operators
        filter = RetrievalFilter()

        # Find documents with specific pattern in source path
        # We'll look for all section titles containing "Knowledge"
        filter.add_operator_filter("section_title", "$ne", "")  # Must have a section title

        print(f"\nQuery: {query}")
        print(f"Filter: section_title is not empty")
        results = kb.retrieve(query, n_results=args.n_results, filter=filter)
        print(f"\nFound {len(results)} results")

        for i, doc in enumerate(results, 1):
            format_document(doc, i)

        # Example 3: Document Content Filtering
        print("\n" + "-" * 50)
        print("Example 3: Document Content Filtering")
        print("-" * 50)

        query = "architecture"

        # For document content filtering, we need to format it properly
        # For ChromaDB 1.0.8+ compatibility
        try:
            filter = RetrievalFilter()

            # Add document content filter to find documents containing specific text
            filter.add_document_contains("knowledge graph")

            print(f"\nQuery: {query}")
            print(f"Filter: document content contains 'knowledge graph'")

            # Using document_content_contains filter directly
            filter_dict = {"$contains": "knowledge graph"}
            results = kb.collection.query(
                query_texts=[query], n_results=args.n_results, where_document=filter_dict
            )

            # Format results
            formatted_results = []
            for i, (doc, metadata, distance) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ):
                # Convert distance to relevance score (0-1 range, higher is better)
                relevance_score = 1.0 - (distance / 2.0)  # Normalize to 0-1
                # Ensure score is in valid range
                relevance_score = max(0.0, min(1.0, relevance_score))

                from atlas.knowledge.retrieval import RetrievalResult

                formatted_results.append(
                    RetrievalResult(
                        content=doc,
                        metadata=metadata,
                        relevance_score=relevance_score,
                        distance=distance,
                    )
                )

            print(f"\nFound {len(formatted_results)} results")

            for i, doc in enumerate(formatted_results, 1):
                format_document(doc, i)

        except Exception as e:
            logger.exception(f"Error with document content filtering: {e}")
            print(f"Error with document content filtering: {e}")
            print(
                "This might happen if your ChromaDB version doesn't support where_document filtering"
            )
            print("Try using version 1.0.8 or later of ChromaDB")

        # Example 4: Combined Metadata and Content Filtering
        print("\n" + "-" * 50)
        print("Example 4: Combined Metadata and Content Filtering")
        print("-" * 50)

        try:
            query = "knowledge system"
            print(f"\nQuery: {query}")
            print(f"Filter: source contains 'knowledge' AND content contains 'retrieval'")

            # Using direct ChromaDB query for combined filtering
            results = kb.collection.query(
                query_texts=[query],
                n_results=args.n_results,
                where={"source": {"$eq": "../docs/components/knowledge/index.md"}},
                where_document={"$contains": "retrieval"},
            )

            # Format results
            formatted_results = []
            if results and len(results["documents"]) > 0 and len(results["documents"][0]) > 0:
                for i, (doc, metadata, distance) in enumerate(
                    zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0],
                    )
                ):
                    # Convert distance to relevance score (0-1 range, higher is better)
                    relevance_score = 1.0 - (distance / 2.0)  # Normalize to 0-1
                    # Ensure score is in valid range
                    relevance_score = max(0.0, min(1.0, relevance_score))

                    from atlas.knowledge.retrieval import RetrievalResult

                    formatted_results.append(
                        RetrievalResult(
                            content=doc,
                            metadata=metadata,
                            relevance_score=relevance_score,
                            distance=distance,
                        )
                    )

            print(f"\nFound {len(formatted_results)} results")

            for i, doc in enumerate(formatted_results, 1):
                format_document(doc, i)

        except Exception as e:
            logger.exception(f"Error with combined filtering: {e}")
            print(f"Error with combined filtering: {e}")
            print(
                "This might happen if your ChromaDB version doesn't fully support combined filters"
            )
            print("Try using version 1.0.8 or later of ChromaDB")

        # Example 5: List-Based Filtering with $in operator
        print("\n" + "-" * 50)
        print("Example 5: List-Based Filtering with $in operator")
        print("-" * 50)

        # Create filter with $in operator
        filter = RetrievalFilter()

        # We'll look for documents from specific sources
        sources = ["docs/components/knowledge", "docs/components/core"]
        filter.add_in_filter("source", sources)

        query = "configuration"
        print(f"\nQuery: {query}")
        print(f"Filter: source in {sources}")
        results = kb.retrieve(query, n_results=args.n_results, filter=filter)
        print(f"\nFound {len(results)} results")

        for i, doc in enumerate(results, 1):
            format_document(doc, i)

        # Example 6: NOT IN Filtering
        print("\n" + "-" * 50)
        print("Example 6: NOT IN Filtering with $nin operator")
        print("-" * 50)

        # Create filter with $nin operator for exclusion
        filter = RetrievalFilter()

        # Exclude certain sources
        exclude_sources = ["docs/guides", "docs/reference"]
        filter.add_nin_filter("source", exclude_sources)

        query = args.query
        print(f"\nQuery: {query}")
        print(f"Filter: source NOT IN {exclude_sources}")
        results = kb.retrieve(query, n_results=args.n_results, filter=filter)
        print(f"\nFound {len(results)} results")

        for i, doc in enumerate(results, 1):
            format_document(doc, i)

        # Example 7: Range Filtering
        print("\n" + "-" * 50)
        print("Example 7: Range Filtering")
        print("-" * 50)

        # Create range filter for numeric values
        filter = RetrievalFilter()

        # Look for documents with version in range
        # This assumes versions might be stored as numbers
        try:
            # First try numeric range
            filter.add_range_filter("version_num", 1, 3)

            # Try the search
            results = kb.retrieve(query, n_results=args.n_results, filter=filter)

            if not results:
                # If no results, try with string versions
                filter = RetrievalFilter()
                filter.add_in_filter("version", ["1", "2", "3"])
                results = kb.retrieve(query, n_results=args.n_results, filter=filter)
                print(f"\nQuery: {query}")
                print(f"Filter: version in ['1', '2', '3']")
            else:
                print(f"\nQuery: {query}")
                print(f"Filter: version_num between 1 and 3")
        except Exception as e:
            logger.warning(f"Range query failed: {e}")
            # Fall back to simpler filter
            filter = RetrievalFilter()
            filter.add_in_filter("version", ["1", "2", "3"])
            results = kb.retrieve(query, n_results=args.n_results, filter=filter)
            print(f"\nQuery: {query}")
            print(f"Filter: version in ['1', '2', '3']")

        print(f"\nFound {len(results)} results")

        for i, doc in enumerate(results, 1):
            format_document(doc, i)

        # Example 8: Integration with Query Client
        print("\n" + "-" * 50)
        print("Example 8: Integration with Query Client")
        print("-" * 50)

        try:
            # Create a simple filter that works reliably
            filter = RetrievalFilter()
            filter.add_filter("section_title", {"$ne": ""})  # Filter for docs with section titles

            query = "How does Atlas handle embedding generation?"
            print(f"\nQuery: {query}")
            print(f"Filter: section_title is not empty")

            # Import from common to use the existing model setup logic
            from common import create_provider_from_args

            # Create provider from command line arguments
            provider = create_provider_from_args(args)
            logger.info(f"Created provider: {provider.name} with model {provider.model_name}")
            print(f"\nCreating provider: {provider.name} with model {provider.model_name}")

            # Create query client with the provider
            client = create_query_client(
                collection_name=collection_name,
                db_path=db_path,
                provider_name=provider.name,
                model_name=provider.model_name,
            )

            result = client.query_with_context(
                query_text=query, filter=filter, max_results=args.n_results
            )

            print(f"\nResponse with {len(result['context']['documents'])} context documents:")
            print(result["response"])

            print("\nSupporting Documents:")
            for i, doc in enumerate(result["context"]["documents"][:3], 1):
                # Convert to consistent format for printing
                formatted_doc = {
                    "metadata": {"source": doc.get("source", "Unknown")},
                    "relevance_score": doc.get("relevance_score", 0.0),
                    "content": doc.get("content", ""),
                }
                format_document(formatted_doc, i)

        except Exception as e:
            logger.exception(f"Error creating query client: {e}")
            print(f"\nError creating query client: {e}")
            print("Try using '--provider mock' for testing without API keys")

    except Exception as e:
        logger.exception(f"Error during advanced filtering: {e}")
        print(f"Error during advanced filtering: {e}")
        sys.exit(1)

    # Print footer
    print_example_footer()

    # Print additional information
    print("\nAdvanced Filtering Techniques:")
    print("- Exact matching with $eq operator")
    print("- Exclusion with $ne and $nin operators")
    print("- Range queries with $gt, $gte, $lt, $lte operators")
    print("- List matching with $in operator")
    print("- Document content filtering with $contains")

    print("\nUsage Tips:")
    print("- Chain filter methods for building complex queries")
    print("- Use add_document_contains() for full-text search within documents")
    print("- Combine metadata and content filtering for precise results")
    print("- Use RetrievalFilter for all ChromaDB-compatible filtering")

    print("\nRelated Examples:")
    print("- For basic retrieval, see example 11_basic_retrieval.py")
    print("- For hybrid search, see example 12_hybrid_retrieval.py")


if __name__ == "__main__":
    main()
