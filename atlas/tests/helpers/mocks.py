"""
Mock utilities for Atlas tests.

This module provides functions and classes for creating mock objects and
mocking external API calls in tests.
"""

import os
import json
import random
from typing import Dict, Any, List, Optional, Type, Callable, TypeVar, Union, Tuple
from unittest.mock import patch, MagicMock


# Mock Message and Response Creation
def create_mock_message(role="user", content="Test message"):
    """Create a mock message for testing.
    
    Args:
        role: The message role.
        content: The message content.
        
    Returns:
        A ModelMessage object.
    """
    from atlas.models import ModelMessage, ModelRole
    
    return ModelMessage(
        role=ModelRole(role),
        content=content
    )


def create_mock_request(messages=None, model=None, max_tokens=100):
    """Create a mock request for testing.
    
    Args:
        messages: List of messages.
        model: Optional model name.
        max_tokens: Maximum tokens for the response.
        
    Returns:
        A ModelRequest object.
    """
    from atlas.models import ModelRequest
    
    if messages is None:
        messages = [create_mock_message()]
    
    return ModelRequest(
        messages=messages,
        model=model,
        max_tokens=max_tokens
    )


def create_mock_response(content="Mock response", provider="mock", model="mock-model",
                         input_tokens=10, output_tokens=10):
    """Create a mock response for testing.
    
    Args:
        content: The response content.
        provider: The provider name.
        model: The model name.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        
    Returns:
        A ModelResponse object.
    """
    from atlas.models import ModelResponse, TokenUsage, CostEstimate
    
    total_tokens = input_tokens + output_tokens
    
    # Estimate cost based on provider and model
    input_cost = 0.0
    output_cost = 0.0
    
    if provider == "openai":
        if "gpt-4" in model:
            if "32k" in model:
                input_cost = input_tokens * 0.00006
                output_cost = output_tokens * 0.00012
            else:
                input_cost = input_tokens * 0.00003
                output_cost = output_tokens * 0.00006
        else:  # gpt-3.5-turbo
            input_cost = input_tokens * 0.000001
            output_cost = output_tokens * 0.000002
    elif provider == "anthropic":
        if "opus" in model:
            input_cost = input_tokens * 0.00003
            output_cost = output_tokens * 0.00015
        elif "sonnet" in model:
            input_cost = input_tokens * 0.000003
            output_cost = output_tokens * 0.000015
        else:  # haiku
            input_cost = input_tokens * 0.000001
            output_cost = output_tokens * 0.000005
    
    return ModelResponse(
        content=content,
        provider=provider,
        model=model,
        usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total_tokens),
        cost=CostEstimate(input_cost=input_cost, output_cost=output_cost, total_cost=input_cost + output_cost),
        finish_reason="stop",
        raw_response={}
    )


