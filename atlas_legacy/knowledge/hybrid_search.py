"""
Hybrid search implementation combining semantic and keyword search methods.

This module provides enhanced hybrid search capabilities by implementing BM25-based
keyword search that can be combined with semantic vector search for more robust
retrieval. It includes classes for keyword search, result merging, and a unified
hybrid search interface.
"""

import logging
import math
import re
from collections import Counter, defaultdict
from typing import Any

from atlas.knowledge.retrieval import KnowledgeBase, RetrievalFilter, RetrievalResult
from atlas.knowledge.settings import RetrievalSettings

logger = logging.getLogger(__name__)


class BM25SearchEngine:
    """BM25 keyword search engine implementation.

    This class implements the BM25 algorithm for keyword-based document retrieval.
    BM25 is a bag-of-words retrieval function that ranks documents based on the
    query terms appearing in each document, regardless of their proximity.
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        """Initialize the BM25 search engine.

        Args:
            k1: Term frequency saturation parameter. Higher values give more weight to term frequency.
            b: Document length normalization parameter. 0.0 means no normalization, 1.0 means full norm.
            epsilon: Smoothing parameter for IDF calculation to prevent division by zero.
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.doc_count = 0
        self.avg_doc_length = 0
        self.doc_lengths = {}
        self.term_doc_freq = defaultdict(dict)  # term -> {doc_id -> term_freq}
        self.doc_freq = Counter()  # term -> number of docs containing term
        self.doc_index = {}  # doc_id -> original document
        self.initialized = False

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words for indexing or querying.

        Args:
            text: Text to tokenize.

        Returns:
            List of tokens (words).
        """
        # Simple tokenization - extract words of at least 3 chars, convert to lowercase
        tokens = re.findall(r"\b\w{3,}\b", text.lower())
        return tokens

    def index_documents(self, documents: list[tuple[str, dict[str, Any]]]) -> None:
        """Index a list of documents for searching.

        Args:
            documents: List of (document_content, metadata) tuples to index.
        """
        self.doc_count = len(documents)
        if self.doc_count == 0:
            logger.warning("No documents to index")
            return

        # Reset index
        self.doc_lengths = {}
        self.term_doc_freq = defaultdict(dict)
        self.doc_freq = Counter()
        self.doc_index = {}

        # Process each document
        total_length = 0
        for doc_id, (content, metadata) in enumerate(documents):
            # Store original document
            self.doc_index[doc_id] = (content, metadata)

            # Tokenize and count term frequencies
            tokens = self._tokenize(content)
            self.doc_lengths[doc_id] = len(tokens)
            total_length += len(tokens)

            # Count term frequencies for this document
            term_freq = Counter(tokens)

            # Update document frequency and term-document frequency
            for term, freq in term_freq.items():
                self.doc_freq[term] += 1
                self.term_doc_freq[term][doc_id] = freq

        # Calculate average document length
        self.avg_doc_length = total_length / self.doc_count if self.doc_count > 0 else 0
        self.initialized = True
        logger.info(f"Indexed {self.doc_count} documents with {len(self.doc_freq)} unique terms")

    def search(
        self, query: str, n_results: int = 5, filter_func: callable | None = None
    ) -> list[RetrievalResult]:
        """Search for documents matching the query.

        Args:
            query: The search query.
            n_results: Maximum number of results to return.
            filter_func: Optional function to filter documents.
                The function should take doc_id, content, and metadata and return a boolean.

        Returns:
            List of RetrievalResult objects sorted by relevance score.
        """
        if not self.initialized or self.doc_count == 0:
            logger.warning("Search engine not initialized or no documents indexed")
            return []

        # Tokenize the query
        query_terms = self._tokenize(query)
        if not query_terms:
            logger.warning("No valid search terms in query")
            return []

        # Calculate scores for each document
        scores = defaultdict(float)
        for term in query_terms:
            if term not in self.doc_freq:
                continue

            # Calculate IDF for this term
            idf = math.log(
                1
                + (self.doc_count - self.doc_freq[term] + self.epsilon)
                / (self.doc_freq[term] + self.epsilon)
            )

            # Update scores for documents containing this term
            for doc_id, term_freq in self.term_doc_freq[term].items():
                # Apply filter if provided
                if filter_func:
                    content, metadata = self.doc_index[doc_id]
                    if not filter_func(doc_id, content, metadata):
                        continue

                # BM25 scoring formula
                doc_length = self.doc_lengths[doc_id]
                numerator = term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (
                    1 - self.b + self.b * doc_length / self.avg_doc_length
                )
                scores[doc_id] += idf * numerator / denominator

        # Sort documents by score
        doc_scores = sorted(
            [(doc_id, score) for doc_id, score in scores.items()], key=lambda x: x[1], reverse=True
        )

        # Return top n_results
        results = []
        for doc_id, score in doc_scores[:n_results]:
            content, metadata = self.doc_index[doc_id]

            # Normalize score to 0-1 range for consistency with vector search
            # The max theoretical BM25 score depends on parameters and corpus statistics
            # We use a simple normalization strategy here
            normalized_score = min(score / (len(query_terms) * 2), 1.0)

            results.append(
                RetrievalResult(
                    content=content,
                    metadata=metadata,
                    relevance_score=normalized_score,
                    distance=1.0 - normalized_score,  # Convert score to distance
                )
            )

        return results


class HybridSearchMerger:
    """Merger for combining semantic and keyword search results.

    This class provides methods for merging and reranking results from different
    search strategies, with configurable weights and merging algorithms.
    """

    @staticmethod
    def merge_results(
        semantic_results: list[RetrievalResult],
        keyword_results: list[RetrievalResult],
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        strategy: str = "weighted_score",
    ) -> list[RetrievalResult]:
        """Merge results from semantic and keyword search methods.

        Args:
            semantic_results: Results from semantic search.
            keyword_results: Results from keyword search.
            semantic_weight: Weight for semantic search results (0-1).
            keyword_weight: Weight for keyword search results (0-1).
            strategy: Merging strategy - one of "weighted_score", "score_add", "score_multiply", "rank_fusion".

        Returns:
            Merged and reranked results.
        """
        # Normalize weights to sum to 1.0
        total_weight = semantic_weight + keyword_weight
        if total_weight <= 0:
            logger.warning("Total weight must be positive. Using default weights.")
            semantic_weight, keyword_weight = 0.7, 0.3
        else:
            semantic_weight = semantic_weight / total_weight
            keyword_weight = keyword_weight / total_weight

        # Use the appropriate strategy
        if strategy == "weighted_score":
            return HybridSearchMerger._merge_weighted_score(
                semantic_results, keyword_results, semantic_weight, keyword_weight
            )
        elif strategy == "score_add":
            return HybridSearchMerger._merge_score_add(
                semantic_results, keyword_results, semantic_weight, keyword_weight
            )
        elif strategy == "score_multiply":
            return HybridSearchMerger._merge_score_multiply(
                semantic_results, keyword_results, semantic_weight, keyword_weight
            )
        elif strategy == "rank_fusion":
            return HybridSearchMerger._merge_rank_fusion(
                semantic_results, keyword_results, semantic_weight, keyword_weight
            )
        else:
            logger.warning(f"Unknown merging strategy: {strategy}. Using weighted_score.")
            return HybridSearchMerger._merge_weighted_score(
                semantic_results, keyword_results, semantic_weight, keyword_weight
            )

    @staticmethod
    def _merge_weighted_score(
        semantic_results: list[RetrievalResult],
        keyword_results: list[RetrievalResult],
        semantic_weight: float,
        keyword_weight: float,
    ) -> list[RetrievalResult]:
        """Merge results using weighted scores.

        This approach uses a unique ID for each result (from metadata) and
        combines scores for documents that appear in both result sets.

        Args:
            semantic_results: Results from semantic search.
            keyword_results: Results from keyword search.
            semantic_weight: Weight for semantic search results.
            keyword_weight: Weight for keyword search results.

        Returns:
            Merged and reranked results.
        """
        result_map: dict[str, RetrievalResult] = {}

        # Process semantic results
        for result in semantic_results:
            # Use metadata ID or create a synthetic one from content
            result_id = result.metadata.get(
                "id", result.metadata.get("simple_id", hash(result.content))
            )
            result_map[str(result_id)] = result
            # Scale score by semantic weight
            result.relevance_score *= semantic_weight

        # Process keyword results
        for result in keyword_results:
            # Use metadata ID or create a synthetic one from content
            result_id = result.metadata.get(
                "id", result.metadata.get("simple_id", hash(result.content))
            )
            result_id = str(result_id)

            if result_id in result_map:
                # Result already in map, add scores
                result_map[result_id].relevance_score += result.relevance_score * keyword_weight
                # Update distance to be consistent with score
                result_map[result_id].distance = 1.0 - result_map[result_id].relevance_score
            else:
                # New result, scale score
                result.relevance_score *= keyword_weight
                # Update distance
                result.distance = 1.0 - result.relevance_score
                result_map[result_id] = result

        # Convert back to list and sort by relevance
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return combined_results

    @staticmethod
    def _merge_score_add(
        semantic_results: list[RetrievalResult],
        keyword_results: list[RetrievalResult],
        semantic_weight: float,
        keyword_weight: float,
    ) -> list[RetrievalResult]:
        """Merge results by adding scores and then normalizing.

        This method gives the highest scores to documents that appear high
        in both result sets.

        Args:
            semantic_results: Results from semantic search.
            keyword_results: Results from keyword search.
            semantic_weight: Weight for semantic search results.
            keyword_weight: Weight for keyword search results.

        Returns:
            Merged and reranked results.
        """
        # Same implementation as weighted_score for now as it already uses addition
        return HybridSearchMerger._merge_weighted_score(
            semantic_results, keyword_results, semantic_weight, keyword_weight
        )

    @staticmethod
    def _merge_score_multiply(
        semantic_results: list[RetrievalResult],
        keyword_results: list[RetrievalResult],
        semantic_weight: float,
        keyword_weight: float,
    ) -> list[RetrievalResult]:
        """Merge results by multiplying scores.

        This approach strongly favors documents that have high scores in both methods.

        Args:
            semantic_results: Results from semantic search.
            keyword_results: Results from keyword search.
            semantic_weight: Weight for semantic search results.
            keyword_weight: Weight for keyword search results.

        Returns:
            Merged and reranked results.
        """
        semantic_map = {}
        keyword_map = {}

        # Create maps for faster lookup
        for result in semantic_results:
            result_id = result.metadata.get(
                "id", result.metadata.get("simple_id", hash(result.content))
            )
            semantic_map[str(result_id)] = result

        for result in keyword_results:
            result_id = result.metadata.get(
                "id", result.metadata.get("simple_id", hash(result.content))
            )
            keyword_map[str(result_id)] = result

        # Find common documents and calculate multiplicative score
        result_map = {}

        # Process all semantic results
        for result_id, semantic_result in semantic_map.items():
            if result_id in keyword_map:
                # Document exists in both sets - multiply scores
                keyword_result = keyword_map[result_id]
                new_score = (semantic_result.relevance_score**semantic_weight) * (
                    keyword_result.relevance_score**keyword_weight
                )

                result = RetrievalResult(
                    content=semantic_result.content,
                    metadata=semantic_result.metadata,
                    relevance_score=new_score,
                    distance=1.0 - new_score,
                )
                result_map[result_id] = result
            else:
                # Only in semantic results - reduce score
                adjusted_score = semantic_result.relevance_score * semantic_weight
                semantic_result.relevance_score = adjusted_score
                semantic_result.distance = 1.0 - adjusted_score
                result_map[result_id] = semantic_result

        # Add keyword-only results
        for result_id, keyword_result in keyword_map.items():
            if result_id not in result_map:
                # Only in keyword results - reduce score
                adjusted_score = keyword_result.relevance_score * keyword_weight
                keyword_result.relevance_score = adjusted_score
                keyword_result.distance = 1.0 - adjusted_score
                result_map[result_id] = keyword_result

        # Convert to list and sort
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return combined_results

    @staticmethod
    def _merge_rank_fusion(
        semantic_results: list[RetrievalResult],
        keyword_results: list[RetrievalResult],
        semantic_weight: float,
        keyword_weight: float,
    ) -> list[RetrievalResult]:
        """Merge results using rank fusion (Reciprocal Rank Fusion).

        This method uses document ranking positions rather than scores, which can be
        more robust when the score distributions are very different between methods.

        Args:
            semantic_results: Results from semantic search.
            keyword_results: Results from keyword search.
            semantic_weight: Weight for semantic search results.
            keyword_weight: Weight for keyword search results.

        Returns:
            Merged and reranked results.
        """
        # Constant for RRF calculation
        k = 60  # Standard value from literature

        # Create maps from document ID to rank
        semantic_ranks = {}
        for rank, result in enumerate(semantic_results):
            result_id = result.metadata.get(
                "id", result.metadata.get("simple_id", hash(result.content))
            )
            semantic_ranks[str(result_id)] = rank + 1  # 1-based ranking

        keyword_ranks = {}
        for rank, result in enumerate(keyword_results):
            result_id = result.metadata.get(
                "id", result.metadata.get("simple_id", hash(result.content))
            )
            keyword_ranks[str(result_id)] = rank + 1  # 1-based ranking

        # Collect all documents
        all_docs = set(semantic_ranks.keys()) | set(keyword_ranks.keys())

        # Calculate RRF scores
        rrf_scores = {}
        for doc_id in all_docs:
            semantic_score = (
                semantic_weight / (k + semantic_ranks.get(doc_id, 1000))
                if doc_id in semantic_ranks
                else 0
            )
            keyword_score = (
                keyword_weight / (k + keyword_ranks.get(doc_id, 1000))
                if doc_id in keyword_ranks
                else 0
            )
            rrf_scores[doc_id] = semantic_score + keyword_score

        # Create result map
        result_map = {}
        for doc_id in all_docs:
            # Find the original result
            if doc_id in semantic_ranks:
                original_result = semantic_results[semantic_ranks[doc_id] - 1]
            else:
                original_result = keyword_results[keyword_ranks[doc_id] - 1]

            # Create a new result with the RRF score
            result = RetrievalResult(
                content=original_result.content,
                metadata=original_result.metadata,
                relevance_score=rrf_scores[doc_id],
                distance=1.0 - rrf_scores[doc_id],
            )
            result_map[doc_id] = result

        # Convert to list and sort
        combined_results = list(result_map.values())

        # Normalize scores to 0-1 range
        if combined_results:
            max_score = max(result.relevance_score for result in combined_results)
            if max_score > 0:
                for result in combined_results:
                    result.relevance_score /= max_score
                    result.distance = 1.0 - result.relevance_score

        combined_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return combined_results


class HybridSearchEngine:
    """Unified search engine combining semantic and keyword search.

    This class provides a unified interface for hybrid search, handling the
    combination of semantic (vector) and keyword (BM25) search methods.
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        merge_strategy: str = "weighted_score",
    ):
        """Initialize the hybrid search engine.

        Args:
            knowledge_base: KnowledgeBase instance for semantic search.
            semantic_weight: Weight for semantic search results (0-1).
            keyword_weight: Weight for keyword search results (0-1).
            merge_strategy: Strategy for merging results (weighted_score, score_add, score_multiply, rank_fusion).
        """
        self.knowledge_base = knowledge_base
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.merge_strategy = merge_strategy
        self.bm25_engine = BM25SearchEngine()
        self.is_indexed = False

    def index_documents(self) -> None:
        """Index documents from the knowledge base for keyword search.

        This creates a BM25 index from the documents in the knowledge base.
        """
        try:
            # Fetch documents from ChromaDB
            # We limit to a reasonable number to avoid performance issues
            max_docs = 10000
            count = self.knowledge_base.collection.count()
            limit = min(count, max_docs)

            if limit == 0:
                logger.warning("No documents in collection for indexing")
                return

            logger.info(f"Indexing {limit} documents for BM25 search")

            # Get documents from collection
            results = self.knowledge_base.collection.get(limit=limit)

            # Prepare documents for BM25 indexing
            documents = []
            for i, (doc, metadata) in enumerate(
                zip(results["documents"], results["metadatas"], strict=False)
            ):
                documents.append((doc, metadata))

            # Index documents
            self.bm25_engine.index_documents(documents)
            self.is_indexed = True
            logger.info(f"Indexed {len(documents)} documents for BM25 search")

        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            self.is_indexed = False

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter: dict[str, Any] | RetrievalFilter | None = None,
        semantic_only: bool = False,
        keyword_only: bool = False,
        settings: RetrievalSettings | None = None,
        semantic_weight: float | None = None,
        keyword_weight: float | None = None,
    ) -> list[RetrievalResult]:
        """Perform a hybrid search with semantic and keyword components.

        Args:
            query: The search query.
            n_results: Number of results to return.
            filter: Optional filter to apply.
            semantic_only: Whether to use only semantic search.
            keyword_only: Whether to use only keyword search.
            settings: Optional retrieval settings to override other parameters.
            semantic_weight: Optional weight for semantic search results (overrides self.semantic_weight).
            keyword_weight: Optional weight for keyword search results (overrides self.keyword_weight).

        Returns:
            List of search results.
        """
        # Apply settings if provided
        if settings:
            n_results = settings.num_results
            semantic_weight_val = settings.semantic_weight
            keyword_weight_val = settings.keyword_weight
        else:
            # Use provided weights, or fall back to defaults
            semantic_weight_val = (
                semantic_weight if semantic_weight is not None else self.semantic_weight
            )
            keyword_weight_val = (
                keyword_weight if keyword_weight is not None else self.keyword_weight
            )

        # Ensure we are indexed for keyword search
        if not self.is_indexed and not semantic_only:
            logger.info("Documents not indexed for BM25, indexing now...")
            self.index_documents()

        # Handle semantic-only search
        if semantic_only or keyword_only or not self.is_indexed:
            if keyword_only and self.is_indexed:
                return self._keyword_search(query, n_results, filter)
            else:
                return self._semantic_search(query, n_results, filter)

        # Fetch more results than needed to allow for merging
        fetch_n = min(n_results * 2, 20)

        # Perform both search types
        semantic_results = self._semantic_search(query, fetch_n, filter)
        keyword_results = self._keyword_search(query, fetch_n, filter)

        # Merge results
        merged_results = HybridSearchMerger.merge_results(
            semantic_results,
            keyword_results,
            semantic_weight_val,
            keyword_weight_val,
            self.merge_strategy,
        )

        # Return requested number of results
        return merged_results[:n_results]

    def _semantic_search(
        self,
        query: str,
        n_results: int,
        filter: dict[str, Any] | RetrievalFilter | None = None,
    ) -> list[RetrievalResult]:
        """Perform semantic search using the knowledge base.

        Args:
            query: The search query.
            n_results: Number of results to return.
            filter: Optional filter to apply.

        Returns:
            List of search results.
        """
        # Create settings that disable hybrid search to avoid recursion
        settings = RetrievalSettings(
            use_hybrid_search=False,
            num_results=n_results,
            rerank_results=False,
        )

        return self.knowledge_base.retrieve(query, n_results, filter, settings=settings)

    def _keyword_search(
        self,
        query: str,
        n_results: int,
        filter: dict[str, Any] | RetrievalFilter | None = None,
    ) -> list[RetrievalResult]:
        """Perform keyword search using the BM25 engine.

        Args:
            query: The search query.
            n_results: Number of results to return.
            filter: Optional filter to apply.

        Returns:
            List of search results.
        """
        if not self.is_indexed:
            logger.warning("BM25 engine not indexed, cannot perform keyword search")
            return []

        # Create filter function if filter is provided
        filter_func = None
        if filter:
            if isinstance(filter, RetrievalFilter):
                where_clause = filter.where
                where_document = filter.where_document

                def filter_func(doc_id, content, metadata):
                    # Simple filtering - actual implementation would be more complex
                    # This is a placeholder for document filtering based on metadata
                    if where_clause:
                        # Check if metadata matches where clause
                        # This is a simplified implementation
                        for key, value in where_clause.items():
                            if key not in metadata or metadata[key] != value:
                                return False

                    if where_document:
                        # Check if document content matches where_document clause
                        # This is a simplified implementation
                        if "$contains" in where_document:
                            return where_document["$contains"] in content
                        if "$not_contains" in where_document:
                            return where_document["$not_contains"] not in content

                    return True

            elif isinstance(filter, dict):
                # Simple direct metadata filter
                where_clause = filter

                def filter_func(doc_id, content, metadata):
                    for key, value in where_clause.items():
                        if key not in metadata or metadata[key] != value:
                            return False
                    return True

        # Perform search with filter
        return self.bm25_engine.search(query, n_results, filter_func)


def retrieve_hybrid(
    knowledge_base: KnowledgeBase,
    query: str,
    n_results: int = 5,
    filter: dict[str, Any] | RetrievalFilter | None = None,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3,
    merge_strategy: str = "weighted_score",
) -> list[RetrievalResult]:
    """Simplified function for performing hybrid search.

    This is a convenience function for easy integration with existing code.

    Args:
        knowledge_base: Knowledge base to search.
        query: The search query.
        n_results: Number of results to return.
        filter: Optional filter to apply.
        semantic_weight: Weight for semantic search results (0-1).
        keyword_weight: Weight for keyword search results (0-1).
        merge_strategy: Strategy for merging results.

    Returns:
        List of search results.
    """
    engine = HybridSearchEngine(knowledge_base, semantic_weight, keyword_weight, merge_strategy)
    engine.index_documents()
    return engine.search(query, n_results, filter)
