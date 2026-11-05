# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**Nexus Babel Alexandria** is the **ARC4N Living Digital Canon** — a breathing organism that atomizes literary works into modular cells for creative recombination, translation, and scholarly exploration. It preserves classic texts at molecular levels and unlocks infinite creative and scholarly recombination through a temporal evolution spiral (expansion → peak → compression → rebirth).

The NLP engine underneath (aka "Theoria Linguae Machina") ingests multimodal documents (text, PDF, image, audio), atomizes them into a 5-level hierarchy (glyph-seed → syllable → word → sentence → paragraph), projects them into a knowledge graph, and provides multi-layer linguistic analysis with dual-mode governance (PUBLIC/RAW).

## ARC4N Concepts

- **5-Level Atomization**: Documents decompose into glyph-seeds (characters with rich metadata: phoneme, historic forms, visual mutations, thematic tags), syllabic clusters, words, sentences, and paragraphs. Each level is independently remixable.
- **Temporal Evolution Spiral**: Language evolves through cyclical phases — expansion (complexity grows), peak (maximum elaboration), compression (glyphs fuse, syllables collapse), rebirth (new sung-language forms emerge). This mirrors both natural linguistic drift and synthetic acceleration.
- **Seed Texts**: Canonical literary works (Homer, Dante, Whitman, Joyce, Shelley) serve as foundational material for the living canon. Each is atomized and available for evolution and remix.
- **Branch Timelines**: Every interaction creates a branch — a deterministic fork of the canon that can drift naturally, mutate synthetically, or remix across documents. Branches are replayable and comparable.
- **Remix/Recombination**: Atoms from different documents can be interleaved, blended by theme, temporally layered, or fused at the glyph level to create new compositions.
- **Natural vs Synthetic Drift**: Natural drift models historic linguistic shifts (Latin→Italian, Old English→Modern). Synthetic drift accelerates evolution beyond historical pace via user intervention or automation.

## Build & Run

Requires Python >=3.11.

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"              # dev includes pytest, httpx, alembic
pip install -e ".[dev,postgres]"     # add PostgreSQL support

# Dev server (defaults to SQLite, binds 0.0.0.0:8000)
make dev                             # uvicorn on :8000 with --reload

# Tests
make test                            # pytest -q (all 3 suites)
pytest tests/test_mvp.py -v          # MVP: ingestion, analysis, evolution, governance
pytest tests/test_wave2.py -v        # Wave-2: async jobs, plugins, metrics
pytest tests/test_arc4n.py -v        # ARC4N: glyph-seeds, remix, seed corpus
pytest tests/test_mvp.py::test_ingestion_completeness -v  # single test

# Database migrations (Alembic, targets SQLite by default via alembic.ini)
make db-upgrade                      # alembic upgrade head

# Background worker (processes async jobs from the jobs table)
make worker                          # python -m nexus_babel.worker
python -m nexus_babel.worker --once  # process one job and exit

# Corpus ingestion script
make ingest                          # python scripts/ingest_corpus.py

# Docker services (Postgres + Neo4j for production-like local dev)
docker compose up -d

# Other scripts
python scripts/load_test.py          # baseline load test
python scripts/repo_certainty_audit.py  # repo certainty audit
```

No linter or type checker is configured in pyproject.toml yet. CI (`ci-minimal.yml`) only validates repo structure (README exists, markdown files present) — it does not run tests or lint.

SDD specifications for all 9 feature domains live in `specs/NN-domain-name/{spec,plan,tasks}.md`. `MANIFEST.yaml` has the full annotated project history (files, threads, relations).

## Environment

Copy `.env.example` to `.env`. All settings use the `NEXUS_` prefix (handled by `pydantic-settings`). Key variables:

- `NEXUS_DATABASE_URL` — SQLite by default (`sqlite:///./nexus_babel.db`), PostgreSQL for docker
- `NEXUS_NEO4J_URI` / `NEXUS_NEO4J_USERNAME` / `NEXUS_NEO4J_PASSWORD` — optional; without Neo4j, the hypergraph uses an in-memory `LocalGraphCache`
- `NEXUS_RAW_MODE_ENABLED` — toggles RAW mode access
- `NEXUS_ASYNC_JOBS_ENABLED` — toggles async job submission
- `NEXUS_BOOTSTRAP_*_KEY` — dev API keys seeded at startup for viewer/operator/researcher/admin roles

## Architecture

### Application Factory

