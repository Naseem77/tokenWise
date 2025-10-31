"""Utility functions for TokenWise."""
import tiktoken
import hashlib
from typing import List, Optional
import re
from datetime import datetime
import math


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Count tokens in text using tiktoken.
    
    Args:
        text: Text to count tokens for
        model: Model name for encoding
        
    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(text))


def generate_chunk_id(text: str, source: str = "", position: int = 0) -> str:
    """
    Generate unique ID for a chunk.
    
    Args:
        text: Chunk text
        source: Source identifier
        position: Position in source
        
    Returns:
        Unique chunk ID
    """
    content = f"{source}_{position}_{text[:100]}"
    return hashlib.md5(content.encode()).hexdigest()[:16]


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """
    Extract keywords from text using simple frequency analysis.
    
    Args:
        text: Text to extract keywords from
        top_n: Number of top keywords to return
        
    Returns:
        List of keywords
    """
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Common stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Split into words and filter
    words = [w for w in text.split() if len(w) > 3 and w not in stop_words]
    
    # Count frequencies
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top N
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]


def calculate_recency_score(timestamp: Optional[datetime]) -> float:
    """
    Calculate recency score using exponential decay.
    
    Args:
        timestamp: Timestamp of content
        
    Returns:
        Recency score between 0 and 1
    """
    if timestamp is None:
        return 0.5  # Neutral score if no timestamp
    
    # Calculate age in hours
    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
    
    # Exponential decay with lambda = 0.01 (half-life ~ 69 hours)
    decay_rate = 0.01
    score = math.exp(-decay_rate * age_hours)
    
    return score


def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score between 0 and 1
    """
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same length")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def estimate_cost_savings(original_tokens: int, optimized_tokens: int, 
                         input_cost_per_1m: float = 3.0) -> float:
    """
    Estimate cost savings from optimization.
    
    Args:
        original_tokens: Original token count
        optimized_tokens: Optimized token count
        input_cost_per_1m: Cost per 1M input tokens
        
    Returns:
        Estimated savings in USD
    """
    tokens_saved = original_tokens - optimized_tokens
    savings = (tokens_saved / 1_000_000) * input_cost_per_1m
    return round(savings, 4)


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Text to split
        
    Returns:
        List of sentences
    """
    # Simple sentence splitting (can be improved with NLTK)
    sentence_endings = re.compile(r'[.!?]+[\s\n]')
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if s.strip()]


def is_code_block(text: str) -> bool:
    """
    Detect if text is likely a code block.
    
    Args:
        text: Text to check
        
    Returns:
        True if likely code, False otherwise
    """
    code_indicators = [
        r'\bdef\s+\w+\s*\(',  # Python function
        r'\bclass\s+\w+',     # Class definition
        r'\bfunction\s+\w+',  # JavaScript function
        r'\bif\s*\(',         # If statement
        r'\bfor\s*\(',        # For loop
        r'\bimport\s+',       # Import statement
        r'=>',                # Arrow function
        r'{\s*$',             # Opening brace
        r'^\s*[\}\]]\s*$',    # Closing brace/bracket
    ]
    
    for pattern in code_indicators:
        if re.search(pattern, text, re.MULTILINE):
            return True
    
    return False

