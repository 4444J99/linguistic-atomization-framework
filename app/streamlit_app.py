#!/usr/bin/env python3
"""
LingFrame Web Application - Main Entry Point

A writer-friendly interface for rhetorical analysis.
No coding required - just upload and see results.

Run with:
    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

# Add framework to path
framework_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(framework_root))

import streamlit as st

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="LingFrame - Writing Analysis",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": """
        ## LingFrame
        Rhetorical analysis for writers.

        Upload your document to discover:
        - What's working in your writing
        - Where critics could attack
        - How to make it stronger
        """
    }
)

# Import components after page config
from app.components.styles import apply_custom_styles
from app.components.header import render_header
from app.components.upload import render_upload_section
from app.components.progress import render_progress
from app.components.results import render_results
from app.components.analysis_engine import run_analysis, AnalysisState


def main():
    """Main application entry point."""
    # Apply custom styling
    apply_custom_styles()

    # Initialize session state
    if "analysis_state" not in st.session_state:
        st.session_state.analysis_state = AnalysisState.READY
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    if "document_title" not in st.session_state:
        st.session_state.document_title = None
    if "uploaded_text" not in st.session_state:
        st.session_state.uploaded_text = None

    # Render header
    render_header()

    # Main content based on state
    state = st.session_state.analysis_state

    if state == AnalysisState.READY:
        # Show upload interface
        render_upload_section()

    elif state == AnalysisState.ANALYZING:
        # Show progress
        render_progress()

        # Run analysis (this updates state when complete)
        with st.spinner(""):
            results = run_analysis(
                st.session_state.uploaded_text,
                st.session_state.document_title,
            )
            if results:
                st.session_state.analysis_results = results
                st.session_state.analysis_state = AnalysisState.COMPLETE
                st.rerun()
            else:
                st.session_state.analysis_state = AnalysisState.ERROR
                st.rerun()

    elif state == AnalysisState.COMPLETE:
        # Show results
        render_results(
            st.session_state.analysis_results,
            st.session_state.document_title,
        )

        # Option to analyze another document
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📄 Analyze Another Document", use_container_width=True):
                # Reset state
                st.session_state.analysis_state = AnalysisState.READY
                st.session_state.analysis_results = None
                st.session_state.document_title = None
                st.session_state.uploaded_text = None
                st.rerun()

    elif state == AnalysisState.ERROR:
        st.error("Something went wrong during analysis. Please try again.")
        if st.button("🔄 Try Again"):
            st.session_state.analysis_state = AnalysisState.READY
            st.rerun()


if __name__ == "__main__":
    main()
