# CLI Usage Guide

The Blur Suite SDK provides a comprehensive command-line interface for batch processing, configuration management, and automation workflows.

## Overview

The CLI module offers:
- **Batch processing** of image datasets
- **Configuration file management** and validation
- **Interactive mode** for guided workflows
- **Plugin management** and discovery
- **Performance monitoring** and reporting

## Installation and Setup

### Basic Installation

```bash
pip install blur_suite[cli]
```

### Development Installation

```bash
git clone https://github.com/blur-suite/blur-suite-sdk.git
cd blur-suite-sdk
pip install -e .[cli]
```

## Command Structure

```bash
blur-suite <command> [subcommand] [options] [arguments]
```

### Available Commands

| Command | Description |
|---------|-------------|
| `process` | Process images with blur effects |
| `config` | Manage configuration files |
| `validate` | Validate configurations and setups |
| `info` | Display system and SDK information |
| `interactive` | Launch interactive configuration tool |
| `plugin` | Manage blur effect plugins |

## Basic Usage

### Process Images

#### Single Image Processing

```bash
# Apply Gaussian blur to single image
blur-suite process single input.jpg output.png --blur-type gaussian --kernel-size 7 --sigma 1.5
```

#### Batch Processing

```bash
# Process all images in directory
blur-suite process batch ./input_images ./output_dataset --config config.json
```

#### Directory Processing with Pattern

```bash
# Process specific file types
blur-suite process directory ./documents ./blurred --pattern "*.jpg" --blur-type motion --angle 45 --length 20
```

### Configuration Management

#### Create Configuration

```bash
# Create sample configuration from image directory
blur-suite config create ./images --output config.json
```

#### Validate Configuration

```bash
# Check configuration for errors
blur-suite config validate config.json
```

#### List Available Blur Types

```bash
# Show all available blur effects
blur-suite config list-blur-types
```

## Command Reference

### Process Command

#### Single Image Processing

```bash
blur-suite process single [OPTIONS] INPUT_PATH OUTPUT_PATH

Options:
  --blur-type TEXT          Blur effect type (gaussian, motion, defocus, etc.) [required]
  --kernel-size INTEGER     Kernel size for gaussian/average blur
  --sigma FLOAT            Sigma value for gaussian blur
  --sigma-x FLOAT          Horizontal sigma for gaussian blur
  --sigma-y FLOAT          Vertical sigma for gaussian blur
  --angle FLOAT            Motion angle (0-360 degrees)
  --length INTEGER         Motion length (1-100 pixels)
  --radius INTEGER         Defocus radius (1-50 pixels)
  --strength FLOAT         Defocus strength (0.1-5.0)
  --diameter INTEGER       Bilateral filter diameter
  --sigma-color FLOAT      Bilateral color sigma
  --sigma-space FLOAT      Bilateral space sigma
  --output-format TEXT     Output format (png, jpg, tiff) [default: png]
  --quality INTEGER        Output quality (1-100) [default: 95]
  --verbose               Enable verbose output
  --dry-run               Show what would be processed without doing it
```

#### Batch Processing

```bash
blur-suite process batch [OPTIONS] INPUT_DIR OUTPUT_DIR

Options:
  --config PATH           Configuration file path [required]
  --workers INTEGER       Number of parallel workers [default: 4]
  --chunk-size INTEGER    Images per processing chunk [default: 20]
  --retry-attempts INTEGER Number of retry attempts [default: 3]
  --continue-on-error     Continue processing if some images fail
  --progress-bar          Show progress bar
  --log-file PATH         Log file path
  --verbose              Enable verbose output
```

#### Directory Processing

```bash
blur-suite process directory [OPTIONS] INPUT_DIR OUTPUT_DIR

Options:
  --pattern TEXT          File pattern to match (e.g., "*.jpg") [default: "*"]
  --recursive            Process subdirectories recursively
  --blur-type TEXT       Blur effect type [required]
  --workers INTEGER      Number of parallel workers [default: 4]
  --output-format TEXT   Output format [default: png]
  --quality INTEGER      Output quality [default: 95]
  [BLUR_PARAMETERS...]   Blur effect parameters
```

### Config Command

#### Create Configuration

```bash
blur-suite config create [OPTIONS] IMAGE_DIR

Options:
  --output PATH              Output configuration file [default: dataset_config.json]
  --format TEXT             Configuration format (json, yaml) [default: json]
  --include-subdirs         Include images in subdirectories
  --sample-size INTEGER     Number of sample configurations to create [default: 5]
  --blur-types TEXT         Comma-separated list of blur types to include
  --parameter-ranges TEXT   Parameter ranges for sample generation
```

#### Validate Configuration

