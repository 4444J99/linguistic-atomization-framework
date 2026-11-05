from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from nexus_babel.api.deps import enforce_mode, open_session, require_auth
from nexus_babel.api.errors import to_http_exception
from nexus_babel.schemas import GovernanceEvaluateRequest, GovernanceEvaluateResponse
from nexus_babel.services.auth import AuthContext

router = APIRouter()


@router.post("/governance/evaluate", response_model=GovernanceEvaluateResponse)
def governance_evaluate(
    payload: GovernanceEvaluateRequest,
    request: Request,
    auth_context: AuthContext = Depends(require_auth("operator")),
) -> GovernanceEvaluateResponse:
    session = open_session(request)
    try:
        enforce_mode(request, auth_context, payload.mode)
        decision = request.app.state.governance_service.evaluate(
            session=session,
            candidate_output=payload.candidate_output,
            mode=payload.mode,
        )
        session.commit()
        return GovernanceEvaluateResponse(
            allow=decision["allow"],
            policy_hits=decision["policy_hits"],
            redactions=decision["redactions"],
            audit_id=decision["audit_id"],
            decision_trace=decision.get("decision_trace", {}),
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        raise to_http_exception(exc, default_status=400) from exc
    finally:
        session.close()


@router.get("/audit/policy-decisions", dependencies=[Depends(require_auth("operator"))])
def audit_policy_decisions(request: Request, limit: int = Query(default=100, ge=1, le=1000)) -> dict:
    session = open_session(request)
    try:
        return {"decisions": request.app.state.governance_service.list_policy_decisions(session=session, limit=limit)}
    finally:
        session.close()
