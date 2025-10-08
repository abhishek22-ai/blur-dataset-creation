"""
Batch Processor

Efficient batch processing for large datasets with adaptive sizing.
"""

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator, List, Optional, Union

from ..memory.memory_manager import MemoryManager


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    initial_batch_size: int = 100
    max_batch_size: int = 1000
    min_batch_size: int = 10
    target_processing_time: float = 1.0  # seconds
    adaptive_sizing: bool = True
    memory_limit_mb: Optional[float] = None


class BatchProcessor:
    """
    Batch processor for large datasets.

    Provides adaptive batch sizing and efficient processing
    of large collections of data.
    """

    def __init__(
        self, memory_manager: MemoryManager, config: Optional[BatchConfig] = None
    ):
        """
        Initialize batch processor.

        Args:
            memory_manager: Memory manager instance
            config: Batch processing configuration
        """
        self.memory_manager = memory_manager
        self.config = config or BatchConfig()

        # Processing state
        self._current_batch_size = self.config.initial_batch_size
        self._processing_stats = {
            "batches_processed": 0,
            "items_processed": 0,
            "total_time": 0.0,
            "avg_batch_time": 0.0,
        }

        # Adaptive sizing
        self._recent_batch_times: List[float] = []
        self._max_recent_times = 10

    def process_dataset(
        self,
        dataset: Union[List[Any], Iterator[Any]],
        processor_func: Callable[[List[Any]], List[Any]],
        **kwargs,
    ) -> List[Any]:
        """
        Process a dataset in adaptive batches.

        Args:
            dataset: Dataset to process (list or iterator)
            processor_func: Function that processes a batch
            **kwargs: Additional arguments for processor function

        Returns:
            List of all processed results
        """
        results = []

        # Convert to list if iterator
        if hasattr(dataset, "__iter__") and not isinstance(dataset, list):
            dataset = list(dataset)

        if not dataset:
            return results

        # Process in batches
        for i in range(0, len(dataset), self._current_batch_size):
            batch = dataset[i : i + self._current_batch_size]

            # Process batch
            start_time = time.time()
            batch_results = self._process_batch_safely(batch, processor_func, **kwargs)
            batch_time = time.time() - start_time

            # Update statistics
            self._update_stats(batch, batch_time)

            # Adapt batch size if enabled
            if self.config.adaptive_sizing:
                self._adapt_batch_size(batch_time)

            # Check memory limits
            if self.config.memory_limit_mb:
                self._check_memory_limits()

            results.extend(batch_results)

        return results

    def _process_batch_safely(
        self,
        batch: List[Any],
        processor_func: Callable[[List[Any]], List[Any]],
        **kwargs,
    ) -> List[Any]:
        """Process a batch with error handling."""
        try:
            return processor_func(batch, **kwargs)
        except Exception as e:
            # Log error and return empty results for this batch
            print(f"Error processing batch: {e}")
            return []

    def _update_stats(self, batch: List[Any], batch_time: float):
        """Update processing statistics."""
        self._processing_stats["batches_processed"] += 1
        self._processing_stats["items_processed"] += len(batch)
        self._processing_stats["total_time"] += batch_time

        # Update average batch time
        if self._processing_stats["batches_processed"] > 0:
            self._processing_stats["avg_batch_time"] = (
                self._processing_stats["total_time"]
                / self._processing_stats["batches_processed"]
            )

        # Track recent batch times for adaptive sizing
        self._recent_batch_times.append(batch_time)
        if len(self._recent_batch_times) > self._max_recent_times:
            self._recent_batch_times.pop(0)

    def _adapt_batch_size(self, batch_time: float):
        """Adapt batch size based on processing time."""
        if len(self._recent_batch_times) < 3:
            return  # Need more data for adaptation

        avg_recent_time = sum(self._recent_batch_times) / len(self._recent_batch_times)

        # Adjust batch size based on target time
        if avg_recent_time < self.config.target_processing_time * 0.8:
            # Processing is fast, increase batch size
            self._current_batch_size = min(
                self._current_batch_size * 2, self.config.max_batch_size
            )
        elif avg_recent_time > self.config.target_processing_time * 1.5:
            # Processing is slow, decrease batch size
            self._current_batch_size = max(
                self._current_batch_size // 2, self.config.min_batch_size
            )

    def _check_memory_limits(self):
        """Check if memory usage is within limits."""
        stats = self.memory_manager.get_memory_stats()

        if stats.memory_percent > 80:  # If memory usage > 80%
            # Trigger cleanup
            self.memory_manager.trigger_cleanup()

            # Reduce batch size to lower memory pressure
            self._current_batch_size = max(
                self._current_batch_size // 2, self.config.min_batch_size
            )

    def process_streaming_dataset(
        self,
        data_stream: Iterator[Any],
        processor_func: Callable[[List[Any]], List[Any]],
        buffer_size: int = 1000,
        **kwargs,
    ) -> Iterator[List[Any]]:
        """
        Process a streaming dataset.

        Args:
            data_stream: Iterator yielding data items
            processor_func: Function that processes a batch
            buffer_size: Size of processing buffer
            **kwargs: Additional arguments

        Yields:
            Processed batch results
        """
        buffer = []

        for item in data_stream:
            buffer.append(item)

            if len(buffer) >= buffer_size:
                # Process current buffer
                results = self._process_batch_safely(buffer, processor_func, **kwargs)

                # Update statistics
                time.time()  # We don't measure time here for streaming
                self._update_stats(buffer, 0.1)  # Use small placeholder time

                yield results
                buffer = []

        # Process remaining items
        if buffer:
            results = self._process_batch_safely(buffer, processor_func, **kwargs)
            self._update_stats(buffer, 0.1)
            yield results

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "current_batch_size": self._current_batch_size,
            "config": {
                "initial_batch_size": self.config.initial_batch_size,
                "max_batch_size": self.config.max_batch_size,
                "min_batch_size": self.config.min_batch_size,
                "target_processing_time": self.config.target_processing_time,
                "adaptive_sizing": self.config.adaptive_sizing,
                "memory_limit_mb": self.config.memory_limit_mb,
            },
            "stats": self._processing_stats.copy(),
            "recent_batch_times": self._recent_batch_times.copy(),
            "avg_recent_time": (
                sum(self._recent_batch_times) / len(self._recent_batch_times)
                if self._recent_batch_times
                else 0.0
            ),
        }

    def reset_stats(self):
        """Reset processing statistics."""
        self._processing_stats = {
            "batches_processed": 0,
            "items_processed": 0,
            "total_time": 0.0,
            "avg_batch_time": 0.0,
        }
        self._recent_batch_times.clear()
        self._current_batch_size = self.config.initial_batch_size


