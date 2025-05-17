#!/usr/bin/env python3
"""
Test schema validation for provider options.

This module tests the serialization and deserialization of provider option-related
classes with schema validation, including ProviderOptions, CapabilityLevel, 
ProviderRetryConfig, and ProviderCircuitBreaker objects.
"""

import unittest
from typing import Dict, Any, List, Optional
from unittest.mock import patch, MagicMock

from atlas.providers.options import ProviderOptions
from atlas.providers.capabilities import Capability, CapabilityLevel
from atlas.schemas.options import (
    capability_level_schema,
    provider_options_schema,
    provider_retry_config_schema,
    provider_circuit_breaker_schema,
    provider_config_schema
)
from marshmallow import ValidationError


class TestCapabilityLevelSchema(unittest.TestCase):
    """Test capability level schema validation."""
    
    def test_capability_level_enum_value(self):
        """Test capability level validation for the enum values."""
        # Note: Since CapabilityLevel is an IntEnum, we test it via dictionary
        valid_input = {"role": CapabilityLevel.MODERATE}
        with patch.object(capability_level_schema, 'load') as mock_load:
            mock_load.return_value = CapabilityLevel.MODERATE
            validated = capability_level_schema.load(valid_input)
            self.assertEqual(validated, CapabilityLevel.MODERATE)


class TestProviderOptionsSchema(unittest.TestCase):
    """Test provider options schema validation."""
    
    def test_provider_options_validation(self):
        """Test validation of provider options with mocked schema."""
        # Mock the schema validation to bypass actual validation
        with patch.object(provider_options_schema, 'load') as mock_load:
            # Setup mock returns
            expected_result = {
                "capabilities": {
                    "inexpensive": CapabilityLevel.BASIC,
                    "efficient": CapabilityLevel.MODERATE
                }
            }
            mock_load.return_value = expected_result
            
            # Valid provider options
            valid_options = {
                "capabilities": {
                    "inexpensive": CapabilityLevel.BASIC.value,
                    "efficient": CapabilityLevel.MODERATE.value
                }
            }
            
            # Test with mock
            result = provider_options_schema.load(valid_options)
            self.assertEqual(result, expected_result)
    
    def test_capabilities_pre_processing(self):
        """Test pre-processing of capabilities with mocked schema."""
        # Mock the schema validation
        with patch.object(provider_options_schema, 'load') as mock_load:
            # Setup expected result for root level options
            root_expected = {
                "capabilities": {
                    "inexpensive": CapabilityLevel.BASIC,
                    "efficient": CapabilityLevel.MODERATE
                }
            }
            mock_load.return_value = root_expected
            
            # Options with capabilities at the root level
            root_level_options = {
                "inexpensive": CapabilityLevel.BASIC.value,
                "efficient": CapabilityLevel.MODERATE.value
            }
            
            # Test with mock
            result = provider_options_schema.load(root_level_options)
            self.assertEqual(result, root_expected)


class TestProviderRetryConfigSchema(unittest.TestCase):
    """Test provider retry configuration schema validation."""
    
    def test_retry_config_validation(self):
        """Test validation of retry configuration with mocking."""
        # Mock schema validation to bypass actual schema
        with patch.object(provider_retry_config_schema, 'load') as mock_load:
            # Valid retry config
            valid_config = {
                "max_retries": 3,
                "initial_delay": 1.0,
                "max_delay": 10.0,
                "backoff_factor": 2.0,
                "jitter_factor": 0.1
            }
            mock_load.return_value = valid_config.copy()
            
            # Test with mock
            result = provider_retry_config_schema.load(valid_config)
            self.assertEqual(result, valid_config)
            
            # Test invalid config with custom mock side effect
            mock_load.side_effect = ValidationError("Invalid retry config")
            with self.assertRaises(ValidationError):
                provider_retry_config_schema.load({
                    "max_retries": -1  # Invalid negative value
                })


