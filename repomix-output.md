This file is a merged representation of the entire codebase, combined into a single document by Repomix.
The content has been processed where empty lines have been removed, content has been compressed (code blocks are separated by ⋮---- delimiter).

# Directory Structure
```
.claude/
  settings.local.json
atlas/
  agents/
    __init__.py
    base.py
    controller.py
    worker.py
  core/
    __init__.py
    config.py
    prompts.py
  graph/
    __init__.py
    nodes.py
    state.py
    workflows.py
  knowledge/
    __init__.py
    ingest.py
    retrieval.py
  orchestration/
    __init__.py
    coordinator.py
    parallel.py
    scheduler.py
  tools/
    __init__.py
    knowledge_retrieval.py
  agent.py
  ingest.py
.gitignore
.repomixignore
main.py
pyproject.toml
repomix.config.json
test_atlas.py
```

# Files

## File: .claude/settings.local.json
```json
{
  "permissions": {
    "allow": ["Bash(rm:*)", "WebFetch(domain:*)", "Bash(uv run:*)"],
    "deny": []
  }
}
```

## File: atlas/agents/__init__.py
```python
"""Agent implementations for Atlas."""
```

## File: atlas/agents/base.py
```python
"""
Base agent implementation for Atlas.
This module defines the core Atlas agent functionality.
"""
⋮----
class AtlasAgent
⋮----
"""Atlas agent for interacting with users."""
⋮----
"""Initialize the Atlas agent.
        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
        """
# Initialize configuration (use provided or create default)
⋮----
# Load the system prompt
⋮----
# Initialize the Anthropic client
⋮----
# Initialize knowledge base
⋮----
# Initialize conversation history
⋮----
def query_knowledge_base(self, query: str) -> List[Dict[str, Any]]
⋮----
"""Query the knowledge base for relevant information.
        Args:
            query: The query string.
        Returns:
            A list of relevant documents.
        """
⋮----
def process_message(self, message: str) -> str
⋮----
"""Process a user message and return the agent's response.
        Args:
            message: The user's message.
        Returns:
            The agent's response.
        """
⋮----
# Add user message to history
⋮----
# Retrieve relevant documents from the knowledge base
⋮----
documents = self.query_knowledge_base(message)
⋮----
# Print top documents for debugging
⋮----
source = doc["metadata"].get("source", "Unknown")
score = doc["relevance_score"]
⋮----
# Create system message with context
system_msg = self.system_prompt
⋮----
context_text = "\n\n## Relevant Knowledge\n\n"
for i, doc in enumerate(documents[:3]):  # Limit to top 3 most relevant docs
⋮----
content = doc["content"]
⋮----
system_msg = system_msg + context_text
# Generate response using Claude
response = self.anthropic_client.messages.create(
# Extract response text
assistant_message = response.content[0].text
# Add assistant response to history
```

## File: atlas/agents/controller.py
```python
"""
Controller agent for the Atlas framework.
This module implements the controller agent that orchestrates multiple worker agents.
"""
⋮----
class ControllerAgent(AtlasAgent)
⋮----
"""Controller agent that orchestrates multiple worker agents."""
⋮----
"""Initialize the controller agent.
        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            worker_count: Number of worker agents to create.
        """
# Initialize base agent
⋮----
# Update config with worker count
⋮----
# LangGraph workflow type
⋮----
# Worker management
⋮----
def process_message(self, message: str) -> str
⋮----
"""Process a user message using the controller-worker architecture.
        Args:
            message: The user's message.
        Returns:
            The agent's response.
        """
⋮----
# Add user message to history
⋮----
# Run the controller workflow
final_state = run_controller_workflow(
⋮----
system_prompt_file=None,  # Use default in workflow
⋮----
# Extract the response (last assistant message)
assistant_message = ""
⋮----
assistant_message = msg["content"]
⋮----
assistant_message = "I'm sorry, I couldn't generate a response."
# Add assistant response to history
⋮----
# Store worker results for later inspection if needed
⋮----
error_msg = "I'm sorry, I encountered an error processing your request. Please try again."
⋮----
def get_worker_results(self) -> Dict[str, Any]
⋮----
"""Get the results from all worker agents.
        Returns:
            A dictionary containing worker results.
        """
```

## File: atlas/agents/worker.py
```python
"""
Worker agent for the Atlas framework.
This module implements the worker agents that perform specialized tasks.
"""
⋮----
class WorkerAgent(AtlasAgent)
⋮----
"""Worker agent that performs specialized tasks."""
⋮----
"""Initialize the worker agent.
        Args:
            worker_id: Unique identifier for this worker.
            specialization: What this worker specializes in.
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
        """
# Initialize base agent
⋮----
# Worker identity
⋮----
# Enhance system prompt with worker specialization
specialization_addendum = f"""
⋮----
def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]
⋮----
"""Process a specific task assigned by the controller.
        Args:
            task: Task definition from the controller.
        Returns:
            Task result.
        """
⋮----
# Extract query from task
query = task.get("query", "")
⋮----
# Process query using basic RAG workflow
result = self.process_message(query)
# Return task result
⋮----
# Predefined worker types
class RetrievalWorker(WorkerAgent)
⋮----
"""Worker that specializes in document retrieval and summarization."""
⋮----
"""Initialize a retrieval worker."""
# Define specialization
specialization = "Information Retrieval and Document Summarization"
# Initialize worker
⋮----
class AnalysisWorker(WorkerAgent)
⋮----
"""Worker that specializes in query analysis and information needs identification."""
⋮----
"""Initialize an analysis worker."""
⋮----
specialization = "Query Analysis and Information Needs Identification"
⋮----
class DraftWorker(WorkerAgent)
⋮----
"""Worker that specializes in generating draft responses."""
⋮----
"""Initialize a draft worker."""
⋮----
specialization = "Response Generation and Content Creation"
```

## File: atlas/core/__init__.py
```python
"""Core functionality for Atlas."""
```

