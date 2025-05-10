# Atlas Implementation Planning

This document provides a comprehensive implementation plan based on the current status audit and priorities for the Atlas project.

## Implementation Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Core Architecture | 🚧 In Progress | Provider system redesign partially implemented |
| Provider System | ✅ Good Progress | Options, resolver, factory implemented |
| Knowledge System | ⚠️ Lagging | Basic retrieval working, advanced features pending |
| Agent System | ⚠️ Blocked | Tool agent updates needed for provider options |
| CLI System | ✅ Implemented | Config and parser modules working |
| Example System | 🔄 Partially Complete | Basic examples working, advanced examples blocked |

## Current Implementation Focus: Enhanced Provider System

The current implementation priority is the Enhanced Provider System which includes three key components:

1. **Provider Registry** - A central registry for provider, model, and capability data
2. **Enhanced Capability System** - An expanded set of capabilities for task-aware model selection
3. **ProviderGroup** - A provider implementation that supports multiple providers with various selection strategies

This enhanced system will enable not only resilience through provider fallback but also intelligent, task-aware model selection based on capability requirements.

### Provider Registry Architecture

The Provider Registry will serve as a central database for all provider, model, and capability relationships, replacing the current scattered approach to provider and model detection.

```
ProviderRegistry
    |
    ├── Providers ──────┐
    |   └── Provider    |
    |       └── Models  |
    |           └── Capabilities
    |               └── Strengths
    |
    ├── Models ────────┘
    |   └── Provider
    |   └── Capabilities
    |       └── Strengths
    |
    └── Capabilities
        └── Models
            └── Strengths
```

Key advantages of this approach:
- Centralized management of provider-model-capability relationships
- Explicit modeling of these relationships instead of implicit detection
- Support for capability strength levels
- Extensible to add new relationship types
- Enables more sophisticated model selection strategies

### Enhanced Capability System

The current capability system will be significantly expanded to cover both operational and task-specific capabilities:

#### Operational Capabilities
- `inexpensive` - Lower cost models
- `efficient` - Fast response time
- `premium` - Highest quality models
- `vision` - Image understanding

#### Task Capabilities
- `code` - Code generation and understanding
- `reasoning` - Logical reasoning and problem-solving
- `creative` - Creative writing and ideation
- `extraction` - Data extraction from documents
- `math` - Mathematical reasoning and calculation
- `multimedia` - Handling multiple media types
- `structured` - Structured output generation (JSON, etc.)
- `chat` - Conversational abilities

#### Domain Capabilities
- `science` - Scientific domain knowledge
- `finance` - Financial domain knowledge
- `legal` - Legal domain knowledge
- `medical` - Medical domain knowledge

#### Capability Strength Levels
- `basic` (1) - Has the capability but limited
- `moderate` (2) - Average capability
- `strong` (3) - Excellent at this capability
- `exceptional` (4) - Best-in-class for this capability

This enhanced capability system will enable much more nuanced model selection based on task requirements.

### ProviderGroup Architecture

The ProviderGroup will implement the same interface as individual providers (BaseProvider), allowing seamless integration with existing components. It will contain multiple provider instances and use a strategy pattern to determine which provider to use for each request.

```
BaseProvider
    ^
    |
ProviderGroup  ----->  ProviderSelectionStrategy
    |                          |
    v                          v
[Provider1, Provider2, ...]   [Failover, RoundRobin, CostOptimized]
```

### ProviderGroup Components

1. **ProviderGroup Class**
   - Implements the BaseProvider interface
   - Contains a list of provider instances
   - Uses a selection strategy to choose providers
   - Tracks provider health status
   - Implements automatic retry with different providers

2. **ProviderSelectionStrategy Class**
   - Abstract strategy pattern for provider selection
   - Implementations:
     - Failover: Try providers in sequence until one works
     - RoundRobin: Rotate through available providers
     - CostOptimized: Select providers based on estimated cost

3. **Factory Integration**
   - Update factory to support creating provider groups
   - Add utilities for provider group configuration
   - Support auto-detection of providers from models

4. **CLI and Configuration Integration**
   - Add CLI arguments for provider group configuration
   - Update configuration system to support provider groups
   - Create documentation for provider group usage

### ProviderGroup Implementation Steps

#### Step 1: Create ProviderGroup and Strategy Classes

