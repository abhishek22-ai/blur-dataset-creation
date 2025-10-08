"""
Buffer Manager

Memory buffer management for efficient I/O and processing operations.
"""

import gc
import mmap
import os
import tempfile
import threading
from collections import deque
from typing import Any, Dict, List

import numpy as np

from .memory_manager import MemoryManager


class BufferManager:
    """
    Memory buffer manager for efficient I/O operations.

    Manages memory-mapped files, temporary buffers, and
    streaming operations for large datasets.
    """

    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize buffer manager.

        Args:
            memory_manager: Parent memory manager instance
        """
        self.memory_manager = memory_manager
        self._buffers: Dict[str, Any] = {}
        self._lock = threading.RLock()

        # Buffer pools
        self._buffer_pools: Dict[int, deque] = {}

        # Memory-mapped files
        self._mmap_files: List[mmap.mmap] = []

        # Configuration
        self.default_buffer_size = 8192  # 8KB
        self.max_buffer_size = 1024 * 1024 * 100  # 100MB
        self.max_pool_size = 50

        # Statistics
        self.stats = {
            "buffers_created": 0,
            "buffers_reused": 0,
            "mmap_files_created": 0,
            "memory_saved_mb": 0.0,
        }

    def get_buffer(self, size: int) -> np.ndarray:
        """
        Get a buffer of specified size.

        Args:
            size: Buffer size in bytes

        Returns:
            Buffer array
        """
        # Round up to nearest page size for efficiency
        page_size = 4096
        size = ((size + page_size - 1) // page_size) * page_size

        pool_key = size

        with self._lock:
            # Try to get from pool
            if pool_key in self._buffer_pools and self._buffer_pools[pool_key]:
                buffer = self._buffer_pools[pool_key].popleft()
                self.stats["buffers_reused"] += 1
                return buffer

            # Pool miss - create new buffer
            self.stats["buffers_created"] += 1

        # Create new buffer outside lock
        return np.zeros(size, dtype=np.uint8)

    def return_buffer(self, buffer: np.ndarray):
        """
        Return a buffer to the pool.

        Args:
            buffer: Buffer to return
        """
        if buffer is None:
            return

        size = buffer.nbytes
        pool_key = size

        with self._lock:
            # Initialize pool if needed
            if pool_key not in self._buffer_pools:
                self._buffer_pools[pool_key] = deque()

            pool = self._buffer_pools[pool_key]

            # Add to pool if not full
            if len(pool) < self.max_pool_size:
                # Clear buffer
                buffer.fill(0)
                pool.append(buffer)
            else:
                # Pool is full, let it be garbage collected
                pass

    def create_memory_mapped_buffer(self, size: int) -> mmap.mmap:
        """
        Create a memory-mapped buffer for large data.

        Args:
            size: Buffer size in bytes

        Returns:
            Memory-mapped buffer
        """
        # Create temporary file
        temp_fd = tempfile.NamedTemporaryFile(delete=False)
        temp_fd.close()

        try:
            # Create memory-mapped file
            with open(temp_fd.name, "w+b") as f:
                f.truncate(size)
                mmap_buffer = mmap.mmap(f.fileno(), size)

            # Track the mmap file
            with self._lock:
                self._mmap_files.append(mmap_buffer)
                self.stats["mmap_files_created"] += 1

            return mmap_buffer

        except Exception:
            # Clean up temp file if mmap failed
            try:
                os.unlink(temp_fd.name)
            except Exception:
                pass
            raise

    def create_temp_file_buffer(self, size: int) -> str:
        """
        Create a temporary file buffer for very large data.

        Args:
            size: Buffer size in bytes

        Returns:
            Path to temporary file
        """
        temp_fd = tempfile.NamedTemporaryFile(delete=False)
        temp_fd.truncate(size)
        temp_fd.close()

        return temp_fd.name

    def cleanup_mmap_files(self):
        """Clean up all memory-mapped files."""
        with self._lock:
            for mmap_file in self._mmap_files:
                try:
                    mmap_file.close()
                except Exception:
                    pass
            self._mmap_files.clear()

    def get_streaming_buffer(self, chunk_size: int = 8192) -> np.ndarray:
        """
        Get a buffer for streaming operations.

        Args:
            chunk_size: Size of each chunk

        Returns:
            Streaming buffer
        """
        return self.get_buffer(chunk_size)

    def return_streaming_buffer(self, buffer: np.ndarray):
        """
        Return a streaming buffer.

        Args:
            buffer: Streaming buffer to return
        """
        self.return_buffer(buffer)

    @property
    def total_mmap_size(self) -> int:
        """Get total size of memory-mapped files."""
        total_size = 0
        with self._lock:
            for mmap_file in self._mmap_files:
                try:
                    total_size += mmap_file.size()
                except Exception:
                    pass
        return total_size

    def get_memory_usage(self) -> int:
        """Get total memory usage in bytes."""
        usage = 0

        # Buffer pools memory
        with self._lock:
            for pool in self._buffer_pools.values():
                for buffer in pool:
                    usage += buffer.nbytes

        # Memory-mapped files
        usage += self.total_mmap_size

        return usage

    def get_buffer_info(self) -> Dict[str, Any]:
        """Get buffer manager information."""
        with self._lock:
            pool_info = {}
            for size, pool in self._buffer_pools.items():
                pool_info[size] = len(pool)

            return {
                "pools": pool_info,
                "total_pools": len(self._buffer_pools),
                "total_buffers": sum(len(pool) for pool in self._buffer_pools.values()),
                "mmap_files": len(self._mmap_files),
                "mmap_total_size": self.total_mmap_size,
                "memory_usage_bytes": self.get_memory_usage(),
                "memory_usage_mb": self.get_memory_usage() / (1024 * 1024),
                "stats": self.stats.copy(),
            }

    def optimize(self):
        """Optimize buffer usage."""
        with self._lock:
            # Clear half of buffers from each pool to free memory
            for pool in self._buffer_pools.values():
                target_size = max(len(pool) // 2, 5)  # Keep at least 5 buffers
                while len(pool) > target_size:
                    pool.popleft()

        # Clean up memory-mapped files that are no longer needed
        self.cleanup_mmap_files()

        # Force garbage collection
        gc.collect()

    def clear_all_buffers(self):
        """Clear all buffer pools."""
        with self._lock:
            total_buffers = sum(len(pool) for pool in self._buffer_pools.values())
            self._buffer_pools.clear()
            self.stats["buffers_created"] -= total_buffers

    def preload_common_buffers(self):
        """Preload common buffer sizes."""
        common_sizes = [
            4096,  # 4KB
            8192,  # 8KB
            16384,  # 16KB
            32768,  # 32KB
            65536,  # 64KB
            131072,  # 128KB
            262144,  # 256KB
        ]

        for size in common_sizes:
            # Pre-create a few buffers of each size
            for _ in range(3):
                buffer = self.get_buffer(size)
                self.return_buffer(buffer)


class StreamingBuffer:
    """
    Buffer for streaming large files or data.
    """

    def __init__(self, buffer_manager: BufferManager, chunk_size: int = 8192):
        """
        Initialize streaming buffer.

        Args:
            buffer_manager: Parent buffer manager
            chunk_size: Size of each chunk
        """
        self.buffer_manager = buffer_manager
        self.chunk_size = chunk_size
        self._current_buffer = None

    def __enter__(self):
        """Enter context manager."""
        self._current_buffer = self.buffer_manager.get_streaming_buffer(self.chunk_size)
        return self._current_buffer

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self._current_buffer is not None:
            self.buffer_manager.return_streaming_buffer(self._current_buffer)
            self._current_buffer = None
