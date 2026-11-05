from __future__ import annotations

import hashlib

from nexus_babel.models import IngestJob
from nexus_babel.services.ingestion_batch_pipeline import build_normalized_parse_options, finalize_job, new_batch_accumulator


def test_build_normalized_parse_options_preserves_extra_fields_and_overrides_atomization():
    normalized = build_normalized_parse_options(
        parse_options={"custom": "value", "force": False, "atomize": False},
        atom_tracks=["literary", "glyphic_seed"],
        atom_levels=["word", "glyph-seed"],
        atomize_enabled=True,
        force_reingest=True,
    )

    assert normalized["custom"] == "value"
    assert normalized["atom_tracks"] == ["literary", "glyphic_seed"]
    assert normalized["atom_levels"] == ["word", "glyph-seed"]
    assert normalized["atomize"] is True
    assert normalized["force"] is True


def test_finalize_job_sets_completed_status_and_deterministic_digest():
    job = IngestJob(status="running", request_payload={})
    acc = new_batch_accumulator()
    acc.files.append({"path": "a.txt", "status": "ingested", "error": None, "document_id": "doc-1"})
    acc.documents_ingested = 1
    acc.atoms_created = 3
    acc.documents_unchanged = 2
    acc.checksums = ["bbb", "aaa"]
    acc.warnings = ["warn-1"]

    result = finalize_job(job, accumulator=acc, ingest_scope="partial")

    expected_digest = hashlib.sha256("\n".join(["aaa", "bbb"]).encode("utf-8")).hexdigest()
    assert job.status == "completed"
    assert result["job"] is job
    assert result["provenance_digest"] == expected_digest
    assert result["warnings"] == ["warn-1"]
    assert result["errors"] == []
    assert job.result_summary["files"] == acc.files


def test_finalize_job_sets_completed_with_errors_when_accumulator_has_errors():
    job = IngestJob(status="running", request_payload={})
    acc = new_batch_accumulator()
    acc.errors = ["boom"]

    result = finalize_job(job, accumulator=acc, ingest_scope="full")

    assert job.status == "completed_with_errors"
    assert result["errors"] == ["boom"]
    assert result["ingest_scope"] == "full"
    assert result["provenance_digest"] == ""
