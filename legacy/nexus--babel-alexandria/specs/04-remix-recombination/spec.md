# Remix & Recombination -- Specification

## Overview

The Remix & Recombination domain enables cross-document creative recombination within the ARC4N Living Digital Canon. It takes atoms (text content at any level) from two sources -- documents or branches -- and fuses them through one of four deterministic strategies (interleave, thematic_blend, temporal_layer, glyph_collide). Each remix produces a new branch with a replay-deterministic event, enabling lineage tracking, reproducibility, and further evolution on the remixed output.

This domain bridges the ingestion/atomization pipeline (domain 01) and the evolution/branching system (domain 03). Source material flows in from ingested documents or previously evolved branches; remix output flows out as a new branch event that can be further evolved, compared, or replayed. Governance (domain 05) enforces mode-level access control at the route layer to determine whether PUBLIC or RAW mode remix is permitted.

Currently, remixes are stored only as branch events -- there is no dedicated remix artifact table, no remix retrieval endpoints, no governance trace per remix, and no atom-level remix capability. The existing implementation operates on full extracted text rather than individual atoms from the 5-level hierarchy. Planned enhancements (AB01-T005 through AB01-T007) will add first-class remix persistence, atom-pool selection, governance trace snapshots, and user break-off timeline hooks.

## User Stories

### P1 -- As-Built (Verified)

#### US-001: Cross-document remix via interleave strategy

> As an **operator**, I want to interleave words from two documents so that I get a word-by-word alternating fusion of both texts.

**Given** two ingested documents with extracted text and an operator API key
**When** I `POST /api/v1/remix` with `source_document_id`, `target_document_id`, `strategy="interleave"`, and `seed=42`
**Then**:
- `RemixService.remix()` resolves source and target text from `document.provenance.extracted_text` (`remix.py:71-80`)
- `_interleave()` splits both texts on `\S+` regex, alternates words: source[0], target[0], source[1], target[1], ... (`remix.py:97-107`)
- If one text has more words than the other, remaining words are appended in order (`remix.py:102-106`)
- Result is joined with single spaces (`remix.py:107`)
- `EvolutionService.evolve_branch()` is called with `event_type="remix"` and `event_payload` containing `seed`, `strategy`, `remixed_text`, and source/target IDs (`remix.py:54-68`)
- A new `Branch` and `BranchEvent` are created; the response includes `new_branch_id`, `event_id`, `strategy`, `diff_summary` (`routes.py:683-716`)

**Code evidence:** `test_arc4n.py:263-273` (`TestRemixStrategies.test_interleave`), `test_arc4n.py:365-400` (`TestRemixAPI.test_remix_with_two_documents`).

#### US-002: Thematic blend remix with seeded RNG

> As an **operator**, I want to blend sentences from two documents in a shuffled order so that I get a thematic fusion that is deterministically reproducible.

**Given** two texts with sentence boundaries (`.`, `!`, `?`)
**When** I `POST /api/v1/remix` with `strategy="thematic_blend"` and a `seed`
**Then**:
- `_thematic_blend()` splits both texts on `[.!?]+` regex into sentence lists, strips whitespace (`remix.py:109-114`)
- Sentences from both texts are combined into a single list (`remix.py:112`)
- The seeded RNG shuffles the combined list (`remix.py:113`)
- Output is truncated to `max(len(source_sentences), len(target_sentences))` sentences (`remix.py:114`)
- Sentences are joined with `". "` and a trailing period (`remix.py:114`)
- Same `seed` + same inputs always produce the same output (deterministic RNG derived from `sha256("remix:thematic_blend:{seed}:{source_hash}:{target_hash}")`) (`remix.py:45-46`)

**Code evidence:** `test_arc4n.py:275-282` (`TestRemixStrategies.test_thematic_blend_deterministic`).

#### US-003: Temporal layer remix with paragraph interleaving

> As an **operator**, I want to overlay one text's paragraphs onto another's with temporal markers so that I get a time-layered composition.

