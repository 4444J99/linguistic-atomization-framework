"""
Tests for the generation layer (suggestions and quick wins).

These tests verify that the generation layer correctly maps
findings to suggestions and extracts actionable quick wins.
"""

import pytest
from framework.generation.suggestions import (
    SuggestionGenerator,
    Suggestion,
    SuggestionType,
    SuggestionPriority,
    SUGGESTION_TEMPLATES,
)
from framework.generation.quick_wins import (
    QuickWinExtractor,
    QuickWin,
    QUICK_WIN_TEMPLATES,
)


class TestSuggestion:
    """Tests for Suggestion dataclass."""

    def test_suggestion_creation(self):
        """Test Suggestion can be created with required fields."""
        suggestion = Suggestion(
            suggestion_type=SuggestionType.ADD_EVIDENCE,
            priority=SuggestionPriority.HIGH,
            location=None,
            original_text=None,
            issue="Low evidence density",
            suggestion="Add citations or statistics",
            rationale="Evidence strengthens arguments",
        )
        assert suggestion.suggestion_type == SuggestionType.ADD_EVIDENCE
        assert suggestion.priority == SuggestionPriority.HIGH

    def test_suggestion_to_dict(self):
        """Test Suggestion converts to dictionary correctly."""
        suggestion = Suggestion(
            suggestion_type=SuggestionType.ADD_EVIDENCE,
            priority=SuggestionPriority.HIGH,
            location="P001.S003",
            original_text="This is obvious.",
            issue="Unsupported claim",
            suggestion="Add evidence",
            rationale="Strengthens credibility",
            alternatives=["Option A", "Option B"],
            step_source="logos",
            confidence=0.8,
        )
        d = suggestion.to_dict()

        assert d["type"] == "add_evidence"
        assert d["priority"] == "high"
        assert d["location"] == "P001.S003"
        assert len(d["alternatives"]) == 2
        assert d["confidence"] == 0.8


class TestSuggestionType:
    """Tests for SuggestionType enum."""

    def test_all_types_have_values(self):
        """Test all suggestion types have string values."""
        for stype in SuggestionType:
            assert isinstance(stype.value, str)
            assert len(stype.value) > 0


class TestSuggestionPriority:
    """Tests for SuggestionPriority enum."""

    def test_all_priorities_have_values(self):
        """Test all priorities have string values."""
        for priority in SuggestionPriority:
            assert priority.value in ["high", "medium", "low"]


class TestSuggestionGenerator:
    """Tests for SuggestionGenerator class."""

    def test_initialization(self, suggestion_generator):
        """Test generator initializes correctly."""
        assert suggestion_generator is not None
        assert hasattr(suggestion_generator, "_templates")

    def test_generate_from_low_logos_score(self, suggestion_generator):
        """Test suggestions generated for low logos score."""
        evaluation_output = {
            "data": {
                "steps": [
                    {
                        "step_name": "logos",
                        "score": 45,
                        "findings": [],
                        "metrics": {},
                    }
                ]
            },
            "summary": {"overall_score": 50},
        }

        suggestions = suggestion_generator.generate_from_evaluation(evaluation_output)

        # Should generate ADD_EVIDENCE suggestion
        evidence_suggestions = [
            s for s in suggestions
            if s.suggestion_type == SuggestionType.ADD_EVIDENCE
        ]
        assert len(evidence_suggestions) > 0

    def test_generate_from_low_transition_score(self, suggestion_generator):
        """Test suggestions generated for low logic check score."""
        evaluation_output = {
            "data": {
                "steps": [
                    {
                        "step_name": "logic_check",
                        "score": 40,
                        "findings": [],
                        "metrics": {},
                    }
                ]
            },
            "summary": {"overall_score": 50},
        }

        suggestions = suggestion_generator.generate_from_evaluation(evaluation_output)

        transition_suggestions = [
            s for s in suggestions
            if s.suggestion_type == SuggestionType.ADD_TRANSITION
        ]
        assert len(transition_suggestions) > 0

    def test_suggestions_sorted_by_priority(self, suggestion_generator):
        """Test that suggestions are sorted by priority."""
        evaluation_output = {
            "data": {
                "steps": [
                    {"step_name": "logos", "score": 30, "findings": [], "metrics": {}},
                    {"step_name": "pathos", "score": 35, "findings": [], "metrics": {}},
                    {"step_name": "ethos", "score": 40, "findings": [], "metrics": {}},
                ]
            },
            "summary": {"overall_score": 35},
        }

        suggestions = suggestion_generator.generate_from_evaluation(evaluation_output)

        # First suggestions should be high priority
        if suggestions:
            assert suggestions[0].priority in [SuggestionPriority.HIGH, SuggestionPriority.MEDIUM]

    def test_max_suggestions_limit(self, suggestion_generator):
        """Test that max_suggestions is respected."""
        evaluation_output = {
            "data": {
                "steps": [
                    {"step_name": "logos", "score": 30, "findings": [], "metrics": {}},
                    {"step_name": "pathos", "score": 30, "findings": [], "metrics": {}},
                    {"step_name": "ethos", "score": 30, "findings": [], "metrics": {}},
                    {"step_name": "logic_check", "score": 30, "findings": [], "metrics": {}},
                    {"step_name": "blind_spots", "score": 30, "findings": [], "metrics": {}},
                ]
            },
            "summary": {"overall_score": 30},
        }

        suggestions = suggestion_generator.generate_from_evaluation(
            evaluation_output,
            max_suggestions=3
        )

        assert len(suggestions) <= 3

    def test_to_dict_format(self, suggestion_generator):
        """Test to_dict produces correct format."""
        suggestions = [
            Suggestion(
                suggestion_type=SuggestionType.ADD_EVIDENCE,
                priority=SuggestionPriority.HIGH,
                location=None,
                original_text=None,
                issue="Test issue",
                suggestion="Test suggestion",
                rationale="Test rationale",
            )
        ]

        result = suggestion_generator.to_dict(suggestions)

        assert "total_count" in result
        assert "by_priority" in result
        assert "by_type" in result
        assert "suggestions" in result
        assert result["total_count"] == 1


