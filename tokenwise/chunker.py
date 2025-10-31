"""Context chunking module."""
from typing import List, Dict, Any
from .models import ContextChunk, ChunkingOptions
from .utils import count_tokens, generate_chunk_id, is_code_block, split_into_sentences
import re
from datetime import datetime


class ContextChunker:
    """Chunks large context into manageable pieces."""
    
    def __init__(self, options: ChunkingOptions = None):
        """
        Initialize chunker.
        
        Args:
            options: Chunking options
        """
        self.options = options or ChunkingOptions()
    
    def chunk(self, content: Dict[str, Any]) -> List[ContextChunk]:
        """
        Chunk content based on strategy.
        
        Args:
            content: Content to chunk with keys: id, text, type, etc.
            
        Returns:
            List of context chunks
        """
        strategy = self.options.strategy
        
        if strategy == "fixed":
            return self._chunk_fixed_size(content)
        elif strategy == "semantic":
            return self._chunk_semantic(content)
        elif strategy == "sliding":
            return self._chunk_sliding_window(content)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    def _chunk_fixed_size(self, content: Dict[str, Any]) -> List[ContextChunk]:
        """
        Chunk content into fixed-size pieces.
        
        Args:
            content: Content to chunk
            
        Returns:
            List of fixed-size chunks
        """
        text = content.get("text", "")
        source = content.get("id", "unknown")
        content_type = content.get("type", "other")
        
        # Split into words for approximate chunking
        words = text.split()
        chunks = []
        current_chunk = []
        current_tokens = 0
        position = 0
        
        for word in words:
            word_tokens = count_tokens(word)
            
            if current_tokens + word_tokens > self.options.chunk_size and current_chunk:
                # Create chunk
                chunk_text = " ".join(current_chunk)
                chunk_id = generate_chunk_id(chunk_text, source, position)
                
                chunks.append(ContextChunk(
                    id=chunk_id,
                    text=chunk_text,
                    type=content_type,
                    source=source,
                    position=position,
                    token_count=current_tokens,
                    metadata=content.get("metadata", {})
                ))
                
                current_chunk = []
                current_tokens = 0
                position += 1
            
            current_chunk.append(word)
            current_tokens += word_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_id = generate_chunk_id(chunk_text, source, position)
            
            chunks.append(ContextChunk(
                id=chunk_id,
                text=chunk_text,
                type=content_type,
                source=source,
                position=position,
                token_count=current_tokens,
                metadata=content.get("metadata", {})
            ))
        
        # Update total_chunks for all
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _chunk_semantic(self, content: Dict[str, Any]) -> List[ContextChunk]:
        """
        Chunk content at semantic boundaries (paragraphs, functions, etc.).
        
        Args:
            content: Content to chunk
            
        Returns:
            List of semantic chunks
        """
        text = content.get("text", "")
        source = content.get("id", "unknown")
        content_type = content.get("type", "other")
        
        chunks = []
        
        if content_type == "code" and self.options.preserve_code_blocks:
            # Split by function/class definitions
            segments = self._split_code_semantic(text)
        else:
            # Split by paragraphs or logical breaks
            segments = self._split_text_semantic(text)
        
        # Combine small segments to reach target chunk size
        position = 0
        current_segment = []
        current_tokens = 0
        
        for segment in segments:
            segment_tokens = count_tokens(segment)
            
            # If single segment is too large, split it
            if segment_tokens > self.options.chunk_size * 1.5:
                if current_segment:
                    # Save current chunk first
                    chunk_text = "\n\n".join(current_segment)
                    chunk_id = generate_chunk_id(chunk_text, source, position)
                    chunks.append(ContextChunk(
                        id=chunk_id,
                        text=chunk_text,
                        type=content_type,
                        source=source,
                        position=position,
                        token_count=current_tokens,
                        metadata=content.get("metadata", {})
                    ))
                    current_segment = []
                    current_tokens = 0
                    position += 1
                
                # Split large segment using fixed size
                large_content = {"id": source, "text": segment, "type": content_type}
                sub_chunks = self._chunk_fixed_size(large_content)
                for sub_chunk in sub_chunks:
                    sub_chunk.position = position
                    chunks.append(sub_chunk)
                    position += 1
                continue
            
            # Add segment to current chunk if it fits
            if current_tokens + segment_tokens <= self.options.chunk_size:
                current_segment.append(segment)
                current_tokens += segment_tokens
            else:
                # Save current chunk and start new one
                if current_segment:
                    chunk_text = "\n\n".join(current_segment)
                    chunk_id = generate_chunk_id(chunk_text, source, position)
                    chunks.append(ContextChunk(
                        id=chunk_id,
                        text=chunk_text,
                        type=content_type,
                        source=source,
                        position=position,
                        token_count=current_tokens,
                        metadata=content.get("metadata", {})
                    ))
                    position += 1
                
                current_segment = [segment]
                current_tokens = segment_tokens
        
        # Add remaining chunk
        if current_segment:
            chunk_text = "\n\n".join(current_segment)
            chunk_id = generate_chunk_id(chunk_text, source, position)
            chunks.append(ContextChunk(
                id=chunk_id,
                text=chunk_text,
                type=content_type,
                source=source,
                position=position,
                token_count=current_tokens,
                metadata=content.get("metadata", {})
            ))
        
        # Update total_chunks for all
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _chunk_sliding_window(self, content: Dict[str, Any]) -> List[ContextChunk]:
        """
        Chunk content with sliding window (overlapping chunks).
        
        Args:
            content: Content to chunk
            
        Returns:
            List of overlapping chunks
        """
        text = content.get("text", "")
        source = content.get("id", "unknown")
        content_type = content.get("type", "other")
        
        words = text.split()
        chunks = []
        position = 0
        
        # Approximate words per chunk (rough estimate: 1 token ≈ 0.75 words)
        words_per_chunk = int(self.options.chunk_size * 0.75)
        overlap_words = int(self.options.overlap * 0.75)
        
        i = 0
        while i < len(words):
            chunk_words = words[i:i + words_per_chunk]
            chunk_text = " ".join(chunk_words)
            chunk_tokens = count_tokens(chunk_text)
            chunk_id = generate_chunk_id(chunk_text, source, position)
            
            chunks.append(ContextChunk(
                id=chunk_id,
                text=chunk_text,
                type=content_type,
                source=source,
                position=position,
                token_count=chunk_tokens,
                metadata=content.get("metadata", {})
            ))
            
            # Move window with overlap
            i += words_per_chunk - overlap_words
            position += 1
            
            # Break if we've consumed all words
            if i >= len(words):
                break
        
        # Update total_chunks for all
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _split_code_semantic(self, code: str) -> List[str]:
        """Split code by functions, classes, and logical blocks."""
        segments = []
        
        # Patterns for code boundaries
        patterns = [
            r'^(def\s+\w+.*?:)',          # Python function
            r'^(class\s+\w+.*?:)',        # Python class
            r'^(function\s+\w+.*?{)',     # JavaScript function
            r'^(const\s+\w+\s*=.*?=>)',   # Arrow function
            r'^(export\s+(?:default\s+)?(?:function|class))',  # ES6 exports
        ]
        
        # Try to split by function/class definitions
        combined_pattern = '|'.join(f'({p})' for p in patterns)
        parts = re.split(combined_pattern, code, flags=re.MULTILINE)
        
        # If no good splits found, split by double newlines
        if len(parts) <= 1:
            segments = [s.strip() for s in code.split('\n\n') if s.strip()]
        else:
            # Combine split parts
            current = []
            for part in parts:
                if part and part.strip():
                    current.append(part)
                    # Check if this looks like a complete block
                    combined = ''.join(current)
                    if self._is_complete_code_block(combined):
                        segments.append(combined.strip())
                        current = []
            
            # Add remaining
            if current:
                segments.append(''.join(current).strip())
        
        return [s for s in segments if s]
    
    def _split_text_semantic(self, text: str) -> List[str]:
        """Split text by paragraphs and sections."""
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Further split very long paragraphs by sentences
        segments = []
        for para in paragraphs:
            if count_tokens(para) > self.options.chunk_size:
                sentences = split_into_sentences(para)
                segments.extend(sentences)
            else:
                segments.append(para)
        
        return segments
    
    def _is_complete_code_block(self, code: str) -> bool:
        """Check if code block looks complete (balanced braces, etc.)."""
        open_braces = code.count('{')
        close_braces = code.count('}')
        open_parens = code.count('(')
        close_parens = code.count(')')
        
        # Simple balance check
        return (open_braces == close_braces and 
                open_parens == close_parens and
                len(code.strip()) > 20)

