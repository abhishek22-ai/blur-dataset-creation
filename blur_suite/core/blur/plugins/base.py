"""
Base classes for blur effect plugins.

This module provides the foundation for creating custom blur effect
plugins that can extend the blur system with new algorithms.
"""

import importlib.util
import inspect
import logging
import os
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Type

from ..base import BlurEffect, BlurType, Parameter
from ..exceptions import PluginError, PluginLoadError, PluginValidationError
from ..factory import BlurEffectMetadata

logger = logging.getLogger(__name__)


class PluginBase(BlurEffect):
    """
    Base class for custom blur effect plugins.

    All custom blur plugins should inherit from this class and implement
    the required abstract methods to integrate with the blur system.
    """

    def __init__(self, blur_type: BlurType):
        """
        Initialize plugin blur effect.

        Args:
            blur_type: The type of blur effect this plugin implements
        """
        super().__init__(blur_type)
        self.plugin_name = self.__class__.__name__
        self.plugin_version = "1.0.0"
        self.plugin_author = "Unknown"
        self.plugin_description = ""

    @abstractmethod
    def _validate_requirements(self):
        """
        Validate that all requirements for this plugin are met.

        Override this method to check for specific dependencies,
        libraries, or system requirements needed by the plugin.
        """
        pass

    @abstractmethod
    def _define_parameters(self) -> Dict[str, Parameter]:
        """
        Define the parameters specific to this plugin.

        Returns:
            Dictionary mapping parameter names to Parameter objects
        """
        pass

    @abstractmethod
    def _apply_blur(self, image):
        """
        Apply the plugin's specific blur algorithm.

        Args:
            image: Input image as numpy array

        Returns:
            Blurred image as numpy array
        """
        pass

    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Get information about this plugin.

        Returns:
            Dictionary containing plugin metadata
        """
        return {
            "name": self.plugin_name,
            "version": self.plugin_version,
            "author": self.plugin_author,
            "description": self.plugin_description,
            "blur_type": self.blur_type.value,
            "parameters": self._get_plugin_parameters_info(),
        }

    def _get_plugin_parameters_info(self) -> Dict[str, Any]:
        """Get parameter information for this plugin."""
        parameters = self.get_parameters()
        return {name: param.to_dict() for name, param in parameters.items()}

    def validate_plugin(self) -> List[str]:
        """
        Validate the plugin implementation.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required attributes
        if not hasattr(self, "plugin_name") or not self.plugin_name:
            errors.append("Plugin must have a valid plugin_name")

        if not hasattr(self, "plugin_version") or not self.plugin_version:
            errors.append("Plugin must have a valid plugin_version")

        # Check if parameters are properly defined
        try:
            parameters = self._define_parameters()
            if not isinstance(parameters, dict):
                errors.append("Plugin _define_parameters() must return a dictionary")
        except Exception as e:
            errors.append(f"Plugin parameter definition failed: {str(e)}")

        # Check if blur method is implemented
        if self._apply_blur.__func__ == PluginBase._apply_blur:
            errors.append("Plugin must implement _apply_blur method")

        # Check if requirements validation is implemented
        if self._validate_requirements.__func__ == PluginBase._validate_requirements:
            errors.append("Plugin must implement _validate_requirements method")

        return errors


