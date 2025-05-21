"""
Controller agent for the Atlas framework.

This module implements the controller agent that orchestrates multiple worker agents.
"""

from collections.abc import Callable, Sequence
from typing import Any

from atlas.agents.base import AtlasAgent
from atlas.core.config import AtlasConfig
from atlas.graph.workflows import run_controller_workflow
from atlas.providers.base import ModelProvider


class ControllerAgent(AtlasAgent):
    """Controller agent that orchestrates multiple worker agents."""

    def __init__(
        self,
        system_prompt_file: str | None = None,
        collection_name: str = "atlas_knowledge_base",
        config: AtlasConfig | None = None,
        worker_count: int = 3,
        provider: ModelProvider | None = None,
        providers: Sequence[ModelProvider] | None = None,
        provider_strategy: str = "failover",
        task_aware: bool = False,
        worker_providers: Sequence[ModelProvider] | None = None,
        worker_provider_strategy: str = "failover",
        worker_task_aware: bool = False,
    ):
        """Initialize the controller agent.

        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            worker_count: Number of worker agents to create.
            provider: Optional pre-configured provider instance for the controller.
            providers: Optional list of provider instances for the controller to use in a provider group.
            provider_strategy: Strategy for provider selection for the controller.
            task_aware: Whether to enable task-aware provider selection for the controller.
            worker_providers: Optional list of provider instances for workers to use.
            worker_provider_strategy: Strategy for provider selection for workers.
            worker_task_aware: Whether to enable task-aware provider selection for workers.
        """
        # Initialize base agent
        super().__init__(
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
            config=config,
            provider=provider,
            providers=providers,
            provider_strategy=provider_strategy,
            task_aware=task_aware,
        )

        # Update config with worker count
        if not config:
            self.config.worker_count = worker_count

        # LangGraph workflow type
        self.workflow_type = "controller"

        # Worker management
        self.worker_count = worker_count
        self.workers: dict[str, Any] = {}
        self.worker_results: dict[str, Any] = {}

        # Store worker provider configuration
        self.worker_providers = worker_providers
        self.worker_provider_strategy = worker_provider_strategy
        self.worker_task_aware = worker_task_aware

    def process_message(
        self,
        message: str,
        task_type: str | None = None,
        capabilities: dict[str, Any] | None = None,
    ) -> str:
        """Process a user message using the controller-worker architecture.

        Args:
            message: The user's message.
            task_type: Optional explicit task type for provider selection.
            capabilities: Optional capability requirements for provider selection.

        Returns:
            The agent's response.
        """
        try:
            # Add user message to history
            self.messages.append({"role": "user", "content": message})

            # Run the controller workflow with provider options
            workflow_options = {
                "query": message,
                "system_prompt_file": None,  # Use default in workflow
                "config": self.config,
                "controller_provider": self.provider,  # Use configured provider
                "worker_providers": self.worker_providers,  # Use configured worker providers
                "worker_provider_strategy": self.worker_provider_strategy,
                "worker_task_aware": self.worker_task_aware,
                "task_type": task_type,
                "capabilities": capabilities,
            }

            final_state = run_controller_workflow(**workflow_options)

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
            import logging

            logging.error(f"Error in controller processing: {e!s}", exc_info=True)
            error_msg = (
                "I'm sorry, I encountered an error processing your request. Please try again."
            )
            self.messages.append({"role": "assistant", "content": error_msg})
            return error_msg

    def process_message_streaming(
        self,
        message: str,
        callback: Callable[[str, str], None],
        task_type: str | None = None,
        capabilities: dict[str, Any] | None = None,
        streaming_control: dict[str, Any] | None = None,
    ) -> str:
        """Process a user message with streaming response.

        Args:
            message: The user's message.
            callback: Function called for each chunk of the response, with arguments (delta, full_text).
            task_type: Optional explicit task type for provider selection.
            capabilities: Optional capability requirements for provider selection.
            streaming_control: Optional controls for streaming behavior.

        Returns:
            The complete agent response.
        """
        try:
            # Add user message to history
            self.messages.append({"role": "user", "content": message})

            # Initialize accumulated response
            full_response = ""

            # Define a callback to track the full response
            def track_response(delta, response_so_far):
                nonlocal full_response
                full_response = response_so_far
                # Forward to user-provided callback
                callback(delta, response_so_far)

            # Use parent's streaming ability with task awareness
            result = super().process_message_streaming(
                message=message,
                callback=track_response,
                task_type=task_type,
                capabilities=capabilities,
                streaming_control=streaming_control,
            )

            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": result})

            return result

        except Exception as e:
            import logging

            logging.error(f"Error in controller streaming: {e!s}", exc_info=True)
            error_message = (
                "I'm sorry, I encountered an error processing your request. Please try again."
            )

            # Call callback with error message
            callback(error_message, error_message)

            # Add to message history
            self.messages.append({"role": "assistant", "content": error_message})

            return error_message

    def get_worker_results(self) -> dict[str, Any]:
        """Get the results from all worker agents.

        Returns:
            A dictionary containing worker results.
        """
        return self.worker_results
