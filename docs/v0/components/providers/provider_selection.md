---

title: Provider Selection

---


# Provider Selection Architecture

Atlas provides a sophisticated provider selection architecture that handles auto-detection of providers from model names, capability-based model selection, and a consistent configuration interface across different application entry points.

## ProviderOptions

The core of the provider selection architecture is the `ProviderOptions` class, which encapsulates all parameters used for provider selection, creation, and configuration.

```python
from atlas.providers import ProviderOptions, create_provider_from_options

# Create options with capability-based selection
options = ProviderOptions(
    provider_name="anthropic",
    capability="inexpensive"
)

# Create provider from options
provider = create_provider_from_options(options)
```

### ProviderOptions Fields

| Field           | Type             | Description                                                                 |
| --------------- | ---------------- | --------------------------------------------------------------------------- |
| `provider_name` | `Optional[str]`  | Name of the provider (e.g., "anthropic", "openai", "ollama", "mock")        |
| `model_name`    | `Optional[str]`  | Name of the model to use                                                    |
| `capability`    | `Optional[str]`  | Capability required (e.g., "inexpensive", "efficient", "premium", "vision") |
| `max_tokens`    | `Optional[int]`  | Maximum tokens for model generation                                         |
| `base_url`      | `Optional[str]`  | Base URL for provider API (primarily used for Ollama)                       |
| `extra_params`  | `Dict[str, Any]` | Additional provider-specific parameters                                     |

### Factory Methods

The `ProviderOptions` class includes factory methods for creating options from different sources:

```python
# Create from environment variables
options = ProviderOptions.from_env()

# Convert to/from dictionary
options_dict = options.to_dict()
options = ProviderOptions.from_dict(options_dict)

# Merge options
default_options = ProviderOptions.from_env()
user_options = ProviderOptions(model_name="claude-3-haiku-20240307")
merged_options = default_options.merge(user_options)
```

## Provider Resolution

The provider resolution process automatically fills in missing details in the `ProviderOptions`:

1. **Auto-detect provider** from model name if provider is not specified
2. **Apply environment defaults** for missing values
3. **Handle capability-based model selection** if model is not specified
4. **Validate model/provider compatibility** to ensure the combination works
5. **Apply sensible defaults** for other parameters like max_tokens and base_url

```python
from atlas.providers import resolve_provider_options

# Create incomplete options
options = ProviderOptions(
    model_name="gpt-4o"  # Only specify model, not provider
)

# Resolve options with auto-detection
resolved = resolve_provider_options(options)
print(resolved.provider_name)  # Will be "openai" based on model name detection
```

## Creating Providers from Options

The `create_provider_from_options` function handles the entire process of resolving options and creating a provider instance:

```python
from atlas.providers import create_provider_from_options

# Create provider with auto-detection and resolution
provider = create_provider_from_options(
    ProviderOptions(model_name="claude-3-opus-20240229")
)

# Use the provider directly
response = provider.generate(request)
```

## CLI Integration

The CLI module provides utilities for converting command-line arguments to `ProviderOptions`:

```python
from atlas.cli import create_provider_options_from_args

# Parse command-line arguments
args = parser.parse_args()

# Convert to ProviderOptions
options = create_provider_options_from_args(args)

# Create provider
provider = create_provider_from_options(options)
```

## Agent Integration

The `AtlasAgent` class has been updated to accept a pre-configured provider instance directly:

```python
from atlas.agents.base import AtlasAgent
from atlas.providers import create_provider_from_options, ProviderOptions

# Create provider with options
options = ProviderOptions(
    provider_name="anthropic",
    capability="premium"
)
provider = create_provider_from_options(options)

# Initialize agent with provider
agent = AtlasAgent(
    system_prompt_file="system_prompt.txt",
    provider=provider
)
```

For backward compatibility, the `AtlasAgent` can also create a provider internally from provider_name, model_name, and capability parameters.

## Usage in Orchestration Systems

The provider selection architecture is designed to be used in orchestration and workflow management systems:

```python
from atlas.providers import ProviderOptions, create_provider_from_options

def create_agent_with_capability(workflow, agent_role, capability):
    """Create an agent with a specific capability."""
    # Create provider options customized for this workflow and role
    options = ProviderOptions(
        capability=capability,
        extra_params={"role": agent_role}
    )

    # Create provider with auto-detection and resolution
    provider = create_provider_from_options(options)

    # Create and return agent
    return workflow.create_agent(
        role=agent_role,
        provider=provider
    )

# Example usage in orchestration
workflow = Workflow()
agents = [
    create_agent_with_capability(workflow, "researcher", "vision"),
    create_agent_with_capability(workflow, "writer", "premium"),
    create_agent_with_capability(workflow, "editor", "efficient")
]
```

## Benefits of the New Architecture

The new provider selection architecture offers several benefits:

1. **Centralized Logic**: All provider/model selection logic lives in one place
2. **Reusable Components**: The `ProviderOptions` class and resolver can be used by any component
3. **Cleaner API**: Components can accept a provider instance directly
4. **Consistent Behavior**: All entry points use the same logic for provider selection
5. **Better Testability**: Isolated components are easier to test
6. **Feature Composability**: Orchestration systems can leverage the same auto-detection

## Example Use Cases

### Auto-Detection from Model Name

```python
# Only specify model name, provider will be auto-detected
options = ProviderOptions(model_name="gpt-4o")
provider = create_provider_from_options(options)
print(provider.name)  # "openai"
```

### Capability-Based Model Selection

```python
# Only specify provider and capability, model will be selected automatically
options = ProviderOptions(provider_name="anthropic", capability="inexpensive")
provider = create_provider_from_options(options)
```

### Direct Provider Integration with Agent

```python
# Create provider with custom options
provider = create_provider_from_options(
    ProviderOptions(model_name="claude-3-haiku-20240307", max_tokens=10000)
)

# Use provider directly with agent
agent = AtlasAgent(provider=provider)
response = agent.process_message("Hello, world!")
```

### Workflow Integration

```python
# Function that creates an agent with appropriate provider for a task
def get_task_agent(task_type):
    if task_type == "research":
        options = ProviderOptions(capability="premium")
    elif task_type == "drafting":
        options = ProviderOptions(capability="efficient")
    else:  # summarization
        options = ProviderOptions(capability="inexpensive")

    provider = create_provider_from_options(options)
    return AtlasAgent(provider=provider)
```
