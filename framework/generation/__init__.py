"""
Generation layer for producing revision suggestions from analysis findings.

This module closes the analysis → action gap by:
1. Mapping analysis findings to specific revision suggestions
2. Extracting "Quick Wins" - top actionable improvements
3. Creating before/after revision comparisons
4. Optionally using LLM for context-aware suggestions

Components:
- SuggestionGenerator: Main generator for revision suggestions
- QuickWinExtractor: Identifies top 3 actionable improvements
- RevisionComparator: Creates before/after comparison views

NOTE: Generation is still heuristic. Suggestions are starting points
for human revision, not automated corrections.
"""

from .suggestions import (
    SuggestionGenerator,
    Suggestion,
    SuggestionType,
    SuggestionPriority,
)
from .quick_wins import (
    QuickWinExtractor,
    QuickWin,
)
from .revision import (
    RevisionComparator,
    RevisionComparison,
    TextChange,
    ChangeType,
    ImprovementMetrics,
    create_revision_view,
)

__all__ = [
    # Suggestions
    "SuggestionGenerator",
    "Suggestion",
    "SuggestionType",
    "SuggestionPriority",
    # Quick Wins
    "QuickWinExtractor",
    "QuickWin",
    # Revision Comparison
    "RevisionComparator",
    "RevisionComparison",
    "TextChange",
    "ChangeType",
    "ImprovementMetrics",
    "create_revision_view",
]
