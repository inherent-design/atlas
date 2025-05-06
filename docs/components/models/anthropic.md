# Anthropic Provider

This document details the Anthropic provider implementation in Atlas, which integrates with Anthropic's Claude language models.

## Overview

The `AnthropicProvider` class in `atlas.models.anthropic` implements the `ModelProvider` interface to provide access to Anthropic's Claude models. This provider enables Atlas to use state-of-the-art Claude models for knowledge-augmented generation.

```mermaid
classDiagram
    ModelProvider <|-- AnthropicProvider
    AnthropicProvider --> "anthropic.Anthropic" : uses

    class ModelProvider {
        <<interface>>
        +validate_api_key()
        +generate()
        +generate_streaming()
        +process_messages()
        +get_cost_estimate()
    }

    class AnthropicProvider {
        -_model_name
        -_max_tokens
        -_api_key
        -_client
        +generate()
        +generate_streaming()
        +process_messages()
        +get_cost_estimate()
    }
```

## Key Features

The Anthropic provider offers the following key features:

1. **Full Claude API Access**: Supports all Claude models, including Claude 3.5 Sonnet, Claude 3.7 Sonnet, Claude 3 Opus, and Claude 3 Haiku
2. **Streaming Support**: Native streaming for interactive UI experiences
3. **Cost Tracking**: Built-in token usage tracking and cost estimation
4. **Error Handling**: Robust error handling with detailed error messages
5. **Telemetry Integration**: Performance monitoring via Atlas's telemetry system

## Supported Models

The provider supports the following Anthropic Claude models:

| Model                        | Description                          | Use Case                                |
| ---------------------------- | ------------------------------------ | --------------------------------------- |
| `claude-3-7-sonnet-20250219` | Latest Claude Sonnet model (default) | Best balance of quality and performance |
| `claude-3-5-sonnet-20240620` | High-quality general-purpose model   | General tasks with good performance     |
| `claude-3-opus-20240229`     | Highest capability Claude model      | Complex reasoning and generation        |
| `claude-3-sonnet-20240229`   | Older Sonnet model                   | Legacy support                          |
| `claude-3-haiku-20240307`    | Fastest, most efficient Claude model | Fast responses, simpler tasks           |

## Initialization

The Anthropic provider can be initialized with various configuration options:

```python
from atlas.models.anthropic import AnthropicProvider

# Default initialization
provider = AnthropicProvider()

# Custom configuration
provider = AnthropicProvider(
    model_name="claude-3-opus-20240229",
    max_tokens=4000,
    api_key="your_api_key_here"  # Optional: defaults to ANTHROPIC_API_KEY env var
)
```

### Required Dependencies

The provider requires the Anthropic Python SDK:

```bash
uv add anthropic
```

## Basic Usage

### Generating Text

```python
from atlas.models.anthropic import AnthropicProvider
from atlas.models.base import ModelRequest

# Create provider
provider = AnthropicProvider()

# Create request
request = ModelRequest(
    messages=[
        {"role": "user", "content": "Explain the concept of knowledge graphs"}
    ],
    system_prompt="You are a helpful AI assistant."
)

# Generate response
response = provider.generate(request)

# Print response
print(response.response_message)

# Check token usage
print(f"Input tokens: {response.token_usage.input_tokens}")
print(f"Output tokens: {response.token_usage.output_tokens}")
print(f"Estimated cost: ${response.cost_estimate.total_cost:.6f}")
```

### Streaming Generation

```python
from atlas.models.anthropic import AnthropicProvider
from atlas.models.base import ModelRequest

# Create provider
provider = AnthropicProvider()

# Create request
request = ModelRequest(
    messages=[
        {"role": "user", "content": "Write a short story about an AI assistant"}
    ],
    system_prompt="You are a creative writing assistant."
)

# Define callback function
def print_streaming(chunk: str, full_text: str) -> None:
    """Print streaming output character by character."""
    print(chunk, end="", flush=True)

# Generate streaming response
for chunk in provider.generate_streaming(request, print_streaming):
    pass  # Processing happens in the callback

print("\nStreaming completed")
```

