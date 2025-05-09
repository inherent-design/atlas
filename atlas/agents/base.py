"""
Base agent implementation for Atlas.

This module defines the unified Atlas agent with multi-provider support.
"""

import logging
from typing import Dict, List, Any, Optional, Callable

from atlas.core.prompts import load_system_prompt
from atlas.core.config import AtlasConfig
from atlas.core.telemetry import traced, TracedClass
from atlas.knowledge.retrieval import KnowledgeBase
from atlas.providers.factory import create_provider, discover_providers
from atlas.providers.base import ModelRequest, ModelMessage

logger = logging.getLogger(__name__)


class AtlasAgent(TracedClass):
    """Unified Atlas agent with multi-provider support."""

    def __init__(
        self,
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None,
        provider_name: str = "anthropic",
        model_name: Optional[str] = None,
    ):
        """Initialize the Atlas agent.

        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            provider_name: Name of the model provider to use (anthropic, openai, ollama).
            model_name: Optional name of the specific model to use (defaults to provider's default).

        Raises:
            RuntimeError: If model provider initialization fails.
        """
        # Initialize configuration (use provided or create default)
        self.config = config or AtlasConfig(collection_name=collection_name)

        # Load the system prompt
        self.system_prompt = load_system_prompt(system_prompt_file)

        # Initialize the model provider
        try:
            self.provider = create_provider(
                provider_name=provider_name,
                model_name=model_name or self.config.model_name,
                max_tokens=self.config.max_tokens,
            )

            # Get model name safely with fallback
            model_display_name = getattr(
                self.provider,
                "model_name",
                model_name or self.config.model_name or "unknown",
            )

            logger.info(
                f"Using {provider_name} provider with model: {model_display_name}"
            )
        except Exception as e:
            error_msg = f"Failed to initialize model provider: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Initialize knowledge base
        self.knowledge_base = KnowledgeBase(
            collection_name=self.config.collection_name, db_path=self.config.db_path
        )

        # Initialize conversation history
        self.messages: List[Dict[str, str]] = []

        # Set up agent metadata
        self.agent_id = f"atlas-{provider_name}-{self.provider.model_name}"
        self.agent_version = "1.0.0"  # Should come from version module later

    @traced(name="query_knowledge_base")
    def query_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant information.

        Args:
            query: The query string.

        Returns:
            A list of relevant documents.
        """
        return self.knowledge_base.retrieve(query)

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
    def process_message(self, message: str) -> str:
        """Process a user message and return the agent's response.

        Args:
            message: The user's message.

        Returns:
            The agent's response.
        """
        try:
            # Add user message to history
            self.messages.append({"role": "user", "content": message})

            # Retrieve relevant documents from the knowledge base
            logger.info(
                f"Querying knowledge base: {message[:50]}{'...' if len(message) > 50 else ''}"
            )
            documents = self.query_knowledge_base(message)
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

            # Generate response using the model provider
            model_request = ModelRequest(
                messages=[ModelMessage.user(msg["content"]) for msg in self.messages],
                system_prompt=system_msg,
                max_tokens=self.config.max_tokens,
            )

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
        self, message: str, callback: Callable[[str, str], None]
    ) -> str:
        """Process a user message with streaming response.

        Args:
            message: The user's message.
            callback: Function called for each chunk of the response, with arguments (delta, full_text).

        Returns:
            The complete agent response.
        """
        try:
            # Add user message to history
            self.messages.append({"role": "user", "content": message})

            # Retrieve relevant documents from the knowledge base
            logger.info(
                f"Querying knowledge base: {message[:50]}{'...' if len(message) > 50 else ''}"
            )
            documents = self.query_knowledge_base(message)
            logger.info(f"Retrieved {len(documents)} relevant documents")

            # Create system message with context
            system_msg = self.system_prompt
            if documents:
                context_text = self.format_knowledge_context(documents)
                system_msg = system_msg + context_text

            # Create model request
            model_request = ModelRequest(
                messages=[ModelMessage.user(msg["content"]) for msg in self.messages],
                system_prompt=system_msg,
                max_tokens=self.config.max_tokens,
            )

            # Stream response
            try:
                initial_response, stream_handler = self.provider.stream(model_request)

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
