# Platform Infrastructure -- Task List

## Phase 1: Setup

### TASK-INFRA-001: Verify existing tests pass [P]
- Run `pytest tests/test_mvp.py tests/test_wave2.py tests/test_arc4n.py -v` and confirm all pass
- Document any failures for investigation
- **Files:** `tests/test_mvp.py`, `tests/test_wave2.py`, `tests/test_arc4n.py`
- **Estimate:** 5 min

### TASK-INFRA-002: Audit current test coverage for this domain [P]
- Run `pytest --cov=src/nexus_babel/services/auth --cov=src/nexus_babel/services/jobs --cov=src/nexus_babel/services/metrics --cov=src/nexus_babel/services/plugins --cov=src/nexus_babel/worker --cov=src/nexus_babel/config --cov=src/nexus_babel/db --cov-report=term-missing`
- Record per-file coverage percentages and uncovered line ranges
- Use results to prioritize gap-filling tasks
- **Depends on:** TASK-INFRA-001
- **Estimate:** 10 min

## Phase 2: Foundational (Schema and Migration Prereqs)

### TASK-INFRA-003: Verify Alembic migrations are up to date with models [P]
- Run `alembic upgrade head` against a fresh SQLite database
- Compare `alembic/versions/` head state against `models.py` table definitions
- Check for any model fields missing from migrations (e.g., `BranchCheckpoint`, `DocumentVariant` added post-initial)
- **Files:** `alembic/versions/*.py`, `src/nexus_babel/models.py`
- **Estimate:** 15 min

### TASK-INFRA-004: Document the Job state machine formally [P]
- Create or update a state diagram in the spec showing all valid transitions
- Verify the code matches: `queued -> running -> succeeded|failed|retry_wait`, `retry_wait -> running`, `* -> cancelled`
- Cross-reference with `services/jobs.py` lines 60-69 (cancel), 142-180 (execute), 116-133 (lease_next)
- **Files:** `src/nexus_babel/services/jobs.py`
- **Estimate:** 15 min

## Phase 3: P1 Story Verification and Gap Coverage

### TASK-INFRA-010: Add dedicated MetricsService unit tests [Story: US-INFRA-12]
- Test `inc()` with default and custom values
- Test `observe()` appending to histogram
- Test `snapshot()` with no data, single data point, and multiple data points
- Verify p95 calculation: for [1, 2, 3, ..., 100], p95 should be 95
- Test that counter keys are isolated
- **Files:** Create `tests/test_metrics.py`; reference `src/nexus_babel/services/metrics.py`
- **Estimate:** 30 min

### TASK-INFRA-011: Add dedicated AuthService unit tests [Story: US-INFRA-01, US-INFRA-02] [P]
- Test `hash_api_key()` produces consistent SHA-256 hex output
- Test `authenticate()` returns `None` for empty string, `None` for unknown key, valid `AuthContext` for known key
- Test `authenticate()` updates `last_used_at`
- Test `authenticate()` returns `None` for disabled key
- Test `role_allows()` for all role pairs (16 combinations)
- Test `mode_allows()` for PUBLIC and RAW with all flag combinations
- Test `ensure_default_api_keys()` idempotency: run twice, verify no duplicates, verify re-enable of disabled key
- **Files:** Create `tests/test_auth_service.py`; reference `src/nexus_babel/services/auth.py`
- **Estimate:** 45 min

### TASK-INFRA-012: Add dedicated PluginRegistry unit tests [Story: US-INFRA-15] [P]
- Test `_profile_chain()` returns correct order for deterministic, ml_first, ml_only, None, and unknown string
- Test `run_layer()` with deterministic profile: returns baseline output, provider=deterministic
- Test `run_layer()` with ml_first + ml_enabled=True: returns enriched output, provider=ml_stub
- Test `run_layer()` with ml_first + ml_enabled=False: falls back to deterministic, fallback_reason populated
- Test `run_layer()` with ml_only + ml_enabled=False: returns baseline with fallback_reason=all_plugins_failed
- Test `health()` returns correct status for each plugin
- Test `DeterministicLayerPlugin.supports()` accepts all modalities including "binary"
- Test `MLStubLayerPlugin.supports()` rejects when disabled
- Test `MLStubLayerPlugin.run()` raises RuntimeError when disabled
- **Files:** Create `tests/test_plugins.py`; reference `src/nexus_babel/services/plugins.py`
- **Estimate:** 45 min

