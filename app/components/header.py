"""
Header Component - App branding and navigation.
"""

import streamlit as st


def render_header():
    """Render the application header."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem;">
        <h1 class="main-title">📝 LingFrame</h1>
        <p class="main-subtitle">Discover the architecture of your argument</p>
    </div>
    """, unsafe_allow_html=True)
