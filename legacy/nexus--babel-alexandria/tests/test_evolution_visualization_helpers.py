from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from nexus_babel.services.evolution_visualization import assemble_visualization_graph


@dataclass
class _BranchStub:
    id: str
    parent_branch_id: str | None
    root_document_id: str | None
    mode: str
    state_snapshot: dict[str, Any]
    created_at: datetime


@dataclass
class _EventStub:
    id: str
    branch_id: str
    event_index: int
    event_type: str
    event_payload: dict[str, Any]
    diff_summary: dict[str, Any]
    created_at: datetime


def test_assemble_visualization_graph_preserves_merge_secondary_parent_edges():
    t0 = datetime(2026, 2, 25, 12, 0, tzinfo=UTC)
    root_doc_id = "doc-1"

    left_root = _BranchStub(
        id="left-root",
        parent_branch_id=None,
        root_document_id=root_doc_id,
        mode="PUBLIC",
        state_snapshot={"phase": "expansion"},
        created_at=t0,
    )
    merge_branch = _BranchStub(
        id="merge-branch",
        parent_branch_id="left-root",
        root_document_id=root_doc_id,
        mode="PUBLIC",
        state_snapshot={"phase": "peak"},
        created_at=t0 + timedelta(seconds=2),
    )
    right_branch = _BranchStub(
        id="right-branch",
        parent_branch_id=None,
        root_document_id=root_doc_id,
        mode="PUBLIC",
        state_snapshot={"phase": "compression"},
        created_at=t0 + timedelta(seconds=1),
    )

    e_left = _EventStub(
        id="e-left",
        branch_id="left-root",
        event_index=1,
        event_type="natural_drift",
        event_payload={"seed": 1},
        diff_summary={"event": "natural_drift"},
        created_at=t0,
    )
    e_right = _EventStub(
        id="e-right",
        branch_id="right-branch",
        event_index=1,
        event_type="reverse_drift",
        event_payload={"seed": 2},
        diff_summary={"event": "reverse_drift"},
        created_at=t0 + timedelta(seconds=1),
    )
    e_merge = _EventStub(
        id="e-merge",
        branch_id="merge-branch",
        event_index=1,
        event_type="merge",
        event_payload={
            "strategy": "interleave",
            "lca_branch_id": "left-root",
            "right_branch_id": "right-branch",
        },
        diff_summary={"event": "merge"},
        created_at=t0 + timedelta(seconds=2),
    )

    payload = assemble_visualization_graph(
        branch=merge_branch,  # type: ignore[arg-type]
        primary_lineage=[left_root, merge_branch],  # type: ignore[list-item]
        branches_by_id={
            left_root.id: left_root,  # type: ignore[dict-item]
            merge_branch.id: merge_branch,  # type: ignore[dict-item]
            right_branch.id: right_branch,  # type: ignore[dict-item]
        },
        branch_events_by_id={
            left_root.id: [e_left],  # type: ignore[list-item]
            merge_branch.id: [e_merge],  # type: ignore[list-item]
            right_branch.id: [e_right],  # type: ignore[list-item]
        },
    )

    assert payload["branch_id"] == "merge-branch"
    assert payload["summary"]["event_count"] == 3
    assert payload["summary"]["secondary_lineage_branch_count"] == 1
    assert payload["summary"]["merge_secondary_edge_count"] == 1
    assert any(edge["type"] == "parent_branch" for edge in payload["edges"])
    assert any(
        edge["type"] == "merge_secondary_parent" and edge["metadata"]["right_branch_id"] == "right-branch"
        for edge in payload["edges"]
    )
    assert any(node["branch_id"] == "right-branch" and node["lineage_role"] == "secondary_merge_parent" for node in payload["nodes"])
