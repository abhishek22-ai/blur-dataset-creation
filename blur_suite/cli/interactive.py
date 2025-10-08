"""
Interactive Tool CLI Module

This module provides the command-line interface for launching the
Blur Suite Interactive Configuration Tool with various options.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    from .utils import CLIConfig, ErrorHandler, LoggingSetup, OutputFormatter
    from .validation import PathValidator, ValidationError
except ImportError:
    from utils import ErrorHandler, LoggingSetup, OutputFormatter
    from validation import PathValidator, ValidationError


def launch_interactive(
    image_dir: Optional[str] = None,
    config_file: Optional[str] = None,
    output_config: Optional[str] = None,
    log_level: str = "INFO",
    theme: str = "default",
    geometry: Optional[str] = None,
    **kwargs,
) -> bool:
    """Launch the interactive blur configuration tool.

    Args:
        image_dir: Directory containing images to load
        config_file: Pre-existing configuration file to load
        output_config: Where to save the generated configuration
        log_level: Logging verbosity level
        theme: GUI theme selection
        geometry: Window size specification (e.g., "1400x900")
        **kwargs: Additional arguments

    Returns:
        True if successful, False otherwise
    """
    # Initialize components
    formatter = OutputFormatter(verbosity=log_level)
    error_handler = ErrorHandler(formatter)

    # Set up logging
    LoggingSetup.setup_logging(log_level)

    formatter.header("Blur Suite Interactive Configuration Tool")

    try:
        # Validate inputs
        if image_dir:
            image_dir = PathValidator.validate_directory_exists(
                image_dir, "Image directory"
            )
            formatter.info(f"Image directory: {image_dir}")

        if config_file:
            config_file = PathValidator.validate_file_exists(
                config_file, "Configuration file"
            )
            formatter.info(f"Configuration file: {config_file}")

        if output_config:
            output_dir = Path(output_config).parent
            if output_dir.exists():
                PathValidator.validate_directory_writable(
                    output_dir, "Output directory"
                )
            formatter.info(f"Output config: {output_config}")

        # Validate theme
        valid_themes = ["default", "dark", "light", "blue", "green"]
        if theme not in valid_themes:
            raise ValidationError(
                f"Invalid theme '{theme}'", f"Valid themes: {valid_themes}"
            )

        # Validate geometry if provided
        if geometry:
            geometry_pattern = r"^\d+x\d+$"
            import re

            if not re.match(geometry_pattern, geometry):
                raise ValidationError(
                    f"Invalid geometry format: {geometry}",
                    "Use format like '1400x900' or '1200x800'",
                )

        formatter.info(f"Theme: {theme}")
        if geometry:
            formatter.info(f"Window geometry: {geometry}")

        # Import and launch the interactive tool
        formatter.section("Launching Interactive Tool")

        try:
            # Import the main application class
            from ..interactive.app import BlurSuiteApp

            formatter.info("Initializing application...")

            # Create application instance
            app = BlurSuiteApp()

            # Set up configuration if provided
            if config_file:
                formatter.info(f"Loading configuration from: {config_file}")
                # TODO: Implement configuration loading in BlurSuiteApp

            if image_dir:
                formatter.info(f"Setting image directory to: {image_dir}")
                # TODO: Implement image directory setting in BlurSuiteApp

            # Create GUI
            formatter.info("Creating GUI...")
            app.create_gui()

            # Apply theme and geometry if specified
            if theme != "default":
                formatter.debug(f"Applying theme: {theme}")
                # TODO: Implement theme application

            if geometry:
                formatter.debug(f"Setting window geometry: {geometry}")
                # TODO: Implement geometry setting

            # Launch the application
            formatter.success("Interactive tool launched successfully!")
            formatter.info("Use Ctrl+O to load images, Ctrl+S to export configurations")
            formatter.info("Close the GUI window to exit")

            app.run()
            return True

        except ImportError as e:
            raise ValidationError(
                f"Failed to import interactive tool: {e}",
                "Make sure all dependencies are installed (tkinter, PIL, etc.)",
            )
        except Exception as e:
            raise ValidationError(f"Failed to launch interactive tool: {e}")

    except ValidationError as e:
        error_handler.handle_validation_error(e)
        return False
    except Exception as e:
        error_handler.handle_error(e, "Unexpected error")
        return False


def create_interactive_parser() -> argparse.ArgumentParser:
    """Create argument parser for interactive tool CLI."""
    parser = argparse.ArgumentParser(
        prog="blur-suite interactive",
        description="Launch the Blur Suite Interactive Configuration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --image-dir ./documents/
  %(prog)s --image-dir ./docs/ --config config.json
  %(prog)s --image-dir ./docs/ --log-level DEBUG --theme dark
  %(prog)s --image-dir ./docs/ --geometry 1600x1000
        """,
    )

    # Image source options
    parser.add_argument(
        "--image-dir",
        type=str,
        help="Directory containing document images to load on startup",
    )

    # Configuration options
    parser.add_argument(
        "--config", type=str, help="Pre-existing configuration file to load"
    )

    parser.add_argument(
        "--output-config", type=str, help="Where to save the generated configuration"
    )

    # GUI options
    parser.add_argument(
        "--theme",
        type=str,
        choices=["default", "dark", "light", "blue", "green"],
        default="default",
        help="GUI theme selection (default: default)",
    )

    parser.add_argument(
        "--geometry",
        type=str,
        help="Window size specification (e.g., 1400x900, 1200x800)",
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging verbosity level (default: INFO)",
    )

    return parser


def main():
    """Main entry point for interactive tool CLI."""
    parser = create_interactive_parser()
    args = parser.parse_args()

    # Convert args to function arguments
    kwargs = vars(args)

    success = launch_interactive(**kwargs)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
