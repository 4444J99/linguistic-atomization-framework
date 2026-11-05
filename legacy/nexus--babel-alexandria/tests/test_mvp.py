from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from statistics import mean

from fastapi.testclient import TestClient
from sqlalchemy import select

from nexus_babel.config import Settings
from nexus_babel.main import create_app
from nexus_babel.models import Atom, Document, DocumentVariant, IngestJob
from nexus_babel.services.text_utils import ATOM_FILENAME_SCHEMA_VERSION


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * 0.95) - 1)
    return ordered[index]


def _ingest(client, paths, headers):
    response = client.post(
        "/api/v1/ingest/batch",
        headers=headers,
        json={
            "source_paths": [str(p) for p in paths],
            "modalities": [],
            "parse_options": {"atomize": True},
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    job = client.get(f"/api/v1/ingest/jobs/{payload['ingest_job_id']}", headers=headers)
    assert job.status_code == 200, job.text
    return payload, job.json()


def test_auth_required_on_protected_routes(client):
    assert client.get("/api/v1/documents").status_code == 401
    assert client.post("/api/v1/ingest/batch", json={"source_paths": [], "modalities": [], "parse_options": {}}).status_code == 401
    assert client.get("/api/v1/auth/whoami").status_code == 401


def test_role_and_raw_mode_enforcement(client, sample_corpus, auth_headers):
    ingest_as_viewer = client.post(
        "/api/v1/ingest/batch",
        headers=auth_headers["viewer"],
        json={"source_paths": [str(sample_corpus["text"])], "modalities": [], "parse_options": {"atomize": True}},
    )
    assert ingest_as_viewer.status_code == 403

    raw_as_operator = client.post(
        "/api/v1/governance/evaluate",
        headers=auth_headers["operator"],
        json={"candidate_output": "test", "mode": "RAW"},
    )
    assert raw_as_operator.status_code == 403

    raw_as_researcher = client.post(
        "/api/v1/governance/evaluate",
        headers=auth_headers["researcher"],
        json={"candidate_output": "test", "mode": "RAW"},
    )
    assert raw_as_researcher.status_code == 200

    whoami_operator = client.get("/api/v1/auth/whoami", headers=auth_headers["operator"])
    whoami_researcher = client.get("/api/v1/auth/whoami", headers=auth_headers["researcher"])
    assert whoami_operator.status_code == 200
    assert whoami_researcher.status_code == 200
    assert whoami_operator.json()["allowed_modes"] == ["PUBLIC"]
    assert whoami_researcher.json()["allowed_modes"] == ["PUBLIC", "RAW"]


def test_ingest_path_traversal_rejection(client, tmp_path, auth_headers):
    escaped = tmp_path.parent / "escape.md"
    escaped.write_text("outside root", encoding="utf-8")
    response = client.post(
        "/api/v1/ingest/batch",
        headers=auth_headers["operator"],
        json={"source_paths": [str(escaped)], "modalities": [], "parse_options": {"atomize": True}},
    )
    assert response.status_code == 400
    assert "escapes corpus_root" in response.text


def test_ingestion_completeness(client, sample_corpus, auth_headers):
    payload, job = _ingest(
        client,
        [sample_corpus["text"], sample_corpus["clean_yaml"], sample_corpus["pdf"]],
        auth_headers["operator"],
    )
    assert payload["documents_ingested"] == 3
    assert payload["atoms_created"] > 0
    assert len(payload["provenance_digest"]) == 64
    assert payload["ingest_scope"] == "partial"

    statuses = {item["status"] for item in job["files"]}
    assert statuses == {"ingested"}

    for entry in job["files"]:
        doc = client.get(f"/api/v1/documents/{entry['document_id']}", headers=auth_headers["viewer"])
        assert doc.status_code == 200
        detail = doc.json()
        assert detail["ingested"] is True
        assert "checksum" in detail["provenance"]
        assert detail["atom_count"] == detail["graph_projected_atom_count"]
        assert detail["graph_projection_status"] in {"complete", "pending"}


def test_seed_profile_cli_dry_run_and_invalid_profile(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "ingest_corpus.py"
    env = {
        **os.environ,
        "NEXUS_CORPUS_ROOT": str(tmp_path),
        "NEXUS_OBJECT_STORAGE_ROOT": str(tmp_path / "object_storage"),
        "NEXUS_DATABASE_URL": f"sqlite:///{tmp_path / 'cli_test.db'}",
    }

    ok = subprocess.run(
        [sys.executable, str(script_path), "--profile", "arc4n-seed", "--dry-run"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert ok.returncode == 0, ok.stderr
    payload = json.loads(ok.stdout)
    assert payload["status"] == "dry_run"
    assert payload["profile"] == "arc4n-seed"
    assert "atom_tracks" in payload["parse_options"]

    bad = subprocess.run(
        [sys.executable, str(script_path), "--profile", "missing-profile", "--dry-run"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert bad.returncode != 0
    assert "Unknown ingest profile" in bad.stderr


def test_ingest_atom_tracks_recorded_in_job_and_provenance(client, sample_corpus, auth_headers):
    response = client.post(
        "/api/v1/ingest/batch",
        headers=auth_headers["operator"],
        json={
            "source_paths": [str(sample_corpus["text"])],
            "modalities": [],
            "parse_options": {"atomize": True, "ingest_profile": "arc4n-seed"},
            "atom_tracks": ["literary", "glyphic_seed"],
        },
    )
    assert response.status_code == 200, response.text
    ingest_job_id = response.json()["ingest_job_id"]

    session = client.app.state.db.session()
    try:
        job = session.scalar(select(IngestJob).where(IngestJob.id == ingest_job_id))
        assert job is not None
        parse_options = (job.request_payload or {}).get("parse_options", {})
        assert parse_options.get("ingest_profile") == "arc4n-seed"
        assert parse_options.get("atom_tracks") == ["literary", "glyphic_seed"]
        assert parse_options.get("atom_levels")
    finally:
        session.close()

    job_payload = client.get(f"/api/v1/ingest/jobs/{ingest_job_id}", headers=auth_headers["viewer"]).json()
    doc_id = job_payload["files"][0]["document_id"]
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers["viewer"]).json()
    atomization = detail["provenance"]["atomization"]
    assert atomization["atom_tracks"] == ["literary", "glyphic_seed"]
    assert atomization["filename_schema_version"] == ATOM_FILENAME_SCHEMA_VERSION
    assert set(atomization["active_atom_levels"]) >= {"glyph-seed", "syllable", "word", "sentence", "paragraph"}


def test_atom_track_counts_differ_predictably(client, tmp_path: Path, auth_headers):
    literary_path = tmp_path / "literary.md"
    glyphic_path = tmp_path / "glyphic.md"
    content = "Alpha beta gamma. Delta epsilon zeta."
    literary_path.write_text(content, encoding="utf-8")
    glyphic_path.write_text(content, encoding="utf-8")

    r1 = client.post(
        "/api/v1/ingest/batch",
        headers=auth_headers["operator"],
        json={"source_paths": [str(literary_path)], "atom_tracks": ["literary"], "parse_options": {"atomize": True}},
    )
    r2 = client.post(
        "/api/v1/ingest/batch",
        headers=auth_headers["operator"],
        json={"source_paths": [str(glyphic_path)], "atom_tracks": ["glyphic_seed"], "parse_options": {"atomize": True}},
    )
    assert r1.status_code == 200, r1.text
    assert r2.status_code == 200, r2.text

    session = client.app.state.db.session()
    try:
        docs = session.scalars(select(Document).where(Document.path.in_([str(literary_path.resolve()), str(glyphic_path.resolve())]))).all()
        by_path = {d.path: d for d in docs}
        literary_doc = by_path[str(literary_path.resolve())]
        glyphic_doc = by_path[str(glyphic_path.resolve())]
        assert literary_doc.atom_count != glyphic_doc.atom_count

        literary_atoms = session.scalars(select(Atom).where(Atom.document_id == literary_doc.id)).all()
        glyphic_atoms = session.scalars(select(Atom).where(Atom.document_id == glyphic_doc.id)).all()
        assert {a.atom_level for a in literary_atoms} == {"word", "sentence", "paragraph"}
        assert {a.atom_level for a in glyphic_atoms} == {"glyph-seed", "syllable"}
    finally:
        session.close()


def test_deterministic_atom_filename_metadata_is_stable(client, sample_corpus, auth_headers):
    first = client.post(
        "/api/v1/ingest/batch",
        headers=auth_headers["operator"],
        json={"source_paths": [str(sample_corpus["text"])], "parse_options": {"atomize": True, "force": True}},
    )
    second = client.post(
        "/api/v1/ingest/batch",
        headers=auth_headers["operator"],
        json={"source_paths": [str(sample_corpus["text"])], "parse_options": {"atomize": True, "force": True}},
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    session = client.app.state.db.session()
    try:
        doc = session.scalar(select(Document).where(Document.path == str(sample_corpus["text"].resolve())))
        assert doc is not None
        atoms = session.scalars(select(Atom).where(Atom.document_id == doc.id)).all()
        filenames = [
            (
                a.atom_level,
                a.ordinal,
                (a.atom_metadata or {}).get("filename"),
                (a.atom_metadata or {}).get("filename_schema_version"),
            )
            for a in atoms
        ]
        assert filenames
        assert all(name for _, _, name, _ in filenames)
        assert all(version == ATOM_FILENAME_SCHEMA_VERSION for _, _, _, version in filenames)

        # Re-read after a third force ingest and ensure filenames remain identical.
        third = client.post(
            "/api/v1/ingest/batch",
            headers=auth_headers["operator"],
            json={"source_paths": [str(sample_corpus["text"])], "parse_options": {"atomize": True, "force": True}},
        )
        assert third.status_code == 200, third.text
        atoms_again = session.scalars(select(Atom).where(Atom.document_id == doc.id)).all()
        filenames_again = [
            (
                a.atom_level,
                a.ordinal,
                (a.atom_metadata or {}).get("filename"),
                (a.atom_metadata or {}).get("filename_schema_version"),
            )
            for a in atoms_again
        ]
        assert filenames_again == filenames
    finally:
        session.close()


def test_conflict_hygiene_and_analyze_409(client, sample_corpus, auth_headers):
    _, job = _ingest(client, [sample_corpus["conflict_yaml"]], auth_headers["operator"])
    assert job["files"][0]["status"] == "conflict"

    listing = client.get("/api/v1/documents", headers=auth_headers["viewer"]).json()["documents"]
    conflicted = [d for d in listing if d["path"].endswith("seed.yaml")]
    assert conflicted
    doc_detail = client.get(f"/api/v1/documents/{conflicted[0]['id']}", headers=auth_headers["viewer"]).json()
    assert doc_detail["conflict_flag"] is True
    assert doc_detail["ingested"] is False
    assert doc_detail["conflict_reason"] == "Conflict markers detected"

    blocked = client.post(
        "/api/v1/analyze",
        headers=auth_headers["operator"],
        json={"document_id": conflicted[0]["id"], "mode": "PUBLIC"},
    )
    assert blocked.status_code == 409


def test_hypergraph_integrity(client, sample_corpus, auth_headers):
    _, job = _ingest(client, [sample_corpus["text"]], auth_headers["operator"])
    doc_id = job["files"][0]["document_id"]

    integrity = client.get(f"/api/v1/hypergraph/documents/{doc_id}/integrity", headers=auth_headers["viewer"])
    assert integrity.status_code == 200
    payload = integrity.json()
    assert payload["document_nodes"] == 1
    assert payload["expected_atom_nodes"] > 0
    assert payload["atom_nodes"] == payload["expected_atom_nodes"]
    assert payload["contains_edges"] == payload["atom_nodes"]
    assert payload["consistent"] is True


def test_canonicalization_stability_under_partial_reingestion(client, sample_corpus, auth_headers):
    _ingest(client, [sample_corpus["text"], sample_corpus["pdf"]], auth_headers["operator"])

    session = client.app.state.db.session()
    try:
        docs = session.scalars(select(Document)).all()
        by_path = {d.path: d for d in docs}
        text_doc = by_path[str(sample_corpus["text"].resolve())]
        pdf_doc = by_path[str(sample_corpus["pdf"].resolve())]

        variants_before = session.scalars(
            select(DocumentVariant).where(DocumentVariant.variant_type == "sibling_representation")
        ).all()
        before_edges = {(v.document_id, v.related_document_id, v.variant_group) for v in variants_before}
    finally:
        session.close()

    _ingest(client, [sample_corpus["text"]], auth_headers["operator"])

    session = client.app.state.db.session()
    try:
        variants_after = session.scalars(
            select(DocumentVariant).where(DocumentVariant.variant_type == "sibling_representation")
        ).all()
        after_edges = {(v.document_id, v.related_document_id, v.variant_group) for v in variants_after}
    finally:
        session.close()

    expected_pair = {
        (text_doc.id, pdf_doc.id, f"sibling::{sample_corpus['text'].stem}"),
        (pdf_doc.id, text_doc.id, f"sibling::{sample_corpus['text'].stem}"),
    }
    assert expected_pair.issubset(before_edges)
    assert expected_pair.issubset(after_edges)
    assert before_edges == after_edges


def test_dual_mode_regression(client, auth_headers):
    text = "This output says we should kill all nuance."

    public_decision = client.post(
        "/api/v1/governance/evaluate",
        headers=auth_headers["operator"],
        json={"candidate_output": text, "mode": "PUBLIC"},
    )
    raw_decision = client.post(
        "/api/v1/governance/evaluate",
        headers=auth_headers["researcher"],
        json={"candidate_output": text, "mode": "RAW"},
    )

    assert public_decision.status_code == 200
    assert raw_decision.status_code == 200

    public_payload = public_decision.json()
    raw_payload = raw_decision.json()
    assert public_payload["allow"] is False
    assert raw_payload["allow"] is True
    assert "kill" in public_payload["policy_hits"]
    assert "kill" in raw_payload["policy_hits"]


def test_branch_determinism(client, sample_corpus, auth_headers):
    _, job = _ingest(client, [sample_corpus["text"]], auth_headers["operator"])
    doc_id = job["files"][0]["document_id"]

    req = {"root_document_id": doc_id, "event_type": "natural_drift", "event_payload": {"seed": 42}, "mode": "RAW"}
    b1 = client.post("/api/v1/evolve/branch", headers=auth_headers["researcher"], json=req)
    b2 = client.post("/api/v1/evolve/branch", headers=auth_headers["researcher"], json=req)

    assert b1.status_code == 200
    assert b2.status_code == 200

    t1 = client.get(f"/api/v1/branches/{b1.json()['new_branch_id']}/timeline", headers=auth_headers["viewer"]).json()
    t2 = client.get(f"/api/v1/branches/{b2.json()['new_branch_id']}/timeline", headers=auth_headers["viewer"]).json()
    assert t1["replay_snapshot"]["text_hash"] == t2["replay_snapshot"]["text_hash"]


def test_multimodal_linkage(client, sample_corpus, auth_headers):
    _, job = _ingest(client, [sample_corpus["text"], sample_corpus["image"], sample_corpus["audio"]], auth_headers["operator"])

    entries = {item["path"]: item for item in job["files"]}
    text_doc = client.get(f"/api/v1/documents/{entries[str(sample_corpus['text'])]['document_id']}", headers=auth_headers["viewer"]).json()
    image_doc = client.get(f"/api/v1/documents/{entries[str(sample_corpus['image'])]['document_id']}", headers=auth_headers["viewer"]).json()
    audio_doc = client.get(f"/api/v1/documents/{entries[str(sample_corpus['audio'])]['document_id']}", headers=auth_headers["viewer"]).json()

    assert "segments" in text_doc["provenance"]
    assert "segments" in image_doc["provenance"]
    assert "segments" in audio_doc["provenance"]
    assert audio_doc["provenance"]["segments"].get("duration_seconds", 0) > 0

    analysis = client.post(
        "/api/v1/analyze",
        headers=auth_headers["operator"],
        json={"document_id": text_doc["id"], "mode": "PUBLIC"},
    )
    assert analysis.status_code == 200
    assert "document_node_id" in analysis.json()["hypergraph_ids"]


def test_rhetorical_output(client, auth_headers):
    response = client.post(
        "/api/v1/rhetorical_analysis",
        headers=auth_headers["operator"],
        json={"text": "According to experts, therefore this proof is valid. Everyone knows this creates fear and hope."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"ethos_score", "pathos_score", "logos_score", "strategies", "fallacies", "explainability"}
    assert isinstance(payload["strategies"], list)


def test_api_contract_validation(client, auth_headers):
    bad_analyze = client.post("/api/v1/analyze", headers=auth_headers["operator"], json={"mode": "PUBLIC"})
    assert bad_analyze.status_code == 400

    bad_branch = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["operator"],
        json={"event_type": "phase_shift", "event_payload": {"phase": "compression"}},
    )
    assert bad_branch.status_code == 400


def test_ui_e2e_flow(client, sample_corpus, auth_headers):
    for page in ["corpus", "hypergraph", "timeline", "governance"]:
        res = client.get(f"/app/{page}")
        assert res.status_code == 200

    _, job = _ingest(client, [sample_corpus["text"]], auth_headers["operator"])
    doc_id = job["files"][0]["document_id"]

    analyze = client.post("/api/v1/analyze", headers=auth_headers["operator"], json={"document_id": doc_id, "mode": "PUBLIC"})
    assert analyze.status_code == 200

    evolve = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["researcher"],
        json={"root_document_id": doc_id, "event_type": "phase_shift", "event_payload": {"phase": "compression", "seed": 7}, "mode": "RAW"},
    )
    assert evolve.status_code == 200

    branch_id = evolve.json()["new_branch_id"]
    timeline = client.get(f"/api/v1/branches/{branch_id}/timeline", headers=auth_headers["viewer"])
    assert timeline.status_code == 200

    policy = client.post(
        "/api/v1/governance/evaluate",
        headers=auth_headers["operator"],
        json={"candidate_output": "clean output", "mode": "PUBLIC"},
    )
    assert policy.status_code == 200


def test_integrity_persists_across_restart(tmp_path, sample_corpus):
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'restart.db'}",
        corpus_root=tmp_path,
        object_storage_root=tmp_path / "object_storage_restart",
        neo4j_uri=None,
        neo4j_username=None,
        neo4j_password=None,
    )
    operator_headers = {"X-Nexus-API-Key": settings.bootstrap_operator_key}
    viewer_headers = {"X-Nexus-API-Key": settings.bootstrap_viewer_key}

    app_one = create_app(settings)
    with TestClient(app_one) as client_one:
        _, job = _ingest(client_one, [sample_corpus["text"]], operator_headers)
        doc_id = job["files"][0]["document_id"]
        doc_detail = client_one.get(f"/api/v1/documents/{doc_id}", headers=viewer_headers).json()
        expected = doc_detail["graph_projected_atom_count"]

    app_two = create_app(settings)
    with TestClient(app_two) as client_two:
        integrity = client_two.get(f"/api/v1/hypergraph/documents/{doc_id}/integrity", headers=viewer_headers)
        assert integrity.status_code == 200
        payload = integrity.json()
        assert payload["atom_nodes"] == expected
        assert payload["contains_edges"] == expected
        assert payload["consistent"] is True


def test_load_baseline(client, sample_corpus, auth_headers):
    _, job = _ingest(client, [sample_corpus["text"]], auth_headers["operator"])
    doc_id = job["files"][0]["document_id"]

    durations = []
    for _ in range(20):
        start = time.perf_counter()
        res = client.post("/api/v1/analyze", headers=auth_headers["operator"], json={"document_id": doc_id, "mode": "PUBLIC"})
        assert res.status_code == 200
        durations.append(time.perf_counter() - start)

    assert mean(durations) < 1.5
    assert _p95(durations) < 2.0
