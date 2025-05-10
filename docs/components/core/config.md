# Configuration System

This document explains the Atlas configuration system and how to use it to customize the framework's behavior.

## Overview

Atlas uses a structured configuration system based on the `AtlasConfig` class, which provides:

1. **Centralized Configuration**: Single source of configuration values for all Atlas components
2. **Environment Integration**: Automatic loading of settings from environment variables
3. **Default Values**: Sensible defaults for non-critical settings
4. **Validation**: Runtime validation of configuration values
5. **Hierarchical Precedence**: Clear resolution order for configuration sources

The configuration system follows a predictable precedence order:

1. Explicitly provided parameters (highest priority)
2. Environment variables (medium priority)
3. Default values (lowest priority)

## AtlasConfig Class

The `AtlasConfig` class is the central configuration object used throughout Atlas. It consolidates all configuration options and handles loading, validation, and access to these settings.

```python
from atlas.core.config import AtlasConfig

# Create a configuration with default settings
config = AtlasConfig()

# Create a configuration with custom settings
custom_config = AtlasConfig(
    anthropic_api_key="your_api_key",
    collection_name="custom_collection",
    db_path="/custom/db/path",
    model_name="claude-3-7-sonnet-20250219",
    max_tokens=4000,
    parallel_enabled=True,
    worker_count=5
)
```

### Constructor Parameters

The `AtlasConfig` constructor accepts the following parameters:

| Parameter           | Type            | Description                 | Default                                                          |
| ------------------- | --------------- | --------------------------- | ---------------------------------------------------------------- |
| `anthropic_api_key` | `Optional[str]` | API key for Anthropic       | From `ANTHROPIC_API_KEY` env var                                 |
| `collection_name`   | `Optional[str]` | Name of ChromaDB collection | From `ATLAS_COLLECTION_NAME` env var or `"atlas_knowledge_base"` |
| `db_path`           | `Optional[str]` | Path to ChromaDB storage    | From `ATLAS_DB_PATH` env var or `~/atlas_chroma_db`              |
| `model_name`        | `Optional[str]` | Name of the model to use    | From `ATLAS_DEFAULT_MODEL` env var or provider-specific default  |
| `max_tokens`        | `Optional[int]` | Maximum tokens in responses | From `ATLAS_MAX_TOKENS` env var or `2000`                        |
| `parallel_enabled`  | `bool`          | Enable parallel processing  | `False`                                                          |
| `worker_count`      | `int`           | Number of worker agents     | `3`                                                              |

### Properties and Methods

The `AtlasConfig` class provides the following properties and methods:

#### Properties

- `anthropic_api_key`: API key for Anthropic Claude (protected)
- `collection_name`: ChromaDB collection name
- `db_path`: Path to ChromaDB database
- `model_name`: Model name to use
- `max_tokens`: Maximum tokens in model responses
- `parallel_enabled`: Whether parallel processing is enabled
- `worker_count`: Number of worker agents for parallel processing
- `dev_mode`: Whether development mode is enabled (from `ATLAS_DEV_MODE` env var)
- `mock_api`: Whether to use mock API responses (from `ATLAS_MOCK_API` env var)
- `log_level`: Logging level (from `ATLAS_LOG_LEVEL` env var)

#### Methods

- `validate()`: Validates all configuration settings
- `to_dict()`: Converts configuration to a dictionary (excluding sensitive values)

## Configuration Usage Patterns

### Basic Usage

The simplest way to use `AtlasConfig` is to create an instance with default settings:

```python
from atlas.core.config import AtlasConfig

# Create configuration with environment-based settings
config = AtlasConfig()

# Pass to Atlas components
from atlas.agents.base import AtlasAgent
agent = AtlasAgent(config=config)
```

### Custom Configuration

For more control, you can override specific settings:

```python
from atlas.core.config import AtlasConfig

# Override specific settings
config = AtlasConfig(
    model_name="claude-3-opus-20240229",  # Use a more powerful model
    max_tokens=4000,                     # Allow longer responses
    db_path="/data/atlas/knowledge"      # Custom database location
)
```

### Multi-Environment Configuration

Different environments often require different configurations:

```python
import os
from atlas.core.config import AtlasConfig

# Determine environment
env = os.environ.get("ATLAS_ENVIRONMENT", "development")

# Base configuration with environment-specific overrides
if env == "development":
    config = AtlasConfig(
        db_path="./dev_db",
        model_name="claude-3-5-sonnet-20240620",  # Smaller model for development
        dev_mode=True
    )
elif env == "testing":
    config = AtlasConfig(
        db_path="./test_db",
        model_name="claude-3-5-sonnet-20240620",
        mock_api=True  # Use mock responses for testing
    )
elif env == "production":
    config = AtlasConfig(
        db_path="/data/atlas_db",
        model_name="claude-3-7-sonnet-20250219",  # More capable model for production
        max_tokens=4000  # Allow longer responses in production
    )
else:
    # Default fallback
    config = AtlasConfig()
```

### Provider-Specific Configuration

Different model providers may require different settings:

```python
from atlas.core.config import AtlasConfig
from atlas.core import env

# Get provider from environment
provider_name = env.get_string("ATLAS_DEFAULT_PROVIDER", "anthropic")

# Configure based on provider
if provider_name == "anthropic":
    config = AtlasConfig(
        model_name="claude-3-5-sonnet-20240620",
        max_tokens=2000
    )
elif provider_name == "openai":
    config = AtlasConfig(
        model_name="gpt-4o",
        max_tokens=4000
    )
elif provider_name == "ollama":
    config = AtlasConfig(
        model_name="llama3",
        max_tokens=2048
    )
```

