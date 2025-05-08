"""
Unit tests for the Atlas configuration module.

These tests verify the functionality of the configuration module,
including environment variable handling, validation, and defaults.
"""

import os
import unittest
from unittest import mock
from pathlib import Path

from atlas.core.config import AtlasConfig
from atlas.core.errors import ConfigurationError, ValidationError
from atlas.tests.helpers.decorators import unit_test


class TestAtlasConfig(unittest.TestCase):
    """Test the AtlasConfig class functionality."""

    def setUp(self):
        """Set up the test environment."""
        # Store original environment variables
        self.original_env = os.environ.copy()
        
        # Set up test environment variables
        os.environ["ANTHROPIC_API_KEY"] = "test_key_for_config"
        
        # Clear other environment variables that might affect the tests
        for var in [
            "ATLAS_COLLECTION_NAME",
            "ATLAS_DB_PATH",
            "ATLAS_DEFAULT_MODEL",
            "ATLAS_MAX_TOKENS",
            "ATLAS_DEV_MODE",
            "ATLAS_MOCK_API",
            "ATLAS_LOG_LEVEL",
        ]:
            if var in os.environ:
                del os.environ[var]

    def tearDown(self):
        """Clean up the test environment."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    @unit_test
    def test_default_config(self):
        """Test creating a config with default values."""
        # Use a custom config with explicitly set values to test defaults correctly
        config = AtlasConfig(
            anthropic_api_key="test_key_for_config"
        )
        
        # Check that defaults are set correctly
        self.assertEqual(config.anthropic_api_key, "test_key_for_config")
        self.assertEqual(config.collection_name, "atlas_knowledge_base")
        self.assertTrue("atlas_chroma_db" in config.db_path)
        # Check model name is a string and contains claude-3
        self.assertTrue(isinstance(config.model_name, str))
        self.assertTrue("claude-3" in config.model_name.lower())
        self.assertEqual(config.max_tokens, 2000)
        self.assertFalse(config.parallel_enabled)
        self.assertEqual(config.worker_count, 3)
        self.assertFalse(config.dev_mode)
        self.assertFalse(config.mock_api)
        self.assertEqual(config.log_level, "INFO")

    @unit_test
    def test_custom_config(self):
        """Test creating a config with custom values."""
        custom_config = AtlasConfig(
            anthropic_api_key="custom_key",
            collection_name="custom_collection",
            db_path="/custom/path",
            model_name="custom-model",
            max_tokens=1000,
            parallel_enabled=True,
            worker_count=5,
        )
        
        # Check custom values
        self.assertEqual(custom_config.anthropic_api_key, "custom_key")
        self.assertEqual(custom_config.collection_name, "custom_collection")
        self.assertEqual(custom_config.db_path, "/custom/path")
        self.assertEqual(custom_config.model_name, "custom-model")
        self.assertEqual(custom_config.max_tokens, 1000)
        self.assertTrue(custom_config.parallel_enabled)
        self.assertEqual(custom_config.worker_count, 5)
        
        # Check default values for properties not explicitly set
        self.assertFalse(custom_config.dev_mode)
        self.assertFalse(custom_config.mock_api)
        self.assertEqual(custom_config.log_level, "INFO")

    @unit_test
    def test_environment_variables(self):
        """Test that environment variables override defaults."""
        # Explicitly set Anthropic API key to avoid errors
        os.environ["ANTHROPIC_API_KEY"] = "test_key_for_config"
        
        # Clear the environment cache to ensure fresh environment reading
        with mock.patch("atlas.core.env._ENV_LOADED", False), \
             mock.patch("atlas.core.env._ENV_CACHE", {}):
            
            # Set environment variables
            os.environ["ATLAS_COLLECTION_NAME"] = "env_collection"
            os.environ["ATLAS_DB_PATH"] = "/env/path"
            os.environ["ATLAS_DEFAULT_MODEL"] = "env-model"
            os.environ["ATLAS_MAX_TOKENS"] = "3000"
            os.environ["ATLAS_DEV_MODE"] = "true"
            os.environ["ATLAS_MOCK_API"] = "true"
            os.environ["ATLAS_LOG_LEVEL"] = "DEBUG"
            
            # Force environment reload
            from atlas.core.env import load_environment
            load_environment(force_reload=True)
            
            # Create config
            config = AtlasConfig()
            
            # Check environment variables were used
            self.assertEqual(config.collection_name, "env_collection")
            self.assertEqual(config.db_path, "/env/path")
            self.assertEqual(config.model_name, "env-model")
            self.assertEqual(config.max_tokens, 3000)
            self.assertTrue(config.dev_mode)
            self.assertTrue(config.mock_api)
            self.assertEqual(config.log_level, "DEBUG")

    @unit_test
    def test_environment_variable_precedence(self):
        """Test that explicit arguments override environment variables."""
        # Set environment variables
        os.environ["ATLAS_COLLECTION_NAME"] = "env_collection"
        os.environ["ATLAS_DEFAULT_MODEL"] = "env-model"
        os.environ["ATLAS_MAX_TOKENS"] = "3000"
        
        # Create config with explicit arguments
        config = AtlasConfig(
            collection_name="arg_collection",
            model_name="arg-model",
            max_tokens=4000,
        )
        
        # Check arguments override environment variables
        self.assertEqual(config.collection_name, "arg_collection")
        self.assertEqual(config.model_name, "arg-model")
        self.assertEqual(config.max_tokens, 4000)

    @unit_test
    def test_db_path_precedence(self):
        """Test the precedence order for database path configuration."""
        # Explicitly set Anthropic API key to avoid errors
        os.environ["ANTHROPIC_API_KEY"] = "test_key_for_config"
        
        # Clear the environment cache to ensure fresh environment reading
        with mock.patch("atlas.core.env._ENV_LOADED", False), \
             mock.patch("atlas.core.env._ENV_CACHE", {}):
            
            # 1. Test with explicit argument
            config = AtlasConfig(db_path="/explicit/path")
            self.assertEqual(config.db_path, "/explicit/path")
            
            # 2. Test with environment variable
            os.environ["ATLAS_DB_PATH"] = "/env/path"
            
            # Force environment reload
            from atlas.core.env import load_environment
            load_environment(force_reload=True)
            
            config = AtlasConfig()
            self.assertEqual(config.db_path, "/env/path")
            
            # 3. Test fallback to home directory
            del os.environ["ATLAS_DB_PATH"]
            
            # Force environment reload
            load_environment(force_reload=True)
            
            with mock.patch.object(Path, "home") as mock_home:
                mock_home.return_value = Path("/mock/home")
                config = AtlasConfig()
                self.assertEqual(config.db_path, "/mock/home/atlas_chroma_db")

    @unit_test
    def test_api_key_validation(self):
        """Test API key validation."""
        # Test with valid API key
        config = AtlasConfig(anthropic_api_key="valid_key")
        self.assertEqual(config.anthropic_api_key, "valid_key")
        
        # Test with missing API key by mocking get_string to return None
        with mock.patch("atlas.core.env.get_string", return_value=None):
            # Also mock get_bool to return False for SKIP_API_KEY_CHECK
            with mock.patch("atlas.core.env.get_bool", return_value=False):
                with self.assertRaises(ConfigurationError) as context:
                    AtlasConfig()
                
                self.assertIn("ANTHROPIC_API_KEY must be provided", str(context.exception))
        
        # Test with SKIP_API_KEY_CHECK by mocking get_string and get_bool
        with mock.patch("atlas.core.env.get_string", return_value=None):
            # Mock get_bool to return the right value based on the parameter name
            def mock_get_bool(param_name, default=False):
                if param_name == "SKIP_API_KEY_CHECK":
                    return True
                return default
                
            with mock.patch("atlas.core.env.get_bool", side_effect=mock_get_bool):
                config = AtlasConfig()  # Should not raise an error
                self.assertIsNone(config.anthropic_api_key)

    @unit_test
    def test_config_validation(self):
        """Test configuration validation rules."""
        # Create a test class that extends AtlasConfig but doesn't validate in __init__
        class TestConfig(AtlasConfig):
            def __init__(self, **kwargs):
                self.anthropic_api_key = kwargs.get('anthropic_api_key', 'test_key')
                self.collection_name = kwargs.get('collection_name', 'atlas_knowledge_base')
                self.db_path = kwargs.get('db_path', str(Path.home() / "atlas_chroma_db"))
                self.model_name = kwargs.get('model_name', 'claude-3-5-sonnet-20240620')
                self.max_tokens = kwargs.get('max_tokens', 2000)
                self.parallel_enabled = kwargs.get('parallel_enabled', False)
                self.worker_count = kwargs.get('worker_count', 3)
                self.dev_mode = kwargs.get('dev_mode', False)
                self.mock_api = kwargs.get('mock_api', False)
                self.log_level = kwargs.get('log_level', 'INFO')
                # No validation call here, unlike the real AtlasConfig
        
        # Test valid configuration
        config = TestConfig(
            anthropic_api_key="valid_key",
            model_name="valid-model",
            max_tokens=1000,
            worker_count=3,
        )
        
        # Should not raise any exceptions
        AtlasConfig.validate(config)
        
        # Test invalid model name
        with self.assertRaises(ValidationError) as context:
            config = TestConfig(anthropic_api_key="valid_key", model_name="")
            AtlasConfig.validate(config)
        
        error = context.exception
        self.assertIn("model_name", str(error.details.get("field_errors", {})))
        
        # Test invalid max_tokens
        with self.assertRaises(ValidationError) as context:
            config = TestConfig(anthropic_api_key="valid_key", max_tokens=-1)
            AtlasConfig.validate(config)
        
        error = context.exception
        self.assertIn("max_tokens", str(error.details.get("field_errors", {})))
        
        # Test invalid worker count with parallel enabled
        with self.assertRaises(ValidationError) as context:
            config = TestConfig(
                anthropic_api_key="valid_key",
                parallel_enabled=True,
                worker_count=0,
            )
            AtlasConfig.validate(config)
        
        error = context.exception
        self.assertIn("worker_count", str(error.details.get("field_errors", {})))
        
        # Test invalid DB path
        with self.assertRaises(ValidationError) as context:
            config = TestConfig(anthropic_api_key="valid_key", db_path="")
            AtlasConfig.validate(config)
        
        error = context.exception
        self.assertIn("db_path", str(error.details.get("field_errors", {})))

    @unit_test
    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = AtlasConfig(
            anthropic_api_key="secret_key",
            collection_name="test_collection",
            db_path="/test/path",
            model_name="test-model",
            max_tokens=1500,
            parallel_enabled=True,
            worker_count=4,
        )
        
        config_dict = config.to_dict()
        
        # Verify all fields are included
        self.assertEqual(config_dict["collection_name"], "test_collection")
        self.assertEqual(config_dict["db_path"], "/test/path")
        self.assertEqual(config_dict["model_name"], "test-model")
        self.assertEqual(config_dict["max_tokens"], 1500)
        self.assertTrue(config_dict["parallel_enabled"])
        self.assertEqual(config_dict["worker_count"], 4)
        self.assertFalse(config_dict["dev_mode"])
        self.assertFalse(config_dict["mock_api"])
        self.assertEqual(config_dict["log_level"], "INFO")
        
        # Ensure API key is not included for security
        self.assertNotIn("anthropic_api_key", config_dict)

    @unit_test
    def test_boolean_environment_variables(self):
        """Test boolean environment variable parsing."""
        # Explicitly set Anthropic API key to avoid errors
        os.environ["ANTHROPIC_API_KEY"] = "test_key_for_config"
        
        # Clear the environment cache to ensure fresh environment reading
        with mock.patch("atlas.core.env._ENV_LOADED", False), \
             mock.patch("atlas.core.env._ENV_CACHE", {}):
             
            # Test truthy values
            for truthy_value in ["true", "True", "TRUE", "1", "yes", "Yes", "YES", "on", "On", "ON"]:
                os.environ["ATLAS_DEV_MODE"] = truthy_value
                os.environ["ATLAS_MOCK_API"] = truthy_value
                
                # Force environment reload
                from atlas.core.env import load_environment
                load_environment(force_reload=True)
                
                config = AtlasConfig()
                self.assertTrue(config.dev_mode, f"Failed with value: {truthy_value}")
                self.assertTrue(config.mock_api, f"Failed with value: {truthy_value}")
            
            # Test falsy values
            for falsy_value in ["false", "False", "FALSE", "0", "no", "No", "NO", "off", "Off", "OFF"]:
                os.environ["ATLAS_DEV_MODE"] = falsy_value
                os.environ["ATLAS_MOCK_API"] = falsy_value
                
                # Force environment reload
                load_environment(force_reload=True)
                
                config = AtlasConfig()
                self.assertFalse(config.dev_mode, f"Failed with value: {falsy_value}")
                self.assertFalse(config.mock_api, f"Failed with value: {falsy_value}")

    @unit_test
    def test_integer_environment_variables(self):
        """Test integer environment variable parsing."""
        # Explicitly set Anthropic API key to avoid errors
        os.environ["ANTHROPIC_API_KEY"] = "test_key_for_config"
        
        # Clear the environment cache to ensure fresh environment reading
        with mock.patch("atlas.core.env._ENV_LOADED", False), \
             mock.patch("atlas.core.env._ENV_CACHE", {}):
            
            # Test valid integer value
            os.environ["ATLAS_MAX_TOKENS"] = "5000"
            
            # Force environment reload
            from atlas.core.env import load_environment
            load_environment(force_reload=True)
            
            config = AtlasConfig()
            self.assertEqual(config.max_tokens, 5000)
            
            # Test invalid integer value (should fall back to default)
            os.environ["ATLAS_MAX_TOKENS"] = "not_an_integer"
            
            # Force environment reload
            load_environment(force_reload=True)
            
            # This would normally log a warning but shouldn't fail
            config = AtlasConfig()
            self.assertEqual(config.max_tokens, 2000)  # Default value


class TestConfigErrorHandling(unittest.TestCase):
    """Test error handling in the configuration module."""

    def setUp(self):
        """Set up the test environment."""
        # Store original environment variables
        self.original_env = os.environ.copy()
        
        # Set up test environment variables
        os.environ["ANTHROPIC_API_KEY"] = "test_key_for_config"

    def tearDown(self):
        """Clean up the test environment."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    @unit_test
    def test_validation_error_logging(self):
        """Test that validation errors are logged but don't prevent creation."""
        # Create a ValidationError that will be raised during validation
        test_validation_error = ValidationError(
            message="Invalid configuration settings",
            field_errors={"model_name": ["Model name must be a non-empty string"]},
        )
        
        # Mock the validate method to raise our test error
        with mock.patch.object(AtlasConfig, "validate") as mock_validate:
            mock_validate.side_effect = test_validation_error
            
            # Mock the ValidationError.log method to do nothing
            with mock.patch.object(ValidationError, "log") as mock_error_log:
                # Mock the logger to check warning calls
                with mock.patch("atlas.core.config.logger") as mock_logger:
                    # Create config that should trigger validation warning
                    config = AtlasConfig(anthropic_api_key="test_key")
                    
                    # Verify the error was logged
                    mock_error_log.assert_called_once()
                    
                    # Verify that the warning was logged
                    mock_logger.warning.assert_called_with(
                        "Configuration validation failed, but proceeding with partial configuration"
                    )
                    
                    # The config should still be created despite validation failure
                    self.assertIsNotNone(config)

    @unit_test
    def test_missing_api_key_error(self):
        """Test the error raised when API key is missing."""
        # Mock get_string to return None for API key
        with mock.patch("atlas.core.env.get_string", side_effect=lambda key, default=None: None):
            # Mock get_bool to return False for SKIP_API_KEY_CHECK
            with mock.patch("atlas.core.env.get_bool", return_value=False):
                # Attempt to create config (should raise ConfigurationError)
                with self.assertRaises(ConfigurationError) as context:
                    AtlasConfig()
                
                # Check error details
                error = context.exception
                self.assertEqual(error.severity.value, "error")  # Use value instead of name
                self.assertIn("ANTHROPIC_API_KEY", error.message)
                self.assertEqual(error.details["missing_config"], "ANTHROPIC_API_KEY")
                self.assertEqual(error.details["config_source"], "environment")

    @unit_test
    def test_skip_api_key_check(self):
        """Test skipping API key validation with environment variable."""
        # Mock get_string to return None for API key
        with mock.patch("atlas.core.env.get_string", side_effect=lambda key, default=None: None):
            # Mock get_bool to return True for SKIP_API_KEY_CHECK and False for others
            def mock_get_bool(param_name, default=False):
                if param_name == "SKIP_API_KEY_CHECK":
                    return True
                return default
                
            with mock.patch("atlas.core.env.get_bool", side_effect=mock_get_bool):
                # Create config (should not raise an error)
                config = AtlasConfig()
                
                # API key should be None
                self.assertIsNone(config.anthropic_api_key)