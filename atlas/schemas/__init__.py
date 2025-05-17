"""
Marshmallow schema definitions for Atlas.

This package provides schema definitions for serialization, deserialization,
and validation of Atlas data structures. These schemas enable robust type checking,
validation, and conversion between different formats.

Schema architecture:
- definitions/: Contains pure schema definitions without post_load methods
  to avoid circular imports
- *.py files: Schema proxies that extend definitions with post_load methods
  that import implementation classes
"""

# Base schemas and utilities
from atlas.schemas.base import *
from atlas.schemas.validation import *

# Schema definition exports should be first (no post_load methods)
from atlas.schemas.definitions import *

# Schema proxy exports with post_load methods
from atlas.schemas.messages import *
from atlas.schemas.providers import *
from atlas.schemas.options import *
from atlas.schemas.config import *
from atlas.schemas.types import *
from atlas.schemas.agents import *
from atlas.schemas.knowledge import *
from atlas.schemas.tools import *