from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import Document, IngestJob
from nexus_babel.services import ingestion_projection
from nexus_babel.services.hypergraph import HypergraphProjector
from nexus_babel.services.ingestion_atoms import create_atoms
from nexus_babel.services.ingestion_documents import store_raw_payload, upsert_document
from nexus_babel.services.ingestion_media import (
    AUDIO_EXT,
    IMAGE_EXT,
    PDF_EXT,
    TEXT_EXT,
    derive_modality_status,
    derive_text_segments,
    detect_modality,
    extract_audio_metadata,
    extract_image_metadata,
    extract_pdf_text,
    pdf_page_count,
)
from nexus_babel.services.ingestion_types import IngestionBatchAccumulator, NormalizedParseOptions
from nexus_babel.services.text_utils import ATOM_FILENAME_SCHEMA_VERSION, has_conflict_markers, sha256_file


def new_batch_accumulator() -> IngestionBatchAccumulator:
    return IngestionBatchAccumulator()


def build_normalized_parse_options(
    *,
    parse_options: dict[str, Any],
    atom_tracks: list[str],
    atom_levels: list[str],
    atomize_enabled: bool,
    force_reingest: bool,
) -> NormalizedParseOptions:
    return {
        **parse_options,
        "atom_tracks": atom_tracks,
        "atom_levels": atom_levels,
        "atomize": atomize_enabled,
        "force": force_reingest,
    }


