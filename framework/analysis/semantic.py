"""
Semantic Analysis Module - Theme similarity and entity networks.

Refactored from gemini_semantic_network.py to work with the framework ontology.
Provides TF-IDF based theme similarity and entity co-occurrence analysis.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

# Optional dependencies
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    np = None
    TfidfVectorizer = None
    cosine_similarity = None
    SKLEARN_AVAILABLE = False

from ..core.ontology import (
    AnalysisOutput,
    Atom,
    AtomLevel,
    Corpus,
    DomainProfile,
)
from ..core.registry import registry
from .base import BaseAnalysisModule


@registry.register_analysis("semantic")
class SemanticAnalysis(BaseAnalysisModule):
    """
    Semantic network analysis using TF-IDF similarity and entity co-occurrence.

    Generates data for force-directed graph visualization of:
    - Theme relationships (similarity-based edges)
    - Entity nodes with mentions
    - Co-occurrence edges between entities
    """

    name = "semantic"
    description = "TF-IDF theme similarity and entity co-occurrence networks"

    def __init__(self):
        super().__init__()
        self._entity_mentions: Dict[str, Set[str]] = defaultdict(set)
        self._compiled_patterns: Dict[str, re.Pattern] = {}

    def _entity_key(self, text: str, label: str) -> str:
        """Create stable entity identifier."""
        return f"{label}:{text.lower()}"

    def _compile_patterns(self, domain: Optional[DomainProfile]) -> Dict[str, re.Pattern]:
        """Compile entity patterns from domain profile."""
        if domain and domain.primary_patterns:
            return domain.primary_patterns.compiled()

        # Fallback patterns
        default_patterns = {
            "ENTITY": r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",
        }
        return {label: re.compile(pattern, re.IGNORECASE) for label, pattern in default_patterns.items()}

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text using compiled patterns."""
        found = []
        for label, pattern in self._compiled_patterns.items():
            for match in pattern.finditer(text):
                found.append({
                    "text": match.group(),
                    "label": label,
                    "start": match.start(),
                    "end": match.end(),
                })
        return found

    def calculate_theme_similarity(
        self,
        corpus: Corpus,
        max_features: int = 500,
        ngram_range: Tuple[int, int] = (1, 2),
    ) -> Tuple[List[str], Any]:
        """
        Calculate TF-IDF cosine similarity between themes.

        Args:
            corpus: The corpus to analyze
            max_features: Maximum vocabulary size
            ngram_range: N-gram range for TF-IDF

        Returns:
            Tuple of (theme_ids, similarity_matrix)
        """
        theme_texts = self.get_theme_texts(corpus)
        theme_ids = list(theme_texts.keys())
        texts = list(theme_texts.values())

        if not texts:
            return [], []

        if not SKLEARN_AVAILABLE:
            # Return empty similarity matrix if sklearn not available
            n = len(theme_ids)
            return theme_ids, [[0.0] * n for _ in range(n)]

        vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words="english",
            ngram_range=ngram_range,
        )

        tfidf_matrix = vectorizer.fit_transform(texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)

        return theme_ids, similarity_matrix

    def build_cooccurrence(
        self,
        corpus: Corpus,
        window: str = "paragraph",
    ) -> Dict[str, Dict[str, int]]:
        """
        Build entity co-occurrence matrix within specified window.

        Args:
            corpus: The corpus to analyze
            window: Window size ('paragraph', 'theme', or 'sentence')

        Returns:
            Nested dict mapping entity pairs to counts
        """
        cooccurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        if window == "theme":
            level = AtomLevel.THEME
        elif window == "paragraph":
            level = AtomLevel.PARAGRAPH
        else:
            level = AtomLevel.SENTENCE

        for _, atom in self.iter_atoms(corpus, level):
            entities = self._extract_entities(atom.text)
            unique_keys = list({self._entity_key(e["text"], e["label"]) for e in entities})

            # Increment co-occurrence for all pairs
            for i, key_a in enumerate(unique_keys):
                for key_b in unique_keys[i + 1:]:
                    cooccurrence[key_a][key_b] += 1
                    cooccurrence[key_b][key_a] += 1

        return cooccurrence

    def extract_all_entities(self, corpus: Corpus) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Extract entities from all themes.

        Returns:
            Dict mapping theme_id -> entity_type -> list of entity dicts
        """
        entities_by_theme: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))

        for _, theme in self.iter_atoms(corpus, AtomLevel.THEME):
            theme_id = theme.id
            for entity in self._extract_entities(theme.text):
                key = self._entity_key(entity["text"], entity["label"])
                self._entity_mentions[key].add(theme_id)
                entities_by_theme[theme_id][entity["label"]].append(entity)

        return entities_by_theme

    def create_network_data(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile],
        similarity_threshold: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Create complete network data for visualization.

        Args:
            corpus: The corpus to analyze
            domain: Optional domain profile for entity patterns
            similarity_threshold: Minimum similarity for theme edges

        Returns:
            Dict with 'nodes' and 'edges' for D3.js visualization
        """
        # Compile patterns
        self._compiled_patterns = self._compile_patterns(domain)

        # Extract entities
        entities_by_theme = self.extract_all_entities(corpus)

        # Build nodes
        nodes = []
        entity_colors = {}

        if domain and domain.primary_patterns:
            # Load colors from domain patterns if available
            try:
                import yaml
                patterns_file = list(domain.entity_patterns[0].patterns)
                # Colors would be in metadata
            except Exception:
                pass

        # Default colors
        default_colors = {
            "MILITARY_TERM": "#d62728",
            "LOCATION": "#2ca02c",
            "EQUIPMENT": "#9467bd",
            "RANK": "#d62728",
            "UNIT": "#ff7f0e",
            "ENTITY": "#7f7f7f",
        }

        # Theme nodes
        for doc in corpus.documents:
            for theme in doc.root_atoms:
                nodes.append({
                    "id": theme.id,
                    "label": theme.metadata.get("title", theme.id),
                    "type": "theme",
                    "size": 20,
                    "color": "#1f77b4",
                })

        # Entity nodes
        for key, themes in self._entity_mentions.items():
            label, text = key.split(":", 1)
            nodes.append({
                "id": key,
                "label": text,
                "type": "entity",
                "entity_type": label,
                "size": 8,
                "mention_count": len(themes),
                "color": default_colors.get(label, "#7f7f7f"),
            })

        # Build edges
        edges = []

        # Theme similarity edges
        theme_ids, similarity_matrix = self.calculate_theme_similarity(corpus)
        for i, theme_id_1 in enumerate(theme_ids):
            for j, theme_id_2 in enumerate(theme_ids):
                if i < j:
                    similarity = similarity_matrix[i][j]
                    if similarity > similarity_threshold:
                        edges.append({
                            "source": theme_id_1,
                            "target": theme_id_2,
                            "weight": float(similarity),
                            "type": "semantic_similarity",
                        })

        # Sequential adjacency
        for idx in range(len(theme_ids) - 1):
            edges.append({
                "source": theme_ids[idx],
                "target": theme_ids[idx + 1],
                "weight": 1.0,
                "type": "sequential_adjacency",
            })

        # Co-occurrence edges
        cooccurrence = self.build_cooccurrence(corpus, window="paragraph")
        for ent_a, neighbors in cooccurrence.items():
            for ent_b, count in neighbors.items():
                if ent_a < ent_b:
                    edges.append({
                        "source": ent_a,
                        "target": ent_b,
                        "weight": int(count),
                        "type": "cooccurrence",
                    })

        # Theme → entity mention edges
        seen_mentions = set()
        for theme_id, entity_map in entities_by_theme.items():
            for entity_type, ent_list in entity_map.items():
                for ent in ent_list:
                    key = self._entity_key(ent["text"], ent["label"])
                    if (theme_id, key) not in seen_mentions:
                        seen_mentions.add((theme_id, key))
                        edges.append({
                            "source": theme_id,
                            "target": key,
                            "weight": 1.0,
                            "type": "mention",
                        })

        return {
            "nodes": nodes,
            "edges": edges,
        }

    def analyze(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Run semantic network analysis.

        Config options:
            similarity_threshold (float): Min similarity for edges (default: 0.3)
            max_features (int): TF-IDF vocabulary size (default: 500)
            ngram_range (tuple): N-gram range (default: (1, 2))
        """
        self._config = config or {}
        threshold = self._config.get("similarity_threshold", 0.3)

        # Clear state
        self._entity_mentions.clear()

        # Generate network data
        network = self.create_network_data(corpus, domain, threshold)

        return self.make_output(
            data=network,
            metadata={
                "total_nodes": len(network["nodes"]),
                "total_edges": len(network["edges"]),
                "similarity_threshold": threshold,
            },
        )
