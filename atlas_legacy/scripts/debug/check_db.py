#!/usr/bin/env python3
"""
Utility to check the contents of the ChromaDB database.
"""

import os

# Set environment variable to skip API key check
os.environ["SKIP_API_KEY_CHECK"] = "1"

from atlas.knowledge.retrieval import KnowledgeBase


def main():
    """Check ChromaDB contents."""
    # Initialize knowledge base
    kb = KnowledgeBase(collection_name="atlas_knowledge_base")

    # Get document count
    doc_count = kb.collection.count()
    print(f"\nTotal documents: {doc_count}")

    # Get a sample of documents
    if doc_count > 0:
        limit = min(10, doc_count)
        results = kb.collection.get(limit=limit)

        # Print document information
        print(f"\nSample of {limit} documents:")

        for i, (doc_id, metadata) in enumerate(
            zip(results["ids"], results["metadatas"], strict=False)
        ):
            path = metadata.get("path", "Unknown")
            source = metadata.get("source", "Unknown")
            section = metadata.get("section", "None")

            print(f"\n{i + 1}. ID: {doc_id}")
            print(f"   Path: {path}")
            print(f"   Source: {source}")
            print(f"   Section: {section}")

        # Count documents per source file
        print("\nAnalyzing document sources...")

        # Get all documents (increase limit if needed)
        try:
            all_results = kb.collection.get(limit=doc_count)

            # Count by source path
            path_counts = {}
            source_counts = {}
            for metadata in all_results["metadatas"]:
                path = metadata.get("path", "Unknown")
                source = metadata.get("source", "Unknown")
                path_counts[path] = path_counts.get(path, 0) + 1
                source_counts[source] = source_counts.get(source, 0) + 1

            # Sort by count (descending)
            sorted_paths = sorted(path_counts.items(), key=lambda x: x[1], reverse=True)

            # Print top 10 most common paths
            print("\nTop 10 most common document sources by path:")
            for i, (path, count) in enumerate(sorted_paths[:10]):
                print(f"{i + 1}. {path}: {count} chunks")

            # Sort by count (descending)
            sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)

            # Print top 10 most common sources
            print("\nTop 10 most common document sources by source field:")
            for i, (source, count) in enumerate(sorted_sources[:10]):
                print(f"{i + 1}. {source}: {count} chunks")

            # Count total unique paths and sources
            print(f"\nTotal unique document paths: {len(path_counts)}")
            print(f"Total unique document sources: {len(source_counts)}")

            # Check for potential duplicates
            repeated_chunks = {path: count for path, count in path_counts.items() if count > 20}
            if repeated_chunks:
                print("\nPotential duplicate sources (>20 chunks):")
                for path, count in sorted(
                    repeated_chunks.items(), key=lambda x: x[1], reverse=True
                ):
                    print(f"- {path}: {count} chunks")

        except Exception as e:
            print(f"Error analyzing all documents: {e}")

    print("\nDatabase check complete.")


if __name__ == "__main__":
    main()
