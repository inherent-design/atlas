---
title: Code Standards
---

# Code Standards

This guide provides comprehensive standards for code quality, formatting, and type system usage in Atlas. Following these standards ensures consistent, maintainable, and high-quality code across the project.

## Code Examples

### Core Principles

1. **Completeness**: Examples should be complete and runnable
2. **Clarity**: Code should be easy to understand with appropriate comments
3. **Conciseness**: Examples should be as short as possible while demonstrating the concept
4. **Correctness**: All examples must work with the current version of Atlas
5. **Consistency**: Maintain consistent style across all examples

### Example Structure

Code examples should follow this general structure:

1. **Imports**: Include all necessary imports
2. **Setup**: Any required initialization or configuration
3. **Core Example**: The main functionality being demonstrated
4. **Output**: Expected output, when helpful (as comments)

### Example Template

```python
# Import necessary modules
from atlas.providers import AnthropicProvider
from atlas.query import query_with_retrieval

# Setup configuration
provider = AnthropicProvider(model_name="claude-3-7-sonnet-20250219")

# Core example functionality
response = query_with_retrieval(
    query="How does the provider system work?",
    provider=provider,
    collection_name="atlas_docs"
)

# Output handling
print(response)
# Expected output:
# "The provider system is responsible for..."
```

### Complexity Progression

When documenting features, provide examples with increasing complexity:

1. **Basic Example**: Minimal implementation showing core functionality
2. **Intermediate Example**: Shows common customization options
3. **Advanced Example**: Demonstrates complex use cases or integrations

### Code Groups

Code groups allow you to present alternative implementations or language versions. Use the following format:

````md
::: code-group

```python [config.py]
# Simple configuration approach
from atlas.providers import AnthropicProvider

provider = AnthropicProvider(model_name="claude-3-7-sonnet-20250219")
```

```python [advanced_config.py]
# Advanced configuration with options
from atlas.providers import AnthropicProvider

provider = AnthropicProvider(
    model_name="claude-3-7-sonnet-20250219",
    temperature=0.7,
    max_tokens=2000
)
```

:::
````

#### When to Use Code Groups

- **Multiple Implementations**: Different languages or frameworks
- **Alternative Approaches**: Multiple valid ways to accomplish a task
- **Configuration Variations**: Different options for the same component
- **Environment Differences**: Code variations for different environments

### Commenting Standards

Include comments for:

1. **Setup Explanation**: Explain initialization steps and configuration
2. **Complex Operations**: Clarify any non-obvious code
3. **Expected Results**: Show what output to expect (when not self-evident)
4. **Key Concepts**: Highlight important concepts or patterns

### Code Style

#### Formatting Guidelines

1. **Line Length**: Keep lines under 88 characters
2. **Indentation**: Use 4 spaces for indentation
3. **Whitespace**: Include whitespace for readability
4. **Variable Names**: Use descriptive variable names

#### Naming Conventions

- **Variables**: Use descriptive `snake_case` names
- **Classes**: Use `PascalCase` for class names
- **Constants**: Use `UPPER_SNAKE_CASE` for constants
- **Functions**: Use descriptive `snake_case` verbs

## Colored Diffs

When documenting code changes, updates, or comparing different implementations, colored diffs highlight what has changed. 

### Basic Syntax

VitePress provides syntax for adding colored diffs to code blocks using inline comments:

```python
def hello_world():
    print("Hello, World!") # [!code --]
    print("Hello, Atlas!") # [!code ++]
```

### Comment Syntax by Language

The comment syntax must match the language:
- Python: `# [!code --]` and `# [!code ++]`
- JavaScript/TypeScript: `// [!code --]` and `// [!code ++]`
- CSS: `/* [!code --] */` and `/* [!code ++] */`
- HTML: `<!-- [!code --] -->` and `<!-- [!code ++] -->`

### When to Use Colored Diffs

1. **API Changes**: Showing how an API has evolved between versions
2. **Code Improvements**: Demonstrating refactoring or optimization
3. **Bug Fixes**: Highlighting the specific lines that fix a bug
4. **Best Practices**: Showing the difference between problematic and recommended code
5. **Subtle Changes**: Making small but important changes more visible

### Example: API Evolution

```python
# Old API (v0.8)
provider = Provider( # [!code --]
    provider_type="anthropic", # [!code --]
    model="claude-2.0", # [!code --]
    api_key=os.environ.get("ANTHROPIC_API_KEY") # [!code --]
) # [!code --]

# New API (v1.0)
from atlas.providers import AnthropicProvider # [!code ++]
 # [!code ++]
provider = AnthropicProvider( # [!code ++]
    model_name="claude-3-7-sonnet-20250219", # [!code ++]
    api_key=os.environ.get("ANTHROPIC_API_KEY") # [!code ++]
) # [!code ++]
```

### Guidelines for Effective Diffs

1. **Focus on the Changes**: Only mark the specific lines that have changed
2. **Include Context**: Provide enough surrounding code for understanding
3. **Clear Comments**: Add explanatory comments as needed
4. **Group Related Changes**: Keep related changes together
5. **Stay Concise**: Avoid showing unnecessary code

## Type System

Atlas combines static type checking with runtime schema validation to ensure code reliability and improve developer experience.

### Core Type Concepts

#### TypedDict vs Dict[str, Any]

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

#### Protocol Interfaces

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
@runtime_checkable
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

### Advanced Typing Scenarios

