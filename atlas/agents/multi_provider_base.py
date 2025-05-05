"""
Multi-provider capable Atlas agent.

This module defines an enhanced Atlas agent that can use various model providers.
"""

import sys
from typing import Dict, List, Any, Optional

from atlas.core.prompts import load_system_prompt
from atlas.core.config import AtlasConfig
from atlas.core.providers import create_provider, get_available_providers, ModelProvider
from atlas.knowledge.retrieval import KnowledgeBase


class MultiProviderAgent:
    """Atlas agent with support for multiple model providers."""

    def __init__(
        self,
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None,
        provider_name: str = "anthropic",
        model_name: Optional[str] = None,
    ):
        """Initialize the multi-provider Atlas agent.

        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            provider_name: Name of the model provider to use (anthropic, openai, ollama).
            model_name: Optional name of the specific model to use (defaults to provider's default).
        """
        # Initialize configuration (use provided or create default)
        self.config = config or AtlasConfig(collection_name=collection_name)

        # Load the system prompt
        self.system_prompt = load_system_prompt(system_prompt_file)

        # Initialize model provider
        try:
            self.provider = create_provider(
                provider_name=provider_name,
                model_name=model_name or self.config.model_name,
                max_tokens=self.config.max_tokens,
            )
            
            print(f"Using {provider_name} provider with model: {self.provider.model_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize model provider: {str(e)}")

        # Initialize knowledge base
        self.knowledge_base = KnowledgeBase(
            collection_name=self.config.collection_name, db_path=self.config.db_path
        )

        # Initialize conversation history
        self.messages = []

    def query_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant information.

        Args:
            query: The query string.

        Returns:
            A list of relevant documents.
        """
        return self.knowledge_base.retrieve(query)

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
            print(
                f"Querying knowledge base for: {message[:50]}{'...' if len(message) > 50 else ''}"
            )
            documents = self.query_knowledge_base(message)
            print(f"Retrieved {len(documents)} relevant documents")

            if documents:
                # Print top documents for debugging
                print("Top relevant documents:")
                for i, doc in enumerate(documents[:3]):
                    source = doc["metadata"].get("source", "Unknown")
                    score = doc["relevance_score"]
                    print(f"  {i + 1}. {source} (score: {score:.4f})")

            # Create system message with context
            system_msg = self.system_prompt
            if documents:
                context_text = "\n\n## Relevant Knowledge\n\n"
                for i, doc in enumerate(
                    documents[:3]
                ):  # Limit to top 3 most relevant docs
                    source = doc["metadata"].get("source", "Unknown")
                    content = doc["content"]
                    context_text += f"### Document {i + 1}: {source}\n{content}\n\n"

                system_msg = system_msg + context_text

            # Generate response using configured model provider
            response = self.provider.generate_response(
                system_prompt=system_msg,
                messages=self.messages,
                max_tokens=self.config.max_tokens,
            )

            # Extract response text
            assistant_message = response.content.text
            
            # Log usage statistics
            if response.usage:
                input_tokens = response.usage.get("input_tokens", 0)
                output_tokens = response.usage.get("output_tokens", 0)
                print(f"API Usage: {input_tokens} input tokens, {output_tokens} output tokens")
                
                # Calculate cost
                input_cost, output_cost, total_cost = self.provider.calculate_cost(response.usage)
                print(f"Estimated Cost: ${total_cost:.6f} (Input: ${input_cost:.6f}, Output: ${output_cost:.6f})")
            
            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except Exception as e:
            print(f"Error processing message: {str(e)}")
            print(f"Error details: {sys.exc_info()}")
            return "I'm sorry, I encountered an error processing your request. Please try again."


def list_available_providers() -> Dict[str, List[str]]:
    """List all available model providers and their supported models.
    
    Returns:
        Dictionary of provider names to lists of model names.
    """
    providers = get_available_providers()
    
    # Format for display
    print("Available Model Providers:")
    for provider, models in providers.items():
        model_list = ", ".join(models)
        print(f"  - {provider}: {model_list}")
    
    return providers