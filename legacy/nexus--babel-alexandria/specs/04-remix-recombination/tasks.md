# Remix & Recombination -- Task List

## Phase 1: Setup

### T-SETUP-001: Create domain test file [P]

Create `tests/test_remix_recombination.py` with domain-specific fixtures and imports. Reuse `conftest.py` fixtures (`client`, `auth_headers`, `sample_corpus`). Add helper fixture `two_ingested_documents` that ingests `sample_corpus["text"]` and `sample_corpus["clean_yaml"]` and returns their document IDs for use across remix tests.

**Files**: `tests/test_remix_recombination.py`, `tests/conftest.py`
**Acceptance**: File exists, `pytest tests/test_remix_recombination.py -v` passes with 0 tests collected (skeleton).

### T-SETUP-002: Verify existing remix test coverage baseline [P]

Run `pytest tests/test_arc4n.py -v -k remix` and document which remix tests pass. Identify any regressions. This establishes the baseline for all subsequent work.

**Files**: `tests/test_arc4n.py`
**Acceptance**: All 8 existing remix tests pass (`TestRemixEvolutionEvents::test_remix_event_validated`, `test_remix_event_applied`, `TestRemixStrategies::test_interleave`, `test_thematic_blend_deterministic`, `test_glyph_collide_produces_output`, `test_temporal_layer`, `TestRemixAPI::test_remix_requires_auth`, `test_remix_with_two_documents`).

### T-SETUP-003: Add ruff/mypy configuration for remix files [P]

No linter or type checker is configured in `pyproject.toml` yet. Add/extend `[tool.ruff]` and `[tool.mypy]` sections targeting `src/nexus_babel/services/remix.py`.

**Files**: `pyproject.toml`
**Acceptance**: `ruff check src/nexus_babel/services/remix.py` passes. `mypy src/nexus_babel/services/remix.py` type-checks with 0 errors.

---

## Phase 2: Foundational -- Schema & Migration Prerequisites

### T-FOUND-001: Define RemixArtifact and RemixSourceLink models [Story: US-009]

Add `RemixArtifact` and `RemixSourceLink` ORM models to `models.py`:

```python
class RemixArtifact(Base):
    __tablename__ = "remix_artifacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    strategy: Mapped[str] = mapped_column(String(64), index=True)
    seed: Mapped[int] = mapped_column(Integer)
    remixed_text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(128), index=True)
    rng_seed_hex: Mapped[str] = mapped_column(String(128))
    mode: Mapped[str] = mapped_column(String(16), default="PUBLIC")
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    branch_event_id: Mapped[str | None] = mapped_column(ForeignKey("branch_events.id", ondelete="SET NULL"), nullable=True)
    governance_decision_id: Mapped[str | None] = mapped_column(ForeignKey("policy_decisions.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class RemixSourceLink(Base):
    __tablename__ = "remix_source_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    remix_artifact_id: Mapped[str] = mapped_column(ForeignKey("remix_artifacts.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # 'source' or 'target'
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id", ondelete="SET NULL"), nullable=True)
    resolved_text_hash: Mapped[str] = mapped_column(String(128))
    resolved_text_len: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("remix_artifact_id", "role", name="uq_remix_source_role"),)
```

**Files**: `src/nexus_babel/models.py`
**Acceptance**: Models defined. `from nexus_babel.models import RemixArtifact, RemixSourceLink` imports without error.

### T-FOUND-002: Create Alembic migration for remix tables [Story: US-009]

Generate Alembic migration `20260223_0003_remix_artifacts` adding `remix_artifacts` and `remix_source_links` tables. Verify upgrade and downgrade both work on SQLite and PostgreSQL.

**Files**: `alembic/versions/20260223_0003_remix_artifacts.py`
**Acceptance**: `make db-upgrade` applies cleanly. `alembic downgrade -1` removes both tables.

### T-FOUND-003: Add Pydantic schemas for remix persistence [Story: US-009, US-010]

Add new Pydantic models to `schemas.py`:

