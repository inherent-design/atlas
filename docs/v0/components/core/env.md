---

title: Environment Variables

---


# Environment Variables

This document describes the environment variables handling system in Atlas, which provides a centralized way to load, access, validate, and manage environment variables.

## Overview

The `atlas.core.env` module is responsible for:

1. **Loading Environment Variables**: From both OS environment and `.env` files
2. **Type Conversion**: Converting string values to appropriate types (int, float, bool, list)
3. **Default Values**: Providing fallbacks when variables are not set
4. **Validation**: Verifying presence and formatting of critical variables
5. **Provider API Keys**: Managing provider-specific API keys
6. **Caching**: Efficient access to environment values

The module is designed to be used throughout the Atlas framework to ensure consistent access to environment-based configuration.

## Core Functionality

### Loading Environment Variables

Atlas uses a layered approach to load environment variables:

1. **Environment File**: Variables from `.env` file (if available)
2. **OS Environment**: Variables from the operating system environment

The module automatically loads environment variables on first access, but you can also load them explicitly:

```python
from atlas.core import env

# Load with defaults
variables = env.load_environment()

# Force reload (useful after changes)
variables = env.load_environment(force_reload=True)

# Load from specific path
variables = env.load_environment(env_path="/path/to/.env")
```

### .env File Support

Atlas can load variables from a `.env` file using the `python-dotenv` package:

```python
from atlas.core import env

# Load from default location (.env in current directory)
env.load_env_file()

# Load from custom location
env.load_env_file("/path/to/custom/.env")

# Get possible .env file locations
env_paths = env.get_env_paths()
print(f"Checking these locations: {env_paths}")
```

The `.env` file should contain key-value pairs:

```
# .env file example
ANTHROPIC_API_KEY=sk-ant-api123...
ATLAS_DB_PATH=/data/atlas/db
ATLAS_MAX_TOKENS=4000
ATLAS_LOG_LEVEL=DEBUG
```

### Accessing Environment Variables

The module provides typed accessors for environment variables:

```python
from atlas.core import env

# String values
api_key = env.get_string("ANTHROPIC_API_KEY")
db_path = env.get_string("ATLAS_DB_PATH", "~/atlas_chroma_db")  # Default value

# Integer values
max_tokens = env.get_int("ATLAS_MAX_TOKENS", 2000)  # Default value
worker_count = env.get_int("ATLAS_WORKER_COUNT", 3)  # Default value

# Boolean values
dev_mode = env.get_bool("ATLAS_DEV_MODE", False)  # Default value
telemetry_enabled = env.get_bool("ATLAS_ENABLE_TELEMETRY", True)  # Default value

# Float values
temperature = env.get_float("ATLAS_TEMPERATURE", 0.7)  # Default value

# List values (comma-separated by default)
allowed_models = env.get_list("ATLAS_ALLOWED_MODELS", ["claude-3"])  # Default value
api_endpoints = env.get_list("ATLAS_API_ENDPOINTS", delimiter=";")  # Custom delimiter
```

### Required Environment Variables

For variables that must be present, use the `get_required_string` function:

```python
from atlas.core import env

try:
    # This will raise ValueError if not set
    api_key = env.get_required_string("ANTHROPIC_API_KEY")
    print(f"Using API key: {api_key[:4]}...{api_key[-4:]}")
except ValueError as e:
    print(f"Error: {e}")
    print("Please set the ANTHROPIC_API_KEY environment variable")
```

### Setting Environment Variables

You can set environment variables programmatically:

```python
from atlas.core import env

# Set a variable in both environment cache and os.environ
env.set_env_var("ATLAS_MAX_TOKENS", "3000")

# Set only in cache (for testing)
env.set_env_var("ATLAS_TEST_VAR", "test", update_os_environ=False)
```

## API Key Management

Atlas includes utilities for managing API keys for different providers:

```python
from atlas.core import env

# Get API key for a specific provider
anthropic_key = env.get_api_key("anthropic")
openai_key = env.get_api_key("openai")
ollama_key = env.get_api_key("ollama")  # Always None since Ollama doesn't use API keys

# Check if API key is available
has_anthropic = env.has_api_key("anthropic")
has_openai = env.has_api_key("openai")
has_ollama = env.has_api_key("ollama")  # Always True since Ollama doesn't need a key

# Get all available providers
available_providers = env.get_available_providers()
print(available_providers)  # {'anthropic': True, 'openai': False, 'ollama': True}
```

### Provider Requirements Validation

To check if a provider's dependencies are met:

```python
from atlas.core import env

# Check specific providers
anthropic_ready = env.validate_provider_requirements(["anthropic"])
print(anthropic_ready)  # {'anthropic': True} if API key is set

# Check all providers
all_providers = env.validate_provider_requirements(["anthropic", "openai", "ollama"])
print(all_providers)  # {'anthropic': True, 'openai': False, 'ollama': True}
```

### API Key Validation

For more thorough validation that actually tests API keys:

