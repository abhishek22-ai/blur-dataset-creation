# Interactive API Reference

This document provides comprehensive API documentation for the Blur Suite SDK interactive module, including GUI components, real-time preview, and configuration management.

## Overview

The interactive module provides:
- **Graphical user interface** for blur effect configuration
- **Real-time preview** with live parameter adjustment
- **Side-by-side comparison** of original and blurred images
- **Quality metrics** calculation and display
- **Configuration export/import** functionality

## Module Structure

```
blur_suite/interactive/
├── __init__.py              # Module exports
├── app.py                  # Main application class
├── gui/
│   ├── __init__.py         # GUI components
│   ├── main_window.py      # Main window implementation
│   ├── preview_widget.py   # Image preview widget
│   ├── parameter_panel.py  # Parameter adjustment panel
│   └── quality_display.py  # Quality metrics display
├── exporters/
│   ├── __init__.py         # Export functionality
│   ├── config_exporter.py  # Configuration export
│   └── dataset_exporter.py # Dataset configuration export
└── utils/
    ├── __init__.py         # Utility functions
    └── image_utils.py      # Image processing utilities
```

## Quick Start

```python
from blur_suite.interactive import BlurSuiteApp

# Create and run interactive application
app = BlurSuiteApp()
app.create_gui()
app.run()
```

## Main Classes

### BlurSuiteApp

Main application class for the interactive tool.

```python
class BlurSuiteApp:
    """Main application class for Blur Suite Interactive Tool."""

    def __init__(self, config_path: str = None):
        """Initialize interactive application.

        Args:
            config_path: Path to configuration file to load
        """
        self.config_path = config_path
        self.image_path: Optional[str] = None
        self.current_image: Optional[np.ndarray] = None
        self.current_blur_type: Optional[BlurType] = None
        self.current_parameters: Dict[str, Any] = {}
        self.blur_factory = BlurFactory()
        self.quality_metrics: Dict[str, float] = {}

    def create_gui(self) -> None:
        """Create and initialize the graphical user interface."""
        self.main_window = MainWindow()
        self.preview_widget = PreviewWidget()
        self.parameter_panel = ParameterPanel()
        self.quality_display = QualityDisplay()

        # Connect signals and slots
        self._connect_components()

    def run(self) -> None:
        """Run the interactive application."""
        self.main_window.show()
        self._start_event_loop()

    def load_image(self, image_path: str) -> bool:
        """Load image for processing.

        Args:
            image_path: Path to image file

        Returns:
            True if image loaded successfully
        """
        try:
            # Load image using PIL or OpenCV
            image = self._load_image_file(image_path)

            # Validate image format and size
            if not self._validate_image(image):
                return False

            self.image_path = image_path
            self.current_image = image

            # Update preview
            self.preview_widget.set_original_image(image)

            return True

        except Exception as e:
            print(f"Error loading image: {e}")
            return False

    def set_blur_type(self, blur_type: Union[str, BlurType]) -> None:
        """Set current blur effect type.

        Args:
            blur_type: Blur effect type to use
        """
        if isinstance(blur_type, str):
            blur_type = BlurType.from_string(blur_type)

        self.current_blur_type = blur_type

        # Update parameter panel with new blur type
        self.parameter_panel.update_blur_type(blur_type)

        # Apply blur with current parameters
        self._apply_current_blur()

    def set_parameters(self, **kwargs) -> None:
        """Set blur effect parameters.

        Args:
            **kwargs: Parameter name-value pairs
        """
        self.current_parameters.update(kwargs)

        # Validate parameters
        if not self._validate_parameters():
            return

        # Apply blur with new parameters
        self._apply_current_blur()

    def get_quality_metrics(self) -> Dict[str, float]:
        """Get current quality metrics.

        Returns:
            Dictionary containing PSNR, SSIM, and processing time
        """
        return self.quality_metrics.copy()

    def export_configuration(self, output_path: str) -> bool:
        """Export current configuration to file.

        Args:
            output_path: Output configuration file path

        Returns:
            True if export successful
        """
        config = self._create_configuration_dict()

        try:
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False

    def _apply_current_blur(self) -> None:
        """Apply current blur effect to loaded image."""
        if self.current_image is None or self.current_blur_type is None:
            return

        try:
            # Create blur effect
            effect = self.blur_factory.create_effect(
                self.current_blur_type,
                **self.current_parameters
            )

            # Apply blur
            start_time = time.time()
            result = effect.apply(self.current_image)
            processing_time = (time.time() - start_time) * 1000

            # Update preview
            self.preview_widget.set_blurred_image(result.result_image)

            # Calculate quality metrics
            self.quality_metrics = result.get_quality_metrics()
            self.quality_metrics['processing_time_ms'] = processing_time

            # Update quality display
            self.quality_display.update_metrics(self.quality_metrics)

        except Exception as e:
            print(f"Error applying blur: {e}")
```

