"""
Configuration Manager

Central configuration management with hierarchical inheritance,
validation, and runtime updates.
"""

import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ConfigLayer:
    """Configuration layer with metadata."""

    name: str
    data: Dict[str, Any]
    priority: int = 0
    source: str = "memory"
    created_at: float = field(default_factory=time.time)
    is_readonly: bool = False


class ConfigManager:
    """
    Advanced configuration manager with hierarchical inheritance.

    Supports multiple configuration sources with priority-based
    inheritance, runtime validation, and dynamic updates.
    """

    def __init__(self, schema: Optional[Any] = None):
        """
        Initialize configuration manager.

        Args:
            schema: Configuration schema for validation
        """
        self.schema = schema
        self._layers: Dict[str, ConfigLayer] = {}
        self._lock = threading.RLock()
        self._change_listeners: List[callable] = []

        # Configuration metadata
        self._metadata = {
            "created_at": time.time(),
            "last_modified": time.time(),
            "version": "1.0.0",
        }

    def add_config_layer(
        self,
        name: str,
        config_data: Dict[str, Any],
        priority: int = 0,
        source: str = "memory",
        readonly: bool = False,
    ):
        """
        Add a configuration layer.

        Args:
            name: Layer name
            config_data: Configuration data
            priority: Layer priority (higher = overrides lower)
            source: Configuration source description
            readonly: Whether layer can be modified
        """
        layer = ConfigLayer(
            name=name,
            data=config_data.copy(),
            priority=priority,
            source=source,
            is_readonly=readonly,
        )

        with self._lock:
            self._layers[name] = layer
            self._metadata["last_modified"] = time.time()

        # Notify listeners
        self._notify_change_listeners(name, "added", config_data)

    def remove_config_layer(self, name: str) -> bool:
        """
        Remove a configuration layer.

        Args:
            name: Layer name to remove

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if name not in self._layers:
                return False

            layer = self._layers[name]
            del self._layers[name]
            self._metadata["last_modified"] = time.time()

        # Notify listeners
        self._notify_change_listeners(name, "removed", layer.data)
        return True

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with inheritance.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        with self._lock:
            # Get layers sorted by priority (highest first)
            sorted_layers = sorted(
                self._layers.values(), key=lambda l: l.priority, reverse=True
            )

            # Search through layers
            for layer in sorted_layers:
                value = self._get_nested_value(layer.data, key)
                if value is not None:
                    return value

            return default

    def set_config_value(self, key: str, value: Any, layer: str = "default"):
        """
        Set configuration value in a specific layer.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            layer: Layer name to modify
        """
        with self._lock:
            if layer not in self._layers:
                # Create layer if it doesn't exist
                self._layers[layer] = ConfigLayer(
                    name=layer, data={}, priority=0, source="runtime"
                )

            target_layer = self._layers[layer]

            if target_layer.is_readonly:
                raise ValueError(f"Cannot modify readonly layer: {layer}")

            # Set nested value
            self._set_nested_value(target_layer.data, key, value)
            self._metadata["last_modified"] = time.time()

        # Notify listeners
        self._notify_change_listeners(layer, "modified", {key: value})

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get nested value using dot notation."""
        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current

    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any):
        """Set nested value using dot notation."""
        keys = key.split(".")
        current = data

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the value
        current[keys[-1]] = value

    def get_all_config(self) -> Dict[str, Any]:
        """
        Get merged configuration from all layers.

        Returns:
            Merged configuration dictionary
        """
        with self._lock:
            merged_config = {}

            # Get layers sorted by priority (highest first)
            sorted_layers = sorted(
                self._layers.values(), key=lambda l: l.priority, reverse=True
            )

            # Merge layers
            for layer in sorted_layers:
                self._merge_config_recursive(merged_config, layer.data)

            return merged_config

    def _merge_config_recursive(self, base: Dict[str, Any], overlay: Dict[str, Any]):
        """Recursively merge configuration dictionaries."""
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config_recursive(base[key], value)
            else:
                base[key] = value

    def load_config_file(
        self, file_path: str, layer_name: str = "file", priority: int = 0
    ):
        """
        Load configuration from file.

        Args:
            file_path: Path to configuration file
            layer_name: Name for the configuration layer
            priority: Layer priority
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        # Determine file type and load
        file_ext = Path(file_path).suffix.lower()

        if file_ext in [".json"]:
            with open(file_path, "r") as f:
                config_data = json.load(f)
        elif file_ext in [".yaml", ".yml"]:
            with open(file_path, "r") as f:
                config_data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {file_ext}")

        self.add_config_layer(
            name=layer_name,
            config_data=config_data,
            priority=priority,
            source=f"file:{file_path}",
        )

    def save_config_file(self, file_path: str, layer: str = "default"):
        """
        Save configuration layer to file.

        Args:
            file_path: Path to save configuration
            layer: Layer name to save
        """
        with self._lock:
            if layer not in self._layers:
                raise ValueError(f"Layer not found: {layer}")

            config_data = self._layers[layer].data

        # Determine file type and save
        file_ext = Path(file_path).suffix.lower()

        if file_ext in [".json"]:
            with open(file_path, "w") as f:
                json.dump(config_data, f, indent=2)
        elif file_ext in [".yaml", ".yml"]:
            with open(file_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported configuration file format: {file_ext}")

    def add_change_listener(self, listener: callable):
        """
        Add a configuration change listener.

        Args:
            listener: Function to call on configuration changes
        """
        self._change_listeners.append(listener)

    def remove_change_listener(self, listener: callable):
        """
        Remove a configuration change listener.

        Args:
            listener: Listener function to remove
        """
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

    def _notify_change_listeners(self, layer: str, action: str, data: Any):
        """Notify change listeners."""
        for listener in self._change_listeners:
            try:
                listener(layer, action, data)
            except Exception:
                # Continue with other listeners
                pass

    def validate_config(self) -> List[str]:
        """
        Validate current configuration against schema.

        Returns:
            List of validation errors (empty if valid)
        """
        if not self.schema:
            return []

        current_config = self.get_all_config()
        return self.schema.validate(current_config)

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary."""
        with self._lock:
            layers = []
            for name, layer in self._layers.items():
                layers.append(
                    {
                        "name": name,
                        "priority": layer.priority,
                        "source": layer.source,
                        "readonly": layer.is_readonly,
                        "key_count": self._count_keys(layer.data),
                        "created_at": layer.created_at,
                    }
                )

            return {
                "total_layers": len(self._layers),
                "layers": sorted(layers, key=lambda l: l["priority"], reverse=True),
                "metadata": self._metadata.copy(),
                "has_schema": self.schema is not None,
                "validation_errors": len(self.validate_config()) if self.schema else 0,
            }

    def _count_keys(self, data: Dict[str, Any]) -> int:
        """Count total keys in nested dictionary."""
        count = 0

        def count_recursive(d):
            nonlocal count
            for v in d.values():
                count += 1
                if isinstance(v, dict):
                    count_recursive(v)

        count_recursive(data)
        return count

    def export_config(self, format: str = "json") -> str:
        """
        Export current configuration.

        Args:
            format: Export format ('json' or 'yaml')

        Returns:
            Configuration as formatted string
        """
        config = self.get_all_config()

        if format.lower() == "json":
            return json.dumps(config, indent=2)
        elif format.lower() in ["yaml", "yml"]:
            return yaml.dump(config, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def import_config(
        self,
        config_string: str,
        format: str = "json",
        layer_name: str = "imported",
        priority: int = 0,
    ):
        """
        Import configuration from string.

        Args:
            config_string: Configuration as string
            format: Import format ('json' or 'yaml')
            layer_name: Name for imported layer
            priority: Layer priority
        """
        if format.lower() == "json":
            config_data = json.loads(config_string)
        elif format.lower() in ["yaml", "yml"]:
            config_data = yaml.safe_load(config_string)
        else:
            raise ValueError(f"Unsupported import format: {format}")

        self.add_config_layer(
            name=layer_name,
            config_data=config_data,
            priority=priority,
            source=f"import:{format}",
        )

    def reset_to_defaults(self, layer: str = "default"):
        """
        Reset a layer to empty configuration.

        Args:
            layer: Layer name to reset
        """
        with self._lock:
            if layer in self._layers:
                self._layers[layer].data.clear()
                self._metadata["last_modified"] = time.time()

        self._notify_change_listeners(layer, "reset", {})

    def get_layer_info(self, layer_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific layer.

        Args:
            layer_name: Name of the layer

        Returns:
            Layer information or None if not found
        """
        with self._lock:
            if layer_name not in self._layers:
                return None

            layer = self._layers[layer_name]
            return {
                "name": layer.name,
                "priority": layer.priority,
                "source": layer.source,
                "readonly": layer.is_readonly,
                "key_count": self._count_keys(layer.data),
                "created_at": layer.created_at,
            }

    def list_layers(self) -> List[str]:
        """List all configuration layer names."""
        with self._lock:
            return list(self._layers.keys())

    def get_effective_config_for_key(self, key: str) -> Dict[str, Any]:
        """
        Get effective configuration for a specific key.

        Args:
            key: Configuration key

        Returns:
            Information about which layers define this key
        """
        with self._lock:
            layer_info = {}

            # Check each layer for the key
            for name, layer in self._layers.items():
                value = self._get_nested_value(layer.data, key)
                if value is not None:
                    layer_info[name] = {
                        "value": value,
                        "priority": layer.priority,
                        "source": layer.source,
                    }

            return layer_info


class ConfigurationContext:
    """
    Context manager for temporary configuration changes.
    """

    def __init__(self, config_manager: ConfigManager, layer: str = "temp"):
        """
        Initialize configuration context.

        Args:
            config_manager: Configuration manager instance
            layer: Temporary layer name
        """
        self.config_manager = config_manager
        self.layer = layer
        self._original_values = {}

    def __enter__(self):
        """Enter configuration context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit configuration context and restore values."""
        # Restore original values
        for key, value in self._original_values.items():
            if value is None:
                # Key should be removed
                try:
                    del self.config_manager._layers[self.layer].data[key]
                except (KeyError, AttributeError):
                    pass
            else:
                self.config_manager.set_config_value(key, value, self.layer)

    def set_temp_value(self, key: str, value: Any):
        """
        Set a temporary configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        # Store original value
        original_value = self.config_manager.get_config_value(key)
        self._original_values[key] = original_value

        # Set new value
        self.config_manager.set_config_value(key, value, self.layer)


def create_default_config() -> Dict[str, Any]:
    """Create default configuration for Blur Suite."""
    return {
        "blur_suite": {
            "version": "1.0.0",
            "debug": False,
            "log_level": "INFO",
            "performance": {
                "enable_caching": True,
                "cache_size_mb": 100,
                "enable_parallel": True,
                "max_workers": None,
                "memory_limit_mb": None,
            },
            "plugins": {
                "auto_discovery": True,
                "search_paths": [],
                "enable_validation": True,
                "enable_testing": False,
            },
            "monitoring": {
                "enable_metrics": True,
                "enable_health_checks": True,
                "metrics_interval": 60,
                "health_check_interval": 300,
            },
        }
    }
