# Platform Infrastructure -- Specification

## Overview

Platform Infrastructure encompasses the foundational subsystems that every other Nexus Babel Alexandria domain depends on: authentication and authorization, asynchronous job processing, application configuration, database management, metrics collection, the plugin execution framework, and the background worker process. These services are wired together in the FastAPI application factory (`create_app()` in `main.py`) and exposed through both API routes and internal service interfaces.

The domain enforces a four-role hierarchy (viewer < operator < researcher < admin) with API-key-based authentication, a dual-mode governance gate (PUBLIC / RAW), a lease-based job queue with retry and exponential backoff, an in-memory metrics collector with timing histograms, and a plugin registry that chains deterministic and ML-stub analysis providers. All configuration flows through a single `pydantic-settings` class with environment variable overrides.

## User Stories

### P1 -- As-Built (Verified)

#### US-INFRA-01: API Key Authentication

**As** an API consumer, **I want to** authenticate via an API key in the `X-Nexus-API-Key` header **so that** the system knows my identity and role.

**Acceptance Scenarios:**

- **Given** no `X-Nexus-API-Key` header is present, **When** I request any protected route (`/api/v1/documents`, `/api/v1/ingest/batch`, `/api/v1/auth/whoami`), **Then** I receive HTTP 401 with detail "Missing or invalid API key".
  - *Evidence:* `tests/test_mvp.py::test_auth_required_on_protected_routes` (line 40); `api/routes.py` `_require_auth` dependency (lines 47-71).
- **Given** I provide a valid API key, **When** I call `GET /api/v1/auth/whoami`, **Then** I receive my `api_key_id`, `owner`, `role`, `raw_mode_enabled`, and `allowed_modes`.
  - *Evidence:* `api/routes.py` lines 434-450; `tests/test_mvp.py::test_role_and_raw_mode_enforcement` (lines 68-73).
- **Given** I authenticate, **When** the system looks up my key, **Then** `ApiKey.last_used_at` is updated to the current UTC timestamp.
  - *Evidence:* `services/auth.py` line 60.
- **Given** an API key exists but `enabled=False`, **When** I authenticate with it, **Then** I receive HTTP 401.
  - *Evidence:* `services/auth.py` line 57 filters on `ApiKey.enabled.is_(True)`.

#### US-INFRA-02: Role-Based Access Control

**As** a platform operator, **I want** endpoints to enforce minimum role requirements **so that** viewers cannot mutate data and only researchers+ can access RAW mode.

**Acceptance Scenarios:**

- **Given** I am a `viewer`, **When** I POST to `/api/v1/ingest/batch`, **Then** I receive HTTP 403.
  - *Evidence:* `tests/test_mvp.py::test_role_and_raw_mode_enforcement` (line 52).
- **Given** I am an `operator`, **When** I request governance evaluation in RAW mode, **Then** I receive HTTP 403.
  - *Evidence:* `tests/test_mvp.py::test_role_and_raw_mode_enforcement` (lines 54-59).
- **Given** I am a `researcher` with `raw_mode_enabled=True` on my key, **When** I request RAW mode, **Then** the request succeeds.
  - *Evidence:* `tests/test_mvp.py::test_role_and_raw_mode_enforcement` (lines 61-66).
- **Given** the global `NEXUS_RAW_MODE_ENABLED=False`, **When** any user requests RAW mode, **Then** they receive HTTP 403 regardless of their role.
  - *Evidence:* `services/auth.py` `mode_allows()` lines 68-69.

#### US-INFRA-03: Bootstrap API Key Seeding

**As** a developer starting the application, **I want** four default API keys to be seeded at startup **so that** I can immediately interact with the API in dev/test.

**Acceptance Scenarios:**

- **Given** the application starts, **When** the lifespan handler runs, **Then** four keys are seeded for `dev-viewer` (viewer, no RAW), `dev-operator` (operator, no RAW), `dev-researcher` (researcher, RAW), `dev-admin` (admin, RAW).
  - *Evidence:* `main.py` lines 38-45; key values from `config.py` lines 29-32.
- **Given** a bootstrap key already exists (matched by `key_hash`), **When** the app starts, **Then** it re-enables the key if disabled and updates `raw_mode_enabled`, but does not create a duplicate.
  - *Evidence:* `services/auth.py` `ensure_default_api_keys()` lines 37-42.

#### US-INFRA-04: Async Job Submission and Lifecycle

**As** an operator, **I want to** submit jobs for async processing **so that** long-running operations (ingest, analyze, replay, audit) do not block the API response.

**Acceptance Scenarios:**

