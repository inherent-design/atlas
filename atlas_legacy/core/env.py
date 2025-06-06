"""
Environment variable handling module for Atlas.

This module provides a centralized way to load and access environment
variables, with support for .env files, type conversion, validation,
and default values.

Environment variables are used for application-level configuration such as
infrastructure settings, logging, telemetry, and API credentials. They should
not be used for business logic configuration, which should be handled through
command-line arguments or configuration objects.

Environment variables:
    # Application Configuration
    ATLAS_ENV_PATH: Path to .env file (default: .env in current directory)
    ATLAS_LOG_LEVEL: Logging level (default: INFO)
    ATLAS_DB_PATH: Path to ChromaDB database (default: ~/atlas_chroma_db)

    # Telemetry Configuration
    ATLAS_ENABLE_TELEMETRY: Enable telemetry (default: true)
    ATLAS_TELEMETRY_CONSOLE_EXPORT: Enable console telemetry export (default: true)
    ATLAS_TELEMETRY_LOG_LEVEL: Telemetry log level (default: INFO)

    # API Credentials
    ANTHROPIC_API_KEY: API key for Anthropic
    OPENAI_API_KEY: API key for OpenAI
    OPENAI_ORGANIZATION: Organization ID for OpenAI (optional)

    # Model Configuration
    ATLAS_DEFAULT_PROVIDER: Default model provider (default: anthropic)
    ATLAS_DEFAULT_MODEL: Default model to use (provider-specific)
    ATLAS_DEFAULT_CAPABILITY: Default capability for model selection (default: inexpensive)
    ATLAS_ANTHROPIC_DEFAULT_MODEL: Default Anthropic model (default: claude-3-5-sonnet-20240620)
    ATLAS_OPENAI_DEFAULT_MODEL: Default OpenAI model (default: gpt-4o)
    ATLAS_OLLAMA_DEFAULT_MODEL: Default Ollama model (default: llama3)

    # Development Settings
    ATLAS_DEV_MODE: Enable development mode (default: false)
"""

import logging
import os
from typing import (
    Any,
)

# Import python-dotenv for .env file support
try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)

# Track if environment has been loaded
_ENV_LOADED = False

# Cache for environment variables
_ENV_CACHE: dict[str, str] = {}

# Known providers and their API key environment variables
PROVIDER_API_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "ollama": None,  # Ollama doesn't require an API key
}

# Provider-specific API endpoints and configuration
PROVIDER_ENDPOINTS = {
    "ollama": "OLLAMA_API_ENDPOINT",  # The endpoint for Ollama server
}

# Provider-specific timeout settings
PROVIDER_TIMEOUTS = {
    "ollama": {
        "connect": "OLLAMA_CONNECT_TIMEOUT",
        "request": "OLLAMA_REQUEST_TIMEOUT",
    }
}


def load_environment(force_reload: bool = False, env_path: str | None = None) -> dict[str, str]:
    """Load environment variables from all sources.

    This function loads environment variables from .env files and the OS environment,
    and caches them for faster access. It is automatically called on first access
    to any environment variable through this module's functions.

    Args:
        force_reload: Force reloading the environment even if already loaded.
        env_path: Optional path to .env file. If None, uses ATLAS_ENV_PATH or defaults to '.env'.

    Returns:
        Dictionary of environment variables.
    """
    global _ENV_LOADED, _ENV_CACHE

    # Skip if already loaded and not forcing reload
    if _ENV_LOADED and not force_reload:
        return _ENV_CACHE

    # Start with an empty cache
    _ENV_CACHE = {}

    # Load from .env file
    if DOTENV_AVAILABLE:
        # Get .env path (in order of priority):
        # 1. Explicitly passed env_path
        # 2. ATLAS_ENV_PATH environment variable
        # 3. Default ".env" in current directory
        env_file = env_path or os.environ.get("ATLAS_ENV_PATH") or ".env"
        env_path_expanded = os.path.expanduser(env_file)

        try:
            # Check if file exists before attempting to load
            if os.path.isfile(env_path_expanded):
                logger.debug(f"Loading environment from: {env_path_expanded}")
                # Load .env file into os.environ
                load_dotenv(env_path_expanded, override=True)
                logger.debug(f"Environment loaded from: {env_path_expanded}")
            else:
                if env_path:  # Only log warning if path was explicitly provided
                    logger.warning(f".env file not found at: {env_path_expanded}")
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e!s}")
    else:
        logger.debug("python-dotenv not available, skipping .env file loading")

    # Cache all environment variables
    for key, value in os.environ.items():
        _ENV_CACHE[key] = value

    _ENV_LOADED = True
    return _ENV_CACHE


