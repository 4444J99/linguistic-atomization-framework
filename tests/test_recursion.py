"""
Tests for the recursion tracking module.

These tests verify that iteration tracking, comparison, and
progress reporting work correctly.
"""

import pytest
from datetime import datetime
from framework.core.recursion import (
    RecursionTracker,
    IterationRecord,
    ScoreComparison,
    format_comparison_report,
    format_progress_report,
)


class TestIterationRecord:
    """Tests for IterationRecord dataclass."""

    def test_creation(self):
        """Test IterationRecord can be created."""
        record = IterationRecord(
            iteration_number=1,
            timestamp=datetime.now(),
            overall_score=75.0,
            step_scores={"logos": 70, "pathos": 80},
        )
        assert record.iteration_number == 1
        assert record.overall_score == 75.0

    def test_to_dict(self):
        """Test IterationRecord converts to dictionary."""
        record = IterationRecord(
            iteration_number=1,
            timestamp=datetime.now(),
            overall_score=75.0,
            step_scores={"logos": 70, "pathos": 80},
            notes="First iteration",
        )
        d = record.to_dict()

        assert d["iteration_number"] == 1
        assert d["overall_score"] == 75.0
        assert d["notes"] == "First iteration"
        assert "timestamp" in d


class TestScoreComparison:
    """Tests for ScoreComparison dataclass."""

    def test_creation(self):
        """Test ScoreComparison can be created."""
        comparison = ScoreComparison(
            from_iteration=1,
            to_iteration=2,
            overall_delta=5.0,
            step_deltas={"logos": 3.0, "pathos": 7.0},
            improved_steps=["pathos"],
            declined_steps=[],
            unchanged_steps=["logos"],
        )
        assert comparison.from_iteration == 1
        assert comparison.to_iteration == 2
        assert comparison.overall_delta == 5.0

    def test_net_improvement_positive(self):
        """Test net_improvement is True for positive delta."""
        comparison = ScoreComparison(
            from_iteration=1,
            to_iteration=2,
            overall_delta=5.0,
            step_deltas={},
        )
        assert comparison.net_improvement is True

    def test_net_improvement_negative(self):
        """Test net_improvement is False for negative delta."""
        comparison = ScoreComparison(
            from_iteration=1,
            to_iteration=2,
            overall_delta=-5.0,
            step_deltas={},
        )
        assert comparison.net_improvement is False

    def test_summary_generation(self):
        """Test summary string is generated."""
        comparison = ScoreComparison(
            from_iteration=1,
            to_iteration=2,
            overall_delta=5.0,
            step_deltas={},
            improved_steps=["logos"],
            declined_steps=[],
        )
        summary = comparison.summary

        assert "1" in summary
        assert "2" in summary
        assert "improved" in summary.lower()


