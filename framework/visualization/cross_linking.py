"""
Cross-Visualization Linking - Enable click-through navigation between visualizations.

Provides URL-based linking between different visualization types, allowing users to:
- Click an element in one view and jump to related content in another
- Share specific views via URL parameters
- Navigate between semantic, temporal, sentiment, and entity views
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path
import json


class CrossVizLinker:
    """
    Handles cross-visualization linking with URL parameters.
    
    Each visualization can accept parameters like:
    - ?highlight=S001  - Highlight a specific atom
    - ?filter=theme:T001 - Filter to a theme
    - ?focus=entity:General - Focus on an entity
    """
    
    # Standard URL parameter names
    PARAM_HIGHLIGHT = "highlight"
    PARAM_FILTER = "filter"
    PARAM_FOCUS = "focus"
    PARAM_VIEW = "view"
    
    # Visualization file names
    VIZ_TYPES = {
        "semantic": "semantic_force_graph.html",
        "temporal": "temporal_sankey.html",
        "sentiment": "sentiment_chart.html",
        "entity": "entity_browser.html",
        "evaluation": "evaluation_dashboard.html",
    }
    
    @staticmethod
    def get_nav_bar_html(current_viz: str, viz_dir: str = ".") -> str:
        """
        Generate navigation bar HTML for cross-visualization linking.
        
        Args:
            current_viz: Current visualization type
            viz_dir: Directory containing visualization files
            
        Returns:
            HTML string for navigation bar
        """
        nav_items = []
        for viz_type, viz_file in CrossVizLinker.VIZ_TYPES.items():
            is_current = viz_type == current_viz
            active_class = "nav-item-active" if is_current else ""
            icon = CrossVizLinker._get_viz_icon(viz_type)
            
            nav_items.append(f"""
                <a href="{viz_dir}/{viz_file}" 
                   class="nav-item {active_class}"
                   data-viz="{viz_type}">
                    <span class="nav-icon">{icon}</span>
                    <span class="nav-label">{viz_type.title()}</span>
                </a>
            """)
        
        return f"""
            <nav class="cross-viz-nav">
                {"".join(nav_items)}
            </nav>
        """
    
    @staticmethod
    def get_nav_bar_css() -> str:
        """Return CSS for the navigation bar."""
        return """
        .cross-viz-nav {
            display: flex;
            justify-content: center;
            gap: 10px;
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .nav-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 18px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            text-decoration: none;
            transition: all 0.3s;
            font-weight: 500;
        }
        
        .nav-item:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }
        
        .nav-item-active {
            background: rgba(255, 255, 255, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .nav-icon {
            font-size: 1.2em;
        }
        
        .nav-label {
            font-size: 0.9em;
        }
        
        @media (max-width: 600px) {
            .nav-item {
                padding: 8px 12px;
            }
            .nav-label {
                display: none;
            }
        }
        """
    
    @staticmethod
    def get_linking_js() -> str:
        """Return JavaScript for cross-visualization linking."""
        return """
        // Cross-visualization linking utilities
        const CrossVizLink = {
            // Parse URL parameters
            getParams() {
                return Object.fromEntries(new URLSearchParams(window.location.search));
            },
            
            // Get a specific parameter
            getParam(name) {
                return this.getParams()[name] || null;
            },
            
            // Build URL with parameters
            buildUrl(baseUrl, params) {
                const url = new URL(baseUrl, window.location.href);
                Object.entries(params).forEach(([key, value]) => {
                    if (value) url.searchParams.set(key, value);
                });
                return url.toString();
            },
            
            // Navigate to another visualization with context
            linkTo(vizType, params = {}) {
                const vizFiles = {
                    semantic: "semantic_force_graph.html",
                    temporal: "temporal_sankey.html",
                    sentiment: "sentiment_chart.html",
                    entity: "entity_browser.html",
                    evaluation: "evaluation_dashboard.html"
                };
                
                const file = vizFiles[vizType];
                if (!file) {
                    console.warn("Unknown visualization type:", vizType);
                    return;
                }
                
                window.location.href = this.buildUrl(file, params);
            },
            
            // Create a link element
            createLink(vizType, params, text, className = "") {
                const link = document.createElement("a");
                link.href = "#";
                link.className = "cross-viz-link " + className;
                link.textContent = text;
                link.onclick = (e) => {
                    e.preventDefault();
                    this.linkTo(vizType, params);
                };
                return link;
            },
            
            // Apply highlight from URL parameter
            applyHighlight(highlightFn) {
                const highlight = this.getParam("highlight");
                if (highlight) {
                    highlightFn(highlight);
                }
            },
            
            // Apply filter from URL parameter
            applyFilter(filterFn) {
                const filter = this.getParam("filter");
                if (filter) {
                    const [type, value] = filter.split(":");
                    filterFn(type, value);
                }
            }
        };
        
        // Initialize on page load
        document.addEventListener("DOMContentLoaded", () => {
            // Check for cross-viz parameters and apply
            const params = CrossVizLink.getParams();
            console.log("Cross-viz params:", params);
        });
        """
    
    @staticmethod
    def _get_viz_icon(viz_type: str) -> str:
        """Get icon for visualization type."""
        icons = {
            "semantic": "🕸️",
            "temporal": "⏳",
            "sentiment": "💭",
            "entity": "👤",
            "evaluation": "📊",
        }
        return icons.get(viz_type, "📈")
    
    @staticmethod
    def create_context_link(
        source_viz: str,
        target_viz: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Create a contextual link from one visualization to another.
        
        Args:
            source_viz: Source visualization type
            target_viz: Target visualization type
            context: Context data (atom_id, entity, theme, etc.)
            
        Returns:
            JavaScript onclick handler string
        """
        params = {}
        
        # Map context to appropriate parameters for target
        if "atom_id" in context:
            params["highlight"] = context["atom_id"]
        if "theme_id" in context:
            params["filter"] = f"theme:{context['theme_id']}"
        if "entity" in context:
            params["focus"] = f"entity:{context['entity']}"
        if "sentence_id" in context:
            params["highlight"] = context["sentence_id"]
        
        params_str = json.dumps(params)
        return f"CrossVizLink.linkTo('{target_viz}', {params_str})"


def inject_cross_linking(html_content: str, viz_type: str) -> str:
    """
    Inject cross-visualization linking into existing HTML.
    
    Args:
        html_content: Original HTML content
        viz_type: Type of visualization (semantic, temporal, etc.)
        
    Returns:
        Modified HTML with cross-linking support
    """
    linker = CrossVizLinker()
    
    # Add CSS
    css_injection = f"<style>\n{linker.get_nav_bar_css()}\n</style>"
    
    # Add JavaScript
    js_injection = f"<script>\n{linker.get_linking_js()}\n</script>"
    
    # Add navigation bar after opening body tag
    nav_bar = linker.get_nav_bar_html(viz_type)
    
    # Inject CSS before </head>
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", f"{css_injection}\n</head>")
    
    # Inject navigation bar after <body> tag or container
    if '<div class="container">' in html_content:
        html_content = html_content.replace(
            '<div class="container">',
            f'<div class="container">\n{nav_bar}'
        )
    elif "<body>" in html_content:
        html_content = html_content.replace("<body>", f"<body>\n{nav_bar}")
    
    # Inject JavaScript before </body>
    if "</body>" in html_content:
        html_content = html_content.replace("</body>", f"{js_injection}\n</body>")
    
    return html_content
