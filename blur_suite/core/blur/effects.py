"""
Concrete blur effect implementations.

This module contains all the specific blur effect implementations,
each extending the base blur effect class with their own algorithms
and parameter definitions.
"""

from typing import Dict

import cv2
import numpy as np

from .base import BaseBlurEffect, BlurType, Parameter


class GaussianBlur(BaseBlurEffect):
    """
    Gaussian blur effect using Gaussian kernel convolution.

    Applies a Gaussian blur with configurable kernel size and sigma values.
    Uses OpenCV's GaussianBlur when available, with fallback implementation.
    """

    def __init__(self):
        """Initialize Gaussian blur effect."""
        super().__init__(BlurType.GAUSSIAN)

    def _validate_requirements(self):
        """Validate OpenCV availability for optimal performance."""
        super()._validate_requirements()
        if not self._opencv_available:
            print("Warning: OpenCV not available, using slower fallback implementation")

    def _define_parameters(self) -> Dict[str, Parameter]:
        """Define Gaussian blur parameters."""
        return {
            "kernel_size": Parameter(
                name="kernel_size",
                value=5,
                param_type=int,
                min_value=3,
                max_value=21,
                description="Size of the Gaussian kernel (must be odd, will be adjusted if even)",
            ),
            "sigma_x": Parameter(
                name="sigma_x",
                value=1.0,
                param_type=float,
                min_value=0.5,
                max_value=5.0,
                description="Standard deviation in X direction",
            ),
            "sigma_y": Parameter(
                name="sigma_y",
                value=1.0,
                param_type=float,
                min_value=0.5,
                max_value=5.0,
                description="Standard deviation in Y direction (0 = same as sigma_x)",
            ),
        }

    def _apply_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Apply Gaussian blur to the image.

        Args:
            image: Input image

        Returns:
            Gaussian blurred image
        """
        kernel_size = self.get_parameter("kernel_size")
        sigma_x = self.get_parameter("sigma_x")
        sigma_y = self.get_parameter("sigma_y")

        # Ensure kernel size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1
            self.set_parameter("kernel_size", kernel_size)

        # Use OpenCV if available
        if self._opencv_available:
            try:
                # Convert to uint8 for OpenCV if needed
                if image.dtype != np.uint8:
                    input_image = (
                        (image * 255).astype(np.uint8)
                        if image.max() <= 1.0
                        else image.astype(np.uint8)
                    )
                else:
                    input_image = image

                # Apply Gaussian blur
                if sigma_y == 0:
                    sigma_y = sigma_x

                blurred = cv2.GaussianBlur(
                    input_image, (kernel_size, kernel_size), sigma_x, sigma_y
                )

                # Convert back to original format
                if image.dtype != np.uint8:
                    blurred = (
                        blurred.astype(np.float32) / 255.0
                        if image.max() <= 1.0
                        else blurred.astype(image.dtype)
                    )

                return blurred
            except Exception as e:
                print(f"OpenCV Gaussian blur failed: {e}, using fallback")

        # Fallback implementation using numpy
        return self._gaussian_blur_fallback(image, kernel_size, sigma_x, sigma_y)

    def _gaussian_blur_fallback(
        self, image: np.ndarray, kernel_size: int, sigma_x: float, sigma_y: float
    ) -> np.ndarray:
        """
        Fallback Gaussian blur implementation using numpy.

        Args:
            image: Input image
            kernel_size: Size of the kernel
            sigma_x: Standard deviation in X direction
            sigma_y: Standard deviation in Y direction

        Returns:
            Gaussian blurred image
        """
        # Create Gaussian kernel
        kernel = self._create_gaussian_kernel(kernel_size, sigma_x, sigma_y)

        # Apply convolution
        if len(image.shape) == 2:
            # Grayscale
            return self._convolve_2d(image, kernel)
        else:
            # Color image - apply to each channel
            result = np.zeros_like(image, dtype=np.float32)
            for channel in range(image.shape[2]):
                result[:, :, channel] = self._convolve_2d(image[:, :, channel], kernel)
            return result

    def _create_gaussian_kernel(
        self, size: int, sigma_x: float, sigma_y: float
    ) -> np.ndarray:
        """Create Gaussian kernel."""
        ksize_half = (size - 1) * 0.5
        x = np.linspace(-ksize_half, ksize_half, size)
        if sigma_y == 0:
            sigma_y = sigma_x

        # Create 2D Gaussian kernel
        kernel_2d = np.zeros((size, size))
        for i in range(size):
            for j in range(size):
                kernel_2d[i, j] = np.exp(
                    -(x[i] ** 2 + x[j] ** 2) / (2 * sigma_x * sigma_y)
                )

        # Normalize
        kernel_2d = kernel_2d / np.sum(kernel_2d)
        return kernel_2d

    def _convolve_2d(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Apply 2D convolution with padding."""
        kernel_size = kernel.shape[0]
        pad_size = kernel_size // 2

        # Pad image
        padded = np.pad(image, pad_size, mode="edge")

        # Apply convolution
        result = np.zeros_like(image, dtype=np.float32)
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                result[i, j] = np.sum(
                    padded[i : i + kernel_size, j : j + kernel_size] * kernel
                )

        return result


