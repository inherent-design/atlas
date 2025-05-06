# Environment Variables in Atlas

This document provides a comprehensive guide to all environment variables used in the Atlas framework.

## Environment Variable Handling

Atlas uses a centralized environment variable management system through the `atlas.core.env` module. This ensures consistent handling of environment variables across the codebase and provides proper validation and type conversion.

### Loading Environment Variables

Environment variables can be set directly in the shell or through a `.env` file in the project root. The `.env` file is loaded automatically when the application starts, but you can also specify a custom path using the `ATLAS_ENV_PATH` environment variable.

Environment variables are loaded from the following sources, in order of precedence:
1. OS environment variables (highest precedence)
2. `.env` file (lower precedence)

Example `.env` file:
```bash
# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Configuration
ATLAS_ENABLE_TELEMETRY=true
ATLAS_TELEMETRY_LOG_LEVEL=INFO
ATLAS_DB_PATH=/path/to/atlas_db
ATLAS_COLLECTION_NAME=atlas_knowledge_base
ATLAS_DEFAULT_MODEL=claude-3-7-sonnet-20250219
```

### Order of Precedence

When multiple configuration sources are available, Atlas follows this order of precedence:

1. **Command-line arguments** (highest priority) - Parameters passed directly to functions or from CLI commands
2. **Environment variables** (medium priority) - Set in the OS or in .env files
3. **Default values** (lowest priority) - Hardcoded in the codebase

This means command-line arguments override environment variables, which override default values.

### Accessing Environment Variables

Always use the `atlas.core.env` module to access environment variables instead of using `os.environ` directly. This ensures consistent handling and proper validation.

```python
from atlas.core import env

# Get a string value with a default
api_endpoint = env.get_string("API_ENDPOINT", default="https://api.example.com")

# Get a required string value (raises ValueError if not present)
api_key = env.get_required_string("API_KEY")

# Get an integer value
timeout = env.get_int("TIMEOUT", default=30)

# Get a float value
threshold = env.get_float("THRESHOLD", default=0.75)

# Get a boolean value
debug_mode = env.get_bool("DEBUG_MODE", default=False)

# Get a list of values from a comma-separated string
allowed_hosts = env.get_list("ALLOWED_HOSTS", default=["localhost"])

# Check if an API key is available
has_openai = env.has_api_key("openai")

# Get an API key
anthropic_key = env.get_api_key("anthropic")

# Set an environment variable
env.set_env_var("CUSTOM_VAR", "custom_value")

# Load environment from a specific .env file
env.load_env_file("/path/to/.env")

# Get all available providers
providers = env.get_available_providers()

# Validate required variables
missing = env.validate_required_vars(["API_KEY", "DB_PATH"])
```

## Available Environment Variables

### Core Environment Variables

| Variable | Description | Used in | Default |
|----------|-------------|---------|---------|
| `ATLAS_ENV_PATH` | Path to .env file | env.py | `.env` in current directory |
| `ATLAS_LOG_LEVEL` | Logging level | config.py | `INFO` |
| `SKIP_API_KEY_CHECK` | Skip API key validation | config.py, factory.py | `false` |

### API Keys

| Variable | Description | Used in | Default |
|----------|-------------|---------|---------|
| `ANTHROPIC_API_KEY` | API key for Anthropic Claude | config.py, env.py | None |
| `OPENAI_API_KEY` | API key for OpenAI | env.py, main.py | None |
| `OPENAI_ORGANIZATION` | Organization ID for OpenAI | env.py | None |

### Telemetry

| Variable | Description | Used in | Default |
|----------|-------------|---------|---------|
| `ATLAS_ENABLE_TELEMETRY` | Enable or disable telemetry | telemetry.py | `true` |
| `ATLAS_TELEMETRY_CONSOLE_EXPORT` | Enable console exporting for telemetry | telemetry.py | `true` |
| `ATLAS_TELEMETRY_LOG_LEVEL` | Log level for telemetry | telemetry.py | `INFO` |

### Database

| Variable | Description | Used in | Default |
|----------|-------------|---------|---------|
| `ATLAS_DB_PATH` | Path to ChromaDB database | config.py, retrieval.py | `~/atlas_chroma_db` |
| `ATLAS_COLLECTION_NAME` | ChromaDB collection name | config.py, retrieval.py | `atlas_knowledge_base` |

### Model Settings

| Variable | Description | Used in | Default |
|----------|-------------|---------|---------|
| `ATLAS_DEFAULT_PROVIDER` | Default model provider | factory.py | `anthropic` |
| `ATLAS_DEFAULT_MODEL` | Default model to use | config.py, factory.py | `claude-3-5-sonnet-20240620` |
| `ATLAS_MAX_TOKENS` | Maximum tokens for model responses | config.py, factory.py | `2000` |
| `ATLAS_{PROVIDER}_DEFAULT_MODEL` | Provider-specific model (e.g., `ATLAS_ANTHROPIC_DEFAULT_MODEL`) | factory.py | Provider-specific default |

### Development and Testing

