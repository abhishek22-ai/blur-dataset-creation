"""
Log Filter

Advanced log filtering and routing capabilities.
"""

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Pattern


@dataclass
class FilterRule:
    """Log filter rule."""

    name: str
    pattern: str
    action: str  # 'allow', 'deny', 'redirect'
    level: Optional[str] = None
    logger_name: Optional[str] = None
    message_pattern: Optional[str] = None
    metadata: Dict[str, Any] = None


class LogFilter:
    """
    Advanced log filtering system.

    Provides sophisticated filtering, routing, and processing
    of log messages based on various criteria.
    """

    def __init__(self):
        """Initialize log filter."""
        self.rules: List[FilterRule] = []
        self.compiled_patterns: Dict[str, Pattern] = {}

    def add_rule(
        self,
        name: str,
        pattern: str,
        action: str,
        level: Optional[str] = None,
        logger_name: Optional[str] = None,
        message_pattern: Optional[str] = None,
        **metadata,
    ):
        """
        Add a filter rule.

        Args:
            name: Rule name
            pattern: Pattern to match
            action: Action to take ('allow', 'deny', 'redirect')
            level: Log level filter
            logger_name: Logger name filter
            message_pattern: Message pattern filter
            **metadata: Additional rule metadata
        """
        rule = FilterRule(
            name=name,
            pattern=pattern,
            action=action,
            level=level,
            logger_name=logger_name,
            message_pattern=message_pattern,
            metadata=metadata,
        )

        self.rules.append(rule)

        # Compile regex patterns
        if message_pattern:
            self.compiled_patterns[name] = re.compile(message_pattern)

    def remove_rule(self, name: str) -> bool:
        """
        Remove a filter rule.

        Args:
            name: Rule name

        Returns:
            True if removed, False if not found
        """
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                del self.rules[i]

                # Remove compiled pattern
                if name in self.compiled_patterns:
                    del self.compiled_patterns[name]

                return True

        return False

    def should_filter(self, record: logging.LogRecord) -> tuple:
        """
        Determine if a log record should be filtered.

        Args:
            record: Log record to check

        Returns:
            Tuple of (should_log, action, rule_name)
        """
        for rule in self.rules:
            if self._matches_rule(record, rule):
                if rule.action == "allow":
                    return True, rule.action, rule.name
                elif rule.action == "deny":
                    return False, rule.action, rule.name
                elif rule.action == "redirect":
                    return True, rule.action, rule.name

        # Default: allow logging
        return True, "allow", None

    def _matches_rule(self, record: logging.LogRecord, rule: FilterRule) -> bool:
        """Check if record matches a filter rule."""
        # Check log level
        if rule.level and record.levelname != rule.level:
            return False

        # Check logger name
        if rule.logger_name and not self._matches_pattern(
            record.name, rule.logger_name
        ):
            return False

        # Check message pattern
        if rule.message_pattern:
            if rule.name in self.compiled_patterns:
                pattern = self.compiled_patterns[rule.name]
                if not pattern.search(record.getMessage()):
                    return False
            else:
                # Simple string matching
                if rule.message_pattern not in record.getMessage():
                    return False

        # Check custom pattern
        if rule.pattern:
            # This could be extended for more complex pattern matching
            if not self._matches_pattern(str(record.__dict__), rule.pattern):
                return False

        return True

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Check if text matches a pattern."""
        if pattern.startswith("*") and pattern.endswith("*"):
            # Contains pattern
            return pattern[1:-1] in text
        elif pattern.startswith("*"):
            # Ends with pattern
            return text.endswith(pattern[1:])
        elif pattern.endswith("*"):
            # Starts with pattern
            return text.startswith(pattern[:-1])
        else:
            # Exact match
            return text == pattern

    def create_level_filter(self, min_level: str, max_level: str = None):
        """
        Create a filter for log levels.

        Args:
            min_level: Minimum log level
            max_level: Maximum log level (optional)
        """
        level_hierarchy = {
            "DEBUG": 1,
            "INFO": 2,
            "WARNING": 3,
            "ERROR": 4,
            "CRITICAL": 5,
        }

        min_value = level_hierarchy.get(min_level.upper())
        max_value = level_hierarchy.get(max_level.upper()) if max_level else 5

        if min_value is None or max_value is None:
            raise ValueError("Invalid log level")

        def level_filter(record):
            record_level = level_hierarchy.get(record.levelname, 0)
            return min_value <= record_level <= max_value

        return level_filter

    def create_logger_filter(self, allowed_loggers: List[str]):
        """
        Create a filter for specific loggers.

        Args:
            allowed_loggers: List of logger names to allow
        """

        def logger_filter(record):
            return record.name in allowed_loggers

        return logger_filter

    def create_message_filter(self, patterns: List[str], action: str = "allow"):
        """
        Create a filter for message patterns.

        Args:
            patterns: List of patterns to match
            action: Action for matching patterns
        """
        compiled_patterns = [re.compile(pattern) for pattern in patterns]

        def message_filter(record):
            message = record.getMessage()
            for pattern in compiled_patterns:
                if pattern.search(message):
                    return action == "allow"
            return action == "deny"

        return message_filter

    def create_time_filter(self, start_time: str = None, end_time: str = None):
        """
        Create a filter for time ranges.

        Args:
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
        """

        def time_filter(record):
            current_time = time.localtime(record.created)
            current_hour_min = current_time.tm_hour * 60 + current_time.tm_min

            if start_time:
                start_hour, start_min = map(int, start_time.split(":"))
                start_total = start_hour * 60 + start_min
                if current_hour_min < start_total:
                    return False

            if end_time:
                end_hour, end_min = map(int, end_time.split(":"))
                end_total = end_hour * 60 + end_min
                if current_hour_min > end_total:
                    return False

            return True

        return time_filter

    def create_performance_filter(self, max_duration: float = None):
        """
        Create a filter for performance-related logs.

        Args:
            max_duration: Maximum duration to log
        """

        def performance_filter(record):
            # Check if record has performance data
            duration = getattr(record, "duration", None)
            if duration is not None and max_duration is not None:
                return duration <= max_duration
            return True

        return performance_filter

    def get_filter_stats(self) -> Dict[str, Any]:
        """Get filter statistics."""
        return {
            "total_rules": len(self.rules),
            "compiled_patterns": len(self.compiled_patterns),
            "rules": [
                {
                    "name": rule.name,
                    "action": rule.action,
                    "level": rule.level,
                    "logger_name": rule.logger_name,
                    "message_pattern": rule.message_pattern,
                }
                for rule in self.rules
            ],
        }


class ConditionalFilter(logging.Filter):
    """
    Conditional filter that applies rules based on conditions.
    """

    def __init__(self, filter_rules: List[FilterRule]):
        """
        Initialize conditional filter.

        Args:
            filter_rules: List of filter rules
        """
        super().__init__()
        self.log_filter = LogFilter()
        self.log_filter.rules = filter_rules

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply conditional filtering."""
        should_log, action, rule_name = self.log_filter.should_filter(record)

        # Store filter result in record for potential use by handlers
        record.filter_action = action
        record.filter_rule = rule_name

        return should_log


