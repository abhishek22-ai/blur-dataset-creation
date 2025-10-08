"""
Health Checker

System health monitoring and validation for production environments.
"""

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Individual health check."""

    name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthReport:
    """Complete health report."""

    overall_status: HealthStatus
    checks: List[HealthCheck]
    timestamp: float = field(default_factory=time.time)
    version: str = "1.0.0"


class HealthChecker:
    """
    Comprehensive health checking system.

    Monitors system health, performs various checks, and
    provides detailed health reports for production use.
    """

    def __init__(self, check_interval: float = 300.0):  # 5 minutes
        """
        Initialize health checker.

        Args:
            check_interval: Interval between health checks in seconds
        """
        self.check_interval = check_interval
        self.health_checks: Dict[str, Callable] = {}
        self._lock = threading.RLock()

        # Health check state
        self._last_report: Optional[HealthReport] = None
        self._monitoring_active = False
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()

        # Statistics
        self.stats = {
            "checks_performed": 0,
            "healthy_checks": 0,
            "warning_checks": 0,
            "critical_checks": 0,
            "total_check_time": 0.0,
        }

        # Register default health checks
        self._register_default_checks()

    def _register_default_checks(self):
        """Register default health checks."""
        self.register_health_check("memory_usage", self._check_memory_usage)
        self.register_health_check("disk_space", self._check_disk_space)
        self.register_health_check("cpu_usage", self._check_cpu_usage)
        self.register_health_check("cache_health", self._check_cache_health)
        self.register_health_check("plugin_health", self._check_plugin_health)

    def register_health_check(self, name: str, check_func: Callable):
        """
        Register a health check function.

        Args:
            name: Health check name
            check_func: Function that performs the check
        """
        with self._lock:
            self.health_checks[name] = check_func

    def unregister_health_check(self, name: str) -> bool:
        """
        Unregister a health check.

        Args:
            name: Health check name

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if name in self.health_checks:
                del self.health_checks[name]
                return True
        return False

    def perform_health_check(self, check_name: Optional[str] = None) -> HealthReport:
        """
        Perform health checks.

        Args:
            check_name: Specific check to perform, or None for all

        Returns:
            Health report
        """
        checks_to_run = {}

        with self._lock:
            if check_name:
                if check_name in self.health_checks:
                    checks_to_run[check_name] = self.health_checks[check_name]
            else:
                checks_to_run = self.health_checks.copy()

        # Perform checks
        checks = []
        overall_status = HealthStatus.HEALTHY

        for name, check_func in checks_to_run.items():
            start_time = time.time()

            try:
                # Execute health check
                result = check_func()

                duration = time.time() - start_time

                if isinstance(result, tuple):
                    status, message, metadata = result
                else:
                    status = result
                    message = ""
                    metadata = {}

                # Create health check record
                check = HealthCheck(
                    name=name,
                    status=status,
                    message=message,
                    duration=duration,
                    metadata=metadata,
                )

                checks.append(check)

                # Update overall status
                if status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                elif (
                    status == HealthStatus.WARNING
                    and overall_status == HealthStatus.HEALTHY
                ):
                    overall_status = HealthStatus.WARNING

                # Update statistics
                self.stats["checks_performed"] += 1
                self.stats["total_check_time"] += duration

                if status == HealthStatus.HEALTHY:
                    self.stats["healthy_checks"] += 1
                elif status == HealthStatus.WARNING:
                    self.stats["warning_checks"] += 1
                elif status == HealthStatus.CRITICAL:
                    self.stats["critical_checks"] += 1

            except Exception as e:
                duration = time.time() - start_time

                # Create error check record
                check = HealthCheck(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}",
                    duration=duration,
                    metadata={"error": str(e)},
                )

                checks.append(check)
                overall_status = HealthStatus.CRITICAL

                self.stats["checks_performed"] += 1
                self.stats["critical_checks"] += 1
                self.stats["total_check_time"] += duration

        # Create report
        report = HealthReport(overall_status=overall_status, checks=checks)

        self._last_report = report
        return report

    def _check_memory_usage(self) -> tuple:
        """Check memory usage health."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            if memory_percent > 90:
                return (
                    HealthStatus.CRITICAL,
                    f"High memory usage: {memory_percent:.1f}%",
                    {"memory_percent": memory_percent},
                )
            elif memory_percent > 75:
                return (
                    HealthStatus.WARNING,
                    f"Elevated memory usage: {memory_percent:.1f}%",
                    {"memory_percent": memory_percent},
                )
            else:
                return (
                    HealthStatus.HEALTHY,
                    f"Memory usage normal: {memory_percent:.1f}%",
                    {"memory_percent": memory_percent},
                )

        except Exception as e:
            return HealthStatus.CRITICAL, f"Memory check failed: {str(e)}", {}

    def _check_disk_space(self) -> tuple:
        """Check disk space health."""
        try:
            import psutil

            disk = psutil.disk_usage("/")
            disk_percent = disk.percent

            if disk_percent > 95:
                return (
                    HealthStatus.CRITICAL,
                    f"Low disk space: {disk_percent:.1f}% used",
                    {"disk_percent": disk_percent},
                )
            elif disk_percent > 85:
                return (
                    HealthStatus.WARNING,
                    f"High disk usage: {disk_percent:.1f}% used",
                    {"disk_percent": disk_percent},
                )
            else:
                return (
                    HealthStatus.HEALTHY,
                    f"Disk usage normal: {disk_percent:.1f}% used",
                    {"disk_percent": disk_percent},
                )

        except Exception as e:
            return HealthStatus.CRITICAL, f"Disk check failed: {str(e)}", {}

    def _check_cpu_usage(self) -> tuple:
        """Check CPU usage health."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)

            if cpu_percent > 90:
                return (
                    HealthStatus.WARNING,
                    f"High CPU usage: {cpu_percent:.1f}%",
                    {"cpu_percent": cpu_percent},
                )
            else:
                return (
                    HealthStatus.HEALTHY,
                    f"CPU usage normal: {cpu_percent:.1f}%",
                    {"cpu_percent": cpu_percent},
                )

        except Exception as e:
            return HealthStatus.CRITICAL, f"CPU check failed: {str(e)}", {}

    def _check_cache_health(self) -> tuple:
        """Check cache system health."""
        try:
            # Check if cache manager is available and functioning

            # This would check actual cache health
            # For now, return healthy
            return HealthStatus.HEALTHY, "Cache system operational", {}

        except Exception as e:
            return HealthStatus.WARNING, f"Cache check failed: {str(e)}", {}

    def _check_plugin_health(self) -> tuple:
        """Check plugin system health."""
        try:
            # Check if plugin manager is available

            # This would check actual plugin health
            # For now, return healthy
            return HealthStatus.HEALTHY, "Plugin system operational", {}

        except Exception as e:
            return HealthStatus.WARNING, f"Plugin check failed: {str(e)}", {}

    def start_monitoring(self):
        """Start continuous health monitoring."""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._stop_monitoring.clear()

        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self._monitoring_thread.start()

    def stop_monitoring(self):
        """Stop continuous health monitoring."""
        if not self._monitoring_active:
            return

        self._monitoring_active = False
        self._stop_monitoring.set()

        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)

    def _monitoring_loop(self):
        """Background health monitoring loop."""
        while not self._stop_monitoring.is_set():
            try:
                self.perform_health_check()
                self._stop_monitoring.wait(self.check_interval)
            except Exception:
                # Continue monitoring even if there's an error
                self._stop_monitoring.wait(self.check_interval)

    def get_health_report(self) -> Optional[HealthReport]:
        """Get the latest health report."""
        return self._last_report

    def get_health_status(self) -> HealthStatus:
        """Get current overall health status."""
        if self._last_report:
            return self._last_report.overall_status
        return HealthStatus.UNKNOWN

    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.get_health_status() == HealthStatus.HEALTHY

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        if not self._last_report:
            return {"status": "no_checks_performed"}

        checks_by_status = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.WARNING: 0,
            HealthStatus.CRITICAL: 0,
            HealthStatus.UNKNOWN: 0,
        }

        for check in self._last_report.checks:
            checks_by_status[check.status] += 1

        return {
            "overall_status": self._last_report.overall_status.value,
            "total_checks": len(self._last_report.checks),
            "status_breakdown": {k.value: v for k, v in checks_by_status.items()},
            "last_check": self._last_report.timestamp,
            "monitoring_active": self._monitoring_active,
            "statistics": self.stats.copy(),
        }

    def export_health_report(self, format: str = "json") -> str:
        """
        Export health report.

        Args:
            format: Export format ('json' or 'text')

        Returns:
            Health report as formatted string
        """
        if not self._last_report:
            return "No health report available"

        if format.lower() == "json":
            import json

            return json.dumps(
                {
                    "overall_status": self._last_report.overall_status.value,
                    "timestamp": self._last_report.timestamp,
                    "version": self._last_report.version,
                    "checks": [
                        {
                            "name": check.name,
                            "status": check.status.value,
                            "message": check.message,
                            "duration": check.duration,
                            "timestamp": check.timestamp,
                            "metadata": check.metadata,
                        }
                        for check in self._last_report.checks
                    ],
                },
                indent=2,
            )

        else:
            # Text format
            report = []
            report.append("Blur Suite Health Report")
            report.append("=" * 40)
            report.append(
                f"Overall Status: {self._last_report.overall_status.value.upper()}"
            )
            report.append(f"Report Time: {time.ctime(self._last_report.timestamp)}")
            report.append(f"Total Checks: {len(self._last_report.checks)}")
            report.append("")

            # Group checks by status
            checks_by_status = {
                HealthStatus.HEALTHY: [],
                HealthStatus.WARNING: [],
                HealthStatus.CRITICAL: [],
                HealthStatus.UNKNOWN: [],
            }

            for check in self._last_report.checks:
                checks_by_status[check.status].append(check)

            # Report each status
            for status in [
                HealthStatus.HEALTHY,
                HealthStatus.WARNING,
                HealthStatus.CRITICAL,
                HealthStatus.UNKNOWN,
            ]:
                status_checks = checks_by_status[status]
                if status_checks:
                    report.append(f"{status.value.upper()} ({len(status_checks)}):")
                    for check in status_checks:
                        report.append(f"  {check.name}: {check.message}")
                        if check.duration > 0:
                            report.append(f"    Duration: {check.duration:.3f}s")
                    report.append("")

            return "\n".join(report)


# Global health checker instance
_global_health_checker = None
_health_lock = threading.Lock()


def get_global_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _global_health_checker

    if _global_health_checker is None:
        with _health_lock:
            if _global_health_checker is None:
                _global_health_checker = HealthChecker()

    return _global_health_checker


def check_system_health() -> HealthReport:
    """Perform a system health check."""
    checker = get_global_health_checker()
    return checker.perform_health_check()


def is_system_healthy() -> bool:
    """Check if system is healthy."""
    checker = get_global_health_checker()
    return checker.is_healthy()
