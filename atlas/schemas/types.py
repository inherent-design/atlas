"""
Type annotations for schema-validated data structures.

This module provides type hints that integrate with the Marshmallow schema
validations, allowing for static type checking while ensuring runtime validation.
"""

from typing import Any, Dict, List, Optional, Protocol, TypeVar, Generic, Type, Union, cast, Literal
from typing_extensions import TypedDict, NotRequired, Required

from marshmallow import Schema, ValidationError

# Type variables for generic schema types
T = TypeVar('T')
SchemaType = TypeVar('SchemaType', bound=Schema)
DataType = TypeVar('DataType')

# Schema-validated type - a wrapper type that indicates data has been validated by a schema
class SchemaValidated(Generic[SchemaType, DataType]):
    """A type that has been validated against a Marshmallow schema.
    
    This is a runtime container for data that has been validated against a schema.
    It provides access to both the validated data and the schema that validated it.
    """
    
    def __init__(self, data: DataType, schema: SchemaType):
        """Initialize a schema-validated value.
        
        Args:
            data: The validated data.
            schema: The schema that validated the data.
        """
        self.data = data
        self.schema = schema
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the validated data to a dictionary.
        
        Returns:
            The dictionary representation of the data.
        """
        return self.schema.dump(self.data)
    
    @classmethod
    def validate(cls, schema: SchemaType, data: Any) -> 'SchemaValidated[SchemaType, DataType]':
        """Validate data against a schema and return a SchemaValidated instance.
        
        Args:
            schema: The schema to validate against.
            data: The data to validate.
            
        Returns:
            A SchemaValidated instance containing the validated data.
            
        Raises:
            ValidationError: If validation fails.
        """
        validated = schema.load(data)
        return cls(validated, schema)


# Protocol for schema-compatible types
class SchemaCompatible(Protocol):
    """Protocol for types that can be validated by a schema."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """Create an instance from a dictionary.
        
        Args:
            data: The dictionary data.
            
        Returns:
            An instance of the type.
            
        Raises:
            ValidationError: If validation fails.
        """
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary.
        
        Returns:
            The dictionary representation.
        """
        ...


# Validated type dictionary - type hints for schema-validated dictionaries
class ValidatedDict(TypedDict, total=False):
    """Base type for validated dictionaries."""
    pass


# Message type definitions
class MessageRoleDict(ValidatedDict):
    """Message role dictionary."""
    role: str


class TextContentDict(ValidatedDict):
    """Text content dictionary."""
    type: Literal["text"]
    text: str


class ImageUrlDict(ValidatedDict):
    """Image URL details dictionary."""
    url: str
    detail: NotRequired[str]


class ImageContentDict(ValidatedDict):
    """Image content dictionary."""
    type: Literal["image_url"]
    image_url: ImageUrlDict


# Union type for all content types
ContentDict = Union[TextContentDict, ImageContentDict, str]


class ModelMessageDict(ValidatedDict):
    """Model message dictionary."""
    role: str
    content: Union[str, List[ContentDict], ContentDict]
    name: NotRequired[str]


# Provider type definitions
class TokenUsageDict(ValidatedDict):
    """Token usage statistics dictionary."""
    input_tokens: int
    output_tokens: int
    total_tokens: int


class CostEstimateDict(ValidatedDict):
    """Cost estimate dictionary."""
    input_cost: float
    output_cost: float
    total_cost: float


class ResponseFormatDict(ValidatedDict):
    """Response format specification dictionary."""
    type: str
    schema: NotRequired[Dict[str, Any]]


class ModelRequestDict(ValidatedDict):
    """Model request dictionary."""
    model: str
    messages: List[ModelMessageDict]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    stop: NotRequired[List[str]]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    response_format: NotRequired[ResponseFormatDict]
    stream: NotRequired[bool]
    system: NotRequired[str]
    metadata: NotRequired[Dict[str, Any]]


class ModelResponseDict(ValidatedDict):
    """Model response dictionary."""
    content: str
    model: str
    provider: str
    usage: NotRequired[TokenUsageDict]
    cost: NotRequired[CostEstimateDict]
    finish_reason: NotRequired[str]
    raw_response: NotRequired[Dict[str, Any]]


# Configuration type definitions
class ProviderRetryConfigDict(ValidatedDict):
    """Provider retry configuration dictionary."""
    max_retries: int
    initial_delay: float
    max_delay: float
    backoff_factor: float
    jitter_factor: float
    retryable_errors: NotRequired[List[str]]


class ProviderCircuitBreakerDict(ValidatedDict):
    """Provider circuit breaker configuration dictionary."""
    failure_threshold: int
    recovery_timeout: float
    test_requests: int
    reset_timeout: float


class ProviderOptionsDict(ValidatedDict):
    """Provider options dictionary."""
    capabilities: NotRequired[Dict[str, Union[int, str]]]


class ProviderConfigDict(ValidatedDict):
    """Provider configuration dictionary."""
    provider_type: str
    model_name: str
    api_key: NotRequired[str]
    api_base: NotRequired[str]
    max_tokens: NotRequired[int]
    retry_config: NotRequired[ProviderRetryConfigDict]
    circuit_breaker: NotRequired[ProviderCircuitBreakerDict]
    options: NotRequired[Dict[str, Any]]


class DatabaseConfigDict(ValidatedDict):
    """Database configuration dictionary."""
    provider: str
    connection_string: NotRequired[str]
    host: NotRequired[str]
    port: NotRequired[int]
    username: NotRequired[str]
    password: NotRequired[str]
    database_name: NotRequired[str]
    collection_name: NotRequired[str]
    persistent: NotRequired[bool]
    options: NotRequired[Dict[str, Any]]


class LoggingConfigDict(ValidatedDict):
    """Logging configuration dictionary."""
    level: NotRequired[str]
    format: NotRequired[str]
    file: NotRequired[str]
    structured: NotRequired[bool]
    console: NotRequired[bool]


class TelemetryConfigDict(ValidatedDict):
    """Telemetry configuration dictionary."""
    enabled: NotRequired[bool]
    endpoint: NotRequired[str]
    service_name: NotRequired[str]
    sample_rate: NotRequired[float]


class AtlasConfigDict(ValidatedDict):
    """Atlas configuration dictionary."""
    providers: NotRequired[Dict[str, ProviderConfigDict]]
    database: NotRequired[DatabaseConfigDict]
    logging: NotRequired[LoggingConfigDict]
    telemetry: NotRequired[TelemetryConfigDict]
    default_provider: NotRequired[str]
    default_model: NotRequired[str]
    api_keys: NotRequired[Dict[str, str]]