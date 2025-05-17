"""
Schema definitions package for Atlas.

This package contains pure schema definitions without circular dependencies.
These schemas define structure and validation rules but don't handle conversion
to implementation classes directly to avoid circular imports.
"""

from atlas.schemas.definitions.messages import (
    message_role_schema,
    text_content_schema,
    image_url_schema,
    image_content_schema,
    message_content_schema,
    model_message_schema,
)

from atlas.schemas.definitions.providers import (
    token_usage_schema,
    cost_estimate_schema,
    model_request_schema,
    model_response_schema
)

from atlas.schemas.definitions.agents import (
    agent_type_schema,
    agent_options_schema,
    task_specification_schema,
    tool_parameter_schema,
    tool_schema_schema,
    tool_agent_options_schema,
    task_aware_agent_options_schema,
    controller_agent_options_schema,
    worker_agent_options_schema,
    agent_config_schema
)

from atlas.schemas.definitions.knowledge import (
    chunking_strategy_enum,
    chunking_config_schema,
    document_metadata_schema,
    document_chunk_schema,
    embedding_model_config_schema,
    retrieval_filter_operator,
    retrieval_filter_condition_schema,
    retrieval_filter_group_schema,
    retrieval_filter_schema,
    retrieval_settings_schema,
    scoring_strategy_enum,
    scoring_config_schema,
    hybrid_search_config_schema,
    retrieval_result_schema
)

from atlas.schemas.definitions.options import (
    capability_level_schema,
    provider_options_schema,
    provider_retry_config_schema,
    provider_circuit_breaker_schema,
    provider_config_schema
)

from atlas.schemas.definitions.tools import (
    ToolParameterSchemaDefinition,
    ToolSchemaDefinitionSchema,
    ToolDefinitionSchemaDefinition,
    ToolPermissionSchemaDefinition,
    ToolCallSchemaDefinition,
    ToolResultSchemaDefinition
)

__all__ = [
    # Messages schemas
    "message_role_schema",
    "text_content_schema",
    "image_url_schema",
    "image_content_schema",
    "message_content_schema",
    "model_message_schema",
    
    # Provider schemas
    "token_usage_schema",
    "cost_estimate_schema",
    "model_request_schema",
    "model_response_schema",
    
    # Agent schemas
    "agent_type_schema",
    "agent_options_schema",
    "task_specification_schema",
    "tool_parameter_schema",
    "tool_schema_schema",
    "tool_agent_options_schema",
    "task_aware_agent_options_schema",
    "controller_agent_options_schema",
    "worker_agent_options_schema",
    "agent_config_schema",
    
    # Knowledge schemas
    "chunking_strategy_enum",
    "chunking_config_schema",
    "document_metadata_schema",
    "document_chunk_schema",
    "embedding_model_config_schema",
    "retrieval_filter_operator",
    "retrieval_filter_condition_schema",
    "retrieval_filter_group_schema",
    "retrieval_filter_schema",
    "retrieval_settings_schema",
    "scoring_strategy_enum",
    "scoring_config_schema",
    "hybrid_search_config_schema",
    "retrieval_result_schema",
    
    # Options schemas
    "capability_level_schema",
    "provider_options_schema",
    "provider_retry_config_schema",
    "provider_circuit_breaker_schema",
    "provider_config_schema",
    
    # Tools schemas
    "ToolParameterSchemaDefinition",
    "ToolSchemaDefinitionSchema",
    "ToolDefinitionSchemaDefinition",
    "ToolPermissionSchemaDefinition",
    "ToolCallSchemaDefinition",
    "ToolResultSchemaDefinition"
]