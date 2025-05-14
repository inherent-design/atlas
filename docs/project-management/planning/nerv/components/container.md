---
title: Container
---

# Container Implementation

## Overview

The Container component implements the Dependency Inversion pattern in NERV, providing a centralized registry for component management, dependency resolution, and lifecycle control. It enables clean separation between component interfaces and implementations, supporting flexible system composition.

## Architectural Role

The Container serves as a foundational infrastructure component in Atlas:

- **Component Registry**: Centralizes component creation and configuration
- **Dependency Resolution**: Automatically resolves and injects dependencies
- **Lifecycle Management**: Controls component creation, sharing, and disposal
- **Configuration Integration**: Binds configuration values to components
- **System Composition**: Enables flexible composition of system components

## Implementation Details

### Library: Dependency Injector

Dependency Injector was chosen for Container implementation because it provides:

- **Declarative container syntax**: Clean definitions of component registrations
- **Multiple provider types**: Support for different component lifecycles
- **Wiring capability**: Automatic dependency injection via type annotations
- **Hierarchical containers**: Support for modular container organization
- **Runtime configuration**: Dynamic configuration of container components

### Key Features

The Container implementation includes:

1. **Hierarchical component organization** for modular system design
2. **Multiple component lifecycles** (singleton, factory, resource)
3. **Dynamic component registration** at runtime
4. **Type-safe dependency resolution** with Python type hints
5. **Configuration integration** with environment variables and configuration files

### Core Data Types

```python
from typing import Dict, Any, Optional, Type, TypeVar, Generic, Callable
from dependency_injector import containers, providers
from enum import Enum, auto
import uuid

T = TypeVar('T')  # Component type

class ComponentScope(Enum):
    """Lifecycle scopes for components."""
    SINGLETON = auto()  # Single instance for entire container
    SCOPED = auto()     # Single instance per defined scope
    TRANSIENT = auto()  # New instance per resolution
    RESOURCE = auto()   # Managed lifecycle with cleanup

class ComponentRegistration(Generic[T]):
    """Registration information for container components."""
    def __init__(self, component_type: Type[T], provider: providers.Provider,
                 scope: ComponentScope, id: str = None):
        self.component_type = component_type
        self.provider = provider
        self.scope = scope
        self.id = id or str(uuid.uuid4())
```

### Implementation Structure

The Container implementation builds on Dependency Injector's container system:

```python
class Container(containers.DeclarativeContainer):
    """Core container implementation for the NERV architecture."""
    
    # Configuration provider
    config = providers.Configuration()
    
    # Core system components
    event_bus = providers.Singleton(EventBus)
    temporal_store = providers.Singleton(TemporalStore)
    state_projector = providers.Singleton(
        StateProjector,
        initial_state=providers.Dict()
    )
    
    # Factory provider for creating provider instances
    provider_factory = providers.FactoryAggregate({
        "anthropic": providers.Factory(
            AnthropicProvider,
            api_key=config.providers.anthropic.api_key
        ),
        "openai": providers.Factory(
            OpenAIProvider,
            api_key=config.providers.openai.api_key
        ),
        "ollama": providers.Factory(
            OllamaProvider,
            base_url=config.providers.ollama.base_url
        ),
        "mock": providers.Factory(MockProvider)
    })
    
    # Dynamic component registry
    def register_component(self, name: str, component_type: Type[T], 
                          provider_type: ComponentScope = ComponentScope.SINGLETON,
                          **dependencies) -> providers.Provider:
        """Register a component at runtime."""
        # Implementation details...
        pass
```

## Performance Considerations

Dependency Injector is designed for efficiency, but the Container implementation adds several optimizations:

### Provider Resolution Caching

The Container caches resolved providers for faster dependency resolution:

```python
# Cached provider resolution
def _get_cached_provider(self, provider_name: str) -> providers.Provider:
    """Get provider with caching for better performance."""
    if provider_name in self._provider_cache:
        return self._provider_cache[provider_name]
    
    provider = getattr(self, provider_name, None)
    if provider:
        self._provider_cache[provider_name] = provider
    
    return provider
```

### Lazy Initialization

The Container uses lazy initialization to defer resource-intensive component creation:

```python
# Lazy initialization for expensive components
database = providers.Singleton(
    Database,
    connection_string=config.database.connection_string,
    # Only created when actually used
    init_on_access=True
)
```

### Selective Wiring

The Container implements selective wiring to minimize dependency resolution overhead:

```python
# Selective wiring for better performance
def wire_components(self, modules: List[str], packages: List[str] = None) -> None:
    """Wire dependency injection selectively to specific modules."""
    from dependency_injector.wiring import wire
    
    # Only wire specified modules
    for module_name in modules:
        module = importlib.import_module(module_name)
        wire(module, packages=packages, container=self)
```

### Resource Management

The Container includes proper resource management for components requiring cleanup:

```python
# Proper resource handling
database_connection = providers.Resource(
    DatabaseConnection,
    connection_string=config.database.connection_string,
    # Ensure connections are properly closed
    shutdown_resource=lambda conn: conn.close()
)
```

## Integration Patterns

### Event Bus Integration

