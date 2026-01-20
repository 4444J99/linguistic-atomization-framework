"""
CLI interface for the Linguistic Analysis Framework.

Provides command-line access to framework functionality:

Quick Start (no setup required):
  lingframe analyze essay.pdf     # Analyze and open report
  lingframe quick essay.pdf       # Quick console summary

Project-based (advanced):
  lingframe run -p project        # Full pipeline
  lingframe atomize -p project    # Atomize documents
  lingframe analyze -p project    # Run analysis modules
  lingframe visualize -p project  # Generate visualizations
"""

from .main import main, create_parser

__all__ = ["main", "create_parser"]