def process_ingest_path(
    *,
    session: Session,
    path: Path,
    modality_filter: set[str],
    force_reingest: bool,
    atomize_enabled: bool,
    atom_tracks: list[str],
    atom_levels: list[str],
    ingest_scope: str,
    object_storage_root: Path,
    hypergraph: HypergraphProjector,
    accumulator: IngestionBatchAccumulator,
) -> None:
    try:
        if not path.exists() or not path.is_file():
            accumulator.files.append({"path": str(path), "status": "error", "error": "File not found", "document_id": None})
            accumulator.errors.append(f"File not found: {path}")
            return

        modality = detect_modality(path)
        if modality_filter and modality not in modality_filter:
            accumulator.files.append({"path": str(path), "status": "skipped", "error": None, "document_id": None})
            return

        checksum = sha256_file(path)
        accumulator.checksums.append(checksum)
        existing = session.scalar(select(Document).where(Document.path == str(path.resolve())))
        if existing and existing.checksum == checksum and existing.ingested and not force_reingest:
            existing.ingest_status = "unchanged"
            existing.modality_status = {
                **(existing.modality_status or {}),
                existing.modality: "complete",
            }
            accumulator.files.append({"path": str(path), "status": "unchanged", "document_id": existing.id, "error": None})
            accumulator.documents_unchanged += 1
            return

        raw_storage_path = store_raw_payload(source_path=path, object_storage_root=object_storage_root, checksum=checksum)

        extracted_text = ""
        segments: dict[str, Any] = {}
        conflict = False
        conflict_reason: str | None = None

        if path.suffix.lower() in TEXT_EXT:
            extracted_text = path.read_text(encoding="utf-8", errors="ignore")
            conflict = has_conflict_markers(extracted_text)
            if conflict:
                conflict_reason = "Conflict markers detected"
            segments = {
                "line_count": extracted_text.count("\n") + 1,
                "char_count": len(extracted_text),
            }
            segments.update(derive_text_segments(extracted_text, is_pdf=False))
        elif path.suffix.lower() in PDF_EXT:
            extracted_text = extract_pdf_text(path)
            segments = {
                "char_count": len(extracted_text),
                "page_count": pdf_page_count(path),
            }
            segments.update(derive_text_segments(extracted_text, is_pdf=True))
        elif path.suffix.lower() in IMAGE_EXT:
            segments = extract_image_metadata(path)
        elif path.suffix.lower() in AUDIO_EXT:
            segments = extract_audio_metadata(path)

        doc = upsert_document(
            session=session,
            path=path,
            modality=modality,
            checksum=checksum,
            conflict=conflict,
            conflict_reason=conflict_reason,
            extracted_text=extracted_text,
            raw_storage_path=raw_storage_path,
            segments=segments,
        )

        if conflict:
            doc.conflict_reason = conflict_reason
            doc.modality_status = {doc.modality: "failed"}
            accumulator.files.append({"path": str(path), "status": "conflict", "document_id": doc.id, "error": conflict_reason})
            return

        atom_payloads: list[dict[str, Any]] = []
        if atomize_enabled and extracted_text:
            atom_payloads = create_atoms(session, doc, extracted_text, atom_levels)
            accumulator.atoms_created += len(atom_payloads)
        doc.atom_count = len(atom_payloads)
        doc.graph_projected_atom_count = 0
        doc.graph_projection_status = "pending"

        projection_warning: str | None = None
        hypergraph_ids: dict[str, Any] = {}
        try:
            hypergraph_ids = hypergraph.project_document(
                document_id=doc.id,
                document_payload={"path": doc.path, "modality": doc.modality, "checksum": doc.checksum},
                atoms=atom_payloads,
            )
            doc.graph_projected_atom_count = len(atom_payloads)
            doc.graph_projection_status = "complete" if doc.graph_projected_atom_count == doc.atom_count else "partial"
            ingestion_projection.update_projection_ledger(
                session,
                document_id=doc.id,
                atom_payloads=atom_payloads,
                status="projected",
            )
        except Exception as graph_exc:  # pragma: no cover - fallback path
            projection_warning = f"Graph projection failed: {graph_exc}"
            doc.graph_projection_status = "failed"
            ingestion_projection.update_projection_ledger(
                session,
                document_id=doc.id,
                atom_payloads=atom_payloads,
                status="failed",
                error=projection_warning,
            )
            accumulator.warnings.append(f"{path}: {projection_warning}")

        doc.provenance = {
            **(doc.provenance or {}),
            "raw_storage_path": str(raw_storage_path),
            "segments": segments,
            "hypergraph": hypergraph_ids,
            "ingest_scope": ingest_scope,
            "atomization": {
                "atom_tracks": atom_tracks,
                "active_atom_levels": atom_levels,
                "filename_schema_version": ATOM_FILENAME_SCHEMA_VERSION,
            },
        }
        doc.modality_status = {
            **(doc.modality_status or {}),
            doc.modality: derive_modality_status(doc.modality, projection_warning, segments),
        }
        doc.provider_summary = {
            **(doc.provider_summary or {}),
            "ingestion_provider": "builtin",
            "projection_provider": "neo4j" if hypergraph.enabled else "local_cache",
        }
        doc.ingested = True
        doc.ingest_status = "ingested" if not projection_warning else "ingested_with_warnings"
        accumulator.updated_doc_ids.add(doc.id)

        accumulator.documents_ingested += 1
        accumulator.files.append(
            {
                "path": str(path),
                "status": doc.ingest_status,
                "document_id": doc.id,
                "error": projection_warning,
            }
        )
    except Exception as exc:  # pragma: no cover - defensive
        accumulator.errors.append(str(exc))
        accumulator.files.append({"path": str(path), "status": "error", "document_id": None, "error": str(exc)})


def finalize_job(
    job: IngestJob,
    *,
    accumulator: IngestionBatchAccumulator,
    ingest_scope: str,
) -> dict[str, Any]:
    digest = (
        hashlib.sha256("\n".join(sorted(accumulator.checksums)).encode("utf-8")).hexdigest()
        if accumulator.checksums
        else ""
    )
    summary = {
        "files": accumulator.files,
        "documents_ingested": accumulator.documents_ingested,
        "documents_unchanged": accumulator.documents_unchanged,
        "atoms_created": accumulator.atoms_created,
        "provenance_digest": digest,
        "ingest_scope": ingest_scope,
        "warnings": accumulator.warnings,
    }
    job.status = "completed" if not accumulator.errors else "completed_with_errors"
    job.result_summary = summary
    job.errors = accumulator.errors
    return {"job": job, **summary, "errors": accumulator.errors, "warnings": accumulator.warnings}
