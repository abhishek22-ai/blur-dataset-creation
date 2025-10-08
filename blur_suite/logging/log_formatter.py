"""
Log Formatter

Advanced log formatting with multiple output formats and customization options.
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class FormatConfig:
    """Log format configuration."""

    include_timestamp: bool = True
    include_level: bool = True
    include_logger_name: bool = True
    include_correlation_id: bool = True
    include_performance_data: bool = True
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
    field_order: List[str] = None
    custom_fields: Dict[str, str] = None

    def __post_init__(self):
        if self.field_order is None:
            self.field_order = [
                "timestamp",
                "level",
                "logger",
                "correlation_id",
                "message",
            ]
        if self.custom_fields is None:
            self.custom_fields = {}


class LogFormatter:
    """
    Advanced log formatter with multiple output formats.

    Supports JSON, structured text, and custom formatting
    with configurable fields and styling.
    """

    def __init__(self, config: Optional[FormatConfig] = None):
        """
        Initialize log formatter.

        Args:
            config: Format configuration
        """
        self.config = config or FormatConfig()

    def format_json(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON formatted log entry
        """
        log_data = {}

        # Add standard fields
        if self.config.include_timestamp:
            log_data["timestamp"] = time.strftime(
                self.config.timestamp_format, time.localtime(record.created)
            )

        if self.config.include_level:
            log_data["level"] = record.levelname

        if self.config.include_logger_name:
            log_data["logger"] = record.name

        # Add correlation ID if available
        if self.config.include_correlation_id:
            correlation_id = getattr(record, "correlation_id", None)
            if correlation_id:
                log_data["correlation_id"] = correlation_id

        # Add message
        log_data["message"] = record.getMessage()

        # Add extra fields from record
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in [
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "getMessage",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                ]:
                    log_data[key] = value

        # Add custom fields
        for field_name, field_value in self.config.custom_fields.items():
            log_data[field_name] = field_value

        # Add performance data if enabled
        if self.config.include_performance_data:
            performance_data = getattr(record, "performance_data", None)
            if performance_data:
                log_data["performance"] = performance_data

        return json.dumps(log_data, default=str)

    def format_text(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured text.

        Args:
            record: Log record to format

        Returns:
            Text formatted log entry
        """
        parts = []

        # Build parts based on configuration
        for field in self.config.field_order:
            if field == "timestamp" and self.config.include_timestamp:
                timestamp = time.strftime(
                    self.config.timestamp_format, time.localtime(record.created)
                )
                parts.append(f"[{timestamp}]")

            elif field == "level" and self.config.include_level:
                parts.append(f"{record.levelname}")

            elif field == "logger" and self.config.include_logger_name:
                parts.append(f"{record.name}")

            elif field == "correlation_id" and self.config.include_correlation_id:
                correlation_id = getattr(record, "correlation_id", None)
                if correlation_id:
                    parts.append(f"[{correlation_id[:8]}]")

            elif field == "message":
                parts.append(record.getMessage())

        return " ".join(parts)

    def format_html(self, record: logging.LogRecord) -> str:
        """
        Format log record as HTML.

        Args:
            record: Log record to format

        Returns:
            HTML formatted log entry
        """
        # Get level-based styling
        level_colors = {
            "DEBUG": "#6B7280",
            "INFO": "#3B82F6",
            "WARNING": "#F59E0B",
            "ERROR": "#EF4444",
            "CRITICAL": "#DC2626",
        }

        color = level_colors.get(record.levelname, "#6B7280")

        html = [
            '<div class="log-entry">',
            f'<span class="log-timestamp">{time.strftime(self.config.timestamp_format, time.localtime(record.created))}</span>',
            f'<span class="log-level" style="color: {color};">[{record.levelname}]</span>',
            f'<span class="log-logger">{record.name}:</span>',
            f'<span class="log-message">{record.getMessage()}</span>',
        ]

        # Add correlation ID if available
        if self.config.include_correlation_id:
            correlation_id = getattr(record, "correlation_id", None)
            if correlation_id:
                html.append(
                    f'<span class="log-correlation">[{correlation_id[:8]}]</span>'
                )

        html.append("</div>")
        return "".join(html)

    def format_syslog(self, record: logging.LogRecord) -> str:
        """
        Format log record for syslog.

        Args:
            record: Log record to format

        Returns:
            Syslog formatted log entry
        """
        # Syslog format: <priority>timestamp hostname process: message
        facility = 1  # user facility
        severity_map = {"DEBUG": 7, "INFO": 6, "WARNING": 4, "ERROR": 3, "CRITICAL": 2}

        severity = severity_map.get(record.levelname, 6)
        priority = (facility * 8) + severity

        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime(record.created))
        hostname = "localhost"  # Would get actual hostname
        process = record.name

        return f"<{priority}>{timestamp} {hostname} {process}: {record.getMessage()}"

    def format(self, record: logging.LogRecord, format_type: str = "auto") -> str:
        """
        Format log record with specified format.

        Args:
            record: Log record to format
            format_type: Format type ('json', 'text', 'html', 'syslog', 'auto')

        Returns:
            Formatted log entry
        """
        if format_type == "auto":
            # Auto-detect based on configuration
            format_type = self.config.custom_fields.get("format", "text")

        if format_type == "json":
            return self.format_json(record)
        elif format_type == "text":
            return self.format_text(record)
        elif format_type == "html":
            return self.format_html(record)
        elif format_type == "syslog":
            return self.format_syslog(record)
        else:
            raise ValueError(f"Unknown format type: {format_type}")


class CustomFormatter(logging.Formatter):
    """
    Custom logging formatter with advanced features.
    """

    def __init__(self, config: Optional[FormatConfig] = None):
        """
        Initialize custom formatter.

        Args:
            config: Format configuration
        """
        super().__init__()
        self.formatter = LogFormatter(config)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record."""
        return self.formatter.format(record, "text")


class JSONFormatter(logging.Formatter):
    """
    JSON logging formatter.
    """

    def __init__(self, config: Optional[FormatConfig] = None):
        """
        Initialize JSON formatter.

        Args:
            config: Format configuration
        """
        super().__init__()
        self.formatter = LogFormatter(config)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        return self.formatter.format(record, "json")


class MultiFormatFormatter:
    """
    Formatter that can output in multiple formats based on record metadata.
    """

    def __init__(self):
        """Initialize multi-format formatter."""
        self.formatters = {
            "json": JSONFormatter(),
            "text": CustomFormatter(),
            "html": self._create_html_formatter(),
            "syslog": self._create_syslog_formatter(),
        }

    def _create_html_formatter(self):
        """Create HTML formatter."""
        config = FormatConfig()
        formatter = LogFormatter(config)
        return formatter

    def _create_syslog_formatter(self):
        """Create syslog formatter."""
        config = FormatConfig()
        formatter = LogFormatter(config)
        return formatter

    def format(self, record: logging.LogRecord) -> str:
        """Format record based on its format specification."""
        # Check if record specifies a format
        format_type = getattr(record, "format_type", "text")

        if format_type in self.formatters:
            formatter = self.formatters[format_type]
            if hasattr(formatter, "formatter"):
                return formatter.formatter.format(record, format_type)
            else:
                return formatter.format(record)

        # Default to text format
        return self.formatters["text"].formatter.format(record, "text")


def create_json_formatter(**kwargs) -> JSONFormatter:
    """
    Create a JSON formatter with configuration.

    Args:
        **kwargs: Format configuration

    Returns:
        JSON formatter
    """
    config = FormatConfig(**kwargs)
    return JSONFormatter(config)


def create_text_formatter(**kwargs) -> CustomFormatter:
    """
    Create a text formatter with configuration.

    Args:
        **kwargs: Format configuration

    Returns:
        Text formatter
    """
    config = FormatConfig(**kwargs)
    return CustomFormatter(config)


def create_custom_formatter(
    format_type: str = "text",
    include_timestamp: bool = True,
    include_level: bool = True,
    include_logger_name: bool = True,
    **kwargs,
) -> logging.Formatter:
    """
    Create a custom formatter.

    Args:
        format_type: Type of formatter ('json', 'text', 'html', 'syslog')
        include_timestamp: Whether to include timestamp
        include_level: Whether to include log level
        include_logger_name: Whether to include logger name
        **kwargs: Additional configuration

    Returns:
        Configured formatter
    """
    config = FormatConfig(
        include_timestamp=include_timestamp,
        include_level=include_level,
        include_logger_name=include_logger_name,
        **kwargs,
    )

    if format_type == "json":
        return JSONFormatter(config)
    elif format_type == "text":
        return CustomFormatter(config)
    elif format_type == "html":
        formatter = LogFormatter(config)
        return HTMLLogHandler(formatter)
    elif format_type == "syslog":
        formatter = LogFormatter(config)
        return SyslogLogHandler(formatter)
    else:
        raise ValueError(f"Unknown format type: {format_type}")


class HTMLLogHandler(logging.Handler):
    """
    Log handler that outputs HTML formatted logs.
    """

    def __init__(self, formatter: LogFormatter):
        """
        Initialize HTML log handler.

        Args:
            formatter: Log formatter instance
        """
        super().__init__()
        self.formatter = formatter

    def emit(self, record: logging.LogRecord):
        """Emit HTML formatted log."""
        try:
            html_output = self.formatter.format_html(record)
            print(html_output, flush=True)
        except Exception:
            print(
                f"<div class='log-error'>Error formatting log: {record.getMessage()}</div>",
                flush=True,
            )


class SyslogLogHandler(logging.Handler):
    """
    Log handler that outputs syslog formatted logs.
    """

    def __init__(self, formatter: LogFormatter):
        """
        Initialize syslog log handler.

        Args:
            formatter: Log formatter instance
        """
        super().__init__()
        self.formatter = formatter

    def emit(self, record: logging.LogRecord):
        """Emit syslog formatted log."""
        try:
            syslog_output = self.formatter.format_syslog(record)
            print(syslog_output, flush=True)
        except Exception:
            print(f"Error formatting syslog: {record.getMessage()}", flush=True)


class LogTemplateFormatter:
    """
    Formatter that uses templates for custom log formats.
    """

    def __init__(self, template: str):
        """
        Initialize template formatter.

        Args:
            template: Format template with placeholders
        """
        self.template = template
        self.placeholders = self._extract_placeholders(template)

    def _extract_placeholders(self, template: str) -> List[str]:
        """Extract placeholder names from template."""
        import re

        # Find all placeholders like {field_name}
        placeholders = re.findall(r"\{(\w+)\}", template)
        return placeholders

    def format(self, record: logging.LogRecord) -> str:
        """Format record using template."""
        values = {}

        # Extract values for placeholders
        for placeholder in self.placeholders:
            if placeholder == "timestamp":
                values[placeholder] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(record.created)
                )
            elif placeholder == "level":
                values[placeholder] = record.levelname
            elif placeholder == "logger":
                values[placeholder] = record.name
            elif placeholder == "message":
                values[placeholder] = record.getMessage()
            elif placeholder == "correlation_id":
                values[placeholder] = getattr(record, "correlation_id", "")
            else:
                # Try to get from record attributes
                values[placeholder] = getattr(record, placeholder, "")

        # Format template
        try:
            return self.template.format(**values)
        except KeyError as e:
            return f"Template error - missing placeholder: {e}"

    def validate_template(self) -> List[str]:
        """
        Validate template for missing placeholders.

        Returns:
            List of validation errors
        """
        errors = []

        # This would implement template validation
        # For now, return empty list
        return errors


def create_template_formatter(template: str) -> LogTemplateFormatter:
    """
    Create a template-based formatter.

    Args:
        template: Format template

    Returns:
        Template formatter
    """
    return LogTemplateFormatter(template)


# Common format templates
LOG_TEMPLATES = {
    "simple": "{timestamp} [{level}] {logger}: {message}",
    "detailed": "{timestamp} [{level}] {logger}:{funcName}:{lineno} - {message}",
    "compact": "{timestamp} {level} {message}",
    "with_correlation": "{timestamp} [{level}] [{correlation_id}] {logger}: {message}",
    "performance": "{timestamp} [{level}] {logger} ({duration:.3f}s): {message}",
}