`create_app()` in `main.py` builds the FastAPI app, wires all services onto `app.state`, and seeds default API keys + governance policies in the lifespan handler. A module-level `app = create_app()` is used by uvicorn. Tests use `create_app(settings_override)` with an isolated SQLite + tmp_path.

### Source Layout

```
src/nexus_babel/
  main.py              # FastAPI app factory, middleware, health/metrics endpoints, frontend shell
  config.py            # Settings (pydantic-settings, NEXUS_ prefix, .env file)
  db.py                # DBManager — SQLAlchemy engine + sessionmaker wrapper
  models.py            # All ORM models (SQLAlchemy 2.0 mapped_column style)
  schemas.py           # Pydantic request/response models for the API
  worker.py            # Polling async job worker (CLI entrypoint)
  api/
    routes.py          # All /api/v1/ endpoints (single router)
  services/
    auth.py            # API key auth, role hierarchy (viewer < operator < researcher < admin)
    ingestion.py       # Multi-modal ingestion pipeline (text/PDF/image/audio)
    analysis.py        # 9-layer linguistic analysis (token → semiotic)
    evolution.py       # Branch evolution: natural_drift, synthetic_mutation, phase_shift, glyph_fusion
    governance.py      # Dual-mode content governance (PUBLIC blocks, RAW flags)
    hypergraph.py      # Neo4j graph projection + local cache fallback
    jobs.py            # Async job queue: submit/lease/execute/retry with backoff
    plugins.py         # Plugin registry with deterministic + ML stub providers
    rhetoric.py        # Rhetorical analysis (ethos/pathos/logos scoring, fallacy detection)
    canonicalization.py # Document variant linking (sibling representations, semantic equivalence)
    text_utils.py      # Atomization (5-level: glyph-seed/syllable/word/sentence/paragraph), conflict detection
    glyph_data.py      # Static lookup tables for glyph-seed metadata (phonemes, historic forms, thematic tags)
    seed_corpus.py     # Seed text registry and Project Gutenberg provisioning
    remix.py           # Remix/recombination engine (interleave, thematic_blend, temporal_layer, glyph_collide)
    metrics.py         # In-memory counters + timing histograms
```

### Core Data Flow

1. **Ingest** (`POST /api/v1/ingest/batch`) — files resolved against `corpus_root`, checksummed, parsed by modality, atomized into 5 levels (with rich glyph-seed metadata), projected to hypergraph, canonicalization applied
2. **Analyze** (`POST /api/v1/analyze`) — runs 9 linguistic analysis layers (token, morphology, syntax, semantics, pragmatics, discourse, sociolinguistics, rhetoric, semiotic) against a document or branch, through the plugin chain
3. **Evolve** (`POST /api/v1/evolve/branch`) — creates branching text evolution (natural_drift, synthetic_mutation, phase_shift, glyph_fusion, remix) with deterministic replay via seeded RNG. Natural drift covers ~25 historic linguistic shifts.
4. **Remix** (`POST /api/v1/remix`) — recombines atoms across documents using strategies: interleave, thematic_blend, temporal_layer, glyph_collide
5. **Provision** (`POST /api/v1/corpus/seed`) — provisions canonical seed texts from Project Gutenberg for atomization
6. **Governance** (`POST /api/v1/governance/evaluate`) — evaluates text against mode-specific policies; PUBLIC blocks on first hit, RAW allows with flagging

### Key Design Patterns

- **Dual-mode system**: PUBLIC mode enforces content filtering; RAW mode allows flagged terms for research. Mode access is controlled by both role level and per-key `raw_mode_enabled` flag.
- **Plugin chain**: Analysis layers run through a `PluginRegistry` with fallback chain (`ml_first` → `deterministic`, or `deterministic` only). Each layer produces output + confidence + provider provenance.
- **Hypergraph dual-write**: Document/atom projections write to both a `LocalGraphCache` (always) and Neo4j (when configured). Integrity checks compare both.
- **Async job queue**: Jobs table with lease-based execution, retry with exponential backoff (`[2, 10, 30]s`), idempotency keys, and artifact tracking. Worker polls and processes.
- **Branch evolution determinism**: Event processing uses seeded RNG derived from `sha256(event_type:seed:text_hash)`, ensuring identical inputs produce identical outputs for reproducible replay.

### Auth Model

Four roles in ascending order: `viewer` → `operator` → `researcher` → `admin`. API key auth via `X-Nexus-API-Key` header. Bootstrap keys are seeded at startup from settings.

