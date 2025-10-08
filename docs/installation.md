# Installation Guide

## Installation Methods

### Method 1: PyPI Installation (Recommended)

The easiest way to install Blur Suite SDK is using pip from PyPI:

```bash
pip install blur-suite
```

#### Upgrade to Latest Version

```bash
pip install --upgrade blur-suite
```

#### Install Specific Version

```bash
pip install blur-suite==1.0.0
```

### Method 2: Development Installation

For development or if you want to access the latest features:

```bash
git clone https://github.com/blur-suite/blur-suite-sdk.git
cd blur-suite-sdk
pip install -e .
```

### Method 3: Installation from Source

```bash
git clone https://github.com/blur-suite/blur-suite-sdk.git
cd blur-suite-sdk
python setup.py install
```

## Dependencies

### Core Dependencies

The SDK automatically installs the following core dependencies:

- **numpy** (>=1.21.0) - Array operations and mathematical functions
- **pillow** (>=8.0.0) - Image format support and basic image processing
- **scipy** (>=1.7.0) - Scientific computing (signal processing)
- **pyyaml** (>=5.4.0) - Configuration file parsing
- **tqdm** (>=4.62.0) - Progress bars for long operations

### Optional Dependencies

Install additional features based on your needs:

#### GUI Components (Interactive Tool)

```bash
pip install pyqt5 pyqtwebengine
```

#### Enhanced Image Processing

```bash
pip install opencv-python scikit-image scipy
```

#### GPU Acceleration (CUDA)

```bash
pip install cupy-cuda12x  # For CUDA 12.x
# or
pip install cupy-cuda11x  # For CUDA 11.x
```

#### Production Features (v2.0.0)

```bash
pip install torch torchvision  # For PyTorch-based optimizations
pip install aiofiles aiohttp  # For async I/O operations
pip install structlog python-json-logger  # For enhanced logging
```

#### Development and Testing

```bash
pip install pytest pytest-cov black flake8 mypy
```

#### Documentation Building

```bash
pip install sphinx sphinx-rtd-theme myst-parser
```

## Platform-Specific Instructions

### Linux (Ubuntu/Debian)

#### Install Python and pip

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Install system dependencies for GUI

```bash
sudo apt install qt5-default pyqt5-dev pyqt5-dev-tools
```

#### Install OpenCV dependencies (optional)

```bash
sudo apt install libopencv-dev python3-opencv
```

### macOS

#### Using Homebrew

```bash
brew install python@3.9
brew install opencv  # Optional, for enhanced image processing
```

#### Using conda (Anaconda/Miniconda)

```bash
conda install python=3.9
conda install -c conda-forge opencv pyqt
```

### Windows

#### Using Chocolatey

```bash
choco install python visualstudio2019buildtools
```

#### Using conda

```bash
conda install python=3.9
conda install -c conda-forge opencv pyqt
```

## Virtual Environment Setup

### Using venv (Recommended)

```bash
# Create virtual environment
python -m venv blur-suite-env

# Activate environment
# On Linux/macOS:
source blur-suite-env/bin/activate
# On Windows:
blur-suite-env\Scripts\activate

# Install Blur Suite SDK
pip install blur-suite
```

### Using conda

```bash
# Create conda environment
conda create -n blur-suite python=3.9
conda activate blur-suite

# Install dependencies
conda install numpy pillow scipy pyyaml tqdm

# Install Blur Suite SDK
pip install blur-suite
```

## Verification

After installation, verify that the SDK is working correctly:

### Basic Import Test

```python
import blur_suite as bs
print(f"Blur Suite SDK version: {bs.__version__}")

# Test basic functionality
import numpy as np
image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
factory = bs.BlurFactory()
gaussian = factory.create_effect("gaussian", kernel_size=5, sigma_x=1.0)
result = gaussian.apply(image)
print(f"Blur applied successfully! Result shape: {result.result_image.shape}")
```

### Interactive Tool Test

```python
from blur_suite.interactive import BlurSuiteApp
app = BlurSuiteApp()
print("Interactive tool components loaded successfully!")
```

### Dataset Creation Test

```python
from blur_suite.dataset import DatasetCreator
creator = DatasetCreator("./test_output")
print("Dataset creation module loaded successfully!")
```

## Troubleshooting

### Common Installation Issues

