from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import delete
from sqlalchemy.orm import Session

from nexus_babel.models import Atom, Document, ProjectionLedger
from nexus_babel.services.text_utils import (
    ATOM_FILENAME_SCHEMA_VERSION,
    atomize_text_rich,
    deterministic_atom_filename,
    normalize_atom_token,
)


def create_atoms(session: Session, doc: Document, text: str, atom_levels: list[str]) -> list[dict[str, Any]]:
    session.execute(delete(Atom).where(Atom.document_id == doc.id))
    session.execute(delete(ProjectionLedger).where(ProjectionLedger.document_id == doc.id))
    rich = atomize_text_rich(text)
    atoms_to_add: list[Atom] = []
    ledger_rows: list[ProjectionLedger] = []
    payloads: list[dict[str, Any]] = []
    filename_seen: dict[tuple[str, str], int] = {}
    for level in atom_levels:
        values = rich.get(level, [])
        for idx, item in enumerate(values, start=1):
            atom_id = str(uuid4())
            if level == "glyph-seed" and hasattr(item, "character"):
                content = item.character
                metadata_json = item.model_dump()
            else:
                content = str(item)
                metadata_json = None
            normalized_token = normalize_atom_token(content)
            dedupe_key = (level, normalized_token)
            duplicate_index = filename_seen.get(dedupe_key, 0) + 1
            filename_seen[dedupe_key] = duplicate_index
            filename = deterministic_atom_filename(
                document_title=doc.title,
                atom_level=level,
                ordinal=idx,
                content=content,
                duplicate_index=duplicate_index,
            )
            atom = Atom(
                id=atom_id,
                document_id=doc.id,
                atom_level=level,
                ordinal=idx,
                content=content,
                atom_metadata={
                    "length": len(content),
                    "filename": filename,
                    "filename_schema_version": ATOM_FILENAME_SCHEMA_VERSION,
                    "normalized_token": normalized_token,
                    "duplicate_index": duplicate_index,
                },
                metadata_json=metadata_json,
            )
            atoms_to_add.append(atom)
            ledger_rows.append(
                ProjectionLedger(
                    document_id=doc.id,
                    atom_id=atom_id,
                    status="pending",
                    attempt_count=0,
                )
            )
            payloads.append(
                {
                    "id": atom_id,
                    "document_id": doc.id,
                    "atom_level": level,
                    "ordinal": idx,
                    "content": content,
                    "filename": filename,
                }
            )
    if atoms_to_add:
        session.add_all(atoms_to_add)
        session.add_all(ledger_rows)
        session.flush()
    return payloads