**Given** two texts with paragraph breaks (`\n\s*\n`)
**When** I `POST /api/v1/remix` with `strategy="temporal_layer"` and a `seed`
**Then**:
- `_temporal_layer()` splits both texts on `\n\s*\n` regex into paragraph lists (`remix.py:116-118`)
- Iterates up to `max(len(source_paras), len(target_paras), 1)` (`remix.py:120`)
- Source paragraphs are always included (`remix.py:122-123`)
- Target paragraphs are included with 70% probability (RNG threshold `0.3`, so `rng.random() > 0.3` = ~70%) and prefixed with `"[temporal overlay] "` (`remix.py:124-125`)
- Paragraphs are joined with `"\n\n"` (`remix.py:126`)

**Code evidence:** `test_arc4n.py:292-297` (`TestRemixStrategies.test_temporal_layer`).

#### US-004: Glyph collision remix at character level

> As an **operator**, I want to collide two texts at the character level so that I get a glyph-by-glyph fusion with random selection at collision points.

**Given** two texts
**When** I `POST /api/v1/remix` with `strategy="glyph_collide"` and a `seed`
**Then**:
- `_glyph_collide()` extracts non-whitespace characters from both texts (`remix.py:129-130`)
- Iterates up to `min(max(len(source_glyphs), len(target_glyphs)), 2000)` characters (hard cap at 2000) (`remix.py:133`)
- Where both texts have a character at the same position:
  - If characters are identical, that character is used (`remix.py:136-137`)
  - If different, one is chosen randomly (50/50) via seeded RNG (`remix.py:138-139`)
- Where only one text has a character, that character is used (`remix.py:140-141`)
- Result is a continuous string with no whitespace (`remix.py:142`)

**Code evidence:** `test_arc4n.py:284-290` (`TestRemixStrategies.test_glyph_collide_produces_output`).

#### US-005: Source resolution from documents or branches

> As an **operator**, I want to remix from either a document or a branch so that I can use any corpus material or evolved state as a remix source.

**Given** a `source_document_id` or `source_branch_id` (and similarly for target)
**When** `RemixService._resolve_text()` is called (`remix.py:71-80`)
**Then**:
- If `branch_id` is provided, text is resolved from `branch.state_snapshot.current_text` (`remix.py:73-75`)
- If `document_id` is provided, text is resolved from `document.provenance.extracted_text` (`remix.py:76-79`)
- Branch takes priority over document when both are provided (`remix.py:72-79`)
- If neither resolves to non-empty text, `ValueError` is raised (`remix.py:42-43`)

**Code evidence:** `test_arc4n.py:365-400` uses `source_document_id` and `target_document_id`.

#### US-006: Deterministic seeded RNG for reproducibility

> As a **researcher**, I want the same remix inputs and seed to always produce the same output so that remix experiments are reproducible.

**Given** identical `source_document_id`, `target_document_id`, `strategy`, and `seed`
**When** `remix()` is called twice
**Then**:
- The RNG seed is derived from `sha256("remix:{strategy}:{seed}:{source_hash}:{target_hash}")` mod 2^32 (`remix.py:45-46`)
- Since `source_hash` and `target_hash` are SHA256 digests of the source and target text, and the `seed` integer is included, identical inputs always produce the same RNG state
- All strategy methods that use RNG (`_thematic_blend`, `_temporal_layer`, `_glyph_collide`) receive the same seeded `random.Random` instance (`remix.py:48`)
- `_interleave` is fully deterministic without RNG (word order is fixed) (`remix.py:97-107`)

**Code evidence:** `test_arc4n.py:275-282` verifies determinism for `thematic_blend`.

#### US-007: Branch event creation via evolution service integration

> As the **system**, I want every remix to produce a new branch with a "remix" event so that remix history is tracked in the branch timeline.

