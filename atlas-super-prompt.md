# Atlas Framework Super-Prompt

This document provides a comprehensive implementation guide for the Atlas Framework, an advanced multi-modal agent system designed for robust provider integration, knowledge retrieval, and tool-augmented interactions. The super-prompt covers all essential aspects required to recreate the system in a single implementation pass.

## 1. Core Architecture

Atlas is structured as a modular system with several key components:

1. **Provider System**: A unified interface to different LLM providers with capability-based selection.
2. **Agent System**: Various agent types with different specializations.
3. **Knowledge System**: Document ingestion, chunking, and retrieval.
4. **Graph System**: Workflow definition and execution using LangGraph.
5. **Tool System**: Extensible tool integration for agent augmentation.
6. **CLI System**: Command-line interface for user interaction.

```
┌───────────────┐  ┌───────────────┐  ┌────────────────┐
│    CLI API    │  │  Controllers  │  │  Tool Registry │
└───────┬───────┘  └───────┬───────┘  └────────┬───────┘
        │                  │                   │
┌───────┴──────────────────┴───────────────────┴───────┐
│                 Orchestration Layer                  │
└───────┬──────────────────┬───────────────────┬───────┘
        │                  │                   │
┌───────┴───────┐  ┌───────┴───────┐  ┌────────┴───────┐
│ Agent System  │  │ Graph System  │  │  Knowledge DB  │
└───────┬───────┘  └───────┬───────┘  └────────┬───────┘
        │                  │                   │
┌───────┴──────────────────┴───────────────────┴───────┐
│               Provider Abstraction Layer             │
└───────┬──────────────────┬───────────────────┬───────┘
        │                  │                   │
┌───────┴───────┐  ┌───────┴───────┐  ┌────────┴───────┐
│ OpenAI API    │  │ Anthropic API │  │   Ollama API   │
└───────────────┘  └───────────────┘  └────────────────┘
```

## 2. Design Principles

Atlas follows several key principles:

1. **Capability-Based Provider Selection**: Providers are selected based on task requirements using a capability registry.

2. **Multi-Modal Support**: Text and image content are handled through a unified message interface.

3. **Streaming-First Design**: All providers implement streaming interfaces with buffer management and control capabilities.

4. **Schema Validation**: Comprehensive schema validation ensures type safety and compatibility.

5. **Fault Tolerance**: Retry mechanisms, circuit breakers, and fallbacks ensure operational reliability.

6. **Extensibility**: The system is designed for extension through provider, agent, and tool registration.

7. **State-Based Workflows**: LangGraph integration enables complex, state-based workflows with conditional routing.

## 3. CLI Implementation

The CLI system serves as the primary interface for users and includes these key components:

### 3.1 Command Structure

```python
def parse_cli_args() -> dict:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Atlas - Advanced LLM Framework")

    # Common arguments
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Provider group
    provider_group = parser.add_argument_group("Provider Options")
    provider_group.add_argument("--provider", type=str, help="Provider to use (openai, anthropic, ollama, mock)")
    provider_group.add_argument("--model", type=str, help="Model to use")
    provider_group.add_argument("--capability", type=str, help="Required capability")
    provider_group.add_argument("--models", action="store_true", help="List available models for the provider")

    # Subcommands
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")

    # CLI mode parser
    cli_parser = subparsers.add_parser("cli", help="Interactive CLI mode")
    cli_parser.add_argument("--system-prompt", type=str, help="Custom system prompt")

    # Query mode parser
    query_parser = subparsers.add_parser("query", help="Single query mode")
    query_parser.add_argument("--query", "-q", type=str, required=True, help="Query text")
    query_parser.add_argument("--retrieve-only", action="store_true", help="Only retrieve documents, don't generate response")
    query_parser.add_argument("--stream", action="store_true", help="Enable streaming response")

    # Ingest mode parser
    ingest_parser = subparsers.add_parser("ingest", help="Document ingestion mode")
    ingest_parser.add_argument("--directory", "-d", type=str, help="Directory containing documents to ingest")
    ingest_parser.add_argument("--file", "-f", type=str, help="File to ingest")
    ingest_parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size for document splitting")
    ingest_parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap for document splitting")

    # Parse arguments
    args = parser.parse_args()

    # Convert args to dictionary
    args_dict = vars(args)

    # Add environment variables as fallbacks
    env_vars = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "OLLAMA_BASE_URL": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        "CHROMADB_DIR": os.environ.get("CHROMADB_DIR", "./chromadb")
    }

    args_dict["env_vars"] = env_vars

    return args_dict
```

### 3.2 Main Entry Point

```python
def main():
    """Main entry point."""
    # Parse CLI arguments
    args = parse_cli_args()

    # Create Atlas configuration
    config = create_atlas_config(args)

    # Configure logging
    log_level = logging.DEBUG if config["debug"] else (logging.INFO if config["verbose"] else logging.WARNING)
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # List models if requested
    if args.get("models"):
        provider_name = config["provider_options"]["provider_name"]
        if not provider_name:
            print("Error: Provider must be specified to list models")
            return

        registry = ProviderRegistry()
        models = registry.get_provider_models(provider_name)

        print(f"\nAvailable models for provider '{provider_name}':")
        for model in models:
            capabilities = registry.get_model_capabilities(provider_name, model)
            print(f"- {model}")
            if capabilities:
                print(f"  Capabilities: {', '.join(capabilities.get('supported', []))}")
        return

    # Run in selected mode
    mode = config["mode"]
    if mode == "cli":
        run_cli_mode(config)
    elif mode == "query":
        run_query_mode(config)
    elif mode == "ingest":
        ingest_documents(config)
    else:
        print(f"Error: Unknown mode '{mode}'. Use --help for usage information.")
```

