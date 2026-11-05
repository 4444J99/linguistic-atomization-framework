# 03 -- Evolution & Branching: Specification

> **Domain:** 03-evolution-branching
> **Status:** Draft
> **Last updated:** 2026-02-23
> **Source of truth:** `src/nexus_babel/services/evolution.py`, `src/nexus_babel/services/remix.py`, `src/nexus_babel/api/routes.py`

---

## 1. Overview

The Evolution & Branching domain is the temporal engine of the ARC4N Living Digital Canon. It models language as a living organism that evolves through deterministic, reproducible transformations: natural linguistic drift (25 historic phonetic shifts), synthetic mutation (glyph pool substitution), phase shifts (expansion/peak/compression/rebirth with acceleration), glyph fusion (character pair merging), and remix (cross-document recombination).

Every evolution event creates a new `Branch` linked to its parent, forming an immutable tree of textual lineage. Events are recorded as `BranchEvent` rows with deterministic hashes derived from seeded RNG, enabling full replay from any root document. The system supports optimistic concurrency control via `expected_parent_event_index`, auto-checkpointing every 10 lineage events (zlib+base64 compressed snapshots), and branch comparison via character-level distance.

The vision extends this foundation with automatic phase state transitions, multi-generation evolution chains producing recognizably distinct language variants, reverse drift (undoing natural shifts), branch merging, sung-language emergence from compression+rebirth cycles, and visual timeline rendering.

---

## 2. Architectural Context

### 2.1 Data Flow

```
POST /api/v1/evolve/branch
  |
  v
routes.py: validate auth (operator), enforce mode (PUBLIC/RAW)
  |
  v
EvolutionService.evolve_branch()
  |-- _validate_event_payload(event_type, event_payload)
  |     |-- natural_drift: default seed=0
  |     |-- synthetic_mutation: validate mutation_rate [0.0, 1.0], default 0.08
  |     |-- phase_shift: validate phase in {expansion, peak, compression, rebirth}
  |     |-- glyph_fusion: require non-empty left/right/fused
  |     |-- remix: default strategy="interleave", seed=0
  |
  |-- resolve base_text:
  |     if parent_branch_id -> Branch.state_snapshot.current_text
  |     if root_document_id -> Document.provenance.extracted_text
  |
  |-- optimistic concurrency check:
  |     if expected_parent_event_index != _lineage_event_count(parent)
  |     -> raise ValueError
  |
  |-- _apply_event(base_text, event_type, event_payload)
  |     |-- seed RNG: sha256(event_type:seed:text_hash) mod 2^32
  |     |-- apply transformation -> DriftResult(output_text, diff_summary)
  |
  |-- create Branch(parent_branch_id, root_document_id, name, mode, state_snapshot, branch_version)
  |-- create BranchEvent(branch_id, event_index, event_type, event_payload, event_hash, diff_summary, result_snapshot)
  |
  |-- auto-checkpoint: if total_lineage_events % 10 == 0
  |     -> BranchCheckpoint(branch_id, event_index, snapshot_hash, snapshot_compressed)
  |
  v
EvolveBranchResponse { new_branch_id, event_id, diff_summary }
```

### 2.2 Key Components

| Component | File | Responsibility |
|-----------|------|----------------|
| `EvolutionService` | `services/evolution.py` | Core evolution engine: event validation, application, branching, replay, compare |
| `RemixService` | `services/remix.py` | Cross-document recombination: interleave, thematic_blend, temporal_layer, glyph_collide |
| `DriftResult` | `services/evolution.py` | Dataclass: `output_text` + `diff_summary` dict |
| `Branch` | `models.py` | ORM: branch with parent link, root document, state snapshot, version |
| `BranchEvent` | `models.py` | ORM: immutable event record with deterministic hash |
| `BranchCheckpoint` | `models.py` | ORM: compressed snapshot at every 10th lineage event |
| `EvolveBranchRequest` / `EvolveBranchResponse` | `schemas.py` | Pydantic request/response contracts |
| `BranchTimelineResponse` | `schemas.py` | Timeline with full event list + replay snapshot |
| `BranchReplayResponse` | `schemas.py` | Replay result with text_hash, preview, event_count |
| `BranchCompareResponse` | `schemas.py` | Branch diff with char-level distance |

### 2.3 Governance Integration

- The `/api/v1/evolve/branch` route enforces mode access via `_enforce_mode()`. RAW mode requires both system-level `raw_mode_enabled` and per-key `raw_mode_enabled` flags.
- Branch mode is stored uppercase in `Branch.mode` (e.g., `"PUBLIC"`, `"RAW"`).
- No content governance filtering is applied to evolution output text. Governance is handled separately via `/api/v1/governance/evaluate`.

### 2.4 Remix Integration

