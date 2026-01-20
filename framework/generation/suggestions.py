"""
Suggestion Generator - Maps analysis findings to revision suggestions.

This module transforms analysis outputs into actionable revision suggestions.
Each finding is mapped to one or more suggestions with:
- Specific location in text
- Description of the issue
- Suggested improvement
- Priority level

NOTE: Suggestions are heuristic starting points, not automated corrections.
Human judgment is required to evaluate appropriateness and apply revisions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SuggestionType(Enum):
    """Types of revision suggestions."""
    ADD_EVIDENCE = "add_evidence"
    ADD_TRANSITION = "add_transition"
    ADD_HEDGING = "add_hedging"
    STRENGTHEN_CLAIM = "strengthen_claim"
    ADDRESS_COUNTERARGUMENT = "address_counterargument"
    REDUCE_VAGUENESS = "reduce_vagueness"
    REMOVE_FALLACY = "remove_fallacy"
    ADD_EMOTIONAL_APPEAL = "add_emotional_appeal"
    ADD_AUTHORITY = "add_authority"
    IMPROVE_COHERENCE = "improve_coherence"
    CLARIFY_ASSUMPTION = "clarify_assumption"
    GENERAL = "general"


class SuggestionPriority(Enum):
    """Priority levels for suggestions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Suggestion:
    """
    A revision suggestion linked to a specific finding.

    Attributes:
        suggestion_type: Category of suggestion
        priority: Importance level (high/medium/low)
        location: Where in the text (atom ID, sentence number, etc.)
        original_text: The text being referenced (if applicable)
        issue: Description of the detected issue
        suggestion: The recommended revision/action
        rationale: Why this suggestion would improve the text
        alternatives: Optional alternative suggestions
        step_source: Which evaluation step generated this
        confidence: Confidence in the suggestion (0-1)
    """
    suggestion_type: SuggestionType
    priority: SuggestionPriority
    location: Optional[str]
    original_text: Optional[str]
    issue: str
    suggestion: str
    rationale: str
    alternatives: List[str] = field(default_factory=list)
    step_source: Optional[str] = None
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.suggestion_type.value,
            "priority": self.priority.value,
            "location": self.location,
            "original_text": self.original_text,
            "issue": self.issue,
            "suggestion": self.suggestion,
            "rationale": self.rationale,
            "alternatives": self.alternatives,
            "step_source": self.step_source,
            "confidence": self.confidence,
        }


# =============================================================================
# SUGGESTION TEMPLATES
# =============================================================================

