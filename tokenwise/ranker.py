"""Relevance ranking module."""

from typing import List, Dict, Set
from .models import ContextChunk, ScoredChunk
from .embedder import EmbeddingService
from .utils import extract_keywords, calculate_recency_score, calculate_cosine_similarity
from .config import get_settings
import asyncio


class RelevanceRanker:
    """Ranks context chunks by relevance to query."""

    def __init__(self, embedder: EmbeddingService = None):
        """
        Initialize ranker.

        Args:
            embedder: Embedding service instance
        """
        self.embedder = embedder or EmbeddingService()
        self.settings = get_settings()

    async def rank_chunks(
        self,
        query: str,
        chunks: List[ContextChunk],
        use_embedding: bool = True,
        use_keywords: bool = True,
        use_recency: bool = True,
        use_relationships: bool = True,
    ) -> List[ScoredChunk]:
        """
        Rank chunks by relevance to query.

        Args:
            query: User query
            chunks: List of context chunks
            use_embedding: Whether to use embedding similarity
            use_keywords: Whether to use keyword matching
            use_recency: Whether to use recency scoring
            use_relationships: Whether to use relationship scoring

        Returns:
            List of scored chunks sorted by relevance
        """
        if not chunks:
            return []

        # Extract query keywords
        query_keywords = set(extract_keywords(query, top_n=15))

        # Get query embedding
        query_embedding = None
        if use_embedding:
            query_embedding = await self.embedder.embed_text(query)

        # Get chunk embeddings (batch)
        chunk_embeddings = None
        if use_embedding:
            chunk_texts = [chunk.text for chunk in chunks]
            chunk_embeddings = await self.embedder.embed_batch(chunk_texts)

        # Score each chunk
        scored_chunks = []
        for i, chunk in enumerate(chunks):
            # Calculate individual scores
            embedding_score = 0.0
            if use_embedding and query_embedding and chunk_embeddings:
                embedding_score = calculate_cosine_similarity(query_embedding, chunk_embeddings[i])

            keyword_score = 0.0
            if use_keywords:
                keyword_score = self._calculate_keyword_score(chunk.text, query_keywords)

            recency_score = 0.0
            if use_recency:
                recency_score = calculate_recency_score(chunk.timestamp)

            relationship_score = 0.0
            if use_relationships:
                relationship_score = self._calculate_relationship_score(chunk, chunks)

            # Combine scores with weights
            relevance_score = (
                self.settings.embedding_weight * embedding_score
                + self.settings.keyword_weight * keyword_score
                + self.settings.recency_weight * recency_score
                + self.settings.relationship_weight * relationship_score
            )

            # Generate reason
            reason = self._generate_reason(
                embedding_score, keyword_score, recency_score, relationship_score
            )

            scored_chunk = ScoredChunk(
                chunk=chunk,
                relevance_score=relevance_score,
                embedding_score=embedding_score,
                keyword_score=keyword_score,
                recency_score=recency_score,
                relationship_score=relationship_score,
                reason=reason,
            )

            scored_chunks.append(scored_chunk)

        # Sort by relevance score
        scored_chunks.sort(key=lambda x: x.relevance_score, reverse=True)

        return scored_chunks

    def _calculate_keyword_score(self, text: str, query_keywords: Set[str]) -> float:
        """
        Calculate keyword matching score.

        Args:
            text: Chunk text
            query_keywords: Set of query keywords

        Returns:
            Keyword score between 0 and 1
        """
        if not query_keywords:
            return 0.0

        # Extract chunk keywords
        text_lower = text.lower()
        chunk_keywords = set(extract_keywords(text_lower, top_n=30))

        # Count matches
        matches = query_keywords.intersection(chunk_keywords)

        # Also check for keyword presence in text (exact matches)
        exact_matches = sum(1 for kw in query_keywords if kw in text_lower)

        # Combine both metrics
        intersection_score = len(matches) / len(query_keywords) if query_keywords else 0
        exact_score = min(exact_matches / len(query_keywords), 1.0) if query_keywords else 0

        # Average of both scores
        return (intersection_score + exact_score) / 2

    def _calculate_relationship_score(
        self, chunk: ContextChunk, all_chunks: List[ContextChunk]
    ) -> float:
        """
        Calculate relationship score based on connections to other chunks.

        Args:
            chunk: Current chunk
            all_chunks: All chunks in context

        Returns:
            Relationship score between 0 and 1
        """
        if not chunk.relationships:
            return 0.0

        # Create chunk ID lookup
        chunk_ids = {c.id for c in all_chunks}

        # Count how many relationships exist in current context
        valid_relationships = sum(1 for rel_id in chunk.relationships if rel_id in chunk_ids)

        # Normalize by total possible relationships
        if len(all_chunks) <= 1:
            return 0.0

        score = valid_relationships / min(len(chunk.relationships), len(all_chunks) - 1)

        return score

    def _generate_reason(
        self,
        embedding_score: float,
        keyword_score: float,
        recency_score: float,
        relationship_score: float,
    ) -> str:
        """
        Generate human-readable reason for relevance score.

        Args:
            embedding_score: Embedding similarity score
            keyword_score: Keyword matching score
            recency_score: Recency score
            relationship_score: Relationship score

        Returns:
            Reason string
        """
        reasons = []

        if embedding_score > 0.7:
            reasons.append("High semantic similarity")
        elif embedding_score > 0.5:
            reasons.append("Moderate semantic similarity")

        if keyword_score > 0.7:
            reasons.append("Strong keyword match")
        elif keyword_score > 0.4:
            reasons.append("Partial keyword match")

        if recency_score > 0.8:
            reasons.append("Recent content")

        if relationship_score > 0.5:
            reasons.append("Connected to relevant chunks")

        if not reasons:
            reasons.append("Low relevance")

        return " + ".join(reasons)

    async def boost_related_chunks(
        self, scored_chunks: List[ScoredChunk], boost_factor: float = 0.2
    ) -> List[ScoredChunk]:
        """
        Boost scores of chunks related to high-scoring chunks.

        Args:
            scored_chunks: List of scored chunks
            boost_factor: How much to boost related chunks

        Returns:
            Updated list of scored chunks
        """
        # Find high-scoring chunks (top 20%)
        threshold_idx = max(1, len(scored_chunks) // 5)
        high_scoring = scored_chunks[:threshold_idx]
        high_scoring_ids = {sc.chunk.id for sc in high_scoring}

        # Build relationship map
        relationships = {}
        for sc in scored_chunks:
            relationships[sc.chunk.id] = set(sc.chunk.relationships)

        # Boost related chunks
        for sc in scored_chunks:
            if sc.chunk.id not in high_scoring_ids:
                # Check if related to any high-scoring chunk
                for high_id in high_scoring_ids:
                    if high_id in relationships.get(
                        sc.chunk.id, set()
                    ) or sc.chunk.id in relationships.get(high_id, set()):
                        # Boost this chunk
                        sc.relevance_score *= 1 + boost_factor
                        sc.reason += " + Related to high-scoring chunk"
                        break

        # Re-sort after boosting
        scored_chunks.sort(key=lambda x: x.relevance_score, reverse=True)

        return scored_chunks
