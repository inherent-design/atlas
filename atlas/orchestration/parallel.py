"""
Parallel processing for Atlas agents.

This module provides tools for running agents in parallel.
"""

import os
import sys
import asyncio
import concurrent.futures
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable

from atlas.core.config import AtlasConfig
from atlas.agents.worker import WorkerAgent


async def run_parallel_tasks(
    workers: Dict[str, WorkerAgent],
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Run multiple tasks in parallel using worker agents.
    
    Args:
        workers: Dictionary of worker agents.
        tasks: List of tasks to process.
        
    Returns:
        Dictionary of task results.
    """
    # Match tasks to workers
    task_assignments = {}
    for task in tasks:
        worker_id = task.get("worker_id")
        if not worker_id:
            continue
            
        # Find the worker for this task
        worker = None
        for w in workers.values():
            if w.worker_id == worker_id:
                worker = w
                break
        
        if worker:
            if worker_id not in task_assignments:
                task_assignments[worker_id] = []
            task_assignments[worker_id].append(task)
    
    # Process tasks with workers
    async def process_worker_tasks(worker_id: str, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        worker = None
        for w in workers.values():
            if w.worker_id == worker_id:
                worker = w
                break
        
        if not worker:
            return [{
                "worker_id": worker_id,
                "status": "error",
                "error": f"Worker {worker_id} not found",
                "result": None
            }]
        
        results = []
        for task in tasks:
            # Run task in separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool, worker.process_task, task
                )
                results.append(result)
        
        return results
    
    # Create tasks for each worker
    coroutines = [
        process_worker_tasks(worker_id, tasks)
        for worker_id, tasks in task_assignments.items()
    ]
    
    # Run all tasks in parallel
    all_results = await asyncio.gather(*coroutines)
    
    # Flatten results
    flattened_results = []
    for result_group in all_results:
        flattened_results.extend(result_group)
    
    # Group results by task ID
    results_by_task = {}
    for result in flattened_results:
        task_id = result.get("task_id", "unknown")
        results_by_task[task_id] = result
    
    return results_by_task


def run_tasks_parallel(
    workers: Dict[str, WorkerAgent],
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Run tasks in parallel (synchronous wrapper for async function).
    
    Args:
        workers: Dictionary of worker agents.
        tasks: List of tasks to process.
        
    Returns:
        Dictionary of task results.
    """
    # Use asyncio to run the parallel tasks
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_parallel_tasks(workers, tasks))
    finally:
        loop.close()