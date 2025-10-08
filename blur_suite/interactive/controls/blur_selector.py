"""
Blur type selector widget for the interactive configuration tool.

This module provides a dropdown widget for selecting different blur effect types
with descriptions and real-time preview of available options.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional

from ...core.blur import BlurType, list_blur_effects


class BlurSelector:
    """
    Widget for selecting blur effect types.

    Provides a dropdown with all available blur types, descriptions,
    and real-time updates when selection changes.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize blur selector widget.

        Args:
            parent: Parent Tkinter widget
            app: Reference to main application instance
        """
        self.parent = parent
        self.app = app

        # Callback for when blur type changes
        self.on_blur_type_changed: Optional[Callable[[str], None]] = None

        # Available blur effects
        self.blur_effects = self._get_available_effects()

        # Create UI components
        self._create_widgets()

        # Set initial selection
        self._set_initial_selection()

    def _get_available_effects(self) -> Dict[str, Dict[str, Any]]:
        """Get available blur effects from the factory."""
        try:
            effects = list_blur_effects()
            blur_effects = {}

            for effect in effects:
                blur_type = effect.get("blur_type", "")
                name = effect.get("name", blur_type)

                blur_effects[name] = {
                    "name": name,
                    "description": effect.get("description", ""),
                    "blur_type": blur_type,
                    "category": effect.get("category", "general"),
                    "tags": effect.get("tags", []),
                    "default_parameters": effect.get("default_parameters", {}),
                }

            return blur_effects

        except Exception as e:
            print(f"Error getting blur effects: {str(e)}")
            # Return fallback effects
            return self._get_fallback_effects()

    def _get_fallback_effects(self) -> Dict[str, Dict[str, Any]]:
        """Get fallback blur effects if factory fails."""
        return {
            "Gaussian Blur": {
                "name": "Gaussian Blur",
                "description": "Applies Gaussian blur using convolution with a Gaussian kernel",
                "blur_type": BlurType.GAUSSIAN.value,
                "category": "smoothing",
                "tags": ["gaussian", "convolution", "smoothing"],
                "default_parameters": {
                    "kernel_size": 5,
                    "sigma_x": 1.0,
                    "sigma_y": 1.0,
                },
            },
            "Motion Blur": {
                "name": "Motion Blur",
                "description": "Simulates motion blur in a specific direction",
                "blur_type": BlurType.MOTION.value,
                "category": "motion",
                "tags": ["motion", "directional", "linear"],
                "default_parameters": {"angle": 0.0, "length": 10},
            },
            "Defocus Blur": {
                "name": "Defocus Blur",
                "description": "Simulates camera defocus or bokeh effect",
                "blur_type": BlurType.DEFOCUS.value,
                "category": "depth",
                "tags": ["defocus", "bokeh", "circular"],
                "default_parameters": {"radius": 5, "strength": 1.0},
            },
            "Average Blur": {
                "name": "Average Blur",
                "description": "Simple averaging blur using mean filtering",
                "blur_type": BlurType.AVERAGE.value,
                "category": "smoothing",
                "tags": ["average", "mean", "simple"],
                "default_parameters": {"kernel_size": 5},
            },
            "Bilateral Blur": {
                "name": "Bilateral Blur",
                "description": "Edge-preserving blur that maintains sharp edges",
                "blur_type": BlurType.BILATERAL.value,
                "category": "edge-preserving",
                "tags": ["bilateral", "edge-preserving", "denoising"],
                "default_parameters": {
                    "diameter": 9,
                    "sigma_color": 75.0,
                    "sigma_space": 75.0,
                },
            },
            "No Blur": {
                "name": "No Blur",
                "description": "Pass-through effect that returns the original image unchanged",
                "blur_type": BlurType.NO_BLUR.value,
                "category": "utility",
                "tags": ["passthrough", "identity", "none"],
                "default_parameters": {},
            },
        }

    def _create_widgets(self) -> None:
        """Create the blur selector widgets."""
        # Main frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.X, pady=(0, 5))

        # Selector label
        self.label = ttk.Label(
            self.main_frame, text="Blur Type:", font=("TkDefaultFont", 9, "bold")
        )
        self.label.pack(anchor=tk.W, pady=(0, 5))

        # Blur type dropdown
        self.blur_combo = ttk.Combobox(
            self.main_frame, state="readonly", font=("TkDefaultFont", 9)
        )
        self.blur_combo.pack(fill=tk.X, pady=(0, 5))

        # Description text area
        self.description_frame = ttk.LabelFrame(
            self.main_frame, text="Description", padding="5"
        )
        self.description_frame.pack(fill=tk.X, pady=(5, 0))

        self.description_text = tk.Text(
            self.description_frame,
            height=3,
            wrap=tk.WORD,
            font=("TkDefaultFont", 8),
            bg="white",
            relief=tk.FLAT,
        )
        self.description_text.pack(fill=tk.BOTH, expand=True)

        # Make description read-only
        self.description_text.config(state=tk.DISABLED)

        # Bind events
        self.blur_combo.bind("<<ComboboxSelected>>", self._on_blur_type_selected)

        # Populate dropdown
        self._populate_dropdown()

    def _populate_dropdown(self) -> None:
        """Populate the dropdown with available blur types."""
        # Sort effects by name for consistent ordering
        effect_names = sorted(self.blur_effects.keys())

        self.blur_combo["values"] = effect_names

        # Set up display mapping for user-friendly names
        self.name_mapping = {name: name for name in effect_names}

    def _set_initial_selection(self) -> None:
        """Set initial selection to 'No Blur' by default."""
        if self.blur_effects:
            # Try to set 'No Blur' as default, fall back to first effect if not available
            if "No Blur" in self.blur_effects:
                self.blur_combo.set("No Blur")
                self._update_description("No Blur")
            else:
                first_effect = next(iter(self.blur_effects.keys()))
                self.blur_combo.set(first_effect)
                self._update_description(first_effect)

    def _on_blur_type_selected(self, event: Any = None) -> None:
        """Handle blur type selection change."""
        selected_name = self.blur_combo.get()

        if not selected_name or selected_name not in self.blur_effects:
            return

        # Check if this is actually a change (not the same selection)
        current_selection = getattr(self, "_current_selection", None)
        is_same_selection = current_selection == selected_name

        # Store current selection
        self._current_selection = selected_name

        # Update description
        self._update_description(selected_name)

        # Get blur effect info
        effect_info = self.blur_effects[selected_name]

        # Only notify application if this is actually a change
        if self.on_blur_type_changed and not is_same_selection:
            self.on_blur_type_changed(effect_info["blur_type"])

        # Only reset parameters to defaults if blur type actually changed
        if hasattr(self.app, "reset_parameters_to_defaults") and not is_same_selection:
            self.app.reset_parameters_to_defaults()

    def _update_description(self, effect_name: str) -> None:
        """Update the description text area."""
        if effect_name not in self.blur_effects:
            return

        effect_info = self.blur_effects[effect_name]

        # Update description text
        self.description_text.config(state=tk.NORMAL)
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(1.0, effect_info["description"])
        self.description_text.config(state=tk.DISABLED)

    def set_blur_type(self, blur_type: str) -> None:
        """
        Set the selected blur type programmatically.

        Args:
            blur_type: Blur type value (e.g., 'gaussian', 'motion')
        """
        # Find the effect name that matches this blur type
        for name, effect_info in self.blur_effects.items():
            if effect_info["blur_type"] == blur_type:
                self.blur_combo.set(name)
                self._update_description(name)

                # Notify application
                if self.on_blur_type_changed:
                    self.on_blur_type_changed(blur_type)
                break

    def get_selected_blur_type(self) -> Optional[str]:
        """Get the currently selected blur type value."""
        selected_name = self.blur_combo.get()

        if selected_name and selected_name in self.blur_effects:
            return self.blur_effects[selected_name]["blur_type"]

        return None

    def get_selected_effect_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently selected effect."""
        selected_name = self.blur_combo.get()

        if selected_name and selected_name in self.blur_effects:
            return self.blur_effects[selected_name]

        return None

    def refresh_effects(self) -> None:
        """Refresh the list of available blur effects."""
        self.blur_effects = self._get_available_effects()
        self._populate_dropdown()
        self._set_initial_selection()

    def enable(self) -> None:
        """Enable the blur selector widget."""
        self.blur_combo.config(state="readonly")

    def disable(self) -> None:
        """Disable the blur selector widget."""
        self.blur_combo.config(state=tk.DISABLED)
