"""
Revision Comparison Module for LingFrame.

Provides before/after comparison views for text revisions based on
suggestions from the generation layer. Enables users to see exactly
how suggested changes would improve their text.

Features:
- Side-by-side comparison of original and revised text
- Inline diff highlighting
- Improvement metrics calculation
- Multiple output formats (text, HTML, JSON)
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class ChangeType(Enum):
    """Types of changes in a revision."""
    ADDITION = "addition"
    DELETION = "deletion"
    MODIFICATION = "modification"
    UNCHANGED = "unchanged"


@dataclass
class TextChange:
    """A single change between original and revised text."""
    change_type: ChangeType
    original: str
    revised: str
    location: Optional[str] = None  # Atom ID or position
    reason: str = ""  # Why this change was suggested
    suggestion_source: str = ""  # Which step/suggestion triggered this

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.change_type.value,
            "original": self.original,
            "revised": self.revised,
            "location": self.location,
            "reason": self.reason,
            "source": self.suggestion_source,
        }


@dataclass
class RevisionComparison:
    """
    Complete comparison between original and revised text.

    Tracks all changes and provides metrics for improvement assessment.
    """
    original_text: str
    revised_text: str
    changes: List[TextChange] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def change_count(self) -> int:
        """Total number of changes."""
        return len([c for c in self.changes if c.change_type != ChangeType.UNCHANGED])

    @property
    def additions(self) -> List[TextChange]:
        """All additions."""
        return [c for c in self.changes if c.change_type == ChangeType.ADDITION]

    @property
    def deletions(self) -> List[TextChange]:
        """All deletions."""
        return [c for c in self.changes if c.change_type == ChangeType.DELETION]

    @property
    def modifications(self) -> List[TextChange]:
        """All modifications."""
        return [c for c in self.changes if c.change_type == ChangeType.MODIFICATION]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "revised_text": self.revised_text,
            "changes": [c.to_dict() for c in self.changes],
            "metrics": {
                "total_changes": self.change_count,
                "additions": len(self.additions),
                "deletions": len(self.deletions),
                "modifications": len(self.modifications),
            },
            "metadata": self.metadata,
        }


@dataclass
class ImprovementMetrics:
    """Metrics quantifying the improvement from revisions."""
    original_score: float
    revised_score: float
    score_delta: float
    changes_applied: int
    improvement_areas: List[str] = field(default_factory=list)

    @property
    def percent_improvement(self) -> float:
        """Percentage improvement in score."""
        if self.original_score == 0:
            return 0.0
        return ((self.revised_score - self.original_score) / self.original_score) * 100

    @property
    def is_improved(self) -> bool:
        """Whether the revision improved the score."""
        return self.score_delta > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_score": self.original_score,
            "revised_score": self.revised_score,
            "score_delta": self.score_delta,
            "percent_improvement": self.percent_improvement,
            "is_improved": self.is_improved,
            "changes_applied": self.changes_applied,
            "improvement_areas": self.improvement_areas,
        }


class RevisionComparator:
    """
    Generates before/after comparisons for text revisions.

    Takes suggestions from the generation layer and applies them
    to create revised text, then generates comparison views.
    """

    def __init__(self):
        self._diff_context_lines = 3

    def create_comparison(
        self,
        original_text: str,
        suggestions: List[Dict[str, Any]],
        apply_all: bool = True,
    ) -> RevisionComparison:
        """
        Create a revision comparison from suggestions.

        Args:
            original_text: The original text
            suggestions: List of suggestion dictionaries from SuggestionGenerator
            apply_all: Whether to apply all suggestions or just high-priority

        Returns:
            RevisionComparison with original, revised, and changes
        """
        changes = []
        revised_text = original_text

        # Filter suggestions if not applying all
        if not apply_all:
            suggestions = [
                s for s in suggestions
                if s.get("priority") == "high"
            ]

        # Apply suggestions and track changes
        for suggestion in suggestions:
            original = suggestion.get("original_text", "")
            suggested = suggestion.get("suggested_text", "")
            location = suggestion.get("location")
            issue = suggestion.get("issue", "")
            source = suggestion.get("step_source", "")

            if original and suggested and original != suggested:
                # Try to apply the change
                if original in revised_text:
                    revised_text = revised_text.replace(original, suggested, 1)
                    changes.append(TextChange(
                        change_type=ChangeType.MODIFICATION,
                        original=original,
                        revised=suggested,
                        location=location,
                        reason=issue,
                        suggestion_source=source,
                    ))
            elif suggested and not original:
                # Addition suggestion (no specific original text)
                changes.append(TextChange(
                    change_type=ChangeType.ADDITION,
                    original="",
                    revised=suggested,
                    location=location,
                    reason=issue,
                    suggestion_source=source,
                ))

        return RevisionComparison(
            original_text=original_text,
            revised_text=revised_text,
            changes=changes,
            metadata={
                "suggestions_count": len(suggestions),
                "applied_count": len(changes),
            },
        )

    def compute_diff(
        self,
        original: str,
        revised: str,
    ) -> List[Tuple[str, str]]:
        """
        Compute line-by-line diff between texts.

        Returns list of (change_marker, line) tuples where
        change_marker is one of: ' ' (unchanged), '+' (added), '-' (removed)
        """
        original_lines = original.splitlines(keepends=True)
        revised_lines = revised.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            original_lines,
            revised_lines,
            fromfile="original",
            tofile="revised",
            lineterm="",
        ))

        result = []
        for line in diff:
            if line.startswith("+++") or line.startswith("---"):
                continue
            elif line.startswith("@@"):
                continue
            elif line.startswith("+"):
                result.append(("+", line[1:]))
            elif line.startswith("-"):
                result.append(("-", line[1:]))
            else:
                result.append((" ", line))

        return result

    def format_side_by_side(
        self,
        comparison: RevisionComparison,
        width: int = 40,
    ) -> str:
        """
        Format comparison as side-by-side text view.

        Args:
            comparison: The revision comparison
            width: Width of each column

        Returns:
            Formatted string with side-by-side comparison
        """
        lines = []
        lines.append("=" * (width * 2 + 3))
        lines.append(f"{'ORIGINAL':<{width}} | {'REVISED':<{width}}")
        lines.append("=" * (width * 2 + 3))

        orig_lines = comparison.original_text.splitlines()
        rev_lines = comparison.revised_text.splitlines()

        max_lines = max(len(orig_lines), len(rev_lines))

        for i in range(max_lines):
            orig = orig_lines[i] if i < len(orig_lines) else ""
            rev = rev_lines[i] if i < len(rev_lines) else ""

            # Truncate if needed
            if len(orig) > width:
                orig = orig[:width-3] + "..."
            if len(rev) > width:
                rev = rev[:width-3] + "..."

            # Mark changed lines
            marker = " " if orig == rev else "*"
            lines.append(f"{orig:<{width}} {marker} {rev:<{width}}")

        lines.append("=" * (width * 2 + 3))

        # Summary
        lines.append("")
        lines.append(f"Changes: {comparison.change_count}")
        lines.append(f"  Additions: {len(comparison.additions)}")
        lines.append(f"  Deletions: {len(comparison.deletions)}")
        lines.append(f"  Modifications: {len(comparison.modifications)}")

        return "\n".join(lines)

    def format_inline_diff(
        self,
        comparison: RevisionComparison,
    ) -> str:
        """
        Format comparison as inline diff with change markers.

        Returns:
            Formatted string with inline diff markers
        """
        lines = []
        lines.append("REVISION COMPARISON")
        lines.append("=" * 60)
        lines.append("")

        diff = self.compute_diff(
            comparison.original_text,
            comparison.revised_text,
        )

        for marker, line in diff:
            if marker == "+":
                lines.append(f"+ {line.rstrip()}")
            elif marker == "-":
                lines.append(f"- {line.rstrip()}")
            else:
                lines.append(f"  {line.rstrip()}")

        lines.append("")
        lines.append("=" * 60)
        lines.append(f"Total changes: {comparison.change_count}")

        return "\n".join(lines)

    def format_html(
        self,
        comparison: RevisionComparison,
    ) -> str:
        """
        Format comparison as HTML with highlighting.

        Returns:
            HTML string with styled diff view
        """
        html_parts = [
            "<!DOCTYPE html>",
            "<html><head>",
            "<style>",
            ".revision-container { font-family: monospace; }",
            ".side-by-side { display: flex; gap: 20px; }",
            ".panel { flex: 1; padding: 10px; border: 1px solid #ccc; }",
            ".original { background: #fff8f8; }",
            ".revised { background: #f8fff8; }",
            ".added { background: #90EE90; }",
            ".removed { background: #FFB6C1; text-decoration: line-through; }",
            ".changed { background: #FFFACD; }",
            ".metrics { margin-top: 20px; padding: 10px; background: #f0f0f0; }",
            "h3 { margin: 0 0 10px 0; }",
            "pre { white-space: pre-wrap; word-wrap: break-word; }",
            "</style>",
            "</head><body>",
            "<div class='revision-container'>",
            "<h2>Revision Comparison</h2>",
        ]

        # Side by side panels
        html_parts.append("<div class='side-by-side'>")

        # Original panel
        html_parts.append("<div class='panel original'>")
        html_parts.append("<h3>Original</h3>")
        html_parts.append(f"<pre>{self._escape_html(comparison.original_text)}</pre>")
        html_parts.append("</div>")

        # Revised panel
        html_parts.append("<div class='panel revised'>")
        html_parts.append("<h3>Revised</h3>")
        html_parts.append(f"<pre>{self._escape_html(comparison.revised_text)}</pre>")
        html_parts.append("</div>")

        html_parts.append("</div>")

        # Changes list
        if comparison.changes:
            html_parts.append("<div class='metrics'>")
            html_parts.append("<h3>Changes Applied</h3>")
            html_parts.append("<ul>")
            for change in comparison.changes:
                change_class = change.change_type.value
                html_parts.append(f"<li class='{change_class}'>")
                html_parts.append(f"<strong>{change.change_type.value.title()}</strong>: ")
                if change.original:
                    html_parts.append(f"<span class='removed'>{self._escape_html(change.original)}</span> → ")
                if change.revised:
                    html_parts.append(f"<span class='added'>{self._escape_html(change.revised)}</span>")
                if change.reason:
                    html_parts.append(f"<br><em>Reason: {self._escape_html(change.reason)}</em>")
                html_parts.append("</li>")
            html_parts.append("</ul>")
            html_parts.append("</div>")

        # Metrics
        html_parts.append("<div class='metrics'>")
        html_parts.append("<h3>Summary</h3>")
        html_parts.append(f"<p>Total changes: {comparison.change_count}</p>")
        html_parts.append(f"<p>Additions: {len(comparison.additions)}</p>")
        html_parts.append(f"<p>Modifications: {len(comparison.modifications)}</p>")
        html_parts.append(f"<p>Deletions: {len(comparison.deletions)}</p>")
        html_parts.append("</div>")

        html_parts.extend([
            "</div>",
            "</body></html>",
        ])

        return "\n".join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )


def create_revision_view(
    original_text: str,
    suggestions: List[Dict[str, Any]],
    format: str = "text",
) -> str:
    """
    Convenience function to create a revision comparison view.

    Args:
        original_text: Original text to revise
        suggestions: Suggestions from SuggestionGenerator
        format: Output format ("text", "html", "diff")

    Returns:
        Formatted comparison string
    """
    comparator = RevisionComparator()
    comparison = comparator.create_comparison(original_text, suggestions)

    if format == "html":
        return comparator.format_html(comparison)
    elif format == "diff":
        return comparator.format_inline_diff(comparison)
    else:
        return comparator.format_side_by_side(comparison)
