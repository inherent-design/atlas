# Advanced Configuration Guide

This guide provides comprehensive information about configuring and customizing Atlas for your specific needs.

## Configuration Overview

Atlas provides a flexible configuration system that allows you to customize its behavior through:

1. **Environment Variables**: For application-level infrastructure configuration (API keys, logging, database paths)
2. **Command-Line Arguments**: For business logic configuration (provider selection, model parameters)
3. **Configuration Objects**: For programmatic configuration
4. **.env Files**: For storing environment variables in project files

These approaches follow a clear separation of concerns:

- **Environment Variables**: Infrastructure configuration that rarely changes
- **Command-Line Arguments**: Business logic configuration that varies between executions
- **Configuration Objects**: Programmatic interface for configuration combination

This separation ensures a clean architecture where infrastructure settings are managed separately from business logic settings.

## Environment Variables

Atlas uses environment variables as the primary configuration mechanism. These can be set in your shell, in a `.env` file, or in your system environment.

### Core Environment Variables

| Variable                 | Description                 | Default                | Example Value                |
| ------------------------ | --------------------------- | ---------------------- | ---------------------------- |
| `ANTHROPIC_API_KEY`      | API key for Anthropic       | (Required)             | `sk-ant-api03...`            |
| `OPENAI_API_KEY`         | API key for OpenAI          | (Required for OpenAI)  | `sk-xyz123...`               |
| `ATLAS_COLLECTION_NAME`  | ChromaDB collection name    | `atlas_knowledge_base` | `my_custom_collection`       |
| `ATLAS_DB_PATH`          | Path to ChromaDB database   | `~/atlas_chroma_db`    | `/path/to/db`                |
| `ATLAS_DEFAULT_PROVIDER` | Default model provider      | `anthropic`            | `openai`                     |
| `ATLAS_DEFAULT_MODEL`    | Default model               | Provider-specific      | `claude-3-7-sonnet-20250219` |
| `ATLAS_MAX_TOKENS`       | Maximum tokens in responses | `2000`                 | `4000`                       |
| `ATLAS_LOG_LEVEL`        | Application log level       | `INFO`                 | `DEBUG`                      |

### Provider-Specific Variables

| Variable                        | Description                | Default                      | Example Value            |
| ------------------------------- | -------------------------- | ---------------------------- | ------------------------ |
| `ATLAS_ANTHROPIC_DEFAULT_MODEL` | Default Anthropic model    | `claude-3-5-sonnet-20240620` | `claude-3-opus-20240229` |
| `ATLAS_OPENAI_DEFAULT_MODEL`    | Default OpenAI model       | `gpt-4o`                     | `gpt-4-turbo`            |
| `ATLAS_OLLAMA_DEFAULT_MODEL`    | Default Ollama model       | `llama3`                     | `mixtral`                |
| `OPENAI_ORGANIZATION`           | Organization ID for OpenAI | (Optional)                   | `org-xyz123...`          |
| `ATLAS_DEFAULT_CAPABILITY`      | Default model capability   | `inexpensive`                | `premium`                |

### Telemetry Variables

| Variable                         | Description                     | Default | Example Value |
| -------------------------------- | ------------------------------- | ------- | ------------- |
| `ATLAS_ENABLE_TELEMETRY`         | Enable/disable telemetry        | `true`  | `false`       |
| `ATLAS_TELEMETRY_CONSOLE_EXPORT` | Enable console telemetry export | `true`  | `false`       |
| `ATLAS_TELEMETRY_LOG_LEVEL`      | Telemetry log level             | `INFO`  | `DEBUG`       |

### Development Variables

| Variable             | Description             | Default | Example Value   |
| -------------------- | ----------------------- | ------- | --------------- |
| `ATLAS_DEV_MODE`     | Enable development mode | `false` | `true`          |
| `ATLAS_MOCK_API`     | Use mock API responses  | `false` | `true`          |
| `ATLAS_ENV_PATH`     | Path to .env file       | `.env`  | `/path/to/.env` |

