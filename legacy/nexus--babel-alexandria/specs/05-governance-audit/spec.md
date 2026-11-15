# Governance & Audit -- Specification

## Overview

The Governance & Audit domain provides dual-mode content filtering, policy evaluation, audit logging, and decision tracking for Nexus Babel Alexandria. All text outputs -- whether from ingestion, analysis, evolution, or remix -- can be evaluated against mode-specific policies that either block or flag sensitive content depending on the operational mode.

The system operates in two modes: **PUBLIC** mode enforces strict content filtering (blocks on first hit) to prevent harmful content from surfacing, while **RAW** mode allows flagged content through for scholarly research with appropriate warnings and tracking. This dual-mode design supports the ARC4N Living Digital Canon's need to preserve and study literary works that may contain historically sensitive language while maintaining safe defaults for general use.

The audit subsystem creates permanent records of every governance evaluation, including the full decision trace with per-term match positions, policy version, and mode rationale. This supports transparency, reproducibility, and compliance requirements. Policy decisions are independently queryable and linked to their audit log entries via foreign key.

## User Stories

### P1 -- As-Built (Verified)

#### US-001: Dual-mode content evaluation

> As an **operator**, I want to evaluate candidate text against the active governance policy so that content is filtered (PUBLIC) or flagged (RAW) before being surfaced to users.

**Given** a candidate text string and a governance mode (PUBLIC or RAW)
**When** I `POST /api/v1/governance/evaluate` with `candidate_output` and `mode`
**Then**:
- The mode is normalized to uppercase (`governance.py:46`)
- The active `ModePolicy` for that mode is loaded with effective date range check (`governance.py:48-54`)
- If no policy exists for the mode, a `ValueError` is raised (`governance.py:55-56`)
- Each blocked term is matched against the text using regex word-boundary matching with `re.IGNORECASE` (`governance.py:70`)
- For each match: the term, start/end character positions, matched text, rule name, and mode are recorded in the decision trace (`governance.py:74-84`)
- Matched terms are collected into `policy_hits` and `redactions` lists (`governance.py:71-73`)
- The text is redacted using the policy's `redaction_style` (`governance.py:85-90`)
- The `allow` flag is computed: `len(policy_hits) < hard_block_threshold` (`governance.py:92`)
  - PUBLIC: threshold=1, so any hit blocks (`allow=False`)
  - RAW: threshold=999, so effectively never blocks (`allow=True`)
- A full `decision_trace` dict is built with mode, policy_version, hard_block_threshold, hits, mode_rationale, redaction_style, and allow (`governance.py:93-101`)
- An `AuditLog` record is created with action=`"governance.evaluate"`, input preview (first 240 chars), policy_hits, policy_version, allow, and full decision_trace (`governance.py:103-114`)
- A `PolicyDecision` record is created with mode, SHA256 of input, allow, policy_hits, redactions, decision_trace, and FK to the audit log (`governance.py:118-126`)
- The response includes `allow`, `policy_hits`, `redactions`, `audit_id`, `redacted_text`, and `decision_trace` (`governance.py:129-136`)

**Code evidence:** `test_mvp.py:183-205` (`test_dual_mode_regression`), `test_wave2.py:132-151` (`test_hypergraph_query_and_audit_decisions`).

#### US-002: PUBLIC mode blocks on first hit

> As the **system**, I want PUBLIC mode to block any text containing at least one blocked term so that harmful content never passes through to end users.

**Given** a text containing the word "kill" and mode="PUBLIC"
**When** governance evaluation runs
**Then**:
- `policy_hits` includes `"kill"` (`governance.py:72`)
- `hard_block_threshold` is 1 (`governance.py:21`)
- `len(policy_hits)` (1) >= threshold (1), so `allow=False` (`governance.py:92`)
- `redactions` includes `"kill"` (`governance.py:73`)
- `redacted_text` has "kill" replaced with `"[REDACTED]"` (`governance.py:85-90`)
- `decision_trace.mode_rationale` = `"PUBLIC blocks flagged terms"` (`governance.py:98`)

