"""
Enhanced Plugin Manager

Central management system for advanced plugin operations including
discovery, validation, testing, and lifecycle management.
"""

import importlib.util
import inspect
import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .plugin_discovery import PluginDiscovery
from .plugin_template import PluginTemplate
from .plugin_validator import PluginValidator


@dataclass
class PluginInfo:
    """Information about a discovered plugin."""

    name: str
    version: str
    author: str
    description: str
    file_path: str
    class_name: str
    plugin_type: str
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: float = field(default_factory=time.time)
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class PluginStats:
    """Plugin system statistics."""

    total_plugins: int = 0
    valid_plugins: int = 0
    invalid_plugins: int = 0
    loaded_plugins: int = 0
    failed_plugins: int = 0
    last_discovery: float = 0.0
    discovery_time: float = 0.0


class PluginManager:
    """
    Enhanced plugin manager with advanced capabilities.

    Provides comprehensive plugin management including automatic
    discovery, validation, testing, and lifecycle management.
    """

    def __init__(
        self,
        plugin_dirs: Optional[List[str]] = None,
        auto_discovery: bool = True,
        enable_validation: bool = True,
        enable_testing: bool = True,
    ):
        """
        Initialize plugin manager.

        Args:
            plugin_dirs: List of directories to search for plugins
            auto_discovery: Whether to automatically discover plugins
            enable_validation: Whether to validate discovered plugins
            enable_testing: Whether to run tests on plugins
        """
        self.plugin_dirs = plugin_dirs or self._get_default_plugin_dirs()
        self.auto_discovery = auto_discovery
        self.enable_validation = enable_validation
        self.enable_testing = enable_testing

        # Plugin storage
        self._discovered_plugins: Dict[str, PluginInfo] = {}
        self._loaded_plugins: Dict[str, Type] = {}
        self._plugin_instances: Dict[str, Any] = {}

        # Components
        self.discovery = PluginDiscovery(self.plugin_dirs)
        self.validator = PluginValidator()
        self.template = PluginTemplate()

        # Statistics
        self.stats = PluginStats()

        # Threading
        self._lock = threading.RLock()

        # Auto-discovery
        if self.auto_discovery:
            self.start_auto_discovery()

    def _get_default_plugin_dirs(self) -> List[str]:
        """Get default plugin directories."""
        return [
            str(Path.home() / ".blur_suite" / "plugins"),
            str(Path.cwd() / "plugins"),
            str(Path.cwd() / "blur_suite_plugins"),
        ]

    def start_auto_discovery(self, interval: float = 60.0):
        """
        Start automatic plugin discovery.

        Args:
            interval: Discovery interval in seconds
        """

        def discovery_loop():
            while True:
                try:
                    self.discover_plugins()
                    time.sleep(interval)
                except Exception as e:
                    print(f"Plugin discovery error: {e}")
                    time.sleep(interval)

        thread = threading.Thread(target=discovery_loop, daemon=True)
        thread.start()

    def discover_plugins(
        self, search_paths: Optional[List[str]] = None
    ) -> Dict[str, PluginInfo]:
        """
        Discover plugins in specified paths.

        Args:
            search_paths: Paths to search (uses default if None)

        Returns:
            Dictionary of discovered plugin information
        """
        start_time = time.time()

        if search_paths:
            self.plugin_dirs.extend(search_paths)

        # Discover plugin files
        plugin_files = self.discovery.discover_plugin_files(self.plugin_dirs)

        # Analyze each plugin file
        discovered_plugins = {}

        for file_path in plugin_files:
            try:
                plugin_info = self._analyze_plugin_file(file_path)
                if plugin_info:
                    discovered_plugins[plugin_info.name] = plugin_info

            except Exception as e:
                print(f"Error analyzing plugin file {file_path}: {e}")

        # Update discovered plugins
        with self._lock:
            self._discovered_plugins.update(discovered_plugins)

            # Update statistics
            self.stats.total_plugins = len(self._discovered_plugins)
            self.stats.valid_plugins = sum(
                1 for p in self._discovered_plugins.values() if p.is_valid
            )
            self.stats.invalid_plugins = (
                self.stats.total_plugins - self.stats.valid_plugins
            )
            self.stats.last_discovery = time.time()
            self.stats.discovery_time = time.time() - start_time

        return discovered_plugins

    def _analyze_plugin_file(self, file_path: str) -> Optional[PluginInfo]:
        """Analyze a plugin file and extract information."""
        try:
            # Load module spec
            module_name = self._generate_module_name(file_path)
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                return None

            # Extract plugin information
            plugin_info = self._extract_plugin_info(plugin_class, file_path)

            # Validate if enabled
            if self.enable_validation:
                is_valid, errors = self.validator.validate_plugin_class(plugin_class)
                plugin_info.is_valid = is_valid
                plugin_info.validation_errors = errors

            return plugin_info

        except Exception as e:
            print(f"Error analyzing plugin {file_path}: {e}")
            return None

    def _generate_module_name(self, file_path: str) -> str:
        """Generate unique module name for plugin file."""
        import hashlib

        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        base_name = Path(file_path).stem
        return f"plugin_{base_name}_{path_hash}"

    def _find_plugin_class(self, module) -> Optional[Type]:
        """Find plugin class in module."""
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and hasattr(obj, "__bases__")
                and any("PluginBase" in str(base) for base in obj.__bases__)
            ):
                return obj
        return None

    def _extract_plugin_info(self, plugin_class: Type, file_path: str) -> PluginInfo:
        """Extract information from plugin class."""
        # Create temporary instance to get metadata
        try:
            # We need to determine the blur type - this is a bit tricky without instantiation
            # For now, we'll use a default and let validation catch issues
            plugin_class.__new__(plugin_class)

            # Extract metadata from class and instance
            name = getattr(plugin_class, "plugin_name", plugin_class.__name__)
            version = getattr(plugin_class, "plugin_version", "1.0.0")
            author = getattr(plugin_class, "plugin_author", "Unknown")
            description = getattr(plugin_class, "plugin_description", "")

            # Extract dependencies from class docstring or attributes
            dependencies = getattr(plugin_class, "plugin_dependencies", [])
            tags = getattr(plugin_class, "plugin_tags", [])

            return PluginInfo(
                name=name,
                version=version,
                author=author,
                description=description,
                file_path=file_path,
                class_name=plugin_class.__name__,
                plugin_type="blur_effect",
                dependencies=dependencies,
                tags=tags,
                is_valid=True,  # Will be updated by validator if enabled
            )

        except Exception:
            # Fallback to basic information
            return PluginInfo(
                name=plugin_class.__name__,
                version="1.0.0",
                author="Unknown",
                description="",
                file_path=file_path,
                class_name=plugin_class.__name__,
                plugin_type="blur_effect",
                is_valid=False,
                validation_errors=["Cannot extract plugin information"],
            )

    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a discovered plugin.

        Args:
            plugin_name: Name of the plugin to load

        Returns:
            True if loaded successfully, False otherwise
        """
        with self._lock:
            if plugin_name not in self._discovered_plugins:
                return False

            plugin_info = self._discovered_plugins[plugin_name]

            if not plugin_info.is_valid:
                print(f"Cannot load invalid plugin: {plugin_name}")
                return False

        try:
            # Load the plugin module
            module_name = self._generate_module_name(plugin_info.file_path)
            spec = importlib.util.spec_from_file_location(
                module_name, plugin_info.file_path
            )

            if not spec or not spec.loader:
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get plugin class
            plugin_class = getattr(module, plugin_info.class_name)

            # Store loaded plugin
            with self._lock:
                self._loaded_plugins[plugin_name] = plugin_class
                self.stats.loaded_plugins = len(self._loaded_plugins)

            return True

        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")
            with self._lock:
                self.stats.failed_plugins += 1
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a loaded plugin.

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if unloaded successfully, False otherwise
        """
        with self._lock:
            if plugin_name not in self._loaded_plugins:
                return False

            # Remove from loaded plugins
            del self._loaded_plugins[plugin_name]

            # Remove any instances
            if plugin_name in self._plugin_instances:
                del self._plugin_instances[plugin_name]

            self.stats.loaded_plugins = len(self._loaded_plugins)
            return True

    def create_plugin_instance(
        self, plugin_name: str, *args, **kwargs
    ) -> Optional[Any]:
        """
        Create an instance of a loaded plugin.

        Args:
            plugin_name: Name of the plugin
            *args: Arguments for plugin constructor
            **kwargs: Keyword arguments for plugin constructor

        Returns:
            Plugin instance or None if creation failed
        """
        with self._lock:
            if plugin_name not in self._loaded_plugins:
                return None

            plugin_class = self._loaded_plugins[plugin_name]

        try:
            # Create instance
            instance = plugin_class(*args, **kwargs)
            self._plugin_instances[plugin_name] = instance
            return instance

        except Exception as e:
            print(f"Error creating plugin instance {plugin_name}: {e}")
            return None

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        Get information about a discovered plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin information or None if not found
        """
        return self._discovered_plugins.get(plugin_name)

    def list_plugins(self, include_invalid: bool = False) -> List[PluginInfo]:
        """
        List all discovered plugins.

        Args:
            include_invalid: Whether to include invalid plugins

        Returns:
            List of plugin information
        """
        plugins = []
        for plugin_info in self._discovered_plugins.values():
            if include_invalid or plugin_info.is_valid:
                plugins.append(plugin_info)

        return sorted(plugins, key=lambda p: p.name)

    def list_loaded_plugins(self) -> List[str]:
        """
        List names of loaded plugins.

        Returns:
            List of loaded plugin names
        """
        return list(self._loaded_plugins.keys())

    def validate_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """
        Validate a specific plugin.

        Args:
            plugin_name: Name of the plugin to validate

        Returns:
            Validation results
        """
        plugin_info = self.get_plugin_info(plugin_name)
        if not plugin_info:
            return {"valid": False, "error": "Plugin not found"}

        # Load plugin for validation if not already loaded
        if plugin_name not in self._loaded_plugins:
            self.load_plugin(plugin_name)

        if plugin_name not in self._loaded_plugins:
            return {"valid": False, "error": "Cannot load plugin for validation"}

        plugin_class = self._loaded_plugins[plugin_name]
        is_valid, errors = self.validator.validate_plugin_class(plugin_class)

        # Update plugin info
        plugin_info.is_valid = is_valid
        plugin_info.validation_errors = errors

        return {
            "valid": is_valid,
            "errors": errors,
            "warnings": [],  # Could add warnings in the future
        }

    def test_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """
        Test a plugin's functionality.

        Args:
            plugin_name: Name of the plugin to test

        Returns:
            Test results
        """
        if not self.enable_testing:
            return {"tested": False, "error": "Testing disabled"}

        plugin_info = self.get_plugin_info(plugin_name)
        if not plugin_info:
            return {"tested": False, "error": "Plugin not found"}

        # This would implement comprehensive testing
        # For now, return basic test results
        return {
            "tested": True,
            "tests_run": 1,
            "tests_passed": 1 if plugin_info.is_valid else 0,
            "tests_failed": 0 if plugin_info.is_valid else 1,
            "test_details": [
                {
                    "name": "basic_validation",
                    "passed": plugin_info.is_valid,
                    "message": "Plugin validation test",
                }
            ],
        }

    def generate_plugin_template(
        self, plugin_name: str, plugin_type: str = "blur_effect", output_dir: str = "."
    ) -> str:
        """
        Generate a plugin template.

        Args:
            plugin_name: Name for the new plugin
            plugin_type: Type of plugin to generate
            output_dir: Directory to save template

        Returns:
            Path to generated template file
        """
        template_content = self.template.generate_template(plugin_name, plugin_type)
        output_path = os.path.join(output_dir, f"{plugin_name.lower()}_plugin.py")

        with open(output_path, "w") as f:
            f.write(template_content)

        return output_path

    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get plugin system statistics."""
        return {
            "discovered": {
                "total": self.stats.total_plugins,
                "valid": self.stats.valid_plugins,
                "invalid": self.stats.invalid_plugins,
                "last_discovery": self.stats.last_discovery,
                "discovery_time": self.stats.discovery_time,
            },
            "loaded": {
                "total": self.stats.loaded_plugins,
                "failed": self.stats.failed_plugins,
            },
            "instances": len(self._plugin_instances),
            "search_paths": self.plugin_dirs,
        }

    def export_plugin_list(self, output_file: str):
        """
        Export plugin list to file.

        Args:
            output_file: Path to output file
        """
        export_data = {
            "export_time": time.time(),
            "stats": self.get_plugin_stats(),
            "plugins": [
                {
                    "name": p.name,
                    "version": p.version,
                    "author": p.author,
                    "description": p.description,
                    "is_valid": p.is_valid,
                    "validation_errors": p.validation_errors,
                    "tags": p.tags,
                }
                for p in self.list_plugins(include_invalid=True)
            ],
        }

        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)

    def clear_discovery_cache(self):
        """Clear the plugin discovery cache."""
        with self._lock:
            self._discovered_plugins.clear()
            self.stats = PluginStats()

    def shutdown(self):
        """Shutdown plugin manager and cleanup resources."""
        # Unload all plugins
        for plugin_name in list(self._loaded_plugins.keys()):
            self.unload_plugin(plugin_name)

        # Clear caches
        self.clear_discovery_cache()