Note: API key validation is now controlled through command-line arguments and provider requirements, not through environment variables.

## Using .env Files

For local development and deployment, you can use a `.env` file to store configuration variables:

```bash
# Create a .env file in the project root
touch .env

# Add configuration values
echo "ANTHROPIC_API_KEY=your_api_key_here" >> .env
echo "ATLAS_DB_PATH=/custom/data/path" >> .env
echo "ATLAS_DEFAULT_MODEL=claude-3-opus-20240229" >> .env
```

Atlas will automatically load the `.env` file when it starts if the `python-dotenv` package is installed. You can also specify a custom path using the `ATLAS_ENV_PATH` variable:

```bash
# Set a custom .env file path
export ATLAS_ENV_PATH=/path/to/custom/.env

# Or set it before running your script
ATLAS_ENV_PATH=/path/to/custom/.env uv run python main.py
```

### Multiple Environment Support

For different environments (development, testing, production), you can create multiple `.env` files:

```
project/
  ├── .env              # Default environment
  ├── .env.development  # Development environment
  ├── .env.testing      # Testing environment
  └── .env.production   # Production environment
```

To use a specific environment:

```bash
# Set the environment
export ATLAS_ENV_PATH=.env.production

# Run Atlas
uv run python main.py
```

## Configuration Object

For programmatic configuration, Atlas provides the `AtlasConfig` class:

```python
from atlas.core.config import AtlasConfig

# Create a configuration with custom settings
config = AtlasConfig(
    anthropic_api_key="your_api_key_here",
    collection_name="custom_collection",
    db_path="/path/to/database",
    model_name="claude-3-7-sonnet-20250219",
    max_tokens=4000,
    parallel_enabled=True,
    worker_count=5
)

# Use the configuration with Atlas components
from atlas.agents.base import AtlasAgent
agent = AtlasAgent(config=config)
```

The `AtlasConfig` object will:

1. Use explicitly provided values first
2. Fall back to environment variables if not specified
3. Use default values as a last resort

This provides a predictable hierarchy of configuration values.

### Serializing and Deserializing

Config objects can be converted to dictionaries for storage or transmission:

```python
# Convert to dictionary (note: API keys are excluded for security)
config_dict = config.to_dict()

# Later, recreate configuration from values
from atlas.core.config import AtlasConfig
config = AtlasConfig(**config_dict)
```

## Environment Manipulation

Atlas provides utilities for working with environment variables in the `atlas.core.env` module:

```python
from atlas.core import env

# Load environment from file
env.load_env_file(".env.production")

# Access environment variables with type conversion
api_key = env.get_string("ANTHROPIC_API_KEY")
max_tokens = env.get_int("ATLAS_MAX_TOKENS", 2000)
telemetry_enabled = env.get_bool("ATLAS_ENABLE_TELEMETRY", True)
comma_separated_list = env.get_list("ATLAS_ALLOWED_MODELS", delimiter=",")

# Set environment variables programmatically
env.set_env_var("ATLAS_DEFAULT_MODEL", "claude-3-opus-20240229")

# Get API key for specified provider
anthropic_key = env.get_api_key("anthropic")

# Check which providers are available
available_providers = env.get_available_providers()
print(available_providers)  # {'anthropic': True, 'openai': False, 'ollama': True}

# Validate required environment variables
missing = env.validate_required_vars(["ANTHROPIC_API_KEY", "ATLAS_DB_PATH"])
if missing:
    print(f"Missing required variables: {missing}")
```

These utilities provide a safe, consistent way to interact with environment variables and ensure proper type conversion.

## Advanced Configuration Patterns

### Capability-Based Model Selection

Atlas now supports selecting models based on their capabilities rather than explicit model names:

