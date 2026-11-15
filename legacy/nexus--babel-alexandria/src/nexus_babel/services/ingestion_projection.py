from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import Document, ProjectionLedger


def update_projection_ledger(
    session: Session,
    *,
    document_id: str,
    atom_payloads: list[dict[str, Any]],
    status: str,
    error: str | None = None,
) -> None:
    if not atom_payloads:
        return
    atom_ids = [payload["id"] for payload in atom_payloads]
    rows = session.scalars(
        select(ProjectionLedger).where(
            ProjectionLedger.document_id == document_id,
            ProjectionLedger.atom_id.in_(atom_ids),
        )
    ).all()
    for row in rows:
        row.status = status
        row.attempt_count = int(row.attempt_count) + 1
        row.last_error = error


def apply_cross_modal_links(session: Session, *, updated_doc_ids: set[str]) -> None:
    if not updated_doc_ids:
        return
    docs = session.scalars(select(Document).where(Document.id.in_(updated_doc_ids))).all()
    if not docs:
        return

    groups: dict[str, list[Document]] = defaultdict(list)
    for doc in docs:
        stem = Path(doc.path).stem.lower()
        groups[stem].append(doc)

    for group in groups.values():
        text_docs = [doc for doc in group if doc.modality in {"text", "pdf"}]
        media_docs = [doc for doc in group if doc.modality in {"image", "audio"}]
        if not text_docs or not media_docs:
            continue
        for text_doc in text_docs:
            links = []
            for media_doc in media_docs:
                links.append(
                    {
                        "target_document_id": media_doc.id,
                        "target_modality": media_doc.modality,
                        "text_anchor": {"start": 0, "end": min(120, len(str((text_doc.provenance or {}).get("extracted_text", ""))))},
                        "target_anchor": {"region": "full" if media_doc.modality == "image" else "0.0-1.0"},
                    }
                )
            text_doc.provenance = {**(text_doc.provenance or {}), "cross_modal_links": links}
        for media_doc in media_docs:
            links = []
            for text_doc in text_docs:
                links.append(
                    {
                        "target_document_id": text_doc.id,
                        "target_modality": text_doc.modality,
                        "target_anchor": {"start": 0, "end": 120},
                    }
                )
            media_doc.provenance = {**(media_doc.provenance or {}), "cross_modal_links": links}
