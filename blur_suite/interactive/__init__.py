"""
Blur Suite Interactive Configuration Tool

This module provides a comprehensive graphical user interface for configuring
blur effects on document images. It allows users to visually configure blur
parameters, preview results in real-time, and export configurations for
dataset generation.

Main Components:
- BlurSuiteApp: Main application coordinator
- GUI Framework: Professional Tkinter-based interface
- Control Widgets: Interactive parameter controls
- Preview System: Real-time image comparison
- Export System: Configuration and dataset generation

Quick Start:
    from blur_suite.interactive import BlurSuiteApp

    # Create and run the application
    app = BlurSuiteApp()
    app.create_gui()
    app.run()

For more detailed usage, see the documentation for each submodule.
"""

from .app import BlurSuiteApp

__version__ = "1.0.0"
__author__ = "Blur Suite SDK Team"
__description__ = "Interactive blur configuration tool"

__all__ = [
    "BlurSuiteApp",
]
