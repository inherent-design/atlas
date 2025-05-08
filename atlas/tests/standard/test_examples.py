"""
Example-based tests for Atlas components.

This module demonstrates how to create tests based on examples, making them more
resilient to implementation changes and easier to understand.
"""

import os
import sys
import unittest
import logging
import json
from unittest import mock
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Import test helpers
from atlas.tests.test_helpers import (
    TestWithTokenTracking,
    api_test,
    mock_test,
    integration_test,
    create_mock_response,
    create_example_test_case,
)

# Import Atlas components
from atlas.models import (
    ModelProvider,
    ModelRequest,
    ModelResponse,
    ModelMessage,
    MessageContent,
    ModelRole,
    TokenUsage,
    CostEstimate,
)

# Import providers
from atlas.models.mock import MockProvider
from atlas.models.openai import OpenAIProvider

# Import knowledge components
from atlas.knowledge.chunking import chunk_text, ChunkingStrategy
from atlas.knowledge.embedding import embed_text
from atlas.knowledge.retrieval import retrieve_relevant_chunks

# Configure logging
logger = logging.getLogger(__name__)


# Example data for knowledge retrieval tests
EXAMPLE_DOCUMENTS = [
    {
        "title": "Introduction to Machine Learning",
        "content": """
        Machine learning is a branch of artificial intelligence that focuses on developing systems
        that can learn from and make decisions based on data. It's used in a variety of applications,
        from image recognition to natural language processing.
        
        There are several types of machine learning:
        1. Supervised learning
        2. Unsupervised learning
        3. Reinforcement learning
        """,
        "metadata": {
            "author": "AI Researcher",
            "year": 2023,
            "category": "technology"
        }
    },
    {
        "title": "Deep Learning Fundamentals",
        "content": """
        Deep learning is a subset of machine learning that uses neural networks with multiple layers.
        These networks are capable of learning from large amounts of data and can achieve state-of-the-art
        results in many tasks.
        
        Key concepts in deep learning include:
        - Neural networks
        - Backpropagation
        - Activation functions
        - Gradient descent
        """,
        "metadata": {
            "author": "Neural Network Expert",
            "year": 2023,
            "category": "technology"
        }
    },
    {
        "title": "Natural Language Processing",
        "content": """
        Natural Language Processing (NLP) is a field of AI that focuses on the interaction between
        computers and human language. It involves tasks such as:
        
        - Text classification
        - Named entity recognition
        - Machine translation
        - Question answering
        - Sentiment analysis
        
        Modern NLP relies heavily on deep learning techniques, particularly transformer models
        like BERT and GPT.
        """,
        "metadata": {
            "author": "Language Researcher",
            "year": 2022,
            "category": "technology"
        }
    }
]


class TestExampleBasedChunking(unittest.TestCase):
    """Test chunking with examples."""
    
    def test_paragraph_chunking(self):
        """Test paragraph-based chunking with example documents."""
        # Example document
        document = EXAMPLE_DOCUMENTS[0]["content"]
        
        # Expected chunk count for paragraph strategy
        expected_chunk_count = 3  # The document has 3 paragraphs
        
        # Chunk the document
        chunks = chunk_text(document, ChunkingStrategy.PARAGRAPH)
        
        # Verify the result
        self.assertEqual(len(chunks), expected_chunk_count)
        self.assertTrue(any("Machine learning is a branch" in chunk for chunk in chunks))
        self.assertTrue(any("There are several types" in chunk for chunk in chunks))
    
    def test_fixed_size_chunking(self):
        """Test fixed-size chunking with example documents."""
        # Example document
        document = EXAMPLE_DOCUMENTS[0]["content"]
        
        # Fixed size in characters
        chunk_size = 100
        
        # Chunk the document
        chunks = chunk_text(document, ChunkingStrategy.FIXED_SIZE, chunk_size=chunk_size)
        
        # Verify the result
        for chunk in chunks:
            # Allow slightly larger chunks due to sentence boundaries
            self.assertLessEqual(len(chunk), chunk_size * 1.5)
    
    def test_sentence_chunking(self):
        """Test sentence-based chunking with example documents."""
        # Example document with clear sentences
        document = ("This is the first sentence. This is the second sentence. "
                   "And here's a third one! And a fourth one?")
        
        # Expected chunk count
        expected_chunk_count = 4
        
        # Chunk the document
        chunks = chunk_text(document, ChunkingStrategy.SENTENCE)
        
        # Verify the result
        self.assertEqual(len(chunks), expected_chunk_count)
        self.assertTrue("This is the first sentence" in chunks[0])
        self.assertTrue("This is the second sentence" in chunks[1])
        self.assertTrue("And here's a third one" in chunks[2])
        self.assertTrue("And a fourth one" in chunks[3])


