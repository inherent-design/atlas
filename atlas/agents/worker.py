"""
Worker agent for the Atlas framework.

This module implements the worker agents that perform specialized tasks.
"""

import os
import sys
from typing import Dict, List, Any, Optional, Union

from anthropic import Anthropic

from atlas.core.prompts import load_system_prompt
from atlas.core.config import AtlasConfig
from atlas.knowledge.retrieval import KnowledgeBase
from atlas.agents.base import AtlasAgent
from atlas.graph.workflows import run_rag_workflow


class WorkerAgent(AtlasAgent):
    """Worker agent that performs specialized tasks."""
    
    def __init__(
        self, 
        worker_id: str,
        specialization: str,
        system_prompt_file: Optional[str] = None, 
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None
    ):
        """Initialize the worker agent.
        
        Args:
            worker_id: Unique identifier for this worker.
            specialization: What this worker specializes in.
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
        """
        # Initialize base agent
        super().__init__(system_prompt_file, collection_name, config)
        
        # Worker identity
        self.worker_id = worker_id
        self.specialization = specialization
        
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
                    "result": "Could not process task: no query provided"
                }
            
            # Process query using basic RAG workflow
            result = self.process_message(query)
            
            # Return task result
            return {
                "worker_id": self.worker_id,
                "task_id": task.get("task_id", "unknown"),
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            print(f"Error in worker processing: {str(e)}")
            print(f"Error details: {sys.exc_info()}")
            return {
                "worker_id": self.worker_id,
                "task_id": task.get("task_id", "unknown"),
                "status": "error",
                "error": str(e),
                "result": "An error occurred while processing the task"
            }


# Predefined worker types
class RetrievalWorker(WorkerAgent):
    """Worker that specializes in document retrieval and summarization."""
    
    def __init__(
        self,
        worker_id: str = "retrieval_worker",
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None
    ):
        """Initialize a retrieval worker."""
        # Define specialization
        specialization = "Information Retrieval and Document Summarization"
        
        # Initialize worker
        super().__init__(worker_id, specialization, system_prompt_file, collection_name, config)


class AnalysisWorker(WorkerAgent):
    """Worker that specializes in query analysis and information needs identification."""
    
    def __init__(
        self,
        worker_id: str = "analysis_worker",
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None
    ):
        """Initialize an analysis worker."""
        # Define specialization
        specialization = "Query Analysis and Information Needs Identification"
        
        # Initialize worker
        super().__init__(worker_id, specialization, system_prompt_file, collection_name, config)


class DraftWorker(WorkerAgent):
    """Worker that specializes in generating draft responses."""
    
    def __init__(
        self,
        worker_id: str = "draft_worker",
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None
    ):
        """Initialize a draft worker."""
        # Define specialization
        specialization = "Response Generation and Content Creation"
        
        # Initialize worker
        super().__init__(worker_id, specialization, system_prompt_file, collection_name, config)