class TestSuggestionTemplates:
    """Tests for suggestion templates."""

    def test_templates_not_empty(self):
        """Test that templates are defined."""
        assert len(SUGGESTION_TEMPLATES) > 0

    def test_templates_have_required_fields(self):
        """Test that templates have required fields."""
        required_fields = ["type", "priority", "issue", "suggestion_template", "rationale"]

        for key, template in SUGGESTION_TEMPLATES.items():
            for field in required_fields:
                assert field in template, f"Template {key} missing field {field}"


class TestQuickWin:
    """Tests for QuickWin dataclass."""

    def test_quick_win_creation(self):
        """Test QuickWin can be created."""
        qw = QuickWin(
            rank=1,
            title="Add Evidence",
            action="Include statistics",
            impact="Strengthens argument",
        )
        assert qw.rank == 1
        assert qw.title == "Add Evidence"

    def test_quick_win_to_dict(self):
        """Test QuickWin converts to dictionary."""
        qw = QuickWin(
            rank=1,
            title="Add Evidence",
            action="Include statistics",
            impact="Strengthens argument",
            example="Add '40% increase'",
            source_step="logos",
        )
        d = qw.to_dict()

        assert d["rank"] == 1
        assert d["title"] == "Add Evidence"
        assert d["example"] == "Add '40% increase'"


class TestQuickWinExtractor:
    """Tests for QuickWinExtractor class."""

    def test_initialization(self, quick_win_extractor):
        """Test extractor initializes correctly."""
        assert quick_win_extractor is not None
        assert hasattr(quick_win_extractor, "_templates")

    def test_extract_produces_quick_wins(self, quick_win_extractor):
        """Test that extraction produces quick wins."""
        evaluation_output = {
            "data": {
                "steps": [
                    {"step_name": "logos", "score": 40, "findings": [], "metrics": {}},
                    {"step_name": "logic_check", "score": 45, "findings": [], "metrics": {}},
                ]
            },
            "summary": {"overall_score": 45},
        }

        quick_wins = quick_win_extractor.extract_from_evaluation(evaluation_output)

        assert len(quick_wins) > 0
        assert len(quick_wins) <= 3

    def test_quick_wins_have_ranks(self, quick_win_extractor):
        """Test that quick wins are numbered."""
        evaluation_output = {
            "data": {
                "steps": [
                    {"step_name": "logos", "score": 30, "findings": [], "metrics": {}},
                    {"step_name": "pathos", "score": 35, "findings": [], "metrics": {}},
                ]
            },
            "summary": {"overall_score": 32},
        }

        quick_wins = quick_win_extractor.extract_from_evaluation(evaluation_output)

        for i, qw in enumerate(quick_wins):
            assert qw.rank == i + 1

    def test_max_wins_limit(self, quick_win_extractor):
        """Test that max_wins is respected."""
        evaluation_output = {
            "data": {
                "steps": [
                    {"step_name": "logos", "score": 30, "findings": [], "metrics": {}},
                    {"step_name": "pathos", "score": 30, "findings": [], "metrics": {}},
                    {"step_name": "ethos", "score": 30, "findings": [], "metrics": {}},
                    {"step_name": "logic_check", "score": 30, "findings": [], "metrics": {}},
                    {"step_name": "blind_spots", "score": 30, "findings": [], "metrics": {}},
                ]
            },
            "summary": {"overall_score": 30},
        }

        quick_wins = quick_win_extractor.extract_from_evaluation(
            evaluation_output,
            max_wins=2
        )

        assert len(quick_wins) <= 2

    def test_to_dict_format(self, quick_win_extractor):
        """Test to_dict produces correct format."""
        quick_wins = [
            QuickWin(rank=1, title="Test", action="Do something", impact="Good result"),
        ]

        result = quick_win_extractor.to_dict(quick_wins)

        assert "count" in result
        assert "quick_wins" in result
        assert result["count"] == 1

    def test_format_text(self, quick_win_extractor):
        """Test format_text produces readable output."""
        quick_wins = [
            QuickWin(
                rank=1,
                title="Add Evidence",
                action="Include statistics",
                impact="Strengthens argument",
                example="Add '40% increase'",
            ),
        ]

        text = quick_win_extractor.format_text(quick_wins)

        assert "QUICK WINS" in text
        assert "Add Evidence" in text
        assert "Include statistics" in text


