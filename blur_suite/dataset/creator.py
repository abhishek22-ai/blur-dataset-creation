"""
Main dataset creation script for the Blur Suite SDK.

This module provides the primary interface for creating blurred document
image datasets with comprehensive configuration and batch processing capabilities.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .batch import BatchConfig
from .metadata import MetadataCollector
from .output import OutputOrganizer
from .pipeline import ProcessingPipeline
from .utils import ConfigurationManager, PathManager, format_time

logger = logging.getLogger(__name__)


class DatasetCreator:
    """
    Main class that orchestrates the entire dataset creation process.

    Provides a high-level interface for loading configurations, processing
    images with various blur effects, and generating organized output datasets.
    """

    def __init__(self, output_directory: Optional[Union[str, Path]] = None):
        """
        Initialize dataset creator.

        Args:
            output_directory: Base directory for dataset output
        """
        self.output_directory = (
            Path(output_directory) if output_directory else Path("./dataset_output")
        )
        self.output_organizer = OutputOrganizer(self.output_directory)
        self.batch_config = BatchConfig()
        self.pipeline = ProcessingPipeline(self.output_organizer, self.batch_config)
        self.metadata_collector = MetadataCollector()

        # Configuration
        self.config = {}
        self.image_paths = []
        self.blur_configs = {}

    def load_configuration(self, config_path: Union[str, Path]) -> bool:
        """
        Load dataset configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            True if successful, False otherwise
        """
        config = ConfigurationManager.load_config(config_path)
        if config is None:
            return False

        # Validate configuration structure
        is_valid, errors = ConfigurationManager.validate_config_structure(config)
        if not is_valid:
            logger.error(f"Invalid configuration: {errors}")
            return False

        self.config = config

        # Extract image paths and blur configurations
        self.image_paths = []
        self.blur_configs = {}

        image_configurations = config.get("image_configurations", {})

        for image_path_str, img_config in image_configurations.items():
            image_path = Path(image_path_str)

            # Check if image exists
            if not image_path.exists():
                logger.warning(f"Image not found, will be skipped: {image_path}")
                continue

            self.image_paths.append(image_path)
            self.blur_configs[image_path.name] = img_config

        logger.info(f"Loaded configuration for {len(self.image_paths)} images")
        return True

    def create_from_config(
        self,
        config_path: Union[str, Path],
        progress_callback: Optional[callable] = None,
    ) -> bool:
        """
        Create dataset from configuration file.

        Args:
            config_path: Path to configuration file
            progress_callback: Optional progress callback function

        Returns:
            True if successful, False otherwise
        """
        # Load configuration
        if not self.load_configuration(config_path):
            return False

        # Create dataset
        return self.create_dataset(progress_callback)

    def create_dataset(self, progress_callback: Optional[callable] = None) -> bool:
        """
        Create dataset with current configuration.

        Args:
            progress_callback: Optional progress callback function

        Returns:
            True if successful, False otherwise
        """
        if not self.image_paths:
            logger.error("No images to process. Load configuration first.")
            return False

        start_time = time.time()
        self.metadata_collector.start_collection()

        try:
            # Initialize output organization
            if not self.output_organizer.initialize():
                logger.error("Failed to initialize output organization")
                return False

            # Validate configuration
            validation_issues = self.pipeline.validate_dataset_configuration(
                self.image_paths, self.blur_configs
            )

            if validation_issues:
                logger.warning("Configuration validation issues found:")
                for issue in validation_issues:
                    logger.warning(f"  - {issue}")

                # Ask user if they want to continue (in interactive mode)
                # For now, we'll continue with warnings
                logger.info("Continuing with warnings...")

            # Register image pairs in output organizer
            for image_path in self.image_paths:
                image_name = Path(image_path).name
                if image_name in self.blur_configs:
                    config = self.blur_configs[image_name]
                    self.output_organizer.register_image_pair(
                        image_path, config["blur_type"], config["parameters"]
                    )

            # Get processing requirements estimate
            requirements = self.pipeline.estimate_processing_requirements(
                self.image_paths, self.blur_configs
            )

            logger.info("Processing requirements estimate:")
            logger.info(f"  Total images: {requirements['total_images']}")
            logger.info(f"  Estimated time: {requirements['estimated_time']}")
            logger.info(
                f"  Estimated memory: {requirements['estimated_memory_gb']:.1f}GB"
            )

            # Process dataset
            if self.batch_config.max_workers > 1:
                # Use batch processing for parallelization
                logger.info("Using parallel batch processing")
                results = self.pipeline.process_with_batch_processor(
                    self.image_paths, self.blur_configs, progress_callback
                )
            else:
                # Use sequential processing
                logger.info("Using sequential processing")
                results = self.pipeline.process_dataset(
                    self.image_paths, self.blur_configs, progress_callback
                )

            # Save metadata and reports
            self._save_dataset_metadata()

            # Log results
            total_time = time.time() - start_time
            success_rate = results.get("success_rate", 0)

            logger.info("Dataset creation completed:")
            logger.info(f"  Total time: {format_time(total_time)}")
            logger.info(f"  Success rate: {success_rate:.1%}")
            logger.info(f"  Output directory: {self.output_directory}")

            return True

        except Exception as e:
            logger.error(f"Dataset creation failed: {str(e)}")
            return False

        finally:
            self.metadata_collector.stop_collection()

    def _save_dataset_metadata(self):
        """Save dataset metadata and reports."""
        try:
            # Save metadata
            metadata_path = (
                self.output_organizer.output_dir.get_metadata_path()
                / "processing_metadata.json"
            )
            self.metadata_collector.save_metadata(metadata_path)

            # Save human-readable report
            report_path = (
                self.output_organizer.output_dir.get_metadata_path()
                / "dataset_report.txt"
            )
            self.metadata_collector.save_report(report_path)

            # Save dataset manifest
            self.output_organizer.save_dataset_manifest()

            # Save configuration copy for reference
            config_copy_path = (
                self.output_organizer.output_dir.get_metadata_path()
                / "dataset_config.json"
            )
            ConfigurationManager.save_config(self.config, config_copy_path)

        except Exception as e:
            logger.error(f"Failed to save dataset metadata: {str(e)}")

    def create_sample_configuration(
        self, image_directory: Union[str, Path], output_path: Union[str, Path]
    ) -> bool:
        """
        Create a sample configuration file from images in a directory.

        Args:
            image_directory: Directory containing images
            output_path: Path for output configuration file

        Returns:
            True if successful, False otherwise
        """
        image_dir = Path(image_directory)

        if not image_dir.exists():
            logger.error(f"Image directory not found: {image_dir}")
            return False

        # Find all images
        image_paths = PathManager.find_images(image_dir)
        if not image_paths:
            logger.error(f"No images found in {image_dir}")
            return False

        # Create sample configuration
        image_configurations = {}
        global_settings = {
            "output_format": "png",
            "quality": 95,
            "preserve_metadata": True,
            "parallel_processing": True,
            "max_workers": self.batch_config.max_workers,
        }

        for image_path in image_paths:
            image_configurations[str(image_path)] = {
                "blur_type": "gaussian",
                "parameters": {
                    "kernel_size": 5,
                    "sigma_x": 1.0,
                    "sigma_y": 1.0,
                },
                "enabled": True,
            }

        config = {
            "metadata": {
                "created_by": "Blur Suite Dataset Creator",
                "creation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0.0",
                "description": "Sample configuration created from image directory",
            },
            "global_settings": global_settings,
            "image_configurations": image_configurations,
        }

        # Save configuration
        return ConfigurationManager.save_config(config, output_path)

    def validate_setup(self) -> List[str]:
        """
        Validate the current setup and configuration.

        Returns:
            List of validation issues
        """
        issues = []

        # Check output directory
        if not PathManager.ensure_directory(self.output_directory):
            issues.append(f"Cannot create output directory: {self.output_directory}")

        # Check blur factory
        try:
            available_effects = self.pipeline.blur_factory.list_available_effects()
            if not available_effects:
                issues.append("No blur effects available")
        except Exception as e:
            issues.append(f"Blur factory error: {str(e)}")

        # Check batch processor configuration
        batch_issues = self.batch_processor.validate_batch_config()
        issues.extend(batch_issues)

        # Check for images if configuration is loaded
        if not self.image_paths:
            issues.append("No images configured for processing")

        return issues

    def get_dataset_info(self) -> Dict[str, Any]:
        """
        Get information about the current dataset configuration.

        Returns:
            Dictionary with dataset information
        """
        return {
            "output_directory": str(self.output_directory),
            "image_count": len(self.image_paths),
            "blur_configs_count": len(self.blur_configs),
            "batch_config": {
                "max_workers": self.batch_config.max_workers,
                "use_multiprocessing": self.batch_config.use_multiprocessing,
                "chunk_size": self.batch_config.chunk_size,
            },
            "available_blur_types": [
                info["name"]
                for info in self.pipeline.blur_factory.list_available_effects()
            ],
            "output_organizer_info": self.output_organizer.get_dataset_info(),
        }

    def cleanup(self) -> bool:
        """
        Clean up temporary files and reset state.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Clean up failed outputs
            cleaned_count = self.output_organizer.cleanup_failed_outputs()

            # Reset state
            self.image_paths.clear()
            self.blur_configs.clear()
            self.config.clear()

            logger.info(f"Cleanup completed, removed {cleaned_count} files")
            return True

        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return False

    def export_processing_script(
        self,
        script_path: Union[str, Path],
        config_path: Optional[Union[str, Path]] = None,
    ) -> bool:
        """
        Export a standalone processing script.

        Args:
            script_path: Path for the exported script
            config_path: Path to configuration file (uses current if not provided)

        Returns:
            True if successful, False otherwise
        """
        try:
            script_content = self._generate_processing_script(config_path)
            script_path = Path(script_path)

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Make script executable on Unix systems
            if script_path.suffix in [".py", ".sh"]:
                script_path.chmod(0o755)

            logger.info(f"Processing script exported to {script_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export processing script: {str(e)}")
            return False

    def _generate_processing_script(
        self, config_path: Optional[Union[str, Path]] = None
    ) -> str:
        """Generate standalone processing script content."""
        if config_path is None:
            # Use the current configuration
            config_path = (
                self.output_organizer.output_dir.get_metadata_path()
                / "dataset_config.json"
            )

        script = '''#!/usr/bin/env python3
"""
Standalone dataset creation script generated by Blur Suite SDK.

This script can be run independently to recreate the dataset.
"""

import sys
import logging
from pathlib import Path

# Add blur_suite to path if needed
try:
    from blur_suite.dataset.creator import DatasetCreator
except ImportError:
    print("Error: Blur Suite not found. Please ensure it's installed.")
    sys.exit(1)

def main():
    """Main processing function."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Configuration file
    config_file = "{config_path}"

    if not Path(config_file).exists():
        print(f"Configuration file not found: {config_file}")
        return False

    # Create dataset
    creator = DatasetCreator()

    def progress_callback(current, total):
        percentage = (current / total) * 100
        print(f"Progress: {current}/{total} ({percentage".1f"}%)")

    success = creator.create_from_config(config_file, progress_callback)

    if success:
        print("Dataset creation completed successfully!")
        return True
    else:
        print("Dataset creation failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
        return script.format(config_path=config_path)

    def get_batch_processor(self):
        """Get the batch processor instance."""
        return self.pipeline.batch_processor

    def get_metadata_collector(self) -> MetadataCollector:
        """Get the metadata collector instance."""
        return self.metadata_collector

    def get_output_organizer(self) -> OutputOrganizer:
        """Get the output organizer instance."""
        return self.output_organizer
