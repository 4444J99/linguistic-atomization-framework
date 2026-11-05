from __future__ import annotations

from typing import Callable

from fastapi import Header, Request
from sqlalchemy.orm import Session

from nexus_babel.api.errors import ForbiddenError, UnauthorizedError
from nexus_babel.services.auth import AuthContext


def open_session(request: Request) -> Session:
    return request.app.state.db.session()


def require_auth(min_role: str = "viewer") -> Callable:
    def dependency(
        request: Request,
        x_nexus_api_key: str | None = Header(default=None, alias="X-Nexus-API-Key"),
    ) -> AuthContext:
        session = request.app.state.db.session()
        try:
            ctx = request.app.state.auth_service.authenticate(session, x_nexus_api_key)
            if not ctx:
                raise UnauthorizedError()
            if not request.app.state.auth_service.role_allows(ctx.role, min_role):
                raise ForbiddenError(f"Role '{ctx.role}' lacks required permission '{min_role}'")
            request.state.auth_context = ctx
            session.commit()
            return ctx
        finally:
            session.close()

    return dependency


def enforce_mode(request: Request, ctx: AuthContext, mode: str) -> None:
    if not request.app.state.auth_service.mode_allows(
        ctx.role,
        mode,
        request.app.state.settings.raw_mode_enabled,
        ctx.raw_mode_enabled,
    ):
        raise ForbiddenError(f"Role '{ctx.role}' is not allowed to execute mode '{mode.upper()}'")
