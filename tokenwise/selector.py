"""Context selection module."""

from typing import List, Set, Dict
from .models import ScoredChunk, OptimizationOptions
from .utils import count_tokens, calculate_cosine_similarity
import random


class ContextSelector:
    """Selects optimal chunks within token budget."""

    def __init__(self):
        """Initialize selector."""
        pass

    def select_chunks(
        self, scored_chunks: List[ScoredChunk], token_budget: int, options: OptimizationOptions
    ) -> List[ScoredChunk]:
        """
        Select optimal chunks within token budget.

        Args:
            scored_chunks: List of scored chunks
            token_budget: Maximum tokens allowed
            options: Optimization options

        Returns:
            Selected chunks
        """
        strategy = options.strategy

        if strategy == "top-n":
            return self._select_top_n(scored_chunks, token_budget, options)
        elif strategy == "diversity":
            return self._select_diverse(scored_chunks, token_budget, options)
        elif strategy == "dependency":
            return self._select_with_dependencies(scored_chunks, token_budget, options)
        else:
            raise ValueError(f"Unknown selection strategy: {strategy}")

    def _select_top_n(
        self, scored_chunks: List[ScoredChunk], token_budget: int, options: OptimizationOptions
    ) -> List[ScoredChunk]:
        """
        Simple top-N selection by score.

        Args:
            scored_chunks: Scored chunks
            token_budget: Token budget
            options: Options

        Returns:
            Top N chunks within budget
        """
        selected = []
        current_tokens = 0

        for sc in scored_chunks:
            # Skip if below minimum relevance
            if sc.relevance_score < options.min_relevance_score:
                continue

            chunk_tokens = sc.chunk.token_count or count_tokens(sc.chunk.text)

            if current_tokens + chunk_tokens <= token_budget:
                selected.append(sc)
                current_tokens += chunk_tokens
            else:
                break

        return selected

    def _select_diverse(
        self, scored_chunks: List[ScoredChunk], token_budget: int, options: OptimizationOptions
    ) -> List[ScoredChunk]:
        """
        Select diverse chunks using Maximal Marginal Relevance (MMR).

        Args:
            scored_chunks: Scored chunks
            token_budget: Token budget
            options: Options with diversity_lambda

        Returns:
            Diverse set of chunks
        """
        # Filter by minimum relevance
        candidates = [
            sc for sc in scored_chunks if sc.relevance_score >= options.min_relevance_score
        ]

        if not candidates:
            return []

        selected = []
        current_tokens = 0
        lambda_param = options.diversity_lambda

        # Start with highest scoring chunk
        first = candidates[0]
        first_tokens = first.chunk.token_count or count_tokens(first.chunk.text)

        if first_tokens <= token_budget:
            selected.append(first)
            current_tokens = first_tokens
            candidates.remove(first)

        # MMR algorithm: balance relevance with diversity
        while candidates and current_tokens < token_budget:
            mmr_scores = []

            for candidate in candidates:
                # Calculate max similarity to already selected chunks
                max_similarity = 0.0
                for selected_chunk in selected:
                    similarity = self._calculate_chunk_similarity(
                        candidate.chunk.text, selected_chunk.chunk.text
                    )
                    max_similarity = max(max_similarity, similarity)

                # MMR formula: λ * Relevance - (1-λ) * MaxSimilarity
                mmr_score = (
                    lambda_param * candidate.relevance_score - (1 - lambda_param) * max_similarity
                )

                mmr_scores.append((candidate, mmr_score))

            # Sort by MMR score
            mmr_scores.sort(key=lambda x: x[1], reverse=True)

            # Try to add best MMR chunk
            added = False
            for candidate, mmr_score in mmr_scores:
                chunk_tokens = candidate.chunk.token_count or count_tokens(candidate.chunk.text)

                if current_tokens + chunk_tokens <= token_budget:
                    selected.append(candidate)
                    current_tokens += chunk_tokens
                    candidates.remove(candidate)
                    added = True
                    break

            # If no chunk fits, break
            if not added:
                break

        # Sort by original relevance score for return
        selected.sort(key=lambda x: x.relevance_score, reverse=True)

        return selected

    def _select_with_dependencies(
        self, scored_chunks: List[ScoredChunk], token_budget: int, options: OptimizationOptions
    ) -> List[ScoredChunk]:
        """
        Select chunks including their dependencies.

        Args:
            scored_chunks: Scored chunks
            token_budget: Token budget
            options: Options

        Returns:
            Chunks with dependencies included
        """
        # Build dependency graph
        chunk_map = {sc.chunk.id: sc for sc in scored_chunks}
        selected_ids: Set[str] = set()
        selected = []
        current_tokens = 0

        # Process chunks by relevance score
        for sc in scored_chunks:
            if sc.relevance_score < options.min_relevance_score:
                continue

            # Skip if already selected
            if sc.chunk.id in selected_ids:
                continue

            # Collect this chunk and its dependencies
            cluster = self._get_dependency_cluster(sc, chunk_map)

            # Calculate total tokens for cluster
            cluster_tokens = sum(c.chunk.token_count or count_tokens(c.chunk.text) for c in cluster)

            # Add cluster if it fits
            if current_tokens + cluster_tokens <= token_budget:
                for chunk in cluster:
                    if chunk.chunk.id not in selected_ids:
                        selected.append(chunk)
                        selected_ids.add(chunk.chunk.id)
                        current_tokens += chunk.chunk.token_count or count_tokens(chunk.chunk.text)
            else:
                # Try to add just the main chunk without dependencies
                main_tokens = sc.chunk.token_count or count_tokens(sc.chunk.text)
                if current_tokens + main_tokens <= token_budget:
                    selected.append(sc)
                    selected_ids.add(sc.chunk.id)
                    current_tokens += main_tokens

        # Sort by relevance
        selected.sort(key=lambda x: x.relevance_score, reverse=True)

        return selected

    def _get_dependency_cluster(
        self, scored_chunk: ScoredChunk, chunk_map: Dict[str, ScoredChunk]
    ) -> List[ScoredChunk]:
        """
        Get chunk and its dependencies.

        Args:
            scored_chunk: Main chunk
            chunk_map: Map of chunk IDs to scored chunks

        Returns:
            List of chunks in dependency cluster
        """
        cluster = [scored_chunk]
        visited = {scored_chunk.chunk.id}
        queue = list(scored_chunk.chunk.relationships)

        # BFS to find dependencies
        while queue:
            dep_id = queue.pop(0)

            if dep_id in visited or dep_id not in chunk_map:
                continue

            visited.add(dep_id)
            dep_chunk = chunk_map[dep_id]
            cluster.append(dep_chunk)

            # Add its dependencies too (1 level deep)
            # Uncomment for deeper traversal:
            # queue.extend(dep_chunk.chunk.relationships)

        return cluster

    def _calculate_chunk_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two chunks (simple version).

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0 and 1
        """
        # Simple word-based similarity (Jaccard)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def reorder_chunks(
        self, selected_chunks: List[ScoredChunk], preserve_order: bool = False
    ) -> List[ScoredChunk]:
        """
        Reorder chunks for optimal context assembly.

        Args:
            selected_chunks: Selected chunks
            preserve_order: Whether to preserve original order

        Returns:
            Reordered chunks
        """
        if preserve_order:
            # Sort by original position if available
            return sorted(
                selected_chunks,
                key=lambda sc: sc.chunk.position if sc.chunk.position is not None else 0,
            )

        # Group by source and maintain order within source
        sources: Dict[str, List[ScoredChunk]] = {}
        for sc in selected_chunks:
            source = sc.chunk.source or "unknown"
            if source not in sources:
                sources[source] = []
            sources[source].append(sc)

        # Sort within each source by position
        for source in sources:
            sources[source].sort(
                key=lambda sc: sc.chunk.position if sc.chunk.position is not None else 0
            )

        # Flatten back to list (sources sorted by first chunk relevance)
        result = []
        for source in sorted(
            sources.keys(), key=lambda s: max(sc.relevance_score for sc in sources[s]), reverse=True
        ):
            result.extend(sources[source])

        return result