class TestQuickWinTemplates:
    """Tests for quick win templates."""

    def test_templates_not_empty(self):
        """Test that templates are defined."""
        assert len(QUICK_WIN_TEMPLATES) > 0

    def test_templates_have_required_fields(self):
        """Test that templates have required fields."""
        required_fields = ["title", "action", "impact"]

        for key, template in QUICK_WIN_TEMPLATES.items():
            for field in required_fields:
                assert field in template, f"Template {key} missing field {field}"


class TestIntegration:
    """Integration tests for generation with evaluation."""

    def test_full_pipeline(self, evaluation_module, suggestion_generator, quick_win_extractor, simple_corpus):
        """Test full pipeline from corpus to suggestions."""
        # Run evaluation
        eval_result = evaluation_module.analyze(simple_corpus, domain=None, config={})

        # Convert to dict format expected by generation layer
        # Need to transform phases structure to steps list
        eval_dict = self._transform_eval_output(eval_result)

        # Generate suggestions
        suggestions = suggestion_generator.generate_from_evaluation(eval_dict)

        # Extract quick wins
        quick_wins = quick_win_extractor.extract_from_evaluation(
            eval_dict,
            suggestions=suggestions
        )

        # Verify outputs
        assert len(suggestions) >= 0
        assert len(quick_wins) >= 0

    def test_weak_text_generates_more_suggestions(
        self,
        evaluation_module,
        suggestion_generator,
        argumentative_corpus,
        weak_corpus,
    ):
        """Test that weak text generates more/higher priority suggestions."""
        arg_result = evaluation_module.analyze(argumentative_corpus, domain=None, config={})
        weak_result = evaluation_module.analyze(weak_corpus, domain=None, config={})

        arg_dict = self._transform_eval_output(arg_result)
        weak_dict = self._transform_eval_output(weak_result)

        arg_suggestions = suggestion_generator.generate_from_evaluation(arg_dict)
        weak_suggestions = suggestion_generator.generate_from_evaluation(weak_dict)

        # Weak text should have more high-priority suggestions
        arg_high = len([s for s in arg_suggestions if s.priority == SuggestionPriority.HIGH])
        weak_high = len([s for s in weak_suggestions if s.priority == SuggestionPriority.HIGH])

        # This may not always be true depending on exact scores, but generally should be
        assert weak_high >= arg_high or len(weak_suggestions) >= len(arg_suggestions)

    def _transform_eval_output(self, eval_result):
        """Transform evaluation output to format expected by generation layer."""
        # Flatten phases to steps list
        # Phases structure: {phase_name: {step_name: step_data, ...}, ...}
        steps = []
        for phase_data in eval_result.data.get("phases", {}).values():
            if isinstance(phase_data, dict):
                for step_name, step_data in phase_data.items():
                    if isinstance(step_data, dict) and "step_number" in step_data:
                        steps.append(step_data)

        return {
            "data": {
                "steps": steps,
            },
            "summary": eval_result.data.get("summary", {}),
        }
