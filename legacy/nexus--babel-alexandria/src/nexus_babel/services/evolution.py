from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import Branch, BranchCheckpoint, BranchEvent, Document
from nexus_babel.services import evolution_events, evolution_merge, evolution_replay, evolution_visualization
from nexus_babel.services.evolution_types import DriftResult


class EvolutionService:
    NATURAL_MAP = dict(evolution_events.NATURAL_MAP)
    REVERSE_NATURAL_MAP = dict(evolution_events.REVERSE_NATURAL_MAP)
    GLYPH_POOL = list(evolution_events.GLYPH_POOL)
    PHASES = set(evolution_events.PHASES)
    MERGE_STRATEGIES = set(evolution_events.MERGE_STRATEGIES)

    def evolve_branch(
        self,
        session: Session,
        parent_branch_id: str | None,
        root_document_id: str | None,
        event_type: str,
        event_payload: dict[str, Any],
        mode: str,
    ) -> tuple[Branch, BranchEvent]:
        payload = self._validate_event_payload(event_type, event_payload)
        parent = None
        lineage_event_count = 0
        if parent_branch_id:
            parent = session.scalar(select(Branch).where(Branch.id == parent_branch_id))
            if not parent:
                raise ValueError(f"Parent branch {parent_branch_id} not found")
            root_document_id = parent.root_document_id
            base_text = str((parent.state_snapshot or {}).get("current_text", ""))
            lineage_event_count = self._lineage_event_count(session, parent)
            expected_parent_event_index = payload.get("expected_parent_event_index")
            if expected_parent_event_index is not None and int(expected_parent_event_index) != lineage_event_count:
                raise ValueError(
                    f"Optimistic concurrency violation: expected_parent_event_index={expected_parent_event_index} actual={lineage_event_count}"
                )
        else:
            if not root_document_id:
                raise ValueError("root_document_id is required when parent_branch_id is not provided")
            doc = session.scalar(select(Document).where(Document.id == root_document_id))
            if not doc:
                raise ValueError(f"Root document {root_document_id} not found")
            base_text = str((doc.provenance or {}).get("extracted_text", ""))

        drift = self._apply_event(base_text, event_type=event_type, event_payload=payload)
        new_hash = hashlib.sha256(drift.output_text.encode("utf-8")).hexdigest()

        new_branch = Branch(
            parent_branch_id=parent.id if parent else None,
            root_document_id=root_document_id,
            name=f"branch-{event_type}",
            mode=mode.upper(),
            state_snapshot={
                "current_text": drift.output_text,
                "phase": payload.get("phase", "expansion"),
                "text_hash": new_hash,
            },
            branch_version=(parent.branch_version + 1) if parent else 1,
        )
        session.add(new_branch)
        session.flush()

        current_event_index = self._next_event_index(session, new_branch.id)
        event_hash = hashlib.sha256(
            f"{new_branch.id}:{current_event_index}:{event_type}:{json.dumps(payload, sort_keys=True)}:{new_hash}".encode("utf-8")
        ).hexdigest()

        event = BranchEvent(
            branch_id=new_branch.id,
            event_index=current_event_index,
            event_type=event_type,
            event_payload=payload,
            payload_schema_version="v2",
            event_hash=event_hash,
            diff_summary=drift.diff_summary,
            result_snapshot={
                "text_hash": new_hash,
                "preview": drift.output_text[:500],
            },
        )
        session.add(event)
        session.flush()

        total_lineage_events = lineage_event_count + 1
        if total_lineage_events % 10 == 0:
            session.add(
                BranchCheckpoint(
                    branch_id=new_branch.id,
                    event_index=total_lineage_events,
                    snapshot_hash=new_hash,
                    snapshot_compressed=self._compress_snapshot(new_branch.state_snapshot),
                )
            )

        return new_branch, event

    def multi_evolve(
        self,
        session: Session,
        parent_branch_id: str | None,
        root_document_id: str | None,
        events: list[dict[str, Any]],
        mode: str,
    ) -> dict[str, Any]:
        if not events:
            raise ValueError("events must not be empty")

        created_pairs: list[tuple[Branch, BranchEvent]] = []
        current_parent_branch_id = parent_branch_id
        current_root_document_id = root_document_id

        for idx, item in enumerate(events):
            event_type = str((item or {}).get("event_type", "")).strip()
            event_payload = dict((item or {}).get("event_payload") or {})
            if not event_type:
                raise ValueError(f"events[{idx}].event_type is required")

            branch, event = self.evolve_branch(
                session=session,
                parent_branch_id=current_parent_branch_id,
                root_document_id=current_root_document_id,
                event_type=event_type,
                event_payload=event_payload,
                mode=mode,
            )
            created_pairs.append((branch, event))
            current_parent_branch_id = branch.id
            current_root_document_id = branch.root_document_id

        final_branch = created_pairs[-1][0]
        final_snapshot = dict(final_branch.state_snapshot or {})
        final_text = str(final_snapshot.get("current_text", ""))
        final_text_hash = str(final_snapshot.get("text_hash") or hashlib.sha256(final_text.encode("utf-8")).hexdigest())

        return {
            "branches": [branch for branch, _ in created_pairs],
            "events": [event for _, event in created_pairs],
            "branch_ids": [branch.id for branch, _ in created_pairs],
            "event_ids": [event.id for _, event in created_pairs],
            "final_branch_id": final_branch.id,
            "event_count": len(created_pairs),
            "final_text_hash": final_text_hash,
            "final_preview": final_text[:500],
        }

    def merge_branches(
        self,
        session: Session,
        left_branch_id: str,
        right_branch_id: str,
        strategy: str,
        *,
        mode: str = "PUBLIC",
    ) -> tuple[Branch, BranchEvent, Branch | None]:
        left_branch = session.scalar(select(Branch).where(Branch.id == left_branch_id))
        if not left_branch:
            raise LookupError(f"Left branch {left_branch_id} not found")
        right_branch = session.scalar(select(Branch).where(Branch.id == right_branch_id))
        if not right_branch:
            raise LookupError(f"Right branch {right_branch_id} not found")

        normalized_strategy = str(strategy).strip().lower()
        if normalized_strategy not in self.MERGE_STRATEGIES:
            raise ValueError(f"Unsupported merge strategy: {strategy}")

        lca = self._find_lca(session, left_branch, right_branch)
        if lca is None and left_branch.root_document_id != right_branch.root_document_id:
            raise ValueError("Branches do not share a common ancestor or root document")

        left_text, _, _ = self._replay_lineage_text(session, left_branch, use_checkpoints=True)
        right_text, _, _ = self._replay_lineage_text(session, right_branch, use_checkpoints=True)
        merged_text = self._merge_texts(left_text, right_text, normalized_strategy)
        conflict_semantics = self._build_merge_conflict_semantics(
            left_text=left_text,
            right_text=right_text,
            merged_text=merged_text,
            strategy=normalized_strategy,
        )

        merge_payload = {
            "strategy": normalized_strategy,
            "left_branch_id": left_branch_id,
            "right_branch_id": right_branch_id,
            "lca_branch_id": getattr(lca, "id", None),
            "merged_text": merged_text,
            "left_text_hash": hashlib.sha256(left_text.encode("utf-8")).hexdigest(),
            "right_text_hash": hashlib.sha256(right_text.encode("utf-8")).hexdigest(),
            "conflict_semantics": conflict_semantics,
            "seed": 0,
        }
        branch, event = self.evolve_branch(
            session=session,
            parent_branch_id=left_branch.id,
            root_document_id=left_branch.root_document_id,
            event_type="merge",
            event_payload=merge_payload,
            mode=mode,
        )
        return branch, event, lca

    def get_timeline(self, session: Session, branch_id: str) -> dict[str, Any]:
        branch = session.scalar(select(Branch).where(Branch.id == branch_id))
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")

        replay_text, lineage, events = self._replay_lineage_text(session, branch, use_checkpoints=True)

        return {
            "branch": branch,
            "events": events,
            "replay_snapshot": {
                "text_hash": hashlib.sha256(replay_text.encode("utf-8")).hexdigest(),
                "preview": replay_text[:500],
                "event_count": len(events),
            },
        }

    def get_visualization(self, session: Session, branch_id: str) -> dict[str, Any]:
        branch = session.scalar(select(Branch).where(Branch.id == branch_id))
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")

        primary_lineage = self._lineage(session, branch)
        branches_by_id: dict[str, Branch] = {node.id: node for node in primary_lineage}
        branch_events_by_id: dict[str, list[BranchEvent]] = {}
        scan_queue: list[Branch] = list(primary_lineage)
        scanned: set[str] = set()

        # Expand graph to include merge secondary parent lineages so secondary-parent
        # edges point to actual nodes in the graph.
        while scan_queue:
            node = scan_queue.pop(0)
            if node.id in scanned:
                continue
            scanned.add(node.id)
            branch_events = session.scalars(
                select(BranchEvent).where(BranchEvent.branch_id == node.id).order_by(BranchEvent.event_index, BranchEvent.created_at)
            ).all()
            branch_events_by_id[node.id] = branch_events

            for event in branch_events:
                if event.event_type != "merge":
                    continue
                right_branch_id = str((event.event_payload or {}).get("right_branch_id") or "").strip()
                if not right_branch_id:
                    continue
                right_branch = session.scalar(select(Branch).where(Branch.id == right_branch_id))
                if not right_branch:
                    continue
                for secondary_node in self._lineage(session, right_branch):
                    if secondary_node.id not in branches_by_id:
                        branches_by_id[secondary_node.id] = secondary_node
                        scan_queue.append(secondary_node)

        return evolution_visualization.assemble_visualization_graph(
            branch=branch,
            primary_lineage=primary_lineage,
            branches_by_id=branches_by_id,
            branch_events_by_id=branch_events_by_id,
        )

    def replay_branch(self, session: Session, branch_id: str) -> dict[str, Any]:
        timeline = self.get_timeline(session, branch_id)
        replay = timeline["replay_snapshot"]
        return {
            "branch_id": branch_id,
            "event_count": replay.get("event_count", 0),
            "text_hash": replay["text_hash"],
            "preview": replay["preview"],
            "replay_snapshot": replay,
        }

    def compare_branches(self, session: Session, left_branch_id: str, right_branch_id: str) -> dict[str, Any]:
        left = self.replay_branch(session, left_branch_id)
        right = self.replay_branch(session, right_branch_id)
        preview_left = left["preview"]
        preview_right = right["preview"]
        distance = self._simple_distance(preview_left, preview_right)
        return {
            "left_branch_id": left_branch_id,
            "right_branch_id": right_branch_id,
            "left_hash": left["text_hash"],
            "right_hash": right["text_hash"],
            "distance": distance,
            "same": left["text_hash"] == right["text_hash"],
            "preview_left": preview_left,
            "preview_right": preview_right,
        }

    def _lineage(self, session: Session, branch: Branch) -> list[Branch]:
        return evolution_replay.lineage(session, branch)

    def _lineage_event_count(self, session: Session, branch: Branch) -> int:
        return evolution_replay.lineage_event_count(session, branch, lineage_fn=self._lineage)

    def _latest_lineage_checkpoint(self, session: Session, lineage: list[Branch]) -> BranchCheckpoint | None:
        return evolution_replay.latest_lineage_checkpoint(session, lineage)

    def _collect_lineage_events(self, session: Session, lineage: list[Branch]) -> list[BranchEvent]:
        return evolution_replay.collect_lineage_events(session, lineage)

    def _resolve_root_text(self, session: Session, root_document_id: str | None) -> str:
        return evolution_replay.resolve_root_text(session, root_document_id)

    def _replay_lineage_text(
        self,
        session: Session,
        branch: Branch,
        *,
        use_checkpoints: bool = True,
    ) -> tuple[str, list[Branch], list[BranchEvent]]:
        return evolution_replay.replay_lineage_text(
            session,
            branch,
            use_checkpoints=use_checkpoints,
            lineage_fn=self._lineage,
            collect_events_fn=self._collect_lineage_events,
            resolve_root_text_fn=self._resolve_root_text,
            latest_checkpoint_fn=self._latest_lineage_checkpoint,
            decompress_snapshot_fn=self._decompress_snapshot,
            apply_event_fn=self._apply_event,
        )

    def _find_lca(self, session: Session, left_branch: Branch, right_branch: Branch) -> Branch | None:
        return evolution_merge.find_lca(session, left_branch, right_branch, lineage_fn=self._lineage)

    def _next_event_index(self, session: Session, branch_id: str) -> int:
        return evolution_replay.next_event_index(session, branch_id)

    def _validate_event_payload(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        return evolution_events.validate_event_payload(
            event_type,
            payload,
            phases=self.PHASES,
            merge_strategies=self.MERGE_STRATEGIES,
        )

    def _apply_event(self, text: str, event_type: str, event_payload: dict[str, Any]) -> DriftResult:
        return evolution_events.apply_event(
            text,
            event_type,
            event_payload,
            natural_map=self.NATURAL_MAP,
            reverse_natural_map=self.REVERSE_NATURAL_MAP,
            glyph_pool=self.GLYPH_POOL,
        )

    def _compress_snapshot(self, snapshot: dict[str, Any]) -> str:
        return evolution_replay.compress_snapshot(snapshot)

    def _decompress_snapshot(self, payload: str) -> dict[str, Any]:
        return evolution_replay.decompress_snapshot(payload)

    def _merge_texts(self, left_text: str, right_text: str, strategy: str) -> str:
        return evolution_merge.merge_texts(left_text, right_text, strategy)

    def _build_merge_conflict_semantics(
        self,
        *,
        left_text: str,
        right_text: str,
        merged_text: str,
        strategy: str,
    ) -> dict[str, Any]:
        return evolution_merge.build_merge_conflict_semantics(
            left_text=left_text,
            right_text=right_text,
            merged_text=merged_text,
            strategy=strategy,
        )

    def _common_prefix_chars(self, left: str, right: str) -> int:
        return evolution_merge.common_prefix_chars(left, right)

    def _common_suffix_chars(self, left: str, right: str) -> int:
        return evolution_merge.common_suffix_chars(left, right)

    def _simple_distance(self, left: str, right: str) -> int:
        return evolution_merge.simple_distance(left, right)
