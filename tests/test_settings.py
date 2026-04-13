"""Tests for nitro.settings — composable app configuration with profiles."""

import os
import threading
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic_settings import SettingsConfigDict

from nitro.settings import (
    AppSettings,
    Secret,
    Section,
    SettingsRegistry,
    configure_settings,
    cross_validate,
    validate_range,
    validate_url,
)


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset the singleton registry between tests."""
    SettingsRegistry.reset()
    yield
    SettingsRegistry.reset()


@pytest.fixture
def tmp_env(tmp_path, monkeypatch):
    """Helper to write .env files and run from tmp_path."""
    monkeypatch.chdir(tmp_path)

    def write(filename: str, content: str) -> Path:
        p = tmp_path / filename
        p.write_text(content)
        return p

    return write


# ── Secret ────────────────────────────────────────────────────────────────


class TestSecret:
    def test_masks_in_str(self):
        s = Secret("my-password")
        assert str(s) == "********"

    def test_masks_in_repr(self):
        s = Secret("my-password")
        assert repr(s) == "Secret('********')"

    def test_get_secret_returns_value(self):
        s = Secret("my-password")
        assert s.get_secret() == "my-password"

    def test_empty_secret(self):
        s = Secret("")
        assert str(s) == ""
        assert repr(s) == "Secret('')"
        assert not s

    def test_bool_truthy(self):
        assert Secret("x")
        assert not Secret("")

    def test_equality(self):
        assert Secret("abc") == Secret("abc")
        assert Secret("abc") != Secret("xyz")
        assert Secret("abc") == "abc"
        assert Secret("abc") != "xyz"

    def test_hash(self):
        s1 = Secret("abc")
        s2 = Secret("abc")
        assert hash(s1) == hash(s2)
        assert {s1, s2} == {s1}


# ── Section ───────────────────────────────────────────────────────────────


class TestSection:
    def test_basic_section(self):
        class CacheSection(Section):
            backend: str = "memory"
            ttl: int = 300

        s = CacheSection()
        assert s.backend == "memory"
        assert s.ttl == 300

    def test_section_override(self):
        class CacheSection(Section):
            backend: str = "memory"

        s = CacheSection(backend="redis")
        assert s.backend == "redis"

    def test_section_ignores_extra(self):
        class CacheSection(Section):
            backend: str = "memory"

        s = CacheSection(backend="redis", unknown_field="ignored")
        assert s.backend == "redis"


# ── AppSettings ───────────────────────────────────────────────────────────


class TestAppSettings:
    def test_defaults(self):
        class MySettings(AppSettings):
            debug: bool = False
            port: int = 8000

        s = MySettings()
        assert s.debug is False
        assert s.port == 8000
        assert s.env == "development"

    def test_explicit_env(self):
        class MySettings(AppSettings):
            debug: bool = False

        s = MySettings(env="production")
        assert s.env == "production"

    def test_env_from_environment(self, monkeypatch):
        monkeypatch.setenv("NITRO_ENV", "staging")

        class MySettings(AppSettings):
            debug: bool = False

        s = MySettings()
        assert s.env == "staging"

    def test_nested_section(self):
        class DbSection(Section):
            url: str = "sqlite:///app.db"
            pool_size: int = 5

        class MySettings(AppSettings):
            db: DbSection = DbSection()

        s = MySettings()
        assert s.db.url == "sqlite:///app.db"
        assert s.db.pool_size == 5

    def test_nested_override(self):
        class DbSection(Section):
            url: str = "sqlite:///app.db"

        class MySettings(AppSettings):
            db: DbSection = DbSection()

        s = MySettings(db={"url": "postgresql://host/db"})
        assert s.db.url == "postgresql://host/db"

    def test_custom_prefix(self, monkeypatch):
        monkeypatch.setenv("APP_PORT", "9000")

        class MySettings(AppSettings):
            model_config = SettingsConfigDict(
                env_prefix="APP_",
                env_nested_delimiter="__",
                case_sensitive=False,
                extra="ignore",
            )
            port: int = 8000

        s = MySettings()
        assert s.port == 9000

    def test_env_nested_delimiter(self, monkeypatch):
        monkeypatch.setenv("NITRO_DB__URL", "postgresql://test/db")

        class DbSection(Section):
            url: str = "sqlite:///app.db"

        class MySettings(AppSettings):
            db: DbSection = DbSection()

        s = MySettings()
        assert s.db.url == "postgresql://test/db"


class TestAppSettingsEnvFile:
    def test_loads_base_env_file(self, tmp_env):
        tmp_env(".env", "NITRO_PORT=9999\n")

        class MySettings(AppSettings):
            port: int = 8000

        s = MySettings()
        assert s.port == 9999

    def test_loads_profile_env_file(self, tmp_env):
        tmp_env(".env.production", "NITRO_PORT=4000\n")

        class MySettings(AppSettings):
            port: int = 8000

        s = MySettings(env="production")
        assert s.port == 4000

    def test_profile_overrides_base(self, tmp_env):
        tmp_env(".env", "NITRO_PORT=9000\n")
        tmp_env(".env.production", "NITRO_PORT=4000\n")

        class MySettings(AppSettings):
            port: int = 8000

        s = MySettings(env="production")
        assert s.port == 4000

    def test_skips_comments_and_blanks(self, tmp_env):
        tmp_env(".env", "# comment\n\nNITRO_PORT=7777\n")

        class MySettings(AppSettings):
            port: int = 8000

        s = MySettings()
        assert s.port == 7777

    def test_strips_quotes(self, tmp_env):
        tmp_env(".env", 'NITRO_NAME="hello world"\n')

        class MySettings(AppSettings):
            name: str = "default"

        s = MySettings()
        assert s.name == "hello world"

    def test_nested_keys_in_env_file(self, tmp_env):
        tmp_env(".env", "NITRO_DB__URL=postgres://file/db\n")

        class DbSection(Section):
            url: str = "sqlite:///app.db"

        class MySettings(AppSettings):
            db: DbSection = DbSection()

        s = MySettings()
        assert s.db.url == "postgres://file/db"

    def test_missing_env_file_is_ok(self, tmp_env):
        # No .env file exists — should use defaults
        class MySettings(AppSettings):
            port: int = 8000

        s = MySettings()
        assert s.port == 8000


class TestDumpSafe:
    def test_masks_secrets(self):
        class MySettings(AppSettings):
            api_key: Secret = Secret("real-key")
            debug: bool = True

        s = MySettings()
        safe = s.dump_safe()
        assert safe["debug"] is True
        # The secret should not leak
        assert "real-key" not in str(safe)

    def test_dump_table(self):
        class MySettings(AppSettings):
            debug: bool = True
            port: int = 8000

        s = MySettings()
        table = s.dump_table()
        assert "debug" in table
        assert "True" in table
        assert "port" in table
        assert "8000" in table

    def test_nested_dump_table(self):
        class DbSection(Section):
            url: str = "sqlite:///app.db"

        class MySettings(AppSettings):
            db: DbSection = DbSection()

        s = MySettings()
        table = s.dump_table()
        assert "db.url" in table


class TestOverride:
    def test_override_creates_new_instance(self):
        class MySettings(AppSettings):
            debug: bool = False
            port: int = 8000

        original = MySettings()
        copy = original.override(debug=True)
        assert copy.debug is True
        assert original.debug is False
        assert copy.port == 8000

    def test_override_preserves_type(self):
        class MySettings(AppSettings):
            debug: bool = False

        s = MySettings()
        copy = s.override(debug=True)
        assert isinstance(copy, MySettings)


class TestGetSection:
    def test_returns_section(self):
        class DbSection(Section):
            url: str = "sqlite:///app.db"

        class MySettings(AppSettings):
            db: DbSection = DbSection()

        s = MySettings()
        section = s.get_section("db")
        assert section is not None
        assert section.url == "sqlite:///app.db"

    def test_returns_none_for_non_section(self):
        class MySettings(AppSettings):
            debug: bool = False

        s = MySettings()
        assert s.get_section("debug") is None

    def test_returns_none_for_missing(self):
        class MySettings(AppSettings):
            debug: bool = False

        s = MySettings()
        assert s.get_section("nonexistent") is None


# ── SettingsRegistry ──────────────────────────────────────────────────────


class TestSettingsRegistry:
    def test_singleton(self):
        r1 = SettingsRegistry()
        r2 = SettingsRegistry()
        assert r1 is r2

    def test_register_and_get(self):
        class MySettings(AppSettings):
            debug: bool = True

        registry = SettingsRegistry()
        settings = MySettings()
        registry.register(settings)
        assert registry.get(MySettings) is settings

    def test_get_missing_raises(self):
        class MySettings(AppSettings):
            debug: bool = False

        registry = SettingsRegistry()
        with pytest.raises(KeyError, match="No settings registered"):
            registry.get(MySettings)

    def test_get_with_default(self):
        class MySettings(AppSettings):
            debug: bool = False

        registry = SettingsRegistry()
        default = MySettings()
        result = registry.get(MySettings, default)
        assert result is default

    def test_has(self):
        class MySettings(AppSettings):
            debug: bool = False

        registry = SettingsRegistry()
        assert not registry.has(MySettings)
        registry.register(MySettings())
        assert registry.has(MySettings)

    def test_unregister(self):
        class MySettings(AppSettings):
            debug: bool = False

        registry = SettingsRegistry()
        registry.register(MySettings())
        registry.unregister(MySettings)
        assert not registry.has(MySettings)

    def test_clear(self):
        class MySettings(AppSettings):
            debug: bool = False

        registry = SettingsRegistry()
        registry.register(MySettings())
        registry.clear()
        assert registry.registered_types() == []

    def test_multiple_types(self):
        class SettingsA(AppSettings):
            a: int = 1

        class SettingsB(AppSettings):
            b: int = 2

        registry = SettingsRegistry()
        sa = SettingsA()
        sb = SettingsB()
        registry.register(sa)
        registry.register(sb)
        assert registry.get(SettingsA) is sa
        assert registry.get(SettingsB) is sb

    def test_overwrite(self):
        class MySettings(AppSettings):
            debug: bool = False

        registry = SettingsRegistry()
        s1 = MySettings()
        s2 = MySettings(debug=True)
        registry.register(s1)
        registry.register(s2)
        assert registry.get(MySettings) is s2

    def test_thread_safety(self):
        class MySettings(AppSettings):
            debug: bool = False

        registry = SettingsRegistry()
        errors = []

        def register_and_get():
            try:
                s = MySettings()
                registry.register(s)
                result = registry.get(MySettings)
                assert isinstance(result, MySettings)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=register_and_get) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors


# ── Validators ────────────────────────────────────────────────────────────


class TestValidateRange:
    def test_valid_range(self):
        assert validate_range(5, min_val=1, max_val=10) == 5

    def test_below_min(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            validate_range(0, min_val=1, name="port")

    def test_above_max(self):
        with pytest.raises(ValueError, match="must be <= 100"):
            validate_range(200, max_val=100, name="size")

    def test_no_bounds(self):
        assert validate_range(999) == 999

    def test_boundary_values(self):
        assert validate_range(1, min_val=1) == 1
        assert validate_range(10, max_val=10) == 10


class TestValidateUrl:
    def test_valid_url(self):
        assert validate_url("https://example.com") == "https://example.com"

    def test_valid_db_url(self):
        assert (
            validate_url("postgresql://host/db", schemes=("postgresql",))
            == "postgresql://host/db"
        )

    def test_sqlite_url(self):
        assert validate_url("sqlite:///app.db") == "sqlite:///app.db"

    def test_no_scheme(self):
        with pytest.raises(ValueError, match="must have a scheme"):
            validate_url("example.com")

    def test_disallowed_scheme(self):
        with pytest.raises(ValueError, match="scheme must be one of"):
            validate_url("ftp://host/file", schemes=("http", "https"))

    def test_empty_schemes_allows_all(self):
        assert validate_url("ftp://host/file", schemes=()) == "ftp://host/file"


class TestCrossValidate:
    def test_passing_rule(self):
        validator = cross_validate(
            "min_val",
            "max_val",
            rule=lambda min_val, max_val: min_val <= max_val,
            message="min must be <= max",
        )

        class FakeObj:
            min_val = 1
            max_val = 10

        result = validator(FakeObj())
        assert result is not None

    def test_failing_rule(self):
        validator = cross_validate(
            "min_val",
            "max_val",
            rule=lambda min_val, max_val: min_val <= max_val,
            message="min must be <= max",
        )

        class FakeObj:
            min_val = 20
            max_val = 10

        with pytest.raises(ValueError, match="min must be <= max"):
            validator(FakeObj())


# ── Integration ───────────────────────────────────────────────────────────


class TestConfigureSettings:
    def test_sanic_like_app(self):
        class FakeCtx:
            pass

        class FakeApp:
            ctx = FakeCtx()

        class MySettings(AppSettings):
            debug: bool = True

        app = FakeApp()
        settings = configure_settings(app, MySettings)
        assert app.ctx.settings is settings
        assert settings.debug is True

    def test_starlette_like_app(self):
        class FakeState:
            pass

        class FakeApp:
            state = FakeState()

        class MySettings(AppSettings):
            port: int = 9000

        app = FakeApp()
        settings = configure_settings(app, MySettings)
        assert app.state.settings is settings

    def test_generic_app(self):
        class FakeApp:
            pass

        class MySettings(AppSettings):
            port: int = 9000

        app = FakeApp()
        settings = configure_settings(app, MySettings)
        assert app.settings is settings  # type: ignore[attr-defined]

    def test_registers_in_global_registry(self):
        class FakeCtx:
            pass

        class FakeApp:
            ctx = FakeCtx()

        class MySettings(AppSettings):
            debug: bool = True

        app = FakeApp()
        configure_settings(app, MySettings)
        registry = SettingsRegistry()
        assert registry.has(MySettings)

    def test_kwargs_passed_through(self):
        class FakeCtx:
            pass

        class FakeApp:
            ctx = FakeCtx()

        class MySettings(AppSettings):
            debug: bool = False

        app = FakeApp()
        settings = configure_settings(app, MySettings, debug=True)
        assert settings.debug is True


# ── End-to-End ────────────────────────────────────────────────────────────


class TestEndToEnd:
    def test_full_workflow(self, tmp_env):
        tmp_env(
            ".env.production",
            "NITRO_DEBUG=false\n"
            "NITRO_DB__URL=postgresql://prod/db\n"
            "NITRO_DB__POOL_SIZE=20\n",
        )

        class DbSection(Section):
            url: str = "sqlite:///app.db"
            pool_size: int = 5
            password: Secret = Secret("")

        class MySettings(AppSettings):
            debug: bool = True
            db: DbSection = DbSection()

        # Development defaults
        dev = MySettings()
        assert dev.debug is True
        assert dev.db.url == "sqlite:///app.db"
        assert dev.db.pool_size == 5

        # Production from env file
        prod = MySettings(env="production")
        assert prod.debug is False
        assert prod.db.url == "postgresql://prod/db"
        assert prod.db.pool_size == 20

        # Safe dump
        safe = prod.dump_safe()
        assert "postgresql://prod/db" in str(safe)

        # Override
        staging = prod.override(env="staging", debug=True)
        assert staging.env == "staging"
        assert staging.debug is True

        # Registry
        registry = SettingsRegistry()
        registry.register(prod)
        retrieved = registry.get(MySettings)
        assert retrieved.env == "production"

    def test_secret_never_leaks(self):
        class MySettings(AppSettings):
            api_key: Secret = Secret("super-secret-key")

        s = MySettings()

        # Check all output forms
        safe = s.dump_safe()
        table = s.dump_table()

        assert "super-secret-key" not in str(safe)
        assert "super-secret-key" not in table
        assert "super-secret-key" not in repr(s.api_key)
        assert "super-secret-key" not in str(s.api_key)

        # But the value IS accessible intentionally
        assert s.api_key.get_secret() == "super-secret-key"
