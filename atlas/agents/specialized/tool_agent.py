"""
Tool-capable agent implementation for the Atlas framework.

This module defines a specialized agent that can use tools to enhance 
its capabilities and perform more complex tasks.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union, Callable, Sequence

from atlas.core.config import AtlasConfig
from atlas.core.telemetry import traced
from atlas.agents.worker import WorkerAgent
from atlas.agents.messaging.message import StructuredMessage
from atlas.tools.base import AgentToolkit, Tool
from atlas.providers.base import ModelProvider
from atlas.providers.options import ProviderOptions
from atlas.providers.resolver import resolve_provider_options
from atlas.providers.capabilities import Capability, CapabilityLevel


logger = logging.getLogger(__name__)


class ToolCapableAgent(WorkerAgent):
    """Worker agent with tool execution capabilities."""
    
    def __init__(
        self,
        worker_id: str,
        specialization: str,
        toolkit: Optional[AgentToolkit] = None,
        system_prompt_file: Optional[str] = None,
        collection_name: str = "atlas_knowledge_base",
        config: Optional[AtlasConfig] = None,
        provider: Optional[ModelProvider] = None,
        providers: Optional[Sequence[ModelProvider]] = None,
        provider_strategy: str = "failover",
        task_aware: bool = True,
        provider_options: Optional[ProviderOptions] = None,
    ):
        """Initialize a tool-capable agent.
        
        Args:
            worker_id: Unique identifier for this worker.
            specialization: What this worker specializes in.
            toolkit: The toolkit containing available tools.
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            provider: Optional pre-configured provider instance.
            providers: Optional list of provider instances to use in a provider group.
            provider_strategy: Strategy for provider selection in a group.
            task_aware: Whether to enable task-aware provider selection.
            provider_options: Optional provider options for more control over provider selection.
        """
        # If provider_options are provided, they take precedence over explicit provider/providers
        if provider_options:
            # Clear any explicit providers to avoid confusion
            provider = None
            providers = None
        
        # Ensure the required capabilities for tool use are present
        if provider_options:
            # Add tool usage as a required capability
            provider_options.require_capability(
                Capability.TOOL_USE, 
                min_level=CapabilityLevel.STRONG
            )
            
            # Add JSON output capability for proper tool call parsing
            provider_options.require_capability(
                Capability.JSON_OUTPUT,
                min_level=CapabilityLevel.MODERATE
            )
        
        # Initialize base worker agent
        super().__init__(
            worker_id=worker_id,
            specialization=specialization,
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
            config=config,
            provider=provider,
            providers=providers,
            provider_strategy=provider_strategy,
            task_aware=task_aware,
        )
        
        # Store provider options for later use
        self.provider_options = provider_options
        
        # Initialize toolkit
        self.toolkit = toolkit or AgentToolkit()
        
        # Store agent capabilities for discovery
        self.capabilities: List[str] = []
        
        # Enhance system prompt with tool capabilities
        self._add_tool_instructions_to_prompt()
        
        # If provider options are set but no provider is resolved yet,
        # resolve provider options now
        if provider_options and not self.provider:
            self.provider = resolve_provider_options(provider_options)
            logger.info(f"Resolved provider {self.provider.name} with model {self.provider.model_name}")
    
    def _add_tool_instructions_to_prompt(self) -> None:
        """Add tool usage instructions to the system prompt."""
        # Get tool descriptions the agent has access to
        tool_descriptions = self.toolkit.get_tool_descriptions(self.worker_id)
        
        if not tool_descriptions:
            # No tools available, no need to modify prompt
            return
            
        # Format tool schemas for the prompt
        tool_schemas_str = json.dumps(tool_descriptions, indent=2)
        
        # Create tool instructions - DO NOT CHANGE THE HEADING FORMAT!
        # Tests will look for this exact heading "## Available Tools"
        tool_instructions = f"""
## Available Tools

You have access to the following tools:

{tool_schemas_str}

To use a tool, include a tool call in your response with the following format:
```json
{{
  "tool_calls": [
    {{
      "name": "tool_name",
      "arguments": {{
        "arg1": "value1",
        "arg2": "value2"
      }}
    }}
  ]
}}
```

