#!/usr/bin/env python3
"""
Blur Suite SDK - Integration Example

This script demonstrates how to integrate Blur Suite SDK with other tools,
frameworks, and workflows for comprehensive image processing pipelines.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np

import blur_suite as bs


def example_web_framework_integration():
    """Demonstrate integration with web frameworks like Flask/FastAPI."""
    print("🔹 Web Framework Integration Example")
    print("=" * 50)

    print("🌐 Example: Flask API endpoint for blur processing")

    # Simulated Flask-like API endpoint
    def process_image_endpoint(image_data, blur_type="gaussian", **params):
        """Simulate a web API endpoint for blur processing."""
        try:
            # Convert image data to numpy array
            image = np.frombuffer(image_data, dtype=np.uint8)
            # In real implementation, you would reshape based on image dimensions

            # Create blur effect
            factory = bs.BlurFactory()
            effect = factory.create_effect(blur_type, **params)

            # Apply blur
            result = effect.apply(image)

            # Return processed image data
            return {
                "success": True,
                "processing_time_ms": result.processing_time_ms,
                "blur_type": str(result.blur_type),
                "parameters": result.parameters,
                "image_data": result.result_image.tobytes(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # Simulate API usage
    print("📡 Simulating API calls:")

    # Create test image
    test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    # Simulate different API requests
    api_requests = [
        {"blur_type": "gaussian", "kernel_size": 5, "sigma_x": 1.0},
        {"blur_type": "motion", "angle": 45.0, "length": 15},
        {"blur_type": "defocus", "radius": 8, "strength": 1.2},
    ]

    for i, request in enumerate(api_requests):
        print(f"\n   📨 API Request {i + 1}: {request['blur_type']}")

        # Simulate API call
        response = process_image_endpoint(test_image.tobytes(), **request)

        if response["success"]:
            print(f"   ✅ Success: {response['processing_time_ms']:.1f}ms")
            print(f"   📊 Blur type: {response['blur_type']}")
        else:
            print(f"   ❌ Failed: {response['error']}")

    print("\n💡 Web integration benefits:")
    print("   • RESTful API for remote processing")
    print("   • Batch processing via HTTP requests")
    print("   • Integration with web applications")
    print("   • Scalable cloud deployment")


def example_ml_pipeline_integration():
    """Demonstrate integration with machine learning pipelines."""
    print("\n🔹 ML Pipeline Integration Example")
    print("=" * 50)

    print("🤖 Example: Image preprocessing for ML models")

    class BlurPreprocessor:
        """Preprocessor for adding blur effects to ML training data."""

        def __init__(self, target_blur_types=None):
            """Initialize ML preprocessor."""
            self.target_blur_types = target_blur_types or [
                "gaussian",
                "motion",
                "defocus",
            ]
            self.factory = bs.BlurFactory()

        def preprocess_dataset(self, image_paths: List[str], output_dir: str) -> Dict:
            """Preprocess dataset for ML training.

            Args:
                image_paths: List of image file paths
                output_dir: Output directory for preprocessed images

            Returns:
                Dictionary with preprocessing statistics
            """
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)

            stats = {
                "total_images": len(image_paths),
                "processed_images": 0,
                "failed_images": 0,
                "blur_distribution": {
                    blur_type: 0 for blur_type in self.target_blur_types
                },
            }

            print(f"🔄 Preprocessing {len(image_paths)} images for ML training...")

            for i, image_path in enumerate(image_paths):
                try:
                    # Load image
                    image = self._load_image(image_path)

                    # Apply random blur effect
                    blur_type = np.random.choice(self.target_blur_types)
                    params = self._get_random_params(blur_type)

                    # Apply blur
                    effect = self.factory.create_effect(blur_type, **params)
                    result = effect.apply(image)

                    # Save preprocessed image
                    output_filename = f"ml_{blur_type}_{i:04d}.png"
                    output_file = output_path / output_filename
                    self._save_image(result.result_image, output_file)

                    # Update statistics
                    stats["processed_images"] += 1
                    stats["blur_distribution"][blur_type] += 1

                    if (i + 1) % 10 == 0:
                        print(f"   Processed {i + 1}/{len(image_paths)} images...")

                except Exception as e:
                    print(f"   ❌ Failed to process {image_path}: {e}")
                    stats["failed_images"] += 1

            print("✅ ML preprocessing completed!")
            return stats

        def _load_image(self, image_path: str) -> np.ndarray:
            """Load image from file path."""
            from PIL import Image

            image = Image.open(image_path)
            if image.mode != "RGB":
                image = image.convert("RGB")
            return np.array(image)

        def _save_image(self, image: np.ndarray, output_path: Path) -> None:
            """Save image to file path."""
            from PIL import Image

            pil_image = Image.fromarray(image)
            pil_image.save(output_path)

        def _get_random_params(self, blur_type: str) -> Dict:
            """Get random parameters for blur type."""
            if blur_type == "gaussian":
                return {
                    "kernel_size": np.random.choice([3, 5, 7, 9]),
                    "sigma_x": np.random.uniform(0.5, 3.0),
                    "sigma_y": np.random.uniform(0.5, 3.0),
                }
            elif blur_type == "motion":
                return {
                    "angle": np.random.uniform(0, 360),
                    "length": np.random.randint(5, 30),
                }
            elif blur_type == "defocus":
                return {
                    "radius": np.random.randint(3, 15),
                    "strength": np.random.uniform(0.5, 2.0),
                }
            else:
                return {}

    # Demonstrate ML integration
    preprocessor = BlurPreprocessor()

    # Create sample dataset for ML
    sample_images = []
    for i in range(20):
        # Create different types of images for ML training
        if i % 3 == 0:
            # Clean image
            img = np.ones((128, 128, 3), dtype=np.uint8) * 255
        elif i % 3 == 1:
            # Pattern image
            img = np.zeros((128, 128, 3), dtype=np.uint8)
            img[30:98, 30:98] = 255
        else:
            # Textured image
            img = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)

        sample_images.append(f"./ml_sample_{i}.png")

        # Save sample image
        from PIL import Image

        Image.fromarray(img).save(sample_images[-1])

    # Preprocess for ML training
    ml_stats = preprocessor.preprocess_dataset(sample_images, "./ml_preprocessed")

    print("📊 ML preprocessing results:")
    print(f"   Total images: {ml_stats['total_images']}")
    print(f"   Successfully processed: {ml_stats['processed_images']}")
    print(f"   Failed: {ml_stats['failed_images']}")
    print("   Blur distribution:")
    for blur_type, count in ml_stats["blur_distribution"].items():
        print(f"     {blur_type}: {count}")

    print("\n💡 ML integration benefits:")
    print("   • Automated data augmentation with blur effects")
    print("   • Consistent preprocessing across training pipeline")
    print("   • Integration with popular ML frameworks")
    print("   • Scalable preprocessing for large datasets")


def example_computer_vision_integration():
    """Demonstrate integration with computer vision workflows."""
    print("\n🔹 Computer Vision Integration Example")
    print("=" * 50)

    print("👁️  Example: Blur effect analysis in CV pipeline")

    class BlurAnalysisPipeline:
        """Computer vision pipeline with blur analysis."""

        def __init__(self):
            """Initialize CV pipeline."""
            self.factory = bs.BlurFactory()
            self.analysis_results = []

        def analyze_image_collection(self, image_paths: List[str]) -> Dict:
            """Analyze collection of images for blur effects.

            Args:
                image_paths: List of image file paths

            Returns:
                Dictionary with analysis results
            """
            results = {
                "total_images": len(image_paths),
                "blur_analysis": {},
                "quality_metrics": {},
                "processing_times": [],
            }

            print(f"🔍 Analyzing {len(image_paths)} images for blur effects...")

            for image_path in image_paths:
                try:
                    # Load and analyze image
                    image = self._load_image(image_path)
                    analysis = self._analyze_blur_effects(image)

                    # Store results
                    results["blur_analysis"][Path(image_path).name] = analysis
                    results["processing_times"].append(analysis["total_time_ms"])

                    print(f"   ✅ Analyzed: {Path(image_path).name}")

                except Exception as e:
                    print(f"   ❌ Failed to analyze {image_path}: {e}")

            # Calculate aggregate metrics
            results["quality_metrics"] = self._calculate_aggregate_metrics(
                results["blur_analysis"]
            )

            return results

        def _load_image(self, image_path: str) -> np.ndarray:
            """Load image for analysis."""
            from PIL import Image

            image = Image.open(image_path)
            if image.mode != "RGB":
                image = image.convert("RGB")
            return np.array(image)

        def _analyze_blur_effects(self, image: np.ndarray) -> Dict:
            """Analyze image with different blur effects."""
            analysis_start = time.time()

            # Test different blur effects
            blur_tests = [
                ("none", None, {}),
                ("light_gaussian", "gaussian", {"kernel_size": 3, "sigma_x": 0.5}),
                ("medium_gaussian", "gaussian", {"kernel_size": 7, "sigma_x": 1.5}),
                ("strong_gaussian", "gaussian", {"kernel_size": 15, "sigma_x": 3.0}),
                ("motion_blur", "motion", {"angle": 45.0, "length": 20}),
                ("defocus_blur", "defocus", {"radius": 10, "strength": 1.5}),
            ]

            effect_results = {}

            for test_name, blur_type, params in blur_tests:
                if blur_type is None:
                    # No blur - use original image
                    processing_time = 0.0
                    psnr = float("inf")
                    ssim = 1.0
                else:
                    # Apply blur effect
                    effect = self.factory.create_effect(blur_type, **params)
                    start_time = time.time()
                    result = effect.apply(image)
                    processing_time = (time.time() - start_time) * 1000

                    # Calculate quality metrics
                    try:
                        psnr = self._calculate_psnr(image, result.result_image)
                        ssim = self._calculate_ssim(image, result.result_image)
                    except:
                        psnr = 0.0
                        ssim = 0.0

                effect_results[test_name] = {
                    "processing_time_ms": processing_time,
                    "psnr": psnr,
                    "ssim": ssim,
                    "parameters": params if params else {},
                }

            total_time = (time.time() - analysis_start) * 1000

            return {
                "total_time_ms": total_time,
                "effect_results": effect_results,
                "image_shape": image.shape,
            }

        def _calculate_psnr(self, original: np.ndarray, processed: np.ndarray) -> float:
            """Calculate PSNR between images."""
            mse = np.mean(
                (original.astype(np.float32) - processed.astype(np.float32)) ** 2
            )
            if mse == 0:
                return float("inf")
            return 20 * np.log10(255.0 / np.sqrt(mse))

        def _calculate_ssim(self, original: np.ndarray, processed: np.ndarray) -> float:
            """Calculate SSIM between images (simplified)."""
            # Simplified SSIM calculation
            orig_float = original.astype(np.float32)
            proc_float = processed.astype(np.float32)

            # Calculate means
            mu1 = np.mean(orig_float)
            mu2 = np.mean(proc_float)

            # Calculate standard deviations
            sigma1 = np.std(orig_float)
            sigma2 = np.std(proc_float)

            # Calculate correlation coefficient
            np.corrcoef(orig_float.flatten(), proc_float.flatten())[0, 1]

            # SSIM components
            c1 = (0.01 * 255) ** 2
            c2 = (0.03 * 255) ** 2

            ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma1 * sigma2 + c2)) / (
                (mu1**2 + mu2**2 + c1) * (sigma1**2 + sigma2**2 + c2)
            )

            return ssim

        def _calculate_aggregate_metrics(self, blur_analysis: Dict) -> Dict:
            """Calculate aggregate metrics across all analyses."""
            all_times = []
            all_psnr = []
            all_ssim = []

            for image_name, analysis in blur_analysis.items():
                for effect_name, effect_result in analysis["effect_results"].items():
                    if effect_result["processing_time_ms"] > 0:
                        all_times.append(effect_result["processing_time_ms"])
                    if effect_result["psnr"] < float("inf"):
                        all_psnr.append(effect_result["psnr"])
                    if effect_result["ssim"] < 1.0:
                        all_ssim.append(effect_result["ssim"])

            return {
                "avg_processing_time_ms": sum(all_times) / len(all_times)
                if all_times
                else 0,
                "avg_psnr": sum(all_psnr) / len(all_psnr) if all_psnr else 0,
                "avg_ssim": sum(all_ssim) / len(all_ssim) if all_ssim else 0,
                "total_analyses": len(all_times),
            }

    # Demonstrate CV integration
    pipeline = BlurAnalysisPipeline()

    # Create sample images for analysis
    sample_images = []
    for i in range(5):
        # Create images with different characteristics
        if i == 0:
            # Sharp image
            img = np.ones((200, 200, 3), dtype=np.uint8) * 255
            # Add sharp edges
            img[50:150, 50:150] = [0, 0, 0]
        else:
            # Blurred variations
            img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)

        filename = f"./cv_sample_{i}.png"
        from PIL import Image

        Image.fromarray(img).save(filename)
        sample_images.append(filename)

    # Analyze images
    analysis_results = pipeline.analyze_image_collection(sample_images)

    print("📊 CV analysis results:")
    print(f"   Images analyzed: {analysis_results['total_images']}")
    print(f"   Total analyses: {analysis_results['quality_metrics']['total_analyses']}")
    print(
        f"   Average processing time: {analysis_results['quality_metrics']['avg_processing_time_ms']:.1f}ms"
    )
    print(f"   Average PSNR: {analysis_results['quality_metrics']['avg_psnr']:.2f}dB")
    print(f"   Average SSIM: {analysis_results['quality_metrics']['avg_ssim']:.4f}")

    print("\n💡 CV integration benefits:")
    print("   • Automated blur effect analysis")
    print("   • Quality assessment for image collections")
    print("   • Integration with existing CV workflows")
    print("   • Batch analysis capabilities")


def example_cloud_integration():
    """Demonstrate cloud platform integration patterns."""
    print("\n🔹 Cloud Integration Example")
    print("=" * 50)

    print("☁️  Example: AWS Lambda function for blur processing")

    def lambda_blur_processor(event, context):
        """AWS Lambda function for blur processing."""
        try:
            # Parse input from event
            input_data = event.get("input_data", {})
            image_data = input_data.get("image_data")
            blur_config = input_data.get("blur_config", {})

            if not image_data or not blur_config:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Missing image_data or blur_config"}),
                }

            # Convert image data to numpy array
            image = np.frombuffer(image_data, dtype=np.uint8)
            # In real implementation, reshape based on metadata

            # Create and apply blur effect
            factory = bs.BlurFactory()
            blur_type = blur_config.get("blur_type", "gaussian")
            parameters = blur_config.get("parameters", {})

            effect = factory.create_effect(blur_type, **parameters)
            result = effect.apply(image)

            # Return processed result
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "success": True,
                        "processing_time_ms": result.processing_time_ms,
                        "blur_type": str(result.blur_type),
                        "parameters": result.parameters,
                        "result_image_data": result.result_image.tobytes(),
                    }
                ),
            }

        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"success": False, "error": str(e)}),
            }

    # Simulate cloud function calls
    print("📡 Simulating cloud function calls:")

    test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    cloud_requests = [
        {"blur_type": "gaussian", "parameters": {"kernel_size": 5, "sigma_x": 1.0}},
        {"blur_type": "motion", "parameters": {"angle": 30.0, "length": 20}},
        {"blur_type": "defocus", "parameters": {"radius": 8, "strength": 1.5}},
    ]

    for i, request in enumerate(cloud_requests):
        print(f"\n   🌐 Cloud Request {i + 1}: {request['blur_type']}")

        # Simulate Lambda event
        event = {
            "input_data": {"image_data": test_image.tobytes(), "blur_config": request}
        }

        # Call Lambda function (simulated)
        response = lambda_blur_processor(event, None)

        if response["statusCode"] == 200:
            result = json.loads(response["body"])
            print(f"   ✅ Success: {result['processing_time_ms']:.1f}ms")
        else:
            error = json.loads(response["body"])
            print(f"   ❌ Failed: {error['error']}")

    print("\n💡 Cloud integration benefits:")
    print("   • Serverless blur processing")
    print("   • Auto-scaling for variable workloads")
    print("   • Pay-per-use pricing model")
    print("   • Global distribution capabilities")


def example_gui_integration():
    """Demonstrate GUI framework integration."""
    print("\n🔹 GUI Framework Integration Example")
    print("=" * 50)

    print("🖼️  Example: PyQt5 integration with Blur Suite SDK")

    class BlurProcessingWidget:
        """PyQt5 widget for blur processing."""

        def __init__(self):
            """Initialize blur processing widget."""
            self.factory = bs.BlurFactory()
            self.current_image = None
            self.current_result = None

        def load_image(self, image_path: str) -> bool:
            """Load image for processing.

            Args:
                image_path: Path to image file

            Returns:
                True if loaded successfully
            """
            try:
                from PIL import Image

                image = Image.open(image_path)
                if image.mode != "RGB":
                    image = image.convert("RGB")
                self.current_image = np.array(image)

                print(f"   📷 Loaded image: {image_path}")
                return True

            except Exception as e:
                print(f"   ❌ Failed to load image: {e}")
                return False

        def apply_blur_effect(self, blur_type: str, **params) -> bool:
            """Apply blur effect to current image.

            Args:
                blur_type: Type of blur effect
                **params: Blur parameters

            Returns:
                True if applied successfully
            """
            if self.current_image is None:
                print("   ❌ No image loaded")
                return False

            try:
                # Create and apply effect
                effect = self.factory.create_effect(blur_type, **params)
                result = effect.apply(self.current_image)

                self.current_result = result

                print(
                    f"   ✅ Applied {blur_type} blur: {result.processing_time_ms:.1f}ms"
                )
                return True

            except Exception as e:
                print(f"   ❌ Failed to apply blur: {e}")
                return False

        def get_processing_info(self) -> Dict:
            """Get information about current processing result."""
            if self.current_result is None:
                return {}

            return {
                "processing_time_ms": self.current_result.processing_time_ms,
                "blur_type": str(self.current_result.blur_type),
                "parameters": self.current_result.parameters,
                "image_shape": self.current_result.result_image.shape,
                "quality_metrics": self.current_result.get_quality_metrics(),
            }

    # Demonstrate GUI integration
    widget = BlurProcessingWidget()

    # Create test image
    test_image = np.random.randint(0, 255, (150, 150, 3), dtype=np.uint8)
    from PIL import Image

    Image.fromarray(test_image).save("./gui_test_image.png")

    # Simulate GUI workflow
    print("🖱️  Simulating GUI workflow:")

    # Load image
    if widget.load_image("./gui_test_image.png"):
        print("   ✅ Image loaded in GUI widget")

        # Apply different blur effects
        gui_operations = [
            ("Gaussian", "gaussian", {"kernel_size": 7, "sigma_x": 1.5}),
            ("Motion", "motion", {"angle": 45.0, "length": 15}),
            ("Defocus", "defocus", {"radius": 8, "strength": 1.2}),
        ]

        for name, blur_type, params in gui_operations:
            if widget.apply_blur_effect(blur_type, **params):
                info = widget.get_processing_info()
                print(f"   🎛️  {name} blur applied: {info['processing_time_ms']:.1f}ms")

    print("\n💡 GUI integration benefits:")
    print("   • Interactive parameter adjustment")
    print("   • Real-time preview capabilities")
    print("   • User-friendly blur effect selection")
    print("   • Integration with popular GUI frameworks")


def example_scripting_integration():
    """Demonstrate command-line scripting integration."""
    print("\n🔹 Scripting Integration Example")
    print("=" * 50)

    print("📜 Example: Shell script integration with Blur Suite CLI")

    # Simulate shell script that uses blur-suite commands
    def simulate_blur_script(input_dir: str, output_dir: str, config_file: str) -> bool:
        """Simulate shell script for batch processing."""
        print("#!/bin/bash")
        print("# Blur processing script")
        print(f"INPUT_DIR='{input_dir}'")
        print(f"OUTPUT_DIR='{output_dir}'")
        print(f"CONFIG_FILE='{config_file}'")
        print("")
        print("# Validate configuration")
        print("echo 'Validating configuration...'")
        print('blur-suite config validate "$CONFIG_FILE"')
        print("")
        print("# Process images")
        print("echo 'Processing images...'")
        print('blur-suite process batch "$INPUT_DIR" "$OUTPUT_DIR" \\')
        print('  --config "$CONFIG_FILE" \\')
        print("  --workers 8 \\")
        print("  --progress-bar")
        print("")
        print("# Generate report")
        print("echo 'Generating report...'")
        print('blur-suite info performance --output-report "$OUTPUT_DIR/report.json"')
        print("")
        print("echo 'Processing completed!'")

        return True

    # Demonstrate scripting integration
    print("📜 Simulated shell script:")
    simulate_blur_script("./input_images", "./output_dataset", "./dataset_config.json")

    print("\n💡 Scripting integration benefits:")
    print("   • Automation of repetitive tasks")
    print("   • Integration with existing workflows")
    print("   • Batch processing capabilities")
    print("   • Error handling and logging")
    print("   • Scheduling and cron job integration")


def main():
    """Run all integration examples."""
    print("Blur Suite SDK - Integration Examples")
    print("=" * 60)
    print()

    try:
        # Run examples
        example_web_framework_integration()
        example_ml_pipeline_integration()
        example_computer_vision_integration()
        example_cloud_integration()
        example_gui_integration()
        example_scripting_integration()

        print("\n" + "=" * 60)
        print("🎉 All integration examples completed successfully!")
        print("=" * 60)

        # Summary
        print("\n📊 Summary:")
        print("   • Demonstrated web framework integration")
        print("   • Showed ML pipeline integration")
        print("   • Explored computer vision workflows")
        print("   • Covered cloud platform integration")
        print("   • Demonstrated GUI framework integration")
        print("   • Showed command-line scripting patterns")

        print("\n🚀 Next steps:")
        print("   • Choose integration pattern for your use case")
        print("   • Adapt examples to your specific requirements")
        print("   • Combine multiple integration patterns")
        print("   • Scale integrations for production use")
        print("   • Monitor and optimize integrated workflows")

        return True

    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
