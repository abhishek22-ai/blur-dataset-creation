# Interactive Tool User Guide

The Blur Suite Interactive Tool provides a comprehensive graphical user interface for configuring and testing blur effects in real-time. This guide covers all aspects of using the interactive tool effectively.

## Overview

The interactive tool offers:
- **Real-time blur effect preview** with live parameter adjustment
- **Side-by-side comparison** of original and blurred images
- **Quality metrics** (PSNR, SSIM, processing time)
- **Configuration export** for batch processing workflows
- **Plugin management** and custom effect integration
- **Performance monitoring** and caching (v2.0.0)
- **Custom effect builder** integration (v2.0.0)
- **Advanced memory management** (v2.0.0)

## Launching the Tool

### Method 1: Python Script

```python
from blur_suite.interactive import BlurSuiteApp

# Create and launch the application
app = BlurSuiteApp()
app.create_gui()
app.run()
```

### Method 2: Command Line

```bash
python -c "from blur_suite.interactive import BlurSuiteApp; app = BlurSuiteApp(); app.create_gui(); app.run()"
```

### Method 3: Direct Module Execution

```bash
python -m blur_suite.interactive
```

## Main Interface

### Layout Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Menu Bar: File | Edit | View | Tools | Help               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┬─────────────────────────────────────────┐  │
│  │ Image List  │           Preview Area                   │  │
│  │             │  ┌─────────────┬─────────────┐           │  │
│  │ • img1.jpg  │  │  Original   │   Blurred   │           │  │
│  │ • img2.png  │  │   Image     │    Image    │           │  │
│  │ • img3.jpeg │  │             │             │           │  │
│  │             │  └─────────────┴─────────────┘           │  │
│  └─────────────┘                                         │  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │ Blur Type   │ Parameters  │  Quality    │  Actions    │  │
│  │ ▼          │ Panel       │  Metrics    │  Panel      │  │
│  │ Gaussian   ▼│ • Kernel: 5 │ • PSNR: 25.3│ • Apply    │  │
│  │ Motion     │ • Sigma: 1.0│ • SSIM: 0.89│ • Reset    │  │
│  │ Defocus    │ • Angle: 0° │ • Time: 15ms│ • Export   │  │
│  │ Average    │             │             │ • Save     │  │
│  │ Bilateral  │             │             │            │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Getting Started

### Step 1: Load Images

1. **Click File → Open** or press `Ctrl+O`
2. **Select one or more images** from the file dialog
3. **Images will appear** in the Image List panel
4. **Click on an image** to select it for processing

**Supported Formats:**
- PNG (recommended for transparency)
- JPEG/JPG (compressed, smaller files)
- TIFF (high quality, large files)
- BMP (uncompressed, large files)

### Step 2: Select Blur Type

Choose from the dropdown menu in the Blur Type panel:

| Blur Type | Description | Use Cases |
|-----------|-------------|-----------|
| **Gaussian** | Smooth, natural blur | General smoothing, noise reduction |
| **Motion** | Linear motion effect | Camera shake, object movement |
| **Defocus** | Camera focus simulation | Depth of field, bokeh effects |
| **Average** | Simple averaging filter | Basic smoothing, educational |
| **Bilateral** | Edge-preserving blur | Detail preservation, denoising |

### Step 3: Adjust Parameters

Each blur type has specific parameters that can be adjusted in real-time:

#### Gaussian Blur Parameters
- **Kernel Size**: 3-25 (odd numbers only)
- **Sigma X**: 0.1-10.0 (horizontal blur strength)
- **Sigma Y**: 0.1-10.0 (vertical blur strength)

#### Motion Blur Parameters
- **Angle**: 0-360° (direction of motion)
- **Length**: 1-100 pixels (motion distance)

#### Defocus Blur Parameters
- **Radius**: 1-50 pixels (blur radius)
- **Strength**: 0.1-5.0 (blur intensity)

#### Average Blur Parameters
- **Kernel Size**: 3-25 (odd numbers only)

#### Bilateral Blur Parameters
- **Diameter**: 5-25 (filter diameter)
- **Sigma Color**: 10-150 (color space standard deviation)
- **Sigma Space**: 10-150 (coordinate space standard deviation)

### Step 4: Preview Results

- **Real-time preview** updates as you adjust parameters
- **Side-by-side comparison** shows original vs blurred
- **Zoom controls** available for detailed inspection
- **Pan tool** for navigating large images

## Quality Metrics

The Quality Metrics panel displays real-time information:

### PSNR (Peak Signal-to-Noise Ratio)
- **Range**: 20-50 dB (higher is better)
- **Interpretation**:
  - > 30 dB: Good quality
  - 20-30 dB: Acceptable quality
  - < 20 dB: Poor quality

### SSIM (Structural Similarity Index)
- **Range**: 0.0-1.0 (higher is better)
- **Interpretation**:
  - > 0.9: Very similar
  - 0.7-0.9: Good similarity
  - < 0.7: Poor similarity

### Processing Time
- **Real-time measurement** of blur application
- **Helps optimize** parameter choices
- **Varies by image size** and complexity

## Advanced Features

### Batch Configuration

Apply the same blur settings to multiple images:

1. **Load multiple images** into the Image List
2. **Configure blur parameters** for the first image
3. **Click Tools → Apply to All**
4. **Review results** for each image
5. **Export batch configuration**

### Configuration Management

#### Save Configuration
```python
# Export current settings for batch processing
app.export_configuration("my_blur_config.json")
```

#### Load Configuration
```python
# Load previously saved settings
app.load_configuration("my_blur_config.json")
```

### Plugin Integration

The interactive tool supports custom blur plugins:

1. **Install custom plugins** in the plugins directory
2. **Restart the application** to load new plugins
3. **Custom blur types** appear in the Blur Type dropdown
4. **Plugin parameters** are automatically generated

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open image(s) |
| `Ctrl+S` | Save blurred image |
| `Ctrl+E` | Export configuration |
| `Ctrl+I` | Import configuration |
| `Ctrl+Z` | Undo last parameter change |
| `Ctrl+Y` | Redo last parameter change |
| `Ctrl+R` | Reset all parameters |
| `Ctrl+A` | Select all images |
| `Ctrl+D` | Deselect all images |
| `F11` | Toggle fullscreen |
| `Ctrl+Q` | Quit application |

## Workflow Examples

### Example 1: Document Blur Analysis

1. **Load document images** (Ctrl+O)
2. **Select Gaussian blur** for general analysis
3. **Adjust kernel size** to simulate different blur levels
4. **Record PSNR/SSIM values** for each setting
5. **Export configurations** for batch processing

### Example 2: Motion Blur Simulation

1. **Load action shots** or moving objects
2. **Choose Motion blur** type
3. **Set appropriate angle** (0-360°)
4. **Adjust length** (1-100 pixels)
5. **Compare with actual motion** in original image

### Example 3: Artistic Effects

1. **Load portrait or artistic images**
2. **Experiment with Defocus blur** for bokeh effects
3. **Use Bilateral blur** for edge preservation
4. **Fine-tune parameters** for desired artistic effect
5. **Save results** for further processing

## Performance Optimization

### For Large Images

1. **Enable image tiling** for memory efficiency
2. **Reduce preview quality** during parameter adjustment
3. **Use smaller kernel sizes** initially
4. **Batch process** similar images together

### For Many Images

1. **Use batch configuration** feature
2. **Export settings** and use dataset creation module
3. **Process in chunks** to manage memory usage
4. **Monitor system resources** during processing

## Troubleshooting

### Common Issues

#### GUI Doesn't Start
```bash
# Install GUI dependencies
pip install pyqt5 pyqtwebengine

# On Linux
sudo apt install qt5-default pyqt5-dev
```

#### Images Don't Load
- **Check file formats** (PNG, JPEG, TIFF, BMP supported)
- **Verify file paths** and permissions
- **Check available memory** for large images
- **Convert to supported format** if necessary

#### Poor Performance
- **Reduce image resolution** for preview
- **Close other applications** to free memory
- **Use SSD storage** for faster I/O
- **Enable GPU acceleration** if available

#### Incorrect Preview
- **Check parameter ranges** for selected blur type
- **Reset parameters** (Ctrl+R) and start over
- **Verify image integrity** with another viewer
- **Update graphics drivers** if using GPU acceleration

## Integration with Other Tools

### Export to Dataset Creation

1. **Configure desired blur settings** in interactive tool
2. **Export configuration** (Ctrl+E)
3. **Use exported JSON** with dataset creation module:

```python
from blur_suite.dataset import DatasetCreator

# Load configuration from interactive tool
creator = DatasetCreator("./output_dataset")
success = creator.create_from_config("interactive_config.json")
```

### Import from Dataset Creation

1. **Create configuration** using dataset creation module
2. **Export configuration file**
3. **Import into interactive tool** for testing and refinement

### Command Line Integration

```bash
# Export configuration for scripting
python -c "
from blur_suite.interactive import BlurSuiteApp
app = BlurSuiteApp()
app.load_image('input.jpg')
app.set_blur_type('gaussian')
app.set_parameters(kernel_size=7, sigma_x=1.5)
app.export_configuration('script_config.json')
"
```

## Best Practices

### Workflow Efficiency

1. **Start with small test images** to verify settings
2. **Use consistent parameter ranges** across similar images
3. **Save configurations** for reproducible results
4. **Document parameter choices** for future reference

### Quality Assurance

1. **Compare multiple blur types** for each image
2. **Record quality metrics** for analysis
3. **Validate results** with multiple observers
4. **Test edge cases** (very small/large parameters)

### Performance Management

1. **Monitor memory usage** with large images
2. **Use appropriate preview sizes**
3. **Batch similar operations** together
4. **Save work regularly** to prevent data loss

## Advanced Configuration

### Custom UI Themes

The interactive tool supports custom themes:

```python
# Apply dark theme
app = BlurSuiteApp()
app.set_theme("dark")

# Available themes: "light", "dark", "blue", "green"
```

### Custom Parameter Ranges

Extend default parameter ranges for specific use cases:

```python
# Extend Gaussian kernel size range
app = BlurSuiteApp()
app.extend_parameter_range("gaussian", "kernel_size", min_val=1, max_val=51)
```

## API Reference

For programmatic access to interactive tool features:

```python
from blur_suite.interactive import BlurSuiteApp

app = BlurSuiteApp()

# Image management
app.load_image("path/to/image.jpg")
app.load_images(["img1.jpg", "img2.png"])

# Blur configuration
app.set_blur_type("gaussian")
app.set_parameters(kernel_size=7, sigma_x=1.5, sigma_y=1.5)

# Quality assessment
metrics = app.get_quality_metrics()
print(f"PSNR: {metrics['psnr']}, SSIM: {metrics['ssim']}")

# Export functionality
app.export_configuration("config.json")
app.save_blurred_image("output.png")
```

## Support and Resources

- 📖 **[API Reference: Interactive](api_reference/interactive.md)** - Complete API documentation
- 💡 **[Examples: Integration](examples/integration_example.py)** - Integration patterns
- 🛠️ **[Troubleshooting Guide](../troubleshooting.md)** - Common solutions
- 💬 **[FAQ](../faq.md)** - Frequently asked questions

---

*Need help?* Check the [Troubleshooting Guide](../troubleshooting.md) or explore the [Examples](../examples/) for more advanced usage patterns.