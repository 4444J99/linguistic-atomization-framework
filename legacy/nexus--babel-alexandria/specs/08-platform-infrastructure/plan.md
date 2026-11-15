# Platform Infrastructure -- Implementation Plan

## Technical Context

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | >= 3.11 |
| Web Framework | FastAPI | latest |
| ORM | SQLAlchemy | 2.0 (mapped_column style) |
| Migrations | Alembic | latest |
| Settings | pydantic-settings | latest |
| Validation | Pydantic | v2 |
| Testing | pytest + FastAPI TestClient | latest |
| Dev DB | SQLite | stdlib |
| Prod DB | PostgreSQL | via Docker Compose |
| Graph DB | Neo4j (optional) | via Docker Compose |

## Project Structure

```
src/nexus_babel/
  main.py                    # App factory, middleware, health/metrics, frontend shell
  config.py                  # Settings (pydantic-settings, NEXUS_ prefix)
  db.py                      # DBManager (engine + sessionmaker)
  models.py                  # ORM: ApiKey, User, Job, JobAttempt, JobArtifact, AuditLog, ...
  schemas.py                 # Pydantic: JobSubmitRequest/Response, JobStatusResponse, AuthContext
  worker.py                  # CLI worker with --once/--max-jobs
  api/
    routes.py                # All /api/v1/ endpoints (single router)
  services/
    auth.py                  # AuthService: authenticate, role_allows, mode_allows, seed keys
    jobs.py                  # JobService: submit, cancel, execute, lease, retry, artifacts
    metrics.py               # MetricsService: counters + timing histograms
    plugins.py               # PluginRegistry: deterministic + ML stub, profile chains
alembic/
  env.py                     # Alembic environment
  versions/
    20260218_0001_initial.py
    20260218_0002_wave2_alpha.py
    20260223_0003_add_atom_metadata.py
tests/
  conftest.py                # test_settings, client, auth_headers, sample_corpus fixtures
  test_mvp.py                # Auth, RBAC, ingestion, governance tests
  test_wave2.py              # Job lifecycle, idempotency, cancel, replay, audit tests
  test_arc4n.py              # Seed corpus, remix, syllable atom tests
```

## Data Models

### ApiKey

```python
# models.py lines 180-191
class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str]           = mapped_column(String(36), primary_key=True, default=uuid4)
    key_hash: Mapped[str]     = mapped_column(String(128), unique=True, index=True)
    owner: Mapped[str]        = mapped_column(String(128), index=True)
    role: Mapped[str]         = mapped_column(String(32), index=True)
    enabled: Mapped[bool]     = mapped_column(Boolean, default=True)
    raw_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]   = mapped_column(DateTime(tz=True), default=utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(tz=True), nullable=True)
```

**Indexes:** `key_hash` (unique, lookup), `owner` (admin queries), `role` (filtering).

**Auth flow:** Plaintext key -> SHA-256 -> lookup by `key_hash` where `enabled=True` -> return `AuthContext` dataclass.

### Job

```python
# models.py lines 204-229
class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str]               = mapped_column(String(36), PK)
    job_type: Mapped[str]         = mapped_column(String(64), index=True)
    status: Mapped[str]           = mapped_column(String(32), default="queued", index=True)
    payload: Mapped[dict]         = mapped_column(JSON, default=dict)
    result: Mapped[dict]          = mapped_column(JSON, default=dict)
    error_text: Mapped[str|None]  = mapped_column(Text, nullable=True)
    execution_mode: Mapped[str]   = mapped_column(String(16), default="async")
    idempotency_key: Mapped[str|None] = mapped_column(String(128), nullable=True)
    max_attempts: Mapped[int]     = mapped_column(Integer, default=3)
    attempt_count: Mapped[int]    = mapped_column(Integer, default=0)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(tz=True), index=True)
    lease_owner: Mapped[str|None] = mapped_column(String(128), nullable=True)
    lease_expires_at: Mapped[datetime|None] = mapped_column(DateTime(tz=True), nullable=True)
    created_by: Mapped[str|None]  = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime]  = mapped_column(DateTime(tz=True), default=utcnow)
    updated_at: Mapped[datetime]  = mapped_column(DateTime(tz=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (UniqueConstraint("job_type", "idempotency_key", name="uq_job_idempotency"),)
```

**State Machine:**

```
queued -------> running -------> succeeded
   |               |
   |               +-------> failed
   |               |
   |               +-------> retry_wait ----> running (re-leased)
   |
   +-------> cancelled (from queued, running, or retry_wait)
```