**Given** a successful remix
**When** `RemixService.remix()` completes
**Then**:
- `EvolutionService.evolve_branch()` is called with `event_type="remix"` (`remix.py:54`)
- The `event_payload` includes: `seed`, `strategy`, `remixed_text`, `source_document_id`, `target_document_id`, `source_branch_id`, `target_branch_id` (`remix.py:59-68`)
- If a `source_branch_id` is provided, the new branch inherits the source branch as `parent_branch_id` (`remix.py:54-57`)
- If only `source_document_id` is provided, it becomes the `root_document_id` for the new branch (`remix.py:50-52`)
- The evolution service derives the branch root document from the source branch if needed via `_branch_root_doc()` (`remix.py:82-84`)
- The `BranchEvent` stores a `diff_summary` with `event`, `strategy`, `before_chars`, `after_chars` (`evolution.py:377-381`)

**Code evidence:** `test_arc4n.py:243-251` verifies remix event validation and application in the evolution service. `test_arc4n.py:397-400` verifies `new_branch_id` in the API response.

#### US-008: Mode enforcement on remix endpoint

> As the **system**, I want remix requests to respect PUBLIC/RAW mode access control so that operators cannot remix in RAW mode without authorization.

**Given** a remix request with a `mode` field (default `"PUBLIC"`)
**When** `POST /api/v1/remix` is called
**Then**:
- `_enforce_mode()` checks whether the authenticated user's role and API key settings allow the requested mode (`routes.py:691`)
- If mode is `"RAW"` and the user lacks RAW access, HTTP 403 is returned (`routes.py:74-84`)
- The mode is passed through to `EvolutionService.evolve_branch()` and recorded on the new branch (`remix.py:69`)

**Code evidence:** `test_arc4n.py:361-363` verifies auth is required.

### P2 -- Partially Built

#### US-009: Remix persistence as first-class artifacts

> As a **researcher**, I want remixes to be persisted as dedicated artifacts with source lineage so that I can retrieve, compare, and audit remixes independently from the branch timeline.

**Current state**: Remixes are stored only as `BranchEvent` rows with `event_type="remix"` and the full remix payload in `event_payload` JSON. There is no `RemixArtifact` table, no source-link join table, and no dedicated retrieval endpoints.

**Gap**: No `remix_artifacts` table. No `remix_source_links` join table. No `GET /api/v1/remix/{id}` or `GET /api/v1/remix` endpoints. No governance decision trace snapshot attached to remix artifacts.

**Vision ref:** AB01-T006 -- Remix Persistence + Retrieval.

#### US-010: Remix retrieval endpoints

> As a **viewer**, I want to list and retrieve remixes so that I can browse the remix library and inspect individual remix artifacts.

**Current state**: The only way to discover remixes is by filtering branch events for `event_type="remix"` in the branch timeline. There is no dedicated listing or detail endpoint.

**Gap**: No `GET /api/v1/remix` (list) endpoint. No `GET /api/v1/remix/{id}` (detail) endpoint. No pagination or filtering.

**Vision ref:** AB01-T006 -- Remix Persistence + Retrieval.

#### US-011: Governance trace per remix

> As an **operator**, I want each remix to carry a governance decision trace snapshot so that the mode, policy version, and any flagged terms are recorded alongside the remix artifact.

**Current state**: Mode enforcement happens at the route level (`_enforce_mode()`), but no `GovernanceService.evaluate()` is called on the remixed text. The mode is stored on the branch but no `PolicyDecision` row is linked to the remix.

**Gap**: No `governance_decision_id` on remix artifacts. No automatic governance evaluation of remixed output text. No audit trail linking remix to policy decisions.

**Vision ref:** AB01-T006 -- Remix Persistence + Retrieval.

### P3+ -- Vision

#### US-012: Atom-level remix from 5-level hierarchy

> As a **researcher**, I want to remix at the atom level (selecting specific words, sentences, or glyph-seeds from source atom pools) so that recombination operates on the rich atomic structure rather than raw text.

**Current state**: All four strategies operate on full extracted text strings. They split text using regex (`\S+`, `[.!?]+`, `\n\s*\n`, or character-level) rather than querying `Atom` rows from the database. The 5-level atomization hierarchy is not used for remix input.

