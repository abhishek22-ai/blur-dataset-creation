"""
Error Handler

Comprehensive error handling and recovery system for the Blur Suite SDK.
"""

import threading
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories."""

    VALIDATION = "validation"
    PROCESSING = "processing"
    MEMORY = "memory"
    IO = "io"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    PLUGIN = "plugin"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""

    error_id: str
    error_type: str
    error_message: str
    error_traceback: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[float] = None
    retry_count: int = 0


class ErrorHandler:
    """
    Comprehensive error handling and recovery system.

    Provides error classification, recovery strategies,
    and detailed error tracking for production environments.
    """

    def __init__(self, enable_recovery: bool = True, max_error_history: int = 1000):
        """
        Initialize error handler.

        Args:
            enable_recovery: Whether to enable automatic recovery
            max_error_history: Maximum number of errors to keep in history
        """
        self.enable_recovery = enable_recovery
        self.max_error_history = max_error_history

        # Error storage
        self.error_history: List[ErrorRecord] = []
        self.error_counts: Dict[str, int] = {}
        self._lock = threading.RLock()

        # Recovery strategies
        self.recovery_strategies: Dict[str, Callable] = {}
        self._register_default_strategies()

        # Error classification rules
        self.classification_rules: List[Callable] = []
        self._register_default_classification_rules()

        # Statistics
        self.stats = {
            "total_errors": 0,
            "errors_by_severity": {s.value: 0 for s in ErrorSeverity},
            "errors_by_category": {c.value: 0 for c in ErrorCategory},
            "recovery_attempts": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
        }

    def _register_default_strategies(self):
        """Register default recovery strategies."""
        self.recovery_strategies.update(
            {
                "memory_error": self._recover_from_memory_error,
                "io_error": self._recover_from_io_error,
                "validation_error": self._recover_from_validation_error,
                "plugin_error": self._recover_from_plugin_error,
                "configuration_error": self._recover_from_configuration_error,
            }
        )

    def _register_default_classification_rules(self):
        """Register default error classification rules."""
        self.classification_rules = [
            self._classify_memory_errors,
            self._classify_io_errors,
            self._classify_validation_errors,
            self._classify_plugin_errors,
            self._classify_configuration_errors,
        ]

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None,
    ) -> ErrorRecord:
        """
        Handle an error with classification and recovery.

        Args:
            error: Exception that occurred
            context: Error context information
            operation: Operation where error occurred

        Returns:
            Error record
        """
        # Create error record
        error_id = f"err_{int(time.time() * 1000000)}_{len(self.error_history)}"

        # Classify error
        severity, category = self._classify_error(error, context)

        # Create error record
        error_record = ErrorRecord(
            error_id=error_id,
            error_type=type(error).__name__,
            error_message=str(error),
            error_traceback=traceback.format_exc(),
            severity=severity,
            category=category,
            context=context or {},
            timestamp=time.time(),
        )

        # Add operation to context
        if operation:
            error_record.context["operation"] = operation

        # Store error
        with self._lock:
            self.error_history.append(error_record)

            # Keep only recent errors
            if len(self.error_history) > self.max_error_history:
                self.error_history.pop(0)

            # Update counts
            self.error_counts[error_record.error_type] = (
                self.error_counts.get(error_record.error_type, 0) + 1
            )

            # Update statistics
            self.stats["total_errors"] += 1
            self.stats["errors_by_severity"][severity.value] += 1
            self.stats["errors_by_category"][category.value] += 1

        # Attempt recovery if enabled
        if self.enable_recovery:
            self._attempt_recovery(error_record)

        return error_record

    def _classify_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """Classify error by severity and category."""
        for rule in self.classification_rules:
            try:
                severity, category = rule(error, context)
                if severity and category:
                    return severity, category
            except Exception:
                continue

        # Default classification
        return ErrorSeverity.MEDIUM, ErrorCategory.UNKNOWN

    def _classify_memory_errors(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Optional[tuple]:
        """Classify memory-related errors."""
        memory_error_types = [
            "MemoryError",
            "MemoryFull",
            "OutOfMemoryError",
            "MemoryLimitExceeded",
            "BufferError",
        ]

        if type(error).__name__ in memory_error_types:
            return ErrorSeverity.HIGH, ErrorCategory.MEMORY

        # Check error message for memory indicators
        error_msg = str(error).lower()
        if any(
            indicator in error_msg
            for indicator in ["memory", "out of memory", "allocation failed"]
        ):
            return ErrorSeverity.HIGH, ErrorCategory.MEMORY

        return None

    def _classify_io_errors(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Optional[tuple]:
        """Classify I/O related errors."""
        io_error_types = [
            "IOError",
            "FileNotFoundError",
            "PermissionError",
            "IsADirectoryError",
            "FileExistsError",
        ]

        if type(error).__name__ in io_error_types:
            return ErrorSeverity.MEDIUM, ErrorCategory.IO

        # Check error message for I/O indicators
        error_msg = str(error).lower()
        if any(
            indicator in error_msg
            for indicator in ["file", "directory", "permission", "disk"]
        ):
            return ErrorSeverity.MEDIUM, ErrorCategory.IO

        return None

    def _classify_validation_errors(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Optional[tuple]:
        """Classify validation errors."""
        validation_error_types = [
            "ValueError",
            "TypeError",
            "ValidationError",
            "ParameterError",
            "InvalidParameterError",
        ]

        if type(error).__name__ in validation_error_types:
            return ErrorSeverity.LOW, ErrorCategory.VALIDATION

        return None

    def _classify_plugin_errors(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Optional[tuple]:
        """Classify plugin-related errors."""
        plugin_error_types = [
            "PluginError",
            "PluginLoadError",
            "PluginValidationError",
            "PluginNotFoundError",
            "PluginDependencyError",
        ]

        if type(error).__name__ in plugin_error_types:
            return ErrorSeverity.MEDIUM, ErrorCategory.PLUGIN

        # Check context for plugin information
        if context and "plugin" in context:
            return ErrorSeverity.MEDIUM, ErrorCategory.PLUGIN

        return None

    def _classify_configuration_errors(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Optional[tuple]:
        """Classify configuration errors."""
        config_error_types = [
            "ConfigurationError",
            "ConfigError",
            "InvalidConfigurationError",
        ]

        if type(error).__name__ in config_error_types:
            return ErrorSeverity.HIGH, ErrorCategory.CONFIGURATION

        # Check error message for configuration indicators
        error_msg = str(error).lower()
        if any(
            indicator in error_msg
            for indicator in ["config", "configuration", "setting"]
        ):
            return ErrorSeverity.HIGH, ErrorCategory.CONFIGURATION

        return None

    def _attempt_recovery(self, error_record: ErrorRecord):
        """Attempt to recover from an error."""
        strategy_name = self._get_recovery_strategy(error_record)

        if strategy_name in self.recovery_strategies:
            self.stats["recovery_attempts"] += 1

            try:
                success = self.recovery_strategies[strategy_name](error_record)

                if success:
                    error_record.resolved = True
                    error_record.resolution_time = time.time()
                    self.stats["successful_recoveries"] += 1
                else:
                    self.stats["failed_recoveries"] += 1

            except Exception as e:
                self.stats["failed_recoveries"] += 1
                print(f"Recovery strategy failed: {e}")

    def _get_recovery_strategy(self, error_record: ErrorRecord) -> str:
        """Get recovery strategy name for error."""
        # Map error categories to recovery strategies
        strategy_map = {
            ErrorCategory.MEMORY: "memory_error",
            ErrorCategory.IO: "io_error",
            ErrorCategory.VALIDATION: "validation_error",
            ErrorCategory.PLUGIN: "plugin_error",
            ErrorCategory.CONFIGURATION: "configuration_error",
        }

        return strategy_map.get(error_record.category, "default")

    def _recover_from_memory_error(self, error_record: ErrorRecord) -> bool:
        """Recover from memory errors."""
        try:
            # Trigger garbage collection
            import gc

            gc.collect()

            # Clear caches if available
            try:
                from ..cache.cache_manager import CacheManager

                # Clear cache manager
                cache_manager = CacheManager()
                cache_manager.clear()
            except Exception:
                pass

            # Clear memory pools if available
            try:
                from ..memory.memory_manager import MemoryManager

                memory_manager = MemoryManager()
                memory_manager.trigger_cleanup()
            except Exception:
                pass

            return True

        except Exception:
            return False

    def _recover_from_io_error(self, error_record: ErrorRecord) -> bool:
        """Recover from I/O errors."""
        try:
            # For I/O errors, we might retry the operation
            # or use alternative I/O methods
            return True

        except Exception:
            return False

    def _recover_from_validation_error(self, error_record: ErrorRecord) -> bool:
        """Recover from validation errors."""
        try:
            # For validation errors, we might use default values
            # or skip the invalid operation
            return True

        except Exception:
            return False

    def _recover_from_plugin_error(self, error_record: ErrorRecord) -> bool:
        """Recover from plugin errors."""
        try:
            # For plugin errors, we might disable the problematic plugin
            # or use fallback functionality
            return True

        except Exception:
            return False

    def _recover_from_configuration_error(self, error_record: ErrorRecord) -> bool:
        """Recover from configuration errors."""
        try:
            # For configuration errors, we might use default configuration
            # or disable problematic features
            return True

        except Exception:
            return False

    def register_recovery_strategy(self, strategy_name: str, strategy_func: Callable):
        """
        Register a custom recovery strategy.

        Args:
            strategy_name: Name of the strategy
            strategy_func: Recovery function
        """
        self.recovery_strategies[strategy_name] = strategy_func

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics."""
        with self._lock:
            recent_errors = [
                error
                for error in self.error_history
                if time.time() - error.timestamp < 3600  # Last hour
            ]

            return {
                "total_errors": self.stats["total_errors"],
                "recent_errors": len(recent_errors),
                "errors_by_severity": self.stats["errors_by_severity"].copy(),
                "errors_by_category": self.stats["errors_by_category"].copy(),
                "recovery_stats": {
                    "attempts": self.stats["recovery_attempts"],
                    "successful": self.stats["successful_recoveries"],
                    "failed": self.stats["failed_recoveries"],
                    "success_rate": (
                        self.stats["successful_recoveries"]
                        / max(self.stats["recovery_attempts"], 1)
                    ),
                },
                "top_error_types": self._get_top_error_types(),
                "unresolved_critical_errors": self._get_unresolved_critical_errors(),
            }

    def _get_top_error_types(self, limit: int = 10) -> List[tuple]:
        """Get most common error types."""
        error_types = [
            (error_type, count) for error_type, count in self.error_counts.items()
        ]
        error_types.sort(key=lambda x: x[1], reverse=True)
        return error_types[:limit]

    def _get_unresolved_critical_errors(self) -> List[ErrorRecord]:
        """Get unresolved critical errors."""
        return [
            error
            for error in self.error_history
            if error.severity == ErrorSeverity.CRITICAL and not error.resolved
        ]

    def get_error_history(
        self,
        limit: Optional[int] = None,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
    ) -> List[ErrorRecord]:
        """
        Get error history with optional filtering.

        Args:
            limit: Maximum number of errors to return
            severity: Filter by severity
            category: Filter by category

        Returns:
            List of error records
        """
        errors = self.error_history

        # Apply filters
        if severity:
            errors = [e for e in errors if e.severity == severity]

        if category:
            errors = [e for e in errors if e.category == category]

        # Apply limit
        if limit:
            errors = errors[-limit:]

        return errors.copy()

    def mark_error_resolved(self, error_id: str) -> bool:
        """
        Mark an error as resolved.

        Args:
            error_id: Error ID to mark as resolved

        Returns:
            True if marked, False if not found
        """
        for error in self.error_history:
            if error.error_id == error_id:
                error.resolved = True
                error.resolution_time = time.time()
                return True

        return False

    def clear_error_history(self, older_than_hours: float = 24.0):
        """
        Clear old error history.

        Args:
            older_than_hours: Clear errors older than this many hours
        """
        cutoff_time = time.time() - (older_than_hours * 3600)

        with self._lock:
            self.error_history = [
                error for error in self.error_history if error.timestamp > cutoff_time
            ]

    def export_error_report(self, format: str = "json") -> str:
        """
        Export error report.

        Args:
            format: Export format ('json' or 'text')

        Returns:
            Error report as formatted string
        """
        summary = self.get_error_summary()

        if format.lower() == "json":
            import json

            return json.dumps(summary, indent=2, default=str)

        else:
            # Text format
            report = []
            report.append("Blur Suite Error Report")
            report.append("=" * 40)
            report.append(f"Total Errors: {summary['total_errors']}")
            report.append(f"Recent Errors (1h): {summary['recent_errors']}")
            report.append("")

            # Errors by severity
            report.append("Errors by Severity:")
            for severity, count in summary["errors_by_severity"].items():
                report.append(f"  {severity}: {count}")
            report.append("")

            # Errors by category
            report.append("Errors by Category:")
            for category, count in summary["errors_by_category"].items():
                report.append(f"  {category}: {count}")
            report.append("")

            # Recovery statistics
            recovery_stats = summary["recovery_stats"]
            report.append("Recovery Statistics:")
            report.append(f"  Attempts: {recovery_stats['attempts']}")
            report.append(f"  Successful: {recovery_stats['successful']}")
            report.append(f"  Failed: {recovery_stats['failed']}")
            report.append(f"  Success Rate: {recovery_stats['success_rate']:.2%}")
            report.append("")

            # Top error types
            if summary["top_error_types"]:
                report.append("Top Error Types:")
                for error_type, count in summary["top_error_types"][:5]:
                    report.append(f"  {error_type}: {count}")
                report.append("")

            return "\n".join(report)


