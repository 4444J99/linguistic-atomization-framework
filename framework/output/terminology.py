"""
Terminology Translation Layer - Maps technical terms to writer-friendly language.

This module provides a consistent translation layer between the technical
internals of the framework and the language used in user-facing output.

The goal is to hide all technical jargon and present analysis results
in a way that resonates with creative writers and linguistic academics.
"""

from typing import Dict, Optional

# =============================================================================
# CORE TERMINOLOGY MAPPING
# =============================================================================

FRIENDLY_NAMES: Dict[str, str] = {
    # ----- Phases (4-phase evaluation flow) -----
    "Evaluation": "Understanding Your Writing",
    "evaluation": "Understanding Your Writing",
    "Reinforcement": "Checking Consistency",
    "reinforcement": "Checking Consistency",
    "Risk": "Finding Vulnerabilities",
    "risk": "Finding Vulnerabilities",
    "Growth": "Discovering Opportunities",
    "growth": "Discovering Opportunities",

    # ----- Steps (9-step evaluation) -----
    "critique": "Strengths & Weaknesses",
    "logic_check": "Internal Consistency",
    "logos": "Logic & Evidence",
    "pathos": "Emotional Impact",
    "ethos": "Credibility & Trust",
    "blind_spots": "What You Might Be Missing",
    "shatter_points": "Where Critics Could Attack",
    "bloom": "Emerging Patterns",
    "evolve": "Improvement Plan",

    # ----- Analysis module names -----
    "semantic": "Theme Connections",
    "sentiment": "Emotional Tone",
    "temporal": "Narrative Timeline",
    "entity": "People, Places & Things",
    "evaluation": "Rhetorical Analysis",

    # ----- Technical processes (hidden from users) -----
    "atomization": "analyzing your text",
    "pipeline": "running analysis",
    "corpus": "your document",
    "ontological naming": "",  # Hidden entirely
    "TF-IDF": "theme importance",

    # ----- Score labels -----
    "overall_score": "Overall Score",
    "phase_scores": "Phase Scores",
    "score": "Score",

    # ----- UI labels -----
    "findings": "Key Findings",
    "recommendations": "Suggestions",
    "top_recommendations": "Top Suggestions",
    "instances": "Examples",
    "details": "Details",
}

# Phase descriptions for narrative context
PHASE_DESCRIPTIONS: Dict[str, str] = {
    "evaluation": (
        "This phase examines the fundamental architecture of your argument - "
        "how you use logic, emotion, and credibility to persuade your reader."
    ),
    "reinforcement": (
        "This phase verifies that your argument holds together internally - "
        "checking that your claims, evidence, and conclusions are consistent."
    ),
    "risk": (
        "This phase identifies potential weaknesses - blind spots you might "
        "not see and vulnerabilities that critics could exploit."
    ),
    "growth": (
        "This phase discovers opportunities for strengthening your work - "
        "emerging patterns worth developing and concrete improvement paths."
    ),
}

# Step descriptions for narrative context
STEP_DESCRIPTIONS: Dict[str, str] = {
    "critique": (
        "A high-level assessment of what's working well in your writing "
        "and what could use attention."
    ),
    "logic_check": (
        "Verifies that your argument's internal logic is sound - that your "
        "conclusions follow from your premises."
    ),
    "logos": (
        "Examines how effectively you use logic, evidence, and reasoning "
        "to build your argument."
    ),
    "pathos": (
        "Analyzes the emotional dimension of your writing - how you connect "
        "with readers on a feeling level."
    ),
    "ethos": (
        "Evaluates how you establish credibility and trustworthiness "
        "with your audience."
    ),
    "blind_spots": (
        "Identifies perspectives, counterarguments, or considerations "
        "that your writing might be overlooking."
    ),
    "shatter_points": (
        "Finds the places where your argument is most vulnerable to "
        "challenge or criticism."
    ),
    "bloom": (
        "Discovers emerging themes and patterns in your writing that "
        "could be developed further."
    ),
    "evolve": (
        "Synthesizes all findings into a prioritized plan for "
        "improving your work."
    ),
}

# Score interpretation thresholds (0-100 scale, matching evaluation module output)
SCORE_INTERPRETATIONS: Dict[str, tuple] = {
    "excellent": (80, 100, "excellent", "This aspect of your writing is very strong."),
    "good": (60, 80, "solid", "This is working well, with room for refinement."),
    "fair": (40, 60, "adequate", "This area needs some attention."),
    "weak": (20, 40, "underdeveloped", "This is a significant area for improvement."),
    "poor": (0, 20, "weak", "This needs substantial work."),
}


# =============================================================================
# TRANSLATION FUNCTIONS
# =============================================================================

def friendly(technical_term: str) -> str:
    """
    Translate a technical term to its user-friendly equivalent.

    Args:
        technical_term: The internal/technical term to translate

    Returns:
        The user-friendly version, or the original if no translation exists
    """
    return FRIENDLY_NAMES.get(technical_term, technical_term)


def get_phase_description(phase: str) -> str:
    """Get the narrative description of an analysis phase."""
    return PHASE_DESCRIPTIONS.get(phase.lower(), "")


def get_step_description(step: str) -> str:
    """Get the narrative description of an analysis step."""
    return STEP_DESCRIPTIONS.get(step.lower(), "")


def interpret_score(score: float) -> tuple:
    """
    Interpret a numeric score as a qualitative assessment.

    Args:
        score: A score between 0 and 100 (evaluation module output)

    Returns:
        Tuple of (label, description) for the score level
    """
    for level, (low, high, label, desc) in SCORE_INTERPRETATIONS.items():
        if low <= score <= high:
            return (label, desc)
    return ("unknown", "Score could not be interpreted.")


def score_to_percentage(score: float) -> int:
    """
    Convert score to percentage display value.

    Note: Evaluation module already returns scores in 0-100 range,
    so this function returns the score as-is (rounded to int).
    """
    return int(round(score))


def format_score_display(score: float) -> str:
    """Format a score for display (e.g., '78%' or 'Strong')."""
    pct = score_to_percentage(score)
    label, _ = interpret_score(score)
    return f"{pct}% ({label})"


# =============================================================================
# EMOJI MAPPINGS (optional, for enhanced displays)
# =============================================================================

STEP_ICONS: Dict[str, str] = {
    "critique": "🔍",
    "logic_check": "🧠",
    "logos": "📊",
    "pathos": "💓",
    "ethos": "👤",
    "blind_spots": "👁️",
    "shatter_points": "💥",
    "bloom": "🌸",
    "evolve": "🚀",
}

PHASE_ICONS: Dict[str, str] = {
    "evaluation": "📊",
    "reinforcement": "🔗",
    "risk": "⚠️",
    "growth": "🌱",
}

SCORE_ICONS: Dict[str, str] = {
    "excellent": "✨",
    "good": "👍",
    "fair": "📝",
    "weak": "⚡",
    "poor": "🔧",
}


def get_step_icon(step: str) -> str:
    """Get the icon/emoji for an analysis step."""
    return STEP_ICONS.get(step.lower(), "•")


def get_phase_icon(phase: str) -> str:
    """Get the icon/emoji for an analysis phase."""
    return PHASE_ICONS.get(phase.lower(), "•")


def get_score_icon(score: float) -> str:
    """Get the icon/emoji for a score level."""
    for level, (low, high, _, _) in SCORE_INTERPRETATIONS.items():
        if low <= score <= high:
            return SCORE_ICONS.get(level, "•")
    return "•"
