"""
Composite schema definitions for higher-order Atlas components.

This module provides schema definitions for composite components that build on core services,
including agent-related schemas, provider-related schemas, knowledge system schemas, and
workflow-related schemas. These schemas define the structure and validation rules
for composite components without implementation-specific code.
"""

from typing import Any, Literal, TypeAlias

from marshmallow import ValidationError, fields, validate, validates, validates_schema

from atlas.schemas.base import AtlasSchema, EnumField
from atlas.schemas.definitions.services import (
    CommandSchema,
    EventSchema,
    ResourceSchema,
    ServiceSchema,
    StateSchema,
)

# Type aliases for improved clarity
ComponentId: TypeAlias = str
AgentId: TypeAlias = str
ProviderId: TypeAlias = str
WorkflowId: TypeAlias = str
KnowledgeBaseId: TypeAlias = str

# Literal type definitions
ComponentStatus: TypeAlias = Literal["initializing", "ready", "active", "paused", "stopping", "terminated", "error"]
AgentStatus: TypeAlias = Literal["idle", "busy", "awaiting_task", "processing", "error"]
ProviderStatus: TypeAlias = Literal["connecting", "ready", "generating", "streaming", "error"]
CapabilityStrength: TypeAlias = Literal["basic", "moderate", "strong", "exceptional"]


class ComponentSchema(AtlasSchema):
    """Schema for service-enabled components."""

    component_id = fields.UUID(required=True)
    component_type = fields.String(required=True)
    status = fields.String(
        required=True,
        validate=validate.OneOf([
            "initializing", "ready", "active", "paused", "stopping", "terminated", "error"
        ]),
    )
    services = fields.List(fields.String(), required=True)
    metadata = fields.Dict(load_default=dict)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)

    @validates("component_type")
    def validate_component_type(self, value: str, **kwargs) -> None:
        """Validate component type format.
        
        Args:
            value: The component type value to validate.
            **kwargs: Additional arguments passed by Marshmallow.
            
        Raises:
            ValidationError: If value has invalid format.
        """
        if not value or not all(part.isalnum() or part == "_" for part in value.split(".")):
            raise ValidationError(
                "Component type must be dot-separated alphanumeric segments (e.g., 'agent.worker')"
            )


class LifecycleEventSchema(EventSchema):
    """Schema for lifecycle events in components."""
    
    component_id = fields.UUID(required=True)
    previous_status = fields.String(allow_none=True)
    new_status = fields.String(required=True)
    reason = fields.String(allow_none=True)


class CapabilitySchema(AtlasSchema):
    """Schema for capability definitions."""
    
    name = fields.String(required=True)
    description = fields.String(required=True)
    strength = fields.String(
        required=True,
        validate=validate.OneOf(["basic", "moderate", "strong", "exceptional"]),
    )
    metadata = fields.Dict(load_default=dict)


class AgentSchema(ComponentSchema):
    """Schema for agent components."""
    
    agent_id = fields.UUID(required=True)
    agent_type = fields.String(required=True)
    agent_status = fields.String(
        required=True,
        validate=validate.OneOf(["idle", "busy", "awaiting_task", "processing", "error"]),
    )
    capabilities = fields.List(fields.Nested(CapabilitySchema), load_default=list)
    task_count = fields.Integer(load_default=0)
    error_count = fields.Integer(load_default=0)
    last_task_id = fields.String(allow_none=True)
    provider_id = fields.String(allow_none=True)


class AgentTaskSchema(AtlasSchema):
    """Schema for agent tasks."""
    
    task_id = fields.UUID(required=True)
    agent_id = fields.UUID(required=True)
    task_type = fields.String(required=True)
    content = fields.Dict(required=True)
    metadata = fields.Dict(load_default=dict)
    created_at = fields.DateTime(required=True)
    started_at = fields.DateTime(allow_none=True)
    completed_at = fields.DateTime(allow_none=True)
    status = fields.String(
        required=True,
        validate=validate.OneOf(["pending", "in_progress", "completed", "failed", "cancelled"]),
    )
    result = fields.Dict(allow_none=True)
    error = fields.String(allow_none=True)


class AgentMessageSchema(AtlasSchema):
    """Schema for agent-to-agent messages."""
    
    message_id = fields.UUID(required=True)
    source_agent = fields.UUID(required=True)
    target_agent = fields.UUID(required=True, allow_none=True)
    content = fields.Dict(required=True)
    metadata = fields.Dict(load_default=dict)
    created_at = fields.DateTime(required=True)
    delivered_at = fields.DateTime(allow_none=True)
    reply_to = fields.UUID(allow_none=True)
    task_id = fields.UUID(allow_none=True)
    tool_calls = fields.List(fields.Dict(), load_default=list)
    tool_results = fields.List(fields.Dict(), load_default=list)


class ProviderSchema(ComponentSchema):
    """Schema for provider components."""
    
    provider_id = fields.UUID(required=True)
    provider_type = fields.String(required=True)
    model_name = fields.String(required=True)
    provider_status = fields.String(
        required=True,
        validate=validate.OneOf(["connecting", "ready", "generating", "streaming", "error"]),
    )
    capabilities = fields.List(fields.Nested(CapabilitySchema), load_default=list)
    request_count = fields.Integer(load_default=0)
    error_count = fields.Integer(load_default=0)
    token_count = fields.Integer(load_default=0)
    latency_avg = fields.Float(load_default=0.0)
    authentication = fields.Dict(load_default=dict)