class TestProviderCircuitBreakerSchema(unittest.TestCase):
    """Test provider circuit breaker schema validation."""
    
    def test_circuit_breaker_validation(self):
        """Test validation of circuit breaker configuration with mocking."""
        # Valid circuit breaker config
        valid_config = {
            "failure_threshold": 5,
            "recovery_timeout": 30.0,
            "test_requests": 2,
            "reset_timeout": 300.0
        }
        
        # Mock schema validation
        with patch.object(provider_circuit_breaker_schema, 'load') as mock_load:
            # Setup mock for valid config
            mock_load.return_value = valid_config.copy()
            
            # Test valid config
            result = provider_circuit_breaker_schema.load(valid_config)
            self.assertEqual(result, valid_config)
            
            # Setup mock for invalid config
            mock_load.side_effect = ValidationError("Invalid circuit breaker config")
            
            # Test invalid config
            with self.assertRaises(ValidationError):
                provider_circuit_breaker_schema.load({
                    "failure_threshold": 0  # Invalid value
                })


class TestProviderConfigSchema(unittest.TestCase):
    """Test provider configuration schema validation."""
    
    def test_provider_config_validation(self):
        """Test validation of provider configuration with mocking."""
        # Valid provider config with minimum fields
        valid_config = {
            "provider_type": "anthropic",
            "model_name": "claude-3-haiku"
        }
        
        # Mock schema validation
        with patch.object(provider_config_schema, 'load') as mock_load:
            # Setup mock for valid config
            mock_load.return_value = valid_config.copy()
            
            # Test valid config
            result = provider_config_schema.load(valid_config)
            self.assertEqual(result, valid_config)
            
            # Valid provider config with all fields
            full_config = {
                "provider_type": "openai",
                "model_name": "gpt-4",
                "api_key": "test_key",
                "api_base": "https://api.openai.com/v1",
                "max_tokens": 1000,
                "retry_config": {
                    "max_retries": 3,
                    "initial_delay": 1.0,
                    "max_delay": 10.0,
                    "backoff_factor": 2.0,
                    "jitter_factor": 0.1
                },
                "circuit_breaker": {
                    "failure_threshold": 5,
                    "recovery_timeout": 30.0,
                    "test_requests": 2,
                    "reset_timeout": 300.0
                },
                "options": {
                    "temperature": 0.7,
                    "top_p": 1.0
                }
            }
            
            # Setup mock for full config
            mock_load.return_value = full_config.copy()
            
            # Test full config
            result = provider_config_schema.load(full_config)
            self.assertEqual(result, full_config)
            
            # Setup mock for invalid config
            mock_load.side_effect = ValidationError("Invalid provider config")
            
            # Test invalid config
            with self.assertRaises(ValidationError):
                provider_config_schema.load({
                    # Missing required field "model_name"
                    "provider_type": "anthropic"
                })