- `RemixArtifactResponse`: full artifact detail with source links
- `RemixArtifactListItem`: summary for listing endpoint
- `RemixArtifactListResponse`: wrapper with `remixes` list
- `RemixSourceLinkView`: source link detail

Extend `RemixRequest` with optional `create_branch: bool = True` and `persist_artifact: bool = True`.
Extend `RemixResponse` with optional `remix_artifact_id: str | None = None`, `text_hash: str | None = None`, `governance_decision_id: str | None = None`.

**Files**: `src/nexus_babel/schemas.py`
**Acceptance**: All new schemas importable. Existing `RemixRequest` backward compatible (new fields have defaults).

---

## Phase 3: User Stories -- P1 Verification & Hardening

### T-P1-001: Add explicit interleave strategy unit tests [Story: US-001] [P]

Test `RemixService._interleave()` directly:
- Equal-length word lists: output alternates correctly
- Source longer than target: remaining source words appended
- Target longer than source: remaining target words appended
- Single-word inputs: output is "source target"
- Empty source: output is target words joined by space
- Empty target: output is source words joined by space
- Both empty: output is empty string

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=7 tests, all pass.

### T-P1-002: Add explicit thematic_blend strategy unit tests [Story: US-002] [P]

Test `RemixService._thematic_blend()` directly:
- Determinism: same seed produces same output
- Different seeds produce different output
- Sentence count: output has `max(src_sentences, tgt_sentences)` sentences
- Input with no sentence-ending punctuation: treated as 1 sentence
- Input with only `!` endings: split correctly
- Input with only `?` endings: split correctly
- Mixed punctuation: split correctly

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=7 tests, all pass.

### T-P1-003: Add explicit temporal_layer strategy unit tests [Story: US-003] [P]

Test `RemixService._temporal_layer()` directly:
- Source paragraphs always present in output
- Target paragraphs prefixed with `"[temporal overlay] "` when included
- ~70% target inclusion rate over many iterations (statistical, seed=42 gives deterministic check)
- Single-paragraph inputs: output includes source + optionally target
- Many paragraphs: verify interleaving order (source first, then target)
- Output joined by `"\n\n"`

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=6 tests, all pass.

### T-P1-004: Add explicit glyph_collide strategy unit tests [Story: US-004] [P]

Test `RemixService._glyph_collide()` directly:
- Identical texts: output equals input (no collisions)
- Disjoint texts: output has characters from both
- Output length = min(max(src_glyphs, tgt_glyphs), 2000)
- 2000-char cap enforced: two 5000-char inputs produce 2000-char output
- Output contains no whitespace
- Short vs long text: shorter text's positions filled, longer text's remainder used

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=6 tests, all pass.

### T-P1-005: Add source resolution tests [Story: US-005] [P]

Test `RemixService._resolve_text()` directly (requires session with seeded data):
- Document with extracted text: resolves correctly
- Branch with state_snapshot.current_text: resolves correctly
- Both document and branch provided: branch takes priority
- Nonexistent document ID: returns empty string
- Nonexistent branch ID: returns empty string
- Document with no extracted_text in provenance: returns empty string

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=6 tests, all pass.

### T-P1-006: Add RNG determinism tests [Story: US-006] [P]

Test seeded RNG behavior:
- Same inputs + same seed: two calls produce identical output for each strategy
- Same inputs + different seed: produce different output for stochastic strategies (thematic_blend, temporal_layer, glyph_collide)
- Different inputs + same seed: produce different output
- Seed derivation formula: verify `sha256("remix:{strategy}:{seed}:{source_hash}:{target_hash}")` matches expected

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=4 tests, all pass.

### T-P1-007: Add branch event integration tests [Story: US-007] [P]

Test remix -> branch -> event chain via API:
- Remix with two documents: branch created with `name="branch-remix"`
- Branch event has `event_type="remix"` and `event_payload` with all fields
- Timeline endpoint shows the remix event
- Replay endpoint returns text matching the remix output hash
- Event hash is deterministic (same remix twice with same inputs produces same event_hash)

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-008: Add mode enforcement tests [Story: US-008] [P]

