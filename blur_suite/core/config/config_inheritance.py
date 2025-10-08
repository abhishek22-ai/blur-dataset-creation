"""
Configuration Inheritance

Hierarchical configuration inheritance with environment-specific
overrides and conditional logic.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class InheritanceRule:
    """Rule for configuration inheritance."""

    condition: str
    source_layer: str
    target_path: str
    merge_strategy: str = "override"  # override, merge, append, prepend


class ConfigInheritance:
    """
    Configuration inheritance system.

    Supports hierarchical configuration with environment-specific
    overrides, conditional inheritance, and merge strategies.
    """

    def __init__(self):
        """Initialize configuration inheritance system."""
        self.inheritance_rules: List[InheritanceRule] = []
        self.environment_variables = self._get_environment_variables()
        self.system_info = self._get_system_info()

    def _get_environment_variables(self) -> Dict[str, str]:
        """Get relevant environment variables."""
        env_vars = {}

        # Common environment variables for configuration
        config_env_vars = [
            "BLUR_SUITE_CONFIG",
            "BLUR_SUITE_DEBUG",
            "BLUR_SUITE_LOG_LEVEL",
            "BLUR_SUITE_CACHE_SIZE",
            "BLUR_SUITE_MAX_WORKERS",
            "HOME",
            "USER",
            "USERNAME",
            "COMPUTERNAME",
            "HOSTNAME",
        ]

        for var in config_env_vars:
            if var in os.environ:
                env_vars[var] = os.environ[var]

        return env_vars

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for conditional configuration."""
        try:
            import platform

            import psutil

            return {
                "platform": platform.platform(),
                "system": platform.system(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "cpu_count": os.cpu_count(),
                "memory_gb": psutil.virtual_memory().total / (1024**3)
                if psutil
                else None,
                "hostname": platform.node(),
            }
        except Exception:
            return {
                "platform": "unknown",
                "system": "unknown",
                "cpu_count": os.cpu_count() or 1,
            }

    def add_inheritance_rule(
        self,
        condition: str,
        source_layer: str,
        target_path: str,
        merge_strategy: str = "override",
    ):
        """
        Add an inheritance rule.

        Args:
            condition: Condition for applying inheritance
            source_layer: Source configuration layer
            target_path: Target path in configuration
            merge_strategy: How to merge values
        """
        rule = InheritanceRule(
            condition=condition,
            source_layer=source_layer,
            target_path=target_path,
            merge_strategy=merge_strategy,
        )
        self.inheritance_rules.append(rule)

    def apply_inheritance(
        self,
        base_config: Dict[str, Any],
        environment_configs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Apply inheritance rules to configuration.

        Args:
            base_config: Base configuration
            environment_configs: Environment-specific configurations

        Returns:
            Configuration with inheritance applied
        """
        result_config = self._deep_copy_config(base_config)

        # Apply each inheritance rule
        for rule in self.inheritance_rules:
            if self._evaluate_condition(rule.condition):
                source_config = environment_configs.get(rule.source_layer, {})
                self._apply_merge_rule(result_config, source_config, rule)

        return result_config

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate inheritance condition."""
        try:
            # Simple condition evaluation
            # This could be extended to support more complex expressions

            # Environment variable conditions
            if condition.startswith("env:"):
                var_name = condition[4:]
                return var_name in self.environment_variables

            # System conditions
            elif condition.startswith("system:"):
                system_key = condition[7:]
                return system_key in self.system_info

            # Path existence conditions
            elif condition.startswith("exists:"):
                path = condition[7:]
                return os.path.exists(path)

            # Boolean conditions
            elif condition in ["true", "True", "1", "yes"]:
                return True
            elif condition in ["false", "False", "0", "no"]:
                return False

            # Default to True for unknown conditions
            return True

        except Exception:
            return False

    def _apply_merge_rule(
        self,
        target_config: Dict[str, Any],
        source_config: Dict[str, Any],
        rule: InheritanceRule,
    ):
        """Apply a merge rule to configuration."""
        source_value = self._get_nested_value(source_config, rule.target_path)

        if source_value is None:
            return

        if rule.merge_strategy == "override":
            self._set_nested_value(target_config, rule.target_path, source_value)
        elif rule.merge_strategy == "merge":
            self._merge_nested_values(target_config, rule.target_path, source_value)
        elif rule.merge_strategy == "append":
            self._append_nested_value(target_config, rule.target_path, source_value)
        elif rule.merge_strategy == "prepend":
            self._prepend_nested_value(target_config, rule.target_path, source_value)

    def _get_nested_value(self, config: Dict[str, Any], path: str) -> Any:
        """Get nested value from configuration."""
        keys = path.split(".")
        current = config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Set nested value in configuration."""
        keys = path.split(".")
        current = config

        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _merge_nested_values(self, config: Dict[str, Any], path: str, value: Any):
        """Merge nested values."""
        existing_value = self._get_nested_value(config, path)

        if existing_value is None:
            self._set_nested_value(config, path, value)
        elif isinstance(existing_value, dict) and isinstance(value, dict):
            # Deep merge dictionaries
            for key, val in value.items():
                if (
                    key in existing_value
                    and isinstance(existing_value[key], dict)
                    and isinstance(val, dict)
                ):
                    self._merge_nested_values(config, f"{path}.{key}", val)
                else:
                    self._set_nested_value(config, f"{path}.{key}", val)
        else:
            # Override with new value
            self._set_nested_value(config, path, value)

    def _append_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Append value to existing configuration."""
        existing_value = self._get_nested_value(config, path)

        if existing_value is None:
            self._set_nested_value(
                config, path, [value] if not isinstance(value, list) else value
            )
        elif isinstance(existing_value, list):
            if isinstance(value, list):
                existing_value.extend(value)
            else:
                existing_value.append(value)
        else:
            # Convert to list and append
            self._set_nested_value(config, path, [existing_value, value])

    def _prepend_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Prepend value to existing configuration."""
        existing_value = self._get_nested_value(config, path)

        if existing_value is None:
            self._set_nested_value(
                config, path, [value] if not isinstance(value, list) else value
            )
        elif isinstance(existing_value, list):
            if isinstance(value, list):
                existing_value[0:0] = value
            else:
                existing_value.insert(0, value)
        else:
            # Convert to list and prepend
            self._set_nested_value(config, path, [value, existing_value])

    def _deep_copy_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create deep copy of configuration."""
        import copy

        return copy.deepcopy(config)

    def create_environment_config(
        self, environment: str, base_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create environment-specific configuration.

        Args:
            environment: Environment name (development, production, testing)
            base_config: Base configuration

        Returns:
            Environment-specific configuration
        """
        env_config = self._deep_copy_config(base_config)

        # Apply environment-specific modifications
        if environment == "development":
            self._apply_development_overrides(env_config)
        elif environment == "production":
            self._apply_production_overrides(env_config)
        elif environment == "testing":
            self._apply_testing_overrides(env_config)

        return env_config

    def _apply_development_overrides(self, config: Dict[str, Any]):
        """Apply development environment overrides."""
        # Enable debug mode
        if "blur_suite" in config:
            config["blur_suite"]["debug"] = True
            config["blur_suite"]["log_level"] = "DEBUG"

            # Development-specific performance settings
            if "performance" in config["blur_suite"]:
                config["blur_suite"]["performance"]["enable_caching"] = True
                config["blur_suite"]["performance"]["cache_size_mb"] = 50

    def _apply_production_overrides(self, config: Dict[str, Any]):
        """Apply production environment overrides."""
        # Disable debug mode
        if "blur_suite" in config:
            config["blur_suite"]["debug"] = False
            config["blur_suite"]["log_level"] = "WARNING"

            # Production-specific performance settings
            if "performance" in config["blur_suite"]:
                config["blur_suite"]["performance"]["enable_caching"] = True
                config["blur_suite"]["performance"]["cache_size_mb"] = 500

    def _apply_testing_overrides(self, config: Dict[str, Any]):
        """Apply testing environment overrides."""
        # Testing-specific settings
        if "blur_suite" in config:
            config["blur_suite"]["debug"] = True
            config["blur_suite"]["log_level"] = "DEBUG"

            # Minimal performance settings for testing
            if "performance" in config["blur_suite"]:
                config["blur_suite"]["performance"]["enable_caching"] = False
                config["blur_suite"]["performance"]["enable_parallel"] = False

    def detect_environment(self) -> str:
        """
        Detect current environment.

        Returns:
            Detected environment name
        """
        # Check environment variables
        if "BLUR_SUITE_ENV" in os.environ:
            return os.environ["BLUR_SUITE_ENV"]

        # Check for common environment indicators
        if os.path.exists("/.dockerenv"):
            return "production"

        if "PYTEST_CURRENT_TEST" in os.environ:
            return "testing"

        # Check for development indicators
        if any(
            indicator in os.getcwd().lower()
            for indicator in ["dev", "development", "test"]
        ):
            return "development"

        # Default to production
        return "production"

    def get_conditional_config(
        self, config: Dict[str, Any], conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get configuration based on conditions.

        Args:
            config: Base configuration
            conditions: Condition definitions

        Returns:
            Conditional configuration
        """
        result_config = self._deep_copy_config(config)

        for condition, config_override in conditions.items():
            if self._evaluate_condition(condition):
                self._merge_config_recursive(result_config, config_override)

        return result_config

    def _merge_config_recursive(self, base: Dict[str, Any], overlay: Dict[str, Any]):
        """Recursively merge configuration dictionaries."""
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config_recursive(base[key], value)
            else:
                base[key] = value

    def create_config_variants(
        self, base_config: Dict[str, Any], variants: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create multiple configuration variants.

        Args:
            base_config: Base configuration
            variants: Variant definitions

        Returns:
            Dictionary of configuration variants
        """
        config_variants = {}

        for variant_name, variant_overrides in variants.items():
            variant_config = self._deep_copy_config(base_config)
            self._merge_config_recursive(variant_config, variant_overrides)
            config_variants[variant_name] = variant_config

        return config_variants

    def validate_inheritance_rules(self) -> List[str]:
        """
        Validate inheritance rules.

        Returns:
            List of validation errors
        """
        errors = []

        for i, rule in enumerate(self.inheritance_rules):
            # Check condition syntax
            if not rule.condition or not isinstance(rule.condition, str):
                errors.append(f"Rule {i}: Invalid condition")

            # Check source layer
            if not rule.source_layer or not isinstance(rule.source_layer, str):
                errors.append(f"Rule {i}: Invalid source layer")

            # Check target path
            if not rule.target_path or not isinstance(rule.target_path, str):
                errors.append(f"Rule {i}: Invalid target path")

            # Check merge strategy
            valid_strategies = ["override", "merge", "append", "prepend"]
            if rule.merge_strategy not in valid_strategies:
                errors.append(f"Rule {i}: Invalid merge strategy")

        return errors
