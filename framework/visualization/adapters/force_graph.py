"""
Force Graph Adapter - D3.js force-directed network visualization.

Generates interactive semantic network visualizations from semantic analysis output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...core.ontology import AnalysisOutput
from ...core.registry import registry
from ..base import BaseVisualizationAdapter


@registry.register_adapter("force_graph")
class ForceGraphAdapter(BaseVisualizationAdapter):
    """
    D3.js force-directed graph adapter for semantic network visualization.

    Features:
    - Interactive node dragging
    - Zoom and pan
    - Node filtering by type
    - Search highlighting
    - Similarity threshold slider
    """

    name = "force_graph"
    description = "D3.js force-directed network graph"
    supported_analysis = ["semantic"]

    def get_d3_script(self, data: Dict[str, Any]) -> str:
        """Generate D3.js visualization script."""
        return f"""
        const data = {json.dumps(data, indent=2)};

        const width = document.getElementById('network').clientWidth;
        const height = 600;

        const svg = d3.select('#network')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        const g = svg.append('g');

        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => g.attr('transform', event.transform));
        svg.call(zoom);

        // Force simulation
        const simulation = d3.forceSimulation(data.nodes)
            .force('link', d3.forceLink(data.edges).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => d.size + 5));

        // Links
        const link = g.append('g')
            .selectAll('line')
            .data(data.edges)
            .join('line')
            .attr('stroke', d => d.type === 'semantic_similarity' ? '#4ECDC4' :
                               d.type === 'sequential_adjacency' ? '#FFD93D' : '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => Math.sqrt(d.weight) * 2);

        // Nodes
        const node = g.append('g')
            .selectAll('circle')
            .data(data.nodes)
            .join('circle')
            .attr('r', d => d.size)
            .attr('fill', d => d.color)
            .attr('stroke', 'white')
            .attr('stroke-width', 2)
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));

        // Labels
        const label = g.append('g')
            .selectAll('text')
            .data(data.nodes)
            .join('text')
            .text(d => d.label)
            .attr('font-size', d => d.type === 'theme' ? '12px' : '10px')
            .attr('fill', 'white')
            .attr('dx', 15)
            .attr('dy', 4);

        // Tooltip
        const tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0);

        node.on('mouseover', (event, d) => {{
            tooltip.transition().duration(200).style('opacity', 1);
            tooltip.html(`<strong>${{d.label}}</strong><br/>Type: ${{d.type}}${{
                d.mention_count ? '<br/>Mentions: ' + d.mention_count : ''
            }}`)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px');
        }})
        .on('mouseout', () => tooltip.transition().duration(500).style('opacity', 0));

        // Simulation tick
        simulation.on('tick', () => {{
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            label
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        }});

        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}

        // Search functionality
        document.getElementById('search').addEventListener('input', (e) => {{
            const term = e.target.value.toLowerCase();
            node.attr('opacity', d =>
                !term || d.label.toLowerCase().includes(term) ? 1 : 0.2);
            label.attr('opacity', d =>
                !term || d.label.toLowerCase().includes(term) ? 1 : 0.2);
        }});

        // Reset view
        window.resetView = function() {{
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity.translate(0, 0).scale(1)
            );
            document.getElementById('search').value = '';
            node.attr('opacity', 1);
            label.attr('opacity', 1);
        }};
        """

    def generate(
        self,
        analysis: AnalysisOutput,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Generate force graph visualization.

        Args:
            analysis: Semantic analysis output with nodes/edges
            output_path: Output file path
            config: Optional configuration (title, colors, etc.)
        """
        self._config = config or {}

        # Get data from analysis
        data = {
            "nodes": analysis.data.get("nodes", []),
            "edges": analysis.data.get("edges", []),
        }

        title = self._config.get("title", "Semantic Network Analysis")
        subtitle = self._config.get("subtitle", "Interactive visualization of theme relationships")

        # Generate content
        content = f"""
        <div class="glass">
            <h1>🌐 {title}</h1>
            <p class="subtitle">{subtitle}</p>
        </div>

        <div class="glass">
            <div class="controls" style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
                <input type="text" id="search" placeholder="🔍 Search nodes..."
                       style="padding: 10px 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.3);
                              background: rgba(255,255,255,0.15); color: white; min-width: 200px;">
                <button onclick="resetView()">Reset View</button>
            </div>

            <div class="legend" style="display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 20px; height: 20px; border-radius: 50%; background: #1f77b4; border: 2px solid white;"></div>
                    <span>Theme</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 20px; height: 20px; border-radius: 50%; background: #d62728; border: 2px solid white;"></div>
                    <span>Military</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 20px; height: 20px; border-radius: 50%; background: #2ca02c; border: 2px solid white;"></div>
                    <span>Location</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 20px; height: 20px; border-radius: 50%; background: #9467bd; border: 2px solid white;"></div>
                    <span>Equipment</span>
                </div>
            </div>

            <div id="network" style="background: rgba(255,255,255,0.05); border-radius: 15px; cursor: grab;"></div>
        </div>

        <div class="glass stats">
            <div class="stat-box">
                <div class="stat-value">{len(data['nodes'])}</div>
                <div class="stat-label">Total Nodes</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(data['edges'])}</div>
                <div class="stat-label">Total Edges</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len([n for n in data['nodes'] if n.get('type') == 'theme'])}</div>
                <div class="stat-label">Themes</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len([n for n in data['nodes'] if n.get('type') == 'entity'])}</div>
                <div class="stat-label">Entities</div>
            </div>
        </div>
        """

        styles = """
        .tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            pointer-events: none;
            font-size: 14px;
            max-width: 300px;
        }
        #network:active { cursor: grabbing; }
        input::placeholder { color: rgba(255, 255, 255, 0.6); }
        """

        head_extras = '<script src="https://d3js.org/d3.v7.min.js"></script>'
        scripts = self.get_d3_script(data)

        html = self.wrap_html(
            title=title,
            content=content,
            scripts=scripts,
            styles=styles,
            head_extras=head_extras,
            viz_type="semantic",
        )

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
