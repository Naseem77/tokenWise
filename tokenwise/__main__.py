"""FastAPI application for TokenWise."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .models import (
    OptimizationRequest,
    OptimizationResponse,
    OptimizationOptions,
    ContextChunk
)
from .optimizer import ContextOptimizer
from .vector_store import get_vector_store
from .embedder import EmbeddingService
from .cache import get_cache
from .config import get_settings
import logging
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TokenWise",
    description="Context optimization API for LLMs - Reduce tokens, save costs, maintain quality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = get_settings()
optimizer = ContextOptimizer()
vector_store = get_vector_store()
cache = get_cache()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "TokenWise",
        "version": "1.0.0",
        "description": "Context optimization API for LLMs",
        "endpoints": {
            "optimize": "/optimize - Optimize context for a query",
            "health": "/health - Health check",
            "stats": "/stats - Get system statistics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check if OpenAI API key is set
        if not settings.openai_api_key:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "OpenAI API key not configured"
                }
            )
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "vector_store_chunks": vector_store.count()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.post("/optimize", response_model=OptimizationResponse)
async def optimize_context(request: OptimizationRequest):
    """
    Optimize context for a given query.
    
    This endpoint takes a user query and a list of context items,
    then returns an optimized subset that maximizes relevance while
    staying within the token budget.
    
    Args:
        request: Optimization request with query, context, and options
        
    Returns:
        Optimized context with statistics
    """
    try:
        # Validate request
        if not request.query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        if not request.context:
            raise HTTPException(status_code=400, detail="Context is required")
        
        # Parse options
        options_dict = request.options or {}
        options = OptimizationOptions(**options_dict)
        
        # Get target token budget
        target_tokens = request.target_tokens or settings.default_token_budget
        
        # Check cache
        cache_key = cache.generate_key(
            request.query,
            str(request.context),
            target_tokens,
            options_dict
        )
        
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached result")
            return cached_result
        
        # Perform optimization
        logger.info(f"Optimizing context for query: {request.query[:50]}...")
        result = await optimizer.optimize(
            query=request.query,
            context=request.context,
            target_tokens=target_tokens,
            options=options
        )
        
        # Cache result
        cache.set(cache_key, result, ttl=settings.cache_ttl)
        
        logger.info(
            f"Optimization complete: {result.stats.reduction_percent}% reduction, "
            f"{result.stats.processing_time_ms}ms"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Optimization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@app.post("/index")
async def index_context(
    context: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Index context in vector store for faster future queries.
    
    This endpoint allows pre-indexing of context items in the vector database
    for faster retrieval during optimization.
    
    Args:
        context: Context item to index
        background_tasks: FastAPI background tasks
        
    Returns:
        Success message with chunk count
    """
    try:
        from chunker import ContextChunker
        from models import ChunkingOptions
        
        # Chunk the content
        chunker = ContextChunker(ChunkingOptions())
        chunks = chunker.chunk(context)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No chunks generated from context")
        
        # Generate embeddings
        embedder = EmbeddingService()
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = await embedder.embed_batch(chunk_texts)
        
        # Add to vector store
        vector_store.add_chunks(chunks, embeddings)
        
        return {
            "status": "success",
            "chunks_indexed": len(chunks),
            "context_id": context.get("id", "unknown")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indexing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@app.get("/stats")
async def get_stats():
    """
    Get system statistics.
    
    Returns:
        System statistics including cache and vector store info
    """
    try:
        return {
            "timestamp": datetime.now().isoformat(),
            "vector_store": {
                "total_chunks": vector_store.count(),
                "persist_directory": settings.chroma_persist_directory
            },
            "cache": {
                "ttl": settings.cache_ttl,
                "type": "in-memory"
            },
            "config": {
                "default_token_budget": settings.default_token_budget,
                "embedding_model": settings.embedding_model,
                "scoring_weights": {
                    "embedding": settings.embedding_weight,
                    "keyword": settings.keyword_weight,
                    "recency": settings.recency_weight,
                    "relationship": settings.relationship_weight
                }
            }
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.post("/clear-cache")
async def clear_cache():
    """Clear the optimization cache."""
    try:
        cache.clear()
        return {
            "status": "success",
            "message": "Cache cleared"
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.post("/clear-vector-store")
async def clear_vector_store():
    """Clear the vector store."""
    try:
        vector_store.clear()
        return {
            "status": "success",
            "message": "Vector store cleared"
        }
    except Exception as e:
        logger.error(f"Failed to clear vector store: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear vector store: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Starting TokenWise API...")
    logger.info(f"Vector store chunks: {vector_store.count()}")
    logger.info(f"Token budget: {settings.default_token_budget}")
    logger.info(f"Embedding model: {settings.embedding_model}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down TokenWise API...")
    cache.cleanup_expired()


def main():
    """Main entry point for TokenWise CLI."""
    import uvicorn
    uvicorn.run(
        "tokenwise.__main__:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()

