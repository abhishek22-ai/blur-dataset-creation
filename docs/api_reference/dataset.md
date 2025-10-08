# Dataset API Reference

This document provides comprehensive API documentation for the Blur Suite SDK dataset creation module, including batch processing, pipeline orchestration, and output management.

## Overview

The dataset module provides:
- **Batch processing** with parallel execution
- **Pipeline orchestration** for complex workflows
- **Output organization** and file management
- **Metadata collection** and statistics tracking
- **Flexible configuration** system
- **Progress monitoring** and error handling

## Module Structure

```
blur_suite/dataset/
├── __init__.py           # Module exports
├── creator.py           # Main DatasetCreator class
├── pipeline.py          # Processing pipeline orchestration
├── batch.py            # Batch processing with parallelization
├── output.py           # Output organization and file management
├── metadata.py         # Dataset metadata and statistics
├── utils.py            # Utility functions for dataset operations
└── validation.py       # Configuration and setup validation
```

## Quick Start

```python
from blur_suite.dataset import DatasetCreator

# Create dataset creator
creator = DatasetCreator("./output_dataset")

# Create dataset from configuration file
success = creator.create_from_config("dataset_config.json")

if success:
    print("✅ Dataset created successfully!")
```

## Main Classes

### DatasetCreator

Main orchestrator class for dataset creation.

```python
class DatasetCreator:
    """Main class for creating blurred image datasets."""

    def __init__(self, output_directory: str, batch_config: BatchConfig = None):
        """Initialize dataset creator.

        Args:
            output_directory: Directory for output dataset
            batch_config: Configuration for batch processing
        """
        self.output_directory = Path(output_directory)
        self.batch_config = batch_config or BatchConfig()
        self.pipeline = ProcessingPipeline(self.batch_config)
        self.output_organizer = OutputOrganizer(self.output_directory)
        self.metadata_collector = MetadataCollector()

    def create_from_config(self, config_path: str, progress_callback: Callable = None) -> bool:
        """Create dataset from configuration file.

        Args:
            config_path: Path to configuration file
            progress_callback: Optional callback for progress updates

        Returns:
            True if dataset creation successful
        """
        try:
            # Load configuration
            config = self._load_configuration(config_path)

            # Validate setup
            issues = self.validate_setup()
            if issues:
                print(f"Setup issues: {issues}")
                return False

            # Create dataset
            return self._create_dataset(config, progress_callback)

        except Exception as e:
            print(f"Error creating dataset: {e}")
            return False

    def create_from_config_dict(self, config: Dict, progress_callback: Callable = None) -> bool:
        """Create dataset from configuration dictionary.

        Args:
            config: Configuration dictionary
            progress_callback: Optional callback for progress updates

        Returns:
            True if dataset creation successful
        """
        try:
            # Validate configuration
            issues = self.validate_config_dict(config)
            if issues:
                print(f"Configuration issues: {issues}")
                return False

            return self._create_dataset(config, progress_callback)

        except Exception as e:
            print(f"Error creating dataset: {e}")
            return False

    def validate_setup(self) -> List[str]:
        """Validate current setup before processing.

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check output directory
        if not self.output_directory.exists():
            try:
                self.output_directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create output directory: {e}")

        # Check batch configuration
        if self.batch_config.max_workers < 1:
            issues.append("max_workers must be at least 1")

        # Check pipeline
        pipeline_issues = self.pipeline.validate_setup()
        issues.extend(pipeline_issues)

        return issues

    def get_dataset_info(self) -> Dict[str, Any]:
        """Get comprehensive dataset information.

        Returns:
            Dictionary containing dataset statistics and information
        """
        return {
            "output_directory": str(self.output_directory),
            "batch_config": self.batch_config.to_dict(),
            "pipeline_info": self.pipeline.get_info(),
            "organizer_info": self.output_organizer.get_info(),
            "metadata_summary": self.metadata_collector.get_summary()
        }
```

### BatchConfig

Configuration class for batch processing settings.

