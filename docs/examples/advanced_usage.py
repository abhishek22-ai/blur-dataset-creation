#!/usr/bin/env python3
"""
Blur Suite SDK - Advanced Usage Examples

This script demonstrates advanced usage patterns for the Blur Suite SDK,
including custom plugins, performance optimization, and complex workflows.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import blur_suite as bs


class CustomBlurEffect(bs.BlurEffect):
    """Example custom blur effect implementation."""

    def __init__(self, intensity: float = 1.0, blend_mode: str = "overlay"):
        """Initialize custom blur effect.

        Args:
            intensity: Blur intensity multiplier (0.1-3.0)
            blend_mode: Blending mode for combining blur with original
        """
        # Use a custom blur type (you would register this in the registry)

        parameters = {"intensity": intensity, "blend_mode": blend_mode}

        # For this example, we'll extend Gaussian blur
        super().__init__(bs.BlurType.GAUSSIAN, parameters)

    def apply(self, image: np.ndarray) -> bs.BlurResult:
        """Apply custom blur effect."""
        start_time = time.time()

        # Get base Gaussian blur
        base_gaussian = bs.GaussianBlur(kernel_size=7, sigma_x=1.5, sigma_y=1.5)
        base_result = base_gaussian.apply(image)

        # Apply custom modifications
        intensity = self.parameters["intensity"]
        blend_mode = self.parameters["blend_mode"]

        # Modify the blurred image based on intensity
        if intensity != 1.0:
            # Scale the blur effect
            blurred = base_result.result_image.astype(np.float32)
            original = image.astype(np.float32)

            # Blend based on mode
            if blend_mode == "overlay":
                # Custom overlay blending
                mask = blurred > 128
                result_image = np.where(
                    mask, blurred * intensity, original * (2 - intensity)
                )
            elif blend_mode == "multiply":
                result_image = (blurred * original / 255.0) * intensity
            else:
                result_image = blurred * intensity + original * (1 - intensity)

            result_image = np.clip(result_image, 0, 255).astype(np.uint8)
        else:
            result_image = base_result.result_image

        processing_time = (time.time() - start_time) * 1000

        return bs.BlurResult(
            result_image=result_image,
            original_image=image,
            blur_type=self.blur_type,
            parameters=self.parameters,
            processing_time_ms=processing_time,
            metadata={
                "custom_effect": True,
                "base_algorithm": "gaussian",
                "intensity_applied": intensity,
                "blend_mode": blend_mode,
            },
        )

    def _validate_parameters(self) -> None:
        """Validate custom effect parameters."""
        intensity = self.parameters.get("intensity", 1.0)
        if not 0.1 <= intensity <= 3.0:
            raise ValueError("intensity must be between 0.1 and 3.0")

        blend_mode = self.parameters.get("blend_mode", "overlay")
        valid_modes = ["overlay", "multiply", "screen", "soft_light"]
        if blend_mode not in valid_modes:
            raise ValueError(f"blend_mode must be one of {valid_modes}")


class PerformanceOptimizer:
    """Helper class for performance optimization examples."""

    def __init__(self):
        """Initialize performance optimizer."""
        self.measurements = []

    def benchmark_effect(
        self, effect: bs.BlurEffect, image: np.ndarray, iterations: int = 100
    ) -> Dict[str, float]:
        """Benchmark blur effect performance.

        Args:
            effect: Blur effect to benchmark
            image: Test image
            iterations: Number of iterations

        Returns:
            Dictionary with performance metrics
        """
        times = []

        # Warm up
        for _ in range(10):
            _ = effect.apply(image)

        # Actual benchmarking
        for _ in range(iterations):
            start_time = time.time()
            effect.apply(image)
            end_time = time.time()
            times.append((end_time - start_time) * 1000)

        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        std_time = (sum((t - avg_time) ** 2 for t in times) / len(times)) ** 0.5

        return {
            "avg_time_ms": avg_time,
            "min_time_ms": min_time,
            "max_time_ms": max_time,
            "std_time_ms": std_time,
            "throughput_ips": 1000 / avg_time if avg_time > 0 else 0,
        }

    def memory_usage_test(
        self, effect: bs.BlurEffect, image_sizes: List[Tuple[int, int]]
    ) -> Dict:
        """Test memory usage with different image sizes.

        Args:
            effect: Blur effect to test
            image_sizes: List of (width, height) tuples

        Returns:
            Dictionary with memory usage data
        """
        import os

        import psutil

        process = psutil.Process(os.getpid())
        results = {}

        for width, height in image_sizes:
            # Create test image
            test_image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

            # Measure memory before
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            # Apply effect multiple times
            for _ in range(5):
                effect.apply(test_image)

            # Measure memory after
            memory_after = process.memory_info().rss / 1024 / 1024  # MB

            memory_used = memory_after - memory_before
            results[f"{width}x{height}"] = {
                "memory_mb": memory_used,
                "image_pixels": width * height,
                "memory_per_pixel": memory_used / (width * height)
                if width * height > 0
                else 0,
            }

        return results


def example_custom_plugin():
    """Demonstrate creating and using custom blur plugins."""
    print("🔹 Custom Plugin Example")
    print("=" * 50)

    # Create custom effect instance
    custom_effect = CustomBlurEffect(intensity=1.5, blend_mode="overlay")

    # Test with sample image
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    print("🧪 Testing custom blur effect:")
    print(f"   Intensity: {custom_effect.parameters['intensity']}")
    print(f"   Blend mode: {custom_effect.parameters['blend_mode']}")

    # Apply custom effect
    result = custom_effect.apply(image)

    print(f"   ✅ Applied in {result.processing_time_ms:.1f}ms")
    print(f"   📊 Result shape: {result.result_image.shape}")
    print(f"   🏷️  Metadata: {result.metadata}")

    return result


def example_performance_optimization():
    """Demonstrate performance optimization techniques."""
    print("\n🔹 Performance Optimization Example")
    print("=" * 50)

    optimizer = PerformanceOptimizer()

    # Test different image sizes
    image_sizes = [(256, 256), (512, 512), (1024, 1024)]
    print("📏 Testing memory usage with different image sizes:")

    for size in image_sizes:
        # Create test image
        test_image = np.random.randint(0, 255, (size[1], size[0], 3), dtype=np.uint8)

        # Test with Gaussian blur
        gaussian = bs.GaussianBlur(kernel_size=7, sigma_x=1.5)

        # Benchmark performance
        perf_metrics = optimizer.benchmark_effect(gaussian, test_image, iterations=50)

        print(f"\n   {size[0]}x{size[1]} image:")
        print(f"     Average time: {perf_metrics['avg_time_ms']:.2f}ms")
        print(f"     Throughput: {perf_metrics['throughput_ips']:.1f} images/sec")
        print(f"     Std deviation: {perf_metrics['std_time_ms']:.2f}ms")

    # Test memory usage
    print("\n💾 Memory usage analysis:")
    gaussian = bs.GaussianBlur(kernel_size=7, sigma_x=1.5)
    memory_results = optimizer.memory_usage_test(gaussian, image_sizes)

    for size_key, memory_data in memory_results.items():
        print(
            f"   {size_key}: {memory_data['memory_mb']:.1f}MB "
            f"({memory_data['memory_per_pixel']:.4f}MB/pixel)"
        )


def example_batch_processing():
    """Demonstrate advanced batch processing techniques."""
    print("\n🔹 Advanced Batch Processing Example")
    print("=" * 50)

    # Create sample dataset
    print("📁 Creating sample image dataset...")

    sample_images = []
    for i in range(5):
        # Create different types of test images
        if i % 2 == 0:
            # Pattern image
            img = np.zeros((200, 200, 3), dtype=np.uint8)
            img[50:150, 50:150] = 255
        else:
            # Random image
            img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)

        filename = f"sample_image_{i + 1}.png"
        # In real usage, you would save these images
        sample_images.append((filename, img))

    print(f"   Created {len(sample_images)} sample images")

    # Configure batch processing
    from blur_suite.dataset import BatchConfig, DatasetCreator

    batch_config = BatchConfig(
        max_workers=4, use_multiprocessing=True, chunk_size=2, retry_attempts=2
    )

    DatasetCreator("./advanced_example_output", batch_config)

    # Create configuration for batch processing
    image_configs = {}
    for i, (filename, img) in enumerate(sample_images):
        # Vary blur parameters across images
        blur_configs = [
            {
                "blur_type": "gaussian",
                "parameters": {"kernel_size": 5, "sigma_x": 1.0 + i * 0.2},
            },
            {
                "blur_type": "motion",
                "parameters": {"angle": i * 30, "length": 10 + i * 2},
            },
        ]

        for j, blur_config in enumerate(blur_configs):
            config_key = f"{filename}_blur_{j + 1}"
            image_configs[config_key] = blur_config

    # Create dataset configuration

    print("⚙️  Batch configuration created")
    print(f"   Images to process: {len(image_configs)}")
    print(f"   Workers: {batch_config.max_workers}")
    print(f"   Chunk size: {batch_config.chunk_size}")

    # In real usage, you would call:
    # success = creator.create_from_config_dict(config)
    print("   (Skipping actual processing in example)")


def example_error_handling():
    """Demonstrate comprehensive error handling."""
    print("\n🔹 Error Handling Example")
    print("=" * 50)

    factory = bs.BlurFactory()

    # Test various error conditions
    error_tests = [
        ("Invalid kernel size", "gaussian", {"kernel_size": 2}),  # Even number
        ("Invalid angle", "motion", {"angle": -10}),  # Out of range
        ("Invalid radius", "defocus", {"radius": 0}),  # Zero radius
        ("Missing parameters", "gaussian", {}),  # No parameters
        ("Invalid blur type", "invalid_blur", {"kernel_size": 5}),  # Non-existent type
    ]

    print("🧪 Testing error conditions:")

    for test_name, blur_type, params in error_tests:
        try:
            factory.create_effect(blur_type, **params)
            print(f"   {test_name}: ❌ Should have failed!")

        except ValueError:
            print(f"   {test_name}: ✅ Correctly caught ValueError")
        except TypeError:
            print(f"   {test_name}: ✅ Correctly caught TypeError")
        except Exception as e:
            print(f"   {test_name}: ✅ Correctly caught {type(e).__name__}")

    # Demonstrate graceful error recovery
    print("\n🔄 Testing error recovery:")

    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    # Try to apply effect with fallback
    def apply_with_fallback(
        blur_type, params, fallback_type="gaussian", fallback_params=None
    ):
        """Apply blur effect with fallback on error."""
        try:
            effect = factory.create_effect(blur_type, **params)
            return effect.apply(image)
        except Exception as e:
            print(f"   Primary effect failed: {e}")
            print(f"   Trying fallback: {fallback_type}")

            fallback_params = fallback_params or {"kernel_size": 5, "sigma_x": 1.0}
            fallback_effect = factory.create_effect(fallback_type, **fallback_params)
            return fallback_effect.apply(image)

    # Test error recovery
    result = apply_with_fallback("invalid_blur", {"kernel_size": 5})
    print(f"   ✅ Recovered with fallback effect: {result.processing_time_ms:.1f}ms")


def example_memory_management():
    """Demonstrate memory management techniques."""
    print("\n🔹 Memory Management Example")
    print("=" * 50)

    import gc
    import os

    import psutil

    def get_memory_usage():
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    print("📊 Memory monitoring example:")

    factory = bs.BlurFactory()

    # Monitor memory usage during multiple operations
    memory_before = get_memory_usage()
    print(f"   Memory before: {memory_before:.1f}MB")

    results = []

    # Process multiple images of different sizes
    for size in [128, 256, 512]:
        image = np.random.randint(0, 255, (size, size, 3), dtype=np.uint8)

        # Apply multiple effects
        for blur_type in ["gaussian", "motion", "defocus"]:
            if blur_type == "gaussian":
                params = {"kernel_size": 7, "sigma_x": 1.5}
            elif blur_type == "motion":
                params = {"angle": 45.0, "length": 15}
            else:
                params = {"radius": 8, "strength": 1.2}

            effect = factory.create_effect(blur_type, **params)
            result = effect.apply(image)
            results.append(result)

        # Force garbage collection periodically
        if size % 256 == 0:
            gc.collect()
            print(f"   After {size}x{size} processing: {get_memory_usage():.1f}MB")

    memory_after = get_memory_usage()
    print(f"   Memory after: {memory_after:.1f}MB")
    print(f"   Memory increase: {memory_after - memory_before:.1f}MB")

    # Clean up
    del results
    gc.collect()
    print(f"   After cleanup: {get_memory_usage():.1f}MB")


def example_configuration_management():
    """Demonstrate advanced configuration management."""
    print("\n🔹 Configuration Management Example")
    print("=" * 50)

    # Create complex configuration programmatically
    print("⚙️  Creating complex configuration...")

    # Base configuration template
    base_config = {
        "metadata": {
            "created_by": "Advanced Configuration Example",
            "version": "1.0.0",
            "description": "Advanced configuration with multiple variants",
        },
        "global_settings": {
            "output_format": "png",
            "quality": 95,
            "parallel_processing": True,
            "max_workers": 4,
            "preserve_metadata": True,
        },
    }

    # Generate multiple configuration variants
    variants = []

    # Parameter study configurations
    kernel_sizes = [3, 5, 7, 9, 11]
    sigma_values = [0.5, 1.0, 1.5, 2.0, 2.5]

    variant_counter = 1
    for kernel_size in kernel_sizes:
        for sigma_x in sigma_values:
            variant_config = base_config.copy()

            # Update metadata
            variant_config["metadata"].update(
                {
                    "variant_id": f"variant_{variant_counter}",
                    "kernel_size": kernel_size,
                    "sigma_x": sigma_x,
                    "description": f"Gaussian blur study: kernel={kernel_size}, sigma={sigma_x}",
                }
            )

            # Add image configurations
            variant_config["image_configurations"] = {
                f"study_image_k{kernel_size}_s{sigma_x}.jpg": {
                    "blur_type": "gaussian",
                    "parameters": {
                        "kernel_size": kernel_size,
                        "sigma_x": sigma_x,
                        "sigma_y": sigma_x,
                    },
                    "enabled": True,
                }
            }

            variants.append(variant_config)
            variant_counter += 1

    print(f"   ✅ Generated {len(variants)} configuration variants")

    # Demonstrate configuration validation
    print("\n🔍 Validating configurations:")

    valid_configs = 0
    for i, config in enumerate(variants[:3]):  # Test first 3
        try:
            # In real usage, you would validate with DatasetCreator
            # creator = DatasetCreator(f"./variant_output_{i+1}")
            # issues = creator.validate_config_dict(config)

            # For this example, just check structure
            required_keys = ["metadata", "global_settings", "image_configurations"]
            if all(key in config for key in required_keys):
                print(f"   Variant {i + 1}: ✅ Valid structure")
                valid_configs += 1
            else:
                print(f"   Variant {i + 1}: ❌ Missing required keys")

        except Exception as e:
            print(f"   Variant {i + 1}: ❌ Validation error: {e}")

    print(
        f"\n   Summary: {valid_configs}/{min(3, len(variants))} tested configurations valid"
    )


def example_real_world_workflow():
    """Demonstrate a real-world image processing workflow."""
    print("\n🔹 Real-World Workflow Example")
    print("=" * 50)

    print("🎯 Scenario: Processing a collection of document images for blur analysis")

    # Simulate workflow steps
    workflow_steps = [
        ("Load and validate images", "load_images"),
        ("Apply quality assessment", "assess_quality"),
        ("Generate blur variants", "generate_blur_variants"),
        ("Extract features", "extract_features"),
        ("Generate analysis report", "generate_report"),
    ]

    for step_name, step_function in workflow_steps:
        print(f"\n📋 Step: {step_name}")

        try:
            # Simulate step execution time
            time.sleep(0.1)

            if step_function == "load_images":
                # Simulate loading images
                image_count = 25
                print(f"   📂 Loaded {image_count} document images")

            elif step_function == "assess_quality":
                # Simulate quality assessment
                avg_quality = 0.87
                print(f"   🔍 Average image quality: {avg_quality:.2f}")

            elif step_function == "generate_blur_variants":
                # Simulate blur variant generation
                variants_per_image = 5
                total_variants = 25 * variants_per_image
                print(f"   ✨ Generated {total_variants} blur variants")

                # Demonstrate different blur types
                blur_types_used = [
                    "Gaussian",
                    "Motion",
                    "Defocus",
                    "Average",
                    "Bilateral",
                ]
                print(f"   🎛️  Blur types: {', '.join(blur_types_used)}")

            elif step_function == "extract_features":
                # Simulate feature extraction
                features = ["edges", "textures", "color_histograms", "blur_metrics"]
                print(f"   📊 Extracted features: {', '.join(features)}")

            elif step_function == "generate_report":
                # Simulate report generation
                report_sections = [
                    "Summary",
                    "Quality Analysis",
                    "Blur Effects",
                    "Recommendations",
                ]
                print(
                    f"   📄 Generated report with sections: {', '.join(report_sections)}"
                )

            print(f"   ✅ {step_name} completed successfully")

        except Exception as e:
            print(f"   ❌ {step_name} failed: {e}")


print("\n🎉 Workflow completed!")
print("   💡 This demonstrates how Blur Suite SDK can be integrated")
print("      into complex image processing pipelines")


def main():
    """Run all advanced usage examples."""
    print("Blur Suite SDK - Advanced Usage Examples")
    print("=" * 60)
    print()

    try:
        # Run examples
        example_custom_plugin()
        example_performance_optimization()
        example_batch_processing()
        example_error_handling()
        example_memory_management()
        example_configuration_management()
        example_real_world_workflow()

        print("\n" + "=" * 60)
        print("🎉 All advanced examples completed successfully!")
        print("=" * 60)

        # Summary
        print("\n📊 Summary:")
        print("   • Demonstrated custom plugin development")
        print("   • Showed performance optimization techniques")
        print("   • Covered advanced batch processing")
        print("   • Explored comprehensive error handling")
        print("   • Demonstrated memory management")
        print("   • Showed configuration management")
        print("   • Presented real-world workflow integration")

        print("\n🚀 Next steps:")
        print("   • Integrate these patterns into your application")
        print("   • Explore the interactive tool for experimentation")
        print("   • Set up automated processing pipelines")
        print("   • Contribute custom plugins to the community")

        return True

    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
