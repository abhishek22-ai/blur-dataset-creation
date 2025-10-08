"""
Log Manager

Centralized log management and configuration for the Blur Suite SDK.
"""

import json
import logging
import logging.handlers
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LogConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"
    enable_file_logging: bool = True
    log_file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console_logging: bool = True
    enable_correlation: bool = True
    enable_performance: bool = True
    filters: List[str] = None

    def __post_init__(self):
        if self.filters is None:
            self.filters = []


class LogManager:
    """
    Centralized log management system.

    Manages logging configuration, output destinations,
    and provides a unified interface for all logging operations.
    """

    def __init__(self, config: Optional[LogConfig] = None):
        """
        Initialize log manager.

        Args:
            config: Logging configuration
        """
        self.config = config or LogConfig()
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: Dict[str, logging.Handler] = {}
        self._lock = threading.RLock()

        # Initialize logging system
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging system with configuration."""
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level.upper()))

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Create formatters
        if self.config.format.lower() == "json":
            formatter = self._create_json_formatter()
        else:
            formatter = self._create_text_formatter()

        # Setup handlers
        if self.config.enable_console_logging:
            console_handler = self._create_console_handler(formatter)
            root_logger.addHandler(console_handler)
            self._handlers["console"] = console_handler

        if self.config.enable_file_logging:
            file_handler = self._create_file_handler(formatter)
            if file_handler:
                root_logger.addHandler(file_handler)
                self._handlers["file"] = file_handler

        # Add correlation filter if enabled
        if self.config.enable_correlation:
            correlation_filter = CorrelationFilter()
            for handler in root_logger.handlers:
                handler.addFilter(correlation_filter)

    def _create_json_formatter(self) -> logging.Formatter:
        """Create JSON formatter."""
        return logging.Formatter(
            "%(message)s"  # StructuredLogHandler will format as JSON
        )

    def _create_text_formatter(self) -> logging.Formatter:
        """Create text formatter."""
        return logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    def _create_console_handler(self, formatter: logging.Formatter) -> logging.Handler:
        """Create console handler."""
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        return handler

    def _create_file_handler(
        self, formatter: logging.Formatter
    ) -> Optional[logging.Handler]:
        """Create file handler with rotation."""
        if not self.config.log_file_path:
            # Default log file path
            log_dir = Path.home() / ".blur_suite" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            self.config.log_file_path = str(log_dir / "blur_suite.log")

        try:
            # Create rotating file handler
            handler = logging.handlers.RotatingFileHandler(
                self.config.log_file_path,
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
            )
            handler.setFormatter(formatter)
            return handler

        except Exception as e:
            print(f"Warning: Could not create log file handler: {e}")
            return None

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        with self._lock:
            if name not in self._loggers:
                self._loggers[name] = logging.getLogger(name)
            return self._loggers[name]

    def set_level(self, level: str, logger_name: Optional[str] = None):
        """
        Set logging level.

        Args:
            level: Logging level
            logger_name: Specific logger name, or None for root
        """
        log_level = getattr(logging, level.upper())

        if logger_name:
            logger = self.get_logger(logger_name)
            logger.setLevel(log_level)
        else:
            # Update configuration and reconfigure
            self.config.level = level
            self._setup_logging()

    def add_filter(self, filter_func: callable, logger_name: Optional[str] = None):
        """
        Add a log filter.

        Args:
            filter_func: Filter function
            logger_name: Specific logger name, or None for all
        """
        filter_instance = logging.Filter()
        filter_instance.filter = filter_func

        if logger_name:
            logger = self.get_logger(logger_name)
            for handler in logger.handlers:
                handler.addFilter(filter_instance)
        else:
            # Add to root logger handlers
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                handler.addFilter(filter_instance)

        self.config.filters.append(
            filter_func.__name__
            if hasattr(filter_func, "__name__")
            else str(filter_func)
        )

    def configure_from_dict(self, config_dict: Dict[str, Any]):
        """
        Configure logging from dictionary.

        Args:
            config_dict: Configuration dictionary
        """
        # Update configuration
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Reconfigure logging
        self._setup_logging()

    def configure_from_file(self, config_file: str):
        """
        Configure logging from file.

        Args:
            config_file: Path to configuration file
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        # Determine file type
        file_ext = Path(config_file).suffix.lower()

        if file_ext == ".json":
            with open(config_file, "r") as f:
                config_dict = json.load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {file_ext}")

        self.configure_from_dict(config_dict)

    def get_log_files(self) -> List[str]:
        """Get list of current log files."""
        if not self.config.log_file_path:
            return []

        log_path = Path(self.config.log_file_path)
        log_dir = log_path.parent

        if not log_dir.exists():
            return []

        # Find all log files (including rotated ones)
        pattern = f"{log_path.stem}*"
        log_files = list(log_dir.glob(pattern))

        return [str(f) for f in sorted(log_files)]

    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        stats = {
            "config": {
                "level": self.config.level,
                "format": self.config.format,
                "enable_file_logging": self.config.enable_file_logging,
                "enable_console_logging": self.config.enable_console_logging,
                "enable_correlation": self.config.enable_correlation,
                "enable_performance": self.config.enable_performance,
                "log_file_path": self.config.log_file_path,
                "max_file_size_mb": self.config.max_file_size / (1024 * 1024),
                "backup_count": self.config.backup_count,
                "filters_count": len(self.config.filters),
            },
            "runtime": {
                "loggers_created": len(self._loggers),
                "handlers_created": len(self._handlers),
                "log_files": self.get_log_files(),
            },
        }

        return stats

    def rotate_logs(self):
        """Manually rotate log files."""
        if "file" in self._handlers:
            handler = self._handlers["file"]
            if hasattr(handler, "doRollover"):
                handler.doRollover()

    def clear_old_logs(self, keep_days: int = 7):
        """
        Clear old log files.

        Args:
            keep_days: Number of days of logs to keep
        """
        cutoff_time = time.time() - (keep_days * 24 * 3600)

        for log_file in self.get_log_files():
            try:
                file_modified = os.path.getmtime(log_file)
                if file_modified < cutoff_time:
                    os.remove(log_file)
            except Exception:
                pass

    def export_logs(
        self,
        output_file: str,
        format: str = "text",
        filter_pattern: Optional[str] = None,
    ):
        """
        Export logs to file.

        Args:
            output_file: Output file path
            format: Export format ('text' or 'json')
            filter_pattern: Pattern to filter log entries
        """
        # This is a simplified implementation
        # In practice, you would read and parse the actual log files

        export_data = {
            "export_time": time.time(),
            "source_files": self.get_log_files(),
            "format": format,
            "filter_pattern": filter_pattern,
            "entries": [],
        }

        if format.lower() == "json":
            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2)
        else:
            with open(output_file, "w") as f:
                f.write(f"Log Export - {time.ctime()}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Source: {', '.join(export_data['source_files'])}\n")
                f.write(f"Format: {format}\n")
                if filter_pattern:
                    f.write(f"Filter: {filter_pattern}\n")
                f.write("\nLog entries would be listed here.\n")

    def create_logger_context(self, logger_name: str, **context):
        """
        Create a logger with context.

        Args:
            logger_name: Logger name
            **context: Context information

        Returns:
            Logger instance
        """
        logger = self.get_logger(logger_name)

        # Add context as logger adapter
        return LoggerContextAdapter(logger, context)

    def enable_debug_logging(self, enable: bool = True):
        """Enable or disable debug logging."""
        level = "DEBUG" if enable else "INFO"
        self.set_level(level)

    def shutdown(self):
        """Shutdown logging system."""
        # Flush all handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.flush()
            handler.close()


