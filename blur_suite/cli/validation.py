"""
CLI Input Validation Module

This module provides validation classes for CLI inputs including
path validation, configuration validation, and parameter validation.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from ..core.blur import BlurType
except ImportError:
    try:
        from blur_suite.core.blur import BlurType
    except ImportError:
        # Fallback for direct script execution
        import os
        import sys

        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.blur import BlurType


class ValidationError(Exception):
    """Exception raised for validation errors."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(message)
        self.suggestion = suggestion


class InputValidator:
    """Base class for input validation."""

    @staticmethod
    def validate_not_empty(value: Any, field_name: str) -> None:
        """Validate that a value is not empty."""
        if not value:
            raise ValidationError(f"{field_name} cannot be empty")

    @staticmethod
    def validate_type(value: Any, expected_type: type, field_name: str) -> None:
        """Validate that a value is of the expected type."""
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"{field_name} must be of type {expected_type.__name__}, got {type(value).__name__}"
            )


class PathValidator:
    """Validator for file and directory paths."""

    SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
    SUPPORTED_CONFIG_EXTENSIONS = {".json", ".yaml", ".yml"}

    @staticmethod
    def validate_directory_exists(
        path: Union[str, Path], field_name: str = "Directory"
    ) -> Path:
        """Validate that a directory exists and is accessible."""
        path = Path(path)

        if not path.exists():
            raise ValidationError(
                f"{field_name} does not exist: {path}",
                "Please create the directory or check the path",
            )

        if not path.is_dir():
            raise ValidationError(
                f"{field_name} is not a directory: {path}",
                "Please provide a valid directory path",
            )

        try:
            # Test if directory is readable
            next(path.iterdir(), None)
        except PermissionError:
            raise ValidationError(
                f"{field_name} is not accessible: {path}",
                "Please check directory permissions",
            )

        return path

    @staticmethod
    def validate_file_exists(path: Union[str, Path], field_name: str = "File") -> Path:
        """Validate that a file exists and is accessible."""
        path = Path(path)

        if not path.exists():
            raise ValidationError(
                f"{field_name} does not exist: {path}", "Please check the file path"
            )

        if not path.is_file():
            raise ValidationError(
                f"{field_name} is not a file: {path}",
                "Please provide a valid file path",
            )

        try:
            # Test if file is readable
            with open(path, "r"):
                pass
        except PermissionError:
            raise ValidationError(
                f"{field_name} is not accessible: {path}",
                "Please check file permissions",
            )

        return path

    @staticmethod
    def validate_image_file(
        path: Union[str, Path], field_name: str = "Image file"
    ) -> Path:
        """Validate that a file is a supported image format."""
        path = PathValidator.validate_file_exists(path, field_name)

        if path.suffix.lower() not in PathValidator.SUPPORTED_IMAGE_EXTENSIONS:
            raise ValidationError(
                f"{field_name} has unsupported format: {path.suffix}",
                f"Supported formats: {', '.join(PathValidator.SUPPORTED_IMAGE_EXTENSIONS)}",
            )

        return path

    @staticmethod
    def validate_config_file(
        path: Union[str, Path], field_name: str = "Configuration file"
    ) -> Path:
        """Validate that a file is a supported configuration format."""
        path = PathValidator.validate_file_exists(path, field_name)

        if path.suffix.lower() not in PathValidator.SUPPORTED_CONFIG_EXTENSIONS:
            raise ValidationError(
                f"{field_name} has unsupported format: {path.suffix}",
                f"Supported formats: {', '.join(PathValidator.SUPPORTED_CONFIG_EXTENSIONS)}",
            )

        return path

    @staticmethod
    def validate_output_directory(
        path: Union[str, Path], field_name: str = "Output directory"
    ) -> Path:
        """Validate output directory path."""
        path = Path(path)

        if path.exists() and not path.is_dir():
            raise ValidationError(
                f"{field_name} exists but is not a directory: {path}",
                "Please provide a valid directory path",
            )

        # Try to create directory if it doesn't exist
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise ValidationError(
                    f"Cannot create {field_name}: {path}",
                    "Please check parent directory permissions",
                )

        return path

    @staticmethod
    def validate_directory_writable(
        path: Union[str, Path], field_name: str = "Directory"
    ) -> Path:
        """Validate that a directory is writable."""
        path = PathValidator.validate_directory_exists(path, field_name)

        # Test if directory is writable
        test_file = path / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise ValidationError(
                f"{field_name} is not writable: {path}",
                f"Please check directory permissions: {e}",
            )

        return path