```python
@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    max_workers: int = 4
    """Maximum number of parallel workers"""

    use_multiprocessing: bool = True
    """Use multiprocessing instead of threading"""

    chunk_size: int = 20
    """Number of images per processing chunk"""

    retry_attempts: int = 3
    """Number of retry attempts for failed operations"""

    timeout_per_image: float = 300.0
    """Timeout per image in seconds"""

    max_memory_gb: float = 8.0
    """Maximum memory usage in GB"""

    continue_on_error: bool = False
    """Continue processing if some images fail"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of configuration
        """
        return {
            "max_workers": self.max_workers,
            "use_multiprocessing": self.use_multiprocessing,
            "chunk_size": self.chunk_size,
            "retry_attempts": self.retry_attempts,
            "timeout_per_image": self.timeout_per_image,
            "max_memory_gb": self.max_memory_gb,
            "continue_on_error": self.continue_on_error
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "BatchConfig":
        """Create from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            BatchConfig instance
        """
        return cls(**config_dict)
```

### ProcessingPipeline

Orchestrates the blur application workflow.

```python
class ProcessingPipeline:
    """Pipeline for processing images through blur effects."""

    def __init__(self, batch_config: BatchConfig):
        """Initialize processing pipeline.

        Args:
            batch_config: Batch processing configuration
        """
        self.batch_config = batch_config
        self.blur_factory = BlurFactory()

    def process_image(self, image_path: str, blur_config: Dict) -> ProcessingResult:
        """Process single image through pipeline.

        Args:
            image_path: Path to input image
            blur_config: Blur configuration dictionary

        Returns:
            ProcessingResult with output information
        """
        start_time = time.time()

        try:
            # Load image
            image = self._load_image(image_path)

            # Create blur effect
            blur_type = blur_config["blur_type"]
            parameters = blur_config["parameters"]

            effect = self.blur_factory.create_effect(blur_type, **parameters)

            # Apply blur effect
            result = effect.apply(image)

            # Generate output path
            output_path = self._generate_output_path(image_path, blur_config)

            # Save result
            self._save_result(result.result_image, output_path)

            processing_time = (time.time() - start_time) * 1000

            return ProcessingResult(
                success=True,
                input_path=image_path,
                output_path=output_path,
                processing_time_ms=processing_time,
                metadata=result.metadata
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            return ProcessingResult(
                success=False,
                input_path=image_path,
                output_path=None,
                processing_time_ms=processing_time,
                error=str(e)
            )

    def validate_blur_effect(self, blur_type: str, parameters: Dict) -> Tuple[bool, str]:
        """Validate blur effect configuration.

        Args:
            blur_type: Type of blur effect
            parameters: Effect parameters

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to create effect with given parameters
            effect = self.blur_factory.create_effect(blur_type, **parameters)
            return True, ""

        except Exception as e:
            return False, str(e)

    def estimate_processing_requirements(
        self,
        image_paths: List[str],
        blur_configs: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Estimate processing time and resource requirements.

        Args:
            image_paths: List of image file paths
            blur_configs: Dictionary of blur configurations

        Returns:
            Dictionary with processing requirements
        """
        # Estimate based on sample processing
        sample_paths = image_paths[:min(5, len(image_paths))]

        total_estimated_time = 0.0
        total_estimated_memory = 0.0

        for path in sample_paths:
            # Get image size for estimation
            image_size = self._get_image_size(path)

            # Estimate processing time based on image size and blur type
            estimated_time = self._estimate_image_processing_time(image_size, blur_configs)
            total_estimated_time += estimated_time

            # Estimate memory usage
            estimated_memory = self._estimate_image_memory_usage(image_size)
            total_estimated_memory += estimated_memory

        # Scale for full dataset
        scale_factor = len(image_paths) / len(sample_paths) if sample_paths else 1
        total_estimated_time *= scale_factor
        total_estimated_memory *= scale_factor

        return {
            "estimated_time": total_estimated_time,
            "estimated_memory_gb": total_estimated_memory / 1024 / 1024 / 1024,
            "estimated_disk_space_gb": self._estimate_disk_space(image_paths),
            "recommended_workers": min(self.batch_config.max_workers, len(image_paths)),
            "batch_config": self.batch_config.to_dict()
        }
```

### OutputOrganizer

Manages directory structure and file naming.

