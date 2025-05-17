# Atlas Type System Guide

This document provides comprehensive guidance on using the Atlas type system effectively. It covers key concepts, design patterns, and practical examples to ensure type safety and maintainability throughout the codebase.

## Overview

Atlas combines static type checking with runtime schema validation to ensure code reliability and improve developer experience. Our type system is built around:

1. **Static Type Checking**: Using Python's typing system for compile-time verification
   - Protocol interfaces for loose coupling
   - Generic type parameters for flexible, reusable code
   - Literal types for type-safe enumerations
   - Type narrowing techniques for Union and Optional types

2. **Runtime Schema Validation**: Using Marshmallow for runtime verification
   - API boundary validation with schema decorators
   - Data structure transformations with serialization/deserialization
   - Self-documenting data requirements
   - Detailed error messages for invalid data

This guide covers both static typing and schema validation components of the Atlas type system.

## Core Type Concepts

### TypedDict vs Dict[str, Any]

TypedDict provides structural typing for dictionaries with a known set of keys.

::: code-group
```python [❌ Avoid]
def process_message(message: Dict[str, Any]) -> Dict[str, Any]:
    # No type safety for dictionary structure
    return {"content": message["content"], "processed": True}
```

```python [✅ Preferred]
class MessageDict(TypedDict):
    content: str
    role: str
    metadata: NotRequired[Dict[str, Any]]

class ProcessedMessageDict(TypedDict):
    content: str
    processed: bool

def process_message(message: MessageDict) -> ProcessedMessageDict:
    # Type-safe dictionary access and creation
    return {"content": message["content"], "processed": True}
```
:::

### Protocol Interfaces

Protocols define structural interfaces without requiring inheritance.

::: code-group
```python [❌ Avoid]
class BaseProvider(ABC):
    @abstractmethod
    def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        pass

class CustomProvider(BaseProvider):
    # Must inherit and implement all methods
    def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {"content": "Hello world"}
```

```python [✅ Preferred]
class ProviderProtocol(Protocol):
    def generate(self, request: ModelRequestDict) -> ModelResponseDict:
        ...

# No inheritance needed, just implement the interface
class CustomProvider:
    def generate(self, request: ModelRequestDict) -> ModelResponseDict:
        return {"content": "Hello world", "model": "custom", "provider": "custom",
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                "cost": {"input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0}}
```
:::

### Type Variables and Generics

Type variables enable generic programming for flexible, reusable code.

::: code-group
```python [❌ Avoid]
class Container:
    def __init__(self, value: Any):
        self.value = value

    def get(self) -> Any:
        return self.value
```

```python [✅ Preferred]
T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T):
        self.value = value

    def get(self) -> T:
        return self.value

# Usage with explicit type
string_container: Container[str] = Container("hello")
value: str = string_container.get()  # Type-safe
```
:::

## Handling Advanced Typing Scenarios

### Union Types and Type Narrowing

When using Union types, narrow the type with appropriate checks before operations.

::: code-group
```python [❌ Avoid]
def process(value: Union[str, int]) -> str:
    # Might fail if value is an int
    return value.upper()
```

```python [✅ Preferred]
def process(value: Union[str, int]) -> str:
    if isinstance(value, str):
        return value.upper()
    return str(value).upper()
```
:::

### Optional Types and None Checks

Always check for None when working with Optional types.

::: code-group
```python [❌ Avoid]
def calculate(value: Optional[int]) -> int:
    # Will fail if value is None
    return value + 10
```

```python [✅ Preferred]
def calculate(value: Optional[int]) -> int:
    if value is None:
        return 10  # Default value
    return value + 10
```
:::

### Type Casting with `cast()`

Use `cast()` when you know more about a type than the type checker can infer.

::: code-group
```python [❌ Avoid]
# In capabilities.py
try:
    strength_level = getattr(CapabilityStrength, strength.upper())
except (AttributeError, KeyError):
    strength_level = CapabilityStrength.MODERATE
```

```python [✅ Preferred]
# In capabilities.py
try:
    # Convert string to actual enum member using proper typing
    strength_level = cast(CapabilityStrength, getattr(CapabilityStrength, strength.upper()))
except (AttributeError, KeyError):
    # Default to MODERATE if unrecognized
    strength_level = CapabilityStrength.MODERATE
```
:::

## Common Type Patterns

### Collection Handling

Use proper collection types for consistent type checking.

::: code-group
```python [❌ Avoid]
def get_models() -> list:
    return ["model1", "model2"]

def process_models(models):
    for model in models:
        print(model.upper())  # No type checking
```

```python [✅ Preferred]
def get_models() -> List[str]:
    return ["model1", "model2"]

def process_models(models: List[str]) -> None:
    for model in models:
        print(model.upper())  # Type-safe
```
:::

