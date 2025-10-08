"""
Hook Manager

Central management system for extensibility hooks throughout the SDK.
"""

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class HookType(Enum):
    """Types of hooks available in the system."""

    PRE_PROCESSING = "pre_processing"
    POST_PROCESSING = "post_processing"
    PARAMETER_VALIDATION = "parameter_validation"
    IMAGE_LOADING = "image_loading"
    IMAGE_SAVING = "image_saving"
    BLUR_EXECUTION = "blur_execution"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE_MONITORING = "performance_monitoring"
    CUSTOM_EFFECT = "custom_effect"
    PLUGIN_LIFECYCLE = "plugin_lifecycle"


@dataclass
class HookContext:
    """Context information for hook execution."""

    hook_type: HookType
    hook_name: str
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def get(self, key: str, default: Any = None) -> Any:
        """Get context data."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        """Set context data."""
        self.data[key] = value


@dataclass
class HookResult:
    """Result of hook execution."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    modified: bool = False
    execution_time: float = 0.0


class HookManager:
    """
    Central hook management system.

    Provides extensibility points throughout the SDK for
    custom integrations and enhanced functionality.
    """

    def __init__(self):
        """Initialize hook manager."""
        self._hooks: Dict[str, List[Callable]] = {}
        self._hook_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

        # Hook execution statistics
        self.stats = {
            "hooks_registered": 0,
            "hooks_executed": 0,
            "total_execution_time": 0.0,
            "errors": 0,
        }

        # Initialize default hooks
        self._initialize_default_hooks()

    def _initialize_default_hooks(self):
        """Initialize default hook points."""
        default_hooks = [
            HookType.PRE_PROCESSING.value,
            HookType.POST_PROCESSING.value,
            HookType.PARAMETER_VALIDATION.value,
            HookType.IMAGE_LOADING.value,
            HookType.IMAGE_SAVING.value,
            HookType.BLUR_EXECUTION.value,
            HookType.ERROR_HANDLING.value,
            HookType.PERFORMANCE_MONITORING.value,
            HookType.CUSTOM_EFFECT.value,
            HookType.PLUGIN_LIFECYCLE.value,
        ]

        for hook_name in default_hooks:
            self._hooks[hook_name] = []

    def register_hook(
        self,
        hook_type: Union[HookType, str],
        hook_func: Callable,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a hook function.

        Args:
            hook_type: Type of hook or hook name
            hook_func: Hook function to register
            priority: Hook priority (higher = executed first)
            metadata: Additional metadata for the hook

        Returns:
            Hook ID for later unregistration
        """
        hook_name = hook_type.value if isinstance(hook_type, HookType) else hook_type

        # Create hook entry
        hook_id = f"{hook_name}_{len(self._hooks.get(hook_name, []))}_{id(hook_func)}"

        hook_entry = {
            "id": hook_id,
            "func": hook_func,
            "priority": priority,
            "metadata": metadata or {},
            "registered_at": time.time(),
        }

        with self._lock:
            if hook_name not in self._hooks:
                self._hooks[hook_name] = []

            # Insert hook in priority order
            self._insert_hook_by_priority(self._hooks[hook_name], hook_entry)
            self.stats["hooks_registered"] += 1

        return hook_id

    def _insert_hook_by_priority(self, hooks_list: List[Dict], hook_entry: Dict):
        """Insert hook entry in priority order."""
        # Sort by priority (higher first)
        sorted_hooks = sorted(
            hooks_list + [hook_entry], key=lambda h: h["priority"], reverse=True
        )

        # Replace the list
        hooks_list.clear()
        hooks_list.extend(sorted_hooks)

    def unregister_hook(self, hook_id: str) -> bool:
        """
        Unregister a hook function.

        Args:
            hook_id: Hook ID returned by register_hook

        Returns:
            True if unregistered, False if not found
        """
        with self._lock:
            for hook_name, hooks_list in self._hooks.items():
                for i, hook_entry in enumerate(hooks_list):
                    if hook_entry["id"] == hook_id:
                        del hooks_list[i]
                        return True

        return False

    def execute_hook(
        self,
        hook_type: Union[HookType, str],
        context: Optional[HookContext] = None,
        **kwargs,
    ) -> List[HookResult]:
        """
        Execute hooks of a specific type.

        Args:
            hook_type: Type of hooks to execute
            context: Hook execution context
            **kwargs: Additional context data

        Returns:
            List of hook execution results
        """
        hook_name = hook_type.value if isinstance(hook_type, HookType) else hook_type

        # Create context if not provided
        if context is None:
            context = HookContext(
                hook_type=HookType(hook_name)
                if hook_name in HookType.__members__
                else HookType.CUSTOM_EFFECT,
                hook_name=hook_name,
                data=kwargs,
            )
        else:
            # Update context data with kwargs
            context.data.update(kwargs)

        results = []

        with self._lock:
            hooks_list = self._hooks.get(hook_name, [])

            for hook_entry in hooks_list:
                start_time = time.time()

                try:
                    # Execute hook function
                    result_data = hook_entry["func"](context)

                    execution_time = time.time() - start_time

                    hook_result = HookResult(
                        success=True,
                        data=result_data,
                        modified=context.get("modified", False),
                        execution_time=execution_time,
                    )

                except Exception as e:
                    execution_time = time.time() - start_time

                    hook_result = HookResult(
                        success=False, error=str(e), execution_time=execution_time
                    )

                    self.stats["errors"] += 1

                results.append(hook_result)
                self.stats["hooks_executed"] += 1
                self.stats["total_execution_time"] += execution_time

        return results

    def execute_hook_sync(
        self,
        hook_type: Union[HookType, str],
        context: Optional[HookContext] = None,
        **kwargs,
    ) -> Any:
        """
        Execute hooks synchronously and return combined result.

        Args:
            hook_type: Type of hooks to execute
            context: Hook execution context
            **kwargs: Additional context data

        Returns:
            Combined result from all hooks
        """
        results = self.execute_hook(hook_type, context, **kwargs)

        # Combine results based on hook type
        if not results:
            return None

        # For synchronous execution, we typically want to chain results
        # or return the first successful result
        for result in results:
            if result.success:
                return result.data

        return None

    def list_hooks(
        self, hook_type: Optional[Union[HookType, str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        List registered hooks.

        Args:
            hook_type: Specific hook type to list, or None for all

        Returns:
            Dictionary of hook information
        """
        with self._lock:
            if hook_type is not None:
                hook_name = (
                    hook_type.value if isinstance(hook_type, HookType) else hook_type
                )
                hooks_list = self._hooks.get(hook_name, [])
                return {hook_name: self._format_hook_list(hooks_list)}
            else:
                all_hooks = {}
                for hook_name, hooks_list in self._hooks.items():
                    all_hooks[hook_name] = self._format_hook_list(hooks_list)
                return all_hooks

    def _format_hook_list(self, hooks_list: List[Dict]) -> List[Dict]:
        """Format hook list for output."""
        formatted = []

        for hook_entry in hooks_list:
            formatted.append(
                {
                    "id": hook_entry["id"],
                    "priority": hook_entry["priority"],
                    "metadata": hook_entry["metadata"],
                    "registered_at": hook_entry["registered_at"],
                }
            )

        return formatted

    def clear_hooks(self, hook_type: Optional[Union[HookType, str]] = None):
        """
        Clear registered hooks.

        Args:
            hook_type: Specific hook type to clear, or None for all
        """
        with self._lock:
            if hook_type is not None:
                hook_name = (
                    hook_type.value if isinstance(hook_type, HookType) else hook_type
                )
                if hook_name in self._hooks:
                    self._hooks[hook_name].clear()
            else:
                for hooks_list in self._hooks.values():
                    hooks_list.clear()

    def get_hook_stats(self) -> Dict[str, Any]:
        """Get hook system statistics."""
        total_hooks = sum(len(hooks) for hooks in self._hooks.values())

        return {
            "total_hooks": total_hooks,
            "hook_types": len(self._hooks),
            "execution_stats": {
                "hooks_executed": self.stats["hooks_executed"],
                "total_execution_time": self.stats["total_execution_time"],
                "errors": self.stats["errors"],
                "avg_execution_time": (
                    self.stats["total_execution_time"] / self.stats["hooks_executed"]
                    if self.stats["hooks_executed"] > 0
                    else 0.0
                ),
            },
            "registration_stats": {"hooks_registered": self.stats["hooks_registered"]},
        }

    def create_hook_decorator(self, hook_type: Union[HookType, str], priority: int = 0):
        """
        Create a decorator for registering hooks.

        Args:
            hook_type: Type of hook
            priority: Hook priority

        Returns:
            Decorator function
        """

        def decorator(func):
            hook_id = self.register_hook(hook_type, func, priority)
            func._hook_id = hook_id  # Store hook ID on function
            return func

        return decorator

    def enable_hook_type(self, hook_type: Union[HookType, str]):
        """
        Enable a hook type.

        Args:
            hook_type: Hook type to enable
        """
        hook_name = hook_type.value if isinstance(hook_type, HookType) else hook_type

        with self._lock:
            if hook_name not in self._hooks:
                self._hooks[hook_name] = []

    def disable_hook_type(self, hook_type: Union[HookType, str]):
        """
        Disable a hook type.

        Args:
            hook_type: Hook type to disable
        """
        hook_name = hook_type.value if isinstance(hook_type, HookType) else hook_type

        with self._lock:
            if hook_name in self._hooks:
                self._hooks[hook_name].clear()


class HookPoint:
    """
    Represents a specific point in the SDK where hooks can be executed.
    """

    def __init__(self, name: str, hook_type: HookType, description: str = ""):
        """
        Initialize hook point.

        Args:
            name: Hook point name
            hook_type: Type of hook
            description: Hook point description
        """
        self.name = name
        self.hook_type = hook_type
        self.description = description

    def execute(
        self, hook_manager: HookManager, context: Optional[HookContext] = None, **kwargs
    ) -> List[HookResult]:
        """
        Execute hooks at this point.

        Args:
            hook_manager: Hook manager instance
            context: Hook execution context
            **kwargs: Additional context data

        Returns:
            List of hook execution results
        """
        if context is None:
            context = HookContext(hook_type=self.hook_type, hook_name=self.name)

        context.hook_name = self.name
        return hook_manager.execute_hook(self.hook_type, context, **kwargs)


# Global hook manager instance
_global_hook_manager = None
_hook_manager_lock = threading.Lock()


def get_global_hook_manager() -> HookManager:
    """Get the global hook manager instance."""
    global _global_hook_manager

    if _global_hook_manager is None:
        with _hook_manager_lock:
            if _global_hook_manager is None:
                _global_hook_manager = HookManager()

    return _global_hook_manager


def register_global_hook(
    hook_type: Union[HookType, str], hook_func: Callable, **kwargs
) -> str:
    """
    Register a hook with the global hook manager.

    Args:
        hook_type: Type of hook
        hook_func: Hook function
        **kwargs: Additional registration arguments

    Returns:
        Hook ID
    """
    manager = get_global_hook_manager()
    return manager.register_hook(hook_type, hook_func, **kwargs)


def execute_global_hook(hook_type: Union[HookType, str], **kwargs) -> List[HookResult]:
    """
    Execute hooks with the global hook manager.

    Args:
        hook_type: Type of hooks to execute
        **kwargs: Context data

    Returns:
        List of hook execution results
    """
    manager = get_global_hook_manager()
    return manager.execute_hook(hook_type, **kwargs)
