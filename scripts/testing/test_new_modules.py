#!/usr/bin/env python
"""
Test script for the new telemetry and models modules.

This script tests the functionality of the enhanced telemetry module
and the new unified models architecture.
"""

import os
import sys
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_new_modules")

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Import telemetry module
from atlas.core.telemetry import (
    initialize_telemetry,
    shutdown_telemetry,
    enable_telemetry,
    disable_telemetry,
    is_telemetry_enabled,
    traced,
    TracedClass,
)

# Import models module
try:
    from atlas.models import (
        discover_providers,
        create_provider,
        ModelRequest,
        ModelMessage,
        ModelRole,
    )

    MODELS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import models module: {e}")
    MODELS_AVAILABLE = False


@traced(name="test_telemetry")
def test_telemetry():
    """Test the telemetry module functionality."""
    logger.info("Testing telemetry module...")

    # Test telemetry initialization
    logger.info("Testing telemetry initialization...")
    result = initialize_telemetry(
        service_name="test_service",
        service_version="0.1.0",
        enable_console_exporter=True,
    )
    logger.info(f"Telemetry initialization result: {result}")

    # Test telemetry enable/disable
    logger.info(f"Current telemetry enabled status: {is_telemetry_enabled()}")

    logger.info("Disabling telemetry...")
    disable_telemetry()
    logger.info(f"Current telemetry enabled status: {is_telemetry_enabled()}")

    logger.info("Re-enabling telemetry...")
    enable_telemetry()
    logger.info(f"Current telemetry enabled status: {is_telemetry_enabled()}")

    # Test TracedClass functionality
    class TestService(TracedClass):
        def do_something(self, param: str) -> str:
            logger.debug(f"Doing something with {param}")
            return f"done with {param}"

    # Create a test service and call a method (should be traced)
    test_service = TestService()
    result = test_service.do_something("test")
    logger.info(f"TestService result: {result}")

    # Test disabling tracing for a specific class
    class TestServiceNoTrace(TracedClass, disable_tracing=True):
        def do_something(self, param: str) -> str:
            logger.debug(f"Doing something with {param} (not traced)")
            return f"done with {param} (not traced)"

    # Create a test service with no tracing and call a method
    test_service_no_trace = TestServiceNoTrace()
    result = test_service_no_trace.do_something("test")
    logger.info(f"TestServiceNoTrace result: {result}")

    # Test environment variable control by simulating environment
    logger.info("Testing environment variable control...")
    os.environ["ATLAS_ENABLE_TELEMETRY"] = "0"

    # Re-initialize telemetry (should respect environment variable)
    shutdown_telemetry()
    initialize_telemetry(service_name="test_service_env")
    logger.info(
        f"Telemetry enabled after setting ATLAS_ENABLE_TELEMETRY=0: {is_telemetry_enabled()}"
    )

    # Reset environment variable
    os.environ["ATLAS_ENABLE_TELEMETRY"] = "1"

    # Re-initialize telemetry
    shutdown_telemetry()
    initialize_telemetry(service_name="test_service_env")
    logger.info(
        f"Telemetry enabled after setting ATLAS_ENABLE_TELEMETRY=1: {is_telemetry_enabled()}"
    )

    # Test telemetry shutdown
    logger.info("Testing telemetry shutdown...")
    shutdown_telemetry()

    logger.info("Telemetry tests completed.")
    return True


@traced(name="test_models")
def test_models():
    """Test the models module functionality."""
    logger.info("Testing models module...")

    if not MODELS_AVAILABLE:
        logger.error("Models module is not available.")
        return False

    # Test provider discovery
    logger.info("Testing provider discovery...")
    available_providers = discover_providers()
    logger.info(f"Available providers: {available_providers}")

    # Test creating a model request
    logger.info("Testing model request creation...")
    request = ModelRequest(
        messages=[
            ModelMessage.system("You are a helpful assistant."),
            ModelMessage.user("Hello, how are you?"),
        ],
        max_tokens=100,
        temperature=0.7,
    )
    logger.info(f"Created model request: {request}")

    # Test provider-specific request conversion
    logger.info("Testing provider-specific request conversion...")
    for provider_name in ["anthropic", "openai", "ollama"]:
        provider_request = request.to_provider_request(provider_name)
        logger.info(f"{provider_name.capitalize()} request: {provider_request}")

    # Test provider creation (don't actually make API calls)
    # Create providers only if you have API keys
    has_provider = False

    if os.environ.get("ANTHROPIC_API_KEY"):
        logger.info("Testing Anthropic provider creation...")
        try:
            provider = create_provider("anthropic")
            logger.info(f"Created Anthropic provider: {provider.name}")
            has_provider = True
        except Exception as e:
            logger.error(f"Failed to create Anthropic provider: {e}")

    if os.environ.get("OPENAI_API_KEY"):
        logger.info("Testing OpenAI provider creation...")
        try:
            provider = create_provider("openai")
            logger.info(f"Created OpenAI provider: {provider.name}")
            has_provider = True
        except Exception as e:
            logger.error(f"Failed to create OpenAI provider: {e}")

    try:
        import requests

        response = requests.get("http://localhost:11434/api/version", timeout=1)
        if response.status_code == 200:
            logger.info("Testing Ollama provider creation...")
            try:
                provider = create_provider("ollama")
                logger.info(f"Created Ollama provider: {provider.name}")
                has_provider = True
            except Exception as e:
                logger.error(f"Failed to create Ollama provider: {e}")
    except Exception:
        logger.info("Ollama server not available")

    logger.info("Models tests completed.")
    return True


def run_tests():
    """Run all tests."""
    logger.info("Starting tests...")

    test_results = {}

    # Test telemetry
    try:
        telemetry_result = test_telemetry()
        test_results["telemetry"] = telemetry_result
    except Exception as e:
        logger.error(f"Error running telemetry tests: {e}")
        test_results["telemetry"] = False

    # Test models
    try:
        models_result = test_models()
        test_results["models"] = models_result
    except Exception as e:
        logger.error(f"Error running models tests: {e}")
        test_results["models"] = False

    # Print test summary
    logger.info("===== Test Summary =====")
    for test_name, result in test_results.items():
        logger.info(f"{test_name.capitalize()}: {'PASS' if result else 'FAIL'}")

    # Return overall result
    return all(test_results.values())


if __name__ == "__main__":
    success = run_tests()
    logger.info(
        f"All tests completed with overall result: {'PASS' if success else 'FAIL'}"
    )
    sys.exit(0 if success else 1)