# Templates map finding types to suggestion patterns
SUGGESTION_TEMPLATES = {
    # Logos (Evidence) suggestions
    "low_evidence_density": {
        "type": SuggestionType.ADD_EVIDENCE,
        "priority": SuggestionPriority.HIGH,
        "issue": "Low evidence density detected in this section",
        "suggestion_template": "Consider adding supporting evidence such as statistics, citations, or concrete examples to strengthen your claims.",
        "rationale": "Evidence-backed claims are more persuasive and credible.",
        "alternatives": [
            "Include a specific statistic or data point",
            "Reference a credible source or study",
            "Provide a concrete example that illustrates your point",
        ],
    },
    "unsupported_claim": {
        "type": SuggestionType.ADD_EVIDENCE,
        "priority": SuggestionPriority.HIGH,
        "issue": "Claim appears unsupported",
        "suggestion_template": "This claim uses assumption language ('{marker}'). Consider providing explicit evidence or acknowledging the assumption.",
        "rationale": "Unsupported claims weaken argument credibility.",
        "alternatives": [
            "Add 'according to [source]' with a credible reference",
            "Acknowledge this as an assumption if evidence is unavailable",
            "Provide logical reasoning to support the claim",
        ],
    },

    # Pathos (Emotion) suggestions
    "low_emotional_engagement": {
        "type": SuggestionType.ADD_EMOTIONAL_APPEAL,
        "priority": SuggestionPriority.MEDIUM,
        "issue": "Low emotional engagement in this section",
        "suggestion_template": "Consider adding language that connects with the reader's emotions or values.",
        "rationale": "Emotional engagement increases reader investment and memorability.",
        "alternatives": [
            "Use inclusive language ('we', 'together')",
            "Add a brief illustrative story or example",
            "Connect the point to reader values or concerns",
        ],
    },
    "excessive_emotion": {
        "type": SuggestionType.ADD_HEDGING,
        "priority": SuggestionPriority.MEDIUM,
        "issue": "High emotional intensity may overwhelm logic",
        "suggestion_template": "Consider balancing emotional appeal with more evidence-based reasoning.",
        "rationale": "Over-reliance on emotion can undermine credibility.",
        "alternatives": [
            "Replace some emotional language with factual support",
            "Add logical reasoning between emotional appeals",
            "Reduce intensity of strongest emotional markers",
        ],
    },

    # Ethos (Authority) suggestions
    "low_authority_markers": {
        "type": SuggestionType.ADD_AUTHORITY,
        "priority": SuggestionPriority.MEDIUM,
        "issue": "Few credibility markers detected",
        "suggestion_template": "Consider adding authority markers such as source citations, relevant credentials, or expert references.",
        "rationale": "Authority markers build reader trust.",
        "alternatives": [
            "Cite a recognized expert or institution",
            "Reference relevant experience or credentials",
            "Include peer-reviewed or reputable sources",
        ],
    },
    "excessive_hedging": {
        "type": SuggestionType.STRENGTHEN_CLAIM,
        "priority": SuggestionPriority.LOW,
        "issue": "High hedging frequency may weaken perceived confidence",
        "suggestion_template": "Consider reducing hedge words when you have strong evidence.",
        "rationale": "Excessive hedging can make arguments seem weak.",
        "alternatives": [
            "Replace 'might' with 'will' when evidence supports certainty",
            "Use hedging strategically for genuinely uncertain claims",
            "Balance caution with confident assertions where appropriate",
        ],
    },

    # Logic Check suggestions
    "low_transition_density": {
        "type": SuggestionType.ADD_TRANSITION,
        "priority": SuggestionPriority.HIGH,
        "issue": "Low transition marker density affects flow",
        "suggestion_template": "Add transition words to improve argument flow and help readers follow your reasoning.",
        "rationale": "Transitions signal relationships between ideas and improve coherence.",
        "alternatives": [
            "Add 'therefore' or 'thus' for conclusions",
            "Add 'however' or 'although' for contrasts",
            "Add 'first/second/finally' for sequences",
        ],
    },
    "weak_conclusion_transition": {
        "type": SuggestionType.ADD_TRANSITION,
        "priority": SuggestionPriority.MEDIUM,
        "issue": "Final section lacks conclusion markers",
        "suggestion_template": "Consider adding conclusion signals to reinforce your argument's ending.",
        "rationale": "Clear conclusions help readers synthesize your argument.",
        "alternatives": [
            "Add 'In conclusion' or 'To summarize'",
            "Restate the main claim with emphasis",
            "End with a call to action or future direction",
        ],
    },

    # Blind Spots suggestions
    "unacknowledged_assumption": {
        "type": SuggestionType.CLARIFY_ASSUMPTION,
        "priority": SuggestionPriority.MEDIUM,
        "issue": "Implicit assumption detected",
        "suggestion_template": "This text may assume '{assumption}'. Consider acknowledging or justifying this assumption.",
        "rationale": "Unacknowledged assumptions can be exploited as weak points.",
        "alternatives": [
            "Explicitly state the assumption and provide justification",
            "Acknowledge the assumption as a limitation",
            "Provide evidence that supports the assumption",
        ],
    },
    "missing_counterargument": {
        "type": SuggestionType.ADDRESS_COUNTERARGUMENT,
        "priority": SuggestionPriority.HIGH,
        "issue": "No counterargument acknowledgment detected",
        "suggestion_template": "Consider addressing potential counterarguments to strengthen your position.",
        "rationale": "Addressing counterarguments demonstrates thorough reasoning.",
        "alternatives": [
            "Add 'Some might argue that..., however...'",
            "Anticipate the strongest objection and respond",
            "Acknowledge limitations while defending your main point",
        ],
    },

    # Shatter Points suggestions
    "vague_language": {
        "type": SuggestionType.REDUCE_VAGUENESS,
        "priority": SuggestionPriority.MEDIUM,
        "issue": "Vague language detected",
        "suggestion_template": "Replace vague terms like '{marker}' with specific language.",
        "rationale": "Specific language is more persuasive and harder to refute.",
        "alternatives": [
            "Replace 'things' with specific nouns",
            "Replace 'stuff' with concrete examples",
            "Replace 'somehow' with explicit mechanism",
        ],
    },
    "logical_fallacy_indicator": {
        "type": SuggestionType.REMOVE_FALLACY,
        "priority": SuggestionPriority.HIGH,
        "issue": "Potential logical fallacy detected",
        "suggestion_template": "This phrase ('{marker}') may indicate a logical fallacy. Consider revising.",
        "rationale": "Logical fallacies weaken arguments and invite refutation.",
        "alternatives": [
            "Replace absolute claims with qualified statements",
            "Address the middle ground, not just extremes",
            "Focus on evidence rather than character or emotion",
        ],
    },
}


