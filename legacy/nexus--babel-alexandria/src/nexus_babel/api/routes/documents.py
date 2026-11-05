from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select

from nexus_babel.api.deps import open_session, require_auth
from nexus_babel.api.errors import NotFoundError
from nexus_babel.models import Document

router = APIRouter()


@router.get("/hypergraph/documents/{document_id}/integrity", dependencies=[Depends(require_auth("viewer"))])
def hypergraph_integrity(document_id: str, request: Request) -> dict:
    session = open_session(request)
    try:
        doc = session.get(Document, document_id)
        if not doc:
            raise NotFoundError("Document not found")
        return request.app.state.hypergraph.integrity_for_document(doc)
    finally:
        session.close()


@router.get("/documents", dependencies=[Depends(require_auth("viewer"))])
def list_documents(request: Request) -> dict:
    session = open_session(request)
    try:
        docs = session.scalars(select(Document).order_by(Document.created_at)).all()
        return {
            "documents": [
                {
                    "id": d.id,
                    "path": d.path,
                    "modality": d.modality,
                    "ingested": d.ingested,
                    "ingest_status": d.ingest_status,
                    "conflict_flag": d.conflict_flag,
                    "conflict_reason": d.conflict_reason,
                    "atom_count": d.atom_count,
                    "graph_projected_atom_count": d.graph_projected_atom_count,
                    "graph_projection_status": d.graph_projection_status,
                    "modality_status": d.modality_status,
                    "provider_summary": d.provider_summary,
                }
                for d in docs
            ]
        }
    finally:
        session.close()


@router.get("/documents/{document_id}", dependencies=[Depends(require_auth("viewer"))])
def get_document(document_id: str, request: Request) -> dict:
    session = open_session(request)
    try:
        doc = session.get(Document, document_id)
        if not doc:
            raise NotFoundError("Document not found")
        return {
            "id": doc.id,
            "path": doc.path,
            "title": doc.title,
            "modality": doc.modality,
            "ingested": doc.ingested,
            "ingest_status": doc.ingest_status,
            "conflict_flag": doc.conflict_flag,
            "conflict_reason": doc.conflict_reason,
            "atom_count": doc.atom_count,
            "graph_projected_atom_count": doc.graph_projected_atom_count,
            "graph_projection_status": doc.graph_projection_status,
            "modality_status": doc.modality_status,
            "provider_summary": doc.provider_summary,
            "provenance": doc.provenance,
        }
    finally:
        session.close()


@router.get("/hypergraph/query", dependencies=[Depends(require_auth("viewer"))])
def hypergraph_query(
    request: Request,
    document_id: str | None = Query(default=None),
    node_id: str | None = Query(default=None),
    relationship_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict:
    return request.app.state.hypergraph.query(
        document_id=document_id,
        node_id=node_id,
        relationship_type=relationship_type,
        limit=limit,
    )
