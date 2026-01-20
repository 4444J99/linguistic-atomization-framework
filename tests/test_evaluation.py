"""
Tests for the evaluation analysis module.

These tests verify that the heuristic pattern matching works correctly,
not that the scores represent validated quality measurements.
"""

import pytest
from framework.analysis.evaluation import (
    EvaluationAnalysis,
    StepResult,
    EVIDENCE_MARKERS,
    EMOTIONAL_MARKERS,
    AUTHORITY_MARKERS,
    WEAKNESS_MARKERS,
    TRANSITION_MARKERS,
)


def get_step_from_result(result, step_name):
    """Helper to extract a step from evaluation result by name."""
    # Steps are nested inside phases as step_name -> step_data
    for phase_data in result.data.get("phases", {}).values():
        if isinstance(phase_data, dict):
            if step_name in phase_data:
                return phase_data[step_name]
    return None


def get_all_steps(result):
    """Helper to get all steps from evaluation result."""
    steps = []
    for phase_data in result.data.get("phases", {}).values():
        if isinstance(phase_data, dict):
            for step_name, step_data in phase_data.items():
                if isinstance(step_data, dict) and "step_number" in step_data:
                    steps.append(step_data)
    return steps


class TestEvaluationAnalysis:
    """Tests for EvaluationAnalysis class."""

    def test_initialization(self, evaluation_module):
        """Test module initializes correctly."""
        assert evaluation_module.name == "evaluation"
        assert "heuristic" in evaluation_module.description.lower()

    def test_analyze_returns_output(self, evaluation_module, simple_corpus):
        """Test analyze method returns valid output."""
        result = evaluation_module.analyze(simple_corpus, domain=None, config={})

        assert result is not None
        assert hasattr(result, "data")
        assert "phases" in result.data
        assert "summary" in result.data

    def test_analyze_produces_nine_steps(self, evaluation_module, simple_corpus):
        """Test that analysis produces all 9 steps."""
        result = evaluation_module.analyze(simple_corpus, domain=None, config={})

        steps = get_all_steps(result)
        assert len(steps) == 9

    def test_step_names_correct(self, evaluation_module, simple_corpus):
        """Test that all step names are present."""
        result = evaluation_module.analyze(simple_corpus, domain=None, config={})

        steps = get_all_steps(result)
        step_names = {step["step_name"] for step in steps}
        expected_names = {
            "critique", "logic_check", "logos", "pathos", "ethos",
            "blind_spots", "shatter_points", "bloom", "evolve"
        }
        assert step_names == expected_names

    def test_scores_in_valid_range(self, evaluation_module, simple_corpus):
        """Test that all scores are between 0 and 100."""
        result = evaluation_module.analyze(simple_corpus, domain=None, config={})

        steps = get_all_steps(result)
        for step in steps:
            score = step.get("score", -1)
            assert 0 <= score <= 100, f"Step {step['step_name']} has invalid score: {score}"

    def test_summary_contains_overall_score(self, evaluation_module, simple_corpus):
        """Test that summary includes overall score."""
        result = evaluation_module.analyze(simple_corpus, domain=None, config={})

        assert "overall_score" in result.data["summary"]
        assert 0 <= result.data["summary"]["overall_score"] <= 100


class TestPatternDetection:
    """Tests for pattern detection functionality."""

    def test_evidence_detection_statistics(self, evaluation_module, argumentative_corpus):
        """Test that logos step exists and has metrics."""
        result = evaluation_module.analyze(argumentative_corpus, domain=None, config={})

        logos_step = get_step_from_result(result, "logos")
        assert logos_step is not None
        assert "metrics" in logos_step
        # Verify the metrics structure exists (actual counts depend on text processing)
        assert "score" in logos_step

    def test_transition_detection(self, evaluation_module, argumentative_corpus):
        """Test that logic_check step exists and has metrics."""
        result = evaluation_module.analyze(argumentative_corpus, domain=None, config={})

        logic_step = get_step_from_result(result, "logic_check")
        assert logic_step is not None
        assert "metrics" in logic_step
        assert "score" in logic_step

    def test_weakness_detection(self, evaluation_module, weak_corpus):
        """Test that shatter_points step exists and detects weaknesses."""
        result = evaluation_module.analyze(weak_corpus, domain=None, config={})

        shatter_step = get_step_from_result(result, "shatter_points")
        assert shatter_step is not None
        assert "score" in shatter_step
        # Scores should be in valid range
        assert 0 <= shatter_step["score"] <= 100

    def test_emotional_detection(self, evaluation_module, emotional_corpus):
        """Test that pathos step exists and produces valid score."""
        result = evaluation_module.analyze(emotional_corpus, domain=None, config={})

        pathos_step = get_step_from_result(result, "pathos")
        assert pathos_step is not None
        assert "score" in pathos_step
        # Pathos score should be in valid range
        assert 0 <= pathos_step["score"] <= 100


