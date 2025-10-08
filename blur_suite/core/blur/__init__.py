"""
Blur Suite Core Blur Module

This module provides the complete blur effect system including:
- Base classes and interfaces for blur effects
- Concrete implementations of various blur algorithms
- Factory pattern for creating blur effects
- Plugin architecture for custom blur effects
- Comprehensive error handling

Main Components:
- BlurEffect: Abstract base class for all blur effects
- BlurFactory: Factory for creating blur effect instances
- BlurRegistry: Registry for managing available blur types
- Plugin system: Extensible architecture for custom blur effects

Available Blur Effects:
- GaussianBlur: Gaussian kernel convolution
- MotionBlur: Directional motion simulation
- DefocusBlur: Camera defocus simulation
- AverageBlur: Simple mean filtering
- BilateralBlur: Edge-preserving smoothing
- NoBlur: Pass-through effect

Example Usage:
    from blur_suite.core.blur import BlurFactory, BlurType

    # Create a factory
    factory = BlurFactory()

    # Create a Gaussian blur effect
    gaussian = factory.create_effect("gaussian", kernel_size=7, sigma_x=1.5)

    # Apply to an image
    result = gaussian.apply(image)

    # Access the blurred image
    blurred_image = result.result_image
"""

from .base import BaseBlurEffect, BlurEffect, BlurResult, BlurType, Parameter
from .effects import (
    AverageBlur,
    BilateralBlur,
    DefocusBlur,
    GaussianBlur,
    MotionBlur,
    NoBlur,
)
from .exceptions import (
    BlurApplicationError,
    BlurError,
    FactoryError,
    InvalidParameterError,
    PluginError,
    PluginLoadError,
    PluginValidationError,
    RegistryError,
    UnsupportedFormatError,
)
from .factory import (
    BlurFactory,
    BlurRegistry,
    create_blur_effect,
    get_blur_factory,
    get_blur_registry,
    list_blur_effects,
)

# Plugin system imports
from .plugins.base import PluginBase, PluginLoader
from .plugins.registry import PluginConfiguration, PluginRegistry

__version__ = "1.0.0"
__author__ = "Blur Suite SDK"
__all__ = [
    # Base classes
    "BlurEffect",
    "BaseBlurEffect",
    "BlurType",
    "Parameter",
    "BlurResult",
    # Effect implementations
    "GaussianBlur",
    "MotionBlur",
    "DefocusBlur",
    "AverageBlur",
    "BilateralBlur",
    "NoBlur",
    # Factory and registry
    "BlurFactory",
    "BlurRegistry",
    "get_blur_factory",
    "get_blur_registry",
    "create_blur_effect",
    "list_blur_effects",
    # Exceptions
    "BlurError",
    "InvalidParameterError",
    "UnsupportedFormatError",
    "BlurApplicationError",
    "PluginError",
    "PluginLoadError",
    "PluginValidationError",
    "FactoryError",
    "RegistryError",
    # Plugin system
    "PluginBase",
    "PluginLoader",
    "PluginConfiguration",
    "PluginRegistry",
]
