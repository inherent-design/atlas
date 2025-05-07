"""
Verify that the document IDs are using the simplified format.

This script queries the ChromaDB collection and prints out a sample of document IDs
to confirm they're using the simplified 'parent_dir/filename.md' format.
"""

import os
import chromadb
import random

def main():
    # Initialize ChromaDB client
    db_path = os.path.expanduser("~/atlas_chroma_db")
    print(f"Connecting to ChromaDB at: {db_path}")
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection("atlas_knowledge_base")
        
        # Get collection stats
        doc_count = collection.count()
        print(f"Collection contains {doc_count} documents")
        
        if doc_count == 0:
            print("No documents found. Please ingest documents first.")
            return
        
        # Get a random sample of document IDs
        result = collection.get(limit=100)
        
        if not result["ids"]:
            print("No documents returned from query.")
            return
        
        # Display some random document IDs
        print("\nSample Document IDs:")
        print("=" * 50)
        
        # Get up to 10 random documents
        sample_count = min(10, len(result["ids"]))
        indices = random.sample(range(len(result["ids"])), sample_count)
        
        for i in indices:
            doc_id = result["ids"][i]
            metadata = result["metadatas"][i]
            source = metadata.get("source", "unknown")
            simple_id = metadata.get("simple_id", "missing")
            
            print(f"Document ID: {doc_id}")
            print(f"Source Path: {source}")
            print(f"Simple ID:   {simple_id}")
            print("-" * 50)
        
        # Check for consistency
        print("\nVerifying ID format consistency...")
        
        # Count documents using the simplified format
        simplified_count = 0
        for doc_id in result["ids"]:
            if "#" in doc_id and len(doc_id.split("/")) <= 3:  # At most parent/file.md#0 format
                simplified_count += 1
        
        consistency = (simplified_count / len(result["ids"])) * 100
        print(f"Simplified ID format usage: {simplified_count}/{len(result['ids'])} documents ({consistency:.1f}%)")
        
        if consistency >= 90:
            print("✓ Document IDs are consistently using the simplified format!")
        else:
            print("⚠ Document IDs are not consistently using the simplified format.")
    
    except Exception as e:
        print(f"Error accessing ChromaDB: {e}")

if __name__ == "__main__":
    main()