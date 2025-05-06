# Atlas Models Module

This document provides an overview of the Atlas models module, which provides a unified interface for interacting with different language model providers.

## Overview

The models module (`atlas.models`) provides a standardized way to interact with different language model providers, including Anthropic, OpenAI, and Ollama. It abstracts away the provider-specific details and presents a consistent API for the rest of the framework.

## Core Components

### Base Interfaces

The base interfaces are defined in `atlas.models.base`:

- `ModelProvider`: Abstract base class for model providers
- `ModelRequest`: Request to generate content from a model
- `ModelResponse`: Response from a language model
- `ModelMessage`: A message in a conversation with a model
- `MessageContent`: Content of a message in the conversation
- `ModelRole`: Roles in a conversation with a model (system, user, assistant, function)
- `TokenUsage`: Token usage statistics for a model response
- `CostEstimate`: Cost estimate for a model response

### Factory Functions

The factory functions are provided by `atlas.models.factory`:

- `discover_providers()`: Discover available model providers
- `create_provider()`: Create a model provider instance
- `get_all_providers()`: Create instances of all available providers
- `register_provider()`: Register a new provider implementation
- `set_default_model()`: Set the default model for a provider
- `ProviderFactory`: Factory class for creating and managing model providers

### Provider Implementations

The module includes implementations for several providers:

- `AnthropicProvider`: Provider for Anthropic's Claude models
- `OpenAIProvider`: Provider for OpenAI's GPT models
- `OllamaProvider`: Provider for Ollama's local models

## Usage

### Basic Usage

```python
from atlas.models import create_provider, ModelRequest, ModelMessage

# Create a provider
provider = create_provider("anthropic")

# Create a request
request = ModelRequest(
    messages=[
        ModelMessage.system("You are a helpful assistant."),
        ModelMessage.user("Hello, how are you?")
    ],
    max_tokens=100
)

# Generate a response
response = provider.generate(request)

# Access the response content
print(response.content)

# Get token usage and cost
print(f"Token usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output")
print(f"Cost: {response.cost}")
```

### Provider Discovery

```python
from atlas.models import discover_providers

# Discover available providers
providers = discover_providers()
print(f"Available providers: {providers}")

# Check if a specific provider is available
if "anthropic" in providers:
    print(f"Anthropic models: {providers['anthropic']}")
```

### Creating Multiple Providers

```python
from atlas.models import get_all_providers

# Create instances of all available providers
providers = get_all_providers()

# Use a specific provider
if "openai" in providers:
    openai_provider = providers["openai"]
    response = openai_provider.generate(request)
    print(f"OpenAI response: {response.content}")
```

### Using Factory Class

```python
from atlas.models import ProviderFactory

# Create a factory
factory = ProviderFactory()

# Discover available providers
available = factory.discover()
print(f"Available providers: {available}")

# Create a provider
provider = factory.create("anthropic")

# Get a provider (creates if not already created)
provider = factory.get("anthropic")

# Set default provider
factory.set_default("anthropic")

# Get default provider
provider = factory.get()
```

## Provider-Specific Features

### Anthropic Provider

```python
from atlas.models import create_provider

# Create Anthropic provider with specific configuration
provider = create_provider(
    provider_name="anthropic",
    model_name="claude-3-7-sonnet-20250219",
    max_tokens=2000
)

# Check available models
models = provider.get_available_models()
print(f"Available Anthropic models: {models}")

# Validate API key
is_valid = provider.validate_api_key()
print(f"API key is valid: {is_valid}")
```

### OpenAI Provider

```python
from atlas.models import create_provider

# Create OpenAI provider with organization
provider = create_provider(
    provider_name="openai",
    model_name="gpt-4o",
    organization="your-organization-id"
)

# List available models
models = provider.get_available_models()
print(f"Available OpenAI models: {models}")
```

### Ollama Provider

```python
from atlas.models import create_provider

# Create Ollama provider with custom endpoint
provider = create_provider(
    provider_name="ollama",
    model_name="llama3",
    api_endpoint="http://localhost:11434/api"
)

# Check if Ollama is running
is_valid = provider.validate_api_key()
print(f"Ollama is running: {is_valid}")
```

## Advanced Features

### Cost Estimation

The models module includes built-in cost estimation based on token usage:

```python
from atlas.models import create_provider, ModelRequest, ModelMessage

provider = create_provider("anthropic")
request = ModelRequest(
    messages=[ModelMessage.user("Hello, world!")],
    max_tokens=100
)
response = provider.generate(request)

# Access cost information
input_cost = response.cost.input_cost
output_cost = response.cost.output_cost
total_cost = response.cost.total_cost

print(f"Total cost: ${total_cost:.6f}")
```

### Streaming Support

Some providers support streaming responses:

```python
from atlas.models import create_provider, ModelRequest, ModelMessage

provider = create_provider("anthropic")
request = ModelRequest(
    messages=[ModelMessage.user("Tell me a story")],
    max_tokens=500
)

# Get the response and stream
response, stream = provider.stream(request)

# Process the stream (implementation depends on provider)
for chunk in stream:
    # Process each chunk
    print(chunk.content[0].text, end="", flush=True)
```

## Integration with Environment Module

The models module should be updated to use the environment module for accessing environment variables:

```python
from atlas.core import env
from atlas.models import create_provider

# Check if API key is available
if env.has_api_key("anthropic"):
    # Create provider
    provider = create_provider("anthropic")
    # Use provider
    # ...
```

## Testing

The models module includes basic tests in `scripts/testing/test_new_modules.py`. Additional tests should be added to ensure robust functionality:

- Unit tests for each provider implementation
- Mock tests to run without actual API keys
- Tests for streaming functionality
- Error handling tests
- Performance benchmarks

## Current Status and Roadmap

The models module is in active development with the following status:

1. **Completed**:
   - ✅ Base provider interface with standardized types
   - ✅ Factory pattern with registration mechanism
   - ✅ Environment variable integration via the env module
   - ✅ Streaming implementation for Anthropic provider
   - ✅ API key validation mechanisms

2. **In Progress**:
   - 🚧 Streaming implementation for OpenAI provider
   - 🚧 Streaming implementation for Ollama provider
   - 🚧 Comprehensive testing for all providers

3. **Planned**:
   - ⏱️ Mock provider implementation for testing without API keys
   - ⏱️ Connection pooling for improved performance
   - ⏱️ Health check mechanisms for provider status
   - ⏱️ Advanced error handling with retries
   - ⏱️ Cost optimization strategies

## Best Practices

When working with the models module:

1. **Provider Selection**:
   - Use `discover_providers()` to dynamically find available providers
   - Fall back to alternative providers when preferred ones are unavailable
   - Document provider-specific requirements in your code

2. **Error Handling**:
   - Handle provider-specific exceptions appropriately
   - Implement retry logic for transient errors
   - Provide fallback behavior when providers are unavailable

3. **Cost Management**:
   - Monitor token usage and costs in your application
   - Set appropriate `max_tokens` to limit response size
   - Consider using cheaper models for non-critical tasks

4. **Configuration**:
   - Store API keys in environment variables, not in code
   - Use the env module to access environment variables
   - Provide sensible defaults for optional parameters