---

title: Conversation Memory Strategies

---

# Conversation Memory and Session Management Strategy

**NOTE: The approaches outlined in this document are design proposals and are not yet implemented in Atlas.**

This document outlines potential implementation strategies for conversation history management and persistence in Atlas, focusing on efficient memory usage, knowledge extraction, and seamless user experience across sessions.

## Strategy Overview

Effective conversation memory management aims to balance several competing requirements:

1. **Context Preservation**
   - Maintain enough conversation history for coherent interactions
   - Preserve important context across multiple sessions
   - Allow users to reference previous interactions

2. **Token Optimization**
   - Efficiently use limited context windows of LLM providers
   - Avoid unnecessary token consumption on irrelevant history
   - Prioritize most relevant context for each interaction

3. **Knowledge Integration**
   - Extract valuable information from conversations into knowledge base
   - Create persistent memory that outlasts individual conversations
   - Build on accumulated knowledge over time

4. **User Experience**
   - Allow seamless continuation of previous conversations
   - Provide clear indicators of what Atlas remembers
   - Support explicit memory management by users

## Current Implementation Limitations

Atlas currently implements basic conversation tracking with these limitations:

1. **In-Memory Storage Only**: Conversation history exists only as the `messages` array in `AtlasAgent`, with no persistence between program runs
2. **Complete Reset Between Sessions**: Each CLI session starts with a fresh conversation history
3. **Manual Management Only**: History can only be cleared via the `reset_conversation()` method
4. **No Knowledge Integration**: Conversations don't feed back into the knowledge base
5. **Fixed Context Strategy**: No smart token management or summarization

## Proposed Implementation Approaches

### 1. Multi-Tiered Memory Architecture (Recommended First Implementation)

```
Conversation
  │
  ├─> Immediate Context (Full Recent Messages)
  │       │
  ├─> Working Memory (Progressive Summarization)
  │       │
  ├─> Long-Term Memory (Knowledge Extraction)
  │       │
  └─> Session Storage (Serialized Conversations)
```

**Implementation Details:**
- **Immediate Context**: Keep the most recent N messages verbatim
- **Working Memory**: Summarize older conversation segments
- **Long-Term Memory**: Extract facts, decisions, and important information into knowledge base
- **Session Storage**: Serialize entire conversations with metadata for later restoration

**Advantages:**
- Balances token usage with context preservation
- Creates natural degradation of detail over time (similar to human memory)
- Integrates with existing knowledge base for long-term retention
- Provides complete session restoration when needed