| Variable | Description | Used in | Default |
|----------|-------------|---------|---------|
| `ATLAS_DEV_MODE` | Enable development mode | config.py | `false` |
| `ATLAS_MOCK_API` | Use mock API responses | config.py | `false` |
| `TOKENIZERS_PARALLELISM` | Control tokenizer parallelism | main.py | `false` |

## Configuration in AtlasConfig

The `AtlasConfig` class in `atlas.core.config` is the primary configuration object used throughout the framework. It respects all environment variables and also accepts direct parameter values:

```python
from atlas.core.config import AtlasConfig

# Create config with defaults (pulls from environment variables)
config = AtlasConfig()

# Override with specific values
config = AtlasConfig(
    collection_name="custom_collection",
    db_path="/path/to/custom/db",
    model_name="claude-3-opus-20240229",
    max_tokens=4000
)
```

## Provider Factory Configuration

The provider factory in `atlas.models.factory` allows you to create model providers with environment-aware configurations:

```python
from atlas.models.factory import create_provider

# Uses environment variables for defaults
provider = create_provider()

# Specific provider with environment variables for model and tokens
provider = create_provider(provider_name="anthropic")

# Fully specified configuration (overrides environment variables)
provider = create_provider(
    provider_name="openai",
    model_name="gpt-4o",
    max_tokens=8000
)
```

## Knowledge Base Configuration

The knowledge base in `atlas.knowledge.retrieval` also respects environment variables:

```python
from atlas.knowledge.retrieval import KnowledgeBase

# Uses environment variables for database path and collection name
kb = KnowledgeBase()

# Specify custom values (overrides environment variables)
kb = KnowledgeBase(
    collection_name="custom_collection",
    db_path="/path/to/custom/db"
)
```

## Adding New Environment Variables

When adding new environment variables to the codebase:

1. Always use the `atlas.core.env` module to access them
2. Add documentation for the new variables in this file
3. Update any relevant configuration classes to use the new variables
4. Add validation for required variables
5. Register new provider API key variables with `register_api_key_var`

### Standardized Naming

Follow these naming conventions for environment variables:

1. Use `ATLAS_` prefix for all Atlas-specific variables
2. Use `ATLAS_{PROVIDER}_` prefix for provider-specific variables
3. Use all caps with underscores as separators
4. Use descriptive names that clearly indicate the variable's purpose

## Using the env.py Module

The `atlas/core/env.py` module provides a centralized way to access environment variables. Here are some examples of how to use it:

### Basic Usage

```python
from atlas.core import env

# Get a string value (returns None if not set)
api_key = env.get_string("ANTHROPIC_API_KEY")

# Get a string with default value
log_level = env.get_string("ATLAS_LOG_LEVEL", "INFO")

# Get a boolean value
telemetry_enabled = env.get_bool("ATLAS_ENABLE_TELEMETRY", True)

# Get an integer value
max_tokens = env.get_int("ATLAS_MAX_TOKENS", 2000)

# Get a required value (raises ValueError if not set)
required_key = env.get_required_string("ANTHROPIC_API_KEY")
```

### Provider-Specific Functions

```python
from atlas.core import env

# Check if a provider's API key is available
if env.has_api_key("anthropic"):
    # Use Anthropic provider
    api_key = env.get_api_key("anthropic")
    # Initialize Anthropic client...

# Get all available providers
providers = env.get_available_providers()
for provider, available in providers.items():
    if available:
        print(f"Provider {provider} is available")
```

### Validating Required Variables

```python
from atlas.core import env

# Check if all required variables are present
missing = env.validate_required_vars(["ANTHROPIC_API_KEY", "ATLAS_DB_PATH"])
if missing:
    print(f"Missing required environment variables: {', '.join(missing)}")
    # Handle missing variables...
```

### Setting Environment Variables

```python
from atlas.core import env

# Set an environment variable
env.set_env_var("ATLAS_CUSTOM_SETTING", "custom_value")

# Set a variable without updating os.environ (for testing)
env.set_env_var("ATLAS_TEST_VAR", "test_value", update_os_environ=False)
```

### Working with .env Files

```python
from atlas.core import env

# Load a specific .env file
env.load_env_file("/path/to/.env")

# Force reload all environment variables
env.load_environment(force_reload=True)
```

### Registering Custom Providers

```python
from atlas.core import env

# Register a new provider with its API key environment variable
env.register_api_key_var("custom_provider", "CUSTOM_PROVIDER_API_KEY")

# Register a provider that doesn't need an API key
env.register_api_key_var("local_provider", None)
```

## Best Practices

1. **Always use the env module** instead of direct `os.environ` access
2. **Document new environment variables** in this file when adding them
3. **Use appropriate type conversion** functions for different variable types
4. **Validate required variables** early in the application startup
5. **Provide sensible defaults** when possible
6. **Use provider-specific functions** for API keys
7. **Keep sensitive information** in environment variables or `.env` files (never commit them)
8. **Group related variables** with consistent prefixes (e.g., `ATLAS_` for Atlas-specific variables)
9. **Use feature flags** for enabling/disabling features (e.g., `ATLAS_ENABLE_TELEMETRY`)
10. **Add validation** for critical configuration values

## CLI Tools

For details on how environment variables interact with command-line tools, see [CLI Tools Documentation](cli/README.md).