## GUI Components

### MainWindow

Main application window implementation.

```python
class MainWindow:
    """Main application window."""

    def __init__(self):
        """Initialize main window."""
        self.window = None
        self.menu_bar = None
        self.status_bar = None

    def create_window(self) -> None:
        """Create the main window."""
        self.window = QMainWindow()
        self.window.setWindowTitle("Blur Suite Interactive Tool")
        self.window.setMinimumSize(1200, 800)

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

    def _create_menu_bar(self) -> None:
        """Create application menu bar."""
        menubar = self.window.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        self._add_file_menu_actions(file_menu)

        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        self._add_edit_menu_actions(edit_menu)

        # View menu
        view_menu = menubar.addMenu('View')
        self._add_view_menu_actions(view_menu)

        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        self._add_tools_menu_actions(tools_menu)

        # Help menu
        help_menu = menubar.addMenu('Help')
        self._add_help_menu_actions(help_menu)

    def show(self) -> None:
        """Show the main window."""
        self.window.show()
```

### PreviewWidget

Widget for displaying original and blurred images side-by-side.

```python
class PreviewWidget:
    """Widget for image preview and comparison."""

    def __init__(self):
        """Initialize preview widget."""
        self.original_label = None
        self.blurred_label = None
        self.splitter = None
        self.zoom_factor = 1.0

    def set_original_image(self, image: np.ndarray) -> None:
        """Set original image for display.

        Args:
            image: Original image as numpy array
        """
        # Convert numpy array to QPixmap for display
        pixmap = self._numpy_to_pixmap(image)
        self.original_label.setPixmap(pixmap)

    def set_blurred_image(self, image: np.ndarray) -> None:
        """Set blurred image for display.

        Args:
            image: Blurred image as numpy array
        """
        pixmap = self._numpy_to_pixmap(image)
        self.blurred_label.setPixmap(pixmap)

    def set_zoom(self, factor: float) -> None:
        """Set zoom factor for preview.

        Args:
            factor: Zoom factor (0.1-5.0)
        """
        self.zoom_factor = max(0.1, min(5.0, factor))

        # Update display with new zoom
        if self.current_image is not None:
            self.set_original_image(self.current_image)
            self.set_blurred_image(self.current_blurred_image)

    def _numpy_to_pixmap(self, image: np.ndarray) -> QPixmap:
        """Convert numpy array to QPixmap for display.

        Args:
            image: Image as numpy array

        Returns:
            QPixmap for Qt display
        """
        # Convert RGB to BGR for OpenCV if needed
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Create QImage from numpy array
        height, width = image.shape[:2]
        bytes_per_line = 3 * width

        q_image = QImage(
            image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        )

        # Scale according to zoom factor
        if self.zoom_factor != 1.0:
            new_width = int(width * self.zoom_factor)
            new_height = int(height * self.zoom_factor)
            q_image = q_image.scaled(new_width, new_height, Qt.KeepAspectRatio)

        return QPixmap.fromImage(q_image)
```

### ParameterPanel

Panel for adjusting blur effect parameters.