**Vision ref:** AB01-T005 -- Remix Composer API + Service.

#### US-013: User break-off timeline hook

> As an **operator**, I want to optionally create a branch when composing a remix so that I can explore remix evolution independently from the main timeline.

**Current state**: Every remix always creates a new branch (via `EvolutionService.evolve_branch()`). There is no `create_branch=false` option to create a remix artifact without branching, nor a `create_branch=true` explicit opt-in that would link a `remix_artifact_id` in the branch event payload.

**Gap**: No `create_branch` option in `RemixRequest`. No conditional branching logic. No `remix_artifact_id` linking in branch event payload. The current behavior always creates a branch -- the vision is to make branching optional and explicitly linked.

**Vision ref:** AB01-T007 -- User Break-Off Timeline Hook.

#### US-014: Remix lineage graph

> As a **researcher**, I want to visualize the lineage graph of remixes -- which documents and branches contributed to which remix artifacts -- so that I can trace creative provenance across the canon.

**Current state**: Remix source/target information is stored in the `BranchEvent.event_payload` JSON but not in a queryable relational structure. No graph projection of remix relationships exists.

**Gap**: No `remix_source_links` table. No hypergraph projection of remix relationships. No lineage query endpoint.

#### US-015: Remix via async job queue

> As an **operator**, I want to submit large remixes (e.g., full-text glyph collision of two novels) as async jobs so that the API does not block on expensive operations.

**Current state**: `POST /api/v1/remix` is fully synchronous. The async job system (`JobService`) exists but is not wired to the remix endpoint.

**Gap**: No `execution_mode` option in `RemixRequest`. No integration with `JobService`.

#### US-016: Multi-source remix (N-way)

> As a **researcher**, I want to remix more than two sources simultaneously so that I can create N-way fusions of corpus material.

**Current state**: `RemixRequest` accepts exactly one source and one target (document or branch each). All four strategies are binary (two inputs).

**Gap**: No multi-source support. Would require new strategies or generalization of existing ones.

## Functional Requirements

### Remix Strategies

- **FR-001** [MUST] The system MUST support four remix strategies: `interleave`, `thematic_blend`, `temporal_layer`, `glyph_collide`. Implemented: `remix.py:86-95`, `schemas.py:11`.
- **FR-002** [MUST] `interleave` MUST alternate words from source and target using `\S+` splitting. When one text is exhausted, remaining words from the other MUST be appended. Implemented: `remix.py:97-107`.
- **FR-003** [MUST] `thematic_blend` MUST split both texts on sentence boundaries (`[.!?]+`), combine into one list, shuffle with seeded RNG, and truncate to `max(len(source_sentences), len(target_sentences))`. Implemented: `remix.py:109-114`.
- **FR-004** [MUST] `temporal_layer` MUST split both texts on paragraph boundaries (`\n\s*\n`), include all source paragraphs, and include target paragraphs with ~70% probability (threshold `0.3`) prefixed with `"[temporal overlay] "`. Implemented: `remix.py:116-126`.
- **FR-005** [MUST] `glyph_collide` MUST extract non-whitespace characters from both texts, iterate up to `min(max_length, 2000)`, choose randomly at collision points (50/50), and produce a whitespace-free string. Implemented: `remix.py:128-142`.
- **FR-006** [MUST] An unknown strategy MUST raise `ValueError`. Implemented: `remix.py:95`.

### Determinism

- **FR-007** [MUST] The RNG seed MUST be derived from `sha256("remix:{strategy}:{seed}:{source_hash}:{target_hash}")` mod 2^32, where `source_hash` and `target_hash` are SHA256 hex digests of the resolved source and target text. Implemented: `remix.py:45-46`.
- **FR-008** [MUST] Identical inputs (same source text, target text, strategy, seed) MUST produce identical remix output. Implemented: verified by `test_arc4n.py:275-282`.

### Source Resolution