The `RemixService` (`services/remix.py`) delegates branch creation to `EvolutionService.evolve_branch()` with `event_type="remix"`. The remix service resolves source and target texts, applies a recombination strategy (interleave, thematic_blend, temporal_layer, glyph_collide), and passes the pre-computed remixed text via `event_payload.remixed_text`. The evolution service stores it as a standard branch event.

---

## 3. User Stories

### P1 -- As-Built (Verified)

#### US-001: Create a branch from a root document via natural drift

> As an **operator**, I want to evolve a document through natural linguistic drift so that I can observe how text transforms under historic phonetic shift rules.

**Given** a `Document` with `extracted_text` and an operator API key
**When** I `POST /api/v1/evolve/branch` with `root_document_id`, `event_type: "natural_drift"`, `event_payload: {seed: N}`
**Then:**
- A new `Branch` is created with `parent_branch_id=null`, `root_document_id` set, `mode` uppercase, `branch_version=1`
- `Branch.state_snapshot` contains `{current_text, phase, text_hash}` where `current_text` is the drift-transformed text
- All 25 `NATURAL_MAP` substitutions are applied case-insensitively (`evolution.py:298-305`)
- A `BranchEvent` is created with `event_index=1`, `payload_schema_version="v2"`, deterministic `event_hash`
- `diff_summary` contains `{event, replacements, before_chars, after_chars}`
- `result_snapshot` contains `{text_hash, preview}` where preview is truncated to 500 chars

**Code refs:** `evolution.py:76-157`, `evolution.py:298-305`

#### US-002: Chain branches via parent branching

> As an **operator**, I want to create a new branch from an existing branch so that I can build a lineage of successive transformations.

**Given** an existing `Branch` with `state_snapshot.current_text`
**When** I `POST /api/v1/evolve/branch` with `parent_branch_id` and any supported `event_type`
**Then:**
- The new branch inherits `root_document_id` from the parent (`evolution.py:92`)
- `base_text` is resolved from `parent.state_snapshot.current_text` (`evolution.py:93`)
- `branch_version` is `parent.branch_version + 1` (`evolution.py:121`)
- The lineage event count is computed by walking all ancestors (`evolution.py:233-243`)

**Code refs:** `evolution.py:88-98`

#### US-003: Synthetic mutation with glyph pool substitution

> As an **operator**, I want to apply synthetic mutations to a text so that I can accelerate language evolution beyond natural drift.

**Given** a base text (from document or parent branch)
**When** I evolve with `event_type: "synthetic_mutation"`, `event_payload: {seed, mutation_rate}`
**Then:**
- Words are tokenized via `re.findall(r"\w+|\W+", text)` (`evolution.py:308`)
- Each alphabetic token has a `rng.random() < mutation_rate` chance of being replaced by a random `GLYPH_POOL` glyph (`evolution.py:310-312`)
- `GLYPH_POOL` contains 10 glyphs: `["DELTA", "AE", "OMEGA", "SECTION", "TRIGRAM", "TRIANGLE", "PSI", "PHI", "THETA", "XI"]`
- `diff_summary` contains `{event, mutations, before_chars, after_chars}`
- `mutation_rate` MUST be in `[0.0, 1.0]` or `ValueError` is raised (`evolution.py:260-261`)

**Code refs:** `evolution.py:307-315`, `evolution.py:258-264`

#### US-004: Phase shift with acceleration multiplier

> As an **operator**, I want to shift text through temporal evolution phases so that I can model the cyclical expansion/peak/compression/rebirth of language.

**Given** a base text
**When** I evolve with `event_type: "phase_shift"`, `event_payload: {phase, seed, acceleration}`
**Then:**
- `phase` MUST be one of `{expansion, peak, compression, rebirth}` (`evolution.py:268-269`)
- Acceleration multiplier modifies intensity:
  - expansion/peak: `intensity = min(acceleration * (1.0 + phase_idx * 0.5), 5.0)` (`evolution.py:324`)
  - compression/rebirth: `intensity = max(acceleration * (1.0 - (phase_idx - 2) * 0.3), 0.2)` (`evolution.py:326`)
- Phase behaviors:
  - **expansion**: Insert "mythic" after every Nth word where `N = max(1, int(7 / intensity))` (`evolution.py:358-365`)
  - **peak**: Uppercase text; if intensity > 1.5, insert "MYTHIC" at interval (`evolution.py:345-356`)
  - **compression**: Remove vowels with probability `min(intensity * 0.6, 1.0)` per vowel (`evolution.py:328-336`)
  - **rebirth**: Remove vowels with probability `min(intensity * 0.4, 1.0)`, append `"\n\n^Triangle SONG-BIRTH ^Triangle"` (`evolution.py:337-344`)
- `diff_summary` contains `{event, phase, acceleration, intensity, before_chars, after_chars}`

**Code refs:** `evolution.py:317-366`

#### US-005: Glyph fusion

> As an **operator**, I want to fuse character pairs into new glyphs so that I can model the compression and fusion of written language.

