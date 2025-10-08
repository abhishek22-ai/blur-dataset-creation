# Dataset Creation User Guide

The Blur Suite Dataset Creation module provides powerful capabilities for generating large-scale blurred image datasets with parallel processing, comprehensive metadata tracking, and flexible configuration options.

## Overview

The dataset creation system offers:
- **Parallel processing** with configurable worker pools
- **Batch operations** for thousands of images
- **Organized output** with structured directory layouts
- **Comprehensive metadata** and quality metrics
- **Flexible configuration** via JSON files
- **Progress tracking** with ETA calculations
- **NEW in v2.0.0:** Intelligent caching for improved performance
- **NEW in v2.0.0:** Advanced memory management and optimization
- **NEW in v2.0.0:** Custom effect builder integration
- **NEW in v2.0.0:** Comprehensive monitoring and error recovery

## Architecture

```
Dataset Creation Workflow
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Configuration   │───▶│   Processing     │───▶│     Output      │
│    Loading      │    │    Pipeline      │    │   Organization  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Validation    │    │  Batch Processor │    │   Metadata      │
│   & Setup       │    │  (Parallel)      │    │   Collection    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quick Start

### Basic Dataset Creation

```python
from blur_suite.dataset import DatasetCreator

# Initialize creator
creator = DatasetCreator("./output_dataset")

# Create from configuration file
success = creator.create_from_config("dataset_config.json")

if success:
    print("✅ Dataset created successfully!")
```

### Configuration File Structure

```json
{
  "metadata": {
    "created_by": "Blur Suite Dataset Creator v2.0.0",
    "creation_date": "2024-10-08T12:00:00Z",
    "version": "2.0.0",
    "description": "Document blur dataset for analysis"
  },
  "global_settings": {
    "output_format": "png",
    "quality": 95,
    "parallel_processing": true,
    "max_workers": 4,
    "preserve_metadata": true
  },
  "image_configurations": {
    "document1.jpg": {
      "blur_type": "gaussian",
      "parameters": {
        "kernel_size": 7,
        "sigma_x": 1.5,
        "sigma_y": 1.5
      },
      "enabled": true
    },
    "document2.jpg": {
      "blur_type": "motion",
      "parameters": {
        "angle": 45.0,
        "length": 15
      },
      "enabled": true
    }
  }
}
```

## Main Components

### DatasetCreator

The main orchestrator class for dataset creation:

```python
from blur_suite.dataset import DatasetCreator, BatchConfig

# Basic initialization
creator = DatasetCreator("./my_dataset")

# Custom batch configuration
batch_config = BatchConfig(
    max_workers=8,
    use_multiprocessing=True,
    chunk_size=20,
    retry_attempts=3
)
creator.batch_config = batch_config

# Create dataset
success = creator.create_from_config("config.json")
```

#### Key Methods

- `create_from_config(config_path)` - Create from JSON configuration
- `create_from_config_dict(config_dict)` - Create from configuration dictionary
- `validate_setup()` - Validate current setup before processing
- `get_dataset_info()` - Get comprehensive dataset information
- `export_processing_script()` - Export standalone processing script

### Processing Pipeline

Manages the blur application workflow:

```python
# Access the processing pipeline
pipeline = creator.pipeline

# Validate blur configuration
is_valid, error = pipeline.validate_blur_effect(
    "gaussian",
    {"kernel_size": 5, "sigma_x": 1.0}
)

# Estimate processing requirements
requirements = pipeline.estimate_processing_requirements(
    image_paths,
    blur_configs
)
print(f"Estimated time: {requirements['estimated_time']}")
```

### Batch Processor

Handles parallel processing with advanced features:

```python
from blur_suite.dataset import BatchProcessor, BatchConfig

# Configure batch processing
batch_config = BatchConfig(
    max_workers=8,              # Number of parallel workers
    use_multiprocessing=True,   # Use multiple processes vs threads
    chunk_size=50,             # Images per chunk
    max_memory_gb=16.0,        # Memory limit
    retry_attempts=3,          # Retry failed operations
    timeout_per_image=300.0    # Timeout per image (seconds)
)

processor = BatchProcessor(batch_config)

# Process with custom function
def process_image_with_blur(image_path, blur_type, params):
    # Your processing logic here
    return success, output_path, result_image, processing_time

results = processor.process_batch(
    image_paths,
    process_image_with_blur,
    "gaussian",
    {"kernel_size": 5}
)
```

## Configuration Management

### Creating Configurations

#### Method 1: JSON File

```python
import json
from datetime import datetime

