"""
Blur Suite Enhanced Plugin System

This module provides advanced plugin management capabilities including
automatic discovery, validation, testing, and template generation.
"""

from .plugin_discovery import PluginDiscovery
from .plugin_manager import PluginManager
from .plugin_template import PluginTemplate
from .plugin_validator import PluginValidator

__all__ = [
    "PluginManager",
    "PluginDiscovery",
    "PluginValidator",
    "PluginTemplate",
]
