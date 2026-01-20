"""
Temporal Analysis Module - Tense detection and narrative flow.

Refactored from jules_temporal_analysis.py to work with the framework ontology.
Provides tense detection, temporal marker extraction, and narrative shift analysis.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from ..core.ontology import (
    AnalysisOutput,
    AtomLevel,
    Corpus,
    DomainProfile,
)
from ..core.registry import registry
from .base import BaseAnalysisModule

# Optional spaCy import
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    SPACY_AVAILABLE = False


@registry.register_analysis("temporal")
class TemporalAnalysis(BaseAnalysisModule):
    """
    Temporal flow analysis for narrative text.

    Analyzes:
    - Verb tense distribution
    - Temporal markers (adverbs, phrases)
    - Flashback/flashforward detection
    - Narrative flow (Sankey diagram data)
    """

    name = "temporal"
    description = "Tense detection, temporal markers, and narrative flow analysis"

    # Temporal marker patterns
    TEMPORAL_ADVERBS = [
        "then", "now", "later", "before", "after", "once", "when",
        "while", "during", "until", "since", "ago", "soon", "already",
        "eventually", "finally", "previously", "formerly", "currently",
    ]

    PAST_INDICATORS = ["was", "were", "had", "did", "went", "saw", "told", "asked"]
    PRESENT_INDICATORS = ["is", "are", "am", "do", "does", "see", "tell", "ask"]
    FUTURE_INDICATORS = ["will", "shall", "going to", "would", "could", "might"]

    FLASHBACK_SIGNALS = [
        "remember", "recalled", "looking back", "once upon", "used to",
        "in the past", "back then", "years ago", "deployment",
    ]

    FLASHFORWARD_SIGNALS = [
        "will be asked", "years later", "in the future", "someday",
        "when I return", "back home", "after the war",
    ]

    def __init__(self):
        super().__init__()
        self._nlp = None
        self._tense_distribution: Dict[str, Counter] = defaultdict(Counter)

        if SPACY_AVAILABLE:
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                self._nlp = None

    def detect_tense(self, sentence: str) -> str:
        """
        Detect primary tense of a sentence.

        Uses spaCy morphological analysis when available,
        falls back to keyword matching.

        Args:
            sentence: The sentence to analyze

        Returns:
            One of: 'past', 'present', 'future', 'ambiguous'
        """
        # spaCy-based detection
        if self._nlp:
            doc = self._nlp(sentence)
            counts = {"past": 0, "present": 0, "future": 0}

            for token in doc:
                if token.pos_ in {"VERB", "AUX"}:
                    tenses = token.morph.get("Tense")
                    for tense in tenses:
                        t = tense.lower()
                        if t.startswith("past"):
                            counts["past"] += 1
                        elif t.startswith("pres"):
                            counts["present"] += 1
                        elif t.startswith("fut"):
                            counts["future"] += 1

            if max(counts.values()) > 0:
                return max(counts, key=counts.get)

        # Fallback: keyword scan
        sentence_lower = sentence.lower()
        past_count = sum(1 for word in self.PAST_INDICATORS if word in sentence_lower)
        present_count = sum(1 for word in self.PRESENT_INDICATORS if word in sentence_lower)
        future_count = sum(1 for word in self.FUTURE_INDICATORS if word in sentence_lower)

        counts = {
            "past": past_count,
            "present": present_count,
            "future": future_count,
        }

        if max(counts.values()) == 0:
            return "ambiguous"

        return max(counts, key=counts.get)

    def extract_temporal_markers(self, text: str) -> List[str]:
        """Extract temporal adverbs and phrases from text."""
        markers = []
        text_lower = text.lower()

        for adverb in self.TEMPORAL_ADVERBS:
            if adverb in text_lower:
                markers.append(adverb)

        return markers

    def detect_narrative_shifts(self, sentence: str) -> Dict[str, bool]:
        """Identify flashbacks and flashforwards in a sentence."""
        sentence_lower = sentence.lower()

        has_flashback = any(signal in sentence_lower for signal in self.FLASHBACK_SIGNALS)
        has_flashforward = any(signal in sentence_lower for signal in self.FLASHFORWARD_SIGNALS)

        return {
            "is_flashback": has_flashback,
            "is_flashforward": has_flashforward,
            "is_linear": not (has_flashback or has_flashforward),
        }

    def analyze_sentences(self, corpus: Corpus) -> List[Dict[str, Any]]:
        """
        Analyze temporal structure of all sentences.

        Returns:
            List of sentence analysis dicts
        """
        temporal_data = []
        self._tense_distribution.clear()

        # Get theme titles for reference
        theme_titles = {}
        for _, theme in self.iter_atoms(corpus, AtomLevel.THEME):
            theme_titles[theme.id] = theme.metadata.get("title", theme.id)

        # Analyze each sentence
        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            text = sentence.text
            theme_id = sentence.theme_id

            # Detect tense
            tense = self.detect_tense(text)
            self._tense_distribution[theme_id][tense] += 1

            # Extract markers
            markers = self.extract_temporal_markers(text)

            # Detect shifts
            shifts = self.detect_narrative_shifts(text)

            temporal_data.append({
                "sentence_id": sentence.id,
                "theme_id": theme_id,
                "theme_title": theme_titles.get(theme_id, theme_id),
                "text": text[:100] + "..." if len(text) > 100 else text,
                "tense": tense,
                "temporal_markers": markers,
                "is_flashback": shifts["is_flashback"],
                "is_flashforward": shifts["is_flashforward"],
                "narrative_type": (
                    "flashback" if shifts["is_flashback"]
                    else "flashforward" if shifts["is_flashforward"]
                    else "linear"
                ),
            })

        return temporal_data

    def generate_sankey_data(self, corpus: Corpus) -> Dict[str, Any]:
        """
        Generate Sankey diagram data for narrative flow visualization.

        Shows flow from themes to chronological buckets.

        Returns:
            Dict with 'nodes' and 'links' for Plotly Sankey
        """
        nodes = []
        links = []
        node_index = {}

        # Theme nodes
        for _, theme in self.iter_atoms(corpus, AtomLevel.THEME):
            node_index[theme.id] = len(nodes)
            nodes.append({
                "id": theme.id,
                "name": theme.metadata.get("title", theme.id),
                "group": "theme",
            })

        # Chronological bucket nodes
        chrono_labels = ["past", "present", "future", "ambiguous"]
        for label in chrono_labels:
            node_id = f"CHRONO:{label}"
            node_index[node_id] = len(nodes)
            nodes.append({
                "id": node_id,
                "name": f"Chronology – {label}",
                "group": "chronology",
            })

        # Links: theme → chronological bucket
        for theme_id, tense_counts in self._tense_distribution.items():
            for label in chrono_labels:
                count = tense_counts.get(label, 0)
                if count > 0:
                    links.append({
                        "source": node_index.get(theme_id, 0),
                        "target": node_index[f"CHRONO:{label}"],
                        "value": int(count),
                        "type": "tense_flow",
                    })

        return {"nodes": nodes, "links": links}

    def analyze(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Run temporal analysis.

        Config options:
            include_sankey (bool): Generate Sankey diagram data (default: True)
        """
        self._config = config or {}
        include_sankey = self._config.get("include_sankey", True)

        # Analyze all sentences
        sentence_analysis = self.analyze_sentences(corpus)

        # Compile statistics
        tense_counts = Counter(s["tense"] for s in sentence_analysis)
        flashback_count = sum(1 for s in sentence_analysis if s["is_flashback"])
        flashforward_count = sum(1 for s in sentence_analysis if s["is_flashforward"])
        linear_count = sum(1 for s in sentence_analysis if s["narrative_type"] == "linear")

        data = {
            "sentence_analysis": sentence_analysis,
            "theme_tense_distribution": {k: dict(v) for k, v in self._tense_distribution.items()},
            "overall_statistics": {
                "total_sentences": len(sentence_analysis),
                "tense_counts": dict(tense_counts),
                "flashback_count": flashback_count,
                "flashforward_count": flashforward_count,
                "linear_count": linear_count,
            },
        }

        if include_sankey:
            data["sankey_data"] = self.generate_sankey_data(corpus)

        return self.make_output(
            data=data,
            metadata={
                "spacy_available": SPACY_AVAILABLE,
                "spacy_model": "en_core_web_sm" if self._nlp else None,
            },
        )
