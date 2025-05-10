#!/usr/bin/env python3
"""
Basic Retrieval Example (11_basic_retrieval.py)

This example demonstrates the core retrieval capabilities of Atlas:
1. Basic document retrieval using the KnowledgeBase
2. Retrieving documents with relevance scoring
3. Filtering documents by metadata
4. Adjusting retrieval parameters for different use cases
5. Integrating retrieval with the query client

It shows how Atlas can be used as a powerful retrieval system for finding
relevant information in a knowledge base.
"""

import sys
from typing import Dict, Any, List

# Import common utilities for Atlas examples
from common import setup_example, create_provider_from_args, print_example_footer, ensure_example_data, handle_example_error
from atlas.core import logging

# Import atlas modules
from atlas.knowledge.retrieval import KnowledgeBase, RetrievalSettings, RetrievalFilter
from atlas import create_query_client


def format_document(doc: Any, index: int) -> None:
    """Format and print a document in a readable way.
    
    Args:
        doc: Document object or dictionary
        index: Result number for display
    """
    # Handle both dictionary and RetrievalResult objects
    if hasattr(doc, 'metadata'):
        # It's a RetrievalResult object
        source = doc.metadata.get('source', 'Unknown')
        doc_id = doc.id if hasattr(doc, 'id') else 'Unknown'
        relevance = doc.relevance_score
        content = doc.content
        metadata = doc.metadata
    else:
        # It's a dictionary
        source = doc['metadata'].get('source', 'Unknown')
        doc_id = doc.get('id', 'Unknown')
        relevance = doc['relevance_score']
        content = doc['content']
        metadata = doc['metadata']
    
    print(f"\nResult {index}:")
    print(f"- Source: {source}")
    print(f"- Document ID: {doc_id}")
    print(f"- Relevance: {relevance:.4f}")
    
    # Print key metadata if available
    if 'chunk_id' in metadata:
        print(f"- Chunk ID: {metadata.get('chunk_id')}")
    if 'filename' in metadata:
        print(f"- Filename: {metadata.get('filename')}")
    
    # Print content preview
    print(f"- Content preview: {content[:150]}...")


def add_example_arguments(parser):
    """Add example-specific arguments to the parser."""
    # Skip database options since they're now in the common parser

    # Retrieval options
    parser.add_argument(
        "--query",
        type=str,
        help="Specific query to use instead of example queries"
    )
    parser.add_argument(
        "--n-results",
        type=int,
        default=5,
        help="Number of results to return (default: 5)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="Relevance threshold for filtering results (default: 0.0)"
    )


