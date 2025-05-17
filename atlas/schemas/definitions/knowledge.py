"""
Pure schema definitions for knowledge-related types.

This module contains schema definitions without any post_load methods or references
to implementation classes, avoiding circular imports. These schemas define the 
structure and validation rules for knowledge types but don't handle conversion
to actual implementation objects.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum

from marshmallow import fields, pre_load, validates, validates_schema, ValidationError

from atlas.schemas.base import AtlasSchema, EnumField, JsonField


class ChunkingStrategyEnum(str, Enum):
    """Enum for document chunking strategies."""
    FIXED_SIZE = "fixed_size"
    PARAGRAPH = "paragraph"
    SECTION = "section"
    SENTENCE = "sentence"
    SEMANTIC = "semantic"
    CUSTOM = "custom"


class ChunkingConfigSchema(AtlasSchema):
    """Schema for document chunking configuration."""
    
    strategy = EnumField(ChunkingStrategyEnum, required=True)
    chunk_size = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x > 0)
    chunk_overlap = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x >= 0)
    separator = fields.String(required=False, allow_none=True)
    custom_chunker = fields.String(required=False, allow_none=True)
    
    @validates_schema
    def validate_configuration(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate that the chunking configuration is consistent.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If the configuration is inconsistent.
        """
        strategy = data.get("strategy")
        
        # Validate fixed_size strategy
        if strategy == ChunkingStrategyEnum.FIXED_SIZE:
            if "chunk_size" not in data:
                raise ValidationError("chunk_size is required for fixed_size strategy")
        
        # Validate custom strategy
        if strategy == ChunkingStrategyEnum.CUSTOM:
            if "custom_chunker" not in data:
                raise ValidationError("custom_chunker is required for custom strategy")


class DocumentMetadataSchema(AtlasSchema):
    """Schema for document metadata."""
    
    source = fields.String(required=True)
    chunk_index = fields.Integer(required=False, allow_none=True)
    chunk_size = fields.Integer(required=False, allow_none=True)
    file_type = fields.String(required=False, allow_none=True)
    created_at = fields.String(required=False, allow_none=True)
    updated_at = fields.String(required=False, allow_none=True)
    tags = fields.List(fields.String(), required=False, allow_none=True)
    custom = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False, allow_none=True)


class DocumentChunkSchema(AtlasSchema):
    """Schema for document chunks."""
    
    id = fields.String(required=True)
    text = fields.String(required=True)
    metadata = fields.Nested(DocumentMetadataSchema, required=True)
    embedding = fields.List(fields.Float(), required=False, allow_none=True)


class EmbeddingModelConfigSchema(AtlasSchema):
    """Schema for embedding model configuration."""
    
    model_name = fields.String(required=True)
    provider = fields.String(required=True)
    dimensions = fields.Integer(required=False, allow_none=True)
    api_key = fields.String(required=False, allow_none=True)
    api_base = fields.String(required=False, allow_none=True)
    batch_size = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x > 0)
    options = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False, allow_none=True)


class RetrievalFilterOperator(str, Enum):
    """Enum for document retrieval filter operators."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_EQUALS = "gte"
    LESS_THAN = "lt"
    LESS_THAN_EQUALS = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class RetrievalFilterConditionSchema(AtlasSchema):
    """Schema for retrieval filter conditions."""
    
    field = fields.String(required=True)
    operator = EnumField(RetrievalFilterOperator, required=True)
    value = fields.Raw(required=True)


class RetrievalFilterGroupSchema(AtlasSchema):
    """Schema for retrieval filter groups."""
    
    operator = fields.String(required=True, validate=lambda x: x in ["and", "or"])
    conditions = fields.List(fields.Nested("self"), required=False, allow_none=True)
    filters = fields.List(fields.Nested(RetrievalFilterConditionSchema), required=False, allow_none=True)
    
    @validates_schema
    def validate_group(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate that the filter group has either conditions or filters.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If the filter group is invalid.
        """
        conditions = data.get("conditions", [])
        filters = data.get("filters", [])
        
        if not conditions and not filters:
            raise ValidationError(
                "Filter group must have either nested conditions or direct filters"
            )


class RetrievalFilterSchema(AtlasSchema):
    """Schema for document retrieval filters."""
    
    where = fields.Nested(RetrievalFilterGroupSchema, required=False, allow_none=True)
    where_document = fields.Dict(keys=fields.String(), values=fields.Raw(), required=False, allow_none=True)
    limit = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x > 0)
    offset = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x >= 0)
    include = fields.List(fields.String(), required=False, allow_none=True)
    exclude = fields.List(fields.String(), required=False, allow_none=True)


class RetrievalSettingsSchema(AtlasSchema):
    """Schema for document retrieval settings."""
    
    filter = fields.Nested(RetrievalFilterSchema, required=False, allow_none=True)
    top_k = fields.Integer(required=False, allow_none=True, validate=lambda x: x is None or x > 0)
    namespace = fields.String(required=False, allow_none=True)
    score_threshold = fields.Float(required=False, allow_none=True, validate=lambda x: x is None or 0 <= x <= 1)
    include_embeddings = fields.Boolean(required=False, allow_none=True)
    include_metadata = fields.Boolean(required=False, allow_none=True)
    search_type = fields.String(required=False, allow_none=True, validate=lambda x: x is None or x in ["similarity", "hybrid", "keyword"])
    reranking_model = fields.String(required=False, allow_none=True)


