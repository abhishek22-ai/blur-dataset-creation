"""
Structured Logger

JSON logging with correlation IDs, contextual information, and structured data.
"""

import json
import logging
import threading
import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LogContext:
    """Logging context with correlation and metadata."""

    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    operation: Optional[str] = None
    component: str = "blur_suite"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "operation": self.operation,
            "component": self.component,
            "metadata": self.metadata,
        }


class StructuredLogger:
    """
    Enhanced logger with structured output and contextual information.

    Provides JSON logging, correlation IDs, and rich contextual
    information for better observability.
    """

    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        format: str = "json",
        enable_correlation: bool = True,
        enable_performance: bool = True,
    ):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            level: Logging level
            format: Output format ('json' or 'text')
            enable_correlation: Whether to include correlation IDs
            enable_performance: Whether to include performance metrics
        """
        self.name = name
        self.format = format
        self.enable_correlation = enable_correlation
        self.enable_performance = enable_performance

        # Create standard Python logger
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        # Remove existing handlers to avoid duplicates
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        # Add structured handler
        handler = StructuredLogHandler(format=format)
        self._logger.addHandler(handler)

        # Thread-local context storage
        self._local = threading.local()

        # Performance tracking
        self._start_times: Dict[str, float] = {}

    @property
    def correlation_id(self) -> Optional[str]:
        """Get current correlation ID."""
        if hasattr(self._local, "context"):
            return self._local.context.correlation_id
        return None

    @correlation_id.setter
    def correlation_id(self, value: str):
        """Set correlation ID."""
        if not hasattr(self._local, "context"):
            self._local.context = LogContext()
        self._local.context.correlation_id = value

    def set_context(self, **context_kwargs):
        """
        Set logging context.

        Args:
            **context_kwargs: Context parameters
        """
        if not hasattr(self._local, "context"):
            self._local.context = LogContext()

        for key, value in context_kwargs.items():
            if hasattr(self._local.context, key):
                setattr(self._local.context, key, value)
            else:
                self._local.context.metadata[key] = value

    def get_context(self) -> LogContext:
        """Get current logging context."""
        if hasattr(self._local, "context"):
            return self._local.context
        return LogContext()

    @contextmanager
    def context_manager(self, **context_kwargs):
        """
        Context manager for temporary logging context.

        Args:
            **context_kwargs: Context parameters for the duration
        """
        # Save current context
        saved_context = getattr(self._local, "context", None)

        try:
            # Set new context
            if not hasattr(self._local, "context"):
                self._local.context = LogContext()

            old_values = {}
            for key, value in context_kwargs.items():
                if hasattr(self._local.context, key):
                    old_values[key] = getattr(self._local.context, key)
                    setattr(self._local.context, key, value)
                else:
                    old_values[key] = self._local.context.metadata.get(key)
                    self._local.context.metadata[key] = value

            yield

        finally:
            # Restore old context
            if saved_context:
                self._local.context = saved_context
            else:
                # Restore old values
                for key, value in old_values.items():
                    if hasattr(self._local.context, key):
                        setattr(self._local.context, key, value)
                    else:
                        if value is None:
                            self._local.context.metadata.pop(key, None)
                        else:
                            self._local.context.metadata[key] = value

    def log_operation_start(self, operation: str, **metadata):
        """
        Log operation start.

        Args:
            operation: Operation name
            **metadata: Operation metadata
        """
        self.set_context(operation=operation, **metadata)
        self.info(f"Starting operation: {operation}", operation=operation, **metadata)

        if self.enable_performance:
            self._start_times[operation] = time.time()

    def log_operation_end(self, operation: str, success: bool = True, **metadata):
        """
        Log operation completion.

        Args:
            operation: Operation name
            success: Whether operation succeeded
            **metadata: Operation metadata
        """
        duration = None
        if self.enable_performance and operation in self._start_times:
            duration = time.time() - self._start_times[operation]
            del self._start_times[operation]

        status = "success" if success else "failure"
        self.info(
            f"Completed operation: {operation}",
            operation=operation,
            status=status,
            duration=duration,
            **metadata,
        )

    def log_operation_error(self, operation: str, error: Exception, **metadata):
        """
        Log operation error.

        Args:
            operation: Operation name
            error: Exception that occurred
            **metadata: Additional metadata
        """
        duration = None
        if self.enable_performance and operation in self._start_times:
            duration = time.time() - self._start_times[operation]
            del self._start_times[operation]

        self.error(
            f"Failed operation: {operation}",
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            error_traceback=traceback.format_exc(),
            duration=duration,
            **metadata,
        )

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method."""
        # Get context
        context = self.get_context()

        # Prepare log data
        log_data = {
            "timestamp": time.time(),
            "level": logging.getLevelName(level),
            "logger": self.name,
            "message": message,
            "context": context.to_dict() if self.enable_correlation else {},
            "extra": kwargs,
        }

        # Add performance data if enabled
        if self.enable_performance and hasattr(self._local, "context"):
            log_data["performance"] = {
                "active_operations": len(self._start_times),
                "context_operations": list(self._start_times.keys()),
            }

        # Log the message
        self._logger.log(
            level,
            json.dumps(log_data) if self.format == "json" else message,
            extra=kwargs,
        )