1. Create `atlas/providers/group.py` with:
   - ProviderSelectionStrategy abstract class
   - Concrete strategy implementations
   - ProviderGroup class implementing BaseProvider

2. Core functionality:
   - Initialize with multiple providers
   - Select provider using strategy
   - Health monitoring for providers
   - Automatic retry with different providers
   - Fallback mechanisms for all operations

#### Step 2: Update Factory and Environment Handling

1. Update `atlas/providers/factory.py` to:
   - Add `create_provider_group` function
   - Support provider group creation from options
   - Add utilities for provider auto-detection

2. Update `atlas/core/env.py` to:
   - Add environment variables for provider groups
   - Add helper functions for provider group configuration

#### Step 3: Update AtlasAgent and Configuration

1. Update `atlas/agent.py` to:
   - Accept provider instances directly
   - Support provider group configuration
   - Maintain backward compatibility

2. Update `atlas/core/config.py` to:
   - Add provider group configuration options
   - Support multiple provider specifications
   - Add provider selection strategy options

#### Step 4: Update CLI Interface

1. Update `atlas/cli/parser.py` to:
   - Add `--providers` argument for multiple providers
   - Add `--provider-strategy` argument for selection strategy
   - Update help text and documentation

2. Update `atlas/cli/config.py` to:
   - Process new CLI arguments
   - Configure provider groups from arguments
   - Maintain compatibility with existing options

#### Step 5: Create Example and Documentation

1. Create `examples/04_provider_group.py` demonstrating:
   - Provider group creation and configuration
   - Different selection strategies
   - Automatic fallback between providers
   - Health monitoring and recovery

2. Update documentation:
   - Add provider group usage guide
   - Update API reference documentation
   - Add provider selection strategy documentation

### ProviderGroup Implementation Timeline

1. **Day 1-2**: Create ProviderGroup and strategy classes
2. **Day 3**: Update factory and environment handling
3. **Day 4**: Update AtlasAgent and configuration
4. **Day 5**: Update CLI interface
5. **Day 6-7**: Create example and documentation

### Enhanced Provider System Code Sketches

#### Provider Registry

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

    def register_model_capability(self, model: str, capability: str,
                                 strength: CapabilityStrength = CapabilityStrength.MODERATE):
        """Register a capability for a model with optional strength."""
        if model not in self._model_capabilities:
            self._model_capabilities[model] = {}
        self._model_capabilities[model][capability] = strength

        if capability not in self._capability_models:
            self._capability_models[capability] = set()
        self._capability_models[capability].add(model)

        return self  # Enable chaining

    def get_provider_for_model(self, model: str) -> Optional[str]:
        """Get provider that supports the given model."""
        return self._model_providers.get(model)

    def get_models_by_capability(self, capability: str,
                                min_strength: CapabilityStrength = CapabilityStrength.BASIC) -> Set[str]:
        """Get all models with the specified capability at minimum strength."""
        if capability not in self._capability_models:
            return set()

        models = set()
        for model in self._capability_models[capability]:
            if self._model_capabilities[model][capability] >= min_strength:
                models.add(model)

        return models

    def get_models_for_provider(self, provider: str) -> List[str]:
        """Get all models supported by the provider."""
        return self._provider_models.get(provider, [])

    def get_capabilities_for_model(self, model: str) -> Dict[str, CapabilityStrength]:
        """Get all capabilities of a model with their strengths."""
        return self._model_capabilities.get(model, {})

    def create_provider(self, provider_name: str, **kwargs) -> BaseProvider:
        """Create a provider instance."""
        provider_class = self._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class(**kwargs)

    def find_provider_by_model(self, model_name: str) -> Optional[Type[BaseProvider]]:
        """Find a provider class that supports the given model."""
        provider_name = self._model_providers.get(model_name)
        if not provider_name:
            return None
        return self._providers.get(provider_name)

    def find_models_with_capabilities(self,
                                    capabilities: Dict[str, CapabilityStrength]) -> Dict[str, List[str]]:
        """Find models that have all the specified capabilities at minimum strengths."""
        if not capabilities:
            return {}

        # Start with all models
        result_models = set(self._model_providers.keys())

        # Filter by capabilities and strengths
        for capability, min_strength in capabilities.items():
            qualified_models = set()
            for model in result_models:
                model_caps = self._model_capabilities.get(model, {})
                if capability in model_caps and model_caps[capability] >= min_strength:
                    qualified_models.add(model)

            result_models = qualified_models
            if not result_models:
                return {}  # No models match all criteria

        # Group by provider
        result = {}
        for model in result_models:
            provider = self._model_providers.get(model)
            if provider not in result:
                result[provider] = []
            result[provider].append(model)

        return result

    def get_all_providers(self) -> List[str]:
        """Get all registered provider names."""
        return list(self._providers.keys())

    def get_all_models(self) -> List[str]:
        """Get all registered model names."""
        return list(self._model_providers.keys())

    def get_all_capabilities(self) -> List[str]:
        """Get all registered capabilities."""
        return list(self._capability_models.keys())


