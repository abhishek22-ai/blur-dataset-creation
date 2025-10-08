"""
Parallel Processor

Multi-threading and multi-processing for parallel image operations.
"""

import concurrent.futures
import multiprocessing
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


from ..memory.memory_manager import MemoryManager


@dataclass
class ProcessingResult:
    """Result of parallel processing operation."""

    success: bool
    data: Any
    processing_time: float
    error: Optional[str] = None
    worker_id: Optional[int] = None


class ParallelProcessor:
    """
    Parallel processor for image operations.

    Provides multi-threading and multi-processing capabilities
    with adaptive resource management.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        max_workers: Optional[int] = None,
        use_multiprocessing: bool = False,
        chunk_size: int = 100,
    ):
        """
        Initialize parallel processor.

        Args:
            memory_manager: Memory manager instance
            max_workers: Maximum number of worker threads/processes
            use_multiprocessing: Whether to use multiprocessing instead of threading
            chunk_size: Size of data chunks for batch processing
        """
        self.memory_manager = memory_manager
        self.chunk_size = chunk_size
        self.use_multiprocessing = use_multiprocessing

        # Determine optimal worker count
        if max_workers is None:
            self.max_workers = self._determine_optimal_workers()
        else:
            self.max_workers = max_workers

        # Processing statistics
        self.stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "total_processing_time": 0.0,
            "errors": 0,
        }

    def _determine_optimal_workers(self) -> int:
        """Determine optimal number of workers based on system resources."""
        cpu_count = multiprocessing.cpu_count()
        memory_stats = self.memory_manager.get_memory_stats()

        # Use CPU count, but limit based on memory availability
        available_memory_gb = memory_stats.available_memory_mb / 1024

        # Reserve some memory for the main process and overhead
        available_memory_gb -= 2.0  # Reserve 2GB for main process

        # Estimate memory per worker (rough estimate)
        memory_per_worker_gb = 0.5  # 500MB per worker

        max_workers_by_memory = max(1, int(available_memory_gb / memory_per_worker_gb))

        return min(cpu_count, max_workers_by_memory, 8)  # Cap at 8 workers

    def process_batch(
        self, items: List[Any], processor_func: Callable[[Any], Any], **kwargs
    ) -> List[ProcessingResult]:
        """
        Process a batch of items in parallel.

        Args:
            items: List of items to process
            processor_func: Function to process each item
            **kwargs: Additional arguments for processor function

        Returns:
            List of processing results
        """
        if not items:
            return []

        # Split into chunks for better load balancing
        chunks = self._create_chunks(items, self.chunk_size)

        # Process chunks in parallel
        results = []
        for chunk in chunks:
            chunk_results = self._process_chunk(chunk, processor_func, **kwargs)
            results.extend(chunk_results)

        return results

    def _create_chunks(self, items: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split items into chunks."""
        chunks = []
        for i in range(0, len(items), chunk_size):
            chunks.append(items[i : i + chunk_size])
        return chunks

    def _process_chunk(
        self, chunk: List[Any], processor_func: Callable[[Any], Any], **kwargs
    ) -> List[ProcessingResult]:
        """Process a chunk of items."""
        if self.use_multiprocessing:
            return self._process_chunk_multiprocessing(chunk, processor_func, **kwargs)
        else:
            return self._process_chunk_threading(chunk, processor_func, **kwargs)

    def _process_chunk_threading(
        self, chunk: List[Any], processor_func: Callable[[Any], Any], **kwargs
    ) -> List[ProcessingResult]:
        """Process chunk using threading."""
        results = []

        def process_item(item):
            start_time = time.time()
            try:
                data = processor_func(item, **kwargs)
                processing_time = time.time() - start_time
                return ProcessingResult(
                    success=True, data=data, processing_time=processing_time
                )
            except Exception as e:
                processing_time = time.time() - start_time
                return ProcessingResult(
                    success=False,
                    data=None,
                    processing_time=processing_time,
                    error=str(e),
                )

        # Process items in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(process_item, item): item for item in chunk
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_item):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # This shouldn't happen since we handle exceptions in process_item
                    results.append(
                        ProcessingResult(
                            success=False, data=None, processing_time=0.0, error=str(e)
                        )
                    )

        return results

    def _process_chunk_multiprocessing(
        self, chunk: List[Any], processor_func: Callable[[Any], Any], **kwargs
    ) -> List[ProcessingResult]:
        """Process chunk using multiprocessing."""
        results = []

        def process_item(item):
            start_time = time.time()
            try:
                data = processor_func(item, **kwargs)
                processing_time = time.time() - start_time
                return ProcessingResult(
                    success=True, data=data, processing_time=processing_time
                )
            except Exception as e:
                processing_time = time.time() - start_time
                return ProcessingResult(
                    success=False,
                    data=None,
                    processing_time=processing_time,
                    error=str(e),
                )

        # Process items in parallel using ProcessPoolExecutor
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(process_item, item): item for item in chunk
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_item):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(
                        ProcessingResult(
                            success=False, data=None, processing_time=0.0, error=str(e)
                        )
                    )

        return results

    def process_stream(
        self,
        data_generator,
        processor_func: Callable[[Any], Any],
        buffer_size: int = 1000,
        **kwargs,
    ) -> List[ProcessingResult]:
        """
        Process streaming data in parallel.

        Args:
            data_generator: Generator yielding data items
            processor_func: Function to process each item
            buffer_size: Size of processing buffer
            **kwargs: Additional arguments for processor function

        Returns:
            List of processing results
        """
        results = []
        buffer = []

        for item in data_generator:
            buffer.append(item)

            if len(buffer) >= buffer_size:
                # Process current buffer
                batch_results = self.process_batch(buffer, processor_func, **kwargs)
                results.extend(batch_results)
                buffer = []

        # Process remaining items
        if buffer:
            batch_results = self.process_batch(buffer, processor_func, **kwargs)
            results.extend(batch_results)

        return results

    def map_reduce(
        self,
        items: List[Any],
        map_func: Callable[[Any], Any],
        reduce_func: Callable[[List[Any]], Any],
        **kwargs,
    ) -> Any:
        """
        Perform map-reduce operation in parallel.

        Args:
            items: List of items to process
            map_func: Map function
            reduce_func: Reduce function
            **kwargs: Additional arguments

        Returns:
            Reduced result
        """
        # Map phase
        map_results = self.process_batch(items, map_func, **kwargs)

        # Filter successful results
        successful_results = [result.data for result in map_results if result.success]

        # Reduce phase
        return reduce_func(successful_results)

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        total_tasks = self.stats["tasks_completed"] + self.stats["errors"]

        return {
            "max_workers": self.max_workers,
            "processing_mode": "multiprocessing"
            if self.use_multiprocessing
            else "threading",
            "tasks_submitted": self.stats["tasks_submitted"],
            "tasks_completed": self.stats["tasks_completed"],
            "errors": self.stats["errors"],
            "success_rate": (self.stats["tasks_completed"] / total_tasks)
            if total_tasks > 0
            else 0.0,
            "avg_processing_time": (
                self.stats["total_processing_time"] / self.stats["tasks_completed"]
                if self.stats["tasks_completed"] > 0
                else 0.0
            ),
            "chunk_size": self.chunk_size,
        }

    def adaptive_batch_size(self, target_time: float = 1.0) -> int:
        """
        Adaptively determine optimal batch size.

        Args:
            target_time: Target processing time per batch in seconds

        Returns:
            Recommended batch size
        """
        if self.stats["tasks_completed"] == 0:
            return self.chunk_size

        avg_time = self.stats["total_processing_time"] / self.stats["tasks_completed"]

        if avg_time == 0:
            return self.chunk_size

        # Adjust batch size based on performance
        current_workers = min(self.max_workers, multiprocessing.cpu_count())

        # Estimate optimal batch size
        optimal_batch_size = int((target_time / avg_time) * current_workers)

        # Clamp to reasonable bounds
        return max(1, min(optimal_batch_size, 1000))


