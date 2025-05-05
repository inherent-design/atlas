"""
Controller agent for the Atlas framework.

This module implements the controller agent that orchestrates multiple worker agents.
"""

import sys
from typing import Dict, Any, Optional


from atlas.core.config import AtlasConfig
from atlas.agents.base import AtlasAgent
from atlas.graph.workflows import run_controller_workflow


class ControllerAgent(AtlasAgent):
    """Controller agent that orchestrates multiple worker agents."""

    def __init__(
        self,
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None,
        worker_count: int = 3,
    ):
        """Initialize the controller agent.

        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            worker_count: Number of worker agents to create.
        """
        # Initialize base agent
        super().__init__(system_prompt_file, collection_name, config)

        # Update config with worker count
        if not config:
            self.config.worker_count = worker_count

        # LangGraph workflow type
        self.workflow_type = "controller"

        # Worker management
        self.worker_count = worker_count
        self.workers = {}
        self.worker_results = {}

    def process_message(self, message: str) -> str:
        """Process a user message using the controller-worker architecture.

        Args:
            message: The user's message.

        Returns:
            The agent's response.
        """
        try:
            # Add user message to history
            self.messages.append({"role": "user", "content": message})

            # Run the controller workflow
            final_state = run_controller_workflow(
                query=message,
                system_prompt_file=None,  # Use default in workflow
                config=self.config,
            )

            # Extract the response (last assistant message)
            assistant_message = ""
            for msg in reversed(final_state.messages):
                if msg["role"] == "assistant":
                    assistant_message = msg["content"]
                    break

            if not assistant_message:
                assistant_message = "I'm sorry, I couldn't generate a response."

            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": assistant_message})

            # Store worker results for later inspection if needed
            self.worker_results = final_state.results

            return assistant_message

        except Exception as e:
            print(f"Error in controller processing: {str(e)}")
            print(f"Error details: {sys.exc_info()}")
            error_msg = "I'm sorry, I encountered an error processing your request. Please try again."
            self.messages.append({"role": "assistant", "content": error_msg})
            return error_msg

    def get_worker_results(self) -> Dict[str, Any]:
        """Get the results from all worker agents.

        Returns:
            A dictionary containing worker results.
        """
        return self.worker_results
