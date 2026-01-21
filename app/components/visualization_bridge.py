"""
Visualization Bridge - Connects framework visualization adapters to Streamlit.

Provides embeddable HTML visualizations for the Streamlit app by:
1. Converting dict analysis results to AnalysisOutput objects
2. Generating HTML that works within st.components.v1.html() iframes
3. Mapping adapter types to user-friendly names
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sys

# Ensure framework is in path
framework_root = Path(__file__).resolve().parent.parent.parent
if str(framework_root) not in sys.path:
    sys.path.insert(0, str(framework_root))


# Friendly names for visualizations
VISUALIZATION_INFO = {
    "force_graph": {
        "name": "Theme Connections",
        "icon": "🔗",
        "description": "Discover how your themes and ideas connect through an interactive network. Drag nodes to explore relationships.",
        "analysis_type": "semantic",
    },
    "sentiment_chart": {
        "name": "Emotional Journey",
        "icon": "💓",
        "description": "See how emotions flow through your writing. Identify peaks of intensity and flat spots.",
        "analysis_type": "sentiment",
    },
    "sankey": {
        "name": "Narrative Timeline",
        "icon": "⏰",
        "description": "Visualize how your narrative moves through time - past, present, and future.",
        "analysis_type": "temporal",
    },
    "entity_browser": {
        "name": "People, Places & Things",
        "icon": "🔍",
        "description": "Browse and search all the named entities in your writing - people, locations, organizations, and more.",
        "analysis_type": "entity",
    },
    "evaluation_dashboard": {
        "name": "Heuristic Analysis Dashboard",
        "icon": "📊",
        "description": "9-step heuristic analysis showing pattern-based indicators across Evaluation, Reinforcement, Risk, and Growth phases.",
        "analysis_type": "evaluation",
    },
}


def get_available_visualizations(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get list of available visualizations based on analysis results.

    Args:
        results: Analysis results dict from analysis_engine.run_analysis()

    Returns:
        List of visualization info dicts with name, icon, description, and adapter_type
    """
    available = []

    # Map analysis types to their presence in results
    analysis_available = {
        "semantic": "semantic" in results and bool(results["semantic"]),
        "sentiment": "sentiment" in results and bool(results["sentiment"]),
        "temporal": "temporal" in results and bool(results["temporal"]),
        "entity": "entity" in results and bool(results["entity"]),
        "evaluation": "evaluation" in results and bool(results["evaluation"]),
    }

    for adapter_type, info in VISUALIZATION_INFO.items():
        analysis_type = info["analysis_type"]
        if analysis_available.get(analysis_type, False):
            available.append({
                "adapter_type": adapter_type,
                "name": info["name"],
                "icon": info["icon"],
                "description": info["description"],
            })

    return available


def generate_embeddable_html(
    adapter_type: str,
    analysis_data: Dict[str, Any],
    height: int = 600,
    title: Optional[str] = None,
) -> Tuple[str, bool]:
    """
    Generate embeddable HTML for Streamlit st.components.v1.html().

    Args:
        adapter_type: Type of visualization adapter (force_graph, sankey, etc.)
        analysis_data: Raw analysis data dict
        height: Height in pixels for the visualization
        title: Optional title override

    Returns:
        Tuple of (html_content, success_bool)
    """
    try:
        from framework.core.ontology import AnalysisOutput
        from framework.visualization.adapters import (
            ForceGraphAdapter,
            SankeyAdapter,
            SentimentChartAdapter,
            EntityBrowserAdapter,
            EvaluationDashboardAdapter,
        )

        # Map adapter types to classes
        ADAPTER_MAP = {
            "force_graph": ForceGraphAdapter,
            "sankey": SankeyAdapter,
            "sentiment_chart": SentimentChartAdapter,
            "entity_browser": EntityBrowserAdapter,
            "evaluation_dashboard": EvaluationDashboardAdapter,
        }

        if adapter_type not in ADAPTER_MAP:
            return f"<p>Unknown adapter type: {adapter_type}</p>", False

        # Create adapter instance
        adapter_class = ADAPTER_MAP[adapter_type]
        adapter = adapter_class()

        # Convert dict to AnalysisOutput
        analysis_output = AnalysisOutput(
            module_name=adapter_type,
            data=analysis_data,
            metadata={},
        )

        # Generate to temp file (adapters require file output)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = Path(f.name)

        # Generate visualization
        config = {}
        if title:
            config["title"] = title

        adapter.generate(analysis_output, temp_path, config)

        # Read generated HTML
        with open(temp_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Clean up temp file
        temp_path.unlink()

        # Modify HTML for iframe embedding
        html_content = _adapt_for_iframe(html_content, height)

        return html_content, True

    except Exception as e:
        import traceback
        error_html = f"""
        <div style="padding: 20px; background: #ffebee; color: #c62828; border-radius: 8px;">
            <h3>Visualization Error</h3>
            <p>{str(e)}</p>
            <pre style="font-size: 0.8em; overflow-x: auto;">{traceback.format_exc()}</pre>
        </div>
        """
        return error_html, False


def _adapt_for_iframe(html: str, height: int) -> str:
    """
    Adapt full HTML document for iframe embedding.

    - Ensures body has no margin/padding overflow
    - Sets explicit height for proper iframe display
    """
    # Add meta viewport for better mobile support and height constraint
    style_inject = f"""
    <style>
        html, body {{
            height: 100%;
            overflow: auto;
        }}
        .container {{
            max-height: {height - 40}px;
            overflow-y: auto;
        }}
    </style>
    """

    # Insert style after opening head tag
    if "<head>" in html:
        html = html.replace("<head>", f"<head>\n{style_inject}")
    elif "<HEAD>" in html:
        html = html.replace("<HEAD>", f"<HEAD>\n{style_inject}")

    return html


def generate_placeholder_html(
    vis_type: str,
    message: str = "Analysis not available",
    height: int = 200,
) -> str:
    """
    Generate placeholder HTML when visualization data is not available.

    Args:
        vis_type: Type of visualization (for icon/name)
        message: Message to display
        height: Height in pixels

    Returns:
        Placeholder HTML
    """
    info = VISUALIZATION_INFO.get(vis_type, {"icon": "📊", "name": vis_type})

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: {height - 40}px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
            }}
            .placeholder {{
                text-align: center;
                padding: 40px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }}
            .icon {{ font-size: 3em; margin-bottom: 15px; }}
            .title {{ font-size: 1.3em; font-weight: bold; margin-bottom: 10px; }}
            .message {{ opacity: 0.8; }}
        </style>
    </head>
    <body>
        <div class="placeholder">
            <div class="icon">{info['icon']}</div>
            <div class="title">{info['name']}</div>
            <div class="message">{message}</div>
        </div>
    </body>
    </html>
    """


def get_semantic_data_for_visualization(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and format semantic analysis data for force graph."""
    semantic = results.get("semantic", {})
    if not semantic:
        return {}

    return {
        "nodes": semantic.get("nodes", []),
        "edges": semantic.get("edges", []),
        "themes": semantic.get("themes", []),
    }