class SamplingFilter(logging.Filter):
    """
    Filter that samples log messages to reduce volume.
    """

    def __init__(self, sample_rate: float = 0.1):
        """
        Initialize sampling filter.

        Args:
            sample_rate: Fraction of messages to let through (0.0 to 1.0)
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.counter = 0

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply sampling filter."""
        self.counter += 1

        # Simple sampling: every 1/sample_rate messages
        return (self.counter % int(1.0 / self.sample_rate)) == 0


class RateLimitFilter(logging.Filter):
    """
    Filter that rate limits log messages.
    """

    def __init__(self, max_per_second: int = 10):
        """
        Initialize rate limit filter.

        Args:
            max_per_second: Maximum messages per second
        """
        super().__init__()
        self.max_per_second = max_per_second
        self.window_start = time.time()
        self.message_count = 0

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply rate limiting."""
        current_time = time.time()

        # Reset window if needed
        if current_time - self.window_start >= 1.0:
            self.window_start = current_time
            self.message_count = 0

        # Check rate limit
        if self.message_count >= self.max_per_second:
            return False

        self.message_count += 1
        return True


class ContentFilter(logging.Filter):
    """
    Filter based on message content analysis.
    """

    def __init__(
        self,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
        min_length: int = 0,
        max_length: int = None,
    ):
        """
        Initialize content filter.

        Args:
            include_patterns: Patterns that must be present
            exclude_patterns: Patterns that must not be present
            min_length: Minimum message length
            max_length: Maximum message length
        """
        super().__init__()
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.min_length = min_length
        self.max_length = max_length

        # Compile patterns
        self.compiled_include = [re.compile(p) for p in self.include_patterns]
        self.compiled_exclude = [re.compile(p) for p in self.exclude_patterns]

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply content filtering."""
        message = record.getMessage()

        # Check length constraints
        if len(message) < self.min_length:
            return False

        if self.max_length and len(message) > self.max_length:
            return False

        # Check include patterns
        for pattern in self.compiled_include:
            if not pattern.search(message):
                return False

        # Check exclude patterns
        for pattern in self.compiled_exclude:
            if pattern.search(message):
                return False

        return True