### TASK-INFRA-013: Add stale lease recovery tests [Story: US-INFRA-10]
- Create a job, manually set `status=running`, `lease_expires_at` to past
- Call `complete_stale_leases()` and verify transition to `retry_wait` with correct `next_run_at`
- Repeat with `attempt_count=max_attempts` and verify transition to `failed`
- Verify the recovery worker name is set as `lease_owner`
- **Files:** Add to `tests/test_wave2.py` or create `tests/test_jobs_service.py`; reference `src/nexus_babel/services/jobs.py` lines 260-275
- **Estimate:** 30 min

### TASK-INFRA-014: Add worker --once and --max-jobs integration tests [Story: US-INFRA-09]
- Test `run_worker(once=True)` processes exactly one job and returns 1
- Test `run_worker(max_jobs=3)` with 5 queued jobs: processes 3 and returns 3
- Test `run_worker(once=True)` with no jobs: returns 0
- Use test settings with SQLite in tmp_path
- **Files:** Create `tests/test_worker.py`; reference `src/nexus_babel/worker.py`
- **Estimate:** 30 min

### TASK-INFRA-015: Add job dispatch and artifact tests for all job types [Story: US-INFRA-08]
- Test `_dispatch()` for `ingest_batch`: verify it calls `ingestion_service.ingest_batch()` and returns correct keys
- Test `_dispatch()` for `analyze`: verify it calls `analysis_service.analyze()` and returns correct keys
- Test `_dispatch()` for `branch_replay`: verify it calls `evolution_service.replay_branch()`
- Test `_dispatch()` for `integrity_audit`: verify it iterates documents and checks integrity
- Test `_dispatch()` for unsupported type raises `ValueError`
- Test `_create_artifacts()` creates correct `JobArtifact` records for each type
- Test `_create_artifacts()` creates no artifact for `integrity_audit`
- **Files:** Add to `tests/test_jobs_service.py`; reference `src/nexus_babel/services/jobs.py` lines 182-258
- **Estimate:** 60 min

### TASK-INFRA-016: Add retry backoff schedule verification test [Story: US-INFRA-07]
- Submit a job that will fail (e.g., invalid payload for analyze)
- Execute it repeatedly, recording `next_run_at` offsets
- Verify attempt 1 failure sets next_run_at += 2s
- Verify attempt 2 failure sets next_run_at += 10s
- Verify attempt 3 failure transitions to `failed` (no retry)
- **Files:** Add to `tests/test_jobs_service.py`; reference `src/nexus_babel/services/jobs.py` lines 163-174, `RETRY_BACKOFF_SECONDS`
- **Estimate:** 30 min

### TASK-INFRA-017: Add request tracking middleware tests [Story: US-INFRA-14]
- Make a request without `X-Request-ID`: verify response has `X-Request-ID` header with a valid UUID
- Make a request with `X-Request-ID: custom-123`: verify response echoes `X-Request-ID: custom-123`
- Verify `request.state.request_id` is set (may need middleware introspection or a test endpoint)
- **Files:** Add to `tests/test_mvp.py` or create `tests/test_middleware.py`; reference `src/nexus_babel/main.py` lines 78-87
- **Estimate:** 20 min

