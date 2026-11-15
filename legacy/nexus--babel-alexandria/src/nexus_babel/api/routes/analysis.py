from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select

from nexus_babel.api.deps import enforce_mode, open_session, require_auth
from nexus_babel.api.errors import ConflictError, NotFoundError, to_http_exception
from nexus_babel.models import AnalysisRun, Document
from nexus_babel.schemas import (
    AnalysisRunResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    RhetoricalAnalysisRequest,
    RhetoricalAnalysisResponse,
)
from nexus_babel.services.auth import AuthContext

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    payload: AnalyzeRequest,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("operator")),
) -> AnalyzeResponse:
    session = open_session(request)
    try:
        enforce_mode(request, auth_context, payload.mode)
        if payload.document_id:
            doc = session.get(Document, payload.document_id)
            if not doc:
                raise NotFoundError("Document not found")
            if doc.conflict_flag or not doc.ingested:
                raise ConflictError("Document is conflicted or non-ingestable; analysis is blocked")
        if payload.execution_mode == "async":
            if not request.app.state.settings.async_jobs_enabled:
                raise HTTPException(status_code=400, detail="Async jobs are disabled by feature flag")
            job = request.app.state.job_service.submit(
                session=session,
                job_type="analyze",
                payload={
                    "document_id": payload.document_id,
                    "branch_id": payload.branch_id,
                    "layers": payload.layers,
                    "mode": payload.mode,
                    "plugin_profile": payload.plugin_profile,
                },
                execution_mode="async",
                created_by=auth_context.owner,
            )
            session.commit()
            return AnalyzeResponse(
                analysis_run_id=None,
                mode=payload.mode,
                layers={},
                confidence_bundle={},
                hypergraph_ids={},
                plugin_provenance={},
                job_id=job.id,
                status=job.status,
            )

        run, result = request.app.state.analysis_service.analyze(
            session=session,
            document_id=payload.document_id,
            branch_id=payload.branch_id,
            layers=payload.layers,
            mode=payload.mode,
            execution_mode="sync",
            plugin_profile=payload.plugin_profile,
            job_id=None,
        )

        shadow_job_id = None
        if payload.execution_mode == "shadow" and request.app.state.settings.shadow_execution_enabled:
            shadow_job = request.app.state.job_service.submit(
                session=session,
                job_type="analyze",
                payload={
                    "document_id": payload.document_id,
                    "branch_id": payload.branch_id,
                    "layers": payload.layers,
                    "mode": payload.mode,
                    "plugin_profile": payload.plugin_profile or "ml_first",
                },
                execution_mode="async",
                created_by=auth_context.owner,
            )
            shadow_job_id = shadow_job.id

        session.commit()
        return AnalyzeResponse(
            analysis_run_id=run.id,
            mode=result["mode"],
            layers=result["layers"],
            confidence_bundle=result["confidence_bundle"],
            hypergraph_ids=result["hypergraph_ids"],
            plugin_provenance=result.get("plugin_provenance", {}),
            job_id=shadow_job_id,
            status="completed" if not shadow_job_id else "shadow_queued",
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise to_http_exception(exc, default_status=400) from exc
    finally:
        session.close()


@router.post("/rhetorical_analysis", response_model=RhetoricalAnalysisResponse)
def rhetorical_analysis(
    payload: RhetoricalAnalysisRequest,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("operator")),
) -> RhetoricalAnalysisResponse:
    session = open_session(request)
    try:
        enforce_mode(request, auth_context, "PUBLIC")
        text = payload.text
        if not text and payload.document_id:
            doc = session.get(Document, payload.document_id)
            if not doc:
                raise NotFoundError("Document not found")
            text = str((doc.provenance or {}).get("extracted_text", ""))
        text = text or ""
        result = request.app.state.rhetorical_analyzer.analyze(text)
        return RhetoricalAnalysisResponse(**result)
    finally:
        session.close()


@router.get("/analysis/runs/{run_id}", response_model=AnalysisRunResponse, dependencies=[Depends(require_auth("viewer"))])
def analysis_run(run_id: str, request: Request) -> AnalysisRunResponse:
    session = open_session(request)
    try:
        data = request.app.state.analysis_service.get_run(session=session, run_id=run_id)
        return AnalysisRunResponse(**data)
    except Exception as exc:
        raise to_http_exception(exc, default_status=404) from exc
    finally:
        session.close()


@router.get("/analysis/runs", dependencies=[Depends(require_auth("viewer"))])
def list_analysis_runs(request: Request, limit: int = Query(default=100, ge=1, le=1000)) -> dict:
    session = open_session(request)
    try:
        runs = session.scalars(select(AnalysisRun).order_by(AnalysisRun.created_at.desc()).limit(limit)).all()
        return {
            "runs": [
                {
                    "analysis_run_id": r.id,
                    "document_id": r.document_id,
                    "branch_id": r.branch_id,
                    "mode": r.mode,
                    "execution_mode": r.execution_mode,
                    "plugin_profile": r.plugin_profile,
                    "created_at": r.created_at,
                }
                for r in runs
            ]
        }
    finally:
        session.close()
