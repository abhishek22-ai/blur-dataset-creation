"""
Image preview widget for displaying blurred images.

This module provides a widget for previewing blurred images with
zoom, pan, and fit-to-window functionality.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Optional

import cv2
import numpy as np
from PIL import Image, ImageTk

logger = logging.getLogger(__name__)


class ComparisonView:
    """
    Widget for previewing original and blurred images with zoom and pan functionality.

    Displays both original and blurred images in a top-bottom layout with shared zoom controls,
    fit-to-window, and navigation capabilities.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize comparison view widget.

        Args:
            parent: Parent Tkinter widget
            app: Reference to main application instance
        """
        self.parent = parent
        self.app = app

        # Image state
        self.original_image: Optional[np.ndarray] = None
        self.blurred_image: Optional[np.ndarray] = None
        self.processing_time_ms: float = 0.0

        # Display state
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0

        # UI state
        self.display_images: Dict[str, ImageTk.PhotoImage] = {}

        # Create UI components
        self._create_widgets()

        # Bind events
        self._bind_events()

    def _create_widgets(self) -> None:
        """Create the comparison view widgets."""
        # Main frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Toolbar
        self._create_toolbar()

        # Image display area
        self._create_display_area()

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

        # Processing time display
        self.time_label = ttk.Label(
            toolbar, text="Processing: 0.0ms", font=("TkDefaultFont", 8)
        )
        self.time_label.pack(side=tk.RIGHT)

    def _create_display_area(self) -> None:
        """Create the main display area with top-bottom layout for original and blurred images."""
        # Display frame
        display_frame = ttk.Frame(self.main_frame)
        display_frame.pack(fill=tk.BOTH, expand=True)

        # Create paned window for top-bottom layout
        self.paned_window = ttk.PanedWindow(display_frame, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Create top canvas for original image
        top_frame = ttk.Frame(self.paned_window)
        self.original_canvas = self._create_image_canvas(top_frame, "original")
        self.paned_window.add(top_frame, weight=1)

        # Create bottom canvas for blurred image
        bottom_frame = ttk.Frame(self.paned_window)
        self.blurred_canvas = self._create_image_canvas(bottom_frame, "blurred")
        self.paned_window.add(bottom_frame, weight=1)

    def _create_image_canvas(self, parent: ttk.Frame, name: str) -> tk.Canvas:
        """Create a canvas for image display."""
        # Canvas frame
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create canvas
        canvas = tk.Canvas(
            canvas_frame,
            bg="#f0f0f0",
            highlightthickness=1,
            highlightcolor="#ccc",
            highlightbackground="#ccc",
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars - only show when needed
        h_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview
        )
        v_scrollbar = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=canvas.yview
        )

        # Initially hide scrollbars
        h_scrollbar.pack_forget()
        v_scrollbar.pack_forget()

        # Configure canvas scrolling
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

        # Create image item
        canvas.create_image(0, 0, anchor=tk.NW, image=None, tags="image")

        # Store canvas reference
        setattr(self, f"{name}_canvas", canvas)

        return canvas

    def _bind_events(self) -> None:
        """Bind mouse and keyboard events."""
        # Mouse wheel for zoom on both canvases
        if hasattr(self, "original_canvas"):
            self.original_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        if hasattr(self, "blurred_canvas"):
            self.blurred_canvas.bind("<MouseWheel>", self._on_mouse_wheel)

        # Keyboard shortcuts
        self.main_frame.bind("<Control-plus>", lambda e: self.zoom_in())
        self.main_frame.bind("<Control-minus>", lambda e: self.zoom_out())
        self.main_frame.bind("<Control-0>", lambda e: self.fit_to_window())

    def show_comparison(
        self, original: np.ndarray, blurred: np.ndarray, processing_time_ms: float
    ) -> None:
        """
        Show both original and blurred images in top-bottom layout.

        Args:
            original: Original image to display (top)
            blurred: Blurred image to display (bottom)
            processing_time_ms: Processing time in milliseconds
        """
        try:
            self.original_image = original
            self.blurred_image = blurred
            self.processing_time_ms = processing_time_ms

            # Update display to show only blurred image
            self._update_display()

            # Update processing time
            self.time_label.config(text=f"Processing: {processing_time_ms:.1f}ms")

            logger.debug(
                f"Blur preview updated with {processing_time_ms:.1f}ms processing time"
            )

        except Exception as e:
            logger.error(f"Failed to show blurred image: {str(e)}")

    def _update_display(self) -> None:
        """Update the display to show both original and blurred images."""
        if self.original_image is None and self.blurred_image is None:
            return

        self._update_dual_images()

    def _update_dual_images(self) -> None:
        """Update display to show both original and blurred images in top-bottom layout."""
        # Update original image (top)
        if self.original_image is not None:
            self._update_canvas_image(
                self.original_canvas, self.original_image, "original"
            )

        # Update blurred image (bottom)
        if self.blurred_image is not None:
            self._update_canvas_image(
                self.blurred_canvas, self.blurred_image, "blurred"
            )

    def _update_canvas_image(
        self, canvas: tk.Canvas, image: np.ndarray, canvas_name: str
    ) -> None:
        """Update a specific canvas with an image."""
        # Prepare image for display
        display_image = self._prepare_image_for_display(image, canvas_name)

        # Create PhotoImage
        self.display_images[canvas_name] = ImageTk.PhotoImage(display_image)

        # Update canvas
        canvas.itemconfig("image", image=self.display_images[canvas_name])

        # Update scroll region
        self._update_scroll_region(canvas, display_image)

    def _update_single_image(self) -> None:
        """Update display to show only blurred image (legacy method)."""
        # Show single canvas
        self.main_canvas.master.pack(fill=tk.BOTH, expand=True)

        # Prepare blurred image for display
        display_image = self._prepare_image_for_display(self.blurred_image, "main")

        # Create PhotoImage
        self.display_images["main"] = ImageTk.PhotoImage(display_image)

        # Update canvas
        self.main_canvas.itemconfig("image", image=self.display_images["main"])

        # Update scroll region
        self._update_scroll_region(self.main_canvas, display_image)

    def _prepare_image_for_display(
        self, image: np.ndarray, canvas_name: str
    ) -> Image.Image:
        """Prepare image for display on specified canvas."""
        # Make a copy to avoid modifying original
        display_image = image.copy()

        # Convert to uint8 if needed
        if display_image.dtype != np.uint8:
            if display_image.max() <= 1.0:
                display_image = (display_image * 255).astype(np.uint8)
            else:
                display_image = display_image.astype(np.uint8)

        # Convert color space if needed
        if len(display_image.shape) == 2:
            display_image = cv2.cvtColor(display_image, cv2.COLOR_GRAY2RGB)
        elif display_image.shape[2] == 4:
            display_image = cv2.cvtColor(display_image, cv2.COLOR_RGBA2RGB)

        # Apply zoom
        if self.zoom_factor != 1.0:
            new_width = int(display_image.shape[1] * self.zoom_factor)
            new_height = int(display_image.shape[0] * self.zoom_factor)
            display_image = cv2.resize(display_image, (new_width, new_height))

        # Create PIL Image
        pil_image = Image.fromarray(display_image)

        return pil_image

    def _update_scroll_region(self, canvas: tk.Canvas, image: Image.Image) -> None:
        """Update scroll region for a canvas."""
        canvas.configure(scrollregion=(0, 0, image.width, image.height))
        self._update_scrollbar_visibility(canvas, image)

    def _hide_scrollbars(self) -> None:
        """Hide all scrollbars for cleaner display."""
        # Hide scrollbar widgets for both canvases
        canvases = []
        if hasattr(self, "original_canvas"):
            canvases.append(self.original_canvas)
        if hasattr(self, "blurred_canvas"):
            canvases.append(self.blurred_canvas)

        for canvas in canvases:
            # Find scrollbar widgets in the canvas frame and hide them
            canvas_frame = canvas.master
            for child in canvas_frame.winfo_children():
                if isinstance(child, ttk.Scrollbar):
                    child.pack_forget()

    def _update_scrollbar_visibility(
        self, canvas: tk.Canvas, image: Image.Image
    ) -> None:
        """Show/hide scrollbars for a canvas based on need."""
        # Get canvas and image dimensions
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        image_width = image.width
        image_height = image.height

        # Find the scrollbar widgets for this canvas
        canvas_frame = canvas.master
        h_scrollbar = None
        v_scrollbar = None

        for child in canvas_frame.winfo_children():
            if isinstance(child, ttk.Scrollbar):
                if child.cget("orient") == "horizontal":
                    h_scrollbar = child
                elif child.cget("orient") == "vertical":
                    v_scrollbar = child

        # Show horizontal scrollbar if image is wider than canvas
        if image_width > canvas_width and h_scrollbar:
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        elif h_scrollbar:
            h_scrollbar.pack_forget()

        # Show vertical scrollbar if image is taller than canvas
        if image_height > canvas_height and v_scrollbar:
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        elif v_scrollbar:
            v_scrollbar.pack_forget()

    def _on_mouse_wheel(self, event: Any) -> None:
        """Handle mouse wheel for zooming."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self, factor: float = 1.2) -> None:
        """Zoom in by the given factor."""
        self.zoom_factor *= factor
        self._update_display()
        self.zoom_label.config(text=f"{int(self.zoom_factor * 100)}%")

    def zoom_out(self, factor: float = 1.2) -> None:
        """Zoom out by the given factor."""
        self.zoom_factor /= factor
        if self.zoom_factor < 0.1:
            self.zoom_factor = 0.1
        self._update_display()
        self.zoom_label.config(text=f"{int(self.zoom_factor * 100)}%")

    def actual_size(self) -> None:
        """Reset to actual size (100% zoom)."""
        self.zoom_factor = 1.0
        self._update_display()
        self.zoom_label.config(text="100%")

    def get_zoom_factor(self) -> float:
        """Get current zoom factor."""
        return self.zoom_factor

    def set_zoom_factor(self, factor: float) -> None:
        """Set zoom factor programmatically."""
        self.zoom_factor = max(0.1, min(5.0, factor))  # Limit range
        self._update_display()

    def fit_to_window(self) -> None:
        """Fit both images to window size in top-bottom layout."""
        if self.original_image is None and self.blurred_image is None:
            return

        # Get canvas size
        canvas_width = self.main_frame.winfo_width()
        canvas_height = self.main_frame.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            self.main_frame.after(100, self.fit_to_window)
            return

        # For dual layout, each image gets roughly half the height
        available_height_per_image = (
            canvas_height - 50
        ) / 2  # Subtract toolbar height and padding

        # Calculate zoom factors for both images
        zoom_factors = []

        # Check original image
        if self.original_image is not None:
            orig_height, orig_width = self.original_image.shape[:2]
            width_factor = canvas_width / orig_width
            height_factor = available_height_per_image / orig_height
            zoom_factors.append(min(width_factor, height_factor) * 0.9)

        # Check blurred image
        if self.blurred_image is not None:
            blur_height, blur_width = self.blurred_image.shape[:2]
            width_factor = canvas_width / blur_width
            height_factor = available_height_per_image / blur_height
            zoom_factors.append(min(width_factor, height_factor) * 0.9)

        # Use the smaller zoom factor to ensure both images fit well
        if zoom_factors:
            self.zoom_factor = min(zoom_factors)
        else:
            self.zoom_factor = 1.0

        # Reset pan
        self.pan_x = 0
        self.pan_y = 0

        self._update_display()

    def clear(self) -> None:
        """Clear the preview view."""
        self.original_image = None
        self.blurred_image = None
        self.processing_time_ms = 0.0

        # Clear display for both canvases
        if hasattr(self, "original_canvas"):
            self.original_canvas.itemconfig("image", image=None)
        if hasattr(self, "blurred_canvas"):
            self.blurred_canvas.itemconfig("image", image=None)

        self.display_images.clear()
        self.time_label.config(text="Processing: 0.0ms")

    def get_processing_time(self) -> float:
        """Get the last processing time."""
        return self.processing_time_ms
