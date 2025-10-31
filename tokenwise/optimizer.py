"""Main optimization orchestrator."""

from typing import List, Dict, Any
from .models import (
    ContextChunk,
    OptimizationOptions,
    OptimizationResponse,
    OptimizationStats,
    OptimizedChunkResult,
    ChunkingOptions,
)
from .chunker import ContextChunker
from .ranker import RelevanceRanker
from .selector import ContextSelector
from .embedder import EmbeddingService
from .cache import get_cache
from .utils import count_tokens, estimate_cost_savings
import time
from datetime import datetime


class ContextOptimizer:
    """Main context optimization service."""

    def __init__(self):
        """Initialize optimizer with all components."""
        self.embedder = EmbeddingService()
        self.ranker = RelevanceRanker(self.embedder)
        self.selector = ContextSelector()
        self.cache = get_cache()

    async def optimize(
        self,
        query: str,
        context: List[Dict[str, Any]],
        target_tokens: int = 4000,
        options: OptimizationOptions = None,
    ) -> OptimizationResponse:
        """
        Optimize context for query.

        Args:
            query: User query
            context: List of context items to optimize
            target_tokens: Target token budget
            options: Optimization options

        Returns:
            Optimization response with selected chunks and stats
        """
        start_time = time.time()

        if options is None:
            options = OptimizationOptions()

        # Step 1: Chunk all context items
        all_chunks = []
        for item in context:
            chunker = ContextChunker(self._get_chunking_options(item))
            chunks = chunker.chunk(item)
            all_chunks.extend(chunks)

        if not all_chunks:
            return self._empty_response(start_time)

        # Calculate original token count
        original_tokens = sum(chunk.token_count or count_tokens(chunk.text) for chunk in all_chunks)

        # Step 2: Rank chunks by relevance
        scored_chunks = await self.ranker.rank_chunks(query, all_chunks)

        # Step 3: Boost related chunks
        scored_chunks = await self.ranker.boost_related_chunks(scored_chunks)

        # Step 4: Select best chunks within budget
        selected_chunks = self.selector.select_chunks(scored_chunks, target_tokens, options)

        # Step 5: Reorder for optimal assembly
        if options.preserve_order:
            selected_chunks = self.selector.reorder_chunks(selected_chunks, preserve_order=True)

        # Calculate final token count
        optimized_tokens = sum(
            chunk.chunk.token_count or count_tokens(chunk.chunk.text) for chunk in selected_chunks
        )

        # Calculate statistics
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        reduction_percent = (
            ((original_tokens - optimized_tokens) / original_tokens * 100)
            if original_tokens > 0
            else 0
        )
        estimated_savings = estimate_cost_savings(original_tokens, optimized_tokens)

        stats = OptimizationStats(
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            reduction_percent=round(reduction_percent, 1),
            estimated_savings_usd=estimated_savings,
            processing_time_ms=round(processing_time, 1),
            chunks_analyzed=len(all_chunks),
            chunks_selected=len(selected_chunks),
        )

        # Format optimized chunks
        optimized_context = [
            OptimizedChunkResult(
                id=sc.chunk.id,
                text=sc.chunk.text,
                relevance_score=round(sc.relevance_score, 3),
                reason=sc.reason,
                source=sc.chunk.source,
                metadata=sc.chunk.metadata if options.include_metadata else {},
            )
            for sc in selected_chunks
        ]

        return OptimizationResponse(optimized_context=optimized_context, stats=stats)

    def _get_chunking_options(self, item: Dict[str, Any]) -> ChunkingOptions:
        """
        Get chunking options based on content type.

        Args:
            item: Context item

        Returns:
            Chunking options
        """
        content_type = item.get("type", "other")

        # Use semantic chunking for code, fixed for others
        if content_type == "code":
            return ChunkingOptions(
                strategy="semantic", chunk_size=512, overlap=50, preserve_code_blocks=True
            )
        else:
            return ChunkingOptions(
                strategy="semantic", chunk_size=512, overlap=50, preserve_paragraphs=True
            )

    def _empty_response(self, start_time: float) -> OptimizationResponse:
        """
        Create empty response when no chunks available.

        Args:
            start_time: Start time for processing time calculation

        Returns:
            Empty optimization response
        """
        processing_time = (time.time() - start_time) * 1000

        return OptimizationResponse(
            optimized_context=[],
            stats=OptimizationStats(
                original_tokens=0,
                optimized_tokens=0,
                reduction_percent=0.0,
                estimated_savings_usd=0.0,
                processing_time_ms=round(processing_time, 1),
                chunks_analyzed=0,
                chunks_selected=0,
            ),
        )
