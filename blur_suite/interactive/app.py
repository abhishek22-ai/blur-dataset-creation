"""
Main application coordinator for the Blur Suite Interactive Configuration Tool.

This module contains the main BlurSuiteApp class that coordinates all components
of the interactive blur configuration tool, including GUI management, image handling,
session management, and integration with the core blur module.
"""

import json
import logging
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Dict, List

import cv2
import numpy as np
from PIL import Image, ImageTk

from ..core.blur import (
    BlurType,
    get_blur_factory,
)
from .controls.blur_selector import BlurSelector
from .controls.parameter_sliders import ParameterSliders
from .exporters.dataset_exporter import DatasetExporter
from .gui import MainWindow
from .preview.comparison_view import ComparisonView
from .preview.quality_metrics import QualityMetrics

logger = logging.getLogger(__name__)


class BlurSuiteApp:
    """
    Main application class for the Blur Suite Interactive Configuration Tool.

    Coordinates all components including GUI, image management, blur processing,
    and configuration export functionality.
    """

    def __init__(self):
        """Initialize the Blur Suite application."""
        self.root = None
        self.main_window = None

        # Core components
        self.blur_factory = get_blur_factory()
        self.current_blur_effect = None
        self.dataset_exporter = DatasetExporter()

        # Image management
        self.image_paths: List[str] = []
        self.current_image_index = 0
        self.images: Dict[str, np.ndarray] = {}
        self.image_thumbnails: Dict[str, ImageTk.PhotoImage] = {}

        # Configuration state
        self.current_configurations: Dict[str, Dict[str, Any]] = {}
        self.session_configurations: Dict[str, Any] = {}

        # Processing state
        self.is_processing = False
        self.processing_thread = None
        self._cancel_processing = False

        # UI components (will be initialized when GUI is created)
        self.blur_selector = None
        self.parameter_sliders = None
        self.comparison_view = None
        self.quality_metrics = None

        logger.info("BlurSuiteApp initialized")

    def create_gui(self) -> None:
        """Create and initialize the main GUI."""
        self.root = tk.Tk()
        self.root.title("Blur Suite Interactive Configuration Tool")
        self.root.geometry("1400x900")

        # Create main window
        self.main_window = MainWindow(self.root, self)

        # Initialize UI components
        self._initialize_ui_components()

        # Set up event handlers
        self._setup_event_handlers()

        logger.info("GUI created successfully")

    def _initialize_ui_components(self) -> None:
        """Initialize all UI components."""
        # Control widgets
        self.blur_selector = BlurSelector(self.main_window.blur_selector_frame, self)
        self.parameter_sliders = ParameterSliders(
            self.main_window.parameters_frame, self
        )

        # Preview components
        self.comparison_view = ComparisonView(self.main_window.comparison_frame, self)
        self.quality_metrics = QualityMetrics(self.main_window.metrics_frame, self)

        # Initialize parameter sliders with empty parameters to show "no parameters" message
        if self.parameter_sliders:
            self.parameter_sliders.update_parameters({})

    def _setup_event_handlers(self) -> None:
        """Set up event handlers for UI interactions."""
        # File menu handlers
        self.main_window.file_menu.add_command(
            label="Load Images", command=self.load_images, accelerator="Ctrl+O"
        )
        self.main_window.file_menu.add_command(
            label="Export Configuration",
            command=self.export_configuration,
            accelerator="Ctrl+S",
        )
        self.main_window.file_menu.add_separator()
        self.main_window.file_menu.add_command(
            label="Exit", command=self.quit_app, accelerator="Ctrl+Q"
        )

        # View menu handlers
        self.main_window.view_menu.add_command(
            label="Reset View", command=self.reset_view
        )
        self.main_window.view_menu.add_command(
            label="Fit to Window", command=self.fit_to_window
        )

        # Keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self.load_images())
        self.root.bind("<Control-s>", lambda e: self.export_configuration())
        self.root.bind("<Control-q>", lambda e: self.quit_app())

        # Blur selector handler
        self.blur_selector.on_blur_type_changed = self.on_blur_type_changed

        # Parameter sliders handler
        self.parameter_sliders.on_parameter_changed = self.on_parameter_changed

    def run(self) -> None:
        """Start the application main loop."""
        if not self.root:
            self.create_gui()

        logger.info("Starting Blur Suite application")
        self.root.mainloop()

    def quit_app(self) -> None:
        """Quit the application."""
        logger.info("Quitting application")

        # Save session state
        self._save_session_state()

        # Close application
        if self.root:
            self.root.quit()
            self.root.destroy()

    def load_images(self) -> None:
        """Load images from directory selection dialog."""
        directory = filedialog.askdirectory(
            title="Select Image Directory", mustexist=True
        )

        if not directory:
            return

        try:
            self._load_images_from_directory(directory)
            self._update_status(f"Loaded {len(self.image_paths)} images")
            logger.info(f"Loaded {len(self.image_paths)} images from {directory}")

        except Exception as e:
            error_msg = f"Failed to load images: {str(e)}"
            messagebox.showerror("Error", error_msg)
            logger.error(error_msg)

    def _load_images_from_directory(self, directory: str) -> None:
        """Load images from the specified directory."""
        # Clear existing images
        self.images.clear()
        self.image_thumbnails.clear()
        self.image_paths.clear()

        # Supported image extensions
        supported_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}

        # Find all image files
        directory_path = Path(directory)
        image_files = []

        for ext in supported_extensions:
            image_files.extend(directory_path.rglob(f"*{ext}"))
            image_files.extend(directory_path.rglob(f"*{ext.upper()}"))

        # Validate minimum number of images
        if len(image_files) < 10:
            raise ValueError(
                f"Insufficient images found. Need at least 10 images, found {len(image_files)}"
            )

        # Load images
        loaded_count = 0
        for image_path in image_files:
            if loaded_count >= 20:  # Limit to 20 images for performance
                break

            try:
                # Load image with OpenCV
                image = cv2.imread(str(image_path))
                if image is None:
                    continue

                # Convert BGR to RGB
                if len(image.shape) == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # Store image
                self.images[str(image_path)] = image
                self.image_paths.append(str(image_path))

                # Create thumbnail
                self._create_thumbnail(str(image_path), image)

                loaded_count += 1

            except Exception as e:
                logger.warning(f"Failed to load image {image_path}: {str(e)}")
                continue

        if loaded_count < 10:
            raise ValueError(
                f"Could only load {loaded_count} valid images. Need at least 10."
            )

        # Initialize configurations for loaded images
        self._initialize_configurations()

        # Initialize default blur effect if not already set
        if not self.current_blur_effect:
            self.current_blur_effect = self.blur_factory.create_effect("gaussian")

        # Show first image
        if self.image_paths:
            self.show_image(0)

        # Update navigation buttons after loading images
        if self.main_window:
            self.main_window.update_navigation_buttons()

    def _create_thumbnail(self, image_path: str, image: np.ndarray) -> None:
        """Create a thumbnail for the given image."""
        try:
            # Resize image for thumbnail
            height, width = image.shape[:2]
            max_size = 100

            if height > width:
                new_height = max_size
                new_width = int(width * max_size / height)
            else:
                new_width = max_size
                new_height = int(height * max_size / width)

            thumbnail = cv2.resize(image, (new_width, new_height))

            # Convert to PIL Image
            pil_image = Image.fromarray(thumbnail)
            photo_image = ImageTk.PhotoImage(pil_image)

            self.image_thumbnails[image_path] = photo_image

        except Exception as e:
            logger.warning(f"Failed to create thumbnail for {image_path}: {str(e)}")

    def _initialize_configurations(self) -> None:
        """Initialize default configurations for all loaded images."""
        self.current_configurations.clear()

        for image_path in self.image_paths:
            self.current_configurations[image_path] = {
                "blur_type": BlurType.GAUSSIAN.value,
                "parameters": {
                    "kernel_size": 5,
                    "sigma_x": 1.0,
                    "sigma_y": 1.0,
                },
                "enabled": True,
            }

    def show_image(self, index: int) -> None:
        """Show the image at the specified index."""
        if not self.image_paths or index < 0 or index >= len(self.image_paths):
            return

        self.current_image_index = index
        image_path = self.image_paths[index]

        # Update image information display
        if self.main_window:
            self.main_window.update_image_info(image_path, self.images[image_path])

        # Update comparison view - always show the current image
        if self.comparison_view:
            current_image = self.images[image_path]
            # For initial display, show original image in both panels
            # The blur effect will be applied when user changes parameters or blur type
            self.comparison_view.show_comparison(current_image, current_image, 0.0)

        # Update navigation buttons and counter
        if self.main_window:
            self.main_window.update_navigation_buttons()

        # Update status
        total_images = len(self.image_paths)
        self._update_status(
            f"Image {index + 1} of {total_images}: {Path(image_path).name}"
        )

    def on_blur_type_changed(self, blur_type: str) -> None:
        """Handle blur type selection change."""
        try:
            print(f"DEBUG: Blur type change requested to: {blur_type}")

            # Check if this is actually a change or the same blur type
            current_blur_type = None
            if self.current_blur_effect:
                # Get current blur type from the effect
                current_params = self.current_blur_effect.get_parameters()
                if current_params:
                    # Try to infer blur type from current effect parameters
                    # This is a fallback since we don't store the blur type directly
                    pass

            # Check if blur type is actually changing by comparing with current configuration
            is_same_blur_type = False
            if self.image_paths and self.current_image_index < len(self.image_paths):
                current_image = self.image_paths[self.current_image_index]
                current_blur_type = self.current_configurations[current_image][
                    "blur_type"
                ]
                is_same_blur_type = current_blur_type == blur_type
                print(
                    f"DEBUG: Current blur type: {current_blur_type}, requested: {blur_type}, same: {is_same_blur_type}"
                )

            # Only create new blur effect if blur type is actually changing
            if not is_same_blur_type or self.current_blur_effect is None:
                print(f"DEBUG: Creating new blur effect for type: {blur_type.lower()}")
                # Create new blur effect
                self.current_blur_effect = self.blur_factory.create_effect(
                    blur_type.lower()
                )

                # Update parameter sliders with new parameters only if blur type changed
                if self.parameter_sliders and self.current_blur_effect:
                    new_params = self.current_blur_effect.get_parameters()
                    print(
                        f"DEBUG: Updating parameter sliders with {len(new_params)} new parameters"
                    )
                    for param_name, param in new_params.items():
                        print(
                            f"DEBUG: New parameter '{param_name}': {param.value} (type: {type(param.value)})"
                        )
                    self.parameter_sliders.update_parameters(new_params)

            # Update current configuration
            if self.image_paths and self.current_image_index < len(self.image_paths):
                current_image = self.image_paths[self.current_image_index]
                self.current_configurations[current_image]["blur_type"] = blur_type

                # Only update parameters in configuration if blur type changed
                if not is_same_blur_type or self.current_blur_effect is None:
                    self.current_configurations[current_image]["parameters"] = {
                        param.name: param.value
                        for param in self.current_blur_effect.get_parameters().values()
                    }

            # Update preview immediately (always do this for visual feedback)
            self._update_preview()

            logger.info(
                f"Blur type {'changed to' if not is_same_blur_type else 'reselected'}: {blur_type}"
            )

        except Exception as e:
            error_msg = f"Failed to change blur type: {str(e)}"
            messagebox.showerror("Error", error_msg)
            logger.error(error_msg)

    def on_parameter_changed(self, param_name: str, value: Any) -> None:
        """Handle parameter value change."""
        if not self.current_blur_effect:
            return

        try:
            # Update blur effect parameter
            self.current_blur_effect.set_parameter(param_name, value)

            # Update current configuration
            if self.image_paths and self.current_image_index < len(self.image_paths):
                current_image = self.image_paths[self.current_image_index]
                self.current_configurations[current_image]["parameters"][param_name] = (
                    value
                )

            # Update preview
            self._update_preview()

            logger.debug(f"Parameter {param_name} changed to {value}")

        except Exception as e:
            error_msg = f"Failed to update parameter {param_name}: {str(e)}"
            messagebox.showerror("Error", error_msg)
            logger.error(error_msg)

    def reset_parameters_to_defaults(self) -> None:
        """Reset all parameters to their default values."""
        if self.current_blur_effect and self.parameter_sliders:
            try:
                # Get default parameters from current blur effect
                default_params = {}
                for (
                    param_name,
                    param,
                ) in self.current_blur_effect.get_parameters().items():
                    default_params[param_name] = param.value

                # Reset parameter sliders to defaults
                self.parameter_sliders.set_parameters(default_params)

                # Update current configuration with defaults
                if self.image_paths and self.current_image_index < len(
                    self.image_paths
                ):
                    current_image = self.image_paths[self.current_image_index]
                    self.current_configurations[current_image]["parameters"] = (
                        default_params.copy()
                    )

                logger.debug("Parameters reset to defaults")

            except Exception as e:
                logger.error(f"Failed to reset parameters to defaults: {str(e)}")

    def collect_user_preference(self) -> None:
        """Collect user preference for current blur settings and store in session_configurations."""
        if not self.current_blur_effect or not self.image_paths:
            return

        try:
            # Get current image and blur configuration
            current_image_path = self.image_paths[self.current_image_index]
            current_blur_type = self.current_configurations[current_image_path][
                "blur_type"
            ]
            current_params = self.current_configurations[current_image_path][
                "parameters"
            ]

            # Create preference entry
            preference_entry = {
                "image_path": current_image_path,
                "blur_type": current_blur_type,
                "parameters": current_params.copy(),
                "timestamp": datetime.now().isoformat(),
                "image_index": self.current_image_index,
            }

            # Initialize session_configurations if not exists
            if (
                not hasattr(self, "session_configurations")
                or self.session_configurations is None
            ):
                self.session_configurations = {}

            # Group preferences by blur type and image
            blur_type_key = current_blur_type
            image_key = current_image_path

            # Initialize nested structure if needed
            if blur_type_key not in self.session_configurations:
                self.session_configurations[blur_type_key] = {}

            if image_key not in self.session_configurations[blur_type_key]:
                self.session_configurations[blur_type_key][image_key] = []

            # Add preference entry (allow multiple values for same blur type on same image)
            self.session_configurations[blur_type_key][image_key].append(
                preference_entry
            )

            # Update status
            total_preferences = sum(
                len(image_list)
                for image_list in self.session_configurations[blur_type_key].values()
            )
            self._update_status(
                f"Collected preference {total_preferences} for {current_blur_type}"
            )

            logger.info(
                f"Collected preference for {current_blur_type} on {Path(current_image_path).name}"
            )

        except Exception as e:
            logger.error(f"Failed to collect user preference: {str(e)}")
            raise

    def get_session_configurations_summary(self) -> Dict[str, Any]:
        """Get summary of collected session configurations for min/max range compilation."""
        if not self.session_configurations:
            return {}

        summary = {}

        for blur_type, image_configs in self.session_configurations.items():
            summary[blur_type] = {}

            for image_path, preferences in image_configs.items():
                # Compile min/max ranges for each parameter across all preferences for this blur type and image
                if preferences:
                    param_ranges = {}

                    # Get all parameter names from first preference
                    first_pref = preferences[0]
                    for param_name in first_pref["parameters"].keys():
                        values = [
                            pref["parameters"][param_name]
                            for pref in preferences
                            if param_name in pref["parameters"]
                        ]

                        if values:
                            if isinstance(values[0], (int, float)):
                                param_ranges[param_name] = {
                                    "min": min(values),
                                    "max": max(values),
                                    "values": values,
                                    "count": len(values),
                                }
                            else:
                                # For non-numeric parameters, just store unique values
                                unique_values = list(set(str(v) for v in values))
                                param_ranges[param_name] = {
                                    "unique_values": unique_values,
                                    "count": len(values),
                                }

                    summary[blur_type][image_path] = param_ranges

        return summary

    def reset_blur_type_to_no_blur(self) -> None:
        """Reset blur type selection to 'No Blur'."""
        try:
            # Set blur type to 'No Blur'
            if self.blur_selector:
                self.blur_selector.set_blur_type(BlurType.NO_BLUR.value)

            # Update current configuration
            if self.image_paths and self.current_image_index < len(self.image_paths):
                current_image = self.image_paths[self.current_image_index]
                self.current_configurations[current_image]["blur_type"] = (
                    BlurType.NO_BLUR.value
                )

            logger.debug("Blur type reset to 'No Blur'")

        except Exception as e:
            logger.error(f"Failed to reset blur type to 'No Blur': {str(e)}")
            raise

    def _apply_blur_to_current_image(self) -> None:
        """Apply blur to current image and update display immediately."""
        if not self.current_blur_effect or not self.images:
            return

        try:
            # Get current image
            current_image_path = self.image_paths[self.current_image_index]
            original_image = self.images[current_image_path]

            # Apply blur effect immediately (no threading for direct apply)
            result = self.current_blur_effect.apply(original_image)

            # Update comparison view immediately on main thread
            if self.comparison_view:
                processing_time = 0.0  # We don't need to measure time for direct apply
                self.comparison_view.show_comparison(
                    original_image, result.result_image, processing_time
                )

            # Update quality metrics
            if self.quality_metrics:
                self.quality_metrics.update_metrics(
                    original_image, result.result_image, processing_time
                )

            logger.info("Blur applied successfully to current image")

        except Exception as e:
            logger.error(f"Failed to apply blur: {str(e)}")
            raise

    def _update_preview(self) -> None:
        """Update the preview with current blur settings."""
        if not self.current_blur_effect or not self.images:
            return

        # Update comparison view in background thread
        if self.comparison_view and not self.is_processing:
            # Cancel previous thread if still running
            if self.processing_thread and self.processing_thread.is_alive():
                # Set flag to cancel previous operation
                self._cancel_processing = True
                # Wait a bit for cancellation
                time.sleep(0.01)

            self._cancel_processing = False
            self.is_processing = True
            self.processing_thread = threading.Thread(
                target=self._update_comparison_view, daemon=True
            )
            self.processing_thread.start()

    def _update_comparison_view(self) -> None:
        """Update the comparison view with blurred image."""
        if not self.current_blur_effect or not self.images:
            return

        try:
            # Check if processing was cancelled
            if self._cancel_processing:
                return

            # Get current image
            current_image_path = self.image_paths[self.current_image_index]
            original_image = self.images[current_image_path]

            # Apply blur effect
            start_time = time.time()
            result = self.current_blur_effect.apply(original_image)
            processing_time = (time.time() - start_time) * 1000

            # Check if processing was cancelled during blur application
            if self._cancel_processing:
                return

            # Update comparison view on main thread
            if self.comparison_view:
                try:
                    self.root.after(
                        0,
                        lambda: self.comparison_view.show_comparison(
                            original_image, result.result_image, processing_time
                        ),
                    )
                except Exception as e:
                    logger.error(f"Failed to update comparison view: {str(e)}")

            # Update quality metrics on main thread
            if self.quality_metrics:
                try:
                    self.root.after(
                        0,
                        lambda: self.quality_metrics.update_metrics(
                            original_image, result.result_image, processing_time
                        ),
                    )
                except Exception as e:
                    logger.error(f"Failed to update quality metrics: {str(e)}")

            logger.debug(f"Preview updated in {processing_time:.2f}ms")

        except Exception as e:
            logger.error(f"Failed to update preview: {str(e)}")
            # Show error on main thread
            if self.main_window:
                error_msg = f"Blur application failed: {str(e)}"
                self.root.after(0, lambda: self._show_error(error_msg))
        finally:
            self.is_processing = False

    def export_configuration(self) -> None:
        """Export current configurations to JSON file."""
        if not self.current_configurations:
            messagebox.showwarning("Warning", "No configurations to export")
            return

        # Prepare export data
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "total_images": len(self.current_configurations),
                "blur_suite_version": "1.0.0",
            },
            "global_settings": {
                "default_blur_type": BlurType.GAUSSIAN.value,
                "default_parameters": {
                    "kernel_size": 5,
                    "sigma_x": 1.0,
                    "sigma_y": 1.0,
                },
            },
            "image_configurations": {},
        }

        # Add image configurations
        for image_path, config in self.current_configurations.items():
            export_data["image_configurations"][image_path] = {
                "blur_type": config["blur_type"],
                "parameters": config["parameters"],
                "enabled": config["enabled"],
                "image_info": {
                    "filename": Path(image_path).name,
                    "size": self.images[image_path].shape,
                },
            }

        # Show save dialog
        filename = filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if not filename:
            return

        try:
            # Export using dataset exporter
            self.dataset_exporter.export_configuration(filename, export_data)
            self._update_status(f"Configuration exported to {filename}")
            logger.info(f"Configuration exported to {filename}")

        except Exception as e:
            error_msg = f"Failed to export configuration: {str(e)}"
            messagebox.showerror("Error", error_msg)
            logger.error(error_msg)

    def reset_view(self) -> None:
        """Reset the view to default state."""
        try:
            # Get current image for reset
            current_image = None
            current_image_path = None
            if self.image_paths and self.current_image_index < len(self.image_paths):
                current_image_path = self.image_paths[self.current_image_index]
                current_image = self.images[current_image_path]

            # Reset current blur effect first
            self.current_blur_effect = self.blur_factory.create_effect("gaussian")

            # Reset configurations to defaults
            if self.image_paths:
                self._initialize_configurations()

            # Reset to default blur effect
            if self.blur_selector:
                self.blur_selector.set_blur_type(BlurType.GAUSSIAN.value)

            # Reset parameter sliders to defaults
            if self.parameter_sliders and self.current_blur_effect:
                self.parameter_sliders.update_parameters(
                    self.current_blur_effect.get_parameters()
                )

            # Clear comparison view completely
            if self.comparison_view:
                self.comparison_view.clear()

            # Clear quality metrics
            if self.quality_metrics:
                self.quality_metrics.clear()

            # Update status
            self._update_status("View reset to defaults")

            logger.info("View reset to defaults")

        except Exception as e:
            error_msg = f"Failed to reset view: {str(e)}"
            logger.error(error_msg)
            self._show_error(error_msg)

    def fit_to_window(self) -> None:
        if self.comparison_view:
            self.comparison_view.fit_to_window()

    def _update_status(self, message: str) -> None:
        """Update the status bar message."""
        if self.main_window and self.main_window.status_bar:
            self.main_window.status_bar.set_status(message)

    def _show_error(self, message: str) -> None:
        """Show error message to user."""
        messagebox.showerror("Error", message)

    def _save_session_state(self) -> None:
        """Save current session state."""
        session_file = Path.home() / ".blur_suite_session.json"

        try:
            session_data = {
                "current_image_index": self.current_image_index,
                "current_configurations": self.current_configurations,
                "window_geometry": self.root.geometry() if self.root else None,
            }

            with open(session_file, "w") as f:
                json.dump(session_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save session state: {str(e)}")

    def _load_session_state(self) -> None:
        """Load previous session state."""
        session_file = Path.home() / ".blur_suite_session.json"

        if session_file.exists():
            try:
                with open(session_file, "r") as f:
                    session_data = json.load(f)

                # Restore state if we have images loaded
                if self.image_paths and "current_image_index" in session_data:
                    index = session_data["current_image_index"]
                    if 0 <= index < len(self.image_paths):
                        self.show_image(index)

                if "current_configurations" in session_data:
                    self.current_configurations.update(
                        session_data["current_configurations"]
                    )

            except Exception as e:
                logger.warning(f"Failed to load session state: {str(e)}")