# Create comprehensive configuration
config = {
    "metadata": {
        "created_by": "My Dataset Tool",
        "creation_date": datetime.now().isoformat(),
        "version": "1.0.0",
        "description": "Custom dataset for analysis"
    },
    "global_settings": {
        "output_format": "png",
        "quality": 95,
        "parallel_processing": True,
        "max_workers": 4,
        "preserve_metadata": True,
        "organize_by_blur_type": True
    },
    "image_configurations": {
        "path/to/document1.jpg": {
            "blur_type": "gaussian",
            "parameters": {"kernel_size": 5, "sigma_x": 1.0, "sigma_y": 1.0},
            "enabled": True
        }
    }
}

# Save configuration
with open("my_config.json", "w") as f:
    json.dump(config, f, indent=2)
```

#### Method 2: Programmatic Creation

```python
from blur_suite.dataset import DatasetCreator

creator = DatasetCreator("./output")

# Create configuration from image directory
success = creator.create_sample_configuration(
    "./input_images",
    "auto_config.json"
)

if success:
    print("✅ Sample configuration created!")
```

### Blur Type Configurations

#### Gaussian Blur
```json
{
  "blur_type": "gaussian",
  "parameters": {
    "kernel_size": 7,
    "sigma_x": 1.5,
    "sigma_y": 1.5
  }
}
```

#### Motion Blur
```json
{
  "blur_type": "motion",
  "parameters": {
    "angle": 45.0,
    "length": 15
  }
}
```

#### Defocus Blur
```json
{
  "blur_type": "defocus",
  "parameters": {
    "radius": 8,
    "strength": 1.2
  }
}
```

#### Average Blur
```json
{
  "blur_type": "average",
  "parameters": {
    "kernel_size": 7
  }
}
```

#### Bilateral Blur
```json
{
  "blur_type": "bilateral",
  "parameters": {
    "diameter": 9,
    "sigma_color": 75.0,
    "sigma_space": 75.0
  }
}
```

## Advanced Features

### Parallel Processing Strategies

#### Multi-threading vs Multi-processing

```python
# Multi-threading (shared memory, good for I/O bound tasks)
batch_config = BatchConfig(
    max_workers=8,
    use_multiprocessing=False,
    chunk_size=20
)

# Multi-processing (isolated memory, good for CPU bound tasks)
batch_config = BatchConfig(
    max_workers=8,
    use_multiprocessing=True,
    chunk_size=10  # Smaller chunks for processes
)
```

#### Adaptive Processing

```python
from blur_suite.dataset import AdaptiveBatchProcessor

# Automatically adjusts to system resources
adaptive_processor = AdaptiveBatchProcessor()

# Custom resource limits
processor = AdaptiveBatchProcessor(
    max_memory_usage=0.8,    # Use 80% of available memory
    min_workers_per_core=1,  # Minimum workers per CPU core
    max_workers_per_core=2   # Maximum workers per CPU core
)
```

### Custom Naming Patterns

```python
from blur_suite.dataset import OutputOrganizer, NamingPattern

# Custom filename pattern
pattern = NamingPattern(
    "{original}_{blur_type}_k{kernel_size}_s{sigma_x}.png"
)

organizer = OutputOrganizer("./output", pattern)

# Generate filename
filename = organizer.naming.generate_filename(
    "document.jpg",
    "gaussian",
    {"kernel_size": 5, "sigma_x": 1.0}
)
# Result: "document_gaussian_k5_s1.0.png"
```

### Progress Monitoring

#### Basic Progress Callback

```python
def progress_callback(current, total, current_file=None):
    percentage = (current / total) * 100
    print(f"Progress: {current}/{total} ({percentage:.1f}%)")

    if current_file:
        print(f"Processing: {current_file}")

# Use with dataset creation
creator.create_from_config("config.json", progress_callback)
```

#### Advanced Progress Tracking

```python
import time
from collections import deque

class AdvancedProgressTracker:
    def __init__(self, window_size=10):
        self.start_time = time.time()
        self.recent_times = deque(maxlen=window_size)

    def __call__(self, current, total, current_file=None):
        elapsed = time.time() - self.start_time
        rate = current / elapsed if elapsed > 0 else 0

        # Calculate ETA
        remaining = total - current
        eta = remaining / rate if rate > 0 else 0

        print(f"Progress: {current}/{total} ({current/total*100:.1f}%)")
        print(f"Rate: {rate:.2f} images/sec, ETA: {eta:.1f} sec")

        if current_file:
            print(f"Current: {current_file}")

# Use advanced tracker
tracker = AdvancedProgressTracker()
creator.create_from_config("config.json", tracker)
```

## Output Organization

### Default Directory Structure

```
dataset_output/
├── clear/                    # Original images
│   ├── document1.png
│   └── document2.png
├── blurred/                  # Blurred images
│   ├── document1_gaussian_k5_s1.0.png
│   ├── document1_motion_a0_l10.png
│   └── document2_defocus_r5_s1.0.png
└── metadata/                 # Metadata and reports
    ├── processing_metadata.json
    ├── dataset_report.txt
    ├── dataset_config.json
    └── dataset_manifest.json
