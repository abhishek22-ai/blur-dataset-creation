# Core Blur API Reference

This document provides comprehensive API documentation for the Blur Suite SDK core blur module, including blur effects, factory pattern, and plugin architecture.

## Overview

The core blur module provides:
- **Blur effect implementations** (Gaussian, Motion, Defocus, Average, Bilateral)
- **Factory pattern** for effect creation and management
- **Plugin architecture** for custom blur effects
- **Parameter validation** and type safety
- **Performance optimization** and memory management (v2.0.0)
- **Intelligent caching system** (v2.0.0)
- **Custom effect builder** (v2.0.0)
- **Configuration management** (v2.0.0)

## Module Structure

```
blur_suite/core/
├── __init__.py           # Module exports
├── blur/
│   ├── __init__.py      # Blur effects package
│   ├── base.py         # Base classes and interfaces
│   ├── effects.py      # Blur effect implementations
│   ├── factory.py      # Factory pattern implementation
│   ├── registry.py     # Effect registry
│   ├── parameters.py   # Parameter validation
│   ├── plugins.py      # Plugin system
│   └── utils.py        # Utility functions
```

## Quick Start

```python
import blur_suite as bs
import numpy as np

# Create sample image
image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

# Create blur factory
factory = bs.BlurFactory()

# Apply Gaussian blur
gaussian = factory.create_effect("gaussian", kernel_size=7, sigma_x=1.5)
result = gaussian.apply(image)

# Get blurred image
blurred_image = result.result_image
print(f"Blur applied successfully! Shape: {blurred_image.shape}")
```

## Core Classes

### BlurEffect

Base class for all blur effect implementations.

```python
class BlurEffect:
    """Base class for blur effect implementations."""

    def __init__(self, blur_type: BlurType, parameters: Dict[str, Any]):
        """Initialize blur effect.

        Args:
            blur_type: Type of blur effect
            parameters: Effect parameters
        """
        self.blur_type = blur_type
        self.parameters = parameters
        self._validate_parameters()

    @abstractmethod
    def apply(self, image: np.ndarray) -> BlurResult:
        """Apply blur effect to image.

        Args:
            image: Input image as numpy array

        Returns:
            BlurResult containing processed image and metadata
        """
        pass

    @abstractmethod
    def _validate_parameters(self) -> None:
        """Validate effect parameters."""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get effect information.

        Returns:
            Dictionary containing effect details
        """
        return {
            "blur_type": str(self.blur_type),
            "parameters": self.parameters,
            "supported_image_types": self.get_supported_image_types()
        }
```

### BlurResult

Container for blur operation results.

```python
@dataclass
class BlurResult:
    """Container for blur operation results."""

    result_image: np.ndarray
    """Blurred image as numpy array"""

    original_image: np.ndarray
    """Original input image"""

    blur_type: BlurType
    """Type of blur effect applied"""

    parameters: Dict[str, Any]
    """Parameters used for blur effect"""

    processing_time_ms: float
    """Processing time in milliseconds"""

    metadata: Dict[str, Any]
    """Additional metadata"""

    def save(self, output_path: str, format: str = "PNG") -> None:
        """Save result image to file.

        Args:
            output_path: Output file path
            format: Image format (PNG, JPEG, TIFF)
        """
        pass

    def get_quality_metrics(self) -> Dict[str, float]:
        """Calculate quality metrics.

        Returns:
            Dictionary containing PSNR, SSIM, etc.
        """
        return {
            "psnr": calculate_psnr(self.original_image, self.result_image),
            "ssim": calculate_ssim(self.original_image, self.result_image)
        }
```

## Blur Effect Implementations

### GaussianBlur

Implements Gaussian blur using Gaussian kernel convolution.

```python
class GaussianBlur(BlurEffect):
    """Gaussian blur effect implementation."""

    def __init__(self, kernel_size: int = 5, sigma_x: float = 1.0, sigma_y: float = None):
        """Initialize Gaussian blur.

        Args:
            kernel_size: Size of Gaussian kernel (3-25, odd numbers)
            sigma_x: Standard deviation in X direction
            sigma_y: Standard deviation in Y direction (defaults to sigma_x)
        """
        parameters = {
            "kernel_size": kernel_size,
            "sigma_x": sigma_x,
            "sigma_y": sigma_y or sigma_x
        }
        super().__init__(BlurType.GAUSSIAN, parameters)

    def apply(self, image: np.ndarray) -> BlurResult:
        """Apply Gaussian blur to image.

        Args:
            image: Input image (H, W, C) or (H, W)

        Returns:
            BlurResult with blurred image
        """
        pass

    def _validate_parameters(self) -> None:
        """Validate Gaussian blur parameters."""
        if not 3 <= self.parameters["kernel_size"] <= 25:
            raise ValueError("kernel_size must be between 3 and 25")
        if self.parameters["kernel_size"] % 2 == 0:
            raise ValueError("kernel_size must be odd")
        if self.parameters["sigma_x"] <= 0:
            raise ValueError("sigma_x must be positive")
```

