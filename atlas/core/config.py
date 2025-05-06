"""
Configuration for Atlas.

This module defines configuration options and settings for the Atlas framework.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from atlas.core.errors import ConfigurationError, ValidationError, ErrorSeverity

logger = logging.getLogger(__name__)


class AtlasConfig:
    """Configuration for Atlas."""

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        db_path: Optional[str] = None,
        model_name: str = "claude-3-5-sonnet-20240620",
        max_tokens: int = 2000,
        parallel_enabled: bool = False,
        worker_count: int = 3,
    ):
        """Initialize Atlas configuration.

        Args:
            anthropic_api_key: API key for Anthropic. If None, read from environment.
            collection_name: Name of the ChromaDB collection.
            db_path: Path to ChromaDB storage. If None, use default in home directory.
            model_name: Name of the Anthropic model to use.
            max_tokens: Maximum number of tokens in responses.
            parallel_enabled: Enable parallel processing with LangGraph.
            worker_count: Number of worker agents in parallel mode.
        """
        # API key (from args or environment)
        self.anthropic_api_key = anthropic_api_key or os.environ.get(
            "ANTHROPIC_API_KEY"
        )
        # Only validate API key if not explicitly skipped
        if not self.anthropic_api_key and not os.environ.get("SKIP_API_KEY_CHECK"):
            raise ConfigurationError(
                message="ANTHROPIC_API_KEY must be provided or set as an environment variable",
                severity=ErrorSeverity.ERROR,
                details={
                    "missing_config": "ANTHROPIC_API_KEY",
                    "config_source": "environment",
                }
            )

        # ChromaDB settings
        self.collection_name = collection_name

        # Set DB path (default to user's home directory if not specified)
        if not db_path:
            home_dir = Path.home()
            db_path = str(home_dir / "atlas_chroma_db")

        self.db_path = db_path

        # Model settings
        self.model_name = model_name
        self.max_tokens = max_tokens

        # Parallel processing settings
        self.parallel_enabled = parallel_enabled
        self.worker_count = worker_count
        
        # Validate configuration
        try:
            self.validate()
            logger.debug("Configuration validated successfully")
        except ValidationError as e:
            # Log the validation error but don't raise it again
            # This allows partially valid configurations to be used
            e.log()
            logger.warning("Configuration validation failed, but proceeding with partial configuration")

    def validate(self) -> None:
        """Validate configuration settings.
        
        Raises:
            ValidationError: If any configuration settings are invalid.
        """
        validation_errors = {}
        
        # Validate model name
        if not self.model_name or not isinstance(self.model_name, str):
            validation_errors["model_name"] = ["Model name must be a non-empty string"]
        
        # Validate token count
        if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
            validation_errors["max_tokens"] = ["Max tokens must be a positive integer"]
        
        # Validate worker count
        if self.parallel_enabled:
            if not isinstance(self.worker_count, int) or self.worker_count <= 0:
                validation_errors["worker_count"] = ["Worker count must be a positive integer"]
        
        # Validate database path
        if not self.db_path or not isinstance(self.db_path, str):
            validation_errors["db_path"] = ["Database path must be a non-empty string"]
        
        # Raise error if any validation failures
        if validation_errors:
            raise ValidationError(
                message="Invalid configuration settings",
                field_errors=validation_errors,
                severity=ErrorSeverity.ERROR,
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        # Note: We don't include the API key in the dict for security
        return {
            "collection_name": self.collection_name,
            "db_path": self.db_path,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "parallel_enabled": self.parallel_enabled,
            "worker_count": self.worker_count,
        }
