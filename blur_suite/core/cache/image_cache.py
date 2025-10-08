"""
Image Cache

Specialized caching for image loading and preprocessing operations.
"""

import hashlib
import json
from typing import Any, Dict, Optional

import cv2
import numpy as np

from .cache_manager import CacheManager


class ImageCache:
    """
    Specialized cache for image operations.

    Handles caching of loaded images, preprocessed images,
    and intermediate processing results.
    """

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize image cache.

        Args:
            cache_manager: Parent cache manager instance
        """
        self.cache_manager = cache_manager
        self._image_formats = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}

    def _generate_image_key(
        self, image_path: str, operations: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key for image operations."""
        key_data = {"path": image_path, "operations": operations or {}}
        key_str = json.dumps(key_data, sort_keys=True)
        return f"img:{hashlib.sha256(key_str.encode()).hexdigest()}"

    def get_loaded_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Get cached loaded image.

        Args:
            image_path: Path to the image file

        Returns:
            Loaded image array or None if not cached
        """
        key = self._generate_image_key(image_path)
        return self.cache_manager.get(key)

    def cache_loaded_image(self, image_path: str, image: np.ndarray):
        """
        Cache a loaded image.

        Args:
            image_path: Path to the image file
            image: Loaded image array
        """
        key = self._generate_image_key(image_path)
        size_bytes = image.nbytes if hasattr(image, "nbytes") else 0
        self.cache_manager.put(
            key, image, size_bytes=size_bytes, ttl=3600
        )  # 1 hour TTL

    def get_processed_image(
        self, image_path: str, operations: Dict[str, Any]
    ) -> Optional[np.ndarray]:
        """
        Get cached processed image.

        Args:
            image_path: Path to the original image
            operations: Processing operations applied

        Returns:
            Processed image or None if not cached
        """
        key = self._generate_image_key(image_path, operations)
        return self.cache_manager.get(key)

    def cache_processed_image(
        self, image_path: str, operations: Dict[str, Any], result: np.ndarray
    ):
        """
        Cache a processed image.

        Args:
            image_path: Path to the original image
            operations: Processing operations applied
            result: Processed image result
        """
        key = self._generate_image_key(image_path, operations)
        size_bytes = result.nbytes if hasattr(result, "nbytes") else 0
        self.cache_manager.put(
            key, result, size_bytes=size_bytes, ttl=1800
        )  # 30 min TTL

    def load_image_cached(self, image_path: str) -> np.ndarray:
        """
        Load image with caching.

        Args:
            image_path: Path to image file

        Returns:
            Loaded image array
        """
        # Check cache first
        cached_image = self.get_loaded_image(image_path)
        if cached_image is not None:
            return cached_image

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Could not load image: {image_path}")

        # Convert BGR to RGB if needed
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Cache the loaded image
        self.cache_loaded_image(image_path, image)

        return image

    def process_image_cached(
        self, image_path: str, operations: Dict[str, Any], processor_func
    ) -> np.ndarray:
        """
        Process image with caching.

        Args:
            image_path: Path to original image
            operations: Processing operations to apply
            processor_func: Function that applies the operations

        Returns:
            Processed image
        """
        # Check cache first
        cached_result = self.get_processed_image(image_path, operations)
        if cached_result is not None:
            return cached_result

        # Load original image if needed
        image = self.load_image_cached(image_path)

        # Apply processing
        result = processor_func(image, **operations)

        # Cache the result
        self.cache_processed_image(image_path, operations, result)

        return result

    def clear_image_cache(self, image_path: Optional[str] = None):
        """
        Clear image cache entries.

        Args:
            image_path: Specific image path to clear, or None for all
        """
        if image_path:
            # Clear specific image entries
            keys_to_remove = [
                key
                for key in self.cache_manager._cache.keys()
                if key.startswith("img:") and image_path in key
            ]
            for key in keys_to_remove:
                self.cache_manager._cache.pop(key, None)
        else:
            # Clear all image entries
            keys_to_remove = [
                key
                for key in self.cache_manager._cache.keys()
                if key.startswith("img:")
            ]
            for key in keys_to_remove:
                self.cache_manager._cache.pop(key, None)

    def preload_images(self, image_paths: list):
        """
        Preload multiple images into cache.

        Args:
            image_paths: List of image paths to preload
        """
        for path in image_paths:
            try:
                self.load_image_cached(path)
            except Exception as e:
                # Log warning but continue with other images
                print(f"Warning: Could not preload image {path}: {e}")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get image cache statistics."""
        image_keys = [
            key for key in self.cache_manager._cache.keys() if key.startswith("img:")
        ]

        total_size = sum(
            entry.size_bytes
            for key, entry in self.cache_manager._cache.items()
            if key.startswith("img:")
        )

        return {
            "cached_images": len(image_keys),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
        }