**Code evidence:** `test_mvp.py:200-204` asserts `public_payload["allow"] is False` and `"kill" in public_payload["policy_hits"]`.

#### US-003: RAW mode allows with flagging

> As a **researcher**, I want RAW mode to allow text through even when blocked terms are present so that I can study sensitive literary material with full awareness of flagged content.

**Given** a text containing the word "kill" and mode="RAW"
**When** governance evaluation runs by a researcher
**Then**:
- `policy_hits` includes `"kill"` (`governance.py:72`)
- `hard_block_threshold` is 999 (`governance.py:27`)
- `len(policy_hits)` (1) < threshold (999), so `allow=True` (`governance.py:92`)
- `redactions` includes `"kill"` (`governance.py:73`)
- `redacted_text` has "kill" replaced with `"[FLAGGED]"` (`governance.py:85-90`)
- `decision_trace.mode_rationale` = `"RAW allows flagged terms for research review"` (`governance.py:98`)

**Code evidence:** `test_mvp.py:200-205` asserts `raw_payload["allow"] is True` and `"kill" in raw_payload["policy_hits"]`.

#### US-004: RAW mode access enforcement

> As the **system**, I want to restrict RAW mode access to researchers and above with explicit RAW mode permission so that sensitive content is not casually accessible.

**Given** the `mode_allows()` function in `auth.py:66-76`
**When** a RAW mode evaluation is requested
**Then**:
- The global `raw_mode_enabled` setting must be `True` (`auth.py:69-70`)
- The API key's `raw_mode_enabled` flag must be `True` (`auth.py:71-72`)
- The requesting role must be `researcher` or higher (role_allows with min_role=`"researcher"`) (`auth.py:73`)
- If any condition fails, mode access is denied with HTTP 403 (`routes.py:74-84`)

**Code evidence:** `test_mvp.py:54-66` (`test_role_and_raw_mode_enforcement`): operator gets 403 on RAW, researcher gets 200. `test_mvp.py:68-73`: whoami shows operator has `["PUBLIC"]`, researcher has `["PUBLIC", "RAW"]`.

#### US-005: PUBLIC mode access enforcement

> As the **system**, I want to restrict PUBLIC mode governance evaluation to operators and above so that viewers cannot trigger policy evaluation.

**Given** mode="PUBLIC"
**When** `mode_allows()` is called
**Then**:
- Role must be `operator` or higher (`auth.py:75`)
- The route itself requires `operator` minimum via `_require_auth("operator")` (`routes.py:339`)

**Code evidence:** `test_mvp.py:46-52` (`test_role_and_raw_mode_enforcement`): viewer gets 403 on ingest (same operator requirement).

#### US-006: Bootstrap default policies at startup

> As the **system**, I want PUBLIC and RAW mode policies to be seeded automatically at application startup so that governance evaluation works out of the box.

**Given** the app lifespan handler in `main.py:33-50`
**When** the application starts
**Then**:
- `GovernanceService.ensure_default_policies()` is called with `settings.public_blocked_terms` (`main.py:47`)
- Default blocked terms are: `["kill", "self-harm", "hate", "ethnic cleansing", "bioweapon", "how to make a bomb"]` (`config.py:33-42`)
- Terms are lowercased, deduplicated, and sorted (`governance.py:16`)
- Two `ModePolicy` records are created if they do not exist (`governance.py:30-43`):
  - PUBLIC: `redaction_style="[REDACTED]"`, `hard_block_threshold=1`
  - RAW: `redaction_style="[FLAGGED]"`, `hard_block_threshold=999`
- Both policies start at `policy_version=1` with `effective_from=utcnow()` and `effective_to=None`
- If a policy already exists, it is NOT overwritten; only `effective_from` is backfilled if null (`governance.py:32-35`)