- **Given** `NEXUS_ASYNC_JOBS_ENABLED=True`, **When** I POST to `/api/v1/jobs/submit` with `execution_mode=async`, **Then** I receive a `JobSubmitResponse` with `status=queued` and a `job_id`.
  - *Evidence:* `tests/test_wave2.py::test_async_job_lifecycle_and_artifacts` (lines 27-42).
- **Given** `NEXUS_ASYNC_JOBS_ENABLED=False`, **When** I submit an async job, **Then** I receive HTTP 400 with detail "Async jobs are disabled by feature flag".
  - *Evidence:* `api/routes.py` lines 464-465.
- **Given** a queued job, **When** I POST with `execution_mode=sync`, **Then** the job executes inline and the response includes the final status.
  - *Evidence:* `api/routes.py` lines 475-476.
- **Given** a submitted job, **When** I call `GET /api/v1/jobs/{id}`, **Then** I receive full `JobStatusResponse` including `attempts` and `artifacts`.
  - *Evidence:* `tests/test_wave2.py` lines 52-57.
- **Given** a submitted job, **When** I call `GET /api/v1/jobs`, **Then** I receive a paginated list of jobs ordered by `created_at` descending.
  - *Evidence:* `api/routes.py` lines 506-527.

#### US-INFRA-05: Job Idempotency

**As** a client, **I want** idempotency keys to prevent duplicate job creation **so that** retried requests do not spawn duplicate work.

**Acceptance Scenarios:**

- **Given** I submit a job with `idempotency_key=X`, **When** I submit the same `job_type` + `idempotency_key`, **Then** I receive the same `job_id`.
  - *Evidence:* `tests/test_wave2.py::test_job_idempotency_returns_same_job` (lines 72-87); `services/jobs.py` lines 36-44; DB unique constraint `uq_job_idempotency` on `(job_type, idempotency_key)` in `models.py` lines 227-229.

#### US-INFRA-06: Job Cancellation

**As** an operator, **I want to** cancel a queued job **so that** unnecessary work is not executed.

**Acceptance Scenarios:**

- **Given** a job in `queued` status, **When** I POST to `/api/v1/jobs/{id}/cancel`, **Then** the job transitions to `cancelled` and its lease is cleared.
  - *Evidence:* `tests/test_wave2.py::test_job_cancel` (lines 90-104); `services/jobs.py` lines 60-69.
- **Given** a job in `succeeded` or `failed` status, **When** I cancel it, **Then** the status remains unchanged (no-op).
  - *Evidence:* `services/jobs.py` lines 64-65.

#### US-INFRA-07: Job Retry with Exponential Backoff

**As** the system, **I want** failed job attempts to be retried with increasing delay **so that** transient failures are handled gracefully.

**Acceptance Scenarios:**

- **Given** a job fails on attempt N where N < `max_attempts`, **When** the exception is caught, **Then** the job transitions to `retry_wait` with `next_run_at` set to `now + RETRY_BACKOFF_SECONDS[min(N-1, 2)]` (backoff schedule: `[2, 10, 30]` seconds).
  - *Evidence:* `services/jobs.py` lines 167-170; `RETRY_BACKOFF_SECONDS` at line 14.
- **Given** a job fails on attempt N == `max_attempts`, **When** the exception is caught, **Then** the job transitions to `failed` permanently.
  - *Evidence:* `services/jobs.py` lines 171-174.
- **Given** each attempt, **When** it completes (success or failure), **Then** a `JobAttempt` record is created with `runtime_ms`, `status`, `started_at`, `finished_at`, and `error_text`.
  - *Evidence:* `services/jobs.py` lines 146-178.

#### US-INFRA-08: Job Dispatch and Artifact Creation

**As** the system, **I want** jobs to be dispatched by type and produce typed artifacts **so that** results are traceable.

**Acceptance Scenarios:**

- **Given** a job with `job_type=ingest_batch`, **When** executed, **Then** it calls `ingestion_service.ingest_batch()` and creates an artifact with `artifact_type=ingest_batch_result`.
  - *Evidence:* `services/jobs.py` `_dispatch()` lines 184-197, `_create_artifacts()` lines 241-245.
- **Given** a job with `job_type=analyze`, **When** executed, **Then** it calls `analysis_service.analyze()` and creates an artifact with `artifact_type=analyze_result`.
  - *Evidence:* `services/jobs.py` lines 199-217, 236-240.
- **Given** a job with `job_type=branch_replay`, **When** executed, **Then** it calls `evolution_service.replay_branch()` and creates an artifact with `artifact_type=branch_replay_result`.
  - *Evidence:* `services/jobs.py` lines 219-221, 246-249.
