# Multi-Agent Workflow Example

This example demonstrates how to use Atlas's multi-agent workflow capabilities to handle complex tasks that benefit from specialized agents working together.

## Overview

Atlas's multi-agent architecture uses a controller-worker pattern where:

1. A controller agent breaks down tasks and coordinates workers
2. Worker agents specialize in different aspects of the task
3. The controller synthesizes worker outputs into a cohesive response

This approach is especially powerful for complex knowledge tasks that require both breadth and depth of analysis.

## Requirements

To run this example, you'll need:

- Atlas installed with all dependencies
- API key for your chosen model provider
- Knowledge base with ingested documents

## Basic Implementation

Here's a simple implementation of a multi-agent workflow:

```python
import os
import logging
from atlas.agents.controller import ControllerAgent
from atlas.core.config import AtlasConfig
from atlas.models.factory import get_model_provider

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    """Run a multi-agent workflow example."""
    print("Initializing Atlas multi-agent workflow...")
    
    # Create a configuration
    config = AtlasConfig()
    
    # Create a controller agent with default worker types
    controller = ControllerAgent(
        config=config,
        provider_name="anthropic",
        model_name="claude-3-7-sonnet-20250219"
    )
    
    # Define a task
    task = """
    Provide a comprehensive analysis of Atlas's knowledge graph structure, 
    including entity types, relationship patterns, and how it integrates 
    with the trimodal methodology.
    """
    
    print(f"Task: {task}")
    print("Processing with multi-agent workflow...")
    
    # Process the task
    response = controller.process_task(task)
    
    print("\nFinal Response:\n")
    print(response)

if __name__ == "__main__":
    main()
```

## Advanced Implementation

For more complex scenarios, you can configure specialized worker agents and customize the controller behavior:

```python
import os
import logging
from typing import Dict, Any, List
from atlas.agents.controller import ControllerAgent
from atlas.agents.registry import AgentRegistry
from atlas.core.config import AtlasConfig
from atlas.models.factory import get_model_provider

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    """Run an advanced multi-agent workflow example."""
    print("Initializing Atlas advanced multi-agent workflow...")
    
    # Create a configuration
    config = AtlasConfig()
    
    # Define custom worker types
    worker_types = [
        "researcher",   # Finds relevant information
        "analyst",      # Analyzes information in depth
        "critic",       # Evaluates and challenges findings
        "synthesizer"   # Combines everything into a coherent whole
    ]
    
    # Create controller with custom worker configuration
    controller = ControllerAgent(
        config=config,
        worker_types=worker_types,
        provider_name="anthropic",
        model_name="claude-3-7-sonnet-20250219",
        kwargs={
            # Custom parameters for specific worker types
            "researcher": {
                "document_count": 10,  # Retrieve more documents
                "relevance_threshold": 0.7  # Higher relevance threshold
            },
            "analyst": {
                "analysis_depth": "deep",
                "max_tokens": 2000  # Allow longer responses
            }
        }
    )
    
    # Define a complex task
    task = """
    Analyze the relationship between Atlas's knowledge graph structure and the trimodal methodology:
    
    1. How do the entity types in the knowledge graph support bottom-up implementation?
    2. What relationship patterns enable top-down design principles?
    3. How does the integration of both support holistic system integration?
    4. What are the specific advantages of this approach over traditional documentation?
    5. What are potential limitations or areas for improvement?
    
    Provide a comprehensive analysis with specific examples and references.
    """
    
    print(f"Task: {task}")
    print("Processing with advanced multi-agent workflow...")
    
    # Process the task
    response = controller.process_task(task)
    
    print("\nFinal Response:\n")
    print(response)
    
    # Access worker contributions
    worker_contributions = controller.get_worker_contributions()
    
    # Print contributions from each worker
    print("\nWorker Contributions:\n")
    for worker_type, contribution in worker_contributions.items():
        print(f"=== {worker_type.upper()} CONTRIBUTION ===")
        print(contribution[:300] + "..." if len(contribution) > 300 else contribution)
        print("\n")

if __name__ == "__main__":
    main()
```

## Controller-Worker Architecture

The controller-worker architecture consists of these key components:

### Controller Agent

The controller agent manages the overall workflow:

1. **Task Breakdown**: Divides complex tasks into subtasks for workers
2. **Worker Coordination**: Assigns subtasks to appropriate workers
3. **Result Integration**: Combines worker outputs
4. **Quality Control**: Ensures completeness and consistency

