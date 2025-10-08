"""
Image Pool

Object pooling for image arrays to reduce memory allocation overhead.
"""

import gc
import threading
from collections import deque
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .memory_manager import MemoryManager


class ImagePool:
    """
    Object pool for image arrays.

    Manages a pool of pre-allocated image arrays to reduce
    memory allocation overhead and improve performance.
    """

    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize image pool.

        Args:
            memory_manager: Parent memory manager instance
        """
        self.memory_manager = memory_manager
        self._pools: Dict[Tuple[int, ...], deque] = {}
        self._lock = threading.RLock()

        # Pool configuration
        self.max_pool_size = 100
        self.min_pool_size = 10
        self.pool_timeout = 300  # 5 minutes

        # Statistics
        self.stats = {"hits": 0, "misses": 0, "created": 0, "destroyed": 0}

    def _get_pool_key(self, shape: Tuple[int, ...], dtype: np.dtype) -> Tuple:
        """Generate pool key from shape and dtype."""
        return (shape, dtype.str)

    def get_image(
        self, shape: Tuple[int, ...], dtype: np.dtype = np.uint8
    ) -> np.ndarray:
        """
        Get an image array from the pool or create a new one.

        Args:
            shape: Image shape (height, width, channels)
            dtype: Image data type

        Returns:
            Image array
        """
        pool_key = self._get_pool_key(shape, dtype)

        with self._lock:
            # Try to get from pool
            if pool_key in self._pools and self._pools[pool_key]:
                image = self._pools[pool_key].popleft()
                self.stats["hits"] += 1
                return image

            # Pool miss - create new image
            self.stats["misses"] += 1
            self.stats["created"] += 1

            # Check if we need to cleanup before creating new image
            if self.get_memory_usage() > 100 * 1024 * 1024:  # 100MB
                self._cleanup_pools()

        # Create new image outside lock to avoid blocking
        return np.zeros(shape, dtype=dtype)

    def return_image(self, image: np.ndarray):
        """
        Return an image array to the pool.

        Args:
            image: Image array to return
        """
        if image is None:
            return

        shape = image.shape
        dtype = image.dtype
        pool_key = self._get_pool_key(shape, dtype)

        with self._lock:
            # Initialize pool if needed
            if pool_key not in self._pools:
                self._pools[pool_key] = deque()

            # Add to pool if not full
            pool = self._pools[pool_key]
            if len(pool) < self.max_pool_size:
                # Clear the image data to free memory
                image.fill(0)
                pool.append(image)
            else:
                self.stats["destroyed"] += 1

    def create_image_pool(
        self, shape: Tuple[int, ...], dtype: np.dtype = np.uint8, count: int = 10
    ):
        """
        Pre-create a pool of images.

        Args:
            shape: Image shape
            dtype: Image data type
            count: Number of images to pre-create
        """
        pool_key = self._get_pool_key(shape, dtype)

        with self._lock:
            if pool_key not in self._pools:
                self._pools[pool_key] = deque()

            pool = self._pools[pool_key]

            # Create images up to max pool size
            while len(pool) < min(count, self.max_pool_size):
                image = np.zeros(shape, dtype=dtype)
                pool.append(image)
                self.stats["created"] += 1

    def _cleanup_pools(self):
        """Clean up old pools to free memory."""
        time.time()

        with self._lock:
            # Remove half of the images from each pool
            for pool in self._pools.values():
                target_size = max(len(pool) // 2, self.min_pool_size)
                while len(pool) > target_size:
                    pool.popleft()
                    self.stats["destroyed"] += 1

    def clear_pool(
        self, shape: Optional[Tuple[int, ...]] = None, dtype: Optional[np.dtype] = None
    ):
        """
        Clear image pools.

        Args:
            shape: Specific shape to clear, or None for all
            dtype: Specific dtype to clear, or None for all
        """
        with self._lock:
            if shape is not None and dtype is not None:
                # Clear specific pool
                pool_key = self._get_pool_key(shape, dtype)
                if pool_key in self._pools:
                    pool_size = len(self._pools[pool_key])
                    self._pools[pool_key].clear()
                    self.stats["destroyed"] += pool_size
            else:
                # Clear all pools
                total_destroyed = sum(len(pool) for pool in self._pools.values())
                self._pools.clear()
                self.stats["destroyed"] += total_destroyed

    def get_pool_info(self) -> Dict[str, Any]:
        """Get pool information and statistics."""
        with self._lock:
            pool_info = {}
            for (shape, dtype_str), pool in self._pools.items():
                pool_info[f"{shape}_{dtype_str}"] = {
                    "count": len(pool),
                    "shape": shape,
                    "dtype": dtype_str,
                }

            return {
                "pools": pool_info,
                "total_pools": len(self._pools),
                "total_images": sum(len(pool) for pool in self._pools.values()),
                "stats": self.stats.copy(),
                "memory_usage_mb": self.get_memory_usage() / (1024 * 1024),
            }

    def get_memory_usage(self) -> int:
        """Get memory usage of all pools in bytes."""
        total_bytes = 0

        with self._lock:
            for pool in self._pools.values():
                for image in pool:
                    total_bytes += image.nbytes

        return total_bytes

    def optimize(self):
        """Optimize pool usage based on statistics."""
        with self._lock:
            # Remove pools that haven't been used recently
            # This is a simplified optimization - in practice you might
            # track access patterns and remove less-used pools

            # For now, just trigger garbage collection
            gc.collect()

    def preload_common_sizes(self):
        """Preload pools for common image sizes."""
        common_sizes = [
            ((256, 256, 3), np.uint8),
            ((512, 512, 3), np.uint8),
            ((1024, 1024, 3), np.uint8),
            ((256, 256), np.uint8),
            ((512, 512), np.uint8),
            ((224, 224, 3), np.float32),  # Common for ML models
            ((416, 416, 3), np.float32),  # Common for ML models
        ]

        for shape, dtype in common_sizes:
            self.create_image_pool(shape, dtype, count=5)


# Import time here to avoid circular imports
import time
