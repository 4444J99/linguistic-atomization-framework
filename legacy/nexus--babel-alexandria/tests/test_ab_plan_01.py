from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType

from sqlalchemy import select

from nexus_babel.models import Atom, IngestJob, RemixArtifact
from nexus_babel.services.seed_corpus import load_ingest_profile
from nexus_babel.services.text_utils import ATOM_FILENAME_SCHEMA_VERSION


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_script_module(module_name: str, relative_path: str) -> ModuleType:
    script_path = _repo_root() / relative_path
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _ingest_one(client, auth_headers, source_path: Path, *, atom_tracks: list[str] | None = None, parse_options: dict | None = None) -> tuple[str, str]:
    payload = {
        "source_paths": [str(source_path)],
        "modalities": [],
        "parse_options": parse_options or {"atomize": True},
    }
    if atom_tracks is not None:
        payload["atom_tracks"] = atom_tracks
    response = client.post("/api/v1/ingest/batch", headers=auth_headers["operator"], json=payload)
    assert response.status_code == 200, response.text
    ingest_job_id = response.json()["ingest_job_id"]
    job = client.get(f"/api/v1/ingest/jobs/{ingest_job_id}", headers=auth_headers["viewer"])
    assert job.status_code == 200, job.text
    return ingest_job_id, job.json()["files"][0]["document_id"]


