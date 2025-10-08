"""
Custom Effects Builder

Easy-to-use builder for creating custom blur effects and image processing operations.
"""

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np


class EffectType(Enum):
    """Types of custom effects."""

    BLUR = "blur"
    SHARPEN = "sharpen"
    ENHANCE = "enhance"
    FILTER = "filter"
    TRANSFORM = "transform"
    COMPOSITE = "composite"


@dataclass
class EffectStep:
    """Single step in an effect pipeline."""

    name: str
    operation: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    order: int = 0


class CustomEffectBuilder:
    """
    Builder for creating custom blur effects and image processing operations.

    Provides a fluent interface for building complex effects from
    simple operations.
    """

    def __init__(self, name: str = "custom_effect"):
        """
        Initialize custom effect builder.

        Args:
            name: Name of the custom effect
        """
        self.name = name
        self.effect_type = EffectType.BLUR
        self.description = ""
        self.version = "1.0.0"
        self.author = "Custom Effect Builder"

        # Effect pipeline
        self._steps: List[EffectStep] = []
        self._parameters: Dict[str, Any] = {}
        self._lock = threading.RLock()

        # Performance settings
        self.enable_caching = True
        self.enable_parallel = False
        self.max_workers = 4

    def set_name(self, name: str) -> "CustomEffectBuilder":
        """Set effect name."""
        self.name = name
        return self

    def set_type(self, effect_type: EffectType) -> "CustomEffectBuilder":
        """Set effect type."""
        self.effect_type = effect_type
        return self

    def set_description(self, description: str) -> "CustomEffectBuilder":
        """Set effect description."""
        self.description = description
        return self

    def set_version(self, version: str) -> "CustomEffectBuilder":
        """Set effect version."""
        self.version = version
        return self

    def set_author(self, author: str) -> "CustomEffectBuilder":
        """Set effect author."""
        self.author = author
        return self

    def add_parameter(
        self,
        name: str,
        default_value: Any,
        value_type: type = None,
        min_value: Any = None,
        max_value: Any = None,
        description: str = "",
    ) -> "CustomEffectBuilder":
        """
        Add a parameter to the effect.

        Args:
            name: Parameter name
            default_value: Default parameter value
            value_type: Parameter type
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            description: Parameter description
        """
        self._parameters[name] = {
            "default": default_value,
            "type": value_type or type(default_value),
            "min": min_value,
            "max": max_value,
            "description": description,
        }
        return self

    def add_step(
        self,
        name: str,
        operation: Callable,
        parameters: Optional[Dict[str, Any]] = None,
        order: int = 0,
    ) -> "CustomEffectBuilder":
        """
        Add a processing step to the effect.

        Args:
            name: Step name
            operation: Operation function
            parameters: Operation parameters
            order: Step execution order
        """
        step = EffectStep(
            name=name, operation=operation, parameters=parameters or {}, order=order
        )

        with self._lock:
            self._steps.append(step)

        return self

    def add_blur_step(
        self,
        kernel_size: int = 3,
        sigma: float = 1.0,
        blur_type: str = "gaussian",
        order: int = 0,
    ) -> "CustomEffectBuilder":
        """
        Add a blur step to the effect.

        Args:
            kernel_size: Size of blur kernel
            sigma: Standard deviation for Gaussian blur
            blur_type: Type of blur ('gaussian', 'box', 'median')
            order: Step execution order
        """

        def blur_operation(image, **kwargs):
            """Apply blur operation."""
            import cv2

            ks = kwargs.get("kernel_size", kernel_size)
            s = kwargs.get("sigma", sigma)
            bt = kwargs.get("blur_type", blur_type)

            if bt == "gaussian":
                return cv2.GaussianBlur(image, (ks, ks), s)
            elif bt == "box":
                return cv2.blur(image, (ks, ks))
            elif bt == "median":
                return cv2.medianBlur(image, ks)
            else:
                raise ValueError(f"Unknown blur type: {bt}")

        return self.add_step(
            name=f"blur_{blur_type}",
            operation=blur_operation,
            parameters={
                "kernel_size": kernel_size,
                "sigma": sigma,
                "blur_type": blur_type,
            },
            order=order,
        )

    def add_sharpen_step(
        self, intensity: float = 1.0, kernel_size: int = 3, order: int = 0
    ) -> "CustomEffectBuilder":
        """
        Add a sharpening step to the effect.

        Args:
            intensity: Sharpening intensity
            kernel_size: Sharpening kernel size
            order: Step execution order
        """

        def sharpen_operation(image, **kwargs):
            """Apply sharpening operation."""
            import cv2

            intensity = kwargs.get("intensity", intensity)
            kwargs.get("kernel_size", kernel_size)

            # Create sharpening kernel
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]) * intensity

            # Normalize kernel
            kernel = kernel / np.sum(np.abs(kernel))

            return cv2.filter2D(image, -1, kernel)

        return self.add_step(
            name="sharpen",
            operation=sharpen_operation,
            parameters={"intensity": intensity, "kernel_size": kernel_size},
            order=order,
        )

    def add_enhance_step(
        self, enhancement_type: str = "contrast", intensity: float = 1.0, order: int = 0
    ) -> "CustomEffectBuilder":
        """
        Add an enhancement step to the effect.

        Args:
            enhancement_type: Type of enhancement ('contrast', 'brightness', 'saturation')
            intensity: Enhancement intensity
            order: Step execution order
        """

        def enhance_operation(image, **kwargs):
            """Apply enhancement operation."""
            import cv2

            et = kwargs.get("enhancement_type", enhancement_type)
            intensity = kwargs.get("intensity", intensity)

            if et == "contrast":
                # Enhance contrast using CLAHE
                if len(image.shape) == 3:
                    # Color image
                    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(
                        clipLimit=2.0 * intensity, tileGridSize=(8, 8)
                    )
                    l = clahe.apply(l)
                    enhanced = cv2.merge([l, a, b])
                    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
                else:
                    # Grayscale image
                    clahe = cv2.createCLAHE(
                        clipLimit=2.0 * intensity, tileGridSize=(8, 8)
                    )
                    return clahe.apply(image)

            elif et == "brightness":
                # Adjust brightness
                return np.clip(image * (1.0 + intensity), 0, 255).astype(np.uint8)

            elif et == "saturation":
                # Adjust saturation (for color images)
                if len(image.shape) == 3:
                    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
                    h, s, v = cv2.split(hsv)
                    s = np.clip(s * (1.0 + intensity), 0, 255).astype(np.uint8)
                    enhanced = cv2.merge([h, s, v])
                    return cv2.cvtColor(enhanced, cv2.COLOR_HSV2RGB)

                return image

            else:
                raise ValueError(f"Unknown enhancement type: {et}")

        return self.add_step(
            name=f"enhance_{enhancement_type}",
            operation=enhance_operation,
            parameters={"enhancement_type": enhancement_type, "intensity": intensity},
            order=order,
        )

    def add_filter_step(
        self,
        filter_type: str = "edge_detection",
        intensity: float = 1.0,
        order: int = 0,
    ) -> "CustomEffectBuilder":
        """
        Add a filter step to the effect.

        Args:
            filter_type: Type of filter ('edge_detection', 'emboss', 'outline')
            intensity: Filter intensity
            order: Step execution order
        """

        def filter_operation(image, **kwargs):
            """Apply filter operation."""
            import cv2

            ft = kwargs.get("filter_type", filter_type)
            intensity = kwargs.get("intensity", intensity)

            if ft == "edge_detection":
                # Edge detection using Sobel
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                else:
                    gray = image

                # Use CV_64F for better precision, then convert to float32 for calculations
                sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3).astype(np.float32)
                sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3).astype(np.float32)
                edges = np.sqrt(sobel_x**2 + sobel_y**2)
                edges = np.uint8(np.clip(edges * intensity, 0, 255))
                return edges

            elif ft == "emboss":
                # Emboss filter
                kernel = np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]]) * intensity

                return cv2.filter2D(image, -1, kernel)

            elif ft == "outline":
                # Outline filter
                kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]]) * intensity

                return cv2.filter2D(image, -1, kernel)

            else:
                raise ValueError(f"Unknown filter type: {ft}")

        return self.add_step(
            name=f"filter_{filter_type}",
            operation=filter_operation,
            parameters={"filter_type": filter_type, "intensity": intensity},
            order=order,
        )

    def enable_caching(self, enable: bool = True) -> "CustomEffectBuilder":
        """Enable or disable result caching."""
        self.enable_caching = enable
        return self

    def enable_parallel_processing(
        self, enable: bool = True, max_workers: int = 4
    ) -> "CustomEffectBuilder":
        """
        Enable parallel processing.

        Args:
            enable: Whether to enable parallel processing
            max_workers: Maximum number of worker threads
        """
        self.enable_parallel = enable
        self.max_workers = max_workers
        return self

    def build(self) -> "CustomEffect":
        """
        Build the custom effect.

        Returns:
            Built custom effect
        """
        # Sort steps by order
        with self._lock:
            sorted_steps = sorted(self._steps, key=lambda s: s.order)

        return CustomEffect(
            name=self.name,
            effect_type=self.effect_type,
            description=self.description,
            version=self.version,
            author=self.author,
            steps=sorted_steps,
            parameters=self._parameters,
            enable_caching=self.enable_caching,
            enable_parallel=self.enable_parallel,
            max_workers=self.max_workers,
        )


