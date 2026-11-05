"""Remix/recombination engine for ARC4N Living Digital Canon."""

from __future__ import annotations

import random
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nexus_babel.models import Branch, BranchEvent, RemixArtifact
from nexus_babel.services import remix_artifact_persistence, remix_artifact_serialization, remix_strategies
from nexus_babel.services.evolution import EvolutionService
from nexus_babel.services.governance import GovernanceService
from nexus_babel.services.remix_compose import compose_text
from nexus_babel.services.remix_context import branch_root_doc, resolve_context, resolve_text
from nexus_babel.services.remix_hashing import build_payload_hash, build_remix_rng, sha256_text
from nexus_babel.services.remix_types import RemixContext


class RemixService:
    def __init__(self, evolution_service: EvolutionService, governance_service: GovernanceService | None = None):
        self.evolution = evolution_service
        self.governance = governance_service

    def remix(
        self,
        session: Session,
        source_document_id: str | None,
        source_branch_id: str | None,
        target_document_id: str | None,
        target_branch_id: str | None,
        strategy: str,
        seed: int,
        mode: str,
    ) -> tuple[Branch, BranchEvent]:
        result = self.compose(
            session=session,
            source_document_id=source_document_id,
            source_branch_id=source_branch_id,
            target_document_id=target_document_id,
            target_branch_id=target_branch_id,
            strategy=strategy,
            seed=seed,
            mode=mode,
            atom_levels=[],
            create_branch=True,
            persist_artifact=False,
        )
        branch = result.get("branch")
        event = result.get("event")
        if not isinstance(branch, Branch) or not isinstance(event, BranchEvent):  # pragma: no cover - defensive
            raise RuntimeError("Legacy remix flow expected branch + event result")
        return branch, event

    def compose(
        self,
        *,
        session: Session,
        source_document_id: str | None,
        source_branch_id: str | None,
        target_document_id: str | None,
        target_branch_id: str | None,
        strategy: str,
        seed: int,
        mode: str,
        atom_levels: list[str] | None = None,
        create_branch: bool = True,
        persist_artifact: bool = True,
    ) -> dict[str, Any]:
        atom_levels = atom_levels or []
        source_ctx = resolve_context(
            session=session,
            role="source",
            document_id=source_document_id,
            branch_id=source_branch_id,
            atom_levels=atom_levels,
        )
        target_ctx = resolve_context(
            session=session,
            role="target",
            document_id=target_document_id,
            branch_id=target_branch_id,
            atom_levels=atom_levels,
        )

        source_text = source_ctx["text"]
        target_text = target_ctx["text"]
        if not source_text or not target_text:
            raise ValueError("Both source and target must resolve to non-empty text")

        rng, rng_seed_hex = build_remix_rng(
            strategy=strategy,
            seed=int(seed),
            source_text=source_text,
            target_text=target_text,
            atom_levels=atom_levels,
        )

        remixed, source_atom_refs = compose_text(
            source_text=source_text,
            target_text=target_text,
            strategy=strategy,
            rng=rng,
            source_ctx=source_ctx,
            target_ctx=target_ctx,
            atom_levels=atom_levels,
        )
        text_hash = sha256_text(remixed)
        payload_hash = build_payload_hash(
            strategy=strategy,
            seed=int(seed),
            mode=mode,
            source_document_id=source_document_id,
            source_branch_id=source_branch_id,
            target_document_id=target_document_id,
            target_branch_id=target_branch_id,
            atom_levels=atom_levels,
            text_hash=text_hash,
        )

        governance_result: dict[str, Any] = {}
        governance_decision_id: str | None = None
        if self.governance is not None:
            governance_result = self.governance.evaluate(session=session, candidate_output=remixed, mode=mode)
            governance_decision_id = governance_result.get("decision_id")

        artifact: RemixArtifact | None = None
        if persist_artifact:
            artifact = self._create_artifact(
                session=session,
                strategy=strategy,
                seed=int(seed),
                mode=mode,
                remixed_text=remixed,
                text_hash=text_hash,
                rng_seed_hex=rng_seed_hex,
                payload_hash=payload_hash,
                create_branch=create_branch,
                governance_decision_id=governance_decision_id,
                governance_trace=(governance_result.get("decision_trace") or {}),
                source_ctx=source_ctx,
                target_ctx=target_ctx,
                source_atom_refs=source_atom_refs,
            )

        branch: Branch | None = None
        event: BranchEvent | None = None
        if create_branch:
            root_doc_id = source_document_id or source_ctx.get("root_document_id")
            branch, event = self.evolution.evolve_branch(
                session=session,
                parent_branch_id=source_branch_id,
                root_document_id=root_doc_id,
                event_type="remix",
                event_payload={
                    "seed": int(seed),
                    "strategy": strategy,
                    "remixed_text": remixed,
                    "remix_payload_hash": payload_hash,
                    "source_document_id": source_document_id,
                    "target_document_id": target_document_id,
                    "source_branch_id": source_branch_id,
                    "target_branch_id": target_branch_id,
                    "atom_levels": atom_levels,
                    "remix_artifact_id": artifact.id if artifact else None,
                },
                mode=mode,
            )
            if artifact is not None:
                artifact.branch_id = branch.id
                artifact.branch_event_id = event.id
                artifact.lineage_graph_refs = self._build_lineage_graph_refs(
                    source_ctx=source_ctx,
                    target_ctx=target_ctx,
                    branch_id=branch.id,
                    branch_event_id=event.id,
                    remix_artifact_id=artifact.id,
                )
        elif artifact is not None:
            artifact.lineage_graph_refs = self._build_lineage_graph_refs(
                source_ctx=source_ctx,
                target_ctx=target_ctx,
                branch_id=None,
                branch_event_id=None,
                remix_artifact_id=artifact.id,
            )

        return {
            "strategy": strategy,
            "seed": int(seed),
            "mode": mode.upper(),
            "remixed_text": remixed,
            "text_hash": text_hash,
            "payload_hash": payload_hash,
            "rng_seed_hex": rng_seed_hex,
            "source_atom_refs": source_atom_refs,
            "remix_artifact": artifact,
            "governance_result": governance_result,
            "branch": branch,
            "event": event,
        }

    def get_remix_artifact(self, session: Session, remix_artifact_id: str) -> dict[str, Any]:
        artifact = session.scalar(select(RemixArtifact).where(RemixArtifact.id == remix_artifact_id))
        if not artifact:
            raise LookupError(f"Remix artifact {remix_artifact_id} not found")
        return self._artifact_to_dict(artifact)

    def list_remix_artifacts(self, session: Session, *, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        total = int(session.scalar(select(func.count(RemixArtifact.id))) or 0)
        artifacts = session.scalars(
            select(RemixArtifact).order_by(RemixArtifact.created_at.desc(), RemixArtifact.id.desc()).offset(offset).limit(limit)
        ).all()
        return {
            "items": [self._artifact_summary(a) for a in artifacts],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    def _artifact_summary(self, artifact: RemixArtifact) -> dict[str, Any]:
        return remix_artifact_serialization.artifact_summary(artifact)

    def _artifact_to_dict(self, artifact: RemixArtifact) -> dict[str, Any]:
        return remix_artifact_serialization.artifact_to_dict(artifact)

    def _create_artifact(
        self,
        *,
        session: Session,
        strategy: str,
        seed: int,
        mode: str,
        remixed_text: str,
        text_hash: str,
        rng_seed_hex: str,
        payload_hash: str,
        create_branch: bool,
        governance_decision_id: str | None,
        governance_trace: dict[str, Any],
        source_ctx: RemixContext,
        target_ctx: RemixContext,
        source_atom_refs: list[dict[str, Any]],
    ) -> RemixArtifact:
        return remix_artifact_persistence.create_artifact(
            session,
            strategy=strategy,
            seed=seed,
            mode=mode,
            remixed_text=remixed_text,
            text_hash=text_hash,
            rng_seed_hex=rng_seed_hex,
            payload_hash=payload_hash,
            create_branch=create_branch,
            governance_decision_id=governance_decision_id,
            governance_trace=governance_trace,
            source_ctx=source_ctx,
            target_ctx=target_ctx,
            source_atom_refs=source_atom_refs,
        )

    def _build_lineage_graph_refs(
        self,
        *,
        source_ctx: RemixContext,
        target_ctx: RemixContext,
        branch_id: str | None,
        branch_event_id: str | None,
        remix_artifact_id: str,
    ) -> dict[str, Any]:
        return remix_artifact_serialization.build_lineage_graph_refs(
            source_ctx=source_ctx,
            target_ctx=target_ctx,
            branch_id=branch_id,
            branch_event_id=branch_event_id,
            remix_artifact_id=remix_artifact_id,
        )

    def _resolve_text(self, session: Session, document_id: str | None, branch_id: str | None) -> str:
        return resolve_text(session, document_id, branch_id)

    def _branch_root_doc(self, session: Session, branch_id: str) -> str | None:
        return branch_root_doc(session, branch_id)

    def _apply_strategy(self, source: str, target: str, strategy: str, rng: random.Random) -> str:
        return remix_strategies.apply_strategy(source=source, target=target, strategy=strategy, rng=rng)

    # Backward-compatible wrappers used by existing tests and internal callers.
    def _interleave(self, source: str, target: str) -> str:
        return remix_strategies.interleave(source, target)

    def _thematic_blend(self, source: str, target: str, rng: random.Random) -> str:
        return remix_strategies.thematic_blend(source, target, rng)

    def _temporal_layer(self, source: str, target: str, rng: random.Random) -> str:
        return remix_strategies.temporal_layer(source, target, rng)

    def _glyph_collide(self, source: str, target: str, rng: random.Random) -> str:
        return remix_strategies.glyph_collide(source, target, rng)