# Example-based test factory with examples as parameters
class TestExampleBasedQuerying(TestWithTokenTracking):
    """Test querying with examples."""
    
    def setUp(self):
        """Set up examples."""
        super().setUp()
        self.examples = [
            {
                "query": "What is machine learning?",
                "expected_keywords": ["artificial intelligence", "data", "supervised", "unsupervised"]
            },
            {
                "query": "Explain deep learning",
                "expected_keywords": ["neural networks", "multiple layers", "backpropagation"]
            },
            {
                "query": "What is NLP used for?",
                "expected_keywords": ["text classification", "translation", "sentiment"]
            }
        ]
        
        # Create a mock provider
        self.provider = MockProvider()
    
    @mock_test
    def test_query_examples(self):
        """Test queries against examples."""
        for example in self.examples:
            query = example["query"]
            expected_keywords = example["expected_keywords"]
            
            # Set up the mock response
            self.provider.set_response(f"Response to: {query}")
            
            # Create a request
            request = ModelRequest(
                messages=[ModelMessage.user(query)],
                max_tokens=50
            )
            
            # Generate a response
            response = self.provider.generate(request)
            
            # Check that the response contains the query
            self.assertIn(query, response.content)
    
    @api_test
    def test_real_query_examples(self):
        """Test queries against examples with a real provider."""
        # Skip if no API key
        if not os.environ.get("OPENAI_API_KEY"):
            self.skipTest("OPENAI_API_KEY not set")
        
        # Create a real provider (use cheaper model)
        provider = OpenAIProvider(model_name="gpt-3.5-turbo")
        
        # Test only the first example to minimize API usage
        example = self.examples[0]
        query = example["query"]
        expected_keywords = example["expected_keywords"]
        
        # Create a request
        request = ModelRequest(
            messages=[ModelMessage.user(query)],
            max_tokens=100
        )
        
        # Generate a response
        response = provider.generate(request)
        
        # Track token usage
        self.track_usage(response)
        
        # Check that the response contains at least one expected keyword
        self.assertTrue(any(keyword.lower() in response.content.lower() 
                           for keyword in expected_keywords))


# Dynamic test creation using examples
def create_test_methods(test_class):
    """Dynamically create test methods from examples.
    
    Args:
        test_class: The test class to add methods to.
    """
    # Example test cases
    examples = [
        {
            "name": "simple_addition",
            "inputs": {"a": 5, "b": 3},
            "expected_outputs": {"result": 8}
        },
        {
            "name": "negative_numbers",
            "inputs": {"a": -2, "b": 7},
            "expected_outputs": {"result": 5}
        },
        {
            "name": "large_numbers",
            "inputs": {"a": 1000, "b": 2000},
            "expected_outputs": {"result": 3000}
        }
    ]
    
    # Test function that will be customized for each example
    def example_test_func(self, inputs, expected_outputs):
        # Simple addition function to test
        def add_numbers(a, b):
            return {"result": a + b}
        
        # Run the function with inputs
        result = add_numbers(inputs["a"], inputs["b"])
        
        # Verify against expected outputs
        self.assertEqual(result["result"], expected_outputs["result"])
    
    # Add a test method for each example
    for example in examples:
        test_name = f"test_{example['name']}"
        test_method = create_example_test_case(
            inputs=example["inputs"],
            expected_outputs=example["expected_outputs"],
            test_func=example_test_func
        )
        setattr(test_class, test_name, test_method)


class TestDynamicExamples(unittest.TestCase):
    """Test class with dynamically created test methods."""
    pass

# Add test methods to the class
create_test_methods(TestDynamicExamples)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main()