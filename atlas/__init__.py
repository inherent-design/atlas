"""
Atlas: Advanced Multi-Modal Learning & Guidance Framework

A comprehensive meta-framework for knowledge representation, documentation,
and adaptive guidance systems.
"""

__version__ = "0.1.0"

# Direct exports for common use cases
from atlas.agents.base import AtlasAgent
from atlas.core.config import AtlasConfig
from atlas.query import AtlasQuery, create_query_client

# Define public API
__all__ = [
    "AtlasAgent",
    "AtlasConfig",
    "AtlasQuery",
    "create_query_client",
]
