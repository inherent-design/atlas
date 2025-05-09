#!/usr/bin/env python3
"""
Example script to demonstrate the retry mechanism in Atlas.

This example shows how to use the retry mechanism with the OpenAI provider,
including custom retry configuration and error handling.
"""

import os
import sys
import logging
import time
from dotenv import load_dotenv

# Set up path to ensure atlas is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
from atlas.core import logging as atlas_logging
atlas_logging.configure_logging(level="INFO", enable_rich=True)
logger = atlas_logging.get_logger(__name__)

# Import the retry-related classes
from atlas.core.retry import RetryConfig, CircuitBreaker
from atlas.providers.openai import OpenAIProvider
from atlas.providers.base import ModelMessage, ModelRequest


def simulate_error_response(count=[0]):
    """Simulates a response that sometimes fails to test retry behavior.
    
    For demonstration purposes, this function will cause an error
    on the first and second calls, then succeed on the third call.
    
    Args:
        count: A list with a single integer to maintain state between calls
        
    Returns:
        The response text
        
    Raises:
        ConnectionError: On simulated network failure
        ValueError: On simulated rate limit error
    """
    count[0] += 1
    
    # Simulate different kinds of failures
    if count[0] == 1:
        logger.warning(f"Attempt {count[0]}: Simulating a network error...")
        raise ConnectionError("Simulated network error")
    elif count[0] == 2:
        logger.warning(f"Attempt {count[0]}: Simulating a rate limit error...")
        raise ValueError("Simulated rate limit error")
    else:
        logger.info(f"Attempt {count[0]}: Success!")
        return "This is a successful response after retries"


def run_basic_retry_example():
    """Run a basic example showing retry behavior with the OpenAI provider."""
    logger.info("Running basic retry example with OpenAI provider")
    
    # Create a custom retry configuration
    retry_config = RetryConfig(
        max_retries=3,                # Maximum number of retry attempts
        initial_delay=0.5,            # Start with a 0.5 second delay
        backoff_factor=2.0,           # Double the delay each time
        max_delay=5.0,                # Cap the delay at 5 seconds
        jitter_factor=0.1,            # Add 10% random jitter to prevent thundering herd
    )
    
    # Create a circuit breaker to prevent cascading failures
    circuit_breaker = CircuitBreaker(
        failure_threshold=5,          # Open the circuit after 5 consecutive failures
        recovery_timeout=30.0,        # Wait 30 seconds before trying again
        test_requests=1,              # Allow 1 test request when half-open
    )
    
    # Initialize the OpenAI provider with our custom retry configuration
    provider = OpenAIProvider(
        model_name="gpt-3.5-turbo",
        api_key=os.environ.get("OPENAI_API_KEY"),
        retry_config=retry_config,
        circuit_breaker=circuit_breaker,
    )
    
    # Create a simple request
    request = ModelRequest(
        messages=[ModelMessage.user("What is the meaning of life?")],
        max_tokens=50,
    )
    
    # Make the request with retry handling
    logger.info("Sending request to OpenAI API with retry handling")
    try:
        # Call the provider's generate method which uses the retry mechanism
        response = provider.generate(request)
        
        # Display the results
        logger.info(f"Response received: {response.content[:50]}...")
        logger.info(f"Token usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output")
        logger.info(f"Estimated cost: {response.cost}")
        
    except Exception as e:
        logger.error(f"Failed after retries: {e}")


def run_simulated_error_example():
    """Run an example with simulated errors to demonstrate retry behavior."""
    logger.info("Running simulated error example to demonstrate retry behavior")
    
    # Create a retry configuration with a short delay for the example
    retry_config = RetryConfig(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        jitter_factor=0.0,  # No jitter for predictable demonstration
    )
    
    logger.info(f"Retry configuration: max_retries={retry_config.max_retries}, initial_delay={retry_config.initial_delay}s")
    
    # Implement a simple retry loop (simplified version of what's in the provider)
    retry_count = 0
    last_error = None
    
    while True:
        try:
            # Attempt to call our simulated error function
            result = simulate_error_response()
            logger.info(f"Success after {retry_count} retries: {result}")
            break
            
        except Exception as error:
            last_error = error
            
            # Check if we should retry
            if retry_count < retry_config.max_retries:
                retry_count += 1
                delay = retry_config.initial_delay * (retry_config.backoff_factor ** (retry_count - 1))
                
                logger.warning(
                    f"Error occurred: {type(error).__name__} - {error}. "
                    f"Retrying in {delay:.2f}s ({retry_count}/{retry_config.max_retries})"
                )
                time.sleep(delay)
            else:
                # Max retries reached, raise the last error
                logger.error(f"Failed after {retry_count} retries: {last_error}")
                raise last_error


def main():
    """Main entry point for the example."""
    logger.info("Atlas Retry Mechanism Example")
    logger.info("----------------------------")
    
    # Check if we should skip API calls
    skip_api = os.environ.get("SKIP_API_KEY_CHECK", "").lower() in ("true", "1")
    
    try:
        # First run the simulated example that doesn't need API keys
        run_simulated_error_example()
        
        # Then run the real API example if not skipped
        if not skip_api:
            # Check for OpenAI API key
            if not os.environ.get("OPENAI_API_KEY"):
                logger.error("OPENAI_API_KEY environment variable is not set.")
                logger.info("Skipping the OpenAI API example. Set OPENAI_API_KEY to run it.")
            else:
                logger.info("\nNow running a real API example...")
                run_basic_retry_example()
        else:
            logger.info("\nSkipping API example due to SKIP_API_KEY_CHECK=true")
            
    except Exception as e:
        logger.error(f"Error running example: {e}")
        return 1
        
    logger.info("Example completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())