class TestRecursionTracker:
    """Tests for RecursionTracker class."""

    def test_initialization(self):
        """Test tracker initializes correctly."""
        tracker = RecursionTracker()
        assert tracker.iteration_count == 0
        assert tracker.latest is None

    def test_record_first_iteration(self):
        """Test recording first iteration."""
        tracker = RecursionTracker()

        eval_output = {
            "data": {
                "steps": [
                    {"step_name": "logos", "score": 60},
                    {"step_name": "pathos", "score": 70},
                ]
            },
            "summary": {"overall_score": 65},
        }

        record = tracker.record_iteration(eval_output)

        assert tracker.iteration_count == 1
        assert record.iteration_number == 1
        assert record.overall_score == 65

    def test_record_multiple_iterations(self):
        """Test recording multiple iterations."""
        tracker = RecursionTracker()

        # First iteration
        eval1 = {
            "data": {"steps": [{"step_name": "logos", "score": 60}]},
            "summary": {"overall_score": 60},
        }
        tracker.record_iteration(eval1)

        # Second iteration
        eval2 = {
            "data": {"steps": [{"step_name": "logos", "score": 70}]},
            "summary": {"overall_score": 70},
        }
        tracker.record_iteration(eval2)

        assert tracker.iteration_count == 2
        assert tracker.latest.overall_score == 70

    def test_compare_latest(self):
        """Test comparing two most recent iterations."""
        tracker = RecursionTracker()

        eval1 = {
            "data": {"steps": [{"step_name": "logos", "score": 60}]},
            "summary": {"overall_score": 60},
        }
        eval2 = {
            "data": {"steps": [{"step_name": "logos", "score": 70}]},
            "summary": {"overall_score": 70},
        }

        tracker.record_iteration(eval1)
        tracker.record_iteration(eval2)

        comparison = tracker.compare_latest()

        assert comparison is not None
        assert comparison.from_iteration == 1
        assert comparison.to_iteration == 2
        assert comparison.overall_delta == 10.0

    def test_compare_latest_single_iteration(self):
        """Test compare_latest returns None with single iteration."""
        tracker = RecursionTracker()

        eval1 = {
            "data": {"steps": []},
            "summary": {"overall_score": 60},
        }
        tracker.record_iteration(eval1)

        comparison = tracker.compare_latest()
        assert comparison is None

    def test_compare_specific_iterations(self):
        """Test comparing specific iterations."""
        tracker = RecursionTracker()

        for i, score in enumerate([50, 60, 70, 65]):
            eval_output = {
                "data": {"steps": []},
                "summary": {"overall_score": score},
            }
            tracker.record_iteration(eval_output)

        # Compare iteration 1 to 3
        comparison = tracker.compare_iterations(1, 3)

        assert comparison is not None
        assert comparison.from_iteration == 1
        assert comparison.to_iteration == 3
        assert comparison.overall_delta == 20.0  # 70 - 50

    def test_compare_to_first(self):
        """Test comparing latest to first iteration."""
        tracker = RecursionTracker()

        for score in [50, 60, 70]:
            eval_output = {
                "data": {"steps": []},
                "summary": {"overall_score": score},
            }
            tracker.record_iteration(eval_output)

        comparison = tracker.compare_to_first()

        assert comparison is not None
        assert comparison.from_iteration == 1
        assert comparison.to_iteration == 3
        assert comparison.overall_delta == 20.0

    def test_has_converged_false(self):
        """Test convergence detection when not converged."""
        tracker = RecursionTracker()

        eval1 = {"data": {"steps": []}, "summary": {"overall_score": 50}}
        eval2 = {"data": {"steps": []}, "summary": {"overall_score": 60}}

        tracker.record_iteration(eval1)
        tracker.record_iteration(eval2)

        assert tracker.has_converged(threshold=5.0) is False

    def test_has_converged_true(self):
        """Test convergence detection when converged."""
        tracker = RecursionTracker()

        eval1 = {"data": {"steps": []}, "summary": {"overall_score": 70}}
        eval2 = {"data": {"steps": []}, "summary": {"overall_score": 70.5}}

        tracker.record_iteration(eval1)
        tracker.record_iteration(eval2)

        assert tracker.has_converged(threshold=1.0) is True

    def test_progress_summary(self):
        """Test progress summary generation."""
        tracker = RecursionTracker()

        for score in [50, 60, 70, 65]:
            eval_output = {
                "data": {"steps": []},
                "summary": {"overall_score": score},
            }
            tracker.record_iteration(eval_output)

        summary = tracker.get_progress_summary()

        assert summary["iterations"] == 4
        assert summary["first_score"] == 50
        assert summary["latest_score"] == 65
        assert summary["total_change"] == 15  # 65 - 50
        assert summary["best_score"] == 70
        assert summary["best_iteration"] == 3

    def test_step_trends(self):
        """Test step trend tracking."""
        tracker = RecursionTracker()

        for logos, pathos in [(50, 60), (55, 65), (60, 70)]:
            eval_output = {
                "data": {
                    "steps": [
                        {"step_name": "logos", "score": logos},
                        {"step_name": "pathos", "score": pathos},
                    ]
                },
                "summary": {"overall_score": (logos + pathos) / 2},
            }
            tracker.record_iteration(eval_output)

        trends = tracker.get_step_trends()

        assert "logos" in trends
        assert "pathos" in trends
        assert trends["logos"] == [50, 55, 60]
        assert trends["pathos"] == [60, 65, 70]

    def test_to_dict(self):
        """Test tracker converts to dictionary."""
        tracker = RecursionTracker()

        eval1 = {"data": {"steps": []}, "summary": {"overall_score": 60}}
        tracker.record_iteration(eval1)

        d = tracker.to_dict()

        assert "iteration_count" in d
        assert "history" in d
        assert "progress_summary" in d


