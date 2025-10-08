#!/usr/bin/env python3
"""
Blur Suite SDK - Basic Usage Examples

This script demonstrates the basic usage patterns for the Blur Suite SDK,
including creating blur effects, applying them to images, and working with results.
"""

import sys
from pathlib import Path

import numpy as np

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import blur_suite as bs


def example_basic_blur_effects():
    """Demonstrate basic blur effect creation and application."""
    print("🔹 Basic Blur Effects Example")
    print("=" * 50)

    # Create a sample image (you can replace this with loading your own image)
    image = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    print(f"Created sample image: {image.shape}")

    # Create blur factory
    factory = bs.BlurFactory()

    # Test different blur effects
    blur_configs = [
        ("Gaussian", "gaussian", {"kernel_size": 7, "sigma_x": 1.5, "sigma_y": 1.5}),
        ("Motion", "motion", {"angle": 45.0, "length": 15}),
        ("Defocus", "defocus", {"radius": 8, "strength": 1.2}),
        ("Average", "average", {"kernel_size": 7}),
        (
            "Bilateral",
            "bilateral",
            {"diameter": 9, "sigma_color": 75.0, "sigma_space": 75.0},
        ),
    ]

    results = {}

    for name, blur_type, params in blur_configs:
        print(f"\n📸 Applying {name} blur...")

        try:
            # Create blur effect
            blur_effect = factory.create_effect(blur_type, **params)

            # Apply to image
            result = blur_effect.apply(image)

            # Store result
            results[name] = result

            print(f"   ✅ Success! Processing time: {result.processing_time_ms:.1f}ms")
            print(f"   📊 Result shape: {result.result_image.shape}")
            print(
                f"   🔍 Original type: {image.dtype}, Result type: {result.result_image.dtype}"
            )

        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")

    return results


def example_blur_result_handling():
    """Demonstrate working with blur results and metadata."""
    print("\n🔹 Blur Result Handling Example")
    print("=" * 50)

    # Create sample image
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    # Create and apply blur effect
    factory = bs.BlurFactory()
    gaussian = factory.create_effect("gaussian", kernel_size=5, sigma_x=1.0)
    result = gaussian.apply(image)

    # Work with the result
    print("📋 Result Information:")
    print(f"   Original image shape: {result.original_image.shape}")
    print(f"   Blurred image shape: {result.result_image.shape}")
    print(f"   Blur type: {result.blur_type}")
    print(f"   Parameters: {result.parameters}")
    print(f"   Processing time: {result.processing_time_ms:.2f}ms")

    # Access metadata
    if result.metadata:
        print(f"   Metadata keys: {list(result.metadata.keys())}")

    # Calculate quality metrics
    try:
        quality_metrics = result.get_quality_metrics()
        print("📊 Quality Metrics:")
        for metric, value in quality_metrics.items():
            if metric.endswith("_ms"):
                print(f"   {metric}: {value:.2f}ms")
            elif metric.endswith("_db"):
                print(f"   {metric}: {value:.2f}dB")
            else:
                print(f"   {metric}: {value:.4f}")
    except Exception as e:
        print(f"   Note: Quality metrics calculation: {e}")

    return result


def example_parameter_validation():
    """Demonstrate parameter validation and error handling."""
    print("\n🔹 Parameter Validation Example")
    print("=" * 50)

    factory = bs.BlurFactory()

    # Test valid parameters
    valid_configs = [
        ("gaussian", {"kernel_size": 5, "sigma_x": 1.0}),
        ("motion", {"angle": 30.0, "length": 10}),
        ("defocus", {"radius": 5, "strength": 1.0}),
    ]

    print("✅ Testing valid parameters:")
    for blur_type, params in valid_configs:
        try:
            factory.create_effect(blur_type, **params)
            print(f"   {blur_type}: {params} ✓")
        except Exception as e:
            print(f"   {blur_type}: {params} ❌ {e}")

    # Test invalid parameters
    invalid_configs = [
        ("gaussian", {"kernel_size": 2}),  # Even kernel size
        ("motion", {"angle": -10}),  # Invalid angle
        ("defocus", {"radius": 0}),  # Zero radius
    ]

    print("\n❌ Testing invalid parameters:")
    for blur_type, params in invalid_configs:
        try:
            factory.create_effect(blur_type, **params)
            print(f"   {blur_type}: {params} ✓ (unexpected)")
        except Exception as e:
            print(f"   {blur_type}: {params} ❌ {type(e).__name__}")


