# Blur Suite Interactive Configuration Tool

A GUI application for configuring blur effects on document images with real-time preview and dataset generation capabilities.

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
2. **Motion Blur**: Directional motion simulation
3. **Defocus Blur**: Camera defocus simulation
4. **Average Blur**: Simple mean filtering
5. **Bilateral Blur**: Edge-preserving smoothing
6. **No Blur**: Pass-through for testing


### Real-time Preview

- **Side-by-side Comparison**: Original vs blurred images
- **Multiple View Modes**: Side-by-side, overlay, difference
- **Zoom and Pan**: Detailed inspection capabilities
- **Synchronized Views**: Linked zoom/pan across views


## Installation

The interactive tool is included with the Blur Suite SDK:

```bash
pip install blur-suite  # or from source
```

### Dependencies

- Python 3.9+
- Tkinter (usually included with Python)
- OpenCV (cv2)
- Numpy
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


## Troubleshooting

### Common Issues

1. **GUI doesn't start**: Ensure Tkinter is available (`python -c "import tkinter"`)

2. **Images don't load**: Check file formats and ensure minimum 10 images

3. **Blur preview slow**: Reduce image size or use simpler blur effects

4. **Export fails**: Check file permissions and disk space


