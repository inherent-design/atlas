# Enhanced Provider System Implementation Plan

This document outlines the implementation plan for the Enhanced Provider System, focusing on the Provider Registry, Enhanced Capability System, and ProviderGroup components.

## Implementation Timeline

Estimated timeline: 2 weeks
- Week 1: Provider Registry, Capability System, ProviderGroup core implementation
- Week 2: Factory integration, CLI updates, examples, and documentation

## Implementation Tasks

### Phase 1: Provider Registry (Days 1-2)

#### 1.1 Core Data Structures
- [ ] Create `providers/registry.py`
- [ ] Implement provider-to-class mapping
- [ ] Implement provider-to-models mapping
- [ ] Implement model-to-provider mapping
- [ ] Implement model-to-capabilities mapping
- [ ] Implement capability-to-models mapping

#### 1.2 Registration Methods
- [ ] Implement `register_provider` method
- [ ] Implement `register_model_capability` method
- [ ] Add support for capability strength levels
- [ ] Add method chaining for fluent API

#### 1.3 Query Methods
- [ ] Implement `get_provider_for_model` method
- [ ] Implement `get_models_by_capability` with strength filtering
- [ ] Implement `get_models_for_provider` method
- [ ] Implement `get_capabilities_for_model` method
- [ ] Implement `find_provider_by_model` method
- [ ] Implement `find_models_with_capabilities` method

#### 1.4 Factory Methods
- [ ] Implement `create_provider` method
- [ ] Add support for capability-based provider creation
- [ ] Implement global registry instance

### Phase 2: Enhanced Capability System (Days 2-3)

#### 2.1 Capability Strength System
- [ ] Create `providers/capabilities.py`
- [ ] Implement `CapabilityStrength` enum with levels
- [ ] Add comparison operators for strength levels

#### 2.2 Capability Constants
- [ ] Define operational capabilities (inexpensive, efficient, premium)
- [ ] Define task capabilities (code, reasoning, creative, etc.)
- [ ] Define domain capabilities (science, finance, legal, etc.)
- [ ] Create `ALL_CAPABILITIES` set

#### 2.3 Task Capability Mapping
- [ ] Create `TASK_CAPABILITY_REQUIREMENTS` dictionary
- [ ] Map common tasks to capability requirements
- [ ] Add capability strength requirements for each task

#### 2.4 Helper Functions
- [ ] Implement `get_capabilities_for_task` function
- [ ] Create `detect_task_type_from_prompt` heuristic function
- [ ] Add utility functions for capability manipulation

### Phase 3: ProviderGroup (Days 3-5)

#### 3.1 Core Implementation
- [ ] Create `providers/group.py`
- [ ] Implement `ProviderGroup` class inheriting from `BaseProvider`
- [ ] Add constructor for multiple provider instances
- [ ] Implement required BaseProvider interface methods
- [ ] Create provider health tracking system
- [ ] Add context management for stateful strategies

#### 3.2 Selection Strategies
- [ ] Implement `ProviderSelectionStrategy` static class
- [ ] Create `failover` strategy (sequential provider usage)
- [ ] Create `round_robin` strategy (load balancing)
- [ ] Create `cost_optimized` strategy (cheapest provider first)
- [ ] Implement `TaskAwareSelectionStrategy` for capability-based selection

#### 3.3 Provider Operations
- [ ] Implement `generate` method with fallback between providers
- [ ] Implement `generate_stream` method with fallback
- [ ] Add provider health monitoring and recovery
- [ ] Implement retry logic for failed providers
- [ ] Add proper error handling and logging

### Phase 4: Factory Integration (Days 5-7)

#### 4.1 Factory Updates
- [ ] Update `factory.py` to use the registry
- [ ] Implement `create_provider_group` function
- [ ] Update provider creation to use registry
- [ ] Add task-aware provider creation
- [ ] Create model-based detection using registry

#### 4.2 Provider Options Updates
- [ ] Update `ProviderOptions` to support provider groups
- [ ] Add task type and capability requirements fields
- [ ] Add provider strategy field
- [ ] Maintain backward compatibility

#### 4.3 Base Provider Updates
- [ ] Add capability retrieval methods to `BaseProvider`
- [ ] Implement `get_capability_strength` method
- [ ] Add capability registration in provider constructors

### Phase 5: Agent System Updates (Days 7-8)

#### 5.1 Agent Updates
- [ ] Update `AtlasAgent` to accept provider instances directly
- [ ] Update provider initialization logic
- [ ] Add support for task-aware provider selection
- [ ] Maintain backward compatibility with string provider names

#### 5.2 Task-Aware Agent
- [ ] Create `TaskAwareAgent` class extending `AtlasAgent`
- [ ] Implement task type detection in query method
- [ ] Add dynamic provider selection based on task
- [ ] Create prompting strategies for different tasks

### Phase 6: CLI and Configuration (Days 8-9)

#### 6.1 CLI Arguments
- [ ] Update `parser.py` to add provider group options
- [ ] Add `--providers` argument for multiple providers
- [ ] Add `--provider-strategy` argument for selection strategies
- [ ] Add `--capabilities` argument for capability requirements
- [ ] Add `--task-type` argument for task-aware selection
- [ ] Create parser for capability format (name:strength)

#### 6.2 Configuration Integration
- [ ] Update `AtlasConfig` to support provider groups
- [ ] Add capability configuration options
- [ ] Add task type configuration option
- [ ] Update environment variables for new options

#### 6.3 Runtime Configuration
- [ ] Add dynamic configuration based on task detection
- [ ] Implement capability parsing from string format
- [ ] Create helper functions for CLI argument handling

