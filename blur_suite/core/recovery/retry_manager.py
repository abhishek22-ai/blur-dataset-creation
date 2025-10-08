"""
Retry Manager

Advanced retry logic with exponential backoff and jitter for robust error recovery.
"""

import random
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type


class RetryStrategy(Enum):
    """Retry strategies."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"


@dataclass
class RetryConfig:
    """Retry configuration."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True
    retryable_exceptions: List[Type[Exception]] = field(default_factory=list)
    non_retryable_exceptions: List[Type[Exception]] = field(default_factory=list)


@dataclass
class RetryAttempt:
    """Information about a retry attempt."""

    attempt_number: int
    timestamp: float
    delay: float
    exception: Exception
    will_retry: bool


class RetryManager:
    """
    Advanced retry management system.

    Provides configurable retry logic with multiple strategies,
    jitter, and comprehensive retry tracking.
    """

    def __init__(self, default_config: Optional[RetryConfig] = None):
        """
        Initialize retry manager.

        Args:
            default_config: Default retry configuration
        """
        self.default_config = default_config or RetryConfig()
        self.retry_history: List[RetryAttempt] = []
        self._lock = threading.RLock()

        # Statistics
        self.stats = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "total_retry_time": 0.0,
        }

    def execute_with_retry(
        self,
        operation_func: Callable,
        config: Optional[RetryConfig] = None,
        operation_name: str = "unknown",
    ) -> Any:
        """
        Execute operation with retry logic.

        Args:
            operation_func: Function to execute
            config: Retry configuration (uses default if None)
            operation_name: Name of the operation for tracking

        Returns:
            Operation result

        Raises:
            Exception: If operation fails after all retries
        """
        retry_config = config or self.default_config

        for attempt in range(retry_config.max_retries + 1):
            try:
                # Execute operation
                result = operation_func()

                # Record successful retry if this wasn't the first attempt
                if attempt > 0:
                    with self._lock:
                        self.stats["successful_retries"] += 1
                        self.stats["total_retries"] += attempt

                    self._record_retry_attempt(
                        attempt, 0.0, None, False, operation_name
                    )

                return result

            except Exception as e:
                # Check if exception is retryable
                if not self._is_retryable_exception(e, retry_config):
                    raise

                # Check if we should retry
                if attempt >= retry_config.max_retries:
                    # Final attempt failed
                    with self._lock:
                        self.stats["failed_retries"] += 1
                        self.stats["total_retries"] += attempt

                    self._record_retry_attempt(attempt, 0.0, e, False, operation_name)

                    raise

                # Calculate delay for next attempt
                delay = self._calculate_delay(attempt, retry_config)

                # Record retry attempt
                self._record_retry_attempt(attempt, delay, e, True, operation_name)

                # Wait before retry
                if delay > 0:
                    time.sleep(delay)

        # This should never be reached
        raise RuntimeError("Retry logic error")

    def _is_retryable_exception(
        self, exception: Exception, config: RetryConfig
    ) -> bool:
        """Check if exception is retryable."""
        # Check non-retryable exceptions first
        for non_retryable in config.non_retryable_exceptions:
            if isinstance(exception, non_retryable):
                return False

        # Check retryable exceptions
        if config.retryable_exceptions:
            for retryable in config.retryable_exceptions:
                if isinstance(exception, retryable):
                    return True
            return False

        # Default retryable exceptions
        default_retryable = [
            ConnectionError,
            TimeoutError,
            OSError,
            # Add more default retryable exceptions as needed
        ]

        return any(isinstance(exception, exc_type) for exc_type in default_retryable)

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt."""
        if config.strategy == RetryStrategy.IMMEDIATE:
            return 0.0

        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay

        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)

        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (2**attempt)

        else:
            delay = config.base_delay

        # Apply maximum delay limit
        delay = min(delay, config.max_delay)

        # Add jitter if enabled
        if config.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay += jitter

        return max(0.0, delay)

    def _record_retry_attempt(
        self,
        attempt: int,
        delay: float,
        exception: Optional[Exception],
        will_retry: bool,
        operation_name: str,
    ):
        """Record retry attempt information."""
        retry_attempt = RetryAttempt(
            attempt_number=attempt,
            timestamp=time.time(),
            delay=delay,
            exception=exception,
            will_retry=will_retry,
        )

        with self._lock:
            self.retry_history.append(retry_attempt)

            # Keep only recent history
            if len(self.retry_history) > 1000:
                self.retry_history.pop(0)

    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry statistics."""
        with self._lock:
            if not self.retry_history:
                return {"message": "No retry attempts recorded"}

            # Calculate statistics
            total_attempts = len(self.retry_history)
            retry_attempts = sum(1 for r in self.retry_history if r.will_retry)
            final_failures = sum(1 for r in self.retry_history if not r.will_retry)

            # Calculate average delay
            delays = [r.delay for r in self.retry_history if r.delay > 0]
            avg_delay = sum(delays) / len(delays) if delays else 0.0

            return {
                "total_attempts": total_attempts,
                "retry_attempts": retry_attempts,
                "final_failures": final_failures,
                "success_rate": (total_attempts - final_failures) / total_attempts
                if total_attempts > 0
                else 0.0,
                "average_delay": avg_delay,
                "total_retry_time": self.stats["total_retry_time"],
                "global_stats": self.stats.copy(),
            }

    def clear_retry_history(self):
        """Clear retry history."""
        with self._lock:
            self.retry_history.clear()

    def create_retry_config(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        **kwargs,
    ) -> RetryConfig:
        """
        Create a retry configuration.

        Args:
            max_retries: Maximum number of retries
            base_delay: Base delay between retries
            strategy: Retry strategy
            **kwargs: Additional configuration

        Returns:
            Retry configuration
        """
        return RetryConfig(
            max_retries=max_retries, base_delay=base_delay, strategy=strategy, **kwargs
        )