```

### Custom Organization

```python
from blur_suite.dataset import OutputOrganizer

# Custom directory structure
organizer = OutputOrganizer("./custom_dataset")

# Organize by blur type
organizer.organize_by_blur_type = True

# Custom subdirectory structure
organizer.subdirectories = {
    "originals": "input",
    "processed": "output",
    "reports": "metadata"
}
```

## Metadata and Reporting

### Processing Metadata

```python
# Access metadata collector
metadata_collector = creator.metadata_collector

# Record custom metrics
metadata_collector.record_processing(
    image_path="document.jpg",
    blur_type="gaussian",
    parameters={"kernel_size": 5},
    processing_time_ms=150.5,
    original_size=(1920, 1080),
    result_size=(1920, 1080),
    success=True,
    custom_metrics={"psnr": 28.5, "ssim": 0.89}
)

# Generate reports
metadata_collector.save_metadata("detailed_metadata.json")
metadata_collector.save_report("processing_report.txt")
```

### Quality Metrics

```python
# Get quality summary
quality_metrics = metadata_collector.get_quality_metrics()

print(f"Success rate: {quality_metrics['success_rate']:.1%}")
print(f"Average processing time: {quality_metrics['avg_processing_time_ms']:.1f}ms")
print(f"Total processing time: {quality_metrics['total_processing_time']:.2f}s")

# Parameter distribution analysis
param_stats = metadata_collector.get_parameter_statistics()
for param, stats in param_stats.items():
    print(f"{param}: mean={stats['mean']:.2f}, std={stats['std']:.2f}")
```

## Error Handling and Validation

### Setup Validation

```python
# Validate before processing
issues = creator.validate_setup()

if issues:
    print("Setup issues found:")
    for issue in issues:
        print(f"  ❌ {issue}")
    exit(1)

print("✅ Setup validation passed!")
```

### Configuration Validation

```python
# Validate configuration
validation_issues = creator.pipeline.validate_dataset_configuration(
    image_paths, blur_configs
)

if validation_issues:
    print("Configuration issues:")
    for issue in validation_issues:
        print(f"  ❌ {issue['image_path']}: {issue['error']}")
```

### Error Recovery

```python
# Configure retry behavior
batch_config = BatchConfig(
    retry_attempts=3,
    retry_delay=1.0,        # Initial delay between retries
    retry_backoff=2.0,      # Exponential backoff multiplier
    retry_on_errors=[IOError, OSError]  # Specific errors to retry
)

