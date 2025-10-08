"""
Factory and registry for blur effects.

This module provides the factory pattern implementation for creating
blur effect instances and managing the registry of available blur types.
"""

import inspect
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from .base import BlurEffect, BlurType
from .effects import (
    AverageBlur,
    BilateralBlur,
    DefocusBlur,
    GaussianBlur,
    MotionBlur,
    NoBlur,
)
from .exceptions import FactoryError, InvalidParameterError, RegistryError


@dataclass
class BlurEffectMetadata:
    """
    Metadata for a blur effect type.

    Contains information about a blur effect including its description,
    parameter specifications, and capabilities.
    """

    name: str
    description: str
    blur_type: BlurType
    effect_class: Type[BlurEffect]
    default_parameters: Dict[str, Any]
    category: str = "general"
    tags: List[str] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = []


class BlurRegistry:
    """
    Registry for managing available blur effect types.

    Provides centralized management of blur effects, their metadata,
    and capabilities for discovery and validation.
    """

    def __init__(self):
        """Initialize the blur registry."""
        self._effects: Dict[str, BlurEffectMetadata] = {}
        self._effects_by_type: Dict[BlurType, BlurEffectMetadata] = {}
        self._categories: Dict[str, List[str]] = {}
        self._register_default_effects()

    def _register_default_effects(self):
        """Register all default blur effect implementations."""
        default_effects = [
            BlurEffectMetadata(
                name="Gaussian Blur",
                description="Applies Gaussian blur using convolution with a Gaussian kernel",
                blur_type=BlurType.GAUSSIAN,
                effect_class=GaussianBlur,
                default_parameters={"kernel_size": 5, "sigma_x": 1.0, "sigma_y": 1.0},
                category="smoothing",
                tags=["gaussian", "convolution", "smoothing"],
            ),
            BlurEffectMetadata(
                name="Motion Blur",
                description="Simulates motion blur in a specific direction",
                blur_type=BlurType.MOTION,
                effect_class=MotionBlur,
                default_parameters={"angle": 0.0, "length": 10},
                category="motion",
                tags=["motion", "directional", "linear"],
            ),
            BlurEffectMetadata(
                name="Defocus Blur",
                description="Simulates camera defocus or bokeh effect",
                blur_type=BlurType.DEFOCUS,
                effect_class=DefocusBlur,
                default_parameters={"radius": 5, "strength": 1.0},
                category="depth",
                tags=["defocus", "bokeh", "circular"],
            ),
            BlurEffectMetadata(
                name="Average Blur",
                description="Simple averaging blur using mean filtering",
                blur_type=BlurType.AVERAGE,
                effect_class=AverageBlur,
                default_parameters={"kernel_size": 5},
                category="smoothing",
                tags=["average", "mean", "simple"],
            ),
            BlurEffectMetadata(
                name="Bilateral Blur",
                description="Edge-preserving blur that maintains sharp edges",
                blur_type=BlurType.BILATERAL,
                effect_class=BilateralBlur,
                default_parameters={
                    "diameter": 9,
                    "sigma_color": 75.0,
                    "sigma_space": 75.0,
                },
                category="edge-preserving",
                tags=["bilateral", "edge-preserving", "denoising"],
            ),
            BlurEffectMetadata(
                name="No Blur",
                description="Pass-through effect that returns the original image unchanged",
                blur_type=BlurType.NO_BLUR,
                effect_class=NoBlur,
                default_parameters={},
                category="utility",
                tags=["passthrough", "identity", "none"],
            ),
        ]

        for effect_metadata in default_effects:
            self.register_effect(effect_metadata)

            # Also register by enum value for GUI compatibility
            self._effects[effect_metadata.blur_type.value] = effect_metadata

    def register_effect(self, metadata: BlurEffectMetadata):
        """
        Register a blur effect with the registry.

        Args:
            metadata: Metadata describing the blur effect

        Raises:
            RegistryError: If registration fails
        """
        try:
            # Validate metadata
            self._validate_metadata(metadata)

            # Register by name
            self._effects[metadata.name.lower()] = metadata

            # Register by type
            self._effects_by_type[metadata.blur_type] = metadata

            # Register in category
            if metadata.category not in self._categories:
                self._categories[metadata.category] = []
            self._categories[metadata.category].append(metadata.name.lower())

        except Exception as e:
            raise RegistryError(f"Failed to register effect {metadata.name}: {str(e)}")

    def _validate_metadata(self, metadata: BlurEffectMetadata):
        """Validate effect metadata."""
        if not metadata.name:
            raise RegistryError("Effect name cannot be empty")

        if not metadata.description:
            raise RegistryError("Effect description cannot be empty")

        if not inspect.isclass(metadata.effect_class):
            raise RegistryError("Effect class must be a class")

        if not issubclass(metadata.effect_class, BlurEffect):
            raise RegistryError("Effect class must inherit from BlurEffect")

        # Check if class can be instantiated
        try:
            # Try to create a temporary instance to validate
            temp_instance = metadata.effect_class()
            if temp_instance.blur_type != metadata.blur_type:
                raise RegistryError(
                    f"Effect class blur_type {temp_instance.blur_type} doesn't match metadata {metadata.blur_type}"
                )
        except Exception as e:
            raise RegistryError(f"Cannot instantiate effect class: {str(e)}")

    def get_effect_metadata(self, name: str) -> Optional[BlurEffectMetadata]:
        """
        Get metadata for a blur effect by name.

        Args:
            name: Name of the blur effect (case-insensitive)

        Returns:
            Effect metadata or None if not found
        """
        return self._effects.get(name.lower())

    def get_effect_by_type(self, blur_type: BlurType) -> Optional[BlurEffectMetadata]:
        """
        Get metadata for a blur effect by type.

        Args:
            blur_type: Type of blur effect

        Returns:
            Effect metadata or None if not found
        """
        return self._effects_by_type.get(blur_type)

    def list_effects(self, category: Optional[str] = None) -> List[str]:
        """
        List available blur effect names.

        Args:
            category: Optional category filter

        Returns:
            List of effect names
        """
        if category:
            return self._categories.get(category, [])
        return list(self._effects.keys())

    def list_categories(self) -> List[str]:
        """List all available categories."""
        return list(self._categories.keys())

    def list_types(self) -> List[BlurType]:
        """List all available blur types."""
        return list(self._effects_by_type.keys())

    def get_effects_by_tag(self, tag: str) -> List[BlurEffectMetadata]:
        """
        Get effects that have a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of matching effect metadata
        """
        return [
            metadata
            for metadata in self._effects.values()
            if tag.lower() in metadata.tags
        ]

    def is_registered(self, name: str) -> bool:
        """
        Check if an effect is registered.

        Args:
            name: Name of the effect

        Returns:
            True if registered, False otherwise
        """
        return name.lower() in self._effects

    def unregister_effect(self, name: str) -> bool:
        """
        Unregister a blur effect.

        Args:
            name: Name of the effect to unregister

        Returns:
            True if unregistered, False if not found
        """
        name_lower = name.lower()
        if name_lower not in self._effects:
            return False

        metadata = self._effects[name_lower]

        # Remove from all collections
        del self._effects[name_lower]
        del self._effects_by_type[metadata.blur_type]

        if metadata.category in self._categories:
            self._categories[metadata.category].remove(name_lower)
            if not self._categories[metadata.category]:
                del self._categories[metadata.category]

        return True


