"""
Knowledge retrieval tools for the Atlas agent.

This module provides tools for retrieving and querying knowledge from the vector database,
with support for metadata filtering, hybrid retrieval, and relevance scoring.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, Set

import chromadb
import re
import numpy as np
from atlas.core import env
from atlas.knowledge.embedding import EmbeddingStrategy, EmbeddingStrategyFactory

logger = logging.getLogger(__name__)


class RetrievalFilter:
    """Filter for retrieval queries."""
    
    def __init__(self, where: Optional[Dict[str, Any]] = None):
        """Initialize a retrieval filter.
        
        Args:
            where: ChromaDB where clause for filtering.
        """
        self.where = where or {}
    
    @staticmethod
    def from_metadata(
        source_path: Optional[str] = None,
        file_type: Optional[str] = None,
        version: Optional[str] = None,
        section_title: Optional[str] = None,
        exclude_duplicates: bool = True,
        additional_filters: Optional[Dict[str, Any]] = None,
    ) -> "RetrievalFilter":
        """Create a filter from metadata fields.
        
        Args:
            source_path: Optional path to filter by source.
            file_type: Optional file type to filter by.
            version: Optional version to filter by.
            section_title: Optional section title to filter by.
            exclude_duplicates: Whether to exclude duplicate chunks.
            additional_filters: Additional filters to apply.
            
        Returns:
            A RetrievalFilter instance.
        """
        where = {}
        
        if source_path:
            # Allow partial path matching
            if source_path.endswith("/"):
                # Directory path, match all files in directory
                where["source"] = {"$regex": f"^{source_path}"}
            else:
                # Exact file path
                where["source"] = source_path
                
        if file_type:
            where["file_type"] = file_type
            
        if version:
            where["version"] = version
            
        if section_title:
            # Allow partial section title matching
            where["section_title"] = {"$contains": section_title}
            
        if exclude_duplicates:
            # Exclude chunks that are duplicates
            where["$not"] = {"duplicate_of": {"$exists": True}}
        
        # Add any additional filters
        if additional_filters:
            where.update(additional_filters)
        
        return RetrievalFilter(where)
    
    def add_filter(self, key: str, value: Any) -> "RetrievalFilter":
        """Add a filter condition.
        
        Args:
            key: The metadata key to filter on.
            value: The value to filter for.
            
        Returns:
            Self for chaining.
        """
        self.where[key] = value
        return self
    
    def remove_filter(self, key: str) -> "RetrievalFilter":
        """Remove a filter condition.
        
        Args:
            key: The metadata key to remove filtering for.
            
        Returns:
            Self for chaining.
        """
        if key in self.where:
            del self.where[key]
        return self


class RetrievalResult:
    """A single retrieval result with content and metadata."""
    
    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        relevance_score: float = 0.0,
        distance: float = 0.0,
    ):
        """Initialize a retrieval result.
        
        Args:
            content: The content of the result.
            metadata: Metadata about the result.
            relevance_score: Relevance score (0-1, higher is more relevant).
            distance: Distance from query (lower is closer).
        """
        self.content = content
        self.metadata = metadata
        self.relevance_score = relevance_score
        self.distance = distance
    
    def __str__(self) -> str:
        """String representation of the result.
        
        Returns:
            String representation with content snippet and score.
        """
        content_snippet = self.content[:100] + "..." if len(self.content) > 100 else self.content
        return f"Result(score={self.relevance_score:.4f}, content='{content_snippet}')"
    
    @property
    def source(self) -> str:
        """Get the source of the result.
        
        Returns:
            Source path from metadata.
        """
        return self.metadata.get("source", "unknown")
    
    @property
    def section_title(self) -> str:
        """Get the section title of the result.
        
        Returns:
            Section title from metadata.
        """
        return self.metadata.get("section_title", "")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the result.
        """
        return {
            "content": self.content,
            "metadata": self.metadata,
            "relevance_score": self.relevance_score,
            "distance": self.distance,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetrievalResult":
        """Create from dictionary.
        
        Args:
            data: Dictionary representation of the result.
            
        Returns:
            A RetrievalResult instance.
        """
        return cls(
            content=data["content"],
            metadata=data["metadata"],
            relevance_score=data["relevance_score"],
            distance=data.get("distance", 0.0),
        )


class KnowledgeBase:
    """Knowledge base for storing and retrieving information."""
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        db_path: Optional[str] = None,
        embedding_strategy: Optional[Union[str, EmbeddingStrategy]] = None,
    ):
        """Initialize the knowledge base.
        
        Args:
            collection_name: Name of the Chroma collection to use. If None, use environment variable.
            db_path: Path for ChromaDB storage. If None, use environment variable or default to home directory.
            embedding_strategy: Optional embedding strategy for queries.
        """
        # Get collection name from parameters, environment, or default
        self.collection_name = collection_name or env.get_string(
            "ATLAS_COLLECTION_NAME", "atlas_knowledge_base"
        )
        
        # Create an absolute path for ChromaDB storage (use provided or environment variable or default)
        self.db_path: str = ""
        if db_path:
            self.db_path = db_path
        else:
            env_db_path = env.get_string("ATLAS_DB_PATH")
            if env_db_path:
                self.db_path = env_db_path
                # Create directory if it doesn't exist
                db_path_obj = Path(self.db_path)
                db_path_obj.mkdir(exist_ok=True, parents=True)
            else:
                home_dir = Path.home()
                db_path_obj = home_dir / "atlas_chroma_db"
                db_path_obj.mkdir(exist_ok=True)
                self.db_path = str(db_path_obj.absolute())
        
        logger.info(f"ChromaDB persistence directory: {self.db_path}")
        print(f"ChromaDB persistence directory: {self.db_path}")
        
        # Initialize ChromaDB
        self._initialize_chroma_db()
        
        # Initialize embedding strategy
        if isinstance(embedding_strategy, EmbeddingStrategy):
            self.embedding_strategy = embedding_strategy
        elif isinstance(embedding_strategy, str):
            self.embedding_strategy = EmbeddingStrategyFactory.create_strategy(embedding_strategy)
        else:
            self.embedding_strategy = EmbeddingStrategyFactory.create_strategy("default")
    
    def _initialize_chroma_db(self) -> None:
        """Initialize the ChromaDB client and collection."""
        try:
            # List contents of DB directory
            if os.path.exists(self.db_path):
                print("Current contents of DB directory:")
                for item in os.listdir(self.db_path):
                    item_path = os.path.join(self.db_path, item)
                    if os.path.isdir(item_path):
                        print(f"  - {item}/ (directory)")
                    else:
                        size = os.path.getsize(item_path) / 1024  # Size in KB
                        print(f"  - {item} ({size:.2f} KB)")
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            logger.info(
                f"ChromaDB client initialized successfully with persistence at: {self.db_path}"
            )
            print(
                f"ChromaDB client initialized successfully with persistence at: {self.db_path}"
            )
            
            # List all collections
            try:
                all_collections = self.chroma_client.list_collections()
                print(f"Available collections: {[c.name for c in all_collections]}")
                logger.debug(
                    f"Available collections: {[c.name for c in all_collections]}"
                )
            except Exception as e:
                print(f"Error listing collections: {e}")
                logger.error(f"Error listing collections: {e}")
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name
                )
                print(f"Collection '{self.collection_name}' accessed successfully")
                logger.info(
                    f"Collection '{self.collection_name}' accessed successfully"
                )
                
                # Verify persistence by checking collection count
                count = self.collection.count()
                print(f"Collection contains {count} documents")
                logger.info(f"Collection contains {count} documents")
                
                if count == 0:
                    print("WARNING: Collection is empty. Has any data been ingested?")
                    print("Try running with -d <directory> flag to ingest documents.")
                    logger.warning(
                        "Collection is empty. No documents have been ingested."
                    )
            except Exception as e:
                print(f"Error accessing collection: {e}")
                logger.error(f"Error accessing collection: {e}")
                raise e
        
        except Exception as e:
            error_msg = f"Error initializing ChromaDB: {str(e)}"
            print(error_msg)
            print("Using fallback in-memory ChromaDB")
            logger.error(f"{error_msg}. Using fallback in-memory ChromaDB")
            
            self.chroma_client = chromadb.Client()
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name
            )
    
    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filter: Optional[RetrievalFilter] = None,
        rerank: bool = False,
    ) -> List[RetrievalResult]:
        """Retrieve relevant documents based on a query.
        
        Args:
            query: The query to search for.
            n_results: Number of results to return.
            filter: Optional filter to apply to the query.
            rerank: Whether to rerank results using additional criteria.
            
        Returns:
            A list of relevant documents with their metadata.
        """
        # Prepare filters if any
        where_clause = filter.where if filter else None
        
        # Generate query embedding if using custom strategy
        query_embedding = self.embedding_strategy.embed_query(query)
        
        # Query the collection
        try:
            # Ensure we don't request more results than exist
            doc_count = self.collection.count()
            if doc_count == 0:
                print("Warning: Collection is empty. No results will be returned.")
                return []
            
            # Set a reasonable limit, but also check collection size
            actual_n_results = min(n_results, doc_count)
            
            # We'll request more results than needed if reranking is enabled
            fetch_n_results = actual_n_results * 2 if rerank else actual_n_results
            fetch_n_results = min(fetch_n_results, doc_count)
            
            # Execute the query
            if query_embedding:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=fetch_n_results,
                    where=where_clause,
                )
            else:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=fetch_n_results,
                    where=where_clause,
                )
            
            # Format results
            retrieval_results = []
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
                
                retrieval_results.append(
                    RetrievalResult(
                        content=doc,
                        metadata=metadata,
                        relevance_score=relevance_score,
                        distance=distance,
                    )
                )
            
            # Apply reranking if requested
            if rerank:
                retrieval_results = self._rerank_results(query, retrieval_results, actual_n_results)
            
            # Return the requested number of results
            return retrieval_results[:actual_n_results]
        
        except Exception as e:
            print(f"Error retrieving from knowledge base: {str(e)}")
            print(f"Query was: {query[:50]}...")
            print(f"Stack trace: {sys.exc_info()[2]}")
            logger.error(f"Error retrieving from knowledge base: {str(e)}")
            return []
    
    def _rerank_results(
        self, 
        query: str, 
        results: List[RetrievalResult],
        n_results: int,
    ) -> List[RetrievalResult]:
        """Rerank results using additional criteria.
        
        Args:
            query: The original query.
            results: The initial results.
            n_results: Number of results to return after reranking.
            
        Returns:
            Reranked results list.
        """
        # Simple keyword-based reranking
        # Extract keywords from query
        keywords = re.findall(r'\b\w{3,}\b', query.lower())
        
        # No keywords to rerank with
        if not keywords:
            return results
        
        # Score each result by keyword presence
        for result in results:
            # Count keyword occurrences in content
            content_lower = result.content.lower()
            keyword_hits = sum(1 for kw in keywords if kw in content_lower)
            
            # Adjust score based on keyword hits
            keyword_boost = min(0.2, keyword_hits * 0.05)  # Cap at 0.2 boost
            result.relevance_score = min(1.0, result.relevance_score + keyword_boost)
        
        # Re-sort by adjusted score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results
    
    def retrieve_hybrid(
        self,
        query: str,
        n_results: int = 5,
        filter: Optional[RetrievalFilter] = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[RetrievalResult]:
        """Hybrid retrieval combining semantic and keyword search.
        
        Args:
            query: The query to search for.
            n_results: Number of results to return.
            filter: Optional filter to apply to the query.
            semantic_weight: Weight for semantic search results (0-1).
            keyword_weight: Weight for keyword search results (0-1).
            
        Returns:
            A list of relevant documents with their metadata.
        """
        # Normalize weights
        if semantic_weight + keyword_weight != 1.0:
            total = semantic_weight + keyword_weight
            semantic_weight = semantic_weight / total
            keyword_weight = keyword_weight / total
        
        # Get more results than needed to allow for merging
        semantic_results = self.retrieve(
            query, 
            n_results=min(n_results * 2, 20),
            filter=filter,
            rerank=False,
        )
        
        # Extract keywords for keyword search
        keywords = re.findall(r'\b\w{3,}\b', query.lower())
        
        # If no keywords, just return semantic results
        if not keywords:
            return semantic_results[:n_results]
        
        # Prepare keyword query
        keyword_query = " OR ".join(keywords)
        
        # Get keyword results
        keyword_results = self.retrieve(
            keyword_query,
            n_results=min(n_results * 2, 20),
            filter=filter,
            rerank=False,
        )
        
        # Combine results
        result_map: Dict[str, RetrievalResult] = {}
        
        # Process semantic results
        for result in semantic_results:
            result_id = result.metadata.get("id", id(result))
            result_map[result_id] = result
            # Scale score by semantic weight
            result.relevance_score *= semantic_weight
        
        # Process keyword results
        for result in keyword_results:
            result_id = result.metadata.get("id", id(result))
            if result_id in result_map:
                # Result already in map, add scores
                result_map[result_id].relevance_score += result.relevance_score * keyword_weight
            else:
                # New result, scale score
                result.relevance_score *= keyword_weight
                result_map[result_id] = result
        
        # Convert back to list and sort by relevance
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Return top results
        return combined_results[:n_results]
    
    def get_versions(self) -> List[str]:
        """Get all available Atlas versions in the knowledge base.
        
        Returns:
            A list of version strings.
        """
        # Get all versions from the collection
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
            logger.error(f"Error getting versions: {str(e)}")
            return []
    
    def search_by_metadata(
        self, 
        metadata_field: str, 
        value: Any, 
        n_results: int = 100
    ) -> List[str]:
        """Search for unique values in a metadata field that match a value.
        
        Args:
            metadata_field: The metadata field to search.
            value: The value to search for (can be a string or regex pattern).
            n_results: Maximum number of results to return.
            
        Returns:
            A list of unique matching values.
        """
        try:
            # Get all documents with this metadata field
            where_clause = {metadata_field: {"$exists": True}}
            results = self.collection.get(where=where_clause, limit=min(5000, n_results))
            
            # Extract values
            values = set()
            for metadata in results["metadatas"]:
                if metadata_field in metadata:
                    field_value = metadata[metadata_field]
                    
                    # Exact value match
                    if isinstance(value, str) and isinstance(field_value, str):
                        if value.lower() in field_value.lower():
                            values.add(field_value)
                    # Direct comparison for non-strings
                    elif field_value == value:
                        values.add(field_value)
            
            # Convert to list and limit
            value_list = list(values)
            return value_list[:n_results]
            
        except Exception as e:
            print(f"Error searching metadata: {str(e)}")
            logger.error(f"Error searching metadata: {str(e)}")
            return []
    
    def get_metadata_fields(self) -> List[str]:
        """Get all metadata fields used in the collection.
        
        Returns:
            A list of metadata field names.
        """
        try:
            # Sample some documents
            doc_count = self.collection.count()
            if doc_count == 0:
                return []
            
            # Get a sample of documents
            limit = min(100, doc_count)
            results = self.collection.get(limit=limit)
            
            # Extract unique metadata fields
            fields = set()
            for metadata in results["metadatas"]:
                fields.update(metadata.keys())
            
            return sorted(list(fields))
        except Exception as e:
            print(f"Error getting metadata fields: {str(e)}")
            logger.error(f"Error getting metadata fields: {str(e)}")
            return []


# Function for use with LangGraph
def retrieve_knowledge(
    state: Dict[str, Any],
    query: Optional[str] = None,
    collection_name: Optional[str] = None,
    db_path: Optional[str] = None,
    filter: Optional[RetrievalFilter] = None,
    use_hybrid: bool = False,
) -> Dict[str, Any]:
    """Retrieve knowledge from the Atlas knowledge base.
    
    Args:
        state: The current state of the agent.
        query: Optional query override. If not provided, uses the user's last message.
        collection_name: Name of the Chroma collection to use. If None, use environment variable.
        db_path: Path to ChromaDB. If None, use environment variable or default.
        filter: Optional filter for retrieval.
        use_hybrid: Whether to use hybrid retrieval.
        
    Returns:
        Updated state with retrieved knowledge.
    """
    # Initialize knowledge base with specified collection or from environment variables
    kb = KnowledgeBase(collection_name=collection_name, db_path=db_path)
    
    # Get the query from the state if not explicitly provided
    if not query:
        messages = state.get("messages", [])
        if not messages:
            logger.warning("No messages in state, cannot determine query")
            print("No messages in state, cannot determine query")
            state["context"] = {"documents": [], "query": ""}
            return state
        
        last_user_message = None
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user_message = message.get("content", "")
                break
        
        if not last_user_message:
            logger.warning("No user messages found in state")
            print("No user messages found in state")
            state["context"] = {"documents": [], "query": ""}
            return state
        
        query = last_user_message
    
    # At this point, query is guaranteed to be a string
    query_str: str = query if isinstance(query, str) else ""
    query_summary = f"{query_str[:50]}{'...' if len(query_str) > 50 else ''}"
    logger.info(f"Retrieving knowledge for query: {query_summary}")
    print(f"Retrieving knowledge for query: {query_summary}")
    
    # Retrieve relevant documents
    if use_hybrid:
        documents = kb.retrieve_hybrid(query_str, filter=filter)
    else:
        documents = kb.retrieve(query_str, filter=filter)
    
    logger.info(f"Retrieved {len(documents)} relevant documents")
    print(f"Retrieved {len(documents)} relevant documents")
    
    if documents:
        # Print the top document sources for debugging
        print("Top relevant documents:")
        for i, doc in enumerate(documents[:3]):
            source = doc.metadata.get("source", "Unknown")
            score = doc.relevance_score
            print(f"  {i + 1}. {source} (score: {score:.4f})")
            logger.debug(f"Document {i + 1}: {source} (score: {score:.4f})")
    
    # Convert RetrievalResult objects to dicts for state
    document_dicts = [doc.to_dict() for doc in documents]
    
    # Update state with retrieved documents
    state["context"] = {"documents": document_dicts, "query": query}
    
    return state