### 3.3 Configuration Creation

```python
def create_provider_options(args: dict) -> dict:
    """Create provider options from CLI arguments."""
    options = {
        "provider_name": args.get("provider"),
        "model_name": args.get("model"),
        "capability": args.get("capability"),
        "api_keys": {
            "openai": args["env_vars"].get("OPENAI_API_KEY"),
            "anthropic": args["env_vars"].get("ANTHROPIC_API_KEY")
        },
        "base_urls": {
            "ollama": args["env_vars"].get("OLLAMA_BASE_URL")
        }
    }

    return options

def create_atlas_config(args: dict) -> dict:
    """Create Atlas configuration from CLI arguments."""
    config = {
        "verbose": args.get("verbose", False),
        "debug": args.get("debug", False),
        "provider_options": create_provider_options(args),
        "chromadb_dir": args["env_vars"].get("CHROMADB_DIR"),
        "system_prompt": args.get("system_prompt"),
        "stream": args.get("stream", False),
        "mode": args.get("mode"),
        "query": args.get("query"),
        "retrieve_only": args.get("retrieve_only", False),
        "ingest": {
            "directory": args.get("directory"),
            "file": args.get("file"),
            "chunk_size": args.get("chunk_size", 1000),
            "chunk_overlap": args.get("chunk_overlap", 200)
        }
    }

    return config
```

### 3.4 Mode Handlers

```python
def run_cli_mode(config: dict):
    """Run in interactive CLI mode."""
    # Create provider
    provider_options = config["provider_options"]
    provider = create_provider(
        provider_name=provider_options["provider_name"],
        model_name=provider_options["model_name"],
        capability=provider_options["capability"]
    )

    # Create agent
    agent = BaseAgent(provider, system_prompt=config.get("system_prompt"))

    # Interactive loop
    print("Atlas CLI - Type 'exit' to quit")
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ("exit", "quit"):
                break

            # Process user input
            if config.get("stream", False):
                print("\nAtlas: ", end="", flush=True)

                # Use streaming interface
                messages = agent._create_messages(user_input)
                request = GenerationRequest(messages=messages)
                stream_handler = provider.generate_stream(request)

                # Process stream
                for chunk in stream_handler.iter_chunks():
                    print(chunk, end="", flush=True)

                # Update history
                agent.message_history.append({"role": "user", "content": user_input})
                agent.message_history.append({"role": "assistant", "content": stream_handler.get_accumulated_content()})

                print("\n")
            else:
                # Use standard interface
                response = agent.process_message(user_input)
                print(f"\nAtlas: {response}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
```

## 4. Provider System

### 4.1 Base Provider Interface

```python
class ModelProvider(ABC):
    def __init__(self, model_name: str, options: Optional[dict] = None):
        self.model_name = model_name
        self.options = options or {}

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a response from the model."""
        pass

    @abstractmethod
    def generate_stream(self, request: GenerationRequest) -> StreamHandler:
        """Generate a streaming response from the model."""
        pass

    @abstractmethod
    def get_token_usage(self, request: GenerationRequest, response: GenerationResponse) -> TokenUsage:
        """Get the token usage for a request/response pair."""
        pass
```

### 4.2 Provider Registry

```python
class ProviderRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProviderRegistry, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._providers = {}
        self._capabilities = {}
        self._lock = threading.RLock()

    def register_provider(self, provider_name: str, provider_class: Type[ModelProvider],
                         models: List[str], capabilities: Dict[str, List[str]]):
        """Register a provider with its models and capabilities."""
        with self._lock:
            self._providers[provider_name] = provider_class
            for model in models:
                model_key = f"{provider_name}:{model}"
                self._capabilities[model_key] = capabilities

    def get_provider_for_capability(self, capability: str,
                                    preferred_providers: Optional[List[str]] = None) -> Tuple[str, str]:
        """Get the best provider and model for a capability."""
        with self._lock:
            candidates = []
            for model_key, caps in self._capabilities.items():
                if capability in caps.get("supported", []):
                    provider_name, model_name = model_key.split(":", 1)
                    candidates.append((provider_name, model_name, caps.get("ranking", {}).get(capability, 0)))

            if not candidates:
                raise NoCapableProviderError(f"No provider found for capability: {capability}")

            # Sort by ranking if preferred_providers is None, otherwise prioritize preferred providers
            if preferred_providers:
                candidates.sort(key=lambda x: (
                    0 if x[0] in preferred_providers else 1,
                    -x[2]  # Negative ranking for descending sort
                ))
            else:
                candidates.sort(key=lambda x: -x[2])  # Sort by ranking, descending

            return candidates[0][0], candidates[0][1]  # Return provider_name, model_name
```

### 4.3 Provider Factory

