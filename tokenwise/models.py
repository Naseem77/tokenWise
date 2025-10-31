"""Data models for TokenWise."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ContextChunk(BaseModel):
    """Represents a chunk of context."""

    id: str
    text: str
    type: Literal["code", "docs", "conversation", "other"] = "other"
    source: Optional[str] = None
    position: Optional[int] = None
    total_chunks: Optional[int] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relationships: List[str] = Field(default_factory=list)
    token_count: Optional[int] = None


class ScoredChunk(BaseModel):
    """A chunk with relevance scores."""

    chunk: ContextChunk
    relevance_score: float
    embedding_score: float = 0.0
    keyword_score: float = 0.0
    recency_score: float = 0.0
    relationship_score: float = 0.0
    reason: Optional[str] = None


class OptimizationRequest(BaseModel):
    """Request for context optimization."""

    query: str
    context: List[Dict[str, Any]]
    target_tokens: Optional[int] = None
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OptimizationOptions(BaseModel):
    """Options for optimization."""

    strategy: Literal["top-n", "diversity", "dependency"] = "diversity"
    include_metadata: bool = True
    preserve_order: bool = False
    min_relevance_score: float = 0.3
    diversity_lambda: float = 0.5  # For MMR algorithm


class OptimizedChunkResult(BaseModel):
    """A single optimized chunk in the result."""

    id: str
    text: str
    relevance_score: float
    reason: str
    source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OptimizationStats(BaseModel):
    """Statistics about the optimization."""

    original_tokens: int
    optimized_tokens: int
    reduction_percent: float
    estimated_savings_usd: float
    processing_time_ms: float
    chunks_analyzed: int
    chunks_selected: int


class OptimizationResponse(BaseModel):
    """Response from context optimization."""

    optimized_context: List[OptimizedChunkResult]
    stats: OptimizationStats


class ChunkingOptions(BaseModel):
    """Options for chunking content."""

    strategy: Literal["fixed", "semantic", "sliding"] = "semantic"
    chunk_size: int = 512
    overlap: int = 50
    preserve_code_blocks: bool = True
    preserve_paragraphs: bool = True
