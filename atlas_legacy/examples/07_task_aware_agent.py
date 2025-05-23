"""
Task-aware agent example with provider selection.

This example demonstrates task detection and provider selection capabilities using
the TaskAwareAgent. It shows how the agent can automatically choose the most appropriate
provider for different task types.
"""

import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Ensure the atlas module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from atlas.agents.specialized.task_aware_agent import TaskAwareAgent
from atlas.providers.base import ModelProvider
from atlas.providers.capabilities import CapabilityStrength
from atlas.providers.factory import create_provider
from atlas.providers.resolver import create_provider_from_name
from examples.common import format_response, handle_example_error, setup_logger

logger = logging.getLogger(__name__)


def create_providers(
    provider_names: List[str], model_mapping: Dict[str, str]
) -> List[ModelProvider]:
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


def add_task_examples(agent: TaskAwareAgent) -> None:
    """Add specialized prompt enhancements for different task types.

    Args:
        agent: The TaskAwareAgent instance to configure.
    """
    # Creative writing enhancement
    creative_enhancement = """
When responding to creative writing tasks:
- Use vivid, descriptive language
- Create engaging narratives with a clear structure
- Develop distinctive character voices
- Show emotions through actions and dialogue rather than telling
- Employ literary techniques appropriate to the genre
"""
    agent.add_task_prompt_enhancement("creative_writing", creative_enhancement)

    # Code generation enhancement
    code_enhancement = """
When responding to code generation tasks:
- Follow modern best practices for the language/framework
- Include comments explaining key sections
- Structure code for readability and maintainability
- Consider edge cases and error handling
- Ensure type safety where applicable
"""
    agent.add_task_prompt_enhancement("code_generation", code_enhancement)

    # Analytical reasoning enhancement
    analysis_enhancement = """
When responding to analytical reasoning tasks:
- Consider multiple perspectives and competing hypotheses
- Evaluate evidence methodically and fairly
- Organize thoughts in a logical progression
- Identify assumptions and potential biases
- Draw measured conclusions while acknowledging limitations
"""
    agent.add_task_prompt_enhancement("analytical_reasoning", analysis_enhancement)


def main(args):
    """Run the example."""
    try:
        # Define providers and their models
        model_mapping = {
            "anthropic": args.anthropic_model,
            "openai": args.openai_model,
            "ollama": args.ollama_model,
            "mock": "mock-premium",
        }

        # Create providers based on available APIs
        provider_names = args.providers or ["mock", "mock"]
        providers = create_providers(provider_names, model_mapping)

        if len(providers) < 2:
            logger.warning("At least two providers are recommended for task-aware selection")
            if len(providers) == 0:
                # Create two mock providers with different capabilities if no real providers
                mock_basic = create_provider_from_name("mock", model_name="mock-basic")
                mock_premium = create_provider_from_name("mock", model_name="mock-premium")
                providers = [mock_basic, mock_premium]

        # Create a task-aware agent with the providers
        agent = TaskAwareAgent(
            providers=providers,
            provider_fallback_strategy="failover",
        )

        # Configure task-specific prompt enhancements
        add_task_examples(agent)

        print("\n=== Task-Aware Agent Example ===\n")
        print("This agent automatically detects tasks and selects the best provider.\n")

        # Demonstrate with different task types
        tasks = {
            "Creative writing": "Write a short story about a robot discovering emotions",
            "Code generation": "Create a Python function that calculates Fibonacci numbers recursively",
            "Analytical reasoning": "Analyze the potential implications of quantum computing on cybersecurity",
            "Math problem solving": "Solve the following equation and show your work: 3x² + 8x - 5 = 0",
        }

        for task_name, query in tasks.items():
            print(f"\n--- Task: {task_name} ---")
            print(f"Query: {query}\n")

            # Process the query with task detection
            response = agent.process_message(query)

            # Format and display response
            formatted = format_response(response)
            print(f"Response:\n{formatted}\n")

        print("\n=== Interactive Mode ===\n")
        print("Enter your queries (or 'exit' to quit):")

        # Interactive mode
        while True:
            query = input("\nYou: ")
            if query.lower() in ("exit", "quit", "q"):
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
    parser = argparse.ArgumentParser(description="Task-aware agent example")
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=["anthropic", "openai", "ollama", "mock"],
        help="Provider names to use (mock will be used if none specified)",
    )
    parser.add_argument(
        "--anthropic-model", default="claude-3-sonnet-20240229", help="Anthropic model to use"
    )
    parser.add_argument("--openai-model", default="gpt-4o", help="OpenAI model to use")
    parser.add_argument("--ollama-model", default="llama3", help="Ollama model to use")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger("atlas").setLevel(logging.DEBUG)

    main(args)