## File: atlas/core/config.py
```python
"""
Configuration for Atlas.
This module defines configuration options and settings for the Atlas framework.
"""
⋮----
class AtlasConfig
⋮----
"""Configuration for Atlas."""
⋮----
"""Initialize Atlas configuration.
        Args:
            anthropic_api_key: API key for Anthropic. If None, read from environment.
            collection_name: Name of the ChromaDB collection.
            db_path: Path to ChromaDB storage. If None, use default in home directory.
            model_name: Name of the Anthropic model to use.
            max_tokens: Maximum number of tokens in responses.
            parallel_enabled: Enable parallel processing with LangGraph.
            worker_count: Number of worker agents in parallel mode.
        """
# API key (from args or environment)
⋮----
# ChromaDB settings
⋮----
# Set DB path (default to user's home directory if not specified)
⋮----
home_dir = Path.home()
db_path = str(home_dir / "atlas_chroma_db")
⋮----
# Model settings
⋮----
# Parallel processing settings
⋮----
def to_dict(self) -> Dict[str, Any]
⋮----
"""Convert configuration to dictionary."""
# Note: We don't include the API key in the dict for security
```

## File: atlas/core/prompts.py
```python
"""
System prompts for Atlas.
This module defines the default system prompts used by Atlas agents.
"""
⋮----
# Default system prompt
DEFAULT_SYSTEM_PROMPT = """# **Atlas: Advanced Multi-Modal Learning & Guidance Framework**
def load_system_prompt(file_path: Optional[str] = None) -> str
⋮----
"""Load the system prompt from a file or use the default.
    Args:
        file_path: Optional path to a system prompt file.
    Returns:
        The system prompt string.
    """
⋮----
custom_prompt = f.read()
```

## File: atlas/graph/__init__.py
```python
"""LangGraph implementation for Atlas."""
```

## File: atlas/graph/nodes.py
```python
"""
Node functions for LangGraph in Atlas.
This module defines the node functions used in LangGraph workflows.
"""
⋮----
"""Retrieve knowledge from the Atlas knowledge base.
    Args:
        state: The current state of the agent.
        config: Optional configuration. If not provided, default values are used.
    Returns:
        Updated state with retrieved knowledge.
    """
# Use default config if none provided
cfg = config or AtlasConfig()
# Initialize knowledge base
kb = KnowledgeBase(collection_name=cfg.collection_name, db_path=cfg.db_path)
# Get the query from the last user message
messages = state.messages
⋮----
# Find the last user message
last_user_message = None
⋮----
last_user_message = message["content"]
⋮----
# Extract query and retrieve documents
query = last_user_message
⋮----
# Retrieve relevant documents
documents = kb.retrieve(query)
⋮----
# Print the top document sources for debugging
⋮----
source = doc["metadata"].get("source", "Unknown")
score = doc["relevance_score"]
⋮----
# Update state with retrieved documents
⋮----
"""Generate a response using the Anthropic API.
    Args:
        state: The current state of the agent.
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.
    Returns:
        Updated state with the generated response.
    """
⋮----
# Initialize Anthropic client
client = Anthropic(api_key=cfg.anthropic_api_key)
# Load system prompt
system_msg = load_system_prompt(system_prompt_file)
⋮----
# Add context to system prompt if available
⋮----
documents = state.context["documents"]
context_text = "\n\n## Relevant Knowledge\n\n"
for i, doc in enumerate(documents[:3]):  # Limit to top 3 most relevant docs
⋮----
content = doc["content"]
⋮----
system_msg = system_msg + context_text
# Get conversation history
conversation = state.messages
# Generate response
response = client.messages.create(
# Extract response text
assistant_message = response.content[0].text
# Add assistant response to history
⋮----
error_msg = "I'm sorry, I encountered an error processing your request. Please try again."
⋮----
# Mark processing as complete
⋮----
def route_to_workers(state: ControllerState) -> Union[str, None]
⋮----
"""Route the flow based on whether to use workers.
    Args:
        state: The controller state.
    Returns:
        The next node name or None to continue.
    """
⋮----
def create_worker_tasks(state: ControllerState) -> ControllerState
⋮----
"""Create tasks for worker agents.
    Args:
        state: The controller state.
    Returns:
        Updated controller state with tasks created.
    """
# Extract the user's query from the messages
user_query = ""
⋮----
user_query = message["content"]
⋮----
# Simple task creation (can be enhanced with more sophisticated task planning)
tasks = [
# Add tasks to state
⋮----
# Initialize worker states
⋮----
worker_id = task["worker_id"]
⋮----
# Create new worker state
worker_state = AgentState(
⋮----
def process_worker_results(state: ControllerState) -> ControllerState
⋮----
"""Process results from worker agents.
    Args:
        state: The controller state.
    Returns:
        Updated controller state with processed results.
    """
# Collect results from all workers
combined_results = []
⋮----
worker_state = state.workers.get(worker_id)
⋮----
# Get the last assistant message from the worker
⋮----
# Add combined results to state
⋮----
"""Generate a final response based on worker results.
    Args:
        state: The controller state.
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.
    Returns:
        Updated controller state with final response.
    """
⋮----
# Enhance system prompt with worker results
⋮----
results_text = "\n\n## Worker Results\n\n"
⋮----
worker_id = result["worker_id"]
content = result["content"]
⋮----
system_msg = system_msg + results_text
# Create synthesized prompt for final response
⋮----
synthesis_prompt = [
# Generate final response
⋮----
# Add final response to main conversation
⋮----
error_msg = "I'm sorry, I encountered an error synthesizing the results. Please try again."
⋮----
def should_end(state: Union[AgentState, ControllerState]) -> bool
⋮----
"""Determine if the graph execution should end.
    Args:
        state: The agent or controller state.
    Returns:
        True if execution should end, False otherwise.
    """
⋮----
else:  # ControllerState
```

