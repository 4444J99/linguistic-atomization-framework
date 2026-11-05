from __future__ import annotations

import logging
from pathlib import Path
import re

from fastapi.testclient import TestClient
from sqlalchemy import inspect, select

from nexus_babel.config import Settings
from nexus_babel.main import create_app
from nexus_babel.models import ApiKey, ModePolicy

API_V1_OPERATION_COUNT = 31
MVP_NEXT_ROADMAP_BASELINE_TEST_COUNT = 129


def _prod_settings(tmp_path: Path, **overrides) -> Settings:
    return Settings(
        environment="prod",
        database_url=f"sqlite:///{tmp_path / 'prod.db'}",
        corpus_root=tmp_path,
        object_storage_root=tmp_path / "object_storage",
        neo4j_uri=None,
        neo4j_username=None,
        neo4j_password=None,
        **overrides,
    )


def test_prod_default_schema_mode_does_not_auto_create(tmp_path: Path):
    settings = _prod_settings(tmp_path)
    app = create_app(settings)
    with TestClient(app):
        pass

    assert settings.resolved_schema_management_mode() == "migrate_only"
    tables = set(inspect(app.state.db.engine).get_table_names())
    assert "documents" not in tables
    assert "api_keys" not in tables


def test_prod_auto_create_with_bootstrap_disabled_skips_key_seeding(tmp_path: Path):
    settings = _prod_settings(tmp_path, schema_management_mode="auto_create", bootstrap_keys_enabled=False)
    app = create_app(settings)
    with TestClient(app):
        pass

    tables = set(inspect(app.state.db.engine).get_table_names())
    assert {"documents", "api_keys", "mode_policies"}.issubset(tables)

    session = app.state.db.session()
    try:
        assert session.scalars(select(ApiKey)).all() == []
        policies = session.scalars(select(ModePolicy)).all()
        assert {p.mode for p in policies} == {"PUBLIC", "RAW"}
    finally:
        session.close()


def test_prod_auto_create_with_bootstrap_enabled_seeds_keys(tmp_path: Path):
    settings = _prod_settings(tmp_path, schema_management_mode="auto_create", bootstrap_keys_enabled=True)
    app = create_app(settings)
    with TestClient(app):
        pass

    session = app.state.db.session()
    try:
        keys = session.scalars(select(ApiKey)).all()
        assert len(keys) == 4
        assert {k.owner for k in keys} == {"dev-viewer", "dev-operator", "dev-researcher", "dev-admin"}
    finally:
        session.close()


def test_non_dev_default_like_path_warnings(tmp_path: Path, caplog):
    db_path = tmp_path / "warn.db"
    with caplog.at_level(logging.WARNING):
        create_app(
            Settings(
                environment="prod",
                database_url=f"sqlite:///{db_path}",
                schema_management_mode="off",
                neo4j_uri=None,
                neo4j_username=None,
                neo4j_password=None,
            )
        )
    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "default-like corpus_root" in messages
    assert "default-like object_storage_root" in messages


def test_request_id_header_preserved_on_domain_errors(client, auth_headers):
    response = client.get("/api/v1/documents/does-not-exist", headers=auth_headers["viewer"])
    assert response.status_code == 404
    assert response.headers.get("X-Request-ID")
    body = response.json()
    assert body["detail"] == "Document not found"


def test_api_route_count_parity(client):
    http_methods = {"get", "post", "put", "patch", "delete"}
    operations = 0
    for path, spec in client.app.openapi()["paths"].items():
        if not path.startswith("/api/v1/"):
            continue
        operations += sum(1 for method in spec if method in http_methods)
    assert operations == API_V1_OPERATION_COUNT


def test_evolution_branch_routes_present_in_openapi(client):
    paths = client.app.openapi()["paths"]
    expected = {
        "/api/v1/evolve/branch",
        "/api/v1/evolve/multi",
        "/api/v1/branches/{branch_id}/timeline",
        "/api/v1/branches/{branch_id}/replay",
        "/api/v1/branches/{branch_id}/compare/{other_branch_id}",
        "/api/v1/branches/merge",
        "/api/v1/branches/{branch_id}/visualization",
    }
    assert expected.issubset(paths.keys())


def test_runbook_make_targets_exist():
    repo_root = Path(__file__).resolve().parents[1]
    runbook = (repo_root / "docs" / "OPERATOR_RUNBOOK.md").read_text(encoding="utf-8")
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")

    for command in (
        "make db-upgrade",
        "make test",
        "make lint",
        "make openapi-snapshot",
        "make certainty",
        "make certainty-check",
        "make evolution-contract-test",
        "make verify",
        "make run-api",
        "make run-worker",
    ):
        assert command in runbook

    for target in (
        "db-upgrade",
        "test",
        "lint",
        "openapi-snapshot",
        "certainty",
        "certainty-check",
        "evolution-contract-test",
        "verify",
        "run-api",
        "run-worker",
    ):
        assert re.search(rf"^{re.escape(target)}:\s*$", makefile, flags=re.MULTILINE)


def test_mvp_next_roadmap_baseline_smoke_alignment():
    repo_root = Path(__file__).resolve().parents[1]
    roadmap = (repo_root / "docs" / "roadmap_mvp_next.md").read_text(encoding="utf-8")

    assert f"`{API_V1_OPERATION_COUNT}` `/api/v1` operations are available" in roadmap
    assert f"`{MVP_NEXT_ROADMAP_BASELINE_TEST_COUNT}` tests before the next evolution modularity wave" in roadmap
    assert "src/nexus_babel/services/evolution.py" in roadmap
    assert "## Hotspot Rotation Rule" in roadmap
