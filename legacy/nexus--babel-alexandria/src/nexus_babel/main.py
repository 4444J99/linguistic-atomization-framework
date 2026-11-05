from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from nexus_babel.api.routes import router as api_router
from nexus_babel.api.errors import register_exception_handlers
from nexus_babel.config import Settings, get_settings
from nexus_babel.db import DBManager
from nexus_babel.models import Base
from nexus_babel.services.analysis import AnalysisService
from nexus_babel.services.auth import AuthService
from nexus_babel.services.evolution import EvolutionService
from nexus_babel.services.governance import GovernanceService
from nexus_babel.services.hypergraph import HypergraphProjector
from nexus_babel.services.ingestion import IngestionService
from nexus_babel.services.jobs import JobService
from nexus_babel.services.metrics import MetricsService
from nexus_babel.services.plugins import PluginRegistry
from nexus_babel.services.remix import RemixService
from nexus_babel.services.rhetoric import RhetoricalAnalyzer
from nexus_babel.services.seed_corpus import SeedCorpusService

logger = logging.getLogger(__name__)


def _warn_runtime_default_paths(settings: Settings) -> None:
    if settings.environment == "dev":
        return
    cwd = Path.cwd().resolve()
    default_corpus = cwd
    default_object_storage = cwd / "object_storage"

    corpus_env_set = "NEXUS_CORPUS_ROOT" in os.environ
    object_env_set = "NEXUS_OBJECT_STORAGE_ROOT" in os.environ
    if settings.corpus_root.resolve() == default_corpus and not corpus_env_set:
        logger.warning(
            "Non-dev environment '%s' is using default-like corpus_root=%s; set NEXUS_CORPUS_ROOT explicitly",
            settings.environment,
            settings.corpus_root,
        )
    if settings.object_storage_root.resolve() == default_object_storage and not object_env_set:
        logger.warning(
            "Non-dev environment '%s' is using default-like object_storage_root=%s; set NEXUS_OBJECT_STORAGE_ROOT explicitly",
            settings.environment,
            settings.object_storage_root,
        )


def _initialize_schema_and_seeds(app: FastAPI) -> None:
    settings: Settings = app.state.settings
    schema_mode = settings.resolved_schema_management_mode()
    if schema_mode == "auto_create":
        app.state.db.create_all(Base.metadata)
    elif schema_mode == "migrate_only":
        logger.info("Schema management mode is migrate_only; skipping create_all() at startup")
    elif schema_mode == "off":
        logger.info("Schema management mode is off; skipping create_all() at startup")

    if not app.state.db.has_all_tables(Base.metadata):
        logger.warning(
            "Database schema is not ready for startup seeding; skipping bootstrap keys and policy initialization "
            "(mode=%s, database_url=%s)",
            schema_mode,
            settings.database_url,
        )
        return

    session = app.state.db.session()
    try:
        if settings.resolved_bootstrap_keys_enabled():
            app.state.auth_service.ensure_default_api_keys(
                session,
                [
                    ("dev-viewer", "viewer", settings.bootstrap_viewer_key, False),
                    ("dev-operator", "operator", settings.bootstrap_operator_key, False),
                    ("dev-researcher", "researcher", settings.bootstrap_researcher_key, True),
                    ("dev-admin", "admin", settings.bootstrap_admin_key, True),
                ],
            )
        else:
            logger.info("Bootstrap API key seeding disabled for environment=%s", settings.environment)
        app.state.governance_service.ensure_default_policies(session, settings.public_blocked_terms)
        session.commit()
    finally:
        session.close()


def create_app(settings_override: Settings | None = None) -> FastAPI:
    settings = settings_override or get_settings()
    templates = Jinja2Templates(directory="src/nexus_babel/frontend/templates")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _initialize_schema_and_seeds(app)
        yield
        app.state.hypergraph.close()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    register_exception_handlers(app)

    app.state.settings = settings
    _warn_runtime_default_paths(settings)
    app.state.db = DBManager(settings.database_url)
    app.state.hypergraph = HypergraphProjector(settings.neo4j_uri, settings.neo4j_username, settings.neo4j_password)
    app.state.metrics = MetricsService()
    app.state.auth_service = AuthService()
    app.state.plugin_registry = PluginRegistry(ml_enabled=settings.plugin_ml_enabled)
    app.state.rhetorical_analyzer = RhetoricalAnalyzer()
    app.state.analysis_service = AnalysisService(app.state.rhetorical_analyzer, app.state.plugin_registry)
    app.state.governance_service = GovernanceService()
    app.state.evolution_service = EvolutionService()
    app.state.ingestion_service = IngestionService(settings=settings, hypergraph=app.state.hypergraph)
    app.state.remix_service = RemixService(
        evolution_service=app.state.evolution_service,
        governance_service=app.state.governance_service,
    )
    app.state.seed_corpus_service = SeedCorpusService(
        seeds_dir=settings.corpus_root / "seeds",
        registry_path=settings.seed_registry_path,
    )
    app.state.job_service = JobService(
        settings=settings,
        ingestion_service=app.state.ingestion_service,
        analysis_service=app.state.analysis_service,
        evolution_service=app.state.evolution_service,
        hypergraph=app.state.hypergraph,
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        started = time.perf_counter()
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        app.state.metrics.observe("http.request.ms", elapsed_ms)
        app.state.metrics.inc(f"http.status.{response.status_code}")
        response.headers["X-Request-ID"] = request_id
        return response

    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/app/corpus")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics() -> dict:
        return app.state.metrics.snapshot()

    @app.get("/app/{view}", response_class=HTMLResponse)
    async def app_view(view: str, request: Request) -> HTMLResponse:
        allowed = {"corpus", "hypergraph", "timeline", "governance"}
        if view not in allowed:
            return HTMLResponse("Not Found", status_code=404)
        return templates.TemplateResponse(request, "shell.html", {"view": view})

    return app


app = create_app()
