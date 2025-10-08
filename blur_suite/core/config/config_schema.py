"""
Configuration Schema

Schema definition and validation for configuration management.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union


@dataclass
class SchemaField:
    """Schema field definition."""

    name: str
    type: Type
    required: bool = False
    default: Any = None
    validators: List[callable] = field(default_factory=list)
    description: str = ""
    allowed_values: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    regex_pattern: Optional[str] = None
    children: Optional[Dict[str, "SchemaField"]] = None


class ConfigSchema:
    """
    Configuration schema for validation and documentation.

    Defines the structure, types, and constraints for
    configuration values.
    """

    def __init__(self, schema_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration schema.

        Args:
            schema_dict: Schema definition dictionary
        """
        self._schema: Dict[str, SchemaField] = {}
        self._build_schema(schema_dict or self._get_default_schema())

    def _get_default_schema(self) -> Dict[str, Any]:
        """Get default schema for Blur Suite."""
        return {
            "blur_suite": {
                "type": "object",
                "required": True,
                "description": "Main Blur Suite configuration",
                "children": {
                    "version": {
                        "type": "string",
                        "required": False,
                        "default": "1.0.0",
                        "description": "Blur Suite version",
                    },
                    "debug": {
                        "type": "boolean",
                        "required": False,
                        "default": False,
                        "description": "Enable debug mode",
                    },
                    "log_level": {
                        "type": "string",
                        "required": False,
                        "default": "INFO",
                        "allowed_values": [
                            "DEBUG",
                            "INFO",
                            "WARNING",
                            "ERROR",
                            "CRITICAL",
                        ],
                        "description": "Logging level",
                    },
                    "performance": {
                        "type": "object",
                        "required": False,
                        "description": "Performance settings",
                        "children": {
                            "enable_caching": {
                                "type": "boolean",
                                "required": False,
                                "default": True,
                                "description": "Enable result caching",
                            },
                            "cache_size_mb": {
                                "type": "number",
                                "required": False,
                                "default": 100,
                                "min_value": 10,
                                "max_value": 10000,
                                "description": "Cache size in MB",
                            },
                            "enable_parallel": {
                                "type": "boolean",
                                "required": False,
                                "default": True,
                                "description": "Enable parallel processing",
                            },
                            "max_workers": {
                                "type": "number",
                                "required": False,
                                "default": None,
                                "min_value": 1,
                                "max_value": 32,
                                "description": "Maximum worker threads/processes",
                            },
                        },
                    },
                    "plugins": {
                        "type": "object",
                        "required": False,
                        "description": "Plugin system settings",
                        "children": {
                            "auto_discovery": {
                                "type": "boolean",
                                "required": False,
                                "default": True,
                                "description": "Enable automatic plugin discovery",
                            },
                            "search_paths": {
                                "type": "array",
                                "required": False,
                                "default": [],
                                "description": "Additional plugin search paths",
                            },
                        },
                    },
                },
            }
        }

    def _build_schema(self, schema_dict: Dict[str, Any], parent_path: str = ""):
        """Build schema from dictionary definition."""
        for key, definition in schema_dict.items():
            full_path = f"{parent_path}.{key}" if parent_path else key

            field = self._create_field_from_definition(key, definition, full_path)
            self._schema[full_path] = field

            # Recursively build children
            if field.children:
                child_path = full_path
                self._build_schema(definition.get("children", {}), child_path)

    def _create_field_from_definition(
        self, name: str, definition: Dict[str, Any], full_path: str
    ) -> SchemaField:
        """Create SchemaField from definition dictionary."""
        # Type mapping
        type_map = {
            "string": str,
            "boolean": bool,
            "number": (int, float),
            "integer": int,
            "object": dict,
            "array": list,
        }

        field_type = type_map.get(definition.get("type", "string"))
        if isinstance(field_type, tuple):
            # For union types, use the first one for validation
            field_type = field_type[0]

        # Extract validators
        validators = []
        if "allowed_values" in definition:
            validators.append(
                self._create_choice_validator(definition["allowed_values"])
            )
        if "min_value" in definition:
            validators.append(
                self._create_range_validator(definition["min_value"], "min")
            )
        if "max_value" in definition:
            validators.append(
                self._create_range_validator(definition["max_value"], "max")
            )
        if "regex_pattern" in definition:
            validators.append(self._create_regex_validator(definition["regex_pattern"]))

        # Handle nested objects
        children = None
        if definition.get("type") == "object" and "children" in definition:
            children = {}
            for child_name, child_def in definition["children"].items():
                child_field = self._create_field_from_definition(
                    child_name, child_def, ""
                )
                children[child_name] = child_field

        return SchemaField(
            name=name,
            type=field_type,
            required=definition.get("required", False),
            default=definition.get("default"),
            validators=validators,
            description=definition.get("description", ""),
            allowed_values=definition.get("allowed_values"),
            min_value=definition.get("min_value"),
            max_value=definition.get("max_value"),
            regex_pattern=definition.get("regex_pattern"),
            children=children,
        )

    def _create_choice_validator(self, allowed_values: List[Any]):
        """Create validator for allowed values."""

        def validator(value):
            if value not in allowed_values:
                raise ValueError(f"Value must be one of: {allowed_values}")

        return validator

    def _create_range_validator(self, limit: Union[int, float], range_type: str):
        """Create validator for numeric ranges."""

        def min_validator(value):
            if value < limit:
                raise ValueError(f"Value must be >= {limit}")

        def max_validator(value):
            if value > limit:
                raise ValueError(f"Value must be <= {limit}")

        return min_validator if range_type == "min" else max_validator

    def _create_regex_validator(self, pattern: str):
        """Create validator for regex patterns."""

        def validator(value):
            if not re.match(pattern, str(value)):
                raise ValueError(f"Value must match pattern: {pattern}")

        return validator

    def validate(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration against schema.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Check required fields
        errors.extend(self._validate_required_fields(config))

        # Validate field types and constraints
        errors.extend(self._validate_field_types(config))

        # Validate field values
        errors.extend(self._validate_field_values(config))

        return errors

    def _validate_required_fields(self, config: Dict[str, Any]) -> List[str]:
        """Validate that all required fields are present."""
        errors = []

        for field_path, field in self._schema.items():
            if not field.required:
                continue

            # Check if field exists in config
            value = self._get_nested_config_value(config, field_path)
            if value is None:
                errors.append(f"Required field missing: {field_path}")

        return errors

    def _validate_field_types(self, config: Dict[str, Any]) -> List[str]:
        """Validate field types."""
        errors = []

        for field_path, field in self._schema.items():
            value = self._get_nested_config_value(config, field_path)
            if value is None:
                continue

            # Check type
            if not isinstance(value, field.type):
                errors.append(
                    f"Field '{field_path}' must be of type {field.type.__name__}, "
                    f"got {type(value).__name__}"
                )

        return errors

    def _validate_field_values(self, config: Dict[str, Any]) -> List[str]:
        """Validate field values against constraints."""
        errors = []

        for field_path, field in self._schema.items():
            value = self._get_nested_config_value(config, field_path)
            if value is None:
                continue

            # Run custom validators
            for validator in field.validators:
                try:
                    validator(value)
                except ValueError as e:
                    errors.append(f"Field '{field_path}': {str(e)}")

        return errors

    def _get_nested_config_value(self, config: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from configuration."""
        keys = field_path.split(".")
        current = config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def get_field_info(self, field_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a schema field.

        Args:
            field_path: Path to the field

        Returns:
            Field information or None if not found
        """
        if field_path not in self._schema:
            return None

        field = self._schema[field_path]
        return {
            "name": field.name,
            "type": field.type.__name__,
            "required": field.required,
            "default": field.default,
            "description": field.description,
            "allowed_values": field.allowed_values,
            "min_value": field.min_value,
            "max_value": field.max_value,
            "regex_pattern": field.regex_pattern,
            "has_children": field.children is not None,
        }

    def list_fields(self, prefix: str = "") -> List[str]:
        """
        List all field paths in the schema.

        Args:
            prefix: Field prefix to filter by

        Returns:
            List of field paths
        """
        if prefix:
            return [path for path in self._schema.keys() if path.startswith(prefix)]
        else:
            return list(self._schema.keys())

    def generate_template(self) -> Dict[str, Any]:
        """
        Generate configuration template with default values.

        Returns:
            Configuration template
        """
        template = {}

        for field_path, field in self._schema.items():
            if field.default is not None:
                self._set_nested_template_value(template, field_path, field.default)

        return template

    def _set_nested_template_value(
        self, template: Dict[str, Any], field_path: str, value: Any
    ):
        """Set nested value in template."""
        keys = field_path.split(".")
        current = template

        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def export_schema(self, format: str = "json") -> str:
        """
        Export schema definition.

        Args:
            format: Export format ('json' or 'dict')

        Returns:
            Schema as formatted string or dictionary
        """
        if format == "dict":
            return self._schema_to_dict()

        schema_dict = self._schema_to_dict()
        return json.dumps(schema_dict, indent=2)

    def _schema_to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary representation."""
        schema_dict = {}

        for field_path, field in self._schema.items():
            current = schema_dict
            keys = field_path.split(".")

            # Navigate to field location
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {"type": "object", "children": {}}
                if "children" not in current[key]:
                    current[key]["children"] = {}
                current = current[key]["children"]

            # Add field definition
            field_dict = {
                "type": field.type.__name__.lower(),
                "required": field.required,
                "description": field.description,
            }

            if field.default is not None:
                field_dict["default"] = field.default
            if field.allowed_values:
                field_dict["allowed_values"] = field.allowed_values
            if field.min_value is not None:
                field_dict["min_value"] = field.min_value
            if field.max_value is not None:
                field_dict["max_value"] = field.max_value
            if field.regex_pattern:
                field_dict["regex_pattern"] = field.regex_pattern

            current[keys[-1]] = field_dict

        return schema_dict

    def merge_schema(self, other_schema: "ConfigSchema"):
        """
        Merge another schema into this one.

        Args:
            other_schema: Schema to merge
        """
        for field_path, field in other_schema._schema.items():
            if field_path not in self._schema:
                self._schema[field_path] = field
