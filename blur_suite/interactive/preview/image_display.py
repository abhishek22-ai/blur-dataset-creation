"""
Image display component for showing original images.

This module provides a widget for displaying original images with zoom,
pan, and fit-to-window functionality for detailed inspection.
"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageTk


class ImageDisplay:
    """
    Widget for displaying original images with zoom and pan functionality.

    Provides smooth image display with mouse interaction for detailed
    inspection of source images.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize image display widget.

        Args:
            parent: Parent Tkinter widget
            app: Reference to main application instance
        """
        self.parent = parent
        self.app = app

        # Image state
        self.current_image: Optional[np.ndarray] = None
        self.current_image_path: str = ""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Display state
        self.display_image: Optional[ImageTk.PhotoImage] = None
        self.image_size: Tuple[int, int] = (0, 0)

        # Create UI components
        self._create_widgets()

        # Bind events
        self._bind_events()

    def _create_widgets(self) -> None:
        """Create the image display widgets."""
        # Main frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Toolbar
        self._create_toolbar()

        # Image canvas
        self._create_image_canvas()

    def _create_toolbar(self) -> None:
        """Create toolbar with zoom controls."""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        # Zoom controls
        zoom_frame = ttk.Frame(toolbar)
        zoom_frame.pack(side=tk.LEFT)

        ttk.Button(zoom_frame, text="Zoom In", command=self.zoom_in, width=10).pack(
            side=tk.LEFT, padx=(0, 2)
        )

        ttk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out, width=10).pack(
            side=tk.LEFT, padx=(0, 2)
        )

        ttk.Button(zoom_frame, text="Fit", command=self.fit_to_window, width=8).pack(
            side=tk.LEFT, padx=(0, 2)
        )

        ttk.Button(
            zoom_frame, text="Actual Size", command=self.actual_size, width=12
        ).pack(side=tk.LEFT, padx=(0, 2))

        # Zoom level label
        self.zoom_label = ttk.Label(zoom_frame, text="100%", width=6)
        self.zoom_label.pack(side=tk.LEFT, padx=(10, 0))

        # Spacer
        separator = ttk.Separator(toolbar, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Image info
        info_frame = ttk.Frame(toolbar)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.info_label = ttk.Label(
            info_frame, text="No image loaded", font=("TkDefaultFont", 8)
        )
        self.info_label.pack(side=tk.LEFT)

    def _create_image_canvas(self) -> None:
        """Create canvas for image display."""
        # Canvas frame
        canvas_frame = ttk.Frame(self.main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#f0f0f0",
            highlightthickness=1,
            highlightcolor="#ccc",
            highlightbackground="#ccc",
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars - only show when needed
        self.h_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )
        self.v_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )

        # Initially hide scrollbars
        self.h_scrollbar.pack_forget()
        self.v_scrollbar.pack_forget()

        # Configure canvas scrolling
        self.canvas.configure(
            xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set
        )

        # Create image item on canvas
        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=None)

    def _bind_events(self) -> None:
        """Bind mouse and keyboard events."""
        # Mouse events for panning
        self.canvas.bind("<ButtonPress-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._pan_image)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)

        # Keyboard events for zoom
        self.canvas.bind("<Control-plus>", lambda e: self.zoom_in())
        self.canvas.bind("<Control-minus>", lambda e: self.zoom_out())
        self.canvas.bind("<Control-0>", lambda e: self.fit_to_window())

        # Canvas resize event
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def show_image(self, image: np.ndarray, image_path: str) -> None:
        """
        Display an image.

        Args:
            image: Image as numpy array
            image_path: Path to the image file
        """
        self.current_image = image
        self.current_image_path = image_path

        # Reset zoom and pan
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Update display
        self._update_display()

        # Update info
        self._update_info()

    def _update_display(self) -> None:
        """Update the displayed image."""
        if self.current_image is None:
            return

        try:
            # Convert image for display
            display_image = self._prepare_image_for_display()

            # Create PhotoImage
            self.display_image = ImageTk.PhotoImage(display_image)

            # Update canvas
            self.canvas.itemconfig(self.canvas_image, image=self.display_image)

            # Update canvas scroll region
            self._update_scroll_region()

            # Update zoom label
            self.zoom_label.config(text=f"{int(self.zoom_factor * 100)}%")

        except Exception as e:
            print(f"Error updating display: {str(e)}")

    def _prepare_image_for_display(self) -> Image.Image:
        """Prepare image for Tkinter display."""
        # Make a copy to avoid modifying original
        image = self.current_image.copy()

        # Convert to uint8 if needed
        if image.dtype != np.uint8:
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
            else:
                image = image.astype(np.uint8)

        # Convert color space if needed
        if len(image.shape) == 2:
            # Grayscale to RGB
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            # RGBA to RGB
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

        # Apply zoom
        if self.zoom_factor != 1.0:
            new_width = int(image.shape[1] * self.zoom_factor)
            new_height = int(image.shape[0] * self.zoom_factor)
            image = cv2.resize(image, (new_width, new_height))

        # Create PIL Image
        pil_image = Image.fromarray(image)

        return pil_image

    def _update_scroll_region(self) -> None:
        """Update canvas scroll region."""
        if self.display_image:
            self.canvas.configure(
                scrollregion=(
                    0,
                    0,
                    self.display_image.width(),
                    self.display_image.height(),
                )
            )

            # Show/hide scrollbars based on need
            self._update_scrollbar_visibility()

    def _update_info(self) -> None:
        """Update image information display."""
        if self.current_image is not None:
            height, width = self.current_image.shape[:2]
            channels = (
                self.current_image.shape[2] if len(self.current_image.shape) > 2 else 1
            )

            info_text = f"{width} × {height} × {channels}"
            if self.current_image_path:
                filename = Path(self.current_image_path).name
                info_text = f"{filename} - {info_text}"

            self.info_label.config(text=info_text)

    def zoom_in(self, factor: float = 1.2) -> None:
        """Zoom in by the given factor."""
        self.zoom_factor *= factor
        self._update_display()

    def zoom_out(self, factor: float = 1.2) -> None:
        """Zoom out by the given factor."""
        self.zoom_factor /= factor
        if self.zoom_factor < 0.1:
            self.zoom_factor = 0.1
        self._update_display()

    def actual_size(self) -> None:
        """Reset to actual size (100% zoom)."""
        self.zoom_factor = 1.0
        self._update_display()

    def fit_to_window(self) -> None:
        """Fit image to window size."""
        if self.current_image is None:
            return

        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not yet sized, try again later
            self.canvas.after(100, self.fit_to_window)
            return

        # Get image size
        image_height, image_width = self.current_image.shape[:2]

        # Calculate zoom factors
        width_factor = canvas_width / image_width
        height_factor = canvas_height / image_height

        # Use minimum factor to ensure image fits
        self.zoom_factor = (
            min(width_factor, height_factor) * 0.9
        )  # 90% to add some margin

        # Reset pan
        self.pan_x = 0
        self.pan_y = 0

        self._update_display()

    def _start_pan(self, event: Any) -> None:
        """Start panning operation."""
        self.canvas.scan_mark(event.x, event.y)

    def _pan_image(self, event: Any) -> None:
        """Pan the image."""
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_mouse_wheel(self, event: Any) -> None:
        """Handle mouse wheel for zooming."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _update_scrollbar_visibility(self) -> None:
        """Show/hide scrollbars based on whether they're needed."""
        if not self.display_image:
            self.h_scrollbar.pack_forget()
            self.v_scrollbar.pack_forget()
            return

        # Get canvas and image dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width = self.display_image.width()
        image_height = self.display_image.height()

        # Show horizontal scrollbar if image is wider than canvas
        if image_width > canvas_width:
            self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        else:
            self.h_scrollbar.pack_forget()

        # Show vertical scrollbar if image is taller than canvas
        if image_height > canvas_height:
            self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.v_scrollbar.pack_forget()

    def _on_canvas_resize(self, event: Any) -> None:
        """Handle canvas resize event."""
        # Update scroll region if we have an image
        if self.display_image:
            self._update_scroll_region()

    def clear(self) -> None:
        """Clear the display."""
        self.current_image = None
        self.current_image_path = ""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # Clear canvas
        self.canvas.itemconfig(self.canvas_image, image=None)
        self.display_image = None

        # Update info
        self.info_label.config(text="No image loaded")
        self.zoom_label.config(text="100%")

    def get_image_size(self) -> Tuple[int, int]:
        """Get the size of the currently displayed image."""
        if self.current_image is not None:
            return self.current_image.shape[1], self.current_image.shape[
                0
            ]  # width, height
        return 0, 0

    def get_zoom_factor(self) -> float:
        """Get current zoom factor."""
        return self.zoom_factor

    def set_zoom_factor(self, factor: float) -> None:
        """Set zoom factor programmatically."""
        self.zoom_factor = max(0.1, min(5.0, factor))  # Limit range
        self._update_display()

    def center_image(self) -> None:
        """Center the image in the canvas."""
        if self.display_image:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            image_width = self.display_image.width()
            image_height = self.display_image.height()

            # Calculate center position
            center_x = max(0, (canvas_width - image_width) // 2)
            center_y = max(0, (canvas_height - image_height) // 2)

            self.canvas.coords(self.canvas_image, center_x, center_y)

    def save_view_state(self) -> Dict[str, Any]:
        """Save current view state."""
        return {
            "zoom_factor": self.zoom_factor,
            "pan_x": self.pan_x,
            "pan_y": self.pan_y,
        }

    def restore_view_state(self, state: Dict[str, Any]) -> None:
        """Restore view state."""
        self.zoom_factor = state.get("zoom_factor", 1.0)
        self.pan_x = state.get("pan_x", 0)
        self.pan_y = state.get("pan_y", 0)
        self._update_display()