**Code Structure:**
```python
class ConversationMemoryManager:
    """Manages conversation history across multiple tiers."""

    def __init__(
        self,
        immediate_context_size: int = 10,
        working_memory_size: int = 20,
        knowledge_base: Optional[KnowledgeBase] = None,
        session_storage: Optional[SessionStorage] = None
    ):
        self.immediate_messages = []  # Most recent messages kept verbatim
        self.working_memory = []      # Older messages in summarized form
        self.knowledge_base = knowledge_base
        self.session_storage = session_storage
        self.immediate_context_size = immediate_context_size
        self.working_memory_size = working_memory_size
        self.session_id = str(uuid.uuid4())
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a new message to the conversation history."""
        # Update metadata
        self.metadata["last_updated"] = datetime.now().isoformat()
        self.metadata["message_count"] = self.metadata.get("message_count", 0) + 1

        # Add to immediate context
        self.immediate_messages.append(message)

        # If immediate context is full, summarize oldest messages into working memory
        if len(self.immediate_messages) > self.immediate_context_size:
            to_summarize = self.immediate_messages[0:5]  # Summarize in batches of 5
            summary = self._create_summary(to_summarize)
            self.working_memory.append(summary)
            self.immediate_messages = self.immediate_messages[5:]

            # If working memory is full, extract knowledge and prune
            if len(self.working_memory) > self.working_memory_size:
                oldest_summaries = self.working_memory[0:5]
                if self.knowledge_base:
                    self._extract_knowledge(oldest_summaries)
                self.working_memory = self.working_memory[5:]

        # Periodically save to session storage
        if self.session_storage and self.metadata["message_count"] % 10 == 0:
            self.save_session()

    def get_context_for_prompt(self, max_tokens: int = 4000) -> List[Dict[str, Any]]:
        """Get optimized conversation history for the prompt context."""
        # Always include all immediate messages
        context = self.immediate_messages.copy()

        # Add working memory summaries until we approach token limit
        # (Implementation would need actual token counting)
        for summary in reversed(self.working_memory):
            # Add summary if we have space
            if len(context) * 100 < max_tokens:  # Rough estimation
                context.insert(0, summary)
            else:
                break

        return context

    def _create_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of a sequence of messages."""
        # In a real implementation, this would use an LLM to create a summary
        # For now, we'll just create a placeholder
        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        assistant_messages = [m["content"] for m in messages if m["role"] == "assistant"]

        summary_content = f"Summary of {len(messages)} messages: "
        summary_content += f"User discussed {', '.join(user_messages[:50])}... "
        summary_content += f"Assistant responded with {', '.join(assistant_messages[:50])}..."

        return {
            "role": "system",
            "content": summary_content,
            "metadata": {
                "type": "summary",
                "message_count": len(messages),
                "timestamp": datetime.now().isoformat()
            }
        }

    def _extract_knowledge(self, summaries: List[Dict[str, Any]]) -> None:
        """Extract knowledge from summaries into the knowledge base."""
        # This would use an LLM to extract key facts, decisions, code snippets, etc.
        # Then store them in the knowledge base with appropriate metadata
        if not self.knowledge_base:
            return

        combined_content = "\n\n".join([s["content"] for s in summaries])

        # Extract entities, facts, and relationships
        # This is a placeholder for the actual extraction logic
        extracted_knowledge = {
            "content": f"Knowledge extracted from conversation {self.session_id}:\n{combined_content[:500]}...",
            "metadata": {
                "source": f"conversation:{self.session_id}",
                "extracted_at": datetime.now().isoformat(),
                "type": "conversation_knowledge"
            }
        }

        # Add to knowledge base
        self.knowledge_base.add_document(
            content=extracted_knowledge["content"],
            metadata=extracted_knowledge["metadata"]
        )

    def save_session(self) -> str:
        """Save the current session to storage."""
        if not self.session_storage:
            return ""

        session_data = {
            "session_id": self.session_id,
            "metadata": self.metadata,
            "immediate_messages": self.immediate_messages,
            "working_memory": self.working_memory,
        }

        return self.session_storage.save_session(session_data)

    def load_session(self, session_id: str) -> bool:
        """Load a session from storage."""
        if not self.session_storage:
            return False

        session_data = self.session_storage.load_session(session_id)
        if not session_data:
            return False

        self.session_id = session_data["session_id"]
        self.metadata = session_data["metadata"]
        self.immediate_messages = session_data["immediate_messages"]
        self.working_memory = session_data["working_memory"]

        return True

    def reset(self) -> None:
        """Reset the conversation memory."""
        self.immediate_messages = []
        self.working_memory = []
        self.session_id = str(uuid.uuid4())
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "message_count": 0
        }
```

### 2. Sliding Window with Summarization

```
Full Conversation
  │
  ▼
Analyze for Importance
  │
  ▼
Keep Recent + Important Messages
  │
  ▼
Summarize Remaining Messages
  │
  ▼
Optimized Context Window
```

**Implementation Details:**
- Keep the N most recent messages fully intact
- Evaluate older messages for importance (decisions, key facts, etc.)
- Keep important older messages intact
- Summarize runs of less important messages into single context entries
- Rebalance token budget based on query relevance

**Advantages:**
- More targeted token optimization
- Retains important context even from older interactions
- Adapts to conversation patterns
- Can be tuned for different prioritization strategies

### 3. Query-Aware Context Selection

```
User Query
  │
  ▼
Relevance Scoring of History
  │
  ▼
Select Most Relevant Context
  │
  ▼
Assemble Dynamic Context Window
  │
  ▼
Generate Response
```

**Implementation Details:**
- Score all previous conversation turns against current query
- Select most relevant context to include in the prompt
- Keep a baseline of recent messages regardless of relevance
- Efficiently retrieve related conversation segments from storage
- Dynamic token allocation based on query complexity

**Advantages:**
- Optimizes for most relevant context to current query
- Can handle larger conversation histories efficiently
- Makes better use of limited token windows
- Adapts to topic shifts in conversation

### 4. Knowledge-Integrated Conversation Management