```python
# Type definition only - not full implementation
class EventComponents(containers.DeclarativeContainer):
    """Container for event-driven components."""
    
    # Container configuration
    config = providers.Configuration()
    
    # Core event bus
    event_bus = providers.Singleton(EventBus)
    
    # Event listeners container
    class Listeners(containers.DeclarativeContainer):
        """Nested container for event listeners."""
        
        # Parent reference
        event_bus = providers.Dependency()
        
        # Provider listeners
        provider_listener = providers.Singleton(
            ProviderEventListener,
            event_bus=event_bus
        )
        
        # Knowledge listeners
        knowledge_listener = providers.Singleton(
            KnowledgeEventListener,
            event_bus=event_bus
        )
    
    # Initialize listeners container with reference to event bus
    listeners = providers.Container(
        Listeners,
        event_bus=event_bus
    )
```

### Provider Integration

```python
# Type definition only - not full implementation
class ProviderComponents(containers.DeclarativeContainer):
    """Container for provider components."""
    
    # Container configuration
    config = providers.Configuration()
    
    # External dependencies
    event_bus = providers.Dependency()
    
    # Provider factory with dynamic model selection
    provider_factory = providers.FactoryAggregate({
        "anthropic": providers.Factory(
            lambda model_name, **kwargs: AnthropicProvider(
                model_name=model_name,
                api_key=config.providers.anthropic.api_key,
                **kwargs
            )
        ),
        "openai": providers.Factory(
            lambda model_name, **kwargs: OpenAIProvider(
                model_name=model_name,
                api_key=config.providers.openai.api_key,
                **kwargs
            )
        )
    })
    
    # Provider registry with event integration
    provider_registry = providers.Singleton(
        ProviderRegistry,
        event_bus=event_bus,
        provider_factory=provider_factory
    )
```

### Effect System Integration

```python
# Type definition only - not full implementation
class EffectComponents(containers.DeclarativeContainer):
    """Container for effect system components."""
    
    # Container configuration
    config = providers.Configuration()
    
    # Effect handler with modular registration
    effect_handler = providers.Singleton(
        EffectHandler
    )
    
    # Handler factory methods
    handler_factory = providers.FactoryAggregate({
        "network": providers.Factory(
            NetworkEffectHandler,
            timeout=config.effects.network.timeout
        ),
        "database": providers.Factory(
            DatabaseEffectHandler,
            connection_pool=providers.Dependency()
        ),
        "file": providers.Factory(
            FileEffectHandler,
            base_path=config.effects.file.base_path
        )
    })
    
    # Initialize effect handler with registered handlers
    @providers.init
    def initialize_handlers(self):
        """Register effect handlers with effect handler."""
        self.effect_handler().register_handler(
            EffectType.NETWORK,
            self.handler_factory("network")
        )
        self.effect_handler().register_handler(
            EffectType.DATABASE,
            self.handler_factory("database", connection_pool=self.database_pool())
        )
        self.effect_handler().register_handler(
            EffectType.FILE,
            self.handler_factory("file")
        )
```

## Usage Patterns

### Basic Container Configuration

::: info Basic Configuration
```python
# Create main container
container = Container()

# Configure from environment and config file
container.config.from_dict({
    "providers": {
        "anthropic": {
            "api_key": os.environ.get("ANTHROPIC_API_KEY")
        },
        "openai": {
            "api_key": os.environ.get("OPENAI_API_KEY")
        }
    },
    "database": {
        "connection_string": "sqlite:///atlas.db"
    }
})

# Wire dependency injection to modules
container.wire(modules=["atlas.agent", "atlas.knowledge"])
```
:::

### Hierarchical Containers

::: tip Modular Container Organization
```python
# Create composite container structure
class AtlasContainer(containers.DeclarativeContainer):
    """Main Atlas container with hierarchical organization."""
    
    # Configuration
    config = providers.Configuration()
    
    # Core components
    core = providers.Container(CoreComponents, config=config)
    
    # Provider components
    providers = providers.Container(
        ProviderComponents,
        config=config.providers,
        event_bus=core.event_bus
    )
    
    # Agent components
    agents = providers.Container(
        AgentComponents,
        config=config.agents,
        event_bus=core.event_bus,
        provider_registry=providers.provider_registry
    )
    
    # Knowledge components
    knowledge = providers.Container(
        KnowledgeComponents,
        config=config.knowledge,
        event_bus=core.event_bus
    )
```
:::

### Dynamic Component Registration

::: warning Runtime Registration
```python
# Register component at runtime based on configuration
def register_custom_provider(container, provider_name, provider_class):
    """Register custom provider implementation dynamically."""
    # Create provider factory
    provider_factory = providers.Factory(
        provider_class,
        api_key=container.config.providers[provider_name].api_key
    )
    
    # Register in container
    container.providers.provider_factory.providers.update({
        provider_name: provider_factory
    })
    
    # Register with provider registry
    container.providers.provider_registry().register_provider(
        provider_name, provider_factory
    )
```
:::

## Performance Optimization

The Container implementation includes several performance optimizations:

1. **Provider Caching**: Caching provider instances for faster resolution
2. **Selective Initialization**: Only initializing components when needed
3. **Scoped Resolution**: Using appropriate lifecycle scopes for components
4. **Minimal Wiring**: Wiring only specific modules rather than entire packages
5. **Nested Containers**: Using hierarchical containers for better modularity

## Relationship to Patterns

Implements:
- **[Dependency Inversion](../patterns/dependency_inversion.md)**: Primary implementation

Supports:
- **[Reactive Event Mesh](../patterns/reactive_event_mesh.md)**: Manages event bus and listener components
- **[Effect System](../patterns/effect_system.md)**: Configures effect handlers and their dependencies
- **[Temporal Versioning](../patterns/temporal_versioning.md)**: Manages versioned components and their dependencies

## Implementation Reference

NERV's Container implementation provides a robust dependency management framework that serves as a foundation for the entire system architecture.