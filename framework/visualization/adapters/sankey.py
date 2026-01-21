"""
Sankey Adapter - Plotly.js Sankey diagram for temporal flow visualization.

Generates narrative flow diagrams from temporal analysis output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ...core.ontology import AnalysisOutput
from ...core.registry import registry
from ..base import BaseVisualizationAdapter


@registry.register_adapter("sankey")
class SankeyAdapter(BaseVisualizationAdapter):
    """
    Plotly.js Sankey diagram adapter for temporal flow visualization.

    Features:
    - Theme to chronology flow
    - Tense distribution heatmap
    - Interactive timeline
    """

    name = "sankey"
    description = "Plotly.js Sankey diagram for narrative flow"
    supported_analysis = ["temporal"]

    def get_plotly_script(self, sankey_data: Dict[str, Any], stats: Dict[str, Any]) -> str:
        """Generate Plotly.js visualization script."""
        return f"""
        const sankeyData = {json.dumps(sankey_data, indent=2)};
        const stats = {json.dumps(stats, indent=2)};

        // Sankey diagram
        const sankeyNodes = sankeyData.nodes.map(n => n.name);
        const sankeyLinks = {{
            source: sankeyData.links.map(l => l.source),
            target: sankeyData.links.map(l => l.target),
            value: sankeyData.links.map(l => l.value),
            color: sankeyData.links.map(l => {{
                const targetNode = sankeyData.nodes[l.target];
                if (targetNode && targetNode.id.includes('past')) return 'rgba(214, 39, 40, 0.5)';
                if (targetNode && targetNode.id.includes('present')) return 'rgba(44, 160, 44, 0.5)';
                if (targetNode && targetNode.id.includes('future')) return 'rgba(31, 119, 180, 0.5)';
                return 'rgba(127, 127, 127, 0.5)';
            }})
        }};

        const sankeyTrace = {{
            type: 'sankey',
            orientation: 'h',
            node: {{
                pad: 15,
                thickness: 20,
                line: {{ color: 'white', width: 0.5 }},
                label: sankeyNodes,
                color: sankeyData.nodes.map(n =>
                    n.group === 'theme' ? 'rgba(31, 119, 180, 0.8)' :
                    n.id.includes('past') ? 'rgba(214, 39, 40, 0.8)' :
                    n.id.includes('present') ? 'rgba(44, 160, 44, 0.8)' :
                    n.id.includes('future') ? 'rgba(31, 119, 180, 0.8)' :
                    'rgba(127, 127, 127, 0.8)'
                )
            }},
            link: sankeyLinks
        }};

        const sankeyLayout = {{
            font: {{ size: 12, color: 'white' }},
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            margin: {{ l: 20, r: 20, t: 20, b: 20 }}
        }};

        Plotly.newPlot('sankey', [sankeyTrace], sankeyLayout, {{responsive: true}});

        // Tense distribution bar chart
        const tenseLabels = ['Past', 'Present', 'Future', 'Ambiguous'];
        const tenseCounts = stats.tense_counts;
        const tenseValues = [
            tenseCounts.past || 0,
            tenseCounts.present || 0,
            tenseCounts.future || 0,
            tenseCounts.ambiguous || 0
        ];

        const tenseTrace = {{
            x: tenseLabels,
            y: tenseValues,
            type: 'bar',
            marker: {{
                color: ['rgba(214, 39, 40, 0.8)', 'rgba(44, 160, 44, 0.8)',
                        'rgba(31, 119, 180, 0.8)', 'rgba(127, 127, 127, 0.8)']
            }}
        }};

        const tenseLayout = {{
            font: {{ color: 'white' }},
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            xaxis: {{ gridcolor: 'rgba(255,255,255,0.1)' }},
            yaxis: {{ gridcolor: 'rgba(255,255,255,0.1)', title: 'Sentence Count' }},
            margin: {{ l: 50, r: 20, t: 20, b: 40 }}
        }};

        Plotly.newPlot('tense-dist', [tenseTrace], tenseLayout, {{responsive: true}});

        // Narrative shifts pie chart
        const shiftTrace = {{
            values: [stats.linear_count || 0, stats.flashback_count || 0, stats.flashforward_count || 0],
            labels: ['Linear', 'Flashback', 'Flashforward'],
            type: 'pie',
            marker: {{
                colors: ['rgba(44, 160, 44, 0.8)', 'rgba(214, 39, 40, 0.8)', 'rgba(31, 119, 180, 0.8)']
            }},
            textfont: {{ color: 'white' }}
        }};

        const shiftLayout = {{
            font: {{ color: 'white' }},
            paper_bgcolor: 'rgba(0,0,0,0)',
            showlegend: true,
            legend: {{ font: {{ color: 'white' }} }},
            margin: {{ l: 20, r: 20, t: 20, b: 20 }}
        }};

        Plotly.newPlot('narrative-shifts', [shiftTrace], shiftLayout, {{responsive: true}});
        """

    def generate(
        self,
        analysis: AnalysisOutput,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Generate Sankey diagram visualization.

        Args:
            analysis: Temporal analysis output with sankey_data
            output_path: Output file path
            config: Optional configuration
        """
        self._config = config or {}

        sankey_data = analysis.data.get("sankey_data", {"nodes": [], "links": []})
        stats = analysis.data.get("overall_statistics", {})

        title = self._config.get("title", "Temporal Flow Analysis")

        content = f"""
        <div class="glass">
            <h1>⏰ {title}</h1>
            <p class="subtitle">Narrative time progression and tense distribution</p>
        </div>

        <div class="glass">
            <h2 style="margin-bottom: 15px;">📊 Narrative Flow (Theme → Chronology)</h2>
            <div id="sankey" style="height: 400px;"></div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div class="glass">
                <h2 style="margin-bottom: 15px;">📈 Tense Distribution</h2>
                <div id="tense-dist" style="height: 300px;"></div>
            </div>
            <div class="glass">
                <h2 style="margin-bottom: 15px;">🔄 Narrative Shifts</h2>
                <div id="narrative-shifts" style="height: 300px;"></div>
            </div>
        </div>

        <div class="glass stats">
            <div class="stat-box">
                <div class="stat-value">{stats.get('total_sentences', 0)}</div>
                <div class="stat-label">Total Sentences</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{stats.get('flashback_count', 0)}</div>
                <div class="stat-label">Flashbacks</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{stats.get('flashforward_count', 0)}</div>
                <div class="stat-label">Flashforwards</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{stats.get('linear_count', 0)}</div>
                <div class="stat-label">Linear Narrative</div>
            </div>
        </div>
        """

        head_extras = '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
        scripts = self.get_plotly_script(sankey_data, stats)

        html = self.wrap_html(
            title=title,
            content=content,
            scripts=scripts,
            head_extras=head_extras,
        viz_type="temporal",
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
