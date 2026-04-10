"""pyproject.toml template for new Nitro projects."""

FRAMEWORK_DEPS = {
    "sanic": "sanic",
    "fastapi": "fastapi[standard]",
}

PYPROJECT_TOML_TEMPLATE = '''\
[project]
name = "{project_name}"
version = "0.1.0"
requires-python = ">= 3.10"
dependencies = [
    "nitro",
    "{framework_dep}",
]

[project.scripts]
dev = "main:app"
'''


def generate_pyproject_toml(project_name: str, framework: str) -> str:
    """Generate a minimal pyproject.toml for the given project and framework.

    Args:
        project_name: The project name (typically the directory name).
        framework: The web framework to use ('sanic' or 'fastapi').

    Returns:
        A string containing the pyproject.toml content.
    """
    framework_dep = FRAMEWORK_DEPS.get(framework, framework)
    return PYPROJECT_TOML_TEMPLATE.format(
        project_name=project_name,
        framework_dep=framework_dep,
    )
