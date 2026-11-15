from __future__ import annotations

from typing import Any, TypedDict

from nexus_babel.models import Atom


class RemixAtomRef(TypedDict):
    atom_id: str
    atom_level: str
    ordinal: int
    role: str


class RemixContext(TypedDict):
    role: str
    document_id: str | None
    branch_id: str | None
    root_document_id: str | None
    text: str
    atoms_by_level: dict[str, list[Atom]]


class GovernanceTraceResult(TypedDict, total=False):
    decision_id: str
    decision_trace: dict[str, Any]