# Handle processing errors gracefully
try:
    success = creator.create_dataset()
    if not success:
        # Get error details
        error_summary = creator.metadata_collector.get_error_summary()
        print("Processing errors:")
        for error in error_summary['errors']:
            print(f"  {error['image_path']}: {error['error_message']}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Optimization

### Memory Management

```python
# Configure for memory-constrained systems
batch_config = BatchConfig(
    max_workers=2,          # Reduce workers
    chunk_size=5,          # Smaller chunks
    max_memory_gb=4.0,     # Memory limit
    memory_buffer_mb=100   # Buffer for safety
)

# Monitor memory usage
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"Current memory usage: {memory_mb:.1f}MB")
```

### Processing Time Estimation

```python
# Get detailed requirements estimate
requirements = creator.pipeline.estimate_processing_requirements(
    image_paths, blur_configs
)

print("Processing requirements:")
print(f"  Estimated time: {requirements['estimated_time']}")
print(f"  Estimated memory: {requirements['estimated_memory_gb']:.1f}GB")
print(f"  Recommended workers: {requirements['recommended_workers']}")
print(f"  Estimated disk space: {requirements['estimated_disk_space_gb']:.1f}GB")
```

### System Resource Detection

```python
from blur_suite.dataset import SystemInfo

# Get system information
cpu_info = SystemInfo.get_cpu_info()
memory_info = SystemInfo.get_memory_info()
storage_info = SystemInfo.get_storage_info()

print(f"CPU cores: {cpu_info['logical_cores']}")
print(f"Available memory: {memory_info['available_gb']:.1f}GB")
print(f"Free storage: {storage_info['free_gb']:.1f}GB")

# Get optimal configuration
optimal_config = SystemInfo.get_optimal_batch_config()
print(f"Optimal workers: {optimal_config['max_workers']}")
print(f"Optimal chunk size: {optimal_config['chunk_size']}")
```

## Integration Examples

### Integration with Interactive Tool

```python
# Export configuration from interactive tool
from blur_suite.interactive.exporters.dataset_exporter import DatasetExporter

exporter = DatasetExporter()
config = exporter.create_dataset_config(image_configurations)
exporter.export_configuration("dataset_config.json", config)

# Use with dataset creator
creator = DatasetCreator("./output")
creator.create_from_config("dataset_config.json")
```

### Batch Processing Workflow

```python
import os
from pathlib import Path

# Process entire directory
input_dir = "./input_images"
output_dir = "./blurred_dataset"

# Find all images
image_paths = []
for ext in ['*.jpg', '*.png', '*.jpeg', '*.tiff']:
    image_paths.extend(Path(input_dir).glob(ext))

print(f"Found {len(image_paths)} images to process")

# Create configuration for all images
image_configs = {}
for i, image_path in enumerate(image_paths):
    # Vary blur parameters across images
    blur_type = ["gaussian", "motion", "defocus"][i % 3]
    image_configs[str(image_path)] = {
        "blur_type": blur_type,
        "parameters": get_blur_params(blur_type, i),
        "enabled": True
    }

# Create and run dataset
config = {
    "metadata": {"created_by": "Batch Processor"},
    "global_settings": {
        "parallel_processing": True,
        "max_workers": 8,
        "output_format": "png"
    },
    "image_configurations": image_configs
}

creator = DatasetCreator(output_dir)
success = creator.create_from_config_dict(config)
```

### Custom Processing Pipeline

```python
class CustomPipeline:
    def __init__(self, creator):
        self.creator = creator
        self.preprocessors = []
        self.postprocessors = []

    def add_preprocessor(self, func):
        """Add image preprocessing function"""
        self.preprocessors.append(func)

    def add_postprocessor(self, func):
        """Add result postprocessing function"""
        self.postprocessors.append(func)

    def process_image(self, image_path, blur_config):
        """Custom processing with pre/post processing"""
        # Load and preprocess image
        image = self.load_image(image_path)
        for preprocessor in self.preprocessors:
            image = preprocessor(image)

        # Apply blur effect
        blur_effect = self.creator.pipeline.create_blur_effect(
            blur_config["blur_type"],
            blur_config["parameters"]
        )
        result = blur_effect.apply(image)

        # Post-process result
        for postprocessor in self.postprocessors:
            result = postprocessor(result)

        return result

# Usage example
pipeline = CustomPipeline(creator)

# Add preprocessing (e.g., resize, normalize)
pipeline.add_preprocessor(lambda img: resize_image(img, (512, 512)))
pipeline.add_postprocessor(lambda result: add_watermark(result))

# Process with custom pipeline
for image_path, config in image_configs.items():
    result = pipeline.process_image(image_path, config)
    # Save result...
```

## Best Practices

### Configuration Management
1. **Validate configurations** before large-scale processing
2. **Use descriptive names** for configuration files
3. **Version control** configuration files
4. **Document parameter choices** for reproducibility

### Performance Optimization
1. **Match worker count** to CPU cores (typically 2-4 workers per core)
2. **Use appropriate chunk sizes** (10-50 images per chunk)
3. **Monitor memory usage** during processing
4. **Process similar images** together for better cache performance

### Error Handling
1. **Implement retry logic** for transient failures
2. **Log detailed error information** for debugging
3. **Validate inputs and outputs** at each stage
4. **Save intermediate results** for recovery

### Quality Assurance
1. **Verify output integrity** after processing
2. **Compare results** with expected outcomes
3. **Document processing parameters** for future reference
4. **Archive source data** and configurations

## Troubleshooting

### Common Issues

#### Memory Errors
- **Reduce `max_workers`** in batch configuration
- **Decrease `chunk_size`** for smaller memory footprint
- **Enable memory limits** in batch configuration
- **Process images in smaller batches**

#### Processing Failures
- **Check image file integrity** and formats
- **Verify file paths** and permissions
- **Review parameter ranges** for selected blur types
- **Check available disk space** for output

#### Slow Processing
- **Enable parallel processing** where possible
- **Increase `max_workers`** based on CPU cores
- **Use faster storage** (SSD vs HDD)
- **Optimize image formats** and sizes

#### Disk Space Issues
- **Monitor output directory** growth during processing
- **Use compressed formats** (JPEG) if quality allows
- **Clean up intermediate files** if necessary
- **Process in stages** for very large datasets

### Debug Information

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed system information
info = creator.get_dataset_info()
print(json.dumps(info, indent=2))

# Validate dataset integrity
validation = creator.output_organizer.validate_dataset_integrity()
print(f"Dataset valid: {validation['is_valid']}")
if validation['issues']:
    for issue in validation['issues']:
        print(f"  Issue: {issue}")
```

## API Reference

For detailed API documentation, see:
- **[Dataset API Reference](api_reference/dataset.md)** - Complete class documentation
- **[Examples: Batch Processing](examples/batch_processing.py)** - Working examples
- **[Examples: Advanced Usage](examples/advanced_usage.py)** - Complex workflows

---

*Need help?* Check the [Troubleshooting Guide](../troubleshooting.md) or explore the [Examples](../examples/) for more advanced usage patterns.