```
Conversation
  │
  ├─> Real-Time Knowledge Extraction ─> Knowledge Base
  │                                          │
  ├─> Document Generation ─────────────────┘
  │       │
  └─> Context Retrieval ◄───────────────────┘
```

**Implementation Details:**
- Extract facts and information from conversations in real-time
- Store this knowledge in the same knowledge base as documents
- Generate "conversation documents" for important exchanges
- During new queries, retrieve relevant knowledge including conversation extracts
- Create a feedback loop where conversation enhances knowledge which enhances future conversations

**Advantages:**
- Unifies knowledge management across sources
- Creates persistent value from conversations
- Provides semantic retrieval of previous conversation knowledge
- More efficient than storing raw conversation history

## Configuration and Tuning

The conversation memory system should allow for extensive configuration:

### Session Management Configuration

- **Session Retention Policy**: How long to keep inactive sessions
- **Storage Backend**: Options for where to persist sessions (local, database, cloud)
- **Serialization Format**: How to efficiently store conversation data
- **Encryption Options**: For securing sensitive conversation content

### Memory Tier Configuration

- **Immediate Context Size**: Number of recent messages to keep verbatim
- **Working Memory Size**: Number of summarized chunks to maintain
- **Summary Strategy**: How to create effective summaries (frequency, granularity)
- **Knowledge Extraction Threshold**: When to extract into knowledge base

### Token Optimization Configuration

- **Token Budget Allocation**: How to distribute tokens across memory tiers
- **Importance Scoring Function**: Algorithm for identifying critical messages
- **Relevance Calculation**: How to match history to current query
- **Provider-Specific Settings**: Optimization targets for different LLM providers

### User Control Configuration

- **User Commands**: Interface for explicit memory management
- **Memory Visibility**: How to show what Atlas remembers
- **Privacy Controls**: User options for conversation persistence
- **Deletion Mechanisms**: How users can remove stored conversations

## Session Storage Implementation

For persisting conversations between application runs:

### 1. Local File Storage

```python
class FileSessionStorage:
    """Store sessions as JSON files in a local directory."""

    def __init__(self, storage_dir: str = ".atlas/sessions"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save session data to a file."""
        session_id = session_data["session_id"]
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")

        with open(file_path, "w") as f:
            json.dump(session_data, f, indent=2)

        return session_id

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from a file."""
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")

        if not os.path.exists(file_path):
            return None

        with open(file_path, "r") as f:
            return json.load(f)

    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List available sessions, sorted by last updated."""
        sessions = []

        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.storage_dir, filename)
                with open(file_path, "r") as f:
                    session_data = json.load(f)
                    sessions.append({
                        "session_id": session_data["session_id"],
                        "last_updated": session_data["metadata"]["last_updated"],
                        "message_count": session_data["metadata"].get("message_count", 0),
                        "title": session_data["metadata"].get("title", "Untitled Session")
                    })

        # Sort by last updated (descending)
        sessions.sort(key=lambda s: s["last_updated"], reverse=True)

        return sessions[:limit]
```

### 2. Database Storage

For larger deployments, a database storage approach would be more appropriate:

```python
class DatabaseSessionStorage:
    """Store sessions in a database for better scaling."""

    def __init__(self, db_connection_string: str):
        # This would connect to a database (SQLite, PostgreSQL, etc.)
        self.connection = self._connect_to_db(db_connection_string)
        self._create_tables_if_needed()

    def save_session(self, session_data: Dict[str, Any]) -> str:
        """Save session data to the database."""
        session_id = session_data["session_id"]
        # Implementation would serialize and store in appropriate tables
        return session_id

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from the database."""
        # Implementation would query and reconstruct session data
        return None  # Placeholder

    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List available sessions, sorted by last updated."""
        # Implementation would query for most recent sessions
        return []  # Placeholder
```

## CLI Integration

The conversation memory system should be integrated with the Atlas CLI:

```python
def run_cli_mode(args: Dict[str, Any]) -> bool:
    """Run Atlas in interactive CLI mode with session management."""
    logger.info("\nAtlas CLI Mode")
    logger.info("-------------")

    # Create session storage
    session_storage = FileSessionStorage()

    # Handle session continuation if requested
    session_id = args.get('continue_session')

    if session_id == "last":
        # Get the most recent session
        sessions = session_storage.list_sessions(limit=1)
        if sessions:
            session_id = sessions[0]["session_id"]
            logger.info(f"Continuing last session from {sessions[0]['last_updated']}")
        else:
            session_id = None
            logger.info("No previous sessions found, starting new session")

    # Create provider and agent as usual
    # (Provider creation code omitted for brevity)

    # Initialize agent with conversation memory
    agent = AtlasAgent(
        system_prompt_file=args.get('system_prompt'),
        collection_name=args.get('collection', 'atlas_knowledge_base'),
        config=config,
        provider=provider,
    )

    # Initialize conversation memory manager
    memory_manager = ConversationMemoryManager(
        knowledge_base=agent.knowledge_base,
        session_storage=session_storage
    )

    # Load existing session if specified
    if session_id:
        if memory_manager.load_session(session_id):
            logger.info(f"Successfully loaded session {session_id}")

            # Set the agent's messages from the memory manager
            agent.messages = memory_manager.get_context_for_prompt()
        else:
            logger.warning(f"Failed to load session {session_id}, starting new session")

    # CLI interaction loop
    logger.info("Atlas is ready. Type 'exit' or 'quit' to end the session.")
    logger.info("Special commands: !clear (reset conversation), !save (save session), !help")
    logger.info("---------------------------------------------------")

    while True:
        # Get user input
        try:
            print("\nYou: ", end="", flush=True)
            user_input = sys.stdin.readline().strip()

            # Check for exit command
            if user_input.lower() in ["exit", "quit"]:
                # Save session before exiting
                memory_manager.save_session()
                print("\nSession saved. Goodbye!")
                break

            # Check for special commands
            if user_input.startswith("!"):
                if user_input == "!clear":
                    memory_manager.reset()
                    agent.reset_conversation()
                    print("Conversation has been reset.")
                    continue
                elif user_input == "!save":
                    session_id = memory_manager.save_session()
                    print(f"Session saved with ID: {session_id}")
                    continue
                elif user_input == "!help":
                    print("\nAvailable commands:")
                    print("  !clear - Reset the conversation history")
                    print("  !save - Save the current session")
                    print("  !help - Show this help message")
                    print("  exit/quit - Exit Atlas")
                    continue

            # Add user message to memory
            memory_manager.add_message({"role": "user", "content": user_input})

            # Update agent messages with optimized context
            agent.messages = memory_manager.get_context_for_prompt()

            # Process the message through the agent
            response = agent.process_message(user_input)

            # Add assistant response to memory
            memory_manager.add_message({"role": "assistant", "content": response})

            # Display the response
            print(f"\nAtlas: {response}")

            # Periodically save session automatically
            if random.random() < 0.2:  # 20% chance to auto-save
                memory_manager.save_session()

        except KeyboardInterrupt:
            print("\nSession interrupted. Saving before exit...")
            memory_manager.save_session()
            print("Goodbye!")
            break
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            print("Let's continue with a fresh conversation.")
            memory_manager.reset()
            agent.reset_conversation()

    return True
```

## Knowledge Extraction Implementation

A key component of the memory strategy is extracting knowledge from conversations:

```python
def extract_knowledge_from_conversation(
    messages: List[Dict[str, Any]],
    knowledge_base: KnowledgeBase
) -> List[str]:
    """Extract knowledge from conversation and add to knowledge base."""
    # Group messages into conversation chunks
    chunks = []
    current_chunk = []

    for msg in messages:
        current_chunk.append(msg)
        if len(current_chunk) >= 6:  # Process in groups of 6 messages (3 turns)
            chunks.append(current_chunk)
            current_chunk = []

    # Add any remaining messages
    if current_chunk:
        chunks.append(current_chunk)

    # Process each chunk to extract knowledge
    extracted_items = []

    for chunk in chunks:
        # Format the conversation for analysis
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in chunk
        ])

        # This would use an LLM to extract knowledge
        # For now, we'll just use a placeholder approach
        extracted_text = f"Knowledge extracted from conversation:\n{conversation_text[:300]}..."

        # Create metadata
        metadata = {
            "source": "conversation",
            "extracted_at": datetime.now().isoformat(),
            "source_messages": len(chunk),
            "extraction_method": "conversation_analysis"
        }

        # Add to knowledge base
        document_id = knowledge_base.add_document(extracted_text, metadata)
        extracted_items.append(document_id)

    return extracted_items
```

