"""
Recursion Module - Iterative Analysis and Improvement Loop.

This module enables the analyze → generate → recurse loop by:
1. Tracking analysis history across iterations
2. Comparing scores between iterations
3. Managing the feedback loop for progressive improvement

The recursion loop:
    Atomize → Analyze → Generate → [Apply Changes] → Re-Atomize → Re-Analyze → Compare

NOTE: The [Apply Changes] step requires human judgment. LingFrame suggests
improvements but does not automatically modify text. The human applies
changes, then re-submits for analysis.

This module tracks the history to enable comparison and convergence detection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .ontology import AnalysisOutput, Corpus

logger = logging.getLogger(__name__)


@dataclass
class IterationRecord:
    """
    Record of a single analysis iteration.

    Attributes:
        iteration_number: Sequential iteration number (1, 2, 3, ...)
        timestamp: When this iteration was performed
        overall_score: The overall evaluation score
        step_scores: Individual step scores
        quick_wins: Top recommendations at this iteration
        suggestions_count: Number of suggestions generated
        text_hash: Hash of analyzed text (for identity verification)
        notes: Optional human notes about changes made
    """
    iteration_number: int
    timestamp: datetime
    overall_score: float
    step_scores: Dict[str, float]
    quick_wins: List[Dict[str, Any]] = field(default_factory=list)
    suggestions_count: int = 0
    text_hash: str = ""
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration_number": self.iteration_number,
            "timestamp": self.timestamp.isoformat(),
            "overall_score": self.overall_score,
            "step_scores": self.step_scores,
            "quick_wins": self.quick_wins,
            "suggestions_count": self.suggestions_count,
            "text_hash": self.text_hash,
            "notes": self.notes,
        }


@dataclass
class ScoreComparison:
    """
    Comparison between two iterations.

    Attributes:
        from_iteration: Previous iteration number
        to_iteration: Current iteration number
        overall_delta: Change in overall score
        step_deltas: Change in each step score
        improved_steps: Steps that improved
        declined_steps: Steps that declined
        unchanged_steps: Steps with no significant change
    """
    from_iteration: int
    to_iteration: int
    overall_delta: float
    step_deltas: Dict[str, float]
    improved_steps: List[str] = field(default_factory=list)
    declined_steps: List[str] = field(default_factory=list)
    unchanged_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_iteration": self.from_iteration,
            "to_iteration": self.to_iteration,
            "overall_delta": self.overall_delta,
            "step_deltas": self.step_deltas,
            "improved_steps": self.improved_steps,
            "declined_steps": self.declined_steps,
            "unchanged_steps": self.unchanged_steps,
        }

    @property
    def net_improvement(self) -> bool:
        """Whether overall score improved."""
        return self.overall_delta > 0

    @property
    def summary(self) -> str:
        """Generate human-readable summary."""
        direction = "improved" if self.overall_delta > 0 else "declined" if self.overall_delta < 0 else "unchanged"
        return (
            f"Iteration {self.from_iteration} → {self.to_iteration}: "
            f"Overall score {direction} by {abs(self.overall_delta):.1f} points. "
            f"{len(self.improved_steps)} steps improved, {len(self.declined_steps)} declined."
        )


class RecursionTracker:
    """
    Tracks analysis iterations for the recursion loop.

    Maintains history of analysis runs to enable:
    - Before/after comparison
    - Convergence detection
    - Progress visualization
    - Regression detection

    Usage:
        tracker = RecursionTracker()

        # First iteration
        result1 = evaluate(corpus1)
        tracker.record_iteration(result1, corpus1)

        # User applies changes...

        # Second iteration
        result2 = evaluate(corpus2)
        tracker.record_iteration(result2, corpus2)

        # Compare
        comparison = tracker.compare_latest()
        print(comparison.summary)
    """

    # Threshold for considering a step "unchanged"
    CHANGE_THRESHOLD = 2.0  # points

    def __init__(self):
        """Initialize the recursion tracker."""
        self._history: List[IterationRecord] = []
        self._comparisons: List[ScoreComparison] = []

    @property
    def iteration_count(self) -> int:
        """Number of iterations tracked."""
        return len(self._history)

    @property
    def history(self) -> List[IterationRecord]:
        """Get iteration history."""
        return list(self._history)

    @property
    def latest(self) -> Optional[IterationRecord]:
        """Get most recent iteration."""
        return self._history[-1] if self._history else None

    def record_iteration(
        self,
        evaluation_output: Dict[str, Any],
        corpus: Optional[Corpus] = None,
        quick_wins: Optional[List[Dict[str, Any]]] = None,
        suggestions_count: int = 0,
        notes: Optional[str] = None,
    ) -> IterationRecord:
        """
        Record a new analysis iteration.

        Args:
            evaluation_output: Output from evaluation analysis
            corpus: The analyzed corpus (for text hash)
            quick_wins: Quick wins generated for this iteration
            suggestions_count: Number of suggestions generated
            notes: Human notes about changes made

        Returns:
            The created IterationRecord
        """
        iteration_num = len(self._history) + 1

        # Extract scores
        summary = evaluation_output.get("summary", {})
        overall_score = summary.get("overall_score", 0)

        # Extract step scores
        step_scores = {}
        steps = evaluation_output.get("data", {}).get("steps", [])
        for step in steps:
            step_scores[step["step_name"]] = step.get("score", 0)

        # Calculate text hash
        text_hash = ""
        if corpus:
            text_hash = self._compute_text_hash(corpus)

        record = IterationRecord(
            iteration_number=iteration_num,
            timestamp=datetime.now(),
            overall_score=overall_score,
            step_scores=step_scores,
            quick_wins=quick_wins or [],
            suggestions_count=suggestions_count,
            text_hash=text_hash,
            notes=notes,
        )

        self._history.append(record)

        # Auto-compare with previous if exists
        if len(self._history) > 1:
            comparison = self._compare_iterations(
                self._history[-2],
                self._history[-1],
            )
            self._comparisons.append(comparison)

        return record

    def compare_latest(self) -> Optional[ScoreComparison]:
        """
        Compare the two most recent iterations.

        Returns:
            ScoreComparison or None if fewer than 2 iterations
        """
        if len(self._history) < 2:
            return None

        return self._compare_iterations(
            self._history[-2],
            self._history[-1],
        )

    def compare_iterations(
        self,
        from_iteration: int,
        to_iteration: int,
    ) -> Optional[ScoreComparison]:
        """
        Compare any two iterations.

        Args:
            from_iteration: Starting iteration number (1-indexed)
            to_iteration: Ending iteration number (1-indexed)

        Returns:
            ScoreComparison or None if iterations don't exist
        """
        if from_iteration < 1 or to_iteration < 1:
            return None
        if from_iteration > len(self._history) or to_iteration > len(self._history):
            return None

        return self._compare_iterations(
            self._history[from_iteration - 1],
            self._history[to_iteration - 1],
        )

    def compare_to_first(self) -> Optional[ScoreComparison]:
        """
        Compare most recent iteration to the first.

        Returns:
            ScoreComparison showing total progress
        """
        if len(self._history) < 2:
            return None

        return self._compare_iterations(
            self._history[0],
            self._history[-1],
        )

    def has_converged(self, threshold: float = 1.0) -> bool:
        """
        Check if improvements have converged (diminishing returns).

        Args:
            threshold: Minimum improvement to be considered non-converged

        Returns:
            True if last improvement was below threshold
        """
        if len(self._history) < 2:
            return False

        comparison = self.compare_latest()
        if comparison is None:
            return False

        return abs(comparison.overall_delta) < threshold

    def get_progress_summary(self) -> Dict[str, Any]:
        """
        Get a summary of progress across all iterations.

        Returns:
            Dictionary with progress metrics
        """
        if not self._history:
            return {"iterations": 0, "message": "No iterations recorded"}

        first = self._history[0]
        latest = self._history[-1]

        total_change = latest.overall_score - first.overall_score
        avg_change = total_change / max(len(self._history) - 1, 1)

        # Find best and worst iterations
        scores = [r.overall_score for r in self._history]
        best_iteration = scores.index(max(scores)) + 1
        worst_iteration = scores.index(min(scores)) + 1

        return {
            "iterations": len(self._history),
            "first_score": first.overall_score,
            "latest_score": latest.overall_score,
            "total_change": total_change,
            "average_change_per_iteration": avg_change,
            "best_iteration": best_iteration,
            "best_score": max(scores),
            "worst_iteration": worst_iteration,
            "worst_score": min(scores),
            "converged": self.has_converged(),
            "trend": "improving" if total_change > 0 else "declining" if total_change < 0 else "stable",
        }

    def get_step_trends(self) -> Dict[str, List[float]]:
        """
        Get score trends for each step across iterations.

        Returns:
            Dictionary mapping step names to list of scores
        """
        if not self._history:
            return {}

        # Collect all step names
        all_steps = set()
        for record in self._history:
            all_steps.update(record.step_scores.keys())

        # Build trends
        trends = {step: [] for step in all_steps}
        for record in self._history:
            for step in all_steps:
                trends[step].append(record.step_scores.get(step, 0))

        return trends

    def to_dict(self) -> Dict[str, Any]:
        """Convert tracker state to dictionary."""
        return {
            "iteration_count": self.iteration_count,
            "history": [r.to_dict() for r in self._history],
            "comparisons": [c.to_dict() for c in self._comparisons],
            "progress_summary": self.get_progress_summary(),
        }

    def _compare_iterations(
        self,
        from_record: IterationRecord,
        to_record: IterationRecord,
    ) -> ScoreComparison:
        """Compare two iteration records."""
        overall_delta = to_record.overall_score - from_record.overall_score

        # Compare step scores
        step_deltas = {}
        improved = []
        declined = []
        unchanged = []

        all_steps = set(from_record.step_scores.keys()) | set(to_record.step_scores.keys())

        for step in all_steps:
            from_score = from_record.step_scores.get(step, 0)
            to_score = to_record.step_scores.get(step, 0)
            delta = to_score - from_score
            step_deltas[step] = delta

            if delta > self.CHANGE_THRESHOLD:
                improved.append(step)
            elif delta < -self.CHANGE_THRESHOLD:
                declined.append(step)
            else:
                unchanged.append(step)

        return ScoreComparison(
            from_iteration=from_record.iteration_number,
            to_iteration=to_record.iteration_number,
            overall_delta=overall_delta,
            step_deltas=step_deltas,
            improved_steps=improved,
            declined_steps=declined,
            unchanged_steps=unchanged,
        )

    def _compute_text_hash(self, corpus: Corpus) -> str:
        """Compute a hash of corpus text for identity verification."""
        import hashlib

        # Collect all text
        text_parts = []
        for doc in corpus.documents:
            for theme in doc.themes:
                text_parts.append(theme.text or "")

        full_text = "".join(text_parts)
        return hashlib.md5(full_text.encode()).hexdigest()[:12]


def format_comparison_report(comparison: ScoreComparison) -> str:
    """
    Format a comparison as a human-readable report.

    Args:
        comparison: ScoreComparison to format

    Returns:
        Formatted string report
    """
    lines = [
        "=" * 50,
        f"ITERATION COMPARISON: {comparison.from_iteration} → {comparison.to_iteration}",
        "=" * 50,
        "",
        f"Overall Score Change: {comparison.overall_delta:+.1f} points",
        "",
    ]

    if comparison.improved_steps:
        lines.append("IMPROVED STEPS:")
        for step in comparison.improved_steps:
            delta = comparison.step_deltas.get(step, 0)
            lines.append(f"  ✓ {step}: {delta:+.1f}")
        lines.append("")

    if comparison.declined_steps:
        lines.append("DECLINED STEPS:")
        for step in comparison.declined_steps:
            delta = comparison.step_deltas.get(step, 0)
            lines.append(f"  ✗ {step}: {delta:+.1f}")
        lines.append("")

    if comparison.unchanged_steps:
        lines.append("UNCHANGED STEPS:")
        for step in comparison.unchanged_steps:
            lines.append(f"  - {step}")
        lines.append("")

    lines.append("=" * 50)

    return "\n".join(lines)


def format_progress_report(tracker: RecursionTracker) -> str:
    """
    Format a progress summary as a human-readable report.

    Args:
        tracker: RecursionTracker with history

    Returns:
        Formatted string report
    """
    summary = tracker.get_progress_summary()

    if summary["iterations"] == 0:
        return "No iterations recorded yet."

    lines = [
        "=" * 50,
        "RECURSION PROGRESS REPORT",
        "=" * 50,
        "",
        f"Total Iterations: {summary['iterations']}",
        f"First Score: {summary['first_score']:.1f}",
        f"Latest Score: {summary['latest_score']:.1f}",
        f"Total Change: {summary['total_change']:+.1f} points",
        f"Average Per Iteration: {summary['average_change_per_iteration']:+.1f}",
        "",
        f"Best: Iteration {summary['best_iteration']} ({summary['best_score']:.1f})",
        f"Worst: Iteration {summary['worst_iteration']} ({summary['worst_score']:.1f})",
        "",
        f"Status: {summary['trend'].upper()}",
        f"Converged: {'Yes' if summary['converged'] else 'No'}",
        "",
        "=" * 50,
    ]

    return "\n".join(lines)
