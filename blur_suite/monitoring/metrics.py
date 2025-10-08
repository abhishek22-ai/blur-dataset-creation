"""
Metrics Collector

Collection and aggregation of usage and performance metrics.
"""

import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MetricPoint:
    """Single metric data point."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series of metric data."""

    name: str
    points: deque = field(default_factory=lambda: deque(maxlen=10000))
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""

    def add_point(self, value: float, timestamp: Optional[float] = None, **metadata):
        """Add a data point to the series."""
        point = MetricPoint(
            name=self.name,
            value=value,
            timestamp=timestamp or time.time(),
            tags=self.tags.copy(),
            metadata=metadata,
        )
        self.points.append(point)

    def get_statistics(self, window: Optional[int] = None) -> Dict[str, float]:
        """Get statistics for the series."""
        if not self.points:
            return {}

        values = [p.value for p in self.points]
        if window:
            values = values[-window:]

        if not values:
            return {}

        return {
            "count": len(values),
            "sum": sum(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "latest": values[-1],
            "oldest": values[0] if values else None,
        }

    def get_percentiles(self, percentiles: List[float] = None) -> Dict[str, float]:
        """Get percentile values."""
        if not self.points:
            return {}

        percentiles = percentiles or [0.5, 0.95, 0.99]
        values = [p.value for p in self.points]

        if not values:
            return {}

        result = {}
        for p in percentiles:
            percentile_value = statistics.quantiles(values, n=100)[int(p * 100) - 1]
            result[f"p{p * 100:.0f}"] = percentile_value

        return result


class MetricsCollector:
    """
    Advanced metrics collection and aggregation system.

    Collects, stores, and provides access to various types of
    metrics including counters, gauges, histograms, and timers.
    """

    def __init__(self, max_series_size: int = 10000):
        """
        Initialize metrics collector.

        Args:
            max_series_size: Maximum number of data points per series
        """
        self.max_series_size = max_series_size
        self._series: Dict[str, MetricSeries] = {}
        self._lock = threading.RLock()

        # Collection settings
        self.collection_enabled = True
        self.auto_flush_interval = 60.0  # seconds

        # Statistics
        self.stats = {
            "series_count": 0,
            "total_points": 0,
            "collection_time": 0.0,
            "flush_count": 0,
        }

    def counter(self, name: str, value: float = 1.0, **tags) -> MetricSeries:
        """
        Create or update a counter metric.

        Args:
            name: Counter name
            value: Value to increment by
            **tags: Metric tags

        Returns:
            Counter metric series
        """
        series = self._get_or_create_series(name, "counter", **tags)
        series.add_point(value)
        return series

    def gauge(self, name: str, value: float, **tags) -> MetricSeries:
        """
        Create or update a gauge metric.

        Args:
            name: Gauge name
            value: Current value
            **tags: Metric tags

        Returns:
            Gauge metric series
        """
        series = self._get_or_create_series(name, "gauge", **tags)
        series.add_point(value)
        return series

    def histogram(self, name: str, value: float, **tags) -> MetricSeries:
        """
        Record a value in a histogram.

        Args:
            name: Histogram name
            value: Value to record
            **tags: Metric tags

        Returns:
            Histogram metric series
        """
        series = self._get_or_create_series(name, "histogram", **tags)
        series.add_point(value)
        return series

    def timer(self, name: str, duration: float, **tags) -> MetricSeries:
        """
        Record a timing measurement.

        Args:
            name: Timer name
            duration: Duration in seconds
            **tags: Metric tags

        Returns:
            Timer metric series
        """
        series = self._get_or_create_series(name, "timer", **tags)
        series.add_point(duration)
        return series

    def _get_or_create_series(
        self, name: str, metric_type: str, **tags
    ) -> MetricSeries:
        """Get or create a metric series."""
        series_key = self._make_series_key(name, tags)

        with self._lock:
            if series_key not in self._series:
                self._series[series_key] = MetricSeries(
                    name=name, tags=tags, description=f"{metric_type} metric: {name}"
                )
                self.stats["series_count"] = len(self._series)

            return self._series[series_key]

    def _make_series_key(self, name: str, tags: Dict[str, str]) -> str:
        """Create unique key for metric series."""
        if not tags:
            return name

        # Sort tags for consistent key generation
        sorted_tags = sorted(tags.items())
        tag_str = ",".join(f"{k}={v}" for k, v in sorted_tags)
        return f"{name}[{tag_str}]"

    def increment_counter(self, name: str, value: float = 1.0, **tags):
        """Increment a counter by a specific value."""
        return self.counter(name, value, **tags)

    def record_timing(self, name: str, start_time: float, **tags):
        """Record timing from start time."""
        duration = time.time() - start_time
        return self.timer(name, duration, **tags)

    def timing_context(self, name: str, **tags):
        """
        Context manager for timing operations.

        Args:
            name: Timer name
            **tags: Timer tags

        Returns:
            TimingContext instance
        """
        return TimingContext(self, name, **tags)

    def get_metric_series(self, name: str, **tags) -> Optional[MetricSeries]:
        """Get a specific metric series."""
        series_key = self._make_series_key(name, tags)

        with self._lock:
            return self._series.get(series_key)

    def list_metrics(self) -> List[Dict[str, Any]]:
        """List all metric series."""
        with self._lock:
            metrics = []

            for series_key, series in self._series.items():
                stats = series.get_statistics()
                percentiles = series.get_percentiles()

                metrics.append(
                    {
                        "name": series.name,
                        "series_key": series_key,
                        "type": "gauge",  # Could be enhanced to track actual type
                        "tags": series.tags,
                        "unit": series.unit,
                        "description": series.description,
                        "statistics": stats,
                        "percentiles": percentiles,
                        "point_count": len(series.points),
                    }
                )

            return metrics

    def query_metrics(
        self,
        name_pattern: str = "*",
        tag_filter: Optional[Dict[str, str]] = None,
        time_range: Optional[tuple] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query metrics with filters.

        Args:
            name_pattern: Pattern to match metric names
            tag_filter: Tags to filter by
            time_range: Time range as (start_time, end_time)

        Returns:
            List of matching metrics
        """
        import fnmatch

        matching_metrics = []

        for metric_info in self.list_metrics():
            # Check name pattern
            if not fnmatch.fnmatch(metric_info["name"], name_pattern):
                continue

            # Check tag filter
            if tag_filter:
                matches_tags = True
                for tag_key, tag_value in tag_filter.items():
                    if (
                        tag_key not in metric_info["tags"]
                        or metric_info["tags"][tag_key] != tag_value
                    ):
                        matches_tags = False
                        break

                if not matches_tags:
                    continue

            # Check time range
            if time_range:
                start_time, end_time = time_range
                # This would require storing timestamps in the metric info
                # For now, we'll skip time filtering

            matching_metrics.append(metric_info)

        return matching_metrics

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        all_stats = {
            "total_series": len(self._series),
            "total_points": sum(len(series.points) for series in self._series.values()),
            "oldest_metric": None,
            "newest_metric": None,
            "top_series": [],
        }

        # Find oldest and newest metrics
        oldest_time = newest_time = None

        for series in self._series.values():
            if series.points:
                series_times = [p.timestamp for p in series.points]
                series_oldest = min(series_times)
                series_newest = max(series_times)

                if oldest_time is None or series_oldest < oldest_time:
                    oldest_time = series_oldest
                if newest_time is None or series_newest > newest_time:
                    newest_time = series_newest

        all_stats["oldest_metric"] = oldest_time
        all_stats["newest_metric"] = newest_time

        # Get top series by point count
        series_by_size = sorted(
            self._series.items(), key=lambda x: len(x[1].points), reverse=True
        )

        all_stats["top_series"] = [
            {
                "name": series.name,
                "point_count": len(series.points),
                "tags": series.tags,
            }
            for _, series in series_by_size[:10]
        ]

        return all_stats

    def export_metrics(self, format: str = "json") -> str:
        """
        Export all metrics.

        Args:
            format: Export format ('json', 'csv', 'prometheus')

        Returns:
            Metrics as formatted string
        """
        metrics = self.list_metrics()

        if format.lower() == "json":
            import json

            return json.dumps(metrics, indent=2, default=str)

        elif format.lower() == "csv":
            lines = ["Name,Type,Value,Tags,Timestamp"]

            for metric in metrics:
                name = metric["name"]
                metric_type = metric["type"]
                stats = metric["statistics"]

                if "mean" in stats:
                    value = stats["mean"]
                    timestamp = "latest"
                    tags = ",".join(f"{k}={v}" for k, v in metric["tags"].items())

                    lines.append(f"{name},{metric_type},{value},{tags},{timestamp}")

            return "\n".join(lines)

        elif format.lower() == "prometheus":
            lines = []

            for metric in metrics:
                name = metric["name"].replace("-", "_").replace(" ", "_")
                stats = metric["statistics"]

                if "mean" in stats:
                    value = stats["mean"]
                    timestamp = int(time.time() * 1000)  # Prometheus uses milliseconds

                    # Add labels
                    labels = ",".join(f'{k}="{v}"' for k, v in metric["tags"].items())
                    if labels:
                        lines.append(f"{name}{{{labels}}} {value} {timestamp}")
                    else:
                        lines.append(f"{name} {value} {timestamp}")

            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def clear_metrics(self, name_pattern: str = "*"):
        """Clear metrics matching a pattern."""
        import fnmatch

        with self._lock:
            keys_to_remove = []

            for series_key in self._series.keys():
                # Extract metric name from series key
                metric_name = series_key.split("[")[0]

                if fnmatch.fnmatch(metric_name, name_pattern):
                    keys_to_remove.append(series_key)

            for key in keys_to_remove:
                del self._series[key]

            self.stats["series_count"] = len(self._series)

    def flush_metrics(self):
        """Flush old metrics to free memory."""
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - (24 * 3600)  # Keep last 24 hours

            for series in self._series.values():
                # Remove old points
                while series.points:
                    oldest_point = series.points[0]
                    if oldest_point.timestamp >= cutoff_time:
                        break
                    series.points.popleft()

            self.stats["flush_count"] += 1


class TimingContext:
    """
    Context manager for timing operations.
    """

    def __init__(self, collector: MetricsCollector, name: str, **tags):
        """
        Initialize timing context.

        Args:
            collector: Metrics collector instance
            name: Timer name
            **tags: Timer tags
        """
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        """Enter timing context."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit timing context."""
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.timer(self.name, duration, **self.tags)


# Global metrics collector instance
_global_metrics_collector = None
_metrics_lock = threading.Lock()


def get_global_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _global_metrics_collector

    if _global_metrics_collector is None:
        with _metrics_lock:
            if _global_metrics_collector is None:
                _global_metrics_collector = MetricsCollector()

    return _global_metrics_collector


def record_metric(name: str, value: float, metric_type: str = "gauge", **tags):
    """
    Record a metric with the global collector.

    Args:
        name: Metric name
        value: Metric value
        metric_type: Type of metric ('counter', 'gauge', 'histogram', 'timer')
        **tags: Metric tags
    """
    collector = get_global_metrics_collector()

    if metric_type == "counter":
        collector.counter(name, value, **tags)
    elif metric_type == "gauge":
        collector.gauge(name, value, **tags)
    elif metric_type == "histogram":
        collector.histogram(name, value, **tags)
    elif metric_type == "timer":
        collector.timer(name, value, **tags)
    else:
        raise ValueError(f"Unknown metric type: {metric_type}")


def timing(name: str, **tags):
    """
    Context manager for timing with global collector.

    Args:
        name: Timer name
        **tags: Timer tags

    Returns:
        TimingContext instance
    """
    collector = get_global_metrics_collector()
    return collector.timing_context(name, **tags)
