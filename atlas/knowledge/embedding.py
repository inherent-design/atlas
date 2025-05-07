"""
Embedding strategies for the Atlas knowledge system.

This module provides interfaces and implementations for different embedding strategies
to optimize vector representations of document chunks for retrieval.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple

import numpy as np
from anthropic import Anthropic

from atlas.core import env

logger = logging.getLogger(__name__)


class EmbeddingStrategy(ABC):
    """Base class for embedding strategies."""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of document texts.
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            List of embedding vectors for each text.
        """
        pass
    
    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding for a query string.
        
        Args:
            query: Query text to embed.
            
        Returns:
            Embedding vector for the query.
        """
        pass


class AnthropicEmbeddingStrategy(EmbeddingStrategy):
    """Embedding strategy that uses Anthropic's embedding models."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
        dimensions: int = 1536,
    ):
        """Initialize the Anthropic embedding strategy.
        
        Args:
            api_key: Optional API key for Anthropic.
            model: The model ID to use for embeddings.
            dimensions: Embedding vector dimensions.
        """
        self.client = Anthropic(
            api_key=api_key or env.get_string("ANTHROPIC_API_KEY")
        )
        self.model = model
        self.dimensions = dimensions
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of document texts using Anthropic.
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            List of embedding vectors for each text.
        """
        if not texts:
            return []
        
        embeddings = []
        # Process in batches to avoid rate limits
        batch_size = 20
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = []
            
            for text in batch:
                try:
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=text,
                        dimensions=self.dimensions,
                    )
                    embedding = response.embedding
                    batch_embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"Error generating embedding: {e}")
                    # Return a zero vector as fallback
                    batch_embeddings.append([0.0] * self.dimensions)
            
            embeddings.extend(batch_embeddings)
            
            if len(texts) > batch_size:
                logger.info(f"Embedded batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding for a query string using Anthropic.
        
        Args:
            query: Query text to embed.
            
        Returns:
            Embedding vector for the query.
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=query,
                dimensions=self.dimensions,
            )
            return response.embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            # Return a zero vector as fallback
            return [0.0] * self.dimensions


class ChromaDefaultEmbeddingStrategy(EmbeddingStrategy):
    """Embedding strategy that uses ChromaDB's default embeddings."""
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return None to let ChromaDB use its default embedding function.
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            None, letting ChromaDB use its default embedding.
        """
        # Return None to let ChromaDB use its default embedding
        return None
    
    def embed_query(self, query: str) -> List[float]:
        """Return None to let ChromaDB use its default embedding function.
        
        Args:
            query: Query text to embed.
            
        Returns:
            None, letting ChromaDB use its default embedding.
        """
        # Return None to let ChromaDB use its default embedding
        return None


class HybridEmbeddingStrategy(EmbeddingStrategy):
    """Embedding strategy that combines multiple embedding approaches."""
    
    def __init__(
        self, 
        strategies: List[Tuple[EmbeddingStrategy, float]] = None,
    ):
        """Initialize the hybrid embedding strategy.
        
        Args:
            strategies: List of (strategy, weight) tuples.
        """
        if strategies is None:
            # Default to ChromaDB's embeddings
            self.strategies = [(ChromaDefaultEmbeddingStrategy(), 1.0)]
        else:
            # Normalize weights
            total_weight = sum(weight for _, weight in strategies)
            self.strategies = [
                (strategy, weight/total_weight) for strategy, weight in strategies
            ]
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using a weighted combination of strategies.
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            List of embedding vectors for each text.
        """
        # For now, just use the first strategy since mixing embeddings is complex
        # In a more advanced implementation, we could concatenate embeddings or 
        # create ensemble approaches
        return self.strategies[0][0].embed_documents(texts)
    
    def embed_query(self, query: str) -> List[float]:
        """Generate a query embedding using a weighted combination of strategies.
        
        Args:
            query: Query text to embed.
            
        Returns:
            Embedding vector for the query.
        """
        # For now, just use the first strategy
        return self.strategies[0][0].embed_query(query)


class EmbeddingStrategyFactory:
    """Factory for creating embedding strategies."""
    
    @staticmethod
    def create_strategy(
        strategy_type: str = "default",
        **kwargs
    ) -> EmbeddingStrategy:
        """Create an embedding strategy based on the specified type.
        
        Args:
            strategy_type: Type of embedding strategy to create.
            **kwargs: Additional parameters for the strategy.
            
        Returns:
            An EmbeddingStrategy instance.
        """
        if strategy_type == "anthropic":
            return AnthropicEmbeddingStrategy(**kwargs)
        elif strategy_type == "hybrid":
            # Extract strategies from kwargs if provided
            strategies = kwargs.get("strategies", None)
            return HybridEmbeddingStrategy(strategies)
        else:
            # Default to ChromaDB's embeddings
            return ChromaDefaultEmbeddingStrategy()