**Given** a base text
**When** I evolve with `event_type: "glyph_fusion"`, `event_payload: {left, right, fused}`
**Then:**
- All occurrences of the pair `left+right` in the text are replaced with `fused` (`evolution.py:372-374`)
- `left`, `right`, and `fused` MUST be non-empty strings (`evolution.py:278-279`)
- `diff_summary` contains `{event, fusions, pair, fused, before_chars, after_chars}`
- Replacement is case-sensitive (unlike natural_drift)

**Code refs:** `evolution.py:368-375`

#### US-006: Deterministic replay via seeded RNG

> As a **researcher**, I want evolution events to be deterministically reproducible so that I can replay and verify branch transformations.

**Given** a branch with events
**When** I replay the branch
**Then:**
- The seeded RNG is derived from `sha256(event_type:seed:text_hash)` mod `2^32` (`evolution.py:294-295`)
- Identical inputs (same text, same event_type, same seed) MUST produce identical outputs
- `get_timeline()` walks the full lineage and replays all events from root document text (`evolution.py:159-191`)
- `replay_branch()` delegates to `get_timeline()` and returns `{branch_id, event_count, text_hash, preview, replay_snapshot}` (`evolution.py:193-202`)

**Code refs:** `evolution.py:159-202`, `evolution.py:293-295`

#### US-007: Optimistic concurrency control

> As an **operator**, I want to detect concurrent branch modifications so that I don't create events on a stale branch state.

**Given** a parent branch with known event count
**When** I evolve with `event_payload: {expected_parent_event_index: N}`
**Then:**
- If `N != _lineage_event_count(parent)`, raise `ValueError` with `"Optimistic concurrency violation"` (`evolution.py:96-99`)
- If `expected_parent_event_index` is not provided, no concurrency check is performed

**Code refs:** `evolution.py:95-99`

#### US-008: Auto-checkpointing

> As a **system operator**, I want the system to periodically snapshot branch state so that long lineage chains can be replayed efficiently.

**Given** a branch evolution event
**When** the total lineage event count (across all ancestors) is a multiple of 10
**Then:**
- A `BranchCheckpoint` is created with `branch_id`, `event_index=total_lineage_events`, `snapshot_hash` (sha256 of current text), and `snapshot_compressed` (zlib level 9 + base64 of JSON state_snapshot) (`evolution.py:147-155`)

**Code refs:** `evolution.py:146-155`, `evolution.py:385-388`

#### US-009: Branch comparison

> As a **researcher**, I want to compare two branches so that I can measure how far they have diverged.

**Given** two branch IDs
**When** I `GET /api/v1/branches/{left}/compare/{right}`
**Then:**
- Both branches are replayed to current state (`evolution.py:204-206`)
- A character-by-character distance is computed on the first 500 chars (preview) (`evolution.py:390-398`)
- Response includes `{left_branch_id, right_branch_id, left_hash, right_hash, distance, same, preview_left, preview_right}` (`evolution.py:210-219`)
- `same` is `True` iff `left_hash == right_hash`

**Code refs:** `evolution.py:204-219`, `evolution.py:390-398`, `routes.py:597-610`

#### US-010: Branch timeline retrieval

> As a **viewer**, I want to retrieve the full event timeline for a branch including all ancestor events so that I can understand the evolution history.

**Given** a branch ID
**When** I `GET /api/v1/branches/{id}/timeline`
**Then:**
- The full lineage is walked via `_lineage()` (child -> ancestors, reversed to root-first) (`evolution.py:221-231`)
- All `BranchEvent` records across the lineage are collected, ordered by `event_index` then `created_at` (`evolution.py:166-171`)
- All events are replayed from root document text to produce a `replay_snapshot` (`evolution.py:179-191`)
- Response includes `{branch_id, root_document_id, events[], replay_snapshot}` with each event as `BranchEventView`

**Code refs:** `evolution.py:159-191`, `routes.py:261-288`

#### US-011: List branches

> As a **viewer**, I want to list all branches so that I can browse the evolution tree.

**Given** a viewer API key
**When** I `GET /api/v1/branches?limit=N`
**Then:**
- Returns up to N branches ordered by `created_at DESC` (`routes.py:295`)
- Each entry includes `{id, parent_branch_id, root_document_id, mode, branch_version, created_at}`
- Default limit is 100, range [1, 1000] (`routes.py:292`)

**Code refs:** `routes.py:291-310`

#### US-012: Remix as evolution event

> As an **operator**, I want to remix atoms from two sources so that I can create new compositions through recombination.

**Given** a source document/branch and a target document/branch
**When** I `POST /api/v1/remix` with strategy and seed
**Then:**
- `RemixService.remix()` resolves both texts, applies strategy, delegates to `EvolutionService.evolve_branch()` with `event_type="remix"` (`remix.py:28-69`)
- Four strategies are supported: `interleave`, `thematic_blend`, `temporal_layer`, `glyph_collide` (`remix.py:86-95`)
- The remixed text is passed via `event_payload.remixed_text` and stored as-is by the evolution engine (`evolution.py:377-381`)
- Response includes `{new_branch_id, event_id, strategy, diff_summary}`

