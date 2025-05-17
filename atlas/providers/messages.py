"""
Message and request modeling for Atlas providers.

This module defines the data structures for messages, requests, responses,
and related metadata used in communication with language model providers.
It uses schema validation to ensure data integrity at runtime.
"""

from typing import Dict, List, Any, Optional, Union, cast, Type
from enum import Enum
from marshmallow import ValidationError

from atlas.core.telemetry import traced
from atlas.core.types import (
    MessageRole,
    MessageDict,
    ModelRequestDict,
    # Import type definitions for backward compatibility with old code
    TextContent as TypedTextContent,
    ImageContent as TypedImageContent,
)
from atlas.schemas.validation import create_schema_validated
from atlas.schemas.messages import (
    message_role_schema,
    text_content_schema,
    image_content_schema,
    message_content_schema,
    model_message_schema,
    validate_message_content,
    validate_model_message,
    validate_message_list,
    validate_message_param,
    validate_messages_param,
    validate_content_param
)
from atlas.schemas.providers import (
    token_usage_schema,
    cost_estimate_schema,
    model_request_schema,
    model_response_schema
)

# Re-export MessageRole to maintain backward compatibility
ModelRole = MessageRole

@create_schema_validated(message_content_schema)
class MessageContent:
    """Content of a message in the conversation."""
    
    type: str
    """The type of content (text, image_url, etc.)."""
    
    text: Optional[str] = None
    """The text content for text type messages."""
    
    image_url: Optional[Dict[str, Any]] = None
    """The image URL details for image_url type messages."""
    
    def __init__(self, type: str, text: Optional[str] = None, image_url: Optional[Dict[str, Any]] = None):
        """Initialize message content.
        
        Args:
            type: The type of content (text, image_url, etc.)
            text: The text content (for text type)
            image_url: The image URL details (for image_url type)
        """
        self.type = type
        self.text = text
        self.image_url = image_url
    
    @classmethod
    def create_direct(cls, type: str, text: Optional[str] = None, image_url: Optional[Dict[str, Any]] = None) -> "MessageContent":
        """Create a MessageContent instance directly without schema validation.
        
        Args:
            type: The type of content (text, image_url, etc.)
            text: The text content (for text type)
            image_url: The image URL details (for image_url type)
            
        Returns:
            A MessageContent instance.
        """
        instance = cls.__new__(cls)
        
        # Set attributes directly
        instance.type = type
        instance.text = text
        instance.image_url = image_url
        
        return instance
    
    @classmethod
    def create_text(cls, text: str) -> "MessageContent":
        """Create a text content.
        
        Args:
            text: The text content.
            
        Returns:
            A MessageContent instance with text type.
        """
        # Use create_direct to avoid schema validation
        return cls.create_direct(
            type="text",
            text=text
        )
        
    @classmethod
    def create_image_url(cls, url: str, detail: str = "auto") -> "MessageContent":
        """Create an image URL content.
        
        Args:
            url: The URL of the image.
            detail: The detail level for the image (auto, high, low).
            
        Returns:
            A MessageContent instance with image_url type.
        """
        # Use create_direct to avoid schema validation
        return cls.create_direct(
            type="image_url",
            image_url={"url": url, "detail": detail}
        )
    
    # Override the default to_dict method from create_schema_validated
    # to ensure all fields are properly included
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation.
        
        Returns:
            Dictionary representation of the content.
        """
        # Always include the type field
        result = {"type": self.type}
        
        # Always include fields based on the type
        if self.type == "text" and self.text is not None:
            result["text"] = self.text
        elif self.type == "image_url" and self.image_url is not None:
            result["image_url"] = self.image_url
        else:
            # Include both fields if type is unknown or for complete representation
            if self.text is not None:
                result["text"] = self.text
                
            if self.image_url is not None:
                result["image_url"] = self.image_url
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageContent":
        """Create a MessageContent from a dictionary.
        
        Args:
            data: Dictionary representation of content.
            
        Returns:
            A MessageContent instance.
        """
        # Handle existing MessageContent objects
        if isinstance(data, cls):
            return data
            
        # Handle string input directly
        if isinstance(data, str):
            return cls.create_text(data)
            
        # Get type or default to "text" if not specified
        content_type = data.get("type", "text")
        
        # Extract other fields based on content type
        if content_type == "text":
            return cls.create_direct(
                type="text",
                text=data.get("text", "")
            )
        elif content_type == "image_url":
            return cls.create_direct(
                type="image_url",
                image_url=data.get("image_url", {})
            )
        else:
            # Generic handler for unknown types
            return cls.create_direct(
                type=content_type,
                text=data.get("text"),
                image_url=data.get("image_url")
            )


@create_schema_validated(model_message_schema)
class ModelMessage:
    """A message in a conversation with a model."""
    
    role: MessageRole
    """The role of the message sender."""
    
    content: Union[str, MessageContent, List[MessageContent]]
    """The content of the message."""
    
    name: Optional[str] = None
    """Optional name for the sender of the message."""
    
    def __init__(
        self,
        role: MessageRole,
        content: Union[str, MessageContent, List[MessageContent]],
        name: Optional[str] = None
    ):
        """Initialize a model message.
        
        Args:
            role: The role of the message sender.
            content: The content of the message.
            name: Optional name for the sender of the message.
        """
        self.role = role
        self.content = content
        self.name = name
    
    def __iter__(self):
        """Make this object iterable like a dictionary."""
        yield 'role', self.role
        yield 'content', self.content
        if self.name is not None:
            yield 'name', self.name
            
    def __getitem__(self, key):
        """Allow dictionary-like access."""
        if key == 'role':
            return self.role
        elif key == 'content':
            return self.content
        elif key == 'name':
            return self.name
        raise KeyError(key)
        
    @classmethod
    def create_direct(cls,
                      role: MessageRole,
                      content: Union[str, MessageContent, List[MessageContent]],
                      name: Optional[str] = None
                     ) -> "ModelMessage":
        """Create a ModelMessage instance directly without schema validation.
        
        Args:
            role: The role of the message sender.
            content: The content of the message.
            name: Optional name for the sender of the message.
            
        Returns:
            A ModelMessage instance.
        """
        # Create instance directly without validation
        instance = cls.__new__(cls)
        
        # Set core attributes
        instance.role = role
        instance.content = content
        instance.name = name
        
        return instance
    
    @classmethod
    def system(cls, content: str) -> "ModelMessage":
        """Create a system message.

        Args:
            content: The text content of the message.

        Returns:
            A ModelMessage with the system role.
        """
        # Use create_direct to avoid schema validation
        return cls.create_direct(
            role=MessageRole.SYSTEM,
            content=str(content),
            name=None
        )

    @classmethod
    def user(
        cls,
        content: Union[str, MessageContent, List[MessageContent]],
        name: Optional[str] = None,
    ) -> "ModelMessage":
        """Create a user message.

        Args:
            content: The content of the message.
            name: Optional name for the user.

        Returns:
            A ModelMessage with the user role.
        """
        # Process content first
        processed_content = cls._process_content(content)
        
        # Use create_direct method with processed content
        return cls.create_direct(
            role=MessageRole.USER,
            content=processed_content,
            name=name
        )

    @classmethod
    def assistant(
        cls,
        content: Union[str, MessageContent, List[MessageContent]],
        name: Optional[str] = None,
    ) -> "ModelMessage":
        """Create an assistant message.

        Args:
            content: The content of the message.
            name: Optional name for the assistant.

        Returns:
            A ModelMessage with the assistant role.
        """
        # Process content first
        processed_content = cls._process_content(content)
        
        # Use create_direct method with processed content
        return cls.create_direct(
            role=MessageRole.ASSISTANT,
            content=processed_content,
            name=name
        )

    @classmethod
    def function(cls, content: str, name: str) -> "ModelMessage":
        """Create a function message.

        Args:
            content: The text content of the message.
            name: Name of the function.

        Returns:
            A ModelMessage with the function role.
        """
        # Use create_direct method
        return cls.create_direct(
            role=MessageRole.FUNCTION,
            content=str(content),
            name=name
        )
        
    @classmethod
    def tool(cls, content: str, name: str) -> "ModelMessage":
        """Create a tool message.
        
        Args:
            content: The text content of the message.
            name: Name of the tool.
            
        Returns:
            A ModelMessage with the tool role.
        """
        # Use create_direct method
        return cls.create_direct(
            role=MessageRole.TOOL,
            content=str(content),
            name=name
        )

    # Override the default to_dict method from create_schema_validated
    # to handle content serialization properly
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary.

        Returns:
            A dictionary representation of the message.
        """
        result: Dict[str, Any] = {"role": self.role.value}

        # Handle different content types
        if isinstance(self.content, str):
            result["content"] = self.content
        elif isinstance(self.content, MessageContent):
            # For text content, simplify to just text
            if self.content.type == "text":
                result["content"] = self.content.text
            else:
                # For non-text content, use the content's to_dict method
                result["content"] = self.content.to_dict()
        elif isinstance(self.content, list):
            # For multi-modal content, convert each item to a dict
            if len(self.content) == 1 and self.content[0].type == "text":
                # Simplify to just text for single text content
                result["content"] = self.content[0].text
            else:
                # Create a list of content item dictionaries
                content_list = []
                for item in self.content:
                    if isinstance(item, MessageContent):
                        content_list.append(item.to_dict())
                    else:
                        # Non-MessageContent item
                        content_list.append(item)
                        
                result["content"] = content_list

        # Add name field (even if None)
        result["name"] = self.name

        return result
    
    @classmethod
    @traced(name="modelMessage_from_dict")
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMessage":
        """Create a ModelMessage from a dictionary.
        
        Args:
            data: Dictionary representation of a message.
            
        Returns:
            A ModelMessage instance.
        """
        # Process content properly if it's in string form or dict form
        role = data.get("role")
        content = data.get("content")
        name = data.get("name")
        
        # Convert string role to enum if needed
        if isinstance(role, str):
            try:
                role = MessageRole(role)
            except (ValueError, AttributeError):
                role = MessageRole.USER
        
        # Process content based on its type
        if isinstance(content, dict) and "type" in content:
            # Content is a structured content dict
            content = MessageContent.from_dict(content)
        elif isinstance(content, list):
            # Content is a list of items
            processed_list = []
            for item in content:
                if isinstance(item, dict) and "type" in item:
                    processed_list.append(MessageContent.from_dict(item))
                else:
                    # For string or other types
                    processed_list.append(MessageContent.create_text(str(item)))
            content = processed_list
            
        # Create directly to avoid validation recursion
        return cls.create_direct(
            role=role,
            content=content,
            name=name
        )
        
    @classmethod
    def _process_content(cls, content: Union[str, MessageContent, List[Any]]) -> Union[str, MessageContent, List[MessageContent]]:
        """Process content in a uniform way for user and assistant messages.
        
        Args:
            content: The content to process.
            
        Returns:
            Processed content ready for a message.
        """
        if isinstance(content, MessageContent):
            return content
        elif isinstance(content, list):
            # Convert list of MessageContent objects or other items
            processed_content = []
            for item in content:
                if isinstance(item, MessageContent):
                    processed_content.append(item)
                elif isinstance(item, dict) and "type" in item:
                    # Create MessageContent from dict
                    mc = MessageContent.from_dict(item)
                    processed_content.append(mc)
                else:
                    # Plain text or other format
                    processed_content.append(MessageContent.create_text(str(item)))
            return processed_content
        else:
            # Plain string or other format
            return str(content)


