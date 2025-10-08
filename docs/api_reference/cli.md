# CLI API Reference

This document provides comprehensive API documentation for the Blur Suite SDK command-line interface module, including batch processing commands, configuration management, and automation workflows.

## Overview

The CLI module provides:
- **Command-line interface** for batch processing operations
- **Configuration file management** and validation
- **Interactive mode** for guided workflows
- **Plugin management** and discovery
- **Performance monitoring** and reporting

## Module Structure

```
blur_suite/cli/
├── __init__.py           # Module exports
├── main.py              # Main CLI entry point
├── commands/
│   ├── __init__.py      # Command definitions
│   ├── process.py       # Processing commands
│   ├── config.py        # Configuration commands
│   ├── validate.py      # Validation commands
│   ├── info.py         # Information commands
│   └── plugin.py       # Plugin management commands
├── utils/
│   ├── __init__.py      # CLI utilities
│   ├── parsing.py      # Argument parsing
│   └── formatting.py   # Output formatting
└── interactive/
    ├── __init__.py      # Interactive CLI mode
    └── prompts.py      # User prompts and input
```

## Quick Start

```bash
# Install CLI module
pip install blur_suite[cli]

# Basic usage
blur-suite process single input.jpg output.png --blur-type gaussian --kernel-size 7

# Show help
blur-suite --help
```

## Main Classes

### BlurCLI

Main CLI application class.

```python
class BlurCLI:
    """Main command-line interface class."""

    def __init__(self):
        """Initialize CLI application."""
        self.parser = self._create_argument_parser()
        self.subcommands = self._register_subcommands()

    def run(self, args: List[str] = None) -> int:
        """Run CLI with provided arguments.

        Args:
            args: Command-line arguments (uses sys.argv if None)

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        if args is None:
            args = sys.argv[1:]

        try:
            # Parse arguments
            parsed_args = self.parser.parse_args(args)

            # Execute command
            return self._execute_command(parsed_args)

        except SystemExit as e:
            return e.code
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _create_argument_parser(self) -> ArgumentParser:
        """Create main argument parser.

        Returns:
            Configured ArgumentParser
        """
        parser = ArgumentParser(
            prog="blur-suite",
            description="Blur Suite SDK Command Line Interface",
            formatter_class=RawDescriptionHelpFormatter
        )

        # Add global options
        parser.add_argument(
            "--version",
            action="version",
            version=f"Blur Suite CLI {self._get_version()}"
        )

        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )

        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug mode"
        )

        parser.add_argument(
            "--config",
            help="Path to configuration file"
        )

        # Create subparsers for commands
        subparsers = parser.add_subparsers(
            dest="command",
            help="Available commands"
        )

        # Register command parsers
        self._register_command_parsers(subparsers)

        return parser

    def _execute_command(self, args) -> int:
        """Execute parsed command.

        Args:
            args: Parsed command arguments

        Returns:
            Exit code
        """
        if not args.command:
            self.parser.print_help()
            return 0

        # Get command handler
        command_handler = self.subcommands.get(args.command)
        if not command_handler:
            print(f"Unknown command: {args.command}")
            return 1

        # Execute command
        try:
            return command_handler.execute(args)
        except Exception as e:
            print(f"Command execution failed: {e}")
            if args.debug:
                traceback.print_exc()
            return 1
```

## Command Classes

### ProcessCommand

Handles image processing operations.