Test mode access control on remix endpoint:
- PUBLIC mode with operator key: succeeds
- RAW mode with operator key (no raw_mode_enabled): returns 403
- RAW mode with researcher key (raw_mode_enabled=True): succeeds (if system raw_mode_enabled)
- No API key: returns 401
- Viewer API key: returns 403

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-009: Add error case tests [P]

Test error conditions:
- Both source and target resolve to empty text: 400 with clear message
- Unknown strategy value (bypass schema validation by calling service directly): ValueError
- Nonexistent source_document_id + no branch: 400
- Nonexistent target_document_id + no branch: 400
- Source side only (no target provided): 400

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-010: Add branch-to-branch remix test [Story: US-005]

Test remix where both source and target are branches (not documents):
1. Ingest a document
2. Evolve it to create branch A
3. Evolve it to create branch B (different evolution)
4. Remix branch A + branch B
5. Verify new branch is created with correct parent

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: 1 integration test, passes.

### T-P1-011: Add cross-source remix test (document-to-branch) [Story: US-005]

Test remix where source is a document and target is a branch:
1. Ingest two documents
2. Evolve document A to create a branch
3. Remix document B (source) + branch (target)
4. Verify root_document_id points to document B

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: 1 integration test, passes.

### T-P1-012: Add self-remix edge case test [P]

Test remixing a document against itself:
- interleave: produces each word doubled ("word word word word ...")
- glyph_collide: produces original text (all collisions are identical)

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: 2 tests, all pass.

---

## Phase 4: User Stories -- P2 Completion

### T-P2-001: Implement RemixService artifact persistence [Story: US-009]

Extend `RemixService.remix()` to create a `RemixArtifact` row and two `RemixSourceLink` rows (source + target) in addition to the existing branch/event creation. Include `text_hash` (SHA256 of remixed text) and `rng_seed_hex` (the full derived seed hex string).

Steps:
1. After strategy application, compute `text_hash`
2. Create `RemixArtifact` with all fields
3. Create `RemixSourceLink` for source side with resolved text hash
4. Create `RemixSourceLink` for target side with resolved text hash
5. After branch creation (if applicable), update artifact with `branch_id` and `branch_event_id`
6. Return extended result

**Files**: `src/nexus_babel/services/remix.py`, `src/nexus_babel/models.py`
**Acceptance**: After remix, `RemixArtifact` and 2 `RemixSourceLink` rows exist. Text hash matches SHA256 of remixed text.

### T-P2-002: Add remix persistence tests [Story: US-009] [P]

Test:
- Remix creates artifact with correct strategy, seed, text_hash, mode
- Two source links created (one source, one target) with correct roles
- Source link resolved_text_hash matches SHA256 of source text
- Artifact branch_id matches the created branch
- Artifact branch_event_id matches the created event

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=5 tests, all pass.

### T-P2-003: Implement GET /api/v1/remix/{id} endpoint [Story: US-010]

Add retrieval endpoint:
1. Query `RemixArtifact` by ID
2. Eager-load `RemixSourceLink` rows
3. Return `RemixArtifactResponse` with text preview (first 500 chars), source links, and all metadata
4. Return 404 if not found

**Files**: `src/nexus_babel/api/routes.py`, `src/nexus_babel/schemas.py`
**Acceptance**: GET returns full artifact detail. 404 for nonexistent ID.

### T-P2-004: Implement GET /api/v1/remix listing endpoint [Story: US-010]

Add listing endpoint:
1. Query `RemixArtifact` ordered by `created_at` descending
2. Support `limit` (default 100, max 1000), `strategy` filter, `mode` filter
3. Return `RemixArtifactListResponse` with summary items

**Files**: `src/nexus_babel/api/routes.py`, `src/nexus_babel/schemas.py`
**Acceptance**: GET returns list. Filters work. Default limit applies.

### T-P2-005: Add retrieval endpoint tests [Story: US-010] [P]

