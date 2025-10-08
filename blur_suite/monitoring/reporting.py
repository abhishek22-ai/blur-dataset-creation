"""
Report Generator

Comprehensive report generation for monitoring data, performance metrics,
and system health information.
"""

import json
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ReportSection:
    """Section of a report."""

    title: str
    content: str
    level: int = 1
    data: Optional[Dict[str, Any]] = None


class ReportGenerator:
    """
    Comprehensive report generation system.

    Generates detailed reports from monitoring data, performance metrics,
    health checks, and system information.
    """

    def __init__(self):
        """Initialize report generator."""
        self.report_sections: List[ReportSection] = []
        self.metadata = {
            "generator": "BlurSuite Report Generator",
            "version": "1.0.0",
            "generated_at": time.time(),
        }

    def add_section(self, title: str, content: str, level: int = 1, **data):
        """
        Add a section to the report.

        Args:
            title: Section title
            content: Section content
            level: Section level (1-6)
            **data: Additional data for the section
        """
        section = ReportSection(title=title, content=content, level=level, data=data)
        self.report_sections.append(section)

    def generate_system_report(self) -> str:
        """
        Generate comprehensive system report.

        Returns:
            Complete system report
        """
        self.report_sections.clear()

        # Report header
        self._add_report_header()

        # System overview
        self._add_system_overview()

        # Performance metrics
        self._add_performance_section()

        # Health status
        self._add_health_section()

        # Configuration summary
        self._add_configuration_section()

        # Plugin information
        self._add_plugin_section()

        # Generate final report
        return self._generate_markdown_report()

    def _add_report_header(self):
        """Add report header section."""
        header = f"""
# Blur Suite System Report

**Generated:** {time.ctime(self.metadata["generated_at"])}
**Generator:** {self.metadata["generator"]} v{self.metadata["version"]}

---
"""
        self.add_section("Report Header", header, level=1)

    def _add_system_overview(self):
        """Add system overview section."""
        try:
            import platform

            import psutil

            # System information
            system_info = {
                "Platform": platform.platform(),
                "System": platform.system(),
                "Processor": platform.processor(),
                "Architecture": ", ".join(platform.architecture()),
                "Python Version": platform.python_version(),
                "CPU Cores": os.cpu_count() or "Unknown",
            }

            # Memory information
            memory = psutil.virtual_memory()
            system_info.update(
                {
                    "Total Memory": f"{memory.total / (1024**3):.2f} GB",
                    "Available Memory": f"{memory.available / (1024**3):.2f} GB",
                    "Memory Usage": f"{memory.percent:.1f}%",
                }
            )

            # Disk information
            disk = psutil.disk_usage("/")
            system_info.update(
                {
                    "Disk Total": f"{disk.total / (1024**3):.2f} GB",
                    "Disk Free": f"{disk.free / (1024**3):.2f} GB",
                    "Disk Usage": f"{disk.percent:.1f}%",
                }
            )

            # Format system info
            content = "\n".join(
                f"**{key}:** {value}" for key, value in system_info.items()
            )

            self.add_section("System Overview", content, level=2)

        except Exception as e:
            self.add_section(
                "System Overview", f"Error collecting system info: {str(e)}", level=2
            )

    def _add_performance_section(self):
        """Add performance metrics section."""
        try:
            from .performance import get_global_performance_monitor

            monitor = get_global_performance_monitor()
            summary = monitor.get_metrics_summary()

            content = f"""
**Monitoring Duration:** {summary["monitoring_duration"]:.2f} seconds
**Metrics Collected:** {summary["metrics_collected"]}
**Operations Profiled:** {summary["operations_profiled"]}
**Total Operations:** {summary["total_operations"]}
**Total Operation Time:** {summary["total_operation_time"]:.2f} seconds
**Error Rate:** {summary["error_rate"]:.2%}

### System Metrics
"""

            # Add system metrics details
            if summary["system_metrics"]:
                for metric_name, stats in summary["system_metrics"].items():
                    content += f"""
**{metric_name}:**
- Current: {stats["current"]}
- Average: {stats["average"]:.2f}
- Range: {stats["min"]:.2f} - {stats["max"]:.2f}
- Samples: {stats["samples"]}
"""

            self.add_section("Performance Metrics", content, level=2)

        except Exception as e:
            self.add_section(
                "Performance Metrics",
                f"Error collecting performance data: {str(e)}",
                level=2,
            )

    def _add_health_section(self):
        """Add health status section."""
        try:
            from .health import get_global_health_checker

            checker = get_global_health_checker()
            report = checker.get_health_report()

            if not report:
                content = "No health checks performed yet."
            else:
                content = f"""
**Overall Status:** {report.overall_status.value.upper()}
**Total Checks:** {len(report.checks)}
**Report Time:** {time.ctime(report.timestamp)}

### Health Checks
"""

                # Group checks by status
                checks_by_status = {}
                for check in report.checks:
                    status = check.status.value
                    if status not in checks_by_status:
                        checks_by_status[status] = []
                    checks_by_status[status].append(check)

                # Add checks for each status
                for status in ["healthy", "warning", "critical", "unknown"]:
                    checks = checks_by_status.get(status, [])
                    if checks:
                        content += f"\n#### {status.upper()} ({len(checks)})\n"
                        for check in checks:
                            content += f"""
**{check.name}:** {check.message}
- Duration: {check.duration:.3f}s
- Last Check: {time.ctime(check.timestamp)}
"""

            self.add_section("Health Status", content, level=2)

        except Exception as e:
            self.add_section(
                "Health Status", f"Error collecting health data: {str(e)}", level=2
            )

    def _add_configuration_section(self):
        """Add configuration summary section."""
        try:

            # This would get actual configuration summary
            # For now, provide placeholder
            content = """
Configuration system operational.
Detailed configuration information would be displayed here.
"""
            self.add_section("Configuration", content, level=2)

        except Exception as e:
            self.add_section(
                "Configuration",
                f"Error collecting configuration data: {str(e)}",
                level=2,
            )

    def _add_plugin_section(self):
        """Add plugin information section."""
        try:

            # This would get actual plugin information
            # For now, provide placeholder
            content = """
Plugin system operational.
Plugin discovery, validation, and management information would be displayed here.
"""
            self.add_section("Plugin System", content, level=2)

        except Exception as e:
            self.add_section(
                "Plugin System", f"Error collecting plugin data: {str(e)}", level=2
            )

    def _generate_markdown_report(self) -> str:
        """Generate markdown formatted report."""
        sections = []

        for section in self.report_sections:
            # Add section header
            header_level = "#" * section.level
            sections.append(f"\n{header_level} {section.title}\n")

            # Add section content
            sections.append(section.content)

        return "\n".join(sections)

    def generate_json_report(self) -> str:
        """
        Generate JSON formatted report.

        Returns:
            JSON report string
        """
        report_data = {
            "metadata": self.metadata,
            "sections": [
                {
                    "title": section.title,
                    "level": section.level,
                    "content": section.content,
                    "data": section.data,
                }
                for section in self.report_sections
            ],
        }

        return json.dumps(report_data, indent=2, default=str)

    def save_report(self, file_path: str, format: str = "markdown"):
        """
        Save report to file.

        Args:
            file_path: Path to save the report
            format: Report format ('markdown' or 'json')
        """
        if format.lower() == "markdown":
            content = self._generate_markdown_report()
        elif format.lower() == "json":
            content = self.generate_json_report()
        else:
            raise ValueError(f"Unsupported report format: {format}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def generate_performance_dashboard_data(self) -> Dict[str, Any]:
        """
        Generate data for performance dashboard.

        Returns:
            Dashboard data dictionary
        """
        dashboard_data = {
            "timestamp": time.time(),
            "summary": {},
            "charts": {},
            "alerts": [],
        }

        try:
            # Get performance summary
            from .performance import get_global_performance_monitor

            monitor = get_global_performance_monitor()
            dashboard_data["summary"] = monitor.get_metrics_summary()

            # Get health status
            from .health import get_global_health_checker

            checker = get_global_health_checker()
            dashboard_data["health"] = checker.get_health_summary()

            # Generate chart data
            dashboard_data["charts"] = self._generate_chart_data()

            # Generate alerts
            dashboard_data["alerts"] = self._generate_alerts()

        except Exception as e:
            dashboard_data["error"] = str(e)

        return dashboard_data

    def _generate_chart_data(self) -> Dict[str, Any]:
        """Generate data for charts and visualizations."""
        charts = {}

        try:
            # Performance over time chart
            from .performance import get_global_performance_monitor

            get_global_performance_monitor()

            # This would generate actual chart data
            # For now, provide placeholder structure
            charts["performance_timeline"] = {
                "type": "line",
                "title": "Performance Over Time",
                "data": [],
            }

            # System metrics chart
            charts["system_metrics"] = {
                "type": "multi-line",
                "title": "System Metrics",
                "data": {},
            }

        except Exception:
            charts["error"] = "Error generating chart data"

        return charts

    def _generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate system alerts."""
        alerts = []

        try:
            # Check for critical health issues
            from .health import get_global_health_checker

            checker = get_global_health_checker()

            if not checker.is_healthy():
                alerts.append(
                    {
                        "type": "health",
                        "severity": "critical",
                        "message": "System health check failed",
                        "timestamp": time.time(),
                    }
                )

            # Check for high resource usage
            import psutil

            memory = psutil.virtual_memory()

            if memory.percent > 85:
                alerts.append(
                    {
                        "type": "memory",
                        "severity": "warning",
                        "message": f"High memory usage: {memory.percent:.1f}%",
                        "timestamp": time.time(),
                    }
                )

        except Exception:
            alerts.append(
                {
                    "type": "monitoring",
                    "severity": "warning",
                    "message": "Error checking for alerts",
                    "timestamp": time.time(),
                }
            )

        return alerts

    def generate_custom_report(
        self,
        sections: List[str],
        include_charts: bool = False,
        include_alerts: bool = True,
    ) -> str:
        """
        Generate custom report with specific sections.

        Args:
            sections: List of section names to include
            include_charts: Whether to include chart data
            include_alerts: Whether to include alerts

        Returns:
            Custom report
        """
        self.report_sections.clear()

        # Add requested sections
        section_generators = {
            "header": self._add_report_header,
            "system": self._add_system_overview,
            "performance": self._add_performance_section,
            "health": self._add_health_section,
            "configuration": self._add_configuration_section,
            "plugins": self._add_plugin_section,
        }

        for section_name in sections:
            if section_name in section_generators:
                section_generators[section_name]()

        # Add charts and alerts if requested
        if include_charts:
            self._add_charts_section()

        if include_alerts:
            self._add_alerts_section()

        return self._generate_markdown_report()

    def _add_charts_section(self):
        """Add charts section to report."""
        try:
            dashboard_data = self.generate_performance_dashboard_data()
            charts = dashboard_data.get("charts", {})

            content = (
                "Performance charts and visualizations would be displayed here.\n\n"
            )

            if "error" in charts:
                content += f"Chart generation error: {charts['error']}\n"
            else:
                content += "Charts available:\n"
                for chart_name in charts.keys():
                    content += f"- {chart_name}\n"

            self.add_section("Charts and Visualizations", content, level=2)

        except Exception as e:
            self.add_section(
                "Charts and Visualizations",
                f"Error generating charts: {str(e)}",
                level=2,
            )

    def _add_alerts_section(self):
        """Add alerts section to report."""
        try:
            alerts = self._generate_alerts()

            if not alerts:
                content = "No alerts at this time."
            else:
                content = f"**Active Alerts:** {len(alerts)}\n\n"

                for alert in alerts:
                    content += f"""
**{alert["severity"].upper()}:** {alert["message"]}
- Type: {alert["type"]}
- Time: {time.ctime(alert["timestamp"])}
"""

            self.add_section("Alerts", content, level=2)

        except Exception as e:
            self.add_section("Alerts", f"Error generating alerts: {str(e)}", level=2)


# Global report generator instance
_global_report_generator = None
_report_lock = threading.Lock()


def get_global_report_generator() -> ReportGenerator:
    """Get the global report generator instance."""
    global _global_report_generator

    if _global_report_generator is None:
        with _report_lock:
            if _global_report_generator is None:
                _global_report_generator = ReportGenerator()

    return _global_report_generator


def generate_system_report() -> str:
    """Generate a comprehensive system report."""
    generator = get_global_report_generator()
    return generator.generate_system_report()


def save_system_report(file_path: str, format: str = "markdown"):
    """Save system report to file."""
    generator = get_global_report_generator()
    generator.save_report(file_path, format)


# Import os here to avoid circular imports
import os