class ProviderRequestSchema(AtlasSchema):
    """Schema for provider requests."""
    
    request_id = fields.UUID(required=True)
    provider_id = fields.UUID(required=True)
    request_type = fields.String(
        required=True,
        validate=validate.OneOf(["generate", "stream", "validate", "cancel"]),
    )
    messages = fields.List(fields.Dict(), required=False)
    parameters = fields.Dict(load_default=dict)
    created_at = fields.DateTime(required=True)
    completed_at = fields.DateTime(allow_none=True)
    status = fields.String(
        required=True,
        validate=validate.OneOf(["pending", "in_progress", "completed", "failed", "cancelled"]),
    )
    result = fields.Dict(allow_none=True)
    error = fields.String(allow_none=True)
    token_count = fields.Integer(allow_none=True)
    latency = fields.Float(allow_none=True)


class ProviderResponseSchema(AtlasSchema):
    """Schema for provider responses."""
    
    response_id = fields.UUID(required=True)
    request_id = fields.UUID(required=True)
    provider_id = fields.UUID(required=True)
    content = fields.Dict(required=True)
    metadata = fields.Dict(load_default=dict)
    created_at = fields.DateTime(required=True)
    token_count = fields.Integer(required=True)
    usage = fields.Dict(load_default=dict)
    

class KnowledgeBaseSchema(ComponentSchema):
    """Schema for knowledge base components."""
    
    knowledge_base_id = fields.UUID(required=True)
    collection_name = fields.String(required=True)
    embedding_model = fields.String(required=True)
    document_count = fields.Integer(load_default=0)
    chunk_count = fields.Integer(load_default=0)
    metadata = fields.Dict(load_default=dict)
    

class DocumentSchema(AtlasSchema):
    """Schema for knowledge base documents."""
    
    document_id = fields.UUID(required=True)
    knowledge_base_id = fields.UUID(required=True)
    file_path = fields.String(allow_none=True)
    content_type = fields.String(required=True)
    content = fields.String(allow_none=True)
    metadata = fields.Dict(load_default=dict)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    chunk_ids = fields.List(fields.UUID(), load_default=list)
    

class ChunkSchema(AtlasSchema):
    """Schema for document chunks."""
    
    chunk_id = fields.UUID(required=True)
    document_id = fields.UUID(required=True)
    content = fields.String(required=True)
    embedding = fields.List(fields.Float(), allow_none=True)
    metadata = fields.Dict(load_default=dict)
    start_idx = fields.Integer(allow_none=True)
    end_idx = fields.Integer(allow_none=True)
    

class QuerySchema(AtlasSchema):
    """Schema for knowledge base queries."""
    
    query_id = fields.UUID(required=True)
    knowledge_base_id = fields.UUID(required=True)
    query_text = fields.String(required=True)
    query_embedding = fields.List(fields.Float(), allow_none=True)
    filters = fields.Dict(load_default=dict)
    top_k = fields.Integer(load_default=5)
    strategy = fields.String(
        load_default="hybrid",
        validate=validate.OneOf(["semantic", "keyword", "hybrid"]),
    )
    created_at = fields.DateTime(required=True)
    results = fields.List(fields.Dict(), load_default=list)
    execution_time = fields.Float(allow_none=True)
    

class WorkflowSchema(ComponentSchema):
    """Schema for workflow components."""
    
    workflow_id = fields.UUID(required=True)
    name = fields.String(required=True)
    description = fields.String(required=True)
    nodes = fields.List(fields.Dict(), required=True)
    edges = fields.List(fields.Dict(), required=True)
    entry_points = fields.List(fields.String(), required=True)
    exit_points = fields.List(fields.String(), required=True)
    

class WorkflowExecutionSchema(AtlasSchema):
    """Schema for workflow executions."""
    
    execution_id = fields.UUID(required=True)
    workflow_id = fields.UUID(required=True)
    state = fields.Dict(required=True)
    current_node = fields.String(allow_none=True)
    history = fields.List(fields.Dict(), load_default=list)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    completed_at = fields.DateTime(allow_none=True)
    status = fields.String(
        required=True,
        validate=validate.OneOf(["running", "completed", "failed", "cancelled"]),
    )
    result = fields.Dict(allow_none=True)
    error = fields.String(allow_none=True)


class ToolSchema(AtlasSchema):
    """Schema for tool components."""
    
    tool_id = fields.UUID(required=True)
    name = fields.String(required=True)
    description = fields.String(required=True)
    parameters_schema = fields.Dict(required=True)
    return_schema = fields.Dict(load_default=dict)
    permissions = fields.List(fields.String(), load_default=list)
    metadata = fields.Dict(load_default=dict)
    

class ToolCallSchema(AtlasSchema):
    """Schema for tool calls."""
    
    call_id = fields.UUID(required=True)
    tool_id = fields.UUID(required=True)
    agent_id = fields.UUID(required=True)
    parameters = fields.Dict(required=True)
    created_at = fields.DateTime(required=True)
    completed_at = fields.DateTime(allow_none=True)
    status = fields.String(
        required=True,
        validate=validate.OneOf(["pending", "in_progress", "completed", "failed"]),
    )
    result = fields.Dict(allow_none=True)
    error = fields.String(allow_none=True)
    execution_time = fields.Float(allow_none=True)


# Export schema instances for convenient use
component_schema = ComponentSchema()
lifecycle_event_schema = LifecycleEventSchema()
capability_schema = CapabilitySchema()
agent_schema = AgentSchema()
agent_task_schema = AgentTaskSchema()
agent_message_schema = AgentMessageSchema()
provider_schema = ProviderSchema()
provider_request_schema = ProviderRequestSchema()
provider_response_schema = ProviderResponseSchema()
knowledge_base_schema = KnowledgeBaseSchema()
document_schema = DocumentSchema()
chunk_schema = ChunkSchema()
query_schema = QuerySchema()
workflow_schema = WorkflowSchema()
workflow_execution_schema = WorkflowExecutionSchema()
tool_schema = ToolSchema()
tool_call_schema = ToolCallSchema()