## Conversation Summarization

Effective summarization is crucial for balancing context preservation with token efficiency:

```python
def create_conversation_summary(
    messages: List[Dict[str, Any]],
    provider: ModelProvider
) -> Dict[str, Any]:
    """Create a dense, informative summary of a conversation segment."""
    # Format messages for the model
    conversation_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in messages
    ])

    # Create prompt for summarization
    prompt = f"""
    Summarize the following conversation segment concisely, preserving key information:

    {conversation_text}

    SUMMARY:
    """

    # Request summary from model
    request = ModelRequest.create_direct(
        messages=[ModelMessage.user(prompt)],
        max_tokens=200
    )

    response = provider.generate(request)
    summary = response.content

    # Create summary message
    return {
        "role": "system",
        "content": f"Previous conversation summary: {summary}",
        "metadata": {
            "type": "summary",
            "message_count": len(messages),
            "timestamp": datetime.now().isoformat()
        }
    }
```

## Performance Considerations

The conversation memory system adds computational overhead that should be managed:

1. **Asynchronous Processing**
   - Run memory operations asynchronously when possible
   - Process summarization and knowledge extraction in background threads
   - Use non-blocking I/O for session storage operations

2. **Smart Batching**
   - Process memory operations in batches to amortize costs
   - Only summarize when crossing specific thresholds
   - Batch knowledge extractions when possible

3. **Caching Layer**
   - Cache session data for quick access
   - Cache summarization results for reuse
   - Implement LRU caching for frequent operations

4. **Incremental Updates**
   - Only process new messages when loading sessions
   - Avoid redundant summarization of already processed messages
   - Track changes to optimize processing

## User Experience Considerations

The memory system should enhance the user experience in several ways:

1. **Seamless Continuity**
   - Users should be able to pick up conversations where they left off
   - System should provide appropriate reminders of previous context
   - Transitions between sessions should feel natural

2. **Transparency**
   - Users should understand what information is being remembered
   - Clear indicators of when memory is being used
   - Options to view what knowledge has been extracted

3. **Control Mechanisms**
   - Commands to save, clear, or load specific sessions
   - Ability to mark certain information as important to remember
   - Options to disable persistence for sensitive conversations

4. **Adaptive Behavior**
   - System should adapt to user's conversation patterns
   - Remember frequently discussed topics more thoroughly
   - Recognize when users reference previous conversations

## Integration with Atlas Architecture

The conversation memory system should integrate cleanly with Atlas's existing architecture:

1. **Agent Integration**
   - Extend the AtlasAgent class to support memory management
   - Add memory-aware context generation methods
   - Implement session serialization and deserialization

2. **Knowledge System Integration**
   - Connect the memory system to the existing KnowledgeBase
   - Implement bidirectional flow between conversations and knowledge
   - Ensure consistent metadata and retrieval patterns

3. **CLI Integration**
   - Add session management commands to the CLI
   - Implement session listing and selection
   - Provide feedback about memory usage in the interface

4. **API Considerations**
   - Define clean interfaces for memory operations
   - Support streaming operations with memory context
   - Ensure stateless API operations can still leverage memory

## Implementation Roadmap

1. **Phase 1: Basic Session Persistence**
   - Implement simple file-based session storage
   - Add commands to save and load sessions
   - Create basic session metadata tracking

2. **Phase 2: Memory Optimization**
   - Implement progressive summarization
   - Add token counting and budget management
   - Create relevance scoring for context selection

3. **Phase 3: Knowledge Integration**
   - Implement knowledge extraction from conversations
   - Create feedback loop to knowledge base
   - Develop session tagging and categorization

4. **Phase 4: Advanced Features**
   - Add cloud sync options for sessions
   - Implement cross-session knowledge connections
   - Create analytics for conversation patterns

## Conclusion

Implementing a robust conversation memory strategy would significantly enhance Atlas's capabilities, creating a system that learns and improves through continued use. The multi-tiered approach balances immediate context needs with long-term knowledge accumulation, while session persistence provides continuity across interactions.

While more complex than the current simple message array, this system would transform Atlas into a true long-term thinking partner rather than just a stateless query responder. The proposed design aligns perfectly with Atlas's core mission of building and leveraging knowledge over time.

**NOTE: These strategies are design proposals and not yet implemented in Atlas.**
