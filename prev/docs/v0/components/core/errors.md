---

title: Error System

---


# Error System

This document describes the error handling system in Atlas, which provides a structured approach to managing, categorizing, and responding to errors throughout the framework.

## Overview

Atlas includes a robust error system with the following key features:

1. **Structured Error Hierarchy**: Organized inheritance hierarchy of error types
2. **Error Categorization**: Classification of errors by domain and severity
3. **Rich Error Information**: Detailed error data including causes and contextual details
4. **Consistent Logging**: Automatic mapping of error severity to log levels
5. **Error Recovery Tools**: Utilities for safe execution and exception handling
6. **Serialization Support**: Conversion of errors to dictionaries for API responses

The error system is designed to be:

- **Informative**: Providing clear context about what went wrong
- **Actionable**: Includes information about possible recovery strategies
- **Consistent**: Following predictable patterns across the codebase
- **Extensible**: Easy to add new error types for specific domains

## Error Hierarchy

The error system is built around a base `AtlasError` class with specialized subclasses:

```
AtlasError
├── ConfigurationError
├── APIError
├── ValidationError
├── AuthenticationError
└── ResourceError
```

Each error type provides specific fields and behavior relevant to its domain.

## Core Components

### Error Severity

The `ErrorSeverity` enum defines how critical an error is:

```python
from atlas.core.errors import ErrorSeverity

# Available severity levels
ErrorSeverity.INFO      # Informational, not impacting operation
ErrorSeverity.WARNING   # Minor issue that can be worked around
ErrorSeverity.ERROR     # Issue that prevents operation but might be recoverable
ErrorSeverity.CRITICAL  # Critical issue that cannot be recovered from
```

### Error Categories

The `ErrorCategory` enum classifies errors by their domain:

```python
from atlas.core.errors import ErrorCategory

# Available categories
ErrorCategory.ENVIRONMENT   # Environmental issues (file access, network, etc.)
ErrorCategory.CONFIGURATION # Configuration problems
ErrorCategory.VALIDATION    # Input validation errors
ErrorCategory.API           # API/external service errors
ErrorCategory.AUTH          # Authentication/authorization errors
ErrorCategory.DATA          # Data processing errors
ErrorCategory.LOGIC         # Core algorithm/logic errors
ErrorCategory.RESOURCE      # Resource constraints (memory, CPU, etc.)
ErrorCategory.UNKNOWN       # Unknown/uncategorized errors
```

### Base Error Class: AtlasError

The `AtlasError` class is the foundation of the error system:

```python
from atlas.core.errors import AtlasError, ErrorSeverity, ErrorCategory

# Create a basic error
error = AtlasError(
    message="An error occurred",
    severity=ErrorSeverity.ERROR,
    category=ErrorCategory.UNKNOWN,
    details={"context": "additional_information"},
    cause=original_exception  # Optional original exception
)

# Convert to dictionary (useful for API responses)
error_dict = error.to_dict()

# Log the error (automatically uses appropriate log level)
error.log()
```

#### Constructor Parameters

| Parameter  | Type                       | Description                                   |
| ---------- | -------------------------- | --------------------------------------------- |
| `message`  | `str`                      | The error message                             |
| `severity` | `ErrorSeverity`            | Severity level of the error                   |
| `category` | `ErrorCategory`            | Category of the error                         |
| `details`  | `Optional[Dict[str, Any]]` | Additional information about the error        |
| `cause`    | `Optional[Exception]`      | The original exception that caused this error |

## Specialized Error Types

Atlas provides specialized error classes for common scenarios:

### ConfigurationError

Used for issues with configuration settings:

```python
from atlas.core.errors import ConfigurationError

# Create a configuration error
error = ConfigurationError(
    message="Invalid database path configuration",
    details={"setting": "db_path", "value": "/invalid/path"},
    severity=ErrorSeverity.ERROR
)
```

### APIError

Used for issues with external API calls:

```python
from atlas.core.errors import APIError

# Create an API error
error = APIError(
    message="Failed to connect to Anthropic API",
    details={"endpoint": "/messages", "status_code": 503},
    retry_possible=True  # Indicate whether retry might succeed
)
```

### ValidationError

Used for input validation issues:

```python
from atlas.core.errors import ValidationError

# Create a validation error
error = ValidationError(
    message="Invalid input parameters",
    field_errors={
        "max_tokens": ["Must be a positive integer"],
        "model_name": ["Unknown model name: 'invalid-model'"]
    },
    severity=ErrorSeverity.WARNING
)
```

