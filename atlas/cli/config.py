"""
CLI configuration utilities for Atlas.

This module provides utilities for converting CLI arguments to configuration
objects that can be used by the Atlas application components.
"""

import argparse
from typing import Dict, Any, Optional, Union

from atlas.core.logging import get_logger
from atlas.providers.options import ProviderOptions

logger = get_logger(__name__)


def create_provider_options_from_args(args: Union[argparse.Namespace, Dict[str, Any]]) -> ProviderOptions:
    """Create ProviderOptions from command-line arguments.
    
    This function converts argparse.Namespace or dictionary arguments to a
    ProviderOptions instance suitable for use with the provider factory.
    
    Args:
        args: Parsed command-line arguments as Namespace or dictionary
        
    Returns:
        ProviderOptions instance configured from args
    """
    # Convert Namespace to dictionary if needed
    if isinstance(args, argparse.Namespace):
        args_dict = vars(args)
    else:
        args_dict = args
    
    # Extract provider-related options
    provider_options = ProviderOptions(
        provider_name=args_dict.get("provider"),
        model_name=args_dict.get("model"),
        capability=args_dict.get("capability"),
        max_tokens=args_dict.get("max_tokens"),
    )
    
    # Extract any additional provider params from args
    extra_params = {}
    
    # Add any other provider-specific parameters here
    # Example: streaming = args_dict.get("streaming", False)
    
    if extra_params:
        provider_options.extra_params = extra_params
    
    return provider_options


def create_atlas_config_from_args(args: Union[argparse.Namespace, Dict[str, Any]]) -> Dict[str, Any]:
    """Create Atlas configuration from command-line arguments.
    
    This function converts argparse.Namespace or dictionary arguments to a
    configuration dictionary suitable for creating an AtlasConfig instance.
    
    Args:
        args: Parsed command-line arguments as Namespace or dictionary
        
    Returns:
        Dictionary of Atlas configuration options
    """
    # Convert Namespace to dictionary if needed
    if isinstance(args, argparse.Namespace):
        args_dict = vars(args)
    else:
        args_dict = args
    
    # Create config dictionary with basic options
    config = {
        "collection_name": args_dict.get("collection", "atlas_knowledge_base"),
        "db_path": args_dict.get("db_path"),
        "max_tokens": args_dict.get("max_tokens", 2000),
    }
    
    # Add optional parameters if present
    if "system_prompt" in args_dict and args_dict["system_prompt"]:
        config["system_prompt_file"] = args_dict["system_prompt"]
    
    # Add experimental parameters if applicable
    if args_dict.get("mode") == "controller" and args_dict.get("parallel"):
        config["parallel_enabled"] = True
        config["worker_count"] = args_dict.get("workers", 3)
    
    return config