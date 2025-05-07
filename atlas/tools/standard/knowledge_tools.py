"""
Standard tools for knowledge base operations.

This module provides tools for interacting with the Atlas knowledge base,
including search, retrieval, and metadata filtering.
"""

from typing import List, Dict, Any, Optional
import logging

from atlas.core.telemetry import traced
from atlas.knowledge.retrieval import KnowledgeBase, RetrievalResult, RetrievalFilter
from atlas.knowledge.settings import RetrievalSettings
from atlas.tools.base import Tool, ToolSchema


logger = logging.getLogger(__name__)


class KnowledgeSearchTool(Tool):
    """Tool for searching the knowledge base."""
    
    def __init__(self, knowledge_base: KnowledgeBase, name: str = "knowledge_search"):
        """Initialize the knowledge search tool.
        
        Args:
            knowledge_base: The knowledge base to search.
            name: The name of the tool.
        """
        super().__init__(name=name)
        self.knowledge_base = knowledge_base
    
    @property
    def schema(self) -> ToolSchema:
        """Get the schema for this tool.
        
        Returns:
            A ToolSchema describing the tool's inputs and outputs.
        """
        return ToolSchema(
            name=self.name,
            description="Search the knowledge base for relevant documents using a query",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum relevance score (0.0-1.0)",
                        "default": 0.0
                    },
                    "use_hybrid": {
                        "type": "boolean",
                        "description": "Whether to use hybrid search (semantic + keyword)",
                        "default": False
                    },
                    "semantic_weight": {
                        "type": "number",
                        "description": "Weight for semantic search results (0.0-1.0)",
                        "default": 0.7
                    },
                    "keyword_weight": {
                        "type": "number",
                        "description": "Weight for keyword search results (0.0-1.0)",
                        "default": 0.3
                    }
                },
                "required": ["query"]
            }
        )
    
    @traced(name="execute")
    def execute(
        self, 
        query: str, 
        max_results: int = 5, 
        min_score: float = 0.0,
        use_hybrid: bool = False,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant documents.
        
        Args:
            query: The search query.
            max_results: Maximum number of results to return.
            min_score: Minimum relevance score threshold.
            use_hybrid: Whether to use hybrid search.
            semantic_weight: Weight for semantic search results.
            keyword_weight: Weight for keyword search results.
            
        Returns:
            A list of documents matching the query.
        """
        logger.info(f"Searching knowledge base for: {query}")
        
        # Create retrieval settings
        settings = RetrievalSettings(
            use_hybrid_search=use_hybrid,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            num_results=max_results,
            min_relevance_score=min_score
        )
        
        # Perform the search
        results = self.knowledge_base.retrieve(query=query, settings=settings)
        
        # Format results for return
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.content,
                "metadata": result.metadata,
                "relevance_score": result.relevance_score
            })
        
        logger.info(f"Found {len(formatted_results)} results for query")
        return formatted_results


class MetadataFilterTool(Tool):
    """Tool for filtering knowledge base by metadata."""
    
    def __init__(self, knowledge_base: KnowledgeBase, name: str = "metadata_filter"):
        """Initialize the metadata filter tool.
        
        Args:
            knowledge_base: The knowledge base to filter.
            name: The name of the tool.
        """
        super().__init__(name=name)
        self.knowledge_base = knowledge_base
    
    @property
    def schema(self) -> ToolSchema:
        """Get the schema for this tool.
        
        Returns:
            A ToolSchema describing the tool's inputs and outputs.
        """
        return ToolSchema(
            name=self.name,
            description="Filter knowledge base documents by metadata attributes",
            parameters={
                "type": "object",
                "properties": {
                    "metadata_filters": {
                        "type": "object",
                        "description": "Metadata key-value pairs to filter by"
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional search query to combine with metadata filter"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["metadata_filters"]
            }
        )
    
    @traced(name="execute")
    def execute(
        self, 
        metadata_filters: Dict[str, Any], 
        query: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Filter knowledge base documents by metadata.
        
        Args:
            metadata_filters: Metadata key-value pairs to filter by.
            query: Optional search query to combine with metadata filter.
            max_results: Maximum number of results to return.
            
        Returns:
            A list of documents matching the filter criteria.
        """
        logger.info(f"Filtering knowledge base by metadata: {metadata_filters}")
        
        # Create filter from metadata
        filter_obj = RetrievalFilter.from_metadata(**metadata_filters)
        
        # Perform retrieval with filter
        if query:
            logger.info(f"Using search query: {query}")
            # Search with query and filter
            settings = RetrievalSettings(num_results=max_results)
            results = self.knowledge_base.retrieve(
                query=query, 
                filter=filter_obj,
                settings=settings
            )
        else:
            # Get all documents matching filter
            results = self.knowledge_base.get_documents(
                filter=filter_obj,
                limit=max_results
            )
        
        # Format results for return
        formatted_results = []
        for result in results:
            # Handle both RetrievalResult and document dictionary formats
            if isinstance(result, RetrievalResult):
                formatted_results.append({
                    "content": result.content,
                    "metadata": result.metadata,
                    "relevance_score": result.relevance_score
                })
            else:
                formatted_results.append({
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "relevance_score": result.get("relevance_score", 1.0)
                })
        
        logger.info(f"Found {len(formatted_results)} documents matching filter")
        return formatted_results


def create_knowledge_toolkit(knowledge_base: KnowledgeBase) -> List[Tool]:
    """Create a set of knowledge tools for a knowledge base.
    
    Args:
        knowledge_base: The knowledge base to use with the tools.
        
    Returns:
        A list of knowledge-related tools.
    """
    return [
        KnowledgeSearchTool(knowledge_base),
        MetadataFilterTool(knowledge_base)
    ]