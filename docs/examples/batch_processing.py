#!/usr/bin/env python3
"""
Blur Suite SDK - Batch Processing Example

This script demonstrates batch processing techniques using the
Blur Suite SDK dataset creation module for large-scale image processing.
"""

import json
import sys
import time
from pathlib import Path
from typing import List

import numpy as np

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from blur_suite.dataset import BatchConfig, DatasetCreator


def create_sample_image_dataset(output_dir: str, num_images: int = 20) -> List[str]:
    """Create a sample dataset of images for batch processing."""
    print(f"📁 Creating sample dataset with {num_images} images...")

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    image_paths = []

    for i in range(num_images):
        # Create different types of test images
        if i % 4 == 0:
            # Pattern image with geometric shapes
            image = np.zeros((256, 256, 3), dtype=np.uint8)
            center = 128

            # Draw concentric circles
            for radius in range(20, 100, 20):
                for y in range(256):
                    for x in range(256):
                        distance = np.sqrt((x - center) ** 2 + (y - center) ** 2)
                        if radius - 2 <= distance <= radius + 2:
                            image[y, x] = [255, 255, 255]

        elif i % 4 == 1:
            # Gradient image
            image = np.zeros((256, 256, 3), dtype=np.uint8)
            for y in range(256):
                for x in range(256):
                    image[y, x] = [x, y, (x + y) // 2]

        elif i % 4 == 2:
            # Text-like pattern
            image = np.ones((256, 256, 3), dtype=np.uint8) * 255
            # Draw horizontal bars
            for bar_y in [50, 100, 150]:
                image[bar_y : bar_y + 20, 50:200] = [0, 0, 0]

        else:
            # Random noise image
            image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)

        # Save image
        image_path = output_path / f"sample_image_{i + 1:03d}.png"
        from PIL import Image

        pil_image = Image.fromarray(image)
        pil_image.save(image_path)

        image_paths.append(str(image_path))

        if (i + 1) % 5 == 0:
            print(f"   Created {i + 1}/{num_images} images...")

    print(f"✅ Created {len(image_paths)} sample images in {output_dir}")
    return image_paths


def example_basic_batch_processing():
    """Demonstrate basic batch processing with configuration file."""
    print("🔹 Basic Batch Processing Example")
    print("=" * 50)

    # Create sample dataset
    input_dir = "./batch_example_input"
    image_paths = create_sample_image_dataset(input_dir, num_images=10)

    # Create dataset creator
    output_dir = "./batch_example_output"
    creator = DatasetCreator(output_dir)

    # Create configuration for batch processing
    image_configs = {}

    for i, image_path in enumerate(image_paths):
        # Vary blur effects across images
        blur_configs = [
            {
                "blur_type": "gaussian",
                "parameters": {"kernel_size": 5, "sigma_x": 1.0 + i * 0.1},
            },
            {"blur_type": "motion", "parameters": {"angle": i * 18, "length": 10 + i}},
        ]

        for j, blur_config in enumerate(blur_configs):
            config_key = f"{Path(image_path).stem}_blur_{j + 1}"
            image_configs[config_key] = blur_config

    # Create complete configuration
    config = {
        "metadata": {
            "created_by": "Basic Batch Processing Example",
            "creation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0.0",
            "description": "Basic batch processing demonstration",
        },
        "global_settings": {
            "output_format": "png",
            "quality": 95,
            "parallel_processing": True,
            "max_workers": 4,
            "preserve_metadata": True,
        },
        "image_configurations": image_configs,
    }

    # Save configuration
    config_file = "./batch_example_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    print("⚙️  Configuration created:")
    print(f"   Images to process: {len(image_configs)}")
    print(f"   Workers: {config['global_settings']['max_workers']}")
    print(f"   Configuration file: {config_file}")

    # Validate setup
    print("\n🔍 Validating setup...")
    issues = creator.validate_setup()
    if issues:
        print("   ❌ Setup issues found:")
        for issue in issues:
            print(f"      - {issue}")
        return False
    else:
        print("   ✅ Setup validation passed")

    # Show dataset info
    info = creator.get_dataset_info()
    print("📊 Dataset info:")
    print(f"   Output directory: {info['output_directory']}")
    print(f"   Available blur types: {len(info.get('available_blur_types', []))}")

    print("🚀 Batch processing would start here...")
    print("   (Skipping actual processing in example)")

    return True


