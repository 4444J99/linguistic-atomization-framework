"""
Visualization adapters and templates.

Adapters transform analysis output into visual artifacts (HTML, SVG, etc.).
Templates provide the base HTML/CSS/JS for each visualization type.

Built-in adapters:
- force_graph: D3.js force-directed graph for semantic networks
- sankey: Plotly.js Sankey diagram for temporal flow
- sentiment_chart: Chart.js charts for sentiment analysis
- entity_browser: Interactive entity search/filter table
- evaluation_dashboard: Interactive 9-step evaluation dashboard

Cross-linking:
- cross_linking: URL-based navigation between visualizations
"""

from .base import BaseVisualizationAdapter, TemplateEngine
from .adapters.force_graph import ForceGraphAdapter
from .adapters.sankey import SankeyAdapter
from .adapters.sentiment_chart import SentimentChartAdapter
from .adapters.entity_browser import EntityBrowserAdapter
from .adapters.evaluation_dashboard import EvaluationDashboardAdapter
from .cross_linking import CrossVizLinker, inject_cross_linking

__all__ = [
    "BaseVisualizationAdapter",
    "TemplateEngine",
    "ForceGraphAdapter",
    "SankeyAdapter",
    "SentimentChartAdapter",
    "EntityBrowserAdapter",
    "EvaluationDashboardAdapter",
    "CrossVizLinker",
    "inject_cross_linking",
]
