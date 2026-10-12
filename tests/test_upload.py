"""
Tests for app/components/upload.py PDF extraction and cleanup.
"""

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.components.upload import extract_text_from_upload


class DummyUploadedFile:
    def __init__(self, name: str, content: bytes):
        self.name = name
        self._buffer = io.BytesIO(content)

    def read(self) -> bytes:
        return self._buffer.getvalue()


def test_pdf_upload_success():
    uploaded_file = DummyUploadedFile("sample.pdf", b"%PDF-1.4 dummy pdf bytes")
    created_temp_path = None

    def mock_extract_text(tmp_path):
        nonlocal created_temp_path
        created_temp_path = Path(tmp_path)
        assert created_temp_path.exists()
        return "Extracted PDF content"

    with patch("framework.loaders.PDFLoader") as MockPDFLoader:
        instance = MockPDFLoader.return_value
        instance.extract_text.side_effect = mock_extract_text

        result = extract_text_from_upload(uploaded_file)

        assert result == "Extracted PDF content"
        assert created_temp_path is not None
        assert not created_temp_path.exists()


def test_pdf_upload_exception_cleans_up_temp_file():
    uploaded_file = DummyUploadedFile("failing.pdf", b"%PDF-1.4 dummy pdf bytes")
    created_temp_path = None

    def mock_extract_text_fail(tmp_path):
        nonlocal created_temp_path
        created_temp_path = Path(tmp_path)
        assert created_temp_path.exists()
        raise RuntimeError("PDF parsing error")

    with patch("framework.loaders.PDFLoader") as MockPDFLoader:
        instance = MockPDFLoader.return_value
        instance.extract_text.side_effect = mock_extract_text_fail

        with pytest.raises(RuntimeError, match="PDF parsing error"):
            extract_text_from_upload(uploaded_file)

        assert created_temp_path is not None
        assert not created_temp_path.exists()


def test_multiple_sequential_pdf_failures_leave_no_artifacts():
    uploaded_files = [
        DummyUploadedFile(f"fail_{i}.pdf", f"%PDF-1.4 dummy {i}".encode())
        for i in range(5)
    ]
    created_paths = []

    def mock_extract_text_fail(tmp_path):
        p = Path(tmp_path)
        created_paths.append(p)
        assert p.exists()
        raise ValueError(f"Corrupt PDF {p.name}")

    with patch("framework.loaders.PDFLoader") as MockPDFLoader:
        instance = MockPDFLoader.return_value
        instance.extract_text.side_effect = mock_extract_text_fail

        for uploaded_file in uploaded_files:
            with pytest.raises(ValueError):
                extract_text_from_upload(uploaded_file)

    assert len(created_paths) == 5
    for p in created_paths:
        assert not p.exists()


def test_pdf_upload_tolerates_already_deleted_temp_file():
    uploaded_file = DummyUploadedFile("already_deleted.pdf", b"%PDF-1.4 dummy")

    def mock_extract_text_and_delete(tmp_path):
        p = Path(tmp_path)
        p.unlink()
        return "Extracted text after manual delete"

    with patch("framework.loaders.PDFLoader") as MockPDFLoader:
        instance = MockPDFLoader.return_value
        instance.extract_text.side_effect = mock_extract_text_and_delete

        result = extract_text_from_upload(uploaded_file)
        assert result == "Extracted text after manual delete"


def test_txt_and_md_upload_unchanged():
    txt_file = DummyUploadedFile("notes.txt", b"Hello world from txt")
    md_file = DummyUploadedFile("readme.md", b"# Hello world from md")

    assert extract_text_from_upload(txt_file) == "Hello world from txt"
    assert extract_text_from_upload(md_file) == "# Hello world from md"


def test_docx_upload_unchanged():
    docx_file = DummyUploadedFile("doc.docx", b"dummy docx bytes")

    mock_docx_module = MagicMock()
    mock_doc = MagicMock()
    p1 = MagicMock()
    p1.text = "Paragraph 1"
    p2 = MagicMock()
    p2.text = "Paragraph 2"
    mock_doc.paragraphs = [p1, p2]
    mock_docx_module.Document.return_value = mock_doc

    with patch.dict(sys.modules, {"docx": mock_docx_module}):
        result = extract_text_from_upload(docx_file)
        assert result == "Paragraph 1\n\nParagraph 2"
