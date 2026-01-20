"""
Jupyter Notebook Templates for LingFrame.

Provides interactive notebooks for:
- exploration: Browse and search the atomized corpus
- evaluation: Run 9-step rhetorical analysis interactively
- visualization: Generate and customize visualizations
"""

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

AVAILABLE_TEMPLATES = [
    "exploration.ipynb",
    "evaluation.ipynb",
    "visualization.ipynb",
]


def get_template_path(name: str) -> Path:
    """Get path to a notebook template."""
    if not name.endswith(".ipynb"):
        name = f"{name}.ipynb"

    template_path = TEMPLATES_DIR / name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {name}")

    return template_path


def list_templates() -> list[str]:
    """List available notebook templates."""
    return AVAILABLE_TEMPLATES


__all__ = [
    "TEMPLATES_DIR",
    "AVAILABLE_TEMPLATES",
    "get_template_path",
    "list_templates",
]
