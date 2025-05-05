#!/usr/bin/env python3
"""
Minimal test script for the Atlas framework.

This script tests basic functionality of the Atlas framework without requiring API access.
"""

import os
import sys
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from atlas.core.config import AtlasConfig
from atlas.core.prompts import load_system_prompt
from atlas.tests.helpers import (
    create_test_config,
    setup_test_environment
)


class TestConfig(unittest.TestCase):
    """Test the AtlasConfig class."""
    
    def test_default_config(self):
        """Test creating a config with default values."""
        config = create_test_config()
        
        # Check that defaults are set
        self.assertEqual(config.collection_name, "atlas_knowledge_base")
        self.assertTrue("atlas_chroma_db" in config.db_path)
        self.assertTrue("claude-3" in config.model_name)
        self.assertEqual(config.max_tokens, 2000)
        self.assertFalse(config.parallel_enabled)
        self.assertEqual(config.worker_count, 3)
        
        print("Config test passed!")
    
    def test_custom_config(self):
        """Test creating a config with custom values."""
        custom_config = AtlasConfig(
            anthropic_api_key="test_key",
            collection_name="custom_collection",
            db_path="/custom/path",
            model_name="custom-model",
            max_tokens=1000,
            parallel_enabled=True,
            worker_count=5
        )
        
        # Check custom values
        self.assertEqual(custom_config.collection_name, "custom_collection")
        self.assertEqual(custom_config.db_path, "/custom/path")
        self.assertEqual(custom_config.model_name, "custom-model")
        self.assertEqual(custom_config.max_tokens, 1000)
        self.assertTrue(custom_config.parallel_enabled)
        self.assertEqual(custom_config.worker_count, 5)
        
        print("Custom config test passed!")


class TestSystemPrompt(unittest.TestCase):
    """Test the system prompt loading."""
    
    def test_load_prompt(self):
        """Test loading the default system prompt."""
        prompt = load_system_prompt()
        
        # Check that it's a non-empty string
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)
        self.assertIn("Atlas", prompt)
        
        print("System prompt test passed!")


def run_tests():
    """Run all tests using the unittest framework."""
    print("=== Running Atlas Minimal Tests ===\n")
    
    # Set up the test environment
    setup_test_environment()
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestConfig))
    suite.addTest(loader.loadTestsFromTestCase(TestSystemPrompt))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n=== {result.testsRun - len(result.errors) - len(result.failures)}/{result.testsRun} tests passed! ===")


if __name__ == "__main__":
    run_tests()