"""
Dataset exporter for generating configuration files.

This module provides functionality to export blur configurations and
image processing settings for use in dataset generation pipelines.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DatasetExporter:
    """
    Exporter for generating dataset configuration files.

    Creates comprehensive configuration files that can be used
    to reproduce blur effects in dataset generation pipelines.
    """

    def __init__(self):
        """Initialize dataset exporter."""
        self.supported_formats = ["json", "yaml", "csv"]
        self.export_version = "1.0.0"

    def export_configuration(
        self, filename: str, data: Dict[str, Any], format_type: str = "json"
    ) -> bool:
        """
        Export configuration data to file.

        Args:
            filename: Output filename
            data: Configuration data to export
            format_type: Export format (json, yaml, csv)

        Returns:
            True if successful, False otherwise
        """
        try:
            if format_type == "json":
                return self._export_json(filename, data)
            elif format_type == "yaml":
                return self._export_yaml(filename, data)
            elif format_type == "csv":
                return self._export_csv(filename, data)
            else:
                raise ValueError(f"Unsupported format: {format_type}")

        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return False

    def _export_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """Export data as JSON."""
        try:
            # Ensure directory exists
            Path(filename).parent.mkdir(parents=True, exist_ok=True)

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration exported to {filename}")
            return True

        except Exception as e:
            logger.error(f"JSON export failed: {str(e)}")
            return False

    def _export_yaml(self, filename: str, data: Dict[str, Any]) -> bool:
        """Export data as YAML."""
        try:
            import yaml

            # Ensure directory exists
            Path(filename).parent.mkdir(parents=True, exist_ok=True)

            with open(filename, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"Configuration exported to {filename}")
            return True

        except ImportError:
            logger.error("PyYAML not available for YAML export")
            return False
        except Exception as e:
            logger.error(f"YAML export failed: {str(e)}")
            return False

    def _export_csv(self, filename: str, data: Dict[str, Any]) -> bool:
        """Export data as CSV."""
        try:
            import csv

            # Ensure directory exists
            Path(filename).parent.mkdir(parents=True, exist_ok=True)

            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow(["Image", "Blur_Type", "Parameters", "Enabled"])

                # Write data
                for image_path, config in data.get("image_configurations", {}).items():
                    params_str = json.dumps(config.get("parameters", {}))
                    writer.writerow(
                        [
                            image_path,
                            config.get("blur_type", ""),
                            params_str,
                            config.get("enabled", True),
                        ]
                    )

            logger.info(f"Configuration exported to {filename}")
            return True

        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")
            return False

    def create_dataset_config(
        self,
        image_configurations: Dict[str, Dict[str, Any]],
        global_settings: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a complete dataset configuration.

        Args:
            image_configurations: Per-image blur configurations
            global_settings: Global settings for the dataset
            metadata: Additional metadata

        Returns:
            Complete configuration dictionary
        """
        # Default global settings
        if global_settings is None:
            global_settings = {
                "output_format": "png",
                "quality": 95,
                "preserve_metadata": True,
                "parallel_processing": True,
                "max_workers": 4,
            }

        # Default metadata
        if metadata is None:
            metadata = {
                "created_by": "Blur Suite Interactive Tool",
                "creation_date": datetime.now().isoformat(),
                "version": self.export_version,
            }

        # Create complete configuration
        config = {
            "metadata": metadata,
            "global_settings": global_settings,
            "image_configurations": image_configurations,
            "statistics": self._calculate_statistics(image_configurations),
        }

        return config

    def _calculate_statistics(
        self, configurations: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate statistics about the configurations."""
        stats = {
            "total_images": len(configurations),
            "enabled_images": 0,
            "blur_types": {},
            "parameter_ranges": {},
        }

        for config in configurations.values():
            if config.get("enabled", True):
                stats["enabled_images"] += 1

            # Count blur types
            blur_type = config.get("blur_type", "unknown")
            stats["blur_types"][blur_type] = stats["blur_types"].get(blur_type, 0) + 1

            # Analyze parameters
            parameters = config.get("parameters", {})
            for param_name, param_value in parameters.items():
                if param_name not in stats["parameter_ranges"]:
                    stats["parameter_ranges"][param_name] = {
                        "min": param_value,
                        "max": param_value,
                        "values": [param_value],
                    }
                else:
                    param_range = stats["parameter_ranges"][param_name]
                    param_range["min"] = min(param_range["min"], param_value)
                    param_range["max"] = max(param_range["max"], param_value)
                    param_range["values"].append(param_value)

        return stats

    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration for potential issues.

        Args:
            config: Configuration to validate

        Returns:
            List of validation warnings/errors
        """
        issues = []

        # Check required sections
        required_sections = ["metadata", "image_configurations"]
        for section in required_sections:
            if section not in config:
                issues.append(f"Missing required section: {section}")

        # Validate image configurations
        image_configs = config.get("image_configurations", {})
        if not image_configs:
            issues.append("No image configurations found")
        else:
            for image_path, img_config in image_configs.items():
                # Check required fields
                if "blur_type" not in img_config:
                    issues.append(f"Missing blur_type for {image_path}")

                if "parameters" not in img_config:
                    issues.append(f"Missing parameters for {image_path}")

                # Validate blur type
                blur_type = img_config.get("blur_type")
                if blur_type and not self._is_valid_blur_type(blur_type):
                    issues.append(f"Invalid blur_type '{blur_type}' for {image_path}")

        return issues

    def _is_valid_blur_type(self, blur_type: str) -> bool:
        """Check if blur type is valid."""
        valid_types = ["gaussian", "motion", "defocus", "average", "bilateral", "none"]
        return blur_type.lower() in valid_types

    def create_batch_script(
        self, config_file: str, output_dir: str, script_type: str = "python"
    ) -> str:
        """
        Create a batch processing script.

        Args:
            config_file: Path to configuration file
            output_dir: Output directory
            script_type: Type of script to generate

        Returns:
            Generated script content
        """
        if script_type == "python":
            return self._create_python_script(config_file, output_dir)
        elif script_type == "bash":
            return self._create_bash_script(config_file, output_dir)
        else:
            raise ValueError(f"Unsupported script type: {script_type}")

    def _create_python_script(self, config_file: str, output_dir: str) -> str:
        """Create Python batch processing script."""
        script = f'''#!/usr/bin/env python3
"""
Batch blur processing script generated by Blur Suite Interactive Tool.

This script applies blur effects to images according to the configuration
specified in {config_file}.
"""

import json
import sys
from pathlib import Path

# Add blur_suite to path if needed
try:
    from blur_suite.core.blur import BlurFactory
except ImportError:
    print("Error: Blur Suite not found. Please ensure it's installed.")
    sys.exit(1)

def main():
    config_file = "{config_file}"
    output_dir = "{output_dir}"

    # Load configuration
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading configuration: {{e}}")
        return False

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize blur factory
    factory = BlurFactory()

    # Process images
    image_configs = config.get("image_configurations", {{}})

    for image_path, img_config in image_configs.items():
        if not img_config.get("enabled", True):
            continue

        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print(f"Warning: Could not load {{image_path}}")
                continue

            # Create blur effect
            blur_type = img_config.get("blur_type")
            parameters = img_config.get("parameters", {{}})

            blur_effect = factory.create_effect(blur_type, **parameters)

            # Apply blur
            result = blur_effect.apply(image)

            # Save result
            input_name = Path(image_path).name
            output_file = output_path / f"blurred_{{input_name}}"
            cv2.imwrite(str(output_file), result.result_image)

            print(f"Processed: {{image_path}} -> {{output_file}}")

        except Exception as e:
            print(f"Error processing {{image_path}}: {{e}}")

    print("Batch processing completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
        return script

    def _create_bash_script(self, config_file: str, output_dir: str) -> str:
        """Create Bash batch processing script."""
        script = f'''#!/bin/bash
# Batch blur processing script generated by Blur Suite Interactive Tool

CONFIG_FILE="{config_file}"
OUTPUT_DIR="{output_dir}"

# Check if configuration file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Process images using Python script
python3 "$(dirname "$0")/batch_process.py" "$CONFIG_FILE" "$OUTPUT_DIR"

echo "Batch processing completed!"
'''
        return script

    def export_with_validation(
        self, filename: str, data: Dict[str, Any], format_type: str = "json"
    ) -> bool:
        """
        Export configuration with validation.

        Args:
            filename: Output filename
            data: Configuration data to export
            format_type: Export format

        Returns:
            True if successful, False otherwise
        """
        # Validate configuration
        issues = self.validate_configuration(data)

        if issues:
            print("Configuration validation issues found:")
            for issue in issues:
                print(f"  - {issue}")

            # Ask user if they want to continue
            from tkinter import messagebox

            if not messagebox.askyesno(
                "Validation Issues",
                f"Found {len(issues)} validation issues. Continue with export?",
            ):
                return False

        # Export configuration
        return self.export_configuration(filename, data, format_type)

    def create_report(self, config: Dict[str, Any]) -> str:
        """
        Create a human-readable report of the configuration.

        Args:
            config: Configuration to report on

        Returns:
            Formatted report string
        """
        report = []
        report.append("Blur Suite Dataset Configuration Report")
        report.append("=" * 50)
        report.append("")

        # Metadata
        metadata = config.get("metadata", {})
        report.append("METADATA:")
        report.append(f"  Created by: {metadata.get('created_by', 'Unknown')}")
        report.append(f"  Creation date: {metadata.get('creation_date', 'Unknown')}")
        report.append(f"  Version: {metadata.get('version', 'Unknown')}")
        report.append("")

        # Statistics
        stats = config.get("statistics", {})
        report.append("STATISTICS:")
        report.append(f"  Total images: {stats.get('total_images', 0)}")
        report.append(f"  Enabled images: {stats.get('enabled_images', 0)}")

        blur_types = stats.get("blur_types", {})
        if blur_types:
            report.append("  Blur type distribution:")
            for blur_type, count in blur_types.items():
                report.append(f"    {blur_type}: {count}")

        report.append("")

        # Global settings
        global_settings = config.get("global_settings", {})
        if global_settings:
            report.append("GLOBAL SETTINGS:")
            for key, value in global_settings.items():
                report.append(f"  {key}: {value}")
            report.append("")

        # Sample configurations
        image_configs = config.get("image_configurations", {})
        if image_configs:
            report.append("SAMPLE IMAGE CONFIGURATIONS:")
            count = 0
            for image_path, img_config in image_configs.items():
                if count >= 5:  # Show only first 5
                    break

                report.append(f"  {Path(image_path).name}:")
                report.append(f"    Blur type: {img_config.get('blur_type', 'N/A')}")
                report.append(f"    Parameters: {img_config.get('parameters', {{}})}")
                report.append(f"    Enabled: {img_config.get('enabled', True)}")
                report.append("")
                count += 1

            if len(image_configs) > 5:
                report.append(f"  ... and {len(image_configs) - 5} more images")
                report.append("")

        return "\n".join(report)

    def save_report(self, config: Dict[str, Any], filename: str) -> bool:
        """
        Save configuration report to file.

        Args:
            config: Configuration to report on
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        try:
            report = self.create_report(config)

            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info(f"Report saved to {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")
            return False