Test:
- GET /remix/{id} returns correct artifact after creation
- GET /remix/{id} returns 404 for nonexistent ID
- GET /remix returns list containing the created remix
- GET /remix with strategy filter returns only matching remixes
- GET /remix with mode filter works
- GET /remix respects limit parameter
- Auth required (viewer minimum for GET)

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=7 tests, all pass.

### T-P2-006: Implement governance evaluation on remix output [Story: US-011]

Add governance trace to remix flow:
1. After strategy application, call `GovernanceService.evaluate(session, remixed_text, mode)`
2. In PUBLIC mode, if governance blocks (policy hits >= threshold), reject the remix with HTTP 422
3. In RAW mode, governance flags but allows
4. Store `governance_decision_id` on the `RemixArtifact`
5. Store `PolicyDecision.id` reference in artifact

**Files**: `src/nexus_babel/services/remix.py`, `src/nexus_babel/api/routes.py`
**Acceptance**: Remix with blocked terms in PUBLIC mode is rejected. RAW mode allows with flag. Governance decision ID is stored on artifact.

### T-P2-007: Add governance trace tests [Story: US-011] [P]

Test:
- Remix producing text with blocked term in PUBLIC mode: rejected (HTTP 422)
- Remix producing text with blocked term in RAW mode: allowed, governance_decision_id set
- Remix producing clean text: no policy hits, governance_decision_id still set
- Governance decision viewable via `GET /audit/policy-decisions`

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=4 tests, all pass.

### T-P2-008: Implement create_branch option [Story: US-013]

Add `create_branch` boolean to `RemixRequest` (default `True`):
1. When `True`: current behavior (create branch + event + artifact)
2. When `False`: create artifact only, skip branch/event creation
3. Artifact `branch_id` and `branch_event_id` are `None` when no branch created
4. When `True` and artifact exists: include `remix_artifact_id` in `BranchEvent.event_payload`

**Files**: `src/nexus_babel/services/remix.py`, `src/nexus_babel/schemas.py`
**Acceptance**: `create_branch=false` creates no branch. `create_branch=true` creates branch with artifact link.

### T-P2-009: Add break-off timeline tests [Story: US-013] [P]

Test:
- `create_branch=false`: no branch created, artifact exists with branch_id=None
- `create_branch=true` (default): branch created, artifact has branch_id set
- `create_branch=true`: branch event payload includes `remix_artifact_id`
- Timeline replay of branch with remix_artifact_id still works

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: >=4 tests, all pass.

---

## Phase 5: User Stories -- P3 Vision

### T-P3-001: Design atom-level remix interface [Story: US-012]

Design the `_resolve_atoms()` method and atom-pool remix interface:
1. New method `_resolve_atoms(session, document_id, branch_id, atom_levels)` queries `Atom` rows
2. Strategy methods accept `list[Atom]` instead of `str` when atom_levels specified
3. `interleave` at word level: alternates `Atom` objects by ordinal
4. `thematic_blend` at sentence level: shuffles sentence Atoms using thematic_tags from glyph-seed metadata

Write design doc in `specs/04-remix-recombination/atom-level-remix-design.md`.

**Files**: `specs/04-remix-recombination/atom-level-remix-design.md`
**Acceptance**: Design doc with interface signatures, data flow diagram, and migration plan.

### T-P3-002: Implement atom-level resolve method [Story: US-012]

Add `_resolve_atoms(session, document_id, branch_id, atom_levels) -> list[Atom]` to `RemixService`:
1. Query `Atom` rows filtered by `document_id` and `atom_level in atom_levels`
2. Order by `ordinal`
3. Return list of `Atom` objects with content and metadata

**Files**: `src/nexus_babel/services/remix.py`
**Acceptance**: Method returns correct atoms for a given document and level. Empty list for nonexistent document.

### T-P3-003: Add atom_levels field to RemixRequest [Story: US-012]

Add optional `atom_levels: list[str] | None = None` to `RemixRequest`. When provided:
1. Validate levels are in `["glyph-seed", "syllable", "word", "sentence", "paragraph"]`
2. Pass to `_resolve_atoms()` instead of `_resolve_text()`
3. Concatenate atom contents as input text for strategies

