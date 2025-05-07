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

1. **Latest GPT Models**: Supports GPT-4.1, GPT-4o, and specialized models
2. **Streaming Support**: Native streaming for interactive UI experiences
3. **Cost Tracking**: Built-in token usage tracking and cost estimation
4. **Organization Support**: Support for OpenAI organization IDs
5. **Robust Error Handling**: Comprehensive error handling with detailed messages

## Supported Models

The provider supports the following OpenAI models:

### Latest Models (GPT-4.1 Series)

| Model           | Description                   | Use Case                            |
| --------------- | ----------------------------- | ----------------------------------- |
| `gpt-4.1`       | Flagship GPT-4.1 (default)    | Complex reasoning and tasks         |
| `gpt-4.1-mini`  | Smaller GPT-4.1 model         | Balance of cost and performance     |
| `gpt-4.1-nano`  | Smallest GPT-4.1 model        | Fast, cost-effective processing     |

### Reasoning Models (o-Series)

| Model           | Description                   | Use Case                            |
| --------------- | ----------------------------- | ----------------------------------- |
| `o3`            | Advanced reasoning model      | Math, coding, and vision tasks      |
| `o4-mini`       | Cost-efficient reasoning      | Efficient multi-step reasoning      |

### GPT-4o Series

| Model           | Description                   | Use Case                            |
| --------------- | ----------------------------- | ----------------------------------- |
| `gpt-4o`        | GPT-4 omni-capable model      | General-purpose tasks with vision   |
| `gpt-4o-mini`   | Smaller GPT-4o model          | Cost-efficient multi-modal tasks    |

### Legacy Models

| Model           | Description                   | Use Case                            |
| --------------- | ----------------------------- | ----------------------------------- |
| `gpt-4-turbo`   | GPT-4 Turbo model             | High-quality with better throughput |
| `gpt-4`         | Original GPT-4 model          | Legacy support                      |
| `gpt-3.5-turbo` | Efficient GPT-3.5 model       | Fast responses for simpler tasks    |

## Initialization

The OpenAI provider can be initialized with various configuration options:

```python
from atlas.models.openai import OpenAIProvider

# Default initialization
provider = OpenAIProvider()

# Custom configuration
provider = OpenAIProvider(
    model_name="gpt-4.1",  # Using the latest GPT-4.1 model
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
provider = OpenAIProvider(model_name="gpt-4.1")

# Calculate cost estimate
usage = TokenUsage(input_tokens=1000, output_tokens=500)
cost = provider.get_cost_estimate(usage)

print(f"Input cost: ${cost.input_cost:.4f}")
print(f"Output cost: ${cost.output_cost:.4f}")
print(f"Total cost: ${cost.total_cost:.4f}")

# Dictionary representation
cost_dict = cost.to_dict()
print(f"Cost dictionary: {cost_dict}")
```

Current pricing (as of May 2025):

**GPT-4.1 Series:**
- GPT-4.1: $2.00/M input tokens, $8.00/M output tokens
- GPT-4.1-mini: $0.40/M input tokens, $1.60/M output tokens
- GPT-4.1-nano: $0.10/M input tokens, $0.40/M output tokens

**o-Series Reasoning Models:**
- o3: $10.00/M input tokens, $40.00/M output tokens
- o4-mini: $1.10/M input tokens, $4.40/M output tokens

**GPT-4o Series:**
- GPT-4o: $5.00/M input tokens, $20.00/M output tokens
- GPT-4o-mini: $0.60/M input tokens, $2.40/M output tokens

**Legacy Models:**
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
| `ATLAS_OPENAI_DEFAULT_MODEL` | Default model to use       | `gpt-4.1`       |

Example `.env` configuration:
```
OPENAI_API_KEY=your_api_key_here
OPENAI_ORGANIZATION=org-abc123
ATLAS_OPENAI_DEFAULT_MODEL=gpt-4.1-mini # Use smaller model for efficiency
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

### Token Usage and Cost Tracking

The OpenAI provider includes comprehensive token usage tracking and cost estimation:

```python
from atlas.models.openai import OpenAIProvider
from atlas.models.base import ModelRequest, ModelMessage

# Create a provider and request
provider = OpenAIProvider(model_name="gpt-4.1-mini")
request = ModelRequest(
    messages=[ModelMessage.user("Explain token usage tracking")],
    max_tokens=100
)

# Generate a response
response = provider.generate(request)

# Access token usage information
usage = response.usage
print(f"Token usage: {usage.input_tokens} input, {usage.output_tokens} output, {usage.total_tokens} total")
print(f"Token usage dict: {usage.to_dict()}")

# Access cost information
cost = response.cost
print(f"Cost: {cost}")
```

The `TokenUsage` and `CostEstimate` classes provide the following methods:

```python
# TokenUsage methods
token_usage = response.usage
total = token_usage.total_tokens  # Sum of input and output tokens
as_dict = token_usage.to_dict()   # Dictionary representation

# CostEstimate methods
cost = response.cost
total_cost = cost.total_cost      # Sum of input and output costs
as_dict = cost.to_dict()          # Dictionary representation
```

Cost formatting varies based on the magnitude:
- Large costs ($0.01+): Two decimal places
- Small costs ($0.001 to $0.01): Four decimal places
- Very small costs ($0.000001 to $0.001): Six decimal places
- Extremely small costs (< $0.000001): Scientific notation

## Related Documentation

- [Models Overview](./) - Overview of all model providers
- [Anthropic Provider](./anthropic.md) - Documentation for the Anthropic provider
- [Ollama Provider](./ollama.md) - Documentation for the Ollama provider
- [Environment Variables](../../reference/env_variables.md) - Configuration options
- [Streaming Example](../../guides/examples/streaming_example.md) - Streaming with tokens and costs