**Code refs:** `remix.py:24-69`, `evolution.py:377-381`, `routes.py:683-716`

### P2 -- Partially Built

#### US-013: Reverse drift engine

> As a **researcher**, I want to reverse natural linguistic drift so that I can reconstruct earlier language forms from evolved branches.

**Current state:** `REVERSE_NATURAL_MAP` exists with 12 entries mapping evolved forms back to originals (`evolution.py:58-71`). No `reverse_drift` event type is implemented in `_validate_event_payload()` or `_apply_event()`.

**Given** a branch that has undergone natural drift
**When** I evolve with `event_type: "reverse_drift"`
**Then:**
- The 12 `REVERSE_NATURAL_MAP` substitutions are applied case-insensitively
- `diff_summary` contains `{event: "reverse_drift", reversals, before_chars, after_chars}`
- Reverse drift is lossy: not all natural drift mappings have reversal entries (25 forward vs 12 reverse). Specifically, `gn`, `n`, `wh`, `w`, `ou`, `ea`, `eye`, `t`, `ow`, `r`, `m` are not reversed because they are common character sequences that would cause false positives.

**Code refs:** `evolution.py:58-71`

### P3+ -- Vision

#### US-014: Automatic phase state transitions

> As a **researcher**, I want the system to track which evolution phase a branch is in and automatically transition between phases based on defined thresholds.

**Vision:** A `PhaseStateManager` tracks per-branch phase state with automatic transitions:
- expansion -> peak: when word count exceeds 2x original
- peak -> compression: after N peak events (configurable)
- compression -> rebirth: when vowel ratio drops below threshold
- rebirth -> expansion: automatic after SONG-BIRTH emission
The current implementation stores phase in `state_snapshot.phase` but does not enforce transitions.

#### US-015: Multi-generation evolution chains

> As a **researcher**, I want to run dozens of sequential evolution events producing recognizably distinct language variants that model real linguistic drift across centuries.

**Vision:** A `multi_evolve()` method that accepts a chain of events and applies them sequentially, producing intermediate snapshots. This would enable "500-year drift" simulations by composing natural_drift + phase_shift + glyph_fusion in sequences.

#### US-016: Glyph-seed evolution lifecycle

> As a **researcher**, I want to track individual glyph-seeds through the full lifecycle: letter -> compressed glyph -> sung-language form.

**Vision:** Extend glyph-seed metadata (from `glyph_data.py`) with evolution state tracking. Each glyph carries its evolution history: original form, compression forms, fusion forms, and final sung-language phoneme. The `future_seeds` field in `GlyphSeed` already points to potential evolution targets.

#### US-017: Branch merging

> As a **researcher**, I want to merge two divergent branches into a unified text that combines their evolutionary paths.

**Vision:** A `merge_branches()` method that:
- Replays both branches to current state
- Identifies common ancestor (LCA in branch tree)
- Three-way merge: common ancestor + left + right
- Conflict resolution strategies: left-wins, right-wins, interleave, manual

#### US-018: Sung-language emergence

> As a **researcher**, I want compression+rebirth cycles to produce musical syllabic structures representing the emergence of "sung-language" forms.

**Vision:** After multiple rebirth events, the system would:
- Analyze remaining consonant clusters for singability
- Insert vowel bridges between hard consonant clusters
- Apply rhythmic patterns (iambic, trochaic, dactylic) to word sequences
- Tag resulting text with musical notation hints (pitch contour, rhythm markers)

#### US-019: Evolution visualization timeline

> As a **researcher**, I want to visualize a branch's evolution as an interactive timeline showing text transformation at each event.

**Vision:** The `/app/timeline` frontend view (currently a shell) would render:
- Horizontal timeline with event nodes
- Text diff visualization at each step
- Phase coloring (expansion=green, peak=gold, compression=red, rebirth=violet)
- Branch tree visualization showing parent-child relationships
- Interactive replay with scrubbing

---

## 4. Functional Requirements

### Natural Drift

- **FR-001** (MUST): `natural_drift` events MUST apply all 25 `NATURAL_MAP` substitutions (`th->THORN`, `ae->ASH`, `ph->f`, `ck->k`, `tion->cion`, `ct->tt`, `pl->pi`, `fl->fi`, `cl->chi`, `x->ss`, `li->gli`, `ni->gn`, `sc->sh`, `cw->qu`, `hw->wh`, `oo->ou`, `ee->ea`, `igh->eye`, `ght->t`, `ough->ow`, `wh->w`, `kn->n`, `wr->r`, `mb->m`, `gn->n`) case-insensitively using `re.sub` with `re.IGNORECASE`. Code ref: `evolution.py:298-305`.
- **FR-002** (MUST): The `diff_summary` for natural drift MUST include `{event: "natural_drift", replacements: int, before_chars: int, after_chars: int}`. Code ref: `evolution.py:305`.
- **FR-003** (MUST): Natural drift with seed=0 on empty text MUST produce empty output with `replacements=0`. Code ref: `evolution.py:299-305`.

