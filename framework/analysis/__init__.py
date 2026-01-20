"""
Analysis modules for linguistic processing.

Each module implements the AnalysisModule interface and can be registered
with the global registry for pipeline use.

Built-in modules:
- semantic: TF-IDF similarity, co-occurrence networks
- temporal: Tense detection, temporal markers, narrative flow
- sentiment: VADER + TextBlob with custom lexicons
- entity: Pattern-based and spaCy NER
"""

from .base import BaseAnalysisModule
from .semantic import SemanticAnalysis
from .temporal import TemporalAnalysis
from .sentiment import SentimentAnalysis
from .entity import EntityAnalysis

__all__ = [
    "BaseAnalysisModule",
    "SemanticAnalysis",
    "TemporalAnalysis",
    "SentimentAnalysis",
    "EntityAnalysis",
]
