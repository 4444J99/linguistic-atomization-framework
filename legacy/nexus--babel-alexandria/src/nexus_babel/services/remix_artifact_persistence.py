from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from nexus_babel.models import RemixArtifact, RemixSourceLink


def build_source_links(
    *,
    remix_artifact_id: str,
    source_ctx: dict[str, Any],
    target_ctx: dict[str, Any],
    source_atom_refs: list[dict[str, Any]],
) -> list[RemixSourceLink]:
    source_refs = [row for row in source_atom_refs if row.get("role") == "source"]
    target_refs = [row for row in source_atom_refs if row.get("role") == "target"]
    source_level = source_refs[0]["atom_level"] if source_refs else None
    target_level = target_refs[0]["atom_level"] if target_refs else None
    return [
        RemixSourceLink(
            remix_artifact_id=remix_artifact_id,
            role="source",
            document_id=source_ctx.get("document_id"),
            branch_id=source_ctx.get("branch_id"),
            atom_level=source_level,
            atom_count=len(source_refs),
            atom_refs=source_refs,
        ),
        RemixSourceLink(
            remix_artifact_id=remix_artifact_id,
            role="target",
            document_id=target_ctx.get("document_id"),
            branch_id=target_ctx.get("branch_id"),
            atom_level=target_level,
            atom_count=len(target_refs),
            atom_refs=target_refs,
        ),
    ]


def create_artifact(
    session: Session,
    *,
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
    source_ctx: dict[str, Any],
    target_ctx: dict[str, Any],
    source_atom_refs: list[dict[str, Any]],
) -> RemixArtifact:
    artifact = RemixArtifact(
        source_document_id=source_ctx.get("document_id"),
        source_branch_id=source_ctx.get("branch_id"),
        target_document_id=target_ctx.get("document_id"),
        target_branch_id=target_ctx.get("branch_id"),
        strategy=strategy,
        seed=seed,
        mode=mode.upper(),
        remixed_text=remixed_text,
        text_hash=text_hash,
        rng_seed_hex=rng_seed_hex,
        payload_hash=payload_hash,
        create_branch=create_branch,
        governance_decision_id=governance_decision_id,
        artifact_metadata={"governance": {"decision_trace": governance_trace}},
    )
    session.add(artifact)
    session.flush()

    session.add_all(
        build_source_links(
            remix_artifact_id=artifact.id,
            source_ctx=source_ctx,
            target_ctx=target_ctx,
            source_atom_refs=source_atom_refs,
        )
    )
    session.flush()
    return artifact