### Structural Typing with TypedDict

Use TypedDict for complex data structures with optional fields.

::: code-group
```python [❌ Avoid]
def create_request(model: str, messages: List[Dict[str, Any]],
                  temperature: float = 0.7) -> Dict[str, Any]:
    request = {"model": model, "messages": messages}
    if temperature != 0.7:
        request["temperature"] = temperature
    return request
```

```python [✅ Preferred]
def create_request(model: str, messages: List[MessageDict],
                  temperature: Optional[float] = None) -> ModelRequestDict:
    request: ModelRequestDict = {"model": model, "messages": messages}
    if temperature is not None:
        request["temperature"] = temperature
    return request
```
:::

### Literal Types for Constrained Values

Use Literal for type-safe string constants instead of arbitrary strings.

::: code-group
```python [❌ Avoid]
def set_role(message: Dict[str, Any], role: str) -> None:
    message["role"] = role  # No validation for role values
```

```python [✅ Preferred]
RoleType = Literal["user", "system", "assistant", "function", "tool"]

def set_role(message: MessageDict, role: RoleType) -> None:
    message["role"] = role  # Type-safe, validates role values
```
:::

## Real-World Examples from Atlas

### Enum Classes with String Values

Use string enums to provide both type safety and string compatibility.

::: code-group
```python [❌ Avoid]
# Using plain strings for message roles
message = {"role": "user", "content": "Hello"}

# Risks typos and invalid values
message = {"role": "uesr", "content": "Hello"}  # Typo!
```

```python [✅ Preferred]
# From atlas/core/types.py
class MessageRole(str, Enum):
    """Roles in a conversation with a model."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"

# Usage
message = {"role": MessageRole.USER, "content": "Hello"}

# String compatibility maintained
assert message["role"] == "user"  # True
```
:::

### Safe Type Handling in Stream Controls

Ensure proper type safety when working with Optional fields.

::: code-group
```python [❌ Avoid]
# From streaming/control.py
def _update_metrics(self, delta: str) -> None:
    with self._metrics_lock:
        if self._metrics["start_time"] is None:
            self._metrics["start_time"] = time.time()

        # Unsafe operations on potentially None values
        self._metrics["chunks_processed"] += 1
```

```python [✅ Preferred]
# From streaming/control.py
def _update_metrics(self, delta: str) -> None:
    with self._metrics_lock:
        # Initialize metrics with default values if they're None
        if self._metrics["start_time"] is None:
            self._metrics["start_time"] = time.time()

        if self._metrics["chunks_processed"] is None:
            self._metrics["chunks_processed"] = 0

        # Get the current values
        chunks_processed = self._metrics["chunks_processed"]

        # Perform operations on local variables
        chunks_processed += 1

        # Store updated values back
        self._metrics["chunks_processed"] = chunks_processed
```
:::

### Protocol vs. ABC for Interfaces

Use Protocol for interface definitions with better flexibility.

::: code-group
```python [❌ Avoid]
# From streaming/control.py (mixed approach)
class StreamControl(abc.ABC, StreamControlProtocol):
    """Interface for controlling a streaming response."""

    @property
    @abc.abstractmethod
    def state(self) -> StreamState:
        """Get the current state of the stream."""
        pass
```

```python [✅ Preferred]
# Better approach with pure Protocol
class StreamControlProtocol(Protocol):
    """Protocol for controlling streaming responses."""

    @property
    def state(self) -> StreamState:
        """Get the current state of the stream."""
        ...

    @property
    def can_pause(self) -> bool:
        """Whether this stream supports pausing."""
        ...
```
:::

### Proper Type Narrowing

Always check types appropriately before operations.

::: code-group
```python [❌ Avoid]
def call_provider(provider: Any, request: Dict[str, Any]) -> str:
    response = provider.generate(request)
    return response.content  # May fail if response structure is unexpected
```

```python [✅ Preferred]
def call_provider(provider: ModelProvider, request: ModelRequestDict) -> str:
    response = provider.generate(request)

    # Ensure content exists and is a string
    if not isinstance(response, dict) or "content" not in response:
        raise ValueError("Invalid response structure")

    content = response["content"]
    if not isinstance(content, str):
        raise ValueError(f"Expected string content, got {type(content)}")

    return content
```
:::

## Best Practices for Atlas Development

