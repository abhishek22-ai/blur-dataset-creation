"""
Blur Suite Plugin System

This module provides the plugin architecture for extending the blur
system with custom blur effect implementations.

The plugin system allows developers to:
- Create custom blur algorithms
- Extend existing functionality
- Add new blur effect types
- Integrate with third-party libraries

Plugin Components:
- PluginBase: Abstract base class for all plugins
- PluginLoader: Handles plugin loading and validation
- PluginRegistry: Manages plugin lifecycle and discovery

Example Plugin:
    from blur_suite.core.blur.plugins.base import PluginBase
    from blur_suite.core.blur.base import BlurType, Parameter

    class MyCustomBlur(PluginBase):
        def __init__(self):
            super().__init__(BlurType.GAUSSIAN)
            self.plugin_name = "MyCustomBlur"

        def _define_parameters(self):
            return {
                "strength": Parameter("strength", 1.0, float, 0.0, 5.0)
            }

        def _apply_blur(self, image):
            # Implement your custom algorithm
            return image  # placeholder
"""

from .base import PluginBase, PluginLoader
from .registry import PluginConfiguration, PluginRegistry

__all__ = [
    "PluginBase",
    "PluginLoader",
    "PluginConfiguration",
    "PluginRegistry",
]
