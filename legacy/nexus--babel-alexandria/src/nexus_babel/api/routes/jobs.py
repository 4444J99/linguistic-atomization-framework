from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select

from nexus_babel.api.deps import enforce_mode, open_session, require_auth
from nexus_babel.api.errors import to_http_exception
from nexus_babel.models import Job
from nexus_babel.schemas import JobStatusResponse, JobSubmitRequest, JobSubmitResponse
from nexus_babel.services.auth import AuthContext

router = APIRouter()


@router.post("/jobs/submit", response_model=JobSubmitResponse)
def submit_job(
    payload: JobSubmitRequest,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("operator")),
) -> JobSubmitResponse:
    session = open_session(request)
    try:
        if payload.job_type == "analyze":
            mode = str(payload.payload.get("mode", "PUBLIC"))
            enforce_mode(request, auth_context, mode)
        if payload.execution_mode == "async" and not request.app.state.settings.async_jobs_enabled:
            raise HTTPException(status_code=400, detail="Async jobs are disabled by feature flag")
        job = request.app.state.job_service.submit(
            session=session,
            job_type=payload.job_type,
            payload=payload.payload,
            execution_mode=payload.execution_mode,
            idempotency_key=payload.idempotency_key,
            created_by=auth_context.owner,
            max_attempts=payload.max_attempts,
        )
        if payload.execution_mode == "sync":
            request.app.state.job_service.execute(session, job)
        session.commit()
        return JobSubmitResponse(
            job_id=job.id,
            status=job.status,
            job_type=job.job_type,
            execution_mode=job.execution_mode,  # type: ignore[arg-type]
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise to_http_exception(exc, default_status=400) from exc
    finally:
        session.close()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse, dependencies=[Depends(require_auth("viewer"))])
def get_job(job_id: str, request: Request) -> JobStatusResponse:
    session = open_session(request)
    try:
        data = request.app.state.job_service.get_job(session=session, job_id=job_id)
        return JobStatusResponse(**data)
    except Exception as exc:
        raise to_http_exception(exc, default_status=404) from exc
    finally:
        session.close()


@router.get("/jobs", dependencies=[Depends(require_auth("viewer"))])
def list_jobs(request: Request, limit: int = Query(default=100, ge=1, le=1000)) -> dict:
    session = open_session(request)
    try:
        jobs = session.scalars(select(Job).order_by(Job.created_at.desc()).limit(limit)).all()
        return {
            "jobs": [
                {
                    "job_id": j.id,
                    "job_type": j.job_type,
                    "status": j.status,
                    "execution_mode": j.execution_mode,
                    "attempt_count": j.attempt_count,
                    "max_attempts": j.max_attempts,
                    "created_at": j.created_at,
                    "updated_at": j.updated_at,
                }
                for j in jobs
            ]
        }
    finally:
        session.close()


@router.post("/jobs/{job_id}/cancel", response_model=JobStatusResponse)
def cancel_job(
    job_id: str,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("operator")),
) -> JobStatusResponse:
    session = open_session(request)
    try:
        _ = auth_context
        request.app.state.job_service.cancel(session=session, job_id=job_id)
        session.commit()
        data = request.app.state.job_service.get_job(session=session, job_id=job_id)
        return JobStatusResponse(**data)
    except Exception as exc:
        session.rollback()
        raise to_http_exception(exc, default_status=404) from exc
    finally:
        session.close()