```python
class OutputOrganizer:
    """Organizes dataset output files and directories."""

    def __init__(self, output_directory: Path, naming_pattern: str = None):
        """Initialize output organizer.

        Args:
            output_directory: Base output directory
            naming_pattern: Pattern for output filenames
        """
        self.output_directory = Path(output_directory)
        self.naming_pattern = naming_pattern or self._default_naming_pattern
        self.naming = NamingPattern(self.naming_pattern)

        # Create directory structure
        self._create_directory_structure()

    def register_image_pair(self, original_path: str, blur_type: str, parameters: Dict) -> Tuple[str, str]:
        """Register original and blurred image pair.

        Args:
            original_path: Path to original image
            blur_type: Type of blur applied
            parameters: Blur parameters used

        Returns:
            Tuple of (clear_image_path, blurred_image_path)
        """
        # Copy original to clear directory
        clear_path = self._copy_to_clear_directory(original_path)

        # Generate blurred image path
        blurred_filename = self.naming.generate_filename(
            Path(original_path).name,
            blur_type,
            parameters
        )
        blurred_path = self.blurred_dir / blurred_filename

        return str(clear_path), str(blurred_path)

    def get_dataset_info(self) -> Dict[str, Any]:
        """Get dataset organization information.

        Returns:
            Dictionary with dataset structure information
        """
        return {
            "output_directory": str(self.output_directory),
            "directory_structure": self._get_directory_structure(),
            "file_counts": self._get_file_counts(),
            "total_size": self._get_total_size(),
            "naming_pattern": self.naming_pattern
        }

    def validate_dataset_integrity(self) -> Dict[str, Any]:
        """Validate dataset integrity and completeness.

        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []

        # Check directory structure
        if not self.clear_dir.exists():
            issues.append("Clear images directory missing")

        if not self.blurred_dir.exists():
            issues.append("Blurred images directory missing")

        if not self.metadata_dir.exists():
            warnings.append("Metadata directory missing")

        # Check file consistency
        clear_files = set(self._get_image_files(self.clear_dir))
        blurred_files = set(self._get_image_files(self.blurred_dir))

        # Check for orphaned files
        manifest_files = set()
        if (self.metadata_dir / "dataset_manifest.json").exists():
            with open(self.metadata_dir / "dataset_manifest.json", 'r') as f:
                manifest = json.load(f)
                manifest_files = set(manifest.get("blurred_images", {}).keys())

        orphaned_blurred = blurred_files - manifest_files
        if orphaned_blurred:
            warnings.append(f"Orphaned blurred files: {len(orphaned_blurred)}")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "file_counts": {
                "clear": len(clear_files),
                "blurred": len(blurred_files),
                "metadata": len(list(self.metadata_dir.glob("*")))
            }
        }
```

### MetadataCollector

Tracks processing statistics and quality metrics.

```python
class MetadataCollector:
    """Collects and manages dataset metadata."""

    def __init__(self):
        """Initialize metadata collector."""
        self.processing_records: List[Dict] = []
        self.error_records: List[Dict] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start_collection(self) -> None:
        """Start metadata collection."""
        self.start_time = time.time()
        self.processing_records.clear()
        self.error_records.clear()

    def end_collection(self) -> None:
        """End metadata collection."""
        self.end_time = time.time()

    def record_processing(self, **kwargs) -> None:
        """Record successful processing operation.

        Args:
            **kwargs: Processing metadata
        """
        record = {
            "timestamp": time.time(),
            "type": "processing",
            **kwargs
        }
        self.processing_records.append(record)

    def record_error(self, **kwargs) -> None:
        """Record processing error.

        Args:
            **kwargs: Error metadata
        """
        record = {
            "timestamp": time.time(),
            "type": "error",
            **kwargs
        }
        self.error_records.append(record)

    def get_processing_summary(self) -> Dict[str, Any]:
        """Get processing summary statistics.

        Returns:
            Dictionary with processing statistics
        """
        if not self.processing_records:
            return {"total_processed": 0, "errors": 0}

        total_processed = len(self.processing_records)
        total_errors = len(self.error_records)
        success_rate = total_processed / (total_processed + total_errors) if (total_processed + total_errors) > 0 else 0

        # Calculate average processing time
        processing_times = [
            record.get("processing_time_ms", 0)
            for record in self.processing_records
        ]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

        return {
            "total_processed": total_processed,
            "total_errors": total_errors,
            "success_rate": success_rate,
            "avg_processing_time_ms": avg_processing_time,
            "total_time_seconds": (self.end_time - self.start_time) if self.end_time and self.start_time else 0
        }

    def save_metadata(self, output_path: str) -> None:
        """Save metadata to JSON file.

        Args:
            output_path: Output file path
        """
        metadata = {
            "collection_info": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "total_records": len(self.processing_records) + len(self.error_records)
            },
            "processing_records": self.processing_records,
            "error_records": self.error_records,
            "summary": self.get_processing_summary()
        }

        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

    def save_report(self, output_path: str) -> None:
        """Save human-readable report.

        Args:
            output_path: Output file path
        """
        summary = self.get_processing_summary()

        with open(output_path, 'w') as f:
            f.write("Blur Suite Dataset Creation Report\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"Total images processed: {summary['total_processed']}\n")
            f.write(f"Total errors: {summary['total_errors']}\n")
            f.write(f"Success rate: {summary['success_rate']:.1%}\n")
            f.write(f"Average processing time: {summary['avg_processing_time_ms']:.1f}ms\n")
            f.write(f"Total processing time: {summary['total_time_seconds']:.2f}s\n")

            if self.error_records:
                f.write("\nErrors by type:\n")
                error_types = {}
                for error in self.error_records:
                    error_type = error.get("error_type", "Unknown")
                    error_types[error_type] = error_types.get(error_type, 0) + 1

                for error_type, count in error_types.items():
                    f.write(f"  {error_type}: {count}\n")
```

