"""
Knowledge retrieval tools for the Atlas agent.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from langgraph.graph import StateGraph


class KnowledgeBase:
    def __init__(
        self,
        collection_name: str = "atlas_knowledge_base",
        db_path: Optional[str] = None,
    ):
        """Initialize the knowledge base.

        Args:
            collection_name: Name of the Chroma collection to use.
            db_path: Optional path for ChromaDB storage. If None, use default in home directory.
        """
        # Create an absolute path for ChromaDB storage (use provided or default to home directory)
        if db_path:
            self.db_path = db_path
        else:
            home_dir = Path.home()
            db_path = home_dir / "atlas_chroma_db"
            db_path.mkdir(exist_ok=True)
            self.db_path = str(db_path.absolute())
        print(f"ChromaDB persistence directory: {self.db_path}")

        # List contents of directory to debug
        print(f"Current contents of DB directory:")
        try:
            for item in os.listdir(self.db_path):
                item_path = os.path.join(self.db_path, item)
                if os.path.isdir(item_path):
                    print(f"  - {item}/ (directory)")
                else:
                    size = os.path.getsize(item_path) / 1024  # Size in KB
                    print(f"  - {item} ({size:.2f} KB)")
        except Exception as e:
            print(f"Error listing DB directory: {e}")

        try:
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            print(
                f"ChromaDB client initialized successfully with persistence at: {self.db_path}"
            )

            # List all collections
            try:
                all_collections = self.chroma_client.list_collections()
                print(f"Available collections: {[c.name for c in all_collections]}")
            except Exception as e:
                print(f"Error listing collections: {e}")

            # Get or create collection
            try:
                self.collection = self.chroma_client.get_or_create_collection(
                    name=collection_name
                )
                print(f"Collection '{collection_name}' accessed successfully")

                # Verify persistence by checking collection count
                count = self.collection.count()
                print(f"Collection contains {count} documents")

                if count == 0:
                    print("WARNING: Collection is empty. Has any data been ingested?")
                    print("Try running with -d <directory> flag to ingest documents.")
            except Exception as e:
                print(f"Error accessing collection: {e}")
                raise e

        except Exception as e:
            print(f"Error initializing ChromaDB: {str(e)}")
            print("Using fallback in-memory ChromaDB")
            self.chroma_client = chromadb.Client()
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name
            )

    def retrieve(
        self, query: str, n_results: int = 5, version_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents based on a query.

        Args:
            query: The query to search for.
            n_results: Number of results to return.
            version_filter: Optional filter for specific Atlas version.

        Returns:
            A list of relevant documents with their metadata.
        """
        # Prepare filters if any
        where_clause = {}
        if version_filter:
            where_clause["version"] = version_filter

        # Query the collection
        try:
            # Ensure we don't request more results than exist
            doc_count = self.collection.count()
            if doc_count == 0:
                print("Warning: Collection is empty. No results will be returned.")
                return []

            actual_n_results = min(n_results, doc_count)

            results = self.collection.query(
                query_texts=[query],
                n_results=actual_n_results,
                where=where_clause if where_clause else None,
            )

            # Format results
            documents = []
            for i, (doc, metadata, distance) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ):
                documents.append(
                    {
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1.0
                        - distance,  # Convert distance to relevance score
                    }
                )

            return documents
        except Exception as e:
            print(f"Error retrieving from knowledge base: {str(e)}")
            print(f"Query was: {query[:50]}...")
            print(f"Stack trace: {sys.exc_info()[2]}")
            return []

    def get_versions(self) -> List[str]:
        """Get all available Atlas versions in the knowledge base.

        Returns:
            A list of version strings.
        """
        # This is a simple implementation that may need optimization for larger datasets
        try:
            doc_count = self.collection.count()
            if doc_count == 0:
                return []

            # Adjust limit based on document count
            limit = min(1000, doc_count)
            results = self.collection.get(limit=limit)

            versions = set()
            for metadata in results["metadatas"]:
                if "version" in metadata:
                    versions.add(metadata["version"])

            return sorted(list(versions))
        except Exception as e:
            print(f"Error getting versions: {str(e)}")
            return []

    def search_by_topic(self, topic: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for documents related to a specific topic.

        Args:
            topic: The topic to search for.
            n_results: Number of results to return.

        Returns:
            A list of relevant documents with their metadata.
        """
        # This could be enhanced with more sophisticated topic matching
        return self.retrieve(topic, n_results)


# Function for use within LangGraph
def retrieve_knowledge(
    state: Dict[str, Any],
    query: Optional[str] = None,
    collection_name: str = "atlas_knowledge_base",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve knowledge from the Atlas knowledge base.

    Args:
        state: The current state of the agent.
        query: Optional query override. If not provided, uses the user's last message.
        collection_name: Name of the Chroma collection to use.
        db_path: Optional path for ChromaDB storage. If None, use default in home directory.

    Returns:
        Updated state with retrieved knowledge.
    """
    # Initialize knowledge base with specified collection
    kb = KnowledgeBase(collection_name=collection_name, db_path=db_path)

    # Get the query from the state if not explicitly provided
    if not query:
        messages = state.get("messages", [])
        if not messages:
            print("No messages in state, cannot determine query")
            state["context"] = {"documents": [], "query": ""}
            return state

        last_user_message = None
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user_message = message.get("content", "")
                break

        if not last_user_message:
            print("No user messages found in state")
            state["context"] = {"documents": [], "query": ""}
            return state

        query = last_user_message

    print(
        f"Retrieving knowledge for query: {query[:50]}{'...' if len(query) > 50 else ''}"
    )

    # Retrieve relevant documents
    documents = kb.retrieve(query)
    print(f"Retrieved {len(documents)} relevant documents")

    if documents:
        # Print the top document sources for debugging
        print("Top relevant documents:")
        for i, doc in enumerate(documents[:3]):
            source = doc["metadata"].get("source", "Unknown")
            score = doc["relevance_score"]
            print(f"  {i + 1}. {source} (score: {score:.4f})")

    # Update state with retrieved documents
    state["context"] = {"documents": documents, "query": query}

    return state
