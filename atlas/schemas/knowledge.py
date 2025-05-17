"""
Knowledge system schemas for Atlas.

This module provides Marshmallow schemas for knowledge-related structures,
including document chunking, embedding, retrieval, and filtering operations.

This module extends pure schema definitions with post_load methods that import
implementation classes when needed to avoid circular import issues.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from enum import Enum

from marshmallow import post_load, pre_load, validates, validates_schema, ValidationError

from atlas.schemas.base import AtlasSchema
from atlas.schemas.definitions.knowledge import (
    chunking_strategy_enum as base_chunking_strategy_enum,
    chunking_config_schema as base_chunking_config_schema,
    document_metadata_schema as base_document_metadata_schema,
    document_chunk_schema as base_document_chunk_schema,
    embedding_model_config_schema as base_embedding_model_config_schema,
    retrieval_filter_operator as base_retrieval_filter_operator,
    retrieval_filter_condition_schema as base_retrieval_filter_condition_schema,
    retrieval_filter_group_schema as base_retrieval_filter_group_schema,
    retrieval_filter_schema as base_retrieval_filter_schema,
    retrieval_settings_schema as base_retrieval_settings_schema,
    scoring_strategy_enum as base_scoring_strategy_enum,
    scoring_config_schema as base_scoring_config_schema,
    hybrid_search_config_schema as base_hybrid_search_config_schema,
    retrieval_result_schema as base_retrieval_result_schema
)


# Re-export enums directly
ChunkingStrategyEnum = base_chunking_strategy_enum
RetrievalFilterOperator = base_retrieval_filter_operator
ScoringStrategyEnum = base_scoring_strategy_enum


class ChunkingConfigSchema(base_chunking_config_schema.__class__):
    """Schema for document chunking configuration with implementation conversion."""
    pass


class DocumentMetadataSchema(base_document_metadata_schema.__class__):
    """Schema for document metadata with implementation conversion."""
    pass


class DocumentChunkSchema(base_document_chunk_schema.__class__):
    """Schema for document chunks with implementation conversion."""
    pass


class EmbeddingModelConfigSchema(base_embedding_model_config_schema.__class__):
    """Schema for embedding model configuration with implementation conversion."""
    pass


class RetrievalFilterConditionSchema(base_retrieval_filter_condition_schema.__class__):
    """Schema for retrieval filter conditions with implementation conversion."""
    pass


class RetrievalFilterGroupSchema(base_retrieval_filter_group_schema.__class__):
    """Schema for retrieval filter groups with implementation conversion."""
    pass


class RetrievalFilterSchema(base_retrieval_filter_schema.__class__):
    """Schema for document retrieval filters with implementation conversion."""
    pass


class RetrievalSettingsSchema(base_retrieval_settings_schema.__class__):
    """Schema for document retrieval settings with implementation conversion."""
    pass


class ScoringConfigSchema(base_scoring_config_schema.__class__):
    """Schema for retrieval scoring configuration with implementation conversion."""
    pass


class HybridSearchConfigSchema(base_hybrid_search_config_schema.__class__):
    """Schema for hybrid search configuration with implementation conversion."""
    pass


class RetrievalResultSchema(base_retrieval_result_schema.__class__):
    """Schema for retrieval results with implementation conversion."""
    pass


# Create schema instances
chunking_config_schema = ChunkingConfigSchema()
document_metadata_schema = DocumentMetadataSchema()
document_chunk_schema = DocumentChunkSchema()
embedding_model_config_schema = EmbeddingModelConfigSchema()
retrieval_filter_condition_schema = RetrievalFilterConditionSchema()
retrieval_filter_group_schema = RetrievalFilterGroupSchema()
retrieval_filter_schema = RetrievalFilterSchema()
retrieval_settings_schema = RetrievalSettingsSchema()
scoring_config_schema = ScoringConfigSchema()
hybrid_search_config_schema = HybridSearchConfigSchema()
retrieval_result_schema = RetrievalResultSchema()