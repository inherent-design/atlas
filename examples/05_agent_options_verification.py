#!/usr/bin/env python3
"""
Atlas agent verification example with ProviderOptions implementation.

This example demonstrates the new ProviderOptions integration with the AtlasAgent.
It verifies that the agent can be properly initialized with various configurations.
"""

import os
import sys

# Import common example utilities
from common import configure_example_logging, logging, print_example_footer, setup_example

# Configure logging via the common utility
configure_example_logging()
logger = logging.get_logger(__name__)

# Import Atlas components
from atlas.agents.base import AtlasAgent
from atlas.providers.base import ModelProvider
from atlas.providers.factory import create_provider
from atlas.providers.options import ProviderOptions


def test_with_direct_provider():
    """Test initializing agent with a directly provided model provider."""
    print("\n=== Testing with direct provider ===")

    # Create a provider first (using mock for testing without API keys)
    provider = create_provider(provider_name="mock", model_name="mock-standard")

    # Initialize agent with the provider
    agent = AtlasAgent(provider=provider)

    # Verify the agent was properly initialized
    print(f"Agent ID: {agent.agent_id}")
    print(f"Provider: {agent.provider.name}")
    print(f"Model: {agent.provider.model_name}")

    return agent


def test_with_provider_options():
    """Test initializing agent with ProviderOptions."""
    print("\n=== Testing with ProviderOptions ===")

    # Create provider options
    options = ProviderOptions(
        provider_name="mock",
        model_name="mock-premium",
        capability="premium",
        max_tokens=1000,
        extra_params={"temperature": 0.7},
    )

    # Initialize agent with provider options
    agent = AtlasAgent(provider_options=options)

    # Verify the agent was properly initialized
    print(f"Agent ID: {agent.agent_id}")
    print(f"Provider: {agent.provider.name}")
    print(f"Model: {agent.provider.model_name}")
    print(f"Stored Provider Options: {agent.provider_options.to_dict()}")

    return agent


def test_with_individual_parameters():
    """Test initializing agent with individual parameters."""
    print("\n=== Testing with individual parameters ===")

    # Initialize agent with individual parameters
    agent = AtlasAgent(
        provider_name="mock",
        model_name="mock-efficient",
        capability="efficient",
        max_tokens=500,
        temperature=0.5,  # This should be passed through to the provider
    )

    # Verify the agent was properly initialized
    print(f"Agent ID: {agent.agent_id}")
    print(f"Provider: {agent.provider.name}")
    print(f"Model: {agent.provider.model_name}")
    print(f"Stored Provider Options: {agent.provider_options.to_dict()}")

    return agent


def test_with_resolution_from_capability():
    """Test provider resolution using capability."""
    print("\n=== Testing with capability-based resolution ===")

    # Add debug prints to understand model resolution
    from atlas.providers.factory import get_model_by_capability

    print(
        f"Direct capability check: premium mock model = {get_model_by_capability('mock', 'premium')}"
    )

    # Create options for testing
    from atlas.providers.options import ProviderOptions
    from atlas.providers.resolver import resolve_provider_options

    options = ProviderOptions(provider_name="mock", capability="premium")
    resolved = resolve_provider_options(options)

    print(f"Debug - After resolution: {resolved.to_dict()}")

    # Initialize agent with resolved options directly
    agent = AtlasAgent(provider_options=resolved)

    # Verify the agent was properly initialized
    print(f"Agent ID: {agent.agent_id}")
    print(f"Provider: {agent.provider.name}")
    print(f"Model: {agent.provider.model_name}")
    print(f"Stored Provider Options: {agent.provider_options.to_dict()}")

    return agent


def test_with_query():
    """Test querying the agent."""
    print("\n=== Testing agent query ===")

    # Initialize agent
    agent = AtlasAgent(provider_name="mock", model_name="mock-standard")

    # Test querying the agent
    response = agent.process_message("What is Atlas?")

    print(f"Query response: {response[:100]}...")

    return response


def add_cli_arguments(parser):
    """Add example-specific CLI arguments."""
    parser.add_argument("--skip-query", action="store_true", help="Skip the query test")
    return parser


def main():
    """Run the agent verification example."""
    # Set up the example with our common utility
    args = setup_example("Atlas Agent ProviderOptions Verification", setup_func=add_cli_arguments)

    logger.info("Testing the agent initialization with different combinations")

    # Run all tests
    test_with_direct_provider()
    test_with_provider_options()
    test_with_individual_parameters()
    test_with_resolution_from_capability()

    # Conditionally run query test
    if not args.skip_query:
        test_with_query()

    logger.info("✅ All tests completed successfully!")
    print_example_footer()


if __name__ == "__main__":
    main()