### TASK-INFRA-018: Add metrics endpoint integration test [Story: US-INFRA-12, US-INFRA-13]
- Call `/healthz` and verify 200 + `{"status": "ok"}`
- Make several requests to various endpoints
- Call `/metrics` and verify `counters` contains `http.status.200` and `timings` contains `http.request.ms` with correct structure
- Verify `/metrics` requires no auth
- **Files:** Add to `tests/test_mvp.py` or create `tests/test_infra_endpoints.py`; reference `src/nexus_babel/main.py` lines 95-101
- **Estimate:** 20 min

### TASK-INFRA-019: Add config validation tests [Story: US-INFRA-16]
- Test default `Settings()` produces valid defaults for all fields
- Test `Settings(environment="invalid")` raises validation error
- Test `Settings(database_url="postgresql://...")` is accepted
- Test `Settings(max_attempts=0)` -- note this is on the schema, not settings; verify schema-level validation
- Test `get_settings()` caching: call twice, verify same instance
- **Files:** Create `tests/test_config.py`; reference `src/nexus_babel/config.py`
- **Estimate:** 20 min

### TASK-INFRA-020: Add DBManager unit tests [Story: US-INFRA-17]
- Test SQLite URL sets `check_same_thread=False`
- Test PostgreSQL-style URL does not set `check_same_thread`
- Test `session()` returns a valid `Session` object
- Test `create_all()` creates tables on a fresh in-memory SQLite database
- **Files:** Create `tests/test_db.py`; reference `src/nexus_babel/db.py`
- **Estimate:** 20 min

### TASK-INFRA-021: Add bootstrap key seeding integration test [Story: US-INFRA-03]
- Start app, verify 4 keys exist with correct roles and raw_mode_enabled flags
- Disable one key manually, restart app, verify it is re-enabled
- Verify no duplicate keys after multiple restarts
- **Files:** Add to `tests/test_mvp.py` or create `tests/test_bootstrap.py`; reference `src/nexus_babel/main.py` lines 38-45, `src/nexus_babel/services/auth.py` lines 34-51
- **Estimate:** 20 min

## Phase 4: P2 Story Implementation

### TASK-INFRA-030: Add job list filtering by status, type, and date [Story: US-INFRA-19]
- Add query parameters to `GET /api/v1/jobs`: `status` (optional str), `job_type` (optional str), `created_by` (optional str), `created_after` (optional datetime), `created_before` (optional datetime)
- Update the SQLAlchemy query in `api/routes.py` `list_jobs()` (lines 506-527) to apply WHERE clauses
- Add `offset` parameter for pagination (in addition to existing `limit`)
- Write tests verifying each filter individually and in combination
- **Files:** `src/nexus_babel/api/routes.py`, `tests/test_wave2.py`
- **Estimate:** 60 min

### TASK-INFRA-031: Add shadow execution test coverage [Story: US-INFRA-18]
- Enable `shadow_execution_enabled=True` in test settings
- Submit an analysis with `execution_mode=shadow`
- Verify the primary (sync) result is returned immediately
- Verify a shadow job was created with `execution_mode=async`
- Process the shadow job and verify it produces its own analysis run
- **Files:** Add to `tests/test_wave2.py`; reference `src/nexus_babel/api/routes.py` lines 194-209
- **Estimate:** 30 min

### TASK-INFRA-032: Add shadow result comparison mechanism [Story: US-INFRA-18]
- Add `shadow_job_id` field to `AnalysisRun` model (nullable FK to `jobs.id`)
- Update analysis route to record the link between primary run and shadow job
- Add `GET /api/v1/analysis/runs/{id}/shadow` endpoint that returns the shadow run's results alongside the primary
- Write tests for the comparison endpoint
- **Files:** `src/nexus_babel/models.py`, `src/nexus_babel/api/routes.py`, `src/nexus_babel/services/analysis.py`
- **Requires migration:** Yes (new column on `analysis_runs`)
- **Estimate:** 90 min