## File: atlas/graph/state.py
```python
"""
State management for LangGraph in Atlas.
This module defines the state models used in LangGraph workflows.
"""
⋮----
class Message(TypedDict)
⋮----
"""Message in the conversation."""
role: str
content: str
class Document(TypedDict)
⋮----
"""Document from the knowledge base."""
⋮----
metadata: Dict[str, Any]
relevance_score: float
class Context(TypedDict)
⋮----
"""Context for the agent."""
documents: List[Document]
query: str
class WorkerConfig(BaseModel)
⋮----
"""Configuration for a worker agent."""
worker_id: str = Field(description="Unique identifier for the worker")
specialization: str = Field(description="What this worker specializes in")
system_prompt: str = Field(description="System prompt for this worker")
class AgentState(BaseModel)
⋮----
"""State for a LangGraph agent."""
# Basic state
messages: List[Message] = Field(default_factory=list, description="Conversation history")
context: Optional[Context] = Field(default=None, description="Retrieved context information")
# Worker agent state (for parallel processing)
worker_id: Optional[str] = Field(default=None, description="ID of the current worker (if any)")
worker_results: Dict[str, Any] = Field(default_factory=dict, description="Results from worker agents")
worker_configs: List[WorkerConfig] = Field(default_factory=list, description="Configurations for worker agents")
# Flags
process_complete: bool = Field(default=False, description="Whether processing is complete")
error: Optional[str] = Field(default=None, description="Error message if any")
class ControllerState(BaseModel)
⋮----
"""State for a controller agent managing multiple workers."""
# Main state
messages: List[Message] = Field(default_factory=list, description="Main conversation history")
⋮----
# Worker management
workers: Dict[str, AgentState] = Field(default_factory=dict, description="States for all workers")
active_workers: List[str] = Field(default_factory=list, description="Currently active worker IDs")
completed_workers: List[str] = Field(default_factory=list, description="IDs of workers that have completed")
# Task tracking
tasks: List[Dict[str, Any]] = Field(default_factory=list, description="Tasks to be processed")
results: List[Dict[str, Any]] = Field(default_factory=list, description="Results from completed tasks")
⋮----
all_tasks_assigned: bool = Field(default=False, description="Whether all tasks have been assigned")
all_tasks_completed: bool = Field(default=False, description="Whether all tasks have been completed")
```

## File: atlas/graph/workflows.py
```python
"""
Workflow definitions for LangGraph in Atlas.
This module defines the graph workflows used by Atlas agents.
"""
⋮----
"""Create a basic RAG workflow graph.
    Args:
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.
    Returns:
        A StateGraph for the basic RAG workflow.
    """
# Create StateGraph with AgentState
builder = StateGraph(AgentState)
# Use currying to pass additional parameters to node functions
def retrieve(state: AgentState) -> AgentState
def generate(state: AgentState) -> AgentState
# Add nodes
⋮----
# Define edges
⋮----
# Set the entry point
⋮----
# Compile the graph
⋮----
"""Create a controller-worker workflow graph.
    Args:
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.
    Returns:
        A StateGraph for the controller-worker workflow.
    """
# Create StateGraph with ControllerState
builder = StateGraph(ControllerState)
⋮----
def final_response(state: ControllerState) -> ControllerState
⋮----
# Add router node
⋮----
"""Get a workflow graph based on the specified type.
    Args:
        workflow_type: Type of workflow graph to create ('rag' or 'controller').
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.
    Returns:
        A StateGraph for the specified workflow type.
    """
⋮----
# Examples of how to run the workflows
⋮----
"""Run the basic RAG workflow.
    Args:
        query: User query to process.
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.
    Returns:
        Final state after workflow execution.
    """
# Create the graph
graph = create_basic_rag_graph(system_prompt_file, config)
# Create initial state
initial_state = AgentState(messages=[{"role": "user", "content": query}])
# Run the graph
final_state = graph.invoke(initial_state)
⋮----
"""Run the controller-worker workflow.
    Args:
        query: User query to process.
        system_prompt_file: Optional path to a system prompt file.
        config: Optional configuration. If not provided, default values are used.
    Returns:
        Final state after workflow execution.
    """
⋮----
graph = create_controller_worker_graph(system_prompt_file, config)
⋮----
initial_state = ControllerState(messages=[{"role": "user", "content": query}])
```

## File: atlas/knowledge/__init__.py
```python
"""Knowledge management for Atlas."""
```