# Global registry instance
registry = ProviderRegistry()
```

#### Capability System

```python
# atlas/providers/capabilities.py
from enum import IntEnum
from typing import Dict, Set, List, Optional

class CapabilityStrength(IntEnum):
    """Enumeration of capability strength levels."""
    BASIC = 1
    MODERATE = 2
    STRONG = 3
    EXCEPTIONAL = 4


# Operational capabilities
CAPABILITY_INEXPENSIVE = "inexpensive"  # Lower cost models
CAPABILITY_EFFICIENT = "efficient"      # Fast response time
CAPABILITY_PREMIUM = "premium"          # Highest quality models
CAPABILITY_VISION = "vision"            # Image understanding

# Task capabilities
CAPABILITY_CODE = "code"                # Code generation and understanding
CAPABILITY_REASONING = "reasoning"      # Logical reasoning and problem-solving
CAPABILITY_CREATIVE = "creative"        # Creative writing and ideation
CAPABILITY_EXTRACTION = "extraction"    # Data extraction from documents
CAPABILITY_MATH = "math"                # Mathematical reasoning and calculation
CAPABILITY_MULTIMEDIA = "multimedia"    # Handling multiple media types
CAPABILITY_STRUCTURED = "structured"    # Structured output generation (JSON, etc.)
CAPABILITY_CHAT = "chat"                # Conversational abilities

# Domain capabilities
CAPABILITY_DOMAIN_SCIENCE = "science"   # Scientific domain knowledge
CAPABILITY_DOMAIN_FINANCE = "finance"   # Financial domain knowledge
CAPABILITY_DOMAIN_LEGAL = "legal"       # Legal domain knowledge
CAPABILITY_DOMAIN_MEDICAL = "medical"   # Medical domain knowledge

# All capabilities
ALL_CAPABILITIES = {
    # Operational
    CAPABILITY_INEXPENSIVE,
    CAPABILITY_EFFICIENT,
    CAPABILITY_PREMIUM,
    CAPABILITY_VISION,

    # Task
    CAPABILITY_CODE,
    CAPABILITY_REASONING,
    CAPABILITY_CREATIVE,
    CAPABILITY_EXTRACTION,
    CAPABILITY_MATH,
    CAPABILITY_MULTIMEDIA,
    CAPABILITY_STRUCTURED,
    CAPABILITY_CHAT,

    # Domain
    CAPABILITY_DOMAIN_SCIENCE,
    CAPABILITY_DOMAIN_FINANCE,
    CAPABILITY_DOMAIN_LEGAL,
    CAPABILITY_DOMAIN_MEDICAL
}

# Task requirements mapping
TASK_CAPABILITY_REQUIREMENTS = {
    "code_generation": {
        CAPABILITY_CODE: CapabilityStrength.STRONG,
        CAPABILITY_REASONING: CapabilityStrength.MODERATE
    },
    "creative_writing": {
        CAPABILITY_CREATIVE: CapabilityStrength.STRONG,
        CAPABILITY_CHAT: CapabilityStrength.MODERATE
    },
    "data_analysis": {
        CAPABILITY_STRUCTURED: CapabilityStrength.MODERATE,
        CAPABILITY_REASONING: CapabilityStrength.STRONG,
        CAPABILITY_MATH: CapabilityStrength.MODERATE
    },
    "document_extraction": {
        CAPABILITY_EXTRACTION: CapabilityStrength.STRONG,
        CAPABILITY_STRUCTURED: CapabilityStrength.MODERATE
    },
    "mathematical_problem_solving": {
        CAPABILITY_MATH: CapabilityStrength.STRONG,
        CAPABILITY_REASONING: CapabilityStrength.STRONG
    },
    "conversational": {
        CAPABILITY_CHAT: CapabilityStrength.STRONG
    },
    "visual_analysis": {
        CAPABILITY_VISION: CapabilityStrength.STRONG,
        CAPABILITY_REASONING: CapabilityStrength.MODERATE
    }
}

