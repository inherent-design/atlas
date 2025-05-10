#!/usr/bin/env python3
"""
Document Ingestion Example (10_document_ingestion.py)

This example demonstrates how to ingest documents into Atlas's knowledge base:
1. Loading documents from a directory
2. Processing and chunking documents
3. Adding metadata to chunks
4. Storing documents in the vector database
5. Verifying ingestion through simple retrieval

It shows the core knowledge management functionality that powers Atlas's
retrieval-augmented generation capabilities.
"""

import os
import sys
import datetime
from typing import Dict, Any, List

# Import common utilities for Atlas examples
from common import setup_example, print_example_footer, handle_example_error
from atlas.core import logging

# Import atlas modules
from atlas.knowledge.ingest import DocumentProcessor
from atlas.knowledge.retrieval import KnowledgeBase


def add_example_arguments(parser):
    """Add example-specific arguments to the parser."""
    # Document source options
    parser.add_argument(
        "--docs-dir",
        type=str,
        default="docs",
        help="Directory containing documents to ingest (default: docs)"
    )
    parser.add_argument(
        "--glob-pattern",
        type=str,
        default="**/*.md",
        help="Glob pattern for matching files (default: **/*.md)"
    )
    
    # Database options - note that --collection and --db-path are already set in common.py
    # We don't need to re-add them here
    
    # Processing options
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1500,
        help="Character size for document chunks (default: 1500)"
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Character overlap between chunks (default: 200)"
    )
    parser.add_argument(
        "--use-existing",
        action="store_true",
        help="Use existing ingestion if available (don't re-ingest)"
    )


def main():
    """Run the document ingestion example."""
    # Set up the example with standardized logging and argument parsing
    args = setup_example("Atlas Document Ingestion Example", add_example_arguments)
    logger = logging.get_logger(__name__)
    
    # Create the document ingestion object
    logger.info(f"Initializing document ingestion:")
    print(f"Initializing document ingestion:")
    print(f"- Document directory: {args.docs_dir}")
    print(f"- Glob pattern: {args.glob_pattern}")
    print(f"- Chunk size: {args.chunk_size} characters")
    print(f"- Chunk overlap: {args.chunk_overlap} characters")
    
    # Resolve paths
    docs_dir = os.path.abspath(args.docs_dir)
    if not os.path.exists(docs_dir):
        logger.error(f"Document directory {docs_dir} does not exist")
        print(f"Error: Document directory {docs_dir} does not exist")
        sys.exit(1)
    
    start_time = datetime.datetime.now()
    
    # Initialize the ingestion system
    try:
        # Create document processor with specified options
        processor = DocumentProcessor(
            collection_name=args.collection,
            db_path=args.db_path,
            # chunk_size and chunk_overlap are not directly passed in constructor
        )
        
        # Check if collection exists and has documents
        collection_count = processor.collection.count() if hasattr(processor, 'collection') else 0
        
        if collection_count > 0 and args.use_existing:
            logger.info(f"Found existing collection with {collection_count} documents")
            print(f"\nFound existing collection with {collection_count} documents")
            print("Using existing documents as --use-existing flag is set")
        else:
            # Perform ingestion
            logger.info(f"Starting document ingestion from {docs_dir}...")
            print(f"\nStarting document ingestion from {docs_dir}...")
            
            # Process the directory recursively
            num_processed = processor.process_directory(docs_dir, recursive=True)
            
            # Report ingestion results
            logger.info(f"Ingestion complete: {num_processed} files processed")
            print(f"\nIngestion complete:")
            print(f"- Files processed: {num_processed}")
            print(f"- Documents stored in collection: {processor.collection.count()}")
            
            # Report timing
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"- Processing time: {duration:.2f} seconds")
            
            if num_processed > 0:
                print(f"- Average time per file: {duration / num_processed:.4f} seconds")
        
        # Initialize knowledge base for retrieval test
        logger.info("Initializing knowledge base for retrieval test")
        print("\nInitializing knowledge base for retrieval test...")
        kb = KnowledgeBase(
            collection_name=args.collection,
            db_path=args.db_path,
        )
        
        # Test retrieval with a sample query
        print("\nTesting retrieval with sample queries:")
        
        sample_queries = [
            "What is the trimodal methodology in Atlas?",
            "How does Atlas handle knowledge representation?",
            "What are the core components of Atlas?",
        ]
        
        for i, query in enumerate(sample_queries, 1):
            logger.info(f"Testing retrieval with query: {query}")
            print(f"\nSample Query {i}: {query}")
            results = kb.retrieve(query, n_results=2)
            
            for j, doc in enumerate(results, 1):
                # Handle both dictionary and retrieval result formats
                if hasattr(doc, 'metadata'):
                    source = doc.metadata.get('source', 'Unknown')
                    relevance = doc.relevance_score
                    content = doc.content
                else:
                    source = doc['metadata'].get('source', 'Unknown')
                    relevance = doc['relevance_score']
                    content = doc['content']
                
                print(f"\nResult {j}:")
                print(f"- Source: {source}")
                print(f"- Relevance: {relevance:.4f}")
                print(f"- Content preview: {content[:150]}...")
    
    except Exception as e:
        handle_example_error(
            logger,
            e,
            "Error during document ingestion",
            exit_code=1
        )
    
    # Print footer
    print_example_footer()
    
    # Print additional information
    print("Additional Information:")
    print("\nSupported Document Types:")
    print("- Markdown (.md): Full support with metadata extraction")
    print("- Text (.txt): Basic support")
    print("- PDF (.pdf): Support via optional dependencies")
    print("- More formats can be added through custom document loaders")
    
    print("\nChunking Strategy:")
    print("Atlas uses a recursive chunking strategy that respects document structure")
    print("- Adjustable chunk size and overlap")
    print("- Preserves context around chunk boundaries")
    print("- Maintains metadata across chunks")
    
    print("\nUsage Tips:")
    print("- Larger chunk sizes preserve more context but use more tokens")
    print("- Smaller chunks allow more focused retrieval")
    print("- Overlap helps maintain continuity between chunks")
    print("- Use more specific queries for better retrieval results")


if __name__ == "__main__":
    main()