from __future__ import annotations

import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from nexus_babel.config import Settings
from nexus_babel.main import create_app


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        corpus_root=tmp_path,
        object_storage_root=tmp_path / "object_storage",
        neo4j_uri=None,
        neo4j_username=None,
        neo4j_password=None,
    )


@pytest.fixture
def auth_headers(test_settings: Settings) -> dict[str, dict[str, str]]:
    return {
        "viewer": {"X-Nexus-API-Key": test_settings.bootstrap_viewer_key},
        "operator": {"X-Nexus-API-Key": test_settings.bootstrap_operator_key},
        "researcher": {"X-Nexus-API-Key": test_settings.bootstrap_researcher_key},
        "admin": {"X-Nexus-API-Key": test_settings.bootstrap_admin_key},
    }


@pytest.fixture
def client(test_settings: Settings):
    settings = test_settings
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_corpus(tmp_path: Path) -> dict[str, Path]:
    text_path = tmp_path / "sample.md"
    text_path.write_text(
        "According to experts, therefore we should act. Everyone knows this! Love and hope drive us.",
        encoding="utf-8",
    )

    clean_yaml = tmp_path / "clean.yaml"
    clean_yaml.write_text("schema_version: '1.0'\nstatus: active\n", encoding="utf-8")

    conflict_yaml = tmp_path / "seed.yaml"
    conflict_yaml.write_text(
        "<<<<<<< HEAD\nvalue: A\n=======\nvalue: B\n>>>>>>> branch\n",
        encoding="utf-8",
    )

    pdf_path = tmp_path / "sample.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with pdf_path.open("wb") as f:
        writer.write(f)

    image_path = tmp_path / "sample.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    audio_path = tmp_path / "sample.wav"
    with wave.open(str(audio_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)

    return {
        "text": text_path,
        "clean_yaml": clean_yaml,
        "conflict_yaml": conflict_yaml,
        "pdf": pdf_path,
        "image": image_path,
        "audio": audio_path,
    }