class ScoringStrategyEnum(str, Enum):
    """Enum for retrieval scoring strategies."""
    BM25 = "bm25"
    TF_IDF = "tf_idf"
    COSINE = "cosine"
    DOT_PRODUCT = "dot_product"
    EUCLIDEAN = "euclidean"
    HYBRID = "hybrid"
    CUSTOM = "custom"


class ScoringConfigSchema(AtlasSchema):
    """Schema for retrieval scoring configuration."""
    
    strategy = EnumField(ScoringStrategyEnum, required=True)
    semantic_weight = fields.Float(required=False, allow_none=True, validate=lambda x: x is None or 0 <= x <= 1)
    keyword_weight = fields.Float(required=False, allow_none=True, validate=lambda x: x is None or 0 <= x <= 1)
    custom_scorer = fields.String(required=False, allow_none=True)
    
    @validates_schema
    def validate_configuration(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate that the scoring configuration is consistent.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If the configuration is inconsistent.
        """
        strategy = data.get("strategy")
        
        # Validate hybrid strategy
        if strategy == ScoringStrategyEnum.HYBRID:
            if "semantic_weight" not in data or "keyword_weight" not in data:
                raise ValidationError(
                    "semantic_weight and keyword_weight are required for hybrid strategy"
                )
            
            semantic_weight = data.get("semantic_weight", 0)
            keyword_weight = data.get("keyword_weight", 0)
            
            if abs((semantic_weight + keyword_weight) - 1.0) > 0.0001:
                raise ValidationError(
                    f"semantic_weight ({semantic_weight}) + keyword_weight ({keyword_weight}) must equal 1.0"
                )
        
        # Validate custom strategy
        if strategy == ScoringStrategyEnum.CUSTOM:
            if "custom_scorer" not in data:
                raise ValidationError("custom_scorer is required for custom strategy")


class HybridSearchConfigSchema(AtlasSchema):
    """Schema for hybrid search configuration."""
    
    semantic_search_enabled = fields.Boolean(required=True)
    keyword_search_enabled = fields.Boolean(required=True)
    semantic_model = fields.String(required=False, allow_none=True)
    semantic_weight = fields.Float(required=False, allow_none=True, validate=lambda x: x is None or 0 <= x <= 1)
    keyword_weight = fields.Float(required=False, allow_none=True, validate=lambda x: x is None or 0 <= x <= 1)
    scorer = fields.String(required=False, allow_none=True)
    
    @validates_schema
    def validate_configuration(self, data: Dict[str, Any], **kwargs) -> None:
        """Validate that the hybrid search configuration is consistent.
        
        Args:
            data: The data to validate.
            **kwargs: Additional arguments.
            
        Raises:
            ValidationError: If the configuration is inconsistent.
        """
        semantic_enabled = data.get("semantic_search_enabled", False)
        keyword_enabled = data.get("keyword_search_enabled", False)
        
        if not semantic_enabled and not keyword_enabled:
            raise ValidationError(
                "At least one search type (semantic or keyword) must be enabled"
            )
        
        if semantic_enabled and keyword_enabled:
            if "semantic_weight" not in data or "keyword_weight" not in data:
                raise ValidationError(
                    "semantic_weight and keyword_weight are required when both search types are enabled"
                )
            
            semantic_weight = data.get("semantic_weight", 0)
            keyword_weight = data.get("keyword_weight", 0)
            
            if abs((semantic_weight + keyword_weight) - 1.0) > 0.0001:
                raise ValidationError(
                    f"semantic_weight ({semantic_weight}) + keyword_weight ({keyword_weight}) must equal 1.0"
                )


class RetrievalResultSchema(AtlasSchema):
    """Schema for retrieval results."""
    
    id = fields.String(required=True)
    text = fields.String(required=True)
    metadata = fields.Nested(DocumentMetadataSchema, required=True)
    score = fields.Float(required=True)
    embedding = fields.List(fields.Float(), required=False, allow_none=True)


# Export schema instances for convenient use
chunking_strategy_enum = ChunkingStrategyEnum
chunking_config_schema = ChunkingConfigSchema()
document_metadata_schema = DocumentMetadataSchema()
document_chunk_schema = DocumentChunkSchema()
embedding_model_config_schema = EmbeddingModelConfigSchema()
retrieval_filter_operator = RetrievalFilterOperator
retrieval_filter_condition_schema = RetrievalFilterConditionSchema()
retrieval_filter_group_schema = RetrievalFilterGroupSchema()
retrieval_filter_schema = RetrievalFilterSchema()
retrieval_settings_schema = RetrievalSettingsSchema()
scoring_strategy_enum = ScoringStrategyEnum
scoring_config_schema = ScoringConfigSchema()
hybrid_search_config_schema = HybridSearchConfigSchema()
retrieval_result_schema = RetrievalResultSchema()