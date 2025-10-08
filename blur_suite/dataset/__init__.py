"""
Blur Suite Dataset Creation Module.

This module provides comprehensive functionality for creating blurred document
image datasets with parallel processing, batch operations, and organized output.

Main Components:
- DatasetCreator: Main orchestrator for dataset creation
- ProcessingPipeline: Coordinates blur application workflow
- BatchProcessor: Handles parallel processing of large datasets
- OutputOrganizer: Manages directory structure and file naming
- MetadataCollector: Tracks dataset statistics and processing info

Example Usage:
    from blur_suite.dataset import DatasetCreator

    # Create dataset from configuration
    creator = DatasetCreator("./output_dataset")
    success = creator.create_from_config("dataset_config.json")

    # Or create sample configuration first
    creator.create_sample_configuration("./input_images", "config.json")
"""

from .batch import AdaptiveBatchProcessor, BatchConfig, BatchProcessor, BatchResult
from .creator import DatasetCreator
from .metadata import DatasetQualityMetrics, MetadataCollector, ProcessingStats
from .output import NamingPattern, OutputDirectory, OutputOrganizer
from .pipeline import ProcessingPipeline
from .utils import (
    ConfigurationManager,
    ImageValidator,
    PathManager,
    PerformanceMonitor,
    SystemInfo,
    calculate_image_stats,
    format_bytes,
    format_time,
)

__version__ = "1.0.0"
__author__ = "Blur Suite SDK"
__description__ = "Dataset creation tools for blurred document images"

__all__ = [
    # Main classes
    "DatasetCreator",
    "ProcessingPipeline",
    "BatchProcessor",
    "AdaptiveBatchProcessor",
    "OutputOrganizer",
    "MetadataCollector",
    # Supporting classes
    "BatchConfig",
    "BatchResult",
    "ProcessingStats",
    "DatasetQualityMetrics",
    "NamingPattern",
    "OutputDirectory",
    # Utility classes
    "ImageValidator",
    "PathManager",
    "ConfigurationManager",
    "PerformanceMonitor",
    "SystemInfo",
    # Utility functions
    "format_time",
    "format_bytes",
    "calculate_image_stats",
]
