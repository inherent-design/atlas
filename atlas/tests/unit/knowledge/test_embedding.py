"""
Unit tests for the embedding strategies module.

These tests verify the functionality of various embedding strategies for
converting document content into vector representations.
"""

import unittest
from unittest import mock
import numpy as np
from typing import List

from atlas.knowledge.embedding import (
    EmbeddingStrategy,
    AnthropicEmbeddingStrategy,
    ChromaDefaultEmbeddingStrategy,
    HybridEmbeddingStrategy,
    EmbeddingStrategyFactory,
)
from atlas.tests.helpers.decorators import unit_test


class TestAnthropicEmbeddingStrategy(unittest.TestCase):
    """Test the AnthropicEmbeddingStrategy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the Anthropic client
        self.mock_client_patcher = mock.patch("atlas.knowledge.embedding.Anthropic")
        self.mock_client_class = self.mock_client_patcher.start()
        self.mock_client = mock.MagicMock()
        self.mock_client_class.return_value = self.mock_client
        
        # Mock the embeddings API
        self.mock_embeddings = mock.MagicMock()
        self.mock_client.embeddings = self.mock_embeddings
        
        # Set up mock response
        self.mock_response = mock.MagicMock()
        self.mock_response.embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        self.mock_embeddings.create.return_value = self.mock_response
        
        # Create strategy with mock client
        self.strategy = AnthropicEmbeddingStrategy(
            api_key="test_key",
            model="claude-3-haiku-20240307",
            dimensions=1536
        )
    
    def tearDown(self):
        """Clean up resources."""
        self.mock_client_patcher.stop()
    
    @unit_test
    def test_initialization(self):
        """Test initializing the embedding strategy."""
        # Verify Anthropic client was created with the API key
        self.mock_client_class.assert_called_once_with(api_key="test_key")
        
        # Check strategy properties
        self.assertEqual(self.strategy.model, "claude-3-haiku-20240307")
        self.assertEqual(self.strategy.dimensions, 1536)
    
    @unit_test
    def test_embed_query(self):
        """Test generating embeddings for a query."""
        query = "This is a test query"
        embedding = self.strategy.embed_query(query)
        
        # Verify the API was called correctly
        self.mock_embeddings.create.assert_called_once_with(
            model="claude-3-haiku-20240307",
            input=query,
            dimensions=1536
        )
        
        # Check the returned embedding
        self.assertEqual(len(embedding), 1536)
        self.assertEqual(embedding, [0.1, 0.2, 0.3] * 512)
    
    @unit_test
    def test_embed_documents(self):
        """Test generating embeddings for multiple documents."""
        texts = ["Document 1", "Document 2", "Document 3"]
        embeddings = self.strategy.embed_documents(texts)
        
        # Verify API was called for each document
        self.assertEqual(self.mock_embeddings.create.call_count, 3)
        
        # Check the returned embeddings
        self.assertEqual(len(embeddings), 3)
        for embedding in embeddings:
            self.assertEqual(len(embedding), 1536)
    
    @unit_test
    def test_embed_empty_list(self):
        """Test handling empty document list."""
        embeddings = self.strategy.embed_documents([])
        
        # Should return empty list without API calls
        self.assertEqual(embeddings, [])
        self.mock_embeddings.create.assert_not_called()
    
    @unit_test
    def test_embed_error_handling(self):
        """Test error handling during embedding."""
        # Make the API call fail
        self.mock_embeddings.create.side_effect = Exception("API error")
        
        # For document embedding
        with mock.patch("atlas.knowledge.embedding.logger") as mock_logger:
            embeddings = self.strategy.embed_documents(["Problematic document"])
            
            # Should return a zero vector and log error
            self.assertEqual(len(embeddings), 1)
            self.assertEqual(embeddings[0], [0.0] * 1536)
            mock_logger.error.assert_called_once()
        
        # Reset the mock
        mock_logger = mock.MagicMock()
        
        # For query embedding
        with mock.patch("atlas.knowledge.embedding.logger") as mock_logger:
            embedding = self.strategy.embed_query("Problematic query")
            
            # Should return a zero vector and log error
            self.assertEqual(embedding, [0.0] * 1536)
            mock_logger.error.assert_called_once()


class TestChromaDefaultEmbeddingStrategy(unittest.TestCase):
    """Test the ChromaDefaultEmbeddingStrategy class."""
    
    @unit_test
    def test_embed_documents(self):
        """Test that None is returned for document embeddings."""
        strategy = ChromaDefaultEmbeddingStrategy()
        embeddings = strategy.embed_documents(["Document 1", "Document 2"])
        
        # Should return None to let ChromaDB use its default
        self.assertIsNone(embeddings)
    
    @unit_test
    def test_embed_query(self):
        """Test that None is returned for query embedding."""
        strategy = ChromaDefaultEmbeddingStrategy()
        embedding = strategy.embed_query("Test query")
        
        # Should return None to let ChromaDB use its default
        self.assertIsNone(embedding)


class TestHybridEmbeddingStrategy(unittest.TestCase):
    """Test the HybridEmbeddingStrategy class."""
    
    @unit_test
    def test_initialization_with_default(self):
        """Test initializing with default strategy."""
        strategy = HybridEmbeddingStrategy()
        
        # Should default to ChromaDefaultEmbeddingStrategy
        self.assertEqual(len(strategy.strategies), 1)
        self.assertIsInstance(strategy.strategies[0][0], ChromaDefaultEmbeddingStrategy)
        self.assertEqual(strategy.strategies[0][1], 1.0)  # Weight should be 1.0
    
    @unit_test
    def test_initialization_with_custom_strategies(self):
        """Test initializing with custom strategies and weights."""
        strategy1 = ChromaDefaultEmbeddingStrategy()
        strategy2 = mock.MagicMock(spec=EmbeddingStrategy)
        
        hybrid_strategy = HybridEmbeddingStrategy([
            (strategy1, 0.7),
            (strategy2, 0.3)
        ])
        
        # Check strategies and normalized weights
        self.assertEqual(len(hybrid_strategy.strategies), 2)
        self.assertIs(hybrid_strategy.strategies[0][0], strategy1)
        self.assertIs(hybrid_strategy.strategies[1][0], strategy2)
        
        # Weights should be normalized
        self.assertAlmostEqual(hybrid_strategy.strategies[0][1], 0.7)
        self.assertAlmostEqual(hybrid_strategy.strategies[1][1], 0.3)
    
    @unit_test
    def test_embed_documents(self):
        """Test document embedding with hybrid strategy."""
        # Create mock strategies
        strategy1 = mock.MagicMock(spec=EmbeddingStrategy)
        strategy1.embed_documents.return_value = [[1.0, 2.0, 3.0]]
        
        strategy2 = mock.MagicMock(spec=EmbeddingStrategy)
        strategy2.embed_documents.return_value = [[4.0, 5.0, 6.0]]
        
        # Create hybrid strategy
        hybrid_strategy = HybridEmbeddingStrategy([
            (strategy1, 0.6),
            (strategy2, 0.4)
        ])
        
        # Test embedding
        documents = ["Test document"]
        embeddings = hybrid_strategy.embed_documents(documents)
        
        # Currently, HybridEmbeddingStrategy just uses the first strategy
        self.assertEqual(embeddings, [[1.0, 2.0, 3.0]])
        strategy1.embed_documents.assert_called_once_with(documents)
        strategy2.embed_documents.assert_not_called()
    
    @unit_test
    def test_embed_query(self):
        """Test query embedding with hybrid strategy."""
        # Create mock strategies
        strategy1 = mock.MagicMock(spec=EmbeddingStrategy)
        strategy1.embed_query.return_value = [1.0, 2.0, 3.0]
        
        strategy2 = mock.MagicMock(spec=EmbeddingStrategy)
        strategy2.embed_query.return_value = [4.0, 5.0, 6.0]
        
        # Create hybrid strategy
        hybrid_strategy = HybridEmbeddingStrategy([
            (strategy1, 0.6),
            (strategy2, 0.4)
        ])
        
        # Test embedding
        query = "Test query"
        embedding = hybrid_strategy.embed_query(query)
        
        # Currently, HybridEmbeddingStrategy just uses the first strategy
        self.assertEqual(embedding, [1.0, 2.0, 3.0])
        strategy1.embed_query.assert_called_once_with(query)
        strategy2.embed_query.assert_not_called()


class TestEmbeddingStrategyFactory(unittest.TestCase):
    """Test the EmbeddingStrategyFactory class."""
    
    @unit_test
    def test_create_anthropic_strategy(self):
        """Test creating an Anthropic embedding strategy."""
        # Mock the Anthropic class to avoid actual client creation
        with mock.patch("atlas.knowledge.embedding.Anthropic"):
            strategy = EmbeddingStrategyFactory.create_strategy("anthropic")
            
            # Check type and default parameters
            self.assertIsInstance(strategy, AnthropicEmbeddingStrategy)
            self.assertEqual(strategy.model, "claude-3-haiku-20240307")
            self.assertEqual(strategy.dimensions, 1536)
    
    @unit_test
    def test_create_anthropic_strategy_with_params(self):
        """Test creating an Anthropic strategy with custom parameters."""
        # Mock the Anthropic class to avoid actual client creation
        with mock.patch("atlas.knowledge.embedding.Anthropic"):
            strategy = EmbeddingStrategyFactory.create_strategy(
                "anthropic",
                model="custom-model",
                dimensions=768
            )
            
            # Check custom parameters were applied
            self.assertIsInstance(strategy, AnthropicEmbeddingStrategy)
            self.assertEqual(strategy.model, "custom-model")
            self.assertEqual(strategy.dimensions, 768)
    
    @unit_test
    def test_create_hybrid_strategy(self):
        """Test creating a hybrid embedding strategy."""
        strategy = EmbeddingStrategyFactory.create_strategy("hybrid")
        
        # Should create hybrid strategy with default ChromaDB strategy
        self.assertIsInstance(strategy, HybridEmbeddingStrategy)
        self.assertEqual(len(strategy.strategies), 1)
        self.assertIsInstance(strategy.strategies[0][0], ChromaDefaultEmbeddingStrategy)
    
    @unit_test
    def test_create_hybrid_strategy_with_strategies(self):
        """Test creating a hybrid strategy with custom strategies."""
        # Create some mock strategies for the test
        mock_strategy1 = mock.MagicMock(spec=EmbeddingStrategy)
        mock_strategy2 = mock.MagicMock(spec=EmbeddingStrategy)
        
        # Create the strategies list
        strategies = [
            (mock_strategy1, 0.7),
            (mock_strategy2, 0.3)
        ]
        
        # Create hybrid strategy through factory
        strategy = EmbeddingStrategyFactory.create_strategy(
            "hybrid",
            strategies=strategies
        )
        
        # Verify the strategy has the correct components
        self.assertIsInstance(strategy, HybridEmbeddingStrategy)
        self.assertEqual(len(strategy.strategies), 2)
        self.assertIs(strategy.strategies[0][0], mock_strategy1)
        self.assertIs(strategy.strategies[1][0], mock_strategy2)
    
    @unit_test
    def test_create_default_strategy(self):
        """Test creating the default embedding strategy."""
        strategy = EmbeddingStrategyFactory.create_strategy()
        
        # Should default to ChromaDB strategy
        self.assertIsInstance(strategy, ChromaDefaultEmbeddingStrategy)
        
        # Also test with explicit "default" type
        strategy = EmbeddingStrategyFactory.create_strategy("default")
        self.assertIsInstance(strategy, ChromaDefaultEmbeddingStrategy)
        
        # And with unknown type
        strategy = EmbeddingStrategyFactory.create_strategy("unknown_type")
        self.assertIsInstance(strategy, ChromaDefaultEmbeddingStrategy)