1. **Define Core Types Centrally**: Keep all shared types in `atlas/core/types.py`
2. **Use Protocol for Interfaces**: Prefer Protocol over ABC for interface definitions
3. **TypedDict for Data Structures**: Use TypedDict for structured data instead of Dict[str, Any]
4. **Explicit Optional Fields**: Use NotRequired for optional fields in TypedDict
5. **Be Explicit About Collections**: Always specify element types in collections
6. **Handle None Properly**: Always check for None in Optional types
7. **Use Generic Types**: Leverage type variables for reusable container types
8. **Consistent Error Handling**: Add proper return typing for error conditions
9. **Return Type Annotations**: Include return type annotations on all functions
10. **Type Narrowing**: Perform proper type narrowing on Union types before operations

## Schema Validation and Type Mappings

Atlas is migrating from static typing with TypedDict to runtime validation with Marshmallow schemas. For detailed information about schema validation and type mappings in Atlas, see these guides:

1. [Schema Validation Guide](./schema-validation.md) - How to use schema validation with examples
2. [Type Mapping Guide](./type-mappings.md) - Handling type conversions between different systems

### Key Benefits of Schema Validation

- **Runtime Validation**: Catch data structure issues at runtime with detailed error messages
- **Data Transformation**: Seamlessly convert between JSON/dict data and typed objects
- **Documentation**: Self-documenting data requirements and constraints
- **Extensibility**: Custom field types and validation logic
- **Error Handling**: Consistent error reporting and conversion to domain-specific errors
- **API Boundaries**: Robust validation at system interfaces

### Type Mapping Benefits

- **Consistent Conversions**: Standard patterns for type conversions
- **Bidirectional Transformations**: Reliable roundtrip conversions
- **System Boundary Integrity**: Safe type handling across API boundaries
- **Serialization Strategies**: Proven approaches for complex type serialization

### Using Schema Validation with Static Types

The ideal pattern is to combine static typing with runtime validation:

```python
from typing import Dict, Any
from atlas.schemas.validation import validate_with_schema
from atlas.schemas.messages import model_message_schema

# Static type hints + runtime validation
@validate_with_schema(model_message_schema)
def process_message(message: Dict[str, Any]) -> str:
    # message is guaranteed to be valid
    return f"Processing {message['role']} message"
```

## Common Type Issues and Solutions

### Issue: Incompatible assignment

```python
# Error: Incompatible types in assignment
result: MyClass = get_result()  # get_result() returns Any
```

**Solution**: Use explicit cast

```python
from typing import cast
result = cast(MyClass, get_result())
```

### Issue: Missing attribute in Union type

```python
# Error: Item "None" of "Optional[Response]" has no attribute "content"
def get_content(response: Optional[Response]) -> str:
    return response.content  # Error when response is None
```

**Solution**: Add explicit type narrowing

```python
def get_content(response: Optional[Response]) -> str:
    if response is None:
        return ""  # Or raise an appropriate exception
    return response.content
```

### Issue: Type confusion with string enums

```python
# Error: Argument 1 to "process" has incompatible type "str"; expected "Status"
status = "active"  # From a config or external source
process(status)  # process expects Status enum
```

**Solution**: Use proper conversion or validation

```python
def get_status(status_str: str) -> Status:
    try:
        return Status(status_str)  # Try to convert string to enum
    except ValueError:
        return Status.UNKNOWN  # Default fallback

process(get_status(status))
```

### Issue: Generic collection type issues

```python
# Error: List item 0 has incompatible type "str"; expected "int"
def add_numbers(numbers: List[int]) -> int:
    return sum(numbers)

add_numbers(["1", "2", "3"])  # Type error
```

**Solution**: Use proper type conversion

```python
def add_numbers(numbers: List[int]) -> int:
    return sum(numbers)

string_values = ["1", "2", "3"]
add_numbers([int(val) for val in string_values])  # Convert to proper type
```

## Running Type Checks

To validate type correctness, use mypy:

```bash
# Check a specific file
uv tool run mypy atlas/module/file.py

# Check the entire project
uv tool run mypy atlas
```

### Common Type Check Flags

```bash
# Strict mode (recommended)
uv tool run mypy --strict atlas/

# Ignore specific errors
uv tool run mypy --ignore-missing-imports atlas/

# Show detailed error messages
uv tool run mypy --show-error-codes atlas/
```

## References

### Static Typing Resources
- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
- [mypy Documentation](https://mypy.readthedocs.io/en/stable/)
- [TypedDict Documentation](https://mypy.readthedocs.io/en/stable/typed_dict.html)
- [Protocol Documentation](https://mypy.readthedocs.io/en/stable/protocols.html)

### Schema Validation Resources
- [Schema Validation Guide](./schema-validation.md)
- [Type Mapping Guide](./type-mappings.md)
- [Marshmallow Documentation](https://marshmallow.readthedocs.io/)

### System Integration Resources
- [NERV-Inner Universe Type Mappings](../v2/inner-universe/type_mappings.md)
- [Inner Universe Types](../v2/inner-universe/types.md)