```python
class ParameterPanel:
    """Panel for blur parameter adjustment."""

    def __init__(self):
        """Initialize parameter panel."""
        self.blur_type_combo = None
        self.parameter_widgets: Dict[str, QWidget] = {}
        self.current_blur_type = None

    def update_blur_type(self, blur_type: BlurType) -> None:
        """Update panel for new blur type.

        Args:
            blur_type: New blur effect type
        """
        self.current_blur_type = blur_type

        # Clear existing parameter widgets
        self._clear_parameter_widgets()

        # Create parameter widgets for new blur type
        self._create_parameter_widgets(blur_type)

        # Update layout
        self._update_layout()

    def _create_parameter_widgets(self, blur_type: BlurType) -> None:
        """Create parameter input widgets for blur type.

        Args:
            blur_type: Blur effect type
        """
        # Get parameter definitions for blur type
        param_defs = self._get_parameter_definitions(blur_type)

        for param_def in param_defs:
            # Create appropriate widget based on parameter type
            if param_def.param_type in [int, float]:
                widget = self._create_numeric_widget(param_def)
            elif param_def.param_type == bool:
                widget = self._create_boolean_widget(param_def)
            elif param_def.param_type == str:
                widget = self._create_choice_widget(param_def)
            else:
                widget = self._create_text_widget(param_def)

            self.parameter_widgets[param_def.name] = widget

    def _create_numeric_widget(self, param_def: Parameter) -> QWidget:
        """Create numeric input widget.

        Args:
            param_def: Parameter definition

        Returns:
            Configured numeric widget
        """
        widget = QWidget()
        layout = QHBoxLayout()

        # Create spin box for integers or double spin box for floats
        if param_def.param_type == int:
            spin_box = QSpinBox()
            spin_box.setRange(param_def.min_value or 0, param_def.max_value or 100)
            spin_box.setValue(param_def.default or 0)
        else:
            spin_box = QDoubleSpinBox()
            spin_box.setRange(param_def.min_value or 0.0, param_def.max_value or 100.0)
            spin_box.setValue(param_def.default or 0.0)
            spin_box.setDecimals(2)

        # Connect value changed signal
        spin_box.valueChanged.connect(
            lambda value, name=param_def.name: self._on_parameter_changed(name, value)
        )

        layout.addWidget(QLabel(f"{param_def.name}:"))
        layout.addWidget(spin_box)

        widget.setLayout(layout)
        return widget
```

### QualityDisplay

Widget for displaying quality metrics.

```python
class QualityDisplay:
    """Widget for displaying quality metrics."""

    def __init__(self):
        """Initialize quality display."""
        self.metrics_labels: Dict[str, QLabel] = {}
        self.chart_widget = None

    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """Update displayed quality metrics.

        Args:
            metrics: Dictionary of quality metrics
        """
        # Update metric labels
        for metric_name, value in metrics.items():
            if metric_name in self.metrics_labels:
                if metric_name.endswith('_ms'):
                    self.metrics_labels[metric_name].setText(f"{value:.1f} ms")
                elif metric_name.endswith('_db'):
                    self.metrics_labels[metric_name].setText(f"{value:.2f} dB")
                else:
                    self.metrics_labels[metric_name].setText(f"{value:.3f}")

        # Update quality chart if available
        if self.chart_widget:
            self._update_quality_chart(metrics)

    def _update_quality_chart(self, metrics: Dict[str, float]) -> None:
        """Update quality comparison chart.

        Args:
            metrics: Current quality metrics
        """
        # Implementation for updating quality visualization chart
        pass
```

## Exporters

### Configuration Exporter

Exports current application configuration for batch processing.

```python
class ConfigExporter:
    """Exporter for application configurations."""

    def __init__(self, app: BlurSuiteApp):
        """Initialize configuration exporter.

        Args:
            app: BlurSuiteApp instance
        """
        self.app = app

    def export_configuration(self, output_path: str) -> bool:
        """Export current configuration to file.

        Args:
            output_path: Output configuration file path

        Returns:
            True if export successful
        """
        config = {
            "metadata": {
                "created_by": "Blur Suite Interactive Tool",
                "creation_date": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "blur_settings": {
                "blur_type": str(self.app.current_blur_type),
                "parameters": self.app.current_parameters
            },
            "image_info": {
                "path": self.app.image_path,
                "loaded": self.app.current_image is not None
            },
            "quality_metrics": self.app.get_quality_metrics()
        }

        try:
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False

    def export_batch_configuration(self, image_paths: List[str], output_path: str) -> bool:
        """Export batch configuration for multiple images.

        Args:
            image_paths: List of image file paths
            output_path: Output configuration file path

        Returns:
            True if export successful
        """
        # Create batch configuration based on current settings
        image_configs = {}

        for image_path in image_paths:
            image_configs[image_path] = {
                "blur_type": str(self.app.current_blur_type),
                "parameters": self.app.current_parameters,
                "enabled": True
            }

        config = {
            "metadata": {
                "created_by": "Blur Suite Interactive Tool",
                "creation_date": datetime.now().isoformat(),
                "batch_size": len(image_paths)
            },
            "global_settings": {
                "parallel_processing": True,
                "max_workers": 4
            },
            "image_configurations": image_configs
        }

        try:
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting batch configuration: {e}")
            return False
```

### Dataset Exporter

Exports configurations specifically for dataset creation module.