class PluginLoader:
    """
    Handles loading and validation of blur effect plugins.

    Provides functionality to load plugins from files or modules,
    validate their implementation, and prepare them for registration.
    """

    def __init__(self):
        """Initialize the plugin loader."""
        self._loaded_plugins: Dict[str, Type[PluginBase]] = {}
        self._plugin_paths: List[str] = []

    def load_plugin_from_file(self, file_path: str) -> Type[PluginBase]:
        """
        Load a plugin from a Python file.

        Args:
            file_path: Path to the plugin file

        Returns:
            Plugin class

        Raises:
            PluginLoadError: If loading fails
        """
        try:
            # Validate file path
            if not os.path.isfile(file_path):
                raise PluginLoadError(f"Plugin file not found: {file_path}")

            if not file_path.endswith(".py"):
                raise PluginLoadError(f"Plugin file must be a Python file: {file_path}")

            # Load module from file
            module_name = self._generate_module_name(file_path)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None:
                raise PluginLoadError(f"Cannot create module spec for: {file_path}")

            module = importlib.util.module_from_spec(spec)

            # Execute the module
            spec.loader.exec_module(module)

            # Find plugin class in module
            plugin_class = self._find_plugin_class(module)
            if plugin_class is None:
                raise PluginLoadError(f"No valid plugin class found in: {file_path}")

            # Validate plugin
            validation_errors = self._validate_plugin_class(plugin_class)
            if validation_errors:
                raise PluginValidationError(
                    f"Plugin validation failed: {'; '.join(validation_errors)}",
                    plugin_name=plugin_class.__name__,
                    validation_errors=validation_errors,
                )

            # Store loaded plugin
            self._loaded_plugins[plugin_class.__name__] = plugin_class
            self._plugin_paths.append(file_path)

            logger.info(
                f"Successfully loaded plugin {plugin_class.__name__} from {file_path}"
            )
            return plugin_class

        except Exception as e:
            if isinstance(e, (PluginLoadError, PluginValidationError)):
                raise
            raise PluginLoadError(f"Failed to load plugin from {file_path}: {str(e)}")

    def load_plugin_from_module(self, module_name: str) -> Type[PluginBase]:
        """
        Load a plugin from an installed Python module.

        Args:
            module_name: Name of the module containing the plugin

        Returns:
            Plugin class

        Raises:
            PluginLoadError: If loading fails
        """
        try:
            # Import the module
            module = importlib.import_module(module_name)

            # Find plugin class in module
            plugin_class = self._find_plugin_class(module)
            if plugin_class is None:
                raise PluginLoadError(
                    f"No valid plugin class found in module: {module_name}"
                )

            # Validate plugin
            validation_errors = self._validate_plugin_class(plugin_class)
            if validation_errors:
                raise PluginValidationError(
                    f"Plugin validation failed: {'; '.join(validation_errors)}",
                    plugin_name=plugin_class.__name__,
                    validation_errors=validation_errors,
                )

            # Store loaded plugin
            self._loaded_plugins[plugin_class.__name__] = plugin_class

            logger.info(
                f"Successfully loaded plugin {plugin_class.__name__} from module {module_name}"
            )
            return plugin_class

        except ImportError as e:
            raise PluginLoadError(f"Cannot import module {module_name}: {str(e)}")
        except Exception as e:
            if isinstance(e, (PluginLoadError, PluginValidationError)):
                raise
            raise PluginLoadError(
                f"Failed to load plugin from module {module_name}: {str(e)}"
            )

    def _generate_module_name(self, file_path: str) -> str:
        """Generate a unique module name for a plugin file."""
        import hashlib

        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        return f"plugin_{base_name}_{path_hash}"

    def _find_plugin_class(self, module) -> Optional[Type[PluginBase]]:
        """Find a plugin class in a module."""
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, PluginBase)
                and obj != PluginBase
            ):
                return obj
        return None

    def _validate_plugin_class(self, plugin_class: Type[PluginBase]) -> List[str]:
        """Validate a plugin class implementation."""
        errors = []

        # Check if it's a proper class
        if not inspect.isclass(plugin_class):
            errors.append("Plugin must be a class")
            return errors

        # Check inheritance
        if not issubclass(plugin_class, PluginBase):
            errors.append("Plugin class must inherit from PluginBase")

        # Try to instantiate and validate
        try:
            # Create a temporary instance for validation
            temp_instance = plugin_class(
                BlurType.GAUSSIAN
            )  # Use dummy blur type for validation

            # Run plugin's own validation
            plugin_errors = temp_instance.validate_plugin()
            errors.extend(plugin_errors)

        except Exception as e:
            errors.append(f"Cannot instantiate plugin class: {str(e)}")

        return errors

    def get_loaded_plugins(self) -> Dict[str, Type[PluginBase]]:
        """
        Get all loaded plugin classes.

        Returns:
            Dictionary mapping plugin names to plugin classes
        """
        return self._loaded_plugins.copy()

    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """
        Check if a plugin is loaded.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if loaded, False otherwise
        """
        return plugin_name in self._loaded_plugins

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if unloaded, False if not found
        """
        if plugin_name not in self._loaded_plugins:
            return False

        del self._loaded_plugins[plugin_name]

        # Remove from paths if found
        if plugin_name in self._plugin_paths:
            self._plugin_paths.remove(plugin_name)

        logger.info(f"Unloaded plugin {plugin_name}")
        return True


class PluginRegistry:
    """
    Registry for managing loaded blur effect plugins.

    Extends the core blur registry with plugin-specific functionality
    for discovery, loading, and management of custom plugins.
    """

    def __init__(self, core_registry=None):
        """
        Initialize plugin registry.

        Args:
            core_registry: Optional core registry to extend
        """
        from ..factory import BlurRegistry

        self.core_registry = core_registry or BlurRegistry()
        self.plugin_loader = PluginLoader()
        self._plugin_metadata: Dict[str, BlurEffectMetadata] = {}

    def register_plugin(
        self,
        plugin_class: Type[PluginBase],
        metadata: Optional[BlurEffectMetadata] = None,
    ) -> str:
        """
        Register a loaded plugin with the registry.

        Args:
            plugin_class: The plugin class to register
            metadata: Optional metadata (will be generated if not provided)

        Returns:
            Plugin name

        Raises:
            PluginError: If registration fails
        """
        try:
            # Create temporary instance to get info
            temp_instance = plugin_class(BlurType.GAUSSIAN)  # Dummy type for metadata
            plugin_info = temp_instance.get_plugin_info()

            # Create metadata if not provided
            if metadata is None:
                metadata = BlurEffectMetadata(
                    name=plugin_info["name"],
                    description=plugin_info.get("description", ""),
                    blur_type=temp_instance.blur_type,
                    effect_class=plugin_class,
                    default_parameters=plugin_info.get("default_parameters", {}),
                    category="plugin",
                    tags=["plugin", "custom"],
                )

            # Register with core registry
            self.core_registry.register_effect(metadata)

            # Store plugin metadata
            self._plugin_metadata[plugin_class.__name__] = metadata

            logger.info(f"Registered plugin {plugin_class.__name__}")
            return plugin_class.__name__

        except Exception as e:
            raise PluginError(
                f"Failed to register plugin {plugin_class.__name__}: {str(e)}"
            )

    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Unregister a plugin.

        Args:
            plugin_name: Name of the plugin to unregister

        Returns:
            True if unregistered, False if not found
        """
        if plugin_name not in self._plugin_metadata:
            return False

        # Unregister from core registry
        metadata = self._plugin_metadata[plugin_name]
        success = self.core_registry.unregister_effect(metadata.name)

        if success:
            del self._plugin_metadata[plugin_name]
            logger.info(f"Unregistered plugin {plugin_name}")

        return success

    def load_plugin_from_file(self, file_path: str) -> str:
        """
        Load and register a plugin from a file.

        Args:
            file_path: Path to the plugin file

        Returns:
            Plugin name

        Raises:
            PluginError: If loading or registration fails
        """
        try:
            # Load the plugin
            plugin_class = self.plugin_loader.load_plugin_from_file(file_path)

            # Register the plugin
            return self.register_plugin(plugin_class)

        except Exception as e:
            raise PluginError(f"Failed to load plugin from {file_path}: {str(e)}")

    def load_plugin_from_module(self, module_name: str) -> str:
        """
        Load and register a plugin from a module.

        Args:
            module_name: Name of the module

        Returns:
            Plugin name

        Raises:
            PluginError: If loading or registration fails
        """
        try:
            # Load the plugin
            plugin_class = self.plugin_loader.load_plugin_from_module(module_name)

            # Register the plugin
            return self.register_plugin(plugin_class)

        except Exception as e:
            raise PluginError(
                f"Failed to load plugin from module {module_name}: {str(e)}"
            )

    def get_plugin_metadata(self, plugin_name: str) -> Optional[BlurEffectMetadata]:
        """
        Get metadata for a registered plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin metadata or None if not found
        """
        return self._plugin_metadata.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """
        List all registered plugin names.

        Returns:
            List of plugin names
        """
        return list(self._plugin_metadata.keys())

    def is_plugin_registered(self, plugin_name: str) -> bool:
        """
        Check if a plugin is registered.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if registered, False otherwise
        """
        return plugin_name in self._plugin_metadata

    def discover_plugins(self, search_paths: List[str]) -> List[str]:
        """
        Discover plugin files in specified paths.

        Args:
            search_paths: List of directories to search

        Returns:
            List of discovered plugin file paths
        """
        plugin_files = []

        for search_path in search_paths:
            if not os.path.isdir(search_path):
                continue

            # Search for Python files that might be plugins
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if file.endswith(".py") and not file.startswith("__"):
                        file_path = os.path.join(root, file)

                        # Quick check if file contains plugin code
                        if self._is_likely_plugin_file(file_path):
                            plugin_files.append(file_path)

        return plugin_files

    def _is_likely_plugin_file(self, file_path: str) -> bool:
        """Check if a file is likely to contain a plugin."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for plugin indicators
            plugin_indicators = [
                "class.*PluginBase",
                "PluginBase",
                "blur_type",
                "BlurType",
            ]

            return any(indicator in content for indicator in plugin_indicators)

        except Exception:
            return False

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Dictionary with plugin information or None if not found
        """
        metadata = self.get_plugin_metadata(plugin_name)
        if not metadata:
            return None

        return {
            "name": metadata.name,
            "description": metadata.description,
            "version": getattr(metadata, "version", "Unknown"),
            "author": getattr(metadata, "author", "Unknown"),
            "blur_type": metadata.blur_type.value,
            "category": metadata.category,
            "tags": metadata.tags,
            "parameters": self._get_plugin_parameters_info(metadata.effect_class),
        }

    def _get_plugin_parameters_info(
        self, plugin_class: Type[PluginBase]
    ) -> Dict[str, Any]:
        """Get parameter information for a plugin class."""
        try:
            # Create temporary instance to get parameters
            temp_plugin = plugin_class(BlurType.GAUSSIAN)  # Dummy type for info
            parameters = temp_plugin.get_parameters()

            param_info = {}
            for name, param in parameters.items():
                param_info[name] = param.to_dict()

            return param_info
        except Exception:
            return {}