## Data Classes

### ProcessingResult

Container for individual image processing results.

```python
@dataclass
class ProcessingResult:
    """Result of processing a single image."""

    success: bool
    """Whether processing was successful"""

    input_path: str
    """Path to input image"""

    output_path: Optional[str]
    """Path to output image (None if failed)"""

    processing_time_ms: float
    """Processing time in milliseconds"""

    error: Optional[str] = None
    """Error message if processing failed"""

    metadata: Optional[Dict[str, Any]] = None
    """Additional metadata"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "success": self.success,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "processing_time_ms": self.processing_time_ms,
            "error": self.error,
            "metadata": self.metadata
        }
```

### NamingPattern

Configurable pattern for output file naming.

```python
class NamingPattern:
    """Configurable pattern for output file naming."""

    def __init__(self, pattern: str):
        """Initialize naming pattern.

        Args:
            pattern: Pattern string with placeholders
        """
        self.pattern = pattern
        self._validate_pattern()

    def generate_filename(self, original_name: str, blur_type: str, parameters: Dict) -> str:
        """Generate output filename.

        Args:
            original_name: Original filename
            blur_type: Type of blur applied
            parameters: Blur parameters used

        Returns:
            Generated output filename
        """
        # Extract base name without extension
        base_name = Path(original_name).stem
        extension = Path(original_name).suffix

        # Format parameters for filename
        formatted_params = self._format_parameters(parameters)

        # Generate filename using pattern
        filename = self.pattern.format(
            original=base_name,
            blur_type=blur_type,
            extension=extension[1:],  # Remove leading dot
            **formatted_params
        )

        return filename

    def _format_parameters(self, parameters: Dict) -> Dict:
        """Format parameters for filename inclusion.

        Args:
            parameters: Raw parameter dictionary

        Returns:
            Formatted parameters
        """
        formatted = {}

        for key, value in parameters.items():
            if isinstance(value, float):
                # Format floats to reasonable precision
                formatted[key] = f"{value:.2f}".rstrip('0').rstrip('.')
            elif isinstance(value, str):
                # Truncate long strings
                formatted[key] = value[:20] if len(value) > 20 else value
            else:
                formatted[key] = str(value)

        return formatted
```

## Utility Functions

### Path Management