def get_capabilities_for_task(task_type: str) -> Dict[str, CapabilityStrength]:
    """Get the capability requirements for a specific task type."""
    return TASK_CAPABILITY_REQUIREMENTS.get(task_type, {})

def detect_task_type_from_prompt(prompt: str) -> str:
    """Attempt to detect the task type from a prompt.

    This is a simple heuristic-based approach. In production, this could
    be replaced with a more sophisticated ML-based classifier.
    """
    prompt_lower = prompt.lower()

    # Simple keyword-based heuristics
    if any(kw in prompt_lower for kw in ["code", "function", "program", "algorithm", "implement"]):
        return "code_generation"
    elif any(kw in prompt_lower for kw in ["creative", "write", "story", "poem", "essay"]):
        return "creative_writing"
    elif any(kw in prompt_lower for kw in ["analyze", "data", "statistics", "trends", "numbers"]):
        return "data_analysis"
    elif any(kw in prompt_lower for kw in ["extract", "document", "find information", "get data from"]):
        return "document_extraction"
    elif any(kw in prompt_lower for kw in ["math", "calculate", "solve", "equation"]):
        return "mathematical_problem_solving"
    elif any(kw in prompt_lower for kw in ["image", "picture", "photo", "visual", "look at"]):
        return "visual_analysis"
    else:
        return "conversational"  # Default task type
```

#### Task-Aware Selection Strategy

```python
# Provider selection strategy for task-aware provider selection
class TaskAwareSelectionStrategy:
    """Selects models based on task requirements and capability strengths."""

    @staticmethod
    def select(providers, context=None):
        """Select providers optimized for specific task types.

        Args:
            providers: List of provider instances
            context: Dictionary containing at least 'task_type' or 'prompt'

        Returns:
            Ordered list of providers
        """
        if not providers:
            return []

        if not context:
            # Fallback to default ordering if no context
            return providers

        # Get task type from context
        task_type = context.get("task_type")
        if not task_type and "prompt" in context:
            # Try to detect task type from prompt
            task_type = detect_task_type_from_prompt(context["prompt"])

        if not task_type:
            # No task type available, use default ordering
            return providers

        # Get required capabilities for this task
        required_capabilities = get_capabilities_for_task(task_type)

        if not required_capabilities:
            # No specific requirements, use default ordering
            return providers

        # Score each provider based on capability match
        scored_providers = []
        for provider in providers:
            # Calculate average capability match score
            total_score = 0
            matches = 0

            for capability, min_strength in required_capabilities.items():
                provider_strength = provider.get_capability_strength(capability)
                if provider_strength >= min_strength:
                    # Provider meets minimum requirement
                    total_score += provider_strength / min_strength  # Relative score
                    matches += 1

            # Only include providers with some capability match
            if matches > 0:
                avg_score = total_score / len(required_capabilities)
                scored_providers.append((provider, avg_score))

        # Sort by score (highest first)
        return [p for p, s in sorted(scored_providers, key=lambda x: x[1], reverse=True)] or providers
```

#### Example Usage

CLI usage example:

```bash
# Basic provider group with failover strategy
uv run python main.py query --providers ollama openai anthropic --provider-strategy failover -q "What is the capital of France?"

# Use task-aware strategy with capabilities
uv run python main.py query --task-type code_generation --capabilities code:strong reasoning:moderate -q "Write a function to calculate Fibonacci numbers"

# Use cost-optimized strategy (tries cheaper providers first)
uv run python main.py query --providers mock ollama openai anthropic --provider-strategy cost_optimized -q "What is the capital of France?"

# Use round-robin strategy to distribute load across providers
uv run python main.py query --providers openai anthropic --provider-strategy round_robin -q "What is the capital of France?"
```

Python API usage example:

```python
from atlas.providers.factory import create_provider, create_provider_group
from atlas.providers.options import ProviderOptions
from atlas.providers.capabilities import CapabilityStrength
from atlas.providers.registry import registry