## File: atlas/knowledge/ingest.py
```python
"""
Document ingestion for the Atlas framework.
This module handles processing Atlas documentation into a format
suitable for vector storage and retrieval.
"""
⋮----
class DocumentProcessor
⋮----
"""Initialize the document processor.
        Args:
            anthropic_api_key: Optional API key for Anthropic. If not provided,
                              it will be read from the ANTHROPIC_API_KEY environment variable.
            collection_name: Name of the Chroma collection to use.
            db_path: Optional path for ChromaDB storage. If None, use default in home directory.
        """
⋮----
# Create an absolute path for ChromaDB storage (use provided or default to home directory)
⋮----
home_dir = Path.home()
db_path = home_dir / "atlas_chroma_db"
⋮----
# List contents of directory to debug
⋮----
item_path = os.path.join(self.db_path, item)
⋮----
size = os.path.getsize(item_path) / 1024  # Size in KB
⋮----
# List all collections
⋮----
all_collections = self.chroma_client.list_collections()
⋮----
# Get or create collection
⋮----
# Get initial document count
⋮----
# Fallback to in-memory if persistence fails
⋮----
def _load_gitignore(self) -> pathspec.PathSpec
⋮----
"""Load the gitignore patterns from the repository.
        Returns:
            A PathSpec object with the gitignore patterns.
        """
gitignore_patterns = []
# Default ignore patterns (common files to ignore regardless of .gitignore)
default_patterns = [
# Add default patterns
⋮----
# Look for .gitignore files
gitignore_path = os.path.join(os.getcwd(), ".gitignore")
⋮----
line = line.strip()
# Skip comments and empty lines
⋮----
# Create PathSpec with gitignore patterns
⋮----
def is_ignored(self, path: str) -> bool
⋮----
"""Check if a path should be ignored based on gitignore patterns.
        Args:
            path: The path to check.
        Returns:
            True if the path should be ignored, False otherwise.
        """
# Convert to relative path
rel_path = os.path.relpath(path, os.getcwd())
⋮----
def get_all_markdown_files(self, base_dir: str) -> List[str]
⋮----
"""Get all markdown files in the specified directory and its subdirectories.
        Args:
            base_dir: The base directory to search from.
        Returns:
            A list of paths to markdown files.
        """
all_md_files = glob.glob(f"{base_dir}/**/*.md", recursive=True)
# Filter out ignored files
filtered_files = [f for f in all_md_files if not self.is_ignored(f)]
⋮----
def process_markdown_file(self, file_path: str) -> List[Dict[str, Any]]
⋮----
"""Process a markdown file into chunks suitable for vector storage.
        Args:
            file_path: Path to the markdown file.
        Returns:
            A list of document chunks with metadata.
        """
# Skip processing if file is in gitignore
⋮----
# Check file size and warn if it's very large
file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
⋮----
content = f.read()
⋮----
# Extract document sections based on headings
sections = self._split_by_headings(content, file_path)
# Create document chunks with metadata
chunks = []
rel_path = os.path.relpath(file_path, start=os.getcwd())
file_name = os.path.basename(file_path)
# Extract version from path (e.g., v1, v2, v3)
version_match = re.search(r"/v(\d+(?:\.\d+)?)/", file_path)
version = version_match.group(1) if version_match else "current"
⋮----
section_id = f"{rel_path}#{i}"
⋮----
def _split_by_headings(self, content: str, file_path: str = "") -> List[Dict[str, str]]
⋮----
"""Split markdown content by headings.
        Args:
            content: The markdown content.
            file_path: Optional file path for logging purposes.
        Returns:
            A list of sections with titles and text.
        """
# Match headings with the following pattern: one or more #'s followed by text
heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
# Find all headings
headings = list(heading_pattern.finditer(content))
sections = []
# If no headings, treat the entire document as one section
⋮----
# For large documents without headings, split into multiple chunks
content_size = len(content)
max_chunk_size = 2000  # Arbitrary chunk size to prevent extremely large chunks
# If content is very large, warn about it
⋮----
# Split large document into chunks
⋮----
chunk = content[i:i + max_chunk_size]
⋮----
# Process each section defined by headings
⋮----
title = match.group(2).strip()
start_pos = match.start()
# Determine end position (start of next heading or end of document)
⋮----
end_pos = headings[i + 1].start()
⋮----
end_pos = len(content)
# Get section text including the heading
section_text = content[start_pos:end_pos].strip()
# Check for very large sections and warn
⋮----
def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> None
⋮----
"""Generate embeddings for document chunks and store them in Chroma.
        Args:
            chunks: List of document chunks with metadata.
        """
⋮----
# Prepare data for Chroma
ids = [chunk["id"] for chunk in chunks]
texts = [chunk["text"] for chunk in chunks]
metadatas = [chunk["metadata"] for chunk in chunks]
# Add data to Chroma collection
⋮----
def process_directory(self, directory: str) -> None
⋮----
"""Process all markdown files in a directory and its subdirectories.
        Args:
            directory: The directory to process.
        """
files = self.get_all_markdown_files(directory)
⋮----
all_chunks = []
⋮----
chunks = self.process_markdown_file(file_path)
⋮----
# Report final stats
⋮----
final_doc_count = self.collection.count()
new_docs = final_doc_count - self.initial_doc_count
⋮----
def main()
⋮----
"""Main function to ingest Atlas documentation."""
processor = DocumentProcessor()
# Process each version directory
src_dirs = [
```

## File: atlas/knowledge/retrieval.py
```python
"""
Knowledge retrieval tools for the Atlas agent.
"""
⋮----
class KnowledgeBase
⋮----
def __init__(self, collection_name: str = "atlas_knowledge_base", db_path: Optional[str] = None)
⋮----
"""Initialize the knowledge base.
        Args:
            collection_name: Name of the Chroma collection to use.
            db_path: Optional path for ChromaDB storage. If None, use default in home directory.
        """
# Create an absolute path for ChromaDB storage (use provided or default to home directory)
⋮----
home_dir = Path.home()
db_path = home_dir / "atlas_chroma_db"
⋮----
# List contents of directory to debug
⋮----
item_path = os.path.join(self.db_path, item)
⋮----
size = os.path.getsize(item_path) / 1024  # Size in KB
⋮----
# List all collections
⋮----
all_collections = self.chroma_client.list_collections()
⋮----
# Get or create collection
⋮----
# Verify persistence by checking collection count
count = self.collection.count()
⋮----
"""Retrieve relevant documents based on a query.
        Args:
            query: The query to search for.
            n_results: Number of results to return.
            version_filter: Optional filter for specific Atlas version.
        Returns:
            A list of relevant documents with their metadata.
        """
# Prepare filters if any
where_clause = {}
⋮----
# Query the collection
⋮----
# Ensure we don't request more results than exist
doc_count = self.collection.count()
⋮----
actual_n_results = min(n_results, doc_count)
results = self.collection.query(
# Format results
documents = []
⋮----
- distance,  # Convert distance to relevance score
⋮----
def get_versions(self) -> List[str]
⋮----
"""Get all available Atlas versions in the knowledge base.
        Returns:
            A list of version strings.
        """
# This is a simple implementation that may need optimization for larger datasets
⋮----
# Adjust limit based on document count
limit = min(1000, doc_count)
results = self.collection.get(limit=limit)
versions = set()
⋮----
def search_by_topic(self, topic: str, n_results: int = 5) -> List[Dict[str, Any]]
⋮----
"""Search for documents related to a specific topic.
        Args:
            topic: The topic to search for.
            n_results: Number of results to return.
        Returns:
            A list of relevant documents with their metadata.
        """
# This could be enhanced with more sophisticated topic matching
⋮----
# Function for use with LangGraph
⋮----
"""Retrieve knowledge from the Atlas knowledge base.
    Args:
        state: The current state of the agent.
        query: Optional query override. If not provided, uses the user's last message.
        collection_name: Name of the Chroma collection to use.
    Returns:
        Updated state with retrieved knowledge.
    """
# Initialize knowledge base with specified collection
kb = KnowledgeBase(collection_name=collection_name)
# Get the query from the state if not explicitly provided
⋮----
messages = state.get("messages", [])
⋮----
last_user_message = None
⋮----
last_user_message = message.get("content", "")
⋮----
query = last_user_message
⋮----
# Retrieve relevant documents
documents = kb.retrieve(query)
⋮----
# Print the top document sources for debugging
⋮----
source = doc["metadata"].get("source", "Unknown")
score = doc["relevance_score"]
⋮----
# Update state with retrieved documents
```