**Code evidence:** All tests that call governance/evaluate work without explicit policy setup, proving bootstrap runs in conftest/client fixture via `create_app()`.

#### US-007: Audit log creation

> As the **system**, I want every governance evaluation to create an audit log entry so that all decisions are permanently traceable.

**Given** a governance evaluation
**When** the evaluation completes
**Then**:
- An `AuditLog` record is created with:
  - `action`: `"governance.evaluate"` (`governance.py:104`)
  - `mode`: normalized mode string (`governance.py:105`)
  - `actor`: `"system"` (hardcoded) (`governance.py:106`)
  - `details`: JSON with `input_preview` (first 240 chars of candidate_output), `policy_hits`, `policy_version`, `allow`, `decision_trace` (`governance.py:107-113`)
  - `created_at`: auto-set UTC timestamp (`models.py:201`)
- The audit log is flushed to get its ID before the PolicyDecision is created (`governance.py:116`)
- The `audit_id` is returned in the response (`governance.py:133`)

**Code evidence:** `test_wave2.py:144-151` verifies `decision_trace` in audit decisions; `test_mvp.py:297` confirms 200 status on governance evaluate.

#### US-008: Policy decision recording

> As an **operator**, I want every governance evaluation to produce a queryable policy decision record so that I can review past decisions and their outcomes.

**Given** a completed governance evaluation
**When** the evaluation is persisted
**Then**:
- A `PolicyDecision` record is created with:
  - `mode`: normalized mode (`governance.py:120`)
  - `input_hash`: SHA256 hex digest of `candidate_output` (`governance.py:121`)
  - `allow`: boolean result (`governance.py:122`)
  - `policy_hits`: list of matched terms (`governance.py:123`)
  - `redactions`: list of terms that were redacted (`governance.py:124`)
  - `decision_trace`: full trace dict (`governance.py:125`)
  - `audit_id`: FK linking to the audit log entry (`governance.py:126`)
  - `created_at`: auto-set UTC timestamp (`models.py:168`)

**Code evidence:** `test_wave2.py:147-151` queries `GET /api/v1/audit/policy-decisions` and asserts `decision_trace` is present in the first row.

#### US-009: List policy decisions

> As an **operator**, I want to list recent governance decisions so that I can audit evaluation history and spot patterns.

**Given** one or more governance evaluations have been performed
**When** I `GET /api/v1/audit/policy-decisions?limit=N`
**Then**:
- Returns up to `N` (default 100, max 1000) `PolicyDecision` records ordered by `created_at` descending (`governance.py:139`)
- Each record includes `id`, `mode`, `allow`, `policy_hits`, `redactions`, `decision_trace`, `audit_id`, `created_at` (`governance.py:141-152`)
- Requires `operator` role minimum (`routes.py:629`)

**Code evidence:** `test_wave2.py:147-151` (`test_hypergraph_query_and_audit_decisions`).

#### US-010: Decision trace detail

> As a **researcher**, I want each governance decision to include a detailed trace showing exactly which terms were matched, where in the text they occurred, and what rule triggered them, so that I can understand and audit the decision.

**Given** a governance evaluation that matches one or more blocked terms
**When** the decision trace is generated
**Then**:
- `decision_trace` contains:
  - `mode`: normalized mode string (`governance.py:94`)
  - `policy_version`: integer version of the active policy (`governance.py:95`)
  - `hard_block_threshold`: the threshold used for the allow/block decision (`governance.py:96`)
  - `hits`: list of hit dicts, each with `term`, `start`, `end`, `matched_text`, `rule`, `mode` (`governance.py:97`)
  - `mode_rationale`: human-readable explanation of mode behavior (`governance.py:98`)
  - `redaction_style`: the replacement string used (`governance.py:99`)
  - `allow`: the final allow/block decision (`governance.py:100`)

**Code evidence:** `test_wave2.py:144-145` asserts `trace["hits"]` is truthy after matching "kill".

#### US-011: Regex word-boundary matching