@create_schema_validated(text_content_schema)
class TextContent:
    """Text content for messages.
    
    This class represents the text content in a message, with schema validation
    to ensure that the text content is valid.
    """
    
    type: str
    """The content type, always "text" for this class."""
    
    text: str
    """The text content."""
    
    def __init__(self, text: str):
        """Initialize text content.
        
        Args:
            text: The text content.
        """
        self.type = "text"
        self.text = text
    
    @classmethod
    def create_direct(cls, text: str) -> "TextContent":
        """Create a TextContent instance directly without schema validation.
        
        Args:
            text: The text content.
            
        Returns:
            A TextContent instance.
        """
        instance = cls.__new__(cls)
        
        # Set core attributes
        instance.type = "text"
        instance.text = text
        
        return instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation.
        
        Returns:
            Dictionary representation of the text content.
        """
        return {
            "type": "text",
            "text": self.text
        }


@create_schema_validated(image_content_schema)
class ImageContent:
    """Image content for messages.
    
    This class represents the image content in a message, with schema validation
    to ensure that the image URL and detail level are valid.
    """
    
    type: str
    """The content type, always "image_url" for this class."""
    
    image_url: Dict[str, Any]
    """The image URL details, including the URL and detail level."""
    
    def __init__(self, url: str, detail: str = "auto"):
        """Initialize image content.
        
        Args:
            url: The URL of the image.
            detail: The detail level (auto, high, low).
        """
        self.type = "image_url"
        self.image_url = {"url": url, "detail": detail}
    
    @classmethod
    def create_direct(cls, url: str, detail: str = "auto") -> "ImageContent":
        """Create an ImageContent instance directly without schema validation.
        
        Args:
            url: The URL of the image.
            detail: The detail level (auto, high, low).
            
        Returns:
            An ImageContent instance.
        """
        instance = cls.__new__(cls)
        
        # Set core attributes
        instance.type = "image_url"
        instance.image_url = {"url": url, "detail": detail}
        
        return instance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation.
        
        Returns:
            Dictionary representation of the image content.
        """
        return {
            "type": "image_url",
            "image_url": self.image_url
        }