```python
# Create a controller with custom settings
controller = ControllerAgent(
    config=config,
    worker_types=["researcher", "analyst", "writer"],
    parallel=True,  # Enable parallel worker execution
    provider_name="anthropic",
    model_name="claude-3-7-sonnet-20250219"
)
```

### Worker Agents

Worker agents specialize in different aspects of the task:

1. **Researcher**: Retrieves and filters relevant information
2. **Analyst**: Performs deep analysis on retrieved information
3. **Writer**: Crafts coherent, well-structured responses
4. **Critic**: Identifies weaknesses and suggests improvements
5. **Synthesizer**: Combines multiple perspectives

You can customize the worker types and their behavior:

```python
# Custom worker configuration
worker_config = {
    "researcher": {
        "document_count": 10,
        "relevance_threshold": 0.7
    },
    "analyst": {
        "analysis_depth": "deep",
        "max_tokens": 2000
    },
    "writer": {
        "style": "academic",
        "structure": "detailed"
    }
}

controller = ControllerAgent(
    config=config,
    worker_types=list(worker_config.keys()),
    kwargs=worker_config
)
```

## Parallel Execution

For improved performance, enable parallel execution of workers:

```python
# Enable parallel execution
controller = ControllerAgent(
    config=config,
    worker_types=["researcher", "analyst", "writer"],
    parallel=True  # Enable parallel worker execution
)
```

With parallel execution:
- Workers operate independently
- The controller manages state and communication
- Results are synchronized before integration

## Customizing Worker Behavior

You can customize worker behavior by:

1. **Passing custom parameters** through the `kwargs` dictionary
2. **Creating custom worker agent classes** and registering them
3. **Modifying the system prompts** for specific worker types

Example of registering a custom worker:

```python
from atlas.agents.registry import AgentRegistry
from atlas.agents.worker import WorkerAgent

# Create a custom worker class
class SpecializedAnalystWorker(WorkerAgent):
    def __init__(self, analysis_depth="standard", **kwargs):
        super().__init__(**kwargs)
        self.analysis_depth = analysis_depth
    
    # Override process_task with specialized behavior
    def process_task(self, task):
        # Custom implementation
        pass

# Register the custom worker
AgentRegistry.register(
    "specialized_analyst", 
    SpecializedAnalystWorker,
    description="Specialized analyst worker with configurable depth"
)

# Use the custom worker
controller = ControllerAgent(
    config=config,
    worker_types=["researcher", "specialized_analyst", "writer"],
    kwargs={
        "specialized_analyst": {
            "analysis_depth": "deep"
        }
    }
)
```

## Accessing Worker Contributions

To examine the contributions from each worker:

```python
# Process a task
response = controller.process_task(task)

# Get worker contributions
worker_contributions = controller.get_worker_contributions()

# Examine individual contributions
for worker_type, contribution in worker_contributions.items():
    print(f"{worker_type}: {contribution}")
```

This is useful for:
- Debugging workflow issues
- Understanding how decisions were made
- Identifying areas for improvement

## Error Handling

The controller agent includes robust error handling:

```python
try:
    response = controller.process_task(task)
    print(response)
except Exception as e:
    print(f"Error in multi-agent workflow: {e}")
    
    # Fall back to simpler processing if needed
    fallback_agent = AtlasAgent(config=config)
    fallback_response = fallback_agent.process_message(task)
    print("Fallback response:", fallback_response)
```

## Performance Considerations

Multi-agent workflows involve multiple model calls, which has implications for:

1. **Latency**: Responses take longer due to sequential processing
2. **Cost**: Multiple API calls increase usage costs
3. **Complexity**: More components mean more potential failure points

Consider these trade-offs when deciding whether to use multi-agent workflows for your specific use case.

## Complete Example

Here's a complete example that demonstrates all the key features:

```python
import os
import logging
import time
from typing import Dict, Any, List, Optional
from atlas.agents.controller import ControllerAgent
from atlas.agents.worker import WorkerAgent
from atlas.agents.registry import AgentRegistry
from atlas.core.config import AtlasConfig
from atlas.models.factory import get_model_provider
from atlas.core.errors import safe_execute

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create a custom worker class
class TimeTrackingWorker(WorkerAgent):
    """Worker that tracks execution time."""
    
    def process_task(self, task: str) -> str:
        """Process a task and track execution time."""
        start_time = time.time()
        result = super().process_task(task)
        end_time = time.time()
        
        # Add execution time to the result
        execution_time = end_time - start_time
        return f"{result}\n\nExecution time: {execution_time:.2f} seconds"

# Register the custom worker
AgentRegistry.register(
    "time_tracking_worker",
    TimeTrackingWorker,
    description="Worker that tracks execution time"
)

def main():
    """Run a comprehensive multi-agent workflow example."""
    # Enable test mode for example purposes
    os.environ["SKIP_API_KEY_CHECK"] = "true"
    
    print("Initializing Atlas multi-agent workflow...")
    
    # Create a configuration
    config = AtlasConfig()
    
    # Define worker types with a mix of standard and custom workers
    worker_types = [
        "researcher",
        "time_tracking_worker",  # Our custom worker
        "writer"
    ]
    
    # Custom parameters for workers
    worker_params = {
        "researcher": {
            "document_count": 8,
            "relevance_threshold": 0.6
        },
        "time_tracking_worker": {
            "max_tokens": 1500
        },
        "writer": {
            "style": "technical",
            "structure": "detailed"
        }
    }
    
    # Create controller with custom settings
    controller = ControllerAgent(
        config=config,
        worker_types=worker_types,
        parallel=True,  # Enable parallel execution
        provider_name="anthropic",
        model_name="claude-3-7-sonnet-20250219",
        kwargs=worker_params
    )
    
    # Define a complex task
    task = """
    Analyze the knowledge graph structure in Atlas and how it integrates with the trimodal methodology:
    
    1. What are the core entity types in the knowledge graph?
    2. How do the relationship types support different perspectives?
    3. In what ways does the knowledge graph enable bottom-up implementation?
    4. How does the graph structure support top-down design?
    5. What role does the graph play in holistic system integration?
    
    Provide specific examples and references where possible.
    """
    
    print(f"Task: {task}")
    print("Processing with multi-agent workflow...")
    
    # Track total execution time
    start_time = time.time()
    
    # Process the task with error handling
    try:
        response = controller.process_task(task)
        
        # Calculate total execution time
        total_time = time.time() - start_time
        
        print(f"\nTask completed in {total_time:.2f} seconds\n")
        print("Final Response:\n")
        print(response)
        
        # Get and display worker contributions
        print("\nWorker Contributions:\n")
        worker_contributions = controller.get_worker_contributions()
        
        for worker_type, contribution in worker_contributions.items():
            print(f"=== {worker_type.upper()} ===")
            # Show a preview of each contribution
            preview = contribution[:300] + "..." if len(contribution) > 300 else contribution
            print(preview)
            print(f"Length: {len(contribution)} characters")
            print("\n")
        
        # Show task breakdown
        print("Task Breakdown:")
        for subtask in controller.get_subtasks():
            print(f"- {subtask}")
        
    except Exception as e:
        print(f"Error in multi-agent workflow: {e}")
        
        # Fall back to simpler processing
        print("Falling back to standard agent...")
        from atlas.agents.base import AtlasAgent
        
        fallback_agent = AtlasAgent(config=config)
        fallback_response = fallback_agent.process_message(task)
        
        print("Fallback Response:\n")
        print(fallback_response)

if __name__ == "__main__":
    main()
```

## Integration with Custom Applications

To integrate multi-agent workflows into your application:

```python
from atlas.agents.controller import ControllerAgent
from atlas.core.config import AtlasConfig

class MyApplication:
    def __init__(self):
        # Initialize the controller
        config = AtlasConfig()
        self.controller = ControllerAgent(
            config=config,
            worker_types=["researcher", "analyst", "writer"],
            parallel=True
        )
    
    def process_user_query(self, query):
        # Process the query using the multi-agent workflow
        try:
            response = self.controller.process_task(query)
            return {
                "status": "success",
                "response": response,
                "metadata": {
                    "workers": list(self.controller.get_worker_contributions().keys()),
                    "subtasks": self.controller.get_subtasks()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
```

## Related Documentation

- [Multi-Agent Workflow](../../workflows/multi_agent.md) - Detailed documentation of multi-agent architecture
- [Controller Agent](../../components/agents/controller.md) - Controller agent implementation details
- [Worker Agents](../../components/agents/workers.md) - Worker agent types and customization
- [Advanced Examples](./advanced_examples.md) - More advanced usage examples