class ParallelImageProcessor(ParallelProcessor):
    """
    Specialized parallel processor for image operations.
    """

    def __init__(self, memory_manager: MemoryManager, **kwargs):
        """Initialize parallel image processor."""
        super().__init__(memory_manager, **kwargs)

    def process_images_parallel(
        self, image_paths: List[str], image_processor_func: Callable, **kwargs
    ) -> List[ProcessingResult]:
        """
        Process multiple images in parallel.

        Args:
            image_paths: List of image file paths
            image_processor_func: Function to process each image
            **kwargs: Additional arguments

        Returns:
            List of processing results
        """

        def load_and_process(image_path):
            """Load image and apply processing."""
            try:
                # Use image cache if available
                from ..cache.image_cache import ImageCache

                image_cache = ImageCache(self.memory_manager)

                # Load image with caching
                image = image_cache.load_image_cached(image_path)

                # Apply processing
                return image_processor_func(image, **kwargs)

            except Exception as e:
                raise Exception(f"Error processing {image_path}: {e}")

        return self.process_batch(image_paths, load_and_process)

    def create_image_tiles_parallel(
        self, image_path: str, tile_size: int = 256, overlap: int = 0
    ) -> List[ProcessingResult]:
        """
        Create image tiles in parallel.

        Args:
            image_path: Path to image
            tile_size: Size of each tile
            overlap: Overlap between tiles

        Returns:
            List of tile processing results
        """

        def create_tile(tile_info):
            """Create a single tile."""
            i, j, image = tile_info

            # Calculate tile bounds
            start_y, start_x = i * (tile_size - overlap), j * (tile_size - overlap)
            end_y = min(start_y + tile_size, image.shape[0])
            end_x = min(start_x + tile_size, image.shape[1])

            # Extract tile
            if len(image.shape) == 3:
                tile = image[start_y:end_y, start_x:end_x, :]
            else:
                tile = image[start_y:end_y, start_x:end_x]

            return {
                "tile": tile,
                "position": (i, j),
                "bounds": (start_y, start_x, end_y, end_x),
            }

        # Load image
        from ..cache.image_cache import ImageCache

        image_cache = ImageCache(self.memory_manager)
        image = image_cache.load_image_cached(image_path)

        # Calculate tile grid
        height, width = image.shape[:2]
        tiles_info = []

        for i in range(0, (height - overlap + tile_size - 1) // (tile_size - overlap)):
            for j in range(
                0, (width - overlap + tile_size - 1) // (tile_size - overlap)
            ):
                tiles_info.append((i, j, image))

        # Process tiles in parallel
        return self.process_batch(tiles_info, create_tile)