@create_schema_validated(model_request_schema)
class ModelRequest:
    """A request to generate content from a model."""
    
    messages: List[ModelMessage]
    """The conversation history."""
    
    max_tokens: Optional[int] = None
    """Maximum number of tokens to generate."""
    
    temperature: Optional[float] = None
    """Temperature for sampling, higher values mean more randomness."""
    
    system_prompt: Optional[str] = None
    """Optional system prompt/instructions."""
    
    model: Optional[str] = None
    """Optional model override."""
    
    stop_sequences: Optional[List[str]] = None
    """Optional sequences that will stop generation."""
    
    top_p: Optional[float] = None
    """Nucleus sampling parameter."""
    
    frequency_penalty: Optional[float] = None
    """Penalty for token frequency."""
    
    presence_penalty: Optional[float] = None
    """Penalty for token presence."""
    
    response_format: Optional[Dict[str, Any]] = None
    """Response format specifier."""
    
    metadata: Dict[str, Any] = {}
    """Metadata for the request."""
    
    def __init__(
        self,
        messages: List[ModelMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        stop_sequences: Optional[List[str]] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize a model request.
        
        Args:
            messages: List of messages in the conversation.
            max_tokens: Maximum number of tokens to generate.
            temperature: Temperature for sampling.
            system_prompt: Optional system prompt/instructions.
            model: Optional model override.
            stop_sequences: Optional sequences that will stop generation.
            top_p: Nucleus sampling parameter.
            frequency_penalty: Penalty for token frequency.
            presence_penalty: Penalty for token presence.
            response_format: Response format specifier.
            metadata: Optional metadata for the request.
            **kwargs: Additional parameters.
        """
        # Store core attributes
        self.messages = messages if messages is not None else []
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.model = model
        self.stop_sequences = stop_sequences
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.response_format = response_format
        self.metadata = metadata if metadata is not None else {}
        
        # Store any additional parameters in metadata
        if kwargs:
            for key, value in kwargs.items():
                self.metadata[key] = value
        
        # If system prompt is provided but not in messages, add it
        if self.system_prompt and not any(
            msg.role == MessageRole.SYSTEM for msg in self.messages
        ):
            self.messages.insert(0, ModelMessage.system(self.system_prompt))
    
    def __iter__(self):
        """Make this object iterable like a dictionary."""
        yield 'messages', self.messages
        
        # Include fields that are not None
        if self.max_tokens is not None:
            yield 'max_tokens', self.max_tokens
        if self.temperature is not None:
            yield 'temperature', self.temperature
        if self.system_prompt is not None:
            yield 'system_prompt', self.system_prompt
        if self.model is not None:
            yield 'model', self.model
        if self.stop_sequences is not None:
            yield 'stop_sequences', self.stop_sequences
        if self.top_p is not None:
            yield 'top_p', self.top_p
        if self.frequency_penalty is not None:
            yield 'frequency_penalty', self.frequency_penalty
        if self.presence_penalty is not None:
            yield 'presence_penalty', self.presence_penalty
        if self.response_format is not None:
            yield 'response_format', self.response_format
        if self.metadata:
            yield 'metadata', self.metadata
            
    def items(self):
        """Dictionary-like items method."""
        return list(self.__iter__())
    
    # Override the default to_dict method from create_schema_validated
    # to handle nested message serialization properly
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary representation.
        
        Returns:
            Dictionary representation of the request.
        """
        result = {}
        
        # Add messages if present
        if hasattr(self, "messages") and self.messages:
            result["messages"] = [
                msg.to_dict() if hasattr(msg, "to_dict") else msg 
                for msg in self.messages
            ]
        
        # Add model if present
        if hasattr(self, "model") and self.model is not None:
            result["model"] = self.model
            
        # Add optional parameters if set
        optional_params = [
            ("max_tokens", "max_tokens"),
            ("temperature", "temperature"),
            ("system_prompt", "system"),
            ("stop_sequences", "stop"),
            ("top_p", "top_p"),
            ("frequency_penalty", "frequency_penalty"),
            ("presence_penalty", "presence_penalty"),
            ("response_format", "response_format"),
        ]
        
        for attr_name, dict_key in optional_params:
            if hasattr(self, attr_name) and getattr(self, attr_name) is not None:
                result[dict_key] = getattr(self, attr_name)
                
        # Add metadata if present
        if hasattr(self, "metadata") and self.metadata:
            # Add metadata as top-level keys for compatibility
            for key, value in self.metadata.items():
                result[key] = value
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelRequest":
        """Create a ModelRequest from a dictionary.
        
        Args:
            data: Dictionary containing request data.
            
        Returns:
            A ModelRequest instance.
        """
        # Process messages to convert to ModelMessage objects
        if "messages" in data and isinstance(data["messages"], list):
            processed_messages = []
            for msg in data["messages"]:
                if isinstance(msg, dict):
                    processed_messages.append(ModelMessage.from_dict(msg))
                elif isinstance(msg, ModelMessage):
                    processed_messages.append(msg)
                # Other types are skipped
            data["messages"] = processed_messages
            
        # Use create_direct to bypass schema validation
        return cls.create_direct(**data)
        
    @classmethod
    def create_direct(
        cls,
        messages: List[ModelMessage],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        stop_sequences: Optional[List[str]] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> "ModelRequest":
        """Create a ModelRequest directly without schema validation.
        
        Args:
            messages: List of messages in the conversation.
            system_prompt: Optional system prompt/instructions.
            max_tokens: Maximum number of tokens to generate.
            temperature: Temperature for sampling.
            model: Optional model override.
            stop_sequences: Optional sequences that will stop generation.
            top_p: Nucleus sampling parameter.
            frequency_penalty: Penalty for token frequency.
            presence_penalty: Penalty for token presence.
            response_format: Response format specifier.
            metadata: Optional metadata for the request.
            
        Returns:
            A ModelRequest instance.
        """
        # Create instance directly without validation
        instance = cls.__new__(cls)
        
        # Set core attributes
        instance.messages = messages if messages is not None else []
        instance.max_tokens = max_tokens
        instance.temperature = temperature
        instance.system_prompt = system_prompt
        instance.model = model
        instance.stop_sequences = stop_sequences
        instance.top_p = top_p
        instance.frequency_penalty = frequency_penalty
        instance.presence_penalty = presence_penalty
        instance.response_format = response_format
        instance.metadata = metadata if metadata is not None else {}
        
        # Store any additional parameters in metadata
        if kwargs:
            for key, value in kwargs.items():
                instance.metadata[key] = value
        
        # If system prompt is provided but not in messages, add it
        if instance.system_prompt and not any(
            msg.role == MessageRole.SYSTEM for msg in instance.messages
        ):
            instance.messages.insert(0, ModelMessage.system(instance.system_prompt))
            
        return instance

    @traced(name="modelRequest_to_provider_request")
    def to_provider_request(self, provider_name: str) -> Dict[str, Any]:
        """Convert to a provider-specific request format.

        Args:
            provider_name: The name of the provider.

        Returns:
            A dictionary with the request in provider-specific format.
        """
        # Base request that works for most providers
        request: Dict[str, Any] = {
            "messages": [msg.to_dict() for msg in self.messages],
        }

        # Add optional parameters if specified
        if self.max_tokens:
            request["max_tokens"] = self.max_tokens

        if self.temperature is not None:
            request["temperature"] = self.temperature

        if self.stop_sequences:
            # Ensure proper key name for stop sequences
            request["stop"] = self.stop_sequences

        if self.top_p is not None:
            request["top_p"] = self.top_p

        if self.response_format:
            request["response_format"] = self.response_format

        # Provider-specific adaptations
        if provider_name.lower() == "anthropic":
            # Anthropic uses system as a separate parameter
            system_messages = [
                msg for msg in self.messages if msg.role == MessageRole.SYSTEM
            ]
            if system_messages:
                # Use the first system message as the system parameter
                system_content = system_messages[0].to_dict()["content"]
                request["system"] = system_content
                # Remove system messages from the messages list
                request["messages"] = [
                    msg.to_dict()
                    for msg in self.messages
                    if msg.role != MessageRole.SYSTEM
                ]

        elif provider_name.lower() == "openai":
            # OpenAI-specific adaptations if needed
            if self.frequency_penalty is not None:
                request["frequency_penalty"] = self.frequency_penalty

            if self.presence_penalty is not None:
                request["presence_penalty"] = self.presence_penalty

        # Add any other provider-specific adaptations as needed

        return request


@create_schema_validated(token_usage_schema)
class TokenUsage:
    """Token usage statistics for a model response."""
    
    input_tokens: int = 0
    """Number of input tokens."""
    
    output_tokens: int = 0
    """Number of output tokens."""
    
    total_tokens: int = 0
    """Total number of tokens."""
    
    def __init__(
        self, 
        input_tokens: int = 0, 
        output_tokens: int = 0,
        total_tokens: Optional[int] = None
    ):
        """Initialize token usage statistics.
        
        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            total_tokens: Total number of tokens. If not provided, calculated from input and output.
        """
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        
        if total_tokens is not None:
            self.total_tokens = total_tokens
        else:
            self.total_tokens = input_tokens + output_tokens
            
    @classmethod
    def create_direct(
        cls,
        input_tokens: int = 0, 
        output_tokens: int = 0,
        total_tokens: Optional[int] = None
    ) -> "TokenUsage":
        """Create a TokenUsage instance directly without schema validation.
        
        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            total_tokens: Total number of tokens. If not provided, calculated from input and output.
            
        Returns:
            A TokenUsage instance.
        """
        instance = cls.__new__(cls)
        
        # Set core attributes
        instance.input_tokens = input_tokens
        instance.output_tokens = output_tokens
        
        if total_tokens is not None:
            instance.total_tokens = total_tokens
        else:
            instance.total_tokens = input_tokens + output_tokens
            
        return instance
            
    def to_dict(self) -> Dict[str, int]:
        """Convert the token usage to a dictionary.
        
        Returns:
            A dictionary representation of the token usage.
        """
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens
        }


@create_schema_validated(cost_estimate_schema)
class CostEstimate:
    """Cost estimate for a model response."""
    
    input_cost: float = 0.0
    """Cost of input tokens in USD."""
    
    output_cost: float = 0.0
    """Cost of output tokens in USD."""
    
    total_cost: float = 0.0
    """Total cost in USD."""
    
    def __init__(
        self, 
        input_cost: float = 0.0, 
        output_cost: float = 0.0,
        total_cost: Optional[float] = None
    ):
        """Initialize cost estimate.
        
        Args:
            input_cost: Cost of input tokens in USD.
            output_cost: Cost of output tokens in USD.
            total_cost: Total cost in USD. If not provided, calculated from input and output.
        """
        self.input_cost = input_cost
        self.output_cost = output_cost
        
        if total_cost is not None:
            self.total_cost = total_cost
        else:
            self.total_cost = input_cost + output_cost
            
    @classmethod
    def create_direct(
        cls,
        input_cost: float = 0.0, 
        output_cost: float = 0.0,
        total_cost: Optional[float] = None
    ) -> "CostEstimate":
        """Create a CostEstimate instance directly without schema validation.
        
        Args:
            input_cost: Cost of input tokens in USD.
            output_cost: Cost of output tokens in USD.
            total_cost: Total cost in USD. If not provided, calculated from input and output.
            
        Returns:
            A CostEstimate instance.
        """
        instance = cls.__new__(cls)
        
        # Set core attributes
        instance.input_cost = input_cost
        instance.output_cost = output_cost
        
        if total_cost is not None:
            instance.total_cost = total_cost
        else:
            instance.total_cost = input_cost + output_cost
            
        return instance

    def __str__(self) -> str:
        """Get a string representation of the cost estimate.

        Returns:
            A formatted cost string.
        """
        # Format costs based on their magnitude for better readability
        if self.total_cost < 0.0000001:
            # For extremely small costs (nearly zero), use scientific notation
            return f"${self.total_cost:.2e} (Input: ${self.input_cost:.2e}, Output: ${self.output_cost:.2e})"
        elif self.total_cost < 0.000001:
            # For extremely small costs, use 7 decimal places
            return f"${self.total_cost:.7f} (Input: ${self.input_cost:.7f}, Output: ${self.output_cost:.7f})"
        elif self.total_cost < 0.001:
            # For very small costs, use 6 decimal places
            return f"${self.total_cost:.6f} (Input: ${self.input_cost:.6f}, Output: ${self.output_cost:.6f})"
        elif self.total_cost < 0.01:
            # For small costs, use 4 decimal places
            return f"${self.total_cost:.4f} (Input: ${self.input_cost:.4f}, Output: ${self.output_cost:.4f})"
        else:
            # For larger costs, use 2 decimal places
            return f"${self.total_cost:.2f} (Input: ${self.input_cost:.2f}, Output: ${self.output_cost:.2f})"
            
    def to_dict(self) -> Dict[str, float]:
        """Convert the cost estimate to a dictionary.
        
        Returns:
            A dictionary representation of the cost estimate.
        """
        return {
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "total_cost": self.total_cost
        }


@create_schema_validated(model_response_schema)
class ModelResponse:
    """Response from a language model."""
    
    content: str
    """The text content of the response."""
    
    model: str
    """The name of the model that generated the response."""
    
    provider: str
    """The provider that generated the response."""
    
    usage: Optional[TokenUsage] = None
    """Token usage statistics."""
    
    cost: Optional[CostEstimate] = None
    """Cost estimate for the response."""
    
    finish_reason: Optional[str] = None
    """The reason the model stopped generating."""
    
    raw_response: Optional[Dict[str, Any]] = None
    """The raw response from the provider API."""
    
    def __init__(
        self,
        content: str,
        model: str,
        provider: str,
        usage: Optional[TokenUsage] = None,
        cost: Optional[CostEstimate] = None,
        finish_reason: Optional[str] = None,
        raw_response: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize a model response.
        
        Args:
            content: The text content of the response.
            model: The name of the model that generated the response.
            provider: The provider that generated the response.
            usage: Token usage statistics.
            cost: Cost estimate for the response.
            finish_reason: The reason the model stopped generating.
            raw_response: The raw response from the provider API.
            **kwargs: Additional parameters.
        """
        self.content = content
        self.model = model
        self.provider = provider
        self.usage = usage if usage is not None else TokenUsage()
        self.cost = cost if cost is not None else CostEstimate()
        self.finish_reason = finish_reason
        self.raw_response = raw_response
        
    @classmethod
    def create_direct(
        cls,
        content: str,
        model: str,
        provider: str,
        usage: Optional[TokenUsage] = None,
        cost: Optional[CostEstimate] = None,
        finish_reason: Optional[str] = None,
        raw_response: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> "ModelResponse":
        """Create a ModelResponse instance directly without schema validation.
        
        Args:
            content: The text content of the response.
            model: The name of the model that generated the response.
            provider: The provider that generated the response.
            usage: Token usage statistics.
            cost: Cost estimate for the response.
            finish_reason: The reason the model stopped generating.
            raw_response: The raw response from the provider API.
            **kwargs: Additional parameters.
            
        Returns:
            A ModelResponse instance.
        """
        instance = cls.__new__(cls)
        
        # Set core attributes
        instance.content = content
        instance.model = model
        instance.provider = provider
        instance.usage = usage if usage is not None else TokenUsage.create_direct()
        instance.cost = cost if cost is not None else CostEstimate.create_direct()
        instance.finish_reason = finish_reason
        instance.raw_response = raw_response
        
        return instance
    
    def __str__(self) -> str:
        """Get a string representation of the response.

        Returns:
            A summary of the response.
        """
        return (
            f"Response from {self.provider}/{self.model}:\n"
            f"Content ({len(self.content)} chars): {self.content[:100]}{'...' if len(self.content) > 100 else ''}\n"
            f"Usage: {self.usage.input_tokens} input, {self.usage.output_tokens} output tokens\n"
            f"Cost: {self.cost}"
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary.
        
        Returns:
            A dictionary representation of the response.
        """
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage.to_dict() if hasattr(self.usage, "to_dict") else self.usage,
            "cost": self.cost.to_dict() if hasattr(self.cost, "to_dict") else self.cost,
            "finish_reason": self.finish_reason,
            # Don't include raw_response to avoid bloating the output
        }