def example_advanced_batch_processing():
    """Demonstrate advanced batch processing with custom configuration."""
    print("\n🔹 Advanced Batch Processing Example")
    print("=" * 50)

    # Create larger sample dataset
    input_dir = "./advanced_batch_input"
    image_paths = create_sample_image_dataset(input_dir, num_images=15)

    # Custom batch configuration
    batch_config = BatchConfig(
        max_workers=6,
        use_multiprocessing=True,
        chunk_size=8,
        retry_attempts=3,
        timeout_per_image=300.0,
        max_memory_gb=4.0,
        continue_on_error=True,
    )

    # Create dataset creator with custom config
    output_dir = "./advanced_batch_output"
    DatasetCreator(output_dir, batch_config)

    # Create complex configuration with multiple blur variants per image
    image_configs = {}

    for i, image_path in enumerate(image_paths):
        # Create multiple blur variants for each image
        variants = [
            {"blur_type": "gaussian", "parameters": {"kernel_size": 3, "sigma_x": 0.5}},
            {"blur_type": "gaussian", "parameters": {"kernel_size": 7, "sigma_x": 1.5}},
            {
                "blur_type": "gaussian",
                "parameters": {"kernel_size": 11, "sigma_x": 2.5},
            },
            {"blur_type": "motion", "parameters": {"angle": i * 24, "length": 15}},
            {
                "blur_type": "defocus",
                "parameters": {"radius": 5 + i, "strength": 1.0 + i * 0.1},
            },
        ]

        for j, variant in enumerate(variants):
            config_key = f"{Path(image_path).stem}_variant_{j + 1}"
            image_configs[config_key] = variant

    # Create configuration with advanced settings
    config = {
        "metadata": {
            "created_by": "Advanced Batch Processing Example",
            "creation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0.0",
            "description": "Advanced batch processing with multiple variants",
            "experiment_type": "parameter_study",
            "total_variants": len(image_configs),
        },
        "global_settings": {
            "output_format": "png",
            "quality": 98,
            "parallel_processing": True,
            "max_workers": 6,
            "chunk_size": 8,
            "retry_attempts": 3,
            "timeout_per_image": 300,
            "preserve_metadata": True,
            "organize_by_blur_type": True,
            "continue_on_error": True,
        },
        "image_configurations": image_configs,
    }

    # Save configuration
    config_file = "./advanced_batch_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    print("⚙️  Advanced configuration created:")
    print(f"   Total variants: {len(image_configs)}")
    print(f"   Images: {len(image_paths)}")
    print(f"   Variants per image: {len(variants)}")
    print(
        f"   Batch config: {batch_config.max_workers} workers, chunk size {batch_config.chunk_size}"
    )

    # Show processing requirements estimate
    print("\n📊 Processing requirements estimate:")
    # In real usage, you would call:
    # requirements = creator.pipeline.estimate_processing_requirements(image_paths, image_configs)
    print("   (Would show estimated time, memory, and disk space)")

    print("🚀 Advanced batch processing would start here...")
    print("   (Skipping actual processing in example)")

    return True


def example_progress_monitoring():
    """Demonstrate progress monitoring during batch processing."""
    print("\n🔹 Progress Monitoring Example")
    print("=" * 50)

    # Create small dataset for demonstration
    input_dir = "./progress_example_input"
    image_paths = create_sample_image_dataset(input_dir, num_images=8)

    DatasetCreator("./progress_example_output")

    # Create simple configuration
    image_configs = {
        Path(p).stem: {
            "blur_type": "gaussian",
            "parameters": {"kernel_size": 5, "sigma_x": 1.0},
            "enabled": True,
        }
        for p in image_paths
    }


    # Progress callback with detailed information
    def detailed_progress_callback(current, total, current_file=None):
        percentage = (current / total) * 100

        print(f"\r📈 Progress: {current}/{total} ({percentage:5.1f}%)", end="")

        if current_file:
            filename = Path(current_file).name
            print(f" - Processing: {filename}", end="")

        # Calculate ETA (simplified)
        if current > 0:
            elapsed = time.time() - start_time
            rate = current / elapsed if elapsed > 0 else 0
            remaining = total - current
            eta = remaining / rate if rate > 0 else 0

            print(f" - ETA: {eta:.0f}s", end="")

        print("", flush=True)  # New line

    print("⏱️  Simulating progress monitoring:")

    # Simulate progress updates
    start_time = time.time()
    total_images = len(image_configs)

    for i in range(total_images + 1):
        time.sleep(0.1)  # Simulate processing time

        if i < total_images:
            current_file = image_paths[i]
        else:
            current_file = None

        detailed_progress_callback(i, total_images, current_file)

    print("✅ Progress monitoring simulation completed")


