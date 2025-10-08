"""
Hook Points

Definition of extensibility points throughout the Blur Suite SDK.
"""

from typing import Dict, List

from .hook_manager import HookContext, HookManager, HookPoint, HookType


class BlurSuiteHookPoints:
    """
    Collection of hook points throughout the Blur Suite SDK.

    Defines specific locations where custom code can be injected
    for enhanced functionality and integration.
    """

    def __init__(self, hook_manager: HookManager):
        """
        Initialize hook points.

        Args:
            hook_manager: Hook manager instance
        """
        self.hook_manager = hook_manager

        # Define hook points
        self._hook_points = {
            "pre_processing": HookPoint(
                "pre_processing",
                HookType.PRE_PROCESSING,
                "Executed before any image processing begins",
            ),
            "post_processing": HookPoint(
                "post_processing",
                HookType.POST_PROCESSING,
                "Executed after all image processing is complete",
            ),
            "parameter_validation": HookPoint(
                "parameter_validation",
                HookType.PARAMETER_VALIDATION,
                "Executed during parameter validation",
            ),
            "image_loading": HookPoint(
                "image_loading",
                HookType.IMAGE_LOADING,
                "Executed when images are loaded",
            ),
            "image_saving": HookPoint(
                "image_saving", HookType.IMAGE_SAVING, "Executed when images are saved"
            ),
            "blur_execution": HookPoint(
                "blur_execution",
                HookType.BLUR_EXECUTION,
                "Executed during blur effect application",
            ),
            "error_handling": HookPoint(
                "error_handling", HookType.ERROR_HANDLING, "Executed when errors occur"
            ),
            "performance_monitoring": HookPoint(
                "performance_monitoring",
                HookType.PERFORMANCE_MONITORING,
                "Executed for performance data collection",
            ),
            "plugin_lifecycle": HookPoint(
                "plugin_lifecycle",
                HookType.PLUGIN_LIFECYCLE,
                "Executed during plugin loading/unloading",
            ),
        }

    def get_hook_point(self, name: str) -> HookPoint:
        """
        Get a specific hook point.

        Args:
            name: Hook point name

        Returns:
            Hook point instance
        """
        return self._hook_points.get(name)

    def list_hook_points(self) -> Dict[str, HookPoint]:
        """List all available hook points."""
        return self._hook_points.copy()

    def execute_pre_processing(self, image_path: str, **kwargs) -> List:
        """
        Execute pre-processing hooks.

        Args:
            image_path: Path to image being processed
            **kwargs: Additional context data

        Returns:
            List of hook results
        """
        context = HookContext(
            hook_type=HookType.PRE_PROCESSING,
            hook_name="pre_processing",
            data={"image_path": image_path, **kwargs},
        )

        return self.hook_manager.execute_hook(HookType.PRE_PROCESSING, context)

    def execute_post_processing(
        self, image_path: str, result_image: any, **kwargs
    ) -> List:
        """
        Execute post-processing hooks.

        Args:
            image_path: Path to processed image
            result_image: Processing result
            **kwargs: Additional context data

        Returns:
            List of hook results
        """
        context = HookContext(
            hook_type=HookType.POST_PROCESSING,
            hook_name="post_processing",
            data={"image_path": image_path, "result_image": result_image, **kwargs},
        )

        return self.hook_manager.execute_hook(HookType.POST_PROCESSING, context)

    def execute_parameter_validation(self, parameters: Dict, **kwargs) -> List:
        """
        Execute parameter validation hooks.

        Args:
            parameters: Parameters being validated
            **kwargs: Additional context data

        Returns:
            List of hook results
        """
        context = HookContext(
            hook_type=HookType.PARAMETER_VALIDATION,
            hook_name="parameter_validation",
            data={"parameters": parameters, **kwargs},
        )

        return self.hook_manager.execute_hook(HookType.PARAMETER_VALIDATION, context)

    def execute_image_loading(
        self, image_path: str, loaded_image: any, **kwargs
    ) -> List:
        """
        Execute image loading hooks.

        Args:
            image_path: Path to loaded image
            loaded_image: Loaded image data
            **kwargs: Additional context data

        Returns:
            List of hook results
        """
        context = HookContext(
            hook_type=HookType.IMAGE_LOADING,
            hook_name="image_loading",
            data={"image_path": image_path, "loaded_image": loaded_image, **kwargs},
        )

        return self.hook_manager.execute_hook(HookType.IMAGE_LOADING, context)

    def execute_image_saving(
        self, image_path: str, image_to_save: any, **kwargs
    ) -> List:
        """
        Execute image saving hooks.

        Args:
            image_path: Path where image will be saved
            image_to_save: Image data to save
            **kwargs: Additional context data

        Returns:
            List of hook results
        """
        context = HookContext(
            hook_type=HookType.IMAGE_SAVING,
            hook_name="image_saving",
            data={"image_path": image_path, "image_to_save": image_to_save, **kwargs},
        )

        return self.hook_manager.execute_hook(HookType.IMAGE_SAVING, context)

    def execute_blur_execution(
        self, blur_type: str, parameters: Dict, input_image: any, **kwargs
    ) -> List:
        """
        Execute blur execution hooks.

        Args:
            blur_type: Type of blur being applied
            parameters: Blur parameters
            input_image: Input image data
            **kwargs: Additional context data

        Returns:
            List of hook results
        """
        context = HookContext(
            hook_type=HookType.BLUR_EXECUTION,
            hook_name="blur_execution",
            data={
                "blur_type": blur_type,
                "parameters": parameters,
                "input_image": input_image,
                **kwargs,
            },
        )

        return self.hook_manager.execute_hook(HookType.BLUR_EXECUTION, context)

    def execute_error_handling(
        self, error: Exception, context_data: Dict, **kwargs
    ) -> List:
        """
        Execute error handling hooks.

        Args:
            error: Exception that occurred
            context_data: Context information about the error
            **kwargs: Additional context data

        Returns:
            List of hook results
        """
        context = HookContext(
            hook_type=HookType.ERROR_HANDLING,
            hook_name="error_handling",
            data={
                "error": error,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context_data,
                **kwargs,
            },
        )

        return self.hook_manager.execute_hook(HookType.ERROR_HANDLING, context)

    def execute_performance_monitoring(
        self, operation: str, duration: float, metadata: Dict, **kwargs
    ) -> List:
        """
        Execute performance monitoring hooks.

        Args:
            operation: Operation that was monitored
            duration: Operation duration in seconds
            metadata: Performance metadata
            **kwargs: Additional context data

        Returns:
            List of hook results
        """
        context = HookContext(
            hook_type=HookType.PERFORMANCE_MONITORING,
            hook_name="performance_monitoring",
            data={
                "operation": operation,
                "duration": duration,
                "metadata": metadata,
                **kwargs,
            },
        )

        return self.hook_manager.execute_hook(HookType.PERFORMANCE_MONITORING, context)

    def execute_plugin_lifecycle(
        self, event: str, plugin_name: str, plugin_data: Dict, **kwargs
    ) -> List:
        """
        Execute plugin lifecycle hooks.

        Args:
            event: Lifecycle event ('loaded', 'unloaded', 'enabled', 'disabled')
            plugin_name: Name of the plugin
            plugin_data: Plugin information
            **kwargs: Additional context data

        Returns:
            List of hook results
        """
        context = HookContext(
            hook_type=HookType.PLUGIN_LIFECYCLE,
            hook_name="plugin_lifecycle",
            data={
                "event": event,
                "plugin_name": plugin_name,
                "plugin_data": plugin_data,
                **kwargs,
            },
        )

        return self.hook_manager.execute_hook(HookType.PLUGIN_LIFECYCLE, context)