- **Given** a job with `job_type=integrity_audit`, **When** executed, **Then** it iterates all ingested documents, checks hypergraph integrity, and returns inconsistencies.
  - *Evidence:* `services/jobs.py` lines 223-230.
- **Given** an unsupported `job_type`, **When** dispatched, **Then** a `ValueError` is raised.
  - *Evidence:* `services/jobs.py` line 232.

#### US-INFRA-09: Worker Process

**As** an operator, **I want** a CLI worker that polls for and processes jobs **so that** async jobs are consumed outside the web process.

**Acceptance Scenarios:**

- **Given** `python -m nexus_babel.worker`, **When** started, **Then** it creates a full app, polls for jobs at `NEXUS_WORKER_POLL_SECONDS` intervals, and processes stale leases before each poll.
  - *Evidence:* `worker.py` lines 9-35.
- **Given** `--once` flag, **When** the worker starts, **Then** it processes at most one job and exits.
  - *Evidence:* `worker.py` lines 28-29.
- **Given** `--max-jobs N`, **When** the worker has processed N jobs, **Then** it exits.
  - *Evidence:* `worker.py` lines 30-31.
- **Given** no work available, **When** the worker polls, **Then** it sleeps for `max(settings.worker_poll_seconds, 0.1)` seconds before retrying.
  - *Evidence:* `worker.py` line 33.

#### US-INFRA-10: Stale Lease Recovery

**As** the system, **I want** stale leases to be detected and recovered **so that** jobs stuck on crashed workers are retried.

**Acceptance Scenarios:**

- **Given** a job with `status=running` and `lease_expires_at < now()`, **When** `complete_stale_leases()` runs, **Then** the job transitions to `retry_wait` (if retries remain) or `failed` (if exhausted).
  - *Evidence:* `services/jobs.py` lines 260-275.
- **Given** a stale job transitioning to `retry_wait`, **When** it is recovered, **Then** `next_run_at` is set using the same backoff schedule.
  - *Evidence:* `services/jobs.py` lines 273-274.

#### US-INFRA-11: Lease-Based Job Acquisition

**As** the system, **I want** job acquisition to use leases **so that** multiple workers can safely compete for jobs without double-execution.

**Acceptance Scenarios:**

- **Given** a job with `status IN (queued, retry_wait)` and `next_run_at <= now` and `lease_expires_at IS NULL OR < now`, **When** `lease_next()` is called, **Then** the job transitions to `running` with `lease_owner` set and `lease_expires_at` set to `now + worker_lease_seconds`.
  - *Evidence:* `services/jobs.py` lines 116-133; `config.py` `worker_lease_seconds` default 30.
- **Given** multiple eligible jobs, **When** `lease_next()` is called, **Then** the oldest job (by `created_at`) is leased first.
  - *Evidence:* `services/jobs.py` line 125.

#### US-INFRA-12: In-Memory Metrics

**As** a developer, **I want** request-level timing and status code counters **so that** I can monitor system health.

**Acceptance Scenarios:**

- **Given** any HTTP request, **When** it completes, **Then** the middleware records `http.request.ms` timing and increments `http.status.{code}` counter.
  - *Evidence:* `main.py` middleware lines 78-87.
- **Given** `GET /metrics`, **When** called (no auth required), **Then** it returns `{"counters": {...}, "timings": {...}}` with `count`, `avg_ms`, and `p95_ms` per timing key.
  - *Evidence:* `main.py` lines 99-101; `services/metrics.py` `snapshot()` lines 18-31.
- **Given** the `MetricsService`, **When** `inc(key)` is called, **Then** the counter increments by the given value (default 1.0).
  - *Evidence:* `services/metrics.py` lines 12-13.
- **Given** the `MetricsService`, **When** `observe(key, value_ms)` is called, **Then** the value is appended to the timing histogram for that key.
  - *Evidence:* `services/metrics.py` lines 15-16.

#### US-INFRA-13: Health Check

**As** a load balancer or monitoring agent, **I want** a health endpoint **so that** I can determine service readiness.

**Acceptance Scenarios:**

- **Given** `GET /healthz` (no auth required), **When** the app is running, **Then** I receive `{"status": "ok"}` with HTTP 200.
  - *Evidence:* `main.py` lines 95-97.

#### US-INFRA-14: Request Tracking Middleware

**As** a developer, **I want** every request to carry a unique request ID **so that** I can correlate logs and traces.

**Acceptance Scenarios:**

- **Given** a request with no `X-Request-ID` header, **When** processed, **Then** a UUID is generated and returned in the `X-Request-ID` response header.
  - *Evidence:* `main.py` lines 81, 86.
