"""
Plugin registry implementation for blur effects.

This module provides the registry functionality for managing
plugin discovery, loading, and lifecycle management.
"""

import inspect
import json
import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from ..base import BlurType
from .base import PluginRegistry as BasePluginRegistry

logger = logging.getLogger(__name__)


@dataclass
class PluginConfiguration:
    """
    Configuration for plugin loading and management.

    Defines settings for how plugins should be discovered,
    loaded, and managed within the system.
    """

    # Search paths for plugin discovery
    search_paths: List[str]

    # File patterns to look for
    file_patterns: List[str]

    # Whether to load plugins automatically on startup
    auto_load: bool

    # Whether to validate plugins before loading
    validate_on_load: bool

    # Plugin loading timeout in seconds
    load_timeout: float

    # Maximum number of plugins to load
    max_plugins: int

    def __post_init__(self):
        """Set default values."""
        if not self.file_patterns:
            self.file_patterns = ["*.py"]

        if self.load_timeout <= 0:
            self.load_timeout = 30.0

        if self.max_plugins <= 0:
            self.max_plugins = 100


class PluginRegistry(BasePluginRegistry):
    """
    Enhanced plugin registry with configuration and lifecycle management.

    Provides comprehensive plugin management including discovery,
    loading, configuration, and monitoring capabilities.
    """

    def __init__(self, config: Optional[PluginConfiguration] = None):
        """
        Initialize enhanced plugin registry.

        Args:
            config: Optional plugin configuration
        """
        super().__init__()
        self.config = config or PluginConfiguration(
            search_paths=["./plugins", "./blur_plugins"],
            auto_load=False,
            validate_on_load=True,
            load_timeout=30.0,
            max_plugins=50,
        )

        # Plugin state tracking
        self._plugin_states: Dict[str, str] = {}
        self._load_errors: Dict[str, str] = {}
        self._plugin_stats: Dict[str, Any] = {}

    def discover_and_load_plugins(
        self, paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Discover and load plugins from specified paths.

        Args:
            paths: Optional list of paths to search (uses config if not provided)

        Returns:
            Dictionary with loading results and statistics
        """
        search_paths = paths or self.config.search_paths
        results = {
            "discovered": 0,
            "loaded": 0,
            "failed": 0,
            "errors": [],
            "loaded_plugins": [],
        }

        # Discover plugin files
        plugin_files = []
        for path in search_paths:
            if os.path.exists(path):
                discovered = self.discover_plugins([path])
                plugin_files.extend(discovered)
                results["discovered"] += len(discovered)

        # Load discovered plugins
        for plugin_file in plugin_files[: self.config.max_plugins]:
            try:
                plugin_name = self.load_plugin_from_file(plugin_file)
                results["loaded"] += 1
                results["loaded_plugins"].append(plugin_name)
                self._plugin_states[plugin_name] = "loaded"
                self._plugin_stats[plugin_name] = {"file": plugin_file}

            except Exception as e:
                results["failed"] += 1
                error_msg = f"Failed to load {plugin_file}: {str(e)}"
                results["errors"].append(error_msg)
                self._load_errors[plugin_file] = error_msg
                logger.error(error_msg)

        logger.info(
            f"Plugin discovery complete: {results['loaded']}/{results['discovered']} loaded"
        )
        return results

    def auto_load_plugins(self) -> Dict[str, Any]:
        """
        Automatically load plugins based on configuration.

        Returns:
            Dictionary with loading results
        """
        if not self.config.auto_load:
            return {"loaded": 0, "message": "Auto-load disabled"}

        return self.discover_and_load_plugins()

    def save_plugin_manifest(self, file_path: str) -> bool:
        """
        Save plugin manifest to a JSON file.

        Args:
            file_path: Path to save the manifest

        Returns:
            True if saved successfully
        """
        try:
            manifest = {
                "plugins": {},
                "config": asdict(self.config),
                "stats": self._plugin_stats,
                "states": self._plugin_states,
            }

            # Add plugin information
            for plugin_name in self.list_plugins():
                metadata = self.get_plugin_metadata(plugin_name)
                if metadata:
                    manifest["plugins"][plugin_name] = {
                        "name": metadata.name,
                        "description": metadata.description,
                        "blur_type": metadata.blur_type.value,
                        "category": metadata.category,
                        "tags": metadata.tags,
                    }

            # Save to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved plugin manifest to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save plugin manifest: {str(e)}")
            return False

    def load_plugin_manifest(self, file_path: str) -> Dict[str, Any]:
        """
        Load plugin manifest from a JSON file.

        Args:
            file_path: Path to the manifest file

        Returns:
            Dictionary with loading results
        """
        results = {"loaded": 0, "failed": 0, "errors": []}

        try:
            if not os.path.exists(file_path):
                return {"error": f"Manifest file not found: {file_path}"}

            with open(file_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # Restore configuration if present
            if "config" in manifest:
                try:
                    self.config = PluginConfiguration(**manifest["config"])
                except Exception as e:
                    logger.warning(f"Failed to restore config from manifest: {str(e)}")

            # Restore plugin states and stats
            if "states" in manifest:
                self._plugin_states.update(manifest["states"])

            if "stats" in manifest:
                self._plugin_stats.update(manifest["stats"])

            logger.info(f"Loaded plugin manifest from {file_path}")
            return results

        except Exception as e:
            error_msg = f"Failed to load plugin manifest: {str(e)}"
            results["errors"].append(error_msg)
            results["failed"] = 1
            logger.error(error_msg)
            return results

    def get_plugin_state(self, plugin_name: str) -> Optional[str]:
        """
        Get the current state of a plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin state or None if not found
        """
        return self._plugin_states.get(plugin_name)

    def get_plugin_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded plugins.

        Returns:
            Dictionary with plugin statistics
        """
        return {
            "total_plugins": len(self._plugin_metadata),
            "states": self._plugin_states.copy(),
            "load_errors": self._load_errors.copy(),
            "plugin_details": self._plugin_stats.copy(),
        }

    def validate_all_plugins(self) -> Dict[str, List[str]]:
        """
        Validate all registered plugins.

        Returns:
            Dictionary mapping plugin names to validation errors
        """
        validation_results = {}

        for plugin_name in self.list_plugins():
            try:
                metadata = self.get_plugin_metadata(plugin_name)
                if metadata:
                    # Create temporary instance for validation
                    temp_instance = metadata.effect_class(BlurType.GAUSSIAN)
                    errors = temp_instance.validate_plugin()
                    validation_results[plugin_name] = errors

            except Exception as e:
                validation_results[plugin_name] = [f"Validation failed: {str(e)}"]

        return validation_results

    def cleanup_failed_plugins(self) -> int:
        """
        Remove plugins that failed to load properly.

        Returns:
            Number of plugins removed
        """
        removed_count = 0
        failed_plugins = []

        # Find plugins with failed states
        for plugin_name, state in self._plugin_states.items():
            if state == "failed":
                failed_plugins.append(plugin_name)

        # Remove failed plugins
        for plugin_name in failed_plugins:
            if self.unregister_plugin(plugin_name):
                removed_count += 1
                if plugin_name in self._load_errors:
                    del self._load_errors[plugin_name]

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} failed plugins")

        return removed_count

    def export_plugin_list(self, format: str = "json") -> str:
        """
        Export list of plugins in specified format.

        Args:
            format: Export format ("json", "csv", "text")

        Returns:
            Formatted plugin list
        """
        plugins = []

        for plugin_name in self.list_plugins():
            metadata = self.get_plugin_metadata(plugin_name)
            if metadata:
                plugin_info = {
                    "name": metadata.name,
                    "description": metadata.description,
                    "blur_type": metadata.blur_type.value,
                    "category": metadata.category,
                    "state": self.get_plugin_state(plugin_name) or "unknown",
                }
                plugins.append(plugin_info)

        if format.lower() == "json":
            import json

            return json.dumps(plugins, indent=2, ensure_ascii=False)

        elif format.lower() == "csv":
            if not plugins:
                return ""

            import csv
            import io

            output = io.StringIO()
            fieldnames = plugins[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(plugins)
            return output.getvalue()

        else:  # text format
            lines = ["Plugin List:"]
            for plugin in plugins:
                lines.append(
                    f"  {plugin['name']} ({plugin['blur_type']}) - {plugin['description']}"
                )
            return "\n".join(lines)

    def create_plugin_template(
        self, plugin_name: str, blur_type: str, output_path: str
    ) -> bool:
        """
        Create a template file for a new plugin.

        Args:
            plugin_name: Name of the plugin class
            blur_type: Type of blur effect
            output_path: Path to save the template

        Returns:
            True if template created successfully
        """
        try:
            template = f'''"""
Template for {plugin_name} blur effect plugin.

This is a template file for creating custom blur effect plugins.
Modify the class implementation to suit your specific blur algorithm.
"""

from typing import Dict
import numpy as np
from blur_suite.core.blur.plugins.base import PluginBase
from blur_suite.core.blur.base import BlurType, Parameter


class {plugin_name}(PluginBase):
    """
    Custom {plugin_name} blur effect plugin.

    Implement your custom blur algorithm in the _apply_blur method.
    """

    def __init__(self):
        """Initialize the {plugin_name} plugin."""
        super().__init__(BlurType.{blur_type.upper()})
        self.plugin_name = "{plugin_name}"
        self.plugin_version = "1.0.0"
        self.plugin_author = "Your Name"
        self.plugin_description = "Custom {plugin_name} blur effect"

    def _validate_requirements(self):
        """
        Validate that all requirements for this plugin are met.

        Add any specific requirement checks here (dependencies, libraries, etc.)
        """
        super()._validate_requirements()
        # Add custom validation logic here

    def _define_parameters(self) -> Dict[str, Parameter]:
        """
        Define the parameters for this blur effect.

        Returns:
            Dictionary mapping parameter names to Parameter objects
        """
        return {{
            # Add your parameters here
            "param1": Parameter(
                name="param1",
                value=1.0,
                param_type=float,
                min_value=0.0,
                max_value=10.0,
                description="Description of parameter 1"
            ),
            # Add more parameters as needed
        }}

    def _apply_blur(self, image: np.ndarray) -> np.ndarray:
        """
        Apply the custom blur algorithm to the image.

        Args:
            image: Input image as numpy array

        Returns:
            Blurred image as numpy array
        """
        # Implement your blur algorithm here
        # This is where you add your custom blur logic

        # For now, return a copy (no-op)
        return image.copy()


# Optional: Export the plugin class for easier importing
__plugin_class__ = {plugin_name}
'''

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write template file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(template)

            logger.info(f"Created plugin template: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create plugin template: {str(e)}")
            return False

    def get_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """
        Get dependencies for a specific plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            List of dependency names
        """
        dependencies = []

        try:
            metadata = self.get_plugin_metadata(plugin_name)
            if metadata:
                # Create temporary instance to check dependencies
                temp_instance = metadata.effect_class(BlurType.GAUSSIAN)

                # Check for common dependencies based on implementation
                source_lines = inspect.getsource(temp_instance._apply_blur)

                # Look for common library imports
                common_deps = {
                    "cv2": "opencv-python",
                    "scipy": "scipy",
                    "skimage": "scikit-image",
                    "PIL": "Pillow",
                    "torch": "torch",
                    "tensorflow": "tensorflow",
                }

                for import_name, package_name in common_deps.items():
                    if import_name in source_lines:
                        dependencies.append(package_name)

        except Exception as e:
            logger.warning(
                f"Could not analyze dependencies for {plugin_name}: {str(e)}"
            )

        return dependencies

    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a loaded plugin.

        Args:
            plugin_name: Name of the plugin to enable

        Returns:
            True if enabled successfully
        """
        if plugin_name not in self._plugin_metadata:
            return False

        self._plugin_states[plugin_name] = "enabled"
        logger.info(f"Enabled plugin {plugin_name}")
        return True

    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a loaded plugin.

        Args:
            plugin_name: Name of the plugin to disable

        Returns:
            True if disabled successfully
        """
        if plugin_name not in self._plugin_metadata:
            return False

        self._plugin_states[plugin_name] = "disabled"
        logger.info(f"Disabled plugin {plugin_name}")
        return True

    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """
        Check if a plugin is enabled.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if enabled, False otherwise
        """
        return self._plugin_states.get(plugin_name) == "enabled"