```python
def create_provider(provider_name: str, model_name: str = None,
                   capability: str = None, options: dict = None) -> ModelProvider:
    """Create a provider instance based on name, model, or capability."""
    registry = ProviderRegistry()

    # If capability is specified, find the best provider/model
    if capability and not model_name:
        provider_name, model_name = registry.get_provider_for_capability(capability)

    # If model_name is specified but provider_name is not, detect provider from model
    if model_name and not provider_name:
        provider_name = detect_provider_from_model(model_name)

    # Get the provider class
    provider_class = registry.get_provider_class(provider_name)
    if not provider_class:
        raise ProviderNotFoundError(f"Provider not found: {provider_name}")

    # Validate model compatibility
    if not registry.is_model_compatible(provider_name, model_name):
        raise ModelNotSupportedError(f"Model {model_name} not supported by provider {provider_name}")

    # Create and initialize the provider
    provider = provider_class(model_name=model_name, options=options)
    return provider
```

### 4.4 Streaming Implementation

```python
class StreamState(Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ERROR = "error"

class StreamControl:
    def pause(self) -> bool:
        """Pause the stream. Returns True if successful."""
        pass

    def resume(self) -> bool:
        """Resume the stream. Returns True if successful."""
        pass

    def cancel(self) -> bool:
        """Cancel the stream. Returns True if successful."""
        pass

class StreamHandler(StreamControl):
    def __init__(self):
        self._state = StreamState.INITIALIZING
        self._state_lock = threading.RLock()
        self._buffer = StreamBuffer()
        self._complete_event = threading.Event()

    def handle_chunk(self, chunk: str):
        """Process a new chunk from the stream."""
        with self._state_lock:
            if self._state == StreamState.ACTIVE:
                self._buffer.append(chunk)

    def complete(self):
        """Mark the stream as complete."""
        with self._state_lock:
            self._state = StreamState.COMPLETED
            self._complete_event.set()

    def get_accumulated_content(self) -> str:
        """Get all content received so far."""
        return self._buffer.get_content()

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for stream to complete. Returns True if completed, False if timed out."""
        return self._complete_event.wait(timeout)

    # StreamControl implementation
    def pause(self) -> bool:
        with self._state_lock:
            if self._state == StreamState.ACTIVE:
                self._state = StreamState.PAUSED
                return True
            return False

    def resume(self) -> bool:
        with self._state_lock:
            if self._state == StreamState.PAUSED:
                self._state = StreamState.ACTIVE
                return True
            return False

    def cancel(self) -> bool:
        with self._state_lock:
            if self._state in (StreamState.ACTIVE, StreamState.PAUSED):
                self._state = StreamState.CANCELLED
                self._complete_event.set()  # Signal completion for anyone waiting
                return True
            return False
```

### 4.5 Provider Implementation Example (Anthropic)

```python
class AnthropicProvider(ModelProvider):
    """Provider implementation for Anthropic Claude models."""

    def __init__(self, model_name: str, options: Optional[dict] = None):
        super().__init__(model_name, options)

        # Get API key from options or environment
        api_key = self.options.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise AuthenticationError("Anthropic API key not found")

        # Initialize client
        self.client = anthropic.Anthropic(api_key=api_key)

        # Set default parameters
        self.default_params = {
            "max_tokens": 1000,
            "temperature": 0.7,
        }

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a response from the model."""
        try:
            # Convert messages to Anthropic format
            messages = self._convert_messages(request.messages)

            # Get generation parameters
            params = self._get_generation_params(request)

            # Generate completion
            response = self.client.messages.create(
                model=self.model_name,
                messages=messages,
                max_tokens=params.get("max_tokens", 1000),
                temperature=params.get("temperature", 0.7),
                system=params.get("system")
            )

            # Create and return response
            return GenerationResponse(
                content=response.content[0].text,
                role="assistant",
                model=self.model_name,
                usage=self._get_token_usage_from_response(response)
            )

        except anthropic.APIError as e:
            # Map Anthropic errors to Atlas errors
            if e.status_code == 401:
                raise AuthenticationError(f"Anthropic authentication error: {str(e)}")
            elif e.status_code == 429:
                raise RateLimitError(f"Anthropic rate limit exceeded: {str(e)}")
            elif e.status_code >= 500:
                raise ServerError(f"Anthropic server error: {str(e)}")
            else:
                raise ProviderError(f"Anthropic API error: {str(e)}", provider="anthropic")

    def generate_stream(self, request: GenerationRequest) -> StreamHandler:
        """Generate a streaming response from the model."""
        # Create stream handler
        handler = EnhancedStreamHandler()

        # Start streaming in a separate thread
        threading.Thread(target=self._stream_worker, args=(request, handler)).start()

        return handler

    def _stream_worker(self, request: GenerationRequest, handler: StreamHandler):
        """Worker function for streaming responses."""
        try:
            # Convert messages to Anthropic format
            messages = self._convert_messages(request.messages)

            # Get generation parameters
            params = self._get_generation_params(request)

            # Create streaming request
            with self.client.messages.stream(
                model=self.model_name,
                messages=messages,
                max_tokens=params.get("max_tokens", 1000),
                temperature=params.get("temperature", 0.7),
                system=params.get("system")
            ) as stream:
                # Process stream events
                for event in stream:
                    if event.type == "content_block_delta" and event.delta.text:
                        handler.handle_chunk(event.delta.text)

                # Mark stream as complete
                handler.complete()

        except Exception as e:
            # Handle errors
            handler.set_error(str(e))

    def _convert_messages(self, messages: List[dict]) -> List[dict]:
        """Convert Atlas messages to Anthropic format."""
        result = []
        system = None

        for message in messages:
            role = message["role"].lower()
            content = message["content"]

            if role == "system":
                # Anthropic handles system messages differently
                system = content
                continue

            if role == "user":
                role = "user"
            elif role in ("assistant", "ai"):
                role = "assistant"
            else:
                # Skip unsupported roles
                continue

            result.append({"role": role, "content": content})

        return result, system

    def _get_generation_params(self, request: GenerationRequest) -> dict:
        """Get generation parameters from request."""
        params = self.default_params.copy()

        if request.max_tokens is not None:
            params["max_tokens"] = request.max_tokens

        if request.temperature is not None:
            params["temperature"] = request.temperature

        if request.top_p is not None:
            params["top_p"] = request.top_p

        return params

    def _get_token_usage_from_response(self, response) -> dict:
        """Get token usage from Anthropic response."""
        return {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }
```

