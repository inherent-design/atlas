# Advanced Examples

This guide demonstrates advanced usage patterns for integrating Atlas into more complex applications and workflows.

## Overview

While the basic examples cover common use cases, these advanced examples showcase more sophisticated integration patterns and customizations:

1. [Multi-Agent Workflow](#multi-agent-workflow)
2. [Custom LangGraph Workflow](#custom-langgraph-workflow)
3. [WebUI Integration](#webui-integration)
4. [CLI Tool Integration](#cli-tool-integration)
5. [Custom Agent Implementation](#custom-agent-implementation)

## Multi-Agent Workflow

Atlas supports complex multi-agent workflows with a controller-worker architecture. This example demonstrates how to set up and use such a workflow.

```python
import os
import logging
from atlas.agents.controller import ControllerAgent
from atlas.core.config import AtlasConfig

# Configure logging
logging.basicConfig(level=logging.INFO)

# Enable test mode for example purposes
os.environ["SKIP_API_KEY_CHECK"] = "true"

def main():
    """Run a multi-agent workflow example."""
    print("Initializing Atlas multi-agent workflow...")

    # Create a configuration
    config = AtlasConfig()

    # Create a controller agent
    controller = ControllerAgent(
        config=config,
        worker_types=["researcher", "analyst", "writer"],
        system_prompt_file=None,  # Use default system prompt
        provider_name="anthropic"
    )

    # Define a complex task
    task = """
    Analyze the following aspects of Atlas's Knowledge Graph structure:
    1. Core entity types
    2. Relationship patterns
    3. How it integrates with the Trimodal methodology

    Provide a comprehensive analysis with specific examples.
    """

    print(f"\nTask: {task}\n")
    print("Processing with multi-agent workflow...")

    # Process the task using multi-agent workflow
    try:
        response = controller.process_task(task)
        print("\nFinal Response:\n")
        print(response)

        # Access worker contributions (in a real example)
        # print("\nWorker Contributions:")
        # for worker_type, contribution in controller.get_worker_contributions().items():
        #     print(f"\n{worker_type.capitalize()} contribution:")
        #     print(contribution[:300] + "..." if len(contribution) > 300 else contribution)

    except Exception as e:
        print(f"Error in multi-agent workflow: {e}")

if __name__ == "__main__":
    main()
```

### Key Components

1. **Controller Agent**: Orchestrates the workflow and coordinates worker agents
2. **Worker Agents**: Specialized agents for different aspects of the task (researcher, analyst, writer)
3. **Task Processing**: Breaking down the complex task into subtasks for each worker
4. **Result Synthesis**: Combining individual worker outputs into a cohesive final response

## Custom LangGraph Workflow

This example shows how to create a custom workflow using LangGraph with Atlas components.

```python
import os
import logging
from typing import Dict, Any, TypedDict, List
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from atlas.core.config import AtlasConfig
from atlas.providers.factory import get_model_provider
from atlas.knowledge.retrieval import KnowledgeBase
from atlas.graph.state import AgentState

# Configure logging
logging.basicConfig(level=logging.INFO)

# Enable test mode for example purposes
os.environ["SKIP_API_KEY_CHECK"] = "true"

# Define custom state for this workflow
class CustomState(BaseModel):
    query: str = ""
    context: List[Dict[str, Any]] = Field(default_factory=list)
    intermediate_analysis: str = ""
    final_response: str = ""

def retrieve_documents(state: CustomState) -> CustomState:
    """Retrieve relevant documents for the query."""
    # Create knowledge base
    kb = KnowledgeBase()

    # Get documents
    documents = kb.retrieve(state.query)

    # Update state
    state.context = [
        {
            "content": doc["content"],
            "source": doc["metadata"].get("source", "Unknown"),
            "relevance_score": doc["relevance_score"]
        }
        for doc in documents[:5]  # Top 5 documents
    ]

    return state

def analyze_context(state: CustomState) -> CustomState:
    """Analyze the context documents."""
    # Create a model provider for analysis
    provider = get_model_provider("anthropic")

    # Create prompt for analysis
    docs_text = "\n\n".join([
        f"Document {i+1} (Source: {doc['source']}):\n{doc['content']}"
        for i, doc in enumerate(state.context)
    ])

    prompt = f"""
    Based on these documents, analyze the key information relevant to: {state.query}

    Documents:
    {docs_text}

    Provide a concise analysis highlighting the most important points for answering the query.
    """

    # Get analysis
    analysis = provider.generate(prompt)

    # Update state
    state.intermediate_analysis = analysis

    return state

def generate_response(state: CustomState) -> CustomState:
    """Generate the final response."""
    # Create a model provider for response generation
    provider = get_model_provider("anthropic")

    # Create prompt for final response
    prompt = f"""
    Query: {state.query}

    Context analysis:
    {state.intermediate_analysis}

    Based on this analysis, provide a comprehensive answer to the original query.
    """

    # Generate response
    response = provider.generate(prompt)

    # Update state
    state.final_response = response

    return state

def decide_next_step(state: CustomState) -> str:
    """Decide the next step in the workflow."""
    if not state.context:
        return "retrieve_documents"
    elif not state.intermediate_analysis:
        return "analyze_context"
    elif not state.final_response:
        return "generate_response"
    else:
        return END

def main():
    """Run a custom workflow example."""
    print("Initializing custom LangGraph workflow...")

    # Build the workflow graph
    workflow = StateGraph(CustomState)

    # Add nodes
    workflow.add_node("retrieve_documents", retrieve_documents)
    workflow.add_node("analyze_context", analyze_context)
    workflow.add_node("generate_response", generate_response)

    # Add conditional edges
    workflow.add_conditional_edges("", decide_next_step)
    workflow.add_conditional_edges("retrieve_documents", decide_next_step)
    workflow.add_conditional_edges("analyze_context", decide_next_step)
    workflow.add_conditional_edges("generate_response", decide_next_step)

    # Compile the graph
    app = workflow.compile()

    # Run the workflow
    try:
        query = "How do knowledge graphs integrate with the trimodal methodology in Atlas?"
        print(f"Query: {query}\n")

        # Initialize state
        initial_state = CustomState(query=query)

        # Run the workflow
        for state in app.stream(initial_state):
            step = list(state.keys())[0] if state else "Starting"
            print(f"Step: {step}")

        # Get final state
        final_state = app.get_state()

        print("\nFinal Response:\n")
        print(final_state.final_response)

    except Exception as e:
        print(f"Error in custom workflow: {e}")

if __name__ == "__main__":
    main()
```

### Key Components

1. **Custom State Model**: Defines the data structure for tracking workflow state
2. **Node Functions**: Implement specific steps in the workflow (retrieval, analysis, response)
3. **Conditional Routing**: Determines the next step based on the current state
4. **Graph Compilation**: Creates an executable workflow from the graph definition

## WebUI Integration

This example demonstrates how to integrate Atlas into a web application using FastAPI and streaming responses.

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import uvicorn
import logging
import os
from typing import Dict, Any, List

from atlas import create_query_client
from atlas.core.config import AtlasConfig

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create app
app = FastAPI(title="Atlas Web UI")

# Create Atlas client
client = create_query_client()

# WebSocket connections
active_connections: List[WebSocket] = []

# Function to handle streaming output
async def streaming_callback(delta: str, full_text: str, websocket: WebSocket):
    """Send streaming output to the connected WebSocket client."""
    try:
        await websocket.send_text(json.dumps({
            "type": "stream",
            "delta": delta,
            "fullText": full_text
        }))
    except Exception as e:
        logging.error(f"Error sending to websocket: {e}")

# WebSocket endpoint for streaming responses
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "query":
                query = message["query"]

                # Notify client that processing has started
                await websocket.send_text(json.dumps({
                    "type": "start",
                    "query": query
                }))

                try:
                    # Process query with streaming
                    from functools import partial
                    callback = partial(streaming_callback, websocket=websocket)

                    # Run in try/except to handle errors
                    try:
                        response = client.query_streaming(query, callback)

                        # Send completion message
                        await websocket.send_text(json.dumps({
                            "type": "complete",
                            "response": response
                        }))

                    except Exception as e:
                        # Send error message
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": str(e)
                        }))

                        # Fall back to document retrieval
                        documents = client.retrieve_only(query)

                        # Send documents
                        await websocket.send_text(json.dumps({
                            "type": "documents",
                            "documents": [
                                {
                                    "content": doc["content"],
                                    "source": doc["metadata"].get("source", "Unknown"),
                                    "relevance_score": doc["relevance_score"]
                                }
                                for doc in documents[:5]  # Top 5 documents
                            ]
                        }))

                except Exception as e:
                    logging.error(f"Error processing query: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Error processing query: {str(e)}"
                    }))

    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