```python
class DatasetExporter:
    """Exporter for dataset creation configurations."""

    def __init__(self, app: BlurSuiteApp):
        """Initialize dataset exporter.

        Args:
            app: BlurSuiteApp instance
        """
        self.app = app

    def create_dataset_config(self, image_configurations: Dict[str, Dict]) -> Dict:
        """Create dataset configuration from current settings.

        Args:
            image_configurations: Dictionary of image configurations

        Returns:
            Dataset configuration dictionary
        """
        config = {
            "metadata": {
                "created_by": "Blur Suite Interactive Tool",
                "creation_date": datetime.now().isoformat(),
                "version": "1.0.0",
                "source": "interactive_tool"
            },
            "global_settings": {
                "output_format": "png",
                "quality": 95,
                "parallel_processing": True,
                "max_workers": 4,
                "preserve_metadata": True
            },
            "image_configurations": image_configurations
        }

        return config

    def export_for_dataset_creator(self, image_paths: List[str], output_path: str) -> bool:
        """Export configuration for use with DatasetCreator.

        Args:
            image_paths: List of image file paths
            output_path: Output configuration file path

        Returns:
            True if export successful
        """
        # Create image configurations based on current blur settings
        image_configs = {}

        for image_path in image_paths:
            image_configs[image_path] = {
                "blur_type": str(self.app.current_blur_type),
                "parameters": self.app.current_parameters,
                "enabled": True
            }

        config = self.create_dataset_config(image_configs)

        try:
            with open(output_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting dataset configuration: {e}")
            return False
```

## Utility Functions

### Image Processing Utilities

```python
class ImageUtils:
    """Utility functions for image processing in interactive mode."""

    @staticmethod
    def load_image(image_path: str) -> np.ndarray:
        """Load image from file path.

        Args:
            image_path: Path to image file

        Returns:
            Image as numpy array

        Raises:
            FileNotFoundError: If image file not found
            ValueError: If image format is not supported
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Load image using PIL
        pil_image = Image.open(image_path)

        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Convert to numpy array
        image = np.array(pil_image)

        return image

    @staticmethod
    def save_image(image: np.ndarray, output_path: str, format: str = "PNG") -> None:
        """Save image to file path.

        Args:
            image: Image as numpy array
            output_path: Output file path
            format: Image format (PNG, JPEG, TIFF)
        """
        # Convert numpy array to PIL Image
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)

        pil_image = Image.fromarray(image)

        # Save with specified format
        pil_image.save(output_path, format=format)

    @staticmethod
    def resize_image(image: np.ndarray, max_size: Tuple[int, int]) -> np.ndarray:
        """Resize image if larger than max_size.

        Args:
            image: Input image
            max_size: Maximum (width, height)

        Returns:
            Resized image if necessary, original otherwise
        """
        height, width = image.shape[:2]

        if width <= max_size[0] and height <= max_size[1]:
            return image

        # Calculate resize ratio
        ratio = min(max_size[0] / width, max_size[1] / height)

        new_width = int(width * ratio)
        new_height = int(height * ratio)

        # Resize using OpenCV or PIL
        resized = cv2.resize(image, (new_width, new_height))

        return resized
```

## Event Handling

### Signal Connections

```python
def _connect_components(self) -> None:
    """Connect GUI component signals to slots."""
    # Image loading connections
    self.main_window.file_menu.open_action.triggered.connect(self._on_open_image)
    self.main_window.file_menu.load_directory_action.triggered.connect(self._on_load_directory)

    # Blur type selection
    self.parameter_panel.blur_type_combo.currentTextChanged.connect(self._on_blur_type_changed)

    # Parameter changes
    for widget in self.parameter_panel.parameter_widgets.values():
        if hasattr(widget, 'valueChanged'):
            widget.valueChanged.connect(self._on_parameter_changed)

    # Menu actions
    self.main_window.file_menu.export_config_action.triggered.connect(self._on_export_config)
    self.main_window.file_menu.save_image_action.triggered.connect(self._on_save_image)

    # View actions
    self.main_window.view_menu.zoom_in_action.triggered.connect(self._on_zoom_in)
    self.main_window.view_menu.zoom_out_action.triggered.connect(self._on_zoom_out)
    self.main_window.view_menu.reset_zoom_action.triggered.connect(self._on_reset_zoom)
```

## Error Handling

### Exception Handling

```python
def _handle_error(self, error: Exception, context: str = "") -> None:
    """Handle and display errors to user.

    Args:
        error: Exception that occurred
        context: Context where error occurred
    """
    error_message = f"Error{' in ' + context if context else ''}: {str(error)}"

    # Log error
    logger.error(error_message, exc_info=True)

    # Display error dialog
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setWindowTitle("Error")
    error_dialog.setText(error_message)
    error_dialog.setDetailedText(traceback.format_exc())
    error_dialog.exec_()

def _handle_warning(self, message: str) -> None:
    """Display warning message to user.

    Args:
        message: Warning message to display
    """
    warning_dialog = QMessageBox()
    warning_dialog.setIcon(QMessageBox.Warning)
    warning_dialog.setWindowTitle("Warning")
    warning_dialog.setText(message)
    warning_dialog.exec_()
```

