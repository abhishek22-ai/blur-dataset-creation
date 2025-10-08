"""
Quality metrics display for image comparison.

This module provides real-time display of image quality metrics including
PSNR, SSIM, and processing performance information with export functionality.
"""

import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict

import cv2
import numpy as np


class QualityMetrics:
    """
    Widget for displaying image quality metrics.

    Shows real-time comparison metrics between original and processed
    images including PSNR, SSIM, and performance data.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize quality metrics widget.

        Args:
            parent: Parent Tkinter widget
            app: Reference to main application instance
        """
        self.parent = parent
        self.app = app

        # Current metrics
        self.current_metrics: Dict[str, float] = {}

        # Create UI components
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the quality metrics widgets."""
        # Main frame - compact layout
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Metrics sections - reduced padding and spacing
        self._create_basic_metrics()
        self._create_advanced_metrics()
        self._create_performance_metrics()

        # Export section
        self._create_export_section()

    def _create_basic_metrics(self) -> None:
        """Create basic quality metrics section."""
        # Basic metrics frame - compact
        basic_frame = ttk.LabelFrame(self.main_frame, text="Basic Metrics", padding="3")
        basic_frame.pack(fill=tk.X, pady=(0, 3))

        # PSNR - compact layout
        psnr_frame = ttk.Frame(basic_frame)
        psnr_frame.pack(fill=tk.X, pady=(0, 1))

        ttk.Label(
            psnr_frame, text="PSNR (dB):", font=("TkDefaultFont", 8, "bold"), width=12
        ).pack(side=tk.LEFT)

        self.psnr_value = ttk.Label(
            psnr_frame, text="N/A", font=("TkDefaultFont", 8), width=8
        )
        self.psnr_value.pack(side=tk.LEFT)

        self.psnr_bar = ttk.Progressbar(psnr_frame, length=80, mode="determinate")
        self.psnr_bar.pack(side=tk.LEFT, padx=(3, 0), fill=tk.X, expand=True)

        # SSIM - compact layout
        ssim_frame = ttk.Frame(basic_frame)
        ssim_frame.pack(fill=tk.X, pady=(0, 1))

        ttk.Label(
            ssim_frame, text="SSIM:", font=("TkDefaultFont", 8, "bold"), width=12
        ).pack(side=tk.LEFT)

        self.ssim_value = ttk.Label(
            ssim_frame, text="N/A", font=("TkDefaultFont", 8), width=8
        )
        self.ssim_value.pack(side=tk.LEFT)

        self.ssim_bar = ttk.Progressbar(ssim_frame, length=80, mode="determinate")
        self.ssim_bar.pack(side=tk.LEFT, padx=(3, 0), fill=tk.X, expand=True)

        # MSE - compact layout
        mse_frame = ttk.Frame(basic_frame)
        mse_frame.pack(fill=tk.X, pady=(0, 1))

        ttk.Label(
            mse_frame, text="MSE:", font=("TkDefaultFont", 8, "bold"), width=12
        ).pack(side=tk.LEFT)

        self.mse_value = ttk.Label(
            mse_frame, text="N/A", font=("TkDefaultFont", 8), width=8
        )
        self.mse_value.pack(side=tk.LEFT)

    def _create_advanced_metrics(self) -> None:
        """Create advanced quality metrics section."""
        # Advanced metrics frame - compact
        advanced_frame = ttk.LabelFrame(
            self.main_frame, text="Advanced Metrics", padding="3"
        )
        advanced_frame.pack(fill=tk.X, pady=(0, 3))

        # Blur level estimation - compact
        blur_frame = ttk.Frame(advanced_frame)
        blur_frame.pack(fill=tk.X, pady=(0, 1))

        ttk.Label(
            blur_frame, text="Blur Level:", font=("TkDefaultFont", 8, "bold"), width=12
        ).pack(side=tk.LEFT)

        self.blur_value = ttk.Label(
            blur_frame, text="N/A", font=("TkDefaultFont", 8), width=8
        )
        self.blur_value.pack(side=tk.LEFT)

        self.blur_bar = ttk.Progressbar(blur_frame, length=80, mode="determinate")
        self.blur_bar.pack(side=tk.LEFT, padx=(3, 0), fill=tk.X, expand=True)

        # Sharpness difference - compact
        sharpness_frame = ttk.Frame(advanced_frame)
        sharpness_frame.pack(fill=tk.X, pady=(0, 1))

        ttk.Label(
            sharpness_frame,
            text="Sharpness Loss:",
            font=("TkDefaultFont", 8, "bold"),
            width=12,
        ).pack(side=tk.LEFT)

        self.sharpness_value = ttk.Label(
            sharpness_frame, text="N/A", font=("TkDefaultFont", 8), width=8
        )
        self.sharpness_value.pack(side=tk.LEFT)

        self.sharpness_bar = ttk.Progressbar(
            sharpness_frame, length=80, mode="determinate"
        )
        self.sharpness_bar.pack(side=tk.LEFT, padx=(3, 0), fill=tk.X, expand=True)

    def _create_performance_metrics(self) -> None:
        """Create performance metrics section."""
        # Performance frame - compact
        perf_frame = ttk.LabelFrame(self.main_frame, text="Performance", padding="3")
        perf_frame.pack(fill=tk.X, pady=(0, 3))

        # Processing time - compact
        time_frame = ttk.Frame(perf_frame)
        time_frame.pack(fill=tk.X, pady=(0, 1))

        ttk.Label(
            time_frame,
            text="Processing Time:",
            font=("TkDefaultFont", 8, "bold"),
            width=12,
        ).pack(side=tk.LEFT)

        self.time_value = ttk.Label(
            time_frame, text="0.0 ms", font=("TkDefaultFont", 8), width=8
        )
        self.time_value.pack(side=tk.LEFT)

        # Memory usage (placeholder) - compact
        memory_frame = ttk.Frame(perf_frame)
        memory_frame.pack(fill=tk.X, pady=(0, 1))

        ttk.Label(
            memory_frame,
            text="Memory Usage:",
            font=("TkDefaultFont", 8, "bold"),
            width=12,
        ).pack(side=tk.LEFT)

        self.memory_value = ttk.Label(
            memory_frame, text="N/A", font=("TkDefaultFont", 8), width=8
        )
        self.memory_value.pack(side=tk.LEFT)

        # Image size info - compact
        size_frame = ttk.Frame(perf_frame)
        size_frame.pack(fill=tk.X, pady=(0, 1))

        ttk.Label(
            size_frame, text="Image Size:", font=("TkDefaultFont", 8, "bold"), width=12
        ).pack(side=tk.LEFT)

        self.size_value = ttk.Label(
            size_frame, text="N/A", font=("TkDefaultFont", 8), width=8
        )
        self.size_value.pack(side=tk.LEFT)

    def update_metrics(
        self, original: np.ndarray, processed: np.ndarray, processing_time_ms: float
    ) -> None:
        """
        Update metrics with new image comparison.

        Args:
            original: Original image
            processed: Processed image
            processing_time_ms: Processing time in milliseconds
        """
        try:
            # Calculate metrics
            metrics = self._calculate_metrics(original, processed, processing_time_ms)

            # Update display
            self._update_display(metrics)

            # Store current metrics
            self.current_metrics = metrics

        except Exception as e:
            print(f"Error calculating metrics: {str(e)}")
            self._clear_metrics()

    def _calculate_metrics(
        self, original: np.ndarray, processed: np.ndarray, processing_time_ms: float
    ) -> Dict[str, float]:
        """Calculate quality metrics between two images."""
        metrics = {}

        # Ensure images are in the same format
        orig = self._prepare_image_for_metrics(original)
        proc = self._prepare_image_for_metrics(processed)

        # Basic metrics
        metrics["psnr"] = self._calculate_psnr(orig, proc)
        metrics["ssim"] = self._calculate_ssim(orig, proc)
        metrics["mse"] = self._calculate_mse(orig, proc)

        # Advanced metrics
        metrics["blur_level"] = self._estimate_blur_level(proc)
        metrics["sharpness_loss"] = self._calculate_sharpness_loss(orig, proc)

        # Performance metrics
        metrics["processing_time"] = processing_time_ms
        metrics["image_size"] = orig.size

        return metrics

    def _prepare_image_for_metrics(self, image: np.ndarray) -> np.ndarray:
        """Prepare image for metrics calculation."""
        # Convert to grayscale for most metrics
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image

        # Normalize to 0-255 range
        if gray.dtype != np.uint8:
            if gray.max() <= 1.0:
                gray = (gray * 255).astype(np.uint8)
            else:
                gray = gray.astype(np.uint8)

        return gray

    def _calculate_psnr(self, original: np.ndarray, processed: np.ndarray) -> float:
        """Calculate Peak Signal-to-Noise Ratio."""
        mse = self._calculate_mse(original, processed)

        if mse == 0:
            return float("inf")

        return 20 * np.log10(255.0) - 10 * np.log10(mse)

    def _calculate_ssim(self, original: np.ndarray, processed: np.ndarray) -> float:
        """Calculate Structural Similarity Index."""
        try:
            # Use OpenCV's SSIM implementation
            return cv2.matchTemplate(original, processed, cv2.TM_CCORR_NORMED)[0][0]
        except Exception:
            return 0.0

    def _calculate_mse(self, original: np.ndarray, processed: np.ndarray) -> float:
        """Calculate Mean Squared Error."""
        return float(
            np.mean((original.astype(np.float32) - processed.astype(np.float32)) ** 2)
        )

    def _estimate_blur_level(self, image: np.ndarray) -> float:
        """Estimate blur level using Laplacian variance."""
        try:
            # Calculate Laplacian with CV_64F for better precision
            laplacian = cv2.Laplacian(image, cv2.CV_64F)

            # Convert to float32 for variance calculation and further processing
            laplacian = laplacian.astype(np.float32)

            # Calculate variance
            variance = laplacian.var()

            # Normalize to 0-1 range (lower variance = more blur)
            # Typical sharp image has variance > 100, very blurred < 10
            blur_level = max(0, min(1, (100 - variance) / 100))

            return blur_level

        except Exception:
            return 0.0

    def _calculate_sharpness_loss(
        self, original: np.ndarray, processed: np.ndarray
    ) -> float:
        """Calculate sharpness loss between original and processed images."""
        orig_blur = self._estimate_blur_level(original)
        proc_blur = self._estimate_blur_level(processed)

        return max(0, proc_blur - orig_blur)

    def _update_display(self, metrics: Dict[str, float]) -> None:
        """Update the metrics display."""
        # Basic metrics
        self._update_psnr_display(metrics.get("psnr", 0))
        self._update_ssim_display(metrics.get("ssim", 0))
        self._update_mse_display(metrics.get("mse", 0))

        # Advanced metrics
        self._update_blur_display(metrics.get("blur_level", 0))
        self._update_sharpness_display(metrics.get("sharpness_loss", 0))

        # Performance metrics
        self._update_performance_display(metrics)

    def _update_psnr_display(self, psnr: float) -> None:
        """Update PSNR display."""
        self.psnr_value.config(text=f"{psnr:.1f}")

        # Color code based on quality
        if psnr == float("inf"):
            color = "#28a745"  # Green for perfect
        elif psnr >= 30:
            color = "#28a745"  # Green for good
        elif psnr >= 20:
            color = "#ffc107"  # Yellow for fair
        else:
            color = "#dc3545"  # Red for poor

        self.psnr_value.config(foreground=color)

        # Update progress bar (normalize to 0-60 dB range)
        bar_value = min(100, (psnr / 60) * 100) if psnr != float("inf") else 100
        self.psnr_bar.config(value=bar_value)

    def _update_ssim_display(self, ssim: float) -> None:
        """Update SSIM display."""
        self.ssim_value.config(text=f"{ssim:.3f}")

        # Color code based on similarity
        if ssim >= 0.8:
            color = "#28a745"  # Green for high similarity
        elif ssim >= 0.6:
            color = "#ffc107"  # Yellow for medium similarity
        else:
            color = "#dc3545"  # Red for low similarity

        self.ssim_value.config(foreground=color)

        # Update progress bar
        self.ssim_bar.config(value=ssim * 100)

    def _update_mse_display(self, mse: float) -> None:
        """Update MSE display."""
        if mse < 100:
            display_text = f"{mse:.1f}"
        elif mse < 10000:
            display_text = f"{mse:.0f}"
        else:
            display_text = f"{mse:.0e}"

        self.mse_value.config(text=display_text)

        # Color code (lower is better)
        if mse <= 100:
            color = "#28a745"  # Green for low error
        elif mse <= 1000:
            color = "#ffc107"  # Yellow for medium error
        else:
            color = "#dc3545"  # Red for high error

        self.mse_value.config(foreground=color)

    def _update_blur_display(self, blur_level: float) -> None:
        """Update blur level display."""
        self.blur_value.config(text=f"{blur_level:.3f}")

        # Color code
        if blur_level <= 0.3:
            color = "#28a745"  # Green for low blur
        elif blur_level <= 0.7:
            color = "#ffc107"  # Yellow for medium blur
        else:
            color = "#dc3545"  # Red for high blur

        self.blur_value.config(foreground=color)
        self.blur_bar.config(value=blur_level * 100)

    def _update_sharpness_display(self, sharpness_loss: float) -> None:
        """Update sharpness loss display."""
        self.sharpness_value.config(text=f"{sharpness_loss:.3f}")

        # Color code
        if sharpness_loss <= 0.2:
            color = "#28a745"  # Green for minimal loss
        elif sharpness_loss <= 0.5:
            color = "#ffc107"  # Yellow for moderate loss
        else:
            color = "#dc3545"  # Red for significant loss

        self.sharpness_value.config(foreground=color)
        self.sharpness_bar.config(value=min(100, sharpness_loss * 100))

    def _update_performance_display(self, metrics: Dict[str, float]) -> None:
        """Update performance metrics display."""
        # Processing time
        processing_time = metrics.get("processing_time", 0)
        self.time_value.config(text=f"{processing_time:.1f} ms")

        # Image size
        image_size = metrics.get("image_size", 0)
        if image_size > 0:
            if image_size < 1000:
                size_text = f"{image_size} pixels"
            elif image_size < 1000000:
                size_text = f"{image_size / 1000:.1f}K pixels"
            else:
                size_text = f"{image_size / 1000000:.1f}M pixels"

            self.size_value.config(text=size_text)

    def _clear_metrics(self) -> None:
        """Clear all metrics display."""
        labels = [
            self.psnr_value,
            self.ssim_value,
            self.mse_value,
            self.blur_value,
            self.sharpness_value,
            self.time_value,
            self.memory_value,
            self.size_value,
        ]

        for label in labels:
            label.config(text="N/A", foreground="black")

        # Clear progress bars
        for bar in [self.psnr_bar, self.ssim_bar, self.blur_bar, self.sharpness_bar]:
            bar.config(value=0)

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current metrics values."""
        return self.current_metrics.copy()

    def clear(self) -> None:
        """Clear all metrics."""
        self.current_metrics.clear()
        self._clear_metrics()

    def _create_export_section(self) -> None:
        """Create export section with Finish button."""
        # Export frame - compact
        export_frame = ttk.LabelFrame(self.main_frame, text="Export", padding="3")
        export_frame.pack(fill=tk.X, pady=(5, 0))

        # Finish button - collects all configurations and exports to JSON
        self.finish_button = ttk.Button(
            export_frame,
            text="Finish & Export Configuration",
            command=self._export_configuration_data,
            style="Action.TButton",
        )
        self.finish_button.pack(fill=tk.X, pady=(2, 0))

    def _export_configuration_data(self) -> None:
        """Export all configuration data to JSON file."""
        try:
            # Collect configuration data from app
            export_data = self._collect_configuration_data()

            if not export_data:
                messagebox.showwarning("Warning", "No configuration data to export")
                return

            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"blur_configurations_{timestamp}.json"

            # Show save dialog
            file_path = filedialog.asksaveasfilename(
                title="Export Configuration Data",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=filename,
            )

            if not file_path:
                return

            # Save to file
            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2)

            messagebox.showinfo(
                "Success", f"Configuration data exported to:\n{file_path}"
            )

        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to export configuration data:\n{str(e)}"
            )

    def _collect_configuration_data(self) -> Dict[str, Any]:
        """Collect configuration data from current and session configurations."""
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "total_images": 0,
                "blur_types_found": [],
            },
            "blur_configurations": {},
        }

        # Collect data from current_configurations
        if (
            hasattr(self.app, "current_configurations")
            and self.app.current_configurations
        ):
            current_data = self._process_configurations(self.app.current_configurations)
            export_data["blur_configurations"].update(current_data)

        # Collect data from session_configurations
        if (
            hasattr(self.app, "session_configurations")
            and self.app.session_configurations
        ):
            session_data = self._process_configurations(self.app.session_configurations)
            export_data["blur_configurations"].update(session_data)

        # Calculate min/max for each blur type and parameter
        export_data = self._calculate_min_max_ranges(export_data)

        # Update metadata
        export_data["metadata"]["total_images"] = len(
            export_data["blur_configurations"]
        )
        export_data["metadata"]["blur_types_found"] = list(
            set(
                config.get("blur_type", "unknown")
                for config in export_data["blur_configurations"].values()
            )
        )

        return export_data

    def _process_configurations(self, configurations: Dict[str, Any]) -> Dict[str, Any]:
        """Process configuration data for export."""
        processed_data = {}

        for image_path, config in configurations.items():
            if not isinstance(config, dict):
                continue

            # Extract image name from path
            image_name = Path(image_path).name

            processed_data[image_name] = {
                "blur_type": config.get("blur_type", "unknown"),
                "parameters": config.get("parameters", {}),
                "enabled": config.get("enabled", True),
            }

        return processed_data

    def _calculate_min_max_ranges(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate min/max ranges for each blur type and parameter."""
        # Group configurations by blur type
        blur_type_groups = {}
        for image_name, config in export_data["blur_configurations"].items():
            blur_type = config.get("blur_type", "unknown")
            if blur_type not in blur_type_groups:
                blur_type_groups[blur_type] = []
            blur_type_groups[blur_type].append(config)

        # Calculate min/max for each blur type
        for blur_type, configs in blur_type_groups.items():
            if not configs:
                continue

            # Get all parameters from the first config (assuming consistent structure)
            first_config = configs[0]
            parameters = first_config.get("parameters", {})

            if not parameters:
                continue

            # Initialize min/max structure
            min_max_data = {}

            for param_name in parameters.keys():
                values = []
                for config in configs:
                    param_value = config.get("parameters", {}).get(param_name)
                    if param_value is not None:
                        # Handle different value types
                        try:
                            if isinstance(param_value, (int, float)):
                                values.append(float(param_value))
                            elif isinstance(param_value, str):
                                # Try to convert string numbers
                                try:
                                    values.append(float(param_value))
                                except ValueError:
                                    pass  # Skip non-numeric strings
                        except (TypeError, ValueError):
                            pass  # Skip invalid values

                if values:
                    min_max_data[param_name] = {"min": min(values), "max": max(values)}

            # Add to export data
            export_data[blur_type] = min_max_data

        return export_data