```bash
blur-suite config validate [OPTIONS] CONFIG_FILE

Options:
  --strict              Strict validation (fail on warnings)
  --show-issues         Display detailed issue information
  --fix-suggestions     Show suggestions for fixing issues
```

#### Convert Configuration Format

```bash
blur-suite config convert [OPTIONS] INPUT_CONFIG OUTPUT_CONFIG

Options:
  --from-format TEXT    Input format (json, yaml) [required]
  --to-format TEXT      Output format (json, yaml) [required]
  --pretty-print       Pretty-print output
```

### Validate Command

#### Validate Setup

```bash
blur-suite validate setup [OPTIONS]

Options:
  --check-dependencies     Check all dependencies
  --check-system           Check system compatibility
  --check-performance      Run performance benchmarks
  --output-format TEXT     Output format (text, json) [default: text]
```

#### Validate Images

```bash
blur-suite validate images [OPTIONS] IMAGE_PATHS...

Options:
  --check-integrity        Check image file integrity
  --check-formats          Verify supported formats
  --check-dimensions       Check image dimensions
  --output-report PATH     Save validation report
```

### Info Command

#### System Information

```bash
blur-suite info system [OPTIONS]

Options:
  --all-details           Show all available information
  --output-format TEXT    Output format (text, json) [default: text]
```

#### SDK Information

```bash
blur-suite info sdk [OPTIONS]

Options:
  --version              Show version information
  --dependencies         List all dependencies
  --plugins              Show loaded plugins
  --performance          Run performance benchmarks
```

### Interactive Command

#### Launch Interactive Tool

```bash
blur-suite interactive [OPTIONS]

Options:
  --config PATH          Load configuration file
  --image PATH           Load specific image
  --theme TEXT           UI theme (light, dark, auto) [default: auto]
  --geometry TEXT        Window geometry (WxH+X+Y)
  --fullscreen           Start in fullscreen mode
```

### Plugin Command

#### List Plugins

```bash
blur-suite plugin list [OPTIONS]

Options:
  --available           Show all available plugins
  --enabled             Show only enabled plugins
  --details             Show plugin details
```

#### Install Plugin

```bash
blur-suite plugin install [OPTIONS] PLUGIN_PATH

Options:
  --force              Force installation over existing plugin
  --enable             Enable plugin after installation
  --config-file PATH   Plugin configuration file
```

#### Enable/Disable Plugin

```bash
blur-suite plugin enable PLUGIN_NAME
blur-suite plugin disable PLUGIN_NAME
```

## Configuration Files

### Global Configuration

Create a global configuration file at `~/.blur-suite/config.yaml`:

```yaml
# Global settings
default_workers: 4
default_chunk_size: 20
default_output_format: png
default_quality: 95

# Logging configuration
logging:
  level: INFO
  file: ~/.blur-suite/blur_suite.log
  max_size_mb: 100

# Plugin configuration
plugins:
  enabled: []
  disabled: []
  search_paths:
    - ~/.blur-suite/plugins
    - ./plugins

# Performance settings
performance:
  use_gpu: auto
  memory_limit_gb: 8
  temp_directory: /tmp/blur_suite
```

### Project Configuration

Create project-specific configuration in your project directory:

```yaml
# Project settings
project_name: "My Blur Analysis"
input_directories:
  - ./data/raw
  - ./data/processed

output_directories:
  datasets: ./output/datasets
  reports: ./output/reports
  logs: ./output/logs

# Default processing settings
processing:
  parallel_processing: true
  max_workers: 8
  retry_attempts: 3

# Quality settings
quality:
  default_psnr_threshold: 25.0
  default_ssim_threshold: 0.8
```

## Advanced Usage

### Batch Processing Scripts

#### Simple Batch Script

```bash
#!/bin/bash
# process_dataset.sh

INPUT_DIR="./input"
OUTPUT_DIR="./output"
CONFIG_FILE="./configs/dataset_config.json"

# Process dataset
blur-suite process batch "$INPUT_DIR" "$OUTPUT_DIR" --config "$CONFIG_FILE" --workers 8

# Generate report
blur-suite info performance --output-report "./output/performance_report.json"
```

#### Advanced Batch Script with Error Handling

