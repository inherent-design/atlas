#!/usr/bin/env python3
"""
Provider Group Example (04_provider_group.py)

This example demonstrates how to use provider groups to combine multiple providers
with fallback capability and different selection strategies.

Usage:
    python examples/04_provider_group.py [--strategy STRATEGY]

Options:
    --strategy STRATEGY  Provider selection strategy to use
                         (failover, round_robin, random, cost_optimized, task_aware)
                         [default: failover]

Strategies explained:
    - failover: Try providers in sequence until one succeeds (default)
    - round_robin: Rotate through providers for load balancing
    - random: Randomly select providers
    - cost_optimized: Try cheaper providers first
    - task_aware: Select providers based on task type detected from prompt
"""

import argparse
import sys
import time
from typing import Any, Dict, List, Optional

# Import common utilities for Atlas examples
from common import (
    handle_example_error,
    highlight,
    print_example_footer,
    print_section,
    setup_example,
)

from atlas.core import logging

# Import Atlas components
from atlas.providers import (
    ModelMessage,
    ModelProvider,
    ModelRequest,
    create_provider,
    create_provider_group,
    discover_providers,
)


def add_example_arguments(parser):
    """Add example-specific arguments to the parser."""
    parser.add_argument(
        "--strategy",
        choices=["failover", "round_robin", "random", "cost_optimized", "task_aware"],
        default="failover",
        help="Provider selection strategy to demonstrate",
    )


# Using common print_section and highlight functions from common.py


def simulate_provider_failure(provider: ModelProvider) -> None:
    """Simulate a provider failure by replacing the generate method temporarily.

    This is for demonstration purposes to show how fallback works.

    Args:
        provider: The provider to modify
    """
    # Store the original generate method
    original_generate = provider.generate

    # Create a wrapper function that will throw an exception
    def failing_generate(request: ModelRequest):
        # Get the provider name safely (with fallback)
        provider_name = getattr(provider, "name", str(provider))
        raise RuntimeError(f"Simulated failure in provider: {provider_name}")

    # Replace the generate method
    provider.generate = failing_generate

    # Return a function to restore the original method
    return lambda: setattr(provider, "generate", original_generate)


# Using common create_providers_for_examples function from common.py
def create_providers_for_example() -> List[ModelProvider]:
    """Create a list of providers to use in the example.

    Returns:
        List of provider instances
    """
    from common import create_providers_for_examples

    # Use the common function with default settings
    return create_providers_for_examples(ensure_mock=True, min_providers=2)


def demonstrate_fallback(
    providers: List[ModelProvider], selection_strategy: str = "failover"
) -> None:
    """Demonstrate provider fallback behavior.

    Args:
        providers: List of provider instances
        selection_strategy: Strategy for selecting providers
    """
    logger = logging.get_logger(__name__)
    print_section("Provider Fallback Demonstration")

    # Create provider group with the specified strategy
    provider_group = create_provider_group(
        providers=providers,
        selection_strategy=selection_strategy,
        name=f"demo_{selection_strategy}",
    )

    # Display group configuration
    provider_names = [getattr(p, "name", str(p)) for p in providers]
    print(f"Provider group created with {len(providers)} providers: {', '.join(provider_names)}")
    print(f"Using '{selection_strategy}' selection strategy")
    print()

    # Create a simple request
    request = ModelRequest(
        messages=[
            ModelMessage.system("You are a helpful assistant."),
            ModelMessage.user("What is your name and model?"),
        ],
        max_tokens=50,
    )

    # Test normal operation first
    print("1. Normal Operation (all providers available):")
    try:
        response = provider_group.generate(request)
        print(highlight(f"Response: {response.content[:100]}...", color="green"))
    except Exception as e:
        logger.exception(f"Error in normal operation: {e}")
        print(highlight(f"Error: {e}", color="red"))
    print()

    # Now simulate failure in the first provider
    print("2. First Provider Failure (simulated):")
    if len(providers) > 1:
        # Simulate failure
        restore_func = simulate_provider_failure(providers[0])

        try:
            response = provider_group.generate(request)
            print(highlight(f"Response: {response.content[:100]}...", color="green"))
            print(
                highlight(
                    "Fallback successful! The request was handled by a subsequent provider.",
                    color="green",
                )
            )
        except Exception as e:
            logger.exception(f"Error in fallback: {e}")
            print(highlight(f"Error: {e}", color="red"))
        finally:
            # Restore original functionality
            restore_func()
    else:
        print("Need at least 2 providers to demonstrate fallback.")
    print()

    # Simulate all providers failing
    print("3. All Providers Failing (simulated):")
    # Store restore functions
    restore_funcs = []

    try:
        # Make all providers fail
        for p in providers:
            restore_funcs.append(simulate_provider_failure(p))

        # Try to generate
        response = provider_group.generate(request)
        print(highlight(f"Response: {response.content[:100]}...", color="green"))
    except Exception as e:
        logger.exception(f"Error when all providers fail: {e}")
        print(highlight(f"Error: {e}", color="red"))
        print(highlight("All providers failed as expected in this scenario.", color="yellow"))
    finally:
        # Restore all providers
        for restore in restore_funcs:
            restore()


def demonstrate_strategy(providers: List[ModelProvider], strategy: str) -> None:
    """Demonstrate a specific provider selection strategy.

    Args:
        providers: List of provider instances
        strategy: Strategy name to demonstrate
    """
    logger = logging.get_logger(__name__)
    print_section(f"'{strategy.title()}' Strategy Demonstration")

    # Create provider group with the specified strategy
    provider_group = create_provider_group(
        providers=providers, selection_strategy=strategy, name=f"demo_{strategy}"
    )

    # Get provider names for display
    provider_names = [getattr(p, "name", str(p)) for p in providers]
    print(f"Provider group with {len(providers)} providers: {', '.join(provider_names)}")
    print(f"Using '{strategy}' selection strategy")
    print()

    # Create different requests to demonstrate the strategy
    request_templates = [
        "Tell me a short joke.",
        "What is the capital of France?",
        "Write a one-sentence poem about the moon.",
        "What is 2+2?",
        "Explain quantum computing in one sentence.",
    ]

    # For task-aware, use more specific requests
    if strategy == "task_aware":
        request_templates = [
            "Write a function in Python to calculate the Fibonacci sequence.",  # code generation
            "Summarize the key points about climate change in 2-3 sentences.",  # summarization
            "Write a creative short poem about autumn leaves.",  # creative writing
            "What is the square root of 144 divided by 4?",  # math problem
            "Extract the names and dates from this text: John Smith was born on April 15, 1982, and married Jane Doe, who was born on August 23, 1984.",  # extraction
        ]

    # Use each request template once
    for i, template in enumerate(request_templates[:3], 1):
        print(f'Request #{i}: "{template}"')

        request = ModelRequest(
            messages=[
                ModelMessage.system(
                    "You are a helpful assistant. Keep responses very short and concise."
                ),
                ModelMessage.user(template),
            ],
            max_tokens=50,
        )

        try:
            start_time = time.time()
            response = provider_group.generate(request)
            end_time = time.time()

            print(highlight(f"Response: {response.content}", color="green"))
            print(f"Time taken: {end_time - start_time:.2f}s")

            # For round robin strategy, show how it rotates through providers
            if strategy == "round_robin":
                print("(Next provider will be different)")

            # For task-aware strategy, explain provider selection
            elif strategy == "task_aware":
                print(
                    f"The request was detected as a specific task type suitable for the selected provider."
                )

        except Exception as e:
            logger.exception(f"Error in strategy demonstration: {e}")
            print(highlight(f"Error: {e}", color="red"))

        print()


def main():
    """Main entry point for the provider group example.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Set up the example with standardized logging and argument parsing
        args = setup_example("Atlas Provider Group Example", add_example_arguments)
        logger = logging.get_logger(__name__)

        # Create providers for the example
        providers = create_providers_for_example()

        if len(providers) < 2:
            logger.error("At least 2 providers are required for this example.")
            print(
                highlight("Error: At least 2 providers are required for this example.", color="red")
            )
            return 1

        # Demonstrate fallback behavior
        demonstrate_fallback(providers, args.strategy)

        # Demonstrate the requested strategy
        demonstrate_strategy(providers, args.strategy)

        # Print footer
        print_example_footer()
        return 0

    except Exception as e:
        logger = logging.get_logger(__name__)
        handle_example_error(
            logger,
            e,
            "Error in provider group example",
            "Try running with only mock providers by setting ATLAS_PROVIDERS=mock",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
