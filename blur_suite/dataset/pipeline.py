"""
Processing pipeline orchestration for dataset creation.

This module provides the main processing pipeline that coordinates
image loading, blur application, validation, and output generation.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from ..core.blur.factory import get_blur_factory
from .batch import BatchConfig, BatchProcessor
from .metadata import MetadataCollector
from .output import OutputOrganizer
from .utils import ImageValidator, format_time

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """
    Coordinates the blur application workflow.

    Manages the complete pipeline from image loading through blur
    application to output generation with error handling and validation.
    """

    def __init__(
        self,
        output_organizer: OutputOrganizer,
        batch_config: Optional[BatchConfig] = None,
    ):
        """
        Initialize processing pipeline.

        Args:
            output_organizer: Output organizer for file management
            batch_config: Configuration for batch processing
        """
        self.output_organizer = output_organizer
        self.batch_processor = BatchProcessor(batch_config)
        self.blur_factory = get_blur_factory()
        self.metadata_collector = MetadataCollector()

    def process_image(
        self,
        image_path: Union[str, Path],
        blur_type: str,
        parameters: Dict[str, Any],
        validate_output: bool = True,
    ) -> Tuple[bool, Optional[str], Optional[np.ndarray], float]:
        """
        Process a single image through the pipeline.

        Args:
            image_path: Path to input image
            blur_type: Type of blur to apply
            parameters: Blur parameters
            validate_output: Whether to validate output quality

        Returns:
            Tuple of (success, output_path, result_image, processing_time_ms)
        """
        start_time = time.time()
        image_path = Path(image_path)

        try:
            # Load and validate image
            image = ImageValidator.load_image(image_path)
            if image is None:
                return False, None, None, (time.time() - start_time) * 1000

            # Validate image format
            is_valid, error_msg = ImageValidator.validate_image(image)
            if not is_valid:
                logger.error(f"Invalid image {image_path}: {error_msg}")
                return False, None, None, (time.time() - start_time) * 1000

            # Create blur effect
            try:
                blur_effect = self.blur_factory.create_effect(blur_type, **parameters)
            except Exception as e:
                logger.error(f"Failed to create blur effect {blur_type}: {str(e)}")
                return False, None, None, (time.time() - start_time) * 1000

            # Apply blur
            try:
                result = blur_effect.apply(image)
                blurred_image = result.result_image

                # Validate output
                if validate_output:
                    is_valid, error_msg = ImageValidator.validate_image(blurred_image)
                    if not is_valid:
                        logger.error(f"Invalid output image: {error_msg}")
                        return False, None, None, (time.time() - start_time) * 1000

                # Generate output filename
                filename = self.output_organizer.naming.generate_filename(
                    image_path, blur_type, parameters
                )

                # Save result
                output_path = self.output_organizer.save_blurred_result(
                    blurred_image, filename
                )

                if output_path is None:
                    logger.error(f"Failed to save blurred image: {filename}")
                    return False, None, None, (time.time() - start_time) * 1000

                return (
                    True,
                    str(output_path),
                    blurred_image,
                    (time.time() - start_time) * 1000,
                )

            except Exception as e:
                logger.error(f"Failed to apply blur to {image_path}: {str(e)}")
                return False, None, None, (time.time() - start_time) * 1000

        except Exception as e:
            logger.error(f"Pipeline error for {image_path}: {str(e)}")
            return False, None, None, (time.time() - start_time) * 1000

    def process_dataset(
        self,
        image_paths: List[Union[str, Path]],
        blur_configs: Dict[str, Dict[str, Any]],
        progress_callback: Optional[callable] = None,
        validate_outputs: bool = True,
    ) -> Dict[str, Any]:
        """
        Process entire dataset with multiple blur configurations.

        Args:
            image_paths: List of image paths to process
            blur_configs: Dictionary mapping image names to blur configurations
            progress_callback: Optional progress callback function
            validate_outputs: Whether to validate output quality

        Returns:
            Dictionary with processing results and statistics
        """
        start_time = time.time()
        self.metadata_collector.start_collection()

        total_images = len(image_paths)
        processed_count = 0
        failed_count = 0
        results = []

        logger.info(f"Starting dataset processing: {total_images} images")

        try:
            for i, image_path in enumerate(image_paths):
                image_name = Path(image_path).name

                # Get blur configuration for this image
                image_config = blur_configs.get(image_name, {})

                if not image_config:
                    logger.warning(f"No configuration found for {image_name}")
                    failed_count += 1
                    continue

                blur_type = image_config.get("blur_type", "none")
                parameters = image_config.get("parameters", {})

                # Process image
                success, output_path, result_image, processing_time = (
                    self.process_image(
                        image_path, blur_type, parameters, validate_outputs
                    )
                )

                # Record result
                result = {
                    "image_path": str(image_path),
                    "success": success,
                    "output_path": output_path,
                    "blur_type": blur_type,
                    "parameters": parameters,
                    "processing_time_ms": processing_time,
                }

                if success:
                    processed_count += 1
                else:
                    failed_count += 1
                    result["error"] = f"Processing failed for {image_name}"

                results.append(result)

                # Record in metadata collector
                self.metadata_collector.record_processing(
                    image_path=str(image_path),
                    blur_type=blur_type,
                    parameters=parameters,
                    processing_time_ms=processing_time,
                    original_size=(0, 0),  # Would need to load image to get actual size
                    result_size=(0, 0),  # Would need result_image to get actual size
                    success=success,
                    error_message=result.get("error"),
                )

                # Update progress
                if progress_callback:
                    progress_callback(i + 1, total_images)

        except Exception as e:
            logger.error(f"Dataset processing failed: {str(e)}")
            failed_count += total_images - processed_count

        finally:
            self.metadata_collector.stop_collection()
            total_time = time.time() - start_time

        # Generate summary
        summary = {
            "total_images": total_images,
            "processed_images": processed_count,
            "failed_images": failed_count,
            "success_rate": processed_count / total_images if total_images > 0 else 0.0,
            "total_time_seconds": total_time,
            "avg_time_per_image": total_time / total_images
            if total_images > 0
            else 0.0,
            "results": results,
            "metadata": self.metadata_collector.get_processing_summary(),
        }

        logger.info(
            f"Dataset processing completed: {processed_count}/{total_images} successful "
            f"in {format_time(total_time)}"
        )

        return summary

    def validate_blur_effect(
        self, blur_type: str, parameters: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate blur effect configuration.

        Args:
            blur_type: Type of blur to validate
            parameters: Blur parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to create the blur effect
            self.blur_factory.create_effect(blur_type, **parameters)

            # Try to get effect info for validation
            effect_info = self.blur_factory.get_effect_info(blur_type)

            if not effect_info:
                return False, f"Unknown blur type: {blur_type}"

            # Validate parameters are within acceptable ranges
            validation_results = self.blur_factory.validate_parameters(
                blur_type, **parameters
            )

            invalid_params = [
                name
                for name, result in validation_results.items()
                if not result["valid"]
            ]

            if invalid_params:
                return (
                    False,
                    f"Invalid parameters for {invalid_params}: {validation_results}",
                )

            return True, ""

        except Exception as e:
            return False, f"Blur effect validation failed: {str(e)}"

    def estimate_processing_requirements(
        self,
        image_paths: List[Union[str, Path]],
        blur_configs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Estimate processing time and resource requirements.

        Args:
            image_paths: List of image paths
            blur_configs: Blur configurations

        Returns:
            Dictionary with requirement estimates
        """
        total_images = len(image_paths)

        # Estimate average image size (assume 2MB per image)
        avg_image_size_mb = 2.0

        # Estimate processing time per image (in seconds)
        # This is a rough estimate based on typical blur operations
        avg_processing_time_per_image = 0.5

        # Get batch processor estimates
        batch_estimate = self.batch_processor.estimate_processing_time(
            total_images, avg_processing_time_per_image
        )

        memory_estimate = self.batch_processor.get_memory_usage_estimate(
            total_images, avg_image_size_mb
        )

        return {
            "total_images": total_images,
            "estimated_time": batch_estimate,
            "estimated_memory_gb": memory_estimate,
            "avg_image_size_mb": avg_image_size_mb,
            "avg_processing_time_per_image": avg_processing_time_per_image,
            "batch_config": {
                "max_workers": self.batch_processor.config.max_workers,
                "chunk_size": self.batch_processor.config.chunk_size,
            },
        }

    def create_blur_function(self):
        """
        Create a blur function for use with batch processing.

        Returns:
            Function that can be used with BatchProcessor
        """

        def blur_function(
            image_path: str, blur_type: str, parameters: Dict[str, Any]
        ) -> Tuple[bool, str, Optional[np.ndarray], float]:
            """
            Apply blur to a single image.

            Args:
                image_path: Path to input image
                blur_type: Type of blur to apply
                parameters: Blur parameters

            Returns:
                Tuple of (success, result_path, result_image, processing_time_ms)
            """
            success, output_path, result_image, processing_time = self.process_image(
                image_path, blur_type, parameters
            )

            return success, output_path or "", result_image, processing_time

        return blur_function

    def process_with_batch_processor(
        self,
        image_paths: List[Union[str, Path]],
        blur_configs: Dict[str, Dict[str, Any]],
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Process dataset using the batch processor for parallelization.

        Args:
            image_paths: List of image paths to process
            blur_configs: Blur configurations per image
            progress_callback: Optional progress callback

        Returns:
            Dictionary with processing results
        """
        # Create blur function for batch processing
        blur_function = self.create_blur_function()

        # Extract blur configurations for each image
        batch_configs = {}
        for image_path in image_paths:
            image_name = Path(image_path).name
            if image_name in blur_configs:
                batch_configs[image_name] = blur_configs[image_name]

        # Process batch
        batch_result = self.batch_processor.process_batch(
            image_paths, blur_function, "batch", {}, progress_callback
        )

        # Get metadata
        metadata = self.batch_processor.get_metadata_collector()

        return {
            "batch_result": batch_result,
            "metadata": metadata.get_processing_summary(),
            "quality_metrics": metadata.get_quality_metrics().to_dict(),
        }

    def validate_dataset_configuration(
        self,
        image_paths: List[Union[str, Path]],
        blur_configs: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """
        Validate dataset configuration for potential issues.

        Args:
            image_paths: List of image paths
            blur_configs: Blur configurations

        Returns:
            List of validation issues
        """
        issues = []

        # Check if all images have configurations
        configured_images = set(blur_configs.keys())
        all_images = {Path(p).name for p in image_paths}

        missing_configs = all_images - configured_images
        if missing_configs:
            issues.append(
                f"Missing configurations for images: {sorted(missing_configs)}"
            )

        # Validate blur effect configurations
        for image_name, config in blur_configs.items():
            blur_type = config.get("blur_type")
            parameters = config.get("parameters", {})

            if not blur_type:
                issues.append(f"Missing blur_type for {image_name}")
                continue

            is_valid, error_msg = self.validate_blur_effect(blur_type, parameters)
            if not is_valid:
                issues.append(f"Invalid configuration for {image_name}: {error_msg}")

        # Check for potentially problematic configurations
        for image_name, config in blur_configs.items():
            parameters = config.get("parameters", {})

            # Check for very large kernel sizes
            kernel_size = parameters.get("kernel_size", 0)
            if isinstance(kernel_size, int) and kernel_size > 50:
                issues.append(
                    f"Very large kernel_size ({kernel_size}) for {image_name}"
                )

            # Check for extreme sigma values
            sigma_x = parameters.get("sigma_x", 0)
            if isinstance(sigma_x, (int, float)) and sigma_x > 10:
                issues.append(f"Very large sigma_x ({sigma_x}) for {image_name}")

        return issues

    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about the pipeline configuration.

        Returns:
            Dictionary with pipeline information
        """
        return {
            "blur_factory_available": True,
            "batch_processor_config": {
                "max_workers": self.batch_processor.config.max_workers,
                "use_multiprocessing": self.batch_processor.config.use_multiprocessing,
                "chunk_size": self.batch_processor.config.chunk_size,
            },
            "output_organizer_config": {
                "base_directory": self.output_organizer.output_dir.base_path,
                "naming_pattern": self.output_organizer.naming.pattern,
            },
            "available_blur_types": [
                info["blur_type"] for info in self.blur_factory.list_available_effects()
            ],
        }