> As the **system**, I want blocked term matching to use regex word boundaries so that substring matches are avoided (e.g., "skill" does not match "kill").

**Given** the blocked term `"kill"` and input text `"These skills are valuable"`
**When** governance evaluation runs
**Then**:
- The regex `\bkill\b` does NOT match `"skills"` because of the word boundary
- `policy_hits` is empty
- `allow` is `True`

**Given** the blocked term `"kill"` and input text `"we should kill this"`
**When** governance evaluation runs
**Then**:
- The regex `\bkill\b` matches `"kill"` at the word boundary
- `policy_hits` includes `"kill"`

**Code evidence:** `governance.py:70` uses `rf"\b{re.escape(term)}\b"` with `re.IGNORECASE`. Covered transitively by `test_mvp.py:183-205`.

#### US-012: Policy versioning and effective date ranges

> As the **system**, I want policies to carry a version number and effective date range so that policy changes can be tracked and historical evaluations can reference the correct policy.

**Given** a ModePolicy record
**When** a governance evaluation runs
**Then**:
- Only policies with valid effective date ranges are loaded: `effective_from <= now` (or null) AND `effective_to > now` (or null) (`governance.py:51-53`)
- The policy's `policy_version` is included in the `decision_trace` (`governance.py:95`)
- The policy's `policy_version` is included in the audit log details (`governance.py:110`)

**Code evidence:** `governance.py:48-53` (date range filter), `governance.py:95` (version in trace).

### P2 -- Partially Built

#### US-013: Redacted text output

> As an **operator**, I want the governance response to include the full redacted version of the input text so that I can see exactly how the text would appear after filtering.

**Current state**: `GovernanceService.evaluate()` builds `redacted_text` by applying `re.sub()` for each matched term (`governance.py:85-90`). The field is included in the service return dict (`governance.py:134`) but is NOT included in the `GovernanceEvaluateResponse` Pydantic schema (`schemas.py:134-139`). The route handler constructs the response from the dict without mapping `redacted_text` (`routes.py:350-356`).

**Gap**: The `redacted_text` field is computed but silently dropped at the API boundary. The `GovernanceEvaluateResponse` schema needs a `redacted_text: str` field and the route must pass it through.

#### US-014: Governance evaluation for pipeline outputs

> As an **operator**, I want evolution, remix, and analysis outputs to be automatically evaluated against governance policies so that harmful content generated by the system is caught before being returned.

**Current state**: Governance evaluation is only available as a manual API call (`POST /api/v1/governance/evaluate`). The evolution (`routes.py:232-258`), remix (`routes.py:683-716`), and analysis (`routes.py:137-229`) routes do not call governance evaluation on their outputs. A researcher could evolve or remix text that contains blocked terms without any governance check.

**Gap**: No automatic governance evaluation integrated into the evolution, remix, or analysis pipelines. This would require adding a post-processing governance pass to each service's output before returning results.

#### US-015: Input hash deduplication for decisions

> As the **system**, I want policy decisions to be indexed by input hash so that repeated evaluations of the same text can be detected and potentially short-circuited.

**Current state**: The `input_hash` field (SHA256 of `candidate_output`) is computed and stored on every `PolicyDecision` (`governance.py:121`, `models.py:162`). It is indexed in the database (`models.py:162`). However, there is no logic to look up a previous decision by input hash before creating a new one. Every evaluation creates a fresh audit log and decision record regardless of whether the exact same text was previously evaluated in the same mode.

**Gap**: No decision caching or deduplication by input hash. The hash is stored but unused for lookup.

### P3+ -- Vision

#### US-016: Policy CRUD API

> As an **admin**, I want to create, update, and delete governance policies via the API so that blocked terms and thresholds can be managed without redeploying the application.

**Current state**: Policies are only seeded at startup via `ensure_default_policies()`. There is no API endpoint for creating, updating, or deleting policies. The `ModePolicy` model supports versioning (`policy_version`) and effective date ranges (`effective_from`, `effective_to`) which would enable policy rollout and rollback, but this infrastructure is unused.

