"""
Output Formatters - Generate user-friendly output from analysis results.

This module provides formatters that transform technical analysis output
into accessible formats for non-technical users (writers, academics).

Output formats:
- Narrative: Coach-like prose report
- Annotated: Document with inline annotations (future)
"""

from .terminology import FRIENDLY_NAMES, friendly, get_phase_description, get_step_description
from .narrative import NarrativeReportGenerator

__all__ = [
    "FRIENDLY_NAMES",
    "friendly",
    "get_phase_description",
    "get_step_description",
    "NarrativeReportGenerator",
]