### Database

SQLAlchemy 2.0 with `mapped_column`. SQLite for dev/test, PostgreSQL for docker. Key models: `Document`, `Atom`, `Branch`, `BranchEvent`, `AnalysisRun`, `LayerOutput`, `Job`, `JobAttempt`, `ModePolicy`, `PolicyDecision`, `AuditLog`, `ProjectionLedger`, `DocumentVariant`.

Alembic migrations in `alembic/versions/`: `20260218_0001_initial` (core tables), `20260218_0002_wave2_alpha` (jobs + checkpoints), `20260223_0003_add_atom_metadata` (glyph-seed metadata column on atoms). The `alembic.ini` defaults to SQLite; for PostgreSQL, set `sqlalchemy.url` or use the `NEXUS_DATABASE_URL` env var in `alembic/env.py`. Migration naming: `YYYYMMDD_NNNN_description.py`.

### Service Dependency Chain

Services are manually wired in `create_app()` onto `app.state` (no DI container). Key dependency flows:

- `ingestion.py` → `text_utils.py` → `glyph_data.py` (atomization chain)
- `ingestion.py` → `canonicalization.py` (variant linking after ingest)
- `ingestion.py` → `hypergraph.py` (graph projection)
- `analysis.py` → `plugins.py` → `rhetoric.py` (plugin fallback chain)
- `remix.py` → `evolution.py` (remix creates branch events)
- `worker.py` → `jobs.py` (polls and executes queued jobs)

### Route Endpoint Pattern

All endpoints in `api/routes.py` follow a consistent pattern: acquire session via `_session(request)` → authenticate via `_require_auth(min_role)` dependency → enforce mode via `_enforce_mode()` → delegate to service → `session.commit()` → return Pydantic response. Errors trigger `session.rollback()`. Sessions are always closed in `finally` blocks. Add new endpoints by following this same pattern.

### Testing Approach

Tests use `FastAPI.TestClient` with an isolated SQLite database per test via `tmp_path`. The `conftest.py` provides `test_settings`, `client`, `auth_headers` (all 4 roles), and `sample_corpus` (text, yaml, conflict yaml, PDF, image, WAV) fixtures. Write new tests by depending on these fixtures — `client` yields a `TestClient` bound to a fresh app with its own DB. Use `auth_headers["operator"]` (or appropriate role) as the `headers` kwarg on requests.

## Routes

Non-API routes (no auth): `GET /healthz` (health check), `GET /metrics` (in-memory counters), `GET /app/{view}` (frontend shell for `corpus`, `hypergraph`, `timeline`, `governance`), `GET /` (redirects to `/app/corpus`).

### API Routes (all under `/api/v1`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/ingest/batch` | operator | Ingest files from corpus |
| GET | `/ingest/jobs/{id}` | viewer | Check ingest job status |
| POST | `/analyze` | operator | Run linguistic analysis |
| GET | `/analysis/runs/{id}` | viewer | Get analysis run detail |
| GET | `/analysis/runs` | viewer | List analysis runs |
| POST | `/evolve/branch` | operator | Create branch evolution |
| GET | `/branches` | viewer | List branches |
| GET | `/branches/{id}/timeline` | viewer | Get branch event timeline |
| POST | `/branches/{id}/replay` | viewer | Replay branch to current state |
| GET | `/branches/{id}/compare/{other}` | viewer | Diff two branches |
| POST | `/governance/evaluate` | operator | Evaluate text against policies |
| POST | `/rhetorical_analysis` | operator | Ethos/pathos/logos analysis |
| POST | `/jobs/submit` | operator | Submit async job |
| GET | `/jobs/{id}` | viewer | Check job status |
| GET | `/jobs` | viewer | List jobs |
| POST | `/jobs/{id}/cancel` | operator | Cancel queued job |
| GET | `/documents` | viewer | List all documents |
| GET | `/documents/{id}` | viewer | Get document detail |
| GET | `/hypergraph/query` | viewer | Query graph nodes/edges |
| GET | `/hypergraph/documents/{id}/integrity` | viewer | Verify graph consistency |
| GET | `/auth/whoami` | viewer | Current auth context |
| GET | `/audit/policy-decisions` | operator | List governance decisions |
| POST | `/corpus/seed` | admin | Provision and ingest a seed text |
| GET | `/corpus/seeds` | viewer | List seed text registry with status |
| POST | `/remix` | operator | Create a remix from two document/branch sources |

