"""
Blur Suite Hook System

This module provides extensibility points throughout the SDK
for custom integrations and enhanced functionality.
"""

from .custom_effects import CustomEffectBuilder
from .event_system import EventSystem
from .hook_manager import HookManager
from .hook_points import HookContext, HookPoint

__all__ = [
    "HookManager",
    "HookPoint",
    "HookContext",
    "EventSystem",
    "CustomEffectBuilder",
]
