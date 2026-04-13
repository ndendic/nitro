"""Tests for the scaffold generator — file presence and expected imports."""

import pytest
from nitro.scaffold import ScaffoldConfig, generate_project


class TestMinimalGenerator:
    def test_generates_expected_files(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        assert "main.py" in files
        assert "settings.py" in files
        assert "entities.py" in files
        assert ".env.example" in files

    def test_no_extra_files_in_minimal(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        # Minimal should not contain auth or i18n files
        assert "auth_views.py" not in files
        assert "locales/en.json" not in files

    def test_main_imports_sanic(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        assert "from sanic import Sanic" in files["main.py"]

    def test_main_imports_configure_nitro(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        assert "configure_nitro" in files["main.py"]

    def test_main_imports_health(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        assert "nitro.health" in files["main.py"]

    def test_main_imports_logging(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        assert "nitro.logging" in files["main.py"]

    def test_settings_imports_nitro_settings(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        assert "nitro.settings" in files["settings.py"]
        assert "AppSettings" in files["settings.py"]

    def test_entities_imports_entity(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        assert "from nitro import Entity" in files["entities.py"]

    def test_env_example_has_port(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        assert "PORT" in files[".env.example"].upper()

    def test_project_name_in_main(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        assert "myapp" in files["main.py"]

    def test_returns_dict_of_strings(self):
        config = ScaffoldConfig(name="myapp", template="minimal")
        files = generate_project(config)
        assert isinstance(files, dict)
        for key, value in files.items():
            assert isinstance(key, str)
            assert isinstance(value, str)


class TestAuthGenerator:
    def test_includes_auth_views(self):
        config = ScaffoldConfig(name="myapp", template="auth")
        files = generate_project(config)
        assert "auth_views.py" in files

    def test_main_imports_auth(self):
        config = ScaffoldConfig(name="myapp", template="auth")
        files = generate_project(config)
        assert "nitro.auth" in files["main.py"]

    def test_auth_views_imports_nitro_auth(self):
        config = ScaffoldConfig(name="myapp", template="auth")
        files = generate_project(config)
        assert "nitro.auth" in files["auth_views.py"]

    def test_auth_views_imports_sessions(self):
        config = ScaffoldConfig(name="myapp", template="auth")
        files = generate_project(config)
        assert "nitro.sessions" in files["auth_views.py"]

    def test_auth_includes_settings_and_entities(self):
        config = ScaffoldConfig(name="myapp", template="auth")
        files = generate_project(config)
        assert "settings.py" in files
        assert "entities.py" in files

    def test_no_i18n_in_auth(self):
        config = ScaffoldConfig(name="myapp", template="auth")
        files = generate_project(config)
        assert "locales/en.json" not in files


class TestFullstackGenerator:
    def test_includes_locale_files(self):
        config = ScaffoldConfig(name="myapp", template="fullstack")
        files = generate_project(config)
        assert "locales/en.json" in files
        assert "locales/sr.json" in files

    def test_main_imports_crud(self):
        config = ScaffoldConfig(name="myapp", template="fullstack")
        files = generate_project(config)
        assert "nitro.crud" in files["main.py"]

    def test_main_imports_i18n(self):
        config = ScaffoldConfig(name="myapp", template="fullstack")
        files = generate_project(config)
        assert "nitro.i18n" in files["main.py"]

    def test_fullstack_includes_auth_views(self):
        config = ScaffoldConfig(name="myapp", template="fullstack")
        files = generate_project(config)
        assert "auth_views.py" in files

    def test_locales_are_valid_json(self):
        import json
        config = ScaffoldConfig(name="myapp", template="fullstack")
        files = generate_project(config)
        json.loads(files["locales/en.json"])
        json.loads(files["locales/sr.json"])


class TestTemplatesComposable:
    def test_auth_is_superset_of_minimal(self):
        minimal = generate_project(ScaffoldConfig(name="x", template="minimal"))
        auth = generate_project(ScaffoldConfig(name="x", template="auth"))
        # auth should contain all keys from minimal
        assert set(minimal.keys()).issubset(set(auth.keys()))

    def test_fullstack_is_superset_of_auth(self):
        auth = generate_project(ScaffoldConfig(name="x", template="auth"))
        fullstack = generate_project(ScaffoldConfig(name="x", template="fullstack"))
        assert set(auth.keys()).issubset(set(fullstack.keys()))

    def test_fullstack_is_superset_of_minimal(self):
        minimal = generate_project(ScaffoldConfig(name="x", template="minimal"))
        fullstack = generate_project(ScaffoldConfig(name="x", template="fullstack"))
        assert set(minimal.keys()).issubset(set(fullstack.keys()))