### TASK-INFRA-033: Add stale lease audit trail [Story: US-INFRA-20]
- In `complete_stale_leases()`, before overwriting `lease_owner`, log the original owner to `AuditLog` with `action=stale_lease_recovery`
- Include `details`: `{"job_id", "original_lease_owner", "recovering_worker", "new_status"}`
- Write tests verifying audit log entries are created on stale recovery
- **Files:** `src/nexus_babel/services/jobs.py` lines 260-275, `src/nexus_babel/models.py` (AuditLog)
- **Estimate:** 30 min

## Phase 5: P3 Vision Stories

### TASK-INFRA-040: Implement per-API-key rate limiting [Story: US-INFRA-21]
- Research FastAPI rate limiting libraries (`slowapi`, `fastapi-limiter`, or custom middleware)
- Add `rate_limit_per_minute` field to `ApiKey` model (nullable, defaults to role-based)
- Add `rate_limit_defaults` dict to `Settings` (per-role defaults)
- Implement middleware that checks rate limits before auth processing
- Return HTTP 429 with `Retry-After` header on limit exceeded
- Write tests for rate limit enforcement and per-key overrides
- **Files:** `src/nexus_babel/models.py`, `src/nexus_babel/config.py`, `src/nexus_babel/main.py`, new `src/nexus_babel/services/rate_limit.py`
- **Requires migration:** Yes (new column on `api_keys`)
- **Estimate:** 4 hours

### TASK-INFRA-041: Implement JWT token authentication [Story: US-INFRA-22]
- Add `POST /api/v1/auth/token` endpoint: accepts API key, returns signed JWT with claims (role, modes, exp)
- Add `POST /api/v1/auth/token/refresh` endpoint: accepts valid JWT, returns new JWT
- Update `_require_auth()` to accept both `X-Nexus-API-Key` and `Authorization: Bearer <jwt>` headers
- Add JWT signing key to Settings (`NEXUS_JWT_SECRET`, `NEXUS_JWT_ALGORITHM`, `NEXUS_JWT_EXPIRY_MINUTES`)
- Use `python-jose` or `PyJWT` for token handling
- Write comprehensive tests for token issuance, expiry, refresh, and invalid tokens
- **Files:** `src/nexus_babel/services/auth.py`, `src/nexus_babel/api/routes.py`, `src/nexus_babel/config.py`
- **Estimate:** 6 hours

### TASK-INFRA-042: Implement structured logging [Story: US-INFRA-23]
- Replace print statements in worker with `structlog` or `logging` JSON formatter
- Add request_id, worker_name, job_id as structured context fields
- Configure log level via `NEXUS_LOG_LEVEL` setting
- Add log entries at key points: auth success/failure, job submit/execute/complete/fail, stale lease recovery
- Write tests verifying log output format
- **Files:** New `src/nexus_babel/logging_config.py`, `src/nexus_babel/config.py`, `src/nexus_babel/main.py`, `src/nexus_babel/worker.py`
- **Estimate:** 4 hours

### TASK-INFRA-043: Implement OpenTelemetry integration [Story: US-INFRA-23]
- Add `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-sqlalchemy` dependencies
- Create tracer provider configuration in `main.py` lifespan
- Add manual spans for job execution, plugin runs, and ingestion pipeline
- Propagate `X-Request-ID` as trace baggage
- Configure OTLP exporter endpoint via `NEXUS_OTLP_ENDPOINT` setting
- **Files:** `src/nexus_babel/main.py`, `src/nexus_babel/config.py`, `src/nexus_babel/services/jobs.py`, `src/nexus_babel/services/plugins.py`
- **Estimate:** 6 hours

### TASK-INFRA-044: Implement Prometheus metrics export [Story: US-INFRA-24]
- Add `/metrics/prometheus` endpoint returning text/plain Prometheus exposition format
- Convert in-memory counters to `# TYPE ... counter` format
- Convert timing histograms to Prometheus histogram buckets or summary format
- Add job-specific gauges: `nexus_jobs_queued`, `nexus_jobs_running` (queried from DB)
- Alternatively, adopt `prometheus-fastapi-instrumentator` for automatic HTTP metrics
- Write tests verifying Prometheus format output
- **Files:** `src/nexus_babel/main.py`, `src/nexus_babel/services/metrics.py`
- **Estimate:** 3 hours