```bash
#!/bin/bash
# advanced_processing.sh

set -e  # Exit on any error

INPUT_DIR="$1"
OUTPUT_DIR="$2"
CONFIG_FILE="$3"

if [[ -z "$INPUT_DIR" || -z "$OUTPUT_DIR" || -z "$CONFIG_FILE" ]]; then
    echo "Usage: $0 <input_dir> <output_dir> <config_file>"
    exit 1
fi

echo "Starting batch processing..."
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo "Config: $CONFIG_FILE"

# Validate inputs
blur-suite validate images "$INPUT_DIR"/* --check-integrity

# Validate configuration
blur-suite config validate "$CONFIG_FILE"

# Process with monitoring
blur-suite process batch "$INPUT_DIR" "$OUTPUT_DIR" \
    --config "$CONFIG_FILE" \
    --workers 8 \
    --progress-bar \
    --log-file "$OUTPUT_DIR/processing.log" \
    --continue-on-error

# Generate comprehensive report
blur-suite info performance --output-report "$OUTPUT_DIR/report.json"

echo "Processing completed successfully!"
```

### Configuration Templates

#### Research Dataset Configuration

```json
{
  "metadata": {
    "project": "Blur Analysis Research",
    "experiment": "Parameter Study",
    "version": "1.0.0"
  },
  "global_settings": {
    "parallel_processing": true,
    "max_workers": 12,
    "preserve_metadata": true,
    "organize_by_blur_type": true
  },
  "image_configurations": {}
}
```

#### Production Configuration

```json
{
  "metadata": {
    "environment": "production",
    "quality_standard": "high"
  },
  "global_settings": {
    "output_format": "png",
    "quality": 98,
    "parallel_processing": true,
    "max_workers": 16,
    "retry_attempts": 5,
    "timeout_per_image": 300
  },
  "image_configurations": {}
}
```

### Automation Workflows

#### Integration with Other Tools

```bash
#!/bin/bash
# integrate_with_ml_pipeline.sh

# Step 1: Preprocess images
echo "Step 1: Preprocessing images..."
blur-suite process directory ./raw_data ./preprocessed \
    --pattern "*.jpg" \
    --blur-type gaussian \
    --kernel-size 3 \
    --sigma 0.5

# Step 2: Generate multiple blur variants
echo "Step 2: Generating blur variants..."
for blur_type in gaussian motion defocus; do
    blur-suite process batch ./preprocessed "./blurred_${blur_type}" \
        --config "./configs/${blur_type}_config.json"
done

# Step 3: Validate results
echo "Step 3: Validating results..."
blur-suite validate images ./blurred_*/* --check-integrity --output-report validation_report.json

# Step 4: Generate analysis report
echo "Step 4: Generating analysis report..."
blur-suite info performance --output-report analysis_report.json
```

#### Scheduled Processing

```bash
#!/bin/bash
# scheduled_processing.sh

LOG_FILE="./logs/daily_processing.log"

echo "$(date): Starting scheduled processing..." >> "$LOG_FILE"

# Process new images
blur-suite process batch ./incoming ./processed \
    --config ./configs/scheduled_config.json \
    --log-file "$LOG_FILE" \
    2>> "$LOG_FILE"

if [[ $? -eq 0 ]]; then
    echo "$(date): Processing completed successfully" >> "$LOG_FILE"
else
    echo "$(date): Processing failed" >> "$LOG_FILE"
    # Send notification or alert
fi
```

## Performance Tuning

### CPU Optimization

```bash
# Use optimal worker count for your CPU
CPU_CORES=$(nproc)
WORKERS=$(( CPU_CORES * 2 ))

blur-suite process batch ./input ./output \
    --config config.json \
    --workers $WORKERS \
    --chunk-size 20
```

### Memory Optimization

```bash
# Monitor and limit memory usage
blur-suite process batch ./input ./output \
    --config config.json \
    --workers 4 \
    --chunk-size 10 \
    --log-file processing.log

# Check memory usage
echo "Memory usage during processing:"
grep "memory" processing.log
```

### GPU Acceleration

```bash
# Enable GPU acceleration if available
export BLUR_SUITE_USE_GPU=1

blur-suite process batch ./input ./output \
    --config config.json \
    --workers 8

# Verify GPU usage
blur-suite info system --all-details | grep -i gpu
```

## Error Handling and Debugging

### Verbose Output

```bash
# Enable verbose logging for debugging
blur-suite process batch ./input ./output \
    --config config.json \
    --verbose \
    --log-file debug.log
```

### Debug Mode

```bash
# Run in debug mode
export BLUR_SUITE_DEBUG=1

blur-suite process single input.jpg output.png \
    --blur-type gaussian \
    --kernel-size 5 \
    --verbose
```

### Log Analysis