## 5. Agent System

### 5.1 Base Agent Implementation

```python
class BaseAgent:
    def __init__(self, provider: ModelProvider, system_prompt: str = None):
        self.provider = provider
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.message_history = []

    def process_message(self, message: str, context: Optional[List[str]] = None) -> str:
        """Process a message and return a response."""
        # Format messages for the provider
        messages = self._create_messages(message, context)

        # Generate a response
        request = GenerationRequest(messages=messages)
        response = self.provider.generate(request)

        # Update history and return response content
        self.message_history.append({"role": "user", "content": message})
        self.message_history.append({"role": "assistant", "content": response.content})

        return response.content

    def _create_messages(self, message: str, context: Optional[List[str]] = None) -> List[dict]:
        """Create a list of messages for the provider."""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add context if provided
        if context:
            context_text = "\n\n".join(context)
            messages.append({
                "role": "system",
                "content": f"Additional context:\n\n{context_text}"
            })

        # Add message history
        messages.extend(self.message_history)

        # Add the current message
        messages.append({"role": "user", "content": message})

        return messages
```

### 5.2 Tool Agent Implementation

```python
class ToolAgent(BaseAgent):
    def __init__(self, provider: ModelProvider, system_prompt: str = None):
        super().__init__(provider, system_prompt)
        self.tools = {}
        self.tool_permissions = {}

    def register_tool(self, tool: Tool, grant_permission: bool = True):
        """Register a tool with the agent."""
        self.tools[tool.name] = tool
        if grant_permission:
            self.tool_permissions[tool.name] = True

    def has_permission(self, tool_name: str) -> bool:
        """Check if the agent has permission to use a tool."""
        return self.tool_permissions.get(tool_name, False)

    def process_message(self, message: str, context: Optional[List[str]] = None) -> str:
        """Process a message, executing tools as needed."""
        # Create initial messages with tool descriptions
        messages = self._create_messages(message, context)

        # Add tool descriptions to system message
        tool_descriptions = self._get_tool_descriptions()
        messages[0]["content"] += f"\n\nYou have access to the following tools:\n{tool_descriptions}"

        # Generate response
        request = GenerationRequest(messages=messages)
        response = self.provider.generate(request)

        # Parse tool calls from response
        tool_calls = self._extract_tool_calls(response.content)

        # Execute tool calls and incorporate results
        if tool_calls:
            tool_results = self._execute_tool_calls(tool_calls)

            # Add tool results to the conversation
            for result in tool_results:
                self.message_history.append({
                    "role": "tool",
                    "tool_name": result["tool_name"],
                    "content": result["result"]
                })

            # Generate final response incorporating tool results
            messages = self._create_messages(message, context)
            request = GenerationRequest(messages=messages)
            response = self.provider.generate(request)

        # Update history and return
        self.message_history.append({"role": "user", "content": message})
        self.message_history.append({"role": "assistant", "content": response.content})

        return response.content

    def _get_tool_descriptions(self) -> str:
        """Get formatted descriptions of available tools."""
        descriptions = []
        for name, tool in self.tools.items():
            if self.has_permission(name):
                descriptions.append(f"- {name}: {tool.description}")
                descriptions.append(f"  Parameters: {json.dumps(tool.parameters)}")
        return "\n".join(descriptions)

    def _extract_tool_calls(self, content: str) -> List[dict]:
        """Extract tool calls from response content."""
        # Simple regex-based extraction
        pattern = r"```json\s*(\{.*?\})\s*```"
        matches = re.findall(pattern, content, re.DOTALL)

        tool_calls = []
        for match in matches:
            try:
                data = json.loads(match)
                if "tool" in data and "parameters" in data:
                    tool_calls.append({
                        "tool_name": data["tool"],
                        "parameters": data["parameters"]
                    })
            except json.JSONDecodeError:
                continue

        return tool_calls

    def _execute_tool_calls(self, tool_calls: List[dict]) -> List[dict]:
        """Execute tool calls and return results."""
        results = []
        for call in tool_calls:
            tool_name = call["tool_name"]
            parameters = call["parameters"]

            if tool_name not in self.tools:
                results.append({
                    "tool_name": tool_name,
                    "result": f"Error: Tool '{tool_name}' not found."
                })
                continue

            if not self.has_permission(tool_name):
                results.append({
                    "tool_name": tool_name,
                    "result": f"Error: Permission denied for tool '{tool_name}'."
                })
                continue

            try:
                tool = self.tools[tool_name]
                result = tool.execute(**parameters)
                results.append({
                    "tool_name": tool_name,
                    "result": str(result)
                })
            except Exception as e:
                results.append({
                    "tool_name": tool_name,
                    "result": f"Error: {str(e)}"
                })

        return results
```