class CustomEffect:
    """
    Built custom effect that can be applied to images.
    """

    def __init__(
        self,
        name: str,
        effect_type: EffectType,
        description: str,
        version: str,
        author: str,
        steps: List[EffectStep],
        parameters: Dict[str, Any],
        enable_caching: bool = True,
        enable_parallel: bool = False,
        max_workers: int = 4,
    ):
        """
        Initialize custom effect.

        Args:
            name: Effect name
            effect_type: Type of effect
            description: Effect description
            version: Effect version
            author: Effect author
            steps: Processing steps
            parameters: Effect parameters
            enable_caching: Whether to enable caching
            enable_parallel: Whether to enable parallel processing
            max_workers: Maximum worker threads
        """
        self.name = name
        self.effect_type = effect_type
        self.description = description
        self.version = version
        self.author = author
        self.steps = steps
        self.parameters = parameters
        self.enable_caching = enable_caching
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers

        # Runtime state
        self._parameter_values = {}
        self._cache = {}
        self._lock = threading.RLock()

        # Initialize default parameter values
        for param_name, param_info in parameters.items():
            self._parameter_values[param_name] = param_info["default"]

    def set_parameter(self, name: str, value: Any):
        """
        Set parameter value.

        Args:
            name: Parameter name
            value: Parameter value
        """
        if name not in self.parameters:
            raise ValueError(f"Unknown parameter: {name}")

        param_info = self.parameters[name]

        # Validate parameter type
        if param_info["type"] and not isinstance(value, param_info["type"]):
            try:
                value = param_info["type"](value)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid type for parameter {name}")

        # Validate parameter range
        if param_info["min"] is not None and value < param_info["min"]:
            raise ValueError(f"Parameter {name} must be >= {param_info['min']}")

        if param_info["max"] is not None and value > param_info["max"]:
            raise ValueError(f"Parameter {name} must be <= {param_info['max']}")

        with self._lock:
            self._parameter_values[name] = value

    def get_parameter(self, name: str) -> Any:
        """
        Get parameter value.

        Args:
            name: Parameter name

        Returns:
            Parameter value
        """
        return self._parameter_values.get(name)

    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        Apply the custom effect to an image.

        Args:
            image: Input image

        Returns:
            Processed image
        """
        # Check cache if enabled
        if self.enable_caching:
            cache_key = self._get_cache_key(image)
            with self._lock:
                if cache_key in self._cache:
                    return self._cache[cache_key].copy()

        # Apply effect steps
        result = image.copy()

        if self.enable_parallel and len(self.steps) > 1:
            result = self._apply_parallel(result)
        else:
            result = self._apply_sequential(result)

        # Cache result if enabled
        if self.enable_caching:
            with self._lock:
                self._cache[cache_key] = result.copy()

        return result

    def _apply_sequential(self, image: np.ndarray) -> np.ndarray:
        """Apply steps sequentially."""
        result = image

        for step in self.steps:
            if not step.enabled:
                continue

            try:
                # Merge step parameters with effect parameters
                step_params = step.parameters.copy()
                step_params.update(self._parameter_values)

                result = step.operation(result, **step_params)

            except Exception as e:
                print(f"Error in step '{step.name}': {e}")
                # Continue with other steps

        return result

    def _apply_parallel(self, image: np.ndarray) -> np.ndarray:
        """Apply steps in parallel where possible."""

        # For simplicity, we'll apply all steps sequentially for now
        # In a more advanced implementation, you could analyze dependencies
        # and parallelize independent steps
        return self._apply_sequential(image)

    def _get_cache_key(self, image: np.ndarray) -> str:
        """Generate cache key for image and parameters."""
        import hashlib

        # Use image shape and parameter values for cache key
        key_data = {"shape": image.shape, "params": self._parameter_values.copy()}

        key_str = str(key_data)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get_info(self) -> Dict[str, Any]:
        """Get effect information."""
        return {
            "name": self.name,
            "type": self.effect_type.value,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "steps": len(self.steps),
            "parameters": len(self.parameters),
            "enable_caching": self.enable_caching,
            "enable_parallel": self.enable_parallel,
            "max_workers": self.max_workers,
        }

    def clear_cache(self):
        """Clear effect cache."""
        with self._lock:
            self._cache.clear()

    def enable_step(self, step_name: str):
        """Enable a specific step."""
        for step in self.steps:
            if step.name == step_name:
                step.enabled = True
                break

    def disable_step(self, step_name: str):
        """Disable a specific step."""
        for step in self.steps:
            if step.name == step_name:
                step.enabled = False
                break


def create_quick_blur_effect(
    name: str = "quick_blur", kernel_size: int = 5, sigma: float = 1.5
) -> CustomEffect:
    """
    Create a quick blur effect.

    Args:
        name: Effect name
        kernel_size: Blur kernel size
        sigma: Gaussian blur sigma

    Returns:
        Custom blur effect
    """
    return (
        CustomEffectBuilder(name)
        .set_description(f"Quick Gaussian blur with kernel size {kernel_size}")
        .add_blur_step(kernel_size=kernel_size, sigma=sigma)
        .build()
    )


def create_enhancement_effect(
    name: str = "enhancement",
    enable_sharpen: bool = True,
    enable_contrast: bool = True,
    sharpen_intensity: float = 0.5,
    contrast_intensity: float = 1.2,
) -> CustomEffect:
    """
    Create an image enhancement effect.

    Args:
        name: Effect name
        enable_sharpen: Whether to enable sharpening
        enable_contrast: Whether to enable contrast enhancement
        sharpen_intensity: Sharpening intensity
        contrast_intensity: Contrast enhancement intensity

    Returns:
        Custom enhancement effect
    """
    builder = (
        CustomEffectBuilder(name)
        .set_type(EffectType.ENHANCE)
        .set_description("Image enhancement effect")
    )

    if enable_sharpen:
        builder.add_sharpen_step(intensity=sharpen_intensity)

    if enable_contrast:
        builder.add_enhance_step(
            enhancement_type="contrast", intensity=contrast_intensity
        )

    return builder.build()
