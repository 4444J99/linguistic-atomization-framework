from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from nexus_babel.api.deps import open_session, require_auth
from nexus_babel.api.errors import to_http_exception
from nexus_babel.schemas import (
    IngestBatchRequest,
    IngestBatchResponse,
    IngestFileStatus,
    IngestJobResponse,
    SeedProvisionRequest,
    SeedProvisionResponse,
    SeedTextEntry,
    SeedTextListResponse,
)
from nexus_babel.services.auth import AuthContext

router = APIRouter()


@router.post("/ingest/batch", response_model=IngestBatchResponse, dependencies=[Depends(require_auth("operator"))])
def ingest_batch(payload: IngestBatchRequest, request: Request) -> IngestBatchResponse:
    session = open_session(request)
    try:
        parse_options = dict(payload.parse_options or {})
        if payload.atom_tracks is not None:
            parse_options["atom_tracks"] = list(payload.atom_tracks)
        result = request.app.state.ingestion_service.ingest_batch(
            session=session,
            source_paths=payload.source_paths,
            modalities=payload.modalities,
            parse_options=parse_options,
        )
        session.commit()
        return IngestBatchResponse(
            ingest_job_id=result["job"].id,
            documents_ingested=result["documents_ingested"],
            documents_unchanged=result.get("documents_unchanged", 0),
            atoms_created=result["atoms_created"],
            provenance_digest=result["provenance_digest"],
            ingest_scope=result["ingest_scope"],
            warnings=result["warnings"],
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise to_http_exception(exc, default_status=400) from exc
    finally:
        session.close()


@router.get("/ingest/jobs/{job_id}", response_model=IngestJobResponse, dependencies=[Depends(require_auth("viewer"))])
def ingest_job(job_id: str, request: Request) -> IngestJobResponse:
    session = open_session(request)
    try:
        result = request.app.state.ingestion_service.get_job_status(session, job_id)
        return IngestJobResponse(
            ingest_job_id=result["ingest_job_id"],
            status=result["status"],
            files=[IngestFileStatus(**item) for item in result["files"]],
            errors=result["errors"],
            documents_ingested=result["documents_ingested"],
            documents_unchanged=result.get("documents_unchanged", 0),
            atoms_created=result["atoms_created"],
            provenance_digest=result["provenance_digest"],
            ingest_scope=result["ingest_scope"],
            warnings=result["warnings"],
        )
    except Exception as exc:
        raise to_http_exception(exc, default_status=404) from exc
    finally:
        session.close()


@router.get("/corpus/seeds", response_model=SeedTextListResponse, dependencies=[Depends(require_auth("viewer"))])
def list_seed_texts(request: Request) -> SeedTextListResponse:
    seeds = request.app.state.seed_corpus_service.list_seed_texts()
    return SeedTextListResponse(seeds=[SeedTextEntry(**s) for s in seeds])


@router.post("/corpus/seed", response_model=SeedProvisionResponse)
def provision_seed_text(
    payload: SeedProvisionRequest,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("admin")),
) -> SeedProvisionResponse:
    session = open_session(request)
    try:
        _ = auth_context
        result = request.app.state.seed_corpus_service.provision_seed_text(payload.title)
        doc_id = None
        if result.get("local_path") and result["status"] in ("provisioned", "already_provisioned"):
            local_path = Path(result["local_path"])
            if local_path.exists():
                ingest_result = request.app.state.ingestion_service.ingest_batch(
                    session=session,
                    source_paths=[str(local_path)],
                    modalities=["text"],
                    parse_options={},
                )
                session.commit()
                files = ingest_result.get("files", [])
                if files:
                    doc_id = files[0].get("document_id")
        return SeedProvisionResponse(
            title=result["title"],
            status=result["status"],
            local_path=result.get("local_path"),
            document_id=doc_id,
        )
    except Exception as exc:
        session.rollback()
        raise to_http_exception(exc, default_status=400) from exc
    finally:
        session.close()
