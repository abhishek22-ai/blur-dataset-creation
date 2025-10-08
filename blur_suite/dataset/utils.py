"""
Utility functions for dataset operations.

This module provides common utility functions used throughout the dataset
creation pipeline, including image validation, path management, and
performance monitoring.
"""

import json
import logging
import os
import platform
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImageValidator:
    """Utility class for image validation and format conversion."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    SUPPORTED_FORMATS = ["JPEG", "PNG", "BMP", "TIFF"]

    @staticmethod
    def is_image_file(file_path: Union[str, Path]) -> bool:
        """
        Check if a file is a supported image format.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file is a supported image format
        """
        path = Path(file_path)
        return path.suffix.lower() in ImageValidator.SUPPORTED_EXTENSIONS

    @staticmethod
    def validate_image(image: np.ndarray) -> Tuple[bool, str]:
        """
        Validate an image array.

        Args:
            image: Image array to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(image, np.ndarray):
            return False, "Image must be a numpy array"

        if image.size == 0:
            return False, "Image cannot be empty"

        if len(image.shape) not in [2, 3]:
            return (
                False,
                f"Image must be 2D (grayscale) or 3D (color), got {len(image.shape)}D",
            )

        if image.shape[0] == 0 or image.shape[1] == 0:
            return False, "Image dimensions cannot be zero"

        return True, ""

    @staticmethod
    def load_image(image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        Load an image from file path.

        Args:
            image_path: Path to the image file

        Returns:
            Loaded image array or None if loading fails
        """
        path = Path(image_path)

        if not path.exists():
            logger.error(f"Image file not found: {path}")
            return None

        if not ImageValidator.is_image_file(path):
            logger.error(f"Unsupported image format: {path.suffix}")
            return None

        try:
            image = cv2.imread(str(path))
            if image is None:
                logger.error(f"Failed to load image: {path}")
                return None

            # Convert BGR to RGB
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            return image

        except Exception as e:
            logger.error(f"Error loading image {path}: {str(e)}")
            return None

    @staticmethod
    def save_image(
        image: np.ndarray, output_path: Union[str, Path], quality: int = 95
    ) -> bool:
        """
        Save an image to file path.

        Args:
            image: Image array to save
            output_path: Path where to save the image
            quality: JPEG quality (0-100)

        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            # Convert RGB to BGR for OpenCV
            if len(image.shape) == 3:
                save_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            else:
                save_image = image

            # Determine format from extension
            ext = path.suffix.lower()

            if ext in [".jpg", ".jpeg"]:
                success = cv2.imwrite(
                    str(path), save_image, [cv2.IMWRITE_JPEG_QUALITY, quality]
                )
            else:
                success = cv2.imwrite(str(path), save_image)

            if not success:
                logger.error(f"Failed to save image: {path}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error saving image to {path}: {str(e)}")
            return False


class PathManager:
    """Utility class for path and directory management."""

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> bool:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            path: Directory path to create

        Returns:
            True if directory exists or was created successfully
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {str(e)}")
            return False

    @staticmethod
    def find_images(directory: Union[str, Path], recursive: bool = True) -> List[Path]:
        """
        Find all image files in a directory.

        Args:
            directory: Directory to search
            recursive: Whether to search subdirectories

        Returns:
            List of paths to image files
        """
        directory = Path(directory)

        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            return []

        pattern = "**/*" if recursive else "*"
        image_paths = []

        for file_path in directory.glob(pattern):
            if file_path.is_file() and ImageValidator.is_image_file(file_path):
                image_paths.append(file_path)

        return sorted(image_paths)

    @staticmethod
    def get_relative_path(
        base_path: Union[str, Path], target_path: Union[str, Path]
    ) -> Path:
        """
        Get relative path from base to target.

        Args:
            base_path: Base directory
            target_path: Target path

        Returns:
            Relative path from base to target
        """
        return Path(target_path).relative_to(Path(base_path))


class ConfigurationManager:
    """Utility class for configuration file management."""

    @staticmethod
    def load_config(config_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary or None if loading fails
        """
        path = Path(config_path)

        if not path.exists():
            logger.error(f"Configuration file not found: {path}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)

            logger.info(f"Configuration loaded from {path}")
            return config

        except Exception as e:
            logger.error(f"Error loading configuration {path}: {str(e)}")
            return None

    @staticmethod
    def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> bool:
        """
        Save configuration to JSON file.

        Args:
            config: Configuration dictionary to save
            config_path: Path where to save configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(config_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Error saving configuration to {path}: {str(e)}")
            return False

    @staticmethod
    def validate_config_structure(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration file structure.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required sections
        required_sections = ["metadata", "image_configurations"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")

        # Validate image configurations
        if "image_configurations" in config:
            image_configs = config["image_configurations"]

            if not isinstance(image_configs, dict):
                errors.append("image_configurations must be a dictionary")
            else:
                for image_path, img_config in image_configs.items():
                    if not isinstance(img_config, dict):
                        errors.append(f"Invalid configuration for {image_path}")
                        continue

                    # Check required fields
                    if "blur_type" not in img_config:
                        errors.append(f"Missing blur_type for {image_path}")

                    if "parameters" not in img_config:
                        errors.append(f"Missing parameters for {image_path}")

        return len(errors) == 0, errors


class PerformanceMonitor:
    """Utility class for performance monitoring and timing."""

    def __init__(self):
        """Initialize performance monitor."""
        self.start_time = None
        self.end_time = None
        self.lap_times = {}

    def start(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def stop(self) -> float:
        """
        Stop timing and return elapsed time.

        Returns:
            Elapsed time in seconds
        """
        self.end_time = time.time()
        return self.end_time - (self.start_time or self.end_time)

    def lap(self, name: str) -> float:
        """
        Record a lap time.

        Args:
            name: Name of the lap

        Returns:
            Current elapsed time in seconds
        """
        current_time = time.time()
        elapsed = current_time - (self.start_time or current_time)
        self.lap_times[name] = elapsed
        return elapsed

    def get_elapsed(self) -> float:
        """
        Get current elapsed time.

        Returns:
            Elapsed time in seconds
        """
        current_time = time.time()
        return current_time - (self.start_time or current_time)

    def get_lap_time(self, name: str) -> Optional[float]:
        """
        Get lap time by name.

        Args:
            name: Name of the lap

        Returns:
            Lap time in seconds or None if not found
        """
        return self.lap_times.get(name)

    def reset(self):
        """Reset all timing data."""
        self.start_time = None
        self.end_time = None
        self.lap_times.clear()


class SystemInfo:
    """Utility class for system information and resource monitoring."""

    @staticmethod
    def get_cpu_count() -> int:
        """Get the number of CPU cores."""
        return os.cpu_count() or 1

    @staticmethod
    def get_memory_info() -> Dict[str, float]:
        """
        Get memory information.

        Returns:
            Dictionary with memory information in GB
        """
        try:
            if platform.system() == "Linux":
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                total = int(meminfo.split("MemTotal:")[1].split()[0]) / (1024**2)  # GB
                available = int(meminfo.split("MemAvailable:")[1].split()[0]) / (
                    1024**2
                )  # GB
                return {"total_gb": total, "available_gb": available}
            else:
                # Fallback for other systems
                return {"total_gb": 8.0, "available_gb": 4.0}
        except:
            return {"total_gb": 8.0, "available_gb": 4.0}

    @staticmethod
    def get_optimal_worker_count() -> int:
        """
        Get optimal number of worker processes based on system resources.

        Returns:
            Recommended number of worker processes
        """
        cpu_count = SystemInfo.get_cpu_count()
        memory_info = SystemInfo.get_memory_info()

        # Use CPU count but limit based on memory
        # Assume each worker needs ~1GB of memory
        memory_based_limit = int(memory_info["available_gb"])

        return min(cpu_count, memory_based_limit, 8)  # Cap at 8 workers


def format_time(seconds: float) -> str:
    """
    Format time in seconds to human-readable string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.0f}s"


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human-readable string.

    Args:
        bytes_value: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}TB"


def calculate_image_stats(image: np.ndarray) -> Dict[str, Any]:
    """
    Calculate basic statistics for an image.

    Args:
        image: Image array

    Returns:
        Dictionary with image statistics
    """
    if len(image.shape) == 3:
        # Color image
        channels = image.shape[2]
        stats = {
            "shape": image.shape,
            "dtype": str(image.dtype),
            "channels": channels,
            "size_bytes": image.nbytes,
        }

        # Per-channel statistics
        for c in range(channels):
            channel_data = image[:, :, c].flatten()
            stats[f"channel_{c}_mean"] = float(np.mean(channel_data))
            stats[f"channel_{c}_std"] = float(np.std(channel_data))
            stats[f"channel_{c}_min"] = float(np.min(channel_data))
            stats[f"channel_{c}_max"] = float(np.max(channel_data))
    else:
        # Grayscale image
        flat = image.flatten()
        stats = {
            "shape": image.shape,
            "dtype": str(image.dtype),
            "channels": 1,
            "size_bytes": image.nbytes,
            "mean": float(np.mean(flat)),
            "std": float(np.std(flat)),
            "min": float(np.min(flat)),
            "max": float(np.max(flat)),
        }

    return stats
