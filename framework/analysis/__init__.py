"""
Analysis modules for linguistic processing.

Each module implements the AnalysisModule interface and can be registered
with the global registry for pipeline use.

Built-in modules:
- semantic: TF-IDF similarity, co-occurrence networks
- temporal: Tense detection, temporal markers, narrative flow
- sentiment: VADER + TextBlob with custom lexicons
- entity: Pattern-based and spaCy NER
- evaluation: Heuristic rhetorical analysis (9-step pattern-based framework)

NOTE: The evaluation module uses pattern matching against predefined markers.
Scores are heuristic indicators, not validated quality measurements.
See docs/limitations.md for methodology and limitations.
"""

from .base import BaseAnalysisModule
from .semantic import SemanticAnalysis
from .temporal import TemporalAnalysis
from .sentiment import SentimentAnalysis
from .entity import EntityAnalysis
from .evaluation import (
    EvaluationAnalysis,
    StepResult,
    EvidenceInstance,
    ScoreComponent,
    ScoreExplanation,
)

__all__ = [
    "BaseAnalysisModule",
    "SemanticAnalysis",
    "TemporalAnalysis",
    "SentimentAnalysis",
    "EntityAnalysis",
    "EvaluationAnalysis",
    # Explainability classes
    "StepResult",
    "EvidenceInstance",
    "ScoreComponent",
    "ScoreExplanation",
]