## 6. Knowledge System

### 6.1 Document Processing

```python
class Document:
    def __init__(self, content: str, metadata: Optional[dict] = None):
        self.content = content
        self.metadata = metadata or {}

class DocumentChunk:
    def __init__(self, content: str, metadata: Optional[dict] = None):
        self.content = content
        self.metadata = metadata or {}
        self.id = str(uuid.uuid4())

class Chunker(ABC):
    @abstractmethod
    def chunk(self, document: Document) -> List[DocumentChunk]:
        """Split a document into chunks."""
        pass

class FixedSizeChunker(Chunker):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: Document) -> List[DocumentChunk]:
        """Split document into fixed-size chunks with overlap."""
        text = document.content
        chunks = []

        if len(text) <= self.chunk_size:
            return [DocumentChunk(content=text, metadata=document.metadata)]

        # Split into overlapping chunks
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end > len(text):
                end = len(text)

            chunk_text = text[start:end]
            chunk_metadata = document.metadata.copy()
            chunk_metadata["chunk_index"] = len(chunks)

            chunks.append(DocumentChunk(content=chunk_text, metadata=chunk_metadata))

            # Move start position for next chunk, considering overlap
            start = end - self.chunk_overlap
            if start >= len(text) or start <= 0:
                break

        return chunks
```

### 6.2 Knowledge Base Implementation

```python
class KnowledgeBase:
    def __init__(self, client=None, collection_name: str = "atlas_documents"):
        self.client = client or chromadb.PersistentClient()
        self.collection_name = collection_name
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Get or create the ChromaDB collection."""
        try:
            return self.client.get_collection(self.collection_name)
        except:
            return self.client.create_collection(self.collection_name)

    def add_document(self, document: Document, chunker: Chunker = None):
        """Add a document to the knowledge base."""
        if chunker is None:
            chunker = FixedSizeChunker()

        chunks = chunker.chunk(document)

        # Prepare data for ChromaDB
        ids = [chunk.id for chunk in chunks]
        texts = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

    def retrieve(self, query: str, filter_dict: Optional[dict] = None, limit: int = 5) -> List[DocumentChunk]:
        """Retrieve relevant documents from the knowledge base."""
        results = self.collection.query(
            query_texts=[query],
            where=filter_dict,
            n_results=limit
        )

        chunks = []
        for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            chunks.append(DocumentChunk(
                content=doc,
                metadata=metadata
            ))

        return chunks
```

### 6.3 Hybrid Search Implementation

```python
class BM25:
    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = documents

        # Tokenize documents
        self.tokenized_docs = [self._tokenize(doc) for doc in documents]

        # Calculate document frequency for each term
        self.doc_freqs = {}
        for tokens in self.tokenized_docs:
            terms = set(tokens)
            for term in terms:
                if term in self.doc_freqs:
                    self.doc_freqs[term] += 1
                else:
                    self.doc_freqs[term] = 1

        # Calculate average document length
        self.avg_doc_len = sum(len(doc) for doc in self.tokenized_docs) / len(self.tokenized_docs)

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization by splitting on whitespace and lowercasing."""
        return text.lower().split()

    def score(self, query: str) -> List[float]:
        """Score all documents against the query."""
        query_terms = self._tokenize(query)
        scores = [0.0] * len(self.documents)

        for term in query_terms:
            if term not in self.doc_freqs:
                continue

            # Calculate IDF (Inverse Document Frequency)
            idf = math.log((len(self.documents) - self.doc_freqs[term] + 0.5) /
                          (self.doc_freqs[term] + 0.5) + 1.0)

            for i, tokens in enumerate(self.tokenized_docs):
                # Calculate term frequency
                term_freq = tokens.count(term)
                if term_freq == 0:
                    continue

                # Apply BM25 formula
                doc_len = len(tokens)
                numerator = term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
                scores[i] += idf * numerator / denominator

        return scores

class HybridSearcher:
    def __init__(self, knowledge_base: KnowledgeBase, semantic_weight: float = 0.7):
        self.knowledge_base = knowledge_base
        self.semantic_weight = semantic_weight

    def search(self, query: str, filter_dict: Optional[dict] = None, limit: int = 5) -> List[DocumentChunk]:
        """Perform hybrid search combining semantic and keyword search."""
        # Get all potential candidates with a larger limit
        candidate_limit = min(limit * 3, 20)  # Get more candidates for re-ranking
        candidates = self.knowledge_base.retrieve(query, filter_dict, candidate_limit)

        if not candidates:
            return []

        # Extract texts for BM25 scoring
        texts = [chunk.content for chunk in candidates]

        # Perform keyword search
        bm25 = BM25(texts)
        keyword_scores = bm25.score(query)

        # Normalize keyword scores
        max_keyword = max(keyword_scores) if keyword_scores else 1.0
        norm_keyword_scores = [s/max_keyword if max_keyword > 0 else 0 for s in keyword_scores]

        # Get semantic scores from the ChromaDB results
        # Assuming the scores are already normalized between 0 and 1
        semantic_scores = self.knowledge_base.collection.query(
            query_texts=[query],
            where=filter_dict,
            n_results=candidate_limit
        )["distances"][0]

        # Apply semantic weighting
        # Note: ChromaDB distances are smaller for better matches, so we invert
        semantic_scores = [1.0 - score for score in semantic_scores]

        # Combine scores
        combined_scores = []
        for i in range(len(candidates)):
            combined_score = (
                self.semantic_weight * semantic_scores[i] +
                (1 - self.semantic_weight) * norm_keyword_scores[i]
            )
            combined_scores.append((combined_score, i))

        # Sort by combined score (descending)
        combined_scores.sort(reverse=True)

        # Return top results
        results = []
        for _, idx in combined_scores[:limit]:
            results.append(candidates[idx])

        return results
```