class StructuredLogHandler(logging.Handler):
    """
    Custom log handler for structured output.
    """

    def __init__(self, format: str = "json"):
        """
        Initialize structured log handler.

        Args:
            format: Output format ('json' or 'text')
        """
        super().__init__()
        self.format = format

    def emit(self, record: logging.LogRecord):
        """Emit log record."""
        try:
            # Parse structured data if JSON format
            if self.format == "json":
                try:
                    log_data = json.loads(record.getMessage())
                    message = log_data.get("message", record.getMessage())
                except (json.JSONDecodeError, ValueError):
                    message = record.getMessage()
                    log_data = {"message": message}
            else:
                message = record.getMessage()

            # Format output
            if self.format == "json":
                output = json.dumps(log_data, default=str)
            else:
                # Text format with structured information
                output = self._format_text_log(record, message)

            # Write to appropriate output
            print(output, flush=True)

        except Exception:
            # Fallback to basic logging
            print(f"LOG ERROR: {record.getMessage()}", flush=True)

    def _format_text_log(self, record: logging.LogRecord, message: str) -> str:
        """Format log as text."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))

        parts = [f"[{timestamp}]", f"{record.levelname}", f"{record.name}:", message]

        return " ".join(parts)


class CorrelationFilter(logging.Filter):
    """
    Filter to add correlation IDs to log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to record."""
        # This would be enhanced to extract correlation ID from thread-local storage
        return True


# Global logger registry
_logger_registry: Dict[str, StructuredLogger] = {}
_registry_lock = threading.Lock()


def get_logger(name: str, **kwargs) -> StructuredLogger:
    """
    Get or create a structured logger.

    Args:
        name: Logger name
        **kwargs: Logger configuration

    Returns:
        Structured logger instance
    """
    with _registry_lock:
        if name not in _logger_registry:
            _logger_registry[name] = StructuredLogger(name, **kwargs)

        return _logger_registry[name]


def set_global_correlation_id(correlation_id: str):
    """
    Set correlation ID for all loggers in current thread.

    Args:
        correlation_id: Correlation ID to set
    """
    # This would set the correlation ID in thread-local storage
    # for all loggers to access
    pass


def get_global_correlation_id() -> Optional[str]:
    """
    Get current global correlation ID.

    Returns:
        Current correlation ID or None
    """
    # This would get the correlation ID from thread-local storage
    return None


@contextmanager
def logging_context(**context_kwargs):
    """
    Context manager for logging context.

    Args:
        **context_kwargs: Context parameters

    Yields:
        None
    """
    # Get current thread's logger context
    # This is a simplified implementation
    yield


def configure_global_logging(
    level: str = "INFO", format: str = "json", enable_correlation: bool = True, **kwargs
):
    """
    Configure global logging for the application.

    Args:
        level: Global logging level
        format: Log format ('json' or 'text')
        enable_correlation: Whether to enable correlation IDs
        **kwargs: Additional configuration
    """
    # Configure Python's root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add structured handler
    handler = StructuredLogHandler(format=format)
    root_logger.addHandler(handler)

    # Store configuration
    global _global_logging_config
    _global_logging_config = {
        "level": level,
        "format": format,
        "enable_correlation": enable_correlation,
        **kwargs,
    }


# Global logging configuration
_global_logging_config = {"level": "INFO", "format": "json", "enable_correlation": True}


def log_performance(operation: str):
    """
    Decorator for logging operation performance.

    Args:
        operation: Operation name

    Returns:
        Decorator function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(f"{func.__module__}.{func.__name__}")

            logger.log_operation_start(operation)

            try:
                result = func(*args, **kwargs)
                logger.log_operation_end(operation, success=True)
                return result

            except Exception as e:
                logger.log_operation_error(operation, e)
                raise

        return wrapper

    return decorator


def log_function(func):
    """
    Decorator for automatic function logging.

    Args:
        func: Function to log

    Returns:
        Wrapped function
    """
    logger = get_logger(f"{func.__module__}.{func.__name__}")

    def wrapper(*args, **kwargs):
        func_name = func.__name__

        logger.debug(f"Entering function: {func_name}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting function: {func_name}")
            return result

        except Exception as e:
            logger.error(f"Exception in function {func_name}: {str(e)}")
            raise

    return wrapper