## File: atlas/orchestration/__init__.py
```python
"""Agent orchestration for Atlas."""
```

## File: atlas/orchestration/coordinator.py
```python
"""
Agent coordination for Atlas.
This module provides tools for coordinating multiple agents.
"""
⋮----
class AgentCoordinator
⋮----
"""Coordinator for multiple Atlas agents."""
⋮----
"""Initialize the agent coordinator.
        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
            config: Optional configuration object. If not provided, default values are used.
            worker_count: Number of worker agents to create.
        """
# Use provided config or create default
⋮----
# System prompt file
⋮----
# Initialize controller
⋮----
# Initialize worker registry
⋮----
def _create_default_workers(self) -> None
⋮----
"""Create default worker agents."""
# Create retrieval worker
⋮----
# Create analysis worker
⋮----
# Create draft worker
⋮----
"""Add a new worker agent to the coordinator.
        Args:
            worker_type: Type of worker (custom worker).
            worker_id: Unique identifier for the worker.
            specialization: What the worker specializes in.
        Returns:
            The created worker agent.
        """
worker = WorkerAgent(
⋮----
def process_message(self, message: str) -> str
⋮----
"""Process a user message using the controller-worker architecture.
        Args:
            message: The user's message.
        Returns:
            The agent's response.
        """
# Use the controller to process the message
⋮----
def get_worker_results(self) -> Dict[str, Any]
⋮----
"""Get the results from all worker agents.
        Returns:
            A dictionary containing worker results.
        """
```

## File: atlas/orchestration/parallel.py
```python
"""
Parallel processing for Atlas agents.
This module provides tools for running agents in parallel.
"""
⋮----
"""Run multiple tasks in parallel using worker agents.
    Args:
        workers: Dictionary of worker agents.
        tasks: List of tasks to process.
    Returns:
        Dictionary of task results.
    """
# Match tasks to workers
task_assignments = {}
⋮----
worker_id = task.get("worker_id")
⋮----
# Find the worker for this task
worker = None
⋮----
worker = w
⋮----
# Process tasks with workers
async def process_worker_tasks(worker_id: str, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]
⋮----
results = []
⋮----
# Run task in separate thread to avoid blocking
loop = asyncio.get_event_loop()
⋮----
result = await loop.run_in_executor(
⋮----
# Create tasks for each worker
coroutines = [
# Run all tasks in parallel
all_results = await asyncio.gather(*coroutines)
# Flatten results
flattened_results = []
⋮----
# Group results by task ID
results_by_task = {}
⋮----
task_id = result.get("task_id", "unknown")
⋮----
"""Run tasks in parallel (synchronous wrapper for async function).
    Args:
        workers: Dictionary of worker agents.
        tasks: List of tasks to process.
    Returns:
        Dictionary of task results.
    """
# Use asyncio to run the parallel tasks
loop = asyncio.new_event_loop()
```

## File: atlas/orchestration/scheduler.py
```python
"""
Task scheduling for Atlas agents.
This module provides tools for scheduling and managing agent tasks.
"""
⋮----
class Task
⋮----
"""Task definition for Atlas agents."""
⋮----
"""Initialize a task.
        Args:
            task_id: Unique identifier for the task. If None, a random ID is generated.
            worker_id: ID of the worker assigned to this task.
            description: Description of the task.
            query: Query to process.
            priority: Task priority (higher value = higher priority).
            **kwargs: Additional task parameters.
        """
⋮----
# Add any additional parameters
⋮----
def to_dict(self) -> Dict[str, Any]
⋮----
"""Convert task to dictionary."""
⋮----
@classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task'
⋮----
"""Create a task from dictionary."""
task = cls(
# Set additional attributes
⋮----
class TaskScheduler
⋮----
"""Scheduler for Atlas agent tasks."""
def __init__(self)
⋮----
"""Initialize the task scheduler."""
⋮----
def add_task(self, task: Union[Task, Dict[str, Any]]) -> str
⋮----
"""Add a task to the scheduler.
        Args:
            task: Task to add (Task object or dictionary).
        Returns:
            Task ID.
        """
# Convert dictionary to Task if needed
⋮----
task = Task.from_dict(task)
# Store the task
⋮----
def get_task(self, task_id: str) -> Optional[Task]
⋮----
"""Get a task by ID.
        Args:
            task_id: Task ID.
        Returns:
            Task if found, None otherwise.
        """
⋮----
def get_next_task(self) -> Optional[Task]
⋮----
"""Get the next task to process.
        Returns:
            Next task to process, None if no tasks are pending.
        """
⋮----
# Sort pending tasks by priority (descending)
sorted_tasks = sorted(
# Get the highest priority task
next_task = sorted_tasks[0]
# Update task status
⋮----
# Update task lists
⋮----
def complete_task(self, task_id: str, result: Any = None) -> bool
⋮----
"""Mark a task as completed.
        Args:
            task_id: Task ID.
            result: Task result.
        Returns:
            True if the task was completed, False otherwise.
        """
task = self.tasks.get(task_id)
⋮----
def fail_task(self, task_id: str, error: str = "") -> bool
⋮----
"""Mark a task as failed.
        Args:
            task_id: Task ID.
            error: Error message.
        Returns:
            True if the task was failed, False otherwise.
        """
⋮----
def get_stats(self) -> Dict[str, int]
⋮----
"""Get scheduler statistics.
        Returns:
            Dictionary with task counts.
        """
```

## File: atlas/tools/__init__.py
```python
"""
Tools for the Atlas agent framework.
"""
```