class BlurFactory:
    """
    Factory for creating blur effect instances.

    Provides methods for creating blur effects with parameter validation
    and automatic configuration based on registered effect types.
    """

    def __init__(self, registry: Optional[BlurRegistry] = None):
        """
        Initialize the blur factory.

        Args:
            registry: Optional registry instance (creates default if not provided)
        """
        self.registry = registry or BlurRegistry()

    def create_effect(self, name: str, **parameters) -> BlurEffect:
        """
        Create a blur effect instance by name.

        Args:
            name: Name of the blur effect
            **parameters: Parameters to configure the effect

        Returns:
            Configured blur effect instance

        Raises:
            FactoryError: If effect creation fails
        """
        try:
            # Get effect metadata
            metadata = self.registry.get_effect_metadata(name)
            if not metadata:
                raise FactoryError(f"Unknown blur effect: {name}")

            # Create effect instance
            effect = metadata.effect_class()

            # Apply default parameters first
            for param_name, default_value in metadata.default_parameters.items():
                try:
                    effect.set_parameter(param_name, default_value)
                except InvalidParameterError:
                    # Skip parameters that don't exist in this effect
                    pass

            # Apply provided parameters
            for param_name, param_value in parameters.items():
                effect.set_parameter(param_name, param_value)

            return effect

        except Exception as e:
            if isinstance(e, FactoryError):
                raise
            raise FactoryError(f"Failed to create effect {name}: {str(e)}")

    def create_effect_by_type(self, blur_type: BlurType, **parameters) -> BlurEffect:
        """
        Create a blur effect instance by type.

        Args:
            blur_type: Type of blur effect
            **parameters: Parameters to configure the effect

        Returns:
            Configured blur effect instance

        Raises:
            FactoryError: If effect creation fails
        """
        try:
            # Get effect metadata
            metadata = self.registry.get_effect_by_type(blur_type)
            if not metadata:
                raise FactoryError(f"Unknown blur type: {blur_type}")

            # Create effect instance
            effect = metadata.effect_class()

            # Apply default parameters first
            for param_name, default_value in metadata.default_parameters.items():
                try:
                    effect.set_parameter(param_name, default_value)
                except InvalidParameterError:
                    # Skip parameters that don't exist in this effect
                    pass

            # Apply provided parameters
            for param_name, param_value in parameters.items():
                effect.set_parameter(param_name, param_value)

            return effect

        except Exception as e:
            if isinstance(e, FactoryError):
                raise
            raise FactoryError(f"Failed to create effect {blur_type}: {str(e)}")

    def get_effect_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a blur effect.

        Args:
            name: Name of the blur effect

        Returns:
            Dictionary with effect information or None if not found
        """
        metadata = self.registry.get_effect_metadata(name)
        if not metadata:
            return None

        return {
            "name": metadata.name,
            "description": metadata.description,
            "blur_type": metadata.blur_type.value,
            "category": metadata.category,
            "tags": metadata.tags,
            "default_parameters": metadata.default_parameters,
            "parameters": self._get_effect_parameters_info(metadata.effect_class),
        }

    def _get_effect_parameters_info(
        self, effect_class: Type[BlurEffect]
    ) -> Dict[str, Any]:
        """Get parameter information for an effect class."""
        try:
            # Create temporary instance to get parameters
            temp_effect = effect_class()
            parameters = temp_effect.get_parameters()

            param_info = {}
            for name, param in parameters.items():
                param_info[name] = param.to_dict()

            return param_info
        except Exception:
            return {}

    def list_available_effects(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all available blur effects.

        Args:
            category: Optional category filter

        Returns:
            List of effect information dictionaries
        """
        effect_names = self.registry.list_effects(category)

        effects_info = []
        for name in effect_names:
            info = self.get_effect_info(name)
            if info:
                effects_info.append(info)

        return effects_info

    def validate_parameters(self, name: str, **parameters) -> Dict[str, Any]:
        """
        Validate parameters for a blur effect without creating it.

        Args:
            name: Name of the blur effect
            **parameters: Parameters to validate

        Returns:
            Dictionary with validation results

        Raises:
            FactoryError: If validation fails
        """
        try:
            # Get effect metadata
            metadata = self.registry.get_effect_metadata(name)
            if not metadata:
                raise FactoryError(f"Unknown blur effect: {name}")

            # Create temporary effect instance
            effect = metadata.effect_class()

            # Try to set each parameter
            validation_results = {}
            for param_name, param_value in parameters.items():
                try:
                    effect.set_parameter(param_name, param_value)
                    validation_results[param_name] = {
                        "valid": True,
                        "value": param_value,
                    }
                except InvalidParameterError as e:
                    validation_results[param_name] = {
                        "valid": False,
                        "error": str(e),
                        "value": param_value,
                    }
                except Exception as e:
                    validation_results[param_name] = {
                        "valid": False,
                        "error": f"Unexpected error: {str(e)}",
                        "value": param_value,
                    }

            return validation_results

        except Exception as e:
            if isinstance(e, FactoryError):
                raise
            raise FactoryError(f"Parameter validation failed for {name}: {str(e)}")


# Global registry and factory instances
_default_registry = BlurRegistry()
_default_factory = BlurFactory(_default_registry)


def get_blur_factory() -> BlurFactory:
    """
    Get the default blur factory instance.

    Returns:
        Default BlurFactory instance
    """
    return _default_factory


def get_blur_registry() -> BlurRegistry:
    """
    Get the default blur registry instance.

    Returns:
        Default BlurRegistry instance
    """
    return _default_registry


def create_blur_effect(name: str, **parameters) -> BlurEffect:
    """
    Convenience function to create a blur effect.

    Args:
        name: Name of the blur effect
        **parameters: Parameters for the effect

    Returns:
        Configured blur effect instance
    """
    return _default_factory.create_effect(name, **parameters)


def list_blur_effects(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to list available blur effects.

    Args:
        category: Optional category filter

    Returns:
        List of effect information dictionaries
    """
    return _default_factory.list_available_effects(category)
