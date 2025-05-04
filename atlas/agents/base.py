"""
Base agent implementation for Atlas.

This module defines the core Atlas agent functionality.
"""

import os
import sys
from typing import Dict, List, Any, Optional, Union

from anthropic import Anthropic

from atlas.core.prompts import load_system_prompt
from atlas.core.config import AtlasConfig
from atlas.knowledge.retrieval import KnowledgeBase


class AtlasAgent:
    """Atlas agent for interacting with users."""

    def __init__(
        self,
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None,
    ):
        """Initialize the Atlas agent.

        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
        """
        # Initialize configuration (use provided or create default)
        self.config = config or AtlasConfig(collection_name=collection_name)

        # Load the system prompt
        self.system_prompt = load_system_prompt(system_prompt_file)

        # Initialize the Anthropic client
        self.anthropic_client = Anthropic(api_key=self.config.anthropic_api_key)

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

            # Generate response using Claude
            response = self.anthropic_client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens,
                system=system_msg,
                messages=self.messages,
            )

            # Extract response text
            assistant_message = response.content[0].text

            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except Exception as e:
            print(f"Error processing message: {str(e)}")
            print(f"Error details: {sys.exc_info()}")
            return "I'm sorry, I encountered an error processing your request. Please try again."