- **Given** a request with an `X-Request-ID` header, **When** processed, **Then** the provided ID is propagated to the response.
  - *Evidence:* `main.py` line 81.

#### US-INFRA-15: Plugin Registry and Execution Chain

**As** the analysis subsystem, **I want** a plugin registry that chains providers with fallback **so that** analysis layers can use deterministic or ML-enhanced processing.

**Acceptance Scenarios:**

- **Given** `plugin_profile=deterministic` (default), **When** `run_layer()` is called, **Then** only the `DeterministicLayerPlugin` runs, returning baseline output at baseline confidence.
  - *Evidence:* `services/plugins.py` `_profile_chain()` line 108; `DeterministicLayerPlugin.run()` lines 55-57.
- **Given** `plugin_profile=ml_first` and `plugin_ml_enabled=True`, **When** `run_layer()` is called, **Then** the ML stub runs first; if it succeeds, its enriched output (confidence + 0.1, capped at 0.95) is returned.
  - *Evidence:* `services/plugins.py` lines 104-105; `MLStubLayerPlugin.run()` lines 84-89.
- **Given** `plugin_profile=ml_first` and `plugin_ml_enabled=False`, **When** `run_layer()` is called, **Then** the ML stub fails `supports()`, falls back to deterministic, and `fallback_reason` is populated.
  - *Evidence:* `services/plugins.py` lines 131-133; `MLStubLayerPlugin.supports()` line 72.
- **Given** all plugins in the chain fail, **When** `run_layer()` is called, **Then** a `PluginExecution` is returned with baseline output, 0.0 confidence, and `fallback_reason="all_plugins_failed"`.
  - *Evidence:* `services/plugins.py` lines 150-157.
- **Given** the `PluginRegistry`, **When** `health()` is called, **Then** it returns a dict of `{plugin_name: bool}` from each plugin's `healthcheck()`.
  - *Evidence:* `services/plugins.py` lines 99-100.

#### US-INFRA-16: Application Configuration

**As** a developer, **I want** all configuration to flow through a single validated `Settings` class **so that** misconfiguration is caught early.

**Acceptance Scenarios:**

- **Given** environment variables with `NEXUS_` prefix (or `.env` file), **When** `Settings` is instantiated, **Then** all fields are populated with defaults or overrides.
  - *Evidence:* `config.py` lines 11-43.
- **Given** the `get_settings()` function, **When** called multiple times, **Then** the same `Settings` instance is returned (LRU cached, maxsize=1).
  - *Evidence:* `config.py` lines 45-47.
- **Given** the test harness, **When** `create_app(settings_override)` is called, **Then** the override settings are used instead of the global singleton.
  - *Evidence:* `main.py` line 30; `tests/conftest.py` lines 38-42.

#### US-INFRA-17: Database Management

**As** the application, **I want** a `DBManager` that wraps SQLAlchemy engine and session creation **so that** database access is centralized.

**Acceptance Scenarios:**

- **Given** a SQLite URL, **When** `DBManager` is initialized, **Then** `check_same_thread=False` is passed as a connect arg.
  - *Evidence:* `db.py` lines 14-15.
- **Given** any URL, **When** `DBManager` is initialized, **Then** a `sessionmaker` is created with `autoflush=False`, `autocommit=False`, `future=True`.
  - *Evidence:* `db.py` line 17.
- **Given** `create_all(metadata)` is called, **When** the app starts, **Then** all tables are created via `metadata.create_all(bind=engine)`.
  - *Evidence:* `db.py` lines 19-20; `main.py` line 35.

### P2 -- Partially Built

#### US-INFRA-18: Shadow Execution Mode

**As** a researcher, **I want** shadow execution to run an ML-enhanced analysis alongside a deterministic one **so that** I can compare results without blocking.

**Current State:** The shadow execution path exists in `api/routes.py` lines 194-209 but only triggers when `settings.shadow_execution_enabled=True` (default `False`). No dedicated tests exercise this path. The shadow job is submitted but there is no mechanism to link or compare shadow results to the primary run.

**Remaining Work:**
- Add test coverage for the shadow execution path
- Add a comparison endpoint or field that links shadow results to primary results
- Add documentation for shadow mode behavior

#### US-INFRA-19: Job Monitoring via API

**As** an operator, **I want** to filter and search jobs by status, type, and date range **so that** I can diagnose processing issues.

**Current State:** `GET /api/v1/jobs` exists but only supports `limit` filtering. There is no filtering by `status`, `job_type`, `created_by`, or date range.

**Remaining Work:**
- Add query parameters: `status`, `job_type`, `created_by`, `created_after`, `created_before`
- Add pagination cursor or offset-based pagination

#### US-INFRA-20: Worker Stale-Lease Edge Cases

