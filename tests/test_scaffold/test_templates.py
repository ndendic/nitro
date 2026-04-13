"""Tests that verify all generated Python files contain valid syntax."""

import pytest
from nitro.scaffold import ScaffoldConfig, generate_project


TEMPLATES = ["minimal", "auth", "fullstack"]


@pytest.mark.parametrize("template", TEMPLATES)
def test_generated_python_is_valid_syntax(template):
    """compile() raises SyntaxError if any generated .py file is invalid."""
    config = ScaffoldConfig(name="myapp", template=template)
    files = generate_project(config)
    for filename, content in files.items():
        if filename.endswith(".py"):
            try:
                compile(content, filename, "exec")
            except SyntaxError as exc:
                pytest.fail(
                    f"SyntaxError in '{filename}' (template={template}): {exc}"
                )


@pytest.mark.parametrize("template", TEMPLATES)
def test_all_py_files_have_content(template):
    """Every .py file must have non-trivial content (not just whitespace)."""
    config = ScaffoldConfig(name="myapp", template=template)
    files = generate_project(config)
    for filename, content in files.items():
        if filename.endswith(".py"):
            assert content.strip(), f"'{filename}' is empty (template={template})"


@pytest.mark.parametrize("template", TEMPLATES)
def test_main_py_has_sanic_app_definition(template):
    """main.py should always declare a Sanic app."""
    config = ScaffoldConfig(name="myapp", template=template)
    files = generate_project(config)
    assert "Sanic(" in files["main.py"], (
        f"main.py (template={template}) does not create a Sanic app"
    )


@pytest.mark.parametrize("template", TEMPLATES)
def test_main_py_has_entrypoint(template):
    """main.py should have an if __name__ == '__main__' guard."""
    config = ScaffoldConfig(name="myapp", template=template)
    files = generate_project(config)
    assert '__name__' in files["main.py"], (
        f"main.py (template={template}) has no __name__ guard"
    )


def test_entities_py_defines_item_class():
    config = ScaffoldConfig(name="myapp", template="minimal")
    files = generate_project(config)
    assert "class Item" in files["entities.py"]


def test_entities_py_defines_data_init():
    config = ScaffoldConfig(name="myapp", template="minimal")
    files = generate_project(config)
    assert "def data_init" in files["entities.py"]


def test_settings_py_defines_appconfig():
    config = ScaffoldConfig(name="myapp", template="minimal")
    files = generate_project(config)
    assert "class AppConfig" in files["settings.py"]


def test_auth_views_defines_register_auth():
    config = ScaffoldConfig(name="myapp", template="auth")
    files = generate_project(config)
    assert "def register_auth" in files["auth_views.py"]


def test_locales_en_has_required_keys():
    import json
    config = ScaffoldConfig(name="myapp", template="fullstack")
    files = generate_project(config)
    catalog = json.loads(files["locales/en.json"])
    assert "nav.home" in catalog
    assert "auth.login" in catalog


def test_locales_sr_has_required_keys():
    import json
    config = ScaffoldConfig(name="myapp", template="fullstack")
    files = generate_project(config)
    catalog = json.loads(files["locales/sr.json"])
    assert "nav.home" in catalog
    assert "auth.login" in catalog
