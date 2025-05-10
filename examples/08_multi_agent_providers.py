"""
Multi-agent system with provider groups example.

This example demonstrates how to use multiple agents with different provider configurations,
including provider groups and task-aware provider selection. It shows how specialized
agents can use different providers based on their specific tasks.
"""

import argparse
import logging
import os
import sys
from typing import List, Dict, Any, Optional

# Ensure the atlas module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from atlas.providers.base import ModelProvider
from atlas.providers.factory import create_provider
from atlas.providers.resolver import create_provider_from_name
from atlas.agents.controller import ControllerAgent
from atlas.agents.worker import RetrievalWorker, AnalysisWorker, DraftWorker
from examples.common import setup_logger, format_response, handle_example_error

logger = logging.getLogger(__name__)


def create_providers(provider_names: List[str], model_mapping: Dict[str, str]) -> List[ModelProvider]:
    """Create a list of providers from provider names.
    
    Args:
        provider_names: List of provider names to create.
        model_mapping: Mapping of provider names to model names.
        
    Returns:
        List of provider instances.
    """
    providers = []
    
    for provider_name in provider_names:
        model_name = model_mapping.get(provider_name)
        try:
            if model_name:
                provider = create_provider_from_name(provider_name, model_name=model_name)
            else:
                provider = create_provider_from_name(provider_name)
                
            providers.append(provider)
            logger.info(f"Created provider {provider_name} with model {provider.model_name}")
        except Exception as e:
            logger.warning(f"Failed to create provider {provider_name}: {e}")
            
    return providers


def create_controller_with_workers(
    controller_providers: List[ModelProvider],
    worker_providers: List[ModelProvider],
    controller_task_aware: bool = False,
    worker_task_aware: bool = False
) -> ControllerAgent:
    """Create a controller agent with specialized workers.
    
    Args:
        controller_providers: List of providers for the controller.
        worker_providers: List of providers for the workers.
        controller_task_aware: Whether the controller should use task-aware selection.
        worker_task_aware: Whether workers should use task-aware selection.
        
    Returns:
        Configured controller agent.
    """
    # Create a controller agent with provided providers
    controller = ControllerAgent(
        worker_count=3,
        providers=controller_providers,
        provider_strategy="failover",
        task_aware=controller_task_aware,
        worker_providers=worker_providers,
        worker_provider_strategy="failover",
        worker_task_aware=worker_task_aware
    )
    
    # Create specialized workers with task-aware provider selection
    retrieval_worker = RetrievalWorker(
        providers=worker_providers,
        provider_strategy="failover",
        task_aware=worker_task_aware
    )
    
    analysis_worker = AnalysisWorker(
        providers=worker_providers,
        provider_strategy="failover",
        task_aware=worker_task_aware
    )
    
    draft_worker = DraftWorker(
        providers=worker_providers,
        provider_strategy="failover",
        task_aware=worker_task_aware
    )
    
    # Store workers in controller (for demonstration purposes)
    controller.workers = {
        "retrieval": retrieval_worker,
        "analysis": analysis_worker,
        "draft": draft_worker
    }
    
    return controller


def main(args):
    """Run the example."""
    try:
        # Define providers and their models
        model_mapping = {
            "anthropic": args.anthropic_model,
            "openai": args.openai_model,
            "ollama": args.ollama_model,
            "mock": "mock-premium"
        }
        
        # Create providers based on available APIs
        provider_names = args.providers or ["mock", "mock", "mock"]
        providers = create_providers(provider_names, model_mapping)
        
        if len(providers) < 2:
            logger.warning("At least two providers are recommended for provider groups")
            if len(providers) == 0:
                # Create multiple mock providers with different capabilities if no real providers
                mock_basic = create_provider_from_name("mock", model_name="mock-basic")
                mock_standard = create_provider_from_name("mock", model_name="mock-standard")
                mock_premium = create_provider_from_name("mock", model_name="mock-premium")
                providers = [mock_basic, mock_standard, mock_premium]
                
        # Separate providers for controller and workers (could be the same)
        controller_providers = providers
        worker_providers = providers
                
        # Create controller and workers with task-aware provider selection
        agent = create_controller_with_workers(
            controller_providers=controller_providers,
            worker_providers=worker_providers,
            controller_task_aware=args.task_aware,
            worker_task_aware=args.task_aware
        )
        
        print("\n=== Multi-Agent System with Provider Groups ===\n")
        print("This example demonstrates a controller agent with specialized workers,")
        print("each using provider groups with optional task-aware selection.\n")
        
        if args.task_aware:
            print("Task-aware provider selection is ENABLED.\n")
        else:
            print("Task-aware provider selection is DISABLED.\n")
            
        # Demonstrate with different task types
        tasks = {
            "Information retrieval": "Find information about quantum computing and summarize the key concepts",
            "Analytical reasoning": "Analyze the potential social implications of artificial general intelligence",
            "Creative writing": "Write a short story about a programmer who discovers a bug in reality",
            "Code generation": "Create a Python function that implements the merge sort algorithm"
        }
        
        for task_name, query in tasks.items():
            print(f"\n--- Task: {task_name} ---")
            print(f"Query: {query}\n")
            
            # Process the query through the multi-agent system
            response = agent.process_message(query)
            
            # Format and display response
            formatted = format_response(response)
            print(f"Response:\n{formatted}\n")
            
            # Print worker results (simplified for this example)
            worker_results = agent.get_worker_results()
            if worker_results and args.debug:
                print("Worker contributions:")
                for worker_id, result in worker_results.items():
                    if isinstance(result, dict) and "task_type" in result:
                        print(f"  {worker_id}: detected task type = {result['task_type']}")
                print()
            
        print("\n=== Interactive Mode ===\n")
        print("Enter your queries (or 'exit' to quit):")
        
        # Interactive mode
        while True:
            query = input("\nYou: ")
            if query.lower() in ('exit', 'quit', 'q'):
                break
                
            response = agent.process_message(query)
            formatted = format_response(response)
            print(f"\nResponse:\n{formatted}")
            
    except Exception as e:
        handle_example_error(e)


if __name__ == "__main__":
    # Setup logger
    setup_logger()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Multi-agent system with provider groups example")
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=["anthropic", "openai", "ollama", "mock"],
        help="Provider names to use (mock will be used if none specified)",
    )
    parser.add_argument(
        "--anthropic-model",
        default="claude-3-sonnet-20240229",
        help="Anthropic model to use"
    )
    parser.add_argument(
        "--openai-model",
        default="gpt-4o",
        help="OpenAI model to use"
    )
    parser.add_argument(
        "--ollama-model",
        default="llama3",
        help="Ollama model to use"
    )
    parser.add_argument(
        "--task-aware",
        action="store_true",
        help="Enable task-aware provider selection"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger("atlas").setLevel(logging.DEBUG)
    
    main(args)