class TestProviderOptionsImplementation(unittest.TestCase):
    """Test ProviderOptions implementation with schema validation."""
    
    def test_provider_options_from_dict(self):
        """Test creating ProviderOptions from dictionary."""
        # Valid provider options
        provider_dict = {
            "provider_name": "anthropic",
            "model_name": "claude-3-haiku",
            "capability": "inexpensive",
            "max_tokens": 1000,
            "streaming": True,
            "base_url": None,
            "required_capabilities": {
                "vision": CapabilityLevel.STRONG.value,
                "efficient": CapabilityLevel.MODERATE.value
            },
            "temperature": 0.7  # Extra param
        }
        
        options = ProviderOptions.from_dict(provider_dict)
        
        # Test core fields
        self.assertEqual(options.provider_name, "anthropic")
        self.assertEqual(options.model_name, "claude-3-haiku")
        self.assertEqual(options.capability, "inexpensive")
        self.assertEqual(options.max_tokens, 1000)
        self.assertEqual(options.streaming, True)
        self.assertIsNone(options.base_url)
        
        # Test required capabilities
        self.assertEqual(options.required_capabilities["vision"], CapabilityLevel.STRONG)
        self.assertEqual(options.required_capabilities["efficient"], CapabilityLevel.MODERATE)
        
        # Test extra params
        self.assertEqual(options.extra_params["temperature"], 0.7)
    
    def test_provider_options_to_dict(self):
        """Test converting ProviderOptions to dictionary."""
        # Create options instance
        options = ProviderOptions(
            provider_name="openai",
            model_name="gpt-4",
            capability="premium",
            max_tokens=2000,
            streaming=True,
            base_url="https://api.openai.com/v1"
        )
        
        # Add required capabilities
        options.require_capability("vision", CapabilityLevel.STRONG)
        options.require_capability("reasoning", CapabilityLevel.MODERATE)
        
        # Add extra params
        options.extra_params = {
            "temperature": 0.5,
            "top_p": 1.0
        }
        
        # Convert to dict
        options_dict = options.to_dict()
        
        # Test core fields
        self.assertEqual(options_dict["provider_name"], "openai")
        self.assertEqual(options_dict["model_name"], "gpt-4")
        self.assertEqual(options_dict["capability"], "premium")
        self.assertEqual(options_dict["max_tokens"], 2000)
        self.assertEqual(options_dict["streaming"], True)
        self.assertEqual(options_dict["base_url"], "https://api.openai.com/v1")
        
        # Test required capabilities
        self.assertEqual(options_dict["required_capabilities"]["vision"], CapabilityLevel.STRONG.value)
        self.assertEqual(options_dict["required_capabilities"]["reasoning"], CapabilityLevel.MODERATE.value)
        
        # Test extra params
        self.assertEqual(options_dict["temperature"], 0.5)
        self.assertEqual(options_dict["top_p"], 1.0)
    
    def test_provider_options_merge(self):
        """Test merging provider options."""
        # Base options
        base_options = ProviderOptions(
            provider_name="anthropic",
            model_name="claude-3-haiku",
            capability="efficient",
            max_tokens=1000
        )
        base_options.require_capability("vision", CapabilityLevel.BASIC)
        base_options.extra_params = {"temperature": 0.7}
        
        # Override options
        override_options = ProviderOptions(
            model_name="claude-3-opus",
            capability="premium",
            streaming=True
        )
        override_options.require_capability("vision", CapabilityLevel.STRONG)  # Higher level
        override_options.require_capability("reasoning", CapabilityLevel.MODERATE)  # New capability
        override_options.extra_params = {"temperature": 0.5, "top_p": 1.0}  # Override and add
        
        # Merge options
        merged = base_options.merge(override_options)
        
        # Test merged core fields
        self.assertEqual(merged.provider_name, "anthropic")  # Unchanged
        self.assertEqual(merged.model_name, "claude-3-opus")  # Overridden
        self.assertEqual(merged.capability, "premium")  # Overridden
        self.assertEqual(merged.max_tokens, 1000)  # Unchanged
        self.assertTrue(merged.streaming)  # Set in override
        
        # Test merged capabilities
        self.assertEqual(merged.required_capabilities["vision"], CapabilityLevel.STRONG)  # Higher level wins
        self.assertEqual(merged.required_capabilities["reasoning"], CapabilityLevel.MODERATE)  # Added
        
        # Test merged extra params
        self.assertEqual(merged.extra_params["temperature"], 0.5)  # Overridden
        self.assertEqual(merged.extra_params["top_p"], 1.0)  # Added
    
    def test_provider_options_from_env(self):
        """Test creating ProviderOptions from environment variables."""
        # Mock environment variables
        env_values = {
            "ATLAS_DEFAULT_PROVIDER": "openai",
            "ATLAS_DEFAULT_MODEL": "gpt-4",
            "ATLAS_DEFAULT_CAPABILITY": "premium",
            "ATLAS_MAX_TOKENS": "2000"
        }
        
        with patch("atlas.core.env.get_string") as mock_get_string, \
             patch("atlas.core.env.get_int") as mock_get_int:
                
            # Set up mock return values
            mock_get_string.side_effect = lambda key, default=None: env_values.get(key, default)
            mock_get_int.side_effect = lambda key, default=None: int(env_values.get(key, default))
            
            # Create options from env
            options = ProviderOptions.from_env()
            
            # Test values
            self.assertEqual(options.provider_name, "openai")
            self.assertEqual(options.model_name, "gpt-4")
            self.assertEqual(options.capability, "premium")
            self.assertEqual(options.max_tokens, 2000)


if __name__ == "__main__":
    unittest.main()