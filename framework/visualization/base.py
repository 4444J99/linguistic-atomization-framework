"""
Base Visualization Classes - Template engine and adapter base class.

Provides common utilities for generating HTML visualizations from templates.
"""

from __future__ import annotations

import json
import re
from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.ontology import AnalysisOutput, VisualizationAdapter


# Lazy import to avoid circular dependency
def _get_cross_linking():
    from .cross_linking import CrossVizLinker
    return CrossVizLinker


class TemplateEngine:
    """
    Simple template engine for generating HTML visualizations.

    Supports:
    - Variable substitution: {{ variable_name }}
    - JSON data injection: {{ DATA:variable_name }}
    - Include statements: {% include "filename.html" %}
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template engine.

        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir or Path(__file__).parent / "templates"

    def load_template(self, template_name: str) -> str:
        """
        Load a template file by name.

        Args:
            template_name: Filename of template

        Returns:
            Template content as string
        """
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def render(
        self,
        template: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Render a template with the given context.

        Args:
            template: Template string (or template name to load)
            context: Dict of variables to substitute

        Returns:
            Rendered HTML string
        """
        # Load template if it's a filename
        if not template.strip().startswith("<") and not "{{" in template:
            template = self.load_template(template)

        # Process includes first
        template = self._process_includes(template)

        # Process JSON data injection
        template = self._process_json_data(template, context)

        # Process simple variable substitution
        template = self._process_variables(template, context)

        return template

    def _process_includes(self, template: str) -> str:
        """Process {% include "filename" %} statements."""
        include_pattern = r'\{%\s*include\s*["\']([^"\']+)["\']\s*%\}'

        def replace_include(match):
            filename = match.group(1)
            try:
                included = self.load_template(filename)
                # Recursively process includes
                return self._process_includes(included)
            except FileNotFoundError:
                return f"<!-- Include not found: {filename} -->"

        return re.sub(include_pattern, replace_include, template)

    def _process_json_data(self, template: str, context: Dict[str, Any]) -> str:
        """Process {{ DATA:variable_name }} for JSON injection."""
        data_pattern = r'\{\{\s*DATA:(\w+)\s*\}\}'

        def replace_data(match):
            var_name = match.group(1)
            if var_name in context:
                return json.dumps(context[var_name], indent=2, ensure_ascii=False)
            return "{}"

        return re.sub(data_pattern, replace_data, template)

    def _process_variables(self, template: str, context: Dict[str, Any]) -> str:
        """Process {{ variable_name }} substitution."""
        var_pattern = r'\{\{\s*(\w+)\s*\}\}'

        def replace_var(match):
            var_name = match.group(1)
            if var_name in context:
                value = context[var_name]
                if isinstance(value, (dict, list)):
                    return json.dumps(value)
                return str(value)
            return ""

        return re.sub(var_pattern, replace_var, template)


class BaseVisualizationAdapter(VisualizationAdapter):
    """
    Base class for visualization adapters.

    Provides common utilities for HTML generation.
    """

    name: str = "base"
    description: str = "Base visualization adapter"
    supported_analysis: List[str] = []

    # Default styling
    DEFAULT_STYLES = {
        "background_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "glass_background": "rgba(255, 255, 255, 0.1)",
        "glass_border": "rgba(255, 255, 255, 0.2)",
        "text_color": "white",
        "accent_color": "#4ECDC4",
    }

    def __init__(self):
        self.engine = TemplateEngine()
        self._config: Dict[str, Any] = {}

    def get_base_css(self) -> str:
        """Return base CSS for glassmorphic styling."""
        return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: %(background_gradient)s;
            min-height: 100vh;
            padding: 20px;
            color: %(text_color)s;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .glass {
            background: %(glass_background)s;
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid %(glass_border)s;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            padding: 30px;
            margin-bottom: 20px;
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            text-align: center;
            opacity: 0.8;
            margin-bottom: 20px;
            font-size: 1.1em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .stat-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
        .stat-label { font-size: 0.9em; opacity: 0.8; }
        button {
            padding: 10px 20px;
            border-radius: 10px;
            border: none;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        button:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
        """ % self.DEFAULT_STYLES

    def wrap_html(
        self,
        title: str,
        content: str,
        scripts: str = "",
        styles: str = "",
        head_extras: str = "",
    ) -> str:
        """
        Wrap content in a complete HTML document.

        Args:
            title: Page title
            content: Main content HTML
            scripts: JavaScript to include
            styles: Additional CSS
            head_extras: Extra content for <head> (e.g., CDN links)

        Returns:
            Complete HTML document
        """
        base_css = self.get_base_css()

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {head_extras}
    <style>
{base_css}
{styles}
    </style>
</head>
<body>
    <div class="container">
{content}
    </div>
    <script>
{scripts}
    </script>
</body>
</html>"""

    @abstractmethod
    def generate(
        self,
        analysis: AnalysisOutput,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Generate visualization artifact."""
        pass