Multiple tool calls can be included in a single response. Include your reasoning before and after the tool call.
"""
        
        # Add to system prompt
        self.system_prompt = self.system_prompt + tool_instructions
    
    @traced(name="register_capability")
    def register_capability(self, capability: str) -> None:
        """Register a capability this agent provides.
        
        Args:
            capability: Description of the capability.
        """
        self.capabilities.append(capability)
        logger.info(f"Agent {self.worker_id} registered capability: {capability}")
    
    @traced(name="register_tool")
    def register_tool(self, tool: Union[Tool, Callable]) -> str:
        """Register a tool for this agent to use.
        
        Args:
            tool: Tool to register (either a Tool instance or a function).
            
        Returns:
            The name of the registered tool.
        """
        # Register in toolkit
        tool_name = self.toolkit.register_tool(tool)
        
        # Grant permission to this agent
        self.toolkit.grant_permission(self.worker_id, tool_name)
        
        # Update system prompt
        self._add_tool_instructions_to_prompt()
        
        return tool_name
    
    @traced(name="process_structured_message")
    def process_structured_message(
        self, message: StructuredMessage
    ) -> StructuredMessage:
        """Process a structured message, handling any tool calls.
        
        Args:
            message: The structured message to process.
            
        Returns:
            A response structured message.
        """
        # Log message receipt
        logger.info(
            f"Agent {self.worker_id} received message from {message.source_agent or 'unknown'}"
        )
        
        try:
            # Process the message content with the LLM
            capabilities = {"tool_use": True}
            response_content = self.process_message(
                message=message.content,
                capabilities=capabilities,
            )
            
            # Create basic response
            response = StructuredMessage.create_response(response_content, message)
            
            # Check if the LLM response contains tool calls
            tool_calls = self._extract_tool_calls_from_content(response_content)
            
            if tool_calls:
                # Process tool calls
                for tool_call in tool_calls:
                    try:
                        # Extract tool name and arguments
                        tool_name = tool_call.get("name")
                        tool_args = tool_call.get("arguments", {})
                        
                        if not tool_name:
                            continue
                            
                        # Execute the tool
                        tool_result = self.toolkit.execute_tool(
                            agent_id=self.worker_id,
                            tool_name=tool_name,
                            args=tool_args
                        )
                        
                        # Add the result to the response
                        call_id = tool_call.get("id") or "unknown"
                        response.add_tool_result(
                            name=tool_name,
                            result=tool_result,
                            call_id=call_id
                        )
                    except Exception as e:
                        # Log the error and add it to tool results
                        logger.error(f"Error executing tool {tool_name}: {str(e)}")
                        call_id = tool_call.get("id") or "unknown"
                        response.add_tool_result(
                            name=tool_name,
                            result=None,
                            call_id=call_id,
                            status="error",
                            error=str(e)
                        )
            
            return response
            
        except Exception as e:
            # Create error response
            logger.error(f"Error processing message: {str(e)}")
            return StructuredMessage.create_error(
                f"Error processing message: {str(e)}",
                message
            )
    
    @traced(name="process_task")
    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task, handling tool calls if present.
        
        Args:
            task: The task to process.
            
        Returns:
            The result of processing the task.
        """
        # Check if task contains tool_calls
        tool_calls = task.get("tool_calls", [])
        tool_results = []
        
        # Process any tool calls in the task
        for tool_call in tool_calls:
            try:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})
                
                if not tool_name:
                    continue
                    
                # Execute the tool
                result = self.toolkit.execute_tool(
                    agent_id=self.worker_id,
                    tool_name=tool_name,
                    args=tool_args
                )
                
                # Add to results
                tool_results.append({
                    "name": tool_name,
                    "result": result,
                    "call_id": tool_call.get("id", "unknown"),
                    "status": "success"
                })
            except Exception as e:
                # Add error to results
                tool_results.append({
                    "name": tool_name,
                    "result": None,
                    "call_id": tool_call.get("id", "unknown"),
                    "status": "error",
                    "error": str(e)
                })
        
        # If there were tool calls, include results in response
        if tool_calls:
            return {
                "worker_id": self.worker_id,
                "task_id": task.get("task_id", "unknown"),
                "status": "completed",
                "tool_results": tool_results
            }
        
        # Otherwise, process normally using base implementation
        # Ensure we include tool_use capability
        capabilities = task.get("capabilities", {})
        capabilities["tool_use"] = True
        task["capabilities"] = capabilities
        
        return super().process_task(task)
    
    def _extract_tool_calls_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Extract tool calls from response content.
        
        Args:
            content: The response content from the LLM.
            
        Returns:
            A list of tool call dictionaries.
        """
        # Look for tool call JSON blocks in the content
        tool_calls = []
        
        # Simple JSON block extraction (could be enhanced with regex)
        start_marker = '```json'
        end_marker = '```'
        
        # Find all JSON blocks
        start_pos = 0
        while True:
            # Find the next JSON block
            start_idx = content.find(start_marker, start_pos)
            if start_idx == -1:
                break
                
            # Find the end of the block
            start_json = start_idx + len(start_marker)
            end_idx = content.find(end_marker, start_json)
            if end_idx == -1:
                break
                
            # Extract the JSON content
            json_text = content[start_json:end_idx].strip()
            
            try:
                # Parse the JSON
                json_obj = json.loads(json_text)
                
                # Extract tool calls if present
                if "tool_calls" in json_obj:
                    tool_calls.extend(json_obj["tool_calls"])
            except json.JSONDecodeError as e:
                # Log error but continue processing
                logger.warning(f"Failed to parse JSON block: {str(e)}")
            
            # Move to the next position
            start_pos = end_idx + len(end_marker)
        
        return tool_calls
    
    @traced(name="get_capabilities")
    def get_capabilities(self) -> List[str]:
        """Get the capabilities of this agent.
        
        Returns:
            A list of capability descriptions.
        """
        capabilities = self.capabilities.copy()
        
        # Add capabilities based on available tools
        tool_names = list(self.toolkit.get_accessible_tools(self.worker_id).keys())
        if tool_names:
            capabilities.append(f"Can use tools: {', '.join(tool_names)}")
        
        return capabilities
    
    @traced(name="run_with_tools")
    def run_with_tools(self, query: str, streaming: bool = False) -> str:
        """Run a query with tool execution capability.
        
        This is a simplified interface for running queries with tool execution,
        which will automatically handle multiple tool calls if needed.
        
        Args:
            query: The query to process.
            streaming: Whether to use streaming mode.
            
        Returns:
            The final response.
        """
        # Set up capabilities
        capabilities = {"tool_use": True}
        
        # Get initial response
        response = self.process_message(query, capabilities=capabilities)
        
        # Extract tool calls from the response
        tool_calls = self._extract_tool_calls_from_content(response)
        
        # If there are no tool calls, return the response
        if not tool_calls:
            return response
        
        # Process tool calls and collect results
        tool_results_text = ""
        for tool_call in tool_calls:
            try:
                # Extract tool name and arguments
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})
                
                if not tool_name:
                    continue
                
                # Execute the tool
                result = self.toolkit.execute_tool(
                    agent_id=self.worker_id,
                    tool_name=tool_name,
                    args=tool_args
                )
                
                # Format result for the follow-up
                tool_results_text += f"\nTool: {tool_name}\nArguments: {json.dumps(tool_args)}\nResult: {result}\n"
                
            except Exception as e:
                # Add error to results
                logger.error(f"Error executing tool {tool_name}: {str(e)}")
                tool_results_text += f"\nTool: {tool_name}\nArguments: {json.dumps(tool_args)}\nError: {str(e)}\n"
        
        # Create a follow-up message with the tool results
        follow_up_message = f"""
