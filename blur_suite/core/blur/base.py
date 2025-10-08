"""
Base classes and interfaces for blur effects.

This module provides the foundation for all blur effect implementations,
including abstract base classes, parameter validation, and result containers.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

from .exceptions import (
    BlurApplicationError,
    InvalidParameterError,
    UnsupportedFormatError,
)

logger = logging.getLogger(__name__)


class BlurType(Enum):
    """Enumeration of supported blur effect types."""

    GAUSSIAN = "gaussian"
    MOTION = "motion"
    DEFOCUS = "defocus"
    AVERAGE = "average"
    BILATERAL = "bilateral"
    NO_BLUR = "none"


@dataclass
class Parameter:
    """
    Data class for blur parameters with validation.

    Provides type-safe parameter storage with range validation and
    meaningful error messages for invalid values.
    """

    name: str
    value: Any
    param_type: type
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[list] = None
    description: str = ""

    def __post_init__(self):
        """Validate parameter after initialization."""
        self._validate()

    def _validate(self):
        """Perform parameter validation."""
        # Type validation
        if not isinstance(self.value, self.param_type):
            raise InvalidParameterError(
                f"Parameter '{self.name}' must be of type {self.param_type.__name__}, "
                f"got {type(self.value).__name__}"
            )

        # Range validation for numeric types
        if isinstance(self.value, (int, float)):
            if self.min_value is not None and self.value < self.min_value:
                raise InvalidParameterError(
                    f"Parameter '{self.name}' value {self.value} is below minimum {self.min_value}"
                )
            if self.max_value is not None and self.value > self.max_value:
                raise InvalidParameterError(
                    f"Parameter '{self.name}' value {self.value} exceeds maximum {self.max_value}"
                )

        # Allowed values validation
        if self.allowed_values is not None and self.value not in self.allowed_values:
            raise InvalidParameterError(
                f"Parameter '{self.name}' value {self.value} not in allowed values {self.allowed_values}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameter to dictionary representation."""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.param_type.__name__,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "allowed_values": self.allowed_values,
            "description": self.description,
        }


@dataclass
class BlurResult:
    """
    Container for blur operation results.

    Stores the processed image, metadata about the operation,
    and any warnings or errors that occurred.
    """

    # Core result data
    result_image: np.ndarray
    blur_type: BlurType
    parameters: Dict[str, Parameter]

    # Metadata
    processing_time_ms: float
    original_shape: Tuple[int, ...]
    result_shape: Tuple[int, ...]

    # Optional information
    warnings: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate result after initialization."""
        if not isinstance(self.result_image, np.ndarray):
            raise BlurApplicationError("Result image must be a numpy array")

        if self.result_image.size == 0:
            raise BlurApplicationError("Result image cannot be empty")

    def add_warning(self, warning: str):
        """Add a warning message to the result."""
        self.warnings.append(warning)
        logger.warning(f"Blur operation warning: {warning}")

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the result."""
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "blur_type": self.blur_type.value,
            "parameters": {k: v.to_dict() for k, v in self.parameters.items()},
            "processing_time_ms": self.processing_time_ms,
            "original_shape": self.original_shape,
            "result_shape": self.result_shape,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "image_dtype": str(self.result_image.dtype),
            "image_shape": self.result_image.shape,
        }