def get_sentiment_data_for_visualization(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and format sentiment analysis data for chart."""
    sentiment = results.get("sentiment", {})
    if not sentiment:
        return {}

    return {
        "sentence_sentiments": sentiment.get("sentence_sentiments", []),
        "theme_statistics": sentiment.get("theme_statistics", {}),
        "overall_statistics": sentiment.get("overall", {}),
        "emotional_peaks": sentiment.get("emotional_peaks", {"most_positive": [], "most_negative": []}),
    }


def get_temporal_data_for_visualization(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and format temporal analysis data for sankey diagram."""
    temporal = results.get("temporal", {})
    if not temporal:
        return {}

    return {
        "sankey_data": temporal.get("sankey_data", {"nodes": [], "links": []}),
        "overall_statistics": temporal.get("overall_statistics", {}),
    }


def get_entity_data_for_visualization(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and format entity analysis data for browser."""
    entity = results.get("entity", {})
    if not entity:
        return {}

    return {
        "entity_statistics": entity.get("entity_statistics", {}),
        "enhanced_atomized": entity.get("enhanced_atomized", {}),
    }


def get_evaluation_data_for_visualization(results: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and format evaluation analysis data for dashboard."""
    evaluation = results.get("evaluation", {})
    if not evaluation:
        return {}

    return evaluation  # Evaluation data is already in the right format


# Mapping of adapter types to data extraction functions
DATA_EXTRACTORS = {
    "force_graph": get_semantic_data_for_visualization,
    "sentiment_chart": get_sentiment_data_for_visualization,
    "sankey": get_temporal_data_for_visualization,
    "entity_browser": get_entity_data_for_visualization,
    "evaluation_dashboard": get_evaluation_data_for_visualization,
}


def render_visualization(
    adapter_type: str,
    results: Dict[str, Any],
    height: int = 600,
    title: Optional[str] = None,
) -> Tuple[str, bool]:
    """
    High-level function to render a visualization from analysis results.

    Args:
        adapter_type: Type of visualization adapter
        results: Full analysis results dict
        height: Height in pixels
        title: Optional title override

    Returns:
        Tuple of (html_content, success_bool)
    """
    # Get the appropriate data extractor
    extractor = DATA_EXTRACTORS.get(adapter_type)
    if not extractor:
        return generate_placeholder_html(
            adapter_type,
            f"No data extractor for {adapter_type}",
            height
        ), False

    # Extract visualization-specific data
    vis_data = extractor(results)
    if not vis_data:
        info = VISUALIZATION_INFO.get(adapter_type, {"name": adapter_type})
        return generate_placeholder_html(
            adapter_type,
            f"Run {info['name'].lower()} analysis to see this visualization",
            height
        ), False

    # Generate the visualization
    return generate_embeddable_html(adapter_type, vis_data, height, title)