<!-- ORGANVM:AUTO:START -->
## System Context (auto-generated — do not edit)

**Organ:** ORGAN-I (Theory) | **Tier:** archive | **Status:** ARCHIVED
**Org:** `organvm-i-theoria` | **Repo:** `nexus--babel-alexandria`

### Edges
- *No inter-repo edges declared in seed.yaml*

### Siblings in Theory
`recursive-engine--generative-entity`, `organon-noumenon--ontogenetic-morphe`, `auto-revision-epistemic-engine`, `narratological-algorithmic-lenses`, `call-function--ontological`, `sema-metra--alchemica-mundi`, `cognitive-archaelogy-tribunal`, `a-recursive-root`, `radix-recursiva-solve-coagula-redi`, `.github`, `4-ivi374-F0Rivi4`, `cog-init-1-0-`, `linguistic-atomization-framework`, `my-knowledge-base`, `scalable-lore-expert` ... and 10 more

### Governance
- Foundational theory layer. No upstream dependencies.

*Last synced: 2026-04-14T21:31:46Z*

## Active Handoff Protocol

If `.conductor/active-handoff.md` exists, **READ IT FIRST** before doing any work.
It contains constraints, locked files, conventions, and completed work from the
originating agent. You MUST honor all constraints listed there.

If the handoff says "CROSS-VERIFICATION REQUIRED", your self-assessment will
NOT be trusted. A different agent will verify your output against these constraints.

## Session Review Protocol

At the end of each session that produces or modifies files:
1. Run `organvm session review --latest` to get a session summary
2. Check for unimplemented plans: `organvm session plans --project .`
3. Export significant sessions: `organvm session export <id> --slug <slug>`
4. Run `organvm prompts distill --dry-run` to detect uncovered operational patterns

Transcripts are on-demand (never committed):
- `organvm session transcript <id>` — conversation summary
- `organvm session transcript <id> --unabridged` — full audit trail
- `organvm session prompts <id>` — human prompts only


## System Library

Plans: 269 indexed | Chains: 5 available | SOPs: 121 active
Discover: `organvm plans search <query>` | `organvm chains list` | `organvm sop lifecycle`
Library: `meta-organvm/praxis-perpetua/library/`


## Active Directives