# Register provider capabilities (done once at application startup)
registry.register_provider("anthropic", AnthropicProvider, models=["claude-3-opus-20240229", "claude-3-sonnet-20240229"])
registry.register_model_capability("claude-3-opus-20240229", "reasoning", CapabilityStrength.EXCEPTIONAL)
registry.register_model_capability("claude-3-opus-20240229", "code", CapabilityStrength.STRONG)

registry.register_provider("openai", OpenAIProvider, models=["gpt-4", "gpt-3.5-turbo"])
registry.register_model_capability("gpt-4", "code", CapabilityStrength.EXCEPTIONAL)
registry.register_model_capability("gpt-4", "reasoning", CapabilityStrength.STRONG)

# Basic provider group with failover strategy
provider_group = create_provider_group(
    providers=["ollama", "openai", "anthropic"],
    strategy="failover",
    options=ProviderOptions(max_tokens=200)
)

# Task-aware provider selection
task_provider = create_provider(
    capabilities={
        "code": CapabilityStrength.STRONG,
        "reasoning": CapabilityStrength.MODERATE
    },
    task_type="code_generation"
)

# Use the provider group like any other provider
response = provider_group.generate({"prompt": "What is the capital of France?"})
print(response.text)

# Use task-aware provider for code generation
code_response = task_provider.generate({
    "prompt": "Write a function to calculate the factorial of a number"
})
print(code_response.text)
```

Example implementation of the task-aware agent:

```python
from atlas.providers.registry import registry
from atlas.providers.capabilities import get_capabilities_for_task, detect_task_type_from_prompt
from atlas.agent import AtlasAgent

class TaskAwareAgent(AtlasAgent):
    """An agent that automatically selects the best provider for the task."""

    def __init__(self, available_providers=None, **kwargs):
        """Initialize with available providers.

        Args:
            available_providers: List of provider names to consider, or None for all
            **kwargs: Other AtlasAgent parameters
        """
        self.available_providers = available_providers or registry.get_all_providers()
        super().__init__(**kwargs)

    def query(self, prompt, **kwargs):
        """Override query to perform task-aware provider selection."""
        # Detect task type from prompt
        task_type = kwargs.get("task_type") or detect_task_type_from_prompt(prompt)

        # Get capability requirements for this task
        capabilities = get_capabilities_for_task(task_type)

        # Find appropriate models for these capabilities
        models_by_provider = registry.find_models_with_capabilities(capabilities)

        if not models_by_provider:
            # No perfect match, fall back to default
            return super().query(prompt, **kwargs)

        # Get the best provider and model
        best_provider = next(iter(models_by_provider.keys()))
        best_model = models_by_provider[best_provider][0]

        # Create provider instance
        provider = registry.create_provider(
            best_provider,
            model_name=best_model
        )

        # Set provider for this query and execute
        self._provider = provider
        return super().query(prompt, **kwargs)
```

#### ProviderSelectionStrategy Class

```python
class ProviderSelectionStrategy:
    """Strategy for selecting providers from a group."""

    @staticmethod
    def failover(providers: List[BaseProvider], context: Dict[str, Any] = None) -> List[BaseProvider]:
        """Returns providers in order, for failover purposes."""
        # Simple implementation - just return providers in the original order
        # This is ideal for reliability as it tries the most reliable provider first
        return providers

    @staticmethod
    def round_robin(providers: List[BaseProvider], context: Dict[str, Any] = None) -> List[BaseProvider]:
        """Rotates through providers in sequence."""
        # Use context to track the last provider used and rotate
        if not context or "last_index" not in context:
            last_index = 0
        else:
            last_index = context.get("last_index", 0)

        # Rotate and update for next call
        rotated = providers[last_index:] + providers[:last_index]

        # Update context for next call (if mutable)
        if context is not None:
            next_index = (last_index + 1) % len(providers)
            context["last_index"] = next_index

        return rotated

    @staticmethod
    def cost_optimized(providers: List[BaseProvider], context: Dict[str, Any] = None) -> List[BaseProvider]:
        """Sorts providers by estimated cost."""
        # For a simple implementation, use a hard-coded cost hierarchy
        # In a real implementation, this would use a cost model based on actual prices
        def get_cost_rank(provider: BaseProvider) -> int:
            cost_ranks = {
                "mock": 0,      # Lowest cost (free)
                "ollama": 1,    # Low cost (local)
                "openai": 2,    # Medium cost
                "anthropic": 3, # Higher cost
            }
            return cost_ranks.get(provider.name.lower(), 99)

        # Sort by cost rank (lowest first)
        return sorted(providers, key=get_cost_rank)
