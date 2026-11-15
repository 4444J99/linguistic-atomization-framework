from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select

from nexus_babel.api.deps import enforce_mode, open_session, require_auth
from nexus_babel.api.errors import to_http_exception
from nexus_babel.models import Branch
from nexus_babel.schemas import (
    BranchCompareResponse,
    BranchEventView,
    BranchReplayResponse,
    BranchTimelineResponse,
    BranchVisualizationResponse,
    EvolveBranchRequest,
    EvolveBranchResponse,
    MergeBranchesRequest,
    MergeBranchesResponse,
    MultiEvolveRequest,
    MultiEvolveResponse,
)
from nexus_babel.services.auth import AuthContext

router = APIRouter()


@router.post("/evolve/branch", response_model=EvolveBranchResponse)
def evolve_branch(
    payload: EvolveBranchRequest,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("operator")),
) -> EvolveBranchResponse:
    session = open_session(request)
    try:
        enforce_mode(request, auth_context, payload.mode)
        branch, event = request.app.state.evolution_service.evolve_branch(
            session=session,
            parent_branch_id=payload.parent_branch_id,
            root_document_id=payload.root_document_id,
            event_type=payload.event_type,
            event_payload=payload.event_payload,
            mode=payload.mode,
        )
        session.commit()
        return EvolveBranchResponse(new_branch_id=branch.id, event_id=event.id, diff_summary=event.diff_summary)
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise to_http_exception(exc, default_status=400) from exc
    finally:
        session.close()


@router.post("/evolve/multi", response_model=MultiEvolveResponse)
def multi_evolve(
    payload: MultiEvolveRequest,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("operator")),
) -> MultiEvolveResponse:
    session = open_session(request)
    try:
        enforce_mode(request, auth_context, payload.mode)
        result = request.app.state.evolution_service.multi_evolve(
            session=session,
            parent_branch_id=payload.parent_branch_id,
            root_document_id=payload.root_document_id,
            events=[
                {
                    "event_type": event.event_type,
                    "event_payload": event.event_payload,
                }
                for event in payload.events
            ],
            mode=payload.mode,
        )
        session.commit()
        return MultiEvolveResponse(
            branch_ids=list(result.get("branch_ids", [])),
            event_ids=list(result.get("event_ids", [])),
            final_branch_id=result["final_branch_id"],
            event_count=int(result["event_count"]),
            final_text_hash=result["final_text_hash"],
            final_preview=result["final_preview"],
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise to_http_exception(exc, default_status=400) from exc
    finally:
        session.close()


@router.get("/branches/{branch_id}/timeline", response_model=BranchTimelineResponse, dependencies=[Depends(require_auth("viewer"))])
def branch_timeline(branch_id: str, request: Request) -> BranchTimelineResponse:
    session = open_session(request)
    try:
        timeline = request.app.state.evolution_service.get_timeline(session=session, branch_id=branch_id)
        branch = timeline["branch"]
        events = [
            BranchEventView(
                branch_id=e.branch_id,
                event_id=e.id,
                event_index=e.event_index,
                event_type=e.event_type,
                event_payload=e.event_payload,
                diff_summary=e.diff_summary,
                created_at=e.created_at,
            )
            for e in timeline["events"]
        ]
        return BranchTimelineResponse(
            branch_id=branch.id,
            root_document_id=branch.root_document_id,
            events=events,
            replay_snapshot=timeline["replay_snapshot"],
        )
    except Exception as exc:
        raise to_http_exception(exc, default_status=404) from exc
    finally:
        session.close()


@router.get("/branches", dependencies=[Depends(require_auth("viewer"))])
def list_branches(request: Request, limit: int = Query(default=100, ge=1, le=1000)) -> dict:
    session = open_session(request)
    try:
        branches = session.scalars(select(Branch).order_by(Branch.created_at.desc()).limit(limit)).all()
        return {
            "branches": [
                {
                    "id": b.id,
                    "parent_branch_id": b.parent_branch_id,
                    "root_document_id": b.root_document_id,
                    "mode": b.mode,
                    "branch_version": b.branch_version,
                    "created_at": b.created_at,
                }
                for b in branches
            ]
        }
    finally:
        session.close()


@router.post("/branches/{branch_id}/replay", response_model=BranchReplayResponse, dependencies=[Depends(require_auth("viewer"))])
def replay_branch(branch_id: str, request: Request) -> BranchReplayResponse:
    session = open_session(request)
    try:
        data = request.app.state.evolution_service.replay_branch(session=session, branch_id=branch_id)
        return BranchReplayResponse(**data)
    except Exception as exc:
        raise to_http_exception(exc, default_status=404) from exc
    finally:
        session.close()


@router.get("/branches/{branch_id}/compare/{other_branch_id}", response_model=BranchCompareResponse, dependencies=[Depends(require_auth("viewer"))])
def compare_branch(branch_id: str, other_branch_id: str, request: Request) -> BranchCompareResponse:
    session = open_session(request)
    try:
        data = request.app.state.evolution_service.compare_branches(
            session=session,
            left_branch_id=branch_id,
            right_branch_id=other_branch_id,
        )
        return BranchCompareResponse(**data)
    except Exception as exc:
        raise to_http_exception(exc, default_status=404) from exc
    finally:
        session.close()


@router.post("/branches/merge", response_model=MergeBranchesResponse)
def merge_branches(
    payload: MergeBranchesRequest,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("operator")),
) -> MergeBranchesResponse:
    session = open_session(request)
    try:
        enforce_mode(request, auth_context, payload.mode)
        branch, event, lca = request.app.state.evolution_service.merge_branches(
            session=session,
            left_branch_id=payload.left_branch_id,
            right_branch_id=payload.right_branch_id,
            strategy=payload.strategy,
            mode=payload.mode,
        )
        session.commit()
        return MergeBranchesResponse(
            new_branch_id=branch.id,
            event_id=event.id,
            strategy=payload.strategy,
            lca_branch_id=getattr(lca, "id", None),
            conflict_semantics=dict((event.diff_summary or {}).get("conflict_semantics", {})),
            diff_summary=event.diff_summary,
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


@router.get(
    "/branches/{branch_id}/visualization",
    response_model=BranchVisualizationResponse,
    dependencies=[Depends(require_auth("viewer"))],
)
def branch_visualization(branch_id: str, request: Request) -> BranchVisualizationResponse:
    session = open_session(request)
    try:
        return BranchVisualizationResponse(**request.app.state.evolution_service.get_visualization(session=session, branch_id=branch_id))
    except Exception as exc:
        raise to_http_exception(exc, default_status=404) from exc
    finally:
        session.close()
