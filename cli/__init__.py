"""
CLI interface for the Linguistic Analysis Framework.

Provides command-line access to framework functionality:
- lingframe atomize: Atomize source documents
- lingframe analyze: Run analysis pipelines
- lingframe visualize: Generate visualizations
- lingframe run: Complete pipeline execution
"""

from .main import main, create_parser

__all__ = ["main", "create_parser"]
