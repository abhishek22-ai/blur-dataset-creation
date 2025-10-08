"""
Circuit Breaker

Circuit breaker pattern implementation for fault tolerance and preventing cascading failures.
"""

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Type


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerMetrics:
    """Circuit breaker performance metrics."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    total_downtime: float = 0.0
    last_state_change: float = field(default_factory=time.time)


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.

    Prevents cascading failures by temporarily stopping
    requests to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
        name: str = "default",
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
            name: Circuit breaker name for identification
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name

        # State management
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = threading.Lock()

        # Metrics
        self.metrics = CircuitBreakerMetrics()

        # Callbacks
        self.state_change_callbacks: List[Callable] = []

    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        # Check if call should be allowed
        if not self._can_execute():
            self.metrics.rejected_calls += 1
            raise Exception(f"Circuit breaker '{self.name}' is OPEN")

        try:
            # Execute function
            self.metrics.total_calls += 1
            result = func(*args, **kwargs)
            self.metrics.successful_calls += 1

            # Reset on success if in half-open state
            if self.state == CircuitBreakerState.HALF_OPEN:
                self._reset()

            return result

        except self.expected_exception:
            self._record_failure()
            raise

    def _can_execute(self) -> bool:
        """Check if execution is allowed."""
        with self._lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True
            elif self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self._notify_state_change(CircuitBreakerState.HALF_OPEN)
                    return True
                else:
                    return False
            elif self.state == CircuitBreakerState.HALF_OPEN:
                return True

        return True

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.last_failure_time is None:
            return True

        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    def _record_failure(self):
        """Record a failure."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            self.metrics.failed_calls += 1

            if (
                self.state == CircuitBreakerState.CLOSED
                or self.state == CircuitBreakerState.HALF_OPEN
            ):
                if self.failure_count >= self.failure_threshold:
                    self._trip_circuit()

    def _trip_circuit(self):
        """Trip the circuit breaker (open it)."""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.metrics.state_changes += 1

        if old_state != CircuitBreakerState.OPEN:
            self._notify_state_change(CircuitBreakerState.OPEN)

    def _reset(self):
        """Reset circuit breaker to closed state."""
        old_state = self.state
        with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitBreakerState.CLOSED

        if old_state != CircuitBreakerState.CLOSED:
            self.metrics.state_changes += 1
            self._notify_state_change(CircuitBreakerState.CLOSED)

    def _notify_state_change(self, new_state: CircuitBreakerState):
        """Notify state change callbacks."""
        for callback in self.state_change_callbacks:
            try:
                callback(self.name, new_state, self.metrics)
            except Exception:
                pass

    def add_state_change_callback(self, callback: Callable):
        """
        Add a callback for state changes.

        Args:
            callback: Function to call on state changes
        """
        self.state_change_callbacks.append(callback)

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "last_failure_time": self.last_failure_time,
                "recovery_timeout": self.recovery_timeout,
                "metrics": {
                    "total_calls": self.metrics.total_calls,
                    "successful_calls": self.metrics.successful_calls,
                    "failed_calls": self.metrics.failed_calls,
                    "rejected_calls": self.metrics.rejected_calls,
                    "success_rate": (
                        self.metrics.successful_calls / max(self.metrics.total_calls, 1)
                    ),
                    "state_changes": self.metrics.state_changes,
                },
            }

    def force_open(self):
        """Force circuit breaker to open state."""
        with self._lock:
            self._trip_circuit()

    def force_close(self):
        """Force circuit breaker to closed state."""
        self._reset()

    def force_half_open(self):
        """Force circuit breaker to half-open state."""
        with self._lock:
            old_state = self.state
            self.state = CircuitBreakerState.HALF_OPEN

            if old_state != CircuitBreakerState.HALF_OPEN:
                self.metrics.state_changes += 1
                self._notify_state_change(CircuitBreakerState.HALF_OPEN)


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    """

    def __init__(self):
        """Initialize circuit breaker registry."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def get_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """
        Get or create a circuit breaker.

        Args:
            name: Circuit breaker name
            **kwargs: Circuit breaker configuration

        Returns:
            Circuit breaker instance
        """
        with self._lock:
            if name not in self.circuit_breakers:
                self.circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)

            return self.circuit_breakers[name]

    def list_circuit_breakers(self) -> List[Dict[str, Any]]:
        """List all circuit breakers."""
        with self._lock:
            return [cb.get_state() for cb in self.circuit_breakers.values()]

    def get_open_circuits(self) -> List[str]:
        """Get names of open circuit breakers."""
        with self._lock:
            open_circuits = []
            for name, cb in self.circuit_breakers.items():
                if cb.state == CircuitBreakerState.OPEN:
                    open_circuits.append(name)
            return open_circuits

    def reset_all(self):
        """Reset all circuit breakers."""
        with self._lock:
            for cb in self.circuit_breakers.values():
                cb.force_close()


# Global circuit breaker registry
_global_circuit_registry = None
_circuit_lock = threading.Lock()


def get_global_circuit_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry."""
    global _global_circuit_registry

    if _global_circuit_registry is None:
        with _circuit_lock:
            if _global_circuit_registry is None:
                _global_circuit_registry = CircuitBreakerRegistry()

    return _global_circuit_registry


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """
    Get a circuit breaker from the global registry.

    Args:
        name: Circuit breaker name
        **kwargs: Circuit breaker configuration

    Returns:
        Circuit breaker instance
    """
    registry = get_global_circuit_registry()
    return registry.get_circuit_breaker(name, **kwargs)