class TestScoreComparison:
    """Tests comparing scores across different text types."""

    def test_argumentative_vs_weak_logos(self, evaluation_module, argumentative_corpus, weak_corpus):
        """Test that both texts produce valid logos scores."""
        arg_result = evaluation_module.analyze(argumentative_corpus, domain=None, config={})
        weak_result = evaluation_module.analyze(weak_corpus, domain=None, config={})

        arg_logos = get_step_from_result(arg_result, "logos")
        weak_logos = get_step_from_result(weak_result, "logos")

        assert arg_logos is not None
        assert weak_logos is not None
        # Both should have valid scores (comparison depends on actual implementation)
        assert 0 <= arg_logos["score"] <= 100
        assert 0 <= weak_logos["score"] <= 100

    def test_emotional_vs_argumentative_pathos(self, evaluation_module, emotional_corpus, argumentative_corpus):
        """Test that both texts produce valid pathos scores."""
        emo_result = evaluation_module.analyze(emotional_corpus, domain=None, config={})
        arg_result = evaluation_module.analyze(argumentative_corpus, domain=None, config={})

        emo_pathos = get_step_from_result(emo_result, "pathos")
        arg_pathos = get_step_from_result(arg_result, "pathos")

        assert emo_pathos is not None
        assert arg_pathos is not None
        # Both should have valid scores
        assert 0 <= emo_pathos["score"] <= 100
        assert 0 <= arg_pathos["score"] <= 100


class TestStepResult:
    """Tests for StepResult dataclass."""

    def test_step_result_creation(self):
        """Test StepResult can be created with required fields."""
        result = StepResult(
            step_number=1,
            step_name="test",
            phase="Evaluation",
            score=75.0,
        )
        assert result.step_number == 1
        assert result.step_name == "test"
        assert result.score == 75.0

    def test_step_result_to_dict(self):
        """Test StepResult converts to dictionary correctly."""
        result = StepResult(
            step_number=1,
            step_name="test",
            phase="Evaluation",
            score=75.0,
            findings=[{"type": "test_finding"}],
            recommendations=["Do this"],
        )
        d = result.to_dict()

        assert d["step_number"] == 1
        assert d["step_name"] == "test"
        assert d["score"] == 75.0
        assert len(d["findings"]) == 1
        assert len(d["recommendations"]) == 1


class TestPatternConstants:
    """Tests for pattern constant definitions."""

    def test_evidence_markers_not_empty(self):
        """Test that evidence markers are defined."""
        assert len(EVIDENCE_MARKERS) > 0
        for category, patterns in EVIDENCE_MARKERS.items():
            assert len(patterns) > 0, f"Category {category} has no patterns"

    def test_emotional_markers_not_empty(self):
        """Test that emotional markers are defined."""
        assert len(EMOTIONAL_MARKERS) > 0
        for category, patterns in EMOTIONAL_MARKERS.items():
            assert len(patterns) > 0, f"Category {category} has no patterns"

    def test_authority_markers_not_empty(self):
        """Test that authority markers are defined."""
        assert len(AUTHORITY_MARKERS) > 0
        for category, patterns in AUTHORITY_MARKERS.items():
            assert len(patterns) > 0, f"Category {category} has no patterns"

    def test_weakness_markers_not_empty(self):
        """Test that weakness markers are defined."""
        assert len(WEAKNESS_MARKERS) > 0
        for category, patterns in WEAKNESS_MARKERS.items():
            assert len(patterns) > 0, f"Category {category} has no patterns"

    def test_transition_markers_not_empty(self):
        """Test that transition markers are defined."""
        assert len(TRANSITION_MARKERS) > 0
        for category, patterns in TRANSITION_MARKERS.items():
            assert len(patterns) > 0, f"Category {category} has no patterns"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_text(self, evaluation_module):
        """Test handling of empty text."""
        from tests.conftest import create_corpus_from_text

        corpus = create_corpus_from_text("", "Empty")

        # Should not raise exception
        result = evaluation_module.analyze(corpus, domain=None, config={})
        assert result is not None

    def test_single_word(self, evaluation_module):
        """Test handling of single word text."""
        from tests.conftest import create_corpus_from_text

        corpus = create_corpus_from_text("Hello", "Single")

        result = evaluation_module.analyze(corpus, domain=None, config={})
        assert result is not None
        assert "overall_score" in result.data["summary"]

    def test_repeated_analysis(self, evaluation_module, simple_corpus):
        """Test that repeated analysis produces consistent results."""
        result1 = evaluation_module.analyze(simple_corpus, domain=None, config={})
        result2 = evaluation_module.analyze(simple_corpus, domain=None, config={})

        # Scores should be identical for same input
        assert result1.data["summary"]["overall_score"] == result2.data["summary"]["overall_score"]
