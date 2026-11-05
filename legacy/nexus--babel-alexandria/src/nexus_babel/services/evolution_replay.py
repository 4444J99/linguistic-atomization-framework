from __future__ import annotations

import base64
import json
import zlib
from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nexus_babel.models import Branch, BranchCheckpoint, BranchEvent, Document
from .evolution_types import DriftResult


def lineage(session: Session, branch: Branch) -> list[Branch]:
    result = [branch]
    current = branch
    while current.parent_branch_id:
        parent = session.scalar(select(Branch).where(Branch.id == current.parent_branch_id))
        if not parent:
            break
        result.append(parent)
        current = parent
    result.reverse()
    return result


def lineage_event_count(
    session: Session,
    branch: Branch,
    *,
    lineage_fn: Callable[[Session, Branch], list[Branch]] = lineage,
) -> int:
    lineage_nodes = lineage_fn(session, branch)
    count = 0
    for node in lineage_nodes:
        count += int(session.scalar(select(func.count(BranchEvent.id)).where(BranchEvent.branch_id == node.id)) or 0)
    return count


def latest_lineage_checkpoint(session: Session, lineage_nodes: list[Branch]) -> BranchCheckpoint | None:
    lineage_ids = [node.id for node in lineage_nodes]
    if not lineage_ids:
        return None
    return session.scalar(
        select(BranchCheckpoint)
        .where(BranchCheckpoint.branch_id.in_(lineage_ids))
        .order_by(BranchCheckpoint.event_index.desc(), BranchCheckpoint.created_at.desc())
    )


def collect_lineage_events(session: Session, lineage_nodes: list[Branch]) -> list[BranchEvent]:
    events: list[BranchEvent] = []
    for node in lineage_nodes:
        events.extend(
            session.scalars(
                select(BranchEvent)
                .where(BranchEvent.branch_id == node.id)
                .order_by(BranchEvent.event_index, BranchEvent.created_at)
            ).all()
        )
    return events


def resolve_root_text(session: Session, root_document_id: str | None) -> str:
    if not root_document_id:
        return ""
    doc = session.scalar(select(Document).where(Document.id == root_document_id))
    if not doc:
        return ""
    return str((doc.provenance or {}).get("extracted_text", ""))


def replay_lineage_text(
    session: Session,
    branch: Branch,
    *,
    use_checkpoints: bool = True,
    lineage_fn: Callable[[Session, Branch], list[Branch]] = lineage,
    collect_events_fn: Callable[[Session, list[Branch]], list[BranchEvent]] = collect_lineage_events,
    resolve_root_text_fn: Callable[[Session, str | None], str] = resolve_root_text,
    latest_checkpoint_fn: Callable[[Session, list[Branch]], BranchCheckpoint | None] = latest_lineage_checkpoint,
    decompress_snapshot_fn: Callable[[str], dict[str, Any]],
    apply_event_fn: Callable[[str, str, dict[str, Any]], DriftResult],
) -> tuple[str, list[Branch], list[BranchEvent]]:
    lineage_nodes = lineage_fn(session, branch)
    events = collect_events_fn(session, lineage_nodes)
    replay_text = resolve_root_text_fn(session, branch.root_document_id)

    checkpoint_start_index = 0
    if use_checkpoints:
        latest_checkpoint = latest_checkpoint_fn(session, lineage_nodes)
        if latest_checkpoint is not None:
            snapshot = decompress_snapshot_fn(latest_checkpoint.snapshot_compressed)
            if "current_text" in snapshot:
                replay_text = str(snapshot.get("current_text", ""))
                checkpoint_start_index = min(max(int(latest_checkpoint.event_index), 0), len(events))

    for event in events[checkpoint_start_index:]:
        replay_text = apply_event_fn(replay_text, event.event_type, event.event_payload).output_text

    return replay_text, lineage_nodes, events


def next_event_index(session: Session, branch_id: str) -> int:
    max_index = session.scalar(select(func.max(BranchEvent.event_index)).where(BranchEvent.branch_id == branch_id))
    return int(max_index or 0) + 1


def compress_snapshot(snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(snapshot, sort_keys=True).encode("utf-8")
    compressed = zlib.compress(encoded, level=9)
    return base64.b64encode(compressed).decode("ascii")


def decompress_snapshot(payload: str) -> dict[str, Any]:
    raw = base64.b64decode(payload.encode("ascii"))
    decoded = zlib.decompress(raw)
    data = json.loads(decoded.decode("utf-8"))
    return data if isinstance(data, dict) else {}
