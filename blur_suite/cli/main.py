"""
Main CLI Entry Point Module

This module provides the main command-line interface entry point with
subcommand structure for the Blur Suite SDK.
"""

import argparse
import sys
from pathlib import Path

try:
    from .utils import CLIConfig, ErrorHandler, LoggingSetup, OutputFormatter
    from .validation import ValidationError
except ImportError:
    from utils import CLIConfig, ErrorHandler, LoggingSetup, OutputFormatter
    from validation import ValidationError


def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="blur-suite",
        description="Blur Suite SDK - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  interactive    Launch the interactive configuration tool
  dataset        Create blur/clear binary classification dataset

Examples:
  %(prog)s interactive --image-dir ./documents/
  %(prog)s dataset --config config.json --output ./dataset/
  %(prog)s --version
  %(prog)s --help
        """,
    )

    # Global options
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times)",
    )

    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Decrease output verbosity"
    )

    parser.add_argument(
        "--config-file", type=str, help="Global configuration file path"
    )

    parser.add_argument("--log-file", type=str, help="Log file path")

    parser.add_argument(
        "--version",
        action="version",
        version="Blur Suite CLI 1.0.0",
        help="Show version information",
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", metavar="COMMAND"
    )

    # Interactive subcommand
    interactive_parser = subparsers.add_parser(
        "interactive",
        help="Launch interactive configuration tool",
        description="Launch the Blur Suite Interactive Configuration Tool",
    )

    _add_interactive_arguments(interactive_parser)

    # Dataset subcommand
    dataset_parser = subparsers.add_parser(
        "dataset",
        help="Create dataset",
        description="Create blur/clear binary classification dataset",
    )

    _add_dataset_arguments(dataset_parser)

    return parser


def _add_interactive_arguments(parser: argparse.ArgumentParser) -> None:
    """Add interactive tool arguments to parser."""
    parser.add_argument(
        "--image-dir",
        type=str,
        help="Directory containing document images to load on startup",
    )

    parser.add_argument(
        "--config", type=str, help="Pre-existing configuration file to load"
    )

    parser.add_argument(
        "--output-config", type=str, help="Where to save the generated configuration"
    )

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

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging verbosity level (default: INFO)",
    )

    parser.set_defaults(func=_run_interactive)


def _add_dataset_arguments(parser: argparse.ArgumentParser) -> None:
    """Add dataset creation arguments to parser."""
    parser.add_argument(
        "--config",
        required=True,
        type=str,
        help="Configuration file from interactive tool",
    )

    parser.add_argument(
        "--output", required=True, type=str, help="Output directory for the dataset"
    )

    parser.add_argument(
        "--workers", type=int, help="Number of parallel workers (default: CPU count)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Images per batch for processing (default: 8)",
    )

    parser.add_argument(
        "--memory-limit", type=str, help="Memory usage limit (e.g., 4GB, 500MB)"
    )

    parser.add_argument(
        "--resume", action="store_true", help="Resume interrupted processing"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be processed without creating files",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["PNG", "JPEG", "TIFF"],
        default="JPEG",
        help="Output image format (default: JPEG)",
    )

    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="Output image quality/compression (1-100, default: 85)",
    )

    parser.set_defaults(func=_run_dataset)


def _run_interactive(args: argparse.Namespace) -> None:
    """Run interactive tool command."""
    from .interactive import launch_interactive

    # Convert args to function arguments
    kwargs = {
        "image_dir": args.image_dir,
        "config_file": args.config,
        "output_config": args.output_config,
        "log_level": args.log_level,
        "theme": args.theme,
        "geometry": args.geometry,
    }

    success = launch_interactive(**kwargs)
    sys.exit(0 if success else 1)


def _run_dataset(args: argparse.Namespace) -> None:
    """Run dataset creation command."""
    from .dataset import create_dataset

    # Convert args to function arguments
    kwargs = {
        "config": args.config,
        "output": args.output,
        "workers": args.workers,
        "batch_size": args.batch_size,
        "memory_limit": args.memory_limit,
        "resume": args.resume,
        "dry_run": args.dry_run,
        "format": args.format,
        "quality": args.quality,
    }

    success = create_dataset(**kwargs)
    sys.exit(0 if success else 1)


def _determine_verbosity(args: argparse.Namespace) -> str:
    """Determine verbosity level from arguments."""
    if args.quiet:
        return "ERROR"
    elif args.verbose >= 2:
        return "DEBUG"
    elif args.verbose >= 1:
        return "INFO"
    else:
        return "INFO"


def _setup_global_config(args: argparse.Namespace) -> CLIConfig:
    """Set up global configuration."""
    config_file = args.config_file
    if not config_file:
        # Use default config location
        config_file = Path.home() / ".blur_suite_cli.json"

    return CLIConfig(config_file)


def main() -> None:
    """Main CLI entry point."""
    # Initialize components
    formatter = OutputFormatter()
    error_handler = ErrorHandler(formatter)

    try:
        # Parse arguments
        parser = create_main_parser()
        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        # Set up global configuration
        _setup_global_config(args)

        # Set up logging
        verbosity = _determine_verbosity(args)
        log_file = args.log_file

        LoggingSetup.setup_logging(
            verbosity=verbosity, log_file=log_file, formatter=formatter
        )

        # Run the appropriate subcommand
        args.func(args)

    except KeyboardInterrupt:
        formatter.info("Operation cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except BrokenPipeError:
        # Handle broken pipe (e.g., when piping output)
        sys.exit(0)
    except ValidationError as e:
        error_handler.handle_validation_error(e)
        sys.exit(1)
    except Exception as e:
        error_handler.handle_error(e, "Unexpected error")
        sys.exit(1)


if __name__ == "__main__":
    main()