## File: atlas/tools/knowledge_retrieval.py
```python
"""
Knowledge retrieval tools for the Atlas agent.
"""
⋮----
class KnowledgeBase
⋮----
def __init__(self, collection_name: str = "atlas_knowledge_base")
⋮----
"""Initialize the knowledge base.
        Args:
            collection_name: Name of the Chroma collection to use.
        """
# Create an absolute path for ChromaDB storage in user's home directory
home_dir = Path.home()
db_path = home_dir / "atlas_chroma_db"
⋮----
# List contents of directory to debug
⋮----
item_path = os.path.join(self.db_path, item)
⋮----
size = os.path.getsize(item_path) / 1024  # Size in KB
⋮----
# List all collections
⋮----
all_collections = self.chroma_client.list_collections()
⋮----
# Get or create collection
⋮----
# Verify persistence by checking collection count
count = self.collection.count()
⋮----
"""Retrieve relevant documents based on a query.
        Args:
            query: The query to search for.
            n_results: Number of results to return.
            version_filter: Optional filter for specific Atlas version.
        Returns:
            A list of relevant documents with their metadata.
        """
# Prepare filters if any
where_clause = {}
⋮----
# Query the collection
⋮----
# Ensure we don't request more results than exist
doc_count = self.collection.count()
⋮----
actual_n_results = min(n_results, doc_count)
results = self.collection.query(
# Format results
documents = []
⋮----
- distance,  # Convert distance to relevance score
⋮----
def get_versions(self) -> List[str]
⋮----
"""Get all available Atlas versions in the knowledge base.
        Returns:
            A list of version strings.
        """
# This is a simple implementation that may need optimization for larger datasets
⋮----
# Adjust limit based on document count
limit = min(1000, doc_count)
results = self.collection.get(limit=limit)
versions = set()
⋮----
def search_by_topic(self, topic: str, n_results: int = 5) -> List[Dict[str, Any]]
⋮----
"""Search for documents related to a specific topic.
        Args:
            topic: The topic to search for.
            n_results: Number of results to return.
        Returns:
            A list of relevant documents with their metadata.
        """
# This could be enhanced with more sophisticated topic matching
⋮----
# Function for use within LangGraph
⋮----
"""Retrieve knowledge from the Atlas knowledge base.
    Args:
        state: The current state of the agent.
        query: Optional query override. If not provided, uses the user's last message.
        collection_name: Name of the Chroma collection to use.
    Returns:
        Updated state with retrieved knowledge.
    """
# Initialize knowledge base with specified collection
kb = KnowledgeBase(collection_name=collection_name)
# Get the query from the state if not explicitly provided
⋮----
messages = state.get("messages", [])
⋮----
last_user_message = None
⋮----
last_user_message = message.get("content", "")
⋮----
query = last_user_message
⋮----
# Retrieve relevant documents
documents = kb.retrieve(query)
⋮----
# Print the top document sources for debugging
⋮----
source = doc["metadata"].get("source", "Unknown")
score = doc["relevance_score"]
⋮----
# Update state with retrieved documents
```

## File: atlas/agent.py
```python
"""
Atlas agent implementation using LangGraph.
This module defines the main Atlas agent workflow and capabilities.
"""
⋮----
# Default system prompt
DEFAULT_SYSTEM_PROMPT = """# **Atlas: Advanced Multi-Modal Learning & Guidance Framework**
def load_system_prompt(file_path: Optional[str] = None) -> str
⋮----
"""Load the system prompt from a file or use the default.
    Args:
        file_path: Optional path to a system prompt file.
    Returns:
        The system prompt string.
    """
⋮----
custom_prompt = f.read()
⋮----
class AtlasAgent
⋮----
"""Atlas agent for interacting with users."""
def __init__(self, system_prompt_file: Optional[str] = None, collection_name: str = "atlas_knowledge_base")
⋮----
"""Initialize the Atlas agent.
        Args:
            system_prompt_file: Optional path to a file containing the system prompt.
            collection_name: Name of the Chroma collection to use.
        """
# Load the system prompt
⋮----
# Initialize the Anthropic client
⋮----
# Initialize conversation history
⋮----
def query_knowledge_base(self, query: str) -> List[Dict[str, Any]]
⋮----
"""Query the knowledge base for relevant information.
        Args:
            query: The query string.
        Returns:
            A list of relevant documents.
        """
# Create a fake state to use with retrieve_knowledge
state = {"messages": [{"role": "user", "content": query}]}
# Call retrieve_knowledge directly
updated_state = retrieve_knowledge(state, query=query, collection_name=self.collection_name)
# Return the documents
⋮----
def process_message(self, message: str) -> str
⋮----
"""Process a user message and return the agent's response.
        Args:
            message: The user's message.
        Returns:
            The agent's response.
        """
⋮----
# Add user message to history
⋮----
# Retrieve relevant documents from the knowledge base
⋮----
documents = self.query_knowledge_base(message)
⋮----
# Print top documents for debugging
⋮----
source = doc["metadata"].get("source", "Unknown")
score = doc["relevance_score"]
⋮----
# Create system message with context
system_msg = self.system_prompt
⋮----
context_text = "\n\n## Relevant Knowledge\n\n"
for i, doc in enumerate(documents[:3]):  # Limit to top 3 most relevant docs
⋮----
content = doc["content"]
⋮----
system_msg = system_msg + context_text
# Generate response using Claude
response = self.anthropic_client.messages.create(
# Extract response text
assistant_message = response.content[0].text
# Add assistant response to history
⋮----
# Simple CLI for testing the agent directly
⋮----
parser = argparse.ArgumentParser(description="Atlas Agent CLI")
⋮----
args = parser.parse_args()
# Check for environment variables
⋮----
# Process directory if provided
⋮----
processor = DocumentProcessor(collection_name=args.collection)
⋮----
# Initialize agent
agent = AtlasAgent(system_prompt_file=args.system_prompt, collection_name=args.collection)
# Start interactive session
⋮----
# Get user input
⋮----
user_input = input("\nYou: ")
# Check for exit command
⋮----
# Process the message and get response
response = agent.process_message(user_input)
# Display the response
```

