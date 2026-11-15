from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from nexus_babel.models import Document, DocumentVariant


def _normalize_stem(path: str) -> str:
    stem = Path(path).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return stem


def _is_semantic_rlos_equivalent(path: str) -> bool:
    p = path.lower()
    return "theoria linguae machina comprehensive design document" in p or "nexus_bable-alexandria" in p


def apply_canonicalization(session: Session) -> None:
    documents = session.scalars(select(Document).where(Document.ingested.is_(True))).all()
    if not documents:
        session.execute(delete(DocumentVariant))
        return

    # Deterministic materialization from authoritative corpus snapshot.
    session.execute(delete(DocumentVariant))

    # Known semantic equivalence group for duplicated long-form RLOS specs.
    semantic_group = [doc for doc in documents if _is_semantic_rlos_equivalent(doc.path)]

    for doc in semantic_group:
        session.add(
            DocumentVariant(
                document_id=doc.id,
                variant_group="rlos_spec_v1_equivalent",
                variant_type="semantic_equivalence",
                related_document_id=None,
            )
        )

    # Pair sibling representations by normalized stem across extensions.
    groups: dict[str, list[Document]] = defaultdict(list)
    for doc in documents:
        groups[_normalize_stem(doc.path)].append(doc)

    for group_name, group_docs in groups.items():
        if len(group_docs) < 2:
            continue
        group_id = f"sibling::{group_name}"
        for doc in group_docs:
            for related in group_docs:
                if related.id == doc.id:
                    continue
                session.add(
                    DocumentVariant(
                        document_id=doc.id,
                        variant_group=group_id,
                        variant_type="sibling_representation",
                        related_document_id=related.id,
                    )
                )


def collect_current_corpus_paths(root: Path) -> list[Path]:
    supported = {
        ".md",
        ".pdf",
        ".txt",
        ".yaml",
        ".yml",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".wav",
        ".mp3",
        ".flac",
    }
    paths: list[Path] = []
    skip_dirs = {".git", ".venv", "__pycache__", "object_storage", ".pytest_cache"}
    paths: list[Path] = []
    for child in sorted(root.rglob("*")):
        if any(part in skip_dirs for part in child.parts):
            continue
        if not child.is_file():
            continue
        if child.name.startswith("."):
            continue
        if child.suffix.lower() in supported:
            paths.append(child)
    return paths


def get_document_text(session: Session, document_id: str) -> str:
    doc = session.scalar(select(Document).where(Document.id == document_id))
    if not doc:
        return ""
    return str((doc.provenance or {}).get("extracted_text", ""))