class MetadataFilter(logging.Filter):
    """
    Filter based on record metadata and attributes.
    """

    def __init__(self, **filters):
        """
        Initialize metadata filter.

        Args:
            **filters: Metadata filters (key: expected_value)
        """
        super().__init__()
        self.filters = filters

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply metadata filtering."""
        for key, expected_value in self.filters.items():
            actual_value = getattr(record, key, None)

            if actual_value != expected_value:
                return False

        return True


def create_composite_filter(*filters) -> logging.Filter:
    """
    Create a composite filter that combines multiple filters.

    Args:
        *filters: Filter instances to combine

    Returns:
        Composite filter
    """

    class CompositeFilter(logging.Filter):
        def __init__(self, filters_list):
            super().__init__()
            self.filters = filters_list

        def filter(self, record):
            for filter_instance in self.filters:
                if not filter_instance.filter(record):
                    return False
            return True

    return CompositeFilter(filters)


def create_filter_from_config(config: Dict[str, Any]) -> logging.Filter:
    """
    Create a filter from configuration dictionary.

    Args:
        config: Filter configuration

    Returns:
        Configured filter
    """
    filters = []

    # Level filter
    if "level" in config:
        level_config = config["level"]
        if isinstance(level_config, dict):
            min_level = level_config.get("min")
            max_level = level_config.get("max")
            if min_level or max_level:
                filter_instance = LogFilter().create_level_filter(min_level, max_level)
                filters.append(filter_instance)

    # Logger filter
    if "loggers" in config:
        allowed_loggers = config["loggers"]
        if isinstance(allowed_loggers, list):
            filter_instance = LogFilter().create_logger_filter(allowed_loggers)
            filters.append(filter_instance)

    # Message filter
    if "messages" in config:
        message_config = config["messages"]
        if isinstance(message_config, dict):
            include_patterns = message_config.get("include", [])
            exclude_patterns = message_config.get("exclude", [])
            if include_patterns or exclude_patterns:
                filter_instance = ContentFilter(include_patterns, exclude_patterns)
                filters.append(filter_instance)

    # Sampling filter
    if "sampling" in config:
        sample_rate = config["sampling"]
        if isinstance(sample_rate, (int, float)) and 0 < sample_rate <= 1:
            filter_instance = SamplingFilter(sample_rate)
            filters.append(filter_instance)

    # Rate limit filter
    if "rate_limit" in config:
        max_per_second = config["rate_limit"]
        if isinstance(max_per_second, int) and max_per_second > 0:
            filter_instance = RateLimitFilter(max_per_second)
            filters.append(filter_instance)

    # Return composite filter or single filter
    if len(filters) == 1:
        return filters[0]
    elif len(filters) > 1:
        return create_composite_filter(*filters)
    else:
        # No filters specified, allow everything
        class AllowAllFilter(logging.Filter):
            def filter(self, record):
                return True

        return AllowAllFilter()


# Predefined filter configurations
PREDEFINED_FILTERS = {
    "debug_only": {"level": {"min": "DEBUG", "max": "DEBUG"}},
    "info_and_above": {"level": {"min": "INFO"}},
    "errors_only": {"level": {"min": "ERROR"}},
    "performance": {
        "messages": {"include": ["duration", "performance", "timing"]},
        "level": {"min": "INFO"},
    },
    "security": {
        "messages": {"include": ["login", "auth", "security", "permission"]},
        "level": {"min": "WARNING"},
    },
    "low_volume": {"sampling": 0.1, "rate_limit": 5},
}
