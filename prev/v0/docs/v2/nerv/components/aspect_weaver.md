---
title: AspectWeaver Implementation
---

---

title: Aspect Weaver

---


# AspectWeaver Implementation

## Overview

The AspectWeaver component implements the Aspect Orientation pattern in NERV, providing a centralized mechanism for managing cross-cutting concerns across Atlas components. It enables clean separation of core business logic from behaviors like logging, security, and performance monitoring.

## Architectural Role

The AspectWeaver serves as a key infrastructure component in Atlas:

- **Cross-Cutting Management**: Centralizes behaviors that span multiple components
- **Consistent Enforcement**: Ensures uniform application of system-wide policies
- **Dynamic Adaptation**: Applies aspects at runtime to modify system behavior
- **Clean Separation**: Isolates secondary concerns from primary business logic
- **Unified Configuration**: Provides a single control point for aspect management

## Implementation Details

### Library: AspectLib

AspectLib was chosen for the AspectWeaver implementation because it provides:

- **Python-native weaving**: Clean integration with Python's object model
- **Expressive pointcut language**: Precise targeting of join points
- **Multiple advice types**: Support for before, after, and around advice
- **Runtime weaving**: Ability to add aspects dynamically at runtime
- **Low overhead**: Minimal impact on method invocation performance

### Key Features

The AspectWeaver implementation includes:

1. **Centralized aspect registry** for managing all system aspects
2. **Dynamic aspect activation/deactivation** during runtime
3. **Aspect ordering control** for managing multiple aspects on the same join point
4. **Pointcut expression language** for declarative aspect targeting
5. **Aspect inheritance and composition** for reusing aspect definitions

### Core Data Types

```python
from typing import Dict, List, Any, Optional, Type, Callable, Set
from aspectl import Aspect, Pointcut, Advice, Weaver
from enum import Enum, auto
import threading

class AdviceType(Enum):
    """Types of advice supported by AspectWeaver."""
    BEFORE = auto()
    AFTER = auto()
    AFTER_RETURNING = auto()
    AFTER_THROWING = auto()
    AROUND = auto()

class AspectDefinition:
    """Definition of an aspect including its pointcut and advice."""
    def __init__(self, name: str, pointcut: str, advice_type: AdviceType,
                 advice_func: Callable, priority: int = 0):
        self.name = name
        self.pointcut = pointcut
        self.advice_type = advice_type
        self.advice_func = advice_func
        self.priority = priority

class AspectRegistry:
    """Registry managing all aspects in the system."""
    def __init__(self):
        self.aspects: Dict[str, AspectDefinition] = {}
        self.woven_targets: Dict[Type, Set[str]] = {}
        self.lock = threading.RLock()
```

### Implementation Structure

The AspectWeaver uses AspectLib's core capabilities while adding a more robust management layer:

```python
class AspectWeaver:
    """Central component for aspect-oriented programming in NERV."""

    def __init__(self):
        """Initialize the aspect weaver with empty registry."""
        self.registry = AspectRegistry()
        self.weaver = Weaver()
        self.enabled = True
        self._lock = threading.RLock()

    def register_aspect(self, aspect_def: AspectDefinition) -> str:
        """Register an aspect definition and return its ID."""
        # Implementation details...

    def apply_to_target(self, target: Type) -> None:
        """Apply all registered aspects to a target class."""
        # Implementation details...

    def remove_from_target(self, target: Type) -> None:
        """Remove all aspects from a target class."""
        # Implementation details...

    def enable_aspect(self, aspect_id: str) -> bool:
        """Enable a previously disabled aspect."""
        # Implementation details...

    def disable_aspect(self, aspect_id: str) -> bool:
        """Temporarily disable an aspect without removing it."""
        # Implementation details...
```

## Performance Considerations

AspectLib is designed for efficiency, but the AspectWeaver implementation adds several optimizations:

### Selective Weaving

The AspectWeaver applies aspects only to specifically targeted classes:

```python
# Selective aspect application for performance
def apply_to_target(self, target: Type) -> None:
    """Apply only relevant aspects to target class."""
    with self._lock:
        applicable_aspects = []

        # Find aspects applicable to this target
        for aspect_id, aspect_def in self.registry.aspects.items():
            if self._matches_target(aspect_def.pointcut, target):
                applicable_aspects.append((aspect_def.priority, aspect_id, aspect_def))

        # Sort by priority
        applicable_aspects.sort(reverse=True)

        # Apply aspects in priority order
        for _, aspect_id, aspect_def in applicable_aspects:
            self._apply_single_aspect(target, aspect_id, aspect_def)
```

### Pointcut Caching

The AspectWeaver caches pointcut evaluation results for improved performance:

```python
# Cache pointcut evaluation results
def _matches_target(self, pointcut: str, target: Type) -> bool:
    """Check if pointcut expression matches target, with caching."""
    cache_key = (pointcut, target.__qualname__)

    if cache_key in self._pointcut_cache:
        return self._pointcut_cache[cache_key]

    result = self._evaluate_pointcut(pointcut, target)
    self._pointcut_cache[cache_key] = result

    return result
```

### Tiered Aspect Strategy

The AspectWeaver uses different application strategies based on aspect priority:

```python
# Apply critical aspects through direct bytecode weaving
def _apply_critical_aspect(self, target: Type, aspect_def: AspectDefinition) -> None:
    """Apply performance-critical aspect through bytecode weaving."""
    # Use more efficient but less dynamic weaving approach

# Apply standard aspects through method wrapping
def _apply_standard_aspect(self, target: Type, aspect_def: AspectDefinition) -> None:
    """Apply standard aspect through method wrapping."""
    # Use standard method wrapping approach
```

### Thread Safety

