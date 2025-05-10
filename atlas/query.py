"""
Query-only interface for Atlas.

This module provides a lightweight query-only interface for Atlas that can be
used by other agentic clients to extend their functionalities.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable

from atlas.core.config import AtlasConfig
from atlas.core.errors import APIError, safe_execute
from atlas.agents.base import AtlasAgent
from atlas.knowledge.retrieval import KnowledgeBase

logger = logging.getLogger(__name__)


class AtlasQuery:
    """Lightweight query-only interface for Atlas."""

    def __init__(
        self,
        system_prompt_file: Optional[str] = None,
        collection_name: Optional[str] = None,
        db_path: Optional[str] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        config: Optional[AtlasConfig] = None,
    ):
        """Initialize the Atlas query interface.

        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use. If None, uses environment variable.
            db_path: Path to the knowledge base. If None, uses environment variable or default.
            provider_name: Name of the model provider to use. If None, uses environment variable.
            model_name: Optional name of the specific model to use. If None, uses environment variable.
            config: Optional configuration object. If not provided, a new one is created.
        """
        # Create configuration with provided parameters, which will pull from environment variables if needed
        self.config = config or AtlasConfig(
            collection_name=collection_name,
            db_path=db_path,
            model_name=model_name,
        )

        # Use the provider_name if specified, otherwise use the default
        if provider_name is None:
            from atlas.core import env

            provider_name = env.get_string("ATLAS_DEFAULT_PROVIDER", "anthropic")

        # Initialize the knowledge base - this will use environment variables if needed
        self.knowledge_base = KnowledgeBase(
            collection_name=self.config.collection_name,
            db_path=self.config.db_path,
        )

        # Initialize the agent for query processing - this will create the actual model provider
        self.agent = AtlasAgent(
            system_prompt_file=system_prompt_file,
            collection_name=self.config.collection_name,
            config=self.config,
            provider_name=provider_name,
            model_name=model_name,
        )

        # Set up query metadata
        self.query_client_id = f"atlas-query-{provider_name}"

        logger.debug(f"Initialized Atlas query interface with {provider_name} provider")

    def query(self, query_text: str) -> str:
        """Query Atlas with a simple text input.

        This is the simplest interface for querying Atlas - it takes a text query
        and returns a text response.

        Args:
            query_text: The text query to process.

        Returns:
            The response text.
        """
        return self.agent.process_message(query_text)

    def query_with_context(
        self,
        query_text: str,
        filter: Optional[Union[Dict[str, Any], 'RetrievalFilter']] = None,
        max_results: int = 10,
        min_relevance_score: float = 0.0,
        use_hybrid_search: bool = False,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> Dict[str, Any]:
        """Query Atlas and return both the response and context used.

        This method is useful for debugging or for applications that need
        to understand what knowledge was used to generate the response.

        Args:
            query_text: The text query to process.
            filter: Optional metadata filter to apply. Can be a dictionary or RetrievalFilter object.
            max_results: Maximum number of results to retrieve (default: 10).
            min_relevance_score: Minimum relevance score threshold for results (default: 0.0).
            use_hybrid_search: Whether to use hybrid search combining semantic and keyword search.
            semantic_weight: Weight for semantic search results (0-1) when using hybrid search.
            keyword_weight: Weight for keyword search results (0-1) when using hybrid search.

        Returns:
            Dictionary containing the response and context used.
        """
        from atlas.knowledge.retrieval import RetrievalFilter, RetrievalSettings

        # Prepare retrieval filter if provided
        retrieval_filter = None
        if filter is not None:
            if isinstance(filter, dict):
                retrieval_filter = RetrievalFilter(where=filter)
            elif isinstance(filter, RetrievalFilter):
                retrieval_filter = filter
            else:
                raise TypeError("filter must be a dictionary or RetrievalFilter object")

        # Prepare retrieval settings
        settings = RetrievalSettings(
            use_hybrid_search=use_hybrid_search,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            num_results=max_results,
            min_relevance_score=min_relevance_score,
            rerank_results=True  # Always apply reranking for better results
        )

        # Retrieve relevant documents from the knowledge base
        documents = self.knowledge_base.retrieve(
            query_text,
            filter=retrieval_filter,
            settings=settings
        )

        # Process the query using the agent with the same filter and settings
        response = self.agent.process_message(
            query_text,
            filter=retrieval_filter,
            settings=settings
        )

        # Format the response with context
        formatted_docs = []
        for doc in documents:  # Include all filtered documents
            if hasattr(doc, 'to_dict'):
                # It's a RetrievalResult object
                doc_dict = doc.to_dict()
                formatted_docs.append({
                    "content": doc_dict["content"],
                    "source": doc_dict["metadata"].get("source", "Unknown"),
                    "relevance_score": doc_dict["relevance_score"],
                    "metadata": doc_dict["metadata"],  # Include all metadata for more context
                })
            else:
                # It's a dictionary
                formatted_docs.append({
                    "content": doc["content"],
                    "source": doc["metadata"].get("source", "Unknown"),
                    "relevance_score": doc["relevance_score"],
                    "metadata": doc["metadata"],  # Include all metadata for more context
                })

        # Build the response with detailed filter and settings information
        filter_info = None
        if retrieval_filter:
            filter_info = retrieval_filter.where

        # Extract settings for context
        settings_dict = settings.to_dict() if settings else {}

        return {
            "response": response,
            "context": {
                "documents": formatted_docs,
                "query": query_text,
                "filter": filter_info,
                "settings": settings_dict,
                "total_documents_found": len(documents),
            },
        }

    def query_streaming(
        self,
        query_text: str,
        callback: Callable[[str, str], None],
        filter: Optional[Union[Dict[str, Any], 'RetrievalFilter']] = None,
        max_results: int = 10,
        min_relevance_score: float = 0.0,
        use_hybrid_search: bool = False,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> str:
        """Query Atlas with streaming response.

        This method is useful for applications that want to display partial responses
        as they are generated, creating a more interactive experience.

        Args:
            query_text: The text query to process.
            callback: Function called for each chunk of the response, with arguments
                      (delta_text, full_text).
            filter: Optional metadata filter to apply. Can be a dictionary or RetrievalFilter object.
            max_results: Maximum number of results to retrieve (default: 10).
            min_relevance_score: Minimum relevance score threshold for results (default: 0.0).
            use_hybrid_search: Whether to use hybrid search combining semantic and keyword search.
            semantic_weight: Weight for semantic search results (0-1) when using hybrid search.
            keyword_weight: Weight for keyword search results (0-1) when using hybrid search.

        Returns:
            The complete response text.
        """
        from atlas.knowledge.retrieval import RetrievalFilter, RetrievalSettings

        try:
            # Prepare retrieval filter if provided
            retrieval_filter = None
            if filter is not None:
                if isinstance(filter, dict):
                    retrieval_filter = RetrievalFilter(where=filter)
                elif isinstance(filter, RetrievalFilter):
                    retrieval_filter = filter
                else:
                    logger.warning(f"Unsupported filter type: {type(filter)}. Converting to string representation.")
                    try:
                        # Try to convert to a dictionary if possible
                        filter_dict = {"custom_filter": str(filter)}
                        retrieval_filter = RetrievalFilter(where=filter_dict)
                    except Exception as filter_err:
                        logger.error(f"Error converting filter to dictionary: {filter_err}")
                        raise TypeError("filter must be a dictionary or RetrievalFilter object")

            # Prepare retrieval settings
            settings = RetrievalSettings(
                use_hybrid_search=use_hybrid_search,
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
                num_results=max_results,
                min_relevance_score=min_relevance_score,
                rerank_results=True  # Always apply reranking for better results
            )

            # Log the filter and settings for debugging
            logger.debug(f"Streaming query with filter: {retrieval_filter.where if retrieval_filter else None}")
            logger.debug(f"Streaming query with settings: {settings.to_dict()}")

            # Check if the agent has the streaming method
            if hasattr(self.agent, "process_message_streaming"):
                # Use the agent's streaming implementation
                return self.agent.process_message_streaming(
                    query_text,
                    callback,
                    filter=retrieval_filter,
                    settings=settings
                )
            else:
                # Fallback to non-streaming if not available
                logger.warning(
                    "Streaming not supported by agent - falling back to regular query"
                )
                response = self.agent.process_message(
                    query_text,
                    filter=retrieval_filter,
                    settings=settings
                )
                # Call the callback once with the full response
                callback(response, response)
                return response
        except Exception as e:
            logger.error(f"Error in streaming query: {e}", exc_info=True)
            # Fall back to regular query without filtering
            response = self.agent.process_message(query_text)
            # Call the callback with the error response
            callback(response, response)
            return response

    def retrieve_only(
        self,
        query_text: str,
        filter: Optional[Union[Dict[str, Any], 'RetrievalFilter']] = None,
        max_results: int = 10,
        min_relevance_score: float = 0.0,
        use_hybrid_search: bool = False,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """Retrieve documents from the knowledge base without generating a response.

        This method is useful for applications that want to access Atlas's knowledge
        retrieval capabilities without generating a model response.

        Args:
            query_text: The text query to search for.
            filter: Optional metadata filter to apply. Can be a dictionary or RetrievalFilter object.
            max_results: Maximum number of results to retrieve (default: 10).
            min_relevance_score: Minimum relevance score threshold for results (default: 0.0).
            use_hybrid_search: Whether to use hybrid search combining semantic and keyword search.
            semantic_weight: Weight for semantic search results (0-1) when using hybrid search.
            keyword_weight: Weight for keyword search results (0-1) when using hybrid search.

        Returns:
            List of relevant documents with their metadata.
        """
        from atlas.knowledge.retrieval import RetrievalFilter, RetrievalSettings

        # Prepare retrieval filter if provided
        retrieval_filter = None
        if filter is not None:
            if isinstance(filter, dict):
                retrieval_filter = RetrievalFilter(where=filter)
            elif isinstance(filter, RetrievalFilter):
                retrieval_filter = filter
            else:
                logger.warning(f"Unsupported filter type: {type(filter)}. Using string representation.")
                try:
                    # Try to convert to a dictionary if possible
                    filter_dict = {"custom_filter": str(filter)}
                    retrieval_filter = RetrievalFilter(where=filter_dict)
                except Exception as filter_err:
                    logger.error(f"Error converting filter to dictionary: {filter_err}")
                    raise TypeError("filter must be a dictionary or RetrievalFilter object")

        # Prepare retrieval settings
        settings = RetrievalSettings(
            use_hybrid_search=use_hybrid_search,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            num_results=max_results,
            min_relevance_score=min_relevance_score,
            rerank_results=not use_hybrid_search  # Apply reranking for regular search
        )

        # Log the filter and settings for debugging
        logger.debug(f"Retrieving documents with filter: {retrieval_filter.where if retrieval_filter else None}")
        logger.debug(f"Retrieving documents with settings: {settings.to_dict()}")

        try:
            # Retrieve relevant documents
            documents = self.knowledge_base.retrieve(
                query_text,
                filter=retrieval_filter,
                settings=settings
            )

            # Format and return documents
            result = []
            for doc in documents:
                # Handle both dictionary-like and RetrievalResult objects
                if hasattr(doc, 'to_dict'):
                    # It's a RetrievalResult object
                    result.append(doc.to_dict())
                else:
                    # It's already a dictionary
                    result.append({
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                        "relevance_score": doc["relevance_score"],
                        "distance": doc.get("distance", 0.0),
                    })

            logger.info(f"Retrieved {len(result)} documents for query: {query_text[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}", exc_info=True)
            # Return empty list on error
            return []


# Convenience factory function
def create_query_client(
    system_prompt_file: Optional[str] = None,
    collection_name: Optional[str] = None,
    db_path: Optional[str] = None,
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
) -> AtlasQuery:
    """Create a query-only Atlas client.

    This function provides a simple way to create an Atlas query client
    for use in other applications. It respects environment variables for
    configuration.

    Args:
        system_prompt_file: Optional path to a file containing the system prompt.
        collection_name: Name of the Chroma collection to use. If None, uses ATLAS_COLLECTION_NAME env var.
        db_path: Path to the knowledge base. If None, uses ATLAS_DB_PATH env var or default home directory.
        provider_name: Name of the model provider to use. If None, uses ATLAS_DEFAULT_PROVIDER env var.
        model_name: Name of the model to use. If None, uses ATLAS_DEFAULT_MODEL env var.

    Returns:
        An initialized AtlasQuery instance.
    """
    from atlas.core import env

    try:
        # Get values from environment if not specified in parameters
        if provider_name is None:
            provider_name = env.get_string("ATLAS_DEFAULT_PROVIDER", "anthropic")

        if collection_name is None:
            collection_name = env.get_string(
                "ATLAS_COLLECTION_NAME", "atlas_knowledge_base"
            )
            logger.info(f"Using collection name from environment: {collection_name}")

        return AtlasQuery(
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
            db_path=db_path,
            provider_name=provider_name,
            model_name=model_name,
        )
    except Exception as e:
        logger.error(f"Error creating Atlas query client: {e}", exc_info=True)
        raise