| Scope | Phase | Name | Description |
|-------|-------|------|-------------|
| system | any | atomic-clock | The Atomic Clock |
| system | any | execution-sequence | Execution Sequence |
| system | any | multi-agent-dispatch | Multi-Agent Dispatch |
| system | any | session-handoff-avalanche | Session Handoff Avalanche |
| system | any | system-loops | System Loops |
| system | any | prompting-standards | Prompting Standards |
| system | any | research-standards-bibliography | APPENDIX: Research Standards Bibliography |
| system | any | phase-closing-and-forward-plan | METADOC: Phase-Closing Commemoration & Forward Attack Plan |
| system | any | research-standards | METADOC: Architectural Typology & Research Standards |
| system | any | sop-ecosystem | METADOC: SOP Ecosystem — Taxonomy, Inventory & Coverage |
| system | any | autonomous-content-syndication | SOP: Autonomous Content Syndication (The Broadcast Protocol) |
| system | any | autopoietic-systems-diagnostics | SOP: Autopoietic Systems Diagnostics (The Mirror of Eternity) |
| system | any | background-task-resilience | background-task-resilience |
| system | any | cicd-resilience-and-recovery | SOP: CI/CD Pipeline Resilience & Recovery |
| system | any | community-event-facilitation | SOP: Community Event Facilitation (The Dialectic Crucible) |
| system | any | context-window-conservation | context-window-conservation |
| system | any | conversation-to-content-pipeline | SOP — Conversation-to-Content Pipeline |
| system | any | cross-agent-handoff | SOP: Cross-Agent Session Handoff |
| system | any | cross-channel-publishing-metrics | SOP: Cross-Channel Publishing Metrics (The Echo Protocol) |
| system | any | data-migration-and-backup | SOP: Data Migration and Backup Protocol (The Memory Vault) |
| system | any | document-audit-feature-extraction | SOP: Document Audit & Feature Extraction |
| system | any | dynamic-lens-assembly | SOP: Dynamic Lens Assembly |
| system | any | essay-publishing-and-distribution | SOP: Essay Publishing & Distribution |
| system | any | formal-methods-applied-protocols | SOP: Formal Methods Applied Protocols |
| system | any | formal-methods-master-taxonomy | SOP: Formal Methods Master Taxonomy (The Blueprint of Proof) |
| system | any | formal-methods-tla-pluscal | SOP: Formal Methods — TLA+ and PlusCal Verification (The Blueprint Verifier) |
| system | any | generative-art-deployment | SOP: Generative Art Deployment (The Gallery Protocol) |
| system | any | market-gap-analysis | SOP: Full-Breath Market-Gap Analysis & Defensive Parrying |
| system | any | mcp-server-fleet-management | SOP: MCP Server Fleet Management (The Server Protocol) |
| system | any | multi-agent-swarm-orchestration | SOP: Multi-Agent Swarm Orchestration (The Polymorphic Swarm) |
| system | any | network-testament-protocol | SOP: Network Testament Protocol (The Mirror Protocol) |
| system | any | open-source-licensing-and-ip | SOP: Open Source Licensing and IP (The Commons Protocol) |
| system | any | performance-interface-design | SOP: Performance Interface Design (The Stage Protocol) |
| system | any | pitch-deck-rollout | SOP: Pitch Deck Generation & Rollout |
| system | any | polymorphic-agent-testing | SOP: Polymorphic Agent Testing (The Adversarial Protocol) |
| system | any | promotion-and-state-transitions | SOP: Promotion & State Transitions |
| system | any | recursive-study-feedback | SOP: Recursive Study & Feedback Loop (The Ouroboros) |
| system | any | repo-onboarding-and-habitat-creation | SOP: Repo Onboarding & Habitat Creation |
| system | any | research-to-implementation-pipeline | SOP: Research-to-Implementation Pipeline (The Gold Path) |
| system | any | security-and-accessibility-audit | SOP: Security & Accessibility Audit |
| system | any | session-self-critique | session-self-critique |
| system | any | smart-contract-audit-and-legal-wrap | SOP: Smart Contract Audit and Legal Wrap (The Ledger Protocol) |
| system | any | source-evaluation-and-bibliography | SOP: Source Evaluation & Annotated Bibliography (The Refinery) |
| system | any | stranger-test-protocol | SOP: Stranger Test Protocol |
| system | any | strategic-foresight-and-futures | SOP: Strategic Foresight & Futures (The Telescope) |
| system | any | styx-pipeline-traversal | SOP: Styx Pipeline Traversal (The 7-Organ Transmutation) |
| system | any | system-dashboard-telemetry | SOP: System Dashboard Telemetry (The Panopticon Protocol) |
| system | any | the-descent-protocol | the-descent-protocol |
| system | any | the-membrane-protocol | the-membrane-protocol |
| system | any | theoretical-concept-versioning | SOP: Theoretical Concept Versioning (The Epistemic Protocol) |
| system | any | theory-to-concrete-gate | theory-to-concrete-gate |
| system | any | typological-hermeneutic-analysis | SOP: Typological & Hermeneutic Analysis (The Archaeology) |
| unknown | any | gpt-to-os | SOP_GPT_TO_OS.md |
| unknown | any | index | SOP_INDEX.md |
| unknown | any | obsidian-sync | SOP_OBSIDIAN_SYNC.md |

Linked skills: cicd-resilience-and-recovery, continuous-learning-agent, evaluation-to-growth, genesis-dna, multi-agent-workforce-planner, promotion-and-state-transitions, quality-gate-baseline-calibration, repo-onboarding-and-habitat-creation, structural-integrity-audit


**Prompting (Anthropic)**: context 200K tokens, format: XML tags, thinking: extended thinking (budget_tokens)


## Ecosystem Status

- **delivery**: 0/1 live, 0 planned
- **content**: 0/1 live, 0 planned

Run: `organvm ecosystem show nexus--babel-alexandria` | `organvm ecosystem validate --organ I`


## External Mirrors (Network Testament)

- **technical** (10): tiangolo/fastapi, encode/uvicorn, sqlalchemy/sqlalchemy, pydantic/pydantic, yaml/pyyaml +5 more

Convergences: 20 | Run: `organvm network map --repo nexus--babel-alexandria` | `organvm network suggest`


## Task Queue (from pipeline)

**36** pending tasks | Last pipeline: unknown

