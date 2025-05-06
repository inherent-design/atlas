"""Core functionality for Atlas."""

from atlas.core.config import AtlasConfig
from atlas.core.prompts import load_system_prompt
from atlas.core.errors import (
    AtlasError,
    ConfigurationError,
    APIError,
    ValidationError,
    AuthenticationError,
    ResourceError,
    ErrorSeverity,
    ErrorCategory,
    safe_execute,
    get_error_message,
    convert_exception,
)
