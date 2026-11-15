# Governance & Audit -- Task List

## Phase 1: Setup

### T-SETUP-001: Create domain test file [P]

Create `tests/test_governance_audit.py` with domain-specific fixtures and imports. Reuse `conftest.py` fixtures (`client`, `auth_headers`). Add helper functions for common governance evaluation calls (evaluate_public, evaluate_raw).

**Files**: `tests/test_governance_audit.py`, `tests/conftest.py`
**Acceptance**: File exists, `pytest tests/test_governance_audit.py -v` passes with 0 tests collected (skeleton).

### T-SETUP-002: Verify existing test coverage baseline [P]

Run `pytest tests/test_mvp.py::test_dual_mode_regression tests/test_mvp.py::test_role_and_raw_mode_enforcement tests/test_wave2.py::test_hypergraph_query_and_audit_decisions -v` and document which governance tests pass. Identify any regressions.

**Files**: `tests/test_mvp.py`, `tests/test_wave2.py`
**Acceptance**: All 3 governance-related tests pass. Coverage report for `services/governance.py`, `services/auth.py` captured.

### T-SETUP-003: Add ruff and mypy targets for governance files [P]

Ensure `[tool.ruff]` and `[tool.mypy]` sections in `pyproject.toml` cover `src/nexus_babel/services/governance.py` and `src/nexus_babel/services/auth.py`.

**Files**: `pyproject.toml`
**Acceptance**: `ruff check src/nexus_babel/services/governance.py src/nexus_babel/services/auth.py` passes. `mypy` type-checks both files with 0 errors.

---

## Phase 2: Foundational -- Schema & Bug Fixes

### T-FOUND-001: Add `redacted_text` to GovernanceEvaluateResponse schema [Story: US-013]

Add `redacted_text: str` field to `GovernanceEvaluateResponse` in `schemas.py`. Update the route handler in `routes.py` to pass `decision["redacted_text"]` through to the response constructor.

**Files**: `src/nexus_babel/schemas.py`, `src/nexus_babel/api/routes.py`
**Acceptance**: `POST /api/v1/governance/evaluate` returns `redacted_text` in the JSON response body. Existing tests continue to pass (new field is additive).

### T-FOUND-002: Propagate actor identity to audit log [Story: FR-033]

Add an `actor` parameter to `GovernanceService.evaluate()` (default `"system"`). Update the route handler to pass `auth_context.owner` as the actor. Update the `AuditLog` creation to use the parameter instead of the hardcoded `"system"`.

**Files**: `src/nexus_babel/services/governance.py`, `src/nexus_babel/api/routes.py`
**Acceptance**: Audit log entries created via the API show the API key owner (e.g., `"dev-operator"`) instead of `"system"`. Direct service calls without an actor still default to `"system"`.

### T-FOUND-003: Add PolicyDecision.audit_id as formal FK [P]

The `audit_id` field on `PolicyDecision` is currently a plain `String(36)` without a formal `ForeignKey` constraint to `audit_logs.id` (`models.py:167`). Add `ForeignKey("audit_logs.id", ondelete="SET NULL")` and make the column nullable to handle orphaned decisions gracefully. Create an Alembic migration.

**Files**: `src/nexus_babel/models.py`, `alembic/versions/20260223_0003_policy_decision_audit_fk.py`
**Acceptance**: Migration applies cleanly on SQLite and PostgreSQL. Existing data is preserved. Deleting an audit log sets `audit_id` to NULL on linked decisions.

---

## Phase 3: User Stories -- P1 Verification & Hardening

### T-P1-001: Add dual-mode evaluation unit tests [Story: US-001, US-002, US-003] [P]

Test `GovernanceService.evaluate()` directly (not via HTTP):
- PUBLIC mode with single blocked term -> `allow=False`, `policy_hits` contains term
- RAW mode with single blocked term -> `allow=True`, `policy_hits` contains term
- PUBLIC mode with clean text -> `allow=True`, empty `policy_hits`
- RAW mode with clean text -> `allow=True`, empty `policy_hits`
- `redacted_text` in PUBLIC uses `"[REDACTED]"`, RAW uses `"[FLAGGED]"`

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-002: Add multi-term matching tests [Story: US-011] [P]

Test:
- Text with 2 different blocked terms -> both in `policy_hits`, 2+ entries in `decision_trace.hits`
- Text with same blocked term appearing twice -> 1 entry in `policy_hits`, 2 entries in `decision_trace.hits` (two match positions)
- All 6 default blocked terms each independently matchable in isolation
- Multi-word term "ethnic cleansing" matches as a phrase
- Multi-word term "how to make a bomb" matches as a phrase

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-003: Add word-boundary matching edge case tests [Story: US-011] [P]

