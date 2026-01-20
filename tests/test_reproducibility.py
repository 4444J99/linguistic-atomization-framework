"""
Tests for the reproducibility module.

These tests verify that analysis runs can be tracked and verified
for scholarly reproducibility.
"""

import pytest
import json
from pathlib import Path
from framework.core.reproducibility import (
    InputFingerprint,
    EnvironmentInfo,
    AnalysisConfig,
    ReproducibilityRecord,
    ReproducibilityTracker,
    create_reproducibility_record,
    format_reproducibility_citation,
    LINGFRAME_VERSION,
)


class TestInputFingerprint:
    """Tests for InputFingerprint."""

    def test_from_text(self):
        """Test creating fingerprint from text."""
        text = "Hello, world!"
        fp = InputFingerprint.from_text(text)

        assert fp.checksum is not None
        assert len(fp.checksum) == 64  # SHA-256 hex length
        assert fp.char_count == len(text)
        assert fp.byte_size == len(text.encode("utf-8"))

    def test_same_text_same_checksum(self):
        """Test that same text produces same checksum."""
        text = "Test content for reproducibility."
        fp1 = InputFingerprint.from_text(text)
        fp2 = InputFingerprint.from_text(text)

        assert fp1.checksum == fp2.checksum

    def test_different_text_different_checksum(self):
        """Test that different text produces different checksum."""
        fp1 = InputFingerprint.from_text("Text A")
        fp2 = InputFingerprint.from_text("Text B")

        assert fp1.checksum != fp2.checksum

    def test_to_dict(self):
        """Test conversion to dictionary."""
        fp = InputFingerprint.from_text("Test", source_path="/tmp/test.txt")
        d = fp.to_dict()

        assert "checksum" in d
        assert "byte_size" in d
        assert "source_path" in d
        assert d["source_path"] == "/tmp/test.txt"


class TestEnvironmentInfo:
    """Tests for EnvironmentInfo."""

    def test_capture(self):
        """Test capturing environment info."""
        env = EnvironmentInfo.capture()

        assert env.python_version is not None
        assert env.platform is not None
        assert env.lingframe_version == LINGFRAME_VERSION

    def test_to_dict(self):
        """Test conversion to dictionary."""
        env = EnvironmentInfo.capture()
        d = env.to_dict()

        assert "python_version" in d
        assert "platform" in d
        assert "lingframe_version" in d
        assert "dependencies" in d


class TestAnalysisConfig:
    """Tests for AnalysisConfig."""

    def test_creation(self):
        """Test creating analysis config."""
        config = AnalysisConfig(
            modules=["semantic", "evaluation"],
            domain="military",
            schema_name="default",
            options={"verbose": True},
        )

        assert len(config.modules) == 2
        assert config.domain == "military"

    def test_to_json(self):
        """Test JSON serialization."""
        config = AnalysisConfig(
            modules=["evaluation"],
            domain=None,
            schema_name="default",
        )
        json_str = config.to_json()
        data = json.loads(json_str)

        assert data["modules"] == ["evaluation"]
        assert data["domain"] is None

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "modules": ["semantic"],
            "domain": "literary",
            "schema_name": "custom",
            "options": {"key": "value"},
        }
        config = AnalysisConfig.from_dict(data)

        assert config.modules == ["semantic"]
        assert config.domain == "literary"
        assert config.options["key"] == "value"


class TestReproducibilityRecord:
    """Tests for ReproducibilityRecord."""

    def test_creation(self):
        """Test creating a record."""
        record = ReproducibilityRecord(
            run_id="test_001",
            timestamp="2025-01-20T12:00:00",
            config=AnalysisConfig(["eval"], None, "default"),
            input_fingerprint=InputFingerprint.from_text("Test"),
            environment=EnvironmentInfo.capture(),
        )

        assert record.run_id == "test_001"
        assert record.config.modules == ["eval"]

    def test_to_json_and_back(self):
        """Test JSON round-trip."""
        original = ReproducibilityRecord(
            run_id="test_002",
            timestamp="2025-01-20T12:00:00",
            config=AnalysisConfig(["semantic"], "military", "default"),
            input_fingerprint=InputFingerprint.from_text("Sample text"),
            environment=EnvironmentInfo.capture(),
            notes="Test run",
        )

        json_str = original.to_json()
        restored = ReproducibilityRecord.from_json(json_str)

        assert restored.run_id == original.run_id
        assert restored.config.modules == original.config.modules
        assert restored.input_fingerprint.checksum == original.input_fingerprint.checksum

    def test_verify_input_success(self):
        """Test input verification with matching text."""
        text = "This is the original text."
        record = ReproducibilityRecord(
            run_id="test",
            timestamp="2025-01-20",
            config=AnalysisConfig([], None, "default"),
            input_fingerprint=InputFingerprint.from_text(text),
            environment=EnvironmentInfo.capture(),
        )

        assert record.verify_input(text) is True

    def test_verify_input_failure(self):
        """Test input verification with different text."""
        record = ReproducibilityRecord(
            run_id="test",
            timestamp="2025-01-20",
            config=AnalysisConfig([], None, "default"),
            input_fingerprint=InputFingerprint.from_text("Original text"),
            environment=EnvironmentInfo.capture(),
        )

        assert record.verify_input("Modified text") is False