def load_env_file(path: str | None = None) -> bool:
    """Load environment variables from .env file.

    Args:
        path: Path to .env file. If None, uses default path.

    Returns:
        True if file was loaded successfully, False otherwise.
    """
    if not DOTENV_AVAILABLE:
        logger.warning("python-dotenv not available, cannot load .env file")
        return False

    try:
        # Expand user directory in path if present
        expanded_path = os.path.expanduser(path) if path else None

        # Load environment and check if file was loaded
        load_environment(force_reload=True, env_path=expanded_path)

        # Check if the file was actually loaded
        if expanded_path and os.path.isfile(expanded_path):
            return True
        elif path:  # Only log warning if path was explicitly provided
            logger.warning(f".env file not found at: {expanded_path}")
            return False
        return False
    except Exception as e:
        logger.warning(f"Failed to load .env file: {e!s}")
        return False


def get_env_paths() -> list[str]:
    """Get possible paths for .env files.

    Returns:
        List of paths where .env files might be located.
    """
    # Common locations for .env files
    paths = []

    # Current directory
    paths.append(os.path.abspath(".env"))

    # Parent directory (if running from a subdirectory)
    parent_env = os.path.abspath(os.path.join("..", ".env"))
    if os.path.isfile(parent_env):
        paths.append(parent_env)

    # From ATLAS_ENV_PATH
    env_path = os.environ.get("ATLAS_ENV_PATH")
    if env_path:
        paths.append(os.path.abspath(os.path.expanduser(env_path)))

    return paths


def _ensure_env_loaded() -> None:
    """Ensure environment is loaded."""
    if not _ENV_LOADED:
        load_environment()


def get_string(name: str, default: str | None = None) -> str | None:
    """Get a string environment variable.

    Args:
        name: Name of the environment variable.
        default: Default value if variable is not set.

    Returns:
        String value of the variable, or default if not set.
    """
    _ensure_env_loaded()
    value = _ENV_CACHE.get(name)
    if value is None or value.strip() == "":
        return default
    return value


