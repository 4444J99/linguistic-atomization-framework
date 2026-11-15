# Nexus Babel-Alexandria MVP Operator Runbook

## 1. Environment

- Python 3.11+
- Optional services (recommended):
  - Postgres 16
  - Neo4j 5.x

Start infra:

```bash
docker compose up -d
```

Install app:

```bash
python3 -m pip install -e .[dev,postgres]
make db-upgrade
```

If `make` is unavailable:

```bash
alembic upgrade head
```

## 2. Configuration

Copy and edit:

```bash
cp .env.example .env
```

Important variables:

- `NEXUS_DATABASE_URL`
- `NEXUS_SCHEMA_MANAGEMENT_MODE` (`auto_create`, `migrate_only`, `off`)
- `NEXUS_NEO4J_URI`
- `NEXUS_NEO4J_USERNAME`
- `NEXUS_NEO4J_PASSWORD`
- `NEXUS_CORPUS_ROOT`
- `NEXUS_OBJECT_STORAGE_ROOT`
- `NEXUS_RAW_MODE_ENABLED`
- `NEXUS_BOOTSTRAP_KEYS_ENABLED`
- `NEXUS_BOOTSTRAP_VIEWER_KEY`
- `NEXUS_BOOTSTRAP_OPERATOR_KEY`
- `NEXUS_BOOTSTRAP_RESEARCHER_KEY`
- `NEXUS_BOOTSTRAP_ADMIN_KEY`

> [!WARNING]
> `.env.example` and `docker-compose.yml` use local-only placeholder credentials. Do not reuse them outside local development.
>
> For production-like environments, set `NEXUS_SCHEMA_MANAGEMENT_MODE=migrate_only` and `NEXUS_BOOTSTRAP_KEYS_ENABLED=false`.

## 3. Start Service

```bash
uvicorn nexus_babel.main:app --host 0.0.0.0 --port 8000 --reload
python -m nexus_babel.worker
```

Equivalent `make` targets:

```bash
make run-api
make run-worker
```

Health check:

```bash
curl http://localhost:8000/healthz
```

Who am I:

```bash
curl -H 'X-Nexus-API-Key: nexus-dev-viewer-key' http://localhost:8000/api/v1/auth/whoami # allow-secret
```

## 4. Ingest Corpus

```bash
python scripts/ingest_corpus.py
```

Or direct API call:

```bash
api_key='nexus-dev-operator-key' # allow-secret
curl -X POST http://localhost:8000/api/v1/ingest/batch \
  -H "X-Nexus-API-Key: ${api_key}" \
  -H 'Content-Type: application/json' \
  -d '{"source_paths":[],"modalities":[],"parse_options":{"atomize":true}}'
```

## 5. Verify System

- `GET /api/v1/documents`
- `GET /api/v1/ingest/jobs/{job_id}`
- `GET /app/corpus`
- `GET /api/v1/hypergraph/documents/{document_id}/integrity`
- `POST /api/v1/jobs/submit`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/analysis/runs/{run_id}`
- `GET /api/v1/audit/policy-decisions`

## 6. Governance Modes

- `PUBLIC`: hard blocks on blocked terms
- `RAW`: researcher/admin only; allows output but logs policy hits

Evaluate sample:

```bash
api_key='nexus-dev-operator-key' # allow-secret
curl -X POST http://localhost:8000/api/v1/governance/evaluate \
  -H "X-Nexus-API-Key: ${api_key}" \
  -H 'Content-Type: application/json' \
  -d '{"candidate_output":"example text","mode":"PUBLIC"}'
```

RAW sample:

```bash
api_key='nexus-dev-researcher-key' # allow-secret
curl -X POST http://localhost:8000/api/v1/governance/evaluate \
  -H "X-Nexus-API-Key: ${api_key}" \
  -H 'Content-Type: application/json' \
  -d '{"candidate_output":"example text","mode":"RAW"}'
```

## 7. Testing

```bash
pytest -q
python scripts/load_test.py
```

Also available:

```bash
make test
make lint
make openapi-snapshot
make certainty
make certainty-check
make evolution-contract-test
make verify
```

Use `make openapi-snapshot` after intentional `/api/v1` contract changes to regenerate the normalized OpenAPI snapshot used by the test suite.
If you are not running inside the project environment, use `.venv/bin/python scripts/generate_openapi_contract_snapshot.py`.
Use `make certainty` after changes that affect repository structure, route inventory, documented endpoints, or roadmap references, and `make certainty-check` to confirm the committed `docs/certainty/*` artifacts are current.
Use `make evolution-contract-test` for a fast branch/replay/merge/visualization API regression loop while refactoring `EvolutionService`.
Use `make verify` for a local pre-PR bundle (`lint` + `certainty-check` + `test`).

## 8. Known Constraints

- RLOS analysis layers are heuristic MVP implementations, not full ML models yet.
- Image OCR and advanced audio analysis are represented via metadata paths in this slice.
- Files containing Git conflict markers are intentionally flagged as non-ingestable until resolved.
- API keys are static bootstrap secrets in MVP mode; rotate in real environments.
- In non-dev environments, set explicit corpus/object storage paths to avoid cwd-dependent defaults at startup.

## 9. Durability and Recovery

- Canonicalization is rebuilt deterministically from current ingested documents after each ingest job.
- Hypergraph integrity uses durable SQL counters and optional Neo4j verification.
- If Neo4j is unavailable, ingestion completes with warning status and sets `graph_projection_status=failed`.
- Re-run ingestion after graph recovery to reproject counters and graph nodes.