```python
class PathManager:
    """Utilities for managing file paths and directories."""

    @staticmethod
    def find_images(directory: Union[str, Path]) -> List[Path]:
        """Find all image files in directory.

        Args:
            directory: Directory to search

        Returns:
            List of image file paths
        """
        directory = Path(directory)

        if not directory.exists():
            return []

        image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
        image_paths = []

        for ext in image_extensions:
            image_paths.extend(directory.rglob(f"*{ext}"))
            image_paths.extend(directory.rglob(f"*{ext.upper()}"))

        return sorted(image_paths)

    @staticmethod
    def validate_image_path(image_path: Union[str, Path]) -> bool:
        """Validate that path points to a valid image file.

        Args:
            image_path: Path to validate

        Returns:
            True if path is valid image file
        """
        path = Path(image_path)

        if not path.exists():
            return False

        if not path.is_file():
            return False

        # Check file extension
        valid_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
        return path.suffix.lower() in valid_extensions

    @staticmethod
    def get_image_info(image_path: Union[str, Path]) -> Dict[str, Any]:
        """Get information about image file.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with image information
        """
        path = Path(image_path)

        try:
            # Get basic file info
            stat = path.stat()

            info = {
                "path": str(path),
                "size_bytes": stat.st_size,
                "modified_time": stat.st_mtime,
                "extension": path.suffix.lower()
            }

            # Try to get image dimensions without loading full image
            try:
                with Image.open(path) as img:
                    info["dimensions"] = (img.width, img.height)
                    info["mode"] = img.mode
                    info["format"] = img.format
            except Exception:
                # If PIL can't read, try OpenCV
                try:
                    import cv2
                    img = cv2.imread(str(path))
                    if img is not None:
                        info["dimensions"] = (img.shape[1], img.shape[0])  # (width, height)
                        info["channels"] = img.shape[2] if len(img.shape) > 2 else 1
                except Exception:
                    pass

            return info

        except Exception as e:
            return {"path": str(path), "error": str(e)}
```

### System Information

```python
class SystemInfo:
    """Utilities for getting system information."""

    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information.

        Returns:
            Dictionary with CPU details
        """
        return {
            "logical_cores": os.cpu_count() or 1,
            "physical_cores": psutil.cpu_count(logical=False) or 1,
            "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            "load_percent": psutil.cpu_percent(interval=1)
        }

    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get memory information.

        Returns:
            Dictionary with memory details
        """
        memory = psutil.virtual_memory()

        return {
            "total_gb": memory.total / 1024 / 1024 / 1024,
            "available_gb": memory.available / 1024 / 1024 / 1024,
            "used_gb": memory.used / 1024 / 1024 / 1024,
            "usage_percent": memory.percent
        }

    @staticmethod
    def get_storage_info(path: str = ".") -> Dict[str, Any]:
        """Get storage information for path.

        Args:
            path: Path to check storage for

        Returns:
            Dictionary with storage details
        """
        usage = psutil.disk_usage(path)

        return {
            "total_gb": usage.total / 1024 / 1024 / 1024,
            "free_gb": usage.free / 1024 / 1024 / 1024,
            "used_gb": usage.used / 1024 / 1024 / 1024,
            "usage_percent": usage.percent
        }

    @staticmethod
    def get_optimal_batch_config() -> BatchConfig:
        """Get optimal batch configuration for current system.

        Returns:
            Optimized BatchConfig
        """
        cpu_info = SystemInfo.get_cpu_info()
        memory_info = SystemInfo.get_memory_info()

        # Recommend workers based on CPU cores
        optimal_workers = max(1, cpu_info["logical_cores"] - 1)

        # Adjust for memory constraints
        if memory_info["available_gb"] < 4:
            optimal_workers = min(optimal_workers, 2)
        elif memory_info["available_gb"] < 8:
            optimal_workers = min(optimal_workers, 4)

        return BatchConfig(
            max_workers=optimal_workers,
            chunk_size=max(10, optimal_workers * 5),
            max_memory_gb=min(memory_info["available_gb"] * 0.8, 16.0)
        )
```

## Error Handling

### Custom Exceptions

```python
class DatasetError(Exception):
    """Base exception for dataset creation errors."""
    pass

class ConfigurationError(DatasetError):
    """Exception for configuration-related errors."""
    pass

class ValidationError(DatasetError):
    """Exception for validation errors."""
    pass

class ProcessingError(DatasetError):
    """Exception for image processing errors."""
    pass

class OutputError(DatasetError):
    """Exception for output-related errors."""
    pass
```

## Integration Examples

### Integration with Interactive Tool

```python
from blur_suite.interactive import BlurSuiteApp
from blur_suite.dataset import DatasetCreator

# Configure in interactive tool
app = BlurSuiteApp()
app.load_image("sample.jpg")
app.set_blur_type("gaussian")
app.set_parameters(kernel_size=7, sigma_x=1.5)

# Export configuration
app.export_configuration("dataset_config.json")

# Use with dataset creator
creator = DatasetCreator("./output_dataset")
success = creator.create_from_config("dataset_config.json")
```