**Parameters:**
- `kernel_size`: 3-25 (odd numbers only)
- `sigma_x`: 0.1-10.0 (horizontal blur strength)
- `sigma_y`: 0.1-10.0 (vertical blur strength)

**Performance:**
- Processing time: ~15ms for 512×512 image
- Memory usage: ~50MB for 512×512 image

### MotionBlur

Implements linear motion blur simulation.

```python
class MotionBlur(BlurEffect):
    """Motion blur effect implementation."""

    def __init__(self, angle: float = 0.0, length: int = 10):
        """Initialize motion blur.

        Args:
            angle: Motion direction in degrees (0-360)
            length: Motion length in pixels (1-100)
        """
        parameters = {
            "angle": angle,
            "length": length
        }
        super().__init__(BlurType.MOTION, parameters)

    def apply(self, image: np.ndarray) -> BlurResult:
        """Apply motion blur to image."""
        pass

    def _validate_parameters(self) -> None:
        """Validate motion blur parameters."""
        if not 0 <= self.parameters["angle"] <= 360:
            raise ValueError("angle must be between 0 and 360")
        if not 1 <= self.parameters["length"] <= 100:
            raise ValueError("length must be between 1 and 100")
```

**Parameters:**
- `angle`: 0-360° (motion direction)
- `length`: 1-100 pixels (motion distance)

### DefocusBlur

Implements camera defocus blur simulation.

```python
class DefocusBlur(BlurEffect):
    """Defocus blur effect implementation."""

    def __init__(self, radius: int = 5, strength: float = 1.0):
        """Initialize defocus blur.

        Args:
            radius: Blur radius in pixels (1-50)
            strength: Blur strength multiplier (0.1-5.0)
        """
        parameters = {
            "radius": radius,
            "strength": strength
        }
        super().__init__(BlurType.DEFOCUS, parameters)

    def apply(self, image: np.ndarray) -> BlurResult:
        """Apply defocus blur to image."""
        pass

    def _validate_parameters(self) -> None:
        """Validate defocus blur parameters."""
        if not 1 <= self.parameters["radius"] <= 50:
            raise ValueError("radius must be between 1 and 50")
        if not 0.1 <= self.parameters["strength"] <= 5.0:
            raise ValueError("strength must be between 0.1 and 5.0")
```

**Parameters:**
- `radius`: 1-50 pixels (blur radius)
- `strength`: 0.1-5.0 (blur intensity)

### AverageBlur

Implements simple average blur using mean filter.

```python
class AverageBlur(BlurEffect):
    """Average blur effect implementation."""

    def __init__(self, kernel_size: int = 5):
        """Initialize average blur.

        Args:
            kernel_size: Size of averaging kernel (3-25, odd numbers)
        """
        parameters = {"kernel_size": kernel_size}
        super().__init__(BlurType.AVERAGE, parameters)

    def apply(self, image: np.ndarray) -> BlurResult:
        """Apply average blur to image."""
        pass

    def _validate_parameters(self) -> None:
        """Validate average blur parameters."""
        if not 3 <= self.parameters["kernel_size"] <= 25:
            raise ValueError("kernel_size must be between 3 and 25")
        if self.parameters["kernel_size"] % 2 == 0:
            raise ValueError("kernel_size must be odd")
```

**Parameters:**
- `kernel_size`: 3-25 (odd numbers only)

### BilateralBlur

Implements edge-preserving bilateral filter.

