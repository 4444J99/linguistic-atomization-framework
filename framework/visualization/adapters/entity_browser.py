"""
Entity Browser Adapter - Interactive entity search and filter table.

Generates a searchable entity browser from entity analysis output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...core.ontology import AnalysisOutput
from ...core.registry import registry
from ..base import BaseVisualizationAdapter


@registry.register_adapter("entity_browser")
class EntityBrowserAdapter(BaseVisualizationAdapter):
    """
    Vanilla JS entity browser adapter.

    Features:
    - Searchable entity table
    - Filter by entity type
    - Statistics summary
    - Entity frequency display
    """

    name = "entity_browser"
    description = "Interactive entity search and filter browser"
    supported_analysis = ["entity"]

    def get_browser_script(self, stats: Dict[str, Any], enhanced_data: Dict[str, Any]) -> str:
        """Generate entity browser JavaScript using safe DOM methods."""
        return f"""
        const stats = {json.dumps(stats, indent=2)};
        const enhancedData = {json.dumps(enhanced_data, indent=2)};

        // Populate statistics using textContent for safety
        document.getElementById('total-entities').textContent = stats.total_entities;

        const byTypeContainer = document.getElementById('by-type-stats');
        for (const [type, info] of Object.entries(stats.by_type)) {{
            const div = document.createElement('div');
            div.className = 'stat-box';

            const valueDiv = document.createElement('div');
            valueDiv.className = 'stat-value';
            valueDiv.textContent = info.total;
            div.appendChild(valueDiv);

            const labelDiv = document.createElement('div');
            labelDiv.className = 'stat-label';
            labelDiv.textContent = type + ' (' + info.unique + ' unique)';
            div.appendChild(labelDiv);

            byTypeContainer.appendChild(div);
        }}

        // Build entity table
        const entityTable = document.getElementById('entity-table-body');
        const allEntities = [];

        for (const [type, info] of Object.entries(stats.by_type)) {{
            for (const [entity, count] of Object.entries(info.top_10)) {{
                allEntities.push({{ type, entity, count }});
            }}
        }}

        allEntities.sort((a, b) => b.count - a.count);

        function createTableRow(e) {{
            const tr = document.createElement('tr');

            const tdEntity = document.createElement('td');
            tdEntity.textContent = e.entity;
            tr.appendChild(tdEntity);

            const tdType = document.createElement('td');
            const typeSpan = document.createElement('span');
            typeSpan.className = 'entity-type';
            typeSpan.setAttribute('data-type', e.type);
            typeSpan.textContent = e.type;
            tdType.appendChild(typeSpan);
            tr.appendChild(tdType);

            const tdCount = document.createElement('td');
            tdCount.textContent = e.count;
            tr.appendChild(tdCount);

            return tr;
        }}

        function renderTable(entities) {{
            entityTable.textContent = '';
            for (const e of entities) {{
                entityTable.appendChild(createTableRow(e));
            }}
        }}

        renderTable(allEntities);

        // Search functionality
        document.getElementById('search').addEventListener('input', (e) => {{
            const term = e.target.value.toLowerCase();
            const filtered = allEntities.filter(ent =>
                ent.entity.toLowerCase().includes(term) ||
                ent.type.toLowerCase().includes(term)
            );
            renderTable(filtered);
        }});

        // Filter by type
        document.getElementById('type-filter').addEventListener('change', (e) => {{
            const type = e.target.value;
            const filtered = type === 'all'
                ? allEntities
                : allEntities.filter(ent => ent.type === type);
            renderTable(filtered);
        }});

        // Populate filter dropdown
        const typeFilter = document.getElementById('type-filter');
        for (const type of Object.keys(stats.by_type)) {{
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            typeFilter.appendChild(option);
        }}
        """

    def generate(
        self,
        analysis: AnalysisOutput,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Generate entity browser visualization.

        Args:
            analysis: Entity analysis output
            output_path: Output file path
            config: Optional configuration
        """
        self._config = config or {}

        stats = analysis.data.get("entity_statistics", {})
        enhanced_data = analysis.data.get("enhanced_atomized", {})

        title = self._config.get("title", "Entity Browser")

        content = f"""
        <div class="glass">
            <h1>🔍 {title}</h1>
            <p class="subtitle">Browse and search named entities extracted from the text</p>
        </div>

        <div class="glass stats">
            <div class="stat-box">
                <div class="stat-value" id="total-entities">0</div>
                <div class="stat-label">Total Entities</div>
            </div>
            <div id="by-type-stats" style="display: contents;"></div>
        </div>

        <div class="glass">
            <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
                <input type="text" id="search" placeholder="🔍 Search entities..."
                       style="flex: 1; min-width: 200px; padding: 10px 15px; border-radius: 10px;
                              border: 1px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.15); color: white;">
                <select id="type-filter" style="padding: 10px 15px; border-radius: 10px;
                        border: 1px solid rgba(255,255,255,0.3); background: rgba(255,255,255,0.15); color: white;">
                    <option value="all">All Types</option>
                </select>
            </div>

            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="border-bottom: 2px solid rgba(255,255,255,0.2);">
                        <th style="text-align: left; padding: 12px;">Entity</th>
                        <th style="text-align: left; padding: 12px;">Type</th>
                        <th style="text-align: left; padding: 12px;">Count</th>
                    </tr>
                </thead>
                <tbody id="entity-table-body">
                </tbody>
            </table>
        </div>
        """

        styles = """
        #entity-table-body tr {
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        #entity-table-body td {
            padding: 12px;
        }
        #entity-table-body tr:hover {
            background: rgba(255,255,255,0.05);
        }
        .entity-type {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .entity-type[data-type="MILITARY_TERM"],
        .entity-type[data-type="RANK"] { background: rgba(214, 39, 40, 0.3); }
        .entity-type[data-type="LOCATION"],
        .entity-type[data-type="REGION"] { background: rgba(44, 160, 44, 0.3); }
        .entity-type[data-type="EQUIPMENT"],
        .entity-type[data-type="VEHICLE"] { background: rgba(148, 103, 189, 0.3); }
        .entity-type[data-type="UNIT"] { background: rgba(255, 127, 14, 0.3); }
        .entity-type[data-type="TEMPORAL"] { background: rgba(23, 190, 207, 0.3); }
        .entity-type[data-type="PERSON"] { background: rgba(31, 119, 180, 0.3); }
        input::placeholder { color: rgba(255, 255, 255, 0.6); }
        select option { background: #333; color: white; }
        """

        scripts = self.get_browser_script(stats, enhanced_data)

        html = self.wrap_html(
            title=title,
            content=content,
            scripts=scripts,
            styles=styles,
        viz_type="entity",
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