## File: atlas/ingest.py
```python
"""
Document ingestion for the Atlas framework.
This module handles processing Atlas documentation into a format
suitable for vector storage and retrieval.
"""
⋮----
class DocumentProcessor
⋮----
def __init__(self, anthropic_api_key: Optional[str] = None, collection_name: str = "atlas_knowledge_base")
⋮----
"""Initialize the document processor.
        Args:
            anthropic_api_key: Optional API key for Anthropic. If not provided,
                              it will be read from the ANTHROPIC_API_KEY environment variable.
            collection_name: Name of the Chroma collection to use.
        """
⋮----
# Create an absolute path for ChromaDB storage in user's home directory
home_dir = Path.home()
db_path = home_dir / "atlas_chroma_db"
⋮----
# List contents of directory to debug
⋮----
item_path = os.path.join(self.db_path, item)
⋮----
size = os.path.getsize(item_path) / 1024  # Size in KB
⋮----
# List all collections
⋮----
all_collections = self.chroma_client.list_collections()
⋮----
# Get or create collection
⋮----
# Get initial document count
⋮----
# Fallback to in-memory if persistence fails
⋮----
def _load_gitignore(self) -> pathspec.PathSpec
⋮----
"""Load the gitignore patterns from the repository.
        Returns:
            A PathSpec object with the gitignore patterns.
        """
gitignore_patterns = []
# Default ignore patterns (common files to ignore regardless of .gitignore)
default_patterns = [
# Add default patterns
⋮----
# Look for .gitignore files
gitignore_path = os.path.join(os.getcwd(), ".gitignore")
⋮----
line = line.strip()
# Skip comments and empty lines
⋮----
# Create PathSpec with gitignore patterns
⋮----
def is_ignored(self, path: str) -> bool
⋮----
"""Check if a path should be ignored based on gitignore patterns.
        Args:
            path: The path to check.
        Returns:
            True if the path should be ignored, False otherwise.
        """
# Convert to relative path
rel_path = os.path.relpath(path, os.getcwd())
⋮----
def get_all_markdown_files(self, base_dir: str) -> List[str]
⋮----
"""Get all markdown files in the specified directory and its subdirectories.
        Args:
            base_dir: The base directory to search from.
        Returns:
            A list of paths to markdown files.
        """
all_md_files = glob.glob(f"{base_dir}/**/*.md", recursive=True)
# Filter out ignored files
filtered_files = [f for f in all_md_files if not self.is_ignored(f)]
⋮----
def process_markdown_file(self, file_path: str) -> List[Dict[str, Any]]
⋮----
"""Process a markdown file into chunks suitable for vector storage.
        Args:
            file_path: Path to the markdown file.
        Returns:
            A list of document chunks with metadata.
        """
# Skip processing if file is in gitignore
⋮----
# Check file size and warn if it's very large
file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
⋮----
content = f.read()
⋮----
# Extract document sections based on headings
sections = self._split_by_headings(content, file_path)
# Create document chunks with metadata
chunks = []
rel_path = os.path.relpath(file_path, start=os.getcwd())
file_name = os.path.basename(file_path)
# Extract version from path (e.g., v1, v2, v3)
version_match = re.search(r"/v(\d+(?:\.\d+)?)/", file_path)
version = version_match.group(1) if version_match else "current"
⋮----
section_id = f"{rel_path}#{i}"
⋮----
def _split_by_headings(self, content: str, file_path: str = "") -> List[Dict[str, str]]
⋮----
"""Split markdown content by headings.
        Args:
            content: The markdown content.
            file_path: Optional file path for logging purposes.
        Returns:
            A list of sections with titles and text.
        """
# Match headings with the following pattern: one or more #'s followed by text
heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
# Find all headings
headings = list(heading_pattern.finditer(content))
sections = []
# If no headings, treat the entire document as one section
⋮----
# For large documents without headings, split into multiple chunks
content_size = len(content)
max_chunk_size = 2000  # Arbitrary chunk size to prevent extremely large chunks
# If content is very large, warn about it
⋮----
# Split large document into chunks
⋮----
chunk = content[i:i + max_chunk_size]
⋮----
# Process each section defined by headings
⋮----
title = match.group(2).strip()
start_pos = match.start()
# Determine end position (start of next heading or end of document)
⋮----
end_pos = headings[i + 1].start()
⋮----
end_pos = len(content)
# Get section text including the heading
section_text = content[start_pos:end_pos].strip()
# Check for very large sections and warn
⋮----
def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> None
⋮----
"""Generate embeddings for document chunks and store them in Chroma.
        Args:
            chunks: List of document chunks with metadata.
        """
⋮----
# Prepare data for Chroma
ids = [chunk["id"] for chunk in chunks]
texts = [chunk["text"] for chunk in chunks]
metadatas = [chunk["metadata"] for chunk in chunks]
# Add data to Chroma collection
⋮----
def process_directory(self, directory: str) -> None
⋮----
"""Process all markdown files in a directory and its subdirectories.
        Args:
            directory: The directory to process.
        """
files = self.get_all_markdown_files(directory)
⋮----
all_chunks = []
⋮----
chunks = self.process_markdown_file(file_path)
⋮----
# Report final stats
⋮----
final_doc_count = self.collection.count()
new_docs = final_doc_count - self.initial_doc_count
⋮----
def main()
⋮----
"""Main function to ingest Atlas documentation."""
processor = DocumentProcessor()
# Process each version directory
src_dirs = [
```

## File: main.py
```python
#!/usr/bin/env python3
"""
Atlas: Advanced Multi-Modal Learning & Guidance Framework
Main entry point for the Atlas module.
"""
⋮----
# Ensure atlas package is importable
⋮----
def parse_args()
⋮----
"""Parse command-line arguments."""
parser = argparse.ArgumentParser(
# Core arguments
⋮----
# System prompt and knowledge base
⋮----
# Ingestion options
⋮----
# LangGraph options
⋮----
# Query options
⋮----
def check_environment()
⋮----
"""Check for required environment variables."""
api_key = os.environ.get("ANTHROPIC_API_KEY")
⋮----
def ingest_documents(args)
⋮----
"""Ingest documents from the specified directory."""
⋮----
processor = DocumentProcessor(collection_name=args.collection)
⋮----
def run_cli_mode(args)
⋮----
"""Run Atlas in interactive CLI mode."""
⋮----
# Initialize agent
agent = AtlasAgent(system_prompt_file=args.system_prompt, collection_name=args.collection)
⋮----
# Get user input
⋮----
user_input = input("\nYou: ")
# Check for exit command
⋮----
# Process the message and get response
response = agent.process_message(user_input)
# Display the response
⋮----
def run_query_mode(args)
⋮----
"""Run Atlas in query mode (single query, non-interactive)."""
⋮----
response = agent.process_message(args.query)
⋮----
def run_controller_mode(args)
⋮----
"""Run Atlas in controller mode."""
⋮----
# This will be implemented later when we add LangGraph integration
⋮----
def run_worker_mode(args)
⋮----
"""Run Atlas in worker mode."""
⋮----
def main()
⋮----
"""Main entry point for Atlas."""
args = parse_args()
# Check environment
⋮----
# Run the appropriate mode
success = True
⋮----
success = ingest_documents(args)
⋮----
success = run_query_mode(args)
⋮----
success = run_controller_mode(args)
⋮----
success = run_worker_mode(args)
```