### Phase 7: Documentation and Examples (Days 9-10)

#### 7.1 Provider Group Example
- [ ] Create `04_provider_group.py` example
- [ ] Show different selection strategies in action
- [ ] Demonstrate fallback behavior with simulated failures
- [ ] Add health monitoring demonstration

#### 7.2 Task-Aware Provider Example
- [ ] Create `05_task_aware_providers.py` example
- [ ] Demonstrate different task types with appropriate providers
- [ ] Show automatic task type detection
- [ ] Implement benchmark comparison between strategies

#### 7.3 Documentation
- [ ] Update API reference with new components
- [ ] Create provider registry architecture documentation
- [ ] Document capability system with examples
- [ ] Add provider group usage guide
- [ ] Create CLI reference for new options

## Dependency Graph

```
Provider Registry ──┬─────> Enhanced Capability System ─┬─> ProviderGroup
                    │                                   │
                    └─────> Factory Integration <───────┘
                                    │
                                    ▼
                             Agent Integration
                                    │
                                    ▼
                         CLI and Configuration
                                    │
                                    ▼
                        Examples and Documentation
```

## Testing Strategy

### Unit Tests
- Test Provider Registry with mock providers and capabilities
- Test Capability System with various task types
- Test ProviderGroup with mock providers and simulated failures
- Test Selection Strategies with different provider configurations

### Integration Tests
- Test Provider Registry with factory integration
- Test Capability System with Provider Registry
- Test ProviderGroup with real provider instances
- Test Agent with Provider Group

### End-to-End Tests
- Test CLI arguments with Provider Group
- Test Task-Aware selection with real queries
- Test fallback behavior with simulated provider failures

## Documentation Plan

1. **Update Architecture Documentation**
   - Add Enhanced Provider System overview
   - Document Provider Registry architecture
   - Explain Capability System and strength levels
   - Describe ProviderGroup and selection strategies

2. **Add New Component Documentation**
   - Create `docs/components/providers/registry.md`
   - Create `docs/components/providers/capabilities.md`
   - Create `docs/components/providers/provider_group.md`
   - Update `docs/components/providers/index.md`

3. **Update API Reference**
   - Document `ProviderRegistry` class and methods
   - Document `CapabilityStrength` enum and constants
   - Document `ProviderGroup` class and methods
   - Document `ProviderSelectionStrategy` classes

4. **Update CLI Reference**
   - Add Provider Group CLI options
   - Add Task-Aware selection options
   - Update example commands

5. **Create Example Documentation**
   - Document Provider Group example usage
   - Document Task-Aware provider selection
   - Add benchmark results for different strategies

## Implementation Code Example

### Provider Registry

```python
# atlas/providers/registry.py
from typing import Dict, List, Set, Optional, Union, Type, Any
from enum import IntEnum

from atlas.providers.base import BaseProvider
from atlas.providers.capabilities import CapabilityStrength

class ProviderRegistry:
    """Central registry for provider, model, and capability information."""
    
    def __init__(self):
        # Core data structures
        self._providers: Dict[str, Type[BaseProvider]] = {}  # name -> Provider class
        self._provider_models: Dict[str, List[str]] = {}  # provider_name -> list of models
        self._model_capabilities: Dict[str, Dict[str, CapabilityStrength]] = {}  # model_name -> {capability -> strength}
        self._capability_models: Dict[str, Set[str]] = {}  # capability -> set of models
        self._model_providers: Dict[str, str] = {}  # model_name -> provider_name
        
    def register_provider(self, name: str, provider_class: Type[BaseProvider], models: List[str] = None):
        """Register a provider and its supported models."""
        self._providers[name] = provider_class
        if models:
            self._provider_models[name] = models
            for model in models:
                self._model_providers[model] = name
                
        return self  # Enable chaining
    
    # Additional methods...
```

### ProviderGroup

```python
# atlas/providers/group.py
from typing import List, Dict, Any, Callable, Optional
import logging

from atlas.providers.base import BaseProvider
from atlas.providers.capabilities import get_capabilities_for_task, detect_task_type_from_prompt

logger = logging.getLogger(__name__)

class ProviderSelectionStrategy:
    """Strategy for selecting providers from a group."""
    
    @staticmethod
    def failover(providers: List[BaseProvider], context: Dict[str, Any] = None) -> List[BaseProvider]:
        """Returns providers in order, for failover purposes."""
        return providers
    
    # Additional strategies...

class ProviderGroup(BaseProvider):
    """A provider that encapsulates multiple providers with fallback capabilities."""
    
    def __init__(
        self,
        providers: List[BaseProvider],
        selection_strategy: Callable = ProviderSelectionStrategy.failover,
        name: str = "provider_group",
    ):
        """Initialize a provider group with a list of providers."""
        if not providers:
            raise ValueError("ProviderGroup requires at least one provider")
            
        self.providers = providers
        self.selection_strategy = selection_strategy
        self._name = name
        self._health_status = {provider: True for provider in providers}
        self._context = {}  # Context for selection strategy
    
    # Additional methods...
```

## Success Criteria

1. ✅ ProviderGroup successfully falls back between providers when one fails
2. ✅ Task-aware selection chooses appropriate providers for different tasks
3. ✅ All existing code continues to work with the Enhanced Provider System
4. ✅ Examples demonstrate different selection strategies and fallback behavior
5. ✅ Documentation is comprehensive and clear
6. ✅ All tests pass with good coverage
7. ✅ CLI arguments and configuration options work as expected