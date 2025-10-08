"""
Main GUI window and layout for the Blur Suite Interactive Configuration Tool.

This module contains the MainWindow class that creates the primary user interface
with proper layout, styling, and responsive design using Tkinter.
"""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any


class StatusBar:
    """Status bar component for displaying application status."""

    def __init__(self, parent: tk.Widget):
        """Initialize status bar."""
        self.parent = parent
        self.frame = ttk.Frame(parent, relief=tk.SUNKEN, padding=(2, 2))

        # Configure frame grid
        self.frame.grid_columnconfigure(0, weight=1)

        # Status label
        self.status_label = ttk.Label(
            self.frame, text="Ready", anchor=tk.W, font=("TkDefaultFont", 9)
        )
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Progress bar for long operations
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(
            self.frame, variable=self.progress_var, mode="determinate", length=200
        )

    def set_status(self, message: str) -> None:
        """Set status message."""
        self.status_label.config(text=message)
        self.parent.update()

    def show_progress(self, value: int) -> None:
        """Show progress bar with given value."""
        self.progress_var.set(value)
        if value == 0:
            self.progress_bar.grid_remove()
        else:
            self.progress_bar.grid(row=0, column=1, padx=(10, 0), sticky=tk.E)
        self.parent.update()

    def hide_progress(self) -> None:
        """Hide progress bar."""
        self.progress_var.set(0)
        self.progress_bar.grid_remove()