class RetryableOperation:
    """
    Wrapper for operations that should be retryable.
    """

    def __init__(
        self,
        operation_func: Callable,
        config: Optional[RetryConfig] = None,
        operation_name: Optional[str] = None,
    ):
        """
        Initialize retryable operation.

        Args:
            operation_func: Function to make retryable
            config: Retry configuration
            operation_name: Name of the operation
        """
        self.operation_func = operation_func
        self.config = config
        self.operation_name = operation_name or getattr(
            operation_func, "__name__", "unknown"
        )
        self.retry_manager = RetryManager()

    def __call__(self, *args, **kwargs):
        """Execute operation with retry logic."""
        return self.retry_manager.execute_with_retry(
            lambda: self.operation_func(*args, **kwargs),
            self.config,
            self.operation_name,
        )

    def execute(self, *args, **kwargs):
        """Execute operation with retry logic."""
        return self(*args, **kwargs)


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    operation_name: Optional[str] = None,
):
    """
    Decorator for making functions retryable.

    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay between retries
        strategy: Retry strategy
        operation_name: Name of the operation

    Returns:
        Decorator function
    """

    def decorator(func):
        config = RetryConfig(
            max_retries=max_retries, base_delay=base_delay, strategy=strategy
        )

        retryable_op = RetryableOperation(func, config, operation_name or func.__name__)

        return retryable_op

    return decorator


def with_retry(
    operation_func: Callable, max_retries: int = 3, **kwargs
) -> RetryableOperation:
    """
    Create a retryable version of a function.

    Args:
        operation_func: Function to make retryable
        max_retries: Maximum number of retries
        **kwargs: Additional retry configuration

    Returns:
        Retryable operation wrapper
    """
    config = RetryConfig(max_retries=max_retries, **kwargs)

    return RetryableOperation(
        operation_func, config, getattr(operation_func, "__name__", "unknown")
    )


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, requests rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


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
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = threading.Lock()

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
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)

            # Success - reset failure count if in half-open state
            with self._lock:
                if self.state == CircuitBreakerState.HALF_OPEN:
                    self._reset()
                elif self.state == CircuitBreakerState.CLOSED:
                    self.failure_count = 0

            return result

        except self.expected_exception:
            self._record_failure()
            raise

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

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN

    def _reset(self):
        """Reset circuit breaker."""
        with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitBreakerState.CLOSED

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state."""
        with self._lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "last_failure_time": self.last_failure_time,
                "recovery_timeout": self.recovery_timeout,
            }


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception,
):
    """
    Decorator for circuit breaker pattern.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before attempting recovery
        expected_exception: Exception type that triggers circuit breaker

    Returns:
        Decorator function
    """

    def decorator(func):
        breaker = CircuitBreaker(
            failure_threshold, recovery_timeout, expected_exception
        )

        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        # Attach circuit breaker to function for inspection
        wrapper.circuit_breaker = breaker

        return wrapper

    return decorator


# Global retry manager instance
_global_retry_manager = None
_retry_lock = threading.Lock()


def get_global_retry_manager() -> RetryManager:
    """Get the global retry manager instance."""
    global _global_retry_manager

    if _global_retry_manager is None:
        with _retry_lock:
            if _global_retry_manager is None:
                _global_retry_manager = RetryManager()

    return _global_retry_manager


def retry_operation(
    max_retries: int = 3, operation_name: str = "unknown", **kwargs
) -> Callable:
    """
    Decorator for retrying operations with global retry manager.

    Args:
        max_retries: Maximum number of retries
        operation_name: Name of the operation
        **kwargs: Additional retry configuration

    Returns:
        Decorator function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_global_retry_manager()
            config = RetryConfig(max_retries=max_retries, **kwargs)

            return manager.execute_with_retry(
                lambda: func(*args, **kwargs), config, operation_name
            )

        return wrapper

    return decorator