```bash
# Analyze processing logs
blur-suite info performance --log-file processing.log --output-report analysis.json

# Check for common issues
grep -i "error\|warning\|failed" processing.log
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

def run_blur_suite_command(cmd_args):
    """Run blur-suite command and return result"""
    try:
        result = subprocess.run(
            ["blur-suite"] + cmd_args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return e.stdout, e.stderr

# Example usage
def process_dataset(input_dir, output_dir, config_file):
    """Process dataset using CLI"""

    # Validate configuration first
    stdout, stderr = run_blur_suite_command([
        "config", "validate", config_file
    ])

    if stderr:
        print(f"Configuration issues: {stderr}")
        return False

    # Process dataset
    stdout, stderr = run_blur_suite_command([
        "process", "batch",
        input_dir, output_dir,
        "--config", config_file,
        "--workers", "8",
        "--progress-bar"
    ])

    print("Processing output:", stdout)
    if stderr:
        print("Warnings:", stderr)

    return True

# Usage
if __name__ == "__main__":
    success = process_dataset(
        "./input_images",
        "./output_dataset",
        "./dataset_config.json"
    )

    if success:
        print("✅ Dataset processing completed!")
```

### Shell Script Integration

```bash
#!/bin/bash
# process_with_cli.sh

# Function to process images with error handling
process_images() {
    local input_dir="$1"
    local output_dir="$2"
    local blur_type="$3"
    shift 3
    local params=("$@")

    echo "Processing $input_dir with $blur_type blur..."

    # Build parameter arguments
    local param_args=()
    for param in "${params[@]}"; do
        param_args+=("$param")
    done

    # Run processing
    blur-suite process directory "$input_dir" "$output_dir" \
        --blur-type "$blur_type" \
        "${param_args[@]}" \
        --workers 8 \
        --verbose

    if [[ $? -eq 0 ]]; then
        echo "✅ Processing completed successfully"
        return 0
    else
        echo "❌ Processing failed"
        return 1
    fi
}

# Example usage
process_images ./documents ./blurred_docs gaussian --kernel-size 7 --sigma 1.5
process_images ./photos ./blurred_photos motion --angle 45 --length 20
```

## Best Practices

### Configuration Management
1. **Validate configurations** before large processing runs
2. **Use descriptive names** for configuration files
3. **Version control** your configurations
4. **Document parameter choices** for reproducibility

### Performance Optimization
1. **Match worker count** to your CPU cores (2-4 workers per core)
2. **Use appropriate chunk sizes** based on memory availability
3. **Monitor system resources** during processing
4. **Enable GPU acceleration** when available

### Error Handling
1. **Use `--continue-on-error`** for large datasets
2. **Enable logging** for production workflows
3. **Validate inputs and outputs** at each stage
4. **Implement retry logic** for network-dependent operations

### Maintenance
1. **Keep the SDK updated** for bug fixes and performance improvements
2. **Monitor log files** for issues and performance trends
3. **Archive old datasets** and configurations
4. **Document custom workflows** and configurations

## Troubleshooting

### Common Issues

#### Command Not Found
```bash
# Ensure blur-suite is installed and in PATH
which blur-suite

# Add to PATH if necessary
export PATH=$PATH:~/.local/bin

# Reinstall if missing
pip install blur_suite[cli]
```

#### Permission Errors
```bash
# Check file permissions
ls -la input_directory/
ls -la output_directory/

# Fix permissions
chmod 755 input_directory/
chmod 755 output_directory/
```

#### Memory Issues
```bash
# Reduce memory usage
blur-suite process batch ./input ./output \
    --config config.json \
    --workers 2 \
    --chunk-size 5
```

#### Processing Errors
```bash
# Enable verbose output for debugging
blur-suite process batch ./input ./output \
    --config config.json \
    --verbose \
    --log-file error.log

# Check error log
cat error.log | grep -i error
```

### Getting Help

```bash
# Show general help
blur-suite --help

# Show command-specific help
blur-suite process --help
blur-suite config --help

# Show version information
blur-suite --version

# Show system information
blur-suite info system --all-details
```

## API Reference

For programmatic access to CLI functionality:

```python
from blur_suite.cli import BlurCLI

# Create CLI instance
cli = BlurCLI()

# Process images programmatically
result = cli.process_batch(
    input_dir="./input",
    output_dir="./output",
    config_file="config.json",
    workers=8
)

# Validate configuration
is_valid = cli.validate_config("config.json")

# Get system information
info = cli.get_system_info()
```

## Support and Resources

- 📖 **[API Reference: CLI](api_reference/cli.md)** - Complete API documentation
- 💡 **[Examples: Integration](examples/integration_example.py)** - Integration patterns
- 🛠️ **[Troubleshooting Guide](../troubleshooting.md)** - Common solutions
- 💬 **[FAQ](../faq.md)** - Frequently asked questions

---

*Need help?* Check the [Troubleshooting Guide](../troubleshooting.md) or explore the [Examples](../examples/) for more advanced usage patterns.