class MainWindow:
    """
    Main window layout for the Blur Suite Interactive Configuration Tool.

    Creates a professional GUI with organized sections for controls,
    image preview, and configuration management.
    """

    def __init__(self, root: tk.Tk, app: Any):
        """
        Initialize main window.

        Args:
            root: Root Tkinter window
            app: Reference to main application instance
        """
        self.root = root
        self.app = app

        # Configure root window
        self._configure_root()

        # Create main layout
        self._create_layout()

        # Set up styling
        self._setup_styles()

    def _configure_root(self) -> None:
        """Configure root window properties."""
        # Set minimum size
        self.root.minsize(1200, 800)

        # Configure grid weights for responsive layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Set window icon (if available)
        try:
            # You can add an icon file here if desired
            pass
        except Exception:
            pass  # Icon not critical for functionality

    def _create_layout(self) -> None:
        """Create the main window layout."""
        # Create main container
        self.main_container = ttk.Frame(self.root, padding="5")
        self.main_container.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))

        # Configure main container grid
        self.main_container.grid_rowconfigure(1, weight=1)  # Content area
        self.main_container.grid_columnconfigure(0, weight=1)

        # Create menu bar
        self._create_menu_bar()

        # Create toolbar
        self._create_toolbar()

        # Create main content area
        self._create_content_area()

        # Create status bar
        self.status_bar = StatusBar(self.main_container)

    def _create_menu_bar(self) -> None:
        """Create menu bar with File, View, and Help menus."""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # View menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)

        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        # Help menu items
        self.help_menu.add_command(label="About", command=self._show_about)
        self.help_menu.add_command(
            label="Keyboard Shortcuts", command=self._show_shortcuts
        )

    def _create_toolbar(self) -> None:
        """Create toolbar with common actions."""
        # Toolbar frame
        self.toolbar_frame = ttk.Frame(self.main_container)
        self.toolbar_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.toolbar_frame.grid_columnconfigure(10, weight=1)  # Spacer

    def _create_content_area(self) -> None:
        """Create the main content area with panels."""
        # Main content frame
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.grid(row=1, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Configure column weights: left=3, center=5, right=2 (30%/50%/20% distribution)
        self.content_frame.grid_columnconfigure(0, weight=3)  # Left panel (30%)
        self.content_frame.grid_columnconfigure(1, weight=5)  # Center panel (50%)
        self.content_frame.grid_columnconfigure(2, weight=2)  # Right panel (20%)

        # Create left panel (controls)
        self._create_left_panel()

        # Create center panel (image preview)
        self._create_center_panel()

        # Create right panel (information)
        self._create_right_panel()

    def _create_left_panel(self) -> None:
        """Create left control panel."""
        # Left panel frame
        self.left_panel = ttk.Frame(self.content_frame, relief=tk.RIDGE, padding="5")
        self.left_panel.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W), padx=(0, 5))

        # Configure left panel grid
        self.left_panel.grid_rowconfigure(1, weight=1)  # Expand content area

        # Panel title
        title_label = ttk.Label(
            self.left_panel, text="Blur Controls", font=("TkDefaultFont", 10, "bold")
        )
        title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # Blur selector section
        self.blur_selector_frame = ttk.LabelFrame(
            self.left_panel, text="Blur Type", padding="5"
        )
        self.blur_selector_frame.grid(
            row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        self.blur_selector_frame.grid_columnconfigure(0, weight=1)

        # Parameter sliders section
        self.parameters_frame = ttk.LabelFrame(
            self.left_panel, text="Parameters", padding="5"
        )
        self.parameters_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.parameters_frame.grid_columnconfigure(0, weight=1)

        # Blur controls section at bottom
        self.blur_controls_frame = ttk.Frame(self.left_panel)
        self.blur_controls_frame.grid(
            row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0)
        )
        self.blur_controls_frame.grid_columnconfigure(0, weight=1)

        # Apply Blur and Reset buttons
        self.apply_blur_button = ttk.Button(
            self.blur_controls_frame,
            text="Apply Blur",
            command=self._apply_current_blur,
            width=12,
        )
        self.apply_blur_button.pack(side=tk.LEFT, padx=(0, 5))

        self.reset_button = ttk.Button(
            self.blur_controls_frame, text="Reset", command=self._reset_blur, width=10
        )
        self.reset_button.pack(side=tk.LEFT)

    def _create_center_panel(self) -> None:
        """Create center image preview panel."""
        # Center panel frame
        self.center_panel = ttk.Frame(self.content_frame, relief=tk.RIDGE, padding="5")
        self.center_panel.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.W, tk.E))
        self.center_panel.grid_rowconfigure(1, weight=0)  # Zoom controls
        self.center_panel.grid_rowconfigure(2, weight=1)  # Image display
        self.center_panel.grid_rowconfigure(3, weight=0)  # Navigation panel
        self.center_panel.grid_columnconfigure(0, weight=1)

        # Panel title
        title_label = ttk.Label(
            self.center_panel, text="Blur Preview", font=("TkDefaultFont", 10, "bold")
        )
        title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # Zoom controls section (top)
        self.zoom_controls_frame = ttk.Frame(self.center_panel)
        self.zoom_controls_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        # Image display section (middle)
        self.comparison_frame = ttk.LabelFrame(
            self.center_panel, text="Preview", padding="5"
        )
        self.comparison_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        self.comparison_frame.grid_columnconfigure(0, weight=1)
        self.comparison_frame.grid_rowconfigure(0, weight=1)

        # Navigation panel (bottom)
        self.nav_frame = ttk.LabelFrame(
            self.center_panel, text="Navigation", padding="2"
        )
        self.nav_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # Create navigation buttons
        self._create_navigation_controls()

    def _create_navigation_controls(self) -> None:
        """Create navigation controls in the center panel."""
        self.prev_button = ttk.Button(
            self.nav_frame,
            text="← Previous",
            command=self._go_to_previous_image,
            width=10,
        )
        self.prev_button.pack(side=tk.LEFT, padx=(0, 2))

        self.next_button = ttk.Button(
            self.nav_frame, text="Next →", command=self._go_to_next_image, width=10
        )
        self.next_button.pack(side=tk.LEFT)

        # Image counter label
        self.image_counter = ttk.Label(self.nav_frame, text="No images loaded")
        self.image_counter.pack(side=tk.LEFT, padx=(10, 0))

    def _create_right_panel(self) -> None:
        """Create right information panel."""
        # Right panel frame
        self.right_panel = ttk.Frame(self.content_frame, relief=tk.RIDGE, padding="5")
        self.right_panel.grid(row=0, column=2, sticky=(tk.N, tk.S, tk.E), padx=(5, 0))

        # Configure right panel grid
        self.right_panel.grid_rowconfigure(1, weight=1)  # Expand content area
        self.right_panel.grid_rowconfigure(2, weight=0)  # Image info - fixed height

        # Panel title
        title_label = ttk.Label(
            self.right_panel, text="Quality Metrics", font=("TkDefaultFont", 10, "bold")
        )
        title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # Quality metrics section - compact version
        self.metrics_frame = ttk.LabelFrame(
            self.right_panel, text="Analysis", padding="3"
        )
        self.metrics_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.metrics_frame.grid_columnconfigure(0, weight=1)

        # Image info section
        self.info_frame = ttk.LabelFrame(
            self.right_panel, text="Image Information", padding="5"
        )
        self.info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        self.info_frame.grid_columnconfigure(0, weight=1)

        # Create info labels
        self._create_info_labels()

    def _create_info_labels(self) -> None:
        """Create information display labels."""
        # Image info labels
        self.image_info_labels = {}

        info_items = [
            ("filename", "Filename:"),
            ("dimensions", "Dimensions:"),
            ("channels", "Channels:"),
            ("dtype", "Data Type:"),
            ("size", "File Size:"),
        ]

        for i, (key, label_text) in enumerate(info_items):
            label = ttk.Label(
                self.info_frame, text=label_text, font=("TkDefaultFont", 8)
            )
            label.grid(row=i, column=0, sticky=tk.W, pady=(2, 0))

            value_label = ttk.Label(
                self.info_frame, text="N/A", font=("TkDefaultFont", 8, "bold")
            )
            value_label.grid(row=i, column=1, sticky=tk.W, pady=(2, 0))

            self.image_info_labels[key] = value_label

    def _setup_styles(self) -> None:
        """Set up custom styles for the GUI."""
        style = ttk.Style()

        # Configure colors and fonts
        style.configure(
            "Title.TLabel", font=("TkDefaultFont", 12, "bold"), foreground="#2E3440"
        )

        style.configure(
            "Section.TLabel", font=("TkDefaultFont", 10, "bold"), foreground="#2E3440"
        )

        style.configure("Value.TLabel", font=("TkDefaultFont", 9), foreground="#4C566A")

        # Configure button styles
        style.configure("Action.TButton", font=("TkDefaultFont", 9), padding=5)

        style.configure("Nav.TButton", font=("TkDefaultFont", 9), padding=5, width=12)

        # Configure frame styles
        style.configure(
            "Card.TLabelframe", background="#F9F9F9", relief=tk.RIDGE, borderwidth=1
        )

        style.configure(
            "Card.TLabelframe.Label",
            font=("TkDefaultFont", 9, "bold"),
            background="#E5E9F0",
            foreground="#2E3440",
        )

    def _go_to_previous_image(self) -> None:
        """Navigate to previous image."""
        if hasattr(self.app, "image_paths") and self.app.image_paths:
            prev_index = (self.app.current_image_index - 1) % len(self.app.image_paths)
            self.app.show_image(prev_index)

    def _go_to_next_image(self) -> None:
        """Navigate to next image."""
        if hasattr(self.app, "image_paths") and self.app.image_paths:
            next_index = (self.app.current_image_index + 1) % len(self.app.image_paths)
            self.app.show_image(next_index)

    def _apply_current_blur(self) -> None:
        """Apply current blur settings and collect user preferences."""
        if not hasattr(self.app, "collect_user_preference"):
            # Fallback to old behavior if method doesn't exist
            self._apply_current_blur_fallback()
            return

        try:
            # Update status to show processing
            self.status_bar.set_status("Collecting user preference...")
            self.apply_blur_button.config(state=tk.DISABLED, text="Collecting...")

            # Collect user preference for current settings
            self.app.collect_user_preference()

            # Update status to success
            self.status_bar.set_status("Preference collected successfully")

        except Exception as e:
            # Show error message
            self.status_bar.set_status(f"Error collecting preference: {str(e)}")
            messagebox.showerror("Preference Collection Error", str(e))
        finally:
            # Re-enable button
            self.apply_blur_button.config(state=tk.NORMAL, text="Apply Blur")

    def _apply_current_blur_fallback(self) -> None:
        """Fallback method for applying blur (old behavior)."""
        if hasattr(self.app, "_apply_blur_to_current_image"):
            # Update status to show processing
            self.status_bar.set_status("Applying blur...")
            self.apply_blur_button.config(state=tk.DISABLED, text="Applying...")

            try:
                # Apply blur directly and update display
                self.app._apply_blur_to_current_image()

                # Update status to success
                self.status_bar.set_status("Blur applied successfully")

            except Exception as e:
                # Show error message
                self.status_bar.set_status(f"Error applying blur: {str(e)}")
                messagebox.showerror("Blur Application Error", str(e))
            finally:
                # Re-enable button
                self.apply_blur_button.config(state=tk.NORMAL, text="Apply Blur")

    def _reset_blur(self) -> None:
        """Reset blur settings to defaults and set blur type to 'No Blur'."""
        try:
            # Update status to show processing
            self.status_bar.set_status("Resetting blur settings...")
            self.reset_button.config(state=tk.DISABLED)

            # Reset blur type to 'No Blur' first
            if hasattr(self.app, "reset_blur_type_to_no_blur"):
                self.app.reset_blur_type_to_no_blur()

            # Reset parameters to defaults
            if hasattr(self.app, "reset_parameters_to_defaults"):
                self.app.reset_parameters_to_defaults()

            # Clear comparison view
            if hasattr(self.app, "comparison_view") and self.app.comparison_view:
                self.app.comparison_view.clear()

            # Clear quality metrics
            if hasattr(self.app, "quality_metrics") and self.app.quality_metrics:
                self.app.quality_metrics.clear()

            # Update status to success
            self.status_bar.set_status("Blur settings reset to defaults")

        except Exception as e:
            # Show error message
            self.status_bar.set_status(f"Error resetting blur: {str(e)}")
            messagebox.showerror("Reset Error", str(e))
        finally:
            # Re-enable button
            self.reset_button.config(state=tk.NORMAL)

    def _show_about(self) -> None:
        """Show about dialog."""
        about_text = (
            "Blur Suite Interactive Configuration Tool\n\n"
            "Version 1.0.0\n"
            "A comprehensive tool for configuring blur effects "
            "on document images for dataset generation.\n\n"
            "Built with Tkinter and integrated with the Blur Suite SDK."
        )

        messagebox.showinfo("About", about_text)

    def _show_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        shortcuts_text = (
            "Keyboard Shortcuts:\n\n"
            "Ctrl+O    Load Images\n"
            "Ctrl+S    Export Configuration\n"
            "Ctrl+Q    Quit Application\n"
            "Ctrl+R    Reset View\n"
            "Ctrl+F    Fit to Window\n"
            "← / →     Navigate Images\n"
        )

        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)

    def update_navigation_buttons(self) -> None:
        """Update navigation button states based on current image index."""
        if hasattr(self.app, "image_paths") and self.app.image_paths:
            total_images = len(self.app.image_paths)
            current_index = self.app.current_image_index

            # Update counter
            self.image_counter.config(
                text=f"Image {current_index + 1} of {total_images}"
            )

            # Enable/disable buttons at boundaries
            self.prev_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)

            if current_index == 0:
                self.prev_button.config(state=tk.DISABLED)
            elif current_index == total_images - 1:
                self.next_button.config(state=tk.DISABLED)
        else:
            self.image_counter.config(text="No images loaded")
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)

    def update_image_info(self, image_path: str, image: Any) -> None:
        """Update image information display."""
        if not image_path or image is None or image.size == 0:
            return

        try:
            # Get image info
            filename = Path(image_path).name
            height, width = image.shape[:2]
            channels = image.shape[2] if len(image.shape) > 2 else 1
            dtype = str(image.dtype)

            # Try to get file size
            try:
                file_size = Path(image_path).stat().st_size
                size_str = self._format_file_size(file_size)
            except Exception:
                size_str = "Unknown"

            # Update labels
            self.image_info_labels["filename"].config(text=filename)
            self.image_info_labels["dimensions"].config(text=f"{width} × {height}")
            self.image_info_labels["channels"].config(text=str(channels))
            self.image_info_labels["dtype"].config(text=dtype)
            self.image_info_labels["size"].config(text=size_str)

        except Exception:
            # Silently handle errors in image info updates
            pass

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
