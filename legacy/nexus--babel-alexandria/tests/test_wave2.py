from __future__ import annotations

from sqlalchemy import select

from nexus_babel.models import AnalysisRun


def _ingest_one(client, sample_corpus, headers):
    response = client.post(
        "/api/v1/ingest/batch",
        headers=headers,
        json={
            "source_paths": [str(sample_corpus["text"])],
            "modalities": [],
            "parse_options": {"atomize": True},
        },
    )
    assert response.status_code == 200, response.text
    job = client.get(f"/api/v1/ingest/jobs/{response.json()['ingest_job_id']}", headers=headers)
    assert job.status_code == 200, job.text
    return job.json()["files"][0]["document_id"]


def test_async_job_lifecycle_and_artifacts(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])

    submit = client.post(
        "/api/v1/jobs/submit",
        headers=auth_headers["operator"],
        json={
            "job_type": "analyze",
            "execution_mode": "async",
            "idempotency_key": "wave2-async-job-1",
            "payload": {
                "document_id": doc_id,
                "mode": "PUBLIC",
                "plugin_profile": "deterministic",
            },
        },
    )
    assert submit.status_code == 200, submit.text
    job_id = submit.json()["job_id"]

    session = client.app.state.db.session()
    try:
        processed = client.app.state.job_service.process_next(session, "pytest-worker")
        assert processed is not None
        session.commit()
    finally:
        session.close()

    status = client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers["viewer"])
    assert status.status_code == 200, status.text
    payload = status.json()
    assert payload["status"] == "succeeded"
    assert payload["attempt_count"] >= 1
    assert payload["artifacts"]

    session = client.app.state.db.session()
    try:
        run = session.scalar(select(AnalysisRun).where(AnalysisRun.job_id == job_id))
        assert run is not None
        run_id = run.id
    finally:
        session.close()

    run_resp = client.get(f"/api/v1/analysis/runs/{run_id}", headers=auth_headers["viewer"])
    assert run_resp.status_code == 200
    assert run_resp.json()["layer_outputs"]


def test_job_idempotency_returns_same_job(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    payload = {
        "job_type": "analyze",
        "execution_mode": "async",
        "idempotency_key": "wave2-idempotent-1",
        "payload": {
            "document_id": doc_id,
            "mode": "PUBLIC",
        },
    }
    first = client.post("/api/v1/jobs/submit", headers=auth_headers["operator"], json=payload)
    second = client.post("/api/v1/jobs/submit", headers=auth_headers["operator"], json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["job_id"] == second.json()["job_id"]


def test_job_cancel(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    submit = client.post(
        "/api/v1/jobs/submit",
        headers=auth_headers["operator"],
        json={
            "job_type": "analyze",
            "execution_mode": "async",
            "payload": {"document_id": doc_id, "mode": "PUBLIC"},
        },
    )
    job_id = submit.json()["job_id"]
    cancel = client.post(f"/api/v1/jobs/{job_id}/cancel", headers=auth_headers["operator"])
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"


def test_branch_replay_and_compare(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    b1 = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["researcher"],
        json={"root_document_id": doc_id, "event_type": "natural_drift", "event_payload": {"seed": 9}, "mode": "RAW"},
    )
    b2 = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["researcher"],
        json={"root_document_id": doc_id, "event_type": "synthetic_mutation", "event_payload": {"seed": 9, "mutation_rate": 0.2}, "mode": "RAW"},
    )
    assert b1.status_code == 200
    assert b2.status_code == 200
    left = b1.json()["new_branch_id"]
    right = b2.json()["new_branch_id"]

    replay = client.post(f"/api/v1/branches/{left}/replay", headers=auth_headers["viewer"])
    compare = client.get(f"/api/v1/branches/{left}/compare/{right}", headers=auth_headers["viewer"])
    assert replay.status_code == 200
    assert compare.status_code == 200
    assert "text_hash" in replay.json()
    assert "distance" in compare.json()


def test_hypergraph_query_and_audit_decisions(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    query = client.get(f"/api/v1/hypergraph/query?document_id={doc_id}&limit=10", headers=auth_headers["viewer"])
    assert query.status_code == 200
    assert "nodes" in query.json()

    decision = client.post(
        "/api/v1/governance/evaluate",
        headers=auth_headers["operator"],
        json={"candidate_output": "we should kill this sentence", "mode": "PUBLIC"},
    )
    assert decision.status_code == 200
    trace = decision.json()["decision_trace"]
    assert trace["hits"]

    audit = client.get("/api/v1/audit/policy-decisions?limit=5", headers=auth_headers["operator"])
    assert audit.status_code == 200
    rows = audit.json()["decisions"]
    assert rows
    assert "decision_trace" in rows[0]