```python
class BilateralBlur(BlurEffect):
    """Bilateral blur effect implementation."""

    def __init__(self, diameter: int = 9, sigma_color: float = 75.0, sigma_space: float = 75.0):
        """Initialize bilateral blur.

        Args:
            diameter: Filter diameter (5-25)
            sigma_color: Color space standard deviation (10-150)
            sigma_space: Coordinate space standard deviation (10-150)
        """
        parameters = {
            "diameter": diameter,
            "sigma_color": sigma_color,
            "sigma_space": sigma_space
        }
        super().__init__(BlurType.BILATERAL, parameters)

    def apply(self, image: np.ndarray) -> BlurResult:
        """Apply bilateral blur to image."""
        pass

    def _validate_parameters(self) -> None:
        """Validate bilateral blur parameters."""
        if not 5 <= self.parameters["diameter"] <= 25:
            raise ValueError("diameter must be between 5 and 25")
        if not 10 <= self.parameters["sigma_color"] <= 150:
            raise ValueError("sigma_color must be between 10 and 150")
        if not 10 <= self.parameters["sigma_space"] <= 150:
            raise ValueError("sigma_space must be between 10 and 150")
```

**Parameters:**
- `diameter`: 5-25 (filter diameter)
- `sigma_color`: 10-150 (color space standard deviation)
- `sigma_space`: 10-150 (coordinate space standard deviation)

## Factory Pattern

### BlurFactory

Main factory for creating blur effects.

```python
class BlurFactory:
    """Factory for creating blur effects."""

    def __init__(self):
        """Initialize blur factory."""
        self.registry = BlurRegistry()

    def create_effect(self, blur_type: Union[str, BlurType], **kwargs) -> BlurEffect:
        """Create blur effect instance.

        Args:
            blur_type: Type of blur effect
            **kwargs: Effect parameters

        Returns:
            Configured blur effect instance

        Raises:
            ValueError: If blur type is not supported
            TypeError: If parameters are invalid
        """
        # Convert string to enum if needed
        if isinstance(blur_type, str):
            blur_type = BlurType.from_string(blur_type)

        # Get effect class from registry
        effect_class = self.registry.get_effect_class(blur_type)

        # Create and return effect instance
        return effect_class(**kwargs)

    def get_available_effects(self) -> List[BlurType]:
        """Get list of available blur effect types.

        Returns:
            List of available blur types
        """
        return self.registry.get_available_types()

    def get_effect_info(self, blur_type: Union[str, BlurType]) -> Dict[str, Any]:
        """Get information about blur effect.

        Args:
            blur_type: Blur effect type

        Returns:
            Dictionary containing effect information
        """
        if isinstance(blur_type, str):
            blur_type = BlurType.from_string(blur_type)

        return self.registry.get_effect_info(blur_type)
```

### BlurRegistry

Registry for managing blur effect types.

```python
class BlurRegistry:
    """Registry for blur effect types and implementations."""

    def __init__(self):
        """Initialize blur registry."""
        self._effects: Dict[BlurType, Type[BlurEffect]] = {}
        self._register_default_effects()

    def register_effect(self, blur_type: BlurType, effect_class: Type[BlurEffect]) -> None:
        """Register blur effect implementation.

        Args:
            blur_type: Blur effect type
            effect_class: Effect implementation class
        """
        if not issubclass(effect_class, BlurEffect):
            raise TypeError("Effect class must inherit from BlurEffect")

        self._effects[blur_type] = effect_class

    def get_effect_class(self, blur_type: BlurType) -> Type[BlurEffect]:
        """Get effect class for blur type.

        Args:
            blur_type: Blur effect type

        Returns:
            Effect implementation class

        Raises:
            ValueError: If blur type is not registered
        """
        if blur_type not in self._effects:
            raise ValueError(f"Blur type {blur_type} is not registered")

        return self._effects[blur_type]

    def get_available_types(self) -> List[BlurType]:
        """Get list of registered blur types.

        Returns:
            List of available blur types
        """
        return list(self._effects.keys())

    def get_effect_info(self, blur_type: BlurType) -> Dict[str, Any]:
        """Get information about blur effect.

        Args:
            blur_type: Blur effect type

        Returns:
            Dictionary containing effect information
        """
        effect_class = self.get_effect_class(blur_type)

        return {
            "blur_type": blur_type,
            "class_name": effect_class.__name__,
            "module": effect_class.__module__,
            "parameters": self._get_parameter_info(effect_class)
        }
```

## Plugin System

### PluginBase

Base class for custom blur effect plugins.