**Lease columns:** `lease_owner` (worker name), `lease_expires_at` (UTC). Lease acquisition: `SELECT ... WHERE status IN (queued, retry_wait) AND next_run_at <= now AND (lease_expires_at IS NULL OR lease_expires_at < now) ORDER BY created_at LIMIT 1`.

### JobAttempt

```python
# models.py lines 232-244
class JobAttempt(Base):
    __tablename__ = "job_attempts"

    id: Mapped[str]              = mapped_column(String(36), PK)
    job_id: Mapped[str]          = mapped_column(FK -> jobs.id CASCADE)
    attempt_number: Mapped[int]  = mapped_column(Integer)           # 1-based
    status: Mapped[str]          = mapped_column(String(32))        # running, succeeded, failed
    error_text: Mapped[str|None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(tz=True))
    finished_at: Mapped[datetime|None] = mapped_column(DateTime(tz=True), nullable=True)
    runtime_ms: Mapped[int|None] = mapped_column(Integer, nullable=True)
```

**Relationship:** `Job.attempts` (cascade all, delete-orphan).

### JobArtifact

```python
# models.py lines 247-257
class JobArtifact(Base):
    __tablename__ = "job_artifacts"

    id: Mapped[str]                  = mapped_column(String(36), PK)
    job_id: Mapped[str]              = mapped_column(FK -> jobs.id CASCADE)
    artifact_type: Mapped[str]       = mapped_column(String(64))
    artifact_ref: Mapped[str|None]   = mapped_column(String(512), nullable=True)
    artifact_payload: Mapped[dict]   = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime]     = mapped_column(DateTime(tz=True))
```

**Artifact types by job_type:**

| job_type | artifact_type | artifact_payload keys |
|----------|--------------|----------------------|
| `ingest_batch` | `ingest_batch_result` | `ingest_job_id`, `documents_ingested` |
| `analyze` | `analyze_result` | `analysis_run_id`, `layer_count` |
| `branch_replay` | `branch_replay_result` | `branch_id`, `text_hash` |
| `integrity_audit` | (none -- no artifact created) | -- |

### User

```python
# models.py lines 171-177
class User(Base):
    __tablename__ = "users"

    id: Mapped[str]           = mapped_column(String(36), PK)
    username: Mapped[str]     = mapped_column(String(128), unique=True)
    role: Mapped[str]         = mapped_column(String(64), default="researcher")
    created_at: Mapped[datetime] = mapped_column(DateTime(tz=True))
```

**Note:** The `User` model exists but is not currently used by the auth flow. Authentication is entirely API-key-based via the `ApiKey` model. The `User` model is a placeholder for future user management (P3+).

### AuditLog

```python
# models.py lines 193-201
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str]           = mapped_column(String(36), PK)
    action: Mapped[str]       = mapped_column(String(128), index=True)
    mode: Mapped[str]         = mapped_column(String(16), index=True)
    actor: Mapped[str]        = mapped_column(String(128), default="system")
    details: Mapped[dict]     = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(tz=True))
```

**Used by:** Governance service for policy decision audit trail. Not yet used by auth or job services.

## API Contracts

### POST /api/v1/jobs/submit

**Auth:** operator (minimum)

**Request (`JobSubmitRequest`):**
```json
{
  "job_type": "analyze",               // required: ingest_batch | analyze | branch_replay | integrity_audit
  "payload": {                          // required: job-type-specific input
    "document_id": "uuid",
    "mode": "PUBLIC",
    "plugin_profile": "deterministic"
  },
  "execution_mode": "async",           // optional: async (default) | sync | shadow
  "idempotency_key": "my-key-123",     // optional: dedup key (unique per job_type)
  "max_attempts": 3                    // optional: 1-10, default 3
}
```

**Response (`JobSubmitResponse`):**
```json
{
  "job_id": "uuid",
  "status": "queued",          // queued (async) or succeeded/failed (sync)
  "job_type": "analyze",
  "execution_mode": "async"
}
```

**Error cases:**
- 401: Missing/invalid API key
- 403: Insufficient role (< operator), or RAW mode not allowed for analyze jobs
- 400: Async jobs disabled (`NEXUS_ASYNC_JOBS_ENABLED=False`), or execution error (sync mode)

### GET /api/v1/jobs/{job_id}

**Auth:** viewer (minimum)

