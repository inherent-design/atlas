# Provider Validation System

This directory contains the validation modules for the Atlas provider system. These modules ensure that provider configurations, options, and model selections are valid and compatible with the provider implementations.

## Overview

The validation system consists of several components:

1. `validation.py`: Core validation decorators and utilities for validating provider requests, responses, and capabilities.
2. `validation_utils.py`: Provider-specific validation utilities for Anthropic, OpenAI, and Ollama.
3. `model_validator.py`: Utilities for validating model names and capabilities for specific providers.
4. `validators.py`: Concrete validator implementations for different provider types.

## Components

### Core Validation (validation.py)

This module provides generic validation decorators and utilities:

- `validate_request`: Decorator to validate request objects against schemas
- `validate_response`: Decorator to validate response objects against schemas
- `validated_by`: Decorator factory for validating with a specific schema
- `validate_options`: Decorator for validating provider options during initialization
- `validate_stream_handler`: Decorator for validating streaming operations
- `validate_capabilities`: Decorator for validating provider capabilities

### Provider-Specific Validation (validation_utils.py)

This module provides provider-specific validation decorators:

- `validate_anthropic_options`: Decorator to validate Anthropic-specific options
- `validate_openai_options`: Decorator to validate OpenAI-specific options
- `validate_ollama_options`: Decorator to validate Ollama-specific options
- `validate_provider_options`: Factory for provider-specific validation decorators
- `validate_model_compatibility`: Decorator to validate model compatibility with providers
- `validate_provider_features`: Decorator to validate feature compatibility with providers

### Model Validation (model_validator.py)

This module provides utilities for validating model names and capabilities:

- `validate_anthropic_model`: Validate Anthropic model names
- `validate_openai_model`: Validate OpenAI model names
- `validate_ollama_model`: Validate Ollama model names
- `validate_model_for_provider`: Generic validation for any provider
- `ensure_valid_model`: Raise error if model is invalid
- `get_default_model`: Get default model for a provider
- `get_model_capabilities`: Get capability levels for a specific model

### Validator Implementations (validators.py)

This module provides concrete validator implementations for different providers:

- `AnthropicValidator`: Validation for Anthropic provider
- `OpenAIValidator`: Validation for OpenAI provider
- `OllamaValidator`: Validation for Ollama provider
- `validate_provider_config`: Validate a provider configuration dictionary

## Usage

### Validating Provider Options

```python
from atlas.providers.validation_utils import validate_anthropic_options

@validate_anthropic_options
def configure_provider(self, options: Dict[str, Any]) -> None:
    # options is guaranteed to be valid for Anthropic
    ...
```

### Validating Models

```python
from atlas.providers.model_validator import validate_model_for_provider, ensure_valid_model

# Check if model is valid
is_valid, error = validate_model_for_provider("claude-3-7-sonnet-20250219", "anthropic")
if not is_valid:
    print(f"Invalid model: {error}")

# Ensure model is valid, raising exception if not
ensure_valid_model("gpt-4.1", "openai")
```

### Validating Provider Configurations

```python
from atlas.providers.validators import validate_provider_config

config = {
    "provider_type": "anthropic",
    "model_name": "claude-3-7-sonnet-20250219",
    "api_key": "YOUR_API_KEY",
    "options": {
        "temperature": 0.7,
        "max_tokens": 2000,
    }
}

try:
    validated_config = validate_provider_config(config)
    # Use validated config...
except ProviderValidationError as e:
    print(f"Validation error: {e}")
```

### Using Provider-Specific Validators

```python
from atlas.providers.validators import AnthropicValidator, OpenAIValidator, OllamaValidator

class AnthropicProvider:
    # Validate initialization parameters
    @AnthropicValidator.validate_init
    def __init__(self, model_name: str, api_key: str, **kwargs):
        # Init is validated
        ...
    
    # Validate generate parameters and response
    @AnthropicValidator.validate_generate
    def generate(self, request: ModelRequest) -> ModelResponse:
        # Request is validated
        ...
        return response  # Response is validated
```

## Example

See `examples/17_provider_validation.py` for a complete example of provider validation.