## 7. Tool System

### 7.1 Tool Base Classes

```python
class Tool(ABC):
    def __init__(self, name: str, description: str, parameters: dict):
        self.name = name
        self.description = description
        self.parameters = parameters

    @abstractmethod
    def execute(self, **kwargs):
        """Execute the tool with the given parameters."""
        pass

class FunctionTool(Tool):
    def __init__(self, name: str, description: str, parameters: dict, func: Callable):
        super().__init__(name, description, parameters)
        self.func = func

    def execute(self, **kwargs):
        """Execute the function with the provided parameters."""
        return self.func(**kwargs)
```

### 7.2 Tool Registry

```python
class AgentToolkit:
    def __init__(self):
        self.tools = {}

    def register_tool(self, tool: Tool):
        """Register a tool in the toolkit."""
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def get_tool_descriptions(self) -> List[dict]:
        """Get descriptions of all tools in the toolkit."""
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append({
                "name": name,
                "description": tool.description,
                "parameters": tool.parameters
            })
        return descriptions
```

### 7.3 Example Tool Implementation

```python
class Calculator(Tool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        )

    def execute(self, expression: str):
        """Safely evaluate a mathematical expression."""
        # Define safe operations
        safe_dict = {
            'abs': abs, 'round': round,
            'max': max, 'min': min,
            'sum': sum, 'len': len,
            'pow': pow, 'int': int,
            'float': float, 'str': str,
            'sin': math.sin, 'cos': math.cos,
            'tan': math.tan, 'sqrt': math.sqrt,
            'pi': math.pi, 'e': math.e
        }

        try:
            # Evaluate the expression in a restricted environment
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            return str(result)
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"
```

## 8. LangGraph Integration

### 8.1 State Definitions

```python
class AgentState(TypedDict):
    query: str
    context: List[str]
    response: Optional[str]
    error: Optional[str]

class ControllerState(TypedDict):
    query: str
    task_list: List[dict]
    results: List[dict]
    response: Optional[str]
    error: Optional[str]
```

### 8.2 Node Functions

```python
def retrieve(state: AgentState) -> AgentState:
    """Retrieve documents relevant to the query."""
    query = state["query"]

    try:
        # Create knowledge base
        knowledge_base = KnowledgeBase()

        # Retrieve documents
        retriever = HybridSearcher(knowledge_base)
        documents = retriever.search(query, limit=5)

        # Update state with context
        context = [doc.content for doc in documents]
        return {"query": query, "context": context, "response": None, "error": None}
    except Exception as e:
        return {"query": query, "context": [], "response": None, "error": str(e)}

def generate(state: AgentState, provider: ModelProvider) -> AgentState:
    """Generate a response using context."""
    query = state["query"]
    context = state.get("context", [])
    error = state.get("error")

    if error:
        return {"query": query, "context": context, "response": f"Error: {error}", "error": error}

    try:
        # Create agent
        agent = BaseAgent(provider)

        # Generate response
        response = agent.process_message(query, context)

        return {"query": query, "context": context, "response": response, "error": None}
    except Exception as e:
        return {"query": query, "context": context, "response": f"Error: {str(e)}", "error": str(e)}
```

### 8.3 Graph Construction

```python
def create_query_workflow(provider: ModelProvider) -> Callable:
    """Create a LangGraph workflow for query processing."""
    # Define workflow
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", partial(generate, provider=provider))

    # Add edges
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    # Set entry point
    workflow.set_entry_point("retrieve")

    # Compile
    return workflow.compile()
```

### 8.4 Graph Execution

```python
def run_query_workflow(query: str, provider: ModelProvider) -> dict:
    """Run the query workflow."""
    # Create workflow
    workflow = create_query_workflow(provider)

    # Initialize state
    initial_state = {"query": query, "context": [], "response": None, "error": None}

    # Run workflow
    result = workflow.invoke(initial_state)

    return result
```

## 9. Error Handling System

### 9.1 Error Classes

```python
class AtlasError(Exception):
    """Base class for all Atlas errors."""
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(message)

class ProviderError(AtlasError):
    """Error from a provider."""
    def __init__(self, message: str, provider: str, code: Optional[str] = None):
        self.provider = provider
        super().__init__(f"Provider '{provider}' error: {message}", code)

class InvalidRequestError(AtlasError):
    """Error due to invalid request parameters."""
    pass

class AuthenticationError(AtlasError):
    """Error due to authentication failure."""
    pass

class RateLimitError(AtlasError):
    """Error due to rate limiting."""
    pass

class ServerError(AtlasError):
    """Error due to server-side issues."""
    pass

class TimeoutError(AtlasError):
    """Error due to request timeout."""
    pass

class ContentFilterError(AtlasError):
    """Error due to content filtering."""
    pass

class UnsupportedOperationError(AtlasError):
    """Error due to an unsupported operation."""
    pass

class ModelOverloadedError(AtlasError):
    """Error due to model being overloaded."""
    pass

class InvalidMessageError(AtlasError):
    """Error due to invalid message format."""
    pass

class InvalidContentError(AtlasError):
    """Error due to invalid content format."""
    pass

class NoCapableProviderError(AtlasError):
    """Error when no provider is found for a capability."""
    pass

class ProviderNotFoundError(AtlasError):
    """Error when a provider is not found."""
    pass

class ModelNotSupportedError(AtlasError):
    """Error when a model is not supported by a provider."""
    pass
```