**As** the system, **I want** stale lease recovery to assign the recovering worker name correctly **so that** recovery provenance is traceable.

**Current State:** `complete_stale_leases()` in `services/jobs.py` line 271 sets `lease_owner` to the recovering worker's name, but this overwrites the crashed worker's identity without logging the original owner. No audit trail is created for recovery events.

**Remaining Work:**
- Log or record the original `lease_owner` before overwriting
- Create an audit event for stale lease recovery
- Add dedicated tests for the stale lease recovery logic

### P3+ -- Vision

#### US-INFRA-21: Rate Limiting per API Key

**As** a platform operator, **I want** per-key rate limits **so that** no single consumer can monopolize system resources.

- Token bucket or sliding window rate limiter
- Configurable per-role defaults with per-key overrides
- HTTP 429 responses with `Retry-After` header

#### US-INFRA-22: JWT Token Support

**As** an API consumer, **I want** to authenticate with JWT tokens alongside API keys **so that** I can use short-lived credentials.

- JWT issuance endpoint (`POST /api/v1/auth/token`)
- Token refresh flow
- Claims include role, modes, expiration
- API key remains supported for backward compatibility

#### US-INFRA-23: Structured Logging and OpenTelemetry

**As** a platform operator, **I want** structured JSON logging and distributed tracing **so that** I can observe system behavior in production.

- `structlog` or standard library JSON formatter
- OpenTelemetry SDK with trace/span propagation
- Request ID correlation in log entries
- Span attributes for job execution, DB queries, plugin runs

#### US-INFRA-24: Prometheus Metrics Export

**As** a monitoring engineer, **I want** Prometheus-compatible metrics **so that** I can scrape and alert on system health.

- `/metrics/prometheus` endpoint with `text/plain` content type
- Counters: `nexus_http_requests_total{method, path, status}`
- Histograms: `nexus_http_request_duration_seconds{method, path}`
- Gauges: `nexus_jobs_queued`, `nexus_jobs_running`
- Job-type-specific counters and latencies

#### US-INFRA-25: Worker Horizontal Scaling

**As** a platform operator, **I want** multiple worker processes to safely compete for jobs **so that** I can scale throughput.

- Worker identity via hostname + PID
- Distributed lock or SELECT FOR UPDATE SKIP LOCKED for lease acquisition
- Worker heartbeat and health reporting
- Graceful shutdown with in-flight job completion

#### US-INFRA-26: Database Connection Pooling Tuning

**As** a platform operator, **I want** configurable connection pool settings **so that** I can tune for my workload and database backend.

- Expose `pool_size`, `max_overflow`, `pool_recycle`, `pool_pre_ping` in Settings
- Different defaults for SQLite vs PostgreSQL
- Connection pool metrics (active, idle, overflow)

#### US-INFRA-27: Role-Based Feature Gating

**As** an admin, **I want** feature flags gated by role **so that** I can enable experimental features for researchers without exposing them to all users.

- Per-feature minimum role requirement
- Feature registry queried at request time
- `GET /api/v1/features` endpoint listing available features for the current role

## Functional Requirements

### Authentication and Authorization

- **FR-001** [MUST]: All `/api/v1/*` endpoints MUST require a valid `X-Nexus-API-Key` header, except where documented otherwise. Invalid or missing keys MUST return HTTP 401. *Implemented in `api/routes.py` `_require_auth()` lines 47-71.*

- **FR-002** [MUST]: The system MUST enforce a four-level role hierarchy: `viewer` (1) < `operator` (2) < `researcher` (3) < `admin` (4). A user's role MUST meet or exceed the minimum role specified for each endpoint. *Implemented in `services/auth.py` `ROLE_ORDER` lines 13-18, `role_allows()` lines 63-64.*

- **FR-003** [MUST]: RAW mode access MUST require all three conditions: (1) global `raw_mode_enabled=True`, (2) per-key `raw_mode_enabled=True`, (3) role >= `researcher`. If any condition fails, HTTP 403 MUST be returned. *Implemented in `services/auth.py` `mode_allows()` lines 66-76.*

- **FR-004** [MUST]: API keys MUST be stored as SHA-256 hashes; plaintext keys MUST never be persisted. *Implemented in `services/auth.py` `hash_api_key()` line 29-30.*

- **FR-005** [MUST]: The system MUST seed four bootstrap API keys at startup from `NEXUS_BOOTSTRAP_*_KEY` settings. *Implemented in `main.py` lines 38-45.*

- **FR-006** [SHOULD]: The `last_used_at` timestamp SHOULD be updated on every successful authentication. *Implemented in `services/auth.py` line 60.*

