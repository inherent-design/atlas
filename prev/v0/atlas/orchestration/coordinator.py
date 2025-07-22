"""
Agent coordination for Atlas.

This module provides tools for coordinating multiple agents.
"""

from typing import Any

from atlas.agents.controller import ControllerAgent
from atlas.agents.worker import (
    AnalysisWorker,
    DraftWorker,
    RetrievalWorker,
    WorkerAgent,
)
from atlas.core.config import AtlasConfig


class AgentCoordinator:
    """Coordinator for multiple Atlas agents."""

    def __init__(
        self,
        system_prompt_file: str | None = None,
        collection_name: str = "atlas_knowledge_base",
        config: AtlasConfig | None = None,
        worker_count: int = 3,
    ):
        """Initialize the agent coordinator.

        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            worker_count: Number of worker agents to create.
        """
        # Use provided config or create default
        self.config = config or AtlasConfig(
            collection_name=collection_name,
            parallel_enabled=True,
            worker_count=worker_count,
            model_name="claude-3-7-sonnet-20250219",
            max_tokens=2000,
        )

        # System prompt file
        self.system_prompt_file = system_prompt_file

        # Initialize controller
        self.controller = ControllerAgent(
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
            config=self.config,
            worker_count=worker_count,
        )

        # Initialize worker registry
        self.workers: dict[str, WorkerAgent] = {}
        self._create_default_workers()

    def _create_default_workers(self) -> None:
        """Create default worker agents."""
        # Create retrieval worker
        self.workers["retrieval"] = RetrievalWorker(
            worker_id="retrieval_worker",
            system_prompt_file=self.system_prompt_file,
            collection_name=self.config.collection_name,
            config=self.config,
        )

        # Create analysis worker
        self.workers["analysis"] = AnalysisWorker(
            worker_id="analysis_worker",
            system_prompt_file=self.system_prompt_file,
            collection_name=self.config.collection_name,
            config=self.config,
        )

        # Create draft worker
        self.workers["draft"] = DraftWorker(
            worker_id="draft_worker",
            system_prompt_file=self.system_prompt_file,
            collection_name=self.config.collection_name,
            config=self.config,
        )

    def add_worker(self, worker_type: str, worker_id: str, specialization: str) -> WorkerAgent:
        """Add a new worker agent to the coordinator.

        Args:
            worker_type: Type of worker (custom worker).
            worker_id: Unique identifier for the worker.
            specialization: What the worker specializes in.

        Returns:
            The created worker agent.
        """
        worker = WorkerAgent(
            worker_id=worker_id,
            specialization=specialization,
            system_prompt_file=self.system_prompt_file,
            collection_name=self.config.collection_name,
            config=self.config,
        )

        self.workers[worker_type] = worker
        return worker

    def process_message(self, message: str) -> str:
        """Process a user message using the controller-worker architecture.

        Args:
            message: The user's message.

        Returns:
            The agent's response.
        """
        # Use the controller to process the message
        return self.controller.process_message(message)

    def get_worker_results(self) -> dict[str, Any]:
        """Get the results from all worker agents.

        Returns:
            A dictionary containing worker results.
        """
        return self.controller.get_worker_results()
