"""
UI Components for LingFrame Web Application.

Components:
- styles: Custom CSS styling
- header: App header/branding
- upload: Document upload interface
- progress: Analysis progress indicator
- results: Results display with tabs
- analysis_engine: Analysis orchestration
- corpus_observatory: Browse and compare corpus texts
- rhetoric_gym: Practice rhetorical techniques
"""

from .styles import apply_custom_styles
from .header import render_header
from .upload import render_upload_section
from .progress import render_progress
from .results import render_results
from .analysis_engine import run_analysis, AnalysisState

# Optional imports for new features (may not exist yet)
try:
    from .corpus_observatory import render_corpus_observatory
except ImportError:
    render_corpus_observatory = None

try:
    from .rhetoric_gym import render_rhetoric_gym
except ImportError:
    render_rhetoric_gym = None

__all__ = [
    "apply_custom_styles",
    "render_header",
    "render_upload_section",
    "render_progress",
    "render_results",
    "run_analysis",
    "AnalysisState",
    "render_corpus_observatory",
    "render_rhetoric_gym",
]