```

#### ProviderGroup Class

```python
class ProviderGroup(BaseProvider):
    """A provider that encapsulates multiple providers with fallback capabilities."""

    def __init__(
        self,
        providers: List[BaseProvider],
        selection_strategy: Callable = ProviderSelectionStrategy.failover,
        name: str = "provider_group",
    ):
        """Initialize a provider group with a list of providers.

        Args:
            providers: A list of provider instances to use
            selection_strategy: A function that determines the order to try providers
            name: A name for this provider group
        """
        if not providers:
            raise ValueError("ProviderGroup requires at least one provider")

        self.providers = providers
        self.selection_strategy = selection_strategy
        self._name = name
        self._health_status = {provider: True for provider in providers}
        self._context = {}  # Context for selection strategy

    @property
    def name(self) -> str:
        return self._name

    def get_available_models(self) -> List[str]:
        """Get all available models across all healthy providers."""
        models = []
        for provider in self.providers:
            if self._health_status[provider]:
                try:
                    models.extend(provider.get_available_models())
                except Exception as e:
                    # Log the error
                    logger.warning(f"Provider {provider.name} failed to get models: {str(e)}")
                    self._health_status[provider] = False
        return list(set(models))

    def generate(self, request):
        """Generate a response using providers according to the selection strategy."""
        ordered_providers = self.selection_strategy(
            [p for p in self.providers if self._health_status[p]],
            context=self._context
        )

        if not ordered_providers:
            raise Exception("No healthy providers available")

        last_error = None
        for provider in ordered_providers:
            try:
                return provider.generate(request)
            except Exception as e:
                # Log the error
                logger.warning(f"Provider {provider.name} failed to generate: {str(e)}")
                last_error = e
                # Mark provider as unhealthy
                self._health_status[provider] = False
                # Continue to next provider
                continue

        # If we get here, all providers failed
        raise Exception(f"All providers failed to generate. Last error: {last_error}")

    def generate_stream(self, request):
        """Stream a response using providers according to the selection strategy."""
        ordered_providers = self.selection_strategy(
            [p for p in self.providers if self._health_status[p]],
            context=self._context
        )

        if not ordered_providers:
            raise Exception("No healthy providers available")

        last_error = None
        for provider in ordered_providers:
            try:
                return provider.generate_stream(request)
            except Exception as e:
                # Log the error
                logger.warning(f"Provider {provider.name} failed to stream: {str(e)}")
                last_error = e
                # Mark provider as unhealthy
                self._health_status[provider] = False
                # Continue to next provider
                continue

        # If we get here, all providers failed
        raise Exception(f"All providers failed to stream. Last error: {last_error}")

    def validate_api_key(self) -> bool:
        """Check if at least one provider has a valid API key."""
        # We only need one valid provider to function
        for provider in self.providers:
            try:
                if provider.validate_api_key():
                    return True
            except Exception:
                # If validation fails, continue to the next provider
                continue
        return False

    def _reset_health_status(self):
        """Reset health status for all providers.

        This is useful to periodically try providers that previously failed.
        """
        self._health_status = {provider: True for provider in self.providers}
