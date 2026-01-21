"""
Results Component - Display analysis results with tabs.

Provides three views:
1. Summary - Executive summary and key metrics
2. Details - Phase-by-phase findings
3. Explore - Interactive exploration (future: visualizations)
"""

import streamlit as st
from typing import Any, Dict

from framework.output.terminology import (
    friendly,
    interpret_score,
    score_to_percentage,
    get_phase_icon,
    get_step_icon,
)


def render_results(results: Dict[str, Any], document_title: str):
    """Render the complete results interface."""
    # Get narrative report from results
    report = results.get("narrative_report")
    if not report:
        st.error("Analysis results not available.")
        return

    # Header with overall score
    render_score_header(report)

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Summary", "📊 Details", "🔍 Explore"])

    with tab1:
        render_summary_tab(report, results)

    with tab2:
        render_details_tab(report, results)

    with tab3:
        render_explore_tab(report, results)


def render_score_header(report):
    """Render the score header section."""
    overall_score = report.overall_score
    score_label, score_desc = interpret_score(overall_score)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        st.markdown(f"""
        <div class="score-card">
            <div class="score-circle">
                <span class="score-value">{int(overall_score)}%</span>
                <span class="score-label">{score_label}</span>
            </div>
            <p style="color: #6c757d; margin-top: 0.5rem;">{score_desc}</p>
        </div>
        """, unsafe_allow_html=True)


def render_summary_tab(report, results: Dict[str, Any]):
    """Render the summary tab with executive summary and key metrics."""
    # Executive Summary
    st.markdown(f"""
    <div class="executive-summary">
        <h3>📋 Executive Summary</h3>
        <p>{report.executive_summary}</p>
    </div>
    """, unsafe_allow_html=True)

    # Document stats
    corpus_stats = results.get("corpus_stats", {})
    if corpus_stats:
        st.markdown("### 📊 Document Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Words", f"{corpus_stats.get('words', 0):,}")
        with col2:
            st.metric("Sections", corpus_stats.get('themes', 0))
        with col3:
            st.metric("Paragraphs", corpus_stats.get('paragraphs', 0))
        with col4:
            st.metric("Sentences", corpus_stats.get('sentences', 0))

    # Quick recommendations
    st.markdown("### 📌 What to Do Next")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**⚡ Quick Wins**")
        if report.quick_wins:
            for rec in report.quick_wins[:3]:
                st.markdown(f"→ {rec}")
        else:
            st.markdown("_See detailed recommendations below_")

    with col2:
        st.markdown("**🏗️ Structural Improvements**")
        if report.structural_improvements:
            for rec in report.structural_improvements[:3]:
                st.markdown(f"→ {rec}")
        else:
            st.markdown("_See detailed recommendations below_")


def render_details_tab(report, results: Dict[str, Any]):
    """Render the details tab with phase-by-phase findings."""
    st.markdown("### Phase-by-Phase Analysis")
    st.markdown("_Click each phase to expand and see detailed findings._")

    # Render each phase as an expandable section
    for section in report.sections:
        phase_class = section.id
        icon = section.icon or get_phase_icon(section.id)
        score = section.score

        # Create expandable section
        with st.expander(f"{icon} **{section.title}** — {int(score) if score else '—'}%", expanded=False):
            # Summary
            st.markdown(f"_{section.summary}_")

            # Findings
            if section.findings:
                st.markdown("**Findings:**")

                for finding in section.findings:
                    # Determine category styling
                    category = finding.category
                    if category == "strength":
                        badge = "🟢"
                    elif category == "concern":
                        badge = "🟡"
                    elif category == "opportunity":
                        badge = "🔵"
                    else:
                        badge = "⚪"

                    st.markdown(f"""
                    <div class="finding {category}">
                        <div class="finding-title">{badge} {finding.title}</div>
                        <div class="finding-text">{finding.explanation}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # All recommendations
    st.markdown("---")
    st.markdown("### 📋 All Recommendations")

    if report.top_recommendations:
        for i, rec in enumerate(report.top_recommendations, 1):
            st.markdown(f"{i}. {rec}")
    else:
        st.markdown("_No specific recommendations generated._")


def render_explore_tab(report, results: Dict[str, Any]):
    """Render the explore tab with interactive visualizations."""
    import streamlit.components.v1 as components

    from .visualization_bridge import (
        get_available_visualizations,
        render_visualization,
        VISUALIZATION_INFO,
    )

    st.markdown("### 🔍 Explore Your Analysis")
    st.markdown("_Click each section to expand and interact with the visualization._")

    # Get available visualizations based on what analyses ran
    available_viz = get_available_visualizations(results)

    if not available_viz:
        st.info("No interactive visualizations available. Run more analysis modules to see rich visualizations.")

    # Render each visualization in an expander
    # Define the order we want to show them (prioritize most useful)
    viz_order = ["force_graph", "sentiment_chart", "sankey", "entity_browser", "evaluation_dashboard"]

    for adapter_type in viz_order:
        info = VISUALIZATION_INFO.get(adapter_type)
        if not info:
            continue

        # Check if this visualization is available
        is_available = any(v["adapter_type"] == adapter_type for v in available_viz)

        expander_label = f"{info['icon']} **{info['name']}**"

        # For available visualizations, show them in expanders
        if is_available:
            with st.expander(expander_label, expanded=False):
                st.markdown(f"_{info['description']}_")

                # Add a loading spinner while generating visualization
                with st.spinner(f"Loading {info['name']}..."):
                    html_content, success = render_visualization(
                        adapter_type=adapter_type,
                        results=results,
                        height=600,
                    )

                if success:
                    # Render the interactive visualization
                    components.html(html_content, height=620, scrolling=True)
                else:
                    st.error(f"Could not generate {info['name']} visualization.")
                    st.code(html_content, language="html")
        else:
            # Show disabled expander for unavailable visualizations
            with st.expander(f"🔒 {info['name']} (not available)", expanded=False):
                st.markdown(f"_{info['description']}_")
                st.info(f"Run {info['analysis_type']} analysis to enable this visualization.")

    # Export section
    st.markdown("---")
    st.markdown("### 📥 Export Options")

    col1, col2 = st.columns(2)

    with col1:
        # Generate HTML report
        from framework.output import NarrativeReportGenerator
        generator = NarrativeReportGenerator(include_icons=True)
        html_content = generator.to_html(report)

        st.download_button(
            label="📄 Download HTML Report",
            data=html_content,
            file_name=f"{report.document_title.lower().replace(' ', '_')}_analysis.html",
            mime="text/html",
            use_container_width=True,
        )

    with col2:
        # Export JSON
        import json
        json_content = generator.to_json(report)

        st.download_button(
            label="📊 Download JSON Data",
            data=json_content,
            file_name=f"{report.document_title.lower().replace(' ', '_')}_analysis.json",
            mime="application/json",
            use_container_width=True,
        )
