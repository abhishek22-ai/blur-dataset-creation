"""
Memory Manager

Central memory management system for monitoring and controlling
memory usage across the Blur Suite SDK.
"""

import gc
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import psutil

from .buffer_manager import BufferManager
from .image_pool import ImagePool


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    process_memory_mb: float
    memory_percent: float
    cache_memory_mb: float = 0.0
    pool_memory_mb: float = 0.0


@dataclass
class MemoryAlert:
    """Memory alert configuration."""

    threshold_mb: float
    callback: Callable[[MemoryStats], None]
    enabled: bool = True


class MemoryManager:
    """
    Central memory manager for the Blur Suite SDK.

    Monitors memory usage, manages memory pools, and provides
    automatic cleanup and optimization features.
    """

    def __init__(
        self,
        max_memory_percent: float = 80.0,
        check_interval: float = 5.0,
        enable_alerts: bool = True,
        enable_auto_cleanup: bool = True,
    ):
        """
        Initialize memory manager.

        Args:
            max_memory_percent: Maximum memory usage percentage before alerts
            check_interval: Memory check interval in seconds
            enable_alerts: Whether to enable memory alerts
            enable_auto_cleanup: Whether to enable automatic cleanup
        """
        self.max_memory_percent = max_memory_percent
        self.check_interval = check_interval
        self.enable_alerts = enable_alerts
        self.enable_auto_cleanup = enable_auto_cleanup

        # Memory pools and managers
        self.image_pool = ImagePool(self)
        self.buffer_manager = BufferManager(self)

        # Monitoring
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        self._lock = threading.RLock()

        # Alerts
        self.alerts: List[MemoryAlert] = []
        self.alert_history: List[Dict[str, Any]] = []

        # Statistics
        self.stats_history: List[MemoryStats] = []
        self.max_history_size = 1000

        # Callbacks
        self.cleanup_callbacks: List[Callable] = []

        # Start monitoring
        self._start_monitoring()

    def _start_monitoring(self):
        """Start memory monitoring thread."""
        if self._monitoring_thread is None:
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_worker, daemon=True
            )
            self._monitoring_thread.start()

    def _monitoring_worker(self):
        """Background memory monitoring worker."""
        while not self._stop_monitoring.is_set():
            try:
                self._check_memory_usage()
                self._stop_monitoring.wait(self.check_interval)
            except Exception:
                # Continue monitoring even if there's an error
                self._stop_monitoring.wait(self.check_interval)

    def _check_memory_usage(self):
        """Check current memory usage and trigger alerts if needed."""
        stats = self.get_memory_stats()

        # Store stats
        with self._lock:
            self.stats_history.append(stats)
            if len(self.stats_history) > self.max_history_size:
                self.stats_history.pop(0)

        # Check alerts
        if self.enable_alerts:
            self._check_alerts(stats)

        # Auto cleanup if enabled
        if self.enable_auto_cleanup:
            self._auto_cleanup(stats)

    def _check_alerts(self, stats: MemoryStats):
        """Check and trigger memory alerts."""
        for alert in self.alerts:
            if not alert.enabled:
                continue

            if stats.used_memory_mb >= alert.threshold_mb:
                try:
                    alert.callback(stats)

                    # Record alert
                    with self._lock:
                        self.alert_history.append(
                            {
                                "timestamp": time.time(),
                                "stats": stats,
                                "threshold_mb": alert.threshold_mb,
                            }
                        )

                        # Keep only recent alerts
                        if len(self.alert_history) > 100:
                            self.alert_history.pop(0)

                except Exception as e:
                    # Log error but continue with other alerts
                    print(f"Error in memory alert callback: {e}")

    def _auto_cleanup(self, stats: MemoryStats):
        """Perform automatic cleanup if memory usage is high."""
        if stats.memory_percent >= self.max_memory_percent:
            self.trigger_cleanup()

    def get_memory_stats(self) -> MemoryStats:
        """
        Get current memory statistics.

        Returns:
            Current memory usage statistics
        """
        # System memory
        memory = psutil.virtual_memory()
        total_memory_mb = memory.total / (1024 * 1024)
        available_memory_mb = memory.available / (1024 * 1024)
        used_memory_mb = memory.used / (1024 * 1024)
        memory_percent = memory.percent

        # Process memory
        process = psutil.Process()
        process_memory_mb = process.memory_info().rss / (1024 * 1024)

        # Component memory usage
        cache_memory_mb = self._get_cache_memory_usage()
        pool_memory_mb = self._get_pool_memory_usage()

        return MemoryStats(
            total_memory_mb=total_memory_mb,
            available_memory_mb=available_memory_mb,
            used_memory_mb=used_memory_mb,
            process_memory_mb=process_memory_mb,
            memory_percent=memory_percent,
            cache_memory_mb=cache_memory_mb,
            pool_memory_mb=pool_memory_mb,
        )

    def _get_cache_memory_usage(self) -> float:
        """Get memory usage from cache manager."""
        try:
            # Import here to avoid circular imports
            from ..cache.cache_manager import CacheManager

            if hasattr(CacheManager, "_instances"):
                total_size = sum(cm._get_cache_size() for cm in CacheManager._instances)
                return total_size / (1024 * 1024)
        except Exception:
            pass
        return 0.0

    def _get_pool_memory_usage(self) -> float:
        """Get memory usage from memory pools."""
        total_size = 0

        # Image pool memory
        total_size += self.image_pool.get_memory_usage()

        # Buffer manager memory
        total_size += self.buffer_manager.get_memory_usage()

        return total_size / (1024 * 1024)

    def add_alert(self, threshold_mb: float, callback: Callable[[MemoryStats], None]):
        """
        Add a memory alert.

        Args:
            threshold_mb: Memory threshold in MB
            callback: Function to call when threshold is exceeded
        """
        alert = MemoryAlert(threshold_mb=threshold_mb, callback=callback)
        self.alerts.append(alert)

    def remove_alert(self, callback: Callable[[MemoryStats], None]):
        """
        Remove a memory alert.

        Args:
            callback: The callback function to remove
        """
        self.alerts = [alert for alert in self.alerts if alert.callback != callback]

    def add_cleanup_callback(self, callback: Callable):
        """
        Add a cleanup callback.

        Args:
            callback: Function to call during cleanup
        """
        self.cleanup_callbacks.append(callback)

    def trigger_cleanup(self):
        """Manually trigger cleanup operations."""
        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in cleanup callback: {e}")

        # Trigger garbage collection
        gc.collect()

        # Clear cache if memory usage is high
        if self.get_memory_stats().memory_percent >= self.max_memory_percent:
            self._clear_caches()

    def _clear_caches(self):
        """Clear cache managers to free memory."""
        try:

            # This would need to be implemented to clear all cache instances
            # For now, we'll just trigger GC
            gc.collect()
        except Exception:
            pass

    def force_garbage_collection(self):
        """Force garbage collection."""
        gc.collect()
        if hasattr(gc, "set_threshold"):
            # Reset GC thresholds to be more aggressive
            gc.set_threshold(700, 10, 10)

    @contextmanager
    def memory_context(self, max_memory_mb: Optional[float] = None):
        """
        Context manager for memory-constrained operations.

        Args:
            max_memory_mb: Maximum memory to use for the operation

        Yields:
            Memory manager instance
        """
        initial_stats = self.get_memory_stats()

        try:
            yield self
        finally:
            # Cleanup after operation
            final_stats = self.get_memory_stats()

            # If memory usage increased significantly, trigger cleanup
            memory_increase = final_stats.used_memory_mb - initial_stats.used_memory_mb
            if max_memory_mb and memory_increase > max_memory_mb:
                self.trigger_cleanup()

    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory report."""
        stats = self.get_memory_stats()

        return {
            "current_stats": {
                "total_memory_mb": stats.total_memory_mb,
                "available_memory_mb": stats.available_memory_mb,
                "used_memory_mb": stats.used_memory_mb,
                "process_memory_mb": stats.process_memory_mb,
                "memory_percent": stats.memory_percent,
                "cache_memory_mb": stats.cache_memory_mb,
                "pool_memory_mb": stats.pool_memory_mb,
            },
            "alerts": [
                {"threshold_mb": alert.threshold_mb, "enabled": alert.enabled}
                for alert in self.alerts
            ],
            "recent_alerts": len(self.alert_history),
            "history_size": len(self.stats_history),
            "pools": {
                "image_pool": self.image_pool.get_pool_info(),
                "buffer_manager": self.buffer_manager.get_buffer_info(),
            },
        }

    def optimize_memory_usage(self):
        """Perform memory optimization."""
        # Force garbage collection
        self.force_garbage_collection()

        # Optimize pools
        self.image_pool.optimize()
        self.buffer_manager.optimize()

        # Clear old stats
        with self._lock:
            if len(self.stats_history) > self.max_history_size // 2:
                self.stats_history = self.stats_history[-self.max_history_size // 2 :]

    def shutdown(self):
        """Shutdown memory manager and cleanup resources."""
        self._stop_monitoring.set()
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)

        # Final cleanup
        self.trigger_cleanup()