### AuthenticationError

Used for authentication-related issues:

```python
from atlas.core.errors import AuthenticationError

# Create an authentication error
error = AuthenticationError(
    message="Invalid API key",
    provider="anthropic",
    details={"error_code": "invalid_api_key"}
)
```

### ResourceError

Used for resource constraint issues:

```python
from atlas.core.errors import ResourceError

# Create a resource error
error = ResourceError(
    message="Database connection limit exceeded",
    resource_type="database",
    details={"limit": 100, "current": 105}
)
```

## Utility Functions

The errors module provides several utility functions for error handling:

### safe_execute

Executes a function safely with exception handling:

```python
from atlas.core.errors import safe_execute, APIError

# Execute a function that might fail
result = safe_execute(
    func=api_client.call_endpoint,
    default={"fallback": "response"},  # Return this if the function fails
    error_handler=lambda e: handle_api_error(e),  # Optional custom handler
    log_error=True,  # Whether to log the error
    error_cls=APIError,  # What type of error to create
    error_msg="Failed to call API endpoint",  # Error message
    # Arguments for the function:
    endpoint="/messages",
    payload={"user_message": "Hello"}
)
```

### get_error_message

Extracts a formatted error message from an exception:

```python
from atlas.core.errors import get_error_message

try:
    # Some code that might fail
    result = complex_operation()
except Exception as e:
    # Get a clean error message
    error_msg = get_error_message(e)
    print(f"Operation failed: {error_msg}")

    # Or with traceback
    detailed_msg = get_error_message(e, include_traceback=True)
    logger.error(detailed_msg)
```

### convert_exception

Converts a standard Python exception to an AtlasError:

```python
from atlas.core.errors import convert_exception, ValidationError

try:
    # Some code that might fail
    config = parse_config(config_file)
except (ValueError, KeyError) as e:
    # Convert to a specific Atlas error type
    atlas_error = convert_exception(
        exception=e,
        error_cls=ValidationError,
        message="Invalid configuration format",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.CONFIGURATION,
        details={"config_file": config_file}
    )

    # Now you can use Atlas error features
    atlas_error.log()
    return {"error": atlas_error.to_dict()}
```

## Common Usage Patterns

### Catching and Converting Exceptions

A common pattern is to catch standard exceptions and convert them to Atlas errors:

```python
from atlas.core.errors import APIError, convert_exception

def call_llm_api(prompt, model):
    try:
        # Call external API
        response = client.generate(prompt=prompt, model=model)
        return response
    except requests.Timeout as e:
        # Convert to Atlas error
        raise convert_exception(
            e,
            error_cls=APIError,
            message="LLM API request timed out",
            details={"model": model, "timeout": client.timeout},
            severity=ErrorSeverity.ERROR
        )
    except requests.ConnectionError as e:
        # Convert to Atlas error
        raise convert_exception(
            e,
            error_cls=APIError,
            message="Failed to connect to LLM API",
            details={"model": model},
            severity=ErrorSeverity.ERROR
        )
```

### Safe Resource Management

Using the safe_execute function for operations that need cleanup:

```python
from atlas.core.errors import safe_execute, ResourceError

def process_large_file(file_path):
    def _process():
        file = open(file_path, 'r')
        try:
            # Process file
            return analyze_content(file)
        finally:
            # Always close the file
            file.close()

    # Execute with safety wrapper
    return safe_execute(
        _process,
        default={"status": "error", "results": []},
        error_cls=ResourceError,
        error_msg=f"Failed to process file: {file_path}"
    )
```

### Validation with Field Errors

Creating detailed validation errors with field-specific messages:

```python
from atlas.core.errors import ValidationError

def validate_config(config):
    field_errors = {}

    # Validate max_tokens
    if "max_tokens" in config:
        if not isinstance(config["max_tokens"], int) or config["max_tokens"] <= 0:
            field_errors["max_tokens"] = ["Max tokens must be a positive integer"]

    # Validate model_name
    if "model_name" not in config or not config["model_name"]:
        field_errors["model_name"] = ["Model name is required"]
    elif config["model_name"] not in SUPPORTED_MODELS:
        field_errors["model_name"] = [f"Unknown model: {config['model_name']}"]

    # Raise error if validation failed
    if field_errors:
        raise ValidationError(
            message="Invalid configuration parameters",
            field_errors=field_errors,
            severity=ErrorSeverity.WARNING
        )

    return config
```

