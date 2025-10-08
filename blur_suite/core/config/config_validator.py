"""
Configuration Validator

Runtime configuration validation and constraint checking.
"""

import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class ConfigValidator:
    """
    Runtime configuration validator.

    Validates configuration values, checks constraints,
    and provides suggestions for optimization.
    """

    def __init__(self):
        """Initialize configuration validator."""
        self.custom_validators: Dict[str, Callable] = {}
        self.validation_history: List[ValidationResult] = []

    def add_custom_validator(self, key_pattern: str, validator: Callable):
        """
        Add a custom validator for specific configuration keys.

        Args:
            key_pattern: Key pattern (supports wildcards)
            validator: Validation function
        """
        self.custom_validators[key_pattern] = validator

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete configuration.

        Args:
            config: Configuration to validate

        Returns:
            Validation result
        """
        errors = []
        warnings = []
        suggestions = []

        # Run standard validations
        errors.extend(self._validate_basic_structure(config))
        errors.extend(self._validate_performance_settings(config))
        errors.extend(self._validate_plugin_settings(config))
        errors.extend(self._validate_file_paths(config))
        errors.extend(self._validate_numeric_ranges(config))

        # Run custom validators
        for key_pattern, validator in self.custom_validators.items():
            custom_errors = self._run_custom_validator(config, key_pattern, validator)
            errors.extend(custom_errors)

        # Generate warnings
        warnings.extend(self._generate_warnings(config))

        # Generate suggestions
        suggestions.extend(self._generate_suggestions(config))

        result = ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

        # Store in history
        self.validation_history.append(result)

        # Keep only recent history
        if len(self.validation_history) > 10:
            self.validation_history.pop(0)

        return result

    def _validate_basic_structure(self, config: Dict[str, Any]) -> List[str]:
        """Validate basic configuration structure."""
        errors = []

        # Check for required top-level sections
        required_sections = ["blur_suite"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Required configuration section missing: {section}")

        # Check blur_suite section
        if "blur_suite" in config:
            bs_config = config["blur_suite"]

            # Check version
            if "version" in bs_config:
                version = bs_config["version"]
                if not isinstance(version, str):
                    errors.append("blur_suite.version must be a string")

            # Check debug mode
            if "debug" in bs_config:
                debug = bs_config["debug"]
                if not isinstance(debug, bool):
                    errors.append("blur_suite.debug must be a boolean")

            # Check log level
            if "log_level" in bs_config:
                log_level = bs_config["log_level"]
                valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                if log_level not in valid_levels:
                    errors.append(
                        f"blur_suite.log_level must be one of: {valid_levels}"
                    )

        return errors

    def _validate_performance_settings(self, config: Dict[str, Any]) -> List[str]:
        """Validate performance-related settings."""
        errors = []

        if "blur_suite" not in config:
            return errors

        bs_config = config["blur_suite"]

        if "performance" in bs_config:
            perf_config = bs_config["performance"]

            # Validate cache size
            if "cache_size_mb" in perf_config:
                cache_size = perf_config["cache_size_mb"]
                if not isinstance(cache_size, (int, float)) or cache_size < 10:
                    errors.append("performance.cache_size_mb must be >= 10 MB")

            # Validate max workers
            if "max_workers" in perf_config:
                max_workers = perf_config["max_workers"]
                if max_workers is not None:
                    if not isinstance(max_workers, int) or max_workers < 1:
                        errors.append("performance.max_workers must be >= 1 or None")
                    elif max_workers > 32:
                        errors.append("performance.max_workers should not exceed 32")

            # Validate memory limit
            if "memory_limit_mb" in perf_config:
                memory_limit = perf_config["memory_limit_mb"]
                if memory_limit is not None:
                    if not isinstance(memory_limit, (int, float)) or memory_limit < 100:
                        errors.append(
                            "performance.memory_limit_mb must be >= 100 MB or None"
                        )

        return errors

    def _validate_plugin_settings(self, config: Dict[str, Any]) -> List[str]:
        """Validate plugin-related settings."""
        errors = []

        if "blur_suite" not in config:
            return errors

        bs_config = config["blur_suite"]

        if "plugins" in bs_config:
            plugin_config = bs_config["plugins"]

            # Validate search paths
            if "search_paths" in plugin_config:
                search_paths = plugin_config["search_paths"]
                if not isinstance(search_paths, list):
                    errors.append("plugins.search_paths must be a list")
                else:
                    for path in search_paths:
                        if not isinstance(path, str):
                            errors.append(
                                "plugins.search_paths must contain only strings"
                            )
                            break

            # Validate auto_discovery
            if "auto_discovery" in plugin_config:
                auto_discovery = plugin_config["auto_discovery"]
                if not isinstance(auto_discovery, bool):
                    errors.append("plugins.auto_discovery must be a boolean")

        return errors

    def _validate_file_paths(self, config: Dict[str, Any]) -> List[str]:
        """Validate file path settings."""
        errors = []

        # Check for file path configurations
        paths_to_check = []

        # Collect paths from configuration
        self._collect_paths_from_config(config, paths_to_check)

        # Validate each path
        for path_info in paths_to_check:
            path = path_info["value"]
            path_type = path_info["type"]
            config_path = path_info["config_path"]

            if not isinstance(path, str):
                continue

            # Check if path exists (for input paths)
            if path_type in ["input", "input_dir"] and not os.path.exists(path):
                errors.append(
                    f"Input path does not exist: {path} (configured at {config_path})"
                )

            # Check if parent directory exists (for output paths)
            elif path_type in ["output", "output_dir"]:
                parent_dir = os.path.dirname(path)
                if parent_dir and not os.path.exists(parent_dir):
                    errors.append(
                        f"Parent directory does not exist: {parent_dir} (configured at {config_path})"
                    )

            # Validate path format
            if ".." in path:
                errors.append(
                    f"Path contains '..': {path} (configured at {config_path})"
                )

        return errors

    def _collect_paths_from_config(
        self, config: Dict[str, Any], paths: List[Dict[str, Any]]
    ):
        """Collect file paths from configuration."""

        def collect_recursive(cfg: Dict[str, Any], current_path: str = ""):
            for key, value in cfg.items():
                full_path = f"{current_path}.{key}" if current_path else key

                if isinstance(value, dict):
                    collect_recursive(value, full_path)
                elif isinstance(value, str) and self._is_path_like_key(key):
                    # Determine path type based on key name
                    if any(word in key.lower() for word in ["input", "source", "read"]):
                        path_type = "input"
                    elif any(
                        word in key.lower() for word in ["output", "write", "save"]
                    ):
                        path_type = "output"
                    elif "dir" in key.lower() or "path" in key.lower():
                        path_type = "path"
                    else:
                        path_type = "unknown"

                    paths.append(
                        {"value": value, "type": path_type, "config_path": full_path}
                    )

        collect_recursive(config)

    def _is_path_like_key(self, key: str) -> bool:
        """Check if a key likely contains a file path."""
        path_indicators = ["path", "file", "dir", "input", "output", "log"]
        return any(indicator in key.lower() for indicator in path_indicators)

    def _validate_numeric_ranges(self, config: Dict[str, Any]) -> List[str]:
        """Validate numeric ranges and constraints."""
        errors = []

        # Define known numeric constraints
        constraints = {
            "blur_suite.performance.cache_size_mb": {"min": 10, "max": 10000},
            "blur_suite.performance.max_workers": {"min": 1, "max": 32},
            "blur_suite.performance.memory_limit_mb": {"min": 100, "max": None},
        }

        for config_path, constraint in constraints.items():
            value = self._get_nested_config_value(config, config_path)
            if value is None:
                continue

            if not isinstance(value, (int, float)):
                errors.append(f"Value at {config_path} must be numeric")
                continue

            if constraint["min"] is not None and value < constraint["min"]:
                errors.append(f"Value at {config_path} must be >= {constraint['min']}")

            if constraint["max"] is not None and value > constraint["max"]:
                errors.append(f"Value at {config_path} must be <= {constraint['max']}")

        return errors

    def _run_custom_validator(
        self, config: Dict[str, Any], pattern: str, validator: Callable
    ) -> List[str]:
        """Run custom validator on matching keys."""
        errors = []

        try:
            # Find keys matching pattern
            matching_keys = self._find_keys_matching_pattern(config, pattern)

            for key in matching_keys:
                value = self._get_nested_config_value(config, key)
                try:
                    validator(value)
                except ValueError as e:
                    errors.append(f"Validation failed for {key}: {str(e)}")

        except Exception as e:
            errors.append(f"Custom validator error for pattern {pattern}: {str(e)}")

        return errors

    def _find_keys_matching_pattern(
        self, config: Dict[str, Any], pattern: str
    ) -> List[str]:
        """Find configuration keys matching a pattern."""
        matching_keys = []

        def search_recursive(cfg: Dict[str, Any], current_path: str = ""):
            for key, value in cfg.items():
                full_path = f"{current_path}.{key}" if current_path else key

                # Check if this key matches the pattern
                if self._matches_pattern(full_path, pattern):
                    matching_keys.append(full_path)

                if isinstance(value, dict):
                    search_recursive(value, full_path)

        search_recursive(config)
        return matching_keys

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (supports wildcards)."""
        # Convert pattern to regex
        regex_pattern = pattern.replace(".", "\\.").replace("*", ".*")
        return re.match(f"^{regex_pattern}$", key) is not None

    def _get_nested_config_value(self, config: Dict[str, Any], path: str) -> Any:
        """Get nested value from configuration."""
        keys = path.split(".")
        current = config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _generate_warnings(self, config: Dict[str, Any]) -> List[str]:
        """Generate configuration warnings."""
        warnings = []

        # Check for potentially problematic settings
        if "blur_suite" in config:
            bs_config = config["blur_suite"]

            # Debug mode in production-like environment
            if bs_config.get("debug", False):
                warnings.append("Debug mode is enabled - ensure this is intentional")

            # High log level in production
            if bs_config.get("log_level") in ["DEBUG", "INFO"]:
                warnings.append(
                    "Log level is set to DEBUG/INFO - consider WARNING for production"
                )

            # Performance warnings
            if "performance" in bs_config:
                perf_config = bs_config["performance"]

                # Large cache size
                cache_size = perf_config.get("cache_size_mb", 100)
                if cache_size > 1000:
                    warnings.append(
                        f"Large cache size ({cache_size}MB) may impact memory usage"
                    )

                # Too many workers
                max_workers = perf_config.get("max_workers")
                if max_workers and max_workers > 16:
                    warnings.append(
                        f"High worker count ({max_workers}) may not improve performance"
                    )

        return warnings

    def _generate_suggestions(self, config: Dict[str, Any]) -> List[str]:
        """Generate configuration suggestions."""
        suggestions = []

        if "blur_suite" in config:
            bs_config = config["blur_suite"]

            # Performance suggestions
            if "performance" in bs_config:
                perf_config = bs_config["performance"]

                # Suggest enabling caching if disabled
                if not perf_config.get("enable_caching", True):
                    suggestions.append(
                        "Consider enabling caching for better performance"
                    )

                # Suggest parallel processing
                if not perf_config.get("enable_parallel", True):
                    suggestions.append(
                        "Consider enabling parallel processing for large workloads"
                    )

                # Suggest appropriate cache size based on available memory
                cache_size = perf_config.get("cache_size_mb", 100)
                if cache_size < 50:
                    suggestions.append(
                        "Consider increasing cache size for better performance"
                    )

            # Plugin suggestions
            if "plugins" in bs_config:
                plugin_config = bs_config["plugins"]

                if not plugin_config.get("auto_discovery", True):
                    suggestions.append(
                        "Enable auto_discovery to automatically find plugins"
                    )

    def get_validation_history(self) -> List[ValidationResult]:
        """Get validation history."""
        return self.validation_history.copy()

    def clear_validation_history(self):
        """Clear validation history."""
        self.validation_history.clear()

    def export_validation_report(self, format: str = "text") -> str:
        """
        Export validation report.

        Args:
            format: Report format ('text' or 'json')

        Returns:
            Validation report
        """
        if not self.validation_history:
            return "No validation history available"

        latest_result = self.validation_history[-1]

        if format == "json":
            import json

            return json.dumps(
                {
                    "is_valid": latest_result.is_valid,
                    "error_count": len(latest_result.errors),
                    "warning_count": len(latest_result.warnings),
                    "suggestion_count": len(latest_result.suggestions),
                    "errors": latest_result.errors,
                    "warnings": latest_result.warnings,
                    "suggestions": latest_result.suggestions,
                },
                indent=2,
            )
        else:
            # Text format
            report = []
            report.append("Configuration Validation Report")
            report.append("=" * 40)
            report.append(f"Valid: {'Yes' if latest_result.is_valid else 'No'}")
            report.append(f"Errors: {len(latest_result.errors)}")
            report.append(f"Warnings: {len(latest_result.warnings)}")
            report.append(f"Suggestions: {len(latest_result.suggestions)}")
            report.append("")

            if latest_result.errors:
                report.append("Errors:")
                for error in latest_result.errors:
                    report.append(f"  - {error}")
                report.append("")

            if latest_result.warnings:
                report.append("Warnings:")
                for warning in latest_result.warnings:
                    report.append(f"  - {warning}")
                report.append("")

            if latest_result.suggestions:
                report.append("Suggestions:")
                for suggestion in latest_result.suggestions:
                    report.append(f"  - {suggestion}")
                report.append("")

            return "\n".join(report)