```python
from atlas.providers.factory import create_provider

# Create a provider using capability-based model selection
provider = create_provider(
    provider_name="anthropic",
    capability="inexpensive"  # Will select the inexpensive model for Anthropic
)

# Available capabilities
# - "inexpensive": Cost-effective models suitable for most tasks
# - "efficient": Models optimized for speed and lower resource usage
# - "premium": High-performance, state-of-the-art models
# - "vision": Models with image processing capabilities
# - "standard": General-purpose models (all models have this capability)

# Create provider with auto-detection from model name
provider = create_provider(
    model_name="gpt-4o"  # Will automatically use OpenAI provider
)

# Get capabilities of a model
from atlas.providers.factory import get_model_capabilities
capabilities = get_model_capabilities("anthropic", "claude-3-opus-20240229")
print(capabilities)  # ['premium', 'vision', 'standard']
```

The capability-based model selection automatically works with the CLI:

```bash
# Use the inexpensive model from Anthropic
uv run python main.py --provider anthropic --capability inexpensive

# Use a premium model from any provider
uv run python main.py --capability premium

# Auto-detect provider from model name
uv run python main.py --model gpt-4o
```

### Dynamic Provider Selection

You can dynamically select different model providers based on your needs:

```python
import os
from atlas import create_query_client

# Function to select best available provider
def get_best_provider():
    from atlas.core import env

    # Check available providers
    providers = env.get_available_providers()

    # Preferred order: Anthropic, OpenAI, Ollama
    if providers.get("anthropic", False):
        return "anthropic"
    elif providers.get("openai", False):
        return "openai"
    elif providers.get("ollama", False):
        return "ollama"
    else:
        raise ValueError("No available providers")

# Use the best available provider
provider = get_best_provider()
client = create_query_client(provider_name=provider)
```

### Provider-Specific Configuration

Different providers may require different configuration options:

```python
from atlas.core.config import AtlasConfig
from atlas.core import env

# Configure based on provider
provider_name = env.get_string("ATLAS_DEFAULT_PROVIDER", "anthropic")

if provider_name == "anthropic":
    # Anthropic-specific settings
    model_name = env.get_string("ATLAS_ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20240620")
    max_tokens = 2000
elif provider_name == "openai":
    # OpenAI-specific settings
    model_name = env.get_string("ATLAS_OPENAI_DEFAULT_MODEL", "gpt-4o")
    max_tokens = 4000
elif provider_name == "ollama":
    # Ollama-specific settings
    model_name = env.get_string("ATLAS_OLLAMA_DEFAULT_MODEL", "llama3")
    max_tokens = 2048
else:
    # Default settings
    model_name = None
    max_tokens = 1000

# Create config with provider-specific settings
config = AtlasConfig(
    model_name=model_name,
    max_tokens=max_tokens
)
```

### Environment-Specific Configuration

Different environments (development, testing, production) often require different configurations:

```python
import os
from atlas.core.config import AtlasConfig

# Get current environment
env_name = os.environ.get("ATLAS_ENVIRONMENT", "development")

# Base configuration shared across all environments
base_config = {
    "collection_name": "atlas_knowledge_base",
    "max_tokens": 2000
}

# Environment-specific configurations
env_configs = {
    "development": {
        "db_path": "./dev_db",
        "model_name": "claude-3-5-sonnet-20240620",  # Smaller model for development
        "dev_mode": True,
        "mock_api": True  # Use mock API responses for faster development
    },
    "testing": {
        "db_path": "./test_db",
        "model_name": "claude-3-5-sonnet-20240620",
        "dev_mode": False,
        "mock_api": False
    },
    "production": {
        "db_path": "/data/atlas_db",
        "model_name": "claude-3-7-sonnet-20250219",  # More capable model for production
        "dev_mode": False,
        "mock_api": False
    }
}

# Merge base config with environment-specific config
config_dict = {**base_config, **env_configs.get(env_name, {})}

# Create config object
config = AtlasConfig(**config_dict)
```

### Parallel Processing Configuration

For parallel processing with multiple workers:

```python
from atlas.core.config import AtlasConfig
from atlas.agents.controller import ControllerAgent

# Configure parallel processing
config = AtlasConfig(
    parallel_enabled=True,  # Enable parallel processing
    worker_count=5  # Number of worker agents
)

# Create controller agent with custom worker types
controller = ControllerAgent(
    config=config,
    worker_types=["researcher", "analyst", "writer"],
    provider_name="anthropic"
)

# Process a task with parallel workers
response = controller.process_task("Analyze the trimodal methodology in Atlas")
```

## Configuration Validation

Atlas includes built-in validation for configuration values:

```python
from atlas.core.config import AtlasConfig
from atlas.core.errors import ValidationError

try:
    # This will raise ValidationError due to invalid model name
    config = AtlasConfig(model_name="")
except ValidationError as e:
    print(f"Configuration validation failed: {e}")
    print(f"Field errors: {e.field_errors}")
```

The validation system checks:

1. Model name validity
2. Token count range
3. Worker count for parallel processing
4. Database path validity
5. Other provider-specific parameters

## Error Handling

Atlas uses a structured error system for configuration issues:

```python
from atlas.core.config import AtlasConfig
from atlas.core.errors import ConfigurationError, ValidationError, ErrorSeverity

try:
    # Missing API key will raise ConfigurationError
    config = AtlasConfig()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    print(f"Severity: {e.severity}")
    print(f"Details: {e.details}")

    # Check if it's a missing API key error
    if e.details.get("missing_config") == "ANTHROPIC_API_KEY":
        print("Please provide an Anthropic API key")
```

The error system provides:

1. **Structured Error Types**: Different exception classes for different error categories
2. **Severity Levels**: WARNING, ERROR, CRITICAL
3. **Detailed Context**: Additional information about what went wrong

## Environment Variable Best Practices

1. **Security**: Never commit API keys to version control
   ```bash
   # Add to .gitignore
   echo ".env*" >> .gitignore
   ```

2. **Documentation**: Document all environment variables
   ```python
   # At the top of modules that use environment variables
   """
   Environment variables:
       ATLAS_DB_PATH: Path to ChromaDB database
       ATLAS_MAX_TOKENS: Maximum tokens in responses
   """
   ```

3. **Validation**: Always validate critical environment variables
   ```python
   from atlas.core import env

   # Validate required variables
   missing = env.validate_required_vars(["ANTHROPIC_API_KEY"])
   if missing:
       raise ValueError(f"Missing required environment variables: {missing}")
   ```

4. **Defaults**: Provide sensible defaults for non-critical variables
   ```python
   # Good: Default provided
   log_level = env.get_string("ATLAS_LOG_LEVEL", "INFO")

   # Bad: No default
   log_level = env.get_string("ATLAS_LOG_LEVEL")  # Could be None
   ```

5. **Type Conversion**: Use the appropriate getter method for each variable type
   ```python
   # Good: Uses type-specific getters
   max_tokens = env.get_int("ATLAS_MAX_TOKENS", 2000)
   debug_mode = env.get_bool("ATLAS_DEBUG_MODE", False)

   # Bad: Manual conversion
   max_tokens = int(os.environ.get("ATLAS_MAX_TOKENS", "2000"))  # Could raise ValueError
   ```

## API Key Management

### Secure Storage

Several options for securely storing API keys:

1. **Environment Variables**: Set for current session only
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

2. **.env File**: Store locally, add to .gitignore
   ```
   # .env
   ANTHROPIC_API_KEY=your_api_key_here
   ```

3. **Secret Management Tools**: Use tools like Hashicorp Vault or AWS Secrets Manager
   ```python
   import boto3

   def get_api_key_from_aws():
       client = boto3.client('secretsmanager')
       response = client.get_secret_value(SecretId='atlas/anthropic-api-key')
       return response['SecretString']

   # Use the key
   from atlas.core import env
   env.set_env_var("ANTHROPIC_API_KEY", get_api_key_from_aws())
   ```

### API Key Validation

Atlas can validate API keys to ensure they're working:

```python
from atlas.core import env

# Check a single provider
anthropic_validation = env.validate_api_keys(["anthropic"])
print(f"Anthropic API key valid: {anthropic_validation['anthropic']['valid']}")

# Check all available providers
all_validations = env.validate_api_keys()
for provider, result in all_validations.items():
    if result["valid"]:
        print(f"{provider}: Valid API key")
    else:
        print(f"{provider}: Invalid API key - {result.get('error')}")
```

## Configuration Examples

### Basic Command-Line Script

```python
#!/usr/bin/env python3
import os
import argparse
from atlas import create_query_client

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Atlas Query Tool")
    parser.add_argument("query", help="Query text")
    parser.add_argument("--provider", help="Model provider", default=None)
    parser.add_argument("--model", help="Model name", default=None)
    parser.add_argument("--capability", help="Model capability", choices=[
        "inexpensive", "efficient", "premium", "vision", "standard"
    ], default="inexpensive")
    parser.add_argument("--max-tokens", type=int, help="Maximum tokens", default=None)
    parser.add_argument("--db-path", help="Path to database", default=None)
    args = parser.parse_args()

    # Create client with arguments
    client = create_query_client(
        provider_name=args.provider,
        model_name=args.model,
        capability=args.capability if not args.model else None,
        db_path=args.db_path,
    )

    # Process query
    response = client.query(args.query)
    print(response)

if __name__ == "__main__":
    main()
```

### Web Service Configuration

```python
#!/usr/bin/env python3
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from atlas import create_query_client
from atlas.core.config import AtlasConfig
from atlas.core.errors import APIError

# Load environment
if "ATLAS_ENVIRONMENT" in os.environ:
    env_file = f".env.{os.environ['ATLAS_ENVIRONMENT']}"
    from atlas.core import env
    env.load_env_file(env_file)

# Create FastAPI app
app = FastAPI(title="Atlas API")

# Pydantic models for API
class QueryRequest(BaseModel):
    query: str
    provider: str = None
    model: str = None
    capability: str = None
    stream: bool = False

class QueryResponse(BaseModel):
    response: str
    model_used: str
    tokens_used: int = 0

# Create Atlas configuration
config = AtlasConfig(
    max_tokens=int(os.environ.get("ATLAS_MAX_TOKENS", "2000")),
    parallel_enabled=os.environ.get("ATLAS_PARALLEL_ENABLED", "false").lower() in ("true", "1", "yes"),
    worker_count=int(os.environ.get("ATLAS_WORKER_COUNT", "3"))
)

# Create clients for each provider
clients = {}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        # Get provider name
        provider_name = request.provider or os.environ.get("ATLAS_DEFAULT_PROVIDER", "anthropic")

        # Create client if needed
        if provider_name not in clients:
            clients[provider_name] = create_query_client(
                provider_name=provider_name,
                model_name=request.model,
                capability=request.capability,
                config=config
            )

        # Get client
        client = clients[provider_name]

        # Process query
        if request.stream:
            # Implement streaming
            raise NotImplementedError("Streaming not implemented in this example")
        else:
            # Process normal query
            response = client.query(request.query)

        return {
            "response": response,
            "model_used": client.agent.provider.model_name,
            "tokens_used": 0  # In a real implementation, you would track this
        }
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

## Configuration Troubleshooting

### Configuration Diagnostic Utility

Atlas includes a comprehensive diagnostic utility in the `scripts/debug` directory that helps you check and validate your configuration settings:

```bash
# Basic usage
uv run python -m atlas.scripts.debug.check_config

# Show detailed information including all environment variables
uv run python -m atlas.scripts.debug.check_config --verbose

# Check a specific provider
uv run python -m atlas.scripts.debug.check_config --provider anthropic

# Load from a custom .env file
uv run python -m atlas.scripts.debug.check_config --env-file /path/to/.env

