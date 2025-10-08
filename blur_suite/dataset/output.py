"""
Output organization and file management for dataset creation.

This module provides functionality for organizing output files, managing
directory structures, and generating consistent file naming conventions
for blurred image datasets.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from .utils import ImageValidator, PathManager, format_bytes

logger = logging.getLogger(__name__)


class NamingPattern:
    """Handles filename pattern generation for dataset files."""

    def __init__(
        self, pattern: str = "{original}_{blur_type}_k{kernel_size}_s{sigma}.png"
    ):
        """
        Initialize naming pattern.

        Args:
            pattern: Pattern template for filenames
        """
        self.pattern = pattern

    def generate_filename(
        self,
        original_path: Union[str, Path],
        blur_type: str,
        parameters: Dict[str, Union[int, float, str]],
        extension: Optional[str] = None,
    ) -> str:
        """
        Generate filename based on pattern.

        Args:
            original_path: Original image path
            blur_type: Type of blur applied
            parameters: Blur parameters used
            extension: File extension (defaults to original)

        Returns:
            Generated filename
        """
        # Get original filename without extension
        original_name = Path(original_path).stem

        # Determine file extension
        if extension is None:
            extension = Path(original_path).suffix or ".png"
        extension = extension.lstrip(".")

        # Prepare pattern variables
        pattern_vars = {
            "original": original_name,
            "blur_type": blur_type.lower(),
            "extension": extension,
        }

        # Add parameter values to pattern variables
        for param_name, param_value in parameters.items():
            if isinstance(param_value, float):
                pattern_vars[param_name] = f"{param_value:.2f}"
            else:
                pattern_vars[param_name] = str(param_value)

        # Generate filename
        try:
            filename = self.pattern.format(**pattern_vars)
            return f"{filename}.{extension}"
        except KeyError as e:
            logger.warning(f"Missing pattern variable: {e}")
            # Fallback to simple naming
            return f"{original_name}_{blur_type}.{extension}"


class OutputDirectory:
    """Manages output directory structure and organization."""

    def __init__(self, base_path: Union[str, Path]):
        """
        Initialize output directory manager.

        Args:
            base_path: Base directory for output
        """
        self.base_path = Path(base_path)
        self.clear_path = self.base_path / "clear"
        self.blurred_path = self.base_path / "blurred"
        self.metadata_path = self.base_path / "metadata"

    def setup_directories(self) -> bool:
        """
        Create and setup output directory structure.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create main directories
            PathManager.ensure_directory(self.clear_path)
            PathManager.ensure_directory(self.blurred_path)
            PathManager.ensure_directory(self.metadata_path)

            logger.info(f"Output directories created at {self.base_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to setup output directories: {str(e)}")
            return False

    def get_clear_path(self) -> Path:
        """Get path for clear (original) images."""
        return self.clear_path

    def get_blurred_path(self) -> Path:
        """Get path for blurred images."""
        return self.blurred_path

    def get_metadata_path(self) -> Path:
        """Get path for metadata files."""
        return self.metadata_path

    def copy_clear_image(
        self, source_path: Union[str, Path], target_name: Optional[str] = None
    ) -> Optional[Path]:
        """
        Copy clear image to output directory.

        Args:
            source_path: Source image path
            target_name: Target filename (defaults to original)

        Returns:
            Path to copied file or None if failed
        """
        source = Path(source_path)

        if not source.exists():
            logger.error(f"Source image not found: {source}")
            return None

        if target_name is None:
            target_name = source.name

        target = self.clear_path / target_name

        try:
            shutil.copy2(source, target)
            logger.debug(f"Copied clear image: {source} -> {target}")
            return target

        except Exception as e:
            logger.error(f"Failed to copy clear image: {str(e)}")
            return None

    def save_blurred_image(self, image: np.ndarray, filename: str) -> Optional[Path]:
        """
        Save blurred image to output directory.

        Args:
            image: Blurred image array
            filename: Target filename

        Returns:
            Path to saved file or None if failed
        """
        target = self.blurred_path / filename

        try:
            success = ImageValidator.save_image(image, target)
            if success:
                logger.debug(f"Saved blurred image: {target}")
                return target
            else:
                logger.error(f"Failed to save blurred image: {target}")
                return None

        except Exception as e:
            logger.error(f"Error saving blurred image: {str(e)}")
            return None