### TASK-INFRA-045: Implement worker horizontal scaling [Story: US-INFRA-25]
- Replace `SELECT ... LIMIT 1` in `lease_next()` with `SELECT ... FOR UPDATE SKIP LOCKED` (PostgreSQL only)
- Add SQLite fallback that uses existing single-writer behavior
- Generate worker identity from `{hostname}-{pid}-{uuid[:8]}` instead of static `worker_name`
- Add worker heartbeat: update a `worker_heartbeats` table every N seconds
- Add `GET /api/v1/workers` admin endpoint listing active workers
- Add graceful shutdown via SIGTERM handler in worker.py
- Write concurrent worker tests using threading or multiprocessing
- **Files:** `src/nexus_babel/services/jobs.py`, `src/nexus_babel/worker.py`, `src/nexus_babel/models.py`, `src/nexus_babel/api/routes.py`
- **Requires migration:** Yes (new `worker_heartbeats` table)
- **Estimate:** 8 hours

### TASK-INFRA-046: Expose database connection pool settings [Story: US-INFRA-26]
- Add to Settings: `db_pool_size` (default 5), `db_max_overflow` (default 10), `db_pool_recycle` (default 3600), `db_pool_pre_ping` (default True)
- Apply settings in `DBManager.__post_init__()` when URL is not SQLite
- Add pool metrics to `GET /metrics`: `db.pool.size`, `db.pool.checked_out`, `db.pool.overflow`
- Write tests verifying pool settings are applied
- **Files:** `src/nexus_babel/config.py`, `src/nexus_babel/db.py`, `src/nexus_babel/services/metrics.py`
- **Estimate:** 2 hours

### TASK-INFRA-047: Implement role-based feature gating [Story: US-INFRA-27]
- Create `FeatureFlag` model: `name`, `min_role`, `enabled`, `description`
- Add `GET /api/v1/features` endpoint: returns features available to the caller's role
- Implement `feature_enabled(name, role) -> bool` helper in auth service
- Gate existing features: `shadow_execution` (researcher+), `ml_plugins` (admin), `raw_mode` (researcher+)
- Seed default feature flags in lifespan handler
- Write tests for feature visibility per role
- **Files:** `src/nexus_babel/models.py`, `src/nexus_babel/services/auth.py`, `src/nexus_babel/api/routes.py`, `src/nexus_babel/main.py`
- **Requires migration:** Yes (new `feature_flags` table)
- **Estimate:** 4 hours

## Phase 6: Cross-Cutting

### TASK-INFRA-050: Add CI test job for platform infrastructure tests [P]
- Update `.github/workflows/ci-minimal.yml` (or create new workflow) to run `pytest tests/test_auth_service.py tests/test_plugins.py tests/test_metrics.py tests/test_worker.py tests/test_config.py tests/test_db.py -v`
- Ensure `pip install -e ".[dev]"` runs before tests
- Add coverage reporting with minimum threshold (suggest 80%)
- **Files:** `.github/workflows/ci-minimal.yml` or new workflow file
- **Estimate:** 30 min

### TASK-INFRA-051: Add ruff linting for platform infrastructure files [P]
- Configure ruff in `pyproject.toml` if not already present
- Run `ruff check src/nexus_babel/services/auth.py src/nexus_babel/services/jobs.py src/nexus_babel/services/metrics.py src/nexus_babel/services/plugins.py src/nexus_babel/worker.py src/nexus_babel/config.py src/nexus_babel/db.py src/nexus_babel/main.py`
- Fix any violations
- Add to CI workflow
- **Files:** `pyproject.toml`, all platform infrastructure source files
- **Estimate:** 30 min