- **FR-009** [MUST] Source and target MUST be resolvable from either a `document_id` (via `document.provenance.extracted_text`) or a `branch_id` (via `branch.state_snapshot.current_text`). Implemented: `remix.py:71-80`.
- **FR-010** [MUST] When both `document_id` and `branch_id` are provided for the same side, branch MUST take priority. Implemented: `remix.py:72-79` (branch checked first).
- **FR-011** [MUST] If both source and target resolve to empty text, the system MUST raise `ValueError("Both source and target must resolve to non-empty text")`. Implemented: `remix.py:42-43`.

### API Contract

- **FR-012** [MUST] `POST /api/v1/remix` MUST accept `RemixRequest` with fields: `source_document_id` (optional str), `source_branch_id` (optional str), `target_document_id` (optional str), `target_branch_id` (optional str), `strategy` (literal enum, default `"interleave"`), `seed` (int, default 0), `mode` (literal `"PUBLIC"` | `"RAW"`, default `"PUBLIC"`). Implemented: `schemas.py:227-234`.
- **FR-013** [MUST] The response MUST include `new_branch_id`, `event_id`, `strategy`, and `diff_summary`. Implemented: `schemas.py:237-241`, `routes.py:703-708`.
- **FR-014** [MUST] The endpoint MUST require `operator` role or higher. Implemented: `routes.py:687`.
- **FR-015** [MUST] The endpoint MUST enforce mode access via `_enforce_mode()`. Implemented: `routes.py:691`.
- **FR-016** [MUST] Auth failure MUST return HTTP 401; insufficient role MUST return HTTP 403. Implemented: `routes.py:48-71`.

### Branch Integration

- **FR-017** [MUST] Every remix MUST produce a new `Branch` with `event_type="remix"` via `EvolutionService.evolve_branch()`. Implemented: `remix.py:54-69`.
- **FR-018** [MUST] The `BranchEvent.event_payload` MUST include `seed`, `strategy`, `remixed_text`, `source_document_id`, `target_document_id`, `source_branch_id`, `target_branch_id`. Implemented: `remix.py:59-68`.
- **FR-019** [MUST] When `source_branch_id` is provided, the new branch MUST use it as `parent_branch_id`. Implemented: `remix.py:54-57`.
- **FR-020** [MUST] The evolution service MUST validate the remix event payload (setting defaults for `seed` and `strategy`). Implemented: `evolution.py:286-289`.
- **FR-021** [MUST] The evolution service MUST return the pre-computed `remixed_text` from the payload rather than recomputing it. Implemented: `evolution.py:377-381`.

### Remix Persistence (P2)

- **FR-022** [SHOULD] The system SHOULD persist remixes as dedicated `RemixArtifact` rows with source-link join records. Not yet implemented (AB01-T006).
- **FR-023** [SHOULD] The system SHOULD provide `GET /api/v1/remix/{id}` returning full remix artifact with source lineage. Not yet implemented (AB01-T006).
- **FR-024** [SHOULD] The system SHOULD provide `GET /api/v1/remix` listing remix artifacts with pagination. Not yet implemented (AB01-T006).
- **FR-025** [SHOULD] Each remix artifact SHOULD include a `governance_decision_id` linking to a `PolicyDecision` row for the remixed text. Not yet implemented (AB01-T006).

### Break-Off Timeline (P2)

- **FR-026** [SHOULD] `RemixRequest` SHOULD accept a `create_branch` boolean (default `true` for backward compatibility). Not yet implemented (AB01-T007).
- **FR-027** [SHOULD] When `create_branch=true`, the branch event payload SHOULD include `remix_artifact_id` linking back to the persisted artifact. Not yet implemented (AB01-T007).
- **FR-028** [SHOULD] When `create_branch=false`, the remix artifact SHOULD be created without a corresponding branch. Not yet implemented (AB01-T007).

### Atom-Level Remix (P3)

