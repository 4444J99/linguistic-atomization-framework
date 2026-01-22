"""
Temporal Analysis Module - Tense detection and narrative flow.

Refactored from jules_temporal_analysis.py to work with the framework ontology.
Provides tense detection, temporal marker extraction, and narrative shift analysis.

Multilingual Support:
- Uses language-appropriate spaCy models for morphological analysis
- Language-specific temporal markers and indicators
- Supports: en, zh, ja, de, fr, es, ru, and more
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
    Multilingual temporal flow analysis for narrative text.

    Analyzes:
    - Verb tense distribution (language-aware)
    - Temporal markers (adverbs, phrases)
    - Flashback/flashforward detection
    - Narrative flow (Sankey diagram data)
    """

    name = "temporal"
    description = "Multilingual tense detection, temporal markers, and narrative flow analysis"

    # Language to spaCy model mapping
    SPACY_MODELS = {
        "en": "en_core_web_sm", "english": "en_core_web_sm",
        "zh": "zh_core_web_sm", "chinese": "zh_core_web_sm",
        "ja": "ja_core_news_sm", "japanese": "ja_core_news_sm",
        "de": "de_core_news_sm", "german": "de_core_news_sm",
        "fr": "fr_core_news_sm", "french": "fr_core_news_sm",
        "es": "es_core_news_sm", "spanish": "es_core_news_sm",
        "ru": "ru_core_news_sm", "russian": "ru_core_news_sm",
        "el": "el_core_news_sm", "greek": "el_core_news_sm",
        "it": "it_core_news_sm", "italian": "it_core_news_sm",
        "pt": "pt_core_news_sm", "portuguese": "pt_core_news_sm",
    }

    # Language-specific temporal markers
    TEMPORAL_MARKERS = {
        "en": {
            "adverbs": ["then", "now", "later", "before", "after", "once", "when",
                       "while", "during", "until", "since", "ago", "soon", "already",
                       "eventually", "finally", "previously", "formerly", "currently"],
            "past_indicators": ["was", "were", "had", "did", "went", "saw", "told", "asked"],
            "present_indicators": ["is", "are", "am", "do", "does", "see", "tell", "ask"],
            "future_indicators": ["will", "shall", "going to", "would", "could", "might"],
            "flashback_signals": ["remember", "recalled", "looking back", "once upon", "used to",
                                  "in the past", "back then", "years ago"],
            "flashforward_signals": ["will be asked", "years later", "in the future", "someday"],
        },
        "zh": {
            "adverbs": ["然后", "现在", "后来", "以前", "之后", "曾经", "当", "在", "直到", "自从", "不久"],
            "past_indicators": ["了", "过", "曾经"],
            "present_indicators": ["在", "正在", "着"],
            "future_indicators": ["将", "会", "要", "将要"],
            "flashback_signals": ["回忆", "记得", "想起", "从前", "过去"],
            "flashforward_signals": ["将来", "未来", "以后"],
        },
        "ja": {
            "adverbs": ["それから", "今", "後で", "前に", "後に", "かつて", "時", "間", "まで", "から", "すぐに"],
            "past_indicators": ["た", "だ", "ました", "でした"],
            "present_indicators": ["る", "います", "です"],
            "future_indicators": ["だろう", "でしょう", "つもり"],
            "flashback_signals": ["思い出す", "覚えている", "昔", "以前"],
            "flashforward_signals": ["将来", "未来", "いつか"],
        },
        "de": {
            "adverbs": ["dann", "jetzt", "später", "vorher", "nachher", "einmal", "als",
                       "während", "bis", "seit", "bald", "schon", "endlich", "früher"],
            "past_indicators": ["war", "hatte", "ging", "sah", "wurde"],
            "present_indicators": ["ist", "sind", "hat", "geht", "sieht"],
            "future_indicators": ["wird", "werden", "soll", "wollen"],
            "flashback_signals": ["erinnern", "damals", "früher", "einst"],
            "flashforward_signals": ["später", "Zukunft", "eines Tages"],
        },
        "fr": {
            "adverbs": ["alors", "maintenant", "plus tard", "avant", "après", "jadis", "quand",
                       "pendant", "jusqu'à", "depuis", "bientôt", "déjà", "enfin", "autrefois"],
            "past_indicators": ["était", "avait", "fut", "alla", "vit"],
            "present_indicators": ["est", "sont", "a", "va", "voit"],
            "future_indicators": ["sera", "aura", "ira", "verra"],
            "flashback_signals": ["souvenir", "rappeler", "autrefois", "jadis"],
            "flashforward_signals": ["avenir", "futur", "un jour"],
        },
    }

    def __init__(self):
        super().__init__()
        self._nlp_cache: Dict[str, Any] = {}
        self._tense_distribution: Dict[str, Counter] = defaultdict(Counter)
        self._current_language = "en"

    def _get_nlp(self, language: str = "en"):
        """Get or load spaCy model for the specified language."""
        if not SPACY_AVAILABLE:
            return None
        
        lang_lower = language.lower()
        
        if lang_lower in self._nlp_cache:
            return self._nlp_cache[lang_lower]
        
        model_name = self.SPACY_MODELS.get(lang_lower)
        if not model_name:
            model_name = "en_core_web_sm"
        
        try:
            nlp = spacy.load(model_name)
            self._nlp_cache[lang_lower] = nlp
            return nlp
        except OSError:
            self._nlp_cache[lang_lower] = None
            return None

    def _get_markers(self, language: str = "en") -> Dict[str, List[str]]:
        """Get temporal markers for the specified language."""
        lang_lower = language.lower()[:2]  # Use first 2 chars for matching
        return self.TEMPORAL_MARKERS.get(lang_lower, self.TEMPORAL_MARKERS["en"])

    def detect_tense(self, sentence: str, language: str = "en") -> str:
        """
        Detect primary tense of a sentence.

        Uses spaCy morphological analysis when available,
        falls back to language-specific keyword matching.

        Args:
            sentence: The sentence to analyze
            language: Language code for model selection

        Returns:
            One of: 'past', 'present', 'future', 'ambiguous'
        """
        # spaCy-based detection
        nlp = self._get_nlp(language)
        if nlp:
            doc = nlp(sentence)
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

        # Fallback: language-specific keyword scan
        markers = self._get_markers(language)
        sentence_lower = sentence.lower()
        
        past_count = sum(1 for word in markers.get("past_indicators", []) if word in sentence_lower)
        present_count = sum(1 for word in markers.get("present_indicators", []) if word in sentence_lower)
        future_count = sum(1 for word in markers.get("future_indicators", []) if word in sentence_lower)

        counts = {
            "past": past_count,
            "present": present_count,
            "future": future_count,
        }

        if max(counts.values()) == 0:
            return "ambiguous"

        return max(counts, key=counts.get)

    def extract_temporal_markers(self, text: str, language: str = "en") -> List[str]:
        """Extract temporal adverbs and phrases from text."""
        markers_found = []
        text_lower = text.lower()
        
        lang_markers = self._get_markers(language)
        adverbs = lang_markers.get("adverbs", [])

        for adverb in adverbs:
            if adverb in text_lower:
                markers_found.append(adverb)

        return markers_found

    def detect_narrative_shifts(self, sentence: str, language: str = "en") -> Dict[str, bool]:
        """Identify flashbacks and flashforwards in a sentence."""
        sentence_lower = sentence.lower()
        
        lang_markers = self._get_markers(language)
        flashback_signals = lang_markers.get("flashback_signals", [])
        flashforward_signals = lang_markers.get("flashforward_signals", [])

        has_flashback = any(signal in sentence_lower for signal in flashback_signals)
        has_flashforward = any(signal in sentence_lower for signal in flashforward_signals)

        return {
            "is_flashback": has_flashback,
            "is_flashforward": has_flashforward,
            "is_linear": not (has_flashback or has_flashforward),
        }

    def analyze_sentences(self, corpus: Corpus) -> List[Dict[str, Any]]:
        """
        Analyze temporal structure of all sentences.

        Uses language-appropriate models and markers per document.

        Returns:
            List of sentence analysis dicts
        """
        temporal_data = []
        self._tense_distribution.clear()

        # Get theme titles for reference
        theme_titles = {}
        for _, theme in self.iter_atoms(corpus, AtomLevel.THEME):
            theme_titles[theme.id] = theme.metadata.get("title", theme.id)

        # Build document language map
        doc_languages = {}
        for doc in corpus.documents:
            doc_languages[doc.id] = doc.language or "en"

        # Analyze each sentence
        for doc, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            text = sentence.text
            theme_id = sentence.theme_id
            language = doc_languages.get(doc.id, "en")

            # Detect tense (language-aware)
            tense = self.detect_tense(text, language=language)
            self._tense_distribution[theme_id][tense] += 1

            # Extract markers (language-aware)
            markers = self.extract_temporal_markers(text, language=language)

            # Detect shifts (language-aware)
            shifts = self.detect_narrative_shifts(text, language=language)

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
                "language": language,
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
                "supported_languages": list(self.SPACY_MODELS.keys()),
            },
        )