**Files**: `src/nexus_babel/schemas.py`, `src/nexus_babel/services/remix.py`
**Acceptance**: API accepts atom_levels. Remix uses atom content. Response includes source atom references.

### T-P3-004: Add source_atom_refs to RemixResponse [Story: US-012]

When atom-level remix is used, include `source_atom_refs` in the response: a list of `{atom_id, atom_level, ordinal, role}` entries identifying which atoms contributed to the remix.

**Files**: `src/nexus_babel/schemas.py`, `src/nexus_babel/services/remix.py`
**Acceptance**: Response includes atom references when atom_levels is specified.

### T-P3-005: Integrate remix with async job system [Story: US-015]

Add `execution_mode` to `RemixRequest` (`"sync"` default, `"async"` optional):
1. When `"async"`, submit a `remix` job to the `Job` queue via `JobService`
2. Worker calls `RemixService.remix()` and updates the job
3. Response includes `job_id` for polling

**Files**: `src/nexus_babel/services/remix.py`, `src/nexus_babel/api/routes.py`, `src/nexus_babel/schemas.py`, `src/nexus_babel/worker.py`
**Acceptance**: Async remix submits job. Worker processes it. Final result available via job endpoint.

### T-P3-006: Add remix lineage graph projection [Story: US-014]

Project remix artifacts as nodes in the hypergraph:
1. Create `remix:{id}` node for each `RemixArtifact`
2. Create `REMIXED_FROM` edges to source document/branch nodes
3. Create `PRODUCED` edge from remix node to output branch node (when create_branch=true)
4. Update `LocalGraphCache` and Neo4j (when configured)

**Files**: `src/nexus_babel/services/hypergraph.py`, `src/nexus_babel/services/remix.py`
**Acceptance**: Remix nodes visible in hypergraph query. Edges correctly link sources and output.

### T-P3-007: Explore N-way remix design [Story: US-016]

Research and design N-way remix support:
1. Generalize `RemixRequest` to accept `sources: list[{document_id, branch_id}]` instead of single source/target
2. Generalize strategies for N inputs (interleave round-robin, thematic_blend merge all, etc.)
3. Update `RemixSourceLink` to support N links per artifact (remove unique constraint on role)

Write design doc. No implementation in this task.

**Files**: `specs/04-remix-recombination/n-way-remix-design.md`
**Acceptance**: Design doc with trade-offs, backward compatibility plan, and schema migration.

---

## Phase 6: Cross-Cutting

### T-CROSS-001: Wire remix domain tests into CI [P]

Update `.github/workflows/ci-minimal.yml` to run `pytest tests/test_remix_recombination.py tests/test_arc4n.py -v -k remix` as part of the pipeline.

**Files**: `.github/workflows/ci-minimal.yml`
**Acceptance**: CI runs remix tests and fails on regression.

### T-CROSS-002: Add remix performance benchmark

Create `scripts/benchmark_remix.py` that:
1. Ingests two seed texts (e.g., The Odyssey + Leaves of Grass)
2. Runs all 4 strategies with seed=0
3. Records wall time, input sizes, output sizes
4. Prints summary table: `strategy | source_chars | target_chars | output_chars | duration_ms`
5. Asserts all strategies complete in <5s for typical seed text pairs

**Files**: `scripts/benchmark_remix.py`
**Acceptance**: Script runs end-to-end. Baseline captured.

### T-CROSS-003: Add concurrent remix safety test

Test that two simultaneous remix calls using the same source documents do not produce data corruption:
1. Submit two remix calls concurrently (different strategies or seeds)
2. Verify both produce valid branches and events
3. Verify no shared state corruption (branch versions, event indices)

**Files**: `tests/test_remix_recombination.py`
**Acceptance**: Concurrent remixes succeed without data corruption.

### T-CROSS-004: Add remix output size limit

Add `max_remix_output_chars` to `Settings` (default 1_000_000). In `RemixService._apply_strategy()`, truncate output if it exceeds the limit and add a warning to the diff_summary. This prevents unbounded storage in `BranchEvent.event_payload`.

