# OpenAI Provider

This document details the OpenAI provider implementation in Atlas, which integrates with OpenAI's GPT-4 and GPT-3.5 models.

## Overview

The `OpenAIProvider` class in `atlas.models.openai` implements the `ModelProvider` interface to provide access to OpenAI's advanced language models. This provider enables Atlas to leverage GPT-4 and GPT-3.5 capabilities for knowledge-augmented generation.

```mermaid
classDiagram
    ModelProvider <|-- OpenAIProvider
    OpenAIProvider --> "openai.OpenAI" : uses

    class ModelProvider {
        <<interface>>
        +validate_api_key()
        +generate()
        +generate_streaming()
        +process_messages()
        +get_cost_estimate()
    }

    class OpenAIProvider {
        -_model_name
        -_max_tokens
        -_api_key
        -_organization
        -_client
        +generate()
        +generate_streaming()
        +process_messages()
        +get_cost_estimate()
    }
```

## Key Features

The OpenAI provider offers the following key features:

1. **Latest GPT Models**: Supports GPT-4o, GPT-4-turbo, GPT-4, and GPT-3.5-turbo
2. **Streaming Support**: Native streaming for interactive UI experiences
3. **Cost Tracking**: Built-in token usage tracking and cost estimation
4. **Organization Support**: Support for OpenAI organization IDs
5. **Robust Error Handling**: Comprehensive error handling with detailed messages

## Supported Models

The provider supports the following OpenAI models:

| Model           | Description                  | Use Case                            |
| --------------- | ---------------------------- | ----------------------------------- |
| `gpt-4o`        | Latest GPT-4 model (default) | Best performance for most tasks     |
| `gpt-4-turbo`   | GPT-4 Turbo model            | High-quality with better throughput |
| `gpt-4`         | Original GPT-4 model         | Legacy support                      |
| `gpt-3.5-turbo` | Efficient GPT-3.5 model      | Fast responses for simpler tasks    |

## Initialization

The OpenAI provider can be initialized with various configuration options:

```python
from atlas.models.openai import OpenAIProvider

# Default initialization
provider = OpenAIProvider()

# Custom configuration
provider = OpenAIProvider(
    model_name="gpt-4-turbo",
    max_tokens=4000,
    api_key="your_api_key_here",  # Optional: defaults to OPENAI_API_KEY env var
    organization="your_org_id"     # Optional: defaults to OPENAI_ORGANIZATION env var
)
```

### Required Dependencies

The provider requires the OpenAI Python SDK:

```bash
uv add openai
```

## Basic Usage

### Generating Text

```python
from atlas.models.openai import OpenAIProvider
from atlas.models.base import ModelRequest

# Create provider
provider = OpenAIProvider()

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
from atlas.models.openai import OpenAIProvider
from atlas.models.base import ModelRequest

# Create provider
provider = OpenAIProvider()

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

The provider includes built-in cost estimation based on current OpenAI pricing:

```python
from atlas.models.openai import OpenAIProvider
from atlas.models.base import TokenUsage

# Create provider
provider = OpenAIProvider(model_name="gpt-4o")

# Calculate cost estimate
usage = TokenUsage(input_tokens=1000, output_tokens=500)
cost = provider.get_cost_estimate(usage)

print(f"Input cost: ${cost.input_cost:.4f}")
print(f"Output cost: ${cost.output_cost:.4f}")
print(f"Total cost: ${cost.total_cost:.4f}")
```

Current pricing (as of 2025):
- GPT-4o: $5.00/M input tokens, $15.00/M output tokens
- GPT-4-turbo: $10.00/M input tokens, $30.00/M output tokens
- GPT-4: $30.00/M input tokens, $60.00/M output tokens
- GPT-3.5-turbo: $0.50/M input tokens, $1.50/M output tokens

### Error Handling

The provider implements robust error handling using Atlas's error system:

```python
from atlas.models.openai import OpenAIProvider
from atlas.core.errors import APIError, AuthenticationError

try:
    # Initialize with invalid API key
    provider = OpenAIProvider(api_key="invalid_key")

    # Try to validate the key
    provider.validate_api_key()
except AuthenticationError as e:
    print(f"Authentication error: {e}")
except APIError as e:
    print(f"API error: {e}")
```

### Organization Support

The provider supports OpenAI organizations:

```python
from atlas.models.openai import OpenAIProvider

# Initialize with organization ID
provider = OpenAIProvider(
    api_key="your_api_key",
    organization="org-abc123"
)
```

### Configuration via Environment Variables

The provider respects several environment variables:

| Variable                     | Description                | Default         |
| ---------------------------- | -------------------------- | --------------- |
| `OPENAI_API_KEY`             | API key for OpenAI         | None (required) |
| `OPENAI_ORGANIZATION`        | Organization ID for OpenAI | None (optional) |
| `ATLAS_OPENAI_DEFAULT_MODEL` | Default model to use       | `gpt-4o`        |

Example `.env` configuration:
```
OPENAI_API_KEY=your_api_key_here
OPENAI_ORGANIZATION=org-abc123
ATLAS_OPENAI_DEFAULT_MODEL=gpt-4-turbo
```

## Implementation Details

### Interface Implementation

The OpenAI provider implements the `ModelProvider` interface:

```python
class OpenAIProvider(ModelProvider):
    """OpenAI model provider."""

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

The OpenAI provider uses the OpenAI Chat Completions API format:

```python
messages = [
    {"role": "system", "content": "You are a helpful AI assistant."},
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "assistant", "content": "I'm doing well, thanks for asking!"},
    {"role": "user", "content": "Tell me about knowledge graphs"}
]
```

Note that in Atlas, the system prompt is handled separately from the message history for consistency across providers.

### Model Parameters

The provider supports standard OpenAI parameters:

```python
provider = OpenAIProvider(
    model_name="gpt-4o",
    max_tokens=2000,
    temperature=0.7,  # Controls randomness (0.0 to 1.0)
    top_p=1.0,        # Controls diversity via nucleus sampling
    frequency_penalty=0.0,  # Penalizes repeated tokens
    presence_penalty=0.0    # Penalizes repeated topics
)
```

## Related Documentation

- [Models Overview](./) - Overview of all model providers
- [Anthropic Provider](./anthropic.md) - Documentation for the Anthropic provider
- [Ollama Provider](./ollama.md) - Documentation for the Ollama provider
- [Environment Variables](../../reference/env_variables.md) - Configuration options