class SuggestionGenerator:
    """
    Generates revision suggestions from analysis findings.

    Takes evaluation analysis output and produces actionable suggestions
    for improving the text. Uses template-based generation with optional
    LLM enhancement for context-aware suggestions.

    Methodology:
    1. Extract findings from analysis output
    2. Map findings to suggestion templates
    3. Contextualize with specific text locations
    4. Optionally enhance with LLM for better suggestions

    NOTE: Suggestions are heuristic starting points. Human judgment
    required for evaluation and application.
    """

    def __init__(self, llm_provider=None):
        """
        Initialize the suggestion generator.

        Args:
            llm_provider: Optional LLM provider for enhanced suggestions
        """
        self._llm_provider = llm_provider
        self._templates = SUGGESTION_TEMPLATES

    def generate_from_evaluation(
        self,
        evaluation_output: Dict[str, Any],
        corpus_text: Optional[str] = None,
        max_suggestions: int = 20,
    ) -> List[Suggestion]:
        """
        Generate suggestions from evaluation analysis output.

        Args:
            evaluation_output: Output from evaluation analysis module
            corpus_text: Original text for context (optional)
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of Suggestion objects, sorted by priority
        """
        suggestions = []

        # Process each step's findings
        steps = evaluation_output.get("data", {}).get("steps", [])
        for step in steps:
            step_suggestions = self._process_step(step, corpus_text)
            suggestions.extend(step_suggestions)

        # Process overall metrics
        summary = evaluation_output.get("summary", {})
        metric_suggestions = self._process_metrics(summary)
        suggestions.extend(metric_suggestions)

        # Sort by priority and limit
        suggestions = self._sort_and_limit(suggestions, max_suggestions)

        return suggestions

    def _process_step(
        self,
        step: Dict[str, Any],
        corpus_text: Optional[str],
    ) -> List[Suggestion]:
        """Process findings from a single evaluation step."""
        suggestions = []
        step_name = step.get("step_name", "unknown")
        findings = step.get("findings", [])
        metrics = step.get("metrics", {})
        score = step.get("score", 50)

        # Generate suggestions based on step type and score
        if step_name == "logos" and score < 60:
            suggestions.append(self._from_template(
                "low_evidence_density",
                step_source=step_name,
                confidence=1 - (score / 100),
            ))

        elif step_name == "pathos":
            if score < 40:
                suggestions.append(self._from_template(
                    "low_emotional_engagement",
                    step_source=step_name,
                    confidence=1 - (score / 100),
                ))
            elif score > 85:
                suggestions.append(self._from_template(
                    "excessive_emotion",
                    step_source=step_name,
                    confidence=score / 100 - 0.5,
                ))

        elif step_name == "ethos":
            if score < 50:
                suggestions.append(self._from_template(
                    "low_authority_markers",
                    step_source=step_name,
                    confidence=1 - (score / 100),
                ))
            # Check hedging ratio
            hedging_ratio = metrics.get("hedging_ratio", 0)
            if hedging_ratio > 0.15:
                suggestions.append(self._from_template(
                    "excessive_hedging",
                    step_source=step_name,
                    confidence=min(hedging_ratio * 2, 1.0),
                ))

        elif step_name == "logic_check" and score < 60:
            suggestions.append(self._from_template(
                "low_transition_density",
                step_source=step_name,
                confidence=1 - (score / 100),
            ))

        elif step_name == "blind_spots":
            # Check for missing counterarguments
            if score < 60:
                suggestions.append(self._from_template(
                    "missing_counterargument",
                    step_source=step_name,
                    confidence=1 - (score / 100),
                ))

        elif step_name == "shatter_points":
            # Process specific weakness findings
            for finding in findings:
                finding_type = finding.get("type", "")
                marker = finding.get("marker", "")

                if "vague" in finding_type.lower():
                    suggestions.append(self._from_template(
                        "vague_language",
                        step_source=step_name,
                        marker=marker,
                        location=finding.get("location"),
                        original_text=finding.get("context"),
                    ))
                elif "fallacy" in finding_type.lower() or "unsupported" in finding_type.lower():
                    suggestions.append(self._from_template(
                        "logical_fallacy_indicator",
                        step_source=step_name,
                        marker=marker,
                        location=finding.get("location"),
                        original_text=finding.get("context"),
                    ))

        return suggestions

    def _process_metrics(self, summary: Dict[str, Any]) -> List[Suggestion]:
        """Generate suggestions from overall metrics."""
        suggestions = []

        overall_score = summary.get("overall_score", 50)
        step_scores = summary.get("step_scores", {})

        # If overall score is low, prioritize the weakest areas
        if overall_score < 60:
            # Find the two lowest scoring steps
            sorted_steps = sorted(step_scores.items(), key=lambda x: x[1])
            for step_name, score in sorted_steps[:2]:
                if score < 50:
                    suggestions.append(Suggestion(
                        suggestion_type=SuggestionType.GENERAL,
                        priority=SuggestionPriority.HIGH,
                        location=None,
                        original_text=None,
                        issue=f"Low score in {step_name} ({score:.0f}/100)",
                        suggestion=f"Focus improvement efforts on {step_name} analysis area.",
                        rationale=f"This area scored significantly below average and offers high improvement potential.",
                        step_source="metrics",
                        confidence=1 - (score / 100),
                    ))

        return suggestions

    def _from_template(
        self,
        template_key: str,
        step_source: Optional[str] = None,
        confidence: float = 0.5,
        marker: str = "",
        location: Optional[str] = None,
        original_text: Optional[str] = None,
        **kwargs,
    ) -> Suggestion:
        """Create a suggestion from a template."""
        template = self._templates.get(template_key, {})

        # Format suggestion template with any variables
        suggestion_text = template.get("suggestion_template", "")
        if "{marker}" in suggestion_text and marker:
            suggestion_text = suggestion_text.format(marker=marker)
        if "{assumption}" in suggestion_text:
            suggestion_text = suggestion_text.format(
                assumption=kwargs.get("assumption", "an implicit premise")
            )

        issue_text = template.get("issue", "")
        if "{marker}" in issue_text and marker:
            issue_text = issue_text.format(marker=marker)

        return Suggestion(
            suggestion_type=template.get("type", SuggestionType.GENERAL),
            priority=template.get("priority", SuggestionPriority.MEDIUM),
            location=location,
            original_text=original_text,
            issue=issue_text,
            suggestion=suggestion_text,
            rationale=template.get("rationale", ""),
            alternatives=template.get("alternatives", []),
            step_source=step_source,
            confidence=confidence,
        )

    def _sort_and_limit(
        self,
        suggestions: List[Suggestion],
        max_count: int,
    ) -> List[Suggestion]:
        """Sort suggestions by priority and confidence, then limit."""
        priority_order = {
            SuggestionPriority.HIGH: 0,
            SuggestionPriority.MEDIUM: 1,
            SuggestionPriority.LOW: 2,
        }

        sorted_suggestions = sorted(
            suggestions,
            key=lambda s: (priority_order.get(s.priority, 2), -s.confidence),
        )

        return sorted_suggestions[:max_count]

    def to_dict(self, suggestions: List[Suggestion]) -> Dict[str, Any]:
        """Convert suggestions to dictionary format."""
        return {
            "total_count": len(suggestions),
            "by_priority": {
                "high": len([s for s in suggestions if s.priority == SuggestionPriority.HIGH]),
                "medium": len([s for s in suggestions if s.priority == SuggestionPriority.MEDIUM]),
                "low": len([s for s in suggestions if s.priority == SuggestionPriority.LOW]),
            },
            "by_type": self._count_by_type(suggestions),
            "suggestions": [s.to_dict() for s in suggestions],
        }

    def _count_by_type(self, suggestions: List[Suggestion]) -> Dict[str, int]:
        """Count suggestions by type."""
        counts = {}
        for s in suggestions:
            type_name = s.suggestion_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