Based on my previous response, I executed the following tool calls:

{tool_results_text}

Please provide a final answer incorporating these tool results.
"""
        
        # Get final response that incorporates tool results
        final_response = self.process_message(
            message=f"{query}\n\n{follow_up_message}",
            capabilities=capabilities
        )
        
        return final_response


def create_tool_agent(
    worker_id: str = "tool_worker",
    specialization: str = "Tool Execution and Augmented Reasoning",
    system_prompt_file: Optional[str] = None,
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None,
    provider: Optional[ModelProvider] = None,
    tools: Optional[List[Tool]] = None,
    streaming: bool = False,
) -> ToolCapableAgent:
    """Create a tool-capable agent with the given configuration.
    
    This is a convenience function for creating a tool agent with
    proper configuration for the provider options system.
    
    Args:
        worker_id: Unique identifier for the worker.
        specialization: What the worker specializes in.
        system_prompt_file: Optional path to a file containing the system prompt.
        provider_name: Optional name of the provider to use.
        model_name: Optional name of the model to use.
        provider: Optional pre-configured provider instance.
        tools: Optional list of tools to register with the agent.
        streaming: Whether to enable streaming output.
        
    Returns:
        A configured tool-capable agent.
    """
    # Set up provider options if provider_name is specified
    provider_options = None
    if provider_name:
        provider_options = ProviderOptions(
            provider_name=provider_name,
            model_name=model_name,
            streaming=streaming
        )
        
        # Require tool use capability
        provider_options.require_capability(
            Capability.TOOL_USE, 
            min_level=CapabilityLevel.STRONG
        )
        
        # Require JSON output capability
        provider_options.require_capability(
            Capability.JSON_OUTPUT,
            min_level=CapabilityLevel.MODERATE
        )
    
    # Create toolkit if tools are provided
    toolkit = None
    if tools:
        toolkit = AgentToolkit()
        
    # Create the agent
    agent = ToolCapableAgent(
        worker_id=worker_id,
        specialization=specialization,
        system_prompt_file=system_prompt_file,
        toolkit=toolkit,
        provider=provider,
        provider_options=provider_options,
        task_aware=True
    )
    
    # Register tools if provided
    if tools:
        for tool in tools:
            agent.register_tool(tool)
    
    return agent