### Batch Processing Workflow

```python
from blur_suite.dataset import DatasetCreator, BatchConfig

# Custom batch configuration for large dataset
batch_config = BatchConfig(
    max_workers=16,
    use_multiprocessing=True,
    chunk_size=50,
    retry_attempts=5,
    timeout_per_image=600,
    max_memory_gb=32.0
)

# Create dataset creator
creator = DatasetCreator("./large_dataset", batch_config)

# Progress callback with detailed information
def detailed_progress_callback(current, total, current_file=None):
    percentage = (current / total) * 100
    print(f"Progress: {current}/{total} ({percentage:.1f}%)")

    if current_file:
        print(f"Processing: {Path(current_file).name}")

    # Show ETA
    if current > 0:
        elapsed = time.time() - start_time
        rate = current / elapsed
        remaining = total - current
        eta = remaining / rate if rate > 0 else 0
        print(f"ETA: {eta:.1f} seconds")

# Process dataset
start_time = time.time()
success = creator.create_from_config("large_config.json", detailed_progress_callback)

if success:
    print("✅ Large dataset created successfully!")
    print(f"Total time: {time.time() - start_time:.2f}s")
```

### Custom Processing Pipeline

```python
class CustomProcessingPipeline:
    """Custom processing pipeline with preprocessing and postprocessing."""

    def __init__(self, creator: DatasetCreator):
        self.creator = creator
        self.preprocessors = []
        self.postprocessors = []

    def add_preprocessor(self, func):
        """Add image preprocessing function."""
        self.preprocessors.append(func)

    def add_postprocessor(self, func):
        """Add result postprocessing function."""
        self.postprocessors.append(func)

    def process_with_custom_pipeline(self, image_path: str, blur_config: Dict):
        """Process image with custom pipeline."""
        # Load and preprocess image
        image = self.creator.pipeline._load_image(image_path)

        for preprocessor in self.preprocessors:
            image = preprocessor(image)

        # Apply blur effect
        result = self.creator.pipeline.process_image_with_blur(image, blur_config)

        # Post-process result
        for postprocessor in self.postprocessors:
            result = postprocessor(result)

        return result

# Usage example
pipeline = CustomProcessingPipeline(creator)

# Add preprocessing (e.g., resize, normalize)
pipeline.add_preprocessor(lambda img: resize_image(img, (512, 512)))
pipeline.add_postprocessor(lambda result: add_watermark(result))

# Process with custom pipeline
for image_path, config in image_configs.items():
    result = pipeline.process_with_custom_pipeline(image_path, config)
```

## Best Practices

### Performance Optimization

1. **Use appropriate worker counts** based on CPU cores
2. **Configure chunk sizes** based on memory availability
3. **Enable multiprocessing** for CPU-bound tasks
4. **Monitor memory usage** during processing

### Error Handling

1. **Implement retry logic** for transient failures
2. **Validate configurations** before large processing runs
3. **Log detailed error information** for debugging
4. **Save intermediate results** for recovery

### Quality Assurance

1. **Verify output integrity** after processing
2. **Compare results** with expected outcomes
3. **Document processing parameters** for reproducibility
4. **Archive source data** and configurations

## API Compatibility

### Version Compatibility

The dataset API maintains backward compatibility:

- **Minor versions**: New features added without breaking existing code
- **Patch versions**: Bug fixes and performance improvements
- **Major versions**: Breaking changes may be introduced

### Deprecation Policy

Features are deprecated before removal:

```python
@deprecated("Use create_from_config() instead")
def create_dataset(self, config_path: str):
    """Deprecated method for dataset creation."""
    warnings.warn(
        "create_dataset() is deprecated, use create_from_config() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return self.create_from_config(config_path)
```

## Support and Resources

- 📚 **[User Guide: Dataset Creation](../user_guide/dataset_creation.md)** - Complete usage guide
- 💡 **[Examples: Batch Processing](../examples/batch_processing.py)** - Working examples
- 💡 **[Examples: Advanced Usage](../examples/advanced_usage.py)** - Complex workflows
- 🛠️ **[Troubleshooting Guide](../troubleshooting.md)** - Common issues and solutions

---

*Need help?* Check the [Troubleshooting Guide](../troubleshooting.md) or explore the [Examples](../examples/) for more advanced usage patterns.