### 9.2 Error Mapping

```python
def map_provider_error(provider: str, error: Exception) -> AtlasError:
    """Map provider-specific errors to Atlas errors."""

    # OpenAI error mapping
    if provider == "openai":
        import openai
        if isinstance(error, openai.AuthenticationError):
            return AuthenticationError(f"OpenAI authentication error: {str(error)}")
        elif isinstance(error, openai.RateLimitError):
            return RateLimitError(f"OpenAI rate limit exceeded: {str(error)}")
        elif isinstance(error, openai.APITimeoutError):
            return TimeoutError(f"OpenAI API timeout: {str(error)}")
        elif isinstance(error, openai.APIError) and error.status_code >= 500:
            return ServerError(f"OpenAI server error: {str(error)}")
        else:
            return ProviderError(f"OpenAI API error: {str(error)}", provider="openai")

    # Anthropic error mapping
    elif provider == "anthropic":
        import anthropic
        if isinstance(error, anthropic.AuthenticationError):
            return AuthenticationError(f"Anthropic authentication error: {str(error)}")
        elif isinstance(error, anthropic.RateLimitError):
            return RateLimitError(f"Anthropic rate limit exceeded: {str(error)}")
        elif isinstance(error, anthropic.APITimeoutError):
            return TimeoutError(f"Anthropic API timeout: {str(error)}")
        elif isinstance(error, anthropic.APIError) and error.status_code >= 500:
            return ServerError(f"Anthropic server error: {str(error)}")
        else:
            return ProviderError(f"Anthropic API error: {str(error)}", provider="anthropic")

    # Default error mapping
    else:
        return ProviderError(f"Provider error: {str(error)}", provider=provider)
```

### 9.3 Retry Mechanism

```python
def with_retry(max_retries: int = 3, backoff_factor: float = 1.5,
              retryable_errors: Tuple[Type[Exception]] = (ServerError, TimeoutError)):
    """Decorator for retrying operations with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check if error is retryable
                    if not isinstance(e, retryable_errors) or retries >= max_retries:
                        raise

                    # Calculate backoff time
                    backoff_time = backoff_factor * (2 ** retries)

                    # Log retry attempt
                    logger.warning(
                        f"Retry {retries + 1}/{max_retries} for {func.__name__} "
                        f"after {backoff_time:.2f}s due to {type(e).__name__}: {str(e)}"
                    )

                    # Wait before retry
                    time.sleep(backoff_time)

                    # Increment retry counter
                    retries += 1
        return wrapper
    return decorator
```

## 10. Schema Validation System

### 10.1 Schema Definitions

```python
class ProviderOptionsSchema(Schema):
    provider_name = fields.String(required=False, allow_none=True)
    model_name = fields.String(required=False, allow_none=True)
    capability = fields.String(required=False, allow_none=True)
    api_keys = fields.Dict(keys=fields.String(), values=fields.String(allow_none=True), required=False)
    base_urls = fields.Dict(keys=fields.String(), values=fields.String(), required=False)

    @post_load
    def make_provider_options(self, data, **kwargs):
        return ProviderOptions(**data)

class GenerationRequestSchema(Schema):
    messages = fields.List(fields.Dict(), required=True)
    stream = fields.Boolean(required=False, default=False)
    max_tokens = fields.Integer(required=False, allow_none=True)
    temperature = fields.Float(required=False, allow_none=True)
    top_p = fields.Float(required=False, allow_none=True)

    @post_load
    def make_generation_request(self, data, **kwargs):
        return GenerationRequest(**data)

class GenerationResponseSchema(Schema):
    content = fields.String(required=True)
    role = fields.String(required=False, default="assistant")
    model = fields.String(required=False, allow_none=True)
    usage = fields.Dict(required=False, allow_none=True)

    @post_load
    def make_generation_response(self, data, **kwargs):
        return GenerationResponse(**data)
```

### 10.2 Validation Decorators

```python
def validate_message_param(param_name: str = "message"):
    """Decorator to validate a message parameter."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the message parameter
            message = kwargs.get(param_name)
            if message is None and param_name == "message" and len(args) > 1:
                message = args[1]  # Assume second positional argument is the message

            if message is not None:
                # Validate and convert the message
                schema = MessageSchema()
                try:
                    if isinstance(message, dict):
                        validated_message = schema.load(message)

                        # Update args or kwargs with validated message
                        if param_name in kwargs:
                            kwargs[param_name] = validated_message
                        else:
                            args_list = list(args)
                            args_list[1] = validated_message
                            args = tuple(args_list)
                except ValidationError as e:
                    raise InvalidMessageError(f"Invalid message format: {str(e)}")

            return func(*args, **kwargs)
        return wrapper
    return decorator
```

## 11. Implementation Requirements

To implement this system, you'll need:

1. **Python 3.13+** with typing support
2. **Dependencies**:
   - langgraph>=0.4.1
   - chromadb>=1.0.7
   - anthropic>=0.50.0
   - openai>=1.5.0
   - marshmallow>=3.2.0

