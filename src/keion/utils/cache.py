"""Cache management utilities for the music bot."""

import time
from functools import lru_cache
from typing import Any


# LRU cache for frequently accessed data
@lru_cache(maxsize=100)
def cache_song_info(url: str) -> dict:
    """Cache song metadata to reduce API calls."""
    # ... implementation
    pass


# Time-based cache for temporary data
class TimeCache:
    def __init__(self, ttl: int = 300):  # 5 minutes default TTL
        self._cache = {}
        self._ttl = ttl

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return data
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = (value, time.time())


class SongCache:
    """LRU cache implementation for song information."""

    def __init__(self, max_size: int = 50, ttl: int = 3600):
        """Initialize the song cache.

        Args:
            max_size: Maximum number of songs to cache
            ttl: Time-to-live in seconds for cache entries
        """
        self._cache: dict[str, dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl

    def get(self, url: str) -> dict | None:
        """Retrieve a song from cache if it exists and is valid."""
        if url in self._cache:
            entry = self._cache[url]
            if time.time() - entry["last_accessed"] <= self.ttl:
                entry["last_accessed"] = time.time()
                entry["play_count"] += 1
                return entry["info"]
        return None

    def add(self, url: str, info: dict) -> None:
        """Add a song to the cache with LRU implementation."""
        now = time.time()

        # Clear expired entries
        expired = [
            u
            for u, data in self._cache.items()
            if now - data["last_accessed"] > self.ttl
        ]
        for u in expired:
            del self._cache[u]

        # Remove least played if still full
        if len(self._cache) >= self.max_size:
            least_played = min(self._cache.items(), key=lambda x: x[1]["play_count"])[0]
            del self._cache[least_played]

        self._cache[url] = {"info": info, "last_accessed": now, "play_count": 0}