```python
from atlas.core import env

# Validate specific provider API key
anthropic_validation = env.validate_api_keys(["anthropic"])
if anthropic_validation["anthropic"]["valid"]:
    print("Anthropic API key is valid")
else:
    print(f"Anthropic API key issue: {anthropic_validation['anthropic']['error']}")

# Validate all providers (this makes API calls to verify keys)
all_validations = env.validate_api_keys()
for provider, result in all_validations.items():
    status = "Valid" if result["valid"] else f"Invalid: {result['error']}"
    print(f"{provider}: {status}")
```

For testing without making actual API calls:

```python
from atlas.core import env

# Skip the actual API calls - just check if keys are present
validations = env.validate_api_keys(skip_validation=True)
```

## Multiple Provider Support

Atlas supports registering new providers and their API key variables:

```python
from atlas.core import env

# Register a new provider with its API key environment variable
env.register_api_key_var("azure_openai", "AZURE_OPENAI_API_KEY")

# Register a provider that doesn't need an API key
env.register_api_key_var("local_llm", None)

# Now you can use these providers
has_azure = env.has_api_key("azure_openai")
azure_key = env.get_api_key("azure_openai")
```

## Boolean Value Handling

The `get_bool` function supports various boolean formats:

| Value                                            | Interpreted As |
| ------------------------------------------------ | -------------- |
| "1", "true", "yes", "on", "enable", "enabled"    | `True`         |
| "0", "false", "no", "off", "disable", "disabled" | `False`        |

Example:

```python
from atlas.core import env

# These all return True
env.set_env_var("TEST_BOOL1", "true")
env.set_env_var("TEST_BOOL2", "yes")
env.set_env_var("TEST_BOOL3", "1")
env.set_env_var("TEST_BOOL4", "enable")
print(env.get_bool("TEST_BOOL1"))  # True
print(env.get_bool("TEST_BOOL2"))  # True
print(env.get_bool("TEST_BOOL3"))  # True
print(env.get_bool("TEST_BOOL4"))  # True

# These all return False
env.set_env_var("TEST_BOOL5", "false")
env.set_env_var("TEST_BOOL6", "no")
env.set_env_var("TEST_BOOL7", "0")
env.set_env_var("TEST_BOOL8", "disable")
print(env.get_bool("TEST_BOOL5"))  # False
print(env.get_bool("TEST_BOOL6"))  # False
print(env.get_bool("TEST_BOOL7"))  # False
print(env.get_bool("TEST_BOOL8"))  # False
```

## Supported Environment Variables

Atlas recognizes a wide range of environment variables:

### Core Configuration

| Variable                 | Type    | Default                  | Description                 |
| ------------------------ | ------- | ------------------------ | --------------------------- |
| `ATLAS_COLLECTION_NAME`  | String  | `"atlas_knowledge_base"` | ChromaDB collection name    |
| `ATLAS_DB_PATH`          | String  | `~/atlas_chroma_db`      | Path to ChromaDB database   |
| `ATLAS_DEFAULT_PROVIDER` | String  | `"anthropic"`            | Default model provider      |
| `ATLAS_DEFAULT_MODEL`    | String  | Provider-specific        | Default model name          |
| `ATLAS_MAX_TOKENS`       | Integer | `2000`                   | Maximum tokens in responses |
| `ATLAS_LOG_LEVEL`        | String  | `"INFO"`                 | Logging level               |
| `ATLAS_ENV_PATH`         | String  | `".env"`                 | Path to .env file           |

### Provider-Specific

| Variable                        | Type   | Description                |
| ------------------------------- | ------ | -------------------------- |
| `ANTHROPIC_API_KEY`             | String | API key for Anthropic      |
| `OPENAI_API_KEY`                | String | API key for OpenAI         |
| `OPENAI_ORGANIZATION`           | String | Organization ID for OpenAI |
| `ATLAS_ANTHROPIC_DEFAULT_MODEL` | String | Default Anthropic model    |
| `ATLAS_OPENAI_DEFAULT_MODEL`    | String | Default OpenAI model       |
| `ATLAS_OLLAMA_DEFAULT_MODEL`    | String | Default Ollama model       |

### Development and Testing

| Variable             | Type    | Default | Description             |
| -------------------- | ------- | ------- | ----------------------- |
| `ATLAS_DEV_MODE`     | Boolean | `false` | Enable development mode |
| `ATLAS_MOCK_API`     | Boolean | `false` | Use mock API responses  |
| `SKIP_API_KEY_CHECK` | Boolean | `false` | Skip API key validation |

### Telemetry

| Variable                         | Type    | Default  | Description                     |
| -------------------------------- | ------- | -------- | ------------------------------- |
| `ATLAS_ENABLE_TELEMETRY`         | Boolean | `true`   | Enable telemetry                |
| `ATLAS_TELEMETRY_CONSOLE_EXPORT` | Boolean | `true`   | Enable console telemetry export |
| `ATLAS_TELEMETRY_LOG_LEVEL`      | String  | `"INFO"` | Telemetry log level             |

