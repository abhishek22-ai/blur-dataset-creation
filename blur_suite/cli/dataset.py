"""
Dataset Creation CLI Module

This module provides the command-line interface for creating blur/clear
binary classification datasets using the Blur Suite SDK.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from .utils import ErrorHandler, LoggingSetup, OutputFormatter, ProgressDisplay
    from .validation import (
        ConfigValidator,
        ParameterValidator,
        PathValidator,
        ValidationError,
    )
except ImportError:
    from utils import ErrorHandler, LoggingSetup, OutputFormatter, ProgressDisplay
    from validation import (
        ConfigValidator,
        ParameterValidator,
        PathValidator,
        ValidationError,
    )


def create_dataset(
    config: str,
    output: str,
    workers: Optional[int] = None,
    batch_size: int = 8,
    memory_limit: Optional[str] = None,
    resume: bool = False,
    dry_run: bool = False,
    format: str = "JPEG",
    quality: int = 85,
    **kwargs,
) -> bool:
    """Create a blur/clear binary classification dataset.

    Args:
        config: Configuration file from interactive tool
        output: Output directory for the dataset
        workers: Number of parallel workers
        batch_size: Images per batch for processing
        memory_limit: Memory usage limit (e.g., '4GB')
        resume: Resume interrupted processing
        dry_run: Preview what would be processed
        format: Output image format (PNG, JPEG, TIFF)
        quality: Output image quality/compression (1-100)
        **kwargs: Additional arguments

    Returns:
        True if successful, False otherwise
    """
    # Initialize components
    formatter = OutputFormatter()
    error_handler = ErrorHandler(formatter)
    progress = ProgressDisplay()

    # Set up logging
    LoggingSetup.setup_logging("INFO")

    formatter.header("Blur Suite Dataset Creation")

    try:
        # Validate inputs
        formatter.section("Validating Inputs")

        # Validate configuration file
        config_path = PathValidator.validate_config_file(config, "Configuration file")
        formatter.info(f"Configuration file: {config_path}")

        # Load and validate configuration
        config_data = ConfigValidator.validate_config_file(config_path)
        formatter.info("Configuration file validated")

        # Validate output directory
        output_path = PathValidator.validate_output_directory(
            output, "Output directory"
        )
        formatter.info(f"Output directory: {output_path}")

        # Validate format
        format = format.upper()
        valid_formats = ["PNG", "JPEG", "TIFF"]
        if format not in valid_formats:
            raise ValidationError(
                f"Invalid format '{format}'", f"Valid formats: {valid_formats}"
            )

        # Validate quality
        quality = ParameterValidator.validate_percentage(quality, "Quality")

        # Validate batch size
        batch_size = ParameterValidator.validate_positive_integer(
            batch_size, "Batch size", 1
        )

        # Validate workers
        if workers is not None:
            workers = ParameterValidator.validate_positive_integer(
                workers, "Workers", 1
            )

        # Validate memory limit
        if memory_limit:
            memory_bytes = ParameterValidator.validate_file_size_limit(memory_limit)
            formatter.info(
                f"Memory limit: {memory_limit} ({memory_bytes // (1024**3):.1f} GB)"
            )

        # Check for resume
        if resume and not dry_run:
            if not _can_resume(output_path):
                formatter.warning(
                    "Cannot resume: output directory is empty or doesn't exist"
                )
                resume = False

        # Dry run preview
        if dry_run:
            return _dry_run_preview(config_data, output_path, formatter)

        formatter.section("Creating Dataset")

        # Import and run dataset creation
        try:
            from ..dataset_creator import DatasetCreator

            formatter.info("Initializing dataset creator...")

            # Create dataset creator instance
            creator = DatasetCreator(
                input_dir=config_data.get("image_directory", ""),
                output_dir=str(output_path),
                batch_size=batch_size,
            )

            # Set up progress tracking
            progress.start_task("Creating dataset", 100)

            # Create the dataset
            creator.create_dataset()

            progress.finish_task("Dataset creation completed successfully!")

            # Print final statistics
            _print_dataset_stats(output_path, formatter)

            return True

        except ImportError as e:
            raise ValidationError(
                f"Failed to import dataset creator: {e}",
                "Make sure all dependencies are installed",
            )
        except Exception as e:
            raise ValidationError(f"Failed to create dataset: {e}")

    except ValidationError as e:
        error_handler.handle_validation_error(e)
        return False
    except Exception as e:
        error_handler.handle_error(e, "Unexpected error")
        return False


def _dry_run_preview(
    config_data: Dict[str, Any], output_path: Path, formatter: OutputFormatter
) -> bool:
    """Perform dry run preview of dataset creation."""
    formatter.section("Dry Run Preview")

    # Analyze configuration
    formatter.info("Configuration Analysis:")
    formatter.key_value("Blur type", config_data.get("blur_type", "N/A"))
    formatter.key_value(
        "Parameters", json.dumps(config_data.get("parameters", {}), indent=2)
    )

    # Estimate dataset size
    image_configs = config_data.get("image_configurations", {})
    total_images = len(image_configs)

    if total_images == 0:
        formatter.warning("No image configurations found in config file")
        return False

    formatter.info("Dataset Preview:")
    formatter.key_value("Total images", str(total_images))
    formatter.key_value("Output directory", str(output_path))
    formatter.key_value(
        "Estimated clear images", str(total_images * 3)
    )  # 3 augmentations per image
    formatter.key_value("Estimated blur images", str(total_images * 3))
    formatter.key_value("Estimated total", str(total_images * 6))

    # Show sample image configurations
    formatter.section("Sample Image Configurations")
    sample_configs = list(image_configs.values())[:3]  # Show first 3

    for i, img_config in enumerate(sample_configs):
        formatter.list_item(
            f"Image {i + 1}: {img_config.get('image_info', {}).get('filename', 'Unknown')}"
        )
        formatter.key_value("  Blur type", img_config.get("blur_type", "N/A"))
        formatter.key_value("  Enabled", str(img_config.get("enabled", False)))

    formatter.success("Dry run completed - no files were created")
    return True


def _can_resume(output_path: Path) -> bool:
    """Check if dataset creation can be resumed."""
    if not output_path.exists():
        return False

    # Check for existing train/test directories
    train_dir = output_path / "train"
    test_dir = output_path / "test"

    if not (train_dir.exists() and test_dir.exists()):
        return False

    # Check for existing data
    has_clear = any((train_dir / "clear").iterdir()) or any(
        (test_dir / "clear").iterdir()
    )
    has_blur = any((train_dir / "blur").iterdir()) or any((test_dir / "blur").iterdir())

    return has_clear or has_blur


def _print_dataset_stats(output_path: Path, formatter: OutputFormatter) -> None:
    """Print final dataset statistics."""
    formatter.section("Dataset Statistics")

    try:
        train_clear = len(list((output_path / "train" / "clear").glob("*.jpg")))
        train_blur = len(list((output_path / "train" / "blur").glob("*.jpg")))
        test_clear = len(list((output_path / "test" / "clear").glob("*.jpg")))
        test_blur = len(list((output_path / "test" / "blur").glob("*.jpg")))

        formatter.key_value("Train - Clear", str(train_clear))
        formatter.key_value("Train - Blur", str(train_blur))
        formatter.key_value("Test - Clear", str(test_clear))
        formatter.key_value("Test - Blur", str(test_blur))
        formatter.key_value(
            "Total images", str(train_clear + train_blur + test_clear + test_blur)
        )

        # Calculate percentages
        total = train_clear + train_blur + test_clear + test_blur
        if total > 0:
            train_pct = (train_clear + train_blur) / total * 100
            test_pct = (test_clear + test_blur) / total * 100
            formatter.key_value(
                "Train/Test split", f"{train_pct:.1f}% / {test_pct:.1f}%"
            )

    except Exception as e:
        formatter.warning(f"Could not calculate statistics: {e}")


def create_dataset_parser() -> argparse.ArgumentParser:
    """Create argument parser for dataset creation CLI."""
    parser = argparse.ArgumentParser(
        prog="blur-suite dataset",
        description="Create blur/clear binary classification dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config.json --output ./dataset/
  %(prog)s --config config.json --output ./dataset/ --workers 8
  %(prog)s --config config.json --output ./dataset/ --batch-size 50 --memory-limit 4GB
  %(prog)s --config config.json --output ./dataset/ --dry-run
  %(prog)s --config config.json --output ./dataset/ --resume
        """,
    )

    # Required arguments
    parser.add_argument(
        "--config",
        required=True,
        type=str,
        help="Configuration file from interactive tool",
    )

    parser.add_argument(
        "--output", required=True, type=str, help="Output directory for the dataset"
    )

    # Processing options
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

    # Operation modes
    parser.add_argument(
        "--resume", action="store_true", help="Resume interrupted processing"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be processed without creating files",
    )

    # Output options
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

    return parser


def main():
    """Main entry point for dataset creation CLI."""
    parser = create_dataset_parser()
    args = parser.parse_args()

    # Convert args to function arguments
    kwargs = vars(args)

    success = create_dataset(**kwargs)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