def get_int(name: str, default: int | None = None) -> int | None:
    """Get an integer environment variable.

    Args:
        name: Name of the environment variable.
        default: Default value if variable is not set or not convertible to int.

    Returns:
        Integer value of the variable, or default if not set or not an integer.
    """
    _ensure_env_loaded()
    value = _ENV_CACHE.get(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        logger.warning(f"Environment variable {name} is not a valid integer: {value}")
        return default


def get_float(name: str, default: float | None = None) -> float | None:
    """Get a float environment variable.

    Args:
        name: Name of the environment variable.
        default: Default value if variable is not set or not convertible to float.

    Returns:
        Float value of the variable, or default if not set or not a float.
    """
    _ensure_env_loaded()
    value = _ENV_CACHE.get(name)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        logger.warning(f"Environment variable {name} is not a valid float: {value}")
        return default


def get_bool(name: str, default: bool = False) -> bool:
    """Get a boolean environment variable.

    Values considered True: 1, true, yes, on, enable, enabled
    Values considered False: 0, false, no, off, disable, disabled
    Case-insensitive.

    Args:
        name: Name of the environment variable.
        default: Default value if variable is not set.

    Returns:
        Boolean value of the variable, or default if not set.
    """
    _ensure_env_loaded()
    value = _ENV_CACHE.get(name)

    if value is None:
        return default

    value = value.lower()
    if value in ("1", "true", "yes", "on", "enable", "enabled"):
        return True
    elif value in ("0", "false", "no", "off", "disable", "disabled"):
        return False
    else:
        logger.warning(f"Environment variable {name} is not a valid boolean: {value}")
        return default


def get_list(name: str, default: list[str] | None = None, delimiter: str = ",") -> list[str]:
    """Get a list environment variable.

    Args:
        name: Name of the environment variable.
        default: Default value if variable is not set.
        delimiter: Delimiter to split the variable value.

    Returns:
        List of strings from the variable, or default if not set.
    """
    _ensure_env_loaded()
    value = _ENV_CACHE.get(name)

    if value is None:
        return default or []

    return [item.strip() for item in value.split(delimiter)]


def get_required_string(name: str) -> str:
    """Get a required string environment variable.

    Args:
        name: Name of the environment variable.

    Returns:
        String value of the variable.

    Raises:
        ValueError: If the variable is not set.
    """
    value = get_string(name)
    if value is None:
        raise ValueError(f"Required environment variable {name} is not set")
    return value


def get_api_key(provider: str) -> str | None:
    """Get an API key for a provider.

    Args:
        provider: Name of the provider (anthropic, openai, ollama).

    Returns:
        API key for the provider, or None if not set or provider unknown.
    """
    # Normalize provider name
    provider = provider.lower()

    # Check if provider is known
    if provider not in PROVIDER_API_KEYS:
        logger.warning(f"Unknown provider: {provider}")
        return None

    # Get environment variable name for API key
    env_var = PROVIDER_API_KEYS.get(provider)

    # Ollama doesn't use an API key
    if env_var is None:
        return None

    return get_string(env_var)


def get_provider_endpoint(provider: str) -> str | None:
    """Get the API endpoint for a provider.

    Args:
        provider: Name of the provider (anthropic, openai, ollama).

    Returns:
        API endpoint for the provider, or None if not set or provider unknown.
    """
    # Normalize provider name
    provider = provider.lower()

    # Check if provider is known
    if provider not in PROVIDER_ENDPOINTS:
        logger.warning(f"Unknown provider endpoint configuration for: {provider}")
        return None

    # Get environment variable name for API endpoint
    env_var = PROVIDER_ENDPOINTS.get(provider)

    # If no environment variable is defined for this provider
    if env_var is None:
        return None

    return get_string(env_var)


def get_provider_timeout(provider: str, timeout_type: str) -> float | None:
    """Get timeout setting for a provider.

    Args:
        provider: Name of the provider (anthropic, openai, ollama).
        timeout_type: Type of timeout ("connect" or "request").

    Returns:
        Timeout value in seconds, or None if not set or provider unknown.
    """
    # Normalize provider name
    provider = provider.lower()

    # Check if provider has timeout settings
    if provider not in PROVIDER_TIMEOUTS:
        return None

    # Check if the timeout type exists for this provider
    if timeout_type not in PROVIDER_TIMEOUTS[provider]:
        return None

    # Get environment variable name for the timeout
    env_var = PROVIDER_TIMEOUTS[provider][timeout_type]

    # Get the value
    return get_float(env_var)


def has_api_key(provider: str) -> bool:
    """Check if an API key is available for a provider.

    Args:
        provider: Name of the provider (anthropic, openai, ollama).

    Returns:
        True if API key is available, False otherwise.
    """
    # Normalize provider name
    provider = provider.lower()

    # Ollama doesn't use an API key, so it's always available
    if provider == "ollama":
        return True

    # Check if provider has an API key
    api_key = get_api_key(provider)
    return bool(api_key)


def get_available_providers() -> dict[str, bool]:
    """Get available providers based on API keys.

    Returns:
        Dictionary of provider names and availability status.
    """
    return {provider: has_api_key(provider) for provider in PROVIDER_API_KEYS}


def validate_provider_requirements(providers: list[str]) -> dict[str, bool]:
    """Validate that requirements for specified providers are met.

    This is a basic validation that only checks if API keys are set, not if they are valid.
    For more thorough validation, use validate_api_keys function.

    Args:
        providers: List of provider names to validate.

    Returns:
        Dictionary mapping provider names to validation status.
    """
    results = {}

    for provider in providers:
        provider = provider.lower()

        if provider not in PROVIDER_API_KEYS:
            results[provider] = False
            continue

        # Ollama availability is checked differently
        if provider == "ollama":
            try:
                import requests

                # Get API endpoint from environment or fall back to default
                api_endpoint = get_provider_endpoint(provider) or "http://localhost:11434/api"

                # Get connect timeout from environment or use default
                connect_timeout = get_provider_timeout("ollama", "connect") or 2

                try:
                    response = requests.get(f"{api_endpoint}/version", timeout=connect_timeout)
                    results[provider] = response.status_code == 200
                    if not results[provider]:
                        logger.warning(f"Ollama server returned status code {response.status_code}")
                except requests.exceptions.ConnectionError as e:
                    logger.warning(f"Unable to connect to Ollama server at {api_endpoint}: {e}")
                    results[provider] = False
                except requests.exceptions.Timeout as e:
                    logger.warning(f"Timeout connecting to Ollama server at {api_endpoint}: {e}")
                    results[provider] = False
                except Exception as e:
                    logger.warning(f"Error checking Ollama: {e}")
                    results[provider] = False
            except ImportError:
                results[provider] = False
        else:
            # Check if API key is available
            results[provider] = has_api_key(provider)

    return results


def validate_api_keys(
    providers: list[str] | None = None, skip_validation: bool = False
) -> dict[str, dict[str, Any]]:
    """Validate API keys for specified providers using API calls.

    This performs a thorough validation by actually making API calls to the providers.
    For a faster, basic check that only verifies keys are set, use validate_provider_requirements.

    Args:
        providers: List of provider names to validate. If None, validates all available providers.
        skip_validation: If True, skips the actual API call validation and only checks if keys are present.

    Returns:
        Dictionary mapping provider names to validation results, with each result containing:
        - valid: Whether the key is valid
        - error: Error message if validation failed
        - key_present: Whether the key is present (but might be invalid)
    """
    try:
        # If no providers specified, check all known providers
        if providers is None:
            providers = list(PROVIDER_API_KEYS.keys())

        # Import at function scope to avoid circular imports
        from atlas.providers.factory import create_provider

        results = {}

        for provider_name in providers:
            provider_name = provider_name.lower()

            if provider_name not in PROVIDER_API_KEYS:
                results[provider_name] = {
                    "valid": False,
                    "provider": provider_name,
                    "key_present": False,
                    "error": f"Unknown provider: {provider_name}",
                }
                continue

            # Skip validation entirely if specific provider doesn't need a key
            if provider_name == "ollama":
                # For Ollama, just check if the server is running
                try:
                    import requests

                    # Get API endpoint and timeout
                    api_endpoint = (
                        get_provider_endpoint(provider_name) or "http://localhost:11434/api"
                    )
                    connect_timeout = get_provider_timeout("ollama", "connect") or 2

                    try:
                        response = requests.get(f"{api_endpoint}/version", timeout=connect_timeout)
                        valid = response.status_code == 200
                        results[provider_name] = {
                            "valid": valid,
                            "provider": provider_name,
                            "key_present": True,  # Ollama doesn't need a key
                            "error": (
                                None
                                if valid
                                else f"Ollama server at {api_endpoint} not running or not responding"
                            ),
                        }
                    except requests.exceptions.ConnectionError as e:
                        results[provider_name] = {
                            "valid": False,
                            "provider": provider_name,
                            "key_present": True,  # Ollama doesn't need a key
                            "error": f"Unable to connect to Ollama server at {api_endpoint}: {e!s}",
                        }
                    except requests.exceptions.Timeout as e:
                        results[provider_name] = {
                            "valid": False,
                            "provider": provider_name,
                            "key_present": True,  # Ollama doesn't need a key
                            "error": f"Timeout connecting to Ollama server at {api_endpoint}: {e!s}",
                        }
                    except Exception as e:
                        results[provider_name] = {
                            "valid": False,
                            "provider": provider_name,
                            "key_present": True,  # Ollama doesn't need a key
                            "error": f"Error connecting to Ollama: {e!s}",
                        }
                except ImportError as e:
                    results[provider_name] = {
                        "valid": False,
                        "provider": provider_name,
                        "key_present": True,  # Ollama doesn't need a key
                        "error": f"Requests package not available: {e!s}",
                    }
                continue

            # Check if API key is present first
            key_present = has_api_key(provider_name)
            if not key_present:
                results[provider_name] = {
                    "valid": False,
                    "provider": provider_name,
                    "key_present": False,
                    "error": f"No API key found for {provider_name}",
                }
                continue

            # If skipping validation, just return that the key is present
            if skip_validation:
                results[provider_name] = {
                    "valid": True,  # Assume valid without checking
                    "provider": provider_name,
                    "key_present": True,
                    "error": None,
                }
                continue

            # Create provider and validate the key
            try:
                provider = create_provider(provider_name=provider_name)
                results[provider_name] = provider.validate_api_key_detailed()
            except Exception as e:
                results[provider_name] = {
                    "valid": False,
                    "provider": provider_name,
                    "key_present": True,
                    "error": f"Error validating {provider_name} API key: {e!s}",
                }

        return results

    except Exception as e:
        logger.error(f"Error validating API keys: {e}")
        # Return basic validation results based on key presence
        if providers is None:
            providers = list(PROVIDER_API_KEYS.keys())

        return {
            provider: {
                "valid": has_api_key(provider) if provider != "ollama" else True,
                "provider": provider,
                "key_present": has_api_key(provider) if provider != "ollama" else True,
                "error": str(e) if not has_api_key(provider) and provider != "ollama" else None,
            }
            for provider in providers
        }


def validate_required_vars(names: list[str]) -> list[str]:
    """Validate that required variables are present.

    Args:
        names: List of required variable names.

    Returns:
        List of missing variables.
    """
    _ensure_env_loaded()
    missing = []

    for name in names:
        if name not in _ENV_CACHE:
            missing.append(name)

    return missing


def register_api_key_var(provider: str, env_var: str | None) -> None:
    """Register a new provider API key environment variable.

    Args:
        provider: Provider name.
        env_var: Environment variable name for API key, or None if no key required.
    """
    global PROVIDER_API_KEYS
    PROVIDER_API_KEYS[provider.lower()] = env_var


def set_env_var(name: str, value: str, update_os_environ: bool = True) -> None:
    """Set an environment variable.

    Args:
        name: Name of the environment variable.
        value: Value to set.
        update_os_environ: Whether to update os.environ (default: True).
    """
    _ensure_env_loaded()

    # Update cache
    _ENV_CACHE[name] = value

    # Update os.environ if requested
    if update_os_environ:
        os.environ[name] = value
    # Note: When update_os_environ is False, the variable is only set in the cache
    # and will not persist beyond the current process. This is primarily for testing.