**Files**: `src/nexus_babel/services/remix.py`, `src/nexus_babel/config.py`
**Acceptance**: Remix output truncated at limit. Warning included in diff_summary. Config overridable.

### T-CROSS-005: Improve error messages for missing sources

Replace silent `""` return in `_resolve_text()` with explicit checks:
1. If `branch_id` is provided but branch does not exist: raise `ValueError(f"Branch {branch_id} not found")`
2. If `document_id` is provided but document does not exist: raise `ValueError(f"Document {document_id} not found")`
3. Map these to HTTP 404 in the route handler

**Files**: `src/nexus_babel/services/remix.py`, `src/nexus_babel/api/routes.py`
**Acceptance**: Nonexistent document/branch returns 404 with specific message. Existing behavior unchanged for valid IDs.

### T-CROSS-006: Add glyph_collide cap info to diff_summary

Include `glyph_cap_applied: true` and `original_max_length` in `diff_summary` when the 2000-char cap truncates output. This makes truncation visible to API consumers.

**Files**: `src/nexus_babel/services/remix.py`
**Acceptance**: diff_summary includes cap info when truncation occurs. No change when output fits within cap.

### T-CROSS-007: Update CLAUDE.md with domain spec references

Add a section to the project CLAUDE.md pointing to the new `specs/04-remix-recombination/` directory and summarizing the domain's P1/P2/P3 scope.

**Files**: `CLAUDE.md`
**Acceptance**: CLAUDE.md references the spec files.

---

## Task Dependency Graph

```
Phase 1 (Setup)
  T-SETUP-001 ─┐
  T-SETUP-002 ─┤── All can run in parallel [P]
  T-SETUP-003 ─┘

Phase 2 (Foundational)
  T-FOUND-001 -> T-FOUND-002
  T-FOUND-003 (independent, can run in parallel with T-FOUND-001)

Phase 3 (P1 Verification) -- all can run in parallel [P]
  T-P1-001 through T-P1-012 (depend on T-SETUP-001)

Phase 4 (P2 Completion)
  T-FOUND-001 -> T-FOUND-002 -> T-P2-001 -> T-P2-002
  T-FOUND-003 -> T-P2-003 ─┐
                 T-P2-004 ─┤── T-P2-005
  T-P2-001 -> T-P2-006 -> T-P2-007
  T-FOUND-003 + T-P2-001 -> T-P2-008 -> T-P2-009

Phase 5 (P3 Vision)
  T-P3-001 (independent)
  T-P3-001 -> T-P3-002 -> T-P3-003 -> T-P3-004
  T-P3-005 (depends on T-P2-001)
  T-P3-006 (depends on T-P2-001)
  T-P3-007 (independent)

Phase 6 (Cross-Cutting)
  T-CROSS-001 (depends on Phase 3 completion)
  T-CROSS-002 (depends on T-P1-001..T-P1-004)
  T-CROSS-003 (depends on T-P1-007)
  T-CROSS-004 (depends on T-P1-004)
  T-CROSS-005 (depends on T-P1-005)
  T-CROSS-006 (depends on T-P1-004)
  T-CROSS-007 (no deps)
```

## Summary

| Phase | Tasks | Parallel | Scope |
|-------|-------|----------|-------|
| Phase 1: Setup | 3 | All [P] | Test infrastructure, baseline verification |
| Phase 2: Foundational | 3 | Partial | New ORM models, migration, schema extensions |
| Phase 3: P1 Verification | 12 | All [P] | Harden existing as-built behavior with targeted tests |
| Phase 4: P2 Completion | 9 | Partial | Artifact persistence, retrieval endpoints, governance traces, break-off hook |
| Phase 5: P3 Vision | 7 | Partial | Atom-level remix, async, lineage graph, N-way design |
| Phase 6: Cross-Cutting | 7 | Partial | CI, benchmarks, concurrency, error handling, size limits |
| **Total** | **41** | | |