class ConfigValidator:
    """Validator for configuration files and parameters."""

    @staticmethod
    def validate_config_file(config_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate and load configuration file."""
        config_path = PathValidator.validate_config_file(config_path)

        try:
            with open(config_path, "r") as f:
                if config_path.suffix.lower() in {".yaml", ".yml"}:
                    import yaml

                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)

            if not isinstance(config, dict):
                raise ValidationError("Configuration must be a valid JSON/YAML object")

            return config

        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON configuration file: {e}", "Please check the JSON syntax"
            )
        except yaml.YAMLError as e:
            raise ValidationError(
                f"Invalid YAML configuration file: {e}", "Please check the YAML syntax"
            )
        except Exception as e:
            raise ValidationError(
                f"Error reading configuration file: {e}",
                "Please check file format and permissions",
            )

    @staticmethod
    def validate_blur_type(blur_type: str, field_name: str = "Blur type") -> str:
        """Validate blur type parameter."""
        InputValidator.validate_not_empty(blur_type, field_name)

        valid_types = [bt.value for bt in BlurType]
        if blur_type.lower() not in valid_types:
            raise ValidationError(
                f"Invalid {field_name}: {blur_type}",
                f"Valid types: {', '.join(valid_types)}",
            )

        return blur_type.lower()

    @staticmethod
    def validate_blur_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate blur configuration structure."""
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary")

        # Validate required fields
        required_fields = ["blur_type", "parameters"]
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"Missing required field: {field}")

        # Validate blur type
        config["blur_type"] = ConfigValidator.validate_blur_type(
            config["blur_type"], "blur_type"
        )

        # Validate parameters
        if not isinstance(config["parameters"], dict):
            raise ValidationError("Parameters must be a dictionary")

        return config


class ParameterValidator:
    """Validator for parameter values and ranges."""

    @staticmethod
    def validate_positive_integer(
        value: Any, field_name: str, min_value: int = 1
    ) -> int:
        """Validate positive integer parameter."""
        try:
            int_value = int(value)
            if int_value < min_value:
                raise ValidationError(
                    f"{field_name} must be >= {min_value}, got {int_value}"
                )
            return int_value
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be an integer >= {min_value}, got {value}"
            )

    @staticmethod
    def validate_positive_float(
        value: Any, field_name: str, min_value: float = 0.0
    ) -> float:
        """Validate positive float parameter."""
        try:
            float_value = float(value)
            if float_value < min_value:
                raise ValidationError(
                    f"{field_name} must be >= {min_value}, got {float_value}"
                )
            return float_value
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be a number >= {min_value}, got {value}"
            )

    @staticmethod
    def validate_percentage(value: Any, field_name: str) -> float:
        """Validate percentage value (0-100)."""
        try:
            float_value = float(value)
            if not (0.0 <= float_value <= 100.0):
                raise ValidationError(
                    f"{field_name} must be between 0 and 100, got {float_value}"
                )
            return float_value
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be a number between 0 and 100, got {value}"
            )

    @staticmethod
    def validate_choice(value: Any, choices: List[str], field_name: str) -> str:
        """Validate that value is one of the allowed choices."""
        if value not in choices:
            raise ValidationError(f"{field_name} must be one of {choices}, got {value}")
        return value

    @staticmethod
    def validate_kernel_size(value: Any, field_name: str = "Kernel size") -> int:
        """Validate kernel size (must be odd and positive)."""
        int_value = ParameterValidator.validate_positive_integer(value, field_name, 1)

        if int_value % 2 == 0:
            raise ValidationError(
                f"{field_name} must be odd, got {int_value}",
                f"Try {int_value + 1} instead",
            )

        return int_value

    @staticmethod
    def validate_sigma(value: Any, field_name: str = "Sigma") -> float:
        """Validate sigma parameter for Gaussian blur."""
        return ParameterValidator.validate_positive_float(value, field_name, 0.1)

    @staticmethod
    def validate_angle(value: Any, field_name: str = "Angle") -> float:
        """Validate angle parameter (0-360 degrees)."""
        try:
            float_value = float(value)
            if not (0.0 <= float_value <= 360.0):
                raise ValidationError(
                    f"{field_name} must be between 0 and 360, got {float_value}"
                )
            return float_value
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be a number between 0 and 360, got {value}"
            )

    @staticmethod
    def validate_file_size_limit(size_limit: str) -> int:
        """Validate file size limit with units (e.g., '4GB', '500MB')."""
        pattern = r"^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB)?$"
        match = re.match(pattern, size_limit.strip(), re.IGNORECASE)

        if not match:
            raise ValidationError(
                f"Invalid size format: {size_limit}",
                "Use format like '4GB', '500MB', '1024KB'",
            )

        size_value = float(match.group(1))
        unit = match.group(2).upper()

        # Convert to bytes
        multipliers = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}

        return int(size_value * multipliers[unit])


class ValidationResult:
    """Result of validation operations."""

    def __init__(
        self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def __str__(self) -> str:
        """String representation of validation result."""
        result = []
        if self.errors:
            result.append(f"Errors ({len(self.errors)}):")
            for error in self.errors:
                result.append(f"  - {error}")
        if self.warnings:
            result.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                result.append(f"  - {warning}")
        return "\n".join(result)
