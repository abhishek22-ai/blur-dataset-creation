# Quick Start Tutorial

Get started with Blur Suite SDK v2.0.0 in just 5 minutes! This guide will walk you through the basic usage patterns and help you create your first blur effects with the enhanced performance and production features.

## Prerequisites

- Python 3.7+ installed
- Blur Suite SDK v2.0.0 installed (see [Installation Guide](installation.md))
- Basic familiarity with Python and image processing concepts

## 5-Minute Getting Started

### Step 1: Basic Blur Effect (1 minute)

Let's start with the simplest possible blur effect:

```python
import blur_suite as bs
import numpy as np

# Create a sample image (you can load your own image instead)
image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

# Create a blur factory and apply Gaussian blur
factory = bs.BlurFactory()
gaussian_blur = factory.create_effect("gaussian", kernel_size=7, sigma_x=1.5)

# Apply the blur effect
result = gaussian_blur.apply(image)

# Get the blurred image
blurred_image = result.result_image
print(f"✅ Success! Blurred image shape: {blurred_image.shape}")
```

**Expected output:**
```
✅ Success! Blurred image shape: (100, 100, 3)
```

### Step 2: Try Different Blur Types (2 minutes)

Experiment with different blur algorithms:

```python
import blur_suite as bs
import numpy as np

# Sample image
image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)

# Create blur factory
factory = bs.BlurFactory()

# Try different blur effects
blur_configs = [
    ("gaussian", {"kernel_size": 9, "sigma_x": 2.0, "sigma_y": 2.0}),
    ("motion", {"angle": 45.0, "length": 15}),
    ("defocus", {"radius": 8, "strength": 1.2}),
    ("average", {"kernel_size": 7}),
    ("bilateral", {"diameter": 9, "sigma_color": 75.0, "sigma_space": 75.0})
]

# Apply each blur effect
results = {}
for blur_type, params in blur_configs:
    blur_effect = factory.create_effect(blur_type, **params)
    result = blur_effect.apply(image)
    results[blur_type] = result.result_image
    print(f"✅ Applied {blur_type} blur")

# Compare results
print(f"\n📊 Processed {len(results)} different blur effects!")
```

### Step 3: Interactive Tool (1 minute)

Launch the interactive configuration tool:

```python
from blur_suite.interactive import BlurSuiteApp

# Create and run the interactive application
app = BlurSuiteApp()
app.create_gui()
app.run()
```

The interactive tool provides:
- **Image loading** with drag-and-drop support
- **Real-time parameter adjustment** with live preview
- **Side-by-side comparison** (original vs blurred)
- **Quality metrics** (PSNR, SSIM, processing time)
- **Configuration export** for batch processing

**Keyboard shortcuts:**
- `Ctrl+O` - Load image
- `Ctrl+S` - Save/export configuration
- `Ctrl+Z` - Undo last change
- `Ctrl+Y` - Redo last change

### Step 4: Advanced Features (v2.0.0) (1 minute)

Experience the new v2.0.0 capabilities with performance monitoring and custom effects:

```python
import blur_suite as bs
import numpy as np

# Initialize performance monitoring (NEW in v2.0.0)
performance_monitor = bs.PerformanceMonitor()
performance_monitor.start_monitoring()

# Setup structured logging (NEW in v2.0.0)
logger = bs.StructuredLogger("quick_start")
logger.set_context(component="tutorial", version="2.0.0")

# Configure caching and memory management (NEW in v2.0.0)
cache_manager = bs.CacheManager(max_memory_mb=100.0)
memory_manager = bs.MemoryManager(max_memory_percent=75.0)

# Create custom effect with caching (NEW in v2.0.0)
@cache_manager.cached_compute
def process_image_with_custom_effect(image, effect_params):
    custom_effect = (
        bs.CustomEffectBuilder("advanced_enhancement")
        .add_blur_step(kernel_size=effect_params['blur_size'])
        .add_sharpen_step(intensity=effect_params['sharpen'])
        .add_enhance_step(enhancement_type="contrast")
        .enable_caching(True)
        .build()
    )
    return custom_effect.apply(image)

# Process images with monitoring and error handling (NEW in v2.0.0)
import time
from blur_suite.monitoring import timing

start_time = time.time()
for i in range(5):
    try:
        # Create sample image
        image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)

        # Process with custom effect
        processed = process_image_with_custom_effect(image, {'blur_size': 7, 'sharpen': 0.8})
        logger.info("Image processed", image_index=i, shape=processed.result_image.shape)

    except Exception as e:
        logger.error("Failed to process image", image_index=i, error=str(e))

processing_time = time.time() - start_time
logger.info("Batch processing completed", duration=processing_time, images_processed=5)

# Generate performance report (NEW in v2.0.0)
report_generator = bs.ReportGenerator()
report = report_generator.generate_system_report()
report_generator.save_report("performance_report.md")

print("✅ Advanced v2.0.0 features demonstrated!")
```

### Step 5: Simple Dataset Creation (1 minute)

Create a basic dataset configuration:

```python
from blur_suite.dataset import DatasetCreator
import json

# Initialize dataset creator
creator = DatasetCreator("./my_first_dataset")

# Create sample configuration
config = {
    "metadata": {
        "created_by": "Quick Start Tutorial",
        "creation_date": "2024-10-08 12:00:00",
        "version": "2.0.0"
    },
    "global_settings": {
        "output_format": "png",
        "quality": 95,
        "parallel_processing": True,
        "max_workers": 4
    },
    "image_configurations": {
        "sample_image.jpg": {
            "blur_type": "gaussian",
            "parameters": {
                "kernel_size": 7,
                "sigma_x": 1.5,
                "sigma_y": 1.5
            },
            "enabled": True
        }
    }
}

# Save configuration
with open("quick_config.json", "w") as f:
    json.dump(config, f, indent=2)

print("✅ Configuration saved to quick_config.json")
```