**Vision ref:** AB-PLAN-04 -- Confirm-build-close ritual requires explicit acceptance of all artifacts; policy CRUD would be the governance layer's artifact management.

#### US-017: Custom blocked term management

> As an **admin**, I want to add, remove, and list blocked terms per mode so that the governance vocabulary can evolve over time.

**Current state**: Blocked terms are defined in `Settings.public_blocked_terms` (config.py:33-42) and baked into the ModePolicy JSON at startup. There is no API for modifying the blocked terms list after startup.

#### US-018: Policy history and rollback

> As an **admin**, I want to view the history of policy changes and roll back to a previous version so that accidental policy modifications can be undone.

**Current state**: `policy_version` is stored but only ever set to 1 at creation. There is no mechanism to increment the version, create a new policy revision, or restore a previous one. The `effective_to` field exists but is never set.

#### US-019: Artifact state tracking

> As a **knowledge operator**, I want every proposed artifact (document, branch, remix, analysis output) to carry an explicit state (Proposed / In-Progress / Saved / Accepted / Rejected) so that the confirm-build-close ritual is enforced.

**Current state**: No artifact state tracking exists. Documents have `ingest_status`, branches have `state_snapshot`, and jobs have `status`, but there is no unified artifact lifecycle model. The AB-PLAN-04 vision calls for a cross-cutting artifact ledger that tracks proposal, acceptance, and save operations across all domain types.

#### US-020: Save receipt generation

> As the **system**, I want every save/persist operation to generate a permanent receipt with timestamp, file path, entity ID, and status so that the system has a verifiable record of all writes.

**Current state**: The `AuditLog` partially covers this for governance evaluations (action + details + timestamp), but there is no generalized save receipt mechanism for document ingestion, branch creation, remix operations, etc.

#### US-021: Thread health metrics

> As a **knowledge operator**, I want to track thread divergence, energy, and productivity metrics so that system health can be monitored and threads that are drifting or stalling can be identified.

**Current state**: The `MetricsService` (`main.py:59`) tracks HTTP request timing and status codes but has no domain-level health metrics for governance threads, evaluation patterns, or policy effectiveness.

#### US-022: Global RAW mode toggle API

> As an **admin**, I want to toggle the global `raw_mode_enabled` setting via the API so that RAW mode can be enabled or disabled without restarting the application.

**Current state**: `raw_mode_enabled` is a `Settings` field loaded from environment/`.env` at startup (`config.py:20`). There is no API endpoint to change it at runtime.

## Functional Requirements

### Governance Evaluation

- **FR-001** [MUST] The system MUST accept `POST /api/v1/governance/evaluate` with `candidate_output` (string) and `mode` (`"PUBLIC"` or `"RAW"`). Implemented: `routes.py:335-364`, `schemas.py:129-131`.
- **FR-002** [MUST] The system MUST normalize the mode to uppercase before processing. Implemented: `governance.py:46`.
- **FR-003** [MUST] The system MUST load the active `ModePolicy` for the requested mode, filtering by effective date range (`effective_from <= now`, `effective_to > now` or null). Implemented: `governance.py:48-54`.
- **FR-004** [MUST] The system MUST raise a `ValueError` if no policy exists for the requested mode. Implemented: `governance.py:55-56`.
- **FR-005** [MUST] The system MUST perform case-insensitive regex word-boundary matching (`\b{term}\b`) for each blocked term against the candidate text. Implemented: `governance.py:70`.
- **FR-006** [MUST] Each match MUST record the term, start position, end position, matched text, rule name (`"blocked_terms"`), and mode in the decision trace. Implemented: `governance.py:74-84`.
- **FR-007** [MUST] The `allow` flag MUST be `True` when the number of unique matched terms is less than the policy's `hard_block_threshold`. Implemented: `governance.py:92`.
- **FR-008** [MUST] PUBLIC mode MUST use `hard_block_threshold=1`, meaning any single term match blocks the content. Implemented: `governance.py:21`.
- **FR-009** [MUST] RAW mode MUST use `hard_block_threshold=999`, meaning content is effectively never blocked. Implemented: `governance.py:27`.
- **FR-010** [MUST] The system MUST produce a `redacted_text` by replacing matched terms with the policy's `redaction_style`. Implemented: `governance.py:85-90`.
- **FR-011** [MUST] PUBLIC mode MUST use `"[REDACTED]"` as the redaction style. Implemented: `governance.py:19`.
- **FR-012** [MUST] RAW mode MUST use `"[FLAGGED]"` as the redaction style. Implemented: `governance.py:26`.
- **FR-013** [SHOULD] The `redacted_text` field SHOULD be included in the API response schema. Not yet implemented: the field is computed (`governance.py:134`) but `GovernanceEvaluateResponse` lacks it (`schemas.py:134-139`).