class OutputOrganizer:
    """
    Organizes and manages dataset output files and directories.

    Provides comprehensive functionality for creating organized dataset
    structures with consistent naming and metadata management.
    """

    def __init__(
        self, output_directory: Union[str, Path], naming_pattern: Optional[str] = None
    ):
        """
        Initialize output organizer.

        Args:
            output_directory: Base output directory
            naming_pattern: Pattern for generating filenames
        """
        self.output_dir = OutputDirectory(output_directory)
        self.naming = NamingPattern(
            naming_pattern or "{original}_{blur_type}_k{kernel_size}_s{sigma}.png"
        )
        self.file_registry: Dict[str, Dict[str, str]] = {}

    def initialize(self) -> bool:
        """
        Initialize output organization.

        Returns:
            True if successful, False otherwise
        """
        return self.output_dir.setup_directories()

    def register_image_pair(
        self,
        original_path: Union[str, Path],
        blur_type: str,
        parameters: Dict[str, Union[int, float, str]],
        blurred_filename: Optional[str] = None,
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Register a clear/blurred image pair.

        Args:
            original_path: Path to original image
            blur_type: Type of blur applied
            parameters: Blur parameters used
            blurred_filename: Custom blurred filename

        Returns:
            Tuple of (clear_path, blurred_path) or (None, None) if failed
        """
        original_path = Path(original_path)

        # Generate blurred filename if not provided
        if blurred_filename is None:
            blurred_filename = self.naming.generate_filename(
                original_path, blur_type, parameters
            )

        # Copy clear image
        clear_path = self.output_dir.copy_clear_image(original_path)

        # Save blurred image (placeholder - actual saving happens in pipeline)
        blurred_path = self.output_dir.get_blurred_path() / blurred_filename

        # Register in file registry
        self.file_registry[original_path.name] = {
            "original_path": str(original_path),
            "clear_path": str(clear_path) if clear_path else None,
            "blurred_path": str(blurred_path),
            "blur_type": blur_type,
            "parameters": parameters,
        }

        return clear_path, blurred_path

    def save_blurred_result(self, image: np.ndarray, filename: str) -> Optional[Path]:
        """
        Save blurred image result.

        Args:
            image: Blurred image array
            filename: Target filename

        Returns:
            Path to saved file or None if failed
        """
        return self.output_dir.save_blurred_image(image, filename)

    def get_dataset_info(self) -> Dict[str, Union[str, int, float]]:
        """
        Get information about the organized dataset.

        Returns:
            Dictionary with dataset information
        """
        try:
            clear_files = list(self.output_dir.get_clear_path().glob("*"))
            blurred_files = list(self.output_dir.get_blurred_path().glob("*"))

            # Calculate total sizes
            clear_size = sum(f.stat().st_size for f in clear_files if f.is_file())
            blurred_size = sum(f.stat().st_size for f in blurred_files if f.is_file())

            return {
                "base_directory": str(self.output_dir.base_path),
                "clear_count": len(clear_files),
                "blurred_count": len(blurred_files),
                "clear_size": format_bytes(clear_size),
                "blurred_size": format_bytes(blurred_size),
                "total_size": format_bytes(clear_size + blurred_size),
                "clear_directory": str(self.output_dir.get_clear_path()),
                "blurred_directory": str(self.output_dir.get_blurred_path()),
                "metadata_directory": str(self.output_dir.get_metadata_path()),
            }

        except Exception as e:
            logger.error(f"Error getting dataset info: {str(e)}")
            return {}

    def create_dataset_manifest(self) -> Dict[str, Dict[str, str]]:
        """
        Create a manifest of all files in the dataset.

        Returns:
            Dictionary mapping filenames to file information
        """
        manifest = {}

        try:
            # Clear images
            for clear_file in self.output_dir.get_clear_path().glob("*"):
                if clear_file.is_file():
                    manifest[clear_file.name] = {
                        "type": "clear",
                        "path": str(clear_file),
                        "size": clear_file.stat().st_size,
                    }

            # Blurred images
            for blurred_file in self.output_dir.get_blurred_path().glob("*"):
                if blurred_file.is_file():
                    manifest[blurred_file.name] = {
                        "type": "blurred",
                        "path": str(blurred_file),
                        "size": blurred_file.stat().st_size,
                    }

            # Metadata files
            for metadata_file in self.output_dir.get_metadata_path().glob("*"):
                if metadata_file.is_file():
                    manifest[metadata_file.name] = {
                        "type": "metadata",
                        "path": str(metadata_file),
                        "size": metadata_file.stat().st_size,
                    }

        except Exception as e:
            logger.error(f"Error creating dataset manifest: {str(e)}")

        return manifest

    def save_dataset_manifest(self, filename: str = "dataset_manifest.json") -> bool:
        """
        Save dataset manifest to file.

        Args:
            filename: Manifest filename

        Returns:
            True if successful, False otherwise
        """
        try:
            manifest = self.create_dataset_manifest()
            manifest_path = self.output_dir.get_metadata_path() / filename

            import json

            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            logger.info(f"Dataset manifest saved to {manifest_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save dataset manifest: {str(e)}")
            return False

    def cleanup_failed_outputs(self) -> int:
        """
        Clean up incomplete or failed output files.

        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0

        try:
            # Remove empty files
            for directory in [
                self.output_dir.get_clear_path(),
                self.output_dir.get_blurred_path(),
            ]:
                for file_path in directory.glob("*"):
                    if file_path.is_file() and file_path.stat().st_size == 0:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"Removed empty file: {file_path}")

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} empty files")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

        return cleaned_count

    def validate_dataset_integrity(self) -> Dict[str, Union[bool, List[str], int]]:
        """
        Validate dataset integrity and completeness.

        Returns:
            Dictionary with validation results
        """
        issues = []
        clear_files = set()
        blurred_files = set()

        try:
            # Collect filenames
            for clear_file in self.output_dir.get_clear_path().glob("*"):
                if clear_file.is_file() and clear_file.suffix.lower() in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                ]:
                    clear_files.add(clear_file.stem)

            for blurred_file in self.output_dir.get_blurred_path().glob("*"):
                if blurred_file.is_file() and blurred_file.suffix.lower() in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                ]:
                    blurred_files.add(blurred_file.stem)

            # Check for missing pairs
            missing_clear = blurred_files - clear_files
            missing_blurred = clear_files - blurred_files

            if missing_clear:
                issues.append(f"Missing clear versions for: {sorted(missing_clear)}")

            if missing_blurred:
                issues.append(
                    f"Missing blurred versions for: {sorted(missing_blurred)}"
                )

            # Check file sizes (non-zero)
            for directory, file_set in [
                ("clear", clear_files),
                ("blurred", blurred_files),
            ]:
                for filename in file_set:
                    file_path = (
                        self.output_dir.get_clear_path()
                        if directory == "clear"
                        else self.output_dir.get_blurred_path()
                    ) / f"{filename}.png"
                    if file_path.exists() and file_path.stat().st_size == 0:
                        issues.append(f"Empty file detected: {file_path}")

            return {
                "is_valid": len(issues) == 0,
                "issues": issues,
                "clear_count": len(clear_files),
                "blurred_count": len(blurred_files),
            }

        except Exception as e:
            logger.error(f"Error validating dataset integrity: {str(e)}")
            return {
                "is_valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "clear_count": 0,
                "blurred_count": 0,
            }

    def get_file_registry(self) -> Dict[str, Dict[str, str]]:
        """
        Get the file registry.

        Returns:
            Dictionary with file registration information
        """
        return self.file_registry.copy()

    def export_file_list(
        self, output_file: Union[str, Path], format_type: str = "txt"
    ) -> bool:
        """
        Export list of files in the dataset.

        Args:
            output_file: Output file path
            format_type: Format type (txt, csv, json)

        Returns:
            True if successful, False otherwise
        """
        try:
            manifest = self.create_dataset_manifest()
            output_path = Path(output_file)

            if format_type == "txt":
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write("Dataset File List\n")
                    f.write("=" * 50 + "\n\n")
                    f.write("CLEAR IMAGES:\n")
                    for filename, info in manifest.items():
                        if info["type"] == "clear":
                            f.write(f"  {filename}\n")

                    f.write("\nBLURRED IMAGES:\n")
                    for filename, info in manifest.items():
                        if info["type"] == "blurred":
                            f.write(f"  {filename}\n")

            elif format_type == "csv":
                import csv

                with open(output_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Filename", "Type", "Size", "Path"])
                    for filename, info in manifest.items():
                        writer.writerow(
                            [filename, info["type"], info["size"], info["path"]]
                        )

            elif format_type == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2, ensure_ascii=False)

            else:
                raise ValueError(f"Unsupported format: {format_type}")

            logger.info(f"File list exported to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export file list: {str(e)}")
            return False
