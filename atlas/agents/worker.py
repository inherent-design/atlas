"""
Worker agent for the Atlas framework.

This module implements the worker agents that perform specialized tasks.
"""

import sys
from typing import Dict, Any, Optional, Sequence, Union, Callable, List


from atlas.core.config import AtlasConfig
from atlas.agents.base import AtlasAgent
from atlas.providers.base import ModelProvider
from atlas.providers.capabilities import detect_task_type_from_prompt


class WorkerAgent(AtlasAgent):
    """Worker agent that performs specialized tasks."""

    def __init__(
        self,
        worker_id: str,
        specialization: str,
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None,
        provider: Optional[ModelProvider] = None,
        providers: Optional[Sequence[ModelProvider]] = None,
        provider_strategy: str = "failover",
        task_aware: bool = False,
        task_type_mapping: Optional[Dict[str, List[str]]] = None,
    ):
        """Initialize the worker agent.

        Args:
            worker_id: Unique identifier for this worker.
            specialization: What this worker specializes in.
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            provider: Optional pre-configured provider instance.
            providers: Optional list of provider instances to use in a provider group.
            provider_strategy: Strategy for provider selection in a group.
            task_aware: Whether to enable task-aware provider selection.
            task_type_mapping: Optional mapping of specialization to relevant task types.
        """
        # Initialize base agent
        super().__init__(
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
            config=config,
            provider=provider,
            providers=providers,
            provider_strategy=provider_strategy,
            task_aware=task_aware
        )

        # Worker identity
        self.worker_id = worker_id
        self.specialization = specialization

        # Store task type mapping for specialization-based selection
        self.task_type_mapping = task_type_mapping or {}

        # Enhance system prompt with worker specialization
        specialization_addendum = f"""
## Worker Role

You are a specialized worker agent with ID: {worker_id}
Your specialization is: {specialization}

Focus your analysis and response on this specific aspect of the query.
"""
        self.system_prompt = self.system_prompt + specialization_addendum

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a specific task assigned by the controller.

        Args:
            task: Task definition from the controller.

        Returns:
            Task result.
        """
        try:
            # Extract query from task
            query = task.get("query", "")
            if not query:
                return {
                    "worker_id": self.worker_id,
                    "task_id": task.get("task_id", "unknown"),
                    "status": "error",
                    "error": "No query provided in task",
                    "result": "Could not process task: no query provided",
                }

            # Extract optional task-specific parameters
            task_type = task.get("task_type")
            capabilities = task.get("capabilities")

            # If task type not provided but we're task-aware, try to determine from specialization
            if not task_type and self.task_aware:
                # First try to detect from the query
                detected_task = detect_task_type_from_prompt(query)

                # If this specialization has specific task mappings, check if detected task matches
                if detected_task and self.task_type_mapping:
                    if self.specialization in self.task_type_mapping:
                        relevant_tasks = self.task_type_mapping[self.specialization]
                        if detected_task in relevant_tasks:
                            task_type = detected_task
                            # Only if a match found, use the detected task
                    else:
                        # No mapping for this specialization, use the detected task
                        task_type = detected_task
                else:
                    # No detection or no mapping, try to determine from specialization directly
                    if self.specialization == "Information Retrieval and Document Summarization":
                        task_type = "information_retrieval"
                    elif self.specialization == "Query Analysis and Information Needs Identification":
                        task_type = "analytical_reasoning"
                    elif self.specialization == "Response Generation and Content Creation":
                        task_type = "content_creation"

            # Process query using task-aware processing
            result = self.process_message(
                message=query,
                task_type=task_type,
                capabilities=capabilities
            )

            # Return task result
            return {
                "worker_id": self.worker_id,
                "task_id": task.get("task_id", "unknown"),
                "status": "completed",
                "result": result,
                "task_type": task_type,  # Include detected task type for debugging
            }

        except Exception as e:
            import logging
            logging.error(f"Error in worker processing: {str(e)}", exc_info=True)
            return {
                "worker_id": self.worker_id,
                "task_id": task.get("task_id", "unknown"),
                "status": "error",
                "error": str(e),
                "result": "An error occurred while processing the task",
            }


# Predefined worker types
class RetrievalWorker(WorkerAgent):
    """Worker that specializes in document retrieval and summarization."""

    def __init__(
        self,
        worker_id: str = "retrieval_worker",
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None,
        provider: Optional[ModelProvider] = None,
        providers: Optional[Sequence[ModelProvider]] = None,
        provider_strategy: str = "failover",
        task_aware: bool = False,
    ):
        """Initialize a retrieval worker."""
        # Define specialization
        specialization = "Information Retrieval and Document Summarization"

        # Define relevant task types for this specialization
        task_type_mapping = {
            specialization: [
                "information_retrieval",
                "document_summarization",
                "question_answering"
            ]
        }

        # Initialize worker
        super().__init__(
            worker_id=worker_id,
            specialization=specialization,
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
            config=config,
            provider=provider,
            providers=providers,
            provider_strategy=provider_strategy,
            task_aware=task_aware,
            task_type_mapping=task_type_mapping
        )


class AnalysisWorker(WorkerAgent):
    """Worker that specializes in query analysis and information needs identification."""

    def __init__(
        self,
        worker_id: str = "analysis_worker",
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None,
        provider: Optional[ModelProvider] = None,
        providers: Optional[Sequence[ModelProvider]] = None,
        provider_strategy: str = "failover",
        task_aware: bool = False,
    ):
        """Initialize an analysis worker."""
        # Define specialization
        specialization = "Query Analysis and Information Needs Identification"

        # Define relevant task types for this specialization
        task_type_mapping = {
            specialization: [
                "analytical_reasoning",
                "conceptual_understanding",
                "critical_thinking",
                "problem_solving"
            ]
        }

        # Initialize worker
        super().__init__(
            worker_id=worker_id,
            specialization=specialization,
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
            config=config,
            provider=provider,
            providers=providers,
            provider_strategy=provider_strategy,
            task_aware=task_aware,
            task_type_mapping=task_type_mapping
        )


class DraftWorker(WorkerAgent):
    """Worker that specializes in generating draft responses."""

    def __init__(
        self,
        worker_id: str = "draft_worker",
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None,
        provider: Optional[ModelProvider] = None,
        providers: Optional[Sequence[ModelProvider]] = None,
        provider_strategy: str = "failover",
        task_aware: bool = False,
    ):
        """Initialize a draft worker."""
        # Define specialization
        specialization = "Response Generation and Content Creation"

        # Define relevant task types for this specialization
        task_type_mapping = {
            specialization: [
                "content_creation",
                "creative_writing",
                "text_generation",
                "code_generation"
            ]
        }

        # Initialize worker
        super().__init__(
            worker_id=worker_id,
            specialization=specialization,
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
            config=config,
            provider=provider,
            providers=providers,
            provider_strategy=provider_strategy,
            task_aware=task_aware,
            task_type_mapping=task_type_mapping
        )
