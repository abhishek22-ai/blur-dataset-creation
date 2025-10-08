"""
Blur Cache

Specialized caching for blur computation results and intermediate calculations.
"""

import hashlib
import json
from typing import Any, Dict, Optional

import numpy as np

from .cache_manager import CacheManager


class BlurCache:
    """
    Specialized cache for blur operations.

    Handles caching of blur computation results, kernel calculations,
    and intermediate processing steps.
    """

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize blur cache.

        Args:
            cache_manager: Parent cache manager instance
        """
        self.cache_manager = cache_manager

    def _generate_blur_key(
        self, blur_type: str, parameters: Dict[str, Any], image_hash: str
    ) -> str:
        """Generate cache key for blur operations."""
        key_data = {"type": blur_type, "params": parameters, "image_hash": image_hash}
        key_str = json.dumps(key_data, sort_keys=True)
        return f"blur:{hashlib.sha256(key_str.encode()).hexdigest()}"

    def _generate_kernel_key(self, kernel_type: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for kernel calculations."""
        key_data = {"kernel_type": kernel_type, "params": parameters}
        key_str = json.dumps(key_data, sort_keys=True)
        return f"kernel:{hashlib.sha256(key_str.encode()).hexdigest()}"

    def _compute_image_hash(self, image: np.ndarray) -> str:
        """Compute hash of image for caching."""
        # Use image shape and mean as a simple hash
        # For production, consider using perceptual hashing
        if len(image.shape) == 3:
            # For color images, use mean of each channel
            means = [float(np.mean(image[:, :, i])) for i in range(image.shape[2])]
        else:
            # For grayscale images
            means = [float(np.mean(image))]

        hash_data = {"shape": image.shape, "means": means, "dtype": str(image.dtype)}

        hash_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()

    def get_blur_result(
        self, blur_type: str, parameters: Dict[str, Any], image: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Get cached blur result.

        Args:
            blur_type: Type of blur effect
            parameters: Blur parameters
            image: Input image

        Returns:
            Cached blur result or None if not found
        """
        image_hash = self._compute_image_hash(image)
        key = self._generate_blur_key(blur_type, parameters, image_hash)
        return self.cache_manager.get(key)

    def cache_blur_result(
        self,
        blur_type: str,
        parameters: Dict[str, Any],
        image: np.ndarray,
        result: np.ndarray,
    ):
        """
        Cache blur computation result.

        Args:
            blur_type: Type of blur effect
            parameters: Blur parameters
            image: Input image
            result: Blur result
        """
        image_hash = self._compute_image_hash(image)
        key = self._generate_blur_key(blur_type, parameters, image_hash)
        size_bytes = result.nbytes if hasattr(result, "nbytes") else 0
        self.cache_manager.put(
            key, result, size_bytes=size_bytes, ttl=7200
        )  # 2 hour TTL

    def get_cached_kernel(
        self, kernel_type: str, parameters: Dict[str, Any]
    ) -> Optional[np.ndarray]:
        """
        Get cached kernel.

        Args:
            kernel_type: Type of kernel
            parameters: Kernel parameters

        Returns:
            Cached kernel or None if not found
        """
        key = self._generate_kernel_key(kernel_type, parameters)
        return self.cache_manager.get(key)

    def cache_kernel(
        self, kernel_type: str, parameters: Dict[str, Any], kernel: np.ndarray
    ):
        """
        Cache computed kernel.

        Args:
            kernel_type: Type of kernel
            parameters: Kernel parameters
            kernel: Computed kernel
        """
        key = self._generate_kernel_key(kernel_type, parameters)
        size_bytes = kernel.nbytes if hasattr(kernel, "nbytes") else 0
        self.cache_manager.put(
            key, kernel, size_bytes=size_bytes, ttl=86400
        )  # 24 hour TTL

    def compute_blur_cached(
        self, blur_type: str, parameters: Dict[str, Any], image: np.ndarray, blur_func
    ) -> np.ndarray:
        """
        Compute blur with caching.

        Args:
            blur_type: Type of blur effect
            parameters: Blur parameters
            image: Input image
            blur_func: Function that computes the blur

        Returns:
            Blurred image
        """
        # Check cache first
        cached_result = self.get_blur_result(blur_type, parameters, image)
        if cached_result is not None:
            return cached_result

        # Compute blur
        result = blur_func(image, **parameters)

        # Cache the result
        self.cache_blur_result(blur_type, parameters, image, result)

        return result

    def compute_kernel_cached(
        self, kernel_type: str, parameters: Dict[str, Any], kernel_func
    ) -> np.ndarray:
        """
        Compute kernel with caching.

        Args:
            kernel_type: Type of kernel
            parameters: Kernel parameters
            kernel_func: Function that computes the kernel

        Returns:
            Computed kernel
        """
        # Check cache first
        cached_kernel = self.get_cached_kernel(kernel_type, parameters)
        if cached_kernel is not None:
            return cached_kernel

        # Compute kernel
        kernel = kernel_func(**parameters)

        # Cache the kernel
        self.cache_kernel(kernel_type, parameters, kernel)

        return kernel

    def clear_blur_cache(self, blur_type: Optional[str] = None):
        """
        Clear blur cache entries.

        Args:
            blur_type: Specific blur type to clear, or None for all
        """
        keys_to_remove = []
        for key in self.cache_manager._cache.keys():
            if key.startswith("blur:"):
                if blur_type is None:
                    keys_to_remove.append(key)
                else:
                    # Check if this key matches the blur type
                    # This is a simplified check - in practice you might want
                    # more sophisticated key parsing
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            self.cache_manager._cache.pop(key, None)

    def clear_kernel_cache(self):
        """Clear all kernel cache entries."""
        keys_to_remove = [
            key for key in self.cache_manager._cache.keys() if key.startswith("kernel:")
        ]
        for key in keys_to_remove:
            self.cache_manager._cache.pop(key, None)

    def get_cache_info(self) -> Dict[str, Any]:
        """Get blur cache statistics."""
        blur_keys = [
            key for key in self.cache_manager._cache.keys() if key.startswith("blur:")
        ]
        kernel_keys = [
            key for key in self.cache_manager._cache.keys() if key.startswith("kernel:")
        ]

        blur_size = sum(
            entry.size_bytes
            for key, entry in self.cache_manager._cache.items()
            if key.startswith("blur:")
        )
        kernel_size = sum(
            entry.size_bytes
            for key, entry in self.cache_manager._cache.items()
            if key.startswith("kernel:")
        )

        return {
            "cached_blur_results": len(blur_keys),
            "cached_kernels": len(kernel_keys),
            "blur_cache_size_bytes": blur_size,
            "kernel_cache_size_bytes": kernel_size,
            "blur_cache_size_mb": blur_size / (1024 * 1024),
            "kernel_cache_size_mb": kernel_size / (1024 * 1024),
        }

    def preload_common_kernels(self):
        """Preload commonly used kernels into cache."""
        # This could be extended to preload standard kernels
        # like common Gaussian kernels, etc.
        pass