# AB01-T001
def test_ab01_t001_seed_profile_cli_and_metadata_contract(client, auth_headers, sample_corpus, tmp_path: Path):
    profile = load_ingest_profile("arc4n-seed", client.app.state.settings.seed_registry_path)
    assert profile["name"] == "arc4n-seed"
    assert len(profile["seed_titles"]) == 5

    repo_root = _repo_root()
    script = repo_root / "scripts" / "ingest_corpus.py"
    env = {
        **os.environ,
        "NEXUS_CORPUS_ROOT": str(tmp_path),
        "NEXUS_OBJECT_STORAGE_ROOT": str(tmp_path / "obj"),
        "NEXUS_DATABASE_URL": f"sqlite:///{tmp_path / 'ab01_t001.db'}",
    }
    dry_run = subprocess.run(
        [sys.executable, str(script), "--profile", "arc4n-seed", "--dry-run"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert dry_run.returncode == 0, dry_run.stderr
    dry_payload = json.loads(dry_run.stdout)
    assert dry_payload["profile"] == "arc4n-seed"

    ingest_job_id, _ = _ingest_one(
        client,
        auth_headers,
        sample_corpus["text"],
        parse_options={"atomize": True, "ingest_profile": "arc4n-seed"},
    )
    session = client.app.state.db.session()
    try:
        job = session.scalar(select(IngestJob).where(IngestJob.id == ingest_job_id))
        assert job is not None
        assert (job.request_payload or {}).get("parse_options", {}).get("ingest_profile") == "arc4n-seed"
    finally:
        session.close()


# AB01-T002
def test_ab01_t002_dual_atom_tracks_contract(client, auth_headers, sample_corpus):
    _, doc_id = _ingest_one(client, auth_headers, sample_corpus["text"], atom_tracks=["literary", "glyphic_seed"])
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers["viewer"])
    assert detail.status_code == 200, detail.text
    atomization = detail.json()["provenance"]["atomization"]
    assert atomization["atom_tracks"] == ["literary", "glyphic_seed"]
    assert set(atomization["active_atom_levels"]) == {"glyph-seed", "syllable", "word", "sentence", "paragraph"}


# AB01-T003
def test_ab01_t003_deterministic_atom_filename_contract(client, auth_headers, sample_corpus):
    _, doc_id = _ingest_one(client, auth_headers, sample_corpus["text"], parse_options={"atomize": True, "force": True})
    _ingest_one(client, auth_headers, sample_corpus["text"], parse_options={"atomize": True, "force": True})

    session = client.app.state.db.session()
    try:
        atoms = session.scalars(select(Atom).where(Atom.document_id == doc_id).order_by(Atom.atom_level, Atom.ordinal)).all()
        filenames = [(a.atom_level, a.ordinal, (a.atom_metadata or {}).get("filename")) for a in atoms]
        assert filenames
        assert all(name for _, _, name in filenames)
        assert all((a.atom_metadata or {}).get("filename_schema_version") == ATOM_FILENAME_SCHEMA_VERSION for a in atoms)
    finally:
        session.close()


# AB01-T004
def test_ab01_t004_export_pipeline_contract(client, auth_headers, sample_corpus, tmp_path: Path):
    _ingest_one(client, auth_headers, sample_corpus["text"], atom_tracks=["literary", "glyphic_seed"])
    exporter = _load_script_module("export_atom_library", "scripts/export_atom_library.py")

    summary = exporter.export_atom_library(
        database_url=client.app.state.settings.database_url,
        output_root=tmp_path,
        overwrite=False,
    )
    assert summary["documents_exported"] >= 1
    export_root = Path(summary["export_root"])
    manifest_paths = sorted(export_root.glob("*/manifest.json"))
    assert manifest_paths

    manifest = json.loads(manifest_paths[0].read_text(encoding="utf-8"))
    assert "document_id" in manifest
    assert "checksum" in manifest
    assert "atom_level_counts" in manifest
    atom_file_count = sum(len(list(p.glob("*.txt"))) for p in manifest_paths[0].parent.iterdir() if p.is_dir())
    assert atom_file_count == manifest["atom_count"]

    summary_again = exporter.export_atom_library(
        database_url=client.app.state.settings.database_url,
        output_root=tmp_path,
        overwrite=False,
    )
    assert summary_again["atoms_exported"] == summary["atoms_exported"]


def _ingest_two_texts_for_remix(client, auth_headers, tmp_path: Path) -> tuple[str, str]:
    left = tmp_path / "left.md"
    right = tmp_path / "right.md"
    left.write_text("Homer sings of wandering seas and patient return.", encoding="utf-8")
    right.write_text("Milton names rebellion, fall, and radiant loss.", encoding="utf-8")
    _, left_id = _ingest_one(client, auth_headers, left, atom_tracks=["literary", "glyphic_seed"])
    _, right_id = _ingest_one(client, auth_headers, right, atom_tracks=["literary", "glyphic_seed"])
    return left_id, right_id


# AB01-T005
def test_ab01_t005_remix_compose_contract(client, auth_headers, tmp_path: Path):
    left_id, right_id = _ingest_two_texts_for_remix(client, auth_headers, tmp_path)
    req = {
        "source_document_id": left_id,
        "target_document_id": right_id,
        "strategy": "interleave",
        "seed": 42,
        "atom_levels": ["word"],
        "create_branch": False,
        "persist_artifact": False,
    }
    first = client.post("/api/v1/remix/compose", headers=auth_headers["operator"], json=req)
    second = client.post("/api/v1/remix/compose", headers=auth_headers["operator"], json=req)
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    p1 = first.json()
    p2 = second.json()
    assert p1["remixed_text"] == p2["remixed_text"]
    assert p1["text_hash"] == p2["text_hash"]
    assert p1["source_atom_refs"]
    assert p1["new_branch_id"] is None

    missing = client.post(
        "/api/v1/remix/compose",
        headers=auth_headers["operator"],
        json={**req, "source_document_id": "does-not-exist"},
    )
    assert missing.status_code == 404


# AB01-T006
def test_ab01_t006_remix_persistence_and_retrieval_contract(client, auth_headers, tmp_path: Path):
    left_id, right_id = _ingest_two_texts_for_remix(client, auth_headers, tmp_path)
    response = client.post(
        "/api/v1/remix/compose",
        headers=auth_headers["operator"],
        json={
            "source_document_id": left_id,
            "target_document_id": right_id,
            "strategy": "thematic_blend",
            "seed": 9,
            "atom_levels": ["sentence", "word"],
            "persist_artifact": True,
            "create_branch": False,
        },
    )
    assert response.status_code == 200, response.text
    compose = response.json()
    remix_id = compose["remix_artifact_id"]
    assert remix_id
    assert compose["governance_decision_id"] is not None

    detail = client.get(f"/api/v1/remix/{remix_id}", headers=auth_headers["viewer"])
    assert detail.status_code == 200, detail.text
    payload = detail.json()
    assert payload["remix_artifact_id"] == remix_id
    assert payload["source_links"]
    assert "nodes" in payload["lineage_graph_refs"]

    listing = client.get("/api/v1/remix?limit=10&offset=0", headers=auth_headers["viewer"])
    assert listing.status_code == 200, listing.text
    rows = listing.json()["remixes"]
    assert any(r["remix_artifact_id"] == remix_id for r in rows)

    session = client.app.state.db.session()
    try:
        artifact = session.scalar(select(RemixArtifact).where(RemixArtifact.id == remix_id))
        assert artifact is not None
        assert artifact.governance_decision_id is not None
    finally:
        session.close()


def test_ab01_t006_alembic_upgrade_downgrade_contract(tmp_path: Path):
    repo_root = _repo_root()
    db_path = tmp_path / "ab01_t006_migrate.db"
    env = {
        **os.environ,
        "NEXUS_DATABASE_URL": f"sqlite:///{db_path}",
    }
    upgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert upgrade.returncode == 0, upgrade.stderr

    downgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "20260223_0003"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert downgrade.returncode == 0, downgrade.stderr

    reupgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert reupgrade.returncode == 0, reupgrade.stderr


# AB01-T007
def test_ab01_t007_create_branch_hook_contract(client, auth_headers, tmp_path: Path):
    left_id, right_id = _ingest_two_texts_for_remix(client, auth_headers, tmp_path)

    no_branch = client.post(
        "/api/v1/remix/compose",
        headers=auth_headers["operator"],
        json={
            "source_document_id": left_id,
            "target_document_id": right_id,
            "strategy": "interleave",
            "seed": 100,
            "atom_levels": ["word"],
            "create_branch": False,
            "persist_artifact": True,
        },
    )
    assert no_branch.status_code == 200, no_branch.text
    no_branch_payload = no_branch.json()
    assert no_branch_payload["new_branch_id"] is None

    with_branch_1 = client.post(
        "/api/v1/remix/compose",
        headers=auth_headers["operator"],
        json={
            "source_document_id": left_id,
            "target_document_id": right_id,
            "strategy": "interleave",
            "seed": 101,
            "atom_levels": ["word"],
            "create_branch": True,
            "persist_artifact": True,
        },
    )
    with_branch_2 = client.post(
        "/api/v1/remix/compose",
        headers=auth_headers["operator"],
        json={
            "source_document_id": left_id,
            "target_document_id": right_id,
            "strategy": "interleave",
            "seed": 102,
            "atom_levels": ["word"],
            "create_branch": True,
            "persist_artifact": True,
        },
    )
    assert with_branch_1.status_code == 200, with_branch_1.text
    assert with_branch_2.status_code == 200, with_branch_2.text
    p1 = with_branch_1.json()
    p2 = with_branch_2.json()
    assert p1["new_branch_id"]
    assert p1["event_id"]

    timeline = client.get(f"/api/v1/branches/{p1['new_branch_id']}/timeline", headers=auth_headers["viewer"])
    assert timeline.status_code == 200, timeline.text
    events = timeline.json()["events"]
    remix_events = [e for e in events if e["event_type"] == "remix"]
    assert remix_events
    payload = remix_events[-1]["event_payload"]
    assert payload.get("remix_artifact_id") == p1["remix_artifact_id"]
    assert payload.get("remix_payload_hash")

    compare = client.get(f"/api/v1/branches/{p1['new_branch_id']}/compare/{p2['new_branch_id']}", headers=auth_headers["viewer"])
    assert compare.status_code == 200, compare.text
    assert compare.json()["distance"] >= 0


# AB01-T008
def test_ab01_t008_scaffold_sync_contract(tmp_path: Path):
    alignment = _load_script_module("alexandria_babel_alignment", "scripts/alexandria_babel_alignment.py")
    out_dir = tmp_path / "docs" / "alexandria_babel"
    out_dir.mkdir(parents=True, exist_ok=True)

    scaffold = alignment.ensure_scaffold(out_dir)
    assert set(scaffold["required"]) == {
        "Thread_Plan_Academic.md",
        "Thread_Plan_Funding.md",
        "Thread_Plan_UX.md",
    }
    index = alignment.build_scaffold_index(out_dir)
    assert Path(index["index_path"]).exists()

    check_ok = alignment.check_scaffold(out_dir)
    assert check_ok["missing"] == []
    assert check_ok["index_exists"] is True
    assert check_ok["missing_from_index"] == []

    (out_dir / "Thread_Plan_UX.md").unlink()
    check_fail = alignment.check_scaffold(out_dir)
    assert "Thread_Plan_UX.md" in check_fail["missing"]


def test_ab01_t008_check_scaffold_cli_fails_when_missing(tmp_path: Path):
    repo_root = _repo_root()
    out_dir = tmp_path / "docs" / "alexandria_babel"
    out_dir.mkdir(parents=True, exist_ok=True)
    script = repo_root / "scripts" / "alexandria_babel_alignment.py"

    run = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), "--out-dir", "docs/alexandria_babel", "--mode", "check-scaffold"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run.returncode == 1
