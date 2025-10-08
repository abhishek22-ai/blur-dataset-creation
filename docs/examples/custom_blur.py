#!/usr/bin/env python3
"""
Blur Suite SDK - Custom Blur Plugin Example

This script demonstrates how to create and use custom blur effect plugins
with the Blur Suite SDK plugin architecture.
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import blur_suite as bs
from blur_suite.core.blur import BlurEffect, BlurResult, BlurType, PluginBase


class RadialBlurEffect(BlurEffect):
    """Custom radial blur effect that blurs towards the center of the image."""

    def __init__(
        self, center_x: float = 0.5, center_y: float = 0.5, strength: float = 1.0
    ):
        """Initialize radial blur effect.

        Args:
            center_x: Center X position as fraction (0.0-1.0)
            center_y: Center Y position as fraction (0.0-1.0)
            strength: Blur strength multiplier (0.1-3.0)
        """
        parameters = {"center_x": center_x, "center_y": center_y, "strength": strength}

        super().__init__(
            BlurType.GAUSSIAN, parameters
        )  # Base on Gaussian for this example

    def apply(self, image: np.ndarray) -> BlurResult:
        """Apply radial blur effect to image."""
        start_time = time.time()

        height, width = image.shape[:2]

        # Calculate center point
        center_x = int(width * self.parameters["center_x"])
        center_y = int(height * self.parameters["center_y"])
        strength = self.parameters["strength"]

        # Create output image
        result_image = np.copy(image).astype(np.float32)

        # Apply radial blur
        for y in range(height):
            for x in range(width):
                # Calculate distance from center
                dx = x - center_x
                dy = y - center_y
                distance = np.sqrt(dx * dx + dy * dy)

                # Calculate blur amount based on distance
                if distance > 0:
                    # Blur more as we move away from center
                    blur_factor = min(distance / max(width, height) * strength, 1.0)

                    # Apply Gaussian-like blur based on distance
                    kernel_size = max(3, int(blur_factor * 10))

                    # Simple box blur for demonstration
                    if kernel_size > 1:
                        half_kernel = kernel_size // 2

                        # Ensure we don't go out of bounds
                        y_start = max(0, y - half_kernel)
                        y_end = min(height, y + half_kernel + 1)
                        x_start = max(0, x - half_kernel)
                        x_end = min(width, x + half_kernel + 1)

                        # Calculate average of surrounding pixels
                        region = image[y_start:y_end, x_start:x_end]
                        if region.size > 0:
                            result_image[y, x] = np.mean(region, axis=(0, 1))

        # Convert back to uint8
        result_image = np.clip(result_image, 0, 255).astype(np.uint8)

        processing_time = (time.time() - start_time) * 1000

        return BlurResult(
            result_image=result_image,
            original_image=image,
            blur_type=self.blur_type,
            parameters=self.parameters,
            processing_time_ms=processing_time,
            metadata={
                "algorithm": "radial_blur",
                "center_point": (center_x, center_y),
                "strength_applied": strength,
            },
        )

    def _validate_parameters(self) -> None:
        """Validate radial blur parameters."""
        center_x = self.parameters.get("center_x", 0.5)
        center_y = self.parameters.get("center_y", 0.5)
        strength = self.parameters.get("strength", 1.0)

        if not 0.0 <= center_x <= 1.0:
            raise ValueError("center_x must be between 0.0 and 1.0")
        if not 0.0 <= center_y <= 1.0:
            raise ValueError("center_y must be between 0.0 and 1.0")
        if not 0.1 <= strength <= 3.0:
            raise ValueError("strength must be between 0.1 and 3.0")


class ZoomBlurEffect(BlurEffect):
    """Custom zoom blur effect that creates a sense of motion towards/from viewer."""

    def __init__(
        self, center_x: float = 0.5, center_y: float = 0.5, zoom_factor: float = 1.5
    ):
        """Initialize zoom blur effect.

        Args:
            center_x: Center X position as fraction (0.0-1.0)
            center_y: Center Y position as fraction (0.0-1.0)
            zoom_factor: Zoom intensity (1.1-3.0)
        """
        parameters = {
            "center_x": center_x,
            "center_y": center_y,
            "zoom_factor": zoom_factor,
        }

        super().__init__(BlurType.MOTION, parameters)  # Base on motion blur

    def apply(self, image: np.ndarray) -> BlurResult:
        """Apply zoom blur effect to image."""
        start_time = time.time()

        height, width = image.shape[:2]

        # Calculate center point
        center_x = int(width * self.parameters["center_x"])
        center_y = int(height * self.parameters["center_y"])
        zoom_factor = self.parameters["zoom_factor"]

        # Create output image
        result_image = np.copy(image).astype(np.float32)

        # Apply zoom blur effect
        for y in range(height):
            for x in range(width):
                # Calculate vector from center
                dx = x - center_x
                dy = y - center_y
                distance = np.sqrt(dx * dx + dy * dy)

                if distance > 0:
                    # Normalize direction vector
                    dx_norm = dx / distance
                    dy_norm = dy / distance

                    # Calculate zoom blur
                    num_samples = int(distance * (zoom_factor - 1.0) / 10)
                    num_samples = max(1, min(num_samples, 20))  # Limit samples

                    # Sample along the radial line
                    samples = []
                    for i in range(num_samples):
                        # Sample point along the radial line
                        sample_distance = distance * (i + 1) / num_samples
                        sample_x = int(center_x + dx_norm * sample_distance)
                        sample_y = int(center_y + dy_norm * sample_distance)

                        # Check bounds
                        if 0 <= sample_x < width and 0 <= sample_y < height:
                            samples.append(image[sample_y, sample_x])

                    if samples:
                        # Average the samples
                        result_image[y, x] = np.mean(samples, axis=0)

        # Convert back to uint8
        result_image = np.clip(result_image, 0, 255).astype(np.uint8)

        processing_time = (time.time() - start_time) * 1000

        return BlurResult(
            result_image=result_image,
            original_image=image,
            blur_type=self.blur_type,
            parameters=self.parameters,
            processing_time_ms=processing_time,
            metadata={
                "algorithm": "zoom_blur",
                "center_point": (center_x, center_y),
                "zoom_factor_applied": zoom_factor,
            },
        )

    def _validate_parameters(self) -> None:
        """Validate zoom blur parameters."""
        center_x = self.parameters.get("center_x", 0.5)
        center_y = self.parameters.get("center_y", 0.5)
        zoom_factor = self.parameters.get("zoom_factor", 1.5)

        if not 0.0 <= center_x <= 1.0:
            raise ValueError("center_x must be between 0.0 and 1.0")
        if not 0.0 <= center_y <= 1.0:
            raise ValueError("center_y must be between 0.0 and 1.0")
        if not 1.1 <= zoom_factor <= 3.0:
            raise ValueError("zoom_factor must be between 1.1 and 3.0")


class CustomBlurPlugin(PluginBase):
    """Custom plugin providing radial and zoom blur effects."""

    def get_blur_types(self) -> List[BlurType]:
        """Get list of blur types provided by this plugin."""
        # Return existing types that we'll override or extend
        return [BlurType.GAUSSIAN, BlurType.MOTION]

    def create_effect(self, blur_type: BlurType, **kwargs) -> BlurEffect:
        """Create blur effect instance.

        Args:
            blur_type: Type of blur effect to create
            **kwargs: Effect parameters

        Returns:
            Blur effect instance
        """
        if blur_type == BlurType.GAUSSIAN:
            # Check if this should be radial blur
            if "center_x" in kwargs or "center_y" in kwargs:
                return RadialBlurEffect(**kwargs)
        elif blur_type == BlurType.MOTION:
            # Check if this should be zoom blur
            if "zoom_factor" in kwargs:
                return ZoomBlurEffect(**kwargs)

        # Fall back to standard effects
        if blur_type == BlurType.GAUSSIAN:
            return bs.GaussianBlur(**kwargs)
        elif blur_type == BlurType.MOTION:
            return bs.MotionBlur(**kwargs)

        raise ValueError(f"Unsupported blur type for custom plugin: {blur_type}")

    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": "Custom Blur Effects Plugin",
            "version": "1.0.0",
            "author": "Blur Suite SDK Examples",
            "description": "Provides radial and zoom blur effects",
            "effects_provided": ["radial_blur", "zoom_blur"],
            "parameters": {
                "radial_blur": ["center_x", "center_y", "strength"],
                "zoom_blur": ["center_x", "center_y", "zoom_factor"],
            },
        }


def example_custom_plugin_usage():
    """Demonstrate using the custom blur plugin."""
    print("🔹 Custom Plugin Usage Example")
    print("=" * 50)

    # Create plugin instance
    plugin = CustomBlurPlugin()

    print("📋 Plugin information:")
    info = plugin.get_plugin_info()
    for key, value in info.items():
        print(f"   {key}: {value}")

    # Create test image with clear center focus area
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    center_x, center_y = 100, 100

    # Create radial pattern
    for y in range(200):
        for x in range(200):
            distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
            intensity = min(255, distance * 2)
            image[y, x] = [intensity, intensity // 2, 255 - intensity]

    print(f"🖼️  Created test image: {image.shape}")

    # Test radial blur
    print("\n🎯 Testing Radial Blur:")
    radial_blur = RadialBlurEffect(center_x=0.5, center_y=0.5, strength=1.5)

    result_radial = radial_blur.apply(image)
    print(f"   ✅ Applied radial blur in {result_radial.processing_time_ms:.1f}ms")
    print(f"   📊 Result shape: {result_radial.result_image.shape}")
    print(f"   🎛️  Parameters: {result_radial.parameters}")

    # Test zoom blur
    print("\n🚀 Testing Zoom Blur:")
    zoom_blur = ZoomBlurEffect(center_x=0.5, center_y=0.5, zoom_factor=2.0)

    result_zoom = zoom_blur.apply(image)
    print(f"   ✅ Applied zoom blur in {result_zoom.processing_time_ms:.1f}ms")
    print(f"   📊 Result shape: {result_zoom.result_image.shape}")
    print(f"   🎛️  Parameters: {result_zoom.parameters}")

    return result_radial, result_zoom


def example_plugin_integration():
    """Demonstrate integrating custom plugin with Blur Suite SDK."""
    print("\n🔹 Plugin Integration Example")
    print("=" * 50)

    # Create plugin
    plugin = CustomBlurPlugin()

    # In a real application, you would register this plugin with the SDK
    print("🔌 Plugin registration:")
    print("   (In real usage, plugin would be registered with PluginLoader)")

    # Simulate using plugin through factory pattern
    print("\n🏭 Testing plugin through factory pattern:")

    # Create a mock factory that uses our plugin
    class PluginEnabledFactory:
        def __init__(self, plugin):
            self.plugin = plugin

        def create_effect(self, blur_type, **kwargs):
            return self.plugin.create_effect(blur_type, **kwargs)

    factory = PluginEnabledFactory(plugin)

    # Test creating effects through plugin
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    test_cases = [
        ("Standard Gaussian", "gaussian", {"kernel_size": 5, "sigma_x": 1.0}),
        (
            "Radial Blur",
            "gaussian",
            {"center_x": 0.5, "center_y": 0.5, "strength": 1.5},
        ),
        ("Standard Motion", "motion", {"angle": 45.0, "length": 15}),
        ("Zoom Blur", "motion", {"zoom_factor": 2.0}),
    ]

    results = {}

    for name, blur_type, params in test_cases:
        try:
            effect = factory.create_effect(blur_type, **params)
            result = effect.apply(image)

            results[name] = result

            print(f"   ✅ {name}: {result.processing_time_ms:.1f}ms")
            print(f"      Algorithm: {result.metadata.get('algorithm', 'standard')}")

        except Exception as e:
            print(f"   ❌ {name}: {e}")

    return results


def example_plugin_development_workflow():
    """Demonstrate complete plugin development workflow."""
    print("\n🔹 Plugin Development Workflow Example")
    print("=" * 50)

    print("📋 Plugin development steps:")
    steps = [
        "1. Define custom blur algorithm",
        "2. Create BlurEffect subclass",
        "3. Implement PluginBase interface",
        "4. Test plugin functionality",
        "5. Register with PluginLoader",
        "6. Package for distribution",
    ]

    for step in steps:
        print(f"   {step}")

    # Demonstrate each step
    print("\n🔧 Step 1-3: Algorithm and class implementation")
    print("   ✅ RadialBlurEffect and ZoomBlurEffect classes created")
    print("   ✅ CustomBlurPlugin class implements PluginBase")

    print("\n🧪 Step 4: Testing plugin functionality")
    # Test the plugin
    plugin = CustomBlurPlugin()

    # Test plugin info
    info = plugin.get_plugin_info()
    print(f"   ✅ Plugin name: {info['name']}")
    print(f"   ✅ Plugin version: {info['version']}")
    print(f"   ✅ Effects provided: {info['effects_provided']}")

    # Test effect creation
    try:
        plugin.create_effect(
            bs.BlurType.GAUSSIAN, center_x=0.5, strength=1.0
        )
        print("   ✅ Radial blur effect creation: Success")
    except Exception as e:
        print(f"   ❌ Radial blur effect creation: {e}")

    print("\n📦 Step 5-6: Registration and packaging")
    print("   💡 In real usage:")
    print("      - Register plugin with PluginLoader")
    print("      - Package as Python module")
    print("      - Install in plugins directory")
    print("      - Configure plugin settings")


def example_advanced_custom_effect():
    """Demonstrate advanced custom effect with complex algorithm."""
    print("\n🔹 Advanced Custom Effect Example")
    print("=" * 50)

    # Create test image with text-like pattern
    image = np.ones((150, 150, 3), dtype=np.uint8) * 255

    # Add some text-like patterns
    font_color = np.array([0, 0, 0], dtype=np.uint8)
    image[20:40, 20:120] = font_color  # Top bar
    image[50:70, 20:120] = font_color  # Middle bar
    image[80:100, 20:120] = font_color  # Bottom bar

    print("📝 Created text-like test pattern")

    # Apply different custom effects
    effects_to_test = [
        (
            "Radial Blur (Center)",
            RadialBlurEffect(center_x=0.5, center_y=0.5, strength=2.0),
        ),
        (
            "Radial Blur (Corner)",
            RadialBlurEffect(center_x=0.2, center_y=0.2, strength=1.5),
        ),
        (
            "Zoom Blur (Inward)",
            ZoomBlurEffect(center_x=0.5, center_y=0.5, zoom_factor=2.5),
        ),
    ]

    print("\n🎨 Applying advanced custom effects:")

    for name, effect in effects_to_test:
        try:
            result = effect.apply(image)

            print(f"\n   🎯 {name}:")
            print(f"      Processing time: {result.processing_time_ms:.1f}ms")
            print(f"      Algorithm: {result.metadata.get('algorithm', 'unknown')}")
            print(f"      Parameters: {result.parameters}")

            # Analyze effect characteristics
            original_mean = np.mean(image)
            result_mean = np.mean(result.result_image)
            difference = abs(original_mean - result_mean)

            print(f"      Brightness change: {difference:.1f}")

        except Exception as e:
            print(f"   ❌ {name}: {e}")


def example_plugin_comparison():
    """Compare custom plugin effects with standard effects."""
    print("\n🔹 Plugin Comparison Example")
    print("=" * 50)

    # Create test image
    image = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)

    # Add a clear circular pattern to visualize effects
    center_x, center_y = 64, 64
    for y in range(128):
        for x in range(128):
            distance = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
            if distance < 30:
                image[y, x] = [255, 0, 0]  # Red circle in center

    print("🎯 Created test image with red circle pattern")

    bs.BlurFactory()

    # Compare standard vs custom effects
    comparisons = [
        ("Standard Gaussian", bs.GaussianBlur(kernel_size=9, sigma_x=2.0, sigma_y=2.0)),
        ("Custom Radial", RadialBlurEffect(center_x=0.5, center_y=0.5, strength=2.0)),
        ("Standard Motion", bs.MotionBlur(angle=0.0, length=20)),
        ("Custom Zoom", ZoomBlurEffect(center_x=0.5, center_y=0.5, zoom_factor=2.0)),
    ]

    print("\n⚖️  Comparing standard vs custom effects:")
    print(f"{'Effect<20'} {'Time (ms)<12'} {'Type<10'}")
    print("-" * 50)

    for name, effect in comparisons:
        try:
            result = effect.apply(image)

            effect_type = "Custom" if "Custom" in str(type(effect)) else "Standard"
            time_str = f"{result.processing_time_ms:>6.1f}"

            print(f"{name:<20} {time_str:<12} {effect_type}")

        except Exception:
            print(f"{name:<20} {'Error':<12} ❌")

    print("\n💡 Custom effects provide unique blur patterns")
    print("   that complement standard blur algorithms")


def main():
    """Run all custom plugin examples."""
    print("Blur Suite SDK - Custom Blur Plugin Examples")
    print("=" * 60)
    print()

    try:
        # Run examples
        example_custom_plugin_usage()
        example_plugin_integration()
        example_plugin_development_workflow()
        example_advanced_custom_effect()
        example_plugin_comparison()

        print("\n" + "=" * 60)
        print("🎉 All custom plugin examples completed successfully!")
        print("=" * 60)

        # Summary
        print("\n📊 Summary:")
        print("   • Demonstrated custom RadialBlurEffect implementation")
        print("   • Showed custom ZoomBlurEffect with motion simulation")
        print("   • Created CustomBlurPlugin following PluginBase interface")
        print("   • Explored plugin integration patterns")
        print("   • Compared custom vs standard effects")
        print("   • Showed complete plugin development workflow")

        print("\n🚀 Next steps:")
        print("   • Create your own custom blur algorithms")
        print("   • Package plugins for distribution")
        print("   • Integrate plugins with the interactive tool")
        print("   • Share plugins with the Blur Suite community")
        print("   • Explore GPU acceleration for custom effects")

        return True

    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
