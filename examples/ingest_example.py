"""
Example script for document ingestion with improved features.

This example demonstrates the improved document ingestion process with:

1. Enhanced Document ID Format:
   - Simplified IDs using "parent_dir/filename.md" format instead of full paths
   - Improves readability and debugging of document references
   - Maintains compatibility with full paths in the source field

2. Comprehensive Progress Indicators:
   - Visual progress bar showing percentage completion during file processing
   - Current file counter (e.g., "Processing: file.md (1/54)")
   - Spinner animation during embedding with elapsed time display
   - Performance metrics showing timing information and throughput

3. Detailed Summary Statistics:
   - Files processed, chunks created, documents added
   - Collection size information
   - Duplicate detection reporting
"""

import os
import argparse
from atlas.knowledge.ingest import DocumentProcessor

def main():
    parser = argparse.ArgumentParser(description="Ingest documents with progress indicators")
    parser.add_argument("-d", "--directory", type=str, default="./docs",
                        help="Directory containing documents to ingest")
    parser.add_argument("-c", "--collection", type=str, default="atlas_knowledge_base",
                        help="Collection name for document storage")
    parser.add_argument("--recursive", action="store_true", default=True,
                        help="Process subdirectories recursively")
    parser.add_argument("--embedding", type=str, choices=["default", "anthropic", "hybrid"],
                        default="default", help="Embedding strategy to use")
    parser.add_argument("--no-dedup", action="store_true",
                        help="Disable content deduplication")
    parser.add_argument("--db-path", type=str,
                        help="Path to ChromaDB database directory")
    
    args = parser.parse_args()
    
    print(f"Starting document ingestion from: {args.directory}")
    print(f"Using collection: {args.collection}")
    
    # Set up embedding strategy and get API key if needed
    anthropic_api_key = None
    if args.embedding == "anthropic":
        # If we're using Anthropic for embeddings, get the API key
        from atlas.core import env
        anthropic_api_key = env.get_api_key("anthropic")
        if not anthropic_api_key:
            print("Error: Anthropic API key required for Anthropic embeddings")
            print("Please set the ANTHROPIC_API_KEY environment variable")
            return
    
    # Create document processor with specified options
    processor = DocumentProcessor(
        collection_name=args.collection,
        db_path=args.db_path,
        enable_deduplication=not args.no_dedup,
        embedding_strategy=args.embedding,
        anthropic_api_key=anthropic_api_key,
    )
    
    # Process the directory
    processor.process_directory(args.directory, recursive=args.recursive)
    
    print("\nIngestion complete!")

if __name__ == "__main__":
    main()