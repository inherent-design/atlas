---
title: Code Examples
---

# Code Examples Standards

Effective code examples are essential for helping users understand and implement Atlas functionality. This guide outlines the standards for creating clear, instructive code examples throughout the documentation.

## Core Principles

1. **Completeness**: Examples should be complete and runnable
2. **Clarity**: Code should be easy to understand with appropriate comments
3. **Conciseness**: Examples should be as short as possible while demonstrating the concept
4. **Correctness**: All examples must work with the current version of Atlas
5. **Consistency**: Maintain consistent style across all examples

## Example Structure

### Basic Structure

Code examples should follow this general structure:

1. **Imports**: Include all necessary imports
2. **Setup**: Any required initialization or configuration
3. **Core Example**: The main functionality being demonstrated
4. **Output**: Expected output, when helpful (as comments)

### Example Template

```python
# Import necessary modules
from atlas.providers import AnthropicProvider
from atlas.query import query_with_retrieval

# Setup configuration
provider = AnthropicProvider(model_name="claude-3-7-sonnet-20250219")

# Core example functionality
response = query_with_retrieval(
    query="How does the provider system work?",
    provider=provider,
    collection_name="atlas_docs"
)

# Output handling
print(response)
# Expected output:
# "The provider system is responsible for..."
```

## Complexity Progression

### Multiple Complexity Levels

When documenting features, provide examples with increasing complexity:

1. **Basic Example**: Minimal implementation showing core functionality
2. **Intermediate Example**: Shows common customization options
3. **Advanced Example**: Demonstrates complex use cases or integrations

### Example of Complexity Progression

```python
# Basic example
from atlas.providers import AnthropicProvider

provider = AnthropicProvider()
response = provider.generate("What is Atlas?")
```

```python
# Intermediate example
from atlas.providers import AnthropicProvider

provider = AnthropicProvider(
    model_name="claude-3-7-sonnet-20250219",
    max_tokens=1000
)
response = provider.generate(
    "Explain the Atlas framework architecture",
    temperature=0.7
)
```

```python
# Advanced example
from atlas.providers import AnthropicProvider, OpenAIProvider
from atlas.providers.group import ProviderGroup
from atlas.providers.capabilities import CapabilityStrength

# Create provider group with multiple models
provider_group = ProviderGroup(
    providers=[
        AnthropicProvider(model_name="claude-3-7-sonnet-20250219"),
        OpenAIProvider(model_name="gpt-4-turbo")
    ],
    selection_strategy="failover"
)

# Query with specific capability requirements
response = provider_group.generate(
    "Analyze this code for security vulnerabilities...",
    capabilities={
        "code": CapabilityStrength.STRONG,
        "security": CapabilityStrength.MODERATE
    }
)
```

## Commenting Standards

### Required Comments

Include comments for:

1. **Setup Explanation**: Explain initialization steps and configuration
2. **Complex Operations**: Clarify any non-obvious code
3. **Expected Results**: Show what output to expect (when not self-evident)
4. **Key Concepts**: Highlight important concepts or patterns

### Comment Style

Use these comment styles:

- **Inline Comments**: For brief clarifications of specific lines
- **Block Comments**: For explaining sections or concepts
- **Docstring Style**: For example function or class documentation

### Example with Proper Comments

```python
from atlas.agents import ControllerAgent, WorkerAgent
from atlas.providers import AnthropicProvider

# Create providers for different agent roles
# The controller needs strong reasoning capabilities
controller_provider = AnthropicProvider(model_name="claude-3-7-sonnet-20250219")

# Workers can use more specialized or efficient models
worker_provider = AnthropicProvider(model_name="claude-3-haiku-20250125")

# Initialize the controller agent
controller = ControllerAgent(
    name="research_controller",
    provider=controller_provider,
    system_prompt_file="prompts/research_controller.txt"  # Custom prompt for research tasks
)

# Create specialized worker agents for different research subtasks
workers = [
    WorkerAgent(
        name="information_gatherer",
        provider=worker_provider,
        system_prompt_file="prompts/information_gatherer.txt"
    ),
    WorkerAgent(
        name="fact_checker",
        provider=worker_provider,
        system_prompt_file="prompts/fact_checker.txt"
    )
]

# Register workers with the controller
for worker in workers:
    controller.register_worker(worker)

# Process a research query with the multi-agent system
# This will distribute subtasks to appropriate workers
result = controller.process_task("Research the environmental impact of LLMs")

# The result contains the consolidated findings from all workers
print(result)
```

