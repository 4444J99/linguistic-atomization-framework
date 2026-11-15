from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import Document


def upsert_document(
    *,
    session: Session,
    path: Path,
    modality: str,
    checksum: str,
    conflict: bool,
    conflict_reason: str | None,
    extracted_text: str,
    raw_storage_path: Path,
    segments: dict[str, Any],
) -> Document:
    resolved = str(path.resolve())
    doc = session.scalar(select(Document).where(Document.path == resolved))
    if not doc:
        doc = Document(
            path=resolved,
            title=path.name,
            modality=modality,
            checksum=checksum,
            size_bytes=path.stat().st_size,
            conflict_flag=conflict,
            conflict_reason=conflict_reason,
            ingest_status="conflict" if conflict else "parsed",
            ingested=not conflict,
            provenance={},
        )
        session.add(doc)
        session.flush()
    else:
        doc.title = path.name
        doc.modality = modality
        doc.checksum = checksum
        doc.size_bytes = path.stat().st_size
        doc.conflict_flag = conflict
        doc.conflict_reason = conflict_reason
        doc.ingest_status = "conflict" if conflict else "parsed"
        doc.ingested = not conflict

    doc.provenance = {
        **(doc.provenance or {}),
        "extracted_text": extracted_text,
        "segments": segments,
        "checksum": checksum,
        "raw_storage_path": str(raw_storage_path),
        "conflict": conflict,
        "conflict_reason": conflict_reason,
    }
    return doc


def store_raw_payload(*, source_path: Path, object_storage_root: Path, checksum: str) -> Path:
    ext = source_path.suffix
    bucket = object_storage_root
    bucket.mkdir(parents=True, exist_ok=True)
    destination = bucket / f"{checksum}{ext}"
    if not destination.exists():
        shutil.copy2(source_path, destination)
    return destination