class AdaptiveBatchProcessor(BatchProcessor):
    """
    Advanced batch processor with machine learning-based adaptation.
    """

    def __init__(self, memory_manager: MemoryManager, **kwargs):
        """Initialize adaptive batch processor."""
        super().__init__(memory_manager, **kwargs)

        # ML-based adaptation parameters
        self._performance_history: List[Dict[str, float]] = []
        self._adaptation_model = {
            "batch_size_factor": 1.0,
            "memory_sensitivity": 0.1,
            "time_sensitivity": 0.1,
        }

    def _adapt_batch_size_ml(self, batch_time: float):
        """Adapt batch size using simple ML approach."""
        # Get current memory stats
        memory_stats = self.memory_manager.get_memory_stats()

        # Record performance data
        performance_data = {
            "batch_time": batch_time,
            "batch_size": self._current_batch_size,
            "memory_percent": memory_stats.memory_percent,
            "available_memory_mb": memory_stats.available_memory_mb,
        }

        self._performance_history.append(performance_data)

        # Keep only recent history
        if len(self._performance_history) > 50:
            self._performance_history.pop(0)

        if len(self._performance_history) < 5:
            return  # Need more data

        # Simple adaptation logic based on trends
        recent_performance = self._performance_history[-5:]

        # Calculate trends
        time_trend = (
            recent_performance[-1]["batch_time"] - recent_performance[0]["batch_time"]
        )
        memory_trend = (
            recent_performance[-1]["memory_percent"]
            - recent_performance[0]["memory_percent"]
        )

        # Adjust batch size based on trends
        adjustment_factor = 1.0

        if time_trend > 0.1:  # Time is increasing
            adjustment_factor *= 0.8
        elif time_trend < -0.1:  # Time is decreasing
            adjustment_factor *= 1.2

        if memory_trend > 5:  # Memory usage increasing
            adjustment_factor *= 0.9
        elif memory_trend < -5:  # Memory usage decreasing
            adjustment_factor *= 1.1

        # Apply adjustment
        new_batch_size = int(self._current_batch_size * adjustment_factor)
        self._current_batch_size = max(
            self.config.min_batch_size, min(new_batch_size, self.config.max_batch_size)
        )