#### Union Types and Type Narrowing

::: code-group
```python [❌ Avoid]
def process(value: Union[str, int]) -> str:
    # Might fail if value is an int
    return value.upper()
```

```python [✅ Preferred]
def process(value: str | int) -> str:
    if isinstance(value, str):
        return value.upper()
    return str(value).upper()
```
:::

#### Optional Types and None Checks

::: code-group
```python [❌ Avoid]
def calculate(value: Optional[int]) -> int:
    # Will fail if value is None
    return value + 10
```

```python [✅ Preferred]
def calculate(value: int | None) -> int:
    if value is None:
        return 10  # Default value
    return value + 10
```
:::

### Modern Typing Features

#### Union Types (Python 3.10+)

Use the pipe operator for union types:

```python
# Instead of
from typing import Union, Optional
x: Union[int, str] = 1
y: Optional[int] = None

# Use
x: int | str = 1  
y: int | None = None
```

#### Required/NotRequired in TypedDict (Python 3.11+)

```python
from typing import NotRequired, TypedDict

class User(TypedDict):
    name: str  # Required field
    email: str  # Required field
    age: NotRequired[int]  # Optional field
```

#### Self Type (Python 3.11+)

```python
from typing import Self

class Builder:
    def with_name(self, name: str) -> Self:
        self.name = name
        return self
```

### Type Aliases for Improved Readability

```python
from typing import TypeAlias

ItemPair: TypeAlias = tuple[int, str]
ItemCollection: TypeAlias = dict[str, list[ItemPair]]

def process_items(items: ItemCollection) -> None:
    # Much clearer with type aliases
    pass
```

### Best Practices

1. **Define Core Types Centrally**: Keep all shared types in `atlas/core/types.py`
2. **Use Protocol for Interfaces**: Prefer Protocol over ABC for interface definitions
3. **TypedDict for Data Structures**: Use TypedDict for structured data instead of Dict[str, Any]
4. **Explicit Optional Fields**: Use NotRequired for optional fields in TypedDict
5. **Be Explicit About Collections**: Always specify element types in collections
6. **Handle None Properly**: Always check for None in Optional types
7. **Use Generic Types**: Leverage type variables for reusable container types
8. **Return Type Annotations**: Include return type annotations on all functions
9. **Type Narrowing**: Perform proper type narrowing on Union types before operations
10. **Use @runtime_checkable**: Add this decorator to Protocol classes that may be used with isinstance()

## Type Mappings

Type mappings ensure consistent type conversions between different components and systems within Atlas.

### Type Mapping Pattern

The recommended pattern for type mappings follows a standardized approach:

```python
class TypeConverter:
    """Handles conversions between different type representations."""

    @staticmethod
    def to_target_format(source_obj):
        """Convert from source format to target format."""
        # Conversion logic here
        pass

    @staticmethod
    def from_target_format(target_obj):
        """Convert from target format back to source format."""
        # Reverse conversion logic here
        pass
```

### Python to JSON Type Mapping

| Python Type        | JSON Representation | Notes                                      |
| ------------------ | ------------------- | ------------------------------------------ |
| `str`              | String              | Direct mapping                             |
| `int`, `float`     | Number              | Direct mapping                             |
| `bool`             | Boolean             | Direct mapping                             |
| `None`             | null                | Direct mapping                             |
| `list`, `tuple`    | Array               | Elements are converted recursively         |
| `dict`             | Object              | Keys must be strings                       |
| `datetime`, `date` | String              | ISO format (YYYY-MM-DDTHH:MM:SS.sssZ)      |
| Custom classes     | Object              | Convert to dict with `__dict__` or schemas |
| `Enum`             | String/Number       | Use enum value                             |

### Schema-Based Type Mapping

For complex objects, use schema-based mapping:

```python
from marshmallow import Schema, fields, post_load

class UserData:
    def __init__(self, name: str, email: str, age: int, roles: List[str]):
        self.name = name
        self.email = email
        self.age = age
        self.roles = roles

class UserSchema(Schema):
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    age = fields.Int(required=True)
    roles = fields.List(fields.Str(), required=True)

    @post_load
    def make_user(self, data, **kwargs):
        return UserData(**data)

# Usage
schema = UserSchema()
user_dict = {"name": "John", "email": "john@example.com", "age": 30, "roles": ["admin", "user"]}
user_obj = schema.load(user_dict)  # Convert dict to UserData
user_dict_again = schema.dump(user_obj)  # Convert UserData back to dict
```

### Type Mapping Best Practices

1. **Bidirectional Conversion**: Implement both to/from conversion functions
2. **Validation**: Always validate data after conversion
3. **Error Handling**: Provide clear error messages for conversion failures
4. **Default Values**: Handle missing or null fields consistently
5. **Version Tolerance**: Design conversions to be tolerant of version differences
6. **Type Safety**: Use static typing for converter functions

## Code Quality Tools

### Type Checking

```bash
# Check a specific file
uv run mypy atlas/module/file.py

# Check the entire project
uv run mypy atlas
```

### Linting and Formatting

```bash
# Run linting
uv run ruff check .

# Fix linting issues automatically
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Testing with Type Safety

```bash
# Run all tests with coverage
uv run pytest

# Run specific test modules
uv run pytest atlas/tests/core/services/
```

By following these code standards, Atlas maintains consistent, high-quality code that is easy to understand, maintain, and extend.