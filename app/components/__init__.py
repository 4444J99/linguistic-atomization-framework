"""
UI Components for LingFrame Web Application.

Components:
- styles: Custom CSS styling
- header: App header/branding
- upload: Document upload interface
- progress: Analysis progress indicator
- results: Results display with tabs
- analysis_engine: Analysis orchestration
"""

from .styles import apply_custom_styles
from .header import render_header
from .upload import render_upload_section
from .progress import render_progress
from .results import render_results
from .analysis_engine import run_analysis, AnalysisState

__all__ = [
    "apply_custom_styles",
    "render_header",
    "render_upload_section",
    "render_progress",
    "render_results",
    "run_analysis",
    "AnalysisState",
]
