# Environment Variables Reference

This document provides a comprehensive reference of all environment variables used in the Atlas framework.

## Environment Variable Handling

Atlas uses a centralized environment variable management system through the `atlas.core.env` module, ensuring consistent handling across the codebase with proper validation and type conversion.

## Loading Environment Variables

Environment variables can be set:
- Directly in the shell
- Through a `.env` file in the project root
- Through a custom path using `ATLAS_ENV_PATH`

**Order of precedence:**
1. OS environment variables (highest precedence)
2. `.env` file (lower precedence)
3. Default values (lowest precedence)

**Example `.env` file:**
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

## Available Environment Variables

### Core Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ATLAS_ENV_PATH` | Path to .env file | `.env` in current directory |
| `ATLAS_LOG_LEVEL` | Logging level | `INFO` |
| `ATLAS_DB_PATH` | Path to ChromaDB database | `~/atlas_chroma_db` |
| `ATLAS_DEV_MODE` | Enable development mode | `false` |

### API Keys (Infrastructure Configuration)

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | API key for Anthropic Claude | None |
| `OPENAI_API_KEY` | API key for OpenAI | None |
| `OPENAI_ORGANIZATION` | Organization ID for OpenAI | None |

### Telemetry

| Variable | Description | Default |
|----------|-------------|---------|
| `ATLAS_ENABLE_TELEMETRY` | Enable or disable telemetry | `true` |
| `ATLAS_TELEMETRY_CONSOLE_EXPORT` | Enable console exporting for telemetry | `false` |
| `ATLAS_TELEMETRY_LOG_LEVEL` | Log level for telemetry | `INFO` |

### Database

| Variable | Description | Default |
|----------|-------------|---------|
| `ATLAS_DB_PATH` | Path to ChromaDB database | `~/atlas_chroma_db` |
| `ATLAS_COLLECTION_NAME` | ChromaDB collection name | `atlas_knowledge_base` |

### Model Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `ATLAS_DEFAULT_PROVIDER` | Default model provider | `anthropic` |
| `ATLAS_DEFAULT_MODEL` | Default model to use | `claude-3-7-sonnet-20250219` |
| `ATLAS_DEFAULT_CAPABILITY` | Default capability when selecting models | `inexpensive` |
| `ATLAS_MAX_TOKENS` | Maximum tokens for model responses | `2000` |
| `ATLAS_{PROVIDER}_DEFAULT_MODEL` | Provider-specific model (e.g., `ATLAS_ANTHROPIC_DEFAULT_MODEL`) | Provider-specific default |

### Provider-Specific Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_API_ENDPOINT` | Endpoint URL for Ollama server | `http://localhost:11434/api` |
| `OLLAMA_CONNECT_TIMEOUT` | Connection timeout for Ollama server in seconds | `2` |
| `OLLAMA_REQUEST_TIMEOUT` | Request timeout for Ollama API calls in seconds | `60` |

### Development Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `ATLAS_DEV_MODE` | Enable development mode | `false` |
| `ATLAS_MOCK_API` | Use mock API responses | `false` |
| `TOKENIZERS_PARALLELISM` | Control tokenizer parallelism | `false` |

Note: The `SKIP_API_KEY_CHECK` environment variable has been removed. API key validation is now controlled through CLI arguments when needed.

## Using Environment Variables

### Accessing Environment Variables

Always use the `atlas.core.env` module to access environment variables:

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
```

### Configuration in AtlasConfig

The `AtlasConfig` class in `atlas.core.config` respects all environment variables and accepts direct parameter values:

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

## Best Practices

1. **Always use the env module** instead of direct `os.environ` access
2. **Use appropriate type conversion** functions for different variable types
3. **Validate required variables** early in the application startup
4. **Provide sensible defaults** when possible
5. **Use provider-specific functions** for API keys
6. **Keep sensitive information** in environment variables or `.env` files (never commit them)
7. **Use feature flags** for enabling/disabling features (e.g., `ATLAS_ENABLE_TELEMETRY`)

## Related Documentation

- [CLI Reference](./cli.md) - Details on how environment variables interact with command-line tools
- [Getting Started Guide](../guides/getting_started.md) - Setting up your environment
- [Configuration Guide](../guides/configuration.md) - Comprehensive configuration information