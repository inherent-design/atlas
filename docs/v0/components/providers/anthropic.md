---

title: Anthropic Provider

---


# Anthropic Provider

This document details the Anthropic provider implementation in Atlas, which integrates with Anthropic's Claude language models.

## Overview

The `AnthropicProvider` class in `atlas.providers.anthropic` implements the `ModelProvider` interface to provide access to Anthropic's Claude models. This provider enables Atlas to use state-of-the-art Claude models for knowledge-augmented generation.

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
| `claude-3-5-haiku-20240620`  | New efficient Haiku model            | Faster responses with good quality      |
| `claude-3-opus-20240229`     | Highest capability Claude model      | Complex reasoning and generation        |
| `claude-3-sonnet-20240229`   | Older Sonnet model                   | Legacy support                          |
| `claude-3-haiku-20240307`    | Original Haiku model                 | Legacy fast responses                   |

## Initialization

The Anthropic provider can be initialized with various configuration options:

```python
from atlas.providers.anthropic import AnthropicProvider

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
from atlas.providers.anthropic import AnthropicProvider
from atlas.providers.base import ModelRequest

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
from atlas.providers.anthropic import AnthropicProvider
from atlas.providers.base import ModelRequest

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

### Model Selection

You can easily switch between different Claude models based on performance needs and cost considerations:

```python
from atlas.providers.anthropic import AnthropicProvider
from atlas.providers.base import ModelRequest

# For high-performance tasks
opus_provider = AnthropicProvider(model_name="claude-3-opus-20240229")

# For balanced performance and cost
sonnet_provider = AnthropicProvider(model_name="claude-3-7-sonnet-20250219")  # default

# For cost-effective, faster responses
haiku_provider = AnthropicProvider(model_name="claude-3-5-haiku-20240620")

# Create a request
request = ModelRequest(
    messages=[
        {"role": "user", "content": "Summarize the key benefits of knowledge graphs in 3 bullet points"}
    ],
    system_prompt="You are a helpful AI assistant specialized in concise responses."
)

# Get a fast response with the Haiku model
response = haiku_provider.generate(request)
print(f"Claude 3.5 Haiku response:\n{response.content}")
print(f"Cost: ${response.cost_estimate.total_cost:.6f}")
```

### Cost Estimation

The provider includes built-in cost estimation based on current Anthropic pricing:

```python
from atlas.providers.anthropic import AnthropicProvider
from atlas.providers.base import TokenUsage

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
- Claude 3.5 Sonnet: $3.00/M input tokens, $15.00/M output tokens
- Claude 3.5 Haiku: $0.80/M input tokens, $4.00/M output tokens
- Claude 3 Opus: $15.00/M input tokens, $75.00/M output tokens
- Claude 3 Haiku: $0.25/M input tokens, $1.25/M output tokens

### Error Handling

The provider implements robust error handling using Atlas's error system:

```python
from atlas.providers.anthropic import AnthropicProvider
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

## Troubleshooting

### Token Usage and Cost Tracking Issues

If you encounter issues with token usage tracking or cost estimation, check the following:

1. **Empty or Zero Token Counts**
   - Verify the response object contains the expected attributes
   - Check for proper API key access (incorrect keys may return mock responses)
   - Ensure you're using the correct model name in your request

   ```python
   # Verify token usage is properly populated
   response = provider.generate(request)
   if response.usage and response.usage.total_tokens > 0:
       print(f"Token tracking is working correctly: {response.usage}")
   else:
       print("Problem with token tracking!")
   ```

2. **Inaccurate Cost Estimates**
   - Confirm the provider is using the correct pricing tier for your model
   - Check that the model name matches exactly with one of the pricing entries
   - Update your code if pricing has changed since your last update

   ```python
   # Check which pricing tier is being used
   import inspect
   print(provider.PRICING.get(provider.model_name, provider.PRICING["default"]))
   ```

3. **Streaming Token Issues**
   - Streaming may show partial token counts during generation
   - Final token counts are only available after the entire response is complete
   - Use the stream_with_callback method to get the final response with token information

   ```python
   # Track streaming token usage
   tokens_so_far = 0

   def token_tracking_callback(delta, response):
       nonlocal tokens_so_far
       print(delta, end="", flush=True)

       # Check if token info has been updated
       if hasattr(response, "usage") and response.usage:
           if tokens_so_far != response.usage.output_tokens:
               tokens_so_far = response.usage.output_tokens
               print(f"\n[Generated {tokens_so_far} tokens so far]", end="\r")

   final_response = provider.stream_with_callback(request, token_tracking_callback)
   print(f"\nFinal tokens: {final_response.usage.total_tokens}")
   print(f"Final cost: ${final_response.cost.total_cost:.6f}")
   ```

4. **Mock Mode Considerations**
   - When `SKIP_API_KEY_CHECK=true`, token counts are simulated
   - Mock responses use fixed token counts (usually 10 input, 20 output)
   - For accurate testing, use real API keys in a controlled environment

### Common Error Messages

| Error                                            | Cause                                    | Solution                                                  |
| ------------------------------------------------ | ---------------------------------------- | --------------------------------------------------------- |
| `AnthropicProvider requires the Anthropic SDK`   | The 'anthropic' package is not installed | Run `uv add anthropic` to install                         |
| `Anthropic API key not provided`                 | Missing API key                          | Set `ANTHROPIC_API_KEY` environment variable              |
| `Authentication error calling Anthropic API`     | Invalid API key                          | Check key format and validity                             |
| `Rate limit exceeded calling Anthropic API`      | Too many requests                        | Implement exponential backoff or reduce request frequency |
| `Failed to generate response from Anthropic API` | General API error                        | Check Anthropic service status and request parameters     |

## Related Documentation

- [Providers Overview](./index.md) - Overview of all providers
- [OpenAI Provider](./openai.md) - Documentation for the OpenAI provider
- [Ollama Provider](./ollama.md) - Documentation for the Ollama provider
- [Streaming Example](https://github.com/inherent-design/atlas/blob/main/examples/02_query_streaming.py) - Example of using streaming with Anthropic
