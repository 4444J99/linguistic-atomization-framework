"""
Narrative Report Generator - Transforms analysis into coach-like prose.

This module generates human-readable, narrative-style reports from
analysis results. The goal is to make the output feel like sitting
with a thoughtful writing coach, not reading a technical report.

Key design principles:
- Lead with insights, not data
- Use "you/your" language (direct address)
- Explain the "so what" of every finding
- Provide actionable next steps
- Hide all technical implementation details
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .terminology import (
    friendly,
    get_phase_description,
    get_step_description,
    interpret_score,
    score_to_percentage,
    format_score_display,
    get_step_icon,
    get_phase_icon,
    get_score_icon,
    STEP_ICONS,
    PHASE_ICONS,
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class NarrativeFinding:
    """A single finding translated for narrative presentation."""
    category: str  # e.g., "strength", "concern", "opportunity"
    title: str
    explanation: str
    examples: List[str] = field(default_factory=list)
    action: Optional[str] = None  # What to do about it


@dataclass
class NarrativeSection:
    """A section of the narrative report."""
    id: str
    title: str
    icon: str
    summary: str
    findings: List[NarrativeFinding] = field(default_factory=list)
    score: Optional[float] = None
    expandable_content: Optional[str] = None


@dataclass
class NarrativeReport:
    """Complete narrative report structure."""
    document_title: str
    generated_at: datetime
    executive_summary: str
    overall_score: float
    sections: List[NarrativeSection]
    top_recommendations: List[str]
    quick_wins: List[str]
    structural_improvements: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# NARRATIVE GENERATION
# =============================================================================

class NarrativeReportGenerator:
    """
    Generates narrative reports from analysis results.

    Transforms technical analysis output into coach-like prose that
    non-technical writers can understand and act upon.
    """

    def __init__(self, include_icons: bool = True, verbose: bool = False):
        """
        Initialize the generator.

        Args:
            include_icons: Whether to include emoji icons in output
            verbose: Whether to include detailed explanations
        """
        self.include_icons = include_icons
        self.verbose = verbose

    def generate(
        self,
        evaluation_data: Dict[str, Any],
        document_title: str = "Your Document",
        additional_analyses: Optional[Dict[str, Any]] = None,
    ) -> NarrativeReport:
        """
        Generate a narrative report from evaluation analysis data.

        Args:
            evaluation_data: Output from the evaluation analysis module
            document_title: Title to use for the document
            additional_analyses: Optional dict of other analysis outputs
                (semantic, sentiment, etc.) to incorporate

        Returns:
            NarrativeReport object with all narrative content
        """
        additional_analyses = additional_analyses or {}

        # Extract core data
        phases = evaluation_data.get("phases", {})
        summary = evaluation_data.get("summary", {})
        flow = evaluation_data.get("flow", [])

        overall_score = summary.get("overall_score", 0)
        phase_scores = summary.get("phase_scores", {})
        recommendations = summary.get("top_recommendations", [])

        # Generate executive summary
        exec_summary = self._generate_executive_summary(
            overall_score, phase_scores, phases
        )

        # Generate sections for each phase
        sections = []

        # Phase order for presentation
        phase_order = ["evaluation", "reinforcement", "risk", "growth"]

        for phase_name in phase_order:
            phase_data = phases.get(phase_name, {})
            if phase_data:
                section = self._generate_phase_section(
                    phase_name, phase_data, phase_scores.get(phase_name)
                )
                sections.append(section)

        # Add supplementary analysis sections if available
        if "semantic" in additional_analyses:
            sections.append(self._generate_semantic_section(
                additional_analyses["semantic"]
            ))

        if "sentiment" in additional_analyses:
            sections.append(self._generate_sentiment_section(
                additional_analyses["sentiment"]
            ))

        # Categorize recommendations
        quick_wins, structural = self._categorize_recommendations(recommendations)

        return NarrativeReport(
            document_title=document_title,
            generated_at=datetime.now(),
            executive_summary=exec_summary,
            overall_score=overall_score,
            sections=sections,
            top_recommendations=recommendations[:5],
            quick_wins=quick_wins,
            structural_improvements=structural,
            metadata={
                "phases_analyzed": list(phases.keys()),
                "total_recommendations": len(recommendations),
            },
        )

    def _generate_executive_summary(
        self,
        overall_score: float,
        phase_scores: Dict[str, float],
        phases: Dict[str, Any],
    ) -> str:
        """Generate a 3-4 sentence executive summary."""
        label, descriptor = interpret_score(overall_score)
        pct = score_to_percentage(overall_score)

        # Find strongest and weakest areas
        sorted_phases = sorted(
            phase_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        strongest = sorted_phases[0] if sorted_phases else None
        weakest = sorted_phases[-1] if len(sorted_phases) > 1 else None

        # Build summary
        lines = []

        # Opening assessment
        if overall_score >= 0.7:
            lines.append(
                f"Your writing demonstrates strong rhetorical awareness, "
                f"scoring {pct}% overall."
            )
        elif overall_score >= 0.5:
            lines.append(
                f"Your writing has a solid foundation with clear opportunities "
                f"for strengthening, scoring {pct}% overall."
            )
        else:
            lines.append(
                f"Your writing would benefit from focused attention to its "
                f"persuasive architecture, currently scoring {pct}%."
            )

        # Highlight strength
        if strongest and strongest[1] >= 0.5:
            strong_name = friendly(strongest[0])
            lines.append(
                f"Your strongest area is {strong_name.lower()}, which provides "
                f"a foundation to build upon."
            )

        # Identify priority area
        if weakest and weakest[1] < 0.6:
            weak_name = friendly(weakest[0])
            lines.append(
                f"The most impactful improvement would come from addressing "
                f"{weak_name.lower()}."
            )

        # Call to action
        lines.append(
            "The detailed analysis below shows exactly what's working and "
            "what needs attention."
        )

        return " ".join(lines)

    def _generate_phase_section(
        self,
        phase_name: str,
        phase_data: Dict[str, Any],
        phase_score: Optional[float],
    ) -> NarrativeSection:
        """Generate a narrative section for a phase."""
        friendly_name = friendly(phase_name)
        description = get_phase_description(phase_name)
        icon = get_phase_icon(phase_name) if self.include_icons else ""

        # Gather findings from all steps in this phase
        findings = []
        for step_name, step_data in phase_data.items():
            step_findings = self._extract_step_findings(step_name, step_data)
            findings.extend(step_findings)

        # Generate summary for the phase
        summary = self._generate_phase_summary(phase_name, phase_data, phase_score)

        return NarrativeSection(
            id=phase_name,
            title=friendly_name,
            icon=icon,
            summary=summary,
            findings=findings,
            score=phase_score,
        )

    def _generate_phase_summary(
        self,
        phase_name: str,
        phase_data: Dict[str, Any],
        score: Optional[float],
    ) -> str:
        """Generate a brief summary for a phase."""
        if score is None:
            return get_phase_description(phase_name)

        label, _ = interpret_score(score)
        pct = score_to_percentage(score)

        phase_summaries = {
            "evaluation": {
                "high": f"Your persuasive architecture is well-constructed ({pct}%). You effectively balance logic, emotion, and credibility.",
                "mid": f"Your persuasive approach shows promise ({pct}%) but could be more intentional in how you use logic, emotion, and credibility.",
                "low": f"Your persuasive structure needs attention ({pct}%). Consider how you're using evidence, emotional connection, and authority.",
            },
            "reinforcement": {
                "high": f"Your argument holds together well ({pct}%). Your reasoning is internally consistent.",
                "mid": f"Your logic is mostly sound ({pct}%), though some connections could be tightened.",
                "low": f"There are gaps in your argument's internal logic ({pct}%). Reviewers may notice inconsistencies.",
            },
            "risk": {
                "high": f"You've anticipated potential criticisms well ({pct}%). Your argument is defensible.",
                "mid": f"Some vulnerabilities exist ({pct}%). Consider how critics might challenge your claims.",
                "low": f"Your argument has notable blind spots ({pct}%). This section shows where you're most vulnerable.",
            },
            "growth": {
                "high": f"Strong opportunities for development exist ({pct}%). Your writing has unrealized potential.",
                "mid": f"Several growth paths are available ({pct}%). The suggestions below can guide your revisions.",
                "low": f"Fundamental improvements are needed ({pct}%). Start with the quick wins below.",
            },
        }

        summaries = phase_summaries.get(phase_name, {})
        if score >= 0.7:
            return summaries.get("high", f"Score: {pct}%")
        elif score >= 0.4:
            return summaries.get("mid", f"Score: {pct}%")
        else:
            return summaries.get("low", f"Score: {pct}%")

    def _extract_step_findings(
        self,
        step_name: str,
        step_data: Dict[str, Any],
    ) -> List[NarrativeFinding]:
        """Extract narrative findings from a step's data."""
        findings = []
        step_icon = get_step_icon(step_name) if self.include_icons else ""
        friendly_step = friendly(step_name)

        # Get score for context
        score = step_data.get("score", 0.5)
        label, _ = interpret_score(score)

        # Extract findings (adapt to different step data structures)
        raw_findings = step_data.get("findings", [])
        llm_insights = step_data.get("llm_insights", {})

        # Handle LLM-enhanced findings
        if llm_insights:
            strengths = llm_insights.get("strengths", [])
            concerns = llm_insights.get("concerns", [])
            suggestions = llm_insights.get("suggestions", [])

            for s in strengths[:2]:  # Limit to top 2
                findings.append(NarrativeFinding(
                    category="strength",
                    title=f"{step_icon} {friendly_step}: Strength",
                    explanation=s,
                ))

            for c in concerns[:2]:
                findings.append(NarrativeFinding(
                    category="concern",
                    title=f"{step_icon} {friendly_step}: Area for Attention",
                    explanation=c,
                ))

        # Handle traditional findings
        for finding in raw_findings[:3]:  # Limit to top 3
            if isinstance(finding, dict):
                text = finding.get("text", finding.get("description", str(finding)))
                category = finding.get("type", "observation")
            else:
                text = str(finding)
                category = "observation"

            # Categorize based on content
            if any(word in text.lower() for word in ["strong", "effective", "good", "well"]):
                category = "strength"
            elif any(word in text.lower() for word in ["weak", "missing", "lack", "concern"]):
                category = "concern"

            findings.append(NarrativeFinding(
                category=category,
                title=f"{step_icon} {friendly_step}",
                explanation=text,
            ))

        # Extract recommendations as opportunities
        recs = step_data.get("recommendations", [])
        for rec in recs[:2]:  # Limit to top 2
            findings.append(NarrativeFinding(
                category="opportunity",
                title=f"{step_icon} {friendly_step}: Suggestion",
                explanation=rec,
            ))

        return findings

    def _generate_semantic_section(
        self,
        semantic_data: Dict[str, Any],
    ) -> NarrativeSection:
        """Generate a section from semantic analysis."""
        # Extract key themes
        themes = semantic_data.get("themes", [])
        connections = semantic_data.get("connections", [])

        findings = []
        if themes:
            top_themes = themes[:5]
            theme_names = [t.get("name", t.get("id", "unknown")) for t in top_themes]
            findings.append(NarrativeFinding(
                category="observation",
                title="Your Central Themes",
                explanation=f"Your writing centers on these key ideas: {', '.join(theme_names)}.",
            ))

        return NarrativeSection(
            id="themes",
            title="How Your Ideas Connect",
            icon="🔗" if self.include_icons else "",
            summary="This shows how your themes relate to each other and which ideas dominate your writing.",
            findings=findings,
        )

    def _generate_sentiment_section(
        self,
        sentiment_data: Dict[str, Any],
    ) -> NarrativeSection:
        """Generate a section from sentiment analysis."""
        overall = sentiment_data.get("overall", {})
        arc = sentiment_data.get("arc", [])

        findings = []

        # Overall tone
        if overall:
            compound = overall.get("compound", 0)
            if compound > 0.3:
                tone = "optimistic and positive"
            elif compound > 0:
                tone = "cautiously positive"
            elif compound > -0.3:
                tone = "measured and neutral"
            else:
                tone = "serious or critical"

            findings.append(NarrativeFinding(
                category="observation",
                title="Your Overall Tone",
                explanation=f"Your writing has a {tone} emotional quality.",
            ))

        # Emotional arc
        if arc and len(arc) > 3:
            # Analyze trajectory
            start_sentiment = arc[0].get("compound", 0)
            end_sentiment = arc[-1].get("compound", 0)

            if end_sentiment > start_sentiment + 0.2:
                trajectory = "builds toward a more positive conclusion"
            elif end_sentiment < start_sentiment - 0.2:
                trajectory = "moves toward a more serious or urgent tone"
            else:
                trajectory = "maintains a consistent emotional tone throughout"

            findings.append(NarrativeFinding(
                category="observation",
                title="Your Emotional Arc",
                explanation=f"Your writing {trajectory}.",
            ))

        return NarrativeSection(
            id="emotion",
            title="Your Emotional Journey",
            icon="💓" if self.include_icons else "",
            summary="This tracks the emotional tone of your writing from beginning to end.",
            findings=findings,
        )

    def _categorize_recommendations(
        self,
        recommendations: List[str],
    ) -> tuple:
        """Separate recommendations into quick wins and structural changes."""
        quick_wins = []
        structural = []

        quick_keywords = ["add", "include", "mention", "clarify", "rephrase", "consider"]
        structural_keywords = ["restructure", "reorganize", "reframe", "develop", "expand", "strengthen"]

        for rec in recommendations:
            rec_lower = rec.lower()
            if any(kw in rec_lower for kw in quick_keywords):
                quick_wins.append(rec)
            elif any(kw in rec_lower for kw in structural_keywords):
                structural.append(rec)
            else:
                # Default to structural if longer, quick if shorter
                if len(rec) > 100:
                    structural.append(rec)
                else:
                    quick_wins.append(rec)

        return quick_wins[:5], structural[:5]

    def to_html(
        self,
        report: NarrativeReport,
        template_path: Optional[Path] = None,
    ) -> str:
        """
        Render the narrative report to HTML.

        Args:
            report: The NarrativeReport to render
            template_path: Optional custom template path

        Returns:
            HTML string
        """
        if template_path and template_path.exists():
            # Use custom template
            template_content = template_path.read_text(encoding="utf-8")
            return self._render_template(template_content, report)

        # Use built-in template
        return self._render_builtin_template(report)

    def _render_builtin_template(self, report: NarrativeReport) -> str:
        """Render using the built-in HTML template."""
        # Build sections HTML
        sections_html = []
        for section in report.sections:
            findings_html = []
            for finding in section.findings:
                category_class = f"finding-{finding.category}"
                findings_html.append(f"""
                <div class="finding {category_class}">
                    <h4>{finding.title}</h4>
                    <p>{finding.explanation}</p>
                    {f'<p class="action"><strong>Action:</strong> {finding.action}</p>' if finding.action else ''}
                </div>
                """)

            score_html = ""
            if section.score is not None:
                pct = score_to_percentage(section.score)
                score_html = f'<div class="score-badge">{pct}%</div>'

            sections_html.append(f"""
            <section class="report-section" id="section-{section.id}">
                <div class="section-header">
                    <span class="section-icon">{section.icon}</span>
                    <h2>{section.title}</h2>
                    {score_html}
                </div>
                <p class="section-summary">{section.summary}</p>
                <div class="findings">
                    {''.join(findings_html)}
                </div>
            </section>
            """)

        # Build recommendations HTML
        recs_html = "\n".join(
            f"<li>{rec}</li>" for rec in report.top_recommendations
        )
        quick_wins_html = "\n".join(
            f"<li>{rec}</li>" for rec in report.quick_wins
        ) if report.quick_wins else "<li>See detailed recommendations above</li>"
        structural_html = "\n".join(
            f"<li>{rec}</li>" for rec in report.structural_improvements
        ) if report.structural_improvements else "<li>See detailed recommendations above</li>"

        overall_pct = score_to_percentage(report.overall_score)
        overall_label, overall_desc = interpret_score(report.overall_score)
        score_icon = get_score_icon(report.overall_score)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Writing Analysis: {report.document_title}</title>
    <style>
        :root {{
            --primary: #2c3e50;
            --secondary: #3498db;
            --success: #27ae60;
            --warning: #f39c12;
            --danger: #e74c3c;
            --light: #ecf0f1;
            --dark: #2c3e50;
            --font-main: 'Segoe UI', system-ui, -apple-system, sans-serif;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: var(--font-main);
            line-height: 1.6;
            color: var(--dark);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        header {{
            background: var(--primary);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        header h1 {{
            font-size: 1.8em;
            margin-bottom: 10px;
        }}

        .subtitle {{
            opacity: 0.8;
            font-size: 1.1em;
        }}

        .score-hero {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            padding: 30px;
            background: var(--light);
        }}

        .score-circle {{
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: white;
            border: 6px solid var(--secondary);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}

        .score-number {{
            font-size: 2.2em;
            font-weight: bold;
            color: var(--primary);
        }}

        .score-label {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
        }}

        .executive-summary {{
            padding: 30px 40px;
            background: white;
            border-bottom: 1px solid var(--light);
        }}

        .executive-summary h2 {{
            color: var(--primary);
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .executive-summary p {{
            font-size: 1.1em;
            color: #555;
        }}

        main {{
            padding: 20px 40px 40px;
        }}

        .report-section {{
            margin-bottom: 40px;
            padding: 25px;
            background: #fafafa;
            border-radius: 12px;
            border-left: 4px solid var(--secondary);
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
        }}

        .section-icon {{
            font-size: 1.5em;
        }}

        .section-header h2 {{
            flex-grow: 1;
            color: var(--primary);
            font-size: 1.4em;
        }}

        .score-badge {{
            background: var(--secondary);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }}

        .section-summary {{
            color: #666;
            margin-bottom: 20px;
            font-style: italic;
        }}

        .findings {{
            display: grid;
            gap: 15px;
        }}

        .finding {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 3px solid #ddd;
        }}

        .finding-strength {{
            border-left-color: var(--success);
        }}

        .finding-concern {{
            border-left-color: var(--warning);
        }}

        .finding-opportunity {{
            border-left-color: var(--secondary);
        }}

        .finding h4 {{
            color: var(--primary);
            margin-bottom: 8px;
            font-size: 1em;
        }}

        .finding p {{
            color: #555;
        }}

        .finding .action {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px dashed #ddd;
            color: var(--secondary);
        }}

        .recommendations {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px 40px;
            margin-top: 40px;
        }}

        .recommendations h2 {{
            margin-bottom: 20px;
        }}

        .rec-columns {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }}

        .rec-column h3 {{
            font-size: 1.1em;
            margin-bottom: 15px;
            opacity: 0.9;
        }}

        .rec-column ul {{
            list-style: none;
        }}

        .rec-column li {{
            padding: 10px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-left: 20px;
            position: relative;
        }}

        .rec-column li::before {{
            content: "→";
            position: absolute;
            left: 0;
            color: var(--secondary);
        }}

        footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 0.9em;
            border-top: 1px solid var(--light);
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            header, .executive-summary, main, .recommendations {{
                padding: 20px;
            }}

            .rec-columns {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Writing Analysis</h1>
            <p class="subtitle">{report.document_title}</p>
        </header>

        <div class="score-hero">
            <div class="score-circle">
                <span class="score-number">{overall_pct}%</span>
                <span class="score-label">{overall_label}</span>
            </div>
            <div>
                <p><strong>{score_icon} {overall_desc}</strong></p>
                <p style="color: #666;">Generated {report.generated_at.strftime('%B %d, %Y')}</p>
            </div>
        </div>

        <div class="executive-summary">
            <h2>📋 Executive Summary</h2>
            <p>{report.executive_summary}</p>
        </div>

        <main>
            {''.join(sections_html)}
        </main>

        <div class="recommendations">
            <h2>📌 What to Do Next</h2>
            <div class="rec-columns">
                <div class="rec-column">
                    <h3>⚡ Quick Wins</h3>
                    <ul>
                        {quick_wins_html}
                    </ul>
                </div>
                <div class="rec-column">
                    <h3>🏗️ Structural Improvements</h3>
                    <ul>
                        {structural_html}
                    </ul>
                </div>
            </div>
        </div>

        <footer>
            <p>Generated by LingFrame • Rhetorical Analysis Framework</p>
        </footer>
    </div>
</body>
</html>"""

    def _render_template(self, template: str, report: NarrativeReport) -> str:
        """Render using a custom template (Jinja2-style placeholders)."""
        # Simple template variable substitution
        # For more complex templates, integrate Jinja2
        replacements = {
            "{{ document_title }}": report.document_title,
            "{{ overall_score }}": str(score_to_percentage(report.overall_score)),
            "{{ executive_summary }}": report.executive_summary,
            "{{ generated_at }}": report.generated_at.strftime("%B %d, %Y at %I:%M %p"),
        }

        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        return result

    def to_json(self, report: NarrativeReport) -> str:
        """Export the report as JSON for further processing."""
        data = {
            "document_title": report.document_title,
            "generated_at": report.generated_at.isoformat(),
            "executive_summary": report.executive_summary,
            "overall_score": report.overall_score,
            "sections": [
                {
                    "id": s.id,
                    "title": s.title,
                    "summary": s.summary,
                    "score": s.score,
                    "findings": [
                        {
                            "category": f.category,
                            "title": f.title,
                            "explanation": f.explanation,
                            "action": f.action,
                        }
                        for f in s.findings
                    ],
                }
                for s in report.sections
            ],
            "recommendations": {
                "top": report.top_recommendations,
                "quick_wins": report.quick_wins,
                "structural": report.structural_improvements,
            },
            "metadata": report.metadata,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