### Job Queue

- **FR-007** [MUST]: Jobs MUST support statuses: `queued`, `running`, `succeeded`, `failed`, `cancelled`, `retry_wait`. Transitions MUST follow the state machine: `queued -> running -> succeeded|failed|retry_wait`, `retry_wait -> running`, `queued|running|retry_wait -> cancelled`. *Implemented in `services/jobs.py`.*

- **FR-008** [MUST]: Job idempotency MUST be enforced via a unique constraint on `(job_type, idempotency_key)`. Duplicate submissions MUST return the existing job. *Implemented in `services/jobs.py` lines 36-44; `models.py` lines 227-229.*

- **FR-009** [MUST]: Failed jobs with remaining attempts MUST be retried with exponential backoff: `[2, 10, 30]` seconds. *Implemented in `services/jobs.py` `RETRY_BACKOFF_SECONDS` line 14, logic lines 167-170.*

- **FR-010** [MUST]: Each job attempt MUST be recorded as a `JobAttempt` with `attempt_number`, `status`, `error_text`, `started_at`, `finished_at`, and `runtime_ms`. *Implemented in `services/jobs.py` lines 146-178.*

- **FR-011** [MUST]: Successful jobs MUST produce `JobArtifact` records typed by `job_type` (e.g., `ingest_batch_result`, `analyze_result`, `branch_replay_result`). *Implemented in `services/jobs.py` `_create_artifacts()` lines 234-258.*

- **FR-012** [MUST]: Job dispatch MUST support four types: `ingest_batch`, `analyze`, `branch_replay`, `integrity_audit`. Unsupported types MUST raise `ValueError`. *Implemented in `services/jobs.py` `_dispatch()` lines 182-232.*

- **FR-013** [MUST]: Cancelling a terminal job (`succeeded`, `failed`, `cancelled`) MUST be a no-op, returning the existing status. *Implemented in `services/jobs.py` lines 64-65.*

- **FR-014** [MUST]: Job leasing MUST select the oldest eligible job (`status IN (queued, retry_wait)`, `next_run_at <= now`, `lease_expires_at IS NULL OR < now`) and set `lease_owner` and `lease_expires_at`. *Implemented in `services/jobs.py` `lease_next()` lines 116-133.*

- **FR-015** [SHOULD]: Stale leases (expired `lease_expires_at` on `running` jobs) SHOULD be recovered by transitioning to `retry_wait` or `failed` based on remaining attempts. *Implemented in `services/jobs.py` `complete_stale_leases()` lines 260-275.*

### Worker

- **FR-016** [MUST]: The worker MUST create a full application instance and poll using a blocking loop. *Implemented in `worker.py` lines 9-35.*

- **FR-017** [MUST]: The worker MUST support `--once` (single job) and `--max-jobs N` (bounded execution) flags. *Implemented in `worker.py` lines 38-44.*

- **FR-018** [MUST]: The worker MUST recover stale leases before each poll cycle. *Implemented in `worker.py` line 17.*

- **FR-019** [MUST]: The worker MUST handle exceptions per-job without crashing; failed sessions MUST be rolled back. *Implemented in `worker.py` lines 23-25.*

### Metrics

- **FR-020** [MUST]: The `MetricsService` MUST provide `inc(key, value)` for counters and `observe(key, value_ms)` for timing histograms. *Implemented in `services/metrics.py` lines 12-16.*

- **FR-021** [MUST]: `snapshot()` MUST return `{"counters": {...}, "timings": {key: {"count", "avg_ms", "p95_ms"}}}`. *Implemented in `services/metrics.py` lines 18-31.*

- **FR-022** [MUST]: HTTP middleware MUST record `http.request.ms` and `http.status.{code}` for every request. *Implemented in `main.py` lines 83-85.*

- **FR-023** [SHOULD]: The metrics endpoint (`GET /metrics`) SHOULD NOT require authentication. *Implemented in `main.py` lines 99-101.*

### Plugin Framework

- **FR-024** [MUST]: The `PluginRegistry` MUST support three profiles: `deterministic` (deterministic only), `ml_first` (ML stub then deterministic fallback), `ml_only` (ML stub only). *Implemented in `services/plugins.py` `_profile_chain()` lines 102-108.*

- **FR-025** [MUST]: `run_layer()` MUST return a `PluginExecution` with `output`, `confidence`, `provider_name`, `provider_version`, `runtime_ms`, and optional `fallback_reason`. *Implemented in `services/plugins.py` lines 110-157.*

- **FR-026** [MUST]: Plugin exceptions MUST be caught per-plugin and trigger fallback to the next plugin in the chain. *Implemented in `services/plugins.py` lines 146-148.*