3. **API Keys for Providers**:
   - OpenAI API key
   - Anthropic API key
   - Ollama server (for local models)

4. **Local Storage**:
   - ChromaDB storage directory

## 12. Complete System Initialization

```python
import os
import json
import logging
import argparse
import threading
import math
import uuid
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Callable, Any, Tuple, Type, TypedDict
from abc import ABC, abstractmethod
from functools import partial, wraps
from enum import Enum

import chromadb
from langgraph.graph import StateGraph, END
from marshmallow import Schema, fields, post_load, ValidationError, validates_schema

# Initialize key components
def initialize_atlas():
    """Initialize all Atlas components."""
    # Register providers
    register_providers()

    # Register tools
    register_tools()

    # Initialize knowledge base
    initialize_knowledge_base()

def register_providers():
    """Register all available providers."""
    registry = ProviderRegistry()

    # Register OpenAI provider
    from providers.implementations.openai import OpenAIProvider
    registry.register_provider(
        provider_name="openai",
        provider_class=OpenAIProvider,
        models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
        capabilities={
            "gpt-3.5-turbo": {
                "supported": ["chat", "tool_use"],
                "ranking": {"chat": 3, "tool_use": 2}
            },
            "gpt-4": {
                "supported": ["chat", "tool_use", "advanced_reasoning"],
                "ranking": {"chat": 4, "tool_use": 4, "advanced_reasoning": 4}
            },
            "gpt-4-turbo": {
                "supported": ["chat", "tool_use", "advanced_reasoning", "vision"],
                "ranking": {"chat": 5, "tool_use": 5, "advanced_reasoning": 5, "vision": 5}
            }
        }
    )

    # Register Anthropic provider
    from providers.implementations.anthropic import AnthropicProvider
    registry.register_provider(
        provider_name="anthropic",
        provider_class=AnthropicProvider,
        models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        capabilities={
            "claude-3-opus": {
                "supported": ["chat", "tool_use", "advanced_reasoning", "vision"],
                "ranking": {"chat": 5, "tool_use": 5, "advanced_reasoning": 5, "vision": 5}
            },
            "claude-3-sonnet": {
                "supported": ["chat", "tool_use", "advanced_reasoning", "vision"],
                "ranking": {"chat": 4, "tool_use": 4, "advanced_reasoning": 4, "vision": 4}
            },
            "claude-3-haiku": {
                "supported": ["chat", "tool_use", "vision"],
                "ranking": {"chat": 3, "tool_use": 3, "vision": 3}
            }
        }
    )

    # Register Ollama provider
    from providers.implementations.ollama import OllamaProvider
    registry.register_provider(
        provider_name="ollama",
        provider_class=OllamaProvider,
        models=["llama3", "mixtral", "phi3"],
        capabilities={
            "llama3": {
                "supported": ["chat"],
                "ranking": {"chat": 3}
            },
            "mixtral": {
                "supported": ["chat", "tool_use"],
                "ranking": {"chat": 4, "tool_use": 3}
            },
            "phi3": {
                "supported": ["chat"],
                "ranking": {"chat": 2}
            }
        }
    )

    # Register Mock provider for testing
    from providers.implementations.mock import MockProvider
    registry.register_provider(
        provider_name="mock",
        provider_class=MockProvider,
        models=["mock-standard", "mock-advanced"],
        capabilities={
            "mock-standard": {
                "supported": ["chat", "tool_use"],
                "ranking": {"chat": 1, "tool_use": 1}
            },
            "mock-advanced": {
                "supported": ["chat", "tool_use", "advanced_reasoning", "vision"],
                "ranking": {"chat": 1, "tool_use": 1, "advanced_reasoning": 1, "vision": 1}
            }
        }
    )

def register_tools():
    """Register all available tools."""
    toolkit = AgentToolkit()

    # Register Calculator tool
    calculator = Calculator()
    toolkit.register_tool(calculator)

    # Register other tools as needed

# Main function
if __name__ == "__main__":
    # Initialize Atlas
    initialize_atlas()

    # Parse CLI arguments and run
    args = parse_cli_args()
    config = create_atlas_config(args)

    # Configure logging
    log_level = logging.DEBUG if config["debug"] else (logging.INFO if config["verbose"] else logging.WARNING)
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    logger = logging.getLogger("atlas")
    logger.info("Starting Atlas...")

    # Run in selected mode
    mode = config["mode"]
    if mode == "cli":
        run_cli_mode(config)
    elif mode == "query":
        run_query_mode(config)
    elif mode == "ingest":
        ingest_documents(config)
    else:
        print(f"Error: Unknown mode '{mode}'. Use --help for usage information.")
```

## 13. Critical Integration Points

1. **Provider Capability Registry**: Ensures models are selected based on required capabilities.

2. **Message Schema Validation**: Enforces consistent message formats across providers.

3. **Stream Control Interface**: Provides unified streaming behavior with control operations.

4. **Tool Integration**: Connects tools to agents with proper permission management.

5. **Knowledge Retrieval**: Combines vector and keyword search for robust document retrieval.

6. **Error Mapping**: Maps provider-specific errors to standardized Atlas errors.

7. **LangGraph State Management**: Uses typed state dictionaries for workflow management.

8. **Schema Validation Decorators**: Automatically validates input parameters to functions.

By implementing all these components, you will have a comprehensive, production-ready framework for building AI agents with knowledge retrieval, tool augmentation, and multi-provider support.