# REST API endpoint for document retrieval (no streaming)
@app.post("/api/retrieve")
async def retrieve_documents(request: Dict[str, Any]):
    """Retrieve documents for a query without generating a response."""
    query = request.get("query", "")
    try:
        documents = client.retrieve_only(query)
        return {
            "success": True,
            "documents": [
                {
                    "content": doc["content"],
                    "source": doc["metadata"].get("source", "Unknown"),
                    "relevance_score": doc["relevance_score"]
                }
                for doc in documents[:10]  # Top 10 documents
            ]
        }
    except Exception as e:
        logging.error(f"Error retrieving documents: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# REST API endpoint for simple query (no streaming)
@app.post("/api/query")
async def query_endpoint(request: Dict[str, Any]):
    """Process a query and return a response."""
    query = request.get("query", "")
    with_context = request.get("with_context", False)

    try:
        if with_context:
            result = client.query_with_context(query)
            return {
                "success": True,
                "response": result["response"],
                "context": result["context"]
            }
        else:
            response = client.query(query)
            return {
                "success": True,
                "response": response
            }
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Serve a sample HTML interface
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

def main():
    print("Starting Atlas Web UI server...")
    print("Access the UI at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
```

### Implementation Notes

This example assumes you have a `static` directory with an `index.html` file that contains a simple chat interface. You would need to create this file with appropriate HTML, CSS, and JavaScript to handle the WebSocket connection and UI updates.

### Key Components

1. **WebSocket API**: Provides real-time streaming responses
2. **REST API**: Offers additional endpoints for non-streaming interactions
3. **Error Handling**: Robust error recovery with fallback to document retrieval
4. **UI Integration**: Demonstrates how to connect Atlas to a web frontend

## CLI Tool Integration

This example shows how to integrate Atlas into a command-line tool using Click.

```python
import click
import os
import sys
from typing import Optional
import logging
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress

from atlas import create_query_client
from atlas.core.config import AtlasConfig

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create console for rich output
console = Console()

@click.group()
@click.option("--provider", help="Model provider to use (anthropic, openai, ollama)", default=None)
@click.option("--model", help="Model name to use", default=None)
@click.option("--db-path", help="Path to knowledge base", default=None)
@click.option("--collection", help="Collection name in knowledge base", default=None)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, provider, model, db_path, collection, verbose):
    """Atlas Knowledge Assistant CLI"""
    # Set up logging based on verbosity
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create config
    ctx.obj = {
        "provider": provider,
        "model": model,
        "db_path": db_path,
        "collection": collection,
        "verbose": verbose
    }

@cli.command()
@click.argument("query")
@click.option("--stream/--no-stream", default=True, help="Enable/disable streaming output")
@click.option("--context/--no-context", default=False, help="Include context documents in output")
@click.option("--format", type=click.Choice(["text", "markdown", "json"]), default="markdown", help="Output format")
@click.pass_context
def query(ctx, query, stream, context, format):
    """Query Atlas knowledge assistant."""
    # Create client using context
    try:
        with Progress() as progress:
            task = progress.add_task("[green]Initializing Atlas...", total=1)

            client = create_query_client(
                provider_name=ctx.obj["provider"],
                model_name=ctx.obj["model"],
                db_path=ctx.obj["db_path"],
                collection_name=ctx.obj["collection"]
            )

            progress.update(task, advance=1)

        console.print(f"\n[bold blue]Query:[/bold blue] {query}\n")

        if context:
            # Get response with context
            with Progress() as progress:
                task = progress.add_task("[green]Processing query with context...", total=1)
                result = client.query_with_context(query)
                progress.update(task, advance=1)

            # Format and display response
            if format == "json":
                console.print(json.dumps(result, indent=2))
            elif format == "markdown":
                console.print(Markdown(result["response"]))

                console.print("\n[bold blue]Context Documents:[/bold blue]")
                for i, doc in enumerate(result["context"]["documents"]):
                    console.print(Panel(
                        f"[bold]Source:[/bold] {doc['source']}\n" +
                        f"[bold]Relevance:[/bold] {doc['relevance_score']:.4f}\n\n" +
                        f"{doc['content'][:300]}..." if len(doc['content']) > 300 else doc['content'],
                        title=f"Document {i+1}",
                        border_style="blue"
                    ))
            else:
                console.print(result["response"])
                console.print("\nContext Documents:")
                for i, doc in enumerate(result["context"]["documents"]):
                    console.print(f"Document {i+1}: {doc['source']}")
                    console.print(f"Relevance: {doc['relevance_score']:.4f}")
                    console.print(f"Excerpt: {doc['content'][:300]}...")

        elif stream:
            # Stream the response
            console.print("[bold green]Response:[/bold green]")

            def print_stream(delta, full_text):
                console.print(delta, end="")

            client.query_streaming(query, print_stream)
            console.print("\n")

        else:
            # Get standard response
            with Progress() as progress:
                task = progress.add_task("[green]Processing query...", total=1)
                response = client.query(query)
                progress.update(task, advance=1)

            # Format and display response
            if format == "json":
                console.print(json.dumps({"response": response}, indent=2))
            elif format == "markdown":
                console.print(Markdown(response))
            else:
                console.print(response)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if ctx.obj["verbose"]:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

@cli.command()
@click.argument("query")
@click.option("--limit", default=5, help="Maximum number of documents to return")
@click.option("--format", type=click.Choice(["text", "markdown", "json"]), default="text", help="Output format")
@click.pass_context
def retrieve(ctx, query, limit, format):
    """Retrieve documents from the knowledge base without generating a response."""
    # Create client using context
    try:
        with Progress() as progress:
            task = progress.add_task("[green]Initializing Atlas...", total=1)

            client = create_query_client(
                provider_name=ctx.obj["provider"],
                model_name=ctx.obj["model"],
                db_path=ctx.obj["db_path"],
                collection_name=ctx.obj["collection"]
            )

            progress.update(task, advance=1)

        console.print(f"\n[bold blue]Query:[/bold blue] {query}\n")

        # Retrieve documents
        with Progress() as progress:
            task = progress.add_task("[green]Retrieving documents...", total=1)
            documents = client.retrieve_only(query)
            progress.update(task, advance=1)

        # Limit to requested number
        documents = documents[:limit]

        console.print(f"[bold green]Found {len(documents)} relevant documents:[/bold green]\n")

        # Format and display documents
        if format == "json":
            console.print(json.dumps({
                "documents": [
                    {
                        "content": doc["content"],
                        "source": doc["metadata"].get("source", "Unknown"),
                        "relevance_score": doc["relevance_score"]
                    }
                    for doc in documents
                ]
            }, indent=2))
        elif format == "markdown":
            for i, doc in enumerate(documents):
                console.print(Panel(
                    f"[bold]Source:[/bold] {doc['metadata'].get('source', 'Unknown')}\n" +
                    f"[bold]Relevance:[/bold] {doc['relevance_score']:.4f}\n\n" +
                    f"{doc['content'][:500]}..." if len(doc['content']) > 500 else doc['content'],
                    title=f"Document {i+1}",
                    border_style="blue"
                ))
        else:
            for i, doc in enumerate(documents):
                console.print(f"Document {i+1}: {doc['metadata'].get('source', 'Unknown')}")
                console.print(f"Relevance: {doc['relevance_score']:.4f}")
                console.print(f"Content: {doc['content'][:300]}...")
                console.print("")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if ctx.obj["verbose"]:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

@cli.command()
@click.option("--provider", type=click.Choice(["anthropic", "openai", "ollama", "all"]), default="all", help="Provider to check")
@click.pass_context
def check(ctx, provider):
    """Check the status of Atlas components and providers."""
    console.print("[bold blue]Atlas Component Check[/bold blue]\n")

    # Check knowledge base
    try:
        from atlas.knowledge.retrieval import KnowledgeBase

        console.print("[bold]Checking Knowledge Base...[/bold]")
        db_path = ctx.obj["db_path"]
        collection = ctx.obj["collection"]

        kb = KnowledgeBase(
            db_path=db_path,
            collection_name=collection
        )

        # Get collection info
        collection_info = kb.get_collection_info()

        console.print(Panel(
            f"[bold]DB Path:[/bold] {kb.db_path}\n" +
            f"[bold]Collection:[/bold] {kb.collection_name}\n" +
            f"[bold]Document Count:[/bold] {collection_info['count'] if collection_info else 'Unknown'}\n",
            title="Knowledge Base",
            border_style="green"
        ))
    except Exception as e:
        console.print(Panel(
            f"Error: {str(e)}",
            title="Knowledge Base",
            border_style="red"
        ))

    # Check providers
    console.print("\n[bold]Checking Model Providers...[/bold]")

    providers_to_check = []
    if provider == "all":
        providers_to_check = ["anthropic", "openai", "ollama"]
    else:
        providers_to_check = [provider]

    for prov in providers_to_check:
        try:
            from atlas.providers.factory import get_model_provider

            # Skip API key check for demo
            os.environ["SKIP_API_KEY_CHECK"] = "true"

            # Try to initialize the provider
            model_provider = get_model_provider(prov)

            # Get available models
            available_models = model_provider.get_available_models()

            console.print(Panel(
                f"[bold]Status:[/bold] Available\n" +
                f"[bold]Default Model:[/bold] {model_provider.model_name}\n" +
                f"[bold]Available Models:[/bold]\n" +
                "\n".join([f"  - {model}" for model in available_models]),
                title=f"{prov.capitalize()} Provider",
                border_style="green"
            ))
        except Exception as e:
            console.print(Panel(
                f"Error: {str(e)}",
                title=f"{prov.capitalize()} Provider",
                border_style="red"
            ))

if __name__ == "__main__":
    cli(obj={})
```

### Key Components

1. **Command Structure**: Organized with Click for a clean CLI interface
2. **Rich Output**: User-friendly formatted output using Rich
3. **Multiple Commands**: Support for different operations (query, retrieve, check)
4. **Progress Indicators**: Visual feedback for long-running operations
5. **Error Handling**: Robust error handling with appropriate exit codes

## Custom Agent Implementation

This example demonstrates how to create a custom agent implementation to extend Atlas functionality.

```python
import logging
from typing import Dict, Any, List, Optional, Callable
import json

from atlas.agents.base import BaseAgent
from atlas.core.config import AtlasConfig
from atlas.providers.factory import get_model_provider
from atlas.knowledge.retrieval import KnowledgeBase

# Configure logging
logging.basicConfig(level=logging.INFO)

class SpecializedAnalysisAgent(BaseAgent):
    """Custom agent specialized for in-depth document analysis."""

    def __init__(
        self,
        system_prompt_file: Optional[str] = None,
        collection_name: Optional[str] = None,
        config: Optional[AtlasConfig] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        analysis_depth: str = "standard"  # Can be "standard", "deep", or "comprehensive"
    ):
        """Initialize the specialized analysis agent.

        Args:
            system_prompt_file: Path to the system prompt file
            collection_name: Name of the collection in the knowledge base
            config: Configuration object
            provider_name: Model provider name
            model_name: Model name
            analysis_depth: Depth of analysis to perform
        """
        # Call parent initializer
        super().__init__(
            system_prompt_file=system_prompt_file,
            collection_name=collection_name,
            config=config,
            provider_name=provider_name,
            model_name=model_name
        )

        # Set analysis depth
        self.analysis_depth = analysis_depth

        # Create knowledge base
        self.knowledge_base = KnowledgeBase(
            collection_name=self.collection_name,
            db_path=self.config.db_path
        )

        # Set up additional settings based on analysis depth
        if analysis_depth == "deep":
            self.document_count = 10
            self.max_tokens = 2000
        elif analysis_depth == "comprehensive":
            self.document_count = 15
            self.max_tokens = 3000
        else:  # standard
            self.document_count = 5
            self.max_tokens = 1000

        logging.info(f"Initialized specialized analysis agent with {analysis_depth} depth")

    def process_message(self, message: str) -> str:
        """Process a user message and return a response.

        Args:
            message: The user message to process

        Returns:
            The agent's response
        """
        # Retrieve documents
        documents = self.knowledge_base.retrieve(message)

        # Limit to document count
        documents = documents[:self.document_count]

        # Extract content and metadata
        docs_with_metadata = []
        for doc in documents:
            docs_with_metadata.append({
                "content": doc["content"],
                "source": doc["metadata"].get("source", "Unknown"),
                "relevance": doc["relevance_score"]
            })

        # Generate a prompt based on analysis depth
        if self.analysis_depth == "deep":
            analysis_instructions = """
            Perform a deep analysis of the provided documents. Your analysis should include:
            1. Key themes and concepts across all documents
            2. Detailed examination of each document's main points
            3. Identification of any contradictions or inconsistencies
            4. Synthesis of the information into a comprehensive understanding
            5. Specific examples and quotes from the documents
            """
        elif self.analysis_depth == "comprehensive":
            analysis_instructions = """
            Perform a comprehensive analysis of the provided documents. Your analysis should include:
            1. Exhaustive examination of all themes, concepts, and ideas
            2. Detailed breakdown of each document with extensive quotes
            3. Cross-referencing information between documents
            4. Multiple levels of interpretation for complex concepts
            5. Historical context and development of ideas over time
            6. Implications and potential future developments
            7. Structured organization with clear sections for each aspect
            """
        else:  # standard
            analysis_instructions = """
            Analyze the provided documents to extract the most relevant information. Your analysis should include:
            1. Main points from each document
            2. Key concepts related to the query
            3. A synthesized response that integrates the information
            """

        # Create the prompt
        prompt = f"""
        Query: {message}

        Analysis Type: {self.analysis_depth.upper()}

        {analysis_instructions}

        Documents:
        {json.dumps(docs_with_metadata, indent=2)}

        Please provide your {self.analysis_depth} analysis based on these documents.
        """

        # Generate the response
        response = self.provider.generate(
            prompt,
            max_tokens=self.max_tokens
        )

        return response

    def process_message_streaming(
        self, message: str, callback: Callable[[str, str], None]
    ) -> str:
        """Process a message with streaming response.

        Args:
            message: The user message to process
            callback: Function to call with each chunk of the response

        Returns:
            The complete response
        """
        # Retrieve documents (same as non-streaming)
        documents = self.knowledge_base.retrieve(message)
        documents = documents[:self.document_count]

        docs_with_metadata = []
        for doc in documents:
            docs_with_metadata.append({
                "content": doc["content"],
                "source": doc["metadata"].get("source", "Unknown"),
                "relevance": doc["relevance_score"]
            })

        # Generate the same prompt as non-streaming
        if self.analysis_depth == "deep":
            analysis_instructions = """
            Perform a deep analysis of the provided documents. Your analysis should include:
            1. Key themes and concepts across all documents
            2. Detailed examination of each document's main points
            3. Identification of any contradictions or inconsistencies
            4. Synthesis of the information into a comprehensive understanding
            5. Specific examples and quotes from the documents
            """
        elif self.analysis_depth == "comprehensive":
            analysis_instructions = """
            Perform a comprehensive analysis of the provided documents. Your analysis should include:
            1. Exhaustive examination of all themes, concepts, and ideas
            2. Detailed breakdown of each document with extensive quotes
            3. Cross-referencing information between documents
            4. Multiple levels of interpretation for complex concepts
            5. Historical context and development of ideas over time
            6. Implications and potential future developments
            7. Structured organization with clear sections for each aspect
            """
        else:  # standard
            analysis_instructions = """
            Analyze the provided documents to extract the most relevant information. Your analysis should include:
            1. Main points from each document
            2. Key concepts related to the query
            3. A synthesized response that integrates the information
            """

        prompt = f"""
        Query: {message}

        Analysis Type: {self.analysis_depth.upper()}

        {analysis_instructions}

        Documents:
        {json.dumps(docs_with_metadata, indent=2)}

        Please provide your {self.analysis_depth} analysis based on these documents.
        """

        # Use the provider's streaming method
        return self.provider.generate_streaming(
            prompt,
            callback,
            max_tokens=self.max_tokens
        )

# Register the custom agent with the agent registry
def register_custom_agent():
    """Register the custom agent with the agent registry."""
    from atlas.agents.registry import AgentRegistry

    # Register the agent class
    AgentRegistry.register(
        "specialized_analysis",
        SpecializedAnalysisAgent,
        description="Specialized agent for in-depth document analysis with configurable depth"
    )

    logging.info("Registered specialized analysis agent with registry")

# Example usage
def main():
    """Demonstrate the custom agent."""
    import os

    # Enable test mode for example purposes
    os.environ["SKIP_API_KEY_CHECK"] = "true"

    # Register the custom agent
    register_custom_agent()

    # Create a configuration
    config = AtlasConfig()

    # Create the custom agent
    agent = SpecializedAnalysisAgent(
        config=config,
        provider_name="anthropic",
        analysis_depth="deep"
    )

    # Process a message
    query = "How does Atlas's knowledge graph structure support the trimodal methodology?"
    print(f"Query: {query}")
    print("\nGenerating deep analysis...")

    response = agent.process_message(query)
    print("\nAnalysis:\n")
    print(response)

if __name__ == "__main__":
    main()
```

### Key Components

1. **Custom Agent Class**: Extends the BaseAgent with specialized functionality
2. **Agent Registration**: Registers the agent with the AgentRegistry for discovery
3. **Configurable Behavior**: Depth settings for different analysis levels
4. **Knowledge Integration**: Uses the existing knowledge base infrastructure
5. **Streaming Support**: Implements both standard and streaming interfaces

## Implementation Examples

These examples are provided as conceptual guides rather than fully executable code. To use them in a real application, you would need to:

1. Adapt them to your specific requirements
2. Install any additional dependencies
3. Create necessary supporting files (e.g., HTML templates for the web UI)
4. Properly handle API keys and authentication for production use

## Related Documentation

- [Multi-Agent Workflow](../../workflows/multi_agent.md) - Details on multi-agent architecture
- [Custom Workflows](../../workflows/custom_workflows.md) - Building custom workflows with LangGraph
- [API Reference](../../reference/api.md) - Complete API documentation