## Common Next Steps

### Load Your Own Images

Replace the sample image with your own:

```python
from PIL import Image
import numpy as np

# Load your image
image = Image.open("your_image.jpg")
image_array = np.array(image)

# Apply blur effect
factory = bs.BlurFactory()
blur_effect = factory.create_effect("gaussian", kernel_size=5, sigma_x=1.0)
result = blur_effect.apply(image_array)

# Save result
result_image = Image.fromarray(result.result_image)
result_image.save("blurred_image.png")
```

### Batch Process Multiple Images

```python
import os
from blur_suite.dataset import DatasetCreator

# Process multiple images
image_folder = "./input_images"
output_folder = "./blurred_dataset"

creator = DatasetCreator(output_folder)

# Create configuration for all images in folder
image_configs = {}
for filename in os.listdir(image_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        image_configs[os.path.join(image_folder, filename)] = {
            "blur_type": "motion",
            "parameters": {"angle": 30.0, "length": 20},
            "enabled": True
        }

# Create dataset
config = {
    "metadata": {"created_by": "Batch Processor"},
    "global_settings": {"parallel_processing": True, "max_workers": 4},
    "image_configurations": image_configs
}

success = creator.create_from_config_dict(config)
print(f"✅ Dataset creation {'succeeded' if success else 'failed'}!")
```

### Custom Blur Parameters

Experiment with different parameter combinations:

```python
# Fine-tune blur effects
configurations = [
    # Light blur
    {"kernel_size": 3, "sigma_x": 0.5, "sigma_y": 0.5},

    # Medium blur
    {"kernel_size": 7, "sigma_x": 1.5, "sigma_y": 1.5},

    # Strong blur
    {"kernel_size": 15, "sigma_x": 3.0, "sigma_y": 3.0},

    # Very strong blur
    {"kernel_size": 25, "sigma_x": 5.0, "sigma_y": 5.0}
]

factory = bs.BlurFactory()
for i, params in enumerate(configurations):
    blur_effect = factory.create_effect("gaussian", **params)
    result = blur_effect.apply(your_image)
    # Save each result with different filename
```

## Quick Reference

### Blur Effect Types

| Type | Key Parameters | Description |
|------|----------------|-------------|
| `gaussian` | `kernel_size`, `sigma_x`, `sigma_y` | Smooth, natural blur |
| `motion` | `angle`, `length` | Motion simulation |
| `defocus` | `radius`, `strength` | Camera defocus effect |
| `average` | `kernel_size` | Simple averaging |
| `bilateral` | `diameter`, `sigma_color`, `sigma_space` | Edge-preserving blur |

### Common Patterns

```python
# Pattern 1: Quick blur application
factory = bs.BlurFactory()
blur = factory.create_effect("gaussian", kernel_size=5, sigma_x=1.0)
result = blur.apply(image)

# Pattern 2: Batch configuration
config = {
    "global_settings": {"parallel_processing": True},
    "image_configurations": {
        "image1.jpg": {"blur_type": "motion", "parameters": {...}},
        "image2.jpg": {"blur_type": "gaussian", "parameters": {...}}
    }
}

# Pattern 3: Interactive workflow
app = BlurSuiteApp()
# Configure in GUI, then export configuration for batch processing
```

## Troubleshooting Quick Tips

### Issue: Import Error
```bash
pip install blur-suite  # Make sure it's installed
```

### Issue: No Images Found (Dataset Creation)
```python
# Check your image paths
from blur_suite.dataset import PathManager
valid_images = PathManager.find_images("./your_image_folder")
print(f"Found {len(valid_images)} valid images")
```

### Issue: GUI Not Opening
```bash
# Install GUI dependencies
pip install pyqt5 pyqtwebengine
```

## What's Next?

🎉 **Congratulations!** You've completed the 5-minute quick start. Here are some suggested next steps:

### For Beginners
- 📖 **[User Guide: Interactive Tool](user_guide/interactive_tool.md)** - Master the GUI
- 💡 **[Examples: Basic Usage](examples/basic_usage.py)** - Learn more patterns
- 📚 **[API Reference: Core Blur](api_reference/core_blur.md)** - Understand the blur algorithms

### For Advanced Users
- 🔧 **[User Guide: Dataset Creation](user_guide/dataset_creation.md)** - Batch processing workflows
- 💡 **[Examples: Advanced Usage](examples/advanced_usage.py)** - Complex scenarios
- 🔌 **[Examples: Custom Blur Plugin](examples/custom_blur.py)** - Extend the SDK

### For Developers
- 🛠️ **[Contributing Guidelines](contributing.md)** - Join the development
- 🧪 **[Testing Guide](troubleshooting.md#testing)** - Run the test suite
- 📊 **[Performance Guide](troubleshooting.md#performance)** - Optimize for your use case

## Quick Commands Reference

```bash
# Install the SDK
pip install blur-suite

# Run interactive tool
python -c "from blur_suite.interactive import BlurSuiteApp; app = BlurSuiteApp(); app.create_gui(); app.run()"

# Quick blur test
python -c "import blur_suite as bs; import numpy as np; img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8); factory = bs.BlurFactory(); blur = factory.create_effect('gaussian', kernel_size=5, sigma_x=1.0); result = blur.apply(img); print('Success!')"

# Create sample dataset
python -c "from blur_suite.dataset import DatasetCreator; creator = DatasetCreator('./test_dataset'); print('Ready for dataset creation!')"
```

---

**Ready for more?** 🚀 Check out the detailed [User Guides](user_guide/) or dive into the [API Reference](api_reference/) for comprehensive documentation.