```

#### CLI Integration

```python
# Provider group options
provider_group = parser.add_argument_group("Provider Group Options")
provider_group.add_argument(
    "--providers",
    type=str,
    nargs="+",
    help="Multiple providers to use as a group (e.g., anthropic openai)",
)
provider_group.add_argument(
    "--provider-strategy",
    type=str,
    choices=["failover", "round_robin", "cost_optimized"],
    default="failover",
    help="Strategy for selecting providers in a group (default: failover)",
)
```

#### Factory Integration

```python
def create_provider_group(
    providers: List[str] = None,
    models: List[str] = None,
    strategy: str = "failover",
    options: Optional[ProviderOptions] = None,
) -> ProviderGroup:
    """Create a provider group with multiple providers.

    Args:
        providers: List of provider names to include
        models: List of specific models to include (providers will be auto-detected)
        strategy: Selection strategy ('failover', 'round_robin', 'cost_optimized')
        options: Common provider options to apply

    Returns:
        A ProviderGroup instance
    """
    # Implementation details
    provider_instances = []

    # Add providers by name
    if providers:
        for provider_name in providers:
            provider_instances.append(create_provider(provider_name, options=options))

    # Add providers by model
    if models:
        for model in models:
            provider_name = detect_provider_from_model(model)
            if provider_name:
                model_options = options.copy() if options else ProviderOptions()
                model_options.model_name = model
                provider_instances.append(create_provider(provider_name, options=model_options))

    # Select strategy
    strategy_func = {
        "failover": ProviderSelectionStrategy.failover,
        "round_robin": ProviderSelectionStrategy.round_robin,
        "cost_optimized": ProviderSelectionStrategy.cost_optimized,
    }.get(strategy, ProviderSelectionStrategy.failover)

    # Create and return provider group
    return ProviderGroup(provider_instances, selection_strategy=strategy_func)
