from __future__ import annotations

from fastapi import APIRouter

from nexus_babel.api.routes.analysis import router as analysis_router
from nexus_babel.api.routes.auth import router as auth_router
from nexus_babel.api.routes.branches import router as branches_router
from nexus_babel.api.routes.documents import router as documents_router
from nexus_babel.api.routes.governance import router as governance_router
from nexus_babel.api.routes.ingest import router as ingest_router
from nexus_babel.api.routes.jobs import router as jobs_router
from nexus_babel.api.routes.remix import router as remix_router

router = APIRouter(prefix="/api/v1")
for child in (
    ingest_router,
    analysis_router,
    branches_router,
    governance_router,
    documents_router,
    auth_router,
    jobs_router,
    remix_router,
):
    router.include_router(child)