def example_error_handling_and_recovery():
    """Demonstrate error handling and recovery in batch processing."""
    print("\n🔹 Error Handling and Recovery Example")
    print("=" * 50)

    # Create dataset with some problematic images
    input_dir = "./error_example_input"
    output_dir = "./error_example_output"

    # Create mix of valid and invalid images
    valid_images = create_sample_image_dataset(input_dir, num_images=6)

    # Create some "problematic" image files (invalid formats, corrupted, etc.)
    problematic_files = []

    for i in range(2):
        # Create files that look like images but aren't
        problem_file = Path(input_dir) / f"problematic_{i + 1}.jpg"
        with open(problem_file, "w") as f:
            f.write("This is not an image file")
        problematic_files.append(str(problem_file))

    all_files = valid_images + problematic_files

    print(
        f"📁 Created dataset with {len(valid_images)} valid and {len(problematic_files)} problematic files"
    )

    # Create configuration
    image_configs = {}
    for file_path in all_files:
        image_configs[Path(file_path).name] = {
            "blur_type": "gaussian",
            "parameters": {"kernel_size": 5, "sigma_x": 1.0},
            "enabled": True,
        }


    # Configure batch processing with error handling
    batch_config = BatchConfig(
        max_workers=2,
        use_multiprocessing=False,  # Use threading for better error handling demo
        chunk_size=3,
        retry_attempts=2,
        continue_on_error=True,
    )

    DatasetCreator(output_dir, batch_config)

    print("🛠️  Batch configuration with error handling:")
    print(f"   Continue on error: {batch_config.continue_on_error}")
    print(f"   Retry attempts: {batch_config.retry_attempts}")
    print(f"   Chunk size: {batch_config.chunk_size}")

    # In real usage, you would process and handle errors:
    print("🚀 Error handling simulation:")
    print("   (In real processing, errors would be caught and handled gracefully)")

    # Simulate error scenarios
    error_scenarios = [
        ("Valid image", True, "gaussian blur applied successfully"),
        ("Corrupted file", False, "File format not recognized"),
        ("Valid image", True, "motion blur applied successfully"),
        ("Permission denied", False, "Permission denied accessing file"),
        ("Valid image", True, "defocus blur applied successfully"),
    ]

    for scenario, success, message in error_scenarios:
        if success:
            print(f"   ✅ {scenario}: {message}")
        else:
            print(f"   ❌ {scenario}: {message}")
            print("      🔄 Retrying... (simulation)")
            print("      ✅ Recovered after retry")
            print("🚀 Batch processing would continue with remaining images")
    return True


