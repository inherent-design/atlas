"""
Multi-provider capable Atlas agent.

This module re-exports the unified AtlasAgent and related functions for backward compatibility.
This module is deprecated and will be removed in a future version.
"""

import warnings
from atlas.agents.base import AtlasAgent, list_available_providers

# Issue deprecation warning
warnings.warn(
    "The multi_provider_base.py module is deprecated and will be removed in a future version. "
    "Import AtlasAgent directly from atlas.agents.base instead.",
    DeprecationWarning,
    stacklevel=2
)

# For backward compatibility, re-export MultiProviderAgent as an alias to AtlasAgent
MultiProviderAgent = AtlasAgent