```python
class ProcessCommand:
    """Command for processing images with blur effects."""

    def __init__(self):
        """Initialize process command."""
        self.name = "process"
        self.help = "Process images with blur effects"

    def create_parser(self, subparsers) -> ArgumentParser:
        """Create argument parser for process command.

        Args:
            subparsers: Subparsers object from main parser

        Returns:
            Configured ArgumentParser
        """
        process_parser = subparsers.add_parser(
            self.name,
            help=self.help,
            formatter_class=RawDescriptionHelpFormatter
        )

        # Create sub-subparsers for process modes
        mode_subparsers = process_parser.add_subparsers(
            dest="mode",
            help="Processing mode"
        )

        # Single image processing
        single_parser = mode_subparsers.add_parser(
            "single",
            help="Process single image"
        )
        self._add_single_image_arguments(single_parser)

        # Batch processing
        batch_parser = mode_subparsers.add_parser(
            "batch",
            help="Process multiple images from directory"
        )
        self._add_batch_arguments(batch_parser)

        # Directory processing
        dir_parser = mode_subparsers.add_parser(
            "directory",
            help="Process all images in directory"
        )
        self._add_directory_arguments(dir_parser)

        return process_parser

    def execute(self, args) -> int:
        """Execute process command.

        Args:
            args: Parsed command arguments

        Returns:
            Exit code
        """
        try:
            if args.mode == "single":
                return self._process_single_image(args)
            elif args.mode == "batch":
                return self._process_batch(args)
            elif args.mode == "directory":
                return self._process_directory(args)
            else:
                print("No processing mode specified")
                return 1

        except Exception as e:
            print(f"Processing failed: {e}")
            return 1

    def _add_single_image_arguments(self, parser: ArgumentParser) -> None:
        """Add arguments for single image processing."""
        parser.add_argument(
            "input_path",
            help="Path to input image"
        )

        parser.add_argument(
            "output_path",
            help="Path for output image"
        )

        parser.add_argument(
            "--blur-type",
            required=True,
            choices=["gaussian", "motion", "defocus", "average", "bilateral"],
            help="Type of blur effect to apply"
        )

        # Add blur-specific parameters
        self._add_blur_parameters(parser)

        parser.add_argument(
            "--output-format",
            default="png",
            choices=["png", "jpg", "jpeg", "tiff", "bmp"],
            help="Output image format"
        )

        parser.add_argument(
            "--quality",
            type=int,
            default=95,
            help="Output quality (1-100)"
        )

    def _add_batch_arguments(self, parser: ArgumentParser) -> None:
        """Add arguments for batch processing."""
        parser.add_argument(
            "input_dir",
            help="Input directory containing images"
        )

        parser.add_argument(
            "output_dir",
            help="Output directory for processed images"
        )

        parser.add_argument(
            "--config",
            required=True,
            help="Path to configuration file"
        )

        parser.add_argument(
            "--workers",
            type=int,
            default=4,
            help="Number of parallel workers"
        )

        parser.add_argument(
            "--chunk-size",
            type=int,
            default=20,
            help="Images per processing chunk"
        )

        parser.add_argument(
            "--continue-on-error",
            action="store_true",
            help="Continue processing if some images fail"
        )

    def _process_single_image(self, args) -> int:
        """Process single image."""
        try:
            # Load image
            image = self._load_image(args.input_path)

            # Create blur effect
            effect = self._create_blur_effect(args.blur_type, args)

            # Apply blur
            result = effect.apply(image)

            # Save result
            self._save_image(result.result_image, args.output_path, args.output_format)

            print(f"✅ Processed {args.input_path} -> {args.output_path}")
            return 0

        except Exception as e:
            print(f"❌ Failed to process image: {e}")
            return 1
```

### ConfigCommand

Handles configuration file operations.

```python
class ConfigCommand:
    """Command for configuration file management."""

    def __init__(self):
        """Initialize config command."""
        self.name = "config"
        self.help = "Manage configuration files"

    def create_parser(self, subparsers) -> ArgumentParser:
        """Create argument parser for config command."""
        config_parser = subparsers.add_parser(
            self.name,
            help=self.help
        )

        # Create sub-subparsers for config operations
        op_subparsers = config_parser.add_subparsers(
            dest="operation",
            help="Configuration operation"
        )

        # Create configuration
        create_parser = op_subparsers.add_parser(
            "create",
            help="Create new configuration file"
        )
        self._add_create_arguments(create_parser)

        # Validate configuration
        validate_parser = op_subparsers.add_parser(
            "validate",
            help="Validate configuration file"
        )
        self._add_validate_arguments(validate_parser)

        # Convert configuration format
        convert_parser = op_subparsers.add_parser(
            "convert",
            help="Convert configuration between formats"
        )
        self._add_convert_arguments(convert_parser)

        return config_parser

    def execute(self, args) -> int:
        """Execute config command."""
        try:
            if args.operation == "create":
                return self._create_config(args)
            elif args.operation == "validate":
                return self._validate_config(args)
            elif args.operation == "convert":
                return self._convert_config(args)
            else:
                print("No configuration operation specified")
                return 1

        except Exception as e:
            print(f"Configuration operation failed: {e}")
            return 1

    def _create_config(self, args) -> int:
        """Create new configuration file."""
        try:
            # Find images in input directory
            image_paths = self._find_images(args.image_dir)

            if not image_paths:
                print(f"No images found in {args.image_dir}")
                return 1

            # Create sample configurations
            config = self._create_sample_config(image_paths, args)

            # Save configuration
            with open(args.output, 'w') as f:
                json.dump(config, f, indent=2)

            print(f"✅ Created configuration with {len(image_paths)} images: {args.output}")
            return 0

        except Exception as e:
            print(f"❌ Failed to create configuration: {e}")
            return 1
```

