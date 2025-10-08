"""
Worker Pool

Reusable pool of worker threads/processes for parallel operations.
"""

import multiprocessing
import queue
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from ..memory.memory_manager import MemoryManager


@dataclass
class WorkerTask:
    """Task for worker pool."""

    task_id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: int = 0
    timeout: Optional[float] = None


@dataclass
class TaskResult:
    """Result of worker task."""

    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0


class WorkerPool:
    """
    Reusable worker pool for parallel operations.

    Manages a pool of workers and provides task queuing,
    prioritization, and result collection.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        max_workers: Optional[int] = None,
        use_multiprocessing: bool = False,
        task_queue_size: int = 1000,
    ):
        """
        Initialize worker pool.

        Args:
            memory_manager: Memory manager instance
            max_workers: Maximum number of workers
            use_multiprocessing: Whether to use multiprocessing
            task_queue_size: Maximum size of task queue
        """
        self.memory_manager = memory_manager
        self.use_multiprocessing = use_multiprocessing
        self.task_queue_size = task_queue_size

        # Determine worker count
        if max_workers is None:
            self.max_workers = min(multiprocessing.cpu_count(), 8)
        else:
            self.max_workers = max_workers

        # Task management
        self._task_queue = queue.PriorityQueue(maxsize=task_queue_size)
        self._results: Dict[str, TaskResult] = {}
        self._results_lock = threading.RLock()

        # Worker management
        self._workers = []
        self._active = False
        self._shutdown_event = threading.Event()

        # Statistics
        self.stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_execution_time": 0.0,
            "workers_active": 0,
        }

    def start(self):
        """Start the worker pool."""
        if self._active:
            return

        self._active = True
        self._shutdown_event.clear()

        # Create executor
        if self.use_multiprocessing:
            self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

        # Start result collector thread
        self._result_collector = threading.Thread(
            target=self._collect_results, daemon=True
        )
        self._result_collector.start()

        # Submit worker tasks
        for i in range(self.max_workers):
            worker_id = f"worker_{i}"
            future = self._executor.submit(self._worker_loop, worker_id)
            self._workers.append((worker_id, future))

    def stop(self, wait: bool = True):
        """Stop the worker pool."""
        if not self._active:
            return

        self._active = False
        self._shutdown_event.set()

        # Wait for workers to complete
        if wait:
            for worker_id, future in self._workers:
                try:
                    future.result(timeout=5.0)
                except Exception:
                    pass

        # Shutdown executor
        self._executor.shutdown(wait=wait)

    def submit_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        priority: int = 0,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> bool:
        """
        Submit a task to the worker pool.

        Args:
            task_id: Unique task identifier
            func: Function to execute
            *args: Function arguments
            priority: Task priority (lower values = higher priority)
            timeout: Task timeout in seconds
            **kwargs: Function keyword arguments

        Returns:
            True if task was submitted, False if queue is full
        """
        if not self._active:
            raise RuntimeError("Worker pool is not active")

        task = WorkerTask(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
        )

        try:
            self._task_queue.put((priority, task_id, task), timeout=1.0)
            self.stats["tasks_submitted"] += 1
            return True
        except queue.Full:
            return False

    def get_result(
        self, task_id: str, timeout: Optional[float] = None
    ) -> Optional[TaskResult]:
        """
        Get result for a completed task.

        Args:
            task_id: Task identifier
            timeout: Maximum time to wait for result

        Returns:
            Task result or None if not found/timeout
        """
        start_time = time.time()

        while True:
            with self._results_lock:
                if task_id in self._results:
                    return self._results.pop(task_id)

            if timeout and (time.time() - start_time) >= timeout:
                return None

            if not self._active:
                return None

            time.sleep(0.01)  # Small delay to avoid busy waiting

    def wait_for_completion(
        self, task_ids: List[str], timeout: Optional[float] = None
    ) -> Dict[str, TaskResult]:
        """
        Wait for multiple tasks to complete.

        Args:
            task_ids: List of task IDs to wait for
            timeout: Maximum time to wait

        Returns:
            Dictionary of task results
        """
        results = {}
        remaining_tasks = set(task_ids)
        start_time = time.time()

        while remaining_tasks:
            if timeout and (time.time() - start_time) >= timeout:
                break

            if not self._active:
                break

            # Check for completed tasks
            for task_id in list(remaining_tasks):
                result = self.get_result(task_id, timeout=0.1)
                if result:
                    results[task_id] = result
                    remaining_tasks.remove(task_id)

            if not remaining_tasks:
                break

            time.sleep(0.01)

        return results

    def _worker_loop(self, worker_id: str):
        """Main worker loop."""
        while not self._shutdown_event.is_set():
            try:
                # Get task from queue
                priority, task_id, task = self._task_queue.get(timeout=1.0)

                if self._shutdown_event.is_set():
                    break

                # Execute task
                start_time = time.time()
                try:
                    result = task.func(*task.args, **task.kwargs)
                    execution_time = time.time() - start_time

                    task_result = TaskResult(
                        task_id=task_id,
                        success=True,
                        result=result,
                        execution_time=execution_time,
                    )

                except Exception as e:
                    execution_time = time.time() - start_time

                    task_result = TaskResult(
                        task_id=task_id,
                        success=False,
                        result=None,
                        error=str(e),
                        execution_time=execution_time,
                    )

                # Store result
                with self._results_lock:
                    self._results[task_id] = task_result

                # Update statistics
                self.stats["tasks_completed"] += 1
                if not task_result.success:
                    self.stats["tasks_failed"] += 1

                # Update average execution time
                total_time = self.stats["avg_execution_time"] * (
                    self.stats["tasks_completed"] - 1
                )
                total_time += execution_time
                self.stats["avg_execution_time"] = (
                    total_time / self.stats["tasks_completed"]
                )

                # Mark task as done
                self._task_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                # Log error but continue working
                print(f"Worker {worker_id} error: {e}")

    def _collect_results(self):
        """Collect and organize results."""
        while self._active and not self._shutdown_event.is_set():
            try:
                # Clean up old results periodically
                time.sleep(10)

                with self._results_lock:
                    # Remove results older than 5 minutes
                    current_time = time.time()
                    expired_tasks = [
                        task_id
                        for task_id, result in self._results.items()
                        if current_time - result.execution_time > 300
                    ]

                    for task_id in expired_tasks:
                        self._results.pop(task_id, None)

            except Exception as e:
                print(f"Result collector error: {e}")

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get worker pool statistics."""
        return {
            "active": self._active,
            "max_workers": self.max_workers,
            "use_multiprocessing": self.use_multiprocessing,
            "task_queue_size": self._task_queue.qsize(),
            "results_pending": len(self._results),
            "stats": self.stats.copy(),
        }

    def clear_results(self, max_age: float = 300):
        """
        Clear old results.

        Args:
            max_age: Maximum age of results to keep in seconds
        """
        current_time = time.time()

        with self._results_lock:
            expired_tasks = [
                task_id
                for task_id, result in self._results.items()
                if current_time - result.execution_time > max_age
            ]

            for task_id in expired_tasks:
                self._results.pop(task_id, None)