def circuit_breaker(
    name: str = "default",
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception,
):
    """
    Decorator for circuit breaker pattern.

    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before attempting recovery
        expected_exception: Exception type that triggers circuit breaker

    Returns:
        Decorator function
    """

    def decorator(func):
        cb = get_circuit_breaker(
            name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
        )

        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)

        # Attach circuit breaker to function for inspection
        wrapper.circuit_breaker = cb

        return wrapper

    return decorator


class AdaptiveCircuitBreaker(CircuitBreaker):
    """
    Circuit breaker with adaptive failure threshold.

    Adjusts failure threshold based on recent success rate.
    """

    def __init__(self, *args, **kwargs):
        """Initialize adaptive circuit breaker."""
        super().__init__(*args, **kwargs)

        # Adaptive parameters
        self.base_threshold = kwargs.get("failure_threshold", 5)
        self.adaptation_window = 100  # calls
        self.success_rate_threshold = 0.8  # 80% success rate

        # Adaptive state
        self.recent_calls = []
        self.recent_successes = 0

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with adaptive circuit breaker."""
        # Update adaptive metrics
        self._update_adaptive_metrics()

        # Adjust threshold if needed
        self._adapt_threshold()

        # Call parent implementation
        return super().call(func, *args, **kwargs)

    def _update_adaptive_metrics(self):
        """Update adaptive metrics."""
        # This would track recent call success/failure
        # For now, use simple implementation
        pass

    def _adapt_threshold(self):
        """Adapt failure threshold based on performance."""
        # This would implement adaptive threshold logic
        # For now, keep base threshold
        pass


def create_circuit_breaker(
    name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0, **kwargs
) -> CircuitBreaker:
    """
    Create a circuit breaker with specified configuration.

    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening
        recovery_timeout: Time to wait before recovery
        **kwargs: Additional configuration

    Returns:
        Configured circuit breaker
    """
    return CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        name=name,
        **kwargs,
    )


class Bulkhead:
    """
    Bulkhead pattern for isolating failures.

    Limits concurrent access to a resource to prevent
    cascading failures.
    """

    def __init__(self, max_concurrent: int = 10):
        """
        Initialize bulkhead.

        Args:
            max_concurrent: Maximum concurrent operations
        """
        self.max_concurrent = max_concurrent
        self.semaphore = threading.Semaphore(max_concurrent)
        self.active_operations = 0
        self._lock = threading.Lock()

    def execute(self, func: Callable, *args, **kwargs):
        """
        Execute function with bulkhead protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If bulkhead is full or function fails
        """
        if not self.semaphore.acquire(blocking=False):
            raise Exception("Bulkhead capacity exceeded")

        try:
            with self._lock:
                self.active_operations += 1

            result = func(*args, **kwargs)
            return result

        finally:
            self.semaphore.release()
            with self._lock:
                self.active_operations -= 1

    def get_status(self) -> Dict[str, Any]:
        """Get bulkhead status."""
        with self._lock:
            return {
                "max_concurrent": self.max_concurrent,
                "active_operations": self.active_operations,
                "available_slots": self.semaphore._value
                if hasattr(self.semaphore, "_value")
                else "unknown",
            }


def bulkhead(max_concurrent: int = 10):
    """
    Decorator for bulkhead pattern.

    Args:
        max_concurrent: Maximum concurrent operations

    Returns:
        Decorator function
    """

    def decorator(func):
        bh = Bulkhead(max_concurrent)

        def wrapper(*args, **kwargs):
            return bh.execute(func, *args, **kwargs)

        wrapper.bulkhead = bh
        return wrapper

    return decorator
