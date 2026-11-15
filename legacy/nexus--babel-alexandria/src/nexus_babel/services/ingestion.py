from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.config import Settings
from nexus_babel.models import IngestJob
from nexus_babel.services import ingestion_projection
from nexus_babel.services.canonicalization import apply_canonicalization, collect_current_corpus_paths
from nexus_babel.services.hypergraph import HypergraphProjector
from nexus_babel.services.ingestion_batch_pipeline import (
    build_normalized_parse_options,
    finalize_job,
    new_batch_accumulator,
    process_ingest_path,
)
from nexus_babel.services.text_utils import resolve_atomization_selection


class IngestionService:
    def __init__(self, settings: Settings, hypergraph: HypergraphProjector):
        self.settings = settings
        self.hypergraph = hypergraph

    def ingest_batch(
        self,
        session: Session,
        source_paths: list[str],
        modalities: list[str],
        parse_options: dict[str, Any],
    ) -> dict[str, Any]:
        ingest_scope = "partial" if source_paths else "full"
        selected_paths = (
            [self._resolve_path(p) for p in source_paths]
            if source_paths
            else collect_current_corpus_paths(self.settings.corpus_root)
        )
        modality_filter = {m.lower() for m in modalities} if modalities else set()
        atom_tracks, atom_levels = resolve_atomization_selection(
            atom_tracks=parse_options.get("atom_tracks"),
            atom_levels=parse_options.get("atom_levels"),
        )
        atomize_enabled = bool(parse_options.get("atomize", True))
        force_reingest = bool(parse_options.get("force", False))
        normalized_parse_options = build_normalized_parse_options(
            parse_options=parse_options,
            atom_tracks=atom_tracks,
            atom_levels=atom_levels,
            atomize_enabled=atomize_enabled,
            force_reingest=force_reingest,
        )

        job = IngestJob(
            status="running",
            request_payload={
                "source_paths": [str(p) for p in selected_paths],
                "modalities": modalities,
                "parse_options": normalized_parse_options,
            },
        )
        session.add(job)
        session.flush()

        accumulator = new_batch_accumulator()
        for path in selected_paths:
            process_ingest_path(
                session=session,
                path=path,
                modality_filter=modality_filter,
                force_reingest=force_reingest,
                atomize_enabled=atomize_enabled,
                atom_tracks=atom_tracks,
                atom_levels=atom_levels,
                ingest_scope=ingest_scope,
                object_storage_root=self.settings.object_storage_root,
                hypergraph=self.hypergraph,
                accumulator=accumulator,
            )

        apply_canonicalization(session)
        self._apply_cross_modal_links(session, accumulator.updated_doc_ids)
        return finalize_job(job, accumulator=accumulator, ingest_scope=ingest_scope)

    def get_job_status(self, session: Session, job_id: str) -> dict[str, Any]:
        job = session.scalar(select(IngestJob).where(IngestJob.id == job_id))
        if not job:
            raise ValueError(f"Ingest job {job_id} not found")

        summary = job.result_summary or {}
        return {
            "ingest_job_id": job.id,
            "status": job.status,
            "files": summary.get("files", []),
            "errors": job.errors or [],
            "documents_ingested": summary.get("documents_ingested", 0),
            "atoms_created": summary.get("atoms_created", 0),
            "documents_unchanged": summary.get("documents_unchanged", 0),
            "provenance_digest": summary.get("provenance_digest", ""),
            "ingest_scope": summary.get("ingest_scope", "partial"),
            "warnings": summary.get("warnings", []),
        }

    def _resolve_path(self, path: str) -> Path:
        root = self.settings.corpus_root.resolve()
        p = Path(path)
        candidate = p.resolve() if p.is_absolute() else (root / p).resolve()
        if not self._is_within_root(candidate, root):
            raise ValueError(f"Path escapes corpus_root and is not allowed: {path}")
        return candidate

    def _is_within_root(self, candidate: Path, root: Path) -> bool:
        try:
            candidate.relative_to(root)
            return True
        except ValueError:
            return False

    def _apply_cross_modal_links(self, session: Session, updated_doc_ids: set[str]) -> None:
        ingestion_projection.apply_cross_modal_links(session, updated_doc_ids=updated_doc_ids)