### Synthetic Mutation

- **FR-004** (MUST): `synthetic_mutation` events MUST tokenize text via `re.findall(r"\w+|\W+", text)`, test each alphabetic token against `rng.random() < mutation_rate`, and replace matching tokens with `rng.choice(GLYPH_POOL)`. Code ref: `evolution.py:307-315`.
- **FR-005** (MUST): `mutation_rate` MUST be validated to `[0.0, 1.0]`; values outside this range MUST raise `ValueError`. Code ref: `evolution.py:260-261`.
- **FR-006** (MUST): `GLYPH_POOL` MUST contain exactly 10 Unicode glyphs: `["DELTA", "AE", "OMEGA", "SECTION", "TRIGRAM", "TRIANGLE", "PSI", "PHI", "THETA", "XI"]`. Code ref: `evolution.py:73`.
- **FR-007** (SHOULD): Default `mutation_rate` SHOULD be 0.08 when not provided. Code ref: `evolution.py:259`.

### Phase Shift

- **FR-008** (MUST): `phase_shift` events MUST validate `phase` against `{expansion, peak, compression, rebirth}`; invalid phases MUST raise `ValueError`. Code ref: `evolution.py:267-269`.
- **FR-009** (MUST): The acceleration multiplier MUST modify intensity per the formulas: expansion/peak: `min(acceleration * (1.0 + phase_idx * 0.5), 5.0)`; compression/rebirth: `max(acceleration * (1.0 - (phase_idx - 2) * 0.3), 0.2)`. Code ref: `evolution.py:322-326`.
- **FR-010** (MUST): Compression phase MUST remove vowels (a/e/i/o/u, case-insensitive) with per-character probability `min(intensity * 0.6, 1.0)`. Code ref: `evolution.py:328-336`.
- **FR-011** (MUST): Rebirth phase MUST remove vowels with probability `min(intensity * 0.4, 1.0)` and append `"\n\n^Triangle SONG-BIRTH ^Triangle"`. Code ref: `evolution.py:337-344`.
- **FR-012** (MUST): Peak phase MUST uppercase the entire text; when intensity > 1.5, MUST also insert "MYTHIC" at intervals. Code ref: `evolution.py:345-356`.
- **FR-013** (MUST): Expansion phase MUST insert "mythic" after every Nth word where `N = max(1, int(7 / intensity))`. Code ref: `evolution.py:358-365`.
- **FR-014** (SHOULD): Default `acceleration` SHOULD be 1.0 when not provided. Code ref: `evolution.py:319`.

### Glyph Fusion

- **FR-015** (MUST): `glyph_fusion` events MUST replace all occurrences of `left+right` with `fused` in the text. Replacement is case-sensitive. Code ref: `evolution.py:368-375`.
- **FR-016** (MUST): `left`, `right`, and `fused` MUST all be non-empty strings; empty values MUST raise `ValueError`. Code ref: `evolution.py:278-279`.
- **FR-017** (MUST): `diff_summary` MUST contain `{event, fusions: int, pair: str, fused: str, before_chars, after_chars}`. Code ref: `evolution.py:375`.

### Remix Event

- **FR-018** (MUST): `remix` events MUST carry pre-computed text in `event_payload.remixed_text` and return it unmodified as `output_text`. Code ref: `evolution.py:377-381`.
- **FR-019** (MUST): The remix event diff_summary MUST contain `{event: "remix", strategy, before_chars, after_chars}`. Code ref: `evolution.py:381`.
- **FR-020** (SHOULD): Default strategy SHOULD be `"interleave"` when not provided. Code ref: `evolution.py:288`.

### Branching

- **FR-021** (MUST): When `parent_branch_id` is provided, the system MUST resolve `root_document_id` from the parent and `base_text` from `parent.state_snapshot.current_text`. Code ref: `evolution.py:89-93`.
- **FR-022** (MUST): When `parent_branch_id` is not provided, `root_document_id` MUST be required. Code ref: `evolution.py:101-102`.
- **FR-023** (MUST): `branch_version` MUST be `parent.branch_version + 1` for child branches, or `1` for root branches. Code ref: `evolution.py:121`.
- **FR-024** (MUST): Branch name MUST be auto-generated as `"branch-{event_type}"`. Code ref: `evolution.py:114`.
- **FR-025** (MUST): Branch mode MUST be stored uppercase. Code ref: `evolution.py:115`.
- **FR-026** (MUST): A nonexistent `parent_branch_id` MUST raise `ValueError`. Code ref: `evolution.py:90-91`.
- **FR-027** (MUST): A nonexistent `root_document_id` (when no parent) MUST raise `ValueError`. Code ref: `evolution.py:104-105`.