### Error Response Serialization

Converting errors to API responses:

```python
from atlas.core.errors import AtlasError, convert_exception
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.exception_handler(AtlasError)
async def atlas_error_handler(request, error: AtlasError):
    error_dict = error.to_dict()
    status_code = 500

    # Map severity to HTTP status code
    if error.category == ErrorCategory.VALIDATION:
        status_code = 400
    elif error.category == ErrorCategory.AUTH:
        status_code = 401
    elif error.category == ErrorCategory.RESOURCE:
        status_code = 429

    return JSONResponse(
        status_code=status_code,
        content={"error": error_dict}
    )

@app.get("/query")
async def query_endpoint(q: str):
    try:
        result = process_query(q)
        return {"result": result}
    except Exception as e:
        # Convert any exception to Atlas error
        atlas_error = convert_exception(e)
        atlas_error.log()  # Log the error
        raise atlas_error  # Will be caught by exception handler
```

## Error Logging Integration

Atlas errors automatically integrate with Python's logging system:

```python
from atlas.core.errors import AtlasError, ErrorSeverity
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Errors automatically use appropriate log levels
info_error = AtlasError("Info message", severity=ErrorSeverity.INFO)
info_error.log()  # Uses logging.INFO

warning_error = AtlasError("Warning message", severity=ErrorSeverity.WARNING)
warning_error.log()  # Uses logging.WARNING

error_error = AtlasError("Error message", severity=ErrorSeverity.ERROR)
error_error.log()  # Uses logging.ERROR with traceback if cause is present

critical_error = AtlasError("Critical message", severity=ErrorSeverity.CRITICAL)
critical_error.log()  # Uses logging.CRITICAL with traceback if cause is present
```

## Extending the Error System

You can create custom error types for specific needs:

```python
from atlas.core.errors import AtlasError, ErrorCategory, ErrorSeverity

class DatabaseError(AtlasError):
    """Error related to database operations."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        query: Optional[str] = None,
    ):
        """Initialize the error.

        Args:
            message: The error message.
            details: Optional detailed information about the error.
            cause: The original exception that caused this error.
            severity: Severity level of the error.
            query: The database query that caused the error.
        """
        details = details or {}
        if query:
            details["query"] = query

        super().__init__(
            message=message,
            severity=severity,
            category=ErrorCategory.DATA,
            details=details,
            cause=cause,
        )
```

## Error Handling Best Practices

1. **Use Specific Error Types**: Use the most specific error class for each situation
   ```python
   # Good - specific error type
   raise ValidationError("Invalid model name")

   # Bad - generic error
   raise AtlasError("Invalid model name")
   ```

2. **Include Contextual Details**: Provide relevant context in the details dict
   ```python
   # Good - includes context
   raise APIError("API request failed", details={"status_code": 404, "endpoint": "/messages"})

   # Bad - minimal context
   raise APIError("API request failed")
   ```

3. **Preserve Original Exceptions**: Include the original exception as the cause
   ```python
   try:
       response = requests.get(url, timeout=5)
       response.raise_for_status()
   except requests.RequestException as e:
       raise APIError("Request failed", cause=e)
   ```

4. **Log At Appropriate Levels**: Match error severity to the actual impact
   ```python
   # Minor formatting issue - use WARNING
   raise ValidationError("Invalid date format", severity=ErrorSeverity.WARNING)

   # Critical authentication failure - use CRITICAL
   raise AuthenticationError("API key rejected", severity=ErrorSeverity.CRITICAL)
   ```

5. **Handle Errors at Appropriate Levels**: Catch errors at levels where you can take meaningful action
   ```python
   def api_call():
       try:
           # Low-level API call
           return make_request()
       except Exception as e:
           # Convert to APIError but let caller decide how to handle it
           raise convert_exception(e, error_cls=APIError)

   def user_request_handler():
       try:
           # Higher-level function
           return api_call()
       except APIError as e:
           # Handle error appropriately at this level
           e.log()
           return {"error": "Service temporarily unavailable"}
   ```

## Related Documentation

- [Configuration System](config.md) - Documentation for the configuration system
- [Environment Variables Module](env.md) - Documentation for environment variables handling
- [Telemetry Module](telemetry.md) - Documentation for telemetry and logging