class TestReproducibilityTracker:
    """Tests for ReproducibilityTracker."""

    def test_start_run(self):
        """Test starting a run."""
        tracker = ReproducibilityTracker()
        config = AnalysisConfig(["evaluation"], None, "default")

        record = tracker.start_run(config, "Test input text")

        assert record.run_id is not None
        assert record.timestamp is not None
        assert record.input_fingerprint.checksum is not None

    def test_finish_run(self):
        """Test finishing a run."""
        tracker = ReproducibilityTracker()
        config = AnalysisConfig(["evaluation"], None, "default")

        record = tracker.start_run(config, "Test input")
        output = {"summary": {"overall_score": 75}}

        record = tracker.finish_run(record, output, notes="Test complete")

        assert record.output_checksum is not None
        assert record.notes == "Test complete"

    def test_save_and_load(self, tmp_path):
        """Test saving and loading records."""
        tracker = ReproducibilityTracker()
        config = AnalysisConfig(["evaluation"], None, "default")

        record = tracker.start_run(config, "Test content")
        record = tracker.finish_run(record, {"score": 50})

        # Save
        file_path = tmp_path / "record.json"
        tracker.save(record, file_path)
        assert file_path.exists()

        # Load
        loaded = tracker.load(file_path)
        assert loaded.run_id == record.run_id
        assert loaded.output_checksum == record.output_checksum


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_reproducibility_record(self):
        """Test create_reproducibility_record function."""
        config = {
            "modules": ["semantic", "evaluation"],
            "domain": "literary",
            "schema_name": "default",
        }
        output = {"summary": {"score": 80}}

        record = create_reproducibility_record(
            config,
            "Analysis input text",
            output=output,
            source_path="essay.txt",
        )

        assert record.config.modules == ["semantic", "evaluation"]
        assert record.input_fingerprint.source_path == "essay.txt"
        assert record.output_checksum is not None

    def test_format_reproducibility_citation(self):
        """Test citation formatting."""
        record = ReproducibilityRecord(
            run_id="run_2025-01-20",
            timestamp="2025-01-20T15:30:00",
            config=AnalysisConfig(["evaluation"], "military", "default"),
            input_fingerprint=InputFingerprint.from_text("Sample text"),
            environment=EnvironmentInfo.capture(),
            output_checksum="abc123",
        )

        citation = format_reproducibility_citation(record)

        assert "run_2025-01-20" in citation
        assert "LingFrame Version" in citation
        assert "SHA-256" in citation
        assert "evaluation" in citation


class TestOutputVerification:
    """Tests for output verification."""

    def test_same_output_same_checksum(self):
        """Test that same output produces same checksum."""
        tracker = ReproducibilityTracker()
        config = AnalysisConfig(["eval"], None, "default")

        output = {"summary": {"score": 75}, "details": [1, 2, 3]}

        record1 = tracker.start_run(config, "text")
        record1 = tracker.finish_run(record1, output)

        record2 = tracker.start_run(config, "text")
        record2 = tracker.finish_run(record2, output)

        assert record1.output_checksum == record2.output_checksum

    def test_different_output_different_checksum(self):
        """Test that different output produces different checksum."""
        tracker = ReproducibilityTracker()
        config = AnalysisConfig(["eval"], None, "default")

        record1 = tracker.start_run(config, "text")
        record1 = tracker.finish_run(record1, {"score": 75})

        record2 = tracker.start_run(config, "text")
        record2 = tracker.finish_run(record2, {"score": 80})

        assert record1.output_checksum != record2.output_checksum

    def test_verify_output(self):
        """Test output verification."""
        tracker = ReproducibilityTracker()
        config = AnalysisConfig(["eval"], None, "default")
        output = {"score": 75}

        record = tracker.start_run(config, "text")
        record = tracker.finish_run(record, output)

        assert record.verify_output(output) is True
        assert record.verify_output({"score": 80}) is False
