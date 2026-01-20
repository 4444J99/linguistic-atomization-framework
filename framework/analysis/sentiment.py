"""
Sentiment Analysis Module - Emotional sentiment mapping.

Refactored from copilot_sentiment_analysis.py to work with the framework ontology.
Provides VADER + TextBlob sentiment analysis with custom lexicon support.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean, stdev
from typing import Any, Dict, List, Optional

from ..core.ontology import (
    AnalysisOutput,
    AtomLevel,
    Corpus,
    DomainLexicon,
    DomainProfile,
)
from ..core.registry import registry
from .base import BaseAnalysisModule

# Optional sentiment library imports
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    SentimentIntensityAnalyzer = None
    VADER_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TextBlob = None
    TEXTBLOB_AVAILABLE = False

SENTIMENT_AVAILABLE = VADER_AVAILABLE and TEXTBLOB_AVAILABLE


@registry.register_analysis("sentiment")
class SentimentAnalysis(BaseAnalysisModule):
    """
    Sentiment analysis using VADER and TextBlob.

    Supports custom domain lexicons for specialized sentiment scoring.
    Generates:
    - Per-sentence sentiment scores
    - Theme-level statistics
    - Emotional peaks (most positive/negative sentences)
    """

    name = "sentiment"
    description = "VADER + TextBlob sentiment analysis with custom lexicons"

    def __init__(self):
        super().__init__()
        self._vader = None
        self._lexicon: Dict[str, float] = {}

        if VADER_AVAILABLE:
            self._vader = SentimentIntensityAnalyzer()

    def load_lexicon(self, domain: Optional[DomainProfile]) -> Dict[str, float]:
        """
        Load lexicon from domain profile.

        Args:
            domain: Domain profile containing lexicons

        Returns:
            Dict mapping terms to sentiment scores
        """
        lexicon = {}

        if domain:
            merged = domain.merged_lexicon()
            lexicon = merged.terms.copy()

        # Apply to VADER if available
        if self._vader and lexicon:
            self._vader.lexicon.update(lexicon)

        return lexicon

    def analyze_sentence(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a single sentence.

        Args:
            text: The sentence text

        Returns:
            Dict with VADER, TextBlob, and composite scores
        """
        if not SENTIMENT_AVAILABLE:
            return {
                "vader_compound": 0.0,
                "vader_pos": 0.0,
                "vader_neg": 0.0,
                "vader_neu": 1.0,
                "textblob_polarity": 0.0,
                "textblob_subjectivity": 0.0,
                "composite_score": 0.0,
                "classification": "neutral",
            }

        # VADER analysis
        vader_scores = self._vader.polarity_scores(text)

        # TextBlob analysis
        blob = TextBlob(text)

        # Composite score: average of VADER compound and TextBlob polarity
        composite = (vader_scores["compound"] + blob.sentiment.polarity) / 2

        # Classify
        if composite >= 0.05:
            classification = "positive"
        elif composite <= -0.05:
            classification = "negative"
        else:
            classification = "neutral"

        return {
            "vader_compound": vader_scores["compound"],
            "vader_pos": vader_scores["pos"],
            "vader_neg": vader_scores["neg"],
            "vader_neu": vader_scores["neu"],
            "textblob_polarity": blob.sentiment.polarity,
            "textblob_subjectivity": blob.sentiment.subjectivity,
            "composite_score": composite,
            "classification": classification,
        }

    def analyze_all_sentences(self, corpus: Corpus) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for all sentences in the corpus.

        Returns:
            List of sentence sentiment data dicts
        """
        sentiment_data = []
        sentence_number = 0

        # Get theme titles
        theme_titles = {}
        for _, theme in self.iter_atoms(corpus, AtomLevel.THEME):
            theme_titles[theme.id] = theme.metadata.get("title", theme.id)

        # Analyze each sentence
        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            sentence_number += 1
            theme_id = sentence.theme_id

            sentiment = self.analyze_sentence(sentence.text)

            sentiment_data.append({
                "sentence_id": sentence.id,
                "sentence_number": sentence_number,
                "theme_id": theme_id,
                "theme_title": theme_titles.get(theme_id, theme_id),
                "text": sentence.text,
                **sentiment,
            })

        return sentiment_data

    def find_emotional_peaks(
        self,
        sentiment_data: List[Dict[str, Any]],
        n: int = 10,
    ) -> Dict[str, List[Dict]]:
        """
        Find most positive and negative sentences.

        Args:
            sentiment_data: List of sentence sentiment dicts
            n: Number of peaks to return for each polarity

        Returns:
            Dict with 'most_positive' and 'most_negative' lists
        """
        sorted_by_score = sorted(sentiment_data, key=lambda x: x["composite_score"])

        return {
            "most_negative": sorted_by_score[:n],
            "most_positive": sorted_by_score[-n:][::-1],
        }

    def calculate_theme_statistics(
        self,
        corpus: Corpus,
        sentiment_data: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate sentiment statistics per theme.

        Returns:
            Dict mapping theme_id to statistics dict
        """
        theme_stats = {}

        # Get theme metadata
        theme_meta = {}
        for _, theme in self.iter_atoms(corpus, AtomLevel.THEME):
            theme_meta[theme.id] = theme.metadata.get("title", theme.id)

        # Group by theme
        by_theme: Dict[str, List[Dict]] = {}
        for s in sentiment_data:
            theme_id = s["theme_id"]
            if theme_id not in by_theme:
                by_theme[theme_id] = []
            by_theme[theme_id].append(s)

        # Calculate stats
        for theme_id, sentences in by_theme.items():
            if not sentences:
                continue

            scores = [s["composite_score"] for s in sentences]

            theme_stats[theme_id] = {
                "title": theme_meta.get(theme_id, theme_id),
                "sentence_count": len(sentences),
                "mean_sentiment": mean(scores),
                "stdev_sentiment": stdev(scores) if len(scores) > 1 else 0.0,
                "min_sentiment": min(scores),
                "max_sentiment": max(scores),
                "classification_counts": dict(Counter(s["classification"] for s in sentences)),
            }

        return theme_stats

    def analyze(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Run sentiment analysis.

        Config options:
            peak_count (int): Number of emotional peaks to return (default: 10)
        """
        self._config = config or {}
        peak_count = self._config.get("peak_count", 10)

        if not SENTIMENT_AVAILABLE:
            return self.make_output(
                data={"error": "vaderSentiment and textblob are required"},
                metadata={"sentiment_available": False},
            )

        # Load domain lexicon
        self._lexicon = self.load_lexicon(domain)

        # Analyze all sentences
        sentiment_data = self.analyze_all_sentences(corpus)

        # Find peaks
        peaks = self.find_emotional_peaks(sentiment_data, n=peak_count)

        # Calculate theme statistics
        theme_stats = self.calculate_theme_statistics(corpus, sentiment_data)

        # Overall statistics
        overall_stats = {
            "total_sentences": len(sentiment_data),
            "classification_counts": dict(Counter(s["classification"] for s in sentiment_data)),
            "mean_composite": (
                sum(s["composite_score"] for s in sentiment_data) / len(sentiment_data)
                if sentiment_data else 0.0
            ),
        }

        return self.make_output(
            data={
                "sentence_sentiments": sentiment_data,
                "emotional_peaks": peaks,
                "theme_statistics": theme_stats,
                "overall_statistics": overall_stats,
                "custom_lexicon": self._lexicon,
            },
            metadata={
                "vader_available": VADER_AVAILABLE,
                "textblob_available": TEXTBLOB_AVAILABLE,
                "lexicon_terms": len(self._lexicon),
            },
        )
