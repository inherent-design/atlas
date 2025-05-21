"""
Settings and configuration classes for the Atlas knowledge system.

This module provides structured settings classes for knowledge retrieval
and document processing, ensuring consistent configuration across the system.
"""

from typing import Any


class RetrievalSettings:
    """Settings for knowledge retrieval operations."""

    def __init__(
        self,
        use_hybrid_search: bool = False,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        num_results: int = 5,
        min_relevance_score: float = 0.0,
        rerank_results: bool = False,
        include_metadata: list[str] | None = None,
    ):
        """Initialize retrieval settings with desired configuration.

        Args:
            use_hybrid_search: Whether to use hybrid search combining semantic and keyword search.
            semantic_weight: Weight for semantic search results (0-1).
            keyword_weight: Weight for keyword search results (0-1).
            num_results: Number of results to return.
            min_relevance_score: Minimum relevance score threshold for results.
            rerank_results: Whether to apply reranking to results.
            include_metadata: List of metadata fields to include in results.
        """
        self.use_hybrid_search = use_hybrid_search

        # Normalize weights if they don't sum to 1.0
        if semantic_weight + keyword_weight != 1.0:
            total = semantic_weight + keyword_weight
            self.semantic_weight = semantic_weight / total
            self.keyword_weight = keyword_weight / total
        else:
            self.semantic_weight = semantic_weight
            self.keyword_weight = keyword_weight

        self.num_results = num_results
        self.min_relevance_score = min_relevance_score
        self.rerank_results = rerank_results
        self.include_metadata = include_metadata or ["source", "file_type", "simple_id"]

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary for serialization.

        Returns:
            Dictionary representation of settings.
        """
        return {
            "use_hybrid_search": self.use_hybrid_search,
            "semantic_weight": self.semantic_weight,
            "keyword_weight": self.keyword_weight,
            "num_results": self.num_results,
            "min_relevance_score": self.min_relevance_score,
            "rerank_results": self.rerank_results,
            "include_metadata": self.include_metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetrievalSettings":
        """Create settings from dictionary.

        Args:
            data: Dictionary representation of settings.

        Returns:
            RetrievalSettings instance.
        """
        return cls(
            use_hybrid_search=data.get("use_hybrid_search", False),
            semantic_weight=data.get("semantic_weight", 0.7),
            keyword_weight=data.get("keyword_weight", 0.3),
            num_results=data.get("num_results", 5),
            min_relevance_score=data.get("min_relevance_score", 0.0),
            rerank_results=data.get("rerank_results", False),
            include_metadata=data.get("include_metadata"),
        )


class ProcessingSettings:
    """Settings for document processing operations."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        enable_deduplication: bool = True,
        deduplication_threshold: float = 0.85,
        embedding_strategy: str = "default",
        file_types: list[str] | None = None,
        preserve_structure: bool = True,
    ):
        """Initialize processing settings with desired configuration.

        Args:
            chunk_size: Maximum size of document chunks.
            chunk_overlap: Overlap between consecutive chunks.
            enable_deduplication: Whether to detect and mark duplicate content.
            deduplication_threshold: Similarity threshold for duplicate detection.
            embedding_strategy: Embedding strategy to use.
            file_types: List of file extensions to process.
            preserve_structure: Whether to preserve document structure.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.enable_deduplication = enable_deduplication
        self.deduplication_threshold = deduplication_threshold
        self.embedding_strategy = embedding_strategy
        self.file_types = file_types or ["md", "txt", "py", "js", "html"]
        self.preserve_structure = preserve_structure

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary for serialization.

        Returns:
            Dictionary representation of settings.
        """
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "enable_deduplication": self.enable_deduplication,
            "deduplication_threshold": self.deduplication_threshold,
            "embedding_strategy": self.embedding_strategy,
            "file_types": self.file_types,
            "preserve_structure": self.preserve_structure,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessingSettings":
        """Create settings from dictionary.

        Args:
            data: Dictionary representation of settings.

        Returns:
            ProcessingSettings instance.
        """
        return cls(
            chunk_size=data.get("chunk_size", 1000),
            chunk_overlap=data.get("chunk_overlap", 100),
            enable_deduplication=data.get("enable_deduplication", True),
            deduplication_threshold=data.get("deduplication_threshold", 0.85),
            embedding_strategy=data.get("embedding_strategy", "default"),
            file_types=data.get("file_types"),
            preserve_structure=data.get("preserve_structure", True),
        )
