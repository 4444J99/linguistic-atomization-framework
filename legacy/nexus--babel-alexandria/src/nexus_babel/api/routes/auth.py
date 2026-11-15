from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from nexus_babel.api.deps import require_auth
from nexus_babel.services.auth import AuthContext

router = APIRouter()


@router.get("/auth/whoami")
def auth_whoami(request: Request, auth_context: AuthContext = Depends(require_auth("viewer"))) -> dict:
    allowed_modes = ["PUBLIC"]
    if request.app.state.auth_service.mode_allows(
        auth_context.role,
        "RAW",
        request.app.state.settings.raw_mode_enabled,
        auth_context.raw_mode_enabled,
    ):
        allowed_modes.append("RAW")
    return {
        "api_key_id": auth_context.api_key_id,
        "owner": auth_context.owner,
        "role": auth_context.role,
        "raw_mode_enabled": auth_context.raw_mode_enabled,
        "allowed_modes": allowed_modes,
    }
