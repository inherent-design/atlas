#!/usr/bin/env python3
"""
Configuration Checker for Atlas

This script provides a diagnostic view of the current environment variables,
configuration settings and provider availability in the Atlas framework.
It's useful for debugging configuration issues and understanding the
current application state.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("check_config")

# Ensure atlas package is importable
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, parent_dir)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Check Atlas configuration settings and environment variables"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Show more detailed information"
    )
    parser.add_argument(
        "--provider", 
        choices=["anthropic", "openai", "ollama", "all"],
        default="all",
        help="Check specific provider(s)"
    )
    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to custom .env file to load"
    )
    parser.add_argument(
        "--validate-api-keys",
        action="store_true",
        help="Validate API keys by making test requests (requires internet)"
    )
    
    return parser.parse_args()


def format_value(key: str, value: Any, mask_sensitive: bool = True) -> str:
    """Format a value for display, masking sensitive information."""
    if value is None:
        return "None"
    
    # Mask sensitive information like API keys
    if mask_sensitive and any(sensitive in key.lower() for sensitive in ["key", "token", "secret", "password"]):
        if isinstance(value, str) and len(value) > 8:
            return f"{value[:4]}...{value[-4:]}"
        return "****"
    
    # Format special cases
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return str(value)
    
    return str(value)


def check_environment_variables(verbose: bool = False):
    """Check and display environment variables related to Atlas."""
    from atlas.core import env
    
    # Force reload environment to get the latest values
    env.load_environment(force_reload=True)
    
    # Define categories for environment variables
    categories = {
        "Application Configuration": [
            "ATLAS_ENV_PATH",
            "ATLAS_LOG_LEVEL",
            "ATLAS_DB_PATH",
            "ATLAS_COLLECTION_NAME",
            "ATLAS_DEV_MODE",
        ],
        "Telemetry Configuration": [
            "ATLAS_ENABLE_TELEMETRY",
            "ATLAS_TELEMETRY_CONSOLE_EXPORT",
            "ATLAS_TELEMETRY_LOG_LEVEL",
        ],
        "API Keys": [
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "OPENAI_ORGANIZATION",
        ],
        "Model Settings": [
            "ATLAS_DEFAULT_PROVIDER",
            "ATLAS_DEFAULT_MODEL",
            "ATLAS_MAX_TOKENS",
            "ATLAS_ANTHROPIC_DEFAULT_MODEL",
            "ATLAS_OPENAI_DEFAULT_MODEL",
            "ATLAS_OLLAMA_DEFAULT_MODEL",
        ],
    }
    
    print("\n=== Environment Variables ===\n")
    
    # Display variables by category
    for category, var_names in categories.items():
        print(f"{category}:")
        for var_name in var_names:
            value = env.get_string(var_name)
            formatted_value = format_value(var_name, value)
            status = "SET" if value is not None else "NOT SET"
            print(f"  {var_name}: {formatted_value} ({status})")
        print()
    
    # Display all environment variables if verbose
    if verbose:
        print("All Environment Variables:")
        for key, value in sorted(env._ENV_CACHE.items()):
            # Skip variables already displayed in categories
            if any(key in category_vars for category_vars in categories.values()):
                continue
            # Skip standard environment variables
            if key.startswith(("PATH", "PYTHON", "HOME", "USER", "SHELL", "TERM")):
                continue
            print(f"  {key}: {format_value(key, value)}")
        print()


def check_config_object():
    """Check and display the Atlas configuration object."""
    from atlas.core.config import AtlasConfig
    
    # Create a default config object
    config = AtlasConfig()
    
    print("\n=== Atlas Configuration ===\n")
    
    # Display config fields
    config_dict = config.to_dict()
    for key, value in config_dict.items():
        formatted_value = format_value(key, value)
        source = "Environment" if getattr(config, f"_{key}", None) is None else "Default"
        print(f"  {key}: {formatted_value} (Source: {source})")
    
    print()


def check_provider_availability(provider_names: List[str], validate_api_keys: bool = False):
    """Check and display provider availability and details."""
    from atlas.core import env
    from atlas.providers.factory import discover_providers, create_provider
    
    print("\n=== Provider Availability ===\n")
    
    # Get available providers
    available_providers = discover_providers()
    
    # Check specific provider(s)
    for provider_name in provider_names:
        # Skip "all" as it's a special case
        if provider_name == "all":
            continue
        
        print(f"{provider_name.capitalize()} Provider:")
        has_key = env.has_api_key(provider_name)
        status = "AVAILABLE" if has_key or provider_name == "ollama" else "NOT AVAILABLE"
        print(f"  Status: {status}")
        
        if provider_name == "ollama":
            print("  API Key: Not required")
            # Check Ollama server
            try:
                import requests
                response = requests.get("http://localhost:11434/api/version", timeout=1)
                print(f"  Server: RUNNING (Version: {response.json().get('version', 'unknown')})")
            except Exception as e:
                print(f"  Server: NOT RUNNING ({str(e)})")
        else:
            env_var = f"{provider_name.upper()}_API_KEY"
            api_key = env.get_string(env_var)
            print(f"  API Key: {'SET' if api_key else 'NOT SET'}")
        
        # Get available models if provider is available
        if provider_name in available_providers and (has_key or provider_name == "ollama"):
            print("  Available Models:")
            try:
                provider = create_provider(provider_name=provider_name)
                models = provider.get_available_models()
                for model in models:
                    print(f"    - {model}")
            except Exception as e:
                print(f"    Error retrieving models: {str(e)}")
        
        # Validate API key if requested
        if validate_api_keys and (has_key or provider_name == "ollama"):
            print("  API Key Validation:")
            try:
                validation_result = env.validate_api_keys([provider_name], skip_validation=False)
                result = validation_result.get(provider_name, {})
                if result.get("valid", False):
                    print("    VALID")
                else:
                    print(f"    INVALID: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"    Error validating API key: {str(e)}")
        
        print()
    
    # Print summary of all providers
    if "all" in provider_names or len(provider_names) > 1:
        print("Provider Summary:")
        for provider_name, models in available_providers.items():
            status = "AVAILABLE" if models or provider_name == "ollama" else "NOT AVAILABLE"
            print(f"  {provider_name.capitalize()}: {status}")
        print()


def check_database_settings():
    """Check and display database settings."""
    from atlas.core.config import AtlasConfig
    from pathlib import Path
    
    print("\n=== Database Settings ===\n")
    
    # Get database settings from config
    config = AtlasConfig()
    db_path = config.db_path
    collection_name = config.collection_name
    
    # Display settings
    print(f"  DB Path: {db_path}")
    print(f"  Collection Name: {collection_name}")
    
    # Check if the database path exists
    db_path_expanded = Path(db_path).expanduser()
    if db_path_expanded.exists():
        print(f"  DB Path Status: EXISTS")
        print(f"  DB Path Type: {'DIRECTORY' if db_path_expanded.is_dir() else 'FILE'}")
        if db_path_expanded.is_dir():
            # Check for typical ChromaDB files
            chroma_files = list(db_path_expanded.glob("chroma-*"))
            if chroma_files:
                print(f"  ChromaDB Files: {len(chroma_files)} files found")
            else:
                print("  ChromaDB Files: None found (might be empty or not a ChromaDB directory)")
    else:
        print("  DB Path Status: DOES NOT EXIST (will be created when needed)")
    
    print()


def check_paths_and_directories():
    """Check and display relevant file paths and directories."""
    print("\n=== Paths and Directories ===\n")
    
    # Get the current working directory
    cwd = os.getcwd()
    print(f"  Current Working Directory: {cwd}")
    
    # Get the Atlas package directory
    atlas_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"  Atlas Package Directory: {atlas_dir}")
    
    # Check for .env files in common locations
    env_files = []
    
    # Check current directory
    if os.path.isfile(os.path.join(cwd, ".env")):
        env_files.append(os.path.join(cwd, ".env"))
    
    # Check atlas directory
    if os.path.isfile(os.path.join(atlas_dir, ".env")):
        env_files.append(os.path.join(atlas_dir, ".env"))
    
    # Check parent directory
    parent_dir = os.path.dirname(cwd)
    if os.path.isfile(os.path.join(parent_dir, ".env")):
        env_files.append(os.path.join(parent_dir, ".env"))
    
    # Display found .env files
    if env_files:
        print("  Found .env Files:")
        for env_file in env_files:
            print(f"    - {env_file}")
    else:
        print("  Found .env Files: None")
    
    # Check ATLAS_ENV_PATH
    from atlas.core import env
    atlas_env_path = env.get_string("ATLAS_ENV_PATH")
    if atlas_env_path:
        atlas_env_path_expanded = os.path.expanduser(atlas_env_path)
        if os.path.isfile(atlas_env_path_expanded):
            print(f"  ATLAS_ENV_PATH: {atlas_env_path_expanded} (EXISTS)")
        else:
            print(f"  ATLAS_ENV_PATH: {atlas_env_path_expanded} (DOES NOT EXIST)")
    else:
        print("  ATLAS_ENV_PATH: Not set")
    
    print()


def main():
    """Main function to check Atlas configuration."""
    args = parse_args()
    
    # Print header
    print("\n" + "=" * 60)
    print(" Atlas Configuration Checker ".center(60, "="))
    print("=" * 60)
    
    # Load custom .env file if specified
    if args.env_file:
        from atlas.core import env
        if env.load_env_file(args.env_file):
            print(f"\nLoaded environment from: {args.env_file}")
        else:
            print(f"\nFailed to load environment from: {args.env_file}")
    
    # Check paths and directories
    check_paths_and_directories()
    
    # Check environment variables
    check_environment_variables(args.verbose)
    
    # Check configuration object
    check_config_object()
    
    # Check database settings
    check_database_settings()
    
    # Check provider availability
    providers_to_check = ["anthropic", "openai", "ollama"] if args.provider == "all" else [args.provider]
    check_provider_availability(providers_to_check, args.validate_api_keys)
    
    # Print footer
    print("=" * 60)
    print(" End of Configuration Check ".center(60, "="))
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()