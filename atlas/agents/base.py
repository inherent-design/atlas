"""
Base agent implementation for Atlas.

This module defines the unified Atlas agent with multi-provider support.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Union, Sequence

from atlas.core.prompts import load_system_prompt
from atlas.core.config import AtlasConfig
from atlas.core.telemetry import traced, TracedClass
from atlas.knowledge.retrieval import KnowledgeBase
from atlas.providers.factory import create_provider, discover_providers
from atlas.providers.base import ModelRequest, ModelMessage, ModelProvider
from atlas.providers.options import ProviderOptions
from atlas.providers.group import ProviderGroup, ProviderSelectionStrategy, TaskAwareSelectionStrategy
from atlas.providers.resolver import create_provider_from_options, resolve_provider_options
from atlas.providers.capabilities import detect_task_type_from_prompt, get_capabilities_for_task

logger = logging.getLogger(__name__)


class AtlasAgent(TracedClass):
    """Unified Atlas agent with multi-provider support."""

    def __init__(
        self,
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None,
        provider: Optional[ModelProvider] = None,
        provider_options: Optional[ProviderOptions] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        capability: Optional[str] = None,
        providers: Optional[Sequence[ModelProvider]] = None,
        provider_strategy: str = "failover",
        task_aware: bool = False,
        streaming_options: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize the Atlas agent.

        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            provider: Optional pre-configured provider instance. If provided, other provider options are ignored.
            provider_options: Optional pre-configured ProviderOptions instance. If provided, individual
                              provider parameters are ignored.
            provider_name: Optional name of the model provider to use (anthropic, openai, ollama, mock).
            model_name: Optional name of the specific model to use (defaults to provider's default).
            capability: Optional capability for model selection (inexpensive, efficient, premium, vision).
            providers: Optional list of provider instances to use in a provider group.
            provider_strategy: Strategy for provider selection in a group ("failover", "round_robin", "random",
                              "cost_optimized", or "task_aware").
            task_aware: Whether to enable task-aware provider selection.
            streaming_options: Optional configuration for streaming behavior.
            **kwargs: Additional provider parameters to pass through.

        Raises:
            RuntimeError: If model provider initialization fails.
            ValueError: If both provider and providers are specified.
        """
        # Initialize configuration (use provided or create default)
        self.config = config or AtlasConfig(collection_name=collection_name)

        # Load the system prompt
        self.system_prompt = load_system_prompt(system_prompt_file)

        # Store provider options for potential reuse
        self.provider_options = None

        # Store streaming options
        self.streaming_options = streaming_options or {}

        # Initialize the model provider
        try:
            # Check for conflicting provider specifications
            if provider is not None and providers is not None:
                raise ValueError("Cannot specify both 'provider' and 'providers'")

            # If a provider group is requested via multiple providers
            if providers is not None:
                # Select the appropriate strategy
                strategy = self._get_provider_strategy(provider_strategy, task_aware)

                # Create a provider group with the specified strategy
                group_name = f"atlas_provider_group_{provider_strategy}"
                self.provider = ProviderGroup(providers, strategy, name=group_name)

                # Store whether this is task-aware for message processing
                self.task_aware = task_aware

            # If a single provider is already provided, use it directly
            elif provider is not None:
                self.provider = provider
                self.task_aware = False
            else:
                # Determine provider options - either use provided options or create new ones
                if provider_options is not None:
                    # Use provided provider options directly
                    options = provider_options
                else:
                    # Create options for provider factory from individual parameters
                    options_kwargs = {
                        "provider_name": provider_name or "anthropic",
                        "model_name": model_name or self.config.model_name,
                        "capability": capability,
                    }

                    # Only add max_tokens if not in kwargs to avoid duplicate argument errors
                    if "max_tokens" not in kwargs and self.config.max_tokens is not None:
                        options_kwargs["max_tokens"] = self.config.max_tokens

                    # Extract known ProviderOptions parameters, put everything else in extra_params
                    known_params = ["provider_name", "model_name", "capability", "max_tokens", "base_url"]
                    extra_params = {k: v for k, v in kwargs.items() if k not in known_params}

                    # Create options with core parameters
                    options = ProviderOptions(**options_kwargs)

                    # Add any extra parameters to extra_params field
                    if extra_params:
                        options.extra_params.update(extra_params)

                # Store resolved options for potential reuse
                self.provider_options = resolve_provider_options(options)

                # Create the provider with all detection logic handled in the factory
                self.provider = create_provider_from_options(self.provider_options)
                self.task_aware = False

            # Get model name safely with fallback
            model_display_name = getattr(
                self.provider,
                "model_name",
                model_name or self.config.model_name or "unknown",
            )

            # Get provider name safely with fallback
            provider_display_name = getattr(
                self.provider,
                "name",
                provider_name or "unknown",
            )

            logger.info(
                f"Using {provider_display_name} provider with model: {model_display_name}"
            )

            # Set up agent metadata
            self.agent_id = f"atlas-{provider_display_name}-{model_display_name}"

        except Exception as e:
            error_msg = f"Failed to initialize model provider: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Initialize knowledge base
        self.knowledge_base = KnowledgeBase(
            collection_name=self.config.collection_name, db_path=self.config.db_path
        )

        # Initialize conversation history
        self.messages = []

        # Set agent version
        self.agent_version = "1.0.0"  # Should come from version module later

    def _get_provider_strategy(self, strategy: str, task_aware: bool) -> Callable:
        """Get the provider selection strategy function based on the strategy name.

        Args:
            strategy: The strategy name.
            task_aware: Whether to use task-aware provider selection.

        Returns:
            Strategy function to use.

        Raises:
            ValueError: If an invalid strategy is specified.
        """
        # If task-aware is requested, it overrides other strategies
        if task_aware:
            return TaskAwareSelectionStrategy.select

        # Otherwise, select the strategy based on the name
        strategy_map = {
            "failover": ProviderSelectionStrategy.failover,
            "round_robin": ProviderSelectionStrategy.round_robin,
            "random": ProviderSelectionStrategy.random,
            "cost_optimized": ProviderSelectionStrategy.cost_optimized,
        }

        if strategy not in strategy_map:
            raise ValueError(f"Invalid provider strategy: {strategy}. "
                             f"Valid options are: {', '.join(strategy_map.keys())}")

        return strategy_map[strategy]

    def __post_init__(self):
        """Additional initialization steps after __init__."""
        # Initialize knowledge base
        self.knowledge_base = KnowledgeBase(
            collection_name=self.config.collection_name, db_path=self.config.db_path
        )

        # Initialize conversation history
        self.messages: List[Dict[str, str]] = []

        # Set agent version
        self.agent_version = "1.0.0"  # Should come from version module later

    @traced(name="query_knowledge_base")
    def query_knowledge_base(
        self,
        query: str,
        filter: Optional[Any] = None,
        settings: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant information.

        Args:
            query: The query string.
            filter: Optional filter for retrieval.
            settings: Optional retrieval settings for fine-grained control.

        Returns:
            A list of relevant documents.
        """
        return self.knowledge_base.retrieve(query, filter=filter, settings=settings)

    @traced(name="format_knowledge_context")
    def format_knowledge_context(self, documents: List[Any]) -> str:
        """Format retrieved documents as context for the model.

        Args:
            documents: List of documents retrieved from knowledge base.
                Can be either dictionaries or RetrievalResult objects.

        Returns:
            Formatted context string to append to system prompt.
        """
        if not documents:
            return ""

        context_text = "\n\n## Relevant Knowledge\n\n"

        # Use only the top 3 most relevant documents to avoid token limits
        for i, doc in enumerate(documents[:3]):
            # Handle both dictionary format and RetrievalResult objects
            if hasattr(doc, 'metadata') and hasattr(doc, 'content'):
                # RetrievalResult object
                source = doc.metadata.get("source", "Unknown")
                content = doc.content
            else:
                # Dictionary format
                source = doc["metadata"].get("source", "Unknown")
                content = doc["content"]
                
            context_text += f"### Document {i + 1}: {source}\n{content}\n\n"

        return context_text

    @traced(name="process_message")
    def process_message(
        self,
        message: str,
        filter: Optional[Union[Dict[str, Any], 'RetrievalFilter']] = None,
        use_hybrid_search: bool = False,
        settings: Optional['RetrievalSettings'] = None,
        task_type: Optional[str] = None,
        capabilities: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Process a user message and return the agent's response.

        Args:
            message: The user's message.
            filter: Optional metadata filter to apply during retrieval.
            use_hybrid_search: Whether to use hybrid search combining semantic and keyword search.
            settings: Optional retrieval settings for fine-grained control. If provided, overrides
                     filter and use_hybrid_search.
            task_type: Optional explicit task type for provider selection.
            capabilities: Optional capability requirements for provider selection.

        Returns:
            The agent's response.
        """
        try:
            from atlas.knowledge.retrieval import RetrievalFilter, RetrievalSettings

            # Add user message to history
            self.messages.append({"role": "user", "content": message})

            # Prepare retrieval settings
            retrieval_filter = None
            retrieval_settings = settings

            if filter is not None and not settings:
                if isinstance(filter, dict):
                    retrieval_filter = RetrievalFilter(where=filter)
                elif hasattr(filter, 'where'):  # Assuming it's a RetrievalFilter instance
                    retrieval_filter = filter
                else:
                    raise TypeError("filter must be a dictionary or RetrievalFilter object")

            if not settings and use_hybrid_search:
                retrieval_settings = RetrievalSettings(use_hybrid_search=True)

            # Retrieve relevant documents from the knowledge base
            logger.info(
                f"Querying knowledge base: {message[:50]}{'...' if len(message) > 50 else ''}"
            )
            documents = self.query_knowledge_base(
                message,
                filter=retrieval_filter,
                settings=retrieval_settings
            )
            logger.info(f"Retrieved {len(documents)} relevant documents")

            if documents:
                # Log top documents for debugging
                logger.debug("Top relevant documents:")
                for i, doc in enumerate(documents[:3]):
                    # Handle both dictionary format and RetrievalResult objects
                    if hasattr(doc, 'metadata') and hasattr(doc, 'relevance_score'):
                        # RetrievalResult object
                        source = doc.metadata.get("source", "Unknown")
                        score = doc.relevance_score
                    else:
                        # Dictionary format
                        source = doc["metadata"].get("source", "Unknown")
                        score = doc["relevance_score"]
                    logger.debug(f"  {i + 1}. {source} (score: {score:.4f})")

            # Create system message with context
            system_msg = self.system_prompt
            if documents:
                context_text = self.format_knowledge_context(documents)
                system_msg = system_msg + context_text

            # Detect task type if task-aware and not explicitly provided
            detected_task = None
            if self.task_aware and task_type is None:
                detected_task = detect_task_type_from_prompt(message)
                logger.info(f"Detected task type: {detected_task}")

            # Create model request with task information
            model_request = ModelRequest(
                messages=[ModelMessage.user(msg["content"]) for msg in self.messages],
                system_prompt=system_msg,
                max_tokens=self.config.max_tokens,
            )

            # Add task information to metadata if available
            if not hasattr(model_request, 'metadata'):
                model_request.metadata = {}

            if detected_task:
                model_request.metadata['task_type'] = detected_task
            elif task_type:
                model_request.metadata['task_type'] = task_type

            # Add capability requirements if provided
            if capabilities:
                model_request.metadata['capabilities'] = capabilities

            # Generate response using the model provider
            response = self.provider.generate(model_request)

            # Extract response text
            assistant_message = response.content

            # Log usage statistics
            if response.usage:
                logger.info(
                    f"API Usage: {response.usage.input_tokens} input tokens, {response.usage.output_tokens} output tokens"
                )
                # Safely format cost even if it's a mock object
                try:
                    cost_str = str(response.cost)
                    logger.info(f"Estimated Cost: {cost_str}")
                except Exception as cost_err:
                    # Handle format issues with mock objects
                    logger.info("Estimated Cost: [Cost info not available]")
                    logger.debug(f"Cost formatting error: {str(cost_err)}")

            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return "I'm sorry, I encountered an error processing your request. Please try again."

    @traced(name="process_message_streaming")
    def process_message_streaming(
        self,
        message: str,
        callback: Callable[[str, str], None],
        filter: Optional[Union[Dict[str, Any], 'RetrievalFilter']] = None,
        use_hybrid_search: bool = False,
        settings: Optional['RetrievalSettings'] = None,
        task_type: Optional[str] = None,
        capabilities: Optional[Dict[str, Any]] = None,
        streaming_control: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Process a user message with streaming response.

        Args:
            message: The user's message.
            callback: Function called for each chunk of the response, with arguments (delta, full_text).
            filter: Optional metadata filter to apply during retrieval.
            use_hybrid_search: Whether to use hybrid search combining semantic and keyword search.
            settings: Optional retrieval settings for fine-grained control. If provided, overrides
                     filter and use_hybrid_search.
            task_type: Optional explicit task type for provider selection.
            capabilities: Optional capability requirements for provider selection.
            streaming_control: Optional controls for streaming behavior (pause, resume, cancel).

        Returns:
            The complete agent response.
        """
        try:
            from atlas.knowledge.retrieval import RetrievalFilter, RetrievalSettings

            # Add user message to history
            self.messages.append({"role": "user", "content": message})

            # Prepare retrieval settings
            retrieval_filter = None
            retrieval_settings = settings

            if filter is not None and not settings:
                if isinstance(filter, dict):
                    retrieval_filter = RetrievalFilter(where=filter)
                elif hasattr(filter, 'where'):  # Assuming it's a RetrievalFilter instance
                    retrieval_filter = filter
                else:
                    raise TypeError("filter must be a dictionary or RetrievalFilter object")

            if not settings and use_hybrid_search:
                retrieval_settings = RetrievalSettings(use_hybrid_search=True)

            # Retrieve relevant documents from the knowledge base
            logger.info(
                f"Querying knowledge base: {message[:50]}{'...' if len(message) > 50 else ''}"
            )
            documents = self.query_knowledge_base(
                message,
                filter=retrieval_filter,
                settings=retrieval_settings
            )
            logger.info(f"Retrieved {len(documents)} relevant documents")

            # Create system message with context
            system_msg = self.system_prompt
            if documents:
                context_text = self.format_knowledge_context(documents)
                system_msg = system_msg + context_text

            # Detect task type if task-aware and not explicitly provided
            detected_task = None
            if self.task_aware and task_type is None:
                detected_task = detect_task_type_from_prompt(message)
                logger.info(f"Detected task type: {detected_task}")

            # Create model request with task information
            model_request = ModelRequest(
                messages=[ModelMessage.user(msg["content"]) for msg in self.messages],
                system_prompt=system_msg,
                max_tokens=self.config.max_tokens,
            )

            # Add task information to metadata if available
            if not hasattr(model_request, 'metadata'):
                model_request.metadata = {}

            if detected_task:
                model_request.metadata['task_type'] = detected_task
            elif task_type:
                model_request.metadata['task_type'] = task_type

            # Add capability requirements if provided
            if capabilities:
                model_request.metadata['capabilities'] = capabilities

            # Add streaming options if available
            if streaming_control:
                model_request.metadata['streaming_control'] = streaming_control
            elif self.streaming_options:
                model_request.metadata['streaming_control'] = self.streaming_options

            # Stream response
            try:
                # Try streaming API with task & capability awareness
                initial_response, stream_handler = self.provider.generate_stream(model_request)

                # Define a callback adapter to match our function signature
                def process_chunk(delta, response):
                    callback(delta, response.content)

                # Process the stream
                final_response = stream_handler.process_stream(process_chunk)

                # Extract response text
                assistant_message = final_response.content

                # Log usage statistics
                if final_response.usage:
                    logger.info(
                        f"API Usage: {final_response.usage.input_tokens} input tokens, "
                        f"{final_response.usage.output_tokens} output tokens"
                    )
                    # Safely format cost even if it's a mock object
                    try:
                        cost_str = str(final_response.cost)
                        logger.info(f"Estimated Cost: {cost_str}")
                    except Exception as cost_err:
                        # Handle format issues with mock objects
                        logger.info("Estimated Cost: [Cost info not available]")
                        logger.debug(f"Cost formatting error: {str(cost_err)}")

                # Add assistant response to history
                self.messages.append(
                    {"role": "assistant", "content": assistant_message}
                )

                return assistant_message

            except (NotImplementedError, AttributeError):
                # Try legacy stream method for backward compatibility
                try:
                    initial_response, stream_handler = self.provider.stream(model_request)

                    # Define a callback adapter to match our function signature
                    def process_chunk(delta, response):
                        callback(delta, response.content)

                    # Process the stream
                    final_response = stream_handler.process_stream(process_chunk)

                    # Extract response text
                    assistant_message = final_response.content

                    # Add assistant response to history
                    self.messages.append(
                        {"role": "assistant", "content": assistant_message}
                    )

                    return assistant_message

                except NotImplementedError:
                    # Fallback to non-streaming if provider doesn't support it
                    logger.warning(
                        f"Streaming not supported by {self.provider.name} provider, fallback to non-streaming"
                    )
                    response = self.provider.generate(model_request)
                    assistant_message = response.content

                    # Call callback once with full response
                    callback(assistant_message, assistant_message)

                    # Add assistant response to history
                    self.messages.append(
                        {"role": "assistant", "content": assistant_message}
                    )

                    return assistant_message

        except Exception as e:
            logger.error(f"Error processing streaming message: {str(e)}", exc_info=True)
            error_message = "I'm sorry, I encountered an error processing your request. Please try again."

            # Call callback with error message
            callback(error_message, error_message)
            return error_message

    def reset_conversation(self):
        """Reset the conversation history."""
        self.messages = []
        logger.info("Conversation history reset")


def list_available_providers() -> Dict[str, List[str]]:
    """List all available model providers and their supported models.

    Returns:
        Dictionary of provider names to lists of model names.
    """
    providers = discover_providers()

    # Format for display
    logger.info("Available Model Providers:")
    for provider, models in providers.items():
        model_list = ", ".join(models)
        logger.info(f"  - {provider}: {model_list}")

    return providers
