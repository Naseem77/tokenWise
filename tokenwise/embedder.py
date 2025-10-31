"""Embedding generation module."""

from typing import List, Dict
import openai
from .config import get_settings
import hashlib
import json


class EmbeddingService:
    """Handles text embedding generation."""

    def __init__(self):
        """Initialize embedding service."""
        self.settings = get_settings()
        self.client = openai.OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.embedding_model
        self._cache: Dict[str, List[float]] = {}

    async def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed
            use_cache: Whether to use cache

        Returns:
            Embedding vector
        """
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                return self._cache[cache_key]

        try:
            # Call OpenAI API
            response = self.client.embeddings.create(
                model=self.model, input=text, encoding_format="float"
            )

            embedding = response.data[0].embedding

            # Cache result
            if use_cache:
                cache_key = self._get_cache_key(text)
                self._cache[cache_key] = embedding

            return embedding

        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536  # Default dimension for text-embedding-3-small

    async def embed_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to embed
            use_cache: Whether to use cache

        Returns:
            List of embedding vectors
        """
        # Check which texts need embedding
        results = [None] * len(texts)
        texts_to_embed = []
        indices_to_embed = []

        for i, text in enumerate(texts):
            if use_cache:
                cache_key = self._get_cache_key(text)
                if cache_key in self._cache:
                    results[i] = self._cache[cache_key]
                    continue

            texts_to_embed.append(text)
            indices_to_embed.append(i)

        # Embed remaining texts
        if texts_to_embed:
            try:
                response = self.client.embeddings.create(
                    model=self.model, input=texts_to_embed, encoding_format="float"
                )

                for idx, data in zip(indices_to_embed, response.data):
                    embedding = data.embedding
                    results[idx] = embedding

                    # Cache result
                    if use_cache:
                        cache_key = self._get_cache_key(texts_to_embed[indices_to_embed.index(idx)])
                        self._cache[cache_key] = embedding

            except Exception as e:
                print(f"Error generating batch embeddings: {e}")
                # Fill remaining with zero vectors
                for idx in indices_to_embed:
                    if results[idx] is None:
                        results[idx] = [0.0] * 1536

        return results

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()

    def clear_cache(self):
        """Clear embedding cache."""
        self._cache.clear()
