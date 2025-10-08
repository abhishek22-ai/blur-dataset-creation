# Blur Suite Interactive Configuration Tool

A comprehensive graphical user interface for configuring blur effects on document images with real-time preview and dataset generation capabilities.

## Overview

The Blur Suite Interactive Configuration Tool provides a professional GUI for:

- **Visual Blur Configuration**: Select from 6 different blur effect types with real-time parameter adjustment
- **Live Preview**: Side-by-side before/after comparison with synchronized zoom and pan
- **Quality Metrics**: Real-time display of PSNR, SSIM, processing time, and other metrics
- **Preset Management**: Save and load configuration presets for quick access
- **Dataset Export**: Generate configuration files for batch processing and dataset creation

## Features

### Blur Effect Types

1. **Gaussian Blur**: Convolution with Gaussian kernel
   - Kernel size (3-21)
   - Sigma X/Y (0.5-5.0)

2. **Motion Blur**: Directional motion simulation
   - Angle (0-180°)
   - Length (1-50 pixels)

3. **Defocus Blur**: Camera defocus simulation
   - Radius (1-20)
   - Strength (0.1-2.0)

4. **Average Blur**: Simple mean filtering
   - Kernel size (3-15)

5. **Bilateral Blur**: Edge-preserving smoothing
   - Diameter (5-25)
   - Sigma Color (10-100)
   - Sigma Space (10-100)

6. **No Blur**: Pass-through for testing

### User Interface

- **Professional Layout**: Clean, organized interface with proper sections
- **Responsive Design**: Works with different screen sizes
- **Keyboard Shortcuts**: Common operations accessible via shortcuts
- **Status Updates**: Real-time feedback on operations

### Image Handling

- **Batch Loading**: Load multiple images from directory (minimum 10 images)
- **Format Support**: PNG, JPEG, BMP, TIFF
- **Thumbnail Generation**: Quick preview of loaded images
- **Navigation**: Easy browsing through image collection

### Real-time Preview

- **Side-by-side Comparison**: Original vs blurred images
- **Multiple View Modes**: Side-by-side, overlay, difference
- **Zoom and Pan**: Detailed inspection capabilities
- **Synchronized Views**: Linked zoom/pan across views

### Quality Analysis

- **PSNR**: Peak Signal-to-Noise Ratio
- **SSIM**: Structural Similarity Index
- **MSE**: Mean Squared Error
- **Processing Time**: Performance metrics
- **Visual Indicators**: Color-coded quality assessment

## Installation

The interactive tool is included with the Blur Suite SDK:

```bash
# The tool is automatically available with the SDK
pip install blur-suite  # or from source
```

### Dependencies

- Python 3.7+
- Tkinter (usually included with Python)
- OpenCV (cv2)
- NumPy
- PIL (Pillow)

## Quick Start

```python
from blur_suite.interactive import BlurSuiteApp

# Create and run the application
app = BlurSuiteApp()
app.create_gui()
app.run()
```

## Usage Guide

### 1. Loading Images

1. Start the application
2. Press `Ctrl+O` or use File → Load Images
3. Select a directory containing at least 10 document images
4. Images will be validated and thumbnails generated

### 2. Configuring Blur Effects

1. **Select Blur Type**: Choose from the dropdown in the left panel
2. **Adjust Parameters**: Use sliders to modify effect parameters in real-time
3. **Preview Results**: View changes immediately in the comparison panel

### 3. Quality Assessment

- Monitor PSNR, SSIM, and other metrics in the right panel
- Green = Good quality, Yellow = Fair, Red = Poor
- Processing time shows performance impact

### 4. Saving Presets

1. Configure desired blur settings
2. Enter a name in the "Preset Name" field
3. Click "Save Current Settings"
4. Load presets anytime with the dropdown and "Load" button

### 5. Exporting Configurations

1. Configure all desired images
2. Press `Ctrl+S` or use File → Export Configuration
3. Choose filename and format (JSON recommended)
4. Generated file can be used for batch processing

## Keyboard Shortcuts

- `Ctrl+O`: Load Images
- `Ctrl+S`: Export Configuration
- `Ctrl+Q`: Quit Application
- `Ctrl+R`: Reset View
- `Ctrl+F`: Fit to Window
- `←/→`: Navigate Images
- `Ctrl+Plus/Minus`: Zoom In/Out

## Configuration Export

The tool generates comprehensive configuration files containing:

```json
{
  "metadata": {
    "export_timestamp": "2025-10-07T10:00:00Z",
    "version": "1.0.0",
    "total_images": 15
  },
  "global_settings": {
    "output_format": "png",
    "quality": 95,
    "parallel_processing": true
  },
  "image_configurations": {
    "image1.jpg": {
      "blur_type": "gaussian",
      "parameters": {
        "kernel_size": 7,
        "sigma_x": 1.5,
        "sigma_y": 1.5
      },
      "enabled": true
    }
  },
  "statistics": {
    "total_images": 15,
    "enabled_images": 15,
    "blur_types": {
      "gaussian": 10,
      "motion": 5
    }
  }
}
```

## Batch Processing

Use exported configurations with the batch processing script:

```python
from blur_suite.interactive.exporters import DatasetExporter

# Load configuration
exporter = DatasetExporter()
config = exporter.load_configuration("config.json")

# Generate batch script
script = exporter.create_batch_script(
    config_file="config.json",
    output_dir="blurred_images",
    script_type="python"
)

# Save and run script
with open("batch_process.py", "w") as f:
    f.write(script)
```

## Advanced Features

### Custom Blur Effects

The tool automatically detects and supports custom blur effects registered with the Blur Suite SDK plugin system.

### Performance Optimization

- Asynchronous image loading
- Blur computation caching
- Memory management for large datasets
- Progress indicators for long operations

### Error Handling

- Graceful handling of invalid images
- Clear error messages with recovery suggestions
- Logging for debugging purposes
- Validation of all inputs

## Troubleshooting

### Common Issues

1. **GUI doesn't start**: Ensure Tkinter is available (`python -c "import tkinter"`)

2. **Images don't load**: Check file formats and ensure minimum 10 images

3. **Blur preview slow**: Reduce image size or use simpler blur effects

4. **Export fails**: Check file permissions and disk space

### Performance Tips

- Load images in smaller batches (10-20 images)
- Use simpler blur effects for faster preview
- Close unused applications to free memory
- Export configurations for batch processing of large datasets

## API Reference

### BlurSuiteApp

Main application class coordinating all components.

```python
class BlurSuiteApp:
    def __init__(self)
    def create_gui(self) -> None
    def run(self) -> None
    def load_images(self) -> None
    def export_configuration(self) -> None
```

### Control Widgets

#### BlurSelector
```python
selector = BlurSelector(parent, app)
selector.set_blur_type("gaussian")
blur_type = selector.get_selected_blur_type()
```

#### ParameterSliders
```python
sliders = ParameterSliders(parent, app)
sliders.update_parameters(parameters)
sliders.set_parameters({"kernel_size": 7})
```

#### PresetManager
```python
presets = PresetManager(parent, app)
presets.save_preset("My Preset", config)
presets.load_preset("My Preset")
```

### Preview Components

#### ImageDisplay
```python
display = ImageDisplay(parent, app)
display.show_image(image, path)
display.fit_to_window()
```

#### ComparisonView
```python
comparison = ComparisonView(parent, app)
comparison.show_comparison(original, blurred, time_ms)
comparison.set_view_mode("overlay")
```

#### QualityMetrics
```python
metrics = QualityMetrics(parent, app)
metrics.update_metrics(original, processed, time_ms)
current_metrics = metrics.get_current_metrics()
```
