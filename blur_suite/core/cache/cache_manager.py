"""
Cache Manager

Central cache management system for the Blur Suite SDK.
Coordinates all caching operations and provides intelligent cache strategies.
"""

import hashlib
import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from .blur_cache import BlurCache
from .config_cache import ConfigCache
from .image_cache import ImageCache


class CacheStrategy(Enum):
    """Cache eviction strategies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    SIZE = "size"  # Size-based eviction


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int
    size_bytes: int
    ttl: Optional[float] = None


class CacheManager:
    """
    Central cache manager for the Blur Suite SDK.

    Provides intelligent caching with multiple strategies and
    automatic cache management for optimal performance.
    """

    def __init__(
        self,
        max_memory_mb: float = 100.0,
        default_ttl: Optional[float] = None,
        strategy: CacheStrategy = CacheStrategy.LRU,
        enable_metrics: bool = True,
    ):
        """
        Initialize the cache manager.

        Args:
            max_memory_mb: Maximum memory usage in MB
            default_ttl: Default time-to-live for cache entries in seconds
            strategy: Cache eviction strategy
            enable_metrics: Whether to collect cache metrics
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.enable_metrics = enable_metrics

        # Cache storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Specialized caches
        self.image_cache = ImageCache(self)
        self.blur_cache = BlurCache(self)
        self.config_cache = ConfigCache(self)

        # Metrics
        self.metrics = CacheMetrics() if enable_metrics else None

        # Background cleanup thread
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start background cleanup thread for TTL entries."""
        if self._cleanup_thread is None:
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_worker, daemon=True
            )
            self._cleanup_thread.start()

    def _cleanup_worker(self):
        """Background worker for cleaning up expired entries."""
        while not self._stop_cleanup.is_set():
            try:
                self._cleanup_expired()
                self._stop_cleanup.wait(60)  # Check every minute
            except Exception:
                # Continue cleanup even if there's an error
                self._stop_cleanup.wait(60)

    def _cleanup_expired(self):
        """Remove expired TTL entries."""
        current_time = time.time()
        expired_keys = []

        with self._lock:
            for key, entry in self._cache.items():
                if entry.ttl and (entry.created_at + entry.ttl) < current_time:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        # Create a normalized representation of the arguments
        key_data = {"args": args, "kwargs": kwargs}

        # Convert to JSON string and hash
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _get_cache_size(self) -> int:
        """Get current cache size in bytes."""
        return sum(entry.size_bytes for entry in self._cache.values())

    def _evict_entries(self, target_bytes: int):
        """Evict entries based on the configured strategy."""
        if self.strategy == CacheStrategy.LRU:
            self._evict_lru(target_bytes)
        elif self.strategy == CacheStrategy.LFU:
            self._evict_lfu(target_bytes)
        elif self.strategy == CacheStrategy.SIZE:
            self._evict_by_size(target_bytes)

    def _evict_lru(self, target_bytes: int):
        """Evict least recently used entries."""
        current_size = self._get_cache_size()
        while current_size > target_bytes and self._cache:
            # Remove oldest entry (LRU)
            key, entry = self._cache.popitem(last=False)
            current_size -= entry.size_bytes

    def _evict_lfu(self, target_bytes: int):
        """Evict least frequently used entries."""
        # Sort by access count, then by access time
        entries = sorted(
            self._cache.items(), key=lambda x: (x[1].access_count, x[1].accessed_at)
        )

        current_size = self._get_cache_size()
        for key, entry in entries:
            if current_size <= target_bytes:
                break
            del self._cache[key]
            current_size -= entry.size_bytes

    def _evict_by_size(self, target_bytes: int):
        """Evict largest entries first."""
        # Sort by size (largest first)
        entries = sorted(
            self._cache.items(), key=lambda x: x[1].size_bytes, reverse=True
        )

        current_size = self._get_cache_size()
        for key, entry in entries:
            if current_size <= target_bytes:
                break
            del self._cache[key]
            current_size -= entry.size_bytes

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                if self.metrics:
                    self.metrics.misses += 1
                return None

            # Check TTL
            if entry.ttl and (entry.created_at + entry.ttl) < time.time():
                del self._cache[key]
                if self.metrics:
                    self.metrics.misses += 1
                return None

            # Update access metadata
            entry.accessed_at = time.time()
            entry.access_count += 1

            if self.metrics:
                self.metrics.hits += 1

            return entry.value

    def put(
        self,
        key: str,
        value: Any,
        size_bytes: Optional[int] = None,
        ttl: Optional[float] = None,
    ):
        """
        Store a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            size_bytes: Size of value in bytes (estimated if None)
            ttl: Time-to-live in seconds
        """
        if size_bytes is None:
            size_bytes = self._estimate_size(value)

        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            accessed_at=time.time(),
            access_count=1,
            size_bytes=size_bytes,
            ttl=ttl or self.default_ttl,
        )

        with self._lock:
            # Check if we need to evict entries
            current_size = self._get_cache_size()
            if current_size + size_bytes > self.max_memory_bytes:
                self._evict_entries(self.max_memory_bytes - size_bytes)

            # Remove existing entry if present
            if key in self._cache:
                current_size -= self._cache[key].size_bytes
                del self._cache[key]

            # Add new entry
            self._cache[key] = entry

            if self.metrics:
                self.metrics.entries = len(self._cache)
                self.metrics.total_size = current_size + size_bytes

    def cached_compute(
        self,
        compute_func,
        *args,
        cache_key: Optional[str] = None,
        ttl: Optional[float] = None,
        **kwargs,
    ):
        """
        Compute a value with caching.

        Args:
            compute_func: Function to compute the value
            *args: Arguments for the function
            cache_key: Custom cache key (auto-generated if None)
            ttl: Cache TTL in seconds
            **kwargs: Keyword arguments for the function

        Returns:
            Computed or cached result
        """
        if cache_key is None:
            cache_key = self._generate_key(*args, **kwargs)

        # Try to get from cache first
        cached_result = self.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Compute the value
        result = compute_func(*args, **kwargs)

        # Cache the result
        self.put(cache_key, result, ttl=ttl)

        return result

    def _estimate_size(self, obj: Any) -> int:
        """Estimate the size of an object in bytes."""
        try:
            import sys

            return sys.getsizeof(obj)
        except Exception:
            # Fallback estimation
            return 1024  # 1KB default

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            if self.metrics:
                self.metrics.entries = 0
                self.metrics.total_size = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            current_size = self._get_cache_size()

            return {
                "entries": len(self._cache),
                "memory_used_bytes": current_size,
                "memory_used_mb": current_size / (1024 * 1024),
                "memory_limit_mb": self.max_memory_bytes / (1024 * 1024),
                "strategy": self.strategy.value,
                "hit_rate": self.metrics.hit_rate if self.metrics else 0.0,
                "total_hits": self.metrics.hits if self.metrics else 0,
                "total_misses": self.metrics.misses if self.metrics else 0,
            }

    def shutdown(self):
        """Shutdown the cache manager and cleanup resources."""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5.0)


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hits: int = 0
    misses: int = 0
    entries: int = 0
    total_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0