class IntegrationHelper:
    """
    Helper class for integrating hooks into existing code.
    """

    def __init__(self, hook_manager: HookManager):
        """
        Initialize integration helper.

        Args:
            hook_manager: Hook manager instance
        """
        self.hook_manager = hook_manager
        self.hook_points = BlurSuiteHookPoints(hook_manager)

    def wrap_image_processing(self, process_func):
        """
        Wrap an image processing function with hooks.

        Args:
            process_func: Function to wrap

        Returns:
            Wrapped function with hooks
        """

        def wrapped_function(image_path, *args, **kwargs):
            # Execute pre-processing hooks
            self.hook_points.execute_pre_processing(image_path)

            try:
                # Execute the original function
                result = process_func(image_path, *args, **kwargs)

                # Execute post-processing hooks
                self.hook_points.execute_post_processing(image_path, result)

                return result

            except Exception as e:
                # Execute error handling hooks
                self.hook_points.execute_error_handling(
                    e, {"function": process_func.__name__, "image_path": image_path}
                )

                raise

        return wrapped_function

    def wrap_blur_application(self, blur_func):
        """
        Wrap a blur application function with hooks.

        Args:
            blur_func: Blur function to wrap

        Returns:
            Wrapped function with hooks
        """

        def wrapped_function(image, blur_type, parameters, *args, **kwargs):
            # Execute blur execution hooks
            self.hook_points.execute_blur_execution(blur_type, parameters, image)

            try:
                # Execute the original function
                result = blur_func(image, blur_type, parameters, *args, **kwargs)

                return result

            except Exception as e:
                # Execute error handling hooks
                self.hook_points.execute_error_handling(
                    e,
                    {
                        "function": blur_func.__name__,
                        "blur_type": blur_type,
                        "parameters": parameters,
                    },
                )

                raise

        return wrapped_function

    def monitor_performance(self, operation_func):
        """
        Wrap a function with performance monitoring hooks.

        Args:
            operation_func: Function to monitor

        Returns:
            Wrapped function with performance monitoring
        """

        def wrapped_function(*args, **kwargs):
            import time

            start_time = time.time()
            operation_name = operation_func.__name__

            try:
                # Execute the original function
                result = operation_func(*args, **kwargs)

                # Calculate duration
                duration = time.time() - start_time

                # Execute performance monitoring hooks
                self.hook_points.execute_performance_monitoring(
                    operation_name,
                    duration,
                    {
                        "success": True,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                )

                return result

            except Exception as e:
                # Calculate duration
                duration = time.time() - start_time

                # Execute performance monitoring hooks (for failed operation)
                self.hook_points.execute_performance_monitoring(
                    operation_name,
                    duration,
                    {
                        "success": False,
                        "error": str(e),
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                )

                raise

        return wrapped_function


# Convenience functions for common hook operations
def register_pre_processing_hook(hook_func, priority: int = 0) -> str:
    """Register a pre-processing hook."""
    manager = HookManager()
    return manager.register_hook(HookType.PRE_PROCESSING, hook_func, priority)


def register_post_processing_hook(hook_func, priority: int = 0) -> str:
    """Register a post-processing hook."""
    manager = HookManager()
    return manager.register_hook(HookType.POST_PROCESSING, hook_func, priority)


def register_error_handler(hook_func, priority: int = 0) -> str:
    """Register an error handling hook."""
    manager = HookManager()
    return manager.register_hook(HookType.ERROR_HANDLING, hook_func, priority)


def register_performance_monitor(hook_func, priority: int = 0) -> str:
    """Register a performance monitoring hook."""
    manager = HookManager()
    return manager.register_hook(HookType.PERFORMANCE_MONITORING, hook_func, priority)
