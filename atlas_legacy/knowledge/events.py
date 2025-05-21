"""
Event-enabled integration for knowledge system components.

This module provides a mixin class that adds event system capabilities to knowledge
components, allowing them to publish events for monitoring and debugging purposes.
These events can be used for tracking knowledge operations, performance metrics,
and diagnostic information.
"""

import time
import uuid
from typing import Any, ClassVar, TypeVar

from atlas.core.logging import get_logger
from atlas.core.services.events import EventSystem, create_event_system
from atlas.knowledge.retrieval import KnowledgeBase, RetrievalFilter, RetrievalResult
from atlas.knowledge.settings import RetrievalSettings

# Create a logger for this module
logger = get_logger(__name__)

# Type variable for generic return type
T = TypeVar("T")
KnowledgeBaseType = TypeVar("KnowledgeBaseType", bound=KnowledgeBase)


class EventEnabledKnowledgeBase:
    """Mixin class that adds event system capabilities to knowledge components."""

    # Standard event types
    EVENT_RETRIEVE_START: ClassVar[str] = "knowledge.retrieve.start"
    EVENT_RETRIEVE_END: ClassVar[str] = "knowledge.retrieve.end"
    EVENT_RETRIEVE_ERROR: ClassVar[str] = "knowledge.retrieve.error"

    EVENT_HYBRID_RETRIEVE_START: ClassVar[str] = "knowledge.hybrid_retrieve.start"
    EVENT_HYBRID_RETRIEVE_END: ClassVar[str] = "knowledge.hybrid_retrieve.end"
    EVENT_HYBRID_RETRIEVE_ERROR: ClassVar[str] = "knowledge.hybrid_retrieve.error"

    EVENT_DOCUMENT_INGEST_START: ClassVar[str] = "knowledge.ingest.start"
    EVENT_DOCUMENT_INGEST_END: ClassVar[str] = "knowledge.ingest.end"
    EVENT_DOCUMENT_INGEST_ERROR: ClassVar[str] = "knowledge.ingest.error"

    EVENT_METADATA_SEARCH_START: ClassVar[str] = "knowledge.metadata_search.start"
    EVENT_METADATA_SEARCH_END: ClassVar[str] = "knowledge.metadata_search.end"

    EVENT_VERSION_LIST_START: ClassVar[str] = "knowledge.version_list.start"
    EVENT_VERSION_LIST_END: ClassVar[str] = "knowledge.version_list.end"

    EVENT_CACHE_HIT: ClassVar[str] = "knowledge.cache.hit"
    EVENT_CACHE_MISS: ClassVar[str] = "knowledge.cache.miss"

    EVENT_COLLECTION_COUNT: ClassVar[str] = "knowledge.collection.count"
    EVENT_COLLECTION_ERROR: ClassVar[str] = "knowledge.collection.error"

    def __init__(self, event_system: EventSystem | None = None, **kwargs):
        """Initialize with an event system.

        Args:
            event_system: Optional event system to use for publishing events.
                If not provided, a new event system will be created.
            **kwargs: Additional arguments to pass to the parent constructor.
        """
        # Set up event system
        self.event_system = event_system or create_event_system()

        # Create event history for this component
        self.event_history: list[dict[str, Any]] = []

        # Track performance metrics
        self.total_retrieval_time = 0.0
        self.total_retrievals = 0
        self.retrieval_times: list[float] = []

        # Initialize cache stats
        self.cache_hits = 0
        self.cache_misses = 0

        # Call parent constructor with remaining arguments
        super().__init__(**kwargs)

        logger.debug(
            f"Initialized EventEnabledKnowledgeBase with {type(self.event_system)} event system"
        )

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filter: dict[str, Any] | RetrievalFilter | None = None,
        rerank: bool = False,
        settings: RetrievalSettings | None = None,
    ) -> list[RetrievalResult]:
        """Event-monitored version of retrieve method.

        Args:
            query: The query to search for.
            n_results: Number of results to return.
            filter: Optional filter to apply to the query.
            rerank: Whether to rerank results using additional criteria.
            settings: Optional retrieval settings to use.

        Returns:
            A list of relevant documents with their metadata.
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Publish start event
        self.event_system.publish(
            event_type=self.EVENT_RETRIEVE_START,
            data={
                "request_id": request_id,
                "query": query,
                "n_results": n_results,
                "filter": str(filter) if filter else None,
                "rerank": rerank,
                "settings": settings.to_dict() if settings else None,
            },
            source=f"knowledge.{self.__class__.__name__}",
        )

        try:
            # Call the actual retrieve method from the parent class
            results = super().retrieve(query, n_results, filter, rerank, settings)

            # Track performance
            duration = time.time() - start_time
            self.total_retrieval_time += duration
            self.total_retrievals += 1
            self.retrieval_times.append(duration)

            # Trim retrieval times list if it gets too long
            if len(self.retrieval_times) > 100:
                self.retrieval_times = self.retrieval_times[-100:]

            # Publish end event with results summary
            result_summary = [
                {
                    "relevance_score": result.relevance_score,
                    "source": result.metadata.get("source", "unknown"),
                    "section_title": result.metadata.get("section_title", ""),
                    "content_preview": (
                        result.content[:100] + "..."
                        if len(result.content) > 100
                        else result.content
                    ),
                }
                for result in results[:3]  # Only include first 3 for brevity
            ]

            self.event_system.publish(
                event_type=self.EVENT_RETRIEVE_END,
                data={
                    "request_id": request_id,
                    "duration_seconds": duration,
                    "result_count": len(results),
                    "result_summary": result_summary,
                    "avg_relevance_score": (
                        sum(r.relevance_score for r in results) / len(results) if results else 0
                    ),
                },
                source=f"knowledge.{self.__class__.__name__}",
            )

            return results

        except Exception as e:
            # Track error
            duration = time.time() - start_time

            # Publish error event
            self.event_system.publish(
                event_type=self.EVENT_RETRIEVE_ERROR,
                data={
                    "request_id": request_id,
                    "duration_seconds": duration,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                source=f"knowledge.{self.__class__.__name__}",
            )

            # Re-raise the exception
            raise

    def retrieve_hybrid(
        self,
        query: str,
        n_results: int = 5,
        filter: RetrievalFilter | None = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[RetrievalResult]:
        """Event-monitored version of retrieve_hybrid method.

        Args:
            query: The query to search for.
            n_results: Number of results to return.
            filter: Optional filter to apply to the query.
            semantic_weight: Weight for semantic search results.
            keyword_weight: Weight for keyword search results.

        Returns:
            A list of relevant documents with their metadata.
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Publish start event
        self.event_system.publish(
            event_type=self.EVENT_HYBRID_RETRIEVE_START,
            data={
                "request_id": request_id,
                "query": query,
                "n_results": n_results,
                "filter": str(filter) if filter else None,
                "semantic_weight": semantic_weight,
                "keyword_weight": keyword_weight,
            },
            source=f"knowledge.{self.__class__.__name__}",
        )

        try:
            # Call the actual retrieve_hybrid method from the parent class
            results = super().retrieve_hybrid(
                query, n_results, filter, semantic_weight, keyword_weight
            )

            # Track performance
            duration = time.time() - start_time

            # Publish end event with results summary
            result_summary = [
                {
                    "relevance_score": result.relevance_score,
                    "source": result.metadata.get("source", "unknown"),
                    "section_title": result.metadata.get("section_title", ""),
                    "content_preview": (
                        result.content[:100] + "..."
                        if len(result.content) > 100
                        else result.content
                    ),
                }
                for result in results[:3]  # Only include first 3 for brevity
            ]

            self.event_system.publish(
                event_type=self.EVENT_HYBRID_RETRIEVE_END,
                data={
                    "request_id": request_id,
                    "duration_seconds": duration,
                    "result_count": len(results),
                    "result_summary": result_summary,
                    "avg_relevance_score": (
                        sum(r.relevance_score for r in results) / len(results) if results else 0
                    ),
                },
                source=f"knowledge.{self.__class__.__name__}",
            )

            return results

        except Exception as e:
            # Track error
            duration = time.time() - start_time

            # Publish error event
            self.event_system.publish(
                event_type=self.EVENT_HYBRID_RETRIEVE_ERROR,
                data={
                    "request_id": request_id,
                    "duration_seconds": duration,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                source=f"knowledge.{self.__class__.__name__}",
            )

            # Re-raise the exception
            raise

    def get_versions(self) -> list[str]:
        """Event-monitored version of get_versions method.

        Returns:
            A list of version strings.
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Publish start event
        self.event_system.publish(
            event_type=self.EVENT_VERSION_LIST_START,
            data={"request_id": request_id},
            source=f"knowledge.{self.__class__.__name__}",
        )

        # Call the actual get_versions method from the parent class
        versions = super().get_versions()

        # Publish end event
        duration = time.time() - start_time
        self.event_system.publish(
            event_type=self.EVENT_VERSION_LIST_END,
            data={
                "request_id": request_id,
                "duration_seconds": duration,
                "version_count": len(versions),
                "versions": versions,
            },
            source=f"knowledge.{self.__class__.__name__}",
        )

        return versions

    def search_by_metadata(
        self, metadata_field: str, value: Any, n_results: int = 100
    ) -> list[str]:
        """Event-monitored version of search_by_metadata method.

        Args:
            metadata_field: The metadata field to search.
            value: The value to search for.
            n_results: Maximum number of results to return.

        Returns:
            A list of unique matching values.
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Publish start event
        self.event_system.publish(
            event_type=self.EVENT_METADATA_SEARCH_START,
            data={
                "request_id": request_id,
                "metadata_field": metadata_field,
                "value": str(value),
                "n_results": n_results,
            },
            source=f"knowledge.{self.__class__.__name__}",
        )

        # Call the actual search_by_metadata method from the parent class
        results = super().search_by_metadata(metadata_field, value, n_results)

        # Publish end event
        duration = time.time() - start_time
        self.event_system.publish(
            event_type=self.EVENT_METADATA_SEARCH_END,
            data={
                "request_id": request_id,
                "duration_seconds": duration,
                "result_count": len(results),
                "metadata_field": metadata_field,
            },
            source=f"knowledge.{self.__class__.__name__}",
        )

        return results

    def track_cache_hit(self, query: str) -> None:
        """Track a cache hit for monitoring.

        Args:
            query: The query that was cached.
        """
        self.cache_hits += 1

        # Publish cache hit event
        self.event_system.publish(
            event_type=self.EVENT_CACHE_HIT,
            data={
                "query": query,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_ratio": (
                    self.cache_hits / (self.cache_hits + self.cache_misses)
                    if (self.cache_hits + self.cache_misses) > 0
                    else 0
                ),
            },
            source=f"knowledge.{self.__class__.__name__}",
        )

    def track_cache_miss(self, query: str) -> None:
        """Track a cache miss for monitoring.

        Args:
            query: The query that was not cached.
        """
        self.cache_misses += 1

        # Publish cache miss event
        self.event_system.publish(
            event_type=self.EVENT_CACHE_MISS,
            data={
                "query": query,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_ratio": (
                    self.cache_hits / (self.cache_hits + self.cache_misses)
                    if (self.cache_hits + self.cache_misses) > 0
                    else 0
                ),
            },
            source=f"knowledge.{self.__class__.__name__}",
        )

    def get_knowledge_metrics(self) -> dict[str, Any]:
        """Get metrics about knowledge base operations.

        Returns:
            Dictionary with performance metrics.
        """
        # Calculate averages
        avg_retrieval_time = (
            self.total_retrieval_time / self.total_retrievals if self.total_retrievals > 0 else 0
        )
        recent_avg_time = (
            sum(self.retrieval_times) / len(self.retrieval_times) if self.retrieval_times else 0
        )

        # Calculate cache hit ratio
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_ratio = self.cache_hits / total_cache_requests if total_cache_requests > 0 else 0

        # Collection stats
        try:
            collection_count = self.collection.count() if hasattr(self, "collection") else 0

            # Publish collection count event
            self.event_system.publish(
                event_type=self.EVENT_COLLECTION_COUNT,
                data={"document_count": collection_count},
                source=f"knowledge.{self.__class__.__name__}",
            )
        except Exception as e:
            collection_count = 0

            # Publish error event
            self.event_system.publish(
                event_type=self.EVENT_COLLECTION_ERROR,
                data={"error": str(e), "error_type": type(e).__name__},
                source=f"knowledge.{self.__class__.__name__}",
            )

        return {
            "total_retrievals": self.total_retrievals,
            "avg_retrieval_time": avg_retrieval_time,
            "recent_avg_retrieval_time": recent_avg_time,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_ratio": cache_hit_ratio,
            "document_count": collection_count,
            "db_path": getattr(self, "db_path", "unknown"),
            "collection_name": getattr(self, "collection_name", "unknown"),
        }

    def get_event_history(
        self, event_type: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get history of knowledge events.

        Args:
            event_type: Optional event type to filter by.
            limit: Maximum number of events to return.

        Returns:
            List of events in chronological order (newest first).
        """
        source_filter = f"knowledge.{self.__class__.__name__}"

        return self.event_system.get_events(
            event_type=event_type, source=source_filter, limit=limit
        )


def create_event_enabled_knowledge_base(
    base_class: type[KnowledgeBaseType] = None, **kwargs
) -> type[KnowledgeBaseType] | KnowledgeBaseType:
    """Create an event-enabled knowledge base from a base class.

    Args:
        base_class: Optional base class to use. If not provided, creates directly.
        **kwargs: Additional arguments to pass to the constructor.

    Returns:
        An event-enabled knowledge base class or instance.
    """
    if base_class is None:
        from atlas.knowledge.retrieval import KnowledgeBase

        base_class = KnowledgeBase

    # Create a new class that inherits from EventEnabledKnowledgeBase and the base class
    class EventEnabledKnowledgeBaseImpl(EventEnabledKnowledgeBase, base_class):
        """Event-enabled implementation of the knowledge base."""

        pass

    # Set the name and docstring
    EventEnabledKnowledgeBaseImpl.__name__ = f"EventEnabled{base_class.__name__}"
    EventEnabledKnowledgeBaseImpl.__doc__ = f"Event-enabled version of {base_class.__name__}."

    # If kwargs are provided, create and return an instance
    if kwargs:
        return EventEnabledKnowledgeBaseImpl(**kwargs)

    # Otherwise, return the class
    return EventEnabledKnowledgeBaseImpl


# Function for use with LangGraph that tracks events
def retrieve_knowledge_with_events(
    state: dict[str, Any],
    query: str | None = None,
    collection_name: str | None = None,
    db_path: str | None = None,
    filter: RetrievalFilter | None = None,
    settings: RetrievalSettings | None = None,
    use_hybrid: bool = False,
    event_system: EventSystem | None = None,
) -> dict[str, Any]:
    """Retrieve knowledge from the Atlas knowledge base with event monitoring.

    This is a drop-in replacement for the standard retrieve_knowledge function
    that adds event monitoring capabilities.

    Args:
        state: The current state of the agent.
        query: Optional query override. If not provided, uses the user's last message.
        collection_name: Name of the Chroma collection to use.
        db_path: Path to ChromaDB. If None, use environment variable or default.
        filter: Optional filter for retrieval.
        settings: Optional retrieval settings for fine-grained control.
        use_hybrid: Whether to use hybrid retrieval (deprecated; use settings instead).
        event_system: Optional event system to use for publishing events.

    Returns:
        Updated state with retrieved knowledge.
    """
    # Create event-enabled knowledge base
    EventEnabledKB = create_event_enabled_knowledge_base()
    kb = EventEnabledKB(collection_name=collection_name, db_path=db_path, event_system=event_system)

    # Log function start
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Get the query from the state if not explicitly provided
    if not query:
        messages = state.get("messages", [])
        if not messages:
            logger.warning("No messages in state, cannot determine query")
            state["context"] = {"documents": [], "query": ""}
            return state

        last_user_message = None
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user_message = message.get("content", "")
                break

        if not last_user_message:
            logger.warning("No user messages found in state")
            state["context"] = {"documents": [], "query": ""}
            return state

        query = last_user_message

    query_str: str = query if isinstance(query, str) else ""

    # Create settings if use_hybrid is specified but no settings provided
    if use_hybrid and not settings:
        settings = RetrievalSettings(use_hybrid_search=True)

    # Publish event for agent retrieval start
    if kb.event_system:
        kb.event_system.publish(
            event_type="agent.knowledge.retrieve.start",
            data={
                "request_id": request_id,
                "query": query_str,
                "filter": str(filter) if filter else None,
                "settings": settings.to_dict() if settings else None,
            },
            source="agent.knowledge",
        )

    # Retrieve relevant documents
    documents = kb.retrieve(query_str, filter=filter, settings=settings)

    # Convert RetrievalResult objects to dicts for state
    document_dicts = [doc.to_dict() for doc in documents]

    # Update state with retrieved documents
    state["context"] = {"documents": document_dicts, "query": query}

    # Publish event for agent retrieval end
    duration = time.time() - start_time
    if kb.event_system:
        kb.event_system.publish(
            event_type="agent.knowledge.retrieve.end",
            data={
                "request_id": request_id,
                "duration_seconds": duration,
                "result_count": len(documents),
                "metrics": kb.get_knowledge_metrics(),
            },
            source="agent.knowledge",
        )

    return state