def create_mock_streaming_response(content="Mock response", provider="mock", model="mock-model",
                                 input_tokens=10, output_tokens=10, chunks=5):
    """Create a series of mock streaming chunks for testing.
    
    Args:
        content: The full response content.
        provider: The provider name.
        model: The model name.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        chunks: Number of streaming chunks to create.
        
    Returns:
        A tuple of (chunks, final_response) where chunks is a list of content
        deltas and final_response is the final ModelResponse.
    """
    from atlas.models import ModelResponse, TokenUsage, CostEstimate
    
    # Split content into chunks
    chunk_size = max(1, len(content) // chunks)
    content_chunks = []
    
    for i in range(chunks - 1):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        content_chunks.append(content[start:end])
    
    # Add the last chunk (may be longer)
    content_chunks.append(content[(chunks - 1) * chunk_size:])
    
    # Create the final response
    final_response = create_mock_response(
        content=content,
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens
    )
    
    return content_chunks, final_response


# Mock Provider Context Managers
class MockProvider:
    """Context manager for mocking provider API calls."""
    
    def __init__(self, provider_class, **kwargs):
        """Initialize with provider class and mock responses.
        
        Args:
            provider_class: The provider class to mock.
            **kwargs: Additional configuration.
        """
        self.provider_class = provider_class
        self.mock_responses = kwargs.get('mock_responses', {})
        self.original_methods = {}
    
    def __enter__(self):
        """Set up mocking."""
        # Store original methods
        for method_name, mock_func in self.mock_responses.items():
            if hasattr(self.provider_class, method_name):
                self.original_methods[method_name] = getattr(self.provider_class, method_name)
                setattr(self.provider_class, method_name, mock_func)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Tear down mocking."""
        # Restore original methods
        for method_name, original_func in self.original_methods.items():
            setattr(self.provider_class, method_name, original_func)


def mock_openai_response(content="This is a mock OpenAI response", model="gpt-4o"):
    """Create a mock OpenAI API response.
    
    Args:
        content: The response content.
        model: The model name.
        
    Returns:
        A dictionary resembling an OpenAI API response.
    """
    return {
        "id": f"chatcmpl-{random.randint(100000, 999999)}",
        "object": "chat.completion",
        "created": int(random.uniform(1600000000, 1700000000)),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 30,
            "total_tokens": 80
        }
    }


def mock_anthropic_response(content="This is a mock Anthropic response", model="claude-3-sonnet-20240229"):
    """Create a mock Anthropic API response.
    
    Args:
        content: The response content.
        model: The model name.
        
    Returns:
        A dictionary resembling an Anthropic API response.
    """
    return {
        "id": f"msg_{random.randint(100000, 999999)}",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": content
            }
        ],
        "model": model,
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 50,
            "output_tokens": 30
        }
    }


def mock_ollama_response(content="This is a mock Ollama response", model="llama2"):
    """Create a mock Ollama API response.
    
    Args:
        content: The response content.
        model: The model name.
        
    Returns:
        A dictionary resembling an Ollama API response.
    """
    return {
        "model": model,
        "created_at": "2023-11-06T20:03:25.048977Z",
        "response": content,
        "done": True,
        "context": [random.randint(1, 10000) for _ in range(10)],
        "total_duration": random.randint(500000000, 2000000000),
        "load_duration": random.randint(10000000, 50000000),
        "prompt_eval_count": 50,
        "prompt_eval_duration": random.randint(100000000, 500000000),
        "eval_count": 30,
        "eval_duration": random.randint(400000000, 1500000000)
    }


def mock_streaming_ollama_response(content="This is a mock Ollama response", model="llama2", chunks=5):
    """Create a series of mock Ollama streaming responses.
    
    Args:
        content: The full response content.
        model: The model name.
        chunks: Number of streaming responses to create.
        
    Returns:
        A list of dictionaries resembling Ollama API streaming responses.
    """
    # Split content into chunks
    chunk_size = max(1, len(content) // chunks)
    responses = []
    
    for i in range(chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, len(content))
        chunk_content = content[start:end]
        
        # For the final chunk, ensure we include all remaining content
        if i == chunks - 1 and end < len(content):
            chunk_content = content[start:]
            
        responses.append({
            "model": model,
            "created_at": "2023-11-06T20:03:25.048977Z",
            "response": chunk_content,
            "done": i == chunks - 1,
            "context": [random.randint(1, 10000) for _ in range(10)] if i == 0 else None,
            "total_duration": random.randint(500000000, 2000000000) if i == chunks - 1 else None,
            "load_duration": random.randint(10000000, 50000000) if i == 0 else None,
            "prompt_eval_count": 50 if i == chunks - 1 else 10,  # Ensure all chunks have token counts
            "prompt_eval_duration": random.randint(100000000, 500000000) if i == 0 else None,
            "eval_count": 30 if i == chunks - 1 else 5,  # Ensure all chunks have token counts
            "eval_duration": random.randint(400000000, 1500000000) // chunks if i == chunks - 1 else None
        })
    
    return responses


# Mock API endpoints
def mock_openai_api():
    """Mock the OpenAI API endpoint.
    
    Returns:
        A patch context manager for requests or httpx.
    """
    def _mock_response(request, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        
        # Parse the request content to determine the response
        data = json.loads(request.kwargs.get('json', '{}'))
        model = data.get('model', 'gpt-4o')
        messages = data.get('messages', [])
        last_message = messages[-1] if messages else {'content': ''}
        
        # Generate a response based on the message
        if "error" in last_message.get('content', '').lower():
            mock_resp.status_code = 400
            mock_resp.json.return_value = {
                "error": {
                    "message": "The model rejected the request",
                    "type": "invalid_request_error",
                    "code": "content_filter"
                }
            }
        else:
            mock_resp.json.return_value = mock_openai_response(
                content=f"Response to: {last_message.get('content', '')}",
                model=model
            )
        
        return mock_resp
    
    # Try to patch the appropriate request library
    try:
        import httpx
        return patch('httpx.Client.post', side_effect=_mock_response)
    except ImportError:
        return patch('requests.post', side_effect=_mock_response)


def mock_anthropic_api():
    """Mock the Anthropic API endpoint.
    
    Returns:
        A patch context manager for the Anthropic client.
    """
    def _mock_response(self, *args, **kwargs):
        # Parse the request to determine the response
        messages = kwargs.get('messages', [])
        model = kwargs.get('model', 'claude-3-opus-20240229')
        last_message = messages[-1] if messages else {'content': ''}
        
        # Generate a response based on the message
        if "error" in last_message.get('content', '').lower():
            raise ValueError("The model rejected the request")
        else:
            return mock_anthropic_response(
                content=f"Response to: {last_message.get('content', '')}",
                model=model
            )
    
    # Patch the appropriate Anthropic client method
    try:
        from anthropic import Anthropic
        return patch.object(Anthropic, 'messages.create', side_effect=_mock_response)
    except ImportError:
        def dummy_context_manager():
            class DummyContextManager:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return DummyContextManager()
        return dummy_context_manager()


def mock_ollama_api():
    """Mock the Ollama API endpoint.
    
    Returns:
        A patch context manager for requests.
    """
    def _mock_response(request, *args, **kwargs):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        
        # Parse the request content to determine the response
        data = json.loads(request.kwargs.get('json', '{}'))
        model = data.get('model', 'llama2')
        prompt = data.get('prompt', '')
        
        # Generate a response based on the prompt
        if "error" in prompt.lower():
            mock_resp.status_code = 400
            mock_resp.json.return_value = {
                "error": "The model rejected the request"
            }
        else:
            mock_resp.json.return_value = mock_ollama_response(
                content=f"Response to: {prompt}",
                model=model
            )
        
        return mock_resp
    
    # Try to patch the appropriate request library
    try:
        import httpx
        return patch('httpx.Client.post', side_effect=_mock_response)
    except ImportError:
        return patch('requests.post', side_effect=_mock_response)