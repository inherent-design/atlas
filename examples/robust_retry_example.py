"""
Example demonstrating the robust retry mechanism with exponential backoff.

This example shows how to configure and use the retry and circuit breaker
patterns to make LLM API calls more resilient to transient failures.
"""

import logging
import time
from typing import Optional, List, Dict, Any

from atlas.providers.base import ModelRequest, ModelMessage
from atlas.providers.openai import OpenAIProvider
from atlas.core.retry import RetryConfig, CircuitBreaker

# Set up logging to see retry information
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def create_robust_provider():
    """
    Create an OpenAI provider with custom retry configuration.
    
    Returns:
        An OpenAIProvider instance with robust retry mechanisms
    """
    # Create a custom retry configuration
    retry_config = RetryConfig(
        max_retries=3,                # Maximum number of retry attempts
        initial_delay=1.0,            # Initial delay before first retry
        backoff_factor=2.0,           # Multiplier for subsequent delays
        max_delay=30.0,               # Maximum delay between retries
        jitter_factor=0.1,            # Random jitter to prevent thundering herd
        retryable_status_codes=[429, 500, 502, 503, 504],  # Retryable HTTP status codes
    )
    
    # Create a circuit breaker to prevent repeated failures
    circuit_breaker = CircuitBreaker(
        failure_threshold=5,          # Number of failures that trips the breaker
        recovery_timeout=60.0,        # Seconds before attempting recovery
        test_requests=1,              # Number of test requests allowed when half-open
    )
    
    # Create and return the provider with retry configuration
    return OpenAIProvider(
        model_name="gpt-4.1",         # Use latest model
        retry_config=retry_config,
        circuit_breaker=circuit_breaker,
    )


def demonstrate_retry_mechanism():
    """
    Demonstrate how the retry mechanism works.
    
    This function simulates different scenarios to show retry behavior.
    """
    print("Creating provider with robust retry mechanism...")
    provider = create_robust_provider()
    
    print(f"Provider created with retry configuration:")
    print(f"- Max retries: {provider.retry_config.max_retries}")
    print(f"- Initial delay: {provider.retry_config.initial_delay}s")
    print(f"- Backoff factor: {provider.retry_config.backoff_factor}")
    print(f"- Jitter: {provider.retry_config.jitter_factor * 100}%")
    print(f"- Circuit breaker threshold: {provider.circuit_breaker.failure_threshold} failures")
    
    # Create a sample request
    request = ModelRequest(
        messages=[
            ModelMessage.system("You are a helpful assistant."),
            ModelMessage.user("What is the capital of France?"),
        ],
        max_tokens=100,
    )
    
    # Use the provider to generate a response
    print("\nSending request with automatic retry handling...")
    try:
        response = provider.generate(request)
        
        print(f"\nResponse received:")
        print(f"- Content: {response.content[:100]}...")
        print(f"- Model: {response.model}")
        print(f"- Token usage: {response.usage.input_tokens} input, {response.usage.output_tokens} output")
        print(f"- Cost: {response.cost}")
        
    except Exception as e:
        print(f"\nRequest failed even with retries: {e}")
    
    print("\nRetry mechanism benefits:")
    print("1. Automatically handles transient failures (rate limits, server errors)")
    print("2. Uses exponential backoff to avoid overwhelming the API")
    print("3. Adds jitter to prevent all clients retrying simultaneously")
    print("4. Circuit breaker prevents cascading failures")
    print("5. Gracefully handles errors with appropriate messages")


if __name__ == "__main__":
    demonstrate_retry_mechanism()