def example_image_formats():
    """Demonstrate working with different image formats."""
    print("\n🔹 Image Format Example")
    print("=" * 50)

    # Create sample image
    image = np.random.randint(0, 255, (150, 150, 3), dtype=np.uint8)

    # Create blur effect
    factory = bs.BlurFactory()
    gaussian = factory.create_effect("gaussian", kernel_size=9, sigma_x=2.0)

    # Apply blur
    result = gaussian.apply(image)

    print("🖼️  Image format information:")
    print(f"   Original: {image.shape}, dtype: {image.dtype}")
    print(
        f"   Blurred:  {result.result_image.shape}, dtype: {result.result_image.dtype}"
    )

    # Demonstrate saving with different formats (if PIL is available)
    try:
        from PIL import Image

        # Save as different formats
        formats_to_test = [
            ("blurred_sample.png", "PNG"),
            ("blurred_sample.jpg", "JPEG"),
        ]

        for filename, format_name in formats_to_test:
            # Convert numpy array back to PIL Image
            pil_image = Image.fromarray(result.result_image)

            # Save with specified format
            pil_image.save(filename, format=format_name)
            print(f"   💾 Saved {filename} ({format_name})")

    except ImportError:
        print("   📦 PIL not available for format conversion")
    except Exception as e:
        print(f"   ❌ Error saving images: {e}")


def example_blur_comparison():
    """Compare different blur effects on the same image."""
    print("\n🔹 Blur Effect Comparison Example")
    print("=" * 50)

    # Create test image with some structure
    image = np.zeros((100, 100, 3), dtype=np.uint8)

    # Add some patterns to make blur effects visible
    image[20:80, 20:80] = 255  # White square
    image[40:60, 40:60] = 128  # Gray square inside

    print("🖼️  Created test image with patterns")

    factory = bs.BlurFactory()

    # Test different blur intensities
    test_cases = [
        (
            "Light Gaussian",
            "gaussian",
            {"kernel_size": 3, "sigma_x": 0.5, "sigma_y": 0.5},
        ),
        (
            "Medium Gaussian",
            "gaussian",
            {"kernel_size": 7, "sigma_x": 1.5, "sigma_y": 1.5},
        ),
        (
            "Strong Gaussian",
            "gaussian",
            {"kernel_size": 15, "sigma_x": 3.0, "sigma_y": 3.0},
        ),
        ("Motion Blur", "motion", {"angle": 45.0, "length": 20}),
        ("Defocus Blur", "defocus", {"radius": 10, "strength": 2.0}),
        (
            "Edge Preserving",
            "bilateral",
            {"diameter": 15, "sigma_color": 50.0, "sigma_space": 50.0},
        ),
    ]

    print("\n📊 Comparing blur effects:")
    print(f"{'Effect':<20} {'Time (ms)':<12} {'Status':<10}")
    print("-" * 45)

    for name, blur_type, params in test_cases:
        try:
            effect = factory.create_effect(blur_type, **params)
            result = effect.apply(image)

            status = "✅"
            time_str = f"{result.processing_time_ms:>6.1f}"

            print(f"{name:<20} {time_str:<12} {status}")

        except Exception:
            print(f"{name:<20} {'Error':<12} ❌")

    print("\n💡 Tip: Use the interactive tool for visual comparison!")


def example_factory_usage():
    """Demonstrate advanced factory usage patterns."""
    print("\n🔹 Factory Usage Example")
    print("=" * 50)

    factory = bs.BlurFactory()

    # Get available effects
    available_effects = factory.get_available_effects()
    print(f"📋 Available blur effects: {len(available_effects)}")
    for effect_type in available_effects:
        print(f"   • {effect_type}")

    # Get effect information
    print("\n📖 Effect information:")
    for effect_type in available_effects:
        try:
            info = factory.get_effect_info(effect_type)
            print(f"\n   {effect_type}:")
            print(f"     Class: {info.get('class_name', 'Unknown')}")
            print(f"     Module: {info.get('module', 'Unknown')}")

            # Show parameter info if available
            if "parameters" in info:
                print("     Parameters: Validated at creation")
        except Exception as e:
            print(f"     Error getting info: {e}")

    # Demonstrate effect reuse
    print("\n🔄 Testing effect reuse:")
    image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

    # Create effect once
    gaussian = factory.create_effect("gaussian", kernel_size=5, sigma_x=1.0)
    print("   Created Gaussian effect")

    # Apply multiple times
    for i in range(3):
        result = gaussian.apply(image)
        print(f"   Application {i + 1}: {result.processing_time_ms:.1f}ms")


def main():
    """Run all basic usage examples."""
    print("Blur Suite SDK - Basic Usage Examples")
    print("=" * 60)
    print()

    try:
        # Run examples
        example_basic_blur_effects()
        example_blur_result_handling()
        example_parameter_validation()
        example_image_formats()
        example_blur_comparison()
        example_factory_usage()

        print("\n" + "=" * 60)
        print("🎉 All basic examples completed successfully!")
        print("=" * 60)

        # Summary
        print("\n📊 Summary:")
        print("   • Demonstrated 5 blur effect types")
        print("   • Showed result handling and metadata")
        print("   • Covered parameter validation")
        print("   • Explored image format handling")
        print("   • Compared different blur intensities")
        print("   • Demonstrated factory patterns")

        print("\n🚀 Next steps:")
        print("   • Try the interactive tool for visual exploration")
        print("   • Explore advanced usage examples")
        print("   • Create custom blur plugins")
        print("   • Set up batch processing workflows")

        return True

    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