### ValidateCommand

Handles validation operations.

```python
class ValidateCommand:
    """Command for validation operations."""

    def __init__(self):
        """Initialize validate command."""
        self.name = "validate"
        self.help = "Validate configurations and setups"

    def create_parser(self, subparsers) -> ArgumentParser:
        """Create argument parser for validate command."""
        validate_parser = subparsers.add_parser(
            self.name,
            help=self.help
        )

        # Create sub-subparsers for validation types
        type_subparsers = validate_parser.add_subparsers(
            dest="validation_type",
            help="Type of validation to perform"
        )

        # Setup validation
        setup_parser = type_subparsers.add_parser(
            "setup",
            help="Validate system setup"
        )
        self._add_setup_arguments(setup_parser)

        # Image validation
        image_parser = type_subparsers.add_parser(
            "images",
            help="Validate image files"
        )
        self._add_image_arguments(image_parser)

        return validate_parser

    def execute(self, args) -> int:
        """Execute validate command."""
        try:
            if args.validation_type == "setup":
                return self._validate_setup(args)
            elif args.validation_type == "images":
                return self._validate_images(args)
            else:
                print("No validation type specified")
                return 1

        except Exception as e:
            print(f"Validation failed: {e}")
            return 1

    def _validate_setup(self, args) -> int:
        """Validate system setup."""
        issues = []

        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            issues.append(f"Python {python_version.major}.{python_version.minor} is not supported")

        # Check required packages
        required_packages = ["numpy", "pillow", "scipy"]
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                issues.append(f"Required package not found: {package}")

        # Check system resources
        memory_gb = psutil.virtual_memory().available / 1024 / 1024 / 1024
        if memory_gb < 2:
            issues.append(f"Insufficient memory: {memory_gb:.1f}GB available")

        # Report results
        if not issues:
            print("✅ System setup is valid")
            return 0
        else:
            print("❌ Setup issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
```

### InfoCommand

Provides system and SDK information.

```python
class InfoCommand:
    """Command for displaying information."""

    def __init__(self):
        """Initialize info command."""
        self.name = "info"
        self.help = "Display system and SDK information"

    def create_parser(self, subparsers) -> ArgumentParser:
        """Create argument parser for info command."""
        info_parser = subparsers.add_parser(
            self.name,
            help=self.help
        )

        # Create sub-subparsers for info types
        type_subparsers = info_parser.add_subparsers(
            dest="info_type",
            help="Type of information to display"
        )

        # System information
        system_parser = type_subparsers.add_parser(
            "system",
            help="Display system information"
        )
        self._add_system_arguments(system_parser)

        # SDK information
        sdk_parser = type_subparsers.add_parser(
            "sdk",
            help="Display SDK information"
        )
        self._add_sdk_arguments(sdk_parser)

        return info_parser

    def execute(self, args) -> int:
        """Execute info command."""
        try:
            if args.info_type == "system":
                return self._show_system_info(args)
            elif args.info_type == "sdk":
                return self._show_sdk_info(args)
            else:
                print("No information type specified")
                return 1

        except Exception as e:
            print(f"Failed to get information: {e}")
            return 1

    def _show_system_info(self, args) -> int:
        """Show system information."""
        info = {
            "Platform": platform.platform(),
            "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "CPU Cores": psutil.cpu_count(),
            "Memory (GB)": f"{psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}",
            "Architecture": platform.architecture()[0]
        }

        if args.all_details:
            # Add more detailed information
            info.update({
                "CPU Frequency": f"{psutil.cpu_freq().current:.0f} MHz" if psutil.cpu_freq() else "Unknown",
                "Load Average": " ".join(f"{x:.2f}" for x in os.getloadavg()) if hasattr(os, 'getloadavg') else "N/A"
            })

        # Format output
        if args.output_format == "json":
            print(json.dumps(info, indent=2))
        else:
            for key, value in info.items():
                print(f"{key}: {value}")

        return 0
```

### InteractiveCommand

Launches interactive configuration tool.

