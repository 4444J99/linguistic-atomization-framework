"""
Validation tests using gold standard annotated data.

These tests verify analysis module outputs against human-annotated
expected results to track precision and recall.

Note: These tests establish baselines. Not all tests are expected to pass
initially - they track improvement over time.
"""

import pytest
import yaml
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from datetime import datetime
from framework.core.ontology import Corpus, Document, Atom, AtomLevel, AtomizationSchema
from framework.core.atomizer import Atomizer


@dataclass
class ValidationResult:
    """Result of comparing expected vs actual analysis output."""
    sample_id: str
    module: str
    expected: dict
    actual: dict
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    notes: str = ""


def create_corpus_from_text(text: str, title: str = "Test Document") -> Corpus:
    """Helper function to create a corpus from raw text."""
    schema = AtomizationSchema(
        name="test",
        levels=[AtomLevel.THEME, AtomLevel.PARAGRAPH, AtomLevel.SENTENCE],
    )
    atomizer = Atomizer(schema)

    doc = Document(
        id=f"DOC_{abs(hash(title)) % 10000:04d}",
        source_path=Path(f"/tmp/test_{title.replace(' ', '_')}.txt"),
        format="plain",
        title=title,
    )

    first_level = schema.levels[0]
    doc.root_atoms = atomizer.atomize_text(text, first_level)

    corpus = Corpus(
        name=title,
        documents=[doc],
        schema=schema,
        created_at=datetime.now(),
    )

    return corpus


def load_gold_standard() -> dict:
    """Load gold standard validation data."""
    gold_path = Path(__file__).parent / "gold_standard.yaml"
    if not gold_path.exists():
        pytest.skip("Gold standard data not found")
    with open(gold_path) as f:
        return yaml.safe_load(f)


