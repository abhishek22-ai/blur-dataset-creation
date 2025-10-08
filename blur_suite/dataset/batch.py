"""
Batch processing with parallelization for dataset creation.

This module provides functionality for processing large datasets in parallel,
with support for multi-threading, multi-processing, and memory management.
"""

import logging
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

from .metadata import MetadataCollector
from .utils import ImageValidator, SystemInfo, format_time

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    max_workers: Optional[int] = None
    use_multiprocessing: bool = True
    chunk_size: int = 10
    max_memory_gb: float = 4.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout_per_image: float = 300.0  # 5 minutes

    def __post_init__(self):
        """Set default values based on system."""
        if self.max_workers is None:
            self.max_workers = SystemInfo.get_optimal_worker_count()


@dataclass
class BatchResult:
    """Result of a batch processing operation."""

    success: bool
    processing_time: float
    images_processed: int
    images_failed: int
    errors: List[str]
    warnings: List[str]


class BatchProcessor:
    """
    Handles parallel processing of large datasets.

    Provides multi-threading and multi-processing capabilities for
    CPU-intensive blur operations with memory management and progress tracking.
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        """
        Initialize batch processor.

        Args:
            config: Batch processing configuration
        """
        self.config = config or BatchConfig()
        self.metadata_collector = MetadataCollector()

    def process_batch(
        self,
        image_paths: List[Union[str, Path]],
        blur_function: Callable[
            [str, str, Dict[str, Any]], Tuple[bool, str, Optional[np.ndarray], float]
        ],
        blur_type: str,
        parameters: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        """
        Process a batch of images in parallel.

        Args:
            image_paths: List of image paths to process
            blur_function: Function to apply blur (image_path, blur_type, parameters) -> (success, result_path, image_array, processing_time)
            blur_type: Type of blur to apply
            parameters: Blur parameters
            progress_callback: Optional callback for progress updates

        Returns:
            BatchResult with processing results
        """
        start_time = time.time()
        self.metadata_collector.start_collection()

        total_images = len(image_paths)
        processed_count = 0
        failed_count = 0
        errors = []
        warnings = []

        logger.info(
            f"Starting batch processing of {total_images} images with {self.config.max_workers} workers"
        )

        try:
            if self.config.use_multiprocessing:
                result = self._process_with_multiprocessing(
                    image_paths, blur_function, blur_type, parameters, progress_callback
                )
            else:
                result = self._process_with_threading(
                    image_paths, blur_function, blur_type, parameters, progress_callback
                )

            processed_count = result["processed"]
            failed_count = result["failed"]
            errors = result["errors"]
            warnings = result["warnings"]

        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            errors.append(str(e))
            failed_count = total_images - processed_count

        finally:
            self.metadata_collector.stop_collection()
            processing_time = time.time() - start_time

        return BatchResult(
            success=len(errors) == 0,
            processing_time=processing_time,
            images_processed=processed_count,
            images_failed=failed_count,
            errors=errors,
            warnings=warnings,
        )

    def _process_with_multiprocessing(
        self,
        image_paths: List[Union[str, Path]],
        blur_function: Callable,
        blur_type: str,
        parameters: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Process images using multiprocessing."""
        processed = 0
        failed = 0
        errors = []
        warnings = []

        # Split into chunks for better memory management
        chunks = self._create_chunks(image_paths, self.config.chunk_size)

        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all chunks
            future_to_chunk = {
                executor.submit(
                    self._process_chunk, chunk, blur_function, blur_type, parameters
                ): chunk
                for chunk in chunks
            }

            # Process completed chunks
            for future in as_completed(
                future_to_chunk, timeout=self.config.timeout_per_image * len(chunks[0])
            ):
                try:
                    chunk_result = future.result(timeout=self.config.timeout_per_image)
                    processed += chunk_result["processed"]
                    failed += chunk_result["failed"]
                    errors.extend(chunk_result["errors"])
                    warnings.extend(chunk_result["warnings"])

                    if progress_callback:
                        progress_callback(processed + failed, len(image_paths))

                except Exception as e:
                    chunk = future_to_chunk[future]
                    error_msg = f"Chunk processing failed: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    failed += len(chunk)

        return {
            "processed": processed,
            "failed": failed,
            "errors": errors,
            "warnings": warnings,
        }

    def _process_with_threading(
        self,
        image_paths: List[Union[str, Path]],
        blur_function: Callable,
        blur_type: str,
        parameters: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """Process images using threading."""
        processed = 0
        failed = 0
        errors = []
        warnings = []

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all images
            future_to_image = {
                executor.submit(
                    self._process_single_image,
                    image_path,
                    blur_function,
                    blur_type,
                    parameters,
                ): image_path
                for image_path in image_paths
            }

            # Process completed images
            for future in as_completed(
                future_to_image, timeout=self.config.timeout_per_image
            ):
                try:
                    result = future.result(timeout=self.config.timeout_per_image)
                    if result["success"]:
                        processed += 1
                    else:
                        failed += 1
                        errors.append(result["error"])

                    if result["warnings"]:
                        warnings.extend(result["warnings"])

                    if progress_callback:
                        progress_callback(processed + failed, len(image_paths))

                except Exception as e:
                    image_path = future_to_image[future]
                    error_msg = f"Image processing failed for {image_path}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    failed += 1

        return {
            "processed": processed,
            "failed": failed,
            "errors": errors,
            "warnings": warnings,
        }

    def _process_chunk(
        self,
        chunk: List[Union[str, Path]],
        blur_function: Callable,
        blur_type: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process a chunk of images."""
        processed = 0
        failed = 0
        errors = []
        warnings = []

        for image_path in chunk:
            try:
                result = self._process_single_image(
                    image_path, blur_function, blur_type, parameters
                )

                if result["success"]:
                    processed += 1
                else:
                    failed += 1
                    errors.append(result["error"])

                if result["warnings"]:
                    warnings.extend(result["warnings"])

                # Record metadata
                self.metadata_collector.record_processing(
                    image_path=str(image_path),
                    blur_type=blur_type,
                    parameters=parameters,
                    processing_time_ms=result["processing_time_ms"],
                    original_size=result["original_size"],
                    result_size=result["result_size"],
                    success=result["success"],
                    error_message=result["error"] if not result["success"] else None,
                    warnings=result["warnings"],
                )

            except Exception as e:
                error_msg = f"Failed to process {image_path}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                failed += 1

        return {
            "processed": processed,
            "failed": failed,
            "errors": errors,
            "warnings": warnings,
        }

    def _process_single_image(
        self,
        image_path: Union[str, Path],
        blur_function: Callable,
        blur_type: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process a single image with retry logic."""
        image_path = Path(image_path)

        # Load image
        image = ImageValidator.load_image(image_path)
        if image is None:
            return {
                "success": False,
                "error": f"Failed to load image: {image_path}",
                "warnings": [],
                "processing_time_ms": 0.0,
                "original_size": (0, 0),
                "result_size": (0, 0),
            }

        original_size = image.shape[:2]

        # Apply blur with retry logic
        for attempt in range(self.config.retry_attempts):
            try:
                success, result_path, result_image, processing_time_ms = blur_function(
                    str(image_path), blur_type, parameters
                )

                if success and result_image is not None:
                    result_size = result_image.shape[:2]
                    return {
                        "success": True,
                        "error": None,
                        "warnings": [],
                        "processing_time_ms": processing_time_ms,
                        "original_size": original_size,
                        "result_size": result_size,
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Blur function failed for {image_path}",
                        "warnings": [],
                        "processing_time_ms": processing_time_ms,
                        "original_size": original_size,
                        "result_size": (0, 0),
                    }

            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {image_path}: {str(e)}"
                    )
                    time.sleep(self.config.retry_delay)
                else:
                    return {
                        "success": False,
                        "error": f"Failed after {self.config.retry_attempts} attempts: {str(e)}",
                        "warnings": [],
                        "processing_time_ms": 0.0,
                        "original_size": original_size,
                        "result_size": (0, 0),
                    }

        return {
            "success": False,
            "error": f"Unexpected error processing {image_path}",
            "warnings": [],
            "processing_time_ms": 0.0,
            "original_size": original_size,
            "result_size": (0, 0),
        }

    def _create_chunks(self, items: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split items into chunks."""
        return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]

    def get_metadata_collector(self) -> MetadataCollector:
        """Get the metadata collector."""
        return self.metadata_collector

    def estimate_processing_time(
        self, image_count: int, avg_time_per_image: float = 1.0
    ) -> str:
        """
        Estimate total processing time.

        Args:
            image_count: Number of images to process
            avg_time_per_image: Average time per image in seconds

        Returns:
            Formatted time estimate
        """
        # Account for parallelization efficiency (typically 70-80% of theoretical max)
        efficiency_factor = 0.75
        workers = self.config.max_workers

        # Calculate estimated time
        if workers > 1:
            parallel_time = (image_count * avg_time_per_image) / (
                workers * efficiency_factor
            )
        else:
            parallel_time = image_count * avg_time_per_image

        return format_time(parallel_time)

    def get_memory_usage_estimate(
        self, image_count: int, avg_image_size_mb: float = 10.0
    ) -> float:
        """
        Estimate memory usage for batch processing.

        Args:
            image_count: Number of images
            avg_image_size_mb: Average image size in MB

        Returns:
            Estimated memory usage in GB
        """
        # Account for multiple copies in memory during processing
        memory_multiplier = 3.0  # Original + blurred + working copies
        workers = self.config.max_workers

        total_memory_gb = (image_count * avg_image_size_mb * memory_multiplier) / (
            1024 * workers
        )

        return total_memory_gb

    def validate_batch_config(self) -> List[str]:
        """
        Validate batch processing configuration.

        Returns:
            List of validation warnings/errors
        """
        issues = []

        # Check worker count
        max_workers = SystemInfo.get_cpu_count()
        if self.config.max_workers > max_workers:
            issues.append(
                f"max_workers ({self.config.max_workers}) exceeds CPU count ({max_workers})"
            )

        # Check memory limits
        memory_info = SystemInfo.get_memory_info()
        estimated_memory = self.get_memory_usage_estimate(
            100
        )  # Estimate for 100 images

        if estimated_memory > memory_info["available_gb"]:
            issues.append(
                f"Estimated memory usage ({estimated_memory:.1f}GB) may exceed available memory "
                f"({memory_info['available_gb']:.1f}GB)"
            )

        # Check chunk size
        if self.config.chunk_size < 1:
            issues.append("chunk_size must be at least 1")

        if self.config.chunk_size > 100:
            issues.append("Very large chunk_size may cause memory issues")

        return issues


class AdaptiveBatchProcessor(BatchProcessor):
    """
    Advanced batch processor with adaptive resource management.

    Automatically adjusts processing parameters based on system resources
    and processing performance.
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        """Initialize adaptive batch processor."""
        super().__init__(config)
        self.performance_history: List[float] = []

    def process_batch_adaptive(
        self,
        image_paths: List[Union[str, Path]],
        blur_function: Callable,
        blur_type: str,
        parameters: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchResult:
        """
        Process batch with adaptive resource management.

        Args:
            image_paths: List of image paths to process
            blur_function: Function to apply blur
            blur_type: Type of blur to apply
            parameters: Blur parameters
            progress_callback: Optional progress callback

        Returns:
            BatchResult with processing results
        """
        # Analyze system resources and adjust configuration
        self._adapt_configuration(image_paths)

        # Process with adapted configuration
        return self.process_batch(
            image_paths, blur_function, blur_type, parameters, progress_callback
        )

    def _adapt_configuration(self, image_paths: List[Union[str, Path]]):
        """Adapt configuration based on system resources and workload."""
        # Get system information
        memory_info = SystemInfo.get_memory_info()
        SystemInfo.get_cpu_count()

        # Estimate memory requirements
        estimated_memory = self.get_memory_usage_estimate(len(image_paths))

        # Adjust worker count based on memory
        if estimated_memory > memory_info["available_gb"] * 0.8:
            # Reduce workers if memory-constrained
            self.config.max_workers = max(1, self.config.max_workers - 1)
            logger.info(
                f"Reduced workers to {self.config.max_workers} due to memory constraints"
            )

        # Adjust chunk size based on worker count and memory
        if self.config.max_workers == 1:
            self.config.chunk_size = min(50, len(image_paths))
        else:
            # Smaller chunks for better memory management with multiple workers
            self.config.chunk_size = min(
                20, max(5, len(image_paths) // self.config.max_workers)
            )

        logger.info(
            f"Adapted configuration: {self.config.max_workers} workers, chunk_size={self.config.chunk_size}"
        )

    def record_performance_sample(self, processing_time: float, image_count: int):
        """
        Record performance sample for adaptation.

        Args:
            processing_time: Processing time in seconds
            image_count: Number of images processed
        """
        if image_count > 0:
            avg_time_per_image = processing_time / image_count
            self.performance_history.append(avg_time_per_image)

            # Keep only recent samples
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-100:]

    def get_performance_stats(self) -> Dict[str, float]:
        """
        Get performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        if not self.performance_history:
            return {}

        return {
            "avg_time_per_image": sum(self.performance_history)
            / len(self.performance_history),
            "min_time_per_image": min(self.performance_history),
            "max_time_per_image": max(self.performance_history),
            "samples": len(self.performance_history),
        }
