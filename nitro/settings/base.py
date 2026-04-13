"""Core settings classes: AppSettings, Section, and Secret."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, ClassVar, Self

from pydantic import BaseModel, Field, GetCoreSchemaHandler, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_core import CoreSchema, core_schema


class Secret(str):
    """A string that masks itself in repr/str for safe logging.

    Wraps a sensitive value so it never leaks into logs or config dumps.

    Usage::

        password = Secret("s3cret")
        str(password)         # '********'
        repr(password)        # "Secret('********')"
        password.get_secret() # 's3cret'
    """

    def __repr__(self) -> str:
        return "Secret('********')" if self else "Secret('')"

    def __str__(self) -> str:
        return "********" if self else ""

    def get_secret(self) -> str:
        """Return the actual secret value."""
        return super().__str__()

    def __bool__(self) -> bool:
        return len(self.get_secret()) > 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Secret):
            return self.get_secret() == other.get_secret()
        if isinstance(other, str):
            return self.get_secret() == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.get_secret())

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: v.get_secret() if isinstance(v, Secret) else str(v),
                info_arg=False,
            ),
        )

    @classmethod
    def _validate(cls, value: Any) -> Secret:
        if isinstance(value, Secret):
            return value
        return cls(str(value))


class Section(BaseModel):
    """A composable configuration section.

    Sections are nested config blocks that group related settings.
    They support defaults and can be overridden by environment variables
    when used inside an AppSettings.

    Usage::

        class CacheSection(Section):
            backend: str = "memory"
            ttl: int = 300
            max_size: int = 1000

        class MySettings(AppSettings):
            cache: CacheSection = CacheSection()
    """

    model_config = {"extra": "ignore"}


class AppSettings(BaseSettings):
    """Base class for application settings with environment profiles.

    Provides:
    - Environment-based profile loading (.env.development, .env.production, etc.)
    - Nested section support via ``__`` separator in env vars
    - Secret masking in dumps
    - Safe display for logging/debugging

    Subclasses should set ``model_config`` with ``env_prefix`` to customize
    the environment variable prefix::

        class MySettings(AppSettings):
            model_config = SettingsConfigDict(
                env_prefix="MY_",
                env_nested_delimiter="__",
                case_sensitive=False,
                extra="ignore",
            )
            debug: bool = False

    Usage::

        settings = MySettings()                  # development defaults
        settings = MySettings(env="production")  # loads .env.production
    """

    # Default prefix — subclasses override via model_config
    _default_prefix: ClassVar[str] = "NITRO_"

    model_config = SettingsConfigDict(
        env_prefix="NITRO_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    env: str = Field(
        default="development",
        description="Active environment profile (development, staging, production)",
    )

    def __init__(self, **kwargs: Any) -> None:
        prefix = self._get_env_prefix()
        env = kwargs.get("env") or os.environ.get(
            f"{prefix}ENV", "development"
        )
        kwargs["env"] = env
        super().__init__(**kwargs)

    @classmethod
    def _get_env_prefix(cls) -> str:
        """Get the env prefix from model_config or default."""
        cfg = cls.model_config
        return cfg.get("env_prefix", cls._default_prefix)

    @model_validator(mode="before")
    @classmethod
    def _load_env_file(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Load profile-specific .env file if it exists."""
        prefix = cls._get_env_prefix()
        env = data.get("env") or os.environ.get(f"{prefix}ENV", "development")

        profile_file = Path(f".env.{env}")
        base_file = Path(".env")

        # Load base .env first, then profile overrides
        # Profile values should win, so we load base with setdefault,
        # then profile with explicit set
        env_values: dict[str, Any] = {}
        if base_file.exists():
            cls._parse_env_file(env_values, base_file, prefix, overwrite=True)
        if profile_file.exists():
            cls._parse_env_file(env_values, profile_file, prefix, overwrite=True)

        # Merge into data — env file values are defaults, init kwargs win
        for key, value in env_values.items():
            if isinstance(value, dict):
                existing = data.get(key)
                if isinstance(existing, dict):
                    # Merge nested — init kwargs win
                    for k, v in value.items():
                        existing.setdefault(k, v)
                else:
                    data.setdefault(key, value)
            else:
                data.setdefault(key, value)

        return data

    @classmethod
    def _parse_env_file(
        cls,
        target: dict[str, Any],
        path: Path,
        prefix: str,
        *,
        overwrite: bool = False,
    ) -> None:
        """Parse a .env file and collect matching prefixed vars."""
        prefix_upper = prefix.upper()
        try:
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                if key.upper().startswith(prefix_upper):
                    field_key = key[len(prefix_upper):].lower()
                    parts = field_key.split("__")
                    if len(parts) == 1:
                        if overwrite:
                            target[parts[0]] = value
                        else:
                            target.setdefault(parts[0], value)
                    else:
                        # Nested: db__url -> {"db": {"url": value}}
                        t = target
                        for part in parts[:-1]:
                            if part not in t or not isinstance(t[part], dict):
                                t[part] = {}
                            t = t[part]
                        if overwrite:
                            t[parts[-1]] = value
                        else:
                            t.setdefault(parts[-1], value)
        except OSError:
            pass

    def dump_safe(self) -> dict[str, Any]:
        """Dump settings with secrets masked.

        Returns a dict safe for logging — Secret values show as '********'.
        """
        return self._mask_secrets(self.model_dump(), self)

    def dump_table(self) -> str:
        """Dump settings as a formatted table string.

        Returns a human-readable table for CLI/log output::

            env         : production
            debug       : False
            db.url      : postgresql://host/db
            db.password : ********
        """
        safe = self.dump_safe()
        lines: list[tuple[str, str]] = []
        self._flatten_dict(safe, lines, prefix="")
        if not lines:
            return "(empty)"
        max_key = max(len(k) for k, _ in lines)
        return "\n".join(f"{k:<{max_key}} : {v}" for k, v in lines)

    @staticmethod
    def _flatten_dict(
        d: dict[str, Any],
        out: list[tuple[str, str]],
        prefix: str,
    ) -> None:
        """Recursively flatten a nested dict into dotted key-value pairs."""
        for key, value in d.items():
            full_key = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
            if isinstance(value, dict):
                AppSettings._flatten_dict(value, out, full_key)
            else:
                out.append((full_key, str(value)))

    @classmethod
    def _mask_secrets(cls, data: dict[str, Any], settings: AppSettings) -> dict[str, Any]:
        """Recursively mask Secret-typed fields in a dict."""
        result = {}
        # Build a set of field names that are Secret-typed
        secret_fields = set()
        for field_name, field_info in type(settings).model_fields.items():
            if field_info.annotation is Secret:
                secret_fields.add(field_name)

        for key, value in data.items():
            if key in secret_fields:
                result[key] = "********"
            elif isinstance(value, dict):
                # For nested sections, try to get the section model
                section = getattr(settings, key, None)
                if isinstance(section, Section):
                    result[key] = cls._mask_section(value, section)
                else:
                    result[key] = value
            else:
                result[key] = value
        return result

    @classmethod
    def _mask_section(cls, data: dict[str, Any], section: Section) -> dict[str, Any]:
        """Mask secrets within a section."""
        result = {}
        secret_fields = set()
        for field_name, field_info in type(section).model_fields.items():
            if field_info.annotation is Secret:
                secret_fields.add(field_name)

        for key, value in data.items():
            if key in secret_fields:
                result[key] = "********"
            elif isinstance(value, dict):
                sub = getattr(section, key, None)
                if isinstance(sub, Section):
                    result[key] = cls._mask_section(value, sub)
                else:
                    result[key] = value
            else:
                result[key] = value
        return result

    def get_section(self, name: str) -> Section | None:
        """Get a named section if it exists."""
        value = getattr(self, name, None)
        return value if isinstance(value, Section) else None

    def override(self, **kwargs: Any) -> Self:
        """Create a copy with overridden values.

        Returns a new settings instance with the specified fields changed::

            prod = settings.override(debug=False, env="production")
        """
        data = self.model_dump()
        data.update(kwargs)
        return self.__class__(**data)
