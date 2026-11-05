from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict


class IngestFileResult(TypedDict):
    path: str
    status: str
    error: str | None
    document_id: str | None


class NormalizedParseOptions(TypedDict, total=False):
    atom_tracks: list[str]
    atom_levels: list[str]
    atomize: bool
    force: bool


@dataclass
class IngestionBatchAccumulator:
    files: list[IngestFileResult] = field(default_factory=list)
    documents_ingested: int = 0
    atoms_created: int = 0
    documents_unchanged: int = 0
    checksums: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    updated_doc_ids: set[str] = field(default_factory=set)