def main():
    """Run the retrieval example."""
    # Set up the example with standardized logging and argument parsing
    args = setup_example("Atlas Basic Retrieval Example", add_example_arguments)
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

        logger.info(f"Knowledge base ready: Collection: {kb.collection_name}, Document count: {collection_count}")
        print(f"\nKnowledge base ready:")
        print(f"- Collection: {kb.collection_name}")
        print(f"- Document count: {collection_count}")
        
        # Example 1: Basic retrieval
        print("\n" + "-"*50)
        print("Example 1: Basic Retrieval")
        print("-"*50)
        
        query = args.query or "What is the trimodal methodology in Atlas?"
        logger.info(f"Performing basic retrieval for query: {query}")
        print(f"\nQuery: {query}")
        print(f"Retrieving top {args.n_results} results...")
        
        results = kb.retrieve(query, n_results=args.n_results)
        print(f"\nFound {len(results)} results")
        
        for i, doc in enumerate(results, 1):
            format_document(doc, i)
        
        # Example 2: Retrieval with threshold filtering
        print("\n" + "-"*50)
        print("Example 2: Retrieval with Relevance Threshold")
        print("-"*50)
        
        threshold = args.threshold or 0.6  # Higher threshold for more relevant results
        query = "How does Atlas handle error management?"
        logger.info(f"Performing retrieval with threshold {threshold} for query: {query}")
        print(f"\nQuery: {query}")
        print(f"Retrieving results with relevance threshold of {threshold}...")
        
        # Use settings for threshold
        from atlas.knowledge.settings import RetrievalSettings
        settings = RetrievalSettings(num_results=args.n_results, min_relevance_score=threshold)
        results = kb.retrieve(query, n_results=args.n_results, settings=settings)
        print(f"\nFound {len(results)} results meeting the threshold")
        
        for i, doc in enumerate(results, 1):
            format_document(doc, i)
        
        # Example 3: Retrieval with metadata filtering
        print("\n" + "-"*50)
        print("Example 3: Retrieval with Metadata Filtering")
        print("-"*50)

        query = "What are the core components of Atlas?"

        # Let's first inspect what metadata we have in the database
        print(f"\nChecking available metadata fields in collection...")
        metadata_fields = kb.get_metadata_fields()
        print(f"Available metadata fields: {', '.join(metadata_fields)}")

        # Create settings and filter for the query
        from atlas.knowledge.settings import RetrievalSettings
        from atlas.knowledge.retrieval import RetrievalFilter

        # Initialize settings
        settings = RetrievalSettings(
            num_results=args.n_results,
            rerank_results=True  # Apply reranking for better results
        )

        # Initialize a basic filter using the RetrievalFilter class
        # We'll look for documents where the 'source' field contains 'components'
        # Using exact equality matching as that's what ChromaDB 1.0.8 supports
        print(f"\nQuery: {query}")
        print(f"Metadata filter: source contains 'components'")
        logger.info(f"Performing retrieval with metadata filter for query: {query}")

        try:
            # Method 1: Using RetrievalFilter and retrieve() method
            # This is the recommended way to use filters with Atlas
            print("\nMethod 1: Using RetrievalFilter with Atlas retrieve() method")
            filter = RetrievalFilter()

            # Simple, direct filter for docs/components path since we're using a
            # consistent example database with known paths
            try:
                # Known paths that should exist in example data
                test_paths = [
                    "docs/components",
                    "docs/components/core",
                    "docs/components/knowledge",
                    "docs/components/agents",
                    "docs/components/models"
                ]

                # Start with these known paths that should work with our example data
                sources = test_paths.copy()

                # Verify the paths actually exist in the database
                existing_sources = []
                for path in test_paths:
                    try:
                        # Check if this exact path exists
                        results = kb.collection.get(
                            where={"source": path},
                            limit=1
                        )
                        if results["ids"] and len(results["ids"]) > 0:
                            existing_sources.append(path)
                    except Exception as source_err:
                        logger.debug(f"Error checking path {path}: {source_err}")

                # If we found valid paths, use only those
                if existing_sources:
                    sources = existing_sources
                    logger.info(f"Found {len(existing_sources)} existing component paths")
                else:
                    # Fall back to a sample-based approach if no exact paths found
                    logger.warning("No exact component paths found, checking sample documents")
                    sample = kb.collection.get(limit=100)
                    sample_sources = []
                    for metadata in sample["metadatas"]:
                        if "source" in metadata and "components" in str(metadata["source"]).lower():
                            sample_sources.append(metadata["source"])

                    if sample_sources:
                        sources = list(set(sample_sources))
                    else:
                        # Final fallback
                        sources = ["docs/components"]
            except Exception as e:
                logger.error(f"Error searching for sources: {e}")
                # Fallback
                sources = ["docs/components"]

            print(f"Found {len(sources)} source values containing 'components':")
            for i, source in enumerate(sources[:5]):
                print(f"  - {source}")

            if sources:
                # Create an $or filter to match any of these sources
                if len(sources) == 1:
                    filter.add_filter("source", sources[0])
                else:
                    # For multiple sources, we need to use $in operator
                    filter.add_in_filter("source", sources)

                # Retrieve with our filter
                results = kb.retrieve(
                    query,
                    filter=filter,
                    settings=settings
                )

                print(f"\nFound {len(results)} results with metadata filter")
                for i, doc in enumerate(results, 1):
                    format_document(doc, i)
            else:
                # If no matching sources found, use a simple exact filter
                # Using "components" would likely not match anything since our paths are normalized
                # to include the parent directory
                filter.add_filter("source", "docs/components")

                # Retrieve with our filter
                results = kb.retrieve(
                    query,
                    filter=filter,
                    settings=settings
                )

                print(f"\nFound {len(results)} results with exact 'docs/components' filter")
                for i, doc in enumerate(results, 1):
                    format_document(doc, i)

                # If still no results, try with the raw ChromaDB API using a direct path
                if not results:
                    print("\nMethod 2: Using direct ChromaDB API with dictionary filter")
                    # Try a known path that should exist in our example data
                    where_filter = {"source": "docs/components"}
                    results = kb.collection.query(
                        query_texts=[query],
                        n_results=args.n_results,
                        where=where_filter
                    )

                    # Format results from ChromaDB's native format to our RetrievalResult format
                    formatted_results = []
                    if results and results["ids"] and len(results["ids"][0]) > 0:
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

                            formatted_results.append(
                                RetrievalResult(
                                    content=doc,
                                    metadata=metadata,
                                    relevance_score=relevance_score,
                                    distance=distance,
                                )
                            )

                    if formatted_results:
                        print(f"\nFound {len(formatted_results)} results with direct ChromaDB query")
                        for i, doc in enumerate(formatted_results, 1):
                            format_document(doc, i)
                    else:
                        print("\nNo results found with the direct ChromaDB query")

        except Exception as e:
            logger.exception(f"Error with metadata filtering: {e}")
            print(f"Error with metadata filtering: {e}")
            print("Showing ChromaDB collection info for debugging:")
            print(f"  - Collection name: {kb.collection_name}")
            print(f"  - Document count: {kb.collection.count()}")
            print(f"  - Available metadata fields: {', '.join(metadata_fields)}")
            print("\nThis might happen if your ChromaDB version doesn't support this filtering syntax")
            print("Try using version 1.0.8 or later of ChromaDB")
        
        # Example 4: Integration with query client
        print("\n" + "-"*50)
        print("Example 4: Integration with Query Client")
        print("-"*50)
        
        try:
            # Create provider from command line arguments
            provider = create_provider_from_args(args)
            logger.info(f"Created provider: {provider.name} with model {provider.model_name}")
            print(f"\nCreating provider: {provider.name} with model {provider.model_name}")
            
            # Create query client
            client = create_query_client(
                provider_name=provider.name, 
                model_name=provider.model_name,
                collection_name=collection_name,
                db_path=db_path
            )
            
            # Query with context
            query = "How does Atlas handle knowledge graph structure?"
            logger.info(f"Performing query with context: {query}")
            print(f"\nQuery: {query}")
            
            result = client.query_with_context(query)
            print(f"\nResponse with {len(result['context']['documents'])} context documents:")
            print(result["response"])
            
            print("\nSupporting Documents:")
            for i, doc in enumerate(result['context']['documents'][:3], 1):
                # Convert to consistent format for printing
                formatted_doc = {
                    'metadata': {'source': doc.get('source', 'Unknown')},
                    'relevance_score': doc.get('relevance_score', 0.0),
                    'content': doc.get('content', '')
                }
                format_document(formatted_doc, i)
                
        except Exception as e:
            logger.exception(f"Error creating query client: {e}")
            print(f"\nError creating query client: {e}")
            print("Try using '--provider mock' for testing without API keys")
    
    except Exception as e:
        logger.exception(f"Error during retrieval: {e}")
        print(f"Error during retrieval: {e}")
        sys.exit(1)
    
    # Print footer
    print_example_footer()
    
    # Print additional information
    print("Additional Information:")
    print("\nRetrieval Methods:")
    print("- Semantic search using embeddings is the default method")
    print("- Supports filtering by metadata to narrow results")
    print("- Relevance threshold can be used to ensure quality")
    print("- The query client integrates retrieval with LLM responses")
    
    print("\nAdvanced Techniques:")
    print("- For hybrid retrieval combining semantic and keyword search, see example 12_hybrid_retrieval.py")
    print("- For multi-retriever workflows, see example 22_agent_workflows.py")
    print("- The default embedding model is text-embedding-ada-002 but can be configured")
    
    print("\nUsage Tips:")
    print("- More specific queries typically yield better results")
    print("- Adjust the relevance threshold based on your application needs")
    print("- Use metadata filtering for targeted retrieval from specific sources")
    print("- Ingest high-quality, well-structured documents for best results")


if __name__ == "__main__":
    main()