### Event Recording

- **FR-028** (MUST): Each `BranchEvent` MUST have a deterministic `event_hash` computed as `sha256(branch_id:event_index:event_type:json(payload, sort_keys=True):text_hash)`. Code ref: `evolution.py:127-129`.
- **FR-029** (MUST): `payload_schema_version` MUST be `"v2"`. Code ref: `evolution.py:136`.
- **FR-030** (MUST): `result_snapshot` MUST contain `{text_hash, preview}` where preview is the first 500 characters of output text. Code ref: `evolution.py:139-142`.
- **FR-031** (MUST): `event_index` MUST be the next sequential index for the branch, starting from 1. Code ref: `evolution.py:126`, `evolution.py:245-247`.

### Deterministic Replay

- **FR-032** (MUST): All event types using RNG MUST derive the seed from `sha256(event_type:seed:sha256(text))` mod `2^32`. Code ref: `evolution.py:294-295`.
- **FR-033** (MUST): Identical inputs (text, event_type, event_payload) MUST produce identical outputs.
- **FR-034** (MUST): `get_timeline()` MUST walk the full lineage (child -> ancestors), collect all events, and replay them sequentially from the root document's extracted text. Code ref: `evolution.py:159-191`.
- **FR-035** (MUST): `replay_branch()` MUST return `{branch_id, event_count, text_hash, preview, replay_snapshot}`. Code ref: `evolution.py:193-202`.

### Optimistic Concurrency

- **FR-036** (MUST): When `event_payload.expected_parent_event_index` is provided and does not match the actual lineage event count, the system MUST raise `ValueError` with message containing `"Optimistic concurrency violation"`. Code ref: `evolution.py:95-99`.
- **FR-037** (MUST): When `expected_parent_event_index` is not provided, no concurrency check MUST be performed. Code ref: `evolution.py:95-96`.

### Checkpointing

- **FR-038** (MUST): A `BranchCheckpoint` MUST be created when `total_lineage_events % 10 == 0`. Code ref: `evolution.py:147`.
- **FR-039** (MUST): `snapshot_compressed` MUST be the result of `base64(zlib(json(state_snapshot, sort_keys=True)))` at compression level 9. Code ref: `evolution.py:385-388`.
- **FR-040** (MUST): `BranchCheckpoint` has a unique constraint on `(branch_id, event_index)`. Code ref: `models.py:306-308`.

### Branch Comparison

- **FR-041** (MUST): `compare_branches()` MUST replay both branches and compute character-by-character distance on their full replayed text (via preview, first 500 chars). Code ref: `evolution.py:204-219`, `evolution.py:390-398`.
- **FR-042** (MUST): `same` field MUST be `True` if and only if `left_hash == right_hash`. Code ref: `evolution.py:217`.
- **FR-043** (MUST): Distance MUST be computed as the count of differing characters at each position, with missing characters counting as differences. Code ref: `evolution.py:390-398`.

### Remix Strategies

- **FR-044** (MUST): `interleave` MUST alternate words from source and target using `re.findall(r"\S+")` tokenization, filling from the longer source. Code ref: `remix.py:97-107`.
- **FR-045** (MUST): `thematic_blend` MUST split both texts on sentence boundaries (`[.!?]+`), combine, shuffle with seeded RNG, and join with `. `. Code ref: `remix.py:109-114`.
- **FR-046** (MUST): `temporal_layer` MUST alternate paragraphs (`\n\s*\n` split) with target paragraphs prefixed `"[temporal overlay] "` included with probability 0.7 per RNG. Code ref: `remix.py:116-126`.
- **FR-047** (MUST): `glyph_collide` MUST compare non-space characters position-by-position: identical chars kept, differing chars chosen with 50/50 RNG, capped at 2000 positions. Code ref: `remix.py:128-142`.
- **FR-048** (MUST): Both source and target texts MUST be non-empty; empty text MUST raise `ValueError`. Code ref: `remix.py:42-43`.

### API Routes

- **FR-049** (MUST): `POST /api/v1/evolve/branch` MUST require `operator` role. Code ref: `routes.py:236`.
- **FR-050** (MUST): `GET /api/v1/branches` MUST require `viewer` role and support `limit` query param (1-1000, default 100). Code ref: `routes.py:291-292`.
- **FR-051** (MUST): `GET /api/v1/branches/{id}/timeline` MUST require `viewer` role. Code ref: `routes.py:261`.
- **FR-052** (MUST): `POST /api/v1/branches/{id}/replay` MUST require `viewer` role. Code ref: `routes.py:585`.
- **FR-053** (MUST): `GET /api/v1/branches/{left}/compare/{right}` MUST require `viewer` role. Code ref: `routes.py:597`.
- **FR-054** (MUST): `POST /api/v1/remix` MUST require `operator` role and enforce mode. Code ref: `routes.py:687-691`.
- **FR-055** (MUST): Nonexistent branch IDs in timeline/replay/compare MUST return HTTP 404. Code ref: `routes.py:285-286`, `routes.py:592-593`, `routes.py:607-608`.
- **FR-056** (MUST): Invalid event payloads (bad mutation_rate, unknown phase, empty glyph_fusion params) MUST return HTTP 400. Code ref: `routes.py:254-256`.

