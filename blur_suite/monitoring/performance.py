"""
Performance Monitor

Comprehensive performance monitoring and profiling for the Blur Suite SDK.
"""

import functools
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import psutil


@dataclass
class PerformanceMetric:
    """Individual performance metric."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    unit: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationProfile:
    """Profile data for a specific operation."""

    operation_name: str
    total_calls: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    error_count: int = 0
    last_called: float = 0.0
    call_history: deque = field(default_factory=lambda: deque(maxlen=1000))


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.

    Tracks system performance, operation timing, resource usage,
    and provides detailed profiling capabilities.
    """

    def __init__(
        self,
        enable_system_monitoring: bool = True,
        enable_operation_profiling: bool = True,
        collection_interval: float = 1.0,
        max_history_size: int = 10000,
    ):
        """
        Initialize performance monitor.

        Args:
            enable_system_monitoring: Whether to monitor system resources
            enable_operation_profiling: Whether to profile operations
            collection_interval: Interval for collecting system metrics
            max_history_size: Maximum number of metrics to keep in history
        """
        self.enable_system_monitoring = enable_system_monitoring
        self.enable_operation_profiling = enable_operation_profiling
        self.collection_interval = collection_interval
        self.max_history_size = max_history_size

        # Performance data storage
        self._metrics_history: deque = deque(maxlen=max_history_size)
        self._operation_profiles: Dict[str, OperationProfile] = {}
        self._system_metrics: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()

        # Monitoring state
        self._monitoring_active = False
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()

        # Statistics
        self.stats = {
            "metrics_collected": 0,
            "operations_profiled": 0,
            "monitoring_duration": 0.0,
            "start_time": time.time(),
        }

        # Start monitoring if enabled
        if self.enable_system_monitoring:
            self.start_monitoring()

    def start_monitoring(self):
        """Start performance monitoring."""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._stop_monitoring.clear()
        self.stats["start_time"] = time.time()

        # Start system monitoring thread
        if self.enable_system_monitoring:
            self._monitoring_thread = threading.Thread(
                target=self._system_monitoring_loop, daemon=True
            )
            self._monitoring_thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring."""
        if not self._monitoring_active:
            return

        self._monitoring_active = False
        self._stop_monitoring.set()

        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)

        # Update final statistics
        self.stats["monitoring_duration"] = time.time() - self.stats["start_time"]

    def record_metric(self, name: str, value: float, unit: str = "", **metadata):
        """
        Record a performance metric.

        Args:
            name: Metric name
            value: Metric value
            unit: Metric unit
            **metadata: Additional metadata
        """
        metric = PerformanceMetric(name=name, value=value, unit=unit, metadata=metadata)

        with self._lock:
            self._metrics_history.append(metric)
            self.stats["metrics_collected"] += 1

    def profile_operation(self, operation_name: str):
        """
        Decorator/context manager for profiling operations.

        Args:
            operation_name: Name of the operation to profile

        Returns:
            Decorator function or context manager
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return self._profile_function_call(
                    operation_name, func, *args, **kwargs
                )

            return wrapper

        return decorator

    def _profile_function_call(
        self, operation_name: str, func: Callable, *args, **kwargs
    ):
        """Profile a function call."""
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            success = True
        except Exception:
            success = False
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time

            # Record operation profile
            self._record_operation_profile(operation_name, duration, success)

        return result

    def _record_operation_profile(
        self, operation_name: str, duration: float, success: bool
    ):
        """Record operation profile data."""
        if not self.enable_operation_profiling:
            return

        with self._lock:
            if operation_name not in self._operation_profiles:
                self._operation_profiles[operation_name] = OperationProfile(
                    operation_name=operation_name
                )

            profile = self._operation_profiles[operation_name]

            # Update profile statistics
            profile.total_calls += 1
            profile.total_time += duration
            profile.avg_time = profile.total_time / profile.total_calls
            profile.min_time = min(profile.min_time, duration)
            profile.max_time = max(profile.max_time, duration)
            profile.last_called = time.time()

            if not success:
                profile.error_count += 1

            # Add to call history
            profile.call_history.append(duration)

            self.stats["operations_profiled"] += 1

    def _system_monitoring_loop(self):
        """Background system monitoring loop."""
        while not self._stop_monitoring.is_set():
            try:
                self._collect_system_metrics()
                self._stop_monitoring.wait(self.collection_interval)
            except Exception:
                # Continue monitoring even if there's an error
                self._stop_monitoring.wait(self.collection_interval)

    def _collect_system_metrics(self):
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            self._system_metrics["cpu_percent"].append(cpu_percent)

            # Memory metrics
            memory = psutil.virtual_memory()
            self._system_metrics["memory_percent"].append(memory.percent)
            self._system_metrics["memory_used_mb"].append(memory.used / (1024 * 1024))
            self._system_metrics["memory_available_mb"].append(
                memory.available / (1024 * 1024)
            )

            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            self._system_metrics["process_memory_mb"].append(
                process_memory.rss / (1024 * 1024)
            )
            self._system_metrics["process_cpu_percent"].append(process.cpu_percent())

            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self._system_metrics["disk_read_mb"].append(
                    disk_io.read_bytes / (1024 * 1024)
                )
                self._system_metrics["disk_write_mb"].append(
                    disk_io.write_bytes / (1024 * 1024)
                )

            # Keep only recent metrics
            max_metrics = 1000
            for key in self._system_metrics:
                if len(self._system_metrics[key]) > max_metrics:
                    self._system_metrics[key] = self._system_metrics[key][-max_metrics:]

        except Exception as e:
            # Log error but continue monitoring
            print(f"Error collecting system metrics: {e}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        current_time = time.time()

        # Get latest system metrics
        system_metrics = {}
        for metric_name, values in self._system_metrics.items():
            if values:
                system_metrics[f"current_{metric_name}"] = values[-1]
                system_metrics[f"avg_{metric_name}"] = (
                    statistics.mean(values[-10:]) if len(values) >= 10 else values[-1]
                )

        # Get operation profiles
        operation_profiles = {}
        with self._lock:
            for op_name, profile in self._operation_profiles.items():
                operation_profiles[op_name] = {
                    "total_calls": profile.total_calls,
                    "total_time": profile.total_time,
                    "avg_time": profile.avg_time,
                    "min_time": profile.min_time,
                    "max_time": profile.max_time,
                    "error_count": profile.error_count,
                    "last_called": profile.last_called,
                    "recent_avg_time": (
                        statistics.mean(list(profile.call_history)[-10:])
                        if profile.call_history
                        else 0.0
                    ),
                }

        return {
            "timestamp": current_time,
            "monitoring_active": self._monitoring_active,
            "system_metrics": system_metrics,
            "operation_profiles": operation_profiles,
            "statistics": self.stats.copy(),
        }

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics."""
        with self._lock:
            # Calculate summary statistics
            total_operations = sum(
                profile.total_calls for profile in self._operation_profiles.values()
            )

            total_operation_time = sum(
                profile.total_time for profile in self._operation_profiles.values()
            )

            error_rate = 0.0
            if total_operations > 0:
                total_errors = sum(
                    profile.error_count for profile in self._operation_profiles.values()
                )
                error_rate = total_errors / total_operations

            # System metrics summary
            system_summary = {}
            for metric_name, values in self._system_metrics.items():
                if values:
                    system_summary[metric_name] = {
                        "current": values[-1],
                        "average": statistics.mean(values),
                        "min": min(values),
                        "max": max(values),
                        "samples": len(values),
                    }

            return {
                "monitoring_duration": self.stats["monitoring_duration"],
                "metrics_collected": self.stats["metrics_collected"],
                "operations_profiled": self.stats["operations_profiled"],
                "total_operations": total_operations,
                "total_operation_time": total_operation_time,
                "error_rate": error_rate,
                "system_metrics": system_summary,
                "operation_count": len(self._operation_profiles),
            }

    def get_operation_profile(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed profile for a specific operation.

        Args:
            operation_name: Name of the operation

        Returns:
            Operation profile data or None if not found
        """
        with self._lock:
            if operation_name not in self._operation_profiles:
                return None

            profile = self._operation_profiles[operation_name]

            # Calculate additional statistics
            call_times = list(profile.call_history)
            if call_times:
                recent_avg = (
                    statistics.mean(call_times[-10:])
                    if len(call_times) >= 10
                    else statistics.mean(call_times)
                )
                p95_time = (
                    statistics.quantiles(call_times, n=20)[18]
                    if len(call_times) >= 20
                    else max(call_times)
                )
                p99_time = (
                    statistics.quantiles(call_times, n=100)[98]
                    if len(call_times) >= 100
                    else max(call_times)
                )
            else:
                recent_avg = p95_time = p99_time = 0.0

            return {
                "operation_name": profile.operation_name,
                "total_calls": profile.total_calls,
                "total_time": profile.total_time,
                "avg_time": profile.avg_time,
                "min_time": profile.min_time,
                "max_time": profile.max_time,
                "error_count": profile.error_count,
                "error_rate": profile.error_count / max(profile.total_calls, 1),
                "last_called": profile.last_called,
                "recent_avg_time": recent_avg,
                "p95_time": p95_time,
                "p99_time": p99_time,
                "call_history_size": len(profile.call_history),
            }

    def export_metrics(self, format: str = "json") -> str:
        """
        Export performance metrics.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            Metrics as formatted string
        """
        data = self.get_current_metrics()

        if format.lower() == "json":
            import json

            return json.dumps(data, indent=2, default=str)
        elif format.lower() == "csv":
            # Convert to CSV format
            lines = ["Metric,Value,Timestamp"]

            for metric in self._metrics_history:
                lines.append(f"{metric.name},{metric.value},{metric.timestamp}")

            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def clear_history(self):
        """Clear performance history and reset statistics."""
        with self._lock:
            self._metrics_history.clear()
            self._operation_profiles.clear()
            self._system_metrics.clear()

            # Reset statistics
            self.stats = {
                "metrics_collected": 0,
                "operations_profiled": 0,
                "monitoring_duration": 0.0,
                "start_time": time.time(),
            }

    def get_performance_report(self) -> str:
        """Generate a human-readable performance report."""
        summary = self.get_metrics_summary()

        report = []
        report.append("Blur Suite Performance Report")
        report.append("=" * 50)
        report.append(f"Monitoring Duration: {summary['monitoring_duration']:.2f}s")
        report.append(f"Metrics Collected: {summary['metrics_collected']}")
        report.append(f"Operations Profiled: {summary['operations_profiled']}")
        report.append(f"Total Operations: {summary['total_operations']}")
        report.append(f"Total Operation Time: {summary['total_operation_time']:.2f}s")
        report.append(f"Error Rate: {summary['error_rate']:.2%}")
        report.append("")

        # System metrics
        if summary["system_metrics"]:
            report.append("System Metrics:")
            for metric_name, stats in summary["system_metrics"].items():
                report.append(f"  {metric_name}:")
                report.append(f"    Current: {stats['current']}")
                report.append(f"    Average: {stats['average']:.2f}")
                report.append(f"    Range: {stats['min']:.2f} - {stats['max']:.2f}")
            report.append("")

        # Top operations by time
        operation_times = []
        for op_name, profile in self._operation_profiles.items():
            operation_times.append((op_name, profile.total_time, profile.total_calls))

        operation_times.sort(key=lambda x: x[1], reverse=True)

        if operation_times:
            report.append("Top Operations by Time:")
            for op_name, total_time, call_count in operation_times[:10]:
                avg_time = total_time / call_count if call_count > 0 else 0
                report.append(
                    f"  {op_name}: {total_time:.2f}s total, {avg_time:.4f}s avg ({call_count} calls)"
                )
            report.append("")

        return "\n".join(report)


class PerformanceContext:
    """
    Context manager for performance monitoring.
    """

    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        """
        Initialize performance context.

        Args:
            monitor: Performance monitor instance
            operation_name: Name of operation to monitor
        """
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        """Enter performance monitoring context."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit performance monitoring context."""
        if self.start_time:
            duration = time.time() - self.start_time
            success = exc_type is None

            self.monitor._record_operation_profile(
                self.operation_name, duration, success
            )


def profile_operation(operation_name: str):
    """
    Decorator for profiling operations.

    Args:
        operation_name: Name of the operation

    Returns:
        Decorator function
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get global performance monitor
            monitor = getattr(func, "_performance_monitor", None)
            if monitor is None:
                # Create default monitor if none exists
                monitor = PerformanceMonitor()
                func._performance_monitor = monitor

            return monitor._profile_function_call(operation_name, func, *args, **kwargs)

        return wrapper

    return decorator


def monitor_performance(operation_name: str = None):
    """
    Context manager for performance monitoring.

    Args:
        operation_name: Name of operation to monitor

    Returns:
        PerformanceContext instance
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            monitor = PerformanceMonitor()
            with PerformanceContext(monitor, name):
                return func(*args, **kwargs)

        return wrapper

    return decorator
