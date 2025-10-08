"""
Dataset metadata collection and statistics.

This module provides functionality for collecting and managing metadata
about dataset creation processes, including processing statistics,
error tracking, and quality metrics.
"""

import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


from .utils import format_time

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Statistics for a single image processing operation."""

    image_path: str
    blur_type: str
    parameters: Dict[str, Any]
    processing_time_ms: float
    original_size: Tuple[int, int]
    result_size: Tuple[int, int]
    success: bool
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "image_path": self.image_path,
            "blur_type": self.blur_type,
            "parameters": self.parameters,
            "processing_time_ms": self.processing_time_ms,
            "original_size": self.original_size,
            "result_size": self.result_size,
            "success": self.success,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


@dataclass
class DatasetQualityMetrics:
    """Quality metrics for the dataset."""

    total_images: int = 0
    successful_images: int = 0
    failed_images: int = 0
    average_processing_time_ms: float = 0.0
    total_processing_time_ms: float = 0.0
    blur_type_distribution: Dict[str, int] = field(default_factory=dict)
    parameter_ranges: Dict[str, Dict[str, float]] = field(default_factory=dict)
    error_types: Dict[str, int] = field(default_factory=dict)
    warning_count: int = 0

    def calculate_derived_metrics(self):
        """Calculate derived metrics like success rate."""
        if self.total_images > 0:
            self.success_rate = self.successful_images / self.total_images
        else:
            self.success_rate = 0.0

        if self.successful_images > 0:
            self.average_processing_time_ms = (
                self.total_processing_time_ms / self.successful_images
            )
        else:
            self.average_processing_time_ms = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        self.calculate_derived_metrics()
        return {
            "total_images": self.total_images,
            "successful_images": self.successful_images,
            "failed_images": self.failed_images,
            "success_rate": self.success_rate,
            "average_processing_time_ms": self.average_processing_time_ms,
            "total_processing_time_ms": self.total_processing_time_ms,
            "blur_type_distribution": self.blur_type_distribution,
            "parameter_ranges": self.parameter_ranges,
            "error_types": self.error_types,
            "warning_count": self.warning_count,
        }


class MetadataCollector:
    """
    Collects and manages metadata for dataset creation processes.

    Tracks processing statistics, errors, warnings, and quality metrics
    for comprehensive dataset documentation.
    """

    def __init__(self):
        """Initialize metadata collector."""
        self.processing_stats: List[ProcessingStats] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.custom_metadata: Dict[str, Any] = {}

    def start_collection(self):
        """Start collecting metadata."""
        self.start_time = time.time()
        logger.info("Started metadata collection")

    def stop_collection(self):
        """Stop collecting metadata."""
        self.end_time = time.time()
        logger.info("Stopped metadata collection")

    def record_processing(
        self,
        image_path: str,
        blur_type: str,
        parameters: Dict[str, Any],
        processing_time_ms: float,
        original_size: Tuple[int, int],
        result_size: Tuple[int, int],
        success: bool,
        error_message: Optional[str] = None,
        warnings: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Record processing statistics for an image.

        Args:
            image_path: Path to the processed image
            blur_type: Type of blur applied
            parameters: Blur parameters used
            processing_time_ms: Processing time in milliseconds
            original_size: Original image dimensions
            result_size: Result image dimensions
            success: Whether processing was successful
            error_message: Error message if processing failed
            warnings: List of warning messages
            metadata: Additional metadata
        """
        stats = ProcessingStats(
            image_path=image_path,
            blur_type=blur_type,
            parameters=parameters,
            processing_time_ms=processing_time_ms,
            original_size=original_size,
            result_size=result_size,
            success=success,
            error_message=error_message,
            warnings=warnings or [],
            metadata=metadata or {},
        )

        self.processing_stats.append(stats)

        if not success and error_message:
            self.errors.append(
                {
                    "image_path": image_path,
                    "error_message": error_message,
                    "timestamp": time.time(),
                }
            )

        if warnings:
            self.warnings.extend(
                [
                    {
                        "image_path": image_path,
                        "warning": warning,
                        "timestamp": time.time(),
                    }
                    for warning in warnings
                ]
            )

        logger.debug(f"Recorded processing stats for {Path(image_path).name}")

    def add_custom_metadata(self, key: str, value: Any):
        """
        Add custom metadata.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.custom_metadata[key] = value
        logger.debug(f"Added custom metadata: {key}")

    def get_quality_metrics(self) -> DatasetQualityMetrics:
        """
        Calculate quality metrics from collected data.

        Returns:
            DatasetQualityMetrics object with calculated metrics
        """
        metrics = DatasetQualityMetrics()

        if not self.processing_stats:
            return metrics

        metrics.total_images = len(self.processing_stats)

        # Count successes and failures
        successful_stats = [s for s in self.processing_stats if s.success]
        failed_stats = [s for s in self.processing_stats if not s.success]

        metrics.successful_images = len(successful_stats)
        metrics.failed_images = len(failed_stats)

        # Calculate processing times
        if successful_stats:
            metrics.total_processing_time_ms = sum(
                s.processing_time_ms for s in successful_stats
            )

        # Blur type distribution
        blur_types = defaultdict(int)
        for stats in self.processing_stats:
            blur_types[stats.blur_type] += 1
        metrics.blur_type_distribution = dict(blur_types)

        # Parameter ranges
        parameter_ranges = defaultdict(
            lambda: {"min": float("inf"), "max": float("-inf")}
        )

        for stats in successful_stats:
            for param_name, param_value in stats.parameters.items():
                if isinstance(param_value, (int, float)):
                    param_range = parameter_ranges[param_name]
                    param_range["min"] = min(param_range["min"], param_value)
                    param_range["max"] = max(param_range["max"], param_value)

        metrics.parameter_ranges = {
            k: {"min": v["min"], "max": v["max"]}
            for k, v in parameter_ranges.items()
            if v["min"] != float("inf") and v["max"] != float("-inf")
        }

        # Error types
        error_types = defaultdict(int)
        for stats in failed_stats:
            if stats.error_message:
                # Extract error type (first word of error message)
                error_type = (
                    stats.error_message.split()[0] if stats.error_message else "Unknown"
                )
                error_types[error_type] += 1
        metrics.error_types = dict(error_types)

        # Warning count
        metrics.warning_count = sum(
            len(stats.warnings) for stats in self.processing_stats
        )

        return metrics

    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the processing operation.

        Returns:
            Dictionary with processing summary
        """
        quality_metrics = self.get_quality_metrics()

        total_time_ms = 0.0
        if self.start_time and self.end_time:
            total_time_ms = (self.end_time - self.start_time) * 1000

        return {
            "metadata": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat()
                if self.start_time
                else None,
                "end_time": datetime.fromtimestamp(self.end_time).isoformat()
                if self.end_time
                else None,
                "total_duration_ms": total_time_ms,
                "custom_metadata": self.custom_metadata,
            },
            "quality_metrics": quality_metrics.to_dict(),
            "errors": self.errors,
            "warnings": self.warnings,
            "processing_count": len(self.processing_stats),
        }

    def save_metadata(self, output_path: Union[str, Path]) -> bool:
        """
        Save metadata to JSON file.

        Args:
            output_path: Path where to save metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            summary = self.get_processing_summary()

            with open(path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            logger.info(f"Metadata saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save metadata to {path}: {str(e)}")
            return False

    def load_metadata(self, metadata_path: Union[str, Path]) -> bool:
        """
        Load metadata from JSON file.

        Args:
            metadata_path: Path to metadata file

        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(metadata_path)

            if not path.exists():
                logger.error(f"Metadata file not found: {path}")
                return False

            with open(path, "r", encoding="utf-8") as f:
                json.load(f)

            logger.info(f"Metadata loaded from {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load metadata from {path}: {str(e)}")
            return False

    def generate_report(self) -> str:
        """
        Generate a human-readable report of the dataset creation.

        Returns:
            Formatted report string
        """
        summary = self.get_processing_summary()
        quality_metrics = summary["quality_metrics"]

        lines = []
        lines.append("Dataset Creation Report")
        lines.append("=" * 50)
        lines.append("")

        # Metadata section
        metadata = summary["metadata"]
        lines.append("PROCESSING METADATA:")
        if metadata["start_time"]:
            lines.append(f"  Start Time: {metadata['start_time']}")
        if metadata["end_time"]:
            lines.append(f"  End Time: {metadata['end_time']}")
        if metadata["total_duration_ms"]:
            lines.append(
                f"  Total Duration: {format_time(metadata['total_duration_ms'] / 1000)}"
            )
        lines.append("")

        # Quality metrics
        lines.append("QUALITY METRICS:")
        lines.append(f"  Total Images: {quality_metrics['total_images']}")
        lines.append(f"  Successful: {quality_metrics['successful_images']}")
        lines.append(f"  Failed: {quality_metrics['failed_images']}")
        lines.append(f"  Success Rate: {quality_metrics['success_rate']:.1%}")

        if quality_metrics["successful_images"] > 0:
            avg_time = quality_metrics["average_processing_time_ms"]
            lines.append(f"  Average Processing Time: {format_time(avg_time / 1000)}")

        lines.append("")

        # Blur type distribution
        if quality_metrics["blur_type_distribution"]:
            lines.append("BLUR TYPE DISTRIBUTION:")
            for blur_type, count in quality_metrics["blur_type_distribution"].items():
                percentage = (count / quality_metrics["total_images"]) * 100
                lines.append(f"  {blur_type}: {count} ({percentage:.1f}%)")
            lines.append("")

        # Parameter ranges
        if quality_metrics["parameter_ranges"]:
            lines.append("PARAMETER RANGES:")
            for param_name, param_range in quality_metrics["parameter_ranges"].items():
                lines.append(
                    f"  {param_name}: {param_range['min']:.2f} - {param_range['max']:.2f}"
                )
            lines.append("")

        # Errors and warnings
        if summary["errors"]:
            lines.append("ERRORS:")
            for error in summary["errors"][:10]:  # Show first 10 errors
                lines.append(
                    f"  {Path(error['image_path']).name}: {error['error_message']}"
                )
            if len(summary["errors"]) > 10:
                lines.append(f"  ... and {len(summary['errors']) - 10} more errors")
            lines.append("")

        if summary["warnings"]:
            lines.append("WARNINGS:")
            for warning in summary["warnings"][:10]:  # Show first 10 warnings
                lines.append(
                    f"  {Path(warning['image_path']).name}: {warning['warning']}"
                )
            if len(summary["warnings"]) > 10:
                lines.append(f"  ... and {len(summary['warnings']) - 10} more warnings")
            lines.append("")

        return "\n".join(lines)

    def save_report(self, output_path: Union[str, Path]) -> bool:
        """
        Save human-readable report to file.

        Args:
            output_path: Path where to save report

        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            report = self.generate_report()

            with open(path, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info(f"Report saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save report to {path}: {str(e)}")
            return False

    def export_statistics(self, output_path: Union[str, Path]) -> bool:
        """
        Export detailed statistics to JSON file.

        Args:
            output_path: Path where to save statistics

        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Create detailed statistics
            stats = {
                "summary": self.get_processing_summary(),
                "detailed_stats": [stat.to_dict() for stat in self.processing_stats],
                "export_timestamp": datetime.now().isoformat(),
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

            logger.info(f"Statistics exported to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export statistics to {path}: {str(e)}")
            return False