**Response (`JobStatusResponse`):**
```json
{
  "job_id": "uuid",
  "job_type": "analyze",
  "status": "succeeded",
  "payload": {},
  "result": {},
  "error_text": null,
  "execution_mode": "async",
  "idempotency_key": "my-key-123",
  "max_attempts": 3,
  "attempt_count": 1,
  "next_run_at": "2026-02-23T12:00:00Z",
  "lease_owner": null,
  "lease_expires_at": null,
  "created_by": "dev-operator",
  "created_at": "2026-02-23T12:00:00Z",
  "updated_at": "2026-02-23T12:00:05Z",
  "attempts": [
    {
      "attempt_number": 1,
      "status": "succeeded",
      "error_text": null,
      "runtime_ms": 42,
      "started_at": "2026-02-23T12:00:00Z",
      "finished_at": "2026-02-23T12:00:00Z"
    }
  ],
  "artifacts": [
    {
      "artifact_type": "analyze_result",
      "artifact_ref": null,
      "artifact_payload": {"analysis_run_id": "uuid", "layer_count": 9},
      "created_at": "2026-02-23T12:00:00Z"
    }
  ]
}
```

### GET /api/v1/jobs

**Auth:** viewer (minimum)

**Query params:** `limit` (1-1000, default 100)

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "uuid",
      "job_type": "analyze",
      "status": "succeeded",
      "execution_mode": "async",
      "attempt_count": 1,
      "max_attempts": 3,
      "created_at": "2026-02-23T12:00:00Z",
      "updated_at": "2026-02-23T12:00:05Z"
    }
  ]
}
```

### POST /api/v1/jobs/{job_id}/cancel

**Auth:** operator (minimum)

**Response:** `JobStatusResponse` (same as GET /api/v1/jobs/{id})

**Error cases:**
- 404: Job not found

### GET /api/v1/auth/whoami

**Auth:** viewer (minimum)

**Response:**
```json
{
  "api_key_id": "uuid",
  "owner": "dev-operator",
  "role": "operator",
  "raw_mode_enabled": false,
  "allowed_modes": ["PUBLIC"]
}
```

### GET /healthz

**Auth:** none

**Response:**
```json
{"status": "ok"}
```

### GET /metrics

**Auth:** none

**Response:**
```json
{
  "counters": {
    "http.status.200": 42.0,
    "http.status.401": 3.0
  },
  "timings": {
    "http.request.ms": {
      "count": 45,
      "avg_ms": 12.345,
      "p95_ms": 28.901
    }
  }
}
```

## Service Architecture

### AuthService (`services/auth.py`)

**Stateless service.** No constructor dependencies. All methods take a `Session` parameter for database access.

**Key methods:**

| Method | Signature | Purpose |
|--------|-----------|---------|
| `ensure_default_api_keys` | `(session, seed_keys: Iterable[tuple[str,str,str,bool]])` | Idempotent bootstrap seeding |
| `authenticate` | `(session, plaintext_key) -> AuthContext \| None` | Key lookup + context creation |
| `role_allows` | `(current_role, min_role) -> bool` | Numeric role comparison |
| `mode_allows` | `(current_role, mode, raw_mode_enabled, key_raw_mode_enabled) -> bool` | Dual-mode gate |

**Role hierarchy constant:** `ROLE_ORDER = {"viewer": 1, "operator": 2, "researcher": 3, "admin": 4}`

**AuthContext dataclass:**
```python
@dataclass
class AuthContext:
    api_key_id: str
    owner: str
    role: str
    raw_mode_enabled: bool