Test:
- `"skill"` does NOT match blocked term `"kill"` (word boundary prevents substring match)
- `"hated"` does NOT match blocked term `"hate"` (actually it DOES because `\bhate\b` matches "hate" in "hated" -- verify actual behavior and document)
- `"KILL"` matches `"kill"` (case-insensitive)
- `"Kill"` matches `"kill"` (mixed case)
- `"killed"` -- verify whether `\bkill\b` matches (it should NOT since "ed" breaks the boundary)
- Term at start of text, end of text, middle of text all match
- Term surrounded by punctuation (e.g., `"kill,"` `"(kill)"`) matches

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=7 tests, all pass. Document any surprising behavior from the regex engine.

### T-P1-004: Add mode enforcement tests [Story: US-004, US-005] [P]

Test via HTTP:
- Viewer -> `POST /governance/evaluate` -> 403 (role insufficient)
- Operator -> `POST /governance/evaluate` with mode=PUBLIC -> 200
- Operator -> `POST /governance/evaluate` with mode=RAW -> 403 (operator lacks RAW access)
- Researcher -> `POST /governance/evaluate` with mode=RAW -> 200
- Admin -> `POST /governance/evaluate` with mode=RAW -> 200
- Researcher with `raw_mode_enabled=False` on key -> `POST /governance/evaluate` with mode=RAW -> 403

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=6 tests, all pass.

### T-P1-005: Add `mode_allows()` unit tests [Story: US-004, US-005] [P]

Test `AuthService.mode_allows()` directly:
- `mode_allows("viewer", "PUBLIC", True, True)` -> False (viewer < operator)
- `mode_allows("operator", "PUBLIC", True, True)` -> True
- `mode_allows("operator", "RAW", True, True)` -> False (operator < researcher)
- `mode_allows("researcher", "RAW", True, True)` -> True
- `mode_allows("researcher", "RAW", False, True)` -> False (global disabled)
- `mode_allows("researcher", "RAW", True, False)` -> False (key disabled)
- `mode_allows("admin", "RAW", True, True)` -> True
- `mode_allows("admin", "UNKNOWN", True, True)` -> False (unknown mode)

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=8 tests, all pass.

### T-P1-006: Add policy bootstrap tests [Story: US-006] [P]

Test:
- After app startup, PUBLIC and RAW ModePolicy records exist
- PUBLIC policy has `redaction_style="[REDACTED]"`, `hard_block_threshold=1`
- RAW policy has `redaction_style="[FLAGGED]"`, `hard_block_threshold=999`
- Both policies have `policy_version=1`
- Both policies have all 6 default blocked terms (sorted, lowercased, deduplicated)
- Restarting the app does NOT overwrite existing policies (idempotent)
- Existing policy with `effective_from=None` gets backfilled on restart

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=6 tests, all pass.

### T-P1-007: Add audit log creation tests [Story: US-007] [P]

Test:
- After evaluation, an AuditLog record exists with `action="governance.evaluate"`
- Audit log `mode` matches the requested mode
- Audit log `details.input_preview` is the first 240 characters of the input
- For input >240 chars, `input_preview` is truncated to 240
- Audit log `details.policy_version` matches the active policy version
- `audit_id` in the response matches the created AuditLog record's ID

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-008: Add policy decision recording tests [Story: US-008] [P]

Test:
- After evaluation, a PolicyDecision record exists
- `input_hash` is the SHA256 hex digest of the candidate text
- `policy_hits` and `redactions` match the evaluation result
- `decision_trace` contains all expected keys (mode, policy_version, hits, mode_rationale, redaction_style, allow, hard_block_threshold)
- `audit_id` on the PolicyDecision matches the linked AuditLog

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-009: Add policy decisions listing tests [Story: US-009] [P]

Test via HTTP:
- `GET /audit/policy-decisions` returns 200 for operator
- `GET /audit/policy-decisions` returns 403 for viewer
- After N evaluations, listing returns N decisions ordered by created_at DESC
- `limit` parameter is respected (returns at most N)
- Each decision has expected fields: id, mode, allow, policy_hits, redactions, decision_trace, audit_id, created_at

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-010: Add decision trace detail tests [Story: US-010] [P]

Test:
- Decision trace `hits` list has one entry per match position (not per unique term)
- Each hit has `term`, `start`, `end`, `matched_text`, `rule`, `mode`
- `start` and `end` are correct character positions in the original text
- `matched_text` preserves the original case from the input
- `mode_rationale` is `"PUBLIC blocks flagged terms"` for PUBLIC mode
- `mode_rationale` is `"RAW allows flagged terms for research review"` for RAW mode

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=6 tests, all pass.

