"""Settings registry — singleton access to application settings."""

from __future__ import annotations

import threading
from typing import TypeVar, overload

from .base import AppSettings

T = TypeVar("T", bound=AppSettings)


class SettingsRegistry:
    """Thread-safe registry for application settings instances.

    Provides singleton access to settings from anywhere in the app,
    avoiding global variables or parameter threading.

    Usage::

        from nitro.settings import SettingsRegistry, AppSettings

        class MySettings(AppSettings):
            debug: bool = False

        # At startup
        registry = SettingsRegistry()
        registry.register(MySettings(debug=True))

        # Anywhere else
        settings = registry.get(MySettings)
        assert settings.debug is True

    Multiple settings types can coexist::

        registry.register(DatabaseSettings())
        registry.register(CacheSettings())

        db = registry.get(DatabaseSettings)
        cache = registry.get(CacheSettings)
    """

    _instance: SettingsRegistry | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> SettingsRegistry:
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._settings: dict[type, AppSettings] = {}
                inst._registry_lock = threading.Lock()
                cls._instance = inst
            return cls._instance

    def register(self, settings: AppSettings) -> None:
        """Register a settings instance by its type.

        Overwrites any previously registered instance of the same type.
        """
        with self._registry_lock:
            self._settings[type(settings)] = settings

    @overload
    def get(self, settings_type: type[T]) -> T: ...
    @overload
    def get(self, settings_type: type[T], default: T) -> T: ...

    def get(self, settings_type: type[T], default: T | None = None) -> T | None:
        """Retrieve a registered settings instance by type.

        Raises KeyError if not registered and no default provided.
        """
        with self._registry_lock:
            result = self._settings.get(settings_type)
        if result is not None:
            return result  # type: ignore[return-value]
        if default is not None:
            return default
        raise KeyError(
            f"No settings registered for {settings_type.__name__}. "
            f"Call registry.register({settings_type.__name__}()) first."
        )

    def has(self, settings_type: type[AppSettings]) -> bool:
        """Check if a settings type is registered."""
        with self._registry_lock:
            return settings_type in self._settings

    def unregister(self, settings_type: type[AppSettings]) -> None:
        """Remove a registered settings type."""
        with self._registry_lock:
            self._settings.pop(settings_type, None)

    def clear(self) -> None:
        """Remove all registered settings."""
        with self._registry_lock:
            self._settings.clear()

    def registered_types(self) -> list[type[AppSettings]]:
        """List all registered settings types."""
        with self._registry_lock:
            return list(self._settings.keys())

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton — for testing only."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._settings.clear()
            cls._instance = None
