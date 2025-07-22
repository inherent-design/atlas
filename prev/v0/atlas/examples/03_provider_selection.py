#!/usr/bin/env python3
"""
Provider Selection Example (03_provider_selection.py)

This example demonstrates the provider options, resolution, and auto-detection system:
1. Creating and resolving ProviderOptions
2. Auto-detecting providers from model names
3. Capability-based model selection
4. Environment variable integration
5. Creating providers from options

It shows the key features of Atlas's provider system to help users understand
how model and provider selection works across the framework.
"""

import os
import sys
from typing import Any, Dict, List, Optional

# Import common example utilities
from common import (
    configure_example_logging,
    create_provider_from_args,
    get_base_argument_parser,
    logging,
    print_example_footer,
    setup_example,
)

# Configure logging via the common utility
configure_example_logging()
logger = logging.get_logger(__name__)

# Import atlas modules
from atlas.providers import (
    ProviderOptions,
    create_provider_from_options,
    resolve_provider_options,
)


def add_cli_arguments(parser):
    """Add example-specific CLI arguments."""
    # Demo control options
    parser.add_argument(
        "--skip-api-call", action="store_true", help="Skip examples that make API calls"
    )

    return parser


def demo_options_creation():
    """Demonstrate creating ProviderOptions in different ways."""
    print("\n" + "-" * 50)
    print("Provider Options Creation")
    print("-" * 50)

    # Example 1: Create options with provider name only
    provider_options = ProviderOptions(provider_name="anthropic")
    print("\n1. Provider-only options:")
    print(f"   - Provider: {provider_options.provider_name}")
    print(f"   - Model: {provider_options.model_name} (not specified yet)")
    print(f"   - Capability: {provider_options.capability} (not specified yet)")

    # Example 2: Create options with model name only
    model_options = ProviderOptions(model_name="gpt-4o")
    print("\n2. Model-only options:")
    print(f"   - Provider: {model_options.provider_name} (not specified yet)")
    print(f"   - Model: {model_options.model_name}")

    # Example 3: Create options with capability only
    capability_options = ProviderOptions(capability="premium")
    print("\n3. Capability-only options:")
    print(f"   - Provider: {capability_options.provider_name} (not specified yet)")
    print(f"   - Model: {capability_options.model_name} (not specified yet)")
    print(f"   - Capability: {capability_options.capability}")

    # Example 4: Create options from environment
    print("\n4. Environment-based options:")
    env_options = ProviderOptions.from_env()
    print(f"   - Provider: {env_options.provider_name}")
    print(f"   - Model: {env_options.model_name}")
    print(f"   - Capability: {env_options.capability}")


def demo_provider_resolution():
    """Demonstrate resolving ProviderOptions with auto-detection."""
    print("\n" + "-" * 50)
    print("Provider Options Resolution")
    print("-" * 50)

    print("\nAuto-detection from model name examples:")

    # OpenAI model examples
    openai_models = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    for model in openai_models:
        options = ProviderOptions(model_name=model)
        resolved = resolve_provider_options(options)
        print(f"Model '{model}' -> Provider: {resolved.provider_name}")

    # Anthropic model examples
    anthropic_models = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]
    for model in anthropic_models:
        options = ProviderOptions(model_name=model)
        resolved = resolve_provider_options(options)
        print(f"Model '{model}' -> Provider: {resolved.provider_name}")

    print("\nCapability-based model selection examples:")

    # Capability examples for Anthropic
    capabilities = ["inexpensive", "efficient", "premium", "vision"]
    provider = "anthropic"
    for capability in capabilities:
        options = ProviderOptions(provider_name=provider, capability=capability)
        resolved = resolve_provider_options(options)
        print(
            f"Provider '{provider}' with capability '{capability}' -> Model: {resolved.model_name}"
        )

    # Capability examples for OpenAI
    provider = "openai"
    for capability in capabilities:
        options = ProviderOptions(provider_name=provider, capability=capability)
        resolved = resolve_provider_options(options)
        print(
            f"Provider '{provider}' with capability '{capability}' -> Model: {resolved.model_name}"
        )


def demo_resolution_precedence():
    """Demonstrate resolution precedence rules."""
    print("\n" + "-" * 50)
    print("Resolution Precedence Rules")
    print("-" * 50)

    # Example 1: Model name takes precedence over capability
    options1 = ProviderOptions(model_name="claude-3-opus-20240229", capability="inexpensive")
    resolved1 = resolve_provider_options(options1)
    print("\n1. Model name takes precedence over capability:")
    print(f"   - Input: model='claude-3-opus-20240229', capability='inexpensive'")
    print(f"   - Result: provider='{resolved1.provider_name}', model='{resolved1.model_name}'")
    print(f"   - Note: Uses opus model despite 'inexpensive' capability")

    # Example 2: Provider name with capability
    options2 = ProviderOptions(provider_name="anthropic", capability="efficient")
    resolved2 = resolve_provider_options(options2)
    print("\n2. Provider with capability selects appropriate model:")
    print(f"   - Input: provider='anthropic', capability='efficient'")
    print(f"   - Result: model='{resolved2.model_name}'")

    # Example 3: Fallback to environment
    options3 = ProviderOptions()
    resolved3 = resolve_provider_options(options3)
    print("\n3. Empty options fall back to environment defaults:")
    print(f"   - Result: provider='{resolved3.provider_name}', model='{resolved3.model_name}'")

    # Example 4: Mixed options
    options4 = ProviderOptions(provider_name="openai", capability="premium")
    resolved4 = resolve_provider_options(options4)
    print("\n4. Provider with capability:")
    print(f"   - Input: provider='openai', capability='premium'")
    print(f"   - Result: model='{resolved4.model_name}'")