The AspectWeaver ensures thread-safe operation with fine-grained locking:

```python
# Thread-safe aspect management
def register_aspect(self, aspect_def: AspectDefinition) -> str:
    """Register an aspect definition with thread safety."""
    aspect_id = str(uuid.uuid4())

    with self._lock:
        self.registry.aspects[aspect_id] = aspect_def

        # Apply to existing woven targets
        for target in self.registry.woven_targets:
            if self._matches_target(aspect_def.pointcut, target):
                self._apply_single_aspect(target, aspect_id, aspect_def)

    return aspect_id
```

## Integration Patterns

### Security Integration

```python
# Type definition only - not full implementation
class SecurityAspectProvider:
    """Creates security aspects for authorization enforcement."""

    def create_authorization_aspect(self, resource_type: str,
                                  permission: str) -> AspectDefinition:
        """Create aspect for permission checking."""
        pointcut = f"execution(* *.get_{resource_type}*(..))"

        def check_permission(join_point):
            """Check permission before allowing access."""
            user_context = get_current_user_context()
            if not user_context.has_permission(permission, resource_type):
                raise PermissionError(f"Permission denied: {permission}")

        return AspectDefinition(
            name=f"Authorization_{resource_type}_{permission}",
            pointcut=pointcut,
            advice_type=AdviceType.BEFORE,
            advice_func=check_permission,
            priority=100  # High priority for security checks
        )
```

### Logging Integration

```python
# Type definition only - not full implementation
class LoggingAspectProvider:
    """Creates logging aspects for different components."""

    def create_provider_logging_aspect(self) -> AspectDefinition:
        """Create aspect for provider operation logging."""
        pointcut = "execution(* Provider.*(..))"

        def log_provider_operation(join_point):
            """Log provider operation with parameters."""
            logger.info(
                f"Provider operation: {join_point.method_name}, "
                f"provider: {join_point.instance.__class__.__name__}, "
                f"args: {join_point.args}"
            )

        return AspectDefinition(
            name="ProviderLogging",
            pointcut=pointcut,
            advice_type=AdviceType.BEFORE,
            advice_func=log_provider_operation,
            priority=10  # Lower priority for logging
        )
```

### Metrics Integration

```python
# Type definition only - not full implementation
class MetricsAspectProvider:
    """Creates performance monitoring aspects."""

    def create_performance_monitoring_aspect(self,
                                          component_name: str) -> AspectDefinition:
        """Create aspect for performance monitoring."""
        pointcut = f"execution(* {component_name}.*(..))"

        def measure_performance(join_point):
            """Measure and record method execution time."""
            start_time = time.time()
            try:
                result = join_point.proceed()
                return result
            finally:
                duration = time.time() - start_time
                metrics.record(
                    f"{component_name}.{join_point.method_name}.duration",
                    duration
                )

        return AspectDefinition(
            name=f"PerformanceMonitoring_{component_name}",
            pointcut=pointcut,
            advice_type=AdviceType.AROUND,
            advice_func=measure_performance,
            priority=5  # Low priority for metrics
        )
```

## Usage Patterns

### Basic Aspect Registration

::: info Basic Usage with AspectLib
```python
# Create aspect weaver
aspect_weaver = AspectWeaver()

# Define and register logging aspect
logging_aspect = AspectDefinition(
    name="MethodLogging",
    pointcut="execution(* Provider.*(..))",
    advice_type=AdviceType.BEFORE,
    advice_func=lambda jp: logger.info(f"Calling {jp.method_name}")
)

aspect_id = aspect_weaver.register_aspect(logging_aspect)

# Apply to target class
aspect_weaver.apply_to_target(AnthropicProvider)
```
:::

### Component-Wide Aspects

::: tip Component Decoration
```python
# Apply aspects to all provider implementations
provider_classes = [
    AnthropicProvider,
    OpenAIProvider,
    OllamaProvider,
    MockProvider
]

# Create metrics aspect
metrics_aspect = MetricsAspectProvider().create_performance_monitoring_aspect(
    "Provider"
)

# Register aspect
aspect_id = aspect_weaver.register_aspect(metrics_aspect)

# Apply to all provider classes
for provider_class in provider_classes:
    aspect_weaver.apply_to_target(provider_class)
```
:::

### Dynamic Aspect Management

::: warning Conditional Aspects
```python
# Enable debug logging only in development environment
if env.is_development:
    # Create detailed logging aspect
    debug_aspect = AspectDefinition(
        name="DetailedLogging",
        pointcut="execution(* *.*(..))",
        advice_type=AdviceType.AROUND,
        advice_func=log_detailed_execution,
        priority=5
    )

    # Register and enable aspect
    debug_aspect_id = aspect_weaver.register_aspect(debug_aspect)
else:
    # Disable detailed logging in production
    aspect_weaver.disable_aspect(debug_aspect_id)
```
:::

## Performance Optimization

The AspectWeaver implementation includes several performance optimizations:

1. **Pointcut Caching**: Caching pointcut evaluation results
2. **Selective Application**: Only applying aspects to relevant targets
3. **Priority-Based Ordering**: Ensuring critical aspects execute first
4. **Granular Locking**: Using fine-grained locks for better concurrency
5. **Conditional Weaving**: Optional runtime checks before applying aspects

## Relationship to Patterns

Implements:
- **[Aspect Orientation](../patterns/aspect_orientation.md)**: Primary implementation

Supports:
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Can publish events for join points
- **[Effect System](../patterns/effect_system.md)**: Can convert operations to explicit effects
- **[Temporal Versioning](../patterns/temporal_versioning.md)**: Can trigger version creation at key points

## Implementation Reference

NERV's AspectWeaver implementation provides a comprehensive approach to cross-cutting concerns throughout the system architecture.