### T-P1-011: Add empty and edge case input tests [P]

Test:
- Empty string input -> `allow=True`, empty hits, empty policy_hits
- Whitespace-only input -> `allow=True`, no matches
- Input that is exactly 240 characters -> `input_preview` is the full input
- Input that is 241 characters -> `input_preview` is truncated to 240
- Input with Unicode characters (accented Latin, CJK) -> evaluation completes without error
- Input with only special characters -> `allow=True`, no matches

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=6 tests, all pass.

### T-P1-012: Add policy date range filter tests [Story: US-012] [P]

Test `GovernanceService.evaluate()` with manually crafted policies:
- Policy with `effective_from=past`, `effective_to=None` -> loaded (active, no expiry)
- Policy with `effective_from=past`, `effective_to=future` -> loaded (active, not yet expired)
- Policy with `effective_from=past`, `effective_to=past` -> NOT loaded (expired)
- Policy with `effective_from=future`, `effective_to=None` -> NOT loaded (not yet active)
- No valid policy for mode -> ValueError raised

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=5 tests, all pass.

---

## Phase 4: User Stories -- P2 Completion

### T-P2-001: Add `redacted_text` integration tests [Story: US-013]

Test via HTTP:
- PUBLIC mode with blocked term -> `redacted_text` contains `"[REDACTED]"` replacement
- RAW mode with blocked term -> `redacted_text` contains `"[FLAGGED]"` replacement
- Multiple blocked terms -> all replaced in `redacted_text`
- Clean text -> `redacted_text` equals original input
- Response schema includes `redacted_text` field

Depends on: T-FOUND-001.

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=5 tests, all pass.

### T-P2-002: Implement governance hooks for evolution output [Story: US-014]

Add a `_govern_output()` helper function in `routes.py` (or a decorator) that evaluates text output against the requested mode's governance policy. Integrate it into the `POST /api/v1/evolve/branch` handler to evaluate the branch's `state_snapshot` text after evolution. If PUBLIC mode blocks, the evolution response should include a `governance` field with the decision. If RAW mode flags, include the flags in the response.

**Files**: `src/nexus_babel/api/routes.py`, `src/nexus_babel/services/governance.py`
**Acceptance**: Evolution output in PUBLIC mode that contains blocked terms returns `governance.allow=False` alongside the evolution result. RAW mode includes flags.

### T-P2-003: Implement governance hooks for remix output [Story: US-014]

Add governance evaluation to the `POST /api/v1/remix` handler. After remix produces a new branch, evaluate the remixed text against the mode's governance policy. Include governance decision in the remix response.

Depends on: T-P2-002 (shared helper).

**Files**: `src/nexus_babel/api/routes.py`
**Acceptance**: Remix output evaluated against governance policy. Decision included in response.

### T-P2-004: Add governance hook integration tests [Story: US-014]

Test:
- Evolution producing text with blocked term in PUBLIC mode -> governance flag in response
- Evolution in RAW mode -> flagged but allowed
- Remix in PUBLIC mode with blocked term in source -> governance flag
- Clean evolution/remix -> no governance flags

Depends on: T-P2-002, T-P2-003.

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=4 tests, all pass.

### T-P2-005: Implement decision caching by input hash [Story: US-015]

In `GovernanceService.evaluate()`, before performing the evaluation, check for an existing `PolicyDecision` with the same `(mode, input_hash)` where the `decision_trace.policy_version` matches the current policy version. If found, return the cached decision (with a `cached: True` indicator) instead of creating new audit and decision records. Add a `cache_hit` field to the return dict.

**Files**: `src/nexus_babel/services/governance.py`
**Acceptance**: Evaluating the same text in the same mode twice returns the cached result on the second call. No new AuditLog or PolicyDecision created for the cached call. Policy version change invalidates cache.

### T-P2-006: Add decision caching tests [Story: US-015]

Test:
- Same text + same mode -> second call returns cached result, no new DB records
- Same text + different mode -> separate evaluations (cache miss)
- Different text + same mode -> separate evaluations (cache miss)
- Same text after policy version change -> cache invalidated, new evaluation

Depends on: T-P2-005.

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=4 tests, all pass.

### T-P2-007: Add audit log actor identity tests [Story: FR-033]

Test via HTTP:
- Evaluation by operator -> audit log `actor` is `"dev-operator"`
- Evaluation by researcher -> audit log `actor` is `"dev-researcher"`
- Evaluation by admin -> audit log `actor` is `"dev-admin"`