class BlurEffect(ABC):
    """
    Abstract base class for all blur effects.

    Defines the interface that all blur effect implementations must follow.
    Provides common functionality and ensures consistent behavior across
    different blur types.
    """

    def __init__(self, blur_type: BlurType):
        """
        Initialize blur effect.

        Args:
            blur_type: The type of blur effect this instance represents
        """
        self.blur_type = blur_type
        self._parameters: Dict[str, Parameter] = {}
        self._validate_requirements()

    @abstractmethod
    def _validate_requirements(self):
        """Validate that all requirements for this blur effect are met."""
        pass

    @abstractmethod
    def _define_parameters(self) -> Dict[str, Parameter]:
        """
        Define the parameters specific to this blur effect.

        Returns:
            Dictionary mapping parameter names to Parameter objects
        """
        pass

    @abstractmethod
    def _apply_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Apply the specific blur algorithm to the image.

        Args:
            image: Input image as numpy array

        Returns:
            Blurred image as numpy array
        """
        pass

    def set_parameter(self, name: str, value: Any):
        """
        Set a parameter value with validation.

        Args:
            name: Parameter name
            value: Parameter value

        Raises:
            InvalidParameterError: If parameter is invalid
        """
        if name not in self._parameters:
            raise InvalidParameterError(f"Unknown parameter: {name}")

        param = self._parameters[name]
        param.value = value
        param._validate()

    def get_parameter(self, name: str) -> Any:
        """
        Get a parameter value.

        Args:
            name: Parameter name

        Returns:
            Parameter value

        Raises:
            InvalidParameterError: If parameter is unknown
        """
        if name not in self._parameters:
            raise InvalidParameterError(f"Unknown parameter: {name}")
        return self._parameters[name].value

    def get_parameters(self) -> Dict[str, Parameter]:
        """
        Get all parameters.

        Returns:
            Dictionary of all parameters
        """
        return self._parameters.copy()

    def validate_image(self, image: np.ndarray) -> bool:
        """
        Validate input image compatibility.

        Args:
            image: Input image to validate

        Returns:
            True if image is valid

        Raises:
            UnsupportedFormatError: If image format is not supported
        """
        if not isinstance(image, np.ndarray):
            raise UnsupportedFormatError("Input must be a numpy array")

        if image.size == 0:
            raise UnsupportedFormatError("Input image cannot be empty")

        if len(image.shape) not in [2, 3]:
            raise UnsupportedFormatError(
                f"Image must be 2D (grayscale) or 3D (color), got {len(image.shape)}D"
            )

        return True

    def apply(self, image: np.ndarray) -> BlurResult:
        """
        Apply blur effect to an image.

        Args:
            image: Input image as numpy array

        Returns:
            BlurResult containing the processed image and metadata

        Raises:
            BlurApplicationError: If blur application fails
        """
        import time

        start_time = time.time()

        try:
            # Validate input image
            self.validate_image(image)

            # Store original shape for result
            original_shape = image.shape

            # Apply the blur effect
            result_image = self._apply_blur(image)

            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000

            # Create result object
            result = BlurResult(
                result_image=result_image,
                blur_type=self.blur_type,
                parameters=self.get_parameters(),
                processing_time_ms=processing_time_ms,
                original_shape=original_shape,
                result_shape=result_image.shape,
            )

            logger.info(
                f"Applied {self.blur_type.value} blur in {processing_time_ms:.2f}ms"
            )
            return result

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Blur application failed after {processing_time_ms:.2f}ms: {str(e)}"
            )
            raise BlurApplicationError(f"Failed to apply blur: {str(e)}") from e


class BaseBlurEffect(BlurEffect):
    """
    Base implementation providing common functionality for blur effects.

    This class handles parameter management and provides default implementations
    for common operations that can be shared across different blur types.
    """

    def __init__(self, blur_type: BlurType):
        """Initialize base blur effect."""
        super().__init__(blur_type)
        self._parameters = self._define_parameters()

    def _validate_requirements(self):
        """Default requirement validation - can be overridden by subclasses."""
        # Check for required dependencies (e.g., OpenCV)
        try:
            import cv2

            self._opencv_available = True
        except ImportError:
            self._opencv_available = False
            logger.warning(
                "OpenCV not available - some blur effects may not work properly"
            )

    def _define_parameters(self) -> Dict[str, Parameter]:
        """
        Define common parameters available to all blur effects.

        Subclasses should override this to add their specific parameters.
        """
        return {}

    def _apply_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Default blur implementation - should be overridden by subclasses.

        Args:
            image: Input image

        Returns:
            Unchanged image (pass-through)
        """
        logger.warning(f"No blur implementation provided for {self.blur_type.value}")
        return image.copy()

    def _ensure_valid_image(self, image: np.ndarray) -> np.ndarray:
        """
        Ensure image is in a valid format for processing.

        Args:
            image: Input image

        Returns:
            Validated and potentially converted image
        """
        # Convert to float32 for better precision in calculations
        if image.dtype != np.float32:
            image = (
                image.astype(np.float32) / 255.0
                if image.dtype == np.uint8
                else image.astype(np.float32)
            )

        return image

    def _restore_image_format(
        self, image: np.ndarray, original_image: np.ndarray
    ) -> np.ndarray:
        """
        Restore image to original format if necessary.

        Args:
            image: Processed image
            original_image: Original input image

        Returns:
            Image in appropriate output format
        """
        # If original was uint8, convert back
        if original_image.dtype == np.uint8:
            image = np.clip(image * 255.0, 0, 255).astype(np.uint8)

        return image
