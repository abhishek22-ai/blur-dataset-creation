"""
Custom exceptions for the blur module.

This module defines all custom exceptions used throughout the blur
system for consistent error handling and meaningful error messages.
"""

from typing import Any, Dict, Optional


class BlurError(Exception):
    """
    Base exception for all blur-related errors.

    This is the parent class for all blur-specific exceptions,
    providing common functionality for error handling.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize blur error.

        Args:
            message: Error message
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class InvalidParameterError(BlurError):
    """
    Exception raised for invalid blur parameters.

    This exception is thrown when parameter values are outside
    acceptable ranges or don't meet validation requirements.
    """

    def __init__(
        self,
        message: str,
        parameter_name: Optional[str] = None,
        parameter_value: Optional[Any] = None,
        valid_range: Optional[str] = None,
    ):
        """
        Initialize invalid parameter error.

        Args:
            message: Error message
            parameter_name: Name of the invalid parameter
            parameter_value: The invalid value
            valid_range: Description of valid range/values
        """
        details = {}
        if parameter_name:
            details["parameter_name"] = parameter_name
        if parameter_value is not None:
            details["parameter_value"] = parameter_value
        if valid_range:
            details["valid_range"] = valid_range

        super().__init__(message, details)
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.valid_range = valid_range


class UnsupportedFormatError(BlurError):
    """
    Exception raised for unsupported image formats.

    This exception is thrown when the input image format is not
    supported by the blur operation or the system.
    """

    def __init__(self, message: str, format_info: Optional[Dict[str, Any]] = None):
        """
        Initialize unsupported format error.

        Args:
            message: Error message
            format_info: Optional information about the format issue
        """
        super().__init__(message, format_info)
        self.format_info = format_info or {}


class BlurApplicationError(BlurError):
    """
    Exception raised during blur application.

    This exception is thrown when errors occur during the actual
    blur processing, such as computation failures or resource issues.
    """

    def __init__(self, message: str, operation_info: Optional[Dict[str, Any]] = None):
        """
        Initialize blur application error.

        Args:
            message: Error message
            operation_info: Optional information about the failed operation
        """
        super().__init__(message, operation_info)
        self.operation_info = operation_info or {}


class PluginError(BlurError):
    """
    Exception raised for plugin-related errors.

    This exception is thrown when errors occur with plugin loading,
    validation, or execution.
    """

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        plugin_info: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize plugin error.

        Args:
            message: Error message
            plugin_name: Name of the problematic plugin
            plugin_info: Optional information about the plugin issue
        """
        details = {}
        if plugin_name:
            details["plugin_name"] = plugin_name
        if plugin_info:
            details.update(plugin_info)

        super().__init__(message, details)
        self.plugin_name = plugin_name
        self.plugin_info = plugin_info or {}


class PluginLoadError(PluginError):
    """
    Exception raised when a plugin fails to load.

    This exception is thrown when plugin files cannot be loaded
    or parsed correctly.
    """

    def __init__(
        self,
        message: str,
        plugin_path: Optional[str] = None,
        load_error: Optional[str] = None,
    ):
        """
        Initialize plugin load error.

        Args:
            message: Error message
            plugin_path: Path to the plugin that failed to load
            load_error: Specific error that occurred during loading
        """
        plugin_info = {}
        if plugin_path:
            plugin_info["plugin_path"] = plugin_path
        if load_error:
            plugin_info["load_error"] = load_error

        super().__init__(message, plugin_info=plugin_info)
        self.plugin_path = plugin_path
        self.load_error = load_error


class PluginValidationError(PluginError):
    """
    Exception raised when a plugin fails validation.

    This exception is thrown when a loaded plugin doesn't meet
    the requirements or has invalid configuration.
    """

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        validation_errors: Optional[list] = None,
    ):
        """
        Initialize plugin validation error.

        Args:
            message: Error message
            plugin_name: Name of the plugin that failed validation
            validation_errors: List of specific validation errors
        """
        plugin_info = {}
        if validation_errors:
            plugin_info["validation_errors"] = validation_errors

        super().__init__(message, plugin_name, plugin_info)
        self.validation_errors = validation_errors or []


class FactoryError(BlurError):
    """
    Exception raised for factory-related errors.

    This exception is thrown when errors occur during blur effect
    creation or registration.
    """

    def __init__(self, message: str, factory_info: Optional[Dict[str, Any]] = None):
        """
        Initialize factory error.

        Args:
            message: Error message
            factory_info: Optional information about the factory operation
        """
        super().__init__(message, factory_info)
        self.factory_info = factory_info or {}


class RegistryError(BlurError):
    """
    Exception raised for registry-related errors.

    This exception is thrown when errors occur with blur effect
    registration or lookup.
    """

    def __init__(self, message: str, registry_info: Optional[Dict[str, Any]] = None):
        """
        Initialize registry error.

        Args:
            message: Error message
            registry_info: Optional information about the registry operation
        """
        super().__init__(message, registry_info)
        self.registry_info = registry_info or {}