class TestFormatFunctions:
    """Tests for formatting functions."""

    def test_format_comparison_report(self):
        """Test comparison report formatting."""
        comparison = ScoreComparison(
            from_iteration=1,
            to_iteration=2,
            overall_delta=5.0,
            step_deltas={"logos": 3.0, "pathos": 7.0},
            improved_steps=["pathos"],
            declined_steps=[],
            unchanged_steps=["logos"],
        )

        report = format_comparison_report(comparison)

        assert "ITERATION COMPARISON" in report
        assert "1" in report
        assert "2" in report
        assert "IMPROVED" in report
        assert "pathos" in report

    def test_format_progress_report(self):
        """Test progress report formatting."""
        tracker = RecursionTracker()

        for score in [50, 60, 70]:
            eval_output = {
                "data": {"steps": []},
                "summary": {"overall_score": score},
            }
            tracker.record_iteration(eval_output)

        report = format_progress_report(tracker)

        assert "PROGRESS REPORT" in report
        assert "50" in report  # First score
        assert "70" in report  # Latest score
        assert "IMPROVING" in report

    def test_format_progress_report_empty(self):
        """Test progress report with no iterations."""
        tracker = RecursionTracker()
        report = format_progress_report(tracker)

        assert "No iterations" in report


class TestStepClassification:
    """Tests for step improvement classification."""

    def test_improved_steps_detected(self):
        """Test improved steps are correctly identified."""
        tracker = RecursionTracker()

        eval1 = {
            "data": {"steps": [{"step_name": "logos", "score": 50}]},
            "summary": {"overall_score": 50},
        }
        eval2 = {
            "data": {"steps": [{"step_name": "logos", "score": 70}]},
            "summary": {"overall_score": 70},
        }

        tracker.record_iteration(eval1)
        tracker.record_iteration(eval2)

        comparison = tracker.compare_latest()

        assert "logos" in comparison.improved_steps

    def test_declined_steps_detected(self):
        """Test declined steps are correctly identified."""
        tracker = RecursionTracker()

        eval1 = {
            "data": {"steps": [{"step_name": "logos", "score": 70}]},
            "summary": {"overall_score": 70},
        }
        eval2 = {
            "data": {"steps": [{"step_name": "logos", "score": 50}]},
            "summary": {"overall_score": 50},
        }

        tracker.record_iteration(eval1)
        tracker.record_iteration(eval2)

        comparison = tracker.compare_latest()

        assert "logos" in comparison.declined_steps

    def test_unchanged_steps_detected(self):
        """Test unchanged steps are correctly identified."""
        tracker = RecursionTracker()

        eval1 = {
            "data": {"steps": [{"step_name": "logos", "score": 70}]},
            "summary": {"overall_score": 70},
        }
        eval2 = {
            "data": {"steps": [{"step_name": "logos", "score": 71}]},  # Within threshold
            "summary": {"overall_score": 71},
        }

        tracker.record_iteration(eval1)
        tracker.record_iteration(eval2)

        comparison = tracker.compare_latest()

        assert "logos" in comparison.unchanged_steps
