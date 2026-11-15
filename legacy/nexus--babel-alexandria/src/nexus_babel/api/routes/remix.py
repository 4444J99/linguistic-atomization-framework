from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from nexus_babel.api.deps import enforce_mode, open_session, require_auth
from nexus_babel.api.errors import to_http_exception
from nexus_babel.schemas import (
    RemixArtifactListItem,
    RemixArtifactListResponse,
    RemixArtifactResponse,
    RemixAtomRef,
    RemixComposeRequest,
    RemixComposeResponse,
    RemixRequest,
    RemixResponse,
)
from nexus_babel.services.auth import AuthContext

router = APIRouter()


@router.post("/remix/compose", response_model=RemixComposeResponse)
def remix_compose(
    payload: RemixComposeRequest,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("operator")),
) -> RemixComposeResponse:
    session = open_session(request)
    try:
        enforce_mode(request, auth_context, payload.mode)
        result = request.app.state.remix_service.compose(
            session=session,
            source_document_id=payload.source_document_id,
            source_branch_id=payload.source_branch_id,
            target_document_id=payload.target_document_id,
            target_branch_id=payload.target_branch_id,
            strategy=payload.strategy,
            seed=payload.seed,
            mode=payload.mode,
            atom_levels=list(payload.atom_levels or []),
            create_branch=payload.create_branch,
            persist_artifact=payload.persist_artifact,
        )
        session.commit()
        artifact = result.get("remix_artifact")
        branch = result.get("branch")
        event = result.get("event")
        gov = result.get("governance_result") or {}
        return RemixComposeResponse(
            strategy=result["strategy"],
            seed=result["seed"],
            mode=result["mode"],
            remixed_text=result["remixed_text"],
            text_hash=result["text_hash"],
            payload_hash=result["payload_hash"],
            source_atom_refs=[RemixAtomRef(**row) for row in result.get("source_atom_refs", [])],
            remix_artifact_id=getattr(artifact, "id", None),
            governance_decision_id=gov.get("decision_id"),
            governance_trace=gov.get("decision_trace") or {},
            create_branch=payload.create_branch,
            new_branch_id=getattr(branch, "id", None),
            event_id=getattr(event, "id", None),
            diff_summary=(event.diff_summary if event is not None else {}),
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        default_status = 404 if isinstance(exc, LookupError) else 400
        raise to_http_exception(exc, default_status=default_status) from exc
    finally:
        session.close()


@router.get("/remix/{remix_artifact_id}", response_model=RemixArtifactResponse, dependencies=[Depends(require_auth("viewer"))])
def remix_artifact_detail(remix_artifact_id: str, request: Request) -> RemixArtifactResponse:
    session = open_session(request)
    try:
        payload = request.app.state.remix_service.get_remix_artifact(session=session, remix_artifact_id=remix_artifact_id)
        return RemixArtifactResponse(**payload)
    except Exception as exc:
        raise to_http_exception(exc, default_status=404) from exc
    finally:
        session.close()


@router.get("/remix", response_model=RemixArtifactListResponse, dependencies=[Depends(require_auth("viewer"))])
def remix_artifact_list(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> RemixArtifactListResponse:
    session = open_session(request)
    try:
        payload = request.app.state.remix_service.list_remix_artifacts(session=session, limit=limit, offset=offset)
        return RemixArtifactListResponse(
            remixes=[RemixArtifactListItem(**item) for item in payload["items"]],
            total=payload["total"],
            offset=payload["offset"],
            limit=payload["limit"],
        )
    finally:
        session.close()


@router.post("/remix", response_model=RemixResponse)
def remix(
    payload: RemixRequest,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("operator")),
) -> RemixResponse:
    session = open_session(request)
    try:
        enforce_mode(request, auth_context, payload.mode)
        branch, event = request.app.state.remix_service.remix(
            session=session,
            source_document_id=payload.source_document_id,
            source_branch_id=payload.source_branch_id,
            target_document_id=payload.target_document_id,
            target_branch_id=payload.target_branch_id,
            strategy=payload.strategy,
            seed=payload.seed,
            mode=payload.mode,
        )
        session.commit()
        return RemixResponse(
            new_branch_id=branch.id,
            event_id=event.id,
            strategy=payload.strategy,
            diff_summary=event.diff_summary,
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise to_http_exception(exc, default_status=400) from exc
    finally:
        session.close()