## Common Usage Patterns

### Environment Pattern for Multiple Configurations

Setting up multiple environments:

```python
from atlas.core import env

# Determine which environment to use
environment = env.get_string("ATLAS_ENVIRONMENT", "development")

# Load environment-specific .env file
env_file = f".env.{environment}"
env.load_env_file(env_file)

# Now all environment variables are loaded from the specific file
db_path = env.get_string("ATLAS_DB_PATH")
print(f"Using DB path for {environment} environment: {db_path}")
```

Example `.env` files:

```
# .env.development
ATLAS_DB_PATH=./dev_db
ATLAS_MAX_TOKENS=2000
ATLAS_DEV_MODE=true
ATLAS_MOCK_API=true

# .env.production
ATLAS_DB_PATH=/data/atlas/production
ATLAS_MAX_TOKENS=4000
ATLAS_DEV_MODE=false
ATLAS_MOCK_API=false
```

### Environment-Based Provider Selection

Choose different providers based on environment:

```python
from atlas.core import env

# Get environment
environment = env.get_string("ATLAS_ENVIRONMENT", "development")

if environment == "development":
    # Use Ollama for development (local, no API costs)
    env.set_env_var("ATLAS_DEFAULT_PROVIDER", "ollama")
    env.set_env_var("ATLAS_OLLAMA_DEFAULT_MODEL", "llama3")
elif environment == "staging":
    # Use OpenAI for staging
    env.set_env_var("ATLAS_DEFAULT_PROVIDER", "openai")
    env.set_env_var("ATLAS_OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo")
elif environment == "production":
    # Use Anthropic for production
    env.set_env_var("ATLAS_DEFAULT_PROVIDER", "anthropic")
    env.set_env_var("ATLAS_ANTHROPIC_DEFAULT_MODEL", "claude-3-7-sonnet-20250219")
```

### Required Variables Check

Before starting your application, validate that all required variables are set:

```python
from atlas.core import env
import sys

# Define required variables
required_vars = [
    "ANTHROPIC_API_KEY",  # Only if using Anthropic
    "ATLAS_DB_PATH",
    "ATLAS_COLLECTION_NAME",
]

# Check for missing variables
missing = env.validate_required_vars(required_vars)
if missing:
    print(f"Error: Missing required environment variables: {missing}")
    print("Please set these variables before running the application")
    sys.exit(1)
else:
    print("All required environment variables are set")
```

### Debugging Environment Issues

When troubleshooting environment-related problems:

```python
from atlas.core import env
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Force reload to see what's happening
env.load_environment(force_reload=True)

# Display all environment variables (with sensitive values masked)
print("Environment Variables:")
env_vars = env.load_environment()
for key, value in env_vars.items():
    # Mask API keys for security
    if "API_KEY" in key and value:
        masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
        print(f"  {key}: {masked}")
    else:
        print(f"  {key}: {value}")

# Display available providers
providers = env.get_available_providers()
print("Available Providers:")
for provider, available in providers.items():
    print(f"  {provider}: {'Available' if available else 'Unavailable'}")

# List possible .env file locations
env_paths = env.get_env_paths()
print("Possible .env Locations:")
for path in env_paths:
    import os
    print(f"  {path}: {'Exists' if os.path.exists(path) else 'Not Found'}")
```

## Best Practices

1. **Use .env Files**: Store environment variables in `.env` files for easy management
   ```
   # .env
   ANTHROPIC_API_KEY=sk-ant-api123...
   ATLAS_DB_PATH=/data/atlas/db
   ```

2. **Don't Commit Secrets**: Always add `.env` files to `.gitignore`
   ```
   # .gitignore
   .env*
   ```

3. **Use Type-Specific Getters**: Always use the appropriate getter for the expected type
   ```python
   # Good
   max_tokens = env.get_int("ATLAS_MAX_TOKENS", 2000)

   # Bad - might get a string instead of an int
   max_tokens = env.get_string("ATLAS_MAX_TOKENS", "2000")
   ```

4. **Provide Defaults**: Always specify default values for non-critical settings
   ```python
   # With default
   log_level = env.get_string("ATLAS_LOG_LEVEL", "INFO")

   # Without default - could be None
   log_level = env.get_string("ATLAS_LOG_LEVEL")
   ```

5. **Register Custom Providers**: When adding new providers, register them properly
   ```python
   env.register_api_key_var("my_provider", "MY_PROVIDER_API_KEY")
   ```

6. **Validate Early**: Check for required variables early in application startup
   ```python
   missing = env.validate_required_vars(["ANTHROPIC_API_KEY", "ATLAS_DB_PATH"])
   if missing:
       raise ValueError(f"Missing required variables: {missing}")
   ```

7. **Environment-Specific Files**: Use different `.env` files for different environments
   ```
   .env.development
   .env.testing
   .env.production
   ```

## Related Documentation

- [Configuration System](config.md) - Documentation for the configuration system
