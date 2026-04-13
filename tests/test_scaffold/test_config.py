"""Tests for ScaffoldConfig validation and template choices."""

import pytest
from nitro.scaffold.config import ScaffoldConfig, TEMPLATE_DESCRIPTIONS


class TestScaffoldConfig:
    def test_minimal_config(self):
        cfg = ScaffoldConfig(name="myapp", template="minimal")
        assert cfg.name == "myapp"
        assert cfg.template == "minimal"

    def test_auth_config(self):
        cfg = ScaffoldConfig(name="myapp", template="auth")
        assert cfg.template == "auth"

    def test_fullstack_config(self):
        cfg = ScaffoldConfig(name="myapp", template="fullstack")
        assert cfg.template == "fullstack"

    def test_default_template_is_minimal(self):
        cfg = ScaffoldConfig(name="myapp")
        assert cfg.template == "minimal"

    def test_default_output_dir(self):
        cfg = ScaffoldConfig(name="myapp")
        assert cfg.output_dir == "."

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="empty"):
            ScaffoldConfig(name="")

    def test_invalid_template_raises(self):
        with pytest.raises(ValueError, match="Unknown template"):
            ScaffoldConfig(name="myapp", template="nonexistent")  # type: ignore[arg-type]

    def test_safe_name_replaces_hyphens(self):
        cfg = ScaffoldConfig(name="my-app")
        assert cfg.safe_name == "my_app"

    def test_safe_name_replaces_spaces(self):
        cfg = ScaffoldConfig(name="my app")
        assert cfg.safe_name == "my_app"

    def test_description_returns_string(self):
        for template in TEMPLATE_DESCRIPTIONS:
            cfg = ScaffoldConfig(name="x", template=template)
            assert isinstance(cfg.description, str)
            assert len(cfg.description) > 0

    def test_all_templates_have_descriptions(self):
        assert "minimal" in TEMPLATE_DESCRIPTIONS
        assert "auth" in TEMPLATE_DESCRIPTIONS
        assert "fullstack" in TEMPLATE_DESCRIPTIONS