```python
class InteractiveCommand:
    """Command for launching interactive tool."""

    def __init__(self):
        """Initialize interactive command."""
        self.name = "interactive"
        self.help = "Launch interactive configuration tool"

    def create_parser(self, subparsers) -> ArgumentParser:
        """Create argument parser for interactive command."""
        interactive_parser = subparsers.add_parser(
            self.name,
            help=self.help
        )

        interactive_parser.add_argument(
            "--config",
            help="Configuration file to load"
        )

        interactive_parser.add_argument(
            "--image",
            help="Image file to load initially"
        )

        interactive_parser.add_argument(
            "--theme",
            choices=["light", "dark", "auto"],
            default="auto",
            help="UI theme"
        )

        interactive_parser.add_argument(
            "--geometry",
            help="Window geometry (WxH+X+Y)"
        )

        interactive_parser.add_argument(
            "--fullscreen",
            action="store_true",
            help="Start in fullscreen mode"
        )

        return interactive_parser

    def execute(self, args) -> int:
        """Execute interactive command."""
        try:
            # Import here to avoid GUI dependencies if not needed
            from blur_suite.interactive import BlurSuiteApp

            # Create application
            app = BlurSuiteApp()

            # Apply command-line options
            if args.config:
                app.load_configuration(args.config)

            if args.image:
                app.load_image(args.image)

            # Launch GUI
            app.create_gui()
            app.run()

            return 0

        except ImportError as e:
            print(f"Cannot launch interactive tool: {e}")
            print("Make sure GUI dependencies are installed:")
            print("pip install pyqt5 pyqtwebengine")
            return 1
        except Exception as e:
            print(f"Failed to launch interactive tool: {e}")
            return 1
```

## Utility Classes

### ArgumentParser

Enhanced argument parser with additional features.

```python
class BlurArgumentParser(ArgumentParser):
    """Enhanced argument parser for Blur Suite CLI."""

    def __init__(self, *args, **kwargs):
        """Initialize enhanced argument parser."""
        super().__init__(*args, **kwargs)
        self._custom_validators = {}

    def add_blur_type_argument(self, *args, **kwargs) -> None:
        """Add blur type argument with validation."""
        choices = ["gaussian", "motion", "defocus", "average", "bilateral"]

        self.add_argument(
            *args,
            choices=choices,
            help="Blur effect type (%(choices)s)",
            **kwargs
        )

    def add_blur_parameters(self, blur_type: str) -> None:
        """Add blur-specific parameter arguments.

        Args:
            blur_type: Type of blur effect
        """
        if blur_type == "gaussian":
            self.add_argument("--kernel-size", type=int, default=5)
            self.add_argument("--sigma-x", type=float, default=1.0)
            self.add_argument("--sigma-y", type=float, default=None)
        elif blur_type == "motion":
            self.add_argument("--angle", type=float, default=0.0)
            self.add_argument("--length", type=int, default=10)
        elif blur_type == "defocus":
            self.add_argument("--radius", type=int, default=5)
            self.add_argument("--strength", type=float, default=1.0)
        elif blur_type == "average":
            self.add_argument("--kernel-size", type=int, default=5)
        elif blur_type == "bilateral":
            self.add_argument("--diameter", type=int, default=9)
            self.add_argument("--sigma-color", type=float, default=75.0)
            self.add_argument("--sigma-space", type=float, default=75.0)
```

### OutputFormatter

Formats CLI output in various formats.

```python
class OutputFormatter:
    """Formatter for CLI output."""

    @staticmethod
    def format_progress(current: int, total: int, width: int = 50) -> str:
        """Format progress bar.

        Args:
            current: Current progress
            total: Total items
            width: Progress bar width

        Returns:
            Formatted progress bar string
        """
        percentage = current / total if total > 0 else 0
        filled_width = int(width * percentage)
        bar = "█" * filled_width + "░" * (width - filled_width)

        return f"[{bar}] {current}/{total} ({percentage*100:.1f}%)"

    @staticmethod
    def format_time(seconds: float) -> str:
        """Format time duration.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            seconds = seconds % 60
            return f"{minutes}m {seconds:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    @staticmethod
    def format_file_size(bytes: int) -> str:
        """Format file size.

        Args:
            bytes: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f}{unit}"
            bytes /= 1024
        return f"{bytes:.1f}TB"
```

## Integration Examples

### Python API Integration