def example_parallel_processing_optimization():
    """Demonstrate parallel processing optimization techniques."""
    print("\n🔹 Parallel Processing Optimization Example")
    print("=" * 50)

    import multiprocessing as mp

    # Get system information
    cpu_count = mp.cpu_count()
    print("🖥️  System information:")
    print(f"   CPU cores: {cpu_count}")

    # Test different worker configurations
    worker_configs = [
        {"max_workers": 1, "description": "Single-threaded"},
        {"max_workers": 2, "description": "Dual-core optimized"},
        {"max_workers": 4, "description": "Quad-core optimized"},
        {"max_workers": cpu_count, "description": "Full CPU utilization"},
        {"max_workers": cpu_count * 2, "description": "Hyperthreading"},
    ]

    print("\n⚡ Testing worker configurations:")

    for config in worker_configs:
        workers = config["max_workers"]
        description = config["description"]

        # Estimate performance for this configuration
        # In real usage, you would benchmark actual processing
        if workers == 1:
            estimated_time = "Baseline"
            efficiency = "100%"
        elif workers <= cpu_count:
            estimated_time = f"{workers}x faster"
            efficiency = "High"
        else:
            estimated_time = f"{workers}x faster (diminishing returns)"
            efficiency = "Medium"

        print(
            f"   Workers: {workers:>2d} - {description:<20} - Time: {estimated_time:<25} - Efficiency: {efficiency}"
        )

    # Optimal configuration recommendation
    print("\n💡 Optimal configuration recommendations:")
    print(f"   • Use {min(cpu_count, 4)}-{cpu_count} workers for CPU-bound tasks")
    print(f"   • Use {cpu_count * 2} workers for I/O-bound tasks")
    print("   • Monitor memory usage and adjust chunk sizes")
    print("   • Consider hyperthreading limitations")

    # Demonstrate adaptive configuration
    print("\n🔧 Adaptive configuration example:")
    if cpu_count >= 8:
        recommended_workers = cpu_count
        chunk_size = 20
    elif cpu_count >= 4:
        recommended_workers = cpu_count
        chunk_size = 15
    else:
        recommended_workers = max(1, cpu_count - 1)
        chunk_size = 10

    adaptive_config = BatchConfig(
        max_workers=recommended_workers,
        chunk_size=chunk_size,
        use_multiprocessing=True,
        retry_attempts=3,
    )

    print(f"   Recommended workers: {adaptive_config.max_workers}")
    print(f"   Recommended chunk size: {adaptive_config.chunk_size}")
    print(f"   Multiprocessing: {adaptive_config.use_multiprocessing}")


def example_large_scale_processing():
    """Demonstrate techniques for large-scale dataset processing."""
    print("\n🔹 Large-Scale Processing Example")
    print("=" * 50)

    # Simulate large dataset scenario
    large_dataset_sizes = [100, 1000, 10000]

    for num_images in large_dataset_sizes:
        print(f"\n📊 Scenario: {num_images} images")

        # Estimate processing requirements
        avg_processing_time_per_image = 0.5  # seconds
        avg_image_size_mb = 2.0  # MB per image

        estimated_time = num_images * avg_processing_time_per_image
        estimated_storage = num_images * avg_image_size_mb

        print("   ⏱️  Estimated processing time:")
        if estimated_time < 60:
            print(f"      {estimated_time:.0f} seconds")
        elif estimated_time < 3600:
            print(f"      {estimated_time / 60:.1f} minutes")
        else:
            print(f"      {estimated_time / 3600:.1f} hours")

        print("   💾 Estimated storage:")
        if estimated_storage < 1024:
            print(f"      {estimated_storage:.0f} MB")
        else:
            print(f"      {estimated_storage / 1024:.1f} GB")

        # Recommend batch configuration
        if num_images <= 100:
            workers = 4
            chunk_size = 10
        elif num_images <= 1000:
            workers = 8
            chunk_size = 20
        else:
            workers = 16
            chunk_size = 50

        print(f"   ⚙️  Recommended config: {workers} workers, chunk size {chunk_size}")

    # Large-scale processing strategies
    print("\n🚀 Large-scale processing strategies:")
    print("   • Process in stages for very large datasets")
    print("   • Use distributed processing for 100k+ images")
    print("   • Implement checkpoint/resume functionality")
    print("   • Monitor system resources and scale accordingly")
    print("   • Consider cloud-based processing for extreme scales")


def main():
    """Run all batch processing examples."""
    print("Blur Suite SDK - Batch Processing Examples")
    print("=" * 60)
    print()

    try:
        # Run examples
        example_basic_batch_processing()
        example_advanced_batch_processing()
        example_progress_monitoring()
        example_error_handling_and_recovery()
        example_parallel_processing_optimization()
        example_large_scale_processing()

        print("\n" + "=" * 60)
        print("🎉 All batch processing examples completed successfully!")
        print("=" * 60)

        # Summary
        print("\n📊 Summary:")
        print("   • Demonstrated basic batch processing setup")
        print("   • Showed advanced configuration with multiple variants")
        print("   • Explored progress monitoring techniques")
        print("   • Covered comprehensive error handling")
        print("   • Optimized parallel processing configurations")
        print("   • Planned large-scale processing strategies")

        print("\n🚀 Next steps:")
        print("   • Apply these techniques to your own datasets")
        print("   • Monitor performance and adjust configurations")
        print("   • Implement automated batch processing pipelines")
        print("   • Scale up to larger datasets as needed")
        print("   • Integrate with workflow management systems")

        return True

    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