- **FR-027** [MUST]: The `MLStubLayerPlugin` MUST be gated by the `plugin_ml_enabled` feature flag. When disabled, `healthcheck()` returns `False` and `supports()` returns `False`. *Implemented in `services/plugins.py` lines 65-72.*

### Configuration

- **FR-028** [MUST]: All application configuration MUST be in a single `Settings` class using `pydantic-settings` with `NEXUS_` env prefix. *Implemented in `config.py` lines 11-43.*

- **FR-029** [MUST]: Settings MUST support `.env` file loading. *Implemented in `config.py` line 12.*

- **FR-030** [MUST]: The `environment` field MUST be restricted to `Literal["dev", "test", "prod"]`. *Implemented in `config.py` line 15.*

- **FR-031** [SHOULD]: Feature flags (`raw_mode_enabled`, `async_jobs_enabled`, `plugin_ml_enabled`, `shadow_execution_enabled`) SHOULD default to safe values (RAW on, async on, ML off, shadow off). *Implemented in `config.py` lines 20-23.*

### Database

- **FR-032** [MUST]: `DBManager` MUST create a SQLAlchemy engine with `future=True` and a sessionmaker with `autoflush=False, autocommit=False`. *Implemented in `db.py` lines 16-17.*

- **FR-033** [MUST]: For SQLite, `check_same_thread=False` MUST be passed to allow multi-threaded access. *Implemented in `db.py` lines 14-15.*

- **FR-034** [SHOULD]: Database migrations SHOULD be managed via Alembic. Existing migrations: `20260218_0001_initial`, `20260218_0002_wave2_alpha`, `20260223_0003_add_atom_metadata`. *Implemented in `alembic/versions/`.*

### Application Lifecycle

- **FR-035** [MUST]: The `create_app()` factory MUST wire all services onto `app.state` and seed bootstrap data in the lifespan handler. *Implemented in `main.py` lines 29-110.*

- **FR-036** [MUST]: The lifespan handler MUST call `db.create_all()` and `ensure_default_api_keys()` before yielding. *Implemented in `main.py` lines 35-50.*

- **FR-037** [MUST]: The lifespan handler MUST close the hypergraph connection on shutdown. *Implemented in `main.py` line 52.*

- **FR-038** [SHOULD]: Non-API routes (`/healthz`, `/metrics`, `/app/{view}`, `/`) SHOULD NOT require authentication. *Implemented in `main.py` lines 91-108.*

## Key Entities

### ApiKey (`api_keys` table)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `String(36)` PK | UUID, auto-generated |
| `key_hash` | `String(128)` UNIQUE INDEX | SHA-256 hash of plaintext key |
| `owner` | `String(128)` INDEX | Human-readable owner identifier |
| `role` | `String(32)` INDEX | One of: viewer, operator, researcher, admin |
| `enabled` | `Boolean` | Default `True`; disabled keys fail auth |
| `raw_mode_enabled` | `Boolean` | Default `False`; per-key RAW mode flag |
| `created_at` | `DateTime(tz)` | UTC timestamp |
| `last_used_at` | `DateTime(tz)` NULLABLE | Updated on each successful auth |

### Job (`jobs` table)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `String(36)` PK | UUID, auto-generated |
| `job_type` | `String(64)` INDEX | One of: ingest_batch, analyze, branch_replay, integrity_audit |
| `status` | `String(32)` INDEX | queued, running, succeeded, failed, cancelled, retry_wait |
| `payload` | `JSON` | Job-type-specific input |
| `result` | `JSON` | Job-type-specific output (on success) |
| `error_text` | `Text` NULLABLE | Last error message |
| `execution_mode` | `String(16)` | async or sync |
| `idempotency_key` | `String(128)` NULLABLE | Unique with job_type (`uq_job_idempotency`) |
| `max_attempts` | `Integer` | Default 3 |
| `attempt_count` | `Integer` | Current attempt number |
| `next_run_at` | `DateTime(tz)` INDEX | When the job becomes eligible |
| `lease_owner` | `String(128)` NULLABLE | Worker holding the lease |
| `lease_expires_at` | `DateTime(tz)` NULLABLE | Lease expiry |
| `created_by` | `String(128)` NULLABLE | Auth context owner |
| `created_at` | `DateTime(tz)` | Auto |
| `updated_at` | `DateTime(tz)` | Auto, onupdate |

