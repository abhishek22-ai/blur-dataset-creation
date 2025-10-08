"""
Event System

Event-driven architecture for custom integrations and extensibility.
"""

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventType(Enum):
    """Types of events in the system."""

    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    BLUR_APPLIED = "blur_applied"
    IMAGE_LOADED = "image_loaded"
    IMAGE_SAVED = "image_saved"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_MILESTONE = "performance_milestone"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    MEMORY_WARNING = "memory_warning"
    CONFIG_CHANGED = "config_changed"


@dataclass
class Event:
    """Event information."""

    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: str = "system"

    def get(self, key: str, default: Any = None) -> Any:
        """Get event data."""
        return self.data.get(key, default)


class EventSystem:
    """
    Event-driven system for extensibility.

    Allows components to emit events and other components
    to listen for and react to those events.
    """

    def __init__(self):
        """Initialize event system."""
        self._listeners: Dict[EventType, List[Callable]] = {}
        self._lock = threading.RLock()

        # Event history
        self.event_history: List[Event] = []
        self.max_history_size = 1000

        # Statistics
        self.stats = {"events_emitted": 0, "events_processed": 0, "errors": 0}

    def emit_event(
        self,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None,
        source: str = "system",
    ) -> Event:
        """
        Emit an event.

        Args:
            event_type: Type of event
            data: Event data
            source: Event source

        Returns:
            Created event
        """
        event = Event(event_type=event_type, data=data or {}, source=source)

        # Store in history
        with self._lock:
            self.event_history.append(event)
            if len(self.event_history) > self.max_history_size:
                self.event_history.pop(0)

            self.stats["events_emitted"] += 1

        # Process event asynchronously
        self._process_event_async(event)

        return event

    def _process_event_async(self, event: Event):
        """Process event asynchronously."""

        def process():
            try:
                listeners = self._get_listeners(event.event_type)
                results = []

                for listener in listeners:
                    try:
                        result = listener(event)
                        results.append(result)
                        self.stats["events_processed"] += 1
                    except Exception as e:
                        self.stats["errors"] += 1
                        print(f"Error in event listener: {e}")

            except Exception as e:
                self.stats["errors"] += 1
                print(f"Error processing event: {e}")

        # Run in background thread
        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def _get_listeners(self, event_type: EventType) -> List[Callable]:
        """Get listeners for an event type."""
        with self._lock:
            return self._listeners.get(event_type, []).copy()

    def add_listener(
        self, event_type: EventType, listener: Callable, priority: int = 0
    ) -> str:
        """
        Add an event listener.

        Args:
            event_type: Type of events to listen for
            listener: Listener function
            priority: Listener priority (higher = called first)

        Returns:
            Listener ID for removal
        """
        listener_id = f"{event_type.value}_{len(self._listeners.get(event_type, []))}_{id(listener)}"

        listener_entry = {
            "id": listener_id,
            "func": listener,
            "priority": priority,
            "added_at": time.time(),
        }

        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []

            # Insert in priority order
            listeners_list = self._listeners[event_type]
            sorted_listeners = sorted(
                listeners_list + [listener_entry],
                key=lambda l: l["priority"],
                reverse=True,
            )

            listeners_list.clear()
            listeners_list.extend(sorted_listeners)

        return listener_id

    def remove_listener(self, listener_id: str) -> bool:
        """
        Remove an event listener.

        Args:
            listener_id: Listener ID returned by add_listener

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            for event_type, listeners_list in self._listeners.items():
                for i, listener_entry in enumerate(listeners_list):
                    if listener_entry["id"] == listener_id:
                        del listeners_list[i]
                        return True

        return False

    def add_listener_for_multiple_events(
        self, event_types: List[EventType], listener: Callable, priority: int = 0
    ) -> List[str]:
        """
        Add listener for multiple event types.

        Args:
            event_types: List of event types
            listener: Listener function
            priority: Listener priority

        Returns:
            List of listener IDs
        """
        listener_ids = []

        for event_type in event_types:
            listener_id = self.add_listener(event_type, listener, priority)
            listener_ids.append(listener_id)

        return listener_ids

    def clear_listeners(self, event_type: Optional[EventType] = None):
        """
        Clear event listeners.

        Args:
            event_type: Specific event type to clear, or None for all
        """
        with self._lock:
            if event_type is not None:
                if event_type in self._listeners:
                    self._listeners[event_type].clear()
            else:
                self._listeners.clear()

    def get_event_history(
        self, event_type: Optional[EventType] = None, limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get event history.

        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        history = self.event_history

        if event_type is not None:
            history = [e for e in history if e.event_type == event_type]

        if limit is not None:
            history = history[-limit:]

        return history.copy()

    def get_listener_count(self, event_type: Optional[EventType] = None) -> int:
        """
        Get number of listeners.

        Args:
            event_type: Specific event type, or None for total

        Returns:
            Number of listeners
        """
        with self._lock:
            if event_type is not None:
                return len(self._listeners.get(event_type, []))
            else:
                return sum(len(listeners) for listeners in self._listeners.values())

    def get_event_stats(self) -> Dict[str, Any]:
        """Get event system statistics."""
        event_type_counts = {}
        for event in self.event_history:
            event_type = event.event_type.value
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        return {
            "events_emitted": self.stats["events_emitted"],
            "events_processed": self.stats["events_processed"],
            "errors": self.stats["errors"],
            "event_history_size": len(self.event_history),
            "listener_count": self.get_listener_count(),
            "event_type_counts": event_type_counts,
        }


# Global event system instance
_global_event_system = None
_event_system_lock = threading.Lock()


def get_global_event_system() -> EventSystem:
    """Get the global event system instance."""
    global _global_event_system

    if _global_event_system is None:
        with _event_system_lock:
            if _global_event_system is None:
                _global_event_system = EventSystem()

    return _global_event_system


def emit_global_event(event_type: EventType, **kwargs) -> Event:
    """
    Emit an event with the global event system.

    Args:
        event_type: Type of event
        **kwargs: Event data

    Returns:
        Created event
    """
    system = get_global_event_system()
    return system.emit_event(event_type, kwargs)


def add_global_listener(event_type: EventType, listener: Callable, **kwargs) -> str:
    """
    Add a listener with the global event system.

    Args:
        event_type: Type of events to listen for
        listener: Listener function
        **kwargs: Additional listener arguments

    Returns:
        Listener ID
    """
    system = get_global_event_system()
    return system.add_listener(event_type, listener, **kwargs)