```python
#!/usr/bin/env python3
"""
Example: Using CLI module from Python
"""

import subprocess
import json
from pathlib import Path

class BlurSuiteCLIManager:
    """Manager for Blur Suite CLI operations."""

    def __init__(self):
        """Initialize CLI manager."""
        self.base_command = ["blur-suite"]

    def run_command(self, args: List[str]) -> Tuple[str, str, int]:
        """Run blur-suite command.

        Args:
            args: Command arguments

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        try:
            result = subprocess.run(
                self.base_command + args,
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout, result.stderr, result.returncode
        except FileNotFoundError:
            raise RuntimeError("blur-suite command not found")

    def process_single_image(self, input_path: str, output_path: str, **kwargs) -> bool:
        """Process single image using CLI.

        Args:
            input_path: Input image path
            output_path: Output image path
            **kwargs: Blur parameters

        Returns:
            True if successful
        """
        args = ["process", "single", input_path, output_path]

        # Add blur parameters
        if "blur_type" in kwargs:
            args.extend(["--blur-type", kwargs["blur_type"]])

        for key, value in kwargs.items():
            if key != "blur_type":
                args.extend([f"--{key.replace('_', '-')}", str(value)])

        stdout, stderr, return_code = self.run_command(args)

        if return_code == 0:
            print(f"✅ Processed: {stdout.strip()}")
            return True
        else:
            print(f"❌ Failed: {stderr.strip()}")
            return False

    def validate_configuration(self, config_path: str) -> bool:
        """Validate configuration file.

        Args:
            config_path: Path to configuration file

        Returns:
            True if valid
        """
        stdout, stderr, return_code = self.run_command([
            "config", "validate", config_path
        ])

        if return_code == 0:
            print("✅ Configuration is valid")
            return True
        else:
            print(f"❌ Configuration issues: {stderr}")
            return False

# Usage example
if __name__ == "__main__":
    cli_manager = BlurSuiteCLIManager()

    # Validate configuration
    if not cli_manager.validate_configuration("dataset_config.json"):
        exit(1)

    # Process sample image
    success = cli_manager.process_single_image(
        "sample.jpg",
        "blurred_sample.png",
        blur_type="gaussian",
        kernel_size=7,
        sigma_x=1.5
    )

    if success:
        print("✅ CLI processing completed successfully!")
```

### Shell Script Integration

```bash
#!/bin/bash
# blur_suite_automation.sh

# Function to process images with error handling
process_with_cli() {
    local input="$1"
    local output="$2"
    local blur_type="$3"
    shift 3
    local params=("$@")

    echo "Processing $input with $blur_type blur..."

    # Build parameter arguments
    local param_args=()
    for param in "${params[@]}"; do
        param_args+=("$param")
    done

    # Run processing
    blur-suite process single "$input" "$output" \
        --blur-type "$blur_type" \
        "${param_args[@]}" \
        --verbose

    return $?
}

# Function to validate setup
validate_setup() {
    echo "Validating setup..."

    if ! command -v blur-suite &> /dev/null; then
        echo "❌ blur-suite command not found"
        return 1
    fi

    if ! blur-suite validate setup; then
        echo "❌ Setup validation failed"
        return 1
    fi

    echo "✅ Setup validation passed"
    return 0
}

# Function to create configuration
create_config() {
    local image_dir="$1"
    local output_config="$2"

    echo "Creating configuration for $image_dir..."

    if ! blur-suite config create "$image_dir" --output "$output_config"; then
        echo "❌ Failed to create configuration"
        return 1
    fi

    echo "✅ Configuration created: $output_config"
    return 0
}

# Main processing workflow
main() {
    echo "Starting Blur Suite automation..."

    # Validate setup
    if ! validate_setup; then
        exit 1
    fi

    # Create configuration if it doesn't exist
    if [[ ! -f "dataset_config.json" ]]; then
        if ! create_config "./input_images" "dataset_config.json"; then
            exit 1
        fi
    fi

    # Process sample images
    echo "Processing sample images..."

    if process_with_cli "sample1.jpg" "blurred1.png" "gaussian" "--kernel-size" "5" "--sigma-x" "1.0"; then
        echo "✅ Processed sample1.jpg"
    else
        echo "❌ Failed to process sample1.jpg"
        exit 1
    fi

    if process_with_cli "sample2.jpg" "blurred2.png" "motion" "--angle" "45" "--length" "15"; then
        echo "✅ Processed sample2.jpg"
    else
        echo "❌ Failed to process sample2.jpg"
        exit 1
    fi

    echo "🎉 Automation completed successfully!"
}

# Run main function
main "$@"
```

### Batch Processing Scripts