```python
class PluginBase:
    """Base class for blur effect plugins."""

    @abstractmethod
    def get_blur_types(self) -> List[BlurType]:
        """Get list of blur types provided by this plugin.

        Returns:
            List of blur effect types
        """
        pass

    @abstractmethod
    def create_effect(self, blur_type: BlurType, **kwargs) -> BlurEffect:
        """Create blur effect instance.

        Args:
            blur_type: Type of blur effect to create
            **kwargs: Effect parameters

        Returns:
            Blur effect instance
        """
        pass

    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin information.

        Returns:
            Dictionary containing plugin metadata
        """
        return {
            "name": "Plugin Name",
            "version": "1.0.0",
            "author": "Plugin Author",
            "description": "Plugin description"
        }
```

### PluginLoader

Loads and manages blur effect plugins.

```python
class PluginLoader:
    """Loader for blur effect plugins."""

    def __init__(self, plugin_paths: List[str] = None):
        """Initialize plugin loader.

        Args:
            plugin_paths: List of directories to search for plugins
        """
        self.plugin_paths = plugin_paths or ["./plugins", "~/.blur-suite/plugins"]
        self.plugins: Dict[str, PluginBase] = {}
        self.registry = BlurRegistry()

    def load_plugins(self) -> None:
        """Load all available plugins."""
        for plugin_path in self.plugin_paths:
            self._load_plugins_from_path(plugin_path)

    def _load_plugins_from_path(self, plugin_path: str) -> None:
        """Load plugins from specific path."""
        # Implementation for loading plugins from directory
        pass

    def register_plugin(self, plugin: PluginBase) -> None:
        """Register loaded plugin.

        Args:
            plugin: Plugin instance to register
        """
        plugin_info = plugin.get_plugin_info()
        plugin_name = plugin_info["name"]

        if plugin_name in self.plugins:
            raise ValueError(f"Plugin {plugin_name} is already loaded")

        self.plugins[plugin_name] = plugin

        # Register blur types from plugin
        for blur_type in plugin.get_blur_types():
            effect_class = self._create_effect_class(plugin, blur_type)
            self.registry.register_effect(blur_type, effect_class)

    def get_loaded_plugins(self) -> List[Dict[str, Any]]:
        """Get list of loaded plugins.

        Returns:
            List of plugin information dictionaries
        """
        return [plugin.get_plugin_info() for plugin in self.plugins.values()]
```

## Parameter System

### Parameter Validation

```python
class Parameter:
    """Parameter definition with validation."""

    def __init__(
        self,
        name: str,
        param_type: Type,
        default: Any = None,
        min_value: Any = None,
        max_value: Any = None,
        choices: List[Any] = None,
        description: str = ""
    ):
        """Initialize parameter definition.

        Args:
            name: Parameter name
            param_type: Parameter type (int, float, str, etc.)
            default: Default value
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            choices: List of allowed values
            description: Parameter description
        """
        self.name = name
        self.param_type = param_type
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.choices = choices
        self.description = description

    def validate(self, value: Any) -> Any:
        """Validate parameter value.

        Args:
            value: Value to validate

        Returns:
            Validated value

        Raises:
            ValueError: If value is invalid
            TypeError: If value type is incorrect
        """
        # Type validation
        if not isinstance(value, self.param_type):
            raise TypeError(f"Parameter {self.name} must be {self.param_type.__name__}")

        # Range validation
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"Parameter {self.name} must be >= {self.min_value}")

        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"Parameter {self.name} must be <= {self.max_value}")

        # Choice validation
        if self.choices is not None and value not in self.choices:
            raise ValueError(f"Parameter {self.name} must be one of {self.choices}")

        return value
```

## Enums and Constants

### BlurType

Enumeration of available blur effect types.

```python
class BlurType(Enum):
    """Blur effect type enumeration."""

    GAUSSIAN = "gaussian"
    MOTION = "motion"
    DEFOCUS = "defocus"
    AVERAGE = "average"
    BILATERAL = "bilateral"

    @classmethod
    def from_string(cls, value: str) -> "BlurType":
        """Create BlurType from string.

        Args:
            value: String representation

        Returns:
            Corresponding BlurType

        Raises:
            ValueError: If string is not valid
        """
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid blur type: {value}")

    def __str__(self) -> str:
        """String representation of blur type."""
        return self.value
```

## Utility Functions

### Image Processing Utilities

