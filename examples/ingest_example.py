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
    
    args = parser.parse_args()
    
    print(f"Starting document ingestion from: {args.directory}")
    print(f"Using collection: {args.collection}")
    
    # Create document processor
    processor = DocumentProcessor(collection_name=args.collection)
    
    # Process the directory
    processor.process_directory(args.directory, recursive=args.recursive)
    
    print("\nIngestion complete!")

if __name__ == "__main__":
    main()