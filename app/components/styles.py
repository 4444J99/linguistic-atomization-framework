"""
Custom Styles - Writer-friendly CSS for the Streamlit app.

Design principles:
- Clean, uncluttered interface
- Warm, approachable colors
- Clear typography
- Focus on content, not chrome
"""

import streamlit as st


def apply_custom_styles():
    """Apply custom CSS styling to the Streamlit app."""
    st.markdown("""
    <style>
    /* ==========================================================================
       ROOT VARIABLES
       ========================================================================== */
    :root {
        --color-primary: #2c3e50;
        --color-secondary: #3498db;
        --color-accent: #9b59b6;
        --color-success: #27ae60;
        --color-warning: #f39c12;
        --color-danger: #e74c3c;
        --color-light: #f8f9fa;
        --color-dark: #2c3e50;
        --color-muted: #6c757d;
        --font-main: 'Segoe UI', system-ui, -apple-system, sans-serif;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.12);
        --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
        --shadow-lg: 0 10px 25px rgba(0,0,0,0.15);
        --radius-sm: 4px;
        --radius-md: 8px;
        --radius-lg: 16px;
    }

    /* ==========================================================================
       GLOBAL STYLES
       ========================================================================== */
    .stApp {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* ==========================================================================
       TYPOGRAPHY
       ========================================================================== */
    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-main);
        color: var(--color-primary);
    }

    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--color-primary);
        margin-bottom: 0.5rem;
        text-align: center;
    }

    .main-subtitle {
        font-size: 1.2rem;
        color: var(--color-muted);
        text-align: center;
        margin-bottom: 2rem;
    }

    /* ==========================================================================
       UPLOAD AREA
       ========================================================================== */
    .upload-container {
        background: white;
        border: 2px dashed #dee2e6;
        border-radius: var(--radius-lg);
        padding: 3rem 2rem;
        text-align: center;
        transition: all 0.3s ease;
        margin: 2rem auto;
        max-width: 600px;
    }

    .upload-container:hover {
        border-color: var(--color-secondary);
        background: #f8fbff;
    }

    .upload-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }

    .upload-text {
        font-size: 1.1rem;
        color: var(--color-dark);
        margin-bottom: 0.5rem;
    }

    .upload-hint {
        font-size: 0.9rem;
        color: var(--color-muted);
    }

    /* ==========================================================================
       SCORE DISPLAY
       ========================================================================== */
    .score-card {
        background: white;
        border-radius: var(--radius-lg);
        padding: 2rem;
        box-shadow: var(--shadow-md);
        text-align: center;
        transition: transform 0.2s ease;
    }

    .score-card:hover {
        transform: translateY(-2px);
    }

    .score-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem;
        background: linear-gradient(135deg, var(--color-secondary), var(--color-accent));
        color: white;
        box-shadow: var(--shadow-lg);
    }

    .score-value {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
    }

    .score-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        opacity: 0.9;
    }

    /* ==========================================================================
       PHASE CARDS
       ========================================================================== */
    .phase-card {
        background: white;
        border-radius: var(--radius-md);
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--color-secondary);
        box-shadow: var(--shadow-sm);
    }

    .phase-card.evaluation { border-left-color: #3498db; }
    .phase-card.reinforcement { border-left-color: #9b59b6; }
    .phase-card.risk { border-left-color: #e74c3c; }
    .phase-card.growth { border-left-color: #27ae60; }

    .phase-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }

    .phase-icon {
        font-size: 1.5rem;
    }

    .phase-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--color-primary);
        flex-grow: 1;
    }

    .phase-score {
        background: var(--color-light);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }

    /* ==========================================================================
       FINDINGS
       ========================================================================== */
    .finding {
        background: var(--color-light);
        border-radius: var(--radius-sm);
        padding: 1rem;
        margin-bottom: 0.75rem;
        border-left: 3px solid #dee2e6;
    }

    .finding.strength { border-left-color: var(--color-success); }
    .finding.concern { border-left-color: var(--color-warning); }
    .finding.opportunity { border-left-color: var(--color-secondary); }

    .finding-title {
        font-weight: 600;
        color: var(--color-primary);
        margin-bottom: 0.25rem;
        font-size: 0.95rem;
    }

    .finding-text {
        color: var(--color-dark);
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* ==========================================================================
       RECOMMENDATIONS
       ========================================================================== */
    .recommendations-section {
        background: var(--color-primary);
        color: white;
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin-top: 2rem;
    }

    .recommendations-section h3 {
        color: white;
        margin-bottom: 1.5rem;
    }

    .rec-item {
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }

    .rec-item:last-child {
        border-bottom: none;
    }

    .rec-arrow {
        color: var(--color-secondary);
        font-weight: bold;
    }

    /* ==========================================================================
       BUTTONS
       ========================================================================== */
    .stButton > button {
        background: linear-gradient(135deg, var(--color-secondary), var(--color-accent));
        color: white;
        border: none;
        border-radius: var(--radius-md);
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }

    /* ==========================================================================
       TABS
       ========================================================================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--color-light);
        padding: 0.5rem;
        border-radius: var(--radius-md);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm);
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: white;
        box-shadow: var(--shadow-sm);
    }

    /* ==========================================================================
       EXECUTIVE SUMMARY
       ========================================================================== */
    .executive-summary {
        background: white;
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-md);
    }

    .executive-summary h3 {
        color: var(--color-primary);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .executive-summary p {
        font-size: 1.1rem;
        line-height: 1.7;
        color: var(--color-dark);
    }

    /* ==========================================================================
       PROGRESS ANIMATION
       ========================================================================== */
    .progress-container {
        text-align: center;
        padding: 3rem;
    }

    .progress-text {
        font-size: 1.2rem;
        color: var(--color-primary);
        margin-top: 1rem;
    }

    .progress-subtext {
        font-size: 0.9rem;
        color: var(--color-muted);
        margin-top: 0.5rem;
    }

    /* ==========================================================================
       RESPONSIVE
       ========================================================================== */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.8rem;
        }

        .upload-container {
            padding: 2rem 1rem;
        }

        .score-circle {
            width: 100px;
            height: 100px;
        }

        .score-value {
            font-size: 2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