### TASK-INFRA-052: Add mypy type checking for platform infrastructure [P]
- Configure mypy in `pyproject.toml` if not already present
- Run `mypy src/nexus_babel/services/auth.py src/nexus_babel/services/jobs.py src/nexus_babel/services/metrics.py src/nexus_babel/services/plugins.py src/nexus_babel/worker.py src/nexus_babel/config.py src/nexus_babel/db.py`
- Fix any type errors
- Add to CI workflow
- **Files:** `pyproject.toml`, all platform infrastructure source files
- **Estimate:** 45 min

### TASK-INFRA-053: Refactor route session management to use dependency injection [P]
- Create a `get_session` FastAPI dependency that yields a session and handles commit/rollback/close
- Refactor all routes in `api/routes.py` to use `session: Session = Depends(get_session)` instead of manual `_session(request)` + try/finally blocks
- Verify all existing tests still pass
- **Files:** `src/nexus_babel/api/routes.py`, `src/nexus_babel/db.py`
- **Estimate:** 90 min

### TASK-INFRA-054: Add auth audit logging [P]
- Log successful authentications to `AuditLog` with `action=auth_success`
- Log authentication failures (invalid key, disabled key) with `action=auth_failure`
- Log role-based access denials with `action=auth_denied`
- Include `details`: `{"key_hash_prefix", "role", "required_role", "endpoint"}`
- Write tests verifying audit entries
- **Files:** `src/nexus_babel/services/auth.py`, `src/nexus_babel/api/routes.py`
- **Estimate:** 45 min

### TASK-INFRA-055: Validate corpus_root exists at startup [P]
- In the lifespan handler, check that `settings.corpus_root` is a valid directory
- Log a warning (not a crash) if it does not exist, since it may be created later
- In `IngestionService`, raise a clear error if corpus_root is missing at ingest time
- **Files:** `src/nexus_babel/main.py`, `src/nexus_babel/services/ingestion.py`
- **Estimate:** 15 min

---

## Task Dependency Summary

```
Phase 1 (Setup)
  TASK-001 ──> TASK-002

Phase 2 (Foundation)
  TASK-003 [P] (independent)
  TASK-004 [P] (independent)

Phase 3 (P1 Verification) -- all can run in parallel after Phase 1
  TASK-010 [P] MetricsService tests
  TASK-011 [P] AuthService tests
  TASK-012 [P] PluginRegistry tests
  TASK-013 [P] Stale lease tests
  TASK-014 [P] Worker tests
  TASK-015 [P] Job dispatch/artifact tests
  TASK-016 [P] Retry backoff tests
  TASK-017 [P] Request tracking tests
  TASK-018 [P] Metrics endpoint tests
  TASK-019 [P] Config validation tests
  TASK-020 [P] DBManager tests
  TASK-021 [P] Bootstrap key tests

Phase 4 (P2 Implementation) -- can start after Phase 3 test baseline
  TASK-030 ──> (independent)
  TASK-031 ──> TASK-032 (shadow test before comparison mechanism)
  TASK-033 ──> (depends on TASK-013 for stale lease test foundation)

Phase 5 (P3 Vision) -- each independent, prioritize by value
  TASK-040 (rate limiting)
  TASK-041 (JWT)
  TASK-042 ──> TASK-043 (structured logging before OTel)
  TASK-044 (Prometheus -- depends on TASK-010 for metrics baseline)
  TASK-045 (worker scaling -- depends on TASK-014 for worker tests)
  TASK-046 (pool tuning)
  TASK-047 (feature gating)

Phase 6 (Cross-Cutting) -- can run in parallel, should come after Phase 3
  TASK-050 [P] CI integration
  TASK-051 [P] Ruff linting
  TASK-052 [P] Mypy typing
  TASK-053 [P] Session refactor
  TASK-054 [P] Auth audit logging
  TASK-055 [P] Corpus root validation
```

**Legend:** `[P]` = parallelizable with other tasks in the same phase. `-->` = depends on.
