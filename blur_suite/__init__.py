"""
Blur Suite SDK

A comprehensive Python SDK for image blur effects and processing.
Provides multiple blur algorithms, plugin architecture, and
professional-grade image processing capabilities.

Main Features:
- Multiple blur effect implementations (Gaussian, Motion, Defocus, etc.)
- Plugin architecture for custom blur effects
- Factory pattern for easy effect creation
- Comprehensive parameter validation
- Performance-optimized algorithms
- Support for various image formats
- CPU and GPU acceleration support

Quick Start:
    import blur_suite as bs
    import numpy as np

    # Create a sample image
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    # Create and apply a Gaussian blur
    factory = bs.BlurFactory()
    gaussian = factory.create_effect("gaussian", kernel_size=7, sigma_x=1.5)
    result = gaussian.apply(image)

    # Get the blurred image
    blurred = result.result_image

For more examples and advanced usage, see the documentation for
each submodule and the complete API reference.
"""

from .core import *

# Performance optimizations
try:
    from .core.cache import BlurCache, CacheManager, ConfigCache, ImageCache
    from .core.memory import BufferManager, CleanupManager, ImagePool, MemoryManager
    from .core.processing import (
        AdaptiveScheduler,
        BatchProcessor,
        ParallelProcessor,
        WorkerPool,
    )

    _performance_available = True
except ImportError:
    _performance_available = False

# Extensibility features
try:
    from .core.config import (
        ConfigInheritance,
        ConfigManager,
        ConfigSchema,
        ConfigValidator,
    )
    from .core.hooks import CustomEffectBuilder, EventSystem, HookManager
    from .core.plugins import (
        PluginDiscovery,
        PluginManager,
        PluginTemplate,
        PluginValidator,
    )

    _extensibility_available = True
except ImportError:
    _extensibility_available = False

# Production features
try:
    from .core.recovery import (
        CircuitBreaker,
        ErrorHandler,
        HealthValidator,
        RetryManager,
    )
    from .logging import LogFilter, LogFormatter, LogManager, StructuredLogger
    from .monitoring import (
        HealthChecker,
        MetricsCollector,
        PerformanceMonitor,
        ReportGenerator,
    )

    _production_available = True
except ImportError:
    _production_available = False

# Interactive module (optional import for GUI functionality)
try:
    from .interactive import BlurSuiteApp

    _interactive_available = True
except ImportError:
    _interactive_available = False

__version__ = "2.0.0"
__author__ = "Blur Suite SDK Team"
__description__ = "Comprehensive Python SDK for image blur effects with advanced performance optimizations and production features"

__all__ = [
    # Core exports
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
            "EventSystem",
            "CustomEffectBuilder",
        ]
    )

# Add production feature exports if available
if _production_available:
    __all__.extend(
        [
            "PerformanceMonitor",
            "MetricsCollector",
            "HealthChecker",
            "ReportGenerator",
            "StructuredLogger",
            "LogManager",
            "LogFormatter",
            "LogFilter",
            "ErrorHandler",
            "RetryManager",
            "CircuitBreaker",
            "HealthValidator",
        ]
    )

# Add interactive exports if available
if _interactive_available:
    __all__.append("BlurSuiteApp")