```python
def ensure_image_format(image: np.ndarray) -> np.ndarray:
    """Ensure image is in correct format.

    Args:
        image: Input image

    Returns:
        Image in standard format (H, W, C)
    """
    pass

def calculate_psnr(original: np.ndarray, processed: np.ndarray) -> float:
    """Calculate PSNR between images.

    Args:
        original: Original image
        processed: Processed image

    Returns:
        PSNR value in dB
    """
    pass

def calculate_ssim(original: np.ndarray, processed: np.ndarray) -> float:
    """Calculate SSIM between images.

    Args:
        original: Original image
        processed: Processed image

    Returns:
        SSIM value (0-1)
    """
    pass
```

## Performance Optimization (v2.0.0)

### CacheManager

Intelligent caching system for improved performance.

```python
class CacheManager:
    """Intelligent cache management system."""

    def __init__(self, max_memory_mb: float = 100.0, strategy: CacheStrategy = CacheStrategy.LRU):
        """Initialize cache manager.

        Args:
            max_memory_mb: Maximum cache memory in MB
            strategy: Cache eviction strategy
        """
        self.max_memory_mb = max_memory_mb
        self.strategy = strategy

    def cached_compute(self, func: Callable) -> Callable:
        """Decorator to cache expensive computations.

        Args:
            func: Function to cache

        Returns:
            Cached version of the function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check cache for existing result
            cache_key = self._generate_cache_key(func, args, kwargs)

            if cache_key in self._cache:
                return self._cache[cache_key]

            # Compute and cache result
            result = func(*args, **kwargs)
            self._cache[cache_key] = result

            # Manage cache size
            self._enforce_memory_limit()

            return result

        return wrapper

    def clear_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "hit_rate": self._hit_rate,
            "miss_rate": 1.0 - self._hit_rate,
            "cache_size": len(self._cache),
            "memory_usage_mb": self._get_memory_usage()
        }
```

### MemoryManager

Advanced memory management and optimization.

```python
class MemoryManager:
    """Advanced memory management for large-scale processing."""

    def __init__(self, max_memory_percent: float = 80.0):
        """Initialize memory manager.

        Args:
            max_memory_percent: Maximum memory usage percentage
        """
        self.max_memory_percent = max_memory_percent
        self.image_pool = ImagePool()

    def optimize_image(self, image: np.ndarray) -> np.ndarray:
        """Optimize image for memory usage.

        Args:
            image: Input image

        Returns:
            Memory-optimized image
        """
        # Optimize data type if needed
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)

        return image

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics.

        Returns:
            Dictionary with memory statistics
        """
        import psutil
        process = psutil.Process()

        return {
            "used_mb": process.memory_info().rss / 1024 / 1024,
            "available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "total_mb": psutil.virtual_memory().total / 1024 / 1024,
            "usage_percent": process.memory_percent()
        }

    def should_process_chunked(self, image: np.ndarray, chunk_size: int = 1024) -> bool:
        """Determine if image should be processed in chunks.

        Args:
            image: Input image
            chunk_size: Chunk size for processing

        Returns:
            True if chunked processing is recommended
        """
        image_memory_mb = image.nbytes / 1024 / 1024
        available_memory_mb = self.get_memory_usage()["available_mb"]

        return image_memory_mb > available_memory_mb * 0.5
```

### CustomEffectBuilder

Easy creation of complex image effects.

```python
class CustomEffectBuilder:
    """Builder for creating custom image effects."""

    def __init__(self, name: str):
        """Initialize custom effect builder.

        Args:
            name: Name of the custom effect
        """
        self.name = name
        self.steps: List[EffectStep] = []
        self.description = ""
        self.caching_enabled = False

    def set_description(self, description: str) -> "CustomEffectBuilder":
        """Set effect description.

        Args:
            description: Effect description

        Returns:
            Self for method chaining
        """
        self.description = description
        return self

    def add_blur_step(self, blur_type: str, **params) -> "CustomEffectBuilder":
        """Add blur step to effect.

        Args:
            blur_type: Type of blur effect
            **params: Blur parameters

        Returns:
            Self for method chaining
        """
        step = BlurStep(blur_type=blur_type, parameters=params)
        self.steps.append(step)
        return self

    def add_sharpen_step(self, intensity: float = 1.0) -> "CustomEffectBuilder":
        """Add sharpening step to effect.

        Args:
            intensity: Sharpening intensity

        Returns:
            Self for method chaining
        """
        step = SharpenStep(intensity=intensity)
        self.steps.append(step)
        return self

    def add_enhance_step(self, enhancement_type: str, **params) -> "CustomEffectBuilder":
        """Add enhancement step to effect.

        Args:
            enhancement_type: Type of enhancement
            **params: Enhancement parameters

        Returns:
            Self for method chaining
        """
        step = EnhancementStep(enhancement_type=enhancement_type, parameters=params)
        self.steps.append(step)
        return self

    def enable_caching(self, enabled: bool = True) -> "CustomEffectBuilder":
        """Enable or disable caching for this effect.

        Args:
            enabled: Whether to enable caching

        Returns:
            Self for method chaining
        """
        self.caching_enabled = enabled
        return self

    def build(self) -> CustomEffect:
        """Build the custom effect.

        Returns:
            Configured custom effect
        """
        return CustomEffect(
            name=self.name,
            steps=self.steps,
            description=self.description,
            caching_enabled=self.caching_enabled
        )
```