# Validate API keys (makes API calls)
uv run python -m atlas.scripts.debug.check_config --validate-api-keys
```

The diagnostic tool provides:

- **Environment Variables**: Shows all Atlas-related environment variables by category
- **Configuration Object**: Displays current AtlasConfig settings and their sources
- **Provider Availability**: Shows which providers are available and lists their models
- **Database Settings**: Displays information about the ChromaDB database configuration
- **Path Information**: Shows important directories and .env file locations
- **API Key Validation**: Optional feature to verify API keys are valid

This is especially useful when:
- Setting up Atlas for the first time
- Debugging configuration-related issues
- Verifying which provider models are available
- Checking if API keys are properly configured

Example output:
```
=== Environment Variables ===

Application Configuration:
  ATLAS_ENV_PATH: None (NOT SET)
  ATLAS_LOG_LEVEL: INFO (SET)
  ATLAS_DB_PATH: /users/username/atlas_db (SET)
  ATLAS_COLLECTION_NAME: atlas_knowledge_base (SET)

API Keys:
  ANTHROPIC_API_KEY: sk-a...nxyz (SET)
  OPENAI_API_KEY: None (NOT SET)

=== Provider Availability ===

Anthropic Provider:
  Status: AVAILABLE
  API Key: SET
  Available Models:
    - claude-3-7-sonnet-20250219
    - claude-3-5-sonnet-20240620
    - claude-3-opus-20240229
```

### Common Issues

1. **Missing API Key**:
   ```
   ConfigurationError: ANTHROPIC_API_KEY must be provided or set as an environment variable
   ```

   **Solution**: Set the API key in your environment or .env file
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

2. **Invalid Database Path**:
   ```
   ValidationError: Invalid configuration settings
   ```

   **Solution**: Ensure the database path is valid and accessible
   ```python
   import os
   from pathlib import Path

   # Create directory if it doesn't exist
   db_path = Path(os.environ.get("ATLAS_DB_PATH", "~/atlas_chroma_db")).expanduser()
   os.makedirs(db_path, exist_ok=True)
   ```

3. **Provider Not Available**:
   ```
   ValueError: Provider 'openai' not available - API key not configured
   ```

   **Solution**: Check provider availability before using
   ```python
   from atlas.core import env

   available_providers = env.get_available_providers()
   if "openai" not in available_providers or not available_providers["openai"]:
       print("OpenAI provider not available - check API key")
       # Fall back to another provider
   ```

4. **Python-dotenv Not Installed**:
   ```
   WARNING:atlas.core.env:python-dotenv not available, skipping .env file loading
   ```

   **Solution**: Install the python-dotenv package
   ```bash
   uv pip install python-dotenv
   ```

5. **Incompatible Model and Provider**:
   ```
   ValueError: Model 'gpt-4o' is not compatible with the anthropic provider
   ```

   **Solution**: Use the auto-detection feature or specify the correct provider
   ```python
   # Let Atlas auto-detect the provider
   provider = create_provider(model_name="gpt-4o")
   
   # Or specify the correct provider
   provider = create_provider(provider_name="openai", model_name="gpt-4o")
   ```

### Manual Debugging

For manual debugging of configuration issues:

```python
# Set debug log level for detailed logs
import logging
logging.basicConfig(level=logging.DEBUG)

# Print all environment variables
from atlas.core import env
env.load_environment(force_reload=True)
print("Environment variables:")
for key, value in env._ENV_CACHE.items():
    # Mask API keys for security
    if "API_KEY" in key:
        masked_value = value[:4] + "..." + value[-4:] if value else None
        print(f"  {key}: {masked_value}")
    else:
        print(f"  {key}: {value}")

# Print config details
from atlas.core.config import AtlasConfig
config = AtlasConfig()
print("Configuration:")
for key, value in config.to_dict().items():
    print(f"  {key}: {value}")
```

## Related Documentation

- [Environment Variables Reference](../reference/env_variables.md)
- [API Reference](../reference/api.md)
- [Model Providers](../components/providers/)
- [Telemetry System](../components/core/telemetry.md)