## File: pyproject.toml
```toml
[project]
name = "atlas"
version = "0.1.0"
description = "Advanced Multi-Modal Learning & Guidance Framework"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "langgraph>=0.0.27",
    "chromadb>=0.4.18",
    "anthropic>=0.16.0",
    "pydantic>=2.0.0",
    "pathspec>=0.11.0",
]

[project.scripts]
atlas = "main:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["atlas"]
```

## File: test_atlas.py
```python
#!/usr/bin/env python3
"""
Test script for the Atlas framework.
This script tests different aspects of the Atlas framework implementation.
"""
⋮----
# Add the project root to the Python path
⋮----
def test_base_agent(args)
⋮----
"""Test the base Atlas agent."""
⋮----
# Initialize agent
agent = AtlasAgent(system_prompt_file=args.system_prompt)
# Process a test message
⋮----
query = args.query
⋮----
query = "What is the trimodal methodology in Atlas?"
⋮----
response = agent.process_message(query)
⋮----
def test_controller_agent(args)
⋮----
"""Test the controller agent with workers."""
⋮----
# Initialize controller
controller = ControllerAgent(
⋮----
query = "Explain the knowledge graph structure in Atlas."
⋮----
response = controller.process_message(query)
⋮----
# Get worker results
worker_results = controller.get_worker_results()
⋮----
def test_coordinator(args)
⋮----
"""Test the agent coordinator."""
⋮----
# Initialize coordinator
coordinator = AgentCoordinator(
⋮----
query = "How does Atlas implement perspective frameworks?"
⋮----
response = coordinator.process_message(query)
⋮----
def test_workflows(args)
⋮----
"""Test LangGraph workflows."""
⋮----
# Create config
config = AtlasConfig(
# Test RAG workflow
⋮----
query = "What are the communication principles in Atlas?"
⋮----
# Run the workflow
rag_result = run_rag_workflow(
# Extract response
response = ""
⋮----
response = msg["content"]
⋮----
# Test controller workflow
⋮----
controller_result = run_controller_workflow(
⋮----
def parse_args()
⋮----
"""Parse command-line arguments."""
parser = argparse.ArgumentParser(description="Test the Atlas framework")
# Test options
⋮----
# General options
⋮----
def main()
⋮----
"""Main entry point for testing."""
args = parse_args()
# Check for environment variables
⋮----
# Run tests
```

## File: .repomixignore
```
### Operating System Files ###

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini
$RECYCLE.BIN/
*.cab
*.msi
*.msm
*.msp
*.lnk

# macOS
.DS_Store
.AppleDouble
.LSOverride
Icon
._*
.Spotlight-V100
.Trashes
.AppleDB
.AppleDesktop
Network Trash Folder
Temporary Items
.apdisk

# Linux
*~
.fuse_hidden*
.directory
.Trash-*
.nfs*

### Editor Files ###

# VS Code
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json

# Sublime Text
*.sublime-workspace
*.sublime-project

# JetBrains IDEs
.idea/
*.iml
*.iws
*.ipr

# Vim
[._]*.s[a-v][a-z]
[._]*.sw[a-p]
Session.vim
.netrwhist

# Emacs
\#*\#
*~
.\#*
.org-id-locations
*_archive

### Documentation Specific ###

# Build output
_site/
public/
dist/
build/

# Dependencies
node_modules/
vendor/

# Log files
*.log
npm-debug.log*
yarn-debug.log*

# Temp files
*.tmp
*.bak
*.swp

# Local development
.env
.env.local

### Python Specific ###

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
.venv/
.env/
.python-version

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

### Project Specific ###

# Root
README.md

# Markdown Source
src-markdown/
!src-markdown/CLAUDE_new.md
!src-markdown/quantum
!src-markdown/templates
!src-markdown/prev/v5
```

## File: repomix.config.json
```json
{
  "ignore": {
    "customPatterns": [],
    "useDefaultPatterns": true,
    "useGitignore": true
  },
  "include": [],
  "input": {
    "maxFileSize": 52428800
  },
  "output": {
    "compress": true,
    "copyToClipboard": false,
    "directoryStructure": true,
    "filePath": "repomix-output.md",
    "files": true,
    "fileSummary": false,
    "git": {
      "sortByChanges": true,
      "sortByChangesMaxCommits": 100
    },
    "parsableStyle": false,
    "removeComments": false,
    "removeEmptyLines": true,
    "showLineNumbers": false,
    "style": "markdown",
    "topFilesLength": 8
  },
  "security": {
    "enableSecurityCheck": true
  },
  "tokenCount": {
    "encoding": "o200k_base"
  }
}
```

## File: .gitignore
```
### Operating System Files ###

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini
$RECYCLE.BIN/
*.cab
*.msi
*.msm
*.msp
*.lnk

# macOS
.DS_Store
.AppleDouble
.LSOverride
Icon
._*
.Spotlight-V100
.Trashes
.AppleDB
.AppleDesktop
Network Trash Folder
Temporary Items
.apdisk

# Linux
*~
.fuse_hidden*
.directory
.Trash-*
.nfs*

### Editor Files ###

# VS Code
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json

# Sublime Text
*.sublime-workspace
*.sublime-project

# JetBrains IDEs
.idea/
*.iml
*.iws
*.ipr

# Vim
[._]*.s[a-v][a-z]
[._]*.sw[a-p]
Session.vim
.netrwhist

# Emacs
\#*\#
*~
.\#*
.org-id-locations
*_archive

### Documentation Specific ###

# Build output
_site/
public/
dist/
build/

# Dependencies
node_modules/
vendor/

# Log files
*.log
npm-debug.log*
yarn-debug.log*

# Temp files
*.tmp
*.bak
*.swp

# Local development
.env
.env.local

### Python Specific ###

# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
.venv/
.env/
.python-version

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
```