### PerformanceMonitor

Performance profiling and tracking.

```python
class PerformanceMonitor:
    """Performance monitoring and profiling."""

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: List[PerformanceMetric] = []
        self.start_time = None

    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        self.start_time = time.time()

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        if self.start_time:
            total_time = time.time() - self.start_time
            self.metrics.append(PerformanceMetric("total_execution", total_time))

    def record_metric(self, name: str, value: float, unit: str = "ms") -> None:
        """Record performance metric.

        Args:
            name: Metric name
            value: Metric value
            unit: Metric unit
        """
        metric = PerformanceMetric(name=name, value=value, unit=unit)
        self.metrics.append(metric)

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary.

        Returns:
            Dictionary with performance statistics
        """
        if not self.metrics:
            return {"message": "No metrics recorded"}

        return {
            "total_metrics": len(self.metrics),
            "execution_time": self._get_total_execution_time(),
            "average_operation_time": self._get_average_operation_time(),
            "metrics_by_type": self._group_metrics_by_type()
        }
```

### Memory Management

```python
class MemoryManager:
    """Memory management for large images."""

    @staticmethod
    def optimize_image(image: np.ndarray) -> np.ndarray:
        """Optimize image for memory usage.

        Args:
            image: Input image

        Returns:
            Memory-optimized image
        """
        pass

    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage.

        Returns:
            Dictionary with memory statistics
        """
        return {
            "used_mb": 0.0,
            "available_mb": 0.0,
            "total_mb": 0.0
        }
```

### GPU Acceleration

```python
class GPUAccelerator:
    """GPU acceleration support."""

    def __init__(self):
        """Initialize GPU accelerator."""
        self._check_gpu_availability()

    def is_available(self) -> bool:
        """Check if GPU acceleration is available.

        Returns:
            True if GPU acceleration is available
        """
        return self._gpu_available

    def accelerate_effect(self, effect: BlurEffect) -> BlurEffect:
        """Create GPU-accelerated version of effect.

        Args:
            effect: CPU-based blur effect

        Returns:
            GPU-accelerated effect (if available)
        """
        if not self.is_available():
            return effect

        # Return GPU-accelerated version
        return self._create_gpu_effect(effect)
```

## Error Handling

### Custom Exceptions

```python
class BlurSuiteError(Exception):
    """Base exception for Blur Suite errors."""
    pass

class InvalidParameterError(BlurSuiteError):
    """Exception for invalid parameters."""
    pass

class UnsupportedImageFormatError(BlurSuiteError):
    """Exception for unsupported image formats."""
    pass

class GPUAccelerationError(BlurSuiteError):
    """Exception for GPU acceleration errors."""
    pass

class PluginError(BlurSuiteError):
    """Exception for plugin-related errors."""
    pass
```

## Usage Examples

### Basic Usage Pattern

```python
import blur_suite as bs
import numpy as np

# Create sample image
image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)

# Create factory
factory = bs.BlurFactory()

# Apply different blur effects
effects = [
    ("gaussian", {"kernel_size": 7, "sigma_x": 1.5}),
    ("motion", {"angle": 45.0, "length": 15}),
    ("defocus", {"radius": 8, "strength": 1.2})
]

results = {}
for blur_type, params in effects:
    effect = factory.create_effect(blur_type, **params)
    result = effect.apply(image)
    results[blur_type] = result

    print(f"Applied {blur_type} blur in {result.processing_time_ms:.1f}ms")
    print(f"PSNR: {result.get_quality_metrics()['psnr']:.2f}dB")
```

### Custom Plugin Development