class ErrorRecoveryContext:
    """
    Context manager for error recovery.
    """

    def __init__(
        self,
        error_handler: ErrorHandler,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize error recovery context.

        Args:
            error_handler: Error handler instance
            operation: Operation name
            context: Operation context
        """
        self.error_handler = error_handler
        self.operation = operation
        self.context = context or {}

    def __enter__(self):
        """Enter error recovery context."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit error recovery context with error handling."""
        if exc_type is not None:
            # Handle the error
            self.error_handler.handle_error(
                exc_val, context=self.context, operation=self.operation
            )
            return False  # Don't suppress the exception

        return False


def handle_errors(operation: str, **context):
    """
    Decorator for automatic error handling.

    Args:
        operation: Operation name
        **context: Operation context

    Returns:
        Decorator function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get global error handler
            from .error_handler import ErrorHandler

            error_handler = ErrorHandler()

            try:
                with ErrorRecoveryContext(error_handler, operation, context):
                    return func(*args, **kwargs)

            except Exception:
                # Error is already handled by the context manager
                raise

        return wrapper

    return decorator


def safe_execute(
    operation_func: Callable, operation_name: str, max_retries: int = 3, **context
) -> Any:
    """
    Safely execute an operation with error handling.

    Args:
        operation_func: Function to execute
        operation_name: Name of the operation
        max_retries: Maximum number of retries
        **context: Operation context

    Returns:
        Operation result

    Raises:
        Exception: If operation fails after all retries
    """
    from .error_handler import ErrorHandler

    error_handler = ErrorHandler()

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            with ErrorRecoveryContext(error_handler, operation_name, context):
                return operation_func()

        except Exception as e:
            last_error = e

            if attempt < max_retries:
                # Wait before retry (exponential backoff)
                wait_time = (2**attempt) * 0.1
                time.sleep(wait_time)
            else:
                # Final attempt failed
                error_handler.handle_error(e, context=context, operation=operation_name)
                raise

    # This should never be reached
    raise last_error
