"""
Tests for the scholarly export module.

These tests verify that LaTeX, TEI-XML, and CONLL exports
produce correctly formatted output.
"""

import pytest
from framework.output.scholarly import (
    LaTeXExporter,
    TEIXMLExporter,
    CONLLExporter,
    ExportMetadata,
    export_analysis,
    get_exporter,
)


@pytest.fixture
def sample_analysis_output():
    """Sample analysis output for testing exports."""
    return {
        "phases": {
            "Evaluation": {
                "logos": {
                    "step_number": 3,
                    "step_name": "logos",
                    "phase": "Evaluation",
                    "score": 65.0,
                    "findings": [
                        {
                            "type": "strength",
                            "category": "citations",
                            "description": "Text includes 3 citation references",
                        },
                        {
                            "type": "weakness",
                            "category": "evidence",
                            "description": "Low statistical evidence",
                        },
                    ],
                    "recommendations": [
                        "Add more statistical data",
                        "Include source citations",
                    ],
                    "explanation": {
                        "final_score": 65.0,
                        "evidence": [
                            {
                                "text": "40%",
                                "category": "statistics",
                                "pattern_group": "evidence",
                                "atom_id": "P001.S001",
                                "context": "increased by 40% over",
                            },
                            {
                                "text": "according to",
                                "category": "citations",
                                "pattern_group": "evidence",
                                "atom_id": "P001.S002",
                                "context": "according to Smith (2023)",
                            },
                        ],
                        "methodology": "Pattern matching test",
                    },
                },
                "pathos": {
                    "step_number": 4,
                    "step_name": "pathos",
                    "phase": "Evaluation",
                    "score": 55.0,
                    "findings": [],
                    "recommendations": [],
                },
            },
        },
        "summary": {
            "overall_score": 60.0,
            "phases_complete": 1,
        },
    }


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing exports."""
    return ExportMetadata(
        title="Test Analysis",
        author="Test Author",
        date="2025-01-20",
        version="1.0.0",
        source_file="test.pdf",
    )


class TestExportMetadata:
    """Tests for ExportMetadata dataclass."""

    def test_creation(self, sample_metadata):
        """Test metadata can be created."""
        assert sample_metadata.title == "Test Analysis"
        assert sample_metadata.author == "Test Author"

    def test_to_dict(self, sample_metadata):
        """Test metadata converts to dictionary."""
        d = sample_metadata.to_dict()
        assert d["title"] == "Test Analysis"
        assert d["source_file"] == "test.pdf"


class TestLaTeXExporter:
    """Tests for LaTeX export."""

    def test_export_produces_latex(self, sample_analysis_output, sample_metadata):
        """Test export produces valid LaTeX structure."""
        exporter = LaTeXExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        # Check LaTeX structure
        assert "\\documentclass{article}" in result
        assert "\\begin{document}" in result
        assert "\\end{document}" in result

    def test_export_includes_metadata(self, sample_analysis_output, sample_metadata):
        """Test export includes metadata."""
        exporter = LaTeXExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        assert "Test Analysis" in result
        assert "Test Author" in result

    def test_export_includes_scores(self, sample_analysis_output, sample_metadata):
        """Test export includes scores in table."""
        exporter = LaTeXExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        assert "65.0" in result  # logos score
        assert "60.0" in result  # overall score

    def test_export_includes_findings(self, sample_analysis_output, sample_metadata):
        """Test export includes findings."""
        exporter = LaTeXExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        assert "citation" in result.lower()
        assert "statistical" in result.lower()

    def test_escape_special_characters(self):
        """Test LaTeX special characters are escaped."""
        exporter = LaTeXExporter()
        escaped = exporter._escape("Test & 100% $special")

        assert "\\&" in escaped
        assert "\\%" in escaped
        assert "\\$" in escaped

    def test_methodology_note_included(self, sample_analysis_output, sample_metadata):
        """Test methodology note is included."""
        exporter = LaTeXExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        assert "Methodology" in result
        assert "heuristic" in result.lower()


class TestTEIXMLExporter:
    """Tests for TEI-XML export."""

    def test_export_produces_xml(self, sample_analysis_output, sample_metadata):
        """Test export produces valid XML structure."""
        exporter = TEIXMLExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        # Check XML structure
        assert '<?xml version=' in result
        assert "<TEI" in result
        assert "</TEI>" in result

    def test_export_includes_header(self, sample_analysis_output, sample_metadata):
        """Test export includes TEI header."""
        exporter = TEIXMLExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        assert "<teiHeader>" in result
        assert "<title>" in result
        assert "Test Analysis" in result

    def test_export_includes_body(self, sample_analysis_output, sample_metadata):
        """Test export includes text body."""
        exporter = TEIXMLExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        assert "<body>" in result
        assert "analysis-summary" in result

    def test_export_includes_standoff(self, sample_analysis_output, sample_metadata):
        """Test export includes stand-off annotations."""
        exporter = TEIXMLExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        assert "<standOff>" in result
        assert "<listAnnotation" in result

    def test_evidence_in_annotations(self, sample_analysis_output, sample_metadata):
        """Test evidence appears in annotations."""
        exporter = TEIXMLExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        assert "40%" in result
        assert "P001.S001" in result


class TestCONLLExporter:
    """Tests for CONLL export."""

    def test_export_produces_tsv(self, sample_analysis_output, sample_metadata):
        """Test export produces tab-separated format."""
        exporter = CONLLExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        # Check header comments
        assert "# LingFrame" in result
        assert "# Title:" in result

        # Check data lines contain tabs
        lines = [l for l in result.split("\n") if l and not l.startswith("#")]
        for line in lines:
            assert "\t" in line

    def test_export_includes_evidence(self, sample_analysis_output, sample_metadata):
        """Test export includes evidence tokens."""
        exporter = CONLLExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        assert "40%" in result
        assert "statistics" in result

    def test_export_includes_atom_ids(self, sample_analysis_output, sample_metadata):
        """Test export includes atom IDs."""
        exporter = CONLLExporter()
        result = exporter.export(sample_analysis_output, sample_metadata)

        assert "P001.S001" in result


class TestGetExporter:
    """Tests for exporter factory function."""

    def test_get_latex_exporter(self):
        """Test getting LaTeX exporter."""
        exporter = get_exporter("latex")
        assert isinstance(exporter, LaTeXExporter)

    def test_get_tei_exporter(self):
        """Test getting TEI exporter."""
        exporter = get_exporter("tei")
        assert isinstance(exporter, TEIXMLExporter)

        exporter2 = get_exporter("tei-xml")
        assert isinstance(exporter2, TEIXMLExporter)

    def test_get_conll_exporter(self):
        """Test getting CONLL exporter."""
        exporter = get_exporter("conll")
        assert isinstance(exporter, CONLLExporter)

    def test_unknown_format_raises(self):
        """Test unknown format raises ValueError."""
        with pytest.raises(ValueError, match="Unknown export format"):
            get_exporter("unknown")


class TestExportAnalysis:
    """Tests for export_analysis convenience function."""

    def test_export_to_latex(self, sample_analysis_output):
        """Test export_analysis with latex format."""
        result = export_analysis(
            sample_analysis_output,
            format_name="latex",
            title="Test Export",
        )

        assert "\\documentclass" in result
        assert "Test Export" in result

    def test_export_to_tei(self, sample_analysis_output):
        """Test export_analysis with TEI format."""
        result = export_analysis(
            sample_analysis_output,
            format_name="tei",
            title="Test Export",
        )

        assert "<TEI" in result
        assert "Test Export" in result

    def test_export_with_custom_metadata(self, sample_analysis_output):
        """Test export_analysis with custom metadata."""
        result = export_analysis(
            sample_analysis_output,
            format_name="latex",
            title="Custom Title",
            author="Custom Author",
            date="2025-12-31",
        )

        assert "Custom Title" in result
        assert "Custom Author" in result
