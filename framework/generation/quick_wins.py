"""
Quick Wins Extractor - Identifies top actionable improvements.

This module extracts the most impactful, immediately actionable
suggestions from analysis results. Quick Wins are designed to be:
- High impact (significant improvement potential)
- Low effort (can be implemented quickly)
- Specific (clear action to take)

NOTE: Quick Wins are heuristic recommendations. Human judgment
determines actual applicability and priority.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .suggestions import Suggestion, SuggestionPriority, SuggestionType

logger = logging.getLogger(__name__)


@dataclass
class QuickWin:
    """
    A high-impact, immediately actionable improvement.

    Attributes:
        rank: Position in quick wins list (1, 2, or 3)
        title: Brief title for the action
        action: Specific action to take
        impact: Expected impact on the text
        location_hint: Where to focus (if applicable)
        example: Optional example of the improvement
        source_step: Which analysis step identified this
    """
    rank: int
    title: str
    action: str
    impact: str
    location_hint: Optional[str] = None
    example: Optional[str] = None
    source_step: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "title": self.title,
            "action": self.action,
            "impact": self.impact,
            "location_hint": self.location_hint,
            "example": self.example,
            "source_step": self.source_step,
        }


# Quick Win templates based on common findings
QUICK_WIN_TEMPLATES = {
    "add_transitions": {
        "title": "Add Transition Words",
        "action": "Insert transition phrases between paragraphs and key sentences.",
        "impact": "Improves argument flow and reader comprehension.",
        "example": "Add 'Therefore,' before conclusions; 'However,' before contrasts; 'First/Second/Finally' for sequences.",
    },
    "add_evidence": {
        "title": "Add Supporting Evidence",
        "action": "Include at least one statistic, citation, or concrete example per major claim.",
        "impact": "Strengthens credibility and persuasive power.",
        "example": "Transform 'This approach is effective' → 'This approach increased engagement by 40% (Smith, 2024)'.",
    },
    "address_counterargument": {
        "title": "Address a Counterargument",
        "action": "Add one paragraph acknowledging and responding to the strongest objection.",
        "impact": "Demonstrates thorough reasoning and anticipates reader concerns.",
        "example": "Add: 'Critics might argue that X. However, this overlooks Y because Z.'",
    },
    "reduce_vagueness": {
        "title": "Replace Vague Language",
        "action": "Find and replace generic terms ('things', 'stuff', 'somehow') with specific nouns and verbs.",
        "impact": "Makes arguments more concrete and harder to refute.",
        "example": "Transform 'things went wrong' → 'production delays increased costs by 15%'.",
    },
    "add_conclusion_signal": {
        "title": "Strengthen Your Conclusion",
        "action": "Add clear conclusion markers and restate your main argument.",
        "impact": "Helps readers synthesize your argument and remember key points.",
        "example": "Begin final paragraph with 'In conclusion,' or 'To summarize,' and restate your thesis.",
    },
    "cite_authority": {
        "title": "Add Authority References",
        "action": "Include references to experts, institutions, or reputable sources.",
        "impact": "Builds credibility through association with recognized authorities.",
        "example": "Add: 'According to [expert/institution]...' or 'Research from [source] shows...'",
    },
    "balance_emotion": {
        "title": "Balance Emotional Appeals",
        "action": "Pair emotional language with factual support.",
        "impact": "Maintains engagement while building rational credibility.",
        "example": "After 'This is devastating,' add specific evidence: 'affecting 2 million families annually.'",
    },
    "clarify_assumptions": {
        "title": "State Your Assumptions",
        "action": "Explicitly acknowledge key assumptions underlying your argument.",
        "impact": "Preempts criticism and demonstrates intellectual honesty.",
        "example": "Add: 'This argument assumes that X, which is supported by Y.'",
    },
}


class QuickWinExtractor:
    """
    Extracts top 3 actionable improvements from analysis results.

    Quick Wins are selected based on:
    1. Impact potential (how much improvement is possible)
    2. Effort required (prefer low-effort, high-impact)
    3. Specificity (clear, actionable recommendations)

    NOTE: Quick Wins are heuristic. They represent common high-value
    improvements but may not be optimal for every text.
    """

    def __init__(self):
        """Initialize the quick win extractor."""
        self._templates = QUICK_WIN_TEMPLATES

    def extract_from_evaluation(
        self,
        evaluation_output: Dict[str, Any],
        suggestions: Optional[List[Suggestion]] = None,
        max_wins: int = 3,
    ) -> List[QuickWin]:
        """
        Extract quick wins from evaluation analysis output.

        Args:
            evaluation_output: Output from evaluation analysis module
            suggestions: Optional pre-generated suggestions to draw from
            max_wins: Maximum number of quick wins (default 3)

        Returns:
            List of QuickWin objects, ranked by priority
        """
        candidates = []

        # Analyze step scores to identify improvement areas
        steps = evaluation_output.get("data", {}).get("steps", [])
        summary = evaluation_output.get("summary", {})

        # Build candidate list based on scores
        for step in steps:
            step_name = step.get("step_name", "")
            score = step.get("score", 50)
            metrics = step.get("metrics", {})

            # Low logic check score → add transitions
            if step_name == "logic_check" and score < 65:
                candidates.append({
                    "template": "add_transitions",
                    "priority": self._score_to_priority(score),
                    "source": step_name,
                    "confidence": 1 - (score / 100),
                })

            # Low logos score → add evidence
            elif step_name == "logos" and score < 60:
                candidates.append({
                    "template": "add_evidence",
                    "priority": self._score_to_priority(score),
                    "source": step_name,
                    "confidence": 1 - (score / 100),
                })

            # Low blind spots score → address counterargument
            elif step_name == "blind_spots" and score < 60:
                candidates.append({
                    "template": "address_counterargument",
                    "priority": self._score_to_priority(score),
                    "source": step_name,
                    "confidence": 1 - (score / 100),
                })

            # Low ethos score → cite authority
            elif step_name == "ethos" and score < 55:
                candidates.append({
                    "template": "cite_authority",
                    "priority": self._score_to_priority(score),
                    "source": step_name,
                    "confidence": 1 - (score / 100),
                })

            # High shatter points findings → reduce vagueness
            elif step_name == "shatter_points":
                vagueness_count = metrics.get("vagueness_count", 0)
                if vagueness_count > 3:
                    candidates.append({
                        "template": "reduce_vagueness",
                        "priority": 1,
                        "source": step_name,
                        "confidence": min(vagueness_count / 10, 1.0),
                    })

            # Low pathos but not too high → balance emotion
            elif step_name == "pathos":
                if score < 45:
                    candidates.append({
                        "template": "balance_emotion",
                        "priority": 2,
                        "source": step_name,
                        "confidence": 0.6,
                    })

        # Add suggestions-based candidates if provided
        if suggestions:
            for s in suggestions[:5]:  # Top 5 suggestions
                if s.priority == SuggestionPriority.HIGH:
                    template_key = self._suggestion_type_to_template(s.suggestion_type)
                    if template_key and template_key not in [c["template"] for c in candidates]:
                        candidates.append({
                            "template": template_key,
                            "priority": 0,  # Highest priority
                            "source": s.step_source,
                            "confidence": s.confidence,
                        })

        # Sort by priority (lower is better) and confidence
        candidates.sort(key=lambda c: (c["priority"], -c["confidence"]))

        # Convert to QuickWin objects, avoiding duplicates
        quick_wins = []
        seen_templates = set()

        for i, candidate in enumerate(candidates):
            if len(quick_wins) >= max_wins:
                break

            template_key = candidate["template"]
            if template_key in seen_templates:
                continue

            seen_templates.add(template_key)
            template = self._templates.get(template_key, {})

            quick_wins.append(QuickWin(
                rank=len(quick_wins) + 1,
                title=template.get("title", "Improve This Area"),
                action=template.get("action", "Review and revise"),
                impact=template.get("impact", "May improve overall quality"),
                example=template.get("example"),
                source_step=candidate["source"],
            ))

        # If we don't have enough, add generic high-impact suggestions
        while len(quick_wins) < max_wins:
            generic_keys = ["add_evidence", "add_transitions", "address_counterargument"]
            for key in generic_keys:
                if key not in seen_templates:
                    seen_templates.add(key)
                    template = self._templates.get(key, {})
                    quick_wins.append(QuickWin(
                        rank=len(quick_wins) + 1,
                        title=template.get("title", "General Improvement"),
                        action=template.get("action", "Review and enhance"),
                        impact=template.get("impact", "May improve quality"),
                        example=template.get("example"),
                        source_step="general",
                    ))
                    break
            else:
                break  # No more templates available

        return quick_wins

    def _score_to_priority(self, score: float) -> int:
        """Convert a score to priority level (lower is higher priority)."""
        if score < 40:
            return 0
        elif score < 55:
            return 1
        elif score < 70:
            return 2
        else:
            return 3

    def _suggestion_type_to_template(self, stype: SuggestionType) -> Optional[str]:
        """Map suggestion type to quick win template key."""
        mapping = {
            SuggestionType.ADD_EVIDENCE: "add_evidence",
            SuggestionType.ADD_TRANSITION: "add_transitions",
            SuggestionType.ADDRESS_COUNTERARGUMENT: "address_counterargument",
            SuggestionType.REDUCE_VAGUENESS: "reduce_vagueness",
            SuggestionType.ADD_AUTHORITY: "cite_authority",
            SuggestionType.ADD_EMOTIONAL_APPEAL: "balance_emotion",
            SuggestionType.CLARIFY_ASSUMPTION: "clarify_assumptions",
        }
        return mapping.get(stype)

    def to_dict(self, quick_wins: List[QuickWin]) -> Dict[str, Any]:
        """Convert quick wins to dictionary format."""
        return {
            "count": len(quick_wins),
            "quick_wins": [qw.to_dict() for qw in quick_wins],
        }

    def format_text(self, quick_wins: List[QuickWin]) -> str:
        """Format quick wins as readable text."""
        if not quick_wins:
            return "No quick wins identified."

        lines = ["QUICK WINS", "=" * 40, ""]

        for qw in quick_wins:
            lines.append(f"{qw.rank}. {qw.title}")
            lines.append(f"   Action: {qw.action}")
            lines.append(f"   Impact: {qw.impact}")
            if qw.example:
                lines.append(f"   Example: {qw.example}")
            lines.append("")

        return "\n".join(lines)
