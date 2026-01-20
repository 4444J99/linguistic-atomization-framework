"""
Entity Recognition Module - Named entity extraction.

Refactored from simple_entity_recognition.py to work with the framework ontology.
Provides pattern-based and optional spaCy NER for entity extraction.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from ..core.ontology import (
    AnalysisOutput,
    AtomLevel,
    Corpus,
    DomainProfile,
    EntityPatternSet,
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


@registry.register_analysis("entity")
class EntityAnalysis(BaseAnalysisModule):
    """
    Entity recognition using pattern matching and optional spaCy NER.

    Extracts named entities from text and provides:
    - Enhanced atomized data with entity annotations
    - Entity statistics by type
    - Entity frequency and distribution data
    """

    name = "entity"
    description = "Pattern-based and spaCy named entity recognition"

    # Default patterns when no domain is provided
    DEFAULT_PATTERNS = {
        "PERSON": r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b",
        "RANK": r"\b(Staff Sergeant|Gunnery Sergeant|Lieutenant|Captain|Corpsman|Sergeant|Private|Colonel|General)\b",
        "LOCATION": r"\b(Arlington|Vietnam|Iraq|Afghanistan|Tomb)\b",
        "EQUIPMENT": r"\b(M40|M16|rifle|mask|Thunderbird|weapon)\b",
        "UNIT": r"\b(Marine Corps|platoon|squad|battalion|regiment)\b",
        "TEMPORAL": r"\b(morning|evening|night|day|hour|minute|dawn|dusk|midnight|noon)\b",
    }

    def __init__(self):
        super().__init__()
        self._patterns: Dict[str, re.Pattern] = {}
        self._nlp = None
        self._use_spacy = False

        if SPACY_AVAILABLE:
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                self._nlp = None

    def load_patterns(self, domain: Optional[DomainProfile]) -> Dict[str, re.Pattern]:
        """
        Load entity patterns from domain profile or defaults.

        Args:
            domain: Optional domain profile with patterns

        Returns:
            Dict mapping entity type to compiled regex
        """
        raw_patterns = {}

        if domain and domain.primary_patterns:
            # Load from domain
            for pattern in domain.primary_patterns.patterns:
                raw_patterns[pattern.label] = pattern.pattern
        else:
            # Use defaults
            raw_patterns = self.DEFAULT_PATTERNS.copy()

        # Compile patterns
        return {
            label: re.compile(pattern, re.IGNORECASE)
            for label, pattern in raw_patterns.items()
        }

    def extract_entities_pattern(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities using pattern matching.

        Args:
            text: Text to analyze

        Returns:
            Dict mapping entity type to list of found entities
        """
        entities: Dict[str, List[str]] = defaultdict(list)

        for entity_type, pattern in self._patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                # Handle tuple matches from groups
                if isinstance(match, tuple):
                    match = match[0]
                entities[entity_type].append(match)

        return dict(entities)

    def extract_entities_spacy(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities using spaCy NER.

        Args:
            text: Text to analyze

        Returns:
            Dict mapping entity type to list of found entities
        """
        if not self._nlp:
            return {}

        entities: Dict[str, List[str]] = defaultdict(list)
        doc = self._nlp(text)

        for ent in doc.ents:
            entities[ent.label_].append(ent.text)

        return dict(entities)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities using configured method.

        Args:
            text: Text to analyze

        Returns:
            Dict mapping entity type to list of found entities
        """
        if self._use_spacy and self._nlp:
            # Combine spaCy and pattern matching
            spacy_entities = self.extract_entities_spacy(text)
            pattern_entities = self.extract_entities_pattern(text)

            # Merge results (pattern entities take precedence for domain-specific types)
            merged = {**spacy_entities}
            for entity_type, values in pattern_entities.items():
                if entity_type in merged:
                    merged[entity_type] = list(set(merged[entity_type] + values))
                else:
                    merged[entity_type] = values

            return merged

        return self.extract_entities_pattern(text)

    def annotate_corpus(
        self,
        corpus: Corpus,
    ) -> Dict[str, Any]:
        """
        Annotate all sentences with entities.

        Returns enhanced data structure compatible with original format.
        """
        enhanced_themes = []
        entity_stats: Dict[str, Counter] = defaultdict(Counter)

        for doc in corpus.documents:
            for theme in doc.root_atoms:
                enhanced_theme = {
                    "id": theme.id,
                    "title": theme.metadata.get("title", theme.id),
                    "text": theme.text,
                    "paragraphs": [],
                }

                for para in theme.children:
                    enhanced_para = {
                        "id": para.id,
                        "text": para.text,
                        "sentences": [],
                    }

                    for sent in para.children:
                        entities = self.extract_entities(sent.text)

                        enhanced_sent = {
                            "id": sent.id,
                            "text": sent.text,
                            "entities": entities,
                        }

                        # Update statistics
                        for entity_type, values in entities.items():
                            for value in values:
                                entity_stats[entity_type][value] += 1

                        enhanced_para["sentences"].append(enhanced_sent)

                    enhanced_theme["paragraphs"].append(enhanced_para)

                enhanced_themes.append(enhanced_theme)

        return {
            "themes": enhanced_themes,
            "entity_stats": {k: dict(v) for k, v in entity_stats.items()},
        }

    def calculate_statistics(
        self,
        entity_stats: Dict[str, Counter],
    ) -> Dict[str, Any]:
        """
        Calculate entity statistics.

        Returns:
            Statistics dict with totals, unique counts, and top entities
        """
        stats = {
            "total_entities": sum(sum(c.values()) for c in entity_stats.values()),
            "by_type": {},
        }

        for entity_type, counter in entity_stats.items():
            stats["by_type"][entity_type] = {
                "total": sum(counter.values()),
                "unique": len(counter),
                "top_10": dict(counter.most_common(10)),
            }

        return stats

    def analyze(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Run entity recognition analysis.

        Config options:
            use_spacy (bool): Use spaCy NER in addition to patterns (default: False)
        """
        self._config = config or {}
        self._use_spacy = self._config.get("use_spacy", False)

        # Load patterns
        self._patterns = self.load_patterns(domain)

        # Annotate corpus
        annotated = self.annotate_corpus(corpus)

        # Calculate statistics
        stats = self.calculate_statistics(
            {k: Counter(v) for k, v in annotated["entity_stats"].items()}
        )

        return self.make_output(
            data={
                "enhanced_atomized": {"themes": annotated["themes"]},
                "entity_statistics": stats,
            },
            metadata={
                "spacy_available": SPACY_AVAILABLE,
                "spacy_used": self._use_spacy and self._nlp is not None,
                "pattern_count": len(self._patterns),
            },
        )