### Mode Enforcement

- **FR-014** [MUST] RAW mode access MUST require all three conditions: global `raw_mode_enabled=True`, API key `raw_mode_enabled=True`, and role >= `researcher`. Implemented: `auth.py:66-73`.
- **FR-015** [MUST] PUBLIC mode access MUST require role >= `operator`. Implemented: `auth.py:74-75`.
- **FR-016** [MUST] The governance evaluate route MUST enforce mode access via `_enforce_mode()` before evaluation. Implemented: `routes.py:343`.
- **FR-017** [MUST] Unauthorized mode access MUST return HTTP 403 with a descriptive message. Implemented: `routes.py:81-84`.

### Policy Management

- **FR-018** [MUST] The system MUST seed default PUBLIC and RAW policies at application startup. Implemented: `main.py:47`, `governance.py:15-43`.
- **FR-019** [MUST] Default blocked terms MUST be configurable via `NEXUS_PUBLIC_BLOCKED_TERMS` environment variable. Implemented: `config.py:33-42`.
- **FR-020** [MUST] Default blocked terms MUST include: `"kill"`, `"self-harm"`, `"hate"`, `"ethnic cleansing"`, `"bioweapon"`, `"how to make a bomb"`. Implemented: `config.py:35-41`.
- **FR-021** [MUST] `ensure_default_policies()` MUST NOT overwrite existing policies on restart. Implemented: `governance.py:32-35` (skips if record exists).
- **FR-022** [MUST] Policies MUST carry a `policy_version` integer starting at 1. Implemented: `governance.py:40`, `models.py:150`.
- **FR-023** [MUST] Policies MUST carry `effective_from` and `effective_to` datetime fields for date-range-based validity. Implemented: `models.py:151-152`.
- **FR-024** [SHOULD] The system SHOULD provide CRUD API endpoints for policy management. Not yet implemented.
- **FR-025** [SHOULD] The system SHOULD support policy versioning with increment-on-update semantics. Not yet implemented (version is always 1).
- **FR-026** [MAY] The system MAY support policy rollback to a previous version. Not yet implemented.

### Audit Trail