## Advanced Features

### Cost Estimation

The provider includes built-in cost estimation based on current Anthropic pricing:

```python
from atlas.models.anthropic import AnthropicProvider
from atlas.models.base import TokenUsage

# Create provider
provider = AnthropicProvider(model_name="claude-3-opus-20240229")

# Calculate cost estimate
usage = TokenUsage(input_tokens=1000, output_tokens=500)
cost = provider.get_cost_estimate(usage)

print(f"Input cost: ${cost.input_cost:.4f}")
print(f"Output cost: ${cost.output_cost:.4f}")
print(f"Total cost: ${cost.total_cost:.4f}")
```

Current pricing (as of 2025):
- Claude 3.7 Sonnet: $3.00/M input tokens, $15.00/M output tokens
- Claude 3 Opus: $15.00/M input tokens, $75.00/M output tokens
- Claude 3 Haiku: $0.25/M input tokens, $1.25/M output tokens

### Error Handling

The provider implements robust error handling using Atlas's error system:

```python
from atlas.models.anthropic import AnthropicProvider
from atlas.core.errors import APIError, AuthenticationError

try:
    # Initialize with invalid API key
    provider = AnthropicProvider(api_key="invalid_key")

    # Try to validate the key
    provider.validate_api_key()
except AuthenticationError as e:
    print(f"Authentication error: {e}")
except APIError as e:
    print(f"API error: {e}")
```

### Configuration via Environment Variables

The provider respects several environment variables:

| Variable                        | Description             | Default                      |
| ------------------------------- | ----------------------- | ---------------------------- |
| `ANTHROPIC_API_KEY`             | API key for Anthropic   | None (required)              |
| `SKIP_API_KEY_CHECK`            | Skip API key validation | `false`                      |
| `ATLAS_ANTHROPIC_DEFAULT_MODEL` | Default model to use    | `claude-3-7-sonnet-20250219` |

Example `.env` configuration:
```
ANTHROPIC_API_KEY=your_api_key_here
ATLAS_ANTHROPIC_DEFAULT_MODEL=claude-3-opus-20240229
```

## Implementation Details

### Interface Implementation

The Anthropic provider implements the `ModelProvider` interface:

```python
class AnthropicProvider(ModelProvider):
    """Anthropic Claude model provider."""

    def validate_api_key(self) -> bool:
        """Validate that the API key is set and valid."""
        # Implementation details...

    def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response for the given request."""
        # Implementation details...

    def generate_streaming(
        self, request: ModelRequest, callback: StreamingCallback
    ) -> Iterator[str]:
        """Generate a streaming response for the given request."""
        # Implementation details...

    def process_messages(
        self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None
    ) -> str:
        """Process a list of messages to generate a response."""
        # Implementation details...

    def get_cost_estimate(self, usage: TokenUsage) -> CostEstimate:
        """Get the cost estimate for the given token usage."""
        # Implementation details...
```

### Message Format

The Anthropic provider uses the Anthropic Messages API format:

```python
messages = [
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "assistant", "content": "I'm doing well, thanks for asking!"},
    {"role": "user", "content": "Tell me about knowledge graphs"}
]

system_prompt = "You are a helpful AI assistant specialized in knowledge graphs."
```

### Telemetry Integration

The provider integrates with Atlas's telemetry system for performance monitoring:

```python
@traced
def generate(self, request: ModelRequest) -> ModelResponse:
    """Generate a response for the given request."""
    # Implementation with telemetry tracing
```

## Related Documentation

- [Models Overview](./) - Overview of all model providers
- [OpenAI Provider](./openai.md) - Documentation for the OpenAI provider
- [Ollama Provider](./ollama.md) - Documentation for the Ollama provider
- [Environment Variables](../../reference/env_variables.md) - Configuration options
