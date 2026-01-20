"""
Output Formatters - Generate user-friendly output from analysis results.

This module provides formatters that transform technical analysis output
into accessible formats for non-technical users (writers, academics).

Output formats:
- Narrative: Coach-like prose report
- Scholarly: Academic formats (LaTeX, TEI-XML, CONLL)
- Annotated: Document with inline annotations (future)
"""

from .terminology import FRIENDLY_NAMES, friendly, get_phase_description, get_step_description
from .narrative import NarrativeReportGenerator
from .scholarly import (
    ScholarlyExporter,
    LaTeXExporter,
    TEIXMLExporter,
    CONLLExporter,
    ExportMetadata,
    export_analysis,
    get_exporter,
)

__all__ = [
    # Terminology
    "FRIENDLY_NAMES",
    "friendly",
    "get_phase_description",
    "get_step_description",
    # Narrative
    "NarrativeReportGenerator",
    # Scholarly exports
    "ScholarlyExporter",
    "LaTeXExporter",
    "TEIXMLExporter",
    "CONLLExporter",
    "ExportMetadata",
    "export_analysis",
    "get_exporter",
]
