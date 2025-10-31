"""
TokenWise - Smart Context Optimization for LLMs

Reduce token usage by 70-90% while maintaining response quality.
"""

__version__ = "1.0.0"
__author__ = "TokenWise Team"
__license__ = "MIT"

from .optimizer import ContextOptimizer
from .models import (
    ContextChunk,
    OptimizationRequest,
    OptimizationResponse,
    OptimizationOptions,
    ChunkingOptions,
)

__all__ = [
    "ContextOptimizer",
    "ContextChunk",
    "OptimizationRequest",
    "OptimizationResponse",
    "OptimizationOptions",
    "ChunkingOptions",
]
