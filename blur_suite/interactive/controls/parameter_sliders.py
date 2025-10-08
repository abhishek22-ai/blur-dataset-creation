"""
Parameter adjustment sliders for blur effects.

This module provides dynamic slider controls that adjust based on the selected
blur effect type and allow real-time parameter modification.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional

from ...core.blur.base import Parameter


class ParameterSliders:
    """
    Dynamic parameter slider controls for blur effects.

    Creates appropriate slider controls based on the current blur effect's
    parameters with proper validation and real-time updates.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize parameter sliders widget.

        Args:
            parent: Parent Tkinter widget
            app: Reference to main application instance
        """
        self.parent = parent
        self.app = app

        # Callback for when parameters change
        self.on_parameter_changed: Optional[Callable[[str, Any], None]] = None

        # Current parameters and their controls
        self.current_parameters: Dict[str, Parameter] = {}
        self.slider_controls: Dict[str, Dict[str, tk.Widget]] = {}

        # Create UI components
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the parameter sliders widgets."""
        # Main frame
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable frame for parameters
        self._create_scrollable_frame()

        # Always show the frame - don't hide it initially
        # The frame will show "No parameters available" when no parameters are loaded

    def _create_scrollable_frame(self) -> None:
        """Create scrollable frame for parameter controls."""
        # Canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(self.main_frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.canvas.config(yscrollcommand=self.scrollbar.set)

        # Scrollable frame inside canvas
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Create window in canvas
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor=tk.NW
        )

        # Pack canvas and scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)

    def _on_mouse_wheel(self, event: Any) -> None:
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_parameters(self, parameters: Dict[str, Parameter]) -> None:
        """
        Update the parameter controls for a new set of parameters.

        Args:
            parameters: Dictionary of parameter objects
        """
        try:
            # Validate parameters input
            if not isinstance(parameters, dict):
                print(
                    f"Warning: Invalid parameters type {type(parameters)}, expected dict"
                )
                return

            # Debug logging for parameter analysis
            print(f"DEBUG: Updating parameters with {len(parameters)} parameters")
            for param_name, param in parameters.items():
                print(
                    f"DEBUG: Parameter '{param_name}': value={param.value}, type={type(param.value)}, param_type={param.param_type}"
                )

            # Clear existing controls
            self._clear_controls()

            # Store new parameters
            self.current_parameters = parameters.copy() if parameters else {}

            # Always show the frame - never hide it
            self.main_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

            # Create controls for each parameter, or show "no parameters" message
            if parameters:
                for param_name, param in parameters.items():
                    try:
                        # Validate parameter name and object
                        if not isinstance(param_name, str) or not hasattr(
                            param, "value"
                        ):
                            print(f"Warning: Invalid parameter {param_name}, skipping")
                            continue
                        print(
                            f"DEBUG: Creating control for parameter '{param_name}' of type {type(param.value)}"
                        )
                        self._create_parameter_control(param_name, param)
                    except Exception as e:
                        print(f"Error creating control for parameter {param_name}: {e}")
                        continue
            else:
                print("DEBUG: No parameters provided, showing no parameters message")
                self._show_no_parameters_message()

            # Update scroll region after creating new controls
            try:
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            except (tk.TclError, AttributeError):
                # Canvas might not be properly initialized or bbox might be empty
                # Force update to ensure proper display
                self.canvas.update_idletasks()
        except Exception as e:
            print(f"Error updating parameters: {e}")

    def _show_no_parameters_message(self) -> None:
        """Show a message when no parameters are available."""
        # Create a frame for the message
        message_frame = ttk.Frame(self.scrollable_frame)
        message_frame.pack(fill=tk.X, pady=(20, 0), padx=5)

        # Add message label
        message_label = ttk.Label(
            message_frame,
            text="No parameters available for the current blur type.\n"
            "Select a blur effect with parameters to see controls here.",
            font=("TkDefaultFont", 10),
            foreground="#666",
            justify=tk.CENTER,
        )
        message_label.pack(pady=(10, 0))

        # Store the message frame so it can be cleared later
        self.slider_controls["_no_parameters_message"] = {
            "frame": message_frame,
            "label": message_label,
        }

        # Update scroll region after showing no parameters message
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except (tk.TclError, AttributeError):
            # Canvas might not be properly initialized
            self.canvas.update_idletasks()

    def _clear_controls(self) -> None:
        """Clear all parameter controls."""
        # Destroy existing controls safely
        for controls in self.slider_controls.values():
            for key, widget in controls.items():
                # Skip variables, only destroy widgets
                if key != "var" and widget is not None:
                    try:
                        # Check if widget still exists before destroying
                        if widget.winfo_exists():
                            widget.destroy()
                    except (tk.TclError, AttributeError):
                        # Widget already destroyed or invalid
                        pass

        # Clear the scrollable frame by destroying all its children
        # This ensures no orphaned widgets remain
        try:
            for child in self.scrollable_frame.winfo_children():
                try:
                    if child.winfo_exists():
                        child.destroy()
                except (tk.TclError, AttributeError):
                    # Widget already destroyed or invalid
                    pass
        except (tk.TclError, AttributeError):
            # Frame might not exist
            pass

        # Update canvas scroll region immediately after clearing
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except (tk.TclError, AttributeError):
            # Canvas might not be properly initialized
            pass

        self.slider_controls.clear()
        self.current_parameters.clear()

    def _create_parameter_control(self, param_name: str, param: Parameter) -> None:
        """Create control widgets for a single parameter."""
        print(
            f"DEBUG: Creating parameter control for '{param_name}' with value '{param.value}' of type {type(param.value)}"
        )

        # Parameter frame
        param_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=param_name.replace("_", " ").title(),
            padding="5",
        )
        param_frame.pack(fill=tk.X, pady=(0, 10), padx=5)

        # Configure grid
        param_frame.grid_columnconfigure(1, weight=1)

        # Parameter info
        info_frame = ttk.Frame(param_frame)
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        info_frame.grid_columnconfigure(1, weight=1)

        # Description label
        if param.description:
            print(
                f"DEBUG: Parameter '{param_name}' has description: {param.description}"
            )
            desc_label = ttk.Label(
                info_frame,
                text=param.description,
                font=("TkDefaultFont", 8),
                foreground="#666",
            )
            desc_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 2))

        # Value range label
        range_text = self._get_range_text(param)
        if range_text:
            print(f"DEBUG: Parameter '{param_name}' has range text: {range_text}")
            range_label = ttk.Label(
                info_frame,
                text=range_text,
                font=("TkDefaultFont", 7),
                foreground="#888",
            )
            range_label.grid(row=1, column=0, sticky=tk.W)

        # Current value label
        value_label = ttk.Label(
            info_frame,
            text=f"Current: {param.value}",
            font=("TkDefaultFont", 8, "bold"),
        )
        value_label.grid(row=0, column=1, sticky=tk.E)

        # Control based on parameter type
        print(
            f"DEBUG: Parameter '{param_name}' value type check - bool: {isinstance(param.value, bool)}, numeric: {isinstance(param.value, (int, float))}"
        )
        if isinstance(param.value, bool):
            print(f"DEBUG: Creating boolean control for '{param_name}'")
            self._create_boolean_control(param_frame, param_name, param, value_label)
        elif isinstance(param.value, (int, float)):
            print(
                f"DEBUG: Creating numeric control for '{param_name}' (type: {type(param.value)})"
            )
            self._create_numeric_control(param_frame, param_name, param, value_label)
        else:
            print(
                f"DEBUG: Creating text control for '{param_name}' (type: {type(param.value)})"
            )
            self._create_text_control(param_frame, param_name, param, value_label)

    def _create_boolean_control(
        self,
        parent: ttk.LabelFrame,
        param_name: str,
        param: Parameter,
        value_label: ttk.Label,
    ) -> None:
        """Create boolean control (checkbox)."""
        var = tk.BooleanVar(value=param.value)

        def on_toggle():
            new_value = var.get()
            self._update_parameter(param_name, new_value, value_label)

        checkbox = ttk.Checkbutton(
            parent, text="Enable", variable=var, command=on_toggle
        )
        checkbox.grid(row=1, column=0, sticky=tk.W)

        self.slider_controls[param_name] = {
            "var": var,
            "checkbox": checkbox,
            "value_label": value_label,
        }

    def _create_numeric_control(
        self,
        parent: ttk.LabelFrame,
        param_name: str,
        param: Parameter,
        value_label: ttk.Label,
    ) -> None:
        """Create numeric control (slider + entry)."""
        print(
            f"DEBUG: Creating numeric control for '{param_name}' - min: {param.min_value}, max: {param.max_value}, current: {param.value}"
        )

        # Control frame
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        control_frame.grid_columnconfigure(0, weight=1)

        # Slider
        slider_frame = ttk.Frame(control_frame)
        slider_frame.pack(fill=tk.X, pady=(0, 5))

        # Determine slider range and resolution
        min_val = param.min_value if param.min_value is not None else 0
        max_val = param.max_value if param.max_value is not None else 100
        resolution = 1 if isinstance(param.value, int) else 0.1

        print(
            f"DEBUG: Numeric control '{param_name}' - range: {min_val} to {max_val}, resolution: {resolution}"
        )

        # Create slider variable with proper type handling
        if isinstance(param.value, int):
            var = tk.IntVar(value=int(param.value))
            print(
                f"DEBUG: Created IntVar for '{param_name}' with value {int(param.value)}"
            )
        else:
            var = tk.DoubleVar(value=float(param.value))
            print(
                f"DEBUG: Created DoubleVar for '{param_name}' with value {float(param.value)}"
            )

        def on_slider_change(event=None):
            new_value = var.get()
            # Ensure type consistency
            if isinstance(param.value, int):
                new_value = int(round(new_value))
            else:
                new_value = float(new_value)
            print(f"DEBUG: Slider change for '{param_name}' - new value: {new_value}")
            self._update_parameter(param_name, new_value, value_label)

        slider = ttk.Scale(
            slider_frame,
            from_=min_val,
            to=max_val,
            variable=var,
            orient=tk.HORIZONTAL,
            command=on_slider_change,
        )
        slider.pack(fill=tk.X)

        # Add value entry field and set button for better user control
        # Create entry field for direct value input
        entry_frame = ttk.Frame(control_frame)
        entry_frame.pack(fill=tk.X, pady=(5, 0))

        # Value entry field
        value_entry = ttk.Entry(
            entry_frame, textvariable=var, width=10, font=("TkDefaultFont", 8)
        )
        value_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Set button to apply the entered value
        def on_set_value():
            try:
                new_value = var.get()
                # Ensure type consistency
                if isinstance(param.value, int):
                    new_value = int(round(new_value))
                else:
                    new_value = float(new_value)
                print(
                    f"DEBUG: Set button clicked for '{param_name}' - setting value: {new_value}"
                )
                self._update_parameter(param_name, new_value, value_label)
            except (ValueError, tk.TclError) as e:
                print(f"DEBUG: Invalid value entered for '{param_name}': {e}")

        set_button = ttk.Button(entry_frame, text="Set", command=on_set_value, width=6)
        set_button.pack(side=tk.LEFT)

        # Reset button to restore default value
        def on_reset_value():
            default_value = param.value
            print(
                f"DEBUG: Reset button clicked for '{param_name}' - resetting to default: {default_value}"
            )
            self._update_parameter(param_name, default_value, value_label)

        reset_button = ttk.Button(
            entry_frame, text="Reset", command=on_reset_value, width=6
        )
        reset_button.pack(side=tk.LEFT, padx=(5, 0))

        # Store controls
        self.slider_controls[param_name] = {
            "var": var,
            "slider": slider,
            "value_label": value_label,
            "entry": value_entry,
            "set_button": set_button,
            "reset_button": reset_button,
        }

    def _create_text_control(
        self,
        parent: ttk.LabelFrame,
        param_name: str,
        param: Parameter,
        value_label: ttk.Label,
    ) -> None:
        """Create text control for non-numeric parameters."""
        print(
            f"DEBUG: Creating text control for '{param_name}' with value '{param.value}' (type: {type(param.value)})"
        )

        # For text parameters, just display current value as label since we're removing interactive elements
        current_value_label = ttk.Label(
            parent, text=f"Current: {param.value}", font=("TkDefaultFont", 8, "bold")
        )
        current_value_label.grid(row=1, column=0, sticky=tk.W)

        # Store controls (minimal for text parameters)
        print(f"DEBUG: Text control for '{param_name}' - stored minimal controls")
        self.slider_controls[param_name] = {
            "value_label": value_label,
            "current_value_label": current_value_label,
        }

    def _get_range_text(self, param: Parameter) -> str:
        """Get formatted range text for parameter."""
        if isinstance(param.value, bool):
            return ""

        parts = []
        if param.min_value is not None:
            parts.append(f"Min: {param.min_value}")
        if param.max_value is not None:
            parts.append(f"Max: {param.max_value}")
        if param.allowed_values:
            parts.append(f"Allowed: {param.allowed_values}")

        return " | ".join(parts) if parts else ""

    def _update_parameter(
        self, param_name: str, value: Any, value_label: ttk.Label
    ) -> None:
        """Update parameter value and notify application."""
        try:
            # Validate inputs
            if not isinstance(param_name, str):
                print(f"Warning: Invalid parameter name type {type(param_name)}")
                return

            if value_label is None or not hasattr(value_label, "config"):
                print(f"Warning: Invalid value label for parameter {param_name}")
                return

            # Update value label safely
            try:
                old_text = value_label.cget("text")
                value_label.config(text=f"Current: {value}")
                print(
                    f"DEBUG: Parameter '{param_name}' updated from '{old_text}' to 'Current: {value}'"
                )
            except (tk.TclError, AttributeError):
                # Label might be destroyed
                return

            # Notify application
            if self.on_parameter_changed:
                try:
                    print(
                        f"DEBUG: Notifying application of parameter change: '{param_name}' = {value}"
                    )
                    self.on_parameter_changed(param_name, value)
                except Exception as e:
                    print(f"Error in parameter change callback for {param_name}: {e}")
        except Exception as e:
            print(f"Error updating parameter {param_name}: {e}")

    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Set parameter values programmatically.

        Args:
            parameters: Dictionary of parameter name -> value
        """
        try:
            # Validate input
            if not isinstance(parameters, dict):
                print(
                    f"Warning: Invalid parameters type {type(parameters)}, expected dict"
                )
                return

            for param_name, value in parameters.items():
                try:
                    if not isinstance(param_name, str):
                        print(
                            f"Warning: Invalid parameter name type {type(param_name)}"
                        )
                        continue

                    if param_name not in self.slider_controls:
                        continue

                    controls = self.slider_controls[param_name]

                    # Update control value for sliders and checkboxes
                    if "var" in controls:
                        var = controls["var"]
                        try:
                            if isinstance(var, tk.BooleanVar):
                                var.set(bool(value))
                            elif isinstance(var, tk.IntVar):
                                var.set(int(value))
                            elif isinstance(var, tk.DoubleVar):
                                var.set(float(value))
                        except (ValueError, tk.TclError) as e:
                            print(
                                f"Warning: Invalid value {value} for parameter {param_name}: {e}"
                            )
                            continue

                    # Update value label safely
                    if "value_label" in controls:
                        label = controls["value_label"]
                        try:
                            if hasattr(label, "config"):
                                label.config(text=f"Current: {value}")
                        except (tk.TclError, AttributeError):
                            pass

                    # Update current value label for text parameters
                    if "current_value_label" in controls:
                        label = controls["current_value_label"]
                        try:
                            if hasattr(label, "config"):
                                label.config(text=f"Current: {value}")
                        except (tk.TclError, AttributeError):
                            pass

                    # Update entry field if it exists
                    if "entry" in controls:
                        entry = controls["entry"]
                        try:
                            if hasattr(entry, "delete") and hasattr(entry, "insert"):
                                entry.delete(0, tk.END)
                                entry.insert(0, str(value))
                        except (tk.TclError, AttributeError):
                            pass
                except Exception as e:
                    print(f"Error setting parameter {param_name}: {e}")
                    continue
        except Exception as e:
            print(f"Error in set_parameters: {e}")

    def get_parameter_values(self) -> Dict[str, Any]:
        """Get current values of all parameters."""
        values = {}

        try:
            for param_name, controls in self.slider_controls.items():
                if not isinstance(param_name, str):
                    continue

                if "var" in controls:
                    var = controls["var"]
                    try:
                        if isinstance(var, tk.BooleanVar):
                            values[param_name] = bool(var.get())
                        elif isinstance(var, tk.IntVar):
                            values[param_name] = int(var.get())
                        elif isinstance(var, tk.DoubleVar):
                            values[param_name] = float(var.get())
                        # Note: Text parameters don't have interactive controls anymore
                    except (ValueError, tk.TclError) as e:
                        print(
                            f"Warning: Error getting value for parameter {param_name}: {e}"
                        )
                        continue
        except Exception as e:
            print(f"Error in get_parameter_values: {e}")

        return values

    def enable(self) -> None:
        """Enable all parameter controls."""
        for controls in self.slider_controls.values():
            for widget in controls.values():
                if isinstance(
                    widget, (ttk.Scale, ttk.Checkbutton, ttk.Entry, ttk.Button)
                ):
                    try:
                        if isinstance(widget, ttk.Entry):
                            widget.config(state=tk.NORMAL)
                        elif isinstance(widget, ttk.Button):
                            widget.config(state=tk.NORMAL)
                        else:
                            widget.config(state=tk.NORMAL)
                    except (tk.TclError, AttributeError):
                        # Widget might not support state configuration or might be destroyed
                        pass

    def disable(self) -> None:
        """Disable all parameter controls."""
        for controls in self.slider_controls.values():
            for widget in controls.values():
                if isinstance(
                    widget, (ttk.Scale, ttk.Checkbutton, ttk.Entry, ttk.Button)
                ):
                    try:
                        if isinstance(widget, ttk.Entry):
                            widget.config(state=tk.DISABLED)
                        elif isinstance(widget, ttk.Button):
                            widget.config(state=tk.DISABLED)
                        else:
                            widget.config(state=tk.DISABLED)
                    except (tk.TclError, AttributeError):
                        # Widget might not support state configuration or might be destroyed
                        pass

    def reset_to_defaults(self) -> None:
        """Reset all parameters to their default values."""
        try:
            for param_name, param in self.current_parameters.items():
                try:
                    if not isinstance(param_name, str) or not hasattr(param, "value"):
                        continue

                    if param_name not in self.slider_controls:
                        continue

                    controls = self.slider_controls[param_name]
                    default_value = param.value

                    # Update control for sliders and checkboxes with proper type handling
                    if "var" in controls:
                        var = controls["var"]
                        try:
                            if isinstance(var, tk.BooleanVar):
                                var.set(bool(default_value))
                            elif isinstance(var, tk.IntVar):
                                var.set(int(default_value))
                            elif isinstance(var, tk.DoubleVar):
                                var.set(float(default_value))
                        except (ValueError, tk.TclError) as e:
                            print(
                                f"Warning: Error setting default value for {param_name}: {e}"
                            )
                            continue

                    # Update value label safely
                    if "value_label" in controls:
                        label = controls["value_label"]
                        try:
                            if hasattr(label, "config"):
                                label.config(text=f"Current: {default_value}")
                        except (tk.TclError, AttributeError):
                            pass

                    # Update current value label for text parameters
                    if "current_value_label" in controls:
                        label = controls["current_value_label"]
                        try:
                            if hasattr(label, "config"):
                                label.config(text=f"Current: {default_value}")
                        except (tk.TclError, AttributeError):
                            pass

                    # Update entry field if it exists
                    if "entry" in controls:
                        entry = controls["entry"]
                        try:
                            if hasattr(entry, "delete") and hasattr(entry, "insert"):
                                entry.delete(0, tk.END)
                                entry.insert(0, str(default_value))
                        except (tk.TclError, AttributeError):
                            pass

                    # Notify application
                    if self.on_parameter_changed:
                        try:
                            self.on_parameter_changed(param_name, default_value)
                        except Exception as e:
                            print(f"Error in reset callback for {param_name}: {e}")
                except Exception as e:
                    print(f"Error resetting parameter {param_name}: {e}")
                    continue
        except Exception as e:
            print(f"Error in reset_to_defaults: {e}")
