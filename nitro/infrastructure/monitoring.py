"""
Monitoring infrastructure for Nitro.

Provides logging, statistics collection, and metrics for:
- Entity operations
- Repository operations
- Event bus activity
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from threading import Lock


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def configure_nitro_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for Nitro.

    Args:
        level: Logging level (logging.DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance

    Example:
        >>> from nitro.infrastructure.monitoring import configure_nitro_logging
        >>> import logging
        >>> logger = configure_nitro_logging(logging.DEBUG)
        >>> logger.info("Nitro initialized")
    """
    logger = logging.getLogger("nitro")
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler with formatting
    handler = logging.StreamHandler()
    handler.setLevel(level)

    # Format: [timestamp] [level] [component] message
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


# Get or create the nitro logger
nitro_logger = logging.getLogger("nitro")


# ============================================================================
# REPOSITORY STATISTICS
# ============================================================================

@dataclass
class RepositoryStats:
    """Statistics for repository operations."""
    queries_executed: int = 0
    saves: int = 0
    deletes: int = 0
    gets: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_query_time: float = 0.0

    def record_save(self):
        """Record a save operation."""
        self.saves += 1
        self.queries_executed += 1

    def record_delete(self):
        """Record a delete operation."""
        self.deletes += 1
        self.queries_executed += 1

    def record_get(self, cache_hit: bool = False):
        """Record a get operation."""
        self.gets += 1
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            self.queries_executed += 1

    def record_query(self, execution_time: float):
        """Record a query with its execution time."""
        self.queries_executed += 1
        self.total_query_time += execution_time

    @property
    def avg_query_time(self) -> float:
        """Average query execution time."""
        if self.queries_executed == 0:
            return 0.0
        return self.total_query_time / self.queries_executed

    @property
    def cache_hit_ratio(self) -> float:
        """Cache hit ratio (0.0 to 1.0)."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "queries_executed": self.queries_executed,
            "saves": self.saves,
            "deletes": self.deletes,
            "gets": self.gets,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_query_time": self.total_query_time,
            "avg_query_time": self.avg_query_time,
            "cache_hit_ratio": self.cache_hit_ratio,
        }


class RepositoryMonitor:
    """Monitor for repository statistics."""

    def __init__(self):
        self._stats: Dict[str, RepositoryStats] = {}
        self._lock = Lock()
        self._enabled = False

    def enable(self):
        """Enable statistics collection."""
        self._enabled = True
        nitro_logger.info("Repository monitoring enabled")

    def disable(self):
        """Disable statistics collection."""
        self._enabled = False
        nitro_logger.info("Repository monitoring disabled")

    def get_stats(self, entity_class: str) -> RepositoryStats:
        """Get stats for an entity class."""
        with self._lock:
            if entity_class not in self._stats:
                self._stats[entity_class] = RepositoryStats()
            return self._stats[entity_class]

    def record_save(self, entity_class: str):
        """Record a save operation."""
        if not self._enabled:
            return
        with self._lock:
            self.get_stats(entity_class).record_save()
            nitro_logger.debug(f"Repository: {entity_class}.save()")

    def record_delete(self, entity_class: str):
        """Record a delete operation."""
        if not self._enabled:
            return
        with self._lock:
            self.get_stats(entity_class).record_delete()
            nitro_logger.debug(f"Repository: {entity_class}.delete()")

    def record_get(self, entity_class: str, cache_hit: bool = False):
        """Record a get operation."""
        if not self._enabled:
            return
        with self._lock:
            self.get_stats(entity_class).record_get(cache_hit)
            nitro_logger.debug(f"Repository: {entity_class}.get() [cache_hit={cache_hit}]")

    def record_query(self, entity_class: str, execution_time: float):
        """Record a query operation."""
        if not self._enabled:
            return
        with self._lock:
            self.get_stats(entity_class).record_query(execution_time)
            nitro_logger.debug(f"Repository: {entity_class} query took {execution_time:.4f}s")

    def all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get all statistics."""
        with self._lock:
            return {
                entity_class: stats.to_dict()
                for entity_class, stats in self._stats.items()
            }

    def reset(self):
        """Reset all statistics."""
        with self._lock:
            self._stats.clear()
            nitro_logger.info("Repository stats reset")


# Global repository monitor instance
repository_monitor = RepositoryMonitor()


# ============================================================================
# EVENT BUS METRICS
# ============================================================================

@dataclass
class EventMetrics:
    """Metrics for event bus activity."""
    events_fired: int = 0
    handlers_executed: int = 0
    total_handler_time: float = 0.0
    errors: int = 0

    @property
    def avg_handler_time(self) -> float:
        """Average handler execution time."""
        if self.handlers_executed == 0:
            return 0.0
        return self.total_handler_time / self.handlers_executed

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "events_fired": self.events_fired,
            "handlers_executed": self.handlers_executed,
            "total_handler_time": self.total_handler_time,
            "avg_handler_time": self.avg_handler_time,
            "errors": self.errors,
        }


class EventBusMonitor:
    """Monitor for event bus metrics."""

    def __init__(self):
        self._metrics: Dict[str, EventMetrics] = {}
        self._lock = Lock()
        self._enabled = False

    def enable(self):
        """Enable event metrics collection."""
        self._enabled = True
        nitro_logger.info("Event bus monitoring enabled")

    def disable(self):
        """Disable event metrics collection."""
        self._enabled = False
        nitro_logger.info("Event bus monitoring disabled")

    def get_metrics(self, event_name: str) -> EventMetrics:
        """Get metrics for an event."""
        with self._lock:
            if event_name not in self._metrics:
                self._metrics[event_name] = EventMetrics()
            return self._metrics[event_name]

    def record_event_fired(self, event_name: str):
        """Record an event being fired."""
        if not self._enabled:
            return
        with self._lock:
            self.get_metrics(event_name).events_fired += 1
            nitro_logger.debug(f"Event fired: {event_name}")

    def record_handler_executed(self, event_name: str, execution_time: float, error: bool = False):
        """Record a handler execution."""
        if not self._enabled:
            return
        with self._lock:
            metrics = self.get_metrics(event_name)
            metrics.handlers_executed += 1
            metrics.total_handler_time += execution_time
            if error:
                metrics.errors += 1
            nitro_logger.debug(f"Event handler: {event_name} took {execution_time:.4f}s [error={error}]")

    def all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all metrics."""
        with self._lock:
            return {
                event_name: metrics.to_dict()
                for event_name, metrics in self._metrics.items()
            }

    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            nitro_logger.info("Event bus metrics reset")


# Global event bus monitor instance
event_bus_monitor = EventBusMonitor()


# ============================================================================
# ENTITY OPERATION LOGGING
# ============================================================================

def log_entity_operation(entity_class: str, operation: str, entity_id: Optional[str] = None, **kwargs):
    """
    Log an entity operation.

    Args:
        entity_class: Name of the entity class
        operation: Operation name (save, delete, get, etc.)
        entity_id: Optional entity ID
        **kwargs: Additional context to log
    """
    context = f" [{', '.join(f'{k}={v}' for k, v in kwargs.items())}]" if kwargs else ""
    id_part = f"(id={entity_id})" if entity_id else ""
    nitro_logger.info(f"Entity: {entity_class}.{operation}{id_part}{context}")
