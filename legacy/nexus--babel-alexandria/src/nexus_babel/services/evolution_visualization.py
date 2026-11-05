from __future__ import annotations

from typing import Any

from nexus_babel.models import Branch, BranchEvent


def assemble_visualization_graph(
    *,
    branch: Branch,
    primary_lineage: list[Branch],
    branches_by_id: dict[str, Branch],
    branch_events_by_id: dict[str, list[BranchEvent]],
) -> dict[str, Any]:
    primary_branch_ids = {node.id for node in primary_lineage}
    lineage = list(primary_lineage) + sorted(
        [node for node_id, node in branches_by_id.items() if node_id not in primary_branch_ids],
        key=lambda node: (node.created_at, node.id),
    )
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    edge_ids: set[str] = set()
    secondary_branch_ids = {node.id for node in lineage if node.id not in primary_branch_ids}

    for node in lineage:
        branch_events = branch_events_by_id.get(node.id, [])
        phase = str((node.state_snapshot or {}).get("phase", "")) or None
        for event in branch_events:
            nodes.append(
                {
                    "id": event.id,
                    "kind": "event",
                    "branch_id": node.id,
                    "lineage_role": "secondary_merge_parent" if node.id in secondary_branch_ids else "primary",
                    "parent_branch_id": node.parent_branch_id,
                    "root_document_id": node.root_document_id,
                    "event_index": event.event_index,
                    "event_type": event.event_type,
                    "phase": phase,
                    "mode": node.mode,
                    "created_at": event.created_at,
                    "metadata": {
                        "diff_summary": event.diff_summary,
                        "event_payload": event.event_payload,
                    },
                }
            )

        for prev, curr in zip(branch_events, branch_events[1:]):
            edge_id = f"{prev.id}->{curr.id}"
            if edge_id in edge_ids:
                continue
            edge_ids.add(edge_id)
            edges.append({"id": edge_id, "source": prev.id, "target": curr.id, "type": "intra_branch_sequence", "metadata": {}})

    last_event_by_branch = {branch_id_: events[-1] for branch_id_, events in branch_events_by_id.items() if events}
    for node in lineage:
        if not node.parent_branch_id:
            continue
        parent_event = last_event_by_branch.get(node.parent_branch_id)
        child_event = last_event_by_branch.get(node.id)
        if parent_event is None or child_event is None:
            continue
        edge_id = f"{parent_event.id}->{child_event.id}:parent"
        if edge_id not in edge_ids:
            edge_ids.add(edge_id)
            edges.append(
                {
                    "id": edge_id,
                    "source": parent_event.id,
                    "target": child_event.id,
                    "type": "parent_branch",
                    "metadata": {"relationship": "primary_parent"},
                }
            )

    merge_secondary_edge_count = 0
    for node in lineage:
        for event in branch_events_by_id.get(node.id, []):
            if event.event_type != "merge":
                continue
            payload = dict(event.event_payload or {})
            right_branch_id = str(payload.get("right_branch_id") or "").strip()
            if not right_branch_id:
                continue
            secondary_parent_event = last_event_by_branch.get(right_branch_id)
            if secondary_parent_event is None:
                continue
            edge_id = f"{secondary_parent_event.id}->{event.id}:merge-secondary"
            if edge_id in edge_ids:
                continue
            edge_ids.add(edge_id)
            merge_secondary_edge_count += 1
            edges.append(
                {
                    "id": edge_id,
                    "source": secondary_parent_event.id,
                    "target": event.id,
                    "type": "merge_secondary_parent",
                    "metadata": {
                        "strategy": payload.get("strategy"),
                        "lca_branch_id": payload.get("lca_branch_id"),
                        "right_branch_id": right_branch_id,
                    },
                }
            )

    return {
        "branch_id": branch.id,
        "root_document_id": branch.root_document_id,
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "event_count": len(nodes),
            "edge_count": len(edges),
            "lineage_depth": len(primary_lineage),
            "secondary_lineage_branch_count": len(secondary_branch_ids),
            "merge_secondary_edge_count": merge_secondary_edge_count,
        },
    }