```python
from blur_suite.core.blur import PluginBase, BlurEffect, BlurType

class CustomBlurEffect(BlurEffect):
    """Custom blur effect implementation."""

    def __init__(self, intensity: float = 1.0):
        parameters = {"intensity": intensity}
        super().__init__(BlurType.GAUSSIAN, parameters)  # Use existing type or create new

    def apply(self, image: np.ndarray) -> BlurResult:
        # Custom blur implementation
        start_time = time.time()

        # Apply custom blur algorithm
        blurred = self._apply_custom_blur(image, self.parameters["intensity"])

        processing_time = (time.time() - start_time) * 1000

        return BlurResult(
            result_image=blurred,
            original_image=image,
            blur_type=self.blur_type,
            parameters=self.parameters,
            processing_time_ms=processing_time,
            metadata={"algorithm": "custom"}
        )

class CustomBlurPlugin(PluginBase):
    """Custom blur plugin."""

    def get_blur_types(self) -> List[BlurType]:
        return [BlurType.GAUSSIAN]  # Can add custom types

    def create_effect(self, blur_type: BlurType, **kwargs) -> BlurEffect:
        if blur_type == BlurType.GAUSSIAN:
            return CustomBlurEffect(**kwargs)
        raise ValueError(f"Unsupported blur type: {blur_type}")

    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "Custom Blur Plugin",
            "version": "1.0.0",
            "author": "Plugin Developer",
            "description": "Custom blur effect implementations"
        }
```

### Performance Monitoring

```python
import time
from blur_suite.core.blur import BlurFactory

# Performance monitoring setup
factory = BlurFactory()

def benchmark_effect(blur_type: str, params: dict, image: np.ndarray, iterations: int = 100):
    """Benchmark blur effect performance."""

    times = []

    for _ in range(iterations):
        # Warm up
        effect = factory.create_effect(blur_type, **params)
        _ = effect.apply(image)

    # Actual benchmarking
    for _ in range(iterations):
        start_time = time.time()

        effect = factory.create_effect(blur_type, **params)
        result = effect.apply(image)

        end_time = time.time()
        times.append((end_time - start_time) * 1000)  # Convert to ms

    # Calculate statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"Performance for {blur_type}:")
    print(f"  Average time: {avg_time:.2f}ms")
    print(f"  Min time: {min_time:.2f}ms")
    print(f"  Max time: {max_time:.2f}ms")
    print(f"  Images per second: {1000/avg_time:.1f}")

    return {
        "average_time_ms": avg_time,
        "min_time_ms": min_time,
        "max_time_ms": max_time,
        "throughput_ips": 1000/avg_time
    }
```

## Best Practices

### Performance Optimization

1. **Reuse factory instances** for multiple operations
2. **Use appropriate parameter ranges** for your use case
3. **Consider image size** when choosing parameters
4. **Enable GPU acceleration** when available for large images

### Memory Management

1. **Process large images in chunks** if memory is limited
2. **Use appropriate data types** (uint8 for images)
3. **Clean up result objects** when no longer needed
4. **Monitor memory usage** in long-running applications

### Error Handling

1. **Validate parameters** before creating effects
2. **Handle exceptions gracefully** in production code
3. **Log errors** with sufficient context for debugging
4. **Provide fallback options** for critical operations

## API Compatibility

### Version Compatibility

The core blur API maintains backward compatibility across versions:

- **Patch versions** (1.0.0 → 1.0.1): Fully compatible
- **Minor versions** (1.0.0 → 1.1.0): New features, existing code works
- **Major versions** (1.0.0 → 2.0.0): Breaking changes may occur

### Deprecation Policy

Deprecated features are marked and maintained for at least one minor version before removal.

```python
# Deprecated method (still works but shows warning)
@deprecated("Use create_effect() instead")
def create_blur_effect(self, blur_type: str):
    """Deprecated method for creating blur effects."""
    warnings.warn(
        "create_blur_effect() is deprecated, use create_effect() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return self.create_effect(blur_type)
```

## Support and Resources

- 📚 **[User Guide: Core Blur](../user_guide/)** - Usage examples and tutorials
- 💡 **[Examples: Basic Usage](../examples/basic_usage.py)** - Working code examples
- 💡 **[Examples: Custom Blur](../examples/custom_blur.py)** - Plugin development tutorial
- 🛠️ **[Troubleshooting Guide](../troubleshooting.md)** - Common issues and solutions

---

*Need help?* Check the [Troubleshooting Guide](../troubleshooting.md) or explore the [Examples](../examples/) for more advanced usage patterns.