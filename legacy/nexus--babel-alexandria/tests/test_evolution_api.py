from __future__ import annotations

import hashlib
import time

import pytest

from sqlalchemy import func, select

from nexus_babel.models import Branch, BranchEvent, Document


def _ingest_one(client, sample_corpus, headers) -> str:
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


def _evolve(client, headers, *, root_document_id=None, parent_branch_id=None, event_type: str, event_payload: dict, mode: str = "PUBLIC") -> str:
    response = client.post(
        "/api/v1/evolve/branch",
        headers=headers,
        json={
            "root_document_id": root_document_id,
            "parent_branch_id": parent_branch_id,
            "event_type": event_type,
            "event_payload": event_payload,
            "mode": mode,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["new_branch_id"]


def test_evolve_branch_reverse_drift_supported(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    response = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["operator"],
        json={
            "root_document_id": doc_id,
            "event_type": "reverse_drift",
            "event_payload": {"seed": 0},
            "mode": "PUBLIC",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["diff_summary"]["event"] == "reverse_drift"
    assert "reversals" in payload["diff_summary"]


def test_multi_evolve_chain(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    response = client.post(
        "/api/v1/evolve/multi",
        headers=auth_headers["operator"],
        json={
            "root_document_id": doc_id,
            "mode": "PUBLIC",
            "events": [
                {"event_type": "natural_drift", "event_payload": {"seed": 11}},
                {"event_type": "reverse_drift", "event_payload": {"seed": 11}},
                {"event_type": "phase_shift", "event_payload": {"phase": "peak", "seed": 1}},
                {"event_type": "synthetic_mutation", "event_payload": {"mutation_rate": 0.15, "seed": 5}},
            ],
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["branch_ids"]) == 4
    assert len(payload["event_ids"]) == 4
    assert payload["final_branch_id"] == payload["branch_ids"][-1]
    assert payload["event_count"] == 4
    assert payload["final_text_hash"]
    assert payload["final_preview"]


def test_multi_evolve_empty_events_raises(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    response = client.post(
        "/api/v1/evolve/multi",
        headers=auth_headers["operator"],
        json={
            "root_document_id": doc_id,
            "mode": "PUBLIC",
            "events": [],
        },
    )
    assert response.status_code == 400, response.text
    assert "events must not be empty" in response.json()["detail"]


def test_multi_evolve_rollback_on_failure(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])

    session = client.app.state.db.session()
    try:
        before_branch_count = int(session.scalar(select(func.count(Branch.id))) or 0)
        before_event_count = int(session.scalar(select(func.count(BranchEvent.id))) or 0)
    finally:
        session.close()

    response = client.post(
        "/api/v1/evolve/multi",
        headers=auth_headers["operator"],
        json={
            "root_document_id": doc_id,
            "mode": "PUBLIC",
            "events": [
                {"event_type": "natural_drift", "event_payload": {"seed": 2}},
                {"event_type": "reverse_drift", "event_payload": {"seed": 2}},
                {"event_type": "synthetic_mutation", "event_payload": {"mutation_rate": 5.0, "seed": 2}},
            ],
        },
    )
    assert response.status_code == 400, response.text

    session = client.app.state.db.session()
    try:
        after_branch_count = int(session.scalar(select(func.count(Branch.id))) or 0)
        after_event_count = int(session.scalar(select(func.count(BranchEvent.id))) or 0)
    finally:
        session.close()

    assert after_branch_count == before_branch_count
    assert after_event_count == before_event_count


def test_multi_evolve_requires_operator(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    response = client.post(
        "/api/v1/evolve/multi",
        headers=auth_headers["viewer"],
        json={
            "root_document_id": doc_id,
            "mode": "PUBLIC",
            "events": [{"event_type": "natural_drift", "event_payload": {"seed": 0}}],
        },
    )
    assert response.status_code == 403, response.text


def test_multi_evolve_raw_mode_enforced(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    response = client.post(
        "/api/v1/evolve/multi",
        headers=auth_headers["operator"],
        json={
            "root_document_id": doc_id,
            "mode": "RAW",
            "events": [{"event_type": "natural_drift", "event_payload": {"seed": 0}}],
        },
    )
    assert response.status_code == 403, response.text


def test_checkpoint_accelerated_replay_correctness(client, sample_corpus, auth_headers, monkeypatch):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    service = client.app.state.evolution_service

    parent_branch_id = None
    for seed in range(20):
        response = client.post(
            "/api/v1/evolve/branch",
            headers=auth_headers["operator"],
            json={
                "root_document_id": doc_id if parent_branch_id is None else None,
                "parent_branch_id": parent_branch_id,
                "event_type": "natural_drift",
                "event_payload": {"seed": seed},
                "mode": "PUBLIC",
            },
        )
        assert response.status_code == 200, response.text
        parent_branch_id = response.json()["new_branch_id"]
    assert parent_branch_id is not None

    calls = {"count": 0}
    original_decompress = service._decompress_snapshot

    def _wrapped_decompress(payload: str):
        calls["count"] += 1
        return original_decompress(payload)

    monkeypatch.setattr(service, "_decompress_snapshot", _wrapped_decompress)

    timeline_resp = client.get(f"/api/v1/branches/{parent_branch_id}/timeline", headers=auth_headers["viewer"])
    assert timeline_resp.status_code == 200, timeline_resp.text
    timeline_payload = timeline_resp.json()
    assert len(timeline_payload["events"]) == 20
    assert timeline_payload["replay_snapshot"]["event_count"] == 20
    assert calls["count"] >= 1

    session = client.app.state.db.session()
    try:
        target_branch = session.scalar(select(Branch).where(Branch.id == parent_branch_id))
        assert target_branch is not None

        lineage = service._lineage(session, target_branch)
        events: list[BranchEvent] = []
        for node in lineage:
            events.extend(
                session.scalars(
                    select(BranchEvent).where(BranchEvent.branch_id == node.id).order_by(BranchEvent.event_index, BranchEvent.created_at)
                ).all()
            )

        root_text = ""
        if target_branch.root_document_id:
            doc = session.scalar(select(Document).where(Document.id == target_branch.root_document_id))
            assert doc is not None
            root_text = str((doc.provenance or {}).get("extracted_text", ""))

        replay_text = root_text
        for event in events:
            replay_text = service._apply_event(replay_text, event.event_type, event.event_payload).output_text

        expected_hash = hashlib.sha256(replay_text.encode("utf-8")).hexdigest()
    finally:
        session.close()

    assert timeline_payload["replay_snapshot"]["text_hash"] == expected_hash


def test_branch_visualization_endpoint(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])

    b1 = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["operator"],
        json={"root_document_id": doc_id, "event_type": "natural_drift", "event_payload": {"seed": 1}, "mode": "PUBLIC"},
    )
    assert b1.status_code == 200, b1.text
    branch_1 = b1.json()["new_branch_id"]

    b2 = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["operator"],
        json={
            "parent_branch_id": branch_1,
            "event_type": "phase_shift",
            "event_payload": {"phase": "peak", "seed": 2},
            "mode": "PUBLIC",
        },
    )
    assert b2.status_code == 200, b2.text
    branch_2 = b2.json()["new_branch_id"]

    b3 = client.post(
        "/api/v1/evolve/branch",
        headers=auth_headers["operator"],
        json={
            "parent_branch_id": branch_2,
            "event_type": "reverse_drift",
            "event_payload": {"seed": 3},
            "mode": "PUBLIC",
        },
    )
    assert b3.status_code == 200, b3.text
    target_branch = b3.json()["new_branch_id"]

    response = client.get(f"/api/v1/branches/{target_branch}/visualization", headers=auth_headers["viewer"])
    assert response.status_code == 200, response.text
    payload = response.json()
    assert {
        "branch_id",
        "root_document_id",
        "nodes",
        "edges",
        "summary",
    }.issubset(payload.keys())
    assert {"event_count", "edge_count", "lineage_depth", "secondary_lineage_branch_count", "merge_secondary_edge_count"}.issubset(
        payload["summary"].keys()
    )

    assert payload["branch_id"] == target_branch
    assert payload["root_document_id"] == doc_id
    assert len(payload["nodes"]) == 3
    assert len(payload["edges"]) >= 2
    assert payload["summary"]["event_count"] == 3
    assert payload["summary"]["lineage_depth"] == 3
    assert all("event_type" in node for node in payload["nodes"])
    assert all("metadata" in node for node in payload["nodes"])


@pytest.mark.slow
def test_checkpoint_replay_faster_than_full(client, sample_corpus, auth_headers, monkeypatch):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    service = client.app.state.evolution_service

    parent_branch_id = None
    for seed in range(50):
        parent_branch_id = _evolve(
            client,
            auth_headers["operator"],
            root_document_id=doc_id if parent_branch_id is None else None,
            parent_branch_id=parent_branch_id,
            event_type="natural_drift",
            event_payload={"seed": seed},
        )
    assert parent_branch_id is not None

    session = client.app.state.db.session()
    try:
        target_branch = session.scalar(select(Branch).where(Branch.id == parent_branch_id))
        assert target_branch is not None

        original_apply = service._apply_event

        def _slow_apply(text: str, event_type: str, event_payload: dict):
            time.sleep(0.0004)
            return original_apply(text, event_type, event_payload)

        monkeypatch.setattr(service, "_apply_event", _slow_apply)

        t0 = time.perf_counter()
        full_text, _, _ = service._replay_lineage_text(session, target_branch, use_checkpoints=False)
        full_elapsed = time.perf_counter() - t0

        t1 = time.perf_counter()
        checkpoint_text, _, _ = service._replay_lineage_text(session, target_branch, use_checkpoints=True)
        checkpoint_elapsed = time.perf_counter() - t1
    finally:
        session.close()

    assert hashlib.sha256(full_text.encode("utf-8")).hexdigest() == hashlib.sha256(checkpoint_text.encode("utf-8")).hexdigest()
    assert checkpoint_elapsed < full_elapsed


def test_branch_merge_interleave(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    left_branch = _evolve(
        client,
        auth_headers["operator"],
        root_document_id=doc_id,
        event_type="phase_shift",
        event_payload={"phase": "peak", "seed": 1},
    )
    right_branch = _evolve(
        client,
        auth_headers["operator"],
        root_document_id=doc_id,
        event_type="reverse_drift",
        event_payload={"seed": 2},
    )

    merge_resp = client.post(
        "/api/v1/branches/merge",
        headers=auth_headers["operator"],
        json={
            "left_branch_id": left_branch,
            "right_branch_id": right_branch,
            "strategy": "interleave",
            "mode": "PUBLIC",
        },
    )
    assert merge_resp.status_code == 200, merge_resp.text
    merge_payload = merge_resp.json()
    assert {"new_branch_id", "event_id", "strategy", "lca_branch_id", "conflict_semantics", "diff_summary"}.issubset(
        merge_payload.keys()
    )
    assert merge_payload["strategy"] == "interleave"
    assert merge_payload["new_branch_id"]
    assert merge_payload["event_id"]
    assert merge_payload["diff_summary"]["event"] == "merge"
    assert merge_payload["diff_summary"]["left_branch_id"] == left_branch
    assert merge_payload["diff_summary"]["right_branch_id"] == right_branch
    assert merge_payload["diff_summary"]["left_text_hash"]
    assert merge_payload["diff_summary"]["right_text_hash"]
    assert merge_payload["conflict_semantics"]
    assert merge_payload["conflict_semantics"]["resolution"] == "interleaved_union"
    assert merge_payload["conflict_semantics"]["strategy_effect"] == "word_interleave"
    assert merge_payload["diff_summary"]["conflict_semantics"] == merge_payload["conflict_semantics"]

    replay_resp = client.post(f"/api/v1/branches/{merge_payload['new_branch_id']}/replay", headers=auth_headers["viewer"])
    assert replay_resp.status_code == 200, replay_resp.text
    replay_payload = replay_resp.json()
    assert {"branch_id", "event_count", "text_hash", "preview", "replay_snapshot"}.issubset(replay_payload.keys())
    merged_preview = replay_payload["preview"]

    left_replay = client.post(f"/api/v1/branches/{left_branch}/replay", headers=auth_headers["viewer"]).json()["preview"]
    right_replay = client.post(f"/api/v1/branches/{right_branch}/replay", headers=auth_headers["viewer"]).json()["preview"]

    left_word = next((w for w in left_replay.split() if w.isalpha()), None)
    right_word = next((w for w in right_replay.split() if w.isalpha()), None)
    assert left_word is not None and left_word in merged_preview
    assert right_word is not None and right_word in merged_preview


def test_branch_visualization_includes_merge_secondary_parent_edges(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])

    left_root = _evolve(
        client,
        auth_headers["operator"],
        root_document_id=doc_id,
        event_type="natural_drift",
        event_payload={"seed": 10},
    )
    left_tip = _evolve(
        client,
        auth_headers["operator"],
        parent_branch_id=left_root,
        event_type="phase_shift",
        event_payload={"phase": "peak", "seed": 11},
    )
    right_root = _evolve(
        client,
        auth_headers["operator"],
        root_document_id=doc_id,
        event_type="reverse_drift",
        event_payload={"seed": 12},
    )
    right_tip = _evolve(
        client,
        auth_headers["operator"],
        parent_branch_id=right_root,
        event_type="synthetic_mutation",
        event_payload={"mutation_rate": 0.05, "seed": 13},
    )

    merge_resp = client.post(
        "/api/v1/branches/merge",
        headers=auth_headers["operator"],
        json={
            "left_branch_id": left_tip,
            "right_branch_id": right_tip,
            "strategy": "interleave",
            "mode": "PUBLIC",
        },
    )
    assert merge_resp.status_code == 200, merge_resp.text
    merged_branch_id = merge_resp.json()["new_branch_id"]

    viz_resp = client.get(f"/api/v1/branches/{merged_branch_id}/visualization", headers=auth_headers["viewer"])
    assert viz_resp.status_code == 200, viz_resp.text
    payload = viz_resp.json()

    assert payload["summary"]["secondary_lineage_branch_count"] >= 1
    assert payload["summary"]["merge_secondary_edge_count"] >= 1
    assert any(edge["type"] == "merge_secondary_parent" for edge in payload["edges"])
    assert any(
        edge["type"] == "merge_secondary_parent" and edge["metadata"]["right_branch_id"] == right_tip
        for edge in payload["edges"]
    )
    assert any(
        node["branch_id"] == right_tip and node["lineage_role"] == "secondary_merge_parent"
        for node in payload["nodes"]
    )


def test_branch_merge_requires_operator(client, sample_corpus, auth_headers):
    doc_id = _ingest_one(client, sample_corpus, auth_headers["operator"])
    left_branch = _evolve(
        client,
        auth_headers["operator"],
        root_document_id=doc_id,
        event_type="natural_drift",
        event_payload={"seed": 1},
    )
    right_branch = _evolve(
        client,
        auth_headers["operator"],
        root_document_id=doc_id,
        event_type="reverse_drift",
        event_payload={"seed": 1},
    )
    merge_resp = client.post(
        "/api/v1/branches/merge",
        headers=auth_headers["viewer"],
        json={"left_branch_id": left_branch, "right_branch_id": right_branch, "strategy": "left_wins", "mode": "PUBLIC"},
    )
    assert merge_resp.status_code == 403
