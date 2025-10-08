"""
CLI Utility Functions Module

This module provides utility classes and functions for CLI operations
including configuration management, output formatting, progress display,
and error handling.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from colorama import Fore, Style


class CLIConfig:
    """CLI configuration management."""

    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """Initialize CLI configuration.

        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = Path(config_file) if config_file else None
        self.config = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_file or not self.config_file.exists():
            self._load_default_config()
            return

        try:
            with open(self.config_file, "r") as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")
            self._load_default_config()

    def _load_default_config(self) -> None:
        """Load default configuration."""
        self.config = {
            "verbosity": "INFO",
            "color_output": True,
            "progress_bars": True,
            "log_file": None,
            "default_image_dir": None,
            "default_output_dir": None,
            "parallel_workers": None,
            "batch_size": 8,
            "memory_limit": "4GB",
            "jpeg_quality": 85,
            "theme": "default",
        }

    def save_config(self) -> None:
        """Save current configuration to file."""
        if not self.config_file:
            return

        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self.config.update(updates)


class OutputFormatter:
    """Consistent output formatting for CLI."""

    def __init__(self, use_colors: bool = True, verbosity: str = "INFO"):
        """Initialize output formatter.

        Args:
            use_colors: Whether to use colored output
            verbosity: Verbosity level (DEBUG, INFO, WARNING, ERROR)
        """
        self.use_colors = use_colors
        self.verbosity = verbosity.upper()
        self.verbosity_levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}

    def _should_output(self, level: str) -> bool:
        """Check if message should be output based on verbosity level."""
        return self.verbosity_levels.get(level, 1) >= self.verbosity_levels.get(
            self.verbosity, 1
        )

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self.use_colors:
            return text

        color_codes = {
            "red": Fore.RED,
            "green": Fore.GREEN,
            "yellow": Fore.YELLOW,
            "blue": Fore.BLUE,
            "magenta": Fore.MAGENTA,
            "cyan": Fore.CYAN,
            "white": Fore.WHITE,
            "bright_red": Style.BRIGHT + Fore.RED,
            "bright_green": Style.BRIGHT + Fore.GREEN,
            "bright_yellow": Style.BRIGHT + Fore.YELLOW,
            "bright_blue": Style.BRIGHT + Fore.BLUE,
        }

        color_code = color_codes.get(color, "")
        reset = Style.RESET_ALL if color_code else ""

        return f"{color_code}{text}{reset}"

    def debug(self, message: str) -> None:
        """Output debug message."""
        if self._should_output("DEBUG"):
            print(f"[{self._colorize('DEBUG', 'cyan')}] {message}")

    def info(self, message: str) -> None:
        """Output info message."""
        if self._should_output("INFO"):
            print(f"[{self._colorize('INFO', 'green')}] {message}")

    def warning(self, message: str) -> None:
        """Output warning message."""
        if self._should_output("WARNING"):
            print(f"[{self._colorize('WARN', 'yellow')}] {message}", file=sys.stderr)

    def error(self, message: str) -> None:
        """Output error message."""
        if self._should_output("ERROR"):
            print(f"[{self._colorize('ERROR', 'red')}] {message}", file=sys.stderr)

    def success(self, message: str) -> None:
        """Output success message."""
        if self._should_output("INFO"):
            print(f"[{self._colorize('SUCCESS', 'green')}] {message}")

    def header(self, message: str) -> None:
        """Output header message."""
        if self._should_output("INFO"):
            print(f"\n{self._colorize('=' * 60, 'blue')}")
            print(f"{self._colorize(message, 'bright_blue')}")
            print(f"{self._colorize('=' * 60, 'blue')}")

    def section(self, message: str) -> None:
        """Output section header."""
        if self._should_output("INFO"):
            print(f"\n{self._colorize(message, 'bright_white')}")
            print(f"{self._colorize('-' * len(message), 'white')}")

    def key_value(self, key: str, value: str, key_color: str = "cyan") -> None:
        """Output key-value pair."""
        if self._should_output("INFO"):
            colored_key = self._colorize(f"{key}:", key_color)
            print(f"  {colored_key} {value}")

    def list_item(self, message: str, bullet: str = "•") -> None:
        """Output list item."""
        if self._should_output("INFO"):
            colored_bullet = self._colorize(bullet, "green")
            print(f"  {colored_bullet} {message}")

    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 1:
            return f"{seconds * 1000:.1f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.1f}m"
        else:
            return f"{seconds / 3600:.1f}h"

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