#### Issue: ImportError - No module named 'blur_suite'

**Solution**: Ensure the package is installed correctly:
```bash
pip list | grep blur-suite
```

If not found, reinstall:
```bash
pip uninstall blur-suite
pip install blur-suite
```

#### Issue: ImportError - Qt related errors (GUI components)

**Solution**: Install PyQt5 dependencies:
```bash
pip install pyqt5 pyqtwebengine
```

On Linux:
```bash
sudo apt install qt5-default pyqt5-dev
```

#### Issue: Performance Issues with Large Images

**Solution**: Install OpenCV for optimized image processing:
```bash
pip install opencv-python
```

#### Issue: CUDA/GPU Acceleration Not Working

**Solution**: Verify CUDA installation:
```bash
nvidia-smi
```

Install CuPy for CUDA support:
```bash
pip install cupy-cuda12x
```

### Dependency Conflicts

If you encounter dependency conflicts, use virtual environments or conda environments to isolate the installation.

#### Creating Isolated Environment

```bash
# Create new conda environment
conda create -n blur-suite-clean python=3.9
conda activate blur-suite-clean

# Install only required dependencies
conda install numpy pillow scipy pyyaml tqdm

# Install Blur Suite SDK
pip install blur-suite
```

### Performance Optimization

#### Memory Issues

If you experience memory issues with large datasets:

1. **Reduce batch sizes** in dataset creation configurations
2. **Use chunked processing** for very large images
3. **Enable memory mapping** for large file operations

```python
# Example: Configure batch processing for memory efficiency
from blur_suite.dataset import BatchConfig

batch_config = BatchConfig(
    max_workers=2,  # Reduce workers
    chunk_size=10,  # Smaller chunks
    max_memory_gb=4.0  # Memory limit
)
```

#### Processing Speed

To improve processing speed:

1. **Enable parallel processing** where available
2. **Use GPU acceleration** if supported
3. **Optimize image formats** (JPEG for smaller files, PNG for lossless)

```python
# Example: Enable GPU acceleration
import os
os.environ['BLUR_SUITE_USE_GPU'] = '1'

# Configure for parallel processing
config = {
    "global_settings": {
        "parallel_processing": True,
        "max_workers": 8  # Adjust based on CPU cores
    }
}
```

## Advanced Installation

### Custom Installation Paths

```bash
# Install to specific directory
pip install --prefix=/custom/path blur-suite

# Add to PYTHONPATH
export PYTHONPATH=/custom/path/lib/python3.9/site-packages:$PYTHONPATH
```

### Development Setup

For contributors and developers:

```bash
git clone https://github.com/blur-suite/blur-suite-sdk.git
cd blur-suite-sdk

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Build documentation
sphinx-build docs/ docs/_build/html
```

### Docker Installation

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    qt5-default \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Blur Suite SDK
RUN pip install blur-suite

# Copy application code
COPY . .

CMD ["python", "your_app.py"]
```

## Post-Installation Configuration

### Environment Variables

Configure the SDK behavior using environment variables:

```bash
# Enable GPU acceleration
export BLUR_SUITE_USE_GPU=1

# Set number of parallel workers
export BLUR_SUITE_MAX_WORKERS=8

# Enable debug logging
export BLUR_SUITE_DEBUG=1

# Set temporary directory
export BLUR_SUITE_TEMP_DIR=/tmp/blur_suite
```

### Configuration Files

Create configuration files for persistent settings:

```python
# blur_suite_config.yaml
gpu_acceleration: true
max_workers: 8
temp_directory: "/tmp/blur_suite"
log_level: "INFO"
default_output_format: "PNG"
```

## Getting Help

If you encounter issues during installation:

1. **Check the troubleshooting section** above
2. **Verify system requirements** are met
3. **Check Python version compatibility**
4. **Review dependency versions**
5. **Search existing issues** on GitHub
6. **Create new issue** with detailed error information

## Next Steps

After successful installation:

1. 📖 **[Read the Quick Start Guide](quickstart.md)** - Get started in 5 minutes
2. 🎛️ **[Try the Interactive Tool](user_guide/interactive_tool.md)** - Explore blur effects
3. 📚 **[Browse the Examples](examples/)** - See working code samples
4. 🔌 **[Check the API Reference](api_reference/core_blur.md)** - Deep dive into functionality

---