### Reverse Drift (P2)

- **FR-057** (SHOULD): The system SHOULD implement a `reverse_drift` event type that applies `REVERSE_NATURAL_MAP` substitutions to undo natural drift.
- **FR-058** (SHOULD): `REVERSE_NATURAL_MAP` SHOULD contain at minimum the 12 existing reverse mappings: `THORN->th`, `ASH->ae`, `f->ph`, `k->ck`, `cion->tion`, `tt->ct`, `pi->pl`, `fi->fl`, `chi->cl`, `ss->x`, `sh->sc`, `qu->cw`. Code ref: `evolution.py:58-71`.

### Phase State Manager (P3)

- **FR-059** (SHOULD): The system SHOULD implement a `PhaseStateManager` that tracks per-branch phase state with automatic transitions based on configurable thresholds.
- **FR-060** (MAY): Phase transitions MAY be triggered by: word count exceeding 2x original (expansion->peak), N peak events elapsed (peak->compression), vowel ratio below threshold (compression->rebirth), SONG-BIRTH emission (rebirth->expansion).

### Multi-Generation Evolution (P3)

- **FR-061** (SHOULD): The system SHOULD support a `multi_evolve()` endpoint that accepts an ordered list of evolution events and applies them sequentially, returning all intermediate branch IDs and snapshots.
- **FR-062** (MAY): Multi-generation chains MAY be optimized by reading from the most recent checkpoint rather than replaying from root.

### Branch Merging (P3)

- **FR-063** (SHOULD): The system SHOULD implement `merge_branches()` that finds the lowest common ancestor, replays both branches, and merges text using a configurable strategy (left-wins, right-wins, interleave).
- **FR-064** (MAY): Merge conflicts MAY be surfaced to the user for manual resolution.

### Sung-Language Emergence (P4)

- **FR-065** (MAY): Multiple rebirth events MAY produce "sung-language" text with vowel bridges, rhythmic patterns, and musical notation hints.
- **FR-066** (MAY): The system MAY track singability metrics (consonant cluster density, vowel-consonant ratio) per branch.

### Evolution Visualization (P4)

- **FR-067** (MAY): The `/app/timeline` view MAY render an interactive evolution timeline with event nodes, text diffs, phase coloring, and branch tree visualization.

---

## 5. Key Entities

### 5.1 Branch

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID str(36) | Primary key |
| `parent_branch_id` | FK -> branches.id | Nullable; self-referential for lineage |
| `root_document_id` | FK -> documents.id | Nullable; the original source document |
| `name` | str(256) | Auto-generated: `"branch-{event_type}"` |
| `mode` | str(16) | `"PUBLIC"` or `"RAW"`, stored uppercase |
| `created_by` | str(128) | Nullable; API key owner |
| `state_snapshot` | JSON | `{current_text, phase, text_hash}` |
| `branch_version` | int | Incremental version (parent + 1, or 1 for root) |
| `created_at` | datetime(tz) | Timestamp |

Relationships: `events` (one-to-many BranchEvent), `checkpoints` (one-to-many BranchCheckpoint).

### 5.2 BranchEvent

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID str(36) | Primary key |
| `branch_id` | FK -> branches.id | Parent branch (CASCADE delete) |
| `event_index` | int | Sequential index within branch, starting at 1 |
| `event_type` | str(64) | `natural_drift`, `synthetic_mutation`, `phase_shift`, `glyph_fusion`, `remix` |
| `event_payload` | JSON | Event-specific parameters (seed, mutation_rate, phase, etc.) |
| `payload_schema_version` | str(16) | Always `"v2"` |
| `event_hash` | str(128) | Deterministic hash for integrity verification |
| `diff_summary` | JSON | Event-specific diff metrics |
| `result_snapshot` | JSON | `{text_hash, preview}` (preview = first 500 chars) |
| `created_at` | datetime(tz) | Timestamp |

### 5.3 BranchCheckpoint

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID str(36) | Primary key |
| `branch_id` | FK -> branches.id | Parent branch (CASCADE delete) |
| `event_index` | int | The lineage event count at checkpoint time |
| `snapshot_hash` | str(128) | sha256 of current_text |
| `snapshot_compressed` | Text | zlib(level=9) + base64 of JSON state_snapshot |
| `created_at` | datetime(tz) | Timestamp |

