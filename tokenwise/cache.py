"""Caching layer for TokenWise."""

from typing import Any, Optional
import json
import hashlib
from datetime import datetime, timedelta


class CacheService:
    """Simple in-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache service.

        Args:
            default_ttl: Default time-to-live in seconds
        """
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None

        value, expiry = self._cache[key]

        # Check if expired
        if datetime.now() > expiry:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)

    def delete(self, key: str):
        """
        Delete key from cache.

        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()

    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def cleanup_expired(self):
        """Remove expired entries from cache."""
        now = datetime.now()
        expired_keys = [key for key, (_, expiry) in self._cache.items() if now > expiry]
        for key in expired_keys:
            del self._cache[key]


# Global cache instance
_cache_instance = None


def get_cache() -> CacheService:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