class ProgressDisplay:
    """CLI progress indicators."""

    def __init__(self, show_progress: bool = True, use_colors: bool = True):
        """Initialize progress display.

        Args:
            show_progress: Whether to show progress bars
            use_colors: Whether to use colored output
        """
        self.show_progress = show_progress
        self.use_colors = use_colors
        self.current_task = None
        self.start_time = None

    def start_task(self, task_name: str, total: int = 100) -> None:
        """Start a new task with progress tracking."""
        self.current_task = task_name
        self.start_time = time.time()

        if self.show_progress:
            try:
                from tqdm import tqdm

                self.progress_bar = tqdm(
                    total=total,
                    desc=self._colorize_task(task_name),
                    unit="it",
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                )
            except ImportError:
                self.progress_bar = None
                print(f"Starting: {task_name}")
        else:
            print(f"Starting: {task_name}")

    def update_progress(self, advance: int = 1) -> None:
        """Update progress."""
        if self.progress_bar:
            self.progress_bar.update(advance)
        elif not self.show_progress:
            # Simple progress indicator
            print(".", end="", flush=True)

    def finish_task(self, success_message: Optional[str] = None) -> None:
        """Finish current task."""
        elapsed_time = time.time() - (self.start_time or time.time())

        if self.progress_bar:
            self.progress_bar.close()

        if not self.show_progress:
            print()  # New line after dots

        if success_message:
            print(f"✓ {success_message}")
        else:
            task_name = self.current_task or "Task"
            print(f"✓ {task_name} completed in {self._format_duration(elapsed_time)}")

        self.current_task = None
        self.start_time = None

    def show_spinner(self, message: str) -> None:
        """Show a simple spinner for indeterminate progress."""
        if not self.show_progress:
            return

        try:
            import itertools

            spinner_chars = itertools.cycle(
                ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            )

            print(f"{message} ", end="", flush=True)
            for _ in range(20):  # Show spinner for 20 cycles
                print(f"\r{message} {next(spinner_chars)}", end="", flush=True)
                time.sleep(0.1)
            print(f"\r{message} ✓")

        except (ImportError, KeyboardInterrupt):
            print(f"{message}...")

    def _colorize_task(self, task: str) -> str:
        """Colorize task name."""
        if self.use_colors:
            return f"{Fore.CYAN}{task}{Style.RESET_ALL}"
        return task

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            return f"{seconds / 60:.1f}m"


class ErrorHandler:
    """CLI error handling and reporting."""

    def __init__(self, formatter: OutputFormatter):
        """Initialize error handler.

        Args:
            formatter: Output formatter instance
        """
        self.formatter = formatter
        self.errors_count = 0
        self.warnings_count = 0

    def handle_error(
        self, error: Exception, context: str = "", exit_on_error: bool = False
    ) -> None:
        """Handle and report an error."""
        self.errors_count += 1

        error_message = str(error)
        if context:
            error_message = f"{context}: {error_message}"

        self.formatter.error(error_message)

        # Log error if logging is configured
        if hasattr(error, "__traceback__"):
            import traceback

            self.formatter.debug(f"Traceback: {traceback.format_exc()}")

        if exit_on_error:
            self.formatter.error("Exiting due to error")
            sys.exit(1)

    def handle_warning(self, message: str, context: str = "") -> None:
        """Handle and report a warning."""
        self.warnings_count += 1

        warning_message = message
        if context:
            warning_message = f"{context}: {message}"

        self.formatter.warning(warning_message)

    def handle_validation_error(self, error: Exception, field_name: str = "") -> None:
        """Handle validation error with helpful suggestions."""
        from .validation import ValidationError

        if isinstance(error, ValidationError):
            self.formatter.error(
                f"Validation error{f' in {field_name}' if field_name else ''}: {error}"
            )
            if error.suggestion:
                self.formatter.info(f"Suggestion: {error.suggestion}")
        else:
            self.handle_error(
                error, f"Validation{f' {field_name}' if field_name else ''}"
            )

    def summary(self) -> None:
        """Print error/warning summary."""
        if self.errors_count > 0 or self.warnings_count > 0:
            self.formatter.section("Summary")
            if self.errors_count > 0:
                self.formatter.error(f"Total errors: {self.errors_count}")
            if self.warnings_count > 0:
                self.formatter.warning(f"Total warnings: {self.warnings_count}")


class LoggingSetup:
    """Logging configuration for CLI."""

    @staticmethod
    def setup_logging(
        verbosity: str = "INFO",
        log_file: Optional[Union[str, Path]] = None,
        formatter: Optional[OutputFormatter] = None,
    ) -> logging.Logger:
        """Set up logging configuration.

        Args:
            verbosity: Logging verbosity level
            log_file: Optional log file path
            formatter: Optional output formatter for console output

        Returns:
            Configured logger instance
        """
        # Clear existing handlers
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Set level
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        level = level_map.get(verbosity.upper(), logging.INFO)
        logger.setLevel(level)

        # Create formatters
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_formatter = logging.Formatter("%(levelname)s: %(message)s")

        # File handler
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        return logger


def format_table(data: List[Dict[str, Any]], headers: List[str]) -> str:
    """Format data as a table string.

    Args:
        data: List of dictionaries containing the data
        headers: List of column headers

    Returns:
        Formatted table string
    """
    if not data:
        return ""

    # Calculate column widths
    col_widths = {}
    for header in headers:
        col_widths[header] = len(header)

    for row in data:
        for header in headers:
            if header in row:
                col_widths[header] = max(col_widths[header], len(str(row[header])))

    # Add padding
    for header in headers:
        col_widths[header] += 2

    # Create table
    lines = []

    # Header
    header_line = "  ".join(f"{header:<{col_widths[header]}}" for header in headers)
    lines.append(header_line)
    lines.append("-" * len(header_line))

    # Data rows
    for row in data:
        row_line = "  ".join(
            f"{str(row.get(header, '')):<{col_widths[header]}}" for header in headers
        )
        lines.append(row_line)

    return "\n".join(lines)


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user to confirm an action.

    Args:
        message: Confirmation message
        default: Default answer (True for yes, False for no)

    Returns:
        True if user confirms, False otherwise
    """
    default_text = "(Y/n)" if default else "(y/N)"

    while True:
        response = input(f"{message} {default_text} ").strip().lower()

        if not response:
            return default

        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please answer 'y' or 'n'")


def get_terminal_width() -> int:
    """Get terminal width."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
