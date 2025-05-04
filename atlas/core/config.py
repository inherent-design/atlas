"""
Configuration for Atlas.

This module defines configuration options and settings for the Atlas framework.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class AtlasConfig:
    """Configuration for Atlas."""

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        db_path: Optional[str] = None,
        model_name: str = "claude-3-sonnet-20240229",
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
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be provided or set as an environment variable"
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