- **FR-027** [MUST] Every governance evaluation MUST create an `AuditLog` record with `action="governance.evaluate"`, mode, actor, and details JSON. Implemented: `governance.py:103-114`.
- **FR-028** [MUST] The audit log `details` MUST include `input_preview` (first 240 characters of candidate text), `policy_hits`, `policy_version`, `allow`, and `decision_trace`. Implemented: `governance.py:107-113`.
- **FR-029** [MUST] The audit log `actor` MUST be set to `"system"` for automated evaluations. Implemented: `governance.py:106`.
- **FR-030** [MUST] Every governance evaluation MUST create a `PolicyDecision` record with mode, input_hash (SHA256), allow, policy_hits, redactions, decision_trace, and audit_id FK. Implemented: `governance.py:118-126`.
- **FR-031** [MUST] `GET /api/v1/audit/policy-decisions` MUST return recent decisions ordered by `created_at` descending with configurable limit (default 100, max 1000). Implemented: `routes.py:629-635`, `governance.py:138-152`.
- **FR-032** [MUST] The audit/policy-decisions endpoint MUST require `operator` role minimum. Implemented: `routes.py:629`.
- **FR-033** [SHOULD] Audit log entries SHOULD include the requesting user's identity (API key owner) rather than hardcoded `"system"`. Not yet implemented.
- **FR-034** [SHOULD] The system SHOULD provide a `GET /api/v1/audit/logs` endpoint for browsing all audit log entries, not just policy decisions. Not yet implemented.
- **FR-035** [MAY] The system MAY provide audit log export in structured formats (JSON lines, CSV). Not yet implemented.

### Cross-Domain Governance

- **FR-036** [SHOULD] Evolution, remix, and analysis outputs SHOULD be automatically evaluated against governance policies before being returned to the caller. Not yet implemented.
- **FR-037** [SHOULD] The system SHOULD support configurable governance hooks at specific pipeline stages (pre-output, post-ingestion, etc.). Not yet implemented.
- **FR-038** [MAY] The system MAY support artifact state tracking (Proposed / In-Progress / Saved / Accepted / Rejected) as a cross-cutting governance concern. Not yet implemented (AB-PLAN-04 vision).
- **FR-039** [MAY] The system MAY generate save receipts for all persist operations. Not yet implemented (AB-PLAN-04 vision).

## Key Entities

### ModePolicy (`models.py:144-154`)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer PK (auto) | Sequential ID |
| `mode` | String(16) UNIQUE | `"PUBLIC"` or `"RAW"` |
| `policy` | JSON | Contains `blocked_terms` (list), `redaction_style` (string), `hard_block_threshold` (int) |
| `policy_version` | Integer | Version counter, starts at 1 |
| `effective_from` | DateTime(tz) nullable | Policy becomes active at this time; null = always active |
| `effective_to` | DateTime(tz) nullable | Policy expires at this time; null = never expires |
| `created_at` | DateTime(tz) | Row creation timestamp |
| `updated_at` | DateTime(tz) | Last modification timestamp |

### PolicyDecision (`models.py:157-168`)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `mode` | String(16) indexed | Mode used for evaluation |
| `input_hash` | String(128) indexed | SHA256 of the candidate text |
| `allow` | Boolean | Whether content was allowed |
| `policy_hits` | JSON | List of matched blocked terms |
| `redactions` | JSON | List of terms that were redacted |
| `decision_trace` | JSON | Full trace with hits detail, mode_rationale, policy_version, etc. |
| `audit_id` | String(36) indexed | FK to audit_logs (not a formal FK constraint in the model) |
| `created_at` | DateTime(tz) | Decision timestamp |

### AuditLog (`models.py:193-201`)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `action` | String(128) indexed | Action identifier (e.g., `"governance.evaluate"`) |
| `mode` | String(16) indexed | Governance mode |
| `actor` | String(128) | Who performed the action (currently `"system"`) |
| `details` | JSON | Action-specific details (input_preview, policy_hits, etc.) |
| `created_at` | DateTime(tz) | Audit timestamp |

### ApiKey (`models.py:180-190`) -- governance-relevant fields

| Field | Type | Purpose |
|-------|------|---------|
| `raw_mode_enabled` | Boolean | Per-key RAW mode permission flag |
| `role` | String(32) | Role for RBAC (viewer/operator/researcher/admin) |

## Edge Cases

### Covered by tests

