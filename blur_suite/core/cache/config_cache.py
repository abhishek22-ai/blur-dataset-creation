"""
Configuration Cache

Specialized caching for configuration parsing and validation results.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .cache_manager import CacheManager


class ConfigCache:
    """
    Specialized cache for configuration operations.

    Handles caching of configuration parsing, validation,
    and preprocessing results.
    """

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize config cache.

        Args:
            cache_manager: Parent cache manager instance
        """
        self.cache_manager = cache_manager

    def _generate_config_key(
        self, config_source: str, config_type: str = "dict"
    ) -> str:
        """Generate cache key for configuration."""
        key_data = {"source": config_source, "type": config_type}
        key_str = json.dumps(key_data, sort_keys=True)
        return f"config:{hashlib.sha256(key_str.encode()).hexdigest()}"

    def _generate_validation_key(
        self, config: Dict[str, Any], schema: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key for validation results."""
        key_data = {
            "config_hash": hashlib.sha256(
                json.dumps(config, sort_keys=True).encode()
            ).hexdigest(),
            "schema_hash": hashlib.sha256(
                json.dumps(schema or {}, sort_keys=True).encode()
            ).hexdigest(),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return f"validation:{hashlib.sha256(key_str.encode()).hexdigest()}"

    def get_parsed_config(
        self, config_source: str, config_type: str = "dict"
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached parsed configuration.

        Args:
            config_source: Configuration source (file path or content)
            config_type: Type of configuration ('dict', 'file', 'json', etc.)

        Returns:
            Cached parsed config or None if not found
        """
        key = self._generate_config_key(config_source, config_type)
        return self.cache_manager.get(key)

    def cache_parsed_config(
        self, config_source: str, config_type: str, config: Dict[str, Any]
    ):
        """
        Cache parsed configuration.

        Args:
            config_source: Configuration source
            config_type: Type of configuration
            config: Parsed configuration
        """
        key = self._generate_config_key(config_source, config_type)
        size_bytes = len(json.dumps(config).encode("utf-8"))
        self.cache_manager.put(
            key, config, size_bytes=size_bytes, ttl=3600
        )  # 1 hour TTL

    def get_validation_result(
        self, config: Dict[str, Any], schema: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached validation result.

        Args:
            config: Configuration to validate
            schema: Validation schema

        Returns:
            Cached validation result or None if not found
        """
        key = self._generate_validation_key(config, schema)
        return self.cache_manager.get(key)

    def cache_validation_result(
        self,
        config: Dict[str, Any],
        schema: Optional[Dict[str, Any]],
        result: Dict[str, Any],
    ):
        """
        Cache validation result.

        Args:
            config: Configuration that was validated
            schema: Validation schema used
            result: Validation result
        """
        key = self._generate_validation_key(config, schema)
        size_bytes = len(json.dumps(result).encode("utf-8"))
        self.cache_manager.put(
            key, result, size_bytes=size_bytes, ttl=1800
        )  # 30 min TTL

    def parse_config_cached(
        self, config_source: str, config_type: str, parser_func
    ) -> Dict[str, Any]:
        """
        Parse configuration with caching.

        Args:
            config_source: Configuration source
            config_type: Type of configuration
            parser_func: Function that parses the configuration

        Returns:
            Parsed configuration
        """
        # Check cache first
        cached_config = self.get_parsed_config(config_source, config_type)
        if cached_config is not None:
            return cached_config

        # Parse configuration
        config = parser_func(config_source)

        # Cache the result
        self.cache_parsed_config(config_source, config_type, config)

        return config

    def validate_config_cached(
        self, config: Dict[str, Any], schema: Optional[Dict[str, Any]], validator_func
    ) -> Dict[str, Any]:
        """
        Validate configuration with caching.

        Args:
            config: Configuration to validate
            schema: Validation schema
            validator_func: Function that validates the configuration

        Returns:
            Validation result
        """
        # Check cache first
        cached_result = self.get_validation_result(config, schema)
        if cached_result is not None:
            return cached_result

        # Validate configuration
        result = validator_func(config, schema)

        # Cache the result
        self.cache_validation_result(config, schema, result)

        return result

    def load_config_file_cached(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration file with caching.

        Args:
            config_path: Path to configuration file

        Returns:
            Loaded and parsed configuration
        """
        config_path = str(config_path)

        def load_and_parse_config(path: str) -> Dict[str, Any]:
            """Load and parse configuration file."""
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Try JSON first
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Try YAML if available
                    try:
                        import yaml

                        return yaml.safe_load(content)
                    except ImportError:
                        # Fallback to simple key=value parsing
                        config = {}
                        for line in content.strip().split("\n"):
                            if "=" in line and not line.strip().startswith("#"):
                                key, value = line.split("=", 1)
                                config[key.strip()] = value.strip()
                        return config

            except Exception as e:
                raise ValueError(f"Failed to load config file {path}: {e}")

        return self.parse_config_cached(config_path, "file", load_and_parse_config)

    def clear_config_cache(self, config_source: Optional[str] = None):
        """
        Clear configuration cache entries.

        Args:
            config_source: Specific config source to clear, or None for all
        """
        keys_to_remove = []
        for key in self.cache_manager._cache.keys():
            if key.startswith("config:"):
                if config_source is None:
                    keys_to_remove.append(key)
                elif config_source in key:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            self.cache_manager._cache.pop(key, None)

    def clear_validation_cache(self):
        """Clear all validation cache entries."""
        keys_to_remove = [
            key
            for key in self.cache_manager._cache.keys()
            if key.startswith("validation:")
        ]
        for key in keys_to_remove:
            self.cache_manager._cache.pop(key, None)

    def get_cache_info(self) -> Dict[str, Any]:
        """Get configuration cache statistics."""
        config_keys = [
            key for key in self.cache_manager._cache.keys() if key.startswith("config:")
        ]
        validation_keys = [
            key
            for key in self.cache_manager._cache.keys()
            if key.startswith("validation:")
        ]

        config_size = sum(
            entry.size_bytes
            for key, entry in self.cache_manager._cache.items()
            if key.startswith("config:")
        )
        validation_size = sum(
            entry.size_bytes
            for key, entry in self.cache_manager._cache.items()
            if key.startswith("validation:")
        )

        return {
            "cached_configs": len(config_keys),
            "cached_validations": len(validation_keys),
            "config_cache_size_bytes": config_size,
            "validation_cache_size_bytes": validation_size,
            "config_cache_size_mb": config_size / (1024 * 1024),
            "validation_cache_size_mb": validation_size / (1024 * 1024),
        }

    def preload_common_configs(self, config_paths: list):
        """
        Preload common configuration files.

        Args:
            config_paths: List of configuration file paths to preload
        """
        for path in config_paths:
            try:
                self.load_config_file_cached(path)
            except Exception as e:
                # Log warning but continue with other configs
                print(f"Warning: Could not preload config {path}: {e}")
