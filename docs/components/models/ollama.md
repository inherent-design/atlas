# Ollama Provider

This document details the Ollama provider implementation in Atlas, which integrates with Ollama for local model inference.

## Overview

The `OllamaProvider` class in `atlas.models.ollama` implements the `ModelProvider` interface to provide access to local language models running on Ollama. This provider enables Atlas to run inference on your own hardware, offering privacy and cost advantages over cloud-based models.

```mermaid
classDiagram
    ModelProvider <|-- OllamaProvider
    OllamaProvider --> "Requests API" : uses

    class ModelProvider {
        <<interface>>
        +validate_api_key()
        +generate()
        +generate_streaming()
        +process_messages()
        +get_cost_estimate()
    }

    class OllamaProvider {
        -_model_name
        -_max_tokens
        -_api_endpoint
        +generate()
        +generate_streaming()
        +process_messages()
        +get_cost_estimate()
    }
```

## Key Features

The Ollama provider offers the following key features:

1. **Local Inference**: Run models on your own hardware
2. **Privacy-Preserving**: All data stays on your machine
3. **Cost-Free Usage**: No per-token charges
4. **Multiple Models**: Support for many open-source models (Llama, Mistral, etc.)
5. **Custom API Endpoint**: Configurable API endpoint for remote Ollama instances

## Supported Models

The provider supports any model available in Ollama, including:

| Model         | Description                     | Use Case                          |
| ------------- | ------------------------------- | --------------------------------- |
| `llama3`      | Meta's Llama 3 models (default) | General-purpose tasks             |
| `mistral`     | Mistral AI's models             | Efficient, high-quality responses |
| `phi`         | Microsoft's Phi models          | Lightweight, efficient models     |
| `nous-hermes` | Nous Research Hermes models     | Instruction-tuned models          |
| `orca-mini`   | Orca mini models                | Smaller, faster models            |

You can use any model that you've pulled into your Ollama installation.

## Initialization

The Ollama provider can be initialized with various configuration options:

```python
from atlas.models.ollama import OllamaProvider

# Default initialization
provider = OllamaProvider()

# Custom configuration
provider = OllamaProvider(
    model_name="llama3",
    max_tokens=4000,
    api_endpoint="http://localhost:11434/api"  # Optional: defaults to this value
)
```

### Required Dependencies

The provider requires the Requests package:

```bash
uv add requests
```

## Basic Usage

### Generating Text

```python
from atlas.models.ollama import OllamaProvider
from atlas.models.base import ModelRequest

# Create provider
provider = OllamaProvider()

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

# Token usage is estimated for Ollama
print(f"Input tokens (estimated): {response.token_usage.input_tokens}")
print(f"Output tokens (estimated): {response.token_usage.output_tokens}")
```

### Streaming Generation

```python
from atlas.models.ollama import OllamaProvider
from atlas.models.base import ModelRequest

# Create provider
provider = OllamaProvider()

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

### Custom API Endpoint

You can configure the provider to connect to a remote Ollama instance:

```python
from atlas.models.ollama import OllamaProvider

# Connect to a remote Ollama instance
provider = OllamaProvider(
    api_endpoint="http://192.168.1.100:11434/api"
)
```

### Model Parameters

The provider supports Ollama-specific parameters:

```python
from atlas.models.ollama import OllamaProvider

# Initialize with Ollama-specific parameters
provider = OllamaProvider(
    model_name="llama3",
    temperature=0.7,      # Controls randomness (0.0 to 1.0)
    top_p=0.9,            # Nucleus sampling parameter
    top_k=40,             # Limits vocabulary to top K options
    repeat_penalty=1.1    # Penalizes token repetition
)
```

### Server Connection Validation

The provider includes validation for the Ollama server connection:

```python
from atlas.models.ollama import OllamaProvider

# Create provider
provider = OllamaProvider()

# Validate server availability
if provider.validate_api_key():  # Note: This validates server connection, not an API key
    print("Ollama server is accessible")
else:
    print("Ollama server is not accessible")
```

### Configuration via Environment Variables

The provider respects several environment variables:

| Variable                     | Description                    | Default                      |
| ---------------------------- | ------------------------------ | ---------------------------- |
| `OLLAMA_API_ENDPOINT`        | URL of the Ollama API endpoint | `http://localhost:11434/api` |
| `ATLAS_OLLAMA_DEFAULT_MODEL` | Default model to use           | `llama3`                     |

Example `.env` configuration:
```
OLLAMA_API_ENDPOINT=http://localhost:11434/api
ATLAS_OLLAMA_DEFAULT_MODEL=mistral
```

## Implementation Details

### Interface Implementation

The Ollama provider implements the `ModelProvider` interface:

```python
class OllamaProvider(ModelProvider):
    """Ollama local model provider."""

    def validate_api_key(self) -> bool:
        """Validate that the API endpoint is accessible."""
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
        # Always returns zero cost for Ollama
        return CostEstimate(input_cost=0.0, output_cost=0.0, total_cost=0.0)
```

### Message Format

The Ollama provider converts the Atlas message format to Ollama's expected format:

```python
# Atlas message format
messages = [
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "assistant", "content": "I'm doing well, thanks for asking!"},
    {"role": "user", "content": "Tell me about knowledge graphs"}
]

# Ollama format
data = {
    "model": "llama3",
    "messages": messages,
    "stream": False,
    "options": {
        "temperature": 0.7,
        "num_predict": 2000  # max_tokens
    }
}
```

### REST API Communication

The provider uses the Requests library to communicate with the Ollama API:

```python
def generate(self, request: ModelRequest) -> ModelResponse:
    """Generate a response for the given request."""
    # Format data for Ollama API
    data = {
        "model": self._model_name,
        "messages": request.messages,
        "stream": False,
        "options": {
            "num_predict": self._max_tokens,
            **self._additional_params
        }
    }

    # Add system prompt if provided
    if request.system_prompt:
        data["system"] = request.system_prompt

    # Make API request
    response = requests.post(
        f"{self._api_endpoint}/chat",
        headers={"Content-Type": "application/json"},
        json=data,
        timeout=60
    )

    # Process response
    # ...
```

## Setup Requirements

To use the Ollama provider, you need to:

1. Install Ollama on your machine from [ollama.com](https://ollama.com/)
2. Pull your desired models:
   ```bash
   ollama pull llama3
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```

## Related Documentation

- [Models Overview](./) - Overview of all model providers
- [Anthropic Provider](./anthropic.md) - Documentation for the Anthropic provider
- [OpenAI Provider](./openai.md) - Documentation for the OpenAI provider
- [Environment Variables](../../reference/env_variables.md) - Configuration options
