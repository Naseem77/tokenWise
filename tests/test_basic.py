"""Basic tests for TokenWise components."""

import pytest
from tokenwise.models import ContextChunk, ChunkingOptions, OptimizationOptions
from tokenwise.chunker import ContextChunker
from tokenwise.utils import count_tokens, extract_keywords, calculate_cosine_similarity


def test_token_counting():
    """Test token counting utility."""
    text = "Hello world, this is a test."
    tokens = count_tokens(text)
    assert tokens > 0
    assert isinstance(tokens, int)


def test_keyword_extraction():
    """Test keyword extraction."""
    text = "Python is a great programming language for machine learning and data science."
    keywords = extract_keywords(text, top_n=5)
    assert len(keywords) <= 5
    assert "python" in keywords or "programming" in keywords


def test_cosine_similarity():
    """Test cosine similarity calculation."""
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    vec3 = [0.0, 1.0, 0.0]

    # Same vectors should have similarity of 1
    sim1 = calculate_cosine_similarity(vec1, vec2)
    assert abs(sim1 - 1.0) < 0.01

    # Orthogonal vectors should have similarity of 0
    sim2 = calculate_cosine_similarity(vec1, vec3)
    assert abs(sim2) < 0.01


def test_fixed_chunking():
    """Test fixed-size chunking."""
    content = {
        "id": "test_doc",
        "text": "This is a test document. " * 100,  # Repeat to make it large
        "type": "docs",
    }

    options = ChunkingOptions(strategy="fixed", chunk_size=50)
    chunker = ContextChunker(options)
    chunks = chunker.chunk(content)

    assert len(chunks) > 1
    assert all(isinstance(chunk, ContextChunk) for chunk in chunks)
    assert all(chunk.source == "test_doc" for chunk in chunks)


def test_semantic_chunking():
    """Test semantic chunking."""
    content = {
        "id": "test_code",
        "text": """
        def function1():
            return "Hello"
        
        def function2():
            return "World"
        
        class MyClass:
            def method(self):
                pass
        """,
        "type": "code",
    }

    options = ChunkingOptions(strategy="semantic", chunk_size=100)
    chunker = ContextChunker(options)
    chunks = chunker.chunk(content)

    assert len(chunks) >= 1
    assert all(chunk.type == "code" for chunk in chunks)


def test_chunk_metadata():
    """Test chunk metadata preservation."""
    content = {
        "id": "test_doc",
        "text": "Test content " * 50,
        "type": "docs",
        "metadata": {"author": "test", "date": "2024"},
    }

    chunker = ContextChunker()
    chunks = chunker.chunk(content)

    assert all(chunk.metadata.get("author") == "test" for chunk in chunks)
    assert all(chunk.total_chunks == len(chunks) for chunk in chunks)


def test_optimization_options():
    """Test optimization options validation."""
    options = OptimizationOptions(
        strategy="diversity", min_relevance_score=0.3, diversity_lambda=0.5
    )

    assert options.strategy == "diversity"
    assert options.min_relevance_score == 0.3
    assert options.diversity_lambda == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
