"""
Translation Analysis Module - Cross-translation comparison and divergence metrics.

Compares original texts with their translations to identify:
- Semantic divergence (meaning shifts)
- Rhetorical divergence (ethos/pathos/logos changes)
- Structural divergence (sentence count, paragraph alignment)
- Lexical divergence (key term translation choices)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..core.ontology import (
    AnalysisOutput,
    AtomLevel,
    Corpus,
    Document,
    DomainProfile,
)
from ..core.registry import registry
from .base import BaseAnalysisModule

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    np = None
    EMBEDDINGS_AVAILABLE = False


@dataclass
class TranslationPair:
    """A pair of aligned text segments (original + translation)."""
    original_id: str
    translation_id: str
    original_text: str
    translation_text: str
    original_language: str
    translation_language: str
    alignment_confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DivergenceMetrics:
    """Metrics measuring divergence between original and translation."""
    semantic_distance: float = 0.0
    length_ratio: float = 1.0
    sentence_count_ratio: float = 1.0
    word_count_ratio: float = 1.0
    sentiment_delta: float = 0.0
    formality_delta: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "semantic_distance": self.semantic_distance,
            "length_ratio": self.length_ratio,
            "sentence_count_ratio": self.sentence_count_ratio,
            "word_count_ratio": self.word_count_ratio,
            "sentiment_delta": self.sentiment_delta,
            "formality_delta": self.formality_delta,
        }


@registry.register_analysis("translation")
class TranslationAnalysis(BaseAnalysisModule):
    """Cross-translation analysis module."""

    name = "translation"
    description = "Cross-translation comparison and divergence analysis"

    def __init__(self):
        super().__init__()
        self._model = None
        self._embeddings_available = EMBEDDINGS_AVAILABLE

        if EMBEDDINGS_AVAILABLE:
            try:
                self._model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            except Exception:
                self._embeddings_available = False

    def _compute_embedding(self, text: str) -> Optional[Any]:
        if not self._embeddings_available or not self._model:
            return None
        try:
            return self._model.encode(text)
        except Exception:
            return None

    def _cosine_similarity(self, vec1: Any, vec2: Any) -> float:
        if vec1 is None or vec2 is None or np is None:
            return 0.5
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot / (norm1 * norm2))

    def align_sentences(
        self,
        original_sentences: List[str],
        translation_sentences: List[str],
        original_lang: str,
        translation_lang: str,
    ) -> List[TranslationPair]:
        pairs = []
        min_len = min(len(original_sentences), len(translation_sentences))
        for i in range(min_len):
            pair = TranslationPair(
                original_id=f"S{i+1:05d}",
                translation_id=f"T{i+1:05d}",
                original_text=original_sentences[i],
                translation_text=translation_sentences[i],
                original_language=original_lang,
                translation_language=translation_lang,
                alignment_confidence=0.8,
            )
            pairs.append(pair)
        return pairs

    def compute_divergence(self, pair: TranslationPair) -> DivergenceMetrics:
        metrics = DivergenceMetrics()
        orig_len = len(pair.original_text)
        trans_len = len(pair.translation_text)
        metrics.length_ratio = trans_len / orig_len if orig_len > 0 else 1.0
        orig_words = len(pair.original_text.split())
        trans_words = len(pair.translation_text.split())
        metrics.word_count_ratio = trans_words / orig_words if orig_words > 0 else 1.0
        if self._embeddings_available:
            orig_emb = self._compute_embedding(pair.original_text)
            trans_emb = self._compute_embedding(pair.translation_text)
            similarity = self._cosine_similarity(orig_emb, trans_emb)
            metrics.semantic_distance = 1.0 - similarity
        return metrics

    def _iter_atoms_recursive(self, atoms, level: AtomLevel):
        for atom in atoms:
            if atom.level == level:
                yield atom
            yield from self._iter_atoms_recursive(atom.children, level)

    def analyze_translation_pair(
        self,
        original_doc: Document,
        translation_doc: Document,
    ) -> Dict[str, Any]:
        original_sentences = []
        translation_sentences = []
        for atom in self._iter_atoms_recursive(original_doc.root_atoms, AtomLevel.SENTENCE):
            original_sentences.append(atom.text)
        for atom in self._iter_atoms_recursive(translation_doc.root_atoms, AtomLevel.SENTENCE):
            translation_sentences.append(atom.text)
        pairs = self.align_sentences(
            original_sentences,
            translation_sentences,
            original_doc.language or "unknown",
            translation_doc.language or "unknown",
        )
        pair_analyses = []
        total_semantic_distance = 0.0
        for pair in pairs:
            metrics = self.compute_divergence(pair)
            total_semantic_distance += metrics.semantic_distance
            pair_analyses.append({
                "original_text": pair.original_text[:100] + "..." if len(pair.original_text) > 100 else pair.original_text,
                "translation_text": pair.translation_text[:100] + "..." if len(pair.translation_text) > 100 else pair.translation_text,
                "divergence": metrics.to_dict(),
                "alignment_confidence": pair.alignment_confidence,
            })
        avg_semantic_distance = total_semantic_distance / len(pairs) if pairs else 0.0
        return {
            "original_document": {"id": original_doc.id, "title": original_doc.title, "language": original_doc.language, "sentence_count": len(original_sentences)},
            "translation_document": {"id": translation_doc.id, "title": translation_doc.title, "language": translation_doc.language, "translator": translation_doc.translator, "sentence_count": len(translation_sentences)},
            "alignment": {"aligned_pairs": len(pairs), "unaligned_original": max(0, len(original_sentences) - len(pairs)), "unaligned_translation": max(0, len(translation_sentences) - len(pairs))},
            "aggregate_metrics": {"avg_semantic_distance": avg_semantic_distance, "sentence_count_ratio": len(translation_sentences) / len(original_sentences) if original_sentences else 1.0},
            "pair_analyses": pair_analyses[:50],
        }

    def find_translation_pairs(self, corpus: Corpus) -> List[Tuple[Document, Document]]:
        pairs = []
        doc_by_id = {doc.id: doc for doc in corpus.documents}
        for doc in corpus.documents:
            if doc.translation_of and doc.translation_of in doc_by_id:
                original = doc_by_id[doc.translation_of]
                pairs.append((original, doc))
        return pairs

    def analyze(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        self._config = config or {}
        max_pairs = self._config.get("max_pairs", 10)
        include_details = self._config.get("include_pair_details", True)
        pairs = self.find_translation_pairs(corpus)
        if not pairs:
            return self.make_output(
                data={"message": "No translation pairs found in corpus", "hint": "Set translation_of field on documents to link translations to originals"},
                metadata={"pairs_found": 0},
            )
        pair_results = []
        for original, translation in pairs[:max_pairs]:
            result = self.analyze_translation_pair(original, translation)
            if not include_details:
                del result["pair_analyses"]
            pair_results.append(result)
        all_distances = [r["aggregate_metrics"]["avg_semantic_distance"] for r in pair_results]
        return self.make_output(
            data={
                "translation_pairs": pair_results,
                "corpus_summary": {
                    "total_pairs": len(pairs),
                    "analyzed_pairs": len(pair_results),
                    "languages": list(set(d.language for d in corpus.documents if d.language)),
                    "avg_semantic_distance": sum(all_distances) / len(all_distances) if all_distances else 0.0,
                },
            },
            metadata={"embeddings_available": self._embeddings_available, "model": "paraphrase-multilingual-MiniLM-L12-v2" if self._embeddings_available else None},
        )