### Configuration Serialization

You can convert configuration to dictionaries for storage or transmission:

```python
from atlas.core.config import AtlasConfig

# Create configuration
config = AtlasConfig(
    collection_name="my_collection",
    max_tokens=3000
)

# Convert to dictionary (excluding sensitive values)
config_dict = config.to_dict()
print(config_dict)
# {'collection_name': 'my_collection', 'db_path': '/home/user/atlas_chroma_db',
#  'model_name': 'claude-3-5-sonnet-20240620', 'max_tokens': 3000,
#  'parallel_enabled': False, 'worker_count': 3, 'dev_mode': False,
#  'mock_api': False, 'log_level': 'INFO'}

# Later, recreate configuration from values
new_config = AtlasConfig(**config_dict)
```

## Validation System

Atlas validates configuration settings to ensure they are valid and consistent:

```python
from atlas.core.config import AtlasConfig
from atlas.core.errors import ValidationError

try:
    # This will fail validation (negative max_tokens)
    config = AtlasConfig(max_tokens=-100)
except ValidationError as e:
    print(f"Validation error: {e}")
    print(f"Field errors: {e.field_errors}")
    # {'max_tokens': ['Max tokens must be a positive integer']}
```

### Validation Rules

The `AtlasConfig.validate()` method checks:

1. **Model Name**: Must be a non-empty string
2. **Max Tokens**: Must be a positive integer
3. **Worker Count**: For parallel mode, must be a positive integer
4. **Database Path**: Must be a non-empty string

### Validation Errors

If validation fails, a `ValidationError` is raised with:

- Error message explaining the issue
- Dictionary of field-specific errors
- Severity level (`WARNING` or `ERROR`)

You can catch these errors to provide user-friendly feedback:

```python
from atlas.core.config import AtlasConfig
from atlas.core.errors import ValidationError, ErrorSeverity

try:
    config = AtlasConfig(model_name="")
except ValidationError as e:
    if e.severity == ErrorSeverity.ERROR:
        print("Critical validation error:")
    else:
        print("Warning:")

    for field, errors in e.field_errors.items():
        print(f"  {field}: {', '.join(errors)}")
```

## API Key Handling

Atlas handles API keys securely by:

1. Loading keys from environment variables
2. Not including keys in serialized configuration
3. Validating key presence on initialization

When no API key is provided:

```python
from atlas.core.config import AtlasConfig
from atlas.core.errors import ConfigurationError

try:
    # No API key provided or in environment
    config = AtlasConfig()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # ConfigurationError: ANTHROPIC_API_KEY must be provided or set as an environment variable
```

You can bypass API key validation for testing:

```python
import os
from atlas.core.config import AtlasConfig

# Skip API key check for testing
os.environ["SKIP_API_KEY_CHECK"] = "true"

# This won't raise an error even without an API key
config = AtlasConfig()
```

## Integration with Components

Atlas components typically accept a config parameter:

```python
from atlas.core.config import AtlasConfig
from atlas.agents.base import AtlasAgent
from atlas.agents.controller import ControllerAgent
from atlas.knowledge.retrieval import KnowledgeBase

# Create configuration
config = AtlasConfig(
    collection_name="my_knowledge_base",
    model_name="claude-3-7-sonnet-20250219"
)

# Use with various components
agent = AtlasAgent(config=config)
controller = ControllerAgent(config=config)
kb = KnowledgeBase(
    collection_name=config.collection_name,
    db_path=config.db_path
)
```

## Configuration Best Practices

1. **Single Config Instance**: Create one configuration object and pass it to all components
   ```python
   config = AtlasConfig()
   agent = AtlasAgent(config=config)
   kb = KnowledgeBase(collection_name=config.collection_name, db_path=config.db_path)
   ```

2. **Environment Variables**: Use environment variables for deployment-specific settings
   ```python
   # .env file
   ATLAS_DB_PATH=/data/atlas/production
   ATLAS_MAX_TOKENS=4000
   ```

3. **Explicit Configuration**: For critical settings, provide them explicitly
   ```python
   config = AtlasConfig(
       model_name="claude-3-7-sonnet-20250219",  # Explicitly choose model
       max_tokens=3000  # Explicitly set token limit
   )
   ```

4. **Validation Handling**: Always handle validation errors gracefully
   ```python
   try:
       config = AtlasConfig(max_tokens=tokens)
   except ValidationError as e:
       print(f"Invalid configuration: {e}")
       # Use default as fallback
       config = AtlasConfig()
   ```

5. **Security**: Never hardcode API keys in your code
   ```python
   # Bad - hardcoded API key
   config = AtlasConfig(anthropic_api_key="sk-ant-api123...")

   # Good - loaded from environment
   config = AtlasConfig()  # Automatically loads from ANTHROPIC_API_KEY
   ```

## Related Documentation

- [Advanced Configuration Guide](../../guides/configuration.md) - Comprehensive configuration patterns and advanced usage
- [Environment Variables Reference](../../reference/env_variables.md) - Complete list of supported environment variables
- [Environment Module Documentation](env.md) - Details on environment variable handling
- [Error System Documentation](errors.md) - Information about the error handling system