```

**Wiring:** Instantiated directly in `create_app()` (no constructor args). Used in `api/routes.py` via `_require_auth()` dependency and `_enforce_mode()` helper.

### JobService (`services/jobs.py`)

**Stateful service.** Constructor takes `settings`, `ingestion_service`, `analysis_service`, `evolution_service`, `hypergraph` -- wired in `create_app()` lines 69-75.

**Key methods:**

| Method | Signature | Purpose |
|--------|-----------|---------|
| `submit` | `(session, *, job_type, payload, execution_mode, idempotency_key, created_by, max_attempts) -> Job` | Create or return existing job |
| `cancel` | `(session, job_id) -> Job` | Transition to cancelled |
| `get_job` | `(session, job_id) -> dict` | Full job with attempts + artifacts |
| `lease_next` | `(session, worker_name) -> Job \| None` | Acquire lease on oldest eligible job |
| `process_next` | `(session, worker_name) -> Job \| None` | Lease + execute in one call |
| `execute` | `(session, job) -> Job` | Run dispatch, record attempt, handle retry |
| `complete_stale_leases` | `(session, worker_name) -> int` | Recover expired leases |
| `_dispatch` | `(session, job) -> dict` | Route to service by job_type |
| `_create_artifacts` | `(session, job, result) -> None` | Create typed artifact records |

**Retry backoff constant:** `RETRY_BACKOFF_SECONDS = [2, 10, 30]`

**Dispatch routing:**

| job_type | Service Method | Artifact Type |
|----------|---------------|---------------|
| `ingest_batch` | `ingestion_service.ingest_batch()` | `ingest_batch_result` |
| `analyze` | `analysis_service.analyze()` | `analyze_result` |
| `branch_replay` | `evolution_service.replay_branch()` | `branch_replay_result` |
| `integrity_audit` | (inline hypergraph check) | (none) |

### MetricsService (`services/metrics.py`)

**Stateful dataclass.** In-memory storage only. No persistence. Thread-safety not guaranteed (acceptable for single-process dev mode).

**State:**
- `counters: dict[str, float]` -- defaultdict(float)
- `timings: dict[str, list[float]]` -- defaultdict(list)

**Key methods:**

| Method | Signature | Purpose |
|--------|-----------|---------|
| `inc` | `(key, value=1.0)` | Increment counter |
| `observe` | `(key, value_ms)` | Append timing sample |
| `snapshot` | `() -> dict` | Export counters + timing summaries |

**p95 calculation:** Sort values, take index `max(0, int(len * 0.95) - 1)`.

### PluginRegistry (`services/plugins.py`)

**Stateful service.** Constructor takes `ml_enabled: bool`. Creates instances of `DeterministicLayerPlugin` and `MLStubLayerPlugin`.

**Key types:**

```python
@dataclass
class PluginExecution:
    output: dict[str, Any]
    confidence: float
    provider_name: str
    provider_version: str
    runtime_ms: int
    fallback_reason: str | None = None

class LayerPlugin(Protocol):
    name: str
    version: str
    modalities: set[str]
    def healthcheck(self) -> bool: ...
    def supports(self, layer: str, modality: str) -> bool: ...
    def run(self, layer, modality, text, baseline_output, context) -> tuple[dict, float]: ...
```

**Profile chains:**

| Profile | Plugin Order |
|---------|-------------|
| `deterministic` (default) | `[deterministic]` |
| `ml_first` | `[ml_stub, deterministic]` |
| `ml_only` | `[ml_stub]` |

**Plugin implementations:**

| Plugin | Name | Version | Modalities | Behavior |
|--------|------|---------|------------|----------|
| `DeterministicLayerPlugin` | `deterministic` | `v2.0` | text, pdf, image, audio, binary | Passthrough: returns baseline output at baseline confidence |
| `MLStubLayerPlugin` | `ml_stub` | `v0.1` | text, pdf, image, audio | Enriches output with `provider_note`, confidence += 0.1 (capped 0.95) |

### DBManager (`db.py`)

**Stateful dataclass.** Constructor takes `database_url: str`.

```python
@dataclass
class DBManager:
    database_url: str

    def __post_init__(self):
        connect_args = {"check_same_thread": False} if self.database_url.startswith("sqlite") else {}
        self.engine = create_engine(self.database_url, future=True, connect_args=connect_args)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, future=True)

    def create_all(self, metadata): ...
    def session(self) -> Session: ...
```

**Note:** No connection pooling configuration is exposed. SQLAlchemy defaults are used. For PostgreSQL, this means `pool_size=5`, `max_overflow=10`.

### Application Factory (`main.py`)

**`create_app(settings_override=None) -> FastAPI`**

1. Resolve settings (override or `get_settings()`)
2. Create `FastAPI` instance with lifespan handler
3. Wire all services onto `app.state`:
   - `app.state.settings` -- Settings instance
   - `app.state.db` -- DBManager
   - `app.state.hypergraph` -- HypergraphProjector
   - `app.state.metrics` -- MetricsService
   - `app.state.auth_service` -- AuthService
   - `app.state.plugin_registry` -- PluginRegistry
   - `app.state.rhetorical_analyzer` -- RhetoricalAnalyzer
   - `app.state.analysis_service` -- AnalysisService
   - `app.state.governance_service` -- GovernanceService
   - `app.state.evolution_service` -- EvolutionService
   - `app.state.ingestion_service` -- IngestionService
   - `app.state.remix_service` -- RemixService
   - `app.state.seed_corpus_service` -- SeedCorpusService
   - `app.state.job_service` -- JobService
4. Register HTTP middleware (request tracking, metrics)
5. Include API router
6. Register non-API routes (healthz, metrics, app shell, root redirect)

**Lifespan handler:**
1. `db.create_all(Base.metadata)` -- create tables
2. `auth_service.ensure_default_api_keys(session, [...])` -- seed 4 keys
3. `governance_service.ensure_default_policies(session, blocked_terms)` -- seed governance
4. `session.commit()`
5. Yield (app running)
6. `hypergraph.close()` -- cleanup

### Worker (`worker.py`)

**`run_worker(*, once=False, max_jobs=None) -> int`**

```
1. app = create_app()            # Full app with all services
2. loop:
   a. session = app.state.db.session()
   b. job_service.complete_stale_leases(session, worker_name)
   c. job_service.process_next(session, worker_name)
   d. session.commit()
   e. on error: session.rollback()
   f. session.close()
   g. if once: break
   h. if max_jobs reached: break
   i. if no work: sleep(poll_seconds)
