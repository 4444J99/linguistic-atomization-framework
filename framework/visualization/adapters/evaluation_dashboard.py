"""
Evaluation Dashboard Adapter - Interactive 9-step evaluation visualization.

Generates an interactive dashboard showing:
- Phase progression (Evaluation → Risk → Growth)
- Step-by-step results with expandable details
- Overall scores and recommendations
- Visual flow diagram
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...core.ontology import AnalysisOutput
from ...core.registry import registry
from ..base import BaseVisualizationAdapter


@registry.register_adapter("evaluation_dashboard")
class EvaluationDashboardAdapter(BaseVisualizationAdapter):
    """
    Interactive dashboard adapter for 9-step evaluation analysis.

    Features:
    - Phase-based organization (Evaluation, Risk, Growth)
    - Score gauges and progress indicators
    - Expandable step details
    - Recommendations panel
    - Flow diagram visualization
    """

    name = "evaluation_dashboard"
    description = "Interactive dashboard for 9-step rhetorical evaluation"
    supported_analysis = ["evaluation"]

    # Step metadata
    STEP_INFO = {
        "critique": {"icon": "🔍", "color": "#3498db"},
        "logic_check": {"icon": "🧠", "color": "#9b59b6"},
        "logos": {"icon": "📊", "color": "#2ecc71"},
        "pathos": {"icon": "💓", "color": "#e74c3c"},
        "ethos": {"icon": "👤", "color": "#f39c12"},
        "blind_spots": {"icon": "👁️", "color": "#e67e22"},
        "shatter_points": {"icon": "💥", "color": "#c0392b"},
        "bloom": {"icon": "🌸", "color": "#1abc9c"},
        "evolve": {"icon": "🚀", "color": "#8e44ad"},
    }

    PHASE_COLORS = {
        "Evaluation": "#3498db",
        "Reinforcement": "#9b59b6",
        "Risk": "#e74c3c",
        "Growth": "#2ecc71",
    }

    PHASE_ICONS = {
        "Evaluation": "📊",
        "Reinforcement": "🔗",
        "Risk": "⚠️",
        "Growth": "🌱",
    }

    def get_dashboard_css(self) -> str:
        """Return dashboard-specific CSS."""
        return """
        .dashboard-header {
            text-align: center;
            padding: 30px;
            margin-bottom: 20px;
        }

        .overall-score {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }

        .score-circle {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: rgba(255, 255, 255, 0.15);
            border: 4px solid;
            transition: transform 0.3s;
        }

        .score-circle:hover {
            transform: scale(1.05);
        }

        .score-value {
            font-size: 2.5em;
            font-weight: bold;
        }

        .score-label {
            font-size: 0.9em;
            opacity: 0.8;
            text-transform: uppercase;
        }

        .phase-section {
            margin-bottom: 30px;
        }

        .phase-header {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px 20px;
            border-radius: 15px 15px 0 0;
            cursor: pointer;
            transition: all 0.3s;
        }

        .phase-header:hover {
            filter: brightness(1.1);
        }

        .phase-title {
            font-size: 1.5em;
            font-weight: bold;
            flex: 1;
        }

        .phase-score {
            font-size: 1.3em;
            font-weight: bold;
            padding: 5px 15px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.2);
        }

        .phase-content {
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 0 0 15px 15px;
        }

        .step-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .step-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s;
            cursor: pointer;
        }

        .step-card:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateY(-3px);
        }

        .step-card.expanded {
            grid-column: 1 / -1;
        }

        .step-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
        }

        .step-icon {
            font-size: 1.5em;
        }

        .step-name {
            font-size: 1.2em;
            font-weight: bold;
            flex: 1;
        }

        .step-score {
            font-size: 1.2em;
            font-weight: bold;
            padding: 3px 12px;
            border-radius: 15px;
            background: rgba(255, 255, 255, 0.2);
        }

        .step-description {
            opacity: 0.8;
            margin-bottom: 15px;
            font-size: 0.9em;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }

        .metric-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 10px;
            text-align: center;
        }

        .metric-value {
            font-size: 1.3em;
            font-weight: bold;
        }

        .metric-label {
            font-size: 0.75em;
            opacity: 0.7;
            text-transform: uppercase;
        }

        .findings-list {
            margin-top: 15px;
        }

        .finding-item {
            display: flex;
            gap: 10px;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.08);
        }

        .finding-type {
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }

        .finding-type.strength { background: rgba(46, 204, 113, 0.3); }
        .finding-type.weakness { background: rgba(231, 76, 60, 0.3); }
        .finding-type.blind_spot { background: rgba(230, 126, 34, 0.3); }
        .finding-type.shatter_point { background: rgba(192, 57, 43, 0.3); }
        .finding-type.insight { background: rgba(26, 188, 156, 0.3); }
        .finding-type.observation { background: rgba(149, 165, 166, 0.3); }

        .recommendations-panel {
            margin-top: 30px;
        }

        .recommendation-item {
            display: flex;
            align-items: flex-start;
            gap: 15px;
            padding: 15px;
            margin-bottom: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            border-left: 4px solid #3498db;
        }

        .recommendation-number {
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #3498db;
            border-radius: 50%;
            font-weight: bold;
            flex-shrink: 0;
        }

        .flow-diagram {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            padding: 30px;
            margin-bottom: 20px;
        }

        .flow-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 15px;
            border-radius: 15px;
            min-width: 80px;
            transition: all 0.3s;
        }

        .flow-step:hover {
            transform: scale(1.1);
        }

        .flow-step-number {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .flow-step-name {
            font-size: 0.8em;
            text-transform: capitalize;
        }

        .flow-arrow {
            font-size: 1.5em;
            opacity: 0.5;
        }

        .flow-phase-divider {
            width: 2px;
            height: 50px;
            background: rgba(255, 255, 255, 0.3);
            margin: 0 10px;
        }

        .llm-insights {
            background: linear-gradient(135deg, rgba(142, 68, 173, 0.2), rgba(155, 89, 182, 0.1));
            border-radius: 15px;
            padding: 20px;
            margin-top: 15px;
            border-left: 4px solid #9b59b6;
        }

        .llm-insights-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            font-weight: bold;
        }

        .progress-bar {
            height: 8px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }

        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease-out;
        }

        .tab-container {
            margin-bottom: 20px;
        }

        .tabs {
            display: flex;
            gap: 5px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }

        .tab-btn {
            padding: 10px 20px;
            border: none;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }

        .tab-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .tab-btn.active {
            background: rgba(255, 255, 255, 0.3);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Prompt Chain Visualization */
        .prompt-chain-container {
            margin-top: 20px;
            background: rgba(155, 89, 182, 0.1);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(155, 89, 182, 0.3);
        }

        .prompt-chain-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }

        .prompt-chain-header h3 {
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .chain-toggle {
            padding: 8px 16px;
            background: rgba(155, 89, 182, 0.3);
            border: none;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }

        .chain-toggle:hover {
            background: rgba(155, 89, 182, 0.5);
        }

        .chain-steps {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .chain-step {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s;
        }

        .chain-step:hover {
            background: rgba(255, 255, 255, 0.12);
        }

        .chain-step-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            cursor: pointer;
        }

        .chain-step-num {
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(155, 89, 182, 0.4);
            border-radius: 50%;
            font-weight: bold;
            font-size: 0.9em;
        }

        .chain-step-name {
            font-weight: 600;
            flex: 1;
        }

        .chain-step-phase {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            text-transform: uppercase;
            font-weight: 600;
        }

        .chain-step-phase.evaluation { background: rgba(52, 152, 219, 0.3); }
        .chain-step-phase.reinforcement { background: rgba(155, 89, 182, 0.3); }
        .chain-step-phase.risk { background: rgba(231, 76, 60, 0.3); }
        .chain-step-phase.growth { background: rgba(46, 204, 113, 0.3); }

        .chain-step-confidence {
            font-size: 0.85em;
            opacity: 0.8;
        }

        .chain-step-details {
            padding: 0 16px 16px 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .prompt-box, .output-box {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 12px;
            margin-top: 10px;
        }

        .prompt-box label, .output-box label {
            display: block;
            font-size: 0.75em;
            text-transform: uppercase;
            opacity: 0.7;
            margin-bottom: 8px;
        }

        .prompt-box pre, .output-box pre {
            margin: 0;
            white-space: pre-wrap;
            font-size: 0.85em;
            line-height: 1.5;
            max-height: 200px;
            overflow-y: auto;
        }

        .chain-arrow {
            text-align: center;
            font-size: 1.2em;
            opacity: 0.5;
            padding: 5px 0;
        }

        .no-chain-data {
            text-align: center;
            padding: 30px;
            opacity: 0.6;
        }

        /* 4-Phase Flow Visualization */
        .four-phase-flow {
            display: flex;
            flex-direction: column;
            gap: 20px;
            padding: 20px;
        }

        .phase-row {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .phase-label {
            min-width: 140px;
            padding: 10px 15px;
            border-radius: 10px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .phase-steps-row {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            flex: 1;
        }

        .phase-connector {
            text-align: center;
            font-size: 1.5em;
            opacity: 0.5;
            padding: 5px 0;
        }

        .feedback-loop {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 15px;
            margin-top: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            border: 1px dashed rgba(255, 255, 255, 0.2);
        }

        .feedback-loop-icon {
            font-size: 1.5em;
        }

        .feedback-loop-text {
            opacity: 0.7;
            font-style: italic;
        }

        /* LLM Badge */
        .llm-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            background: rgba(155, 89, 182, 0.3);
            border-radius: 8px;
            font-size: 0.7em;
            font-weight: 600;
        }

        @media (max-width: 768px) {
            .overall-score {
                flex-direction: column;
            }

            .step-grid {
                grid-template-columns: 1fr;
            }

            .flow-diagram {
                flex-direction: column;
            }

            .flow-arrow {
                transform: rotate(90deg);
            }

            .four-phase-flow {
                padding: 10px;
            }

            .phase-row {
                flex-direction: column;
                align-items: flex-start;
            }

            .phase-label {
                width: 100%;
            }

            .chain-step-header {
                flex-wrap: wrap;
            }
        }
        """

    def get_dashboard_script(self, data: Dict[str, Any]) -> str:
        """Generate dashboard JavaScript."""
        return f"""
        const analysisData = {json.dumps(data, indent=2)};

        // Tab switching
        function switchTab(tabName) {{
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.toggle('active', btn.dataset.tab === tabName);
            }});
            document.querySelectorAll('.tab-content').forEach(content => {{
                content.classList.toggle('active', content.id === tabName + '-tab');
            }});
        }}

        // Step card expansion
        function toggleStep(stepId) {{
            const card = document.getElementById(stepId);
            card.classList.toggle('expanded');

            const details = card.querySelector('.step-details');
            if (details) {{
                details.style.display = details.style.display === 'none' ? 'block' : 'none';
            }}
        }}

        // Score color calculation
        function getScoreColor(score) {{
            if (score >= 75) return '#2ecc71';
            if (score >= 50) return '#f39c12';
            return '#e74c3c';
        }}

        // Animate scores on load
        document.addEventListener('DOMContentLoaded', () => {{
            // Animate progress bars
            document.querySelectorAll('.progress-fill').forEach(bar => {{
                const targetWidth = bar.dataset.score + '%';
                setTimeout(() => {{
                    bar.style.width = targetWidth;
                }}, 300);
            }});

            // Animate score circles
            document.querySelectorAll('.score-value[data-target]').forEach(elem => {{
                const target = parseFloat(elem.dataset.target);
                animateValue(elem, 0, target, 1000);
            }});
        }});

        function animateValue(elem, start, end, duration) {{
            const range = end - start;
            const startTime = performance.now();

            function update(currentTime) {{
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);

                // Ease out
                const easeProgress = 1 - Math.pow(1 - progress, 3);
                const current = start + (range * easeProgress);

                elem.textContent = Math.round(current);

                if (progress < 1) {{
                    requestAnimationFrame(update);
                }}
            }}

            requestAnimationFrame(update);
        }}

        // Export functionality
        function exportResults() {{
            const dataStr = JSON.stringify(analysisData, null, 2);
            const blob = new Blob([dataStr], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'evaluation_results.json';
            a.click();
            URL.revokeObjectURL(url);
        }}

        // Toggle all chain details
        let chainExpanded = false;
        function toggleChainDetails() {{
            chainExpanded = !chainExpanded;
            document.querySelectorAll('.chain-step-details').forEach(details => {{
                details.style.display = chainExpanded ? 'block' : 'none';
            }});
        }}

        // Toggle individual step details
        function toggleStepDetails(stepId) {{
            const details = document.getElementById(stepId);
            if (details) {{
                details.style.display = details.style.display === 'none' ? 'block' : 'none';
            }}
        }}

        // Highlight current phase in flow
        function highlightPhase(phase) {{
            document.querySelectorAll('.phase-row').forEach(row => {{
                row.style.opacity = row.dataset.phase === phase ? '1' : '0.5';
            }});
        }}

        function resetPhaseHighlight() {{
            document.querySelectorAll('.phase-row').forEach(row => {{
                row.style.opacity = '1';
            }});
        }}
        """

    def _get_score_color(self, score: float) -> str:
        """Get color based on score value."""
        if score >= 75:
            return "#2ecc71"  # Green
        elif score >= 50:
            return "#f39c12"  # Orange
        return "#e74c3c"  # Red

    def _render_flow_diagram(self, flow: List[Dict[str, Any]]) -> str:
        """Render the step flow diagram."""
        html_parts = ['<div class="flow-diagram">']

        current_phase = None
        for i, step in enumerate(flow):
            phase = step.get("phase", "")
            step_num = step.get("step", i + 1)
            step_name = step.get("name", "")
            score = step.get("score", 0)
            color = self._get_score_color(score)

            # Add phase divider if phase changes
            if current_phase and current_phase != phase:
                html_parts.append('<div class="flow-phase-divider"></div>')

            current_phase = phase

            # Add arrow between steps (except first)
            if i > 0 and flow[i-1].get("phase") == phase:
                html_parts.append('<span class="flow-arrow">→</span>')

            step_info = self.STEP_INFO.get(step_name, {"icon": "📌", "color": "#95a5a6"})

            html_parts.append(f'''
                <div class="flow-step" style="background: rgba({self._hex_to_rgb(color)}, 0.3); border: 2px solid {color};">
                    <div class="step-icon">{step_info["icon"]}</div>
                    <div class="flow-step-number">{score:.0f}</div>
                    <div class="flow-step-name">{step_name.replace("_", " ")}</div>
                </div>
            ''')

        html_parts.append('</div>')
        return "\n".join(html_parts)

    def _render_four_phase_flow(self, flow: List[Dict[str, Any]]) -> str:
        """Render the 4-phase flow diagram with feedback loop."""
        if not flow:
            return '<div class="no-data">No flow data available</div>'

        # Organize steps by phase
        phase_order = ["Evaluation", "Reinforcement", "Risk", "Growth"]
        phases_data: Dict[str, List[Dict]] = {p: [] for p in phase_order}

        for step in flow:
            phase = step.get("phase", "Evaluation")
            if phase in phases_data:
                phases_data[phase].append(step)

        html_parts = ['<div class="four-phase-flow">']

        for i, phase_name in enumerate(phase_order):
            phase_steps = phases_data.get(phase_name, [])
            if not phase_steps and phase_name != "Reinforcement":
                continue

            phase_color = self.PHASE_COLORS.get(phase_name, "#95a5a6")
            phase_icon = self.PHASE_ICONS.get(phase_name, "📌")

            # Phase row
            html_parts.append(f'''
                <div class="phase-row">
                    <div class="phase-label" style="background: rgba({self._hex_to_rgb(phase_color)}, 0.3);">
                        <span>{phase_icon}</span>
                        <span>{phase_name}</span>
                    </div>
                    <div class="phase-steps-row">
            ''')

            # Steps in this phase
            for j, step in enumerate(phase_steps):
                step_name = step.get("name", "")
                step_score = step.get("score", 0)
                llm_enhanced = step.get("llm_enhanced", False)
                step_info = self.STEP_INFO.get(step_name, {"icon": "📌", "color": "#95a5a6"})
                score_color = self._get_score_color(step_score)

                llm_badge = '<span class="llm-badge">🤖 AI</span>' if llm_enhanced else ''

                if j > 0:
                    html_parts.append('<span class="flow-arrow">→</span>')

                html_parts.append(f'''
                    <div class="flow-step" style="background: rgba({self._hex_to_rgb(score_color)}, 0.3); border: 2px solid {score_color};">
                        <div class="step-icon">{step_info["icon"]}</div>
                        <div class="flow-step-number">{step_score:.0f}</div>
                        <div class="flow-step-name">{step_name.replace("_", " ")}</div>
                        {llm_badge}
                    </div>
                ''')

            html_parts.append('</div></div>')

            # Add connector between phases
            if i < len(phase_order) - 1 and (phase_steps or phase_name == "Reinforcement"):
                html_parts.append('<div class="phase-connector">↓</div>')

        # Feedback loop indicator
        html_parts.append('''
            <div class="feedback-loop">
                <span class="feedback-loop-icon">⟲</span>
                <span class="feedback-loop-text">Iterate: Apply improvements and re-evaluate for continuous growth</span>
            </div>
        ''')

        html_parts.append('</div>')
        return "\n".join(html_parts)

    def _render_prompt_chain_panel(self, chain_data: List[Dict[str, Any]]) -> str:
        """Render the AI reasoning chain visualization panel."""
        if not chain_data:
            return '''
                <div class="prompt-chain-container">
                    <div class="no-chain-data">
                        <p>🤖 AI Prompt Chain not available</p>
                        <p style="font-size: 0.85em;">Enable LLM analysis in project.yaml to see AI reasoning</p>
                    </div>
                </div>
            '''

        html_parts = ['''
            <div class="prompt-chain-container">
                <div class="prompt-chain-header">
                    <h3>🤖 AI Reasoning Chain</h3>
                    <button class="chain-toggle" onclick="toggleChainDetails()">
                        Show/Hide Details
                    </button>
                </div>
                <div class="chain-steps" id="chain-steps-container">
        ''']

        for i, step in enumerate(chain_data):
            step_name = step.get("step", f"Step {i+1}")
            phase = step.get("phase", "").lower()
            confidence = step.get("confidence", 0)
            prompt_preview = step.get("prompt_preview", "")
            output_preview = step.get("output_preview", "")
            success = step.get("success", True)

            confidence_display = f"{confidence:.0%}" if isinstance(confidence, (int, float)) else str(confidence)
            status_icon = "✓" if success else "✗"
            status_class = "" if success else "style='opacity: 0.6;'"

            html_parts.append(f'''
                <div class="chain-step" {status_class}>
                    <div class="chain-step-header" onclick="toggleStepDetails('chain-step-{i}')">
                        <span class="chain-step-num">{i + 1}</span>
                        <span class="chain-step-name">{step_name}</span>
                        <span class="chain-step-phase {phase}">{phase.title()}</span>
                        <span class="chain-step-confidence">{status_icon} {confidence_display}</span>
                    </div>
                    <div class="chain-step-details" id="chain-step-{i}" style="display: none;">
                        <div class="prompt-box">
                            <label>📝 Prompt Sent:</label>
                            <pre>{self._escape_html(prompt_preview)}</pre>
                        </div>
                        <div class="chain-arrow">↓ AI Processing</div>
                        <div class="output-box">
                            <label>💡 Output Received:</label>
                            <pre>{self._escape_html(output_preview)}</pre>
                        </div>
                    </div>
                </div>
            ''')

        html_parts.append('</div></div>')
        return "\n".join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color to RGB string."""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"

    def _render_step_card(
        self,
        step_name: str,
        step_data: Dict[str, Any],
    ) -> str:
        """Render a single step card."""
        step_info = self.STEP_INFO.get(step_name, {"icon": "📌", "color": "#95a5a6"})
        score = step_data.get("score", 0)
        score_color = self._get_score_color(score)

        # Metrics
        metrics_html = ""
        metrics = step_data.get("metrics", {})
        if metrics:
            metrics_items = []
            for key, value in list(metrics.items())[:6]:
                display_key = key.replace("_", " ").title()
                # Handle different value types
                if isinstance(value, float):
                    display_value = f"{value:.1f}"
                elif isinstance(value, dict):
                    # For dict metrics, show count of items
                    display_value = f"{len(value)} items"
                elif isinstance(value, list):
                    display_value = f"{len(value)} items"
                elif isinstance(value, bool):
                    display_value = "Yes" if value else "No"
                else:
                    display_value = str(value)
                metrics_items.append(f'''
                    <div class="metric-item">
                        <div class="metric-value">{display_value}</div>
                        <div class="metric-label">{display_key}</div>
                    </div>
                ''')
            metrics_html = f'<div class="metrics-grid">{"".join(metrics_items)}</div>'

        # Findings
        findings_html = ""
        findings = step_data.get("findings", [])
        if findings:
            finding_items = []
            for finding in findings[:5]:
                f_type = finding.get("type", "observation")
                f_desc = finding.get("description", "")
                finding_items.append(f'''
                    <div class="finding-item">
                        <span class="finding-type {f_type}">{f_type}</span>
                        <span>{f_desc}</span>
                    </div>
                ''')
            findings_html = f'<div class="findings-list">{"".join(finding_items)}</div>'

        # Recommendations
        recs_html = ""
        recs = step_data.get("recommendations", [])
        if recs:
            rec_items = [f'<li>{rec}</li>' for rec in recs[:3]]
            recs_html = f'<div class="step-recommendations"><strong>Recommendations:</strong><ul>{"".join(rec_items)}</ul></div>'

        # LLM Insights
        llm_html = ""
        llm_insights = step_data.get("llm_insights")
        if llm_insights:
            llm_html = f'''
                <div class="llm-insights">
                    <div class="llm-insights-header">
                        <span>🤖</span>
                        <span>AI-Powered Insights</span>
                    </div>
                    <div>{llm_insights}</div>
                </div>
            '''

        return f'''
            <div class="step-card" id="step-{step_name}" onclick="toggleStep('step-{step_name}')">
                <div class="step-header">
                    <span class="step-icon">{step_info["icon"]}</span>
                    <span class="step-name">{step_name.replace("_", " ").title()}</span>
                    <span class="step-score" style="color: {score_color};">{score:.0f}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" data-score="{score}" style="width: 0%; background: {score_color};"></div>
                </div>
                <div class="step-details" style="display: none;">
                    {metrics_html}
                    {findings_html}
                    {recs_html}
                    {llm_html}
                </div>
            </div>
        '''

    def _render_phase_section(
        self,
        phase_name: str,
        phase_data: Dict[str, Dict[str, Any]],
        phase_score: float,
    ) -> str:
        """Render a phase section with its steps."""
        phase_color = self.PHASE_COLORS.get(phase_name, "#95a5a6")

        steps_html = ""
        for step_name, step_data in phase_data.items():
            steps_html += self._render_step_card(step_name, step_data)

        return f'''
            <div class="phase-section glass">
                <div class="phase-header" style="background: rgba({self._hex_to_rgb(phase_color)}, 0.3);">
                    <span class="phase-title">{phase_name}</span>
                    <span class="phase-score" style="color: {self._get_score_color(phase_score)};">
                        {phase_score:.0f}/100
                    </span>
                </div>
                <div class="phase-content">
                    <div class="step-grid">
                        {steps_html}
                    </div>
                </div>
            </div>
        '''

    def _render_recommendations_panel(self, recommendations: List[str]) -> str:
        """Render the recommendations panel."""
        if not recommendations:
            return ""

        items_html = ""
        for i, rec in enumerate(recommendations[:10], 1):
            items_html += f'''
                <div class="recommendation-item">
                    <span class="recommendation-number">{i}</span>
                    <span>{rec}</span>
                </div>
            '''

        return f'''
            <div class="recommendations-panel glass">
                <h2 style="margin-bottom: 20px;">📋 Top Recommendations</h2>
                {items_html}
            </div>
        '''

    def generate(
        self,
        analysis: AnalysisOutput,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Generate evaluation dashboard visualization."""
        self._config = config or {}

        # Extract data
        phases = analysis.data.get("phases", {})
        summary = analysis.data.get("summary", {})
        flow = analysis.data.get("flow", [])
        prompt_chain = analysis.data.get("prompt_chain", [])

        overall_score = summary.get("overall_score", 0)
        phase_scores = summary.get("phase_scores", {})
        top_recommendations = summary.get("top_recommendations", [])

        # Check if this is 4-phase analysis
        is_four_phase = "reinforcement" in phases or any(s.get("phase") == "Reinforcement" for s in flow)

        title = self._config.get("title", "Rhetorical Evaluation Dashboard")
        subtitle = self._config.get(
            "subtitle",
            "9-Step Analysis: Evaluation → Reinforcement → Risk → Growth" if is_four_phase
            else "9-Step Analysis: Evaluation → Risk → Growth"
        )

        # Build overall score circles
        score_circles_html = f'''
            <div class="score-circle" style="border-color: {self._get_score_color(overall_score)};">
                <div class="score-value" data-target="{overall_score}">0</div>
                <div class="score-label">Overall</div>
            </div>
        '''

        for phase_name, phase_score in phase_scores.items():
            phase_color = self.PHASE_COLORS.get(phase_name.title(), "#95a5a6")
            score_circles_html += f'''
                <div class="score-circle" style="border-color: {phase_color};">
                    <div class="score-value" data-target="{phase_score}"">0</div>
                    <div class="score-label">{phase_name.title()}</div>
                </div>
            '''

        # Build flow diagram (use 4-phase if available)
        if is_four_phase:
            flow_html = self._render_four_phase_flow(flow) if flow else ""
        else:
            flow_html = self._render_flow_diagram(flow) if flow else ""

        # Build prompt chain panel
        chain_html = self._render_prompt_chain_panel(prompt_chain)

        # Build phase sections (include reinforcement phase)
        phases_html = ""
        phase_order = ["evaluation", "reinforcement", "risk", "growth"] if is_four_phase else ["evaluation", "risk", "growth"]
        for phase_name in phase_order:
            phase_data = phases.get(phase_name, {})
            if phase_data:
                phase_score = phase_scores.get(phase_name, 0)
                phases_html += self._render_phase_section(
                    phase_name.title(),
                    phase_data,
                    phase_score,
                )

        # Build recommendations panel
        recommendations_html = self._render_recommendations_panel(top_recommendations)

        # Build content
        llm_status = "🤖 AI-Enhanced" if prompt_chain else "📊 Heuristic"

        content = f'''
            <div class="glass dashboard-header">
                <h1>📊 {title}</h1>
                <p class="subtitle">{subtitle}</p>
                <p style="opacity: 0.7; font-size: 0.9em;">{llm_status} Analysis</p>
                <div class="overall-score">
                    {score_circles_html}
                </div>
                <button onclick="exportResults()" style="margin-top: 15px;">
                    📥 Export Results
                </button>
            </div>

            <div class="glass">
                <h2 style="text-align: center; margin-bottom: 15px;">
                    {"4-Phase" if is_four_phase else ""} Analysis Flow
                </h2>
                {flow_html}
            </div>

            <div class="tab-container">
                <div class="tabs">
                    <button class="tab-btn active" data-tab="phases" onclick="switchTab('phases')">
                        📋 Phase Details
                    </button>
                    <button class="tab-btn" data-tab="recommendations" onclick="switchTab('recommendations')">
                        💡 Recommendations
                    </button>
                    <button class="tab-btn" data-tab="ai-chain" onclick="switchTab('ai-chain')">
                        🤖 AI Reasoning
                    </button>
                </div>

                <div id="phases-tab" class="tab-content active">
                    {phases_html}
                </div>

                <div id="recommendations-tab" class="tab-content">
                    {recommendations_html}
                </div>

                <div id="ai-chain-tab" class="tab-content">
                    {chain_html}
                </div>
            </div>

            <div class="glass" style="text-align: center; opacity: 0.7;">
                <p>Generated by LingFrame Evaluation Module</p>
                <p>Click on any step card to expand details • View AI reasoning in the "AI Reasoning" tab</p>
            </div>
        '''

        styles = self.get_dashboard_css()
        scripts = self.get_dashboard_script(analysis.data)

        html = self.wrap_html(
            title=title,
            content=content,
            scripts=scripts,
            styles=styles,
        )

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