class LoggerContextAdapter:
    """
    Logger adapter that adds context to all log messages.
    """

    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        """
        Initialize logger context adapter.

        Args:
            logger: Logger instance
            context: Context information to add
        """
        self.logger = logger
        self.context = context

    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with context."""
        # Merge context with kwargs
        log_kwargs = {**self.context, **kwargs}

        # Add context information to message if text format
        if hasattr(self.logger, "handlers") and self.logger.handlers:
            handler = self.logger.handlers[0]
            if hasattr(handler, "format") and hasattr(handler.formatter, "_fmt"):
                # Text format - add context to message
                if self.context:
                    context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
                    message = f"[{context_str}] {message}"

        self.logger.log(level, message, extra=log_kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)


class CorrelationFilter(logging.Filter):
    """
    Filter to add correlation IDs to log records.
    """

    def __init__(self):
        """Initialize correlation filter."""
        super().__init__()
        self._correlation_ids = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        # This is a simplified implementation
        # In practice, you would get the correlation ID from thread-local storage
        return True


# Global log manager instance
_global_log_manager = None
_log_manager_lock = threading.Lock()


def get_global_log_manager() -> LogManager:
    """Get the global log manager instance."""
    global _global_log_manager

    if _global_log_manager is None:
        with _log_manager_lock:
            if _global_log_manager is None:
                _global_log_manager = LogManager()

    return _global_log_manager


def configure_logging(config: Optional[Dict[str, Any]] = None):
    """
    Configure global logging.

    Args:
        config: Logging configuration
    """
    manager = get_global_log_manager()

    if config:
        manager.configure_from_dict(config)
    else:
        # Use default configuration
        manager._setup_logging()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger from the global log manager.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    manager = get_global_log_manager()
    return manager.get_logger(name)


def set_global_log_level(level: str):
    """
    Set global logging level.

    Args:
        level: Logging level
    """
    manager = get_global_log_manager()
    manager.set_level(level)


def enable_debug_logging():
    """Enable debug logging globally."""
    set_global_log_level("DEBUG")


def disable_debug_logging():
    """Disable debug logging globally."""
    set_global_log_level("INFO")