- RAW mode denied to operator role (`test_mvp.py:54-59` -- gets HTTP 403)
- RAW mode allowed for researcher role (`test_mvp.py:61-66` -- gets HTTP 200)
- PUBLIC mode blocks on first hit of "kill" (`test_mvp.py:202`)
- RAW mode allows despite hit on "kill" (`test_mvp.py:203`)
- Decision trace contains hits detail with matched positions (`test_wave2.py:144-145`)
- Policy decisions are queryable via audit endpoint (`test_wave2.py:147-151`)
- Whoami reflects allowed modes per role (`test_mvp.py:68-73`)
- Clean text in PUBLIC mode returns `allow=True` (`test_mvp.py:292-297`)

### Not covered / known gaps

- **Multi-term matching**: No test verifies that multiple different blocked terms in the same text produce multiple entries in `policy_hits` and `decision_trace.hits`. The code handles this (`governance.py:67-84` iterates all blocked terms), but no test exercises it.
- **Overlapping match positions**: If two blocked terms overlap in the text (e.g., "self-harm" and "harm"), both would be matched independently. The redaction order matters -- first term's `re.sub` may alter positions for subsequent matches. No test covers this.
- **Case sensitivity in matching**: The `re.IGNORECASE` flag is used (`governance.py:70`), but no test verifies that uppercase or mixed-case blocked terms are caught (e.g., "KILL", "Kill").
- **Multi-word blocked terms**: The default list includes `"ethnic cleansing"` and `"how to make a bomb"`. Regex word boundaries on multi-word phrases require the phrase to appear as written. No test verifies multi-word phrase matching.
- **Empty candidate text**: Evaluating an empty string should produce zero hits and `allow=True`. No dedicated test.
- **Very long candidate text**: No test for texts longer than 240 characters to verify the `input_preview` truncation in the audit log.
- **Unicode in blocked terms**: No test for blocked terms or candidate text containing Unicode characters (e.g., accented Latin, CJK, emoji).
- **Missing policy**: If no policy exists for the mode (e.g., a third mode is requested), a `ValueError` is raised. No test directly verifies this path.
- **Expired policy**: If `effective_to` is set to a past date, the policy should not be loaded. No test covers policy expiration.
- **Audit log actor identity**: The actor is always `"system"` regardless of who made the request. The auth context's `owner` field is not propagated to the audit log.
- **Concurrent evaluations**: No test verifies behavior under concurrent governance evaluations (potential race on audit log ID generation, though UUID should be safe).
- **`redacted_text` not in API response**: The computed `redacted_text` is returned by the service but silently dropped at the API boundary because it is missing from `GovernanceEvaluateResponse`.
- **Input hash collision**: SHA256 collisions are astronomically unlikely but the system has no defense if two different texts produce the same hash.

## Success Criteria

1. **Dual-mode correctness**: PUBLIC mode blocks on any hit (`allow=False`, threshold=1). RAW mode allows with flagging (`allow=True`, threshold=999). Same text, same terms, different outcomes based on mode.
2. **Mode enforcement**: RAW mode is inaccessible to operators and below. PUBLIC mode is inaccessible to viewers. The enforcement is checked before evaluation, not after.
3. **Audit completeness**: Every governance evaluation produces both an `AuditLog` and a `PolicyDecision` record. The audit trail is permanent and queryable.
4. **Decision trace fidelity**: Every matched term is recorded with exact character positions, matched text, rule name, and mode. The trace includes policy version and human-readable rationale.
5. **Redaction correctness**: Blocked terms are replaced with the mode-appropriate style (`[REDACTED]`/`[FLAGGED]`) using word-boundary-aware regex. Non-matching substrings (e.g., "skill" for term "kill") are not redacted.
6. **Bootstrap reliability**: Default policies are seeded on every app start without overwriting existing policies. All 6 default blocked terms are present.
7. **Input integrity**: Candidate text is SHA256 hashed and stored in the decision record. The first 240 characters are preserved in the audit log for human review.
8. **API contract compliance**: All governance endpoints return the documented response schema. Auth requirements are enforced. Error responses include descriptive messages.
9. **Performance baseline**: Governance evaluation of a 10KB text against 6 blocked terms completes in <50ms. Audit query of 100 decisions completes in <100ms.
