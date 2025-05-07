# Mock Provider

The Mock Provider is a specialized provider implementation designed for testing and development without requiring actual API access. It simulates the behavior of real model providers (like Anthropic, OpenAI, and Ollama) by generating synthetic responses.

## Overview

The Mock Provider offers several benefits:

- **API-Free Testing**: Run tests without requiring API keys or incurring costs
- **Deterministic Testing**: Create predictable test cases with simulated responses
- **Error Simulation**: Test error handling by configuring the provider to throw specific errors
- **Performance Testing**: Simulate different response times with configurable delays
- **Cost Estimation**: Demonstrate cost calculation functionality without real API charges

## Implementation

The Mock Provider implements the same interfaces as other model providers in Atlas, ensuring full compatibility with all Atlas features:

- Standard generation with `generate()`
- Streaming with both `stream()` and `stream_with_callback()`
- Token usage and cost calculation
- Error handling and retry logic

## Configuration

### Basic Usage

```python
from atlas.models.factory import create_provider

# Create a mock provider
provider = create_provider(
    provider_name="mock",
    model_name="mock-standard"  # Options: mock-basic, mock-standard, mock-advanced
)

# Use like any other provider
response = provider.generate(request)
```

### Advanced Configuration

The Mock Provider supports several configuration options:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model_name` | str | Mock model to use (mock-basic, mock-standard, mock-advanced) | "mock-standard" |
| `max_tokens` | int | Maximum tokens for generation | 2000 |
| `delay_ms` | int | Simulated latency in milliseconds | 100 |
| `simulate_errors` | bool | Whether to simulate API errors | False |
| `error_type` | str | Type of error to simulate (api, authentication, validation) | "api" |

Example with advanced configuration:

```python
from atlas.models.factory import create_provider

# Create a mock provider with custom settings
provider = create_provider(
    provider_name="mock",
    model_name="mock-advanced",
    max_tokens=1000,
    delay_ms=200,  # 200ms simulated latency
    simulate_errors=False
)
```

## Testing with Errors

The Mock Provider can simulate various error conditions, which is useful for testing error handling:

```python
from atlas.models.factory import create_provider

# Create a provider that will throw authentication errors
auth_error_provider = create_provider(
    provider_name="mock",
    simulate_errors=True,
    error_type="authentication"
)

# Create a provider that will throw validation errors
validation_error_provider = create_provider(
    provider_name="mock",
    simulate_errors=True,
    error_type="validation"
)

# Create a provider that will throw general API errors
api_error_provider = create_provider(
    provider_name="mock",
    simulate_errors=True,
    error_type="api"
)
```

## Mock Models

The Mock Provider offers three different mock models with varying characteristics:

| Model | Description |
|-------|-------------|
| `mock-basic` | Simulates a basic model with low cost ($0.50/M input, $1.50/M output) |
| `mock-standard` | Simulates a standard model with moderate cost ($3.00/M input, $15.00/M output) |
| `mock-advanced` | Simulates an advanced model with high cost ($10.00/M input, $30.00/M output) |

## Implementation Details

### Response Generation

The Mock Provider generates responses by:

1. Taking a user message from the request
2. Creating a synthetic response that refers to the user's query
3. Simulating appropriate token counts for the response
4. Calculating estimated costs based on simulated token usage

### Streaming Simulation

When streaming, the Mock Provider:

1. Breaks the response into word-level chunks
2. Delivers each chunk with a configurable delay
3. Updates token counts and costs incrementally
4. Provides a final response with complete metadata when finished

## Use Cases

The Mock Provider is particularly useful for:

1. **Test Suites**: Creating comprehensive test coverage without API dependencies
2. **CI/CD Pipelines**: Running automated tests in continuous integration environments
3. **Local Development**: Developing new features without requiring API keys
4. **Demos and Examples**: Creating demonstration examples that work without setup
5. **Performance Testing**: Testing application behavior with different response times

## Example

```python
from atlas.models.factory import create_provider
from atlas.models.base import ModelRequest, Message, Role

# Create a mock provider
provider = create_provider(
    provider_name="mock",
    model_name="mock-standard"
)

# Create a request
request = ModelRequest(
    messages=[
        Message(role=Role.SYSTEM, content="You are a helpful assistant."),
        Message(role=Role.USER, content="Tell me about Atlas.")
    ],
    max_tokens=500
)

# Generate a response
response = provider.generate(request)

print(f"Response: {response.content}")
print(f"Tokens: {response.usage}")
print(f"Cost: ${response.cost.total_cost:.6f}")
```