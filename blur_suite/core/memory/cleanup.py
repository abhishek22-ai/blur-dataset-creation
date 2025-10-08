"""
Cleanup Manager

Automatic cleanup and garbage collection for memory management.
"""

import gc
import threading
import time
import weakref
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional

from .memory_manager import MemoryManager


class CleanupManager:
    """
    Automatic cleanup manager for memory and resources.

    Provides automatic cleanup of resources, finalizers for objects,
    and background cleanup operations.
    """

    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize cleanup manager.

        Args:
            memory_manager: Parent memory manager instance
        """
        self.memory_manager = memory_manager
        self._finalizers: Dict[int, Callable] = {}
        self._cleanup_callbacks: List[Callable] = []
        self._lock = threading.RLock()

        # Background cleanup
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        self._start_background_cleanup()

        # Statistics
        self.stats = {
            "objects_tracked": 0,
            "objects_cleaned": 0,
            "background_cleanups": 0,
            "manual_cleanups": 0,
        }

    def _start_background_cleanup(self):
        """Start background cleanup thread."""
        if self._cleanup_thread is None:
            self._cleanup_thread = threading.Thread(
                target=self._background_cleanup_worker, daemon=True
            )
            self._cleanup_thread.start()

    def _background_cleanup_worker(self):
        """Background cleanup worker."""
        while not self._stop_cleanup.is_set():
            try:
                # Run cleanup every 30 seconds
                self._stop_cleanup.wait(30)

                if not self._stop_cleanup.is_set():
                    self._perform_background_cleanup()

            except Exception:
                # Continue cleanup even if there's an error
                pass

    def _perform_background_cleanup(self):
        """Perform background cleanup operations."""
        # Trigger garbage collection
        gc.collect()

        # Run cleanup callbacks
        with self._lock:
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception:
                    # Continue with other callbacks
                    pass

        self.stats["background_cleanups"] += 1

    def add_cleanup_callback(self, callback: Callable):
        """
        Add a cleanup callback.

        Args:
            callback: Function to call during cleanup
        """
        with self._lock:
            self._cleanup_callbacks.append(callback)

    def remove_cleanup_callback(self, callback: Callable):
        """
        Remove a cleanup callback.

        Args:
            callback: The callback function to remove
        """
        with self._lock:
            if callback in self._cleanup_callbacks:
                self._cleanup_callbacks.remove(callback)

    def add_finalizer(self, obj: Any, finalizer: Callable):
        """
        Add a finalizer for an object.

        Args:
            obj: Object to track
            finalizer: Function to call when object is destroyed
        """

        # Create a weak reference to avoid circular references
        def cleanup(ref):
            try:
                finalizer()
                self.stats["objects_cleaned"] += 1
            except Exception:
                pass

        # Store finalizer with object id
        obj_id = id(obj)
        with self._lock:
            self._finalizers[obj_id] = finalizer
            self.stats["objects_tracked"] += 1

        # Create weak reference with callback
        weakref.ref(obj, cleanup)

    def remove_finalizer(self, obj: Any):
        """
        Remove a finalizer for an object.

        Args:
            obj: Object to remove finalizer for
        """
        obj_id = id(obj)
        with self._lock:
            self._finalizers.pop(obj_id, None)

    def force_cleanup(self):
        """Force immediate cleanup."""
        # Trigger garbage collection
        gc.collect()

        # Run all cleanup callbacks
        with self._lock:
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception:
                    pass

        # Clear finalizers for collected objects
        self._cleanup_finalizers()

        self.stats["manual_cleanups"] += 1

    def _cleanup_finalizers(self):
        """Clean up finalizers for collected objects."""
        # Force garbage collection to identify dead objects
        gc.collect()

        # This is a simplified approach - in practice you might
        # want to track which objects are still alive
        with self._lock:
            # Clear all finalizers (they'll be re-added if objects are still alive)
            self._finalizers.clear()

    @contextmanager
    def auto_cleanup(self, obj: Any, cleanup_func: Optional[Callable] = None):
        """
        Context manager that automatically cleans up objects.

        Args:
            obj: Object to track for cleanup
            cleanup_func: Optional cleanup function

        Yields:
            The tracked object
        """
        if cleanup_func:
            self.add_finalizer(obj, cleanup_func)

        try:
            yield obj
        finally:
            if cleanup_func:
                try:
                    cleanup_func()
                except Exception:
                    pass

    def schedule_cleanup(self, delay: float, cleanup_func: Callable):
        """
        Schedule a cleanup function to run after a delay.

        Args:
            delay: Delay in seconds
            cleanup_func: Function to run
        """

        def delayed_cleanup():
            time.sleep(delay)
            try:
                cleanup_func()
            except Exception:
                pass

        thread = threading.Thread(target=delayed_cleanup, daemon=True)
        thread.start()

    def get_cleanup_info(self) -> Dict[str, Any]:
        """Get cleanup manager information."""
        with self._lock:
            return {
                "objects_tracked": self.stats["objects_tracked"],
                "objects_cleaned": self.stats["objects_cleaned"],
                "background_cleanups": self.stats["background_cleanups"],
                "manual_cleanups": self.stats["manual_cleanups"],
                "cleanup_callbacks": len(self._cleanup_callbacks),
                "active_finalizers": len(self._finalizers),
            }

    def optimize_memory(self):
        """Perform memory optimization."""
        # Force garbage collection with aggressive settings
        gc.collect()

        # Set aggressive GC thresholds temporarily
        original_thresholds = gc.get_threshold()
        try:
            gc.set_threshold(100, 10, 10)  # Very aggressive
            gc.collect()
        finally:
            # Restore original thresholds
            gc.set_threshold(*original_thresholds)

        # Run cleanup callbacks
        self.force_cleanup()

    def shutdown(self):
        """Shutdown cleanup manager."""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5.0)

        # Final cleanup
        self.force_cleanup()


class ResourceTracker:
    """
    Track resources and ensure proper cleanup.
    """

    def __init__(self, cleanup_manager: CleanupManager):
        """
        Initialize resource tracker.

        Args:
            cleanup_manager: Parent cleanup manager
        """
        self.cleanup_manager = cleanup_manager
        self._resources: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def add_resource(
        self, name: str, resource: Any, cleanup_func: Optional[Callable] = None
    ):
        """
        Add a resource to track.

        Args:
            name: Resource name
            resource: Resource object
            cleanup_func: Optional cleanup function
        """
        with self._lock:
            self._resources[name] = {
                "resource": resource,
                "cleanup_func": cleanup_func,
                "added_at": time.time(),
            }

        if cleanup_func:
            self.cleanup_manager.add_finalizer(resource, cleanup_func)

    def remove_resource(self, name: str):
        """
        Remove a tracked resource.

        Args:
            name: Resource name
        """
        with self._lock:
            self._resources.pop(name, None)

    def cleanup_resource(self, name: str):
        """
        Manually cleanup a specific resource.

        Args:
            name: Resource name
        """
        with self._lock:
            if name in self._resources:
                resource_info = self._resources[name]
                if resource_info["cleanup_func"]:
                    try:
                        resource_info["cleanup_func"]()
                    except Exception:
                        pass
                del self._resources[name]

    def cleanup_all_resources(self):
        """Cleanup all tracked resources."""
        with self._lock:
            for name, resource_info in list(self._resources.items()):
                if resource_info["cleanup_func"]:
                    try:
                        resource_info["cleanup_func"]()
                    except Exception:
                        pass

            self._resources.clear()

    def get_tracked_resources(self) -> List[str]:
        """Get list of tracked resource names."""
        with self._lock:
            return list(self._resources.keys())


# Import time here to avoid circular imports
