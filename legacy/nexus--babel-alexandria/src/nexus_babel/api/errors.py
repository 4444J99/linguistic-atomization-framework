from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


@dataclass
class ApiDomainError(Exception):
    detail: str
    status_code: int = 400
    code: str | None = None

    def __str__(self) -> str:
        return self.detail


class UnauthorizedError(ApiDomainError):
    def __init__(self, detail: str = "Missing or invalid API key"):
        super().__init__(detail=detail, status_code=401, code="unauthorized")


class ForbiddenError(ApiDomainError):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=403, code="forbidden")


class NotFoundError(ApiDomainError):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=404, code="not_found")


class ConflictError(ApiDomainError):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=409, code="conflict")


class ValidationError(ApiDomainError):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=400, code="validation_error")


async def _api_domain_error_handler(_: Request, exc: ApiDomainError) -> JSONResponse:
    payload = {"detail": exc.detail}
    if exc.code:
        payload["code"] = exc.code
    return JSONResponse(status_code=exc.status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiDomainError, _api_domain_error_handler)


def to_http_exception(exc: Exception, *, default_status: int = 400) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, ApiDomainError):
        return HTTPException(status_code=exc.status_code, detail=exc.detail)
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=default_status, detail=str(exc))
    return HTTPException(status_code=default_status, detail=str(exc))