## Configuration Management

### Loading Configuration

```python
def load_configuration(self, config_path: str) -> bool:
    """Load configuration from file.

    Args:
        config_path: Path to configuration file

    Returns:
        True if configuration loaded successfully
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Apply loaded configuration
        if "blur_settings" in config:
            blur_settings = config["blur_settings"]

            if "blur_type" in blur_settings:
                self.set_blur_type(blur_settings["blur_type"])

            if "parameters" in blur_settings:
                self.set_parameters(**blur_settings["parameters"])

        return True

    except Exception as e:
        self._handle_error(e, "loading configuration")
        return False
```

### Saving Configuration

```python
def save_configuration(self, config_path: str) -> bool:
    """Save current configuration to file.

    Args:
        config_path: Path to save configuration file

    Returns:
        True if configuration saved successfully
    """
    try:
        config = self._create_configuration_dict()

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return True

    except Exception as e:
        self._handle_error(e, "saving configuration")
        return False
```

## Integration Examples

### Integration with Dataset Creation

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

### Batch Processing Integration

```python
from blur_suite.interactive import BlurSuiteApp

# Configure multiple blur settings
app = BlurSuiteApp()

blur_settings = [
    {"blur_type": "gaussian", "kernel_size": 5, "sigma_x": 1.0},
    {"blur_type": "gaussian", "kernel_size": 9, "sigma_x": 2.0},
    {"blur_type": "motion", "angle": 45.0, "length": 15}
]

# Apply each setting and export
for i, settings in enumerate(blur_settings):
    app.set_blur_type(settings.pop("blur_type"))
    app.set_parameters(**settings)

    # Export configuration for this setting
    config_file = f"config_setting_{i+1}.json"
    app.export_configuration(config_file)
```

### Custom Plugin Integration

```python
from blur_suite.interactive import BlurSuiteApp
from blur_suite.core.blur import PluginBase, BlurEffect, BlurType

class CustomPlugin(PluginBase):
    """Custom plugin for interactive tool."""

    def get_blur_types(self) -> List[BlurType]:
        return [BlurType.GAUSSIAN]  # Custom blur type

    def create_effect(self, blur_type: BlurType, **kwargs) -> BlurEffect:
        return CustomBlurEffect(**kwargs)

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "Custom Interactive Plugin",
            "version": "1.0.0",
            "description": "Custom blur effects for interactive tool"
        }

# Register plugin with interactive app
app = BlurSuiteApp()
app.register_plugin(CustomPlugin())

# Custom blur type now available in GUI
```

## Best Practices

### Performance Optimization

1. **Resize large images** for preview to improve responsiveness
2. **Debounce parameter changes** to avoid excessive processing
3. **Use appropriate quality settings** for preview vs final output
4. **Cache processed results** when possible

### User Experience

1. **Provide clear feedback** for all operations
2. **Show progress indicators** for long operations
3. **Validate inputs** before applying effects
4. **Offer sensible defaults** for all parameters

### Error Handling

1. **Handle all exceptions gracefully** with user-friendly messages
2. **Provide detailed error information** for debugging
3. **Log errors** for troubleshooting
4. **Offer recovery options** when possible

## API Compatibility

### Version Compatibility

The interactive API maintains backward compatibility:

- **Minor versions**: New features added without breaking existing code
- **Patch versions**: Bug fixes and performance improvements
- **Major versions**: Breaking changes may be introduced

### Deprecation Policy

Features are deprecated before removal:

```python
@deprecated("Use set_blur_type() instead")
def set_blur_effect(self, blur_type: str):
    """Deprecated method for setting blur type."""
    warnings.warn(
        "set_blur_effect() is deprecated, use set_blur_type() instead",
        DeprecationWarning,
        stacklevel=2
    )
    self.set_blur_type(blur_type)
```

## Support and Resources

- 📚 **[User Guide: Interactive Tool](../user_guide/interactive_tool.md)** - Complete usage guide
- 💡 **[Examples: Integration](../examples/integration_example.py)** - Integration patterns
- 🛠️ **[Troubleshooting Guide](../troubleshooting.md)** - Common issues and solutions

---

*Need help?* Check the [Troubleshooting Guide](../troubleshooting.md) or explore the [Examples](../examples/) for more advanced usage patterns.