Depends on: T-FOUND-002.

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=3 tests, all pass.

---

## Phase 5: User Stories -- P3 Vision

### T-P3-001: Implement policy CRUD API endpoints [Story: US-016]

Create new endpoints:
- `GET /api/v1/governance/policies` (admin) -- list all policies with version history
- `GET /api/v1/governance/policies/{mode}` (operator) -- get active policy for mode
- `PUT /api/v1/governance/policies/{mode}` (admin) -- update policy (increments version, sets effective_from on new, effective_to on old)
- `POST /api/v1/governance/policies` (admin) -- create new mode policy

Add corresponding Pydantic schemas: `PolicyResponse`, `PolicyUpdateRequest`.

**Files**: `src/nexus_babel/api/routes.py`, `src/nexus_babel/schemas.py`, `src/nexus_babel/services/governance.py`
**Acceptance**: Admin can create, read, and update policies via API. Version number increments on update. Old policy gets `effective_to` timestamp.

### T-P3-002: Add policy CRUD tests [Story: US-016]

Test:
- List policies returns PUBLIC and RAW with version 1
- Update PUBLIC policy increments to version 2
- Old version has `effective_to` set
- New evaluation uses updated policy
- Non-admin role cannot update/create policies (403)
- Invalid mode name rejected

**Files**: `tests/test_governance_audit.py`
**Acceptance**: >=6 tests, all pass.

### T-P3-003: Implement custom blocked term management [Story: US-017]

Add endpoints:
- `POST /api/v1/governance/policies/{mode}/terms` (admin) -- add blocked terms
- `DELETE /api/v1/governance/policies/{mode}/terms` (admin) -- remove blocked terms
- `GET /api/v1/governance/policies/{mode}/terms` (operator) -- list blocked terms

Each term modification creates a new policy version.

**Files**: `src/nexus_babel/api/routes.py`, `src/nexus_babel/services/governance.py`
**Acceptance**: Admin can add/remove blocked terms. Policy version increments. Evaluations use updated terms.

### T-P3-004: Implement policy history and rollback [Story: US-018]

Change `ModePolicy` to store all versions (not just current). Add:
- `GET /api/v1/governance/policies/{mode}/history` (admin) -- list all versions
- `POST /api/v1/governance/policies/{mode}/rollback` (admin) -- rollback to specified version

Rollback creates a new version that copies the target version's policy JSON, setting `effective_from=utcnow()`.

**Files**: `src/nexus_babel/services/governance.py`, `src/nexus_babel/api/routes.py`, `src/nexus_babel/models.py`
**Acceptance**: Admin can view policy history and rollback. Rollback creates new version. Old evaluations reference their original policy version.

### T-P3-005: Implement general audit log endpoint [Story: FR-034]

Add `GET /api/v1/audit/logs` (admin) endpoint that returns all audit log entries (not just governance decisions) with filtering by action, mode, actor, and date range.

**Files**: `src/nexus_babel/api/routes.py`, `src/nexus_babel/services/governance.py`
**Acceptance**: Endpoint returns audit logs with filtering. Supports pagination via offset+limit.

### T-P3-006: Add audit log generalization for other domains [Story: FR-034]

Add `AuditService` class with `log(session, action, mode, actor, details)` method. Integrate into ingestion, evolution, remix, and analysis services so that all significant operations produce audit log entries.

**Files**: `src/nexus_babel/services/audit.py` (new), `src/nexus_babel/services/ingestion.py`, `src/nexus_babel/services/evolution.py`, `src/nexus_babel/services/remix.py`
**Acceptance**: Ingestion, evolution, and remix operations produce audit log entries. `GET /api/v1/audit/logs` returns entries from all domains.

### T-P3-007: Implement global RAW mode toggle API [Story: US-022]

Add `PUT /api/v1/governance/settings/raw-mode` (admin) endpoint that toggles `raw_mode_enabled` at runtime. Store the override in the database (new `SystemSetting` model) so it persists across restarts but does not require env var changes.

**Files**: `src/nexus_babel/api/routes.py`, `src/nexus_babel/models.py`, `src/nexus_babel/services/governance.py`
**Acceptance**: Admin can toggle RAW mode via API. Change takes effect immediately. Persists across restart.

### T-P3-008: Implement artifact state tracking [Story: US-019]

Create an `ArtifactLedger` model with fields: `entity_type` (document/branch/remix/analysis), `entity_id`, `state` (proposed/in_progress/saved/accepted/rejected), `proposed_by`, `decided_by`, `decided_at`, `receipt_hash`. Add API endpoints for proposing, accepting, and rejecting artifacts.