class AdaptiveScheduler:
    """
    Adaptive scheduler for optimizing worker pool usage.
    """

    def __init__(self, worker_pool: WorkerPool):
        """
        Initialize adaptive scheduler.

        Args:
            worker_pool: Worker pool to manage
        """
        self.worker_pool = worker_pool
        self._performance_history: List[Dict[str, float]] = []

    def optimize_workers(self):
        """Optimize number of workers based on performance."""
        stats = self.worker_pool.get_pool_stats()

        # Record performance data
        performance_data = {
            "queue_size": stats["task_queue_size"],
            "tasks_completed": stats["stats"]["tasks_completed"],
            "avg_execution_time": stats["stats"]["avg_execution_time"],
            "workers_active": stats["max_workers"],
        }

        self._performance_history.append(performance_data)

        # Keep only recent history
        if len(self._performance_history) > 20:
            self._performance_history.pop(0)

        if len(self._performance_history) < 5:
            return  # Need more data

        # Analyze trends and adjust worker count
        recent = self._performance_history[-5:]

        # Calculate queue trend
        queue_trend = recent[-1]["queue_size"] - recent[0]["queue_size"]

        # Calculate throughput trend
        throughput_trend = recent[-1]["tasks_completed"] - recent[0]["tasks_completed"]

        # Adjust worker count based on trends
        current_workers = stats["max_workers"]

        if queue_trend > 100 and throughput_trend > 0:
            # Queue is growing and we're making progress - need more workers
            new_workers = min(current_workers + 1, multiprocessing.cpu_count())
        elif queue_trend < -50 and current_workers > 1:
            # Queue is shrinking - can reduce workers
            new_workers = max(current_workers - 1, 1)
        else:
            new_workers = current_workers

        # Update worker pool if needed
        if new_workers != current_workers:
            self._adjust_worker_count(new_workers)

    def _adjust_worker_count(self, new_count: int):
        """Adjust the number of workers in the pool."""
        # This would require recreating the pool with new worker count
        # For now, we'll just log the recommendation
        print(f"Adaptive scheduler recommends {new_count} workers")
