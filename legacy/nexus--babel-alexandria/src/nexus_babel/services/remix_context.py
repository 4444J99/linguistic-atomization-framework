from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import Atom, Branch, Document
from nexus_babel.services.remix_types import RemixContext


def resolve_context(
    *,
    session: Session,
    role: str,
    document_id: str | None,
    branch_id: str | None,
    atom_levels: list[str],
) -> RemixContext:
    text = ""
    root_document_id: str | None = None
    branch: Branch | None = None
    document: Document | None = None
    if branch_id:
        branch = session.scalar(select(Branch).where(Branch.id == branch_id))
        if not branch:
            raise LookupError(f"{role} branch {branch_id} not found")
        text = str((branch.state_snapshot or {}).get("current_text", ""))
        root_document_id = branch.root_document_id
    if document_id:
        document = session.scalar(select(Document).where(Document.id == document_id))
        if not document:
            raise LookupError(f"{role} document {document_id} not found")
        if not text:
            text = str((document.provenance or {}).get("extracted_text", ""))
        root_document_id = root_document_id or document.id

    atoms_by_level: dict[str, list[Atom]] = {}
    if document and atom_levels:
        atoms = session.scalars(
            select(Atom)
            .where(Atom.document_id == document.id, Atom.atom_level.in_(atom_levels))
            .order_by(Atom.atom_level, Atom.ordinal, Atom.id)
        ).all()
        for atom in atoms:
            atoms_by_level.setdefault(atom.atom_level, []).append(atom)

    return {
        "role": role,
        "document_id": document_id,
        "branch_id": branch_id,
        "root_document_id": root_document_id,
        "text": text,
        "atoms_by_level": atoms_by_level,
    }


def preferred_levels_for_strategy(strategy: str) -> list[str]:
    if strategy == "thematic_blend":
        return ["sentence", "word", "paragraph", "glyph-seed", "syllable"]
    if strategy == "temporal_layer":
        return ["paragraph", "sentence", "word", "glyph-seed", "syllable"]
    if strategy == "glyph_collide":
        return ["glyph-seed", "word", "syllable", "sentence", "paragraph"]
    return ["word", "sentence", "paragraph", "glyph-seed", "syllable"]


def pick_atom_level(atoms_by_level: dict[str, list[Atom]], preferred_levels: list[str]) -> str | None:
    for level in preferred_levels:
        if atoms_by_level.get(level):
            return level
    return None


def join_atoms_for_strategy(atoms: list[Atom], atom_level: str) -> str:
    if atom_level == "paragraph":
        return "\n\n".join(a.content for a in atoms)
    if atom_level == "sentence":
        return " ".join(a.content for a in atoms)
    if atom_level == "glyph-seed":
        return "".join(a.content for a in atoms)
    return " ".join(a.content for a in atoms)


def resolve_text(session: Session, document_id: str | None, branch_id: str | None) -> str:
    if branch_id:
        branch = session.scalar(select(Branch).where(Branch.id == branch_id))
        if branch:
            return str((branch.state_snapshot or {}).get("current_text", ""))
    if document_id:
        doc = session.scalar(select(Document).where(Document.id == document_id))
        if doc:
            return str((doc.provenance or {}).get("extracted_text", ""))
    return ""


def branch_root_doc(session: Session, branch_id: str) -> str | None:
    branch = session.scalar(select(Branch).where(Branch.id == branch_id))
    return branch.root_document_id if branch else None