- **FR-029** [MAY] The system MAY accept `atom_levels` in `RemixRequest` to select atoms from the 5-level hierarchy for remix input. Not yet implemented (AB01-T005).
- **FR-030** [MAY] The remix response MAY include `source_atom_refs` linking to specific `Atom` row IDs used in the remix. Not yet implemented (AB01-T005).
- **FR-031** [MAY] The system MAY support N-way remix with more than two sources. Not yet implemented.

### Async Remix (P3)

- **FR-032** [MAY] `RemixRequest` MAY accept `execution_mode` (`"sync"` | `"async"`) to submit remix as an async job. Not yet implemented.
- **FR-033** [MAY] The async response MAY include a `job_id` for polling progress via `GET /api/v1/jobs/{id}`. Not yet implemented.

## Key Entities

### Branch (`models.py:110-124`) -- Existing

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `parent_branch_id` | FK -> branches | Parent branch (source branch for remix) |
| `root_document_id` | FK -> documents | Source document for the branch lineage |
| `name` | String(256) | Auto-generated: `"branch-remix"` for remix events |
| `mode` | String(16) | `PUBLIC` or `RAW` |
| `state_snapshot` | JSON | `{current_text, phase, text_hash}` after remix |
| `branch_version` | Integer | Incremented from parent |
| `created_at` | DateTime(tz) | Timestamp |

### BranchEvent (`models.py:127-141`) -- Existing

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `branch_id` | FK -> branches | Parent branch |
| `event_index` | Integer | Sequential event number |
| `event_type` | String(64) | `"remix"` for remix events |
| `event_payload` | JSON | `{seed, strategy, remixed_text, source_document_id, target_document_id, source_branch_id, target_branch_id}` |
| `payload_schema_version` | String(16) | `"v2"` |
| `event_hash` | String(128) | SHA256 of branch_id:index:type:payload:text_hash |
| `diff_summary` | JSON | `{event, strategy, before_chars, after_chars}` |
| `result_snapshot` | JSON | `{text_hash, preview}` |

### RemixRequest (`schemas.py:227-234`) -- Existing

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `source_document_id` | str or None | None | Source document UUID |
| `source_branch_id` | str or None | None | Source branch UUID |
| `target_document_id` | str or None | None | Target document UUID |
| `target_branch_id` | str or None | None | Target branch UUID |
| `strategy` | RemixStrategy | `"interleave"` | One of 4 strategies |
| `seed` | int | 0 | RNG seed for determinism |
| `mode` | Mode | `"PUBLIC"` | Governance mode |

### RemixResponse (`schemas.py:237-241`) -- Existing

| Field | Type | Purpose |
|-------|------|---------|
| `new_branch_id` | str | UUID of the created branch |
| `event_id` | str | UUID of the created branch event |
| `strategy` | str | Strategy that was applied |
| `diff_summary` | dict | Before/after character counts and metadata |

### RemixArtifact -- Proposed (P2)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `strategy` | String(64) | Strategy used |
| `seed` | Integer | RNG seed |
| `remixed_text` | Text | Full remixed output |
| `text_hash` | String(128) | SHA256 of remixed text |
| `mode` | String(16) | `PUBLIC` or `RAW` |
| `branch_id` | FK -> branches (nullable) | Linked branch if `create_branch=true` |
| `branch_event_id` | FK -> branch_events (nullable) | Linked branch event |
| `governance_decision_id` | FK -> policy_decisions (nullable) | Governance trace |
| `created_by` | String(128) | API key owner |
| `created_at` | DateTime(tz) | Timestamp |

### RemixSourceLink -- Proposed (P2)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `remix_artifact_id` | FK -> remix_artifacts | Parent remix |
| `role` | String(16) | `"source"` or `"target"` |
| `document_id` | FK -> documents (nullable) | Source/target document |
| `branch_id` | FK -> branches (nullable) | Source/target branch |
| `resolved_text_hash` | String(128) | SHA256 of the text that was resolved from this source |
| `created_at` | DateTime(tz) | Timestamp |

## Edge Cases

### Covered by tests