### JobAttempt (`job_attempts` table)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `String(36)` PK | UUID |
| `job_id` | FK -> `jobs.id` CASCADE | Parent job |
| `attempt_number` | `Integer` | 1-based |
| `status` | `String(32)` | running, succeeded, failed |
| `error_text` | `Text` NULLABLE | Per-attempt error |
| `started_at` | `DateTime(tz)` | Auto |
| `finished_at` | `DateTime(tz)` NULLABLE | Set on completion |
| `runtime_ms` | `Integer` NULLABLE | Execution time |

### JobArtifact (`job_artifacts` table)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `String(36)` PK | UUID |
| `job_id` | FK -> `jobs.id` CASCADE | Parent job |
| `artifact_type` | `String(64)` | e.g., `ingest_batch_result`, `analyze_result` |
| `artifact_ref` | `String(512)` NULLABLE | External reference (unused currently) |
| `artifact_payload` | `JSON` | Structured artifact data |
| `created_at` | `DateTime(tz)` | Auto |

### User (`users` table)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `String(36)` PK | UUID |
| `username` | `String(128)` UNIQUE | |
| `role` | `String(64)` | Default "researcher" |
| `created_at` | `DateTime(tz)` | Auto |

### AuditLog (`audit_logs` table)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `String(36)` PK | UUID |
| `action` | `String(128)` INDEX | Event type |
| `mode` | `String(16)` INDEX | PUBLIC or RAW |
| `actor` | `String(128)` | Default "system" |
| `details` | `JSON` | Event-specific data |
| `created_at` | `DateTime(tz)` | Auto |

## Edge Cases

### Authentication

- **EC-01**: Empty string API key (not null) should still return 401 -- covered by `hash_api_key("")` producing a valid hash that won't match any stored key.
- **EC-02**: Disabled key re-enabled at next startup if it matches a bootstrap key hash. No test coverage for this path.
- **EC-03**: Concurrent authentication requests updating `last_used_at` -- no locking; potential lost-update on high concurrency (SQLite single-writer mitigates).

### Job Queue

- **EC-04**: Idempotency key collision across different `job_type` values -- the unique constraint is on `(job_type, idempotency_key)`, so same key with different types creates separate jobs. Correctly handled.
- **EC-05**: Job with `max_attempts=1` fails on first try -- should go directly to `failed`, not `retry_wait`. Correctly handled (`attempt_count=1 < max_attempts=1` is false).
- **EC-06**: Worker crash during `session.commit()` after `execute()` -- job remains `running` with active lease; recovered by `complete_stale_leases()` after lease expiry. GAP: No test coverage.
- **EC-07**: `integrity_audit` job type with zero ingested documents -- returns `{"document_count": 0, "inconsistencies": []}`. Correctly handled.
- **EC-08**: Cancelling an already-cancelled job -- returns the job unchanged (no-op). Correctly handled.

### Worker

- **EC-09**: Worker started with no database -- `create_app()` will fail during `db.create_all()`. Unhandled; will crash with a database connection error.
- **EC-10**: Worker poll with `worker_poll_seconds=0` -- clamped to `0.1` by `max(settings.worker_poll_seconds, 0.1)`.

### Metrics

- **EC-11**: `snapshot()` called with no data -- returns `{"counters": {}, "timings": {}}`. Correctly handled.
- **EC-12**: Timing key with empty values list -- returns `{"count": 0, "avg_ms": 0.0, "p95_ms": 0.0}`. Correctly handled (line 22).
- **EC-13**: Metrics are in-memory only -- all data lost on process restart. Acceptable for dev; not production-ready.

### Configuration

- **EC-14**: Missing `.env` file -- `pydantic-settings` uses defaults; no error. Correctly handled.
- **EC-15**: Invalid `environment` value (not dev/test/prod) -- pydantic validation error at startup. Correctly handled.
- **EC-16**: `corpus_root` pointing to non-existent directory -- no startup validation; will fail at ingestion time. GAP.

## Success Criteria

| Criterion | Metric | Target |
|-----------|--------|--------|
| Auth coverage | All protected routes return 401 without key, 403 with insufficient role | 100% route coverage |
| Job lifecycle | Submit -> Execute -> Succeed/Fail/Cancel state transitions verified | All 6 statuses tested |
| Retry correctness | Backoff delays match `[2, 10, 30]s` schedule | Exact match in tests |
| Idempotency | Duplicate submission returns same job_id | Verified in `test_wave2.py` |
| Metrics accuracy | p95 calculation matches independent verification | Within 1ms tolerance |
| Worker reliability | `--once` and `--max-jobs` exit correctly | Verified in integration |
| Plugin fallback | ML failure falls back to deterministic | Full chain tested |
| Zero-downtime bootstrap | Existing keys not duplicated on restart | Idempotent seeding verified |
| Configuration validation | Invalid settings rejected at startup | Type errors caught by pydantic |
