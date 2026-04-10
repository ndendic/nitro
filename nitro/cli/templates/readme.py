"""README.md template for new Nitro projects."""

README_TEMPLATE = '''\
# {project_name}

Built with [Nitro](https://nitro.systems) — a collection of abstraction layers for Python web development.

## Quick Start

### 1. Install dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or with `pip`:
```bash
pip install -e .
```

### 2. Run the dev server

```bash
python main.py
```

### 3. Watch for CSS changes

In a separate terminal:
```bash
nitro tw dev
```

Your app will be running at [http://localhost:8000](http://localhost:8000).

## Stack

- **Framework:** {framework}
- **Template:** {template}
- **Styling:** Tailwind CSS v4 + BaseCoat

## Learn More

- [Nitro Documentation](https://nitro.systems/docs)
- [Nitro GitHub](https://github.com/nitro-systems/nitro)
'''


def generate_readme(project_name: str, framework: str, template: str) -> str:
    """Generate a project-specific README.md.

    Args:
        project_name: The project name (typically the directory name).
        framework: The web framework used ('sanic' or 'fastapi').
        template: The project template used (e.g. 'blank', 'app').

    Returns:
        A string containing the README.md content.
    """
    return README_TEMPLATE.format(
        project_name=project_name,
        framework=framework,
        template=template,
    )