- Auth required for remix endpoint (`test_arc4n.py:361-363`)
- Remix with two ingested documents produces valid branch and event (`test_arc4n.py:365-400`)
- Interleave produces alternating word pattern (`test_arc4n.py:263-273`)
- Thematic blend is deterministic with same seed (`test_arc4n.py:275-282`)
- Glyph collide produces output of expected length (`test_arc4n.py:284-290`)
- Temporal layer includes source paragraphs and "[temporal overlay]" marker (`test_arc4n.py:292-297`)
- Remix event payload validation in evolution service (`test_arc4n.py:243-246`)
- Remix event application returns pre-computed text (`test_arc4n.py:248-251`)

### Not covered / known gaps

- **Empty source or target text**: `_resolve_text()` returns `""` for missing documents/branches, which triggers `ValueError`. Not explicitly tested with valid IDs pointing to documents with empty `extracted_text`.
- **Both document and branch provided for same side**: Branch takes priority by code structure, but this is not tested. No validation rejects providing both.
- **Nonexistent document/branch IDs**: `_resolve_text()` silently returns `""` for nonexistent IDs rather than raising a 404-style error. Combined with the `ValueError` check, this produces a generic error message rather than a specific "document not found" error.
- **Very long texts**: `glyph_collide` has a 2000-char cap, but `interleave`, `thematic_blend`, and `temporal_layer` have no size limits. Two large novels could produce very large remix output stored in `BranchEvent.event_payload.remixed_text` as JSON.
- **Texts with no sentence boundaries**: `thematic_blend` on text without `.`, `!`, or `?` produces a single "sentence" -- the full text. Shuffle of one element is a no-op.
- **Texts with no paragraph breaks**: `temporal_layer` on text without `\n\s*\n` produces a single paragraph per text. Result is source text plus (with 70% probability) `"[temporal overlay] {target}"`.
- **Unicode-heavy texts**: `\S+` splitting in `interleave` handles Unicode correctly, but CJK text (no whitespace between words) would treat the entire text as a single "word".
- **Concurrent remixes on same branch**: No optimistic concurrency control specific to remix. The evolution service checks `expected_parent_event_index` but remix does not set it.
- **Self-remix**: Remixing a document against itself is allowed but not tested. `interleave` would produce each word doubled; `glyph_collide` would produce the original (all characters identical).
- **Remix from branch then further evolution**: A remixed branch can be further evolved (natural_drift, etc.), but this chain is not tested.
- **Mode mismatch**: A remix in PUBLIC mode using sources from RAW-mode branches is not checked. The mode enforcement only validates the requesting user's access.

## Success Criteria

1. **Strategy correctness**: All four remix strategies produce output matching their documented algorithm. `interleave` alternates words, `thematic_blend` shuffles sentences, `temporal_layer` overlays paragraphs with markers, `glyph_collide` fuses at character level with a 2000-char cap.
2. **Determinism**: Same inputs (source text, target text, strategy, seed) always produce identical output. Verified by running the same remix twice and comparing.
3. **Branch lineage**: Every remix produces a new `Branch` and `BranchEvent` with `event_type="remix"`. The event payload contains all source metadata for replay.
4. **Source flexibility**: Remixes work with document-to-document, branch-to-branch, document-to-branch, and branch-to-document combinations.
5. **Auth and governance**: Remix endpoint requires `operator` role. Mode enforcement blocks unauthorized RAW access.
6. **Replay correctness**: A remix branch can be replayed via the timeline/replay endpoints and produces the same text hash as the original remix output (evolution service returns `remixed_text` from payload).
7. **Artifact persistence** (P2): Remix artifacts are stored in dedicated tables with source links, governance traces, and retrieval endpoints.
8. **Break-off hook** (P2): `create_branch` option controls whether a branch is created, and remix artifact IDs are linked in branch event payloads when branching occurs.
9. **Atom-level remix** (P3): Remix operates on the 5-level atom hierarchy rather than raw text, with source atom references in the response.