def demo_provider_creation(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
    capability: Optional[str] = None,
    skip_api_call: bool = False,
):
    """Demonstrate creating a provider from options.

    Args:
        provider_name: Optional provider name
        model_name: Optional model name
        capability: Optional capability
        skip_api_call: Whether to skip making actual API calls
    """
    if skip_api_call:
        print("\n" + "-" * 50)
        print("Provider Creation (API calls skipped)")
        print("-" * 50)
        print("\nSkipping provider creation with API calls as requested.")
        print("To see this in action, run without --skip-api-call")
        return

    print("\n" + "-" * 50)
    print("Provider Creation")
    print("-" * 50)

    # Create options based on parameters
    options = ProviderOptions(
        provider_name=provider_name,
        model_name=model_name,
        capability=capability,
    )

    print(f"\nCreating provider with options:")
    print(f"- Provider: {options.provider_name or 'auto-detect'}")
    print(f"- Model: {options.model_name or 'capability-based'}")
    print(f"- Capability: {options.capability or 'default'}")

    try:
        # Resolve options
        resolved = resolve_provider_options(options)
        print(f"\nResolved to:")
        print(f"- Provider: {resolved.provider_name}")
        print(f"- Model: {resolved.model_name}")

        # Create provider
        provider = create_provider_from_options(resolved)
        print(f"\nSuccessfully created {provider.name} provider with {provider.model_name} model")

        # If mock provider or requested to skip API call, don't test generation
        if provider.name == "mock":
            print("\nMock provider created - skipping actual API calls")
        else:
            print("\nTesting with a simple generation...")
            # Create a simple request using the standard ModelRequest and ModelMessage classes
            from atlas.providers.base import ModelMessage, ModelRequest

            request = ModelRequest(
                messages=[ModelMessage.user("Hello!")],
                system_prompt="You are a helpful assistant. Give a short response!",
            )

            # Generate a response
            response = provider.generate(request)
            print(
                f"\nResponse: {response.content[:100]}..."
                + ("" if len(response.content) <= 100 else "")
            )

            # Show token usage if available
            if response.usage:
                print(f"\nToken Usage:")
                print(f"- Input: {response.usage.input_tokens} tokens")
                print(f"- Output: {response.usage.output_tokens} tokens")
                print(f"- Total: {response.usage.total_tokens} tokens")
    except Exception as e:
        print(f"\nError creating or using provider: {e}")
        print("This may happen if:")
        print("- You're missing API keys for the selected provider")
        print("- The provider service is unavailable")
        print("- You're trying to use a model not available to your account")
        print("\nTry using '--provider mock' for testing without API keys")


def main():
    """Run the provider selection example."""
    # Set up the example with our common utility
    args = setup_example("Atlas Provider Selection Example", setup_func=add_cli_arguments)

    # Print overview
    print("This example demonstrates Atlas's provider selection system, including:")
    print("- Creating provider options in different ways")
    print("- Auto-detecting providers from model names")
    print("- Capability-based model selection")
    print("- Resolution precedence rules")
    print("- Creating providers from options")

    # Run the demonstrations
    demo_options_creation()
    demo_provider_resolution()
    demo_resolution_precedence()
    demo_provider_creation(
        provider_name=args.provider,
        model_name=args.model,
        capability=args.capability,
        skip_api_call=args.skip_api_call,
    )

    # Use our common footer
    print_example_footer()

    # Print information about provider selection
    logger.info("Additional Information")
    print("\nSupported Providers:")
    print("- anthropic: Claude models (requires ANTHROPIC_API_KEY)")
    print("- openai: OpenAI/GPT models (requires OPENAI_API_KEY)")
    print("- ollama: Local models via Ollama (requires running Ollama server)")
    print("- mock: Test provider (no API key required)")

    print("\nCapability-to-Model Mapping:")
    print("Each provider maps capabilities to specific models:")
    print("- inexpensive: Less expensive, faster models (e.g., Claude Haiku, GPT-3.5)")
    print("- efficient: Balance of cost and performance (e.g., Claude Sonnet)")
    print("- premium: Highest capability models (e.g., Claude Opus, GPT-4)")
    print("- vision: Models with image understanding (e.g., Claude Opus, GPT-4o)")

    print("\nRunning with Different Options:")
    print("Try running this example with different combinations:")
    print("- python examples/03_provider_selection.py --provider anthropic --capability premium")
    print("- python examples/03_provider_selection.py --model gpt-4o")
    print("- python examples/03_provider_selection.py --provider mock --skip-api-call")


if __name__ == "__main__":
    main()
