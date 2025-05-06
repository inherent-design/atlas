"""
Task scheduling for Atlas agents.

This module provides tools for scheduling and managing agent tasks.
"""

import time
import uuid
from typing import Dict, Any, Optional, Union


class Task:
    """Task definition for Atlas agents."""

    def __init__(
        self,
        task_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        description: str = "",
        query: str = "",
        priority: int = 1,
        **kwargs,
    ):
        """Initialize a task.

        Args:
            task_id: Unique identifier for the task. If None, a random ID is generated.
            worker_id: ID of the worker assigned to this task.
            description: Description of the task.
            query: Query to process.
            priority: Task priority (higher value = higher priority).
            **kwargs: Additional task parameters.
        """
        self.task_id = task_id or f"task_{str(uuid.uuid4())[:8]}"
        self.worker_id = worker_id
        self.description = description
        self.query = query
        self.priority = priority
        self.status = "pending"
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None

        # Add any additional parameters
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "worker_id": self.worker_id,
            "description": self.description,
            "query": self.query,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create a task from dictionary."""
        task = cls(
            task_id=data.get("task_id"),
            worker_id=data.get("worker_id"),
            description=data.get("description", ""),
            query=data.get("query", ""),
            priority=data.get("priority", 1),
        )

        # Set additional attributes
        task.status = data.get("status", "pending")
        task.created_at = data.get("created_at", time.time())
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        task.result = data.get("result")
        task.error = data.get("error")

        return task


class TaskScheduler:
    """Scheduler for Atlas agent tasks."""

    def __init__(self):
        """Initialize the task scheduler."""
        self.tasks = {}
        self.pending_tasks = []
        self.in_progress_tasks = []
        self.completed_tasks = []
        self.failed_tasks = []

    def add_task(self, task: Union[Task, Dict[str, Any]]) -> str:
        """Add a task to the scheduler.

        Args:
            task: Task to add (Task object or dictionary).

        Returns:
            Task ID.
        """
        # Convert dictionary to Task if needed
        if isinstance(task, dict):
            task = Task.from_dict(task)

        # Store the task
        self.tasks[task.task_id] = task
        self.pending_tasks.append(task.task_id)

        return task.task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID.

        Args:
            task_id: Task ID.

        Returns:
            Task if found, None otherwise.
        """
        return self.tasks.get(task_id)

    def get_next_task(self) -> Optional[Task]:
        """Get the next task to process.

        Returns:
            Next task to process, None if no tasks are pending.
        """
        if not self.pending_tasks:
            return None

        # Sort pending tasks by priority (descending)
        sorted_tasks = sorted(
            [self.tasks[task_id] for task_id in self.pending_tasks],
            key=lambda t: t.priority,
            reverse=True,
        )

        # Get the highest priority task
        next_task = sorted_tasks[0]

        # Update task status
        next_task.status = "in_progress"
        next_task.started_at = time.time()

        # Update task lists
        self.pending_tasks.remove(next_task.task_id)
        self.in_progress_tasks.append(next_task.task_id)

        return next_task

    def complete_task(self, task_id: str, result: Any = None) -> bool:
        """Mark a task as completed.

        Args:
            task_id: Task ID.
            result: Task result.

        Returns:
            True if the task was completed, False otherwise.
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        # Update task status
        task.status = "completed"
        task.completed_at = time.time()
        task.result = result

        # Update task lists
        if task_id in self.in_progress_tasks:
            self.in_progress_tasks.remove(task_id)
        self.completed_tasks.append(task_id)

        return True

    def fail_task(self, task_id: str, error: str = "") -> bool:
        """Mark a task as failed.

        Args:
            task_id: Task ID.
            error: Error message.

        Returns:
            True if the task was failed, False otherwise.
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        # Update task status
        task.status = "failed"
        task.completed_at = time.time()
        task.error = error

        # Update task lists
        if task_id in self.in_progress_tasks:
            self.in_progress_tasks.remove(task_id)
        self.failed_tasks.append(task_id)

        return True

    def get_stats(self) -> Dict[str, int]:
        """Get scheduler statistics.

        Returns:
            Dictionary with task counts.
        """
        return {
            "total": len(self.tasks),
            "pending": len(self.pending_tasks),
            "in_progress": len(self.in_progress_tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
        }