3. return processed_count
```

**CLI:** `python -m nexus_babel.worker [--once] [--max-jobs N]`

## Research Notes

### Dependencies

- **pydantic-settings**: Used for `Settings` class. Supports `.env` files and env prefix. No version pin in source; relies on pip resolution.
- **SQLAlchemy 2.0**: Uses `mapped_column` style. `future=True` on engine and sessionmaker for 2.0 behavior.
- **Alembic**: Three migrations exist. `alembic.ini` defaults to SQLite. `env.py` can use `NEXUS_DATABASE_URL`.
- **FastAPI**: App factory pattern with lifespan. `TestClient` for testing.

### Complexity Assessment

| Component | Complexity | Risk |
|-----------|-----------|------|
| Auth (as-built) | Low | Well-tested, simple hash-based lookup |
| Job queue (as-built) | Medium | Lease logic has subtle edge cases (stale recovery, concurrent access) |
| Worker (as-built) | Low | Simple poll loop, but no graceful shutdown signal handling |
| Metrics (as-built) | Low | In-memory only, not thread-safe |
| Plugins (as-built) | Low | Two concrete plugins, straightforward chain |
| Config (as-built) | Low | Standard pydantic-settings |
| DB manager (as-built) | Low | Thin wrapper over SQLAlchemy |
| Rate limiting (P3) | Medium | Requires distributed state or middleware library |
| JWT support (P3) | Medium | Token lifecycle, refresh, key management |
| OpenTelemetry (P3) | Medium-High | Instrumentation across all services, export configuration |
| Prometheus export (P3) | Low-Medium | Format conversion from in-memory metrics |
| Worker scaling (P3) | High | Requires SELECT FOR UPDATE SKIP LOCKED, heartbeats, distributed coordination |

### Known Risks

1. **No database-level locking on lease acquisition.** The current `lease_next()` uses `SELECT ... LIMIT 1` without `FOR UPDATE SKIP LOCKED`. Under concurrent workers with PostgreSQL, two workers could lease the same job. SQLite's single-writer lock mitigates this in dev.

2. **In-memory metrics loss.** All counters and timing data are lost on process restart. No persistence or export mechanism.

3. **No graceful worker shutdown.** The worker has no signal handler (SIGTERM/SIGINT). In-flight jobs may be abandoned without proper cleanup. They will eventually be recovered by stale lease detection.

4. **Session management in routes.** Each route creates its own session via `_session(request)`, manually managing commit/rollback/close. This is repetitive and error-prone. A middleware or dependency-injection approach for session lifecycle would reduce bugs.

5. **No connection pool tuning.** SQLAlchemy defaults are used. For production PostgreSQL, explicit pool settings are needed.

6. **User model unused.** The `User` model exists but is not referenced by any auth flow. Authentication is entirely API-key-based. The User model should either be integrated or documented as a future placeholder.

7. **No audit trail for auth events.** Authentication successes, failures, and role violations are not logged to the `AuditLog` table. Only governance decisions are audited.

### Test Coverage Summary

| Area | Test File | Tests | Coverage |
|------|-----------|-------|----------|
| Auth required | `test_mvp.py` | `test_auth_required_on_protected_routes` | 3 routes |
| RBAC + RAW mode | `test_mvp.py` | `test_role_and_raw_mode_enforcement` | viewer/operator/researcher |
| Async job lifecycle | `test_wave2.py` | `test_async_job_lifecycle_and_artifacts` | submit -> process -> verify |
| Job idempotency | `test_wave2.py` | `test_job_idempotency_returns_same_job` | duplicate submission |
| Job cancel | `test_wave2.py` | `test_job_cancel` | queued -> cancelled |
| Healthz | (implicit) | via test client creation | always passes |
| Metrics | (no dedicated test) | -- | GAP |
| Worker CLI | (no dedicated test) | -- | GAP |
| Plugin chain | (no dedicated test) | -- | GAP (exercised indirectly via analysis) |
| Config validation | (no dedicated test) | -- | GAP |
| Stale lease recovery | (no dedicated test) | -- | GAP |
| Shadow execution | (no dedicated test) | -- | GAP |