Unique constraint: `(branch_id, event_index)`.

---

## 6. Edge Cases

### 6.1 Empty Text

- Natural drift on empty text produces empty output with `replacements=0`.
- Synthetic mutation on empty text produces empty output with `mutations=0` (no words to tokenize).
- Phase shift on empty text: expansion produces `"mythic"` (single insertion), peak produces `""` (empty uppercase), compression produces `""`, rebirth produces `"\n\n^Triangle SONG-BIRTH ^Triangle"`.
- Glyph fusion on empty text produces empty output with `fusions=0`.

### 6.2 Conflicting Natural Map Entries

The `NATURAL_MAP` contains overlapping entries: `"gn"` maps to `"n"`, but `"ni"` maps to `"gn"`, meaning `"ni"` -> `"gn"` -> `"n"` if both applied. Since substitutions are applied sequentially via separate `re.sub` calls in dict iteration order, the result depends on Python dict ordering (insertion order in Python 3.7+). The `"ni"` entry (key position 12) is applied before `"gn"` (key position 25), so `"ni"` text first becomes `"gn"`, then `"gn"` becomes `"n"`. This produces a double-replacement chain.

### 6.3 Very Long Text

- Preview in `result_snapshot` is truncated to 500 characters (`evolution.py:141`).
- Branch comparison operates on previews (first 500 chars), not full text.
- Checkpoint compression uses zlib level 9, which handles large texts but stores the full `state_snapshot` including `current_text`.

### 6.4 Parent Branch Not Found

When `parent_branch_id` is provided but the branch does not exist in the database, `ValueError` is raised (`evolution.py:90-91`), which the route handler converts to HTTP 400 (`routes.py:254-256`).

### 6.5 Concurrent Branching Without Optimistic Lock

If `expected_parent_event_index` is not provided, multiple clients can create branches from the same parent simultaneously without conflict. Each creates an independent branch; they do not share a timeline.

### 6.6 Unicode in Evolution

- Natural drift substitutions use `re.IGNORECASE` which handles basic Unicode case folding.
- Glyph fusion is case-sensitive: `"AE"` and `"ae"` are different pairs.
- GLYPH_POOL contains Unicode characters (Delta, Omega, etc.) that survive all transformations.
- Phase shift vowel detection checks lowercase `"aeiou"` only; accented vowels (e.g., `"a-grave"`, `"e-acute"`) are not removed during compression/rebirth.

---

## 7. Non-Functional Requirements

- **NFR-01** (MUST): A single `evolve_branch()` call MUST complete in under 200ms for texts under 100KB.
- **NFR-02** (MUST): Branch replay via `get_timeline()` MUST complete in under 2s for lineages of up to 100 events.
- **NFR-03** (MUST): Checkpoint compression MUST produce output smaller than uncompressed JSON for texts > 1KB.
- **NFR-04** (SHOULD): The system SHOULD handle branch lineages of up to 1000 events without stack overflow (lineage walking is iterative, not recursive).
- **NFR-05** (SHOULD): Checkpoint-based replay optimization SHOULD be implemented to avoid full replay from root for deep lineages.
- **NFR-06** (MAY): Event hashes MAY be verified during replay to detect data corruption.

---

## 8. Success Criteria

1. All 5 event types (natural_drift, synthetic_mutation, phase_shift, glyph_fusion, remix) are covered by unit tests with deterministic assertions on output text.
2. Branch lineage (parent chaining, version incrementing) is tested for chains of depth >= 3.
3. Optimistic concurrency violation is tested for both passing and failing cases.
4. Auto-checkpointing is verified at the 10th lineage event boundary.
5. Branch replay produces identical results to fresh evolution (determinism test).
6. Branch comparison returns correct distance for identical, similar, and completely different texts.
7. All 4 remix strategies produce deterministic output for fixed seeds.
8. All API routes enforce correct auth roles and return appropriate HTTP error codes.
9. Empty text, single-character text, and large text (100KB) edge cases are covered.
10. Natural drift's 25 mappings are individually verified against known input/output pairs.

---

## 9. Constraints & Assumptions

- Branch comparison operates on previews (first 500 characters), not full text. For long texts, the distance metric may underrepresent total divergence.
- The `_lineage()` method walks parent pointers iteratively. There is no cycle detection; the data model's foreign key structure prevents cycles but orphaned parent references could cause infinite loops if data is corrupted.
- Checkpoint-based replay acceleration is not yet implemented; `get_timeline()` always replays from root.
- The remix service's `_interleave` strategy does not use the seeded RNG (it is deterministic by construction), while the other three strategies do.
- Natural drift applies all 25 substitutions to every text regardless of language. English text with no matching patterns passes through unchanged.
- The `event_type` field is a free string validated by `_validate_event_payload()`; unsupported types raise `ValueError`. There is no Enum constraint at the schema level.
