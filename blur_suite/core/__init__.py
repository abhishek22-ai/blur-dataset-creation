"""
Blur Suite Core Module

This module contains the core functionality of the Blur Suite SDK,
organized into specialized submodules for different aspects of
blur effect processing.

Submodules:
- blur: Complete blur effect system with implementations,
        factory pattern, and plugin architecture

The core module provides the foundation for all blur operations
and serves as the main API for the Blur Suite SDK.
"""

from .blur import *

# Performance optimizations
try:
    from .cache import *
    from .memory import *
    from .processing import *

    _performance_available = True
except ImportError:
    _performance_available = False

# Extensibility features
try:
    from .config import *
    from .hooks import *
    from .plugins import *

    _extensibility_available = True
except ImportError:
    _extensibility_available = False

# Production features
try:
    from ..recovery import *

    _recovery_available = True
except ImportError:
    _recovery_available = False

__all__ = [
    # Re-export blur module contents
    "BlurEffect",
    "BaseBlurEffect",
    "BlurType",
    "Parameter",
    "BlurResult",
    "GaussianBlur",
    "MotionBlur",
    "DefocusBlur",
    "AverageBlur",
    "BilateralBlur",
    "NoBlur",
    "BlurFactory",
    "BlurRegistry",
    "PluginBase",
    "PluginLoader",
    "PluginConfiguration",
    "PluginRegistry",
]

# Add performance optimization exports if available
if _performance_available:
    __all__.extend(
        [
            "CacheManager",
            "ImageCache",
            "BlurCache",
            "ConfigCache",
            "MemoryManager",
            "ImagePool",
            "BufferManager",
            "CleanupManager",
            "ParallelProcessor",
            "BatchProcessor",
            "AdaptiveScheduler",
            "WorkerPool",
        ]
    )

# Add extensibility exports if available
if _extensibility_available:
    __all__.extend(
        [
            "PluginManager",
            "PluginDiscovery",
            "PluginValidator",
            "PluginTemplate",
            "ConfigManager",
            "ConfigSchema",
            "ConfigValidator",
            "ConfigInheritance",
            "HookManager",
            "HookPoint",
            "HookContext",
            "EventSystem",
            "CustomEffectBuilder",
        ]
    )

# Add recovery exports if available
if _recovery_available:
    __all__.extend(
        [
            "ErrorHandler",
            "RetryManager",
            "CircuitBreaker",
            "HealthValidator",
        ]
    )
