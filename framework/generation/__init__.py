"""
Generation layer for producing revision suggestions from analysis findings.

This module closes the analysis → action gap by:
1. Mapping analysis findings to specific revision suggestions
2. Extracting "Quick Wins" - top actionable improvements
3. Optionally using LLM for context-aware suggestions

Components:
- SuggestionGenerator: Main generator for revision suggestions
- QuickWinExtractor: Identifies top 3 actionable improvements
- SuggestionTemplate: Template-based suggestion generation

NOTE: Generation is still heuristic. Suggestions are starting points
for human revision, not automated corrections.
"""

from .suggestions import (
    SuggestionGenerator,
    Suggestion,
    SuggestionType,
)
from .quick_wins import (
    QuickWinExtractor,
    QuickWin,
)

__all__ = [
    "SuggestionGenerator",
    "Suggestion",
    "SuggestionType",
    "QuickWinExtractor",
    "QuickWin",
]
