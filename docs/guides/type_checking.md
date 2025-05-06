# Type Checking Guide

This guide provides comprehensive information about type checking in the Atlas project, including how to set up, run, and fix common type issues.

## Introduction to Type Checking

Type checking is a static analysis technique that helps catch type-related errors during development rather than at runtime. It offers several benefits:

1. **Catch errors early**: Identify type mismatches before running the code
2. **Improve code quality**: Better documentation and more maintainable code
3. **Enable IDE features**: Enhanced autocompletion and code navigation
4. **Facilitate refactoring**: Safer code changes with immediate feedback

Atlas uses [mypy](https://mypy.readthedocs.io/), the standard Python type checker, to verify type correctness across the codebase.

## Type Checking Setup

### Configuration

Atlas includes a `mypy.ini` configuration file in the project root that specifies type checking behavior:

```ini
[mypy]
python_version = 3.13
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False
disallow_incomplete_defs = False
check_untyped_defs = True
disallow_untyped_decorators = False
no_implicit_optional = True
strict_optional = True

# Ignore missing imports for third-party libraries
[mypy-pydantic.*]
ignore_missing_imports = True

# Additional third-party libraries with ignored imports
[mypy-chromadb.*]
ignore_missing_imports = True

# ... additional configurations ...
```

This configuration:

1. Targets Python 3.13
2. Enables warnings for returning `Any` and unused configurations
3. Checks functions without type annotations
4. Enforces strict handling of `Optional` types
5. Ignores missing type stubs for third-party libraries

### Installation

To set up type checking in your development environment:

```bash
# Install development dependencies including mypy
uv pip install mypy

# For improved type checking of specific libraries
uv pip install types-requests types-PyYAML
```

## Running Type Checking

### Basic Usage

To run type checking on the entire Atlas codebase:

```bash
uv tool run mypy .
```

To check specific modules or files:

```bash
# Check a specific file
uv tool run mypy atlas/agents/base.py

# Check a specific directory
uv tool run mypy atlas/models/
```

### Integration with Development Workflow

#### Command Line

Add type checking to your development workflow:

```bash
# Run before committing changes
uv tool run mypy .

# Check only changed files
git diff --name-only | grep '\.py$' | xargs uv tool run mypy
```

#### Editor Integration

For VSCode, add these settings to your configuration:

```json
{
    "python.linting.mypyEnabled": true,
    "python.linting.enabled": true,
    "python.linting.mypyArgs": [
        "--config-file=mypy.ini"
    ]
}
```

For PyCharm, enable mypy in:
Settings → Tools → Python Integrated Tools → Mypy

## Type Annotations in Atlas

### Core Type Patterns

Atlas uses several common type annotation patterns:

#### Basic Types

```python
def get_model_name(provider_name: str) -> str:
    # Function that takes a string and returns a string
    ...
```

#### Optional and Union Types

```python
from typing import Optional, Union

def process_config(config: Optional[dict] = None) -> Union[str, None]:
    # Function that takes an optional dictionary and returns either a string or None
    ...
```

#### Collections

```python
from typing import List, Dict, Set, Tuple

def get_document_metadata(document_ids: List[str]) -> Dict[str, Dict[str, str]]:
    # Function that takes a list of strings and returns a nested dictionary
    ...
```

#### Callables

```python
from typing import Callable

def apply_streaming(
    text: str, 
    callback: Callable[[str, str], None]
) -> None:
    # Function that takes a string and a callback function
    ...
```

#### Type Aliases

```python
from typing import Dict, Any, TypeAlias

# Define type aliases for complex types
DocumentMetadata: TypeAlias = Dict[str, Any]
RetrievalResult: TypeAlias = Dict[str, Dict[str, Any]]

def retrieve_documents(query: str) -> RetrievalResult:
    # More readable function signature using type aliases
    ...
```

### State Models with Pydantic

Atlas uses Pydantic extensively for state models:

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AgentState(BaseModel):
    """State model for agent operations."""
    
    query: str = ""
    context: List[Dict[str, Any]] = Field(default_factory=list)
    response: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

## Common Type Issues and Solutions

### 1. Missing Type Stubs for External Libraries

**Issue**: Type errors from missing type stubs for libraries like `chromadb`, `anthropic`, etc.

**Solutions**:

1. **Install type stubs if available**:
   ```bash
   uv pip install types-requests
   ```

2. **Create stub files for critical libraries**:
   ```python
   # in stubs/chromadb/__init__.pyi
   from typing import Any, Dict, List, Optional
   
   class PersistentClient:
      def __init__(self, path: str) -> None: ...
      def get_collection(self, name: str) -> Collection: ...
   
   class Collection:
      def add(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]) -> None: ...
      def query(self, query_texts: List[str], n_results: int) -> Dict[str, Any]: ...
   ```

3. **Use type ignores for specific lines**:
   ```python
   result = chromadb_client.query(query_text)  # type: ignore
   ```

### 2. Union Type Handling

**Issue**: Errors with union types (`Union[str, None]` or `str | None`).

**Solutions**:

1. **Explicit type checks**:
   ```python
   def process_value(value: Optional[str]) -> str:
       if value is None:
           return "default"
       return value.upper()
   ```

2. **Type guards**:
   ```python
   def is_string_list(value: Union[List[str], List[int]]) -> bool:
       return all(isinstance(x, str) for x in value)
   
   def process_list(items: Union[List[str], List[int]]) -> None:
       if is_string_list(items):
           # mypy now knows items is List[str]
           for item in items:
               print(item.upper())
   ```

3. **Using get_type_hints**:
   ```python
   from typing import get_type_hints
   
   def get_function_return_type(func):
       hints = get_type_hints(func)
       return hints.get('return')
   ```

### 3. Generic Types

**Issue**: Complex container types with generics.

**Solutions**:

1. **Type variables**:
   ```python
   from typing import TypeVar, List, Callable
   
   T = TypeVar('T')
   
   def first_element(items: List[T]) -> T:
       return items[0]
   ```

2. **Generic type aliases**:
   ```python
   from typing import Dict, TypeVar, List
   
   K = TypeVar('K')
   V = TypeVar('V')
   
   ResultDict = Dict[K, List[V]]
   
   def group_by_key(items: List[V], key_func: Callable[[V], K]) -> ResultDict[K, V]:
       result: ResultDict[K, V] = {}
       for item in items:
           key = key_func(item)
           if key not in result:
               result[key] = []
           result[key].append(item)
       return result
   ```

### 4. Any Type Issues

**Issue**: Overusing `Any` reduces type safety.

**Solutions**:

1. **Use more specific types**:
   ```python
   # Instead of:
   def process_data(data: Any) -> Any:
       ...
   
   # Use:
   def process_data(data: Dict[str, Union[str, int]]) -> List[str]:
       ...
   ```

2. **Cast when necessary**:
   ```python
   from typing import cast
   
   def get_document(doc_id: str) -> Dict[str, Any]:
       result = db.query(doc_id)
       return cast(Dict[str, Any], result)
   ```

3. **Protocol classes for duck typing**:
   ```python
   from typing import Protocol
   
   class Queryable(Protocol):
       def query(self, text: str) -> Dict[str, Any]: ...
   
   def perform_search(provider: Queryable, query: str) -> Dict[str, Any]:
       return provider.query(query)
   ```

## Advanced Type Checking Techniques

### Type Guards

Type guards help narrow down union types:

```python
from typing import Union, List, Dict, TypeGuard

def is_dict_list(obj: Union[List[Dict[str, Any]], Dict[str, Any]]) -> TypeGuard[List[Dict[str, Any]]]:
    return isinstance(obj, list) and all(isinstance(x, dict) for x in obj)

def process_result(result: Union[List[Dict[str, Any]], Dict[str, Any]]) -> None:
    if is_dict_list(result):
        # mypy now knows result is List[Dict[str, Any]]
        for item in result:
            print(item.keys())
    else:
        # mypy now knows result is Dict[str, Any]
        print(result.keys())
```

### Overload Decorators

For functions with multiple valid signatures:

```python
from typing import overload, Union, List, Dict, Any

@overload
def retrieve(query: str) -> List[Dict[str, Any]]: ...

@overload
def retrieve(query: str, return_dict: bool = True) -> Dict[str, List[Dict[str, Any]]]: ...

def retrieve(query: str, return_dict: bool = False) -> Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    results = knowledge_base.query(query)
    if return_dict:
        return {"results": results}
    return results
```

### Using Type Aliases

Type aliases make complex types more readable:

```python
from typing import TypeAlias, Dict, List, Any

# Define type aliases
DocumentDict: TypeAlias = Dict[str, Any]
DocumentList: TypeAlias = List[DocumentDict]
SearchResult: TypeAlias = Dict[str, DocumentList]

# Use the aliases in function signatures
def search_documents(query: str) -> SearchResult:
    """Search for documents matching the query."""
    ...
```

## Best Practices

### 1. Consistent Annotation Style

Be consistent with type annotations:

```python
# Always annotate function parameters and return types
def get_document(document_id: str) -> Dict[str, Any]:
    ...

# Use explicit Optional for parameters that might be None
def configure_client(api_key: Optional[str] = None) -> None:
    ...

# Annotate class variables in __init__
class DocumentProcessor:
    def __init__(self, batch_size: int = 10):
        self.batch_size: int = batch_size
        self.documents: List[Dict[str, Any]] = []
```

### 2. Appropriate Use of Any

Use `Any` deliberately and sparingly:

```python
# Good: Only use Any where actually needed
def process_dynamic_data(data: Dict[str, Any]) -> List[str]:
    result = []
    for key, value in data.items():
        if isinstance(value, str):
            result.append(value)
        elif isinstance(value, int):
            result.append(str(value))
    return result

# Better: Use Union for known possibilities
def process_restricted_data(data: Dict[str, Union[str, int, float]]) -> List[str]:
    result = []
    for key, value in data.items():
        if isinstance(value, str):
            result.append(value)
        else:
            result.append(str(value))
    return result
```

### 3. Comment Type Ignores

When using `# type: ignore`, always add a comment explaining why:

```python
# Bad:
result = some_untyped_function()  # type: ignore

# Good:
# Third-party library without stubs
result = some_untyped_function()  # type: ignore

# Better:
# TODO: Create stub for module_without_types (issue #123)
result = some_untyped_function()  # type: ignore
```

### 4. Typed Dictionaries

For complex dictionary structures, use TypedDict:

```python
from typing import TypedDict, List, Optional

class DocumentMetadata(TypedDict):
    source: str
    author: str
    date: str
    tags: List[str]
    summary: Optional[str]

def process_document(metadata: DocumentMetadata) -> None:
    print(f"Processing document from {metadata['source']}")
    for tag in metadata['tags']:
        print(f"  - Tag: {tag}")
```

## Gradual Type Checking Strategy

Atlas is implementing typing gradually, focusing on:

1. **Core APIs first**: Highest priority for public interfaces
2. **Critical path components**: Parts of the codebase with complex logic
3. **New code**: Requiring type annotations for all new contributions
4. **Incremental improvement**: Adding types during refactoring or bug fixes

The long-term goal is to enable stricter type checking options:

```ini
# Future mypy.ini target
[mypy]
python_version = 3.13
disallow_untyped_defs = True        # All functions must have type annotations
disallow_incomplete_defs = True     # All function parameters must be annotated
disallow_untyped_decorators = True  # All decorators must be annotated
warn_redundant_casts = True         # Warn about unnecessary casts
warn_unused_ignores = True          # Warn about unnecessary type ignores
warn_return_any = True              # Warn about returning Any
warn_unreachable = True             # Warn about unreachable code
```

## Troubleshooting Common Errors

### "Cannot infer type of lambda"

**Problem**:
```
atlas/models/factory.py:45: error: Cannot infer type of lambda
```

**Solution**: Add explicit type annotations to lambda parameters:
```python
# Instead of:
providers = {"anthropic": lambda: AnthropicProvider()}

# Use:
providers = {"anthropic": lambda: AnthropicProvider()}  # type: ignore
# Or better:
def create_anthropic_provider() -> BaseProvider:
    return AnthropicProvider()
providers = {"anthropic": create_anthropic_provider}
```

### "Incompatible return value type"

**Problem**:
```
atlas/agents/base.py:85: error: Incompatible return value type (got "None", expected "str")
```

**Solution**: Ensure all code paths return the expected type:
```python
def get_response(self, query: str) -> str:
    if not query:
        return ""  # Return empty string instead of None
    # Rest of function...
```

### "Item "None" of "Optional[Dict[str, Any]]" has no attribute"

**Problem**:
```
error: Item "None" of "Optional[Dict[str, Any]]" has no attribute "get"
```

**Solution**: Add explicit None check:
```python
def process_config(config: Optional[Dict[str, Any]]) -> str:
    if config is None:
        return "default"
    return config.get("name", "unknown")
```

### "Revealed type is ..."

**Problem**: Understanding inferred types

**Solution**: Use `reveal_type()` to debug:
```python
from typing import List, Dict, Any

def process_items(items: List[Dict[str, Any]]) -> None:
    for item in items:
        reveal_type(item)  # mypy will show the inferred type
```

Run with `mypy --show-error-codes` to see detailed information.

## Resources

### Official Documentation

- [mypy documentation](https://mypy.readthedocs.io/)
- [Python typing module](https://docs.python.org/3/library/typing.html)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [PEP 585 - Type Hinting Generics in Standard Collections](https://peps.python.org/pep-0585/)
- [PEP 593 - Flexible function and variable annotations](https://peps.python.org/pep-0593/)

### Cheat Sheets and Guides

- [mypy cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [Python Type Checking Guide](https://realpython.com/python-type-checking/)
- [Awesome Python Typing](https://github.com/typeddjango/awesome-python-typing) - Curated list of resources

### Advanced Topics

- [TypeVar and Generics](https://mypy.readthedocs.io/en/stable/generics.html)
- [TypedDict](https://mypy.readthedocs.io/en/stable/more_types.html#typeddict)
- [Stub files](https://mypy.readthedocs.io/en/stable/stubs.html)
- [Protocol types](https://mypy.readthedocs.io/en/stable/protocols.html)

## Contributing Type Improvements

When adding or improving type annotations in Atlas:

1. **Start with core modules**: Focus on public APIs and critical components
2. **Test changes**: Run `mypy` to verify your changes improve type coverage
3. **Update documentation**: Add or update docstrings with parameter and return types
4. **Consider gradual adoption**: Use `# type: ignore` with comments if necessary
5. **Create stub files**: For third-party libraries without type annotations

The goal is to improve type safety incrementally while maintaining code readability and functionality.