```

## Critical Implementation Priorities

Based on the implementation audit and project needs, these are the most critical implementation priorities:

1. **Update the agent system to work with provider options** - This will unblock the tool agent examples and enable multi-agent workflows
2. **Implement hybrid retrieval system** - Enables hybrid retrieval examples and improves knowledge system capabilities
3. **Complete streaming architecture standardization** - Ensures consistent streaming behavior across all providers
4. **Implement ProviderGroup for aggregation and fallback** - Enhances reliability and provider flexibility

## Detailed Implementation Analysis

### 1. Provider System Updates (High Priority)

**Implemented Components:**
- ✅ `ProviderOptions` data class for all provider parameters
- ✅ Provider detection logic in factory layer
- ✅ Provider resolution system for auto-detection
- ✅ Capability-based model selection
- ✅ Standardized provider interface initialization

**Pending Components:**
- ❌ `ProviderGroup` for aggregation and fallback
- ❌ Provider health monitoring system
- ❌ Advanced streaming architecture with unified interfaces
- ❌ Stream control capabilities (pause/resume/cancel)

**Implementation Plan:**
1. Create ProviderGroup interface for multiple provider access
2. Implement fallback mechanism between providers
3. Add provider selection strategy (round-robin, failover, etc.)
4. Create provider health monitoring system
5. Refactor streaming interfaces for consistency
6. Implement stream control capabilities

### 2. CLI & Core Updates

**Implemented Components:**
- ✅ CLI argument parsing system
- ✅ Configuration translation from args to options
- ✅ Environment variable integration
- ✅ Provider selection from CLI args

**Pending Components:**
- ❌ Interactive mode for complex operations
- ❌ Progress indicators for long-running operations
- ❌ Enhanced error presentation system

**Implementation Plan:**
1. Create unified CLI architecture with subcommands
2. Add progress indicators for long-running operations
3. Improve error presentation with user-friendly formatting
4. Enhance logging system with structured logging

### 3. Knowledge System

**Implemented Components:**
- ✅ Basic document ingestion (with chunking)
- ✅ Basic document retrieval
- ✅ Metadata handling
- ✅ Advanced metadata filtering with ChromaDB 1.0.8+ compatibility
- ✅ Document content filtering

**Pending Components:**
- ❌ Enhanced chunking strategies
- ❌ Hybrid retrieval system (semantic + keyword)
- ❌ Document management features

**Implementation Plan:**
1. Create semantic-aware chunking
2. Implement hybrid retrieval combining keyword + semantic search
3. ✅ Add metadata-based filtering interface (Completed)
4. ✅ Add document content filtering (Completed)
5. Implement incremental updates for document changes
6. Add document versioning system

### 4. Agent System

**Blocked Components:**
- ❌ Tool agent updates for provider options
- ❌ Agent communication protocols
- ❌ Workflow state management system
- ❌ Clear separation between agents and tools

**Implementation Plan:**
1. Update agent system to work with provider options
2. Create tool discovery and capability interfaces
3. Implement standardized tool invocation patterns
4. Create workflow state management system
5. Add message passing interfaces between agents

### 5. Example System

**Implemented Examples:**
- ✅ Basic query functionality (`01_query_simple.py`)
- ✅ Streaming responses (`02_query_streaming.py`)
- ✅ Provider options & selection (`03_provider_selection.py`)
- ✅ Document ingestion (`10_document_ingestion.py`)
- ✅ Basic retrieval (`11_basic_retrieval.py`)
- ✅ Advanced filtering (`15_advanced_filtering.py`)

**Blocked Examples:**
- ❌ Hybrid retrieval (`12_hybrid_retrieval.py.todo`)
- ❌ Tool agent usage (`20_tool_agent.py.todo`)
- ❌ Multi-agent workflows (`21_multi_agent.py.todo`)
- ❌ Agent workflows with LangGraph (`22_agent_workflows.py.todo`)

**Implementation Plan:**
1. ✅ Fix examples with outstanding issues:
   - ✅ Fix metadata handling in `query_with_context()` (Completed)
   - ✅ Update ChromaDB query format in RetrievalFilter (Completed)
   - ✅ Add advanced filtering example (Completed)
2. Implement hybrid retrieval example
3. Update tool agent example with provider options
4. Develop multi-agent workflow example
5. Create workflow state management example

## Gap Analysis & Mitigation

The following areas show significant differences between documentation and implementation:

### Provider System
**Gap:** Documentation describes a complete provider system with aggregation and fallback, but implementation only has the basic infrastructure (options, resolver, factory).

**Mitigation:** 
1. Prioritize the implementation of ProviderGroup
2. Document current limitations clearly while work is in progress
3. Create a phased roadmap for provider system completion

### Agent System
**Gap:** Documentation describes a robust multi-agent system with controller-worker architecture, but implementation needs updates to work with new provider options.

**Mitigation:**
1. Update agent system to work with provider options as top priority
2. Create examples of simple agent workflows as intermediate step
3. Document current agent limitations and workarounds

### Tool System
**Gap:** Documentation describes a comprehensive tool framework, but implementation hasn't started the redesign yet.

**Mitigation:**
1. Create a simplified tool interface as initial implementation
2. Document tool system design with clear implementation phases
3. Prioritize basic tool functionality needed for examples

### Knowledge System
**Gap:** Documentation describes advanced retrieval features like hybrid search, but not all advanced features are implemented.

**Mitigation:**
1. Implement hybrid retrieval as high priority feature
2. ✅ Document current retrieval capabilities including advanced filtering (Completed)
3. ✅ Create examples showing current retrieval functionality with filters (Completed)
4. Continue extending the knowledge system with remaining advanced features

## Development Approach

To address the implementation gaps while making progress, the following approach is recommended:

1. **Focus on Unblockers:** Prioritize work that unblocks the most examples and functionality
2. **Phased Implementation:** Break large components into phases with usable functionality at each step
3. **Documentation Alignment:** Update documentation to match implementation reality while preserving the design intent
4. **Example-Driven Development:** Use examples as validation of functionality and to guide implementation priorities

## Implementation Timeline

### Phase 1: Unblock Agent System (2 weeks)
- Update AtlasAgent to work with provider options
- Create simplified tool interface for agent examples
- Fix metadata handling in query_with_context
- Update tool agent example (20_tool_agent.py)

### Phase 2: Enhance Knowledge & Provider Systems (2 weeks)
- Implement hybrid retrieval system
- Create ProviderGroup for fallback
- Standardize streaming interfaces
- Update hybrid retrieval example (12_hybrid_retrieval.py)

### Phase 3: Multi-Agent Workflows (3 weeks)
- Implement agent communication protocols
- Create workflow state management system
- Update multi-agent example (21_multi_agent.py)
- Update workflow example (22_agent_workflows.py)

### Phase 4: Refinement & Documentation (1 week)
- Improve error handling across all components
- Enhance documentation with current implementation details
- Create additional examples for advanced features
- Add performance optimizations

## Conclusion

The current implementation shows good progress in core areas but has several key gaps that need to be addressed. By focusing on the critical implementation priorities identified in this document, particularly the agent system updates to work with provider options, we can unblock the most functionality and make rapid progress toward a complete implementation.

The phased approach outlined in the timeline will ensure steady progress while delivering usable functionality at each step, with a focus on example-driven validation to ensure the implementation meets user needs.