"""Vector database integration."""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from .models import ContextChunk, ScoredChunk
from .config import get_settings
import uuid


class VectorStore:
    """Vector database for storing and retrieving chunks."""

    def __init__(self):
        """Initialize vector store."""
        self.settings = get_settings()

        # Initialize ChromaDB
        self.client = chromadb.Client(
            Settings(
                persist_directory=self.settings.chroma_persist_directory, anonymized_telemetry=False
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="context_chunks", metadata={"description": "Context chunks for optimization"}
        )

    def add_chunks(self, chunks: List[ContextChunk], embeddings: List[List[float]]):
        """
        Add chunks to vector store.

        Args:
            chunks: List of context chunks
            embeddings: List of embedding vectors
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        ids = [chunk.id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "source": chunk.source or "",
                "type": chunk.type,
                "position": chunk.position or 0,
                "token_count": chunk.token_count or 0,
                "timestamp": chunk.timestamp.isoformat() if chunk.timestamp else "",
            }
            for chunk in chunks
        ]

        self.collection.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def search(self, query_embedding: List[float], n_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return

        Returns:
            List of search results with ids, documents, and distances
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append(
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                }
            )

        return formatted_results

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific chunk by ID.

        Args:
            chunk_id: Chunk ID

        Returns:
            Chunk data or None if not found
        """
        results = self.collection.get(ids=[chunk_id], include=["documents", "metadatas"])

        if not results["ids"]:
            return None

        return {
            "id": results["ids"][0],
            "document": results["documents"][0],
            "metadata": results["metadatas"][0],
        }

    def delete_chunks(self, chunk_ids: List[str]):
        """
        Delete chunks from store.

        Args:
            chunk_ids: List of chunk IDs to delete
        """
        self.collection.delete(ids=chunk_ids)

    def clear(self):
        """Clear all chunks from store."""
        self.client.delete_collection("context_chunks")
        self.collection = self.client.get_or_create_collection(
            name="context_chunks", metadata={"description": "Context chunks for optimization"}
        )

    def count(self) -> int:
        """
        Get total number of chunks in store.

        Returns:
            Number of chunks
        """
        return self.collection.count()


# Global vector store instance
_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """Get global vector store instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
