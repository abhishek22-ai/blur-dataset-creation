"""
Blur Suite CLI Module

This module provides command-line interfaces for the Blur Suite SDK,
including tools for interactive configuration and dataset creation.
"""

__version__ = "1.0.0"
__author__ = "Blur Suite Team"

from .dataset import create_dataset
from .interactive import launch_interactive
from .main import main

__all__ = ["main", "launch_interactive", "create_dataset"]