## Code Style

### Formatting Guidelines

1. **Line Length**: Keep lines under 88 characters
2. **Indentation**: Use 4 spaces for indentation
3. **Whitespace**: Include whitespace for readability
4. **Variable Names**: Use descriptive variable names

### Naming Conventions

Follow these naming conventions:

- **Variables**: Use descriptive `snake_case` names
- **Classes**: Use `PascalCase` for class names
- **Constants**: Use `UPPER_SNAKE_CASE` for constants
- **Functions**: Use descriptive `snake_case` verbs

### Style Example

```python
# Good example
from atlas.knowledge import EmbeddingStrategy, ChunkingStrategy
from atlas.knowledge.ingest import ingest_directory

# Configuration constants
MAX_CHUNK_SIZE = 1000
OVERLAP_SIZE = 200

# Initialize with descriptive variable names
semantic_chunker = ChunkingStrategy(
    method="semantic",
    max_chunk_size=MAX_CHUNK_SIZE,
    overlap_size=OVERLAP_SIZE
)

embedding_strategy = EmbeddingStrategy(
    model_name="text-embedding-3-large",
    dimensions=1536
)

# Function with clear parameters
ingest_result = ingest_directory(
    directory_path="/path/to/docs",
    collection_name="atlas_documentation",
    chunking_strategy=semantic_chunker,
    embedding_strategy=embedding_strategy,
    file_types=[".md", ".txt"]
)
```

## Code Groups

Code groups allow you to present alternative implementations or language versions of the same functionality. They are especially useful when showing code snippets with logical branches or variants.

### Basic Code Group Format

Use the following format to create code groups:

````md
::: code-group

```js [config.js]
/**
 * @type {import('vitepress').UserConfig}
 */
const config = {
  // ...
}

export default config
```

```ts [config.ts]
import type { UserConfig } from 'vitepress'

const config: UserConfig = {
  // ...
}

export default config
```

:::
````

This produces a tabbed interface where users can switch between implementations.

### When to Use Code Groups

Code groups should be used when:

1. **Multiple Implementations**: You need to show the same functionality in different languages or frameworks
2. **Alternative Approaches**: There are multiple valid ways to accomplish a task
3. **Configuration Variations**: Different configuration options for the same component
4. **Environment Differences**: Code variations for different environments (development, production)

### Example: Provider Selection Strategies

::: code-group

```python [Failover Strategy]
from atlas.providers import AnthropicProvider, OpenAIProvider
from atlas.providers.group import ProviderGroup

# Create a provider group with failover strategy
provider_group = ProviderGroup(
    providers=[
        AnthropicProvider(model_name="claude-3-7-sonnet-20250219"),
        OpenAIProvider(model_name="gpt-4-turbo")
    ],
    selection_strategy="failover"  # Try providers in order until success
)

response = provider_group.generate("Explain quantum computing")
```

```python [Load Balancing]
from atlas.providers import AnthropicProvider, OpenAIProvider
from atlas.providers.group import ProviderGroup

# Create a provider group with load balancing
provider_group = ProviderGroup(
    providers=[
        AnthropicProvider(model_name="claude-3-7-sonnet-20250219"),
        OpenAIProvider(model_name="gpt-4-turbo")
    ],
    selection_strategy="load_balancing",  # Distribute requests across providers
    weights=[0.7, 0.3]  # 70% to Anthropic, 30% to OpenAI
)

response = provider_group.generate("Explain quantum computing")
```

```python [Capability-Based]
from atlas.providers import AnthropicProvider, OpenAIProvider
from atlas.providers.group import ProviderGroup
from atlas.providers.capabilities import CapabilityStrength

# Create a provider group with capability-based selection
provider_group = ProviderGroup(
    providers=[
        AnthropicProvider(model_name="claude-3-7-sonnet-20250219"),
        OpenAIProvider(model_name="gpt-4-turbo")
    ],
    selection_strategy="capability_based"  # Select based on task requirements
)

# Provider with best math capabilities will be selected
response = provider_group.generate(
    "Calculate the integral of x²sin(x)",
    capabilities={"math": CapabilityStrength.STRONG}
)
```

:::

## Special Examples

### Error Handling

Include examples of error handling for important functionality:

