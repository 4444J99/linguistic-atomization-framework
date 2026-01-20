"""
Progress Component - Analysis progress indicator.
"""

import streamlit as st
import time


def render_progress():
    """Render the analysis progress indicator."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div class="progress-container">
            <div style="font-size: 4rem;">🔍</div>
            <div class="progress-text">Analyzing your writing...</div>
            <div class="progress-subtext">This usually takes 10-30 seconds</div>
        </div>
        """, unsafe_allow_html=True)

        # Progress bar with stages
        progress_bar = st.progress(0)
        status_text = st.empty()

        stages = [
            (0.1, "📖 Reading document structure..."),
            (0.3, "🧠 Analyzing rhetorical patterns..."),
            (0.5, "📊 Evaluating logic and evidence..."),
            (0.7, "💓 Measuring emotional impact..."),
            (0.85, "🔍 Finding blind spots..."),
            (0.95, "✨ Generating insights..."),
        ]

        for progress, message in stages:
            progress_bar.progress(progress)
            status_text.markdown(f"<p style='text-align: center; color: #6c757d;'>{message}</p>",
                                unsafe_allow_html=True)
            time.sleep(0.5)  # Small delay for visual feedback