class MotionBlur(BaseBlurEffect):
    """
    Motion blur effect simulating camera or object movement.

    Creates a blur effect in a specific direction with configurable
    angle and length parameters.
    """

    def __init__(self):
        """Initialize motion blur effect."""
        super().__init__(BlurType.MOTION)

    def _define_parameters(self) -> Dict[str, Parameter]:
        """Define motion blur parameters."""
        return {
            "angle": Parameter(
                name="angle",
                value=0.0,
                param_type=float,
                min_value=0.0,
                max_value=180.0,
                description="Direction of motion in degrees (0 = horizontal right)",
            ),
            "length": Parameter(
                name="length",
                value=10,
                param_type=int,
                min_value=1,
                max_value=50,
                description="Length of motion blur in pixels",
            ),
        }

    def _apply_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Apply motion blur to the image.

        Args:
            image: Input image

        Returns:
            Motion blurred image
        """
        angle = self.get_parameter("angle")
        length = self.get_parameter("length")

        # Use OpenCV if available
        if self._opencv_available:
            try:
                # Convert to uint8 for OpenCV if needed
                if image.dtype != np.uint8:
                    input_image = (
                        (image * 255).astype(np.uint8)
                        if image.max() <= 1.0
                        else image.astype(np.uint8)
                    )
                else:
                    input_image = image

                # Create motion blur kernel
                kernel = self._create_motion_kernel(length, angle)

                # Apply filter
                blurred = cv2.filter2D(input_image, -1, kernel)

                # Convert back to original format
                if image.dtype != np.uint8:
                    blurred = (
                        blurred.astype(np.float32) / 255.0
                        if image.max() <= 1.0
                        else blurred.astype(image.dtype)
                    )

                return blurred
            except Exception as e:
                print(f"OpenCV motion blur failed: {e}, using fallback")

        # Fallback implementation
        return self._motion_blur_fallback(image, length, angle)

    def _create_motion_kernel(self, length: int, angle: float) -> np.ndarray:
        """Create motion blur kernel."""
        # Convert angle to radians
        angle_rad = np.deg2rad(angle)

        # Calculate kernel size (odd number)
        kernel_size = max(3, length * 2 + 1)
        if kernel_size % 2 == 0:
            kernel_size += 1

        # Create kernel
        kernel = np.zeros((kernel_size, kernel_size))

        # Calculate center
        center = kernel_size // 2

        # Calculate line points
        for i in range(-length, length + 1):
            x = int(center + i * np.cos(angle_rad))
            y = int(center + i * np.sin(angle_rad))

            if 0 <= x < kernel_size and 0 <= y < kernel_size:
                kernel[y, x] = 1

        # Normalize kernel
        kernel = kernel / np.sum(kernel)
        return kernel

    def _motion_blur_fallback(
        self, image: np.ndarray, length: int, angle: float
    ) -> np.ndarray:
        """Fallback motion blur implementation."""
        kernel = self._create_motion_kernel(length, angle)

        if len(image.shape) == 2:
            return self._convolve_2d(image, kernel)
        else:
            result = np.zeros_like(image, dtype=np.float32)
            for channel in range(image.shape[2]):
                result[:, :, channel] = self._convolve_2d(image[:, :, channel], kernel)
            return result

    def _convolve_2d(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Apply 2D convolution with padding."""
        kernel_size = kernel.shape[0]
        pad_size = kernel_size // 2

        # Pad image
        padded = np.pad(image, pad_size, mode="edge")

        # Apply convolution
        result = np.zeros_like(image, dtype=np.float32)
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                result[i, j] = np.sum(
                    padded[i : i + kernel_size, j : j + kernel_size] * kernel
                )

        return result