```python
from atlas.providers import AnthropicProvider
from atlas.core.errors import ProviderAuthenticationError, ProviderQuotaError

provider = AnthropicProvider()

try:
    response = provider.generate("What is Atlas?")
    print(response)
except ProviderAuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Implement authentication retry or fallback
except ProviderQuotaError as e:
    print(f"API quota exceeded: {e}")
    # Implement rate limiting or fallback
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
```

### Asynchronous Code

For asynchronous functionality, include both synchronous and async versions:

```python
# Synchronous version
from atlas.providers import AnthropicProvider

provider = AnthropicProvider()
response = provider.generate("What is Atlas?")
print(response)
```

```python
# Asynchronous version
import asyncio
from atlas.providers import AnthropicProvider

async def generate_async():
    provider = AnthropicProvider()
    response = await provider.generate_async("What is Atlas?")
    print(response)

asyncio.run(generate_async())
```

### Configuration Examples

For configurable components, show multiple configuration options:

```python
from atlas.core.config import AtlasConfig

# Minimal configuration
config = AtlasConfig()

# Environment variable configuration
config = AtlasConfig.from_env()

# File-based configuration
config = AtlasConfig.from_file("atlas_config.yaml")

# Detailed configuration with multiple options
config = AtlasConfig(
    default_provider="anthropic",
    default_model="claude-3-7-sonnet-20250219",
    log_level="INFO",
    telemetry_enabled=True,
    max_tokens=2000,
    database_path="./atlas_data/",
    cache_enabled=True,
    cache_ttl=3600
)
```

## Example Context and Framing

### Contextualizing Examples

For each example, provide:

1. **Purpose**: What the example demonstrates
2. **Use Case**: When to use this pattern
3. **Prerequisites**: What needs to be set up first
4. **Next Steps**: Where to go after understanding this example

### Framing Example

```md
### Streaming Response Example

This example demonstrates how to handle streaming responses from providers,
which is useful for creating real-time user interfaces or processing large
responses incrementally.

**Prerequisites**:
- Atlas installed
- Provider API keys configured

```python
from atlas.providers import AnthropicProvider

# Initialize provider with streaming enabled
provider = AnthropicProvider(
    model_name="claude-3-7-sonnet-20250219"
)

# Define a callback function to process each chunk
def process_chunk(chunk):
    print(f"Received chunk: {chunk}", end="", flush=True)

# Generate a streaming response
full_response = provider.generate_streaming(
    "Explain the benefits of streaming LLM responses",
    callback=process_chunk
)

# The full_response contains the complete text after streaming completes
print("\n\nFull response:", full_response)
```

After implementing streaming, consider adding advanced stream control
features like pause and resume as shown in the [🚧 Enhanced Streaming guide](#).
```

## Common Patterns Library

For frequently used patterns, we maintain a standardized approach:

### Provider Initialization

```python
from atlas.providers import AnthropicProvider

provider = AnthropicProvider(
    model_name="claude-3-7-sonnet-20250219",
    max_tokens=2000
)
```

### Multi-Agent Setup

```python
from atlas.agents import ControllerAgent, WorkerAgent

controller = ControllerAgent(name="main_controller")
workers = [
    WorkerAgent(name="worker_1"),
    WorkerAgent(name="worker_2")
]

for worker in workers:
    controller.register_worker(worker)
```

### Knowledge Retrieval

```python
from atlas.knowledge import retrieve_documents

documents = retrieve_documents(
    query="How does Atlas work?",
    collection_name="atlas_docs",
    limit=5
)
```

## Testing Examples

All code examples in documentation should be tested to ensure they work correctly. We recommend:

1. Extracting examples into runnable files during documentation development
2. Verifying examples work with the latest Atlas version
3. Including examples in documentation tests when possible
4. Updating examples when API changes occur

::: tip Example Verification
Use the `examples/check_docs_examples.py` script to verify that documentation examples are valid and runnable.
:::

## Example Maintenance

To maintain example quality over time:

1. **Version Tagging**: Clearly note which Atlas version examples work with
2. **Deprecation Notices**: Mark deprecated patterns with warning containers
3. **Update Tracking**: Track which examples need updates during API changes
4. **User Feedback**: Update examples based on user confusion or questions

Following these standards will ensure that Atlas documentation contains clear, helpful code examples that guide users effectively through implementation.