**Files**: `src/nexus_babel/models.py`, `src/nexus_babel/services/governance.py`, `src/nexus_babel/api/routes.py`, `src/nexus_babel/schemas.py`
**Acceptance**: Artifacts can be proposed and moved through the state machine. Each transition is audited. Accept/reject requires explicit action.

---

## Phase 6: Cross-Cutting

### T-CROSS-001: Wire governance domain tests into CI [P]

Update `.github/workflows/ci-minimal.yml` to run `pytest tests/test_governance_audit.py -v` as part of the pipeline.

**Files**: `.github/workflows/ci-minimal.yml`
**Acceptance**: CI runs the governance test suite and fails on regression.

### T-CROSS-002: Add governance evaluation performance benchmark

Create a benchmark in `scripts/benchmark_governance.py` that:
1. Seeds a policy with 6, 50, and 200 blocked terms
2. Evaluates texts of 100, 1000, 10000 characters against each policy size
3. Records wall time per evaluation
4. Prints summary table: `terms | text_size | eval_ms`
5. Asserts 10KB text against 6 terms completes in <50ms

**Files**: `scripts/benchmark_governance.py`
**Acceptance**: Script runs end-to-end. Baseline captured. No evaluation exceeds 500ms.

### T-CROSS-003: Add regex pattern pre-compilation optimization

Profile `GovernanceService.evaluate()` with a large blocked terms list (200+). If regex compilation is a bottleneck, pre-compile all patterns at policy load time and cache them on the service instance. Alternatively, combine all terms into a single alternation pattern: `\b(term1|term2|...)\b`.

**Files**: `src/nexus_babel/services/governance.py`
**Acceptance**: Evaluation with 200 blocked terms is <2x slower than with 6 terms. Pattern compilation happens once per policy load, not per evaluation.

### T-CROSS-004: Add concurrent governance evaluation safety test

Test that two simultaneous `POST /governance/evaluate` calls produce correct and independent audit log and policy decision records. Verify no ID collisions or record corruption.

**Files**: `tests/test_governance_audit.py`
**Acceptance**: Concurrent evaluations produce 2 independent AuditLog and 2 independent PolicyDecision records with distinct IDs.

### T-CROSS-005: Update CLAUDE.md with domain spec references

Add a section to the project CLAUDE.md pointing to the new `specs/05-governance-audit/` directory and summarizing the domain's P1/P2/P3 scope.

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
  T-FOUND-001 (redacted_text schema fix -- independent)
  T-FOUND-002 (actor propagation -- independent)
  T-FOUND-003 (FK constraint -- independent)

Phase 3 (P1 Verification) -- all can run in parallel [P]
  T-P1-001 through T-P1-012 (depend on T-SETUP-001)

Phase 4 (P2 Completion)
  T-FOUND-001 -> T-P2-001 (redacted_text integration tests)
  T-FOUND-002 -> T-P2-007 (actor identity tests)
  T-P2-002 -> T-P2-003 -> T-P2-004 (governance hooks chain)
  T-P2-005 -> T-P2-006 (decision caching chain)

Phase 5 (P3 Vision)
  T-P3-001 -> T-P3-002 (policy CRUD chain)
  T-P3-001 -> T-P3-003 (term management depends on CRUD)
  T-P3-001 -> T-P3-004 (rollback depends on CRUD + versioning)
  T-P3-005 -> T-P3-006 (audit generalization chain)
  T-P3-007 (RAW toggle -- independent)
  T-P3-008 (artifact state -- independent but large)

Phase 6 (Cross-Cutting)
  T-CROSS-001 (depends on Phase 3 completion)
  T-CROSS-002 (depends on T-SETUP-001)
  T-CROSS-003 (depends on T-CROSS-002 benchmark results)
  T-CROSS-004 (depends on T-P1-001)
  T-CROSS-005 (no deps)
```

## Summary

| Phase | Tasks | Parallel | Scope |
|-------|-------|----------|-------|
| Phase 1: Setup | 3 | All [P] | Test infrastructure, baseline verification |
| Phase 2: Foundational | 3 | All [P] | Schema fix, actor propagation, FK constraint |
| Phase 3: P1 Verification | 12 | All [P] | Harden existing as-built governance + audit behavior |
| Phase 4: P2 Completion | 7 | Partial | redacted_text, pipeline hooks, caching, actor tests |
| Phase 5: P3 Vision | 8 | Partial | Policy CRUD, term mgmt, rollback, audit generalization, artifact tracking |
| Phase 6: Cross-Cutting | 5 | Partial | CI, benchmarks, optimization, concurrency |
| **Total** | **38** | | |
