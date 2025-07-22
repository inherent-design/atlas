"""
Task-aware agent implementation for Atlas.

This module defines a specialized Atlas agent that can automatically detect tasks
and select the most appropriate provider for each task.
"""

import logging
from collections.abc import Sequence
from typing import Any, Optional, Union

from atlas.agents.base import AtlasAgent
from atlas.core.config import AtlasConfig
from atlas.core.telemetry import traced
from atlas.providers.base import ModelProvider
from atlas.providers.capabilities import detect_task_type_from_prompt, get_capabilities_for_task

logger = logging.getLogger(__name__)


class TaskAwareAgent(AtlasAgent):
    """Task-aware agent with automatic provider selection.

    This agent extends the base AtlasAgent with automatic task detection and
    provider selection capabilities. It dynamically routes requests to the most
    appropriate provider based on the detected task type.
    """

    def __init__(
        self,
        system_prompt_file: str | None = None,
        collection_name: str = "atlas_knowledge_base",
        config: AtlasConfig | None = None,
        providers: Sequence[ModelProvider] | None = None,
        provider_fallback_strategy: str = "failover",
        streaming_options: dict[str, Any] | None = None,
        **kwargs,
    ):
        """Initialize a task-aware agent.

        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            providers: List of provider instances to use for task routing. At least two are recommended.
            provider_fallback_strategy: Strategy for provider fallback ("failover", "round_robin",
                                       "random", "cost_optimized").
            streaming_options: Optional configuration for streaming behavior.
            **kwargs: Additional parameters to pass to the parent class.

        Raises:
            ValueError: If no providers are specified.
        """
        if not providers:
            raise ValueError("TaskAwareAgent requires at least one provider")

        # Initialize the parent class with task_aware=True
        super().__init__(
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
            config=config,
            providers=providers,
            provider_strategy=provider_fallback_strategy,
            task_aware=True,  # Always use task-aware selection
            streaming_options=streaming_options,
            **kwargs,
        )

        # Store task-aware specific configuration
        self.prompt_enhancements = {}

        # Initialize conversation history
        self.messages = []

        # Set agent version
        self.agent_version = "1.0.0"  # Should come from version module later

    def add_task_prompt_enhancement(self, task_type: str, enhancement: str) -> None:
        """Add a prompt enhancement for a specific task type.

        This allows for specialized prompting based on the detected task. The enhancement
        will be added to the system prompt when the specified task type is detected.

        Args:
            task_type: The task type to enhance prompts for.
            enhancement: The text to add to the system prompt.
        """
        self.prompt_enhancements[task_type] = enhancement
        logger.info(f"Added prompt enhancement for task type: {task_type}")

    @traced(name="process_message_with_task_awareness")
    def process_message(
        self,
        message: str,
        filter: Union[dict[str, Any], "RetrievalFilter"] | None = None,
        use_hybrid_search: bool = False,
        settings: Optional["RetrievalSettings"] = None,
        task_type: str | None = None,
        capabilities: dict[str, Any] | None = None,
    ) -> str:
        """Process a message with automatic task detection and provider selection.

        This overrides the parent method to add automatic task detection and
        prompt enhancement features.

        Args:
            message: The user's message.
            filter: Optional metadata filter to apply during retrieval.
            use_hybrid_search: Whether to use hybrid search.
            settings: Optional retrieval settings for fine-grained control.
            task_type: Optional explicit task type (overrides detection).
            capabilities: Optional capability requirements for provider selection.

        Returns:
            The agent's response.
        """
        # Detect task if not explicitly provided
        detected_task = task_type
        if detected_task is None:
            detected_task = detect_task_type_from_prompt(message)
            logger.info(f"TaskAwareAgent detected task type: {detected_task}")

        # Get capability requirements for this task
        try:
            detected_capabilities = get_capabilities_for_task(detected_task)
            if capabilities:
                # Merge explicit capabilities with detected ones, with explicit taking precedence
                merged_capabilities = detected_capabilities.copy()
                merged_capabilities.update(capabilities)
                capabilities = merged_capabilities
            else:
                capabilities = detected_capabilities

            logger.debug(f"Using capabilities for task {detected_task}: {capabilities}")
        except ValueError:
            # Unknown task type, just use provided capabilities
            logger.warning(f"Unknown task type detected: {detected_task}")
            if not capabilities:
                capabilities = {}

        # Add task-specific prompt enhancement if available
        original_system_prompt = self.system_prompt
        if detected_task in self.prompt_enhancements:
            enhancement = self.prompt_enhancements[detected_task]
            self.system_prompt = (
                f"{original_system_prompt}\n\n## Task-Specific Instructions\n\n{enhancement}"
            )
            logger.debug(f"Added prompt enhancement for task: {detected_task}")

        try:
            # Call the parent method with detected task and capabilities
            return super().process_message(
                message=message,
                filter=filter,
                use_hybrid_search=use_hybrid_search,
                settings=settings,
                task_type=detected_task,
                capabilities=capabilities,
            )
        finally:
            # Restore original system prompt
            self.system_prompt = original_system_prompt

    @traced(name="process_message_streaming_with_task_awareness")
    def process_message_streaming(
        self,
        message: str,
        callback,
        filter: Union[dict[str, Any], "RetrievalFilter"] | None = None,
        use_hybrid_search: bool = False,
        settings: Optional["RetrievalSettings"] = None,
        task_type: str | None = None,
        capabilities: dict[str, Any] | None = None,
        streaming_control: dict[str, Any] | None = None,
    ) -> str:
        """Process a message with streaming and automatic task detection.

        This overrides the parent method to add automatic task detection and
        prompt enhancement features with streaming support.

        Args:
            message: The user's message.
            callback: Function called for each chunk of the response.
            filter: Optional metadata filter to apply during retrieval.
            use_hybrid_search: Whether to use hybrid search.
            settings: Optional retrieval settings for fine-grained control.
            task_type: Optional explicit task type (overrides detection).
            capabilities: Optional capability requirements for provider selection.
            streaming_control: Optional controls for streaming behavior.

        Returns:
            The complete agent response.
        """
        # Detect task if not explicitly provided
        detected_task = task_type
        if detected_task is None:
            detected_task = detect_task_type_from_prompt(message)
            logger.info(f"TaskAwareAgent detected task type: {detected_task}")

        # Get capability requirements for this task
        try:
            detected_capabilities = get_capabilities_for_task(detected_task)
            if capabilities:
                # Merge explicit capabilities with detected ones, with explicit taking precedence
                merged_capabilities = detected_capabilities.copy()
                merged_capabilities.update(capabilities)
                capabilities = merged_capabilities
            else:
                capabilities = detected_capabilities

            logger.debug(f"Using capabilities for task {detected_task}: {capabilities}")
        except ValueError:
            # Unknown task type, just use provided capabilities
            logger.warning(f"Unknown task type detected: {detected_task}")
            if not capabilities:
                capabilities = {}

        # Add task-specific prompt enhancement if available
        original_system_prompt = self.system_prompt
        if detected_task in self.prompt_enhancements:
            enhancement = self.prompt_enhancements[detected_task]
            self.system_prompt = (
                f"{original_system_prompt}\n\n## Task-Specific Instructions\n\n{enhancement}"
            )
            logger.debug(f"Added prompt enhancement for task: {detected_task}")

        try:
            # Call the parent method with detected task and capabilities
            return super().process_message_streaming(
                message=message,
                callback=callback,
                filter=filter,
                use_hybrid_search=use_hybrid_search,
                settings=settings,
                task_type=detected_task,
                capabilities=capabilities,
                streaming_control=streaming_control,
            )
        finally:
            # Restore original system prompt
            self.system_prompt = original_system_prompt