- `908516b81d88` orchestration-start-here — submodule [mcp]
- `8115789b2e28` petasum-super-petasum — submodule [mcp]
- `c1cacf4bae40` universal-node-network — submodule [mcp]
- `ab3f8e21b60f` org-dotgithub (.github) — submodule [mcp]
- `701ba201e6b3` agentic-titan — submodule [mcp]
- `0139c27499ce` agent--claude-smith — submodule [mcp]
- `76ece8ea967d` a-i--skills — submodule [mcp]
- `24600e4b2fa3` tool-interaction-design — git repo (170MB, organvm-iv-taxis org) [mcp]
- ... and 28 more

Cross-organ links: 66 | Top tags: `python`, `bash`, `mcp`, `pytest`, `express`

Run: `organvm atoms pipeline --write && organvm atoms fanout --write`


## Entity Identity (Ontologia)

**UID:** `ent_repo_01KKKX3RVHWCRH5V56E0YRJ8CH` | **Matched by:** primary_name

Resolve: `organvm ontologia resolve nexus--babel-alexandria` | History: `organvm ontologia history ent_repo_01KKKX3RVHWCRH5V56E0YRJ8CH`


## Live System Variables (Ontologia)

| Variable | Value | Scope | Updated |
|----------|-------|-------|---------|
| `active_repos` | 89 | global | 2026-04-14 |
| `archived_repos` | 54 | global | 2026-04-14 |
| `ci_workflows` | 107 | global | 2026-04-14 |
| `code_files` | 0 | global | 2026-04-14 |
| `dependency_edges` | 60 | global | 2026-04-14 |
| `operational_organs` | 10 | global | 2026-04-14 |
| `published_essays` | 29 | global | 2026-04-14 |
| `repos_with_tests` | 0 | global | 2026-04-14 |
| `sprints_completed` | 33 | global | 2026-04-14 |
| `test_files` | 0 | global | 2026-04-14 |
| `total_organs` | 10 | global | 2026-04-14 |
| `total_repos` | 145 | global | 2026-04-14 |
| `total_words_formatted` | 0 | global | 2026-04-14 |
| `total_words_numeric` | 0 | global | 2026-04-14 |
| `total_words_short` | 0K+ | global | 2026-04-14 |

Metrics: 9 registered | Observations: 32128 recorded
Resolve: `organvm ontologia status` | Refresh: `organvm refresh`


## System Density (auto-generated)

AMMOI: 58% | Edges: 42 | Tensions: 33 | Clusters: 5 | Adv: 23 | Events(24h): 32336
Structure: 8 organs / 145 repos / 1654 components (depth 17) | Inference: 98% | Organs: META-ORGANVM:65%, ORGAN-I:53%, ORGAN-II:48%, ORGAN-III:54% +5 more
Last pulse: 2026-04-14T21:31:36 | Δ24h: -1.0% | Δ7d: n/a


## Dialect Identity (Trivium)

**Dialect:** FORMAL_LOGIC | **Classical Parallel:** Logic | **Translation Role:** The Grammar — defines well-formedness in any dialect

Strongest translations: III (formal), IV (formal), META (formal)

Scan: `organvm trivium scan I <OTHER>` | Matrix: `organvm trivium matrix` | Synthesize: `organvm trivium synthesize`


## Logos Documentation Layer

**Status:** MISSING | **Symmetry:** 0.5 (GHOST)

Nature demands a documentation counterpart. This formation maintains its narrative record in `docs/logos/`.

### The Tetradic Counterpart
- **[Telos (Idealized Form)](../docs/logos/telos.md)** — The dream and theoretical grounding.
- **[Pragma (Concrete State)](../docs/logos/pragma.md)** — The honest account of what exists.
- **[Praxis (Remediation Plan)](../docs/logos/praxis.md)** — The attack vectors for evolution.
- **[Receptio (Reception)](../docs/logos/receptio.md)** — The account of the constructed polis.

### Alchemical I/O
- **[Source & Transmutation](../docs/logos/alchemical-io.md)** — Narrative of inputs, process, and returns.



*Compliance: Implementation exists without record.*

<!-- ORGANVM:AUTO:END -->











## ⚡ Conductor OS Integration
This repository is a managed component of the ORGANVM meta-workspace.
- **Orchestration:** Use `conductor patch` for system status and work queue.
- **Lifecycle:** Follow the `FRAME -> SHAPE -> BUILD -> PROVE` workflow.
- **Governance:** Promotions are managed via `conductor wip promote`.
- **Intelligence:** Conductor MCP tools are available for routing and mission synthesis.