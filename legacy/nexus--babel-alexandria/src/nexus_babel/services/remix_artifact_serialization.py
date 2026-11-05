from __future__ import annotations

from typing import Any

from nexus_babel.models import RemixArtifact


def artifact_summary(artifact: RemixArtifact) -> dict[str, Any]:
    return {
        "remix_artifact_id": artifact.id,
        "strategy": artifact.strategy,
        "seed": artifact.seed,
        "mode": artifact.mode,
        "text_hash": artifact.text_hash,
        "create_branch": artifact.create_branch,
        "branch_id": artifact.branch_id,
        "governance_decision_id": artifact.governance_decision_id,
        "source_document_id": artifact.source_document_id,
        "target_document_id": artifact.target_document_id,
        "created_at": artifact.created_at,
    }


def artifact_to_dict(artifact: RemixArtifact) -> dict[str, Any]:
    source_links = sorted(list(artifact.source_links or []), key=lambda r: (r.role, r.id))
    governance_trace = ((artifact.artifact_metadata or {}).get("governance") or {}).get("decision_trace") or {}
    return {
        "remix_artifact_id": artifact.id,
        "strategy": artifact.strategy,
        "seed": artifact.seed,
        "mode": artifact.mode,
        "remixed_text": artifact.remixed_text,
        "text_hash": artifact.text_hash,
        "payload_hash": artifact.payload_hash,
        "rng_seed_hex": artifact.rng_seed_hex,
        "create_branch": artifact.create_branch,
        "source_document_id": artifact.source_document_id,
        "source_branch_id": artifact.source_branch_id,
        "target_document_id": artifact.target_document_id,
        "target_branch_id": artifact.target_branch_id,
        "branch_id": artifact.branch_id,
        "branch_event_id": artifact.branch_event_id,
        "governance_decision_id": artifact.governance_decision_id,
        "governance_trace": governance_trace,
        "lineage_graph_refs": artifact.lineage_graph_refs or {},
        "source_links": [
            {
                "role": row.role,
                "document_id": row.document_id,
                "branch_id": row.branch_id,
                "atom_level": row.atom_level,
                "atom_count": row.atom_count,
                "atom_refs": row.atom_refs or [],
            }
            for row in source_links
        ],
        "created_at": artifact.created_at,
    }


def build_lineage_graph_refs(
    *,
    source_ctx: dict[str, Any],
    target_ctx: dict[str, Any],
    branch_id: str | None,
    branch_event_id: str | None,
    remix_artifact_id: str,
) -> dict[str, Any]:
    nodes: list[str] = [f"remix:{remix_artifact_id}"]
    for key in ("document_id", "branch_id"):
        if source_ctx.get(key):
            nodes.append(f"source_{key}:{source_ctx[key]}")
        if target_ctx.get(key):
            nodes.append(f"target_{key}:{target_ctx[key]}")
    if branch_id:
        nodes.append(f"branch:{branch_id}")
    if branch_event_id:
        nodes.append(f"branch_event:{branch_event_id}")
    return {
        "nodes": nodes,
        "edges": [
            {"from": f"remix:{remix_artifact_id}", "to": f"branch:{branch_id}", "type": "PRODUCED"}
            for _ in [1]
            if branch_id
        ],
    }
