#!/usr/bin/env python3
"""
Test provider-specific schema validation.

This module tests the validation of provider-specific options schemas 
(Anthropic, OpenAI, Ollama) and their integration with the provider factory.
"""

import unittest
from typing import Dict, Any, List, Optional
from unittest.mock import patch, MagicMock

from atlas.providers.capabilities import Capability, CapabilityLevel
from atlas.schemas.options import (
    anthropic_options_schema,
    openai_options_schema,
    ollama_options_schema,
    provider_options_schema,
    PROVIDER_OPTIONS_SCHEMAS
)
from marshmallow import ValidationError


class TestProviderSpecificSchemas(unittest.TestCase):
    """Test provider-specific option schemas."""
    
    def test_anthropic_options_schema(self):
        """Test Anthropic-specific options schema."""
        # Valid Anthropic options
        valid_options = {
            "system": "You are a helpful assistant.",
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_tokens": 1000,
            "stream": True,
            "capabilities": {
                "vision": "strong",
                "reasoning": "moderate"
            }
        }
        
        # Load the options
        result = anthropic_options_schema.load(valid_options)
        
        # Test Anthropic-specific fields were preserved
        self.assertEqual(result["system"], "You are a helpful assistant.")
        self.assertEqual(result["temperature"], 0.7)
        self.assertEqual(result["max_tokens"], 1000)
        self.assertEqual(result["stream"], True)
        
        # Test capabilities were converted
        self.assertEqual(result["capabilities"]["vision"], CapabilityLevel.STRONG)
        self.assertEqual(result["capabilities"]["reasoning"], CapabilityLevel.MODERATE)
        
        # Test invalid Anthropic options
        invalid_options = {
            "system": "You are a helpful assistant.",
            "temperature": 1.5,  # Invalid: must be between 0 and 1
            "functions": [{"name": "test"}]  # Not supported by Anthropic
        }
        
        # Expect validation error
        with self.assertRaises(ValidationError):
            anthropic_options_schema.load(invalid_options)
            
    def test_openai_options_schema(self):
        """Test OpenAI-specific options schema."""
        # Valid OpenAI options with functions
        valid_function_options = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1000,
            "stream": True,
            "functions": [
                {
                    "name": "get_weather",
                    "description": "Get the weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        },
                        "required": ["location"]
                    }
                }
            ],
            "function_call": "auto",
            "capabilities": {
                "vision": "strong",
                "reasoning": "moderate"
            }
        }
        
        # Load the options
        result = openai_options_schema.load(valid_function_options)
        
        # Test OpenAI-specific fields were preserved
        self.assertEqual(result["temperature"], 0.7)
        self.assertEqual(result["max_tokens"], 1000)
        self.assertEqual(result["stream"], True)
        self.assertEqual(len(result["functions"]), 1)
        self.assertEqual(result["functions"][0]["name"], "get_weather")
        self.assertEqual(result["function_call"], "auto")
        
        # Test capabilities were converted
        self.assertEqual(result["capabilities"]["vision"], CapabilityLevel.STRONG)
        self.assertEqual(result["capabilities"]["reasoning"], CapabilityLevel.MODERATE)
        
        # Valid OpenAI options with tools
        valid_tool_options = {
            "temperature": 0.7,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get the weather for a location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string"}
                            },
                            "required": ["location"]
                        }
                    }
                }
            ],
            "tool_choice": "auto"
        }
        
        # Load the options
        result = openai_options_schema.load(valid_tool_options)
        
        # Test OpenAI-specific tool fields were preserved
        self.assertEqual(result["temperature"], 0.7)
        self.assertEqual(len(result["tools"]), 1)
        self.assertEqual(result["tools"][0]["function"]["name"], "get_weather")
        self.assertEqual(result["tool_choice"], "auto")
        
        # Test invalid OpenAI options - using both functions and tools
        invalid_options = {
            "functions": [{"name": "test"}],
            "tools": [{"type": "function", "function": {"name": "test"}}]
        }
        
        # Expect validation error
        with self.assertRaises(ValidationError):
            openai_options_schema.load(invalid_options)
            
    def test_ollama_options_schema(self):
        """Test Ollama-specific options schema."""
        # Valid Ollama options
        valid_options = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_tokens": 1000,
            "stream": True,
            "mirostat": 2,
            "mirostat_eta": 0.1,
            "mirostat_tau": 5.0,
            "num_ctx": 4096,
            "repeat_penalty": 1.1,
            "seed": 42,
            "stop": ["END", "STOP"],
            "capabilities": {
                "efficient": "strong",
                "inexpensive": "exceptional"
            }
        }
        
        # Load the options
        result = ollama_options_schema.load(valid_options)
        
        # Test Ollama-specific fields were preserved
        self.assertEqual(result["temperature"], 0.7)
        self.assertEqual(result["max_tokens"], 1000)
        self.assertEqual(result["stream"], True)
        self.assertEqual(result["mirostat"], 2)
        self.assertEqual(result["mirostat_eta"], 0.1)
        self.assertEqual(result["mirostat_tau"], 5.0)
        self.assertEqual(result["num_ctx"], 4096)
        self.assertEqual(result["repeat_penalty"], 1.1)
        self.assertEqual(result["seed"], 42)
        self.assertEqual(result["stop"], ["END", "STOP"])
        
        # Test capabilities were converted
        self.assertEqual(result["capabilities"]["efficient"], CapabilityLevel.STRONG)
        self.assertEqual(result["capabilities"]["inexpensive"], CapabilityLevel.EXCEPTIONAL)


class TestProviderOptionsMapping(unittest.TestCase):
    """Test provider options schema mapping."""
    
    def test_provider_schema_mapping(self):
        """Test provider options schema mapping."""
        # Test that all provider types have a schema
        self.assertIn("anthropic", PROVIDER_OPTIONS_SCHEMAS)
        self.assertIn("openai", PROVIDER_OPTIONS_SCHEMAS)
        self.assertIn("ollama", PROVIDER_OPTIONS_SCHEMAS)
        self.assertIn("default", PROVIDER_OPTIONS_SCHEMAS)
        
        # Test that schemas are the correct type
        self.assertEqual(PROVIDER_OPTIONS_SCHEMAS["anthropic"], anthropic_options_schema)
        self.assertEqual(PROVIDER_OPTIONS_SCHEMAS["openai"], openai_options_schema)
        self.assertEqual(PROVIDER_OPTIONS_SCHEMAS["ollama"], ollama_options_schema)
        self.assertEqual(PROVIDER_OPTIONS_SCHEMAS["default"], provider_options_schema)
        
        # Test fallback to default for unknown provider
        unknown_provider = "unknown_provider"
        self.assertNotIn(unknown_provider, PROVIDER_OPTIONS_SCHEMAS)
        schema = PROVIDER_OPTIONS_SCHEMAS.get(unknown_provider, PROVIDER_OPTIONS_SCHEMAS["default"])
        self.assertEqual(schema, provider_options_schema)


if __name__ == "__main__":
    unittest.main()