"""
Adaptive Scheduler

Machine learning-based scheduler for optimizing parallel processing.
"""

import statistics
import threading
import time
from collections import deque
from typing import Any, Dict

from ..memory.memory_manager import MemoryManager
from .batch_processor import BatchProcessor
from .parallel_processor import ParallelProcessor


class AdaptiveScheduler:
    """
    Adaptive scheduler that learns optimal processing parameters.

    Uses historical performance data to optimize batch sizes,
    worker counts, and resource allocation.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        learning_rate: float = 0.1,
        history_size: int = 100,
    ):
        """
        Initialize adaptive scheduler.

        Args:
            memory_manager: Memory manager instance
            learning_rate: Learning rate for parameter updates
            history_size: Maximum history size for learning
        """
        self.memory_manager = memory_manager
        self.learning_rate = learning_rate
        self.history_size = history_size

        # Performance history
        self.performance_history: deque = deque(maxlen=history_size)

        # Current parameters
        self.parameters = {
            "batch_size": 100,
            "worker_count": 4,
            "memory_threshold": 80.0,
            "processing_timeout": 30.0,
        }

        # Learning state
        self._learning_active = False
        self._learning_thread = None

        # Statistics
        self.stats = {"adaptations": 0, "improvements": 0, "learning_iterations": 0}

    def record_performance(
        self,
        batch_size: int,
        worker_count: int,
        processing_time: float,
        memory_usage: float,
        throughput: float,
        success_rate: float,
    ):
        """
        Record performance data for learning.

        Args:
            batch_size: Batch size used
            worker_count: Number of workers used
            processing_time: Total processing time
            memory_usage: Memory usage percentage
            throughput: Items processed per second
            success_rate: Success rate (0.0 to 1.0)
        """
        performance_data = {
            "timestamp": time.time(),
            "batch_size": batch_size,
            "worker_count": worker_count,
            "processing_time": processing_time,
            "memory_usage": memory_usage,
            "throughput": throughput,
            "success_rate": success_rate,
            "efficiency": throughput / max(worker_count, 1),  # Throughput per worker
            "memory_efficiency": throughput
            / max(memory_usage, 1),  # Throughput per memory %
        }

        self.performance_history.append(performance_data)

    def start_learning(self):
        """Start the learning process."""
        if self._learning_active:
            return

        self._learning_active = True
        self._learning_thread = threading.Thread(
            target=self._learning_loop, daemon=True
        )
        self._learning_thread.start()

    def stop_learning(self):
        """Stop the learning process."""
        self._learning_active = False
        if self._learning_thread:
            self._learning_thread.join(timeout=5.0)

    def _learning_loop(self):
        """Main learning loop."""
        while self._learning_active:
            try:
                self._update_parameters()
                self.stats["learning_iterations"] += 1

                # Learn every 30 seconds
                time.sleep(30)

            except Exception as e:
                print(f"Learning error: {e}")
                time.sleep(30)

    def _update_parameters(self):
        """Update parameters based on performance history."""
        if len(self.performance_history) < 10:
            return  # Need more data

        # Extract recent performance data
        recent_data = list(self.performance_history)[-20:]

        # Calculate performance metrics
        avg_throughput = statistics.mean([d["throughput"] for d in recent_data])
        avg_memory_usage = statistics.mean([d["memory_usage"] for d in recent_data])
        avg_success_rate = statistics.mean([d["success_rate"] for d in recent_data])
        avg_efficiency = statistics.mean([d["efficiency"] for d in recent_data])

        # Update parameters based on performance

        # Adjust batch size based on throughput and memory
        if avg_throughput > 50 and avg_memory_usage < 70:  # Good performance
            new_batch_size = min(self.parameters["batch_size"] * 1.1, 1000)
        elif avg_throughput < 10 or avg_memory_usage > 85:  # Poor performance
            new_batch_size = max(self.parameters["batch_size"] * 0.9, 10)
        else:
            new_batch_size = self.parameters["batch_size"]

        # Adjust worker count based on efficiency
        if avg_efficiency > 15:  # High efficiency per worker
            new_worker_count = min(self.parameters["worker_count"] + 1, 16)
        elif avg_efficiency < 5:  # Low efficiency per worker
            new_worker_count = max(self.parameters["worker_count"] - 1, 1)
        else:
            new_worker_count = self.parameters["worker_count"]

        # Adjust memory threshold based on success rate
        if avg_success_rate > 0.95:  # High success rate
            new_memory_threshold = min(self.parameters["memory_threshold"] + 5, 95)
        elif avg_success_rate < 0.8:  # Low success rate
            new_memory_threshold = max(self.parameters["memory_threshold"] - 5, 60)
        else:
            new_memory_threshold = self.parameters["memory_threshold"]

        # Apply updates with smoothing
        self.parameters["batch_size"] = (
            self.parameters["batch_size"] * (1 - self.learning_rate)
            + new_batch_size * self.learning_rate
        )
        self.parameters["worker_count"] = (
            self.parameters["worker_count"] * (1 - self.learning_rate)
            + new_worker_count * self.learning_rate
        )
        self.parameters["memory_threshold"] = (
            self.parameters["memory_threshold"] * (1 - self.learning_rate)
            + new_memory_threshold * self.learning_rate
        )

        # Round to integers where appropriate
        self.parameters["batch_size"] = int(self.parameters["batch_size"])
        self.parameters["worker_count"] = int(self.parameters["worker_count"])

        self.stats["adaptations"] += 1

    def get_optimal_config(self) -> Dict[str, Any]:
        """
        Get optimal configuration based on learning.

        Returns:
            Dictionary with optimal parameters
        """
        return {
            "batch_size": int(self.parameters["batch_size"]),
            "worker_count": int(self.parameters["worker_count"]),
            "memory_threshold": self.parameters["memory_threshold"],
            "processing_timeout": self.parameters["processing_timeout"],
        }

    def predict_performance(
        self, batch_size: int, worker_count: int, data_size: int
    ) -> Dict[str, float]:
        """
        Predict performance for given parameters.

        Args:
            batch_size: Proposed batch size
            worker_count: Proposed worker count
            data_size: Size of dataset

        Returns:
            Predicted performance metrics
        """
        if len(self.performance_history) < 5:
            # No historical data, return default predictions
            return {
                "predicted_throughput": 10.0,
                "predicted_memory_usage": 50.0,
                "predicted_success_rate": 0.9,
                "confidence": 0.1,
            }

        # Simple prediction based on historical data
        similar_configs = [
            d
            for d in self.performance_history
            if abs(d["batch_size"] - batch_size) / batch_size < 0.2
            and abs(d["worker_count"] - worker_count) / worker_count < 0.2
        ]

        if not similar_configs:
            # No similar configurations, use overall averages
            similar_configs = list(self.performance_history)

        # Calculate predictions
        predicted_throughput = statistics.mean(
            [d["throughput"] for d in similar_configs]
        )
        predicted_memory_usage = statistics.mean(
            [d["memory_usage"] for d in similar_configs]
        )
        predicted_success_rate = statistics.mean(
            [d["success_rate"] for d in similar_configs]
        )

        # Adjust for data size
        scale_factor = data_size / 1000  # Assume 1000 is baseline
        predicted_throughput *= scale_factor
        predicted_memory_usage *= scale_factor

        # Calculate confidence based on data similarity
        confidence = min(len(similar_configs) / 10, 1.0)

        return {
            "predicted_throughput": predicted_throughput,
            "predicted_memory_usage": predicted_memory_usage,
            "predicted_success_rate": predicted_success_rate,
            "confidence": confidence,
        }

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        if not self.performance_history:
            return {"message": "No performance data available"}

        recent_data = list(self.performance_history)[-10:]

        return {
            "history_size": len(self.performance_history),
            "learning_active": self._learning_active,
            "current_parameters": self.parameters.copy(),
            "stats": self.stats.copy(),
            "recent_performance": {
                "avg_throughput": statistics.mean(
                    [d["throughput"] for d in recent_data]
                ),
                "avg_memory_usage": statistics.mean(
                    [d["memory_usage"] for d in recent_data]
                ),
                "avg_success_rate": statistics.mean(
                    [d["success_rate"] for d in recent_data]
                ),
                "avg_efficiency": statistics.mean(
                    [d["efficiency"] for d in recent_data]
                ),
            },
        }

    def reset_learning(self):
        """Reset learning state."""
        self.performance_history.clear()
        self.parameters = {
            "batch_size": 100,
            "worker_count": 4,
            "memory_threshold": 80.0,
            "processing_timeout": 30.0,
        }
        self.stats = {"adaptations": 0, "improvements": 0, "learning_iterations": 0}


class ProcessingOptimizer:
    """
    High-level optimizer that coordinates all processing components.
    """

    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize processing optimizer.

        Args:
            memory_manager: Memory manager instance
        """
        self.memory_manager = memory_manager

        # Create processing components
        self.parallel_processor = ParallelProcessor(memory_manager)
        self.batch_processor = BatchProcessor(memory_manager)
        self.adaptive_scheduler = AdaptiveScheduler(memory_manager)

        # Optimization state
        self._optimizer_active = False
        self._optimization_thread = None

    def start_optimization(self):
        """Start automatic optimization."""
        if self._optimizer_active:
            return

        self._optimizer_active = True
        self.adaptive_scheduler.start_learning()

        self._optimization_thread = threading.Thread(
            target=self._optimization_loop, daemon=True
        )
        self._optimization_thread.start()

    def stop_optimization(self):
        """Stop automatic optimization."""
        self._optimizer_active = False
        self.adaptive_scheduler.stop_learning()

        if self._optimization_thread:
            self._optimization_thread.join(timeout=5.0)

    def _optimization_loop(self):
        """Main optimization loop."""
        while self._optimizer_active:
            try:
                # Update scheduler
                self.adaptive_scheduler.optimize_workers()

                # Update batch processor configuration
                optimal_config = self.adaptive_scheduler.get_optimal_config()
                self.batch_processor._current_batch_size = optimal_config["batch_size"]

                # Sleep for optimization interval
                time.sleep(60)  # Optimize every minute

            except Exception as e:
                print(f"Optimization error: {e}")
                time.sleep(60)

    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report."""
        return {
            "optimizer_active": self._optimizer_active,
            "parallel_processor_stats": self.parallel_processor.get_processing_stats(),
            "batch_processor_stats": self.batch_processor.get_processing_stats(),
            "scheduler_stats": self.adaptive_scheduler.get_learning_stats(),
            "memory_stats": self.memory_manager.get_memory_report(),
        }
