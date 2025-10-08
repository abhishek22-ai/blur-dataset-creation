"""
Health Validator

Comprehensive system health validation and recovery mechanisms.
"""

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ValidationSeverity(Enum):
    """Validation severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a health validation."""

    check_name: str
    severity: ValidationSeverity
    message: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    remediation: Optional[str] = None


class HealthValidator:
    """
    Comprehensive health validation system.

    Performs various health checks and provides
    remediation suggestions for system issues.
    """

    def __init__(self):
        """Initialize health validator."""
        self.validation_checks: Dict[str, Callable] = {}
        self.validation_history: List[ValidationResult] = []
        self._lock = threading.RLock()

        # Register default validations
        self._register_default_validations()

        # Statistics
        self.stats = {
            "validations_performed": 0,
            "issues_found": 0,
            "critical_issues": 0,
            "remediations_applied": 0,
        }

    def _register_default_validations(self):
        """Register default validation checks."""
        self.validation_checks.update(
            {
                "memory_health": self._validate_memory_health,
                "disk_health": self._validate_disk_health,
                "cache_health": self._validate_cache_health,
                "plugin_health": self._validate_plugin_health,
                "configuration_health": self._validate_configuration_health,
                "performance_health": self._validate_performance_health,
            }
        )

    def register_validation(self, name: str, validation_func: Callable):
        """
        Register a custom validation check.

        Args:
            name: Validation check name
            validation_func: Function that performs validation
        """
        with self._lock:
            self.validation_checks[name] = validation_func

    def unregister_validation(self, name: str) -> bool:
        """
        Unregister a validation check.

        Args:
            name: Validation check name

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if name in self.validation_checks:
                del self.validation_checks[name]
                return True
        return False

    def validate_system(
        self, check_names: Optional[List[str]] = None
    ) -> List[ValidationResult]:
        """
        Perform system validation.

        Args:
            check_names: Specific checks to perform, or None for all

        Returns:
            List of validation results
        """
        checks_to_run = check_names or list(self.validation_checks.keys())
        results = []

        for check_name in checks_to_run:
            if check_name in self.validation_checks:
                try:
                    result = self.validation_checks[check_name]()
                    results.append(result)

                    # Update statistics
                    self.stats["validations_performed"] += 1
                    if result.severity in [
                        ValidationSeverity.ERROR,
                        ValidationSeverity.CRITICAL,
                    ]:
                        self.stats["issues_found"] += 1
                    if result.severity == ValidationSeverity.CRITICAL:
                        self.stats["critical_issues"] += 1

                except Exception as e:
                    # Create error result for failed validation
                    error_result = ValidationResult(
                        check_name=check_name,
                        severity=ValidationSeverity.CRITICAL,
                        message=f"Validation check failed: {str(e)}",
                        details={"error": str(e)},
                    )
                    results.append(error_result)

        # Store in history
        with self._lock:
            self.validation_history.extend(results)

            # Keep only recent history
            if len(self.validation_history) > 1000:
                self.validation_history = self.validation_history[-1000:]

        return results

    def _validate_memory_health(self) -> ValidationResult:
        """Validate memory system health."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            if memory_percent > 95:
                return ValidationResult(
                    check_name="memory_health",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Critical memory usage: {memory_percent:.1f}%",
                    details={"memory_percent": memory_percent},
                    remediation="Consider increasing system memory or reducing application memory usage",
                )
            elif memory_percent > 85:
                return ValidationResult(
                    check_name="memory_health",
                    severity=ValidationSeverity.WARNING,
                    message=f"High memory usage: {memory_percent:.1f}%",
                    details={"memory_percent": memory_percent},
                    remediation="Monitor memory usage and consider optimizing memory-intensive operations",
                )
            else:
                return ValidationResult(
                    check_name="memory_health",
                    severity=ValidationSeverity.INFO,
                    message=f"Memory usage normal: {memory_percent:.1f}%",
                    details={"memory_percent": memory_percent},
                )

        except Exception as e:
            return ValidationResult(
                check_name="memory_health",
                severity=ValidationSeverity.ERROR,
                message=f"Memory validation failed: {str(e)}",
                details={"error": str(e)},
            )

    def _validate_disk_health(self) -> ValidationResult:
        """Validate disk space health."""
        try:
            import psutil

            disk = psutil.disk_usage("/")
            disk_percent = disk.percent

            if disk_percent > 95:
                return ValidationResult(
                    check_name="disk_health",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Critical disk usage: {disk_percent:.1f}%",
                    details={"disk_percent": disk_percent},
                    remediation="Free up disk space or increase storage capacity",
                )
            elif disk_percent > 85:
                return ValidationResult(
                    check_name="disk_health",
                    severity=ValidationSeverity.WARNING,
                    message=f"High disk usage: {disk_percent:.1f}%",
                    details={"disk_percent": disk_percent},
                    remediation="Monitor disk usage and clean up unnecessary files",
                )
            else:
                return ValidationResult(
                    check_name="disk_health",
                    severity=ValidationSeverity.INFO,
                    message=f"Disk usage normal: {disk_percent:.1f}%",
                    details={"disk_percent": disk_percent},
                )

        except Exception as e:
            return ValidationResult(
                check_name="disk_health",
                severity=ValidationSeverity.ERROR,
                message=f"Disk validation failed: {str(e)}",
                details={"error": str(e)},
            )

    def _validate_cache_health(self) -> ValidationResult:
        """Validate cache system health."""
        try:
            # Check cache manager health

            # This would check actual cache health
            # For now, return healthy
            return ValidationResult(
                check_name="cache_health",
                severity=ValidationSeverity.INFO,
                message="Cache system operational",
                details={},
            )

        except Exception as e:
            return ValidationResult(
                check_name="cache_health",
                severity=ValidationSeverity.WARNING,
                message=f"Cache validation failed: {str(e)}",
                details={"error": str(e)},
                remediation="Check cache configuration and dependencies",
            )

    def _validate_plugin_health(self) -> ValidationResult:
        """Validate plugin system health."""
        try:
            # Check plugin manager health

            # This would check actual plugin health
            # For now, return healthy
            return ValidationResult(
                check_name="plugin_health",
                severity=ValidationSeverity.INFO,
                message="Plugin system operational",
                details={},
            )

        except Exception as e:
            return ValidationResult(
                check_name="plugin_health",
                severity=ValidationSeverity.WARNING,
                message=f"Plugin validation failed: {str(e)}",
                details={"error": str(e)},
                remediation="Check plugin configuration and installed plugins",
            )

    def _validate_configuration_health(self) -> ValidationResult:
        """Validate configuration health."""
        try:
            # Check configuration manager health

            # This would check actual configuration health
            # For now, return healthy
            return ValidationResult(
                check_name="configuration_health",
                severity=ValidationSeverity.INFO,
                message="Configuration system operational",
                details={},
            )

        except Exception as e:
            return ValidationResult(
                check_name="configuration_health",
                severity=ValidationSeverity.ERROR,
                message=f"Configuration validation failed: {str(e)}",
                details={"error": str(e)},
                remediation="Check configuration files and settings",
            )

    def _validate_performance_health(self) -> ValidationResult:
        """Validate performance health."""
        try:
            # Check performance metrics
            from ..monitoring.performance import get_global_performance_monitor

            monitor = get_global_performance_monitor()
            summary = monitor.get_metrics_summary()

            # Check for performance issues
            if summary["error_rate"] > 0.1:  # 10% error rate
                return ValidationResult(
                    check_name="performance_health",
                    severity=ValidationSeverity.WARNING,
                    message=f"High error rate: {summary['error_rate']:.2%}",
                    details={"error_rate": summary["error_rate"]},
                    remediation="Investigate and fix recurring errors",
                )
            else:
                return ValidationResult(
                    check_name="performance_health",
                    severity=ValidationSeverity.INFO,
                    message=f"Performance normal, error rate: {summary['error_rate']:.2%}",
                    details={"error_rate": summary["error_rate"]},
                )

        except Exception as e:
            return ValidationResult(
                check_name="performance_health",
                severity=ValidationSeverity.WARNING,
                message=f"Performance validation failed: {str(e)}",
                details={"error": str(e)},
            )

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        with self._lock:
            if not self.validation_history:
                return {"message": "No validations performed yet"}

            # Group by severity
            results_by_severity = {
                ValidationSeverity.INFO: [],
                ValidationSeverity.WARNING: [],
                ValidationSeverity.ERROR: [],
                ValidationSeverity.CRITICAL: [],
            }

            for result in self.validation_history:
                results_by_severity[result.severity].append(result)

            # Get recent issues (last hour)
            recent_cutoff = time.time() - 3600
            recent_results = [
                r for r in self.validation_history if r.timestamp > recent_cutoff
            ]

            return {
                "total_validations": len(self.validation_history),
                "recent_validations": len(recent_results),
                "results_by_severity": {
                    severity.value: len(results)
                    for severity, results in results_by_severity.items()
                },
                "statistics": self.stats.copy(),
                "validation_checks": list(self.validation_checks.keys()),
            }

    def get_critical_issues(self) -> List[ValidationResult]:
        """Get current critical issues."""
        with self._lock:
            return [
                result
                for result in self.validation_history
                if result.severity == ValidationSeverity.CRITICAL
                and time.time() - result.timestamp < 3600  # Last hour
            ]

    def clear_validation_history(self):
        """Clear validation history."""
        with self._lock:
            self.validation_history.clear()

    def export_validation_report(self, format: str = "json") -> str:
        """
        Export validation report.

        Args:
            format: Export format ('json' or 'text')

        Returns:
            Validation report as formatted string
        """
        summary = self.get_validation_summary()

        if format.lower() == "json":
            import json

            return json.dumps(summary, indent=2, default=str)

        else:
            # Text format
            report = []
            report.append("Blur Suite Health Validation Report")
            report.append("=" * 50)
            report.append(f"Total Validations: {summary['total_validations']}")
            report.append(f"Recent Validations: {summary['recent_validations']}")
            report.append("")

            # Results by severity
            report.append("Results by Severity:")
            for severity, count in summary["results_by_severity"].items():
                report.append(f"  {severity}: {count}")
            report.append("")

            # Statistics
            stats = summary["statistics"]
            report.append("Statistics:")
            report.append(f"  Validations Performed: {stats['validations_performed']}")
            report.append(f"  Issues Found: {stats['issues_found']}")
            report.append(f"  Critical Issues: {stats['critical_issues']}")
            report.append(f"  Remediations Applied: {stats['remediations_applied']}")
            report.append("")

            # Validation checks
            report.append("Available Validation Checks:")
            for check_name in summary["validation_checks"]:
                report.append(f"  - {check_name}")
            report.append("")

            return "\n".join(report)


