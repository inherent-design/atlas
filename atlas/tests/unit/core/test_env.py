"""
Unit tests for the env.py module.

This module provides comprehensive tests for the environment variable handling module.
"""

import os
import unittest
import tempfile
from pathlib import Path

from atlas.tests.helpers.decorators import unit_test
from atlas.core import env


class TestEnvironmentModule(unittest.TestCase):
    """Test cases for the environment variable handling module."""

    def setUp(self):
        """Set up test environment."""
        # Store original environment
        self.original_env = os.environ.copy()

        # Set test variables
        os.environ["ATLAS_TEST_STRING"] = "test_value"
        os.environ["ATLAS_TEST_INT"] = "42"
        os.environ["ATLAS_TEST_FLOAT"] = "3.14"
        os.environ["ATLAS_TEST_BOOL_TRUE"] = "true"
        os.environ["ATLAS_TEST_BOOL_FALSE"] = "false"
        os.environ["ATLAS_TEST_LIST"] = "one,two,three"

        # Force reload environment
        env.load_environment(force_reload=True)

    def tearDown(self):
        """Restore original environment."""
        os.environ.clear()
        os.environ.update(self.original_env)
        env.load_environment(force_reload=True)

    @unit_test
    def test_basic_functions(self):
        """Test basic environment variable functions."""
        # Test string functions
        self.assertEqual(env.get_string("ATLAS_TEST_STRING"), "test_value")
        self.assertIsNone(env.get_string("ATLAS_NON_EXISTENT"))
        self.assertEqual(env.get_string("ATLAS_NON_EXISTENT", "default"), "default")

        # Test int functions
        self.assertEqual(env.get_int("ATLAS_TEST_INT"), 42)
        self.assertIsNone(env.get_int("ATLAS_NON_EXISTENT"))
        self.assertEqual(env.get_int("ATLAS_NON_EXISTENT", 99), 99)

        # Test float functions
        self.assertEqual(env.get_float("ATLAS_TEST_FLOAT"), 3.14)
        self.assertIsNone(env.get_float("ATLAS_NON_EXISTENT"))
        self.assertEqual(env.get_float("ATLAS_NON_EXISTENT", 2.71), 2.71)

        # Test bool functions
        self.assertTrue(env.get_bool("ATLAS_TEST_BOOL_TRUE"))
        self.assertFalse(env.get_bool("ATLAS_TEST_BOOL_FALSE"))
        self.assertFalse(env.get_bool("ATLAS_NON_EXISTENT"))
        self.assertTrue(env.get_bool("ATLAS_NON_EXISTENT", True))

        # Test list functions
        self.assertEqual(env.get_list("ATLAS_TEST_LIST"), ["one", "two", "three"])
        self.assertEqual(env.get_list("ATLAS_NON_EXISTENT"), [])
        self.assertEqual(env.get_list("ATLAS_NON_EXISTENT", ["default"]), ["default"])

    @unit_test
    def test_required_string(self):
        """Test the get_required_string function."""
        # Test with existing variable
        self.assertEqual(env.get_required_string("ATLAS_TEST_STRING"), "test_value")

        # Test with non-existent variable
        with self.assertRaises(ValueError):
            env.get_required_string("ATLAS_NON_EXISTENT")

    @unit_test
    def test_api_key_functions(self):
        """Test API key handling functions."""
        # Clear any existing error
        env._ENV_LOADED = False

        # Set test API keys directly in env cache
        env.set_env_var("ANTHROPIC_API_KEY", "test_anthropic_key")
        env.set_env_var("OPENAI_API_KEY", "test_openai_key")

        # Test API key functions
        self.assertEqual(env.get_api_key("anthropic"), "test_anthropic_key")
        self.assertEqual(env.get_api_key("openai"), "test_openai_key")
        self.assertIsNone(env.get_api_key("unknown"))

        # Test has_api_key function
        self.assertTrue(env.has_api_key("anthropic"))
        self.assertTrue(env.has_api_key("openai"))
        self.assertFalse(env.has_api_key("unknown"))

        # Test get_available_providers function
        providers = env.get_available_providers()
        self.assertIsInstance(providers, dict)
        self.assertTrue(providers["anthropic"])
        self.assertTrue(providers["openai"])

    @unit_test
    def test_env_file_loading(self):
        """Test loading environment variables from .env file."""
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".env", delete=False
        ) as temp_env:
            temp_env.write("ATLAS_TEST_FROM_FILE=file_value\n")
            temp_env.write("ATLAS_TEST_OVERRIDE=file_override\n")
            temp_env_path = temp_env.name

        try:
            # Set a variable to be overridden
            os.environ["ATLAS_TEST_OVERRIDE"] = "original_value"

            # Load the .env file
            self.assertTrue(env.load_env_file(temp_env_path))

            # Check variables
            self.assertEqual(env.get_string("ATLAS_TEST_FROM_FILE"), "file_value")
            self.assertEqual(env.get_string("ATLAS_TEST_OVERRIDE"), "file_override")

            # Test with non-existent file
            self.assertFalse(env.load_env_file("/non/existent/path.env"))

        finally:
            # Clean up
            try:
                os.unlink(temp_env_path)
            except:
                pass

    @unit_test
    def test_required_vars_validation(self):
        """Test validation of required environment variables."""
        # Set test variables
        os.environ["ATLAS_TEST_REQUIRED_1"] = "value1"
        os.environ["ATLAS_TEST_REQUIRED_2"] = "value2"

        # Force reload environment
        env.load_environment(force_reload=True)

        # Test validation with all variables present
        missing = env.validate_required_vars(
            ["ATLAS_TEST_REQUIRED_1", "ATLAS_TEST_REQUIRED_2"]
        )
        self.assertEqual(len(missing), 0)

        # Test validation with missing variables
        missing = env.validate_required_vars(
            ["ATLAS_TEST_REQUIRED_1", "ATLAS_TEST_REQUIRED_3"]
        )
        self.assertEqual(len(missing), 1)
        self.assertIn("ATLAS_TEST_REQUIRED_3", missing)

    @unit_test
    def test_set_env_var(self):
        """Test setting environment variables."""
        # Set an environment variable
        env.set_env_var("ATLAS_TEST_SET", "set_value")

        # Check that it was set in the cache and os.environ
        self.assertEqual(env.get_string("ATLAS_TEST_SET"), "set_value")
        self.assertEqual(os.environ.get("ATLAS_TEST_SET"), "set_value")

        # Test with update_os_environ=False
        env.set_env_var(
            "ATLAS_TEST_SET_CACHE_ONLY", "cache_only", update_os_environ=False
        )
        self.assertEqual(env.get_string("ATLAS_TEST_SET_CACHE_ONLY"), "cache_only")
        self.assertNotIn("ATLAS_TEST_SET_CACHE_ONLY", os.environ)


if __name__ == "__main__":
    unittest.main()