def calculate_set_metrics(expected: set, actual: set) -> tuple[int, int, int, float, float, float]:
    """Calculate precision, recall, and F1 for set comparison."""
    true_positives = len(expected & actual)
    false_positives = len(actual - expected)
    false_negatives = len(expected - actual)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return true_positives, false_positives, false_negatives, precision, recall, f1


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, strip)."""
    return text.lower().strip()


class TestSentimentValidation:
    """Validation tests for sentiment analysis module."""

    @pytest.fixture
    def sentiment_module(self):
        """Load sentiment analysis module."""
        from framework.analysis.sentiment import SentimentAnalysis
        return SentimentAnalysis()

    @pytest.fixture
    def gold_samples(self):
        """Load sentiment-related gold standard samples."""
        data = load_gold_standard()
        return [s for s in data.get("validation_samples", []) if s["id"].startswith("sentiment-")]

    def test_sentiment_analysis_runs(self, sentiment_module, gold_samples):
        """Test sentiment analysis produces results for all samples."""
        for sample in gold_samples:
            text = sample["text"]
            corpus = create_corpus_from_text(text, sample["id"])
            result = sentiment_module.analyze(corpus, domain=None, config={})
            assert result is not None, f"Analysis failed for {sample['id']}"
            assert "sentence_sentiments" in result.data or "overall_statistics" in result.data

    def test_sentiment_polarity_baseline(self, sentiment_module, gold_samples):
        """Baseline measurement of sentiment polarity accuracy (tracking only)."""
        correct = 0
        total = len(gold_samples)

        for sample in gold_samples:
            text = sample["text"]
            expected = sample["expected"]["sentiment"]
            corpus = create_corpus_from_text(text, sample["id"])
            result = sentiment_module.analyze(corpus, domain=None, config={})

            avg_sentiment = result.data.get("average_sentiment", 0)
            if avg_sentiment > 0.1:
                actual_polarity = "positive"
            elif avg_sentiment < -0.1:
                actual_polarity = "negative"
            else:
                actual_polarity = "neutral"

            if actual_polarity == expected["polarity"]:
                correct += 1

        accuracy = correct / total if total > 0 else 0
        print(f"\n[BASELINE] Sentiment polarity accuracy: {accuracy:.1%} ({correct}/{total})")
        # No assertion - this is a baseline measurement


class TestEntityValidation:
    """Validation tests for entity extraction module."""

    @pytest.fixture
    def entity_module(self):
        """Load entity analysis module."""
        from framework.analysis.entity import EntityAnalysis
        return EntityAnalysis()

    @pytest.fixture
    def gold_samples(self):
        """Load entity-related gold standard samples."""
        data = load_gold_standard()
        return [s for s in data.get("validation_samples", []) if s["id"].startswith("entity-")]

    def test_entity_analysis_runs(self, entity_module, gold_samples):
        """Test entity analysis produces results for all samples."""
        for sample in gold_samples:
            text = sample["text"]
            corpus = create_corpus_from_text(text, sample["id"])
            result = entity_module.analyze(corpus, domain=None, config={})
            assert result is not None, f"Analysis failed for {sample['id']}"

    def test_entity_extraction_baseline(self, entity_module, gold_samples):
        """Baseline measurement of entity extraction (tracking only)."""
        for sample in gold_samples:
            text = sample["text"]
            corpus = create_corpus_from_text(text, sample["id"])
            result = entity_module.analyze(corpus, domain=None, config={})

            total_entities = result.data.get("total_entities", 0)
            entities = result.data.get("entities", [])
            print(f"\n[BASELINE] {sample['id']}: Found {total_entities} entities, {len(entities)} items")
            # No assertion - this is a baseline measurement


class TestTemporalValidation:
    """Validation tests for temporal analysis module."""

    @pytest.fixture
    def temporal_module(self):
        """Load temporal analysis module."""
        from framework.analysis.temporal import TemporalAnalysis
        return TemporalAnalysis()

    @pytest.fixture
    def gold_samples(self):
        """Load temporal-related gold standard samples."""
        data = load_gold_standard()
        return [s for s in data.get("validation_samples", []) if s["id"].startswith("temporal-")]

    def test_temporal_analysis_runs(self, temporal_module, gold_samples):
        """Test temporal analysis produces results for all samples."""
        for sample in gold_samples:
            text = sample["text"]
            corpus = create_corpus_from_text(text, sample["id"])
            result = temporal_module.analyze(corpus, domain=None, config={})
            assert result is not None, f"Analysis failed for {sample['id']}"

    def test_tense_detection_baseline(self, temporal_module, gold_samples):
        """Baseline measurement of tense detection (tracking only)."""
        for sample in gold_samples:
            text = sample["text"]
            corpus = create_corpus_from_text(text, sample["id"])
            result = temporal_module.analyze(corpus, domain=None, config={})

            tense_counts = result.data.get("tense_distribution", {})
            total = sum(tense_counts.values())
            print(f"\n[BASELINE] {sample['id']}: Detected {total} verb tenses")
            print(f"  Distribution: {tense_counts}")
            # No assertion - this is a baseline measurement


class TestSemanticValidation:
    """Validation tests for semantic analysis module."""

    @pytest.fixture
    def semantic_module(self):
        """Load semantic analysis module."""
        from framework.analysis.semantic import SemanticAnalysis
        return SemanticAnalysis()

    @pytest.fixture
    def gold_samples(self):
        """Load semantic-related gold standard samples."""
        data = load_gold_standard()
        return [s for s in data.get("validation_samples", []) if s["id"].startswith("semantic-")]

    def test_semantic_analysis_runs(self, semantic_module, gold_samples):
        """Test semantic analysis produces results for all samples."""
        for sample in gold_samples:
            text = sample["text"]
            corpus = create_corpus_from_text(text, sample["id"])
            result = semantic_module.analyze(corpus, domain=None, config={})
            assert result is not None, f"Analysis failed for {sample['id']}"

    def test_theme_extraction_baseline(self, semantic_module, gold_samples):
        """Baseline measurement of theme extraction (tracking only)."""
        for sample in gold_samples:
            text = sample["text"]
            corpus = create_corpus_from_text(text, sample["id"])
            result = semantic_module.analyze(corpus, domain=None, config={})

            theme_count = result.data.get("theme_count", 0)
            print(f"\n[BASELINE] {sample['id']}: Found {theme_count} themes")
            # No assertion - this is a baseline measurement


class TestValidationReport:
    """Generate validation report across all modules."""

    def test_generate_validation_report(self):
        """Generate comprehensive validation report."""
        gold_data = load_gold_standard()
        samples = gold_data.get("validation_samples", [])

        report = {
            "total_samples": len(samples),
            "samples_by_module": {},
        }

        for sample in samples:
            module = sample["id"].split("-")[0]
            if module not in report["samples_by_module"]:
                report["samples_by_module"][module] = 0
            report["samples_by_module"][module] += 1

        print(f"\n=== Validation Data Summary ===")
        print(f"Total gold standard samples: {report['total_samples']}")
        for module, count in report["samples_by_module"].items():
            print(f"  {module}: {count} samples")

        assert report["total_samples"] > 0, "No validation samples found"