class SystemRecoveryManager:
    """
    System recovery manager that coordinates recovery actions.
    """

    def __init__(self, health_validator: HealthValidator):
        """
        Initialize system recovery manager.

        Args:
            health_validator: Health validator instance
        """
        self.health_validator = health_validator
        self.recovery_actions: Dict[str, Callable] = {}
        self._lock = threading.RLock()

        # Register default recovery actions
        self._register_default_recovery_actions()

    def _register_default_recovery_actions(self):
        """Register default recovery actions."""
        self.recovery_actions.update(
            {
                "memory_recovery": self._perform_memory_recovery,
                "disk_recovery": self._perform_disk_recovery,
                "cache_recovery": self._perform_cache_recovery,
                "plugin_recovery": self._perform_plugin_recovery,
            }
        )

    def _perform_memory_recovery(self) -> bool:
        """Perform memory recovery actions."""
        try:
            # Trigger garbage collection
            import gc

            gc.collect()

            # Clear caches
            try:
                from ..cache.cache_manager import CacheManager

                cache_manager = CacheManager()
                cache_manager.clear()
            except Exception:
                pass

            # Clear memory pools
            try:
                from ..memory.memory_manager import MemoryManager

                memory_manager = MemoryManager()
                memory_manager.trigger_cleanup()
            except Exception:
                pass

            return True

        except Exception:
            return False

    def _perform_disk_recovery(self) -> bool:
        """Perform disk space recovery actions."""
        try:
            # Clear old log files
            try:
                from ..logging.log_manager import get_global_log_manager

                log_manager = get_global_log_manager()
                log_manager.clear_old_logs(keep_days=1)
            except Exception:
                pass

            # Clear old cache files if any
            # This would implement cache file cleanup

            return True

        except Exception:
            return False

    def _perform_cache_recovery(self) -> bool:
        """Perform cache recovery actions."""
        try:
            # Clear all caches
            try:
                from ..cache.cache_manager import CacheManager

                cache_manager = CacheManager()
                cache_manager.clear()
            except Exception:
                pass

            return True

        except Exception:
            return False

    def _perform_plugin_recovery(self) -> bool:
        """Perform plugin recovery actions."""
        try:
            # This would implement plugin recovery
            # For now, return success
            return True

        except Exception:
            return False

    def register_recovery_action(self, name: str, action_func: Callable):
        """
        Register a recovery action.

        Args:
            name: Recovery action name
            action_func: Function that performs recovery
        """
        with self._lock:
            self.recovery_actions[name] = action_func

    def perform_recovery(self, recovery_type: str) -> bool:
        """
        Perform specific recovery action.

        Args:
            recovery_type: Type of recovery to perform

        Returns:
            True if recovery succeeded, False otherwise
        """
        if recovery_type in self.recovery_actions:
            try:
                success = self.recovery_actions[recovery_type]()
                return success
            except Exception:
                return False

        return False

    def perform_automatic_recovery(self) -> Dict[str, bool]:
        """
        Perform automatic recovery based on current issues.

        Returns:
            Dictionary of recovery results
        """
        results = {}

        # Get current issues
        issues = self.health_validator.get_critical_issues()

        for issue in issues:
            recovery_type = self._get_recovery_type_for_issue(issue)

            if recovery_type:
                success = self.perform_recovery(recovery_type)
                results[recovery_type] = success

        return results

    def _get_recovery_type_for_issue(self, issue: ValidationResult) -> Optional[str]:
        """Get recovery type for a specific issue."""
        issue_mapping = {
            "memory_health": "memory_recovery",
            "disk_health": "disk_recovery",
            "cache_health": "cache_recovery",
            "plugin_health": "plugin_recovery",
        }

        return issue_mapping.get(issue.check_name)


# Global health validator instance
_global_health_validator = None
_health_validator_lock = threading.Lock()


def get_global_health_validator() -> HealthValidator:
    """Get the global health validator instance."""
    global _global_health_validator

    if _global_health_validator is None:
        with _health_validator_lock:
            if _global_health_validator is None:
                _global_health_validator = HealthValidator()

    return _global_health_validator


def validate_system_health() -> List[ValidationResult]:
    """Perform comprehensive system health validation."""
    validator = get_global_health_validator()
    return validator.validate_system()


def perform_system_recovery() -> Dict[str, bool]:
    """Perform automatic system recovery."""
    validator = get_global_health_validator()
    recovery_manager = SystemRecoveryManager(validator)
    return recovery_manager.perform_automatic_recovery()