```python
#!/usr/bin/env python3
"""
Batch processing script using CLI module
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

class BatchProcessor:
    """Batch processor using CLI module."""

    def __init__(self, cli_path: str = "blur-suite"):
        """Initialize batch processor.

        Args:
            cli_path: Path to blur-suite executable
        """
        self.cli_path = cli_path

    def run_cli_command(self, args: List[str]) -> Tuple[str, str, int]:
        """Run CLI command.

        Args:
            args: Command arguments

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        try:
            result = subprocess.run(
                [self.cli_path] + args,
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), 1

    def process_directory(self, input_dir: str, output_dir: str, config: Dict) -> bool:
        """Process directory of images.

        Args:
            input_dir: Input directory
            output_dir: Output directory
            config: Processing configuration

        Returns:
            True if successful
        """
        # Find all images
        image_paths = []
        for ext in ['*.jpg', '*.png', '*.jpeg', '*.tiff']:
            image_paths.extend(Path(input_dir).rglob(ext))

        if not image_paths:
            print(f"No images found in {input_dir}")
            return False

        print(f"Found {len(image_paths)} images to process")

        # Create temporary configuration
        config_path = self._create_temp_config(config, image_paths)

        try:
            # Run batch processing
            stdout, stderr, return_code = self.run_cli_command([
                "process", "batch",
                input_dir, output_dir,
                "--config", config_path,
                "--workers", str(config.get("workers", 4)),
                "--verbose"
            ])

            if return_code == 0:
                print("✅ Batch processing completed")
                print(stdout)
                return True
            else:
                print("❌ Batch processing failed")
                print(stderr)
                return False

        finally:
            # Clean up temporary config
            if config_path and os.path.exists(config_path):
                os.remove(config_path)

    def _create_temp_config(self, config: Dict, image_paths: List[Path]) -> str:
        """Create temporary configuration file."""
        # Create image configurations
        image_configs = {}
        for image_path in image_paths:
            image_configs[str(image_path)] = config.get("image_config", {
                "blur_type": "gaussian",
                "parameters": {"kernel_size": 5, "sigma_x": 1.0},
                "enabled": True
            })

        # Create full configuration
        full_config = {
            "metadata": {
                "created_by": "Batch Processor CLI",
                "creation_date": "2024-10-07T12:00:00Z",
                "version": "1.0.0"
            },
            "global_settings": config.get("global_settings", {
                "parallel_processing": True,
                "max_workers": 4
            }),
            "image_configurations": image_configs
        }

        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(full_config, f, indent=2)
            return f.name

# Usage example
if __name__ == "__main__":
    processor = BatchProcessor()

    config = {
        "global_settings": {
            "parallel_processing": True,
            "max_workers": 8
        },
        "image_config": {
            "blur_type": "motion",
            "parameters": {"angle": 30.0, "length": 20},
            "enabled": True
        }
    }

    success = processor.process_directory(
        "./input_images",
        "./output_dataset",
        config
    )

    if success:
        print("🎉 Batch processing completed successfully!")
    else:
        print("❌ Batch processing failed!")
        exit(1)
```

## Best Practices

### Command Organization

1. **Use descriptive command names** and options
2. **Provide comprehensive help text** for all commands
3. **Group related options** logically
4. **Use consistent naming conventions**

### Error Handling

1. **Validate inputs** before processing
2. **Provide clear error messages** with actionable information
3. **Include debug information** when requested
4. **Handle edge cases** gracefully

### Performance Optimization

1. **Use appropriate worker counts** for batch operations
2. **Provide progress feedback** for long-running operations
3. **Optimize output formatting** for different use cases
4. **Support different output formats** (text, JSON, etc.)

## API Compatibility

### Version Compatibility

The CLI API maintains backward compatibility:

- **Minor versions**: New commands and options added
- **Patch versions**: Bug fixes and improvements
- **Major versions**: Breaking changes may be introduced

### Deprecation Policy

Commands and options are deprecated before removal:

```python
def _add_deprecated_option(self, parser):
    """Add deprecated option with warning."""
    parser.add_argument(
        "--old-option",
        help="Deprecated: Use --new-option instead"
    )

    # Issue deprecation warning if used
    if hasattr(parser.parse_args(), 'old_option'):
        warnings.warn(
            "--old-option is deprecated, use --new-option instead",
            DeprecationWarning,
            stacklevel=2
        )
```

## Support and Resources

- 📚 **[User Guide: CLI Usage](../user_guide/cli_usage.md)** - Complete usage guide
- 💡 **[Examples: Integration](../examples/integration_example.py)** - Integration patterns
- 🛠️ **[Troubleshooting Guide](../troubleshooting.md)** - Common issues and solutions

---

*Need help?* Check the [Troubleshooting Guide](../troubleshooting.md) or explore the [Examples](../examples/) for more advanced usage patterns.