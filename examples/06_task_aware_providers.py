#!/usr/bin/env python3
"""
Task-Aware Provider Selection Example (05_task_aware_providers.py)

This example demonstrates how to use task-aware provider selection to automatically
choose the best provider based on the type of task detected in the user's prompt.

Usage:
    python examples/05_task_aware_providers.py [--providers PROVIDER1,PROVIDER2,...]

Options:
    --providers PROVIDERS  Comma-separated list of providers to include
                           [default: all available providers]

Key Features Demonstrated:
    - Task detection from prompts
    - Capability-based provider selection
    - Provider group with task-aware selection strategy
    - Automatic task capability mapping
"""

import sys
import argparse
from typing import List, Dict, Any, Optional

# Import common utilities for Atlas examples
from common import setup_example, print_example_footer, handle_example_error, print_section, highlight
from atlas.core import logging

# Import Atlas components
from atlas.providers import (
    create_provider,
    create_provider_group,
    discover_providers,
    ModelProvider,
    ModelRequest, 
    ModelMessage,
)
from atlas.providers.capabilities import (
    detect_task_type_from_prompt,
    get_capabilities_for_task,
    CapabilityStrength,
    TASK_CONVERSATIONAL,
    TASK_CODE_GENERATION,
    TASK_SUMMARIZATION,
    TASK_CREATIVE_WRITING,
    TASK_DATA_ANALYSIS,
    TASK_INFORMATION_EXTRACTION,
    TASK_MATH_PROBLEM_SOLVING,
)


def add_example_arguments(parser):
    """Add example-specific arguments to the parser."""
    parser.add_argument(
        "--providers",
        help="Comma-separated list of providers to include (default: all available)"
    )


# Using common print_section and highlight functions from common.py


# Using common create_provider_group_for_examples function from common.py
def create_provider_group_for_example(provider_names: Optional[List[str]] = None) -> ModelProvider:
    """Create a provider group with task-aware selection for the example.

    Args:
        provider_names: Optional list of specific provider names to include

    Returns:
        ProviderGroup instance with task-aware selection

    Raises:
        RuntimeError: If no suitable providers are available
    """
    from common import create_provider_group_for_examples

    # Use the common function with task-aware selection strategy
    return create_provider_group_for_examples(
        provider_names=provider_names,
        selection_strategy="task_aware",
        name="task_aware_provider_group",
        min_providers=2
    )


def demonstrate_task_detection() -> None:
    """Demonstrate how task types are detected from prompts."""
    print_section("Task Detection Demonstration")
    
    # Example prompts for different task types
    example_prompts = {
        TASK_CONVERSATIONAL: "How's the weather today?",
        TASK_CODE_GENERATION: "Write a Python function to calculate the fibonacci sequence.",
        TASK_SUMMARIZATION: "Summarize the key points about climate change.",
        TASK_CREATIVE_WRITING: "Write a poem about autumn leaves.",
        TASK_DATA_ANALYSIS: "Analyze this data and identify trends: Revenue 2020: $1.2M, 2021: $1.5M, 2022: $2.1M",
        TASK_INFORMATION_EXTRACTION: "Extract the names and dates from this text: John Smith was born on April 15, 1982.",
        TASK_MATH_PROBLEM_SOLVING: "What is the square root of 144 divided by 4?",
    }
    
    print("| Prompt | Detected Task Type | Key Capabilities |")
    print("|--------|-------------------|------------------|")
    
    for expected_task, prompt in example_prompts.items():
        # Detect task type
        detected_task = detect_task_type_from_prompt(prompt)
        
        # Get required capabilities
        capabilities = get_capabilities_for_task(detected_task)
        capability_str = ", ".join([f"{cap}:{strength.name}" for cap, strength in capabilities.items()])
        
        # Highlight if detection matches expectation
        if detected_task == expected_task:
            task_display = highlight(detected_task, color="green")
        else:
            task_display = f"{detected_task} (expected: {expected_task})"
        
        # Display truncated prompt if too long
        display_prompt = prompt if len(prompt) < 40 else prompt[:37] + "..."
        
        print(f"| {display_prompt} | {task_display} | {capability_str} |")
    
    print()


def demonstrate_task_aware_selection(provider_group: ModelProvider) -> None:
    """Demonstrate task-aware provider selection with different tasks.
    
    Args:
        provider_group: Provider group with task-aware selection
    """
    logger = logging.get_logger(__name__)
    print_section("Task-Aware Provider Selection")
    
    # Tasks to demonstrate
    tasks = [
        {
            "name": "Code Generation",
            "prompt": "Write a function in Python to check if a number is prime."
        },
        {
            "name": "Summarization",
            "prompt": "Summarize the key features of task-aware provider selection in 2-3 sentences."
        },
        {
            "name": "Creative Writing",
            "prompt": "Write a haiku poem about artificial intelligence."
        },
        {
            "name": "Math Problem",
            "prompt": "If x² + 5x + 6 = 0, what are the values of x?"
        },
        {
            "name": "Simple Conversation",
            "prompt": "What are your capabilities?"
        }
    ]
    
    # Process each task
    for i, task in enumerate(tasks, 1):
        print(f"\nTask #{i}: {task['name']}")
        print(f"Prompt: \"{task['prompt']}\"")
        
        # Detect task type
        task_type = detect_task_type_from_prompt(task['prompt'])
        capabilities = get_capabilities_for_task(task_type)
        
        print(f"Detected task type: {highlight(task_type, color='blue')}")
        print(f"Required capabilities: {', '.join([f'{cap}:{strength.name}' for cap, strength in capabilities.items()])}")
        
        # Create request
        request = ModelRequest(
            messages=[
                ModelMessage.system("You are a helpful assistant. Keep responses brief."),
                ModelMessage.user(task['prompt'])
            ],
            max_tokens=100
        )
        
        # Generate response
        try:
            response = provider_group.generate(request)
            print(highlight("Response:", color="green"))
            print(response.content)
        except Exception as e:
            logger.exception(f"Error processing task: {e}")
            print(highlight(f"Error: {e}", color="red"))


def main():
    """Main entry point for the task-aware providers example.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Set up the example with standardized logging and argument parsing
        args = setup_example("Atlas Task-Aware Provider Selection Example", add_example_arguments)
        logger = logging.get_logger(__name__)
        
        # Parse provider names if specified
        provider_names = args.providers.split(",") if args.providers else None
        
        # Create provider group
        provider_group = create_provider_group_for_example(provider_names)
        
        # Demonstrate task detection
        demonstrate_task_detection()
        
        # Demonstrate task-aware selection
        demonstrate_task_aware_selection(provider_group)
        
        # Print footer
        print_example_footer()
        return 0
    
    except Exception as e:
        logger = logging.get_logger(__name__)
        handle_example_error(
            logger, 
            e, 
            "Error in task-aware provider example",
            "Try running with only mock providers by setting ATLAS_PROVIDERS=mock"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())