class DefocusBlur(BaseBlurEffect):
    """
    Defocus blur effect simulating out-of-focus areas.

    Creates a circular blur effect with configurable radius and strength,
    simulating the bokeh effect of camera defocus.
    """

    def __init__(self):
        """Initialize defocus blur effect."""
        super().__init__(BlurType.DEFOCUS)

    def _define_parameters(self) -> Dict[str, Parameter]:
        """Define defocus blur parameters."""
        return {
            "radius": Parameter(
                name="radius",
                value=5,
                param_type=int,
                min_value=1,
                max_value=20,
                description="Radius of the defocus blur in pixels",
            ),
            "strength": Parameter(
                name="strength",
                value=1.0,
                param_type=float,
                min_value=0.1,
                max_value=2.0,
                description="Strength multiplier for the blur effect",
            ),
        }

    def _apply_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Apply defocus blur to the image.

        Args:
            image: Input image

        Returns:
            Defocus blurred image
        """
        radius = self.get_parameter("radius")
        strength = self.get_parameter("strength")

        # Use OpenCV if available
        if self._opencv_available:
            try:
                # Convert to uint8 for OpenCV if needed
                if image.dtype != np.uint8:
                    input_image = (
                        (image * 255).astype(np.uint8)
                        if image.max() <= 1.0
                        else image.astype(np.uint8)
                    )
                else:
                    input_image = image

                # Create disk kernel for defocus effect
                kernel_size = radius * 2 + 1
                kernel = self._create_disk_kernel(kernel_size)

                # Apply blur with strength adjustment
                blurred = cv2.filter2D(input_image, -1, kernel)

                # Apply strength multiplier
                if strength != 1.0:
                    blurred = input_image + (blurred - input_image) * strength

                # Convert back to original format
                if image.dtype != np.uint8:
                    blurred = (
                        blurred.astype(np.float32) / 255.0
                        if image.max() <= 1.0
                        else blurred.astype(image.dtype)
                    )

                return blurred
            except Exception as e:
                print(f"OpenCV defocus blur failed: {e}, using fallback")

        # Fallback implementation
        return self._defocus_blur_fallback(image, radius, strength)

    def _create_disk_kernel(self, size: int) -> np.ndarray:
        """Create a disk-shaped kernel for defocus effect."""
        kernel = np.zeros((size, size))
        center = size // 2
        radius = min(center, size - center - 1)

        for i in range(size):
            for j in range(size):
                distance = np.sqrt((i - center) ** 2 + (j - center) ** 2)
                if distance <= radius:
                    kernel[i, j] = 1

        # Normalize
        kernel = kernel / np.sum(kernel)
        return kernel

    def _defocus_blur_fallback(
        self, image: np.ndarray, radius: int, strength: float
    ) -> np.ndarray:
        """Fallback defocus blur implementation."""
        kernel_size = radius * 2 + 1
        kernel = self._create_disk_kernel(kernel_size)

        if len(image.shape) == 2:
            result = self._convolve_2d(image, kernel)
        else:
            result = np.zeros_like(image, dtype=np.float32)
            for channel in range(image.shape[2]):
                result[:, :, channel] = self._convolve_2d(image[:, :, channel], kernel)

        # Apply strength
        if strength != 1.0:
            result = image + (result - image) * strength

        return result

    def _convolve_2d(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Apply 2D convolution with padding."""
        kernel_size = kernel.shape[0]
        pad_size = kernel_size // 2

        # Pad image
        padded = np.pad(image, pad_size, mode="edge")

        # Apply convolution
        result = np.zeros_like(image, dtype=np.float32)
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                result[i, j] = np.sum(
                    padded[i : i + kernel_size, j : j + kernel_size] * kernel
                )

        return result


class AverageBlur(BaseBlurEffect):
    """
    Average blur effect using mean filtering.

    Applies a simple average blur with configurable kernel size,
    where each output pixel is the average of surrounding pixels.
    """

    def __init__(self):
        """Initialize average blur effect."""
        super().__init__(BlurType.AVERAGE)

    def _define_parameters(self) -> Dict[str, Parameter]:
        """Define average blur parameters."""
        return {
            "kernel_size": Parameter(
                name="kernel_size",
                value=5,
                param_type=int,
                min_value=3,
                max_value=15,
                description="Size of the averaging kernel (must be odd, will be adjusted if even)",
            )
        }

    def _apply_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Apply average blur to the image.

        Args:
            image: Input image

        Returns:
            Average blurred image
        """
        kernel_size = self.get_parameter("kernel_size")

        # Ensure kernel size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1
            self.set_parameter("kernel_size", kernel_size)

        # Use OpenCV if available
        if self._opencv_available:
            try:
                # Convert to uint8 for OpenCV if needed
                if image.dtype != np.uint8:
                    input_image = (
                        (image * 255).astype(np.uint8)
                        if image.max() <= 1.0
                        else image.astype(np.uint8)
                    )
                else:
                    input_image = image

                # Apply blur
                blurred = cv2.blur(input_image, (kernel_size, kernel_size))

                # Convert back to original format
                if image.dtype != np.uint8:
                    blurred = (
                        blurred.astype(np.float32) / 255.0
                        if image.max() <= 1.0
                        else blurred.astype(image.dtype)
                    )

                return blurred
            except Exception as e:
                print(f"OpenCV average blur failed: {e}, using fallback")

        # Fallback implementation
        return self._average_blur_fallback(image, kernel_size)

    def _average_blur_fallback(self, image: np.ndarray, kernel_size: int) -> np.ndarray:
        """Fallback average blur implementation."""
        # Create uniform kernel
        kernel = np.ones((kernel_size, kernel_size)) / (kernel_size * kernel_size)

        if len(image.shape) == 2:
            return self._convolve_2d(image, kernel)
        else:
            result = np.zeros_like(image, dtype=np.float32)
            for channel in range(image.shape[2]):
                result[:, :, channel] = self._convolve_2d(image[:, :, channel], kernel)
            return result

    def _convolve_2d(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """Apply 2D convolution with padding."""
        kernel_size = kernel.shape[0]
        pad_size = kernel_size // 2

        # Pad image
        padded = np.pad(image, pad_size, mode="edge")

        # Apply convolution
        result = np.zeros_like(image, dtype=np.float32)
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                result[i, j] = np.sum(
                    padded[i : i + kernel_size, j : j + kernel_size] * kernel
                )

        return result


class BilateralBlur(BaseBlurEffect):
    """
    Bilateral blur effect preserving edges.

    Applies edge-preserving smoothing using bilateral filtering,
    which reduces noise while maintaining sharp edges.
    """

    def __init__(self):
        """Initialize bilateral blur effect."""
        super().__init__(BlurType.BILATERAL)

    def _define_parameters(self) -> Dict[str, Parameter]:
        """Define bilateral blur parameters."""
        return {
            "diameter": Parameter(
                name="diameter",
                value=9,
                param_type=int,
                min_value=5,
                max_value=25,
                description="Diameter of pixel neighborhood for filtering",
            ),
            "sigma_color": Parameter(
                name="sigma_color",
                value=75.0,
                param_type=float,
                min_value=10.0,
                max_value=100.0,
                description="Filter sigma in color space",
            ),
            "sigma_space": Parameter(
                name="sigma_space",
                value=75.0,
                param_type=float,
                min_value=10.0,
                max_value=100.0,
                description="Filter sigma in coordinate space",
            ),
        }

    def _apply_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Apply bilateral blur to the image.

        Args:
            image: Input image

        Returns:
            Bilateral blurred image
        """
        diameter = self.get_parameter("diameter")
        sigma_color = self.get_parameter("sigma_color")
        sigma_space = self.get_parameter("sigma_space")

        # Use OpenCV if available (required for bilateral filter)
        if self._opencv_available:
            try:
                # Convert to uint8 for OpenCV if needed
                if image.dtype != np.uint8:
                    input_image = (
                        (image * 255).astype(np.uint8)
                        if image.max() <= 1.0
                        else image.astype(np.uint8)
                    )
                else:
                    input_image = image

                # Apply bilateral filter
                blurred = cv2.bilateralFilter(
                    input_image, diameter, sigma_color, sigma_space
                )

                # Convert back to original format
                if image.dtype != np.uint8:
                    blurred = (
                        blurred.astype(np.float32) / 255.0
                        if image.max() <= 1.0
                        else blurred.astype(image.dtype)
                    )

                return blurred
            except Exception as e:
                print(f"OpenCV bilateral blur failed: {e}, using fallback")

        # Fallback implementation using Gaussian blur approximation
        print("Warning: Bilateral filter requires OpenCV, using Gaussian approximation")
        return self._bilateral_approximation(image, diameter, sigma_color, sigma_space)

    def _bilateral_approximation(
        self, image: np.ndarray, diameter: int, sigma_color: float, sigma_space: float
    ) -> np.ndarray:
        """Approximate bilateral filter using multiple Gaussian blurs."""
        # This is a simplified approximation - real bilateral filter is more complex
        kernel_size = min(diameter, 15)  # Limit kernel size for performance

        # Use Gaussian blur as approximation
        gaussian = GaussianBlur()
        gaussian.set_parameter("kernel_size", kernel_size)
        gaussian.set_parameter("sigma_x", sigma_space / 10)  # Approximate conversion
        gaussian.set_parameter("sigma_y", sigma_space / 10)

        return gaussian.apply(image).result_image


class NoBlur(BaseBlurEffect):
    """
    No-op blur effect that returns the original image unchanged.

    Useful for testing, benchmarking, or as a placeholder effect.
    """

    def __init__(self):
        """Initialize no-blur effect."""
        super().__init__(BlurType.NO_BLUR)

    def _validate_requirements(self):
        """No special requirements for no-blur effect."""
        pass

    def _define_parameters(self) -> Dict[str, Parameter]:
        """No parameters needed for no-blur effect."""
        return {}

    def _apply_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Return the original image unchanged.

        Args:
            image: Input image

        Returns:
            Original image (unchanged)
        """
        return image.copy()
