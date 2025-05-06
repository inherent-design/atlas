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
        collection_name: str = "atlas_knowledge_base",
        db_path: Optional[str] = None,
        provider_name: str = "anthropic",
        model_name: Optional[str] = None,
        config: Optional[AtlasConfig] = None,
    ):
        """Initialize the Atlas query interface.
        
        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            db_path: Path to the knowledge base. If None, use default in home directory.
            provider_name: Name of the model provider to use.
            model_name: Optional name of the specific model to use.
            config: Optional configuration object. If not provided, default values are used.
        """
        # Create configuration with provided parameters
        self.config = config or AtlasConfig(
            collection_name=collection_name,
            db_path=db_path,
        )
        
        # Initialize the knowledge base
        self.knowledge_base = KnowledgeBase(
            collection_name=self.config.collection_name,
            db_path=self.config.db_path,
        )
        
        # Initialize the agent for query processing
        self.agent = AtlasAgent(
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
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
    
    def query_with_context(self, query_text: str) -> Dict[str, Any]:
        """Query Atlas and return both the response and context used.
        
        This method is useful for debugging or for applications that need
        to understand what knowledge was used to generate the response.
        
        Args:
            query_text: The text query to process.
            
        Returns:
            Dictionary containing the response and context used.
        """
        # Retrieve relevant documents from the knowledge base
        documents = self.knowledge_base.retrieve(query_text)
        
        # Process the query using the agent
        response = self.agent.process_message(query_text)
        
        # Format the response with context
        return {
            "response": response,
            "context": {
                "documents": [
                    {
                        "content": doc["content"],
                        "source": doc["metadata"].get("source", "Unknown"),
                        "relevance_score": doc["relevance_score"],
                    }
                    for doc in documents[:3]  # Include top 3 documents
                ],
                "query": query_text,
            },
        }
    
    def query_streaming(self, query_text: str, callback: Callable[[str, str], None]) -> str:
        """Query Atlas with streaming response.
        
        This method is useful for applications that want to display partial responses
        as they are generated, creating a more interactive experience.
        
        Args:
            query_text: The text query to process.
            callback: Function called for each chunk of the response, with arguments
                      (delta_text, full_text).
            
        Returns:
            The complete response text.
        """
        try:
            # Check if the agent has the streaming method
            if hasattr(self.agent, "process_message_streaming"):
                # Use the agent's streaming implementation
                return self.agent.process_message_streaming(query_text, callback)
            else:
                # Fallback to non-streaming if not available
                logger.warning("Streaming not supported by agent - falling back to regular query")
                response = self.agent.process_message(query_text)
                # Call the callback once with the full response
                callback(response, response)
                return response
        except Exception as e:
            logger.error(f"Error in streaming query: {e}", exc_info=True)
            # Fall back to regular query
            response = self.agent.process_message(query_text)
            return response
    
    def retrieve_only(self, query_text: str) -> List[Dict[str, Any]]:
        """Retrieve documents from the knowledge base without generating a response.
        
        This method is useful for applications that want to access Atlas's knowledge
        retrieval capabilities without generating a model response.
        
        Args:
            query_text: The text query to search for.
            
        Returns:
            List of relevant documents with their metadata.
        """
        documents = self.knowledge_base.retrieve(query_text)
        
        # Format and return documents
        return [
            {
                "content": doc["content"],
                "metadata": doc["metadata"],
                "relevance_score": doc["relevance_score"],
            }
            for doc in documents
        ]
    

# Convenience factory function
def create_query_client(
    system_prompt_file: Optional[str] = None,
    collection_name: str = "atlas_knowledge_base",
    db_path: Optional[str] = None,
    provider_name: str = "anthropic",
    model_name: Optional[str] = None,
) -> AtlasQuery:
    """Create a query-only Atlas client.
    
    This function provides a simple way to create an Atlas query client
    for use in other applications.
    
    Args:
        system_prompt_file: Optional path to a file containing the system prompt.
        collection_name: Name of the Chroma collection to use.
        db_path: Path to the knowledge base. If None, use default in home directory.
        provider_name: Name of the model provider to use.
        model_name: Optional name of the specific model to use.
        
    Returns:
        An initialized AtlasQuery instance.
    """
    try:
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