# 03 -- Evolution & Branching: Implementation Plan

> **Domain:** 03-evolution-branching
> **Status:** Draft
> **Last updated:** 2026-02-23
> **Spec reference:** `specs/03-evolution-branching/spec.md`

---

## 1. Priority Tiers

| Tier | Scope | Goal |
|------|-------|------|
| P1 | As-built hardening | Test coverage for all 5 event types, branching mechanics, replay determinism, concurrency, checkpointing, comparison, API routes |
| P2 | Reverse drift & multi-evolve | Add `reverse_drift` event type, batch evolution endpoint, checkpoint-accelerated replay |
| P3 | Phase state & branch merging | Automatic phase transitions, branch merge with LCA, multi-generation simulation |
| P4 | Sung-language & visualization | Musical syllabic emergence, interactive timeline UI |

---

## 2. Technical Context

### 2.1 Project Structure

```
src/nexus_babel/
  services/
    evolution.py        # EvolutionService (core: evolve, replay, compare, checkpoint)
    remix.py            # RemixService (4 strategies, delegates to EvolutionService)
    glyph_data.py       # Static glyph-seed metadata lookup tables
  models.py             # Branch, BranchEvent, BranchCheckpoint ORM models
  schemas.py            # Request/response Pydantic models
  api/
    routes.py           # All /api/v1/ endpoints including evolution routes

tests/
  conftest.py           # Shared fixtures (test_settings, client, auth_headers, sample_corpus)
  test_wave2.py         # test_branch_replay_and_compare (integration)
  test_arc4n.py         # TestExpandedNaturalDrift, TestPhaseShiftAcceleration, TestRemixEventType,
                        # TestRemixStrategies, TestRemixAPI (unit + integration)
```

### 2.2 Existing Test Coverage

| Test | Location | What It Covers |
|------|----------|----------------|
| `test_branch_replay_and_compare` | `test_wave2.py:107-129` | E2E: create two branches (natural_drift + synthetic_mutation), replay one, compare both |
| `TestExpandedNaturalDrift` (6 tests) | `test_arc4n.py:175-207` | NATURAL_MAP size >=25, original entries preserved, Latin/Italian shifts, OE shifts, REVERSE_MAP exists, drift applies new mappings, determinism |
| `TestPhaseShiftAcceleration` (5 tests) | `test_arc4n.py:210-237` | Expansion default, acceleration increases intensity, compression removes vowels, rebirth adds SONG-BIRTH, acceleration in diff_summary |
| `TestRemixEventType` (2 tests) | `test_arc4n.py:239-251` | Remix payload validation, remix event application |
| `TestRemixStrategies` (4 tests) | `test_arc4n.py:257-298` | Interleave, thematic_blend determinism, glyph_collide output, temporal_layer |
| `TestRemixAPI` (2 tests) | `test_arc4n.py:360-400` | Auth requirement, remix with two documents |

### 2.3 Coverage Gaps Identified

1. **No unit tests for glyph_fusion event type** (only integration coverage via API)
2. **No unit tests for synthetic_mutation edge cases** (mutation_rate=0.0, mutation_rate=1.0, empty text)
3. **No tests for optimistic concurrency violation**
4. **No tests for auto-checkpointing** at the 10th event boundary
5. **No tests for branch lineage walking** (depth > 2)
6. **No tests for event hash determinism** or `event_hash` correctness
7. **No tests for `_validate_event_payload()` error paths** (bad mutation_rate, unknown phase, empty glyph params, unsupported event_type)
8. **No tests for `_compress_snapshot()`** roundtrip correctness
9. **No API-level tests for error cases** (missing root_document_id, nonexistent branch, viewer-forbidden-POST)
10. **No tests for replay_branch returning correct `event_count`**
11. **Branch comparison distance calculation** not directly tested for correctness
12. **No tests for the `name` and `mode` fields** on created branches

---

## 3. Data Models

### 3.1 Branch (existing -- `models.py:110-124`)

```python
class Branch(Base):
    __tablename__ = "branches"
    id: str             # UUID, PK
    parent_branch_id: str | None  # FK self, nullable
    root_document_id: str | None  # FK documents, nullable
    name: str           # "branch-{event_type}"
    mode: str           # "PUBLIC" | "RAW"
    created_by: str | None
    state_snapshot: dict # {current_text, phase, text_hash}
    branch_version: int  # parent.version + 1 or 1
    created_at: datetime
```

### 3.2 BranchEvent (existing -- `models.py:127-141`)

```python
class BranchEvent(Base):
    __tablename__ = "branch_events"
    id: str             # UUID, PK
    branch_id: str      # FK branches, CASCADE
    event_index: int    # sequential per-branch
    event_type: str     # natural_drift | synthetic_mutation | phase_shift | glyph_fusion | remix
    event_payload: dict # event-specific params
    payload_schema_version: str  # "v2"
    event_hash: str     # deterministic integrity hash
    diff_summary: dict  # event-specific metrics
    result_snapshot: dict  # {text_hash, preview[:500]}
    created_at: datetime
```

### 3.3 BranchCheckpoint (existing -- `models.py:294-308`)

```python
class BranchCheckpoint(Base):
    __tablename__ = "branch_checkpoints"
    id: str             # UUID, PK
    branch_id: str      # FK branches, CASCADE
    event_index: int    # lineage event count at checkpoint
    snapshot_hash: str  # sha256 of current_text
    snapshot_compressed: str  # base64(zlib(json(state_snapshot)))
    created_at: datetime
    # Unique: (branch_id, event_index)
```

### 3.4 P2 Additions (proposed)

No new tables required. `reverse_drift` adds a new `event_type` value using existing `BranchEvent` schema.

For `multi_evolve`, a new Pydantic request/response schema:

```python
class MultiEvolveRequest(BaseModel):
    root_document_id: str | None = None
    parent_branch_id: str | None = None
    events: list[dict]   # [{event_type, event_payload}, ...]
    mode: Mode = "PUBLIC"

class MultiEvolveResponse(BaseModel):
    branch_ids: list[str]
    final_branch_id: str
    event_count: int
    final_text_hash: str
    final_preview: str
```

### 3.5 P3 Additions (proposed)

For phase state tracking, extend `Branch.state_snapshot` with:

```json
{
  "current_text": "...",
  "phase": "expansion",
  "text_hash": "abc123",
  "phase_history": [
    {"phase": "expansion", "entered_at": "2026-02-23T00:00:00Z", "word_count": 150},
    {"phase": "peak", "entered_at": "2026-02-23T01:00:00Z", "word_count": 300}
  ],
  "original_word_count": 150,
  "original_vowel_ratio": 0.38
}
```

No new ORM models required; phase state fits within the existing JSON `state_snapshot`.

---

## 4. API Contracts

### 4.1 POST /api/v1/evolve/branch (existing)

**Auth:** operator

**Request:**
```json
{
  "parent_branch_id": null,
  "root_document_id": "doc-uuid-123",
  "event_type": "natural_drift",
  "event_payload": {"seed": 42},
  "mode": "PUBLIC"
}
```

**Response (200):**
```json
{
  "new_branch_id": "branch-uuid-456",
  "event_id": "event-uuid-789",
  "diff_summary": {
    "event": "natural_drift",
    "replacements": 7,
    "before_chars": 450,
    "after_chars": 443
  }
}
```

**Error (400) -- bad event payload:**
```json
{"detail": "mutation_rate must be between 0.0 and 1.0"}
```

**Error (400) -- missing root_document_id:**
```json
{"detail": "root_document_id is required when parent_branch_id is not provided"}
```

**Error (400) -- optimistic concurrency:**
```json
{"detail": "Optimistic concurrency violation: expected_parent_event_index=5 actual=7"}
```

### 4.2 GET /api/v1/branches (existing)

**Auth:** viewer

**Query params:** `limit` (int, 1-1000, default 100)

**Response (200):**
```json
{
  "branches": [
    {
      "id": "branch-uuid-456",
      "parent_branch_id": null,
      "root_document_id": "doc-uuid-123",
      "mode": "PUBLIC",
      "branch_version": 1,
      "created_at": "2026-02-23T12:00:00Z"
    }
  ]
}
```

### 4.3 GET /api/v1/branches/{id}/timeline (existing)

**Auth:** viewer

**Response (200):**
```json
{
  "branch_id": "branch-uuid-456",
  "root_document_id": "doc-uuid-123",
  "events": [
    {
      "branch_id": "branch-uuid-456",
      "event_id": "event-uuid-789",
      "event_index": 1,
      "event_type": "natural_drift",
      "event_payload": {"seed": 42},
      "diff_summary": {"event": "natural_drift", "replacements": 7, "before_chars": 450, "after_chars": 443},
      "created_at": "2026-02-23T12:00:00Z"
    }
  ],
  "replay_snapshot": {
    "text_hash": "sha256hex...",
    "preview": "first 500 chars of replayed text...",
    "event_count": 1
  }
}
```

**Error (404):**
```json
{"detail": "Branch branch-nonexistent not found"}
```

### 4.4 POST /api/v1/branches/{id}/replay (existing)

**Auth:** viewer

**Response (200):**
```json
{
  "branch_id": "branch-uuid-456",
  "event_count": 3,
  "text_hash": "sha256hex...",
  "preview": "first 500 chars...",
  "replay_snapshot": {
    "text_hash": "sha256hex...",
    "preview": "first 500 chars...",
    "event_count": 3
  }
}
```

### 4.5 GET /api/v1/branches/{left}/compare/{right} (existing)

**Auth:** viewer

**Response (200):**
```json
{
  "left_branch_id": "branch-uuid-1",
  "right_branch_id": "branch-uuid-2",
  "left_hash": "sha256hex...",
  "right_hash": "sha256hex...",
  "distance": 42,
  "same": false,
  "preview_left": "first 500 chars left...",
  "preview_right": "first 500 chars right..."
}
```

### 4.6 POST /api/v1/remix (existing)

**Auth:** operator

**Request:**
```json
{
  "source_document_id": "doc-uuid-1",
  "target_document_id": "doc-uuid-2",
  "strategy": "interleave",
  "seed": 42,
  "mode": "PUBLIC"
}
```

**Response (200):**
```json
{
  "new_branch_id": "branch-uuid-remix",
  "event_id": "event-uuid-remix",
  "strategy": "interleave",
  "diff_summary": {
    "event": "remix",
    "strategy": "interleave",
    "before_chars": 450,
    "after_chars": 890
  }
}
```

### 4.7 POST /api/v1/evolve/multi (proposed P2)

**Auth:** operator

**Request:**
```json
{
  "root_document_id": "doc-uuid-123",
  "events": [
    {"event_type": "natural_drift", "event_payload": {"seed": 1}},
    {"event_type": "phase_shift", "event_payload": {"phase": "expansion", "seed": 2}},
    {"event_type": "synthetic_mutation", "event_payload": {"seed": 3, "mutation_rate": 0.1}},
    {"event_type": "glyph_fusion", "event_payload": {"left": "A", "right": "E", "fused": "AE"}}
  ],
  "mode": "PUBLIC"
}
```

**Response (200):**
```json
{
  "branch_ids": ["b1", "b2", "b3", "b4"],
  "final_branch_id": "b4",
  "event_count": 4,
  "final_text_hash": "sha256hex...",
  "final_preview": "first 500 chars of final state..."
}
```

---

## 5. Service Architecture

### 5.1 EvolutionService Method Map

| Method | Visibility | Purpose |
|--------|-----------|---------|
| `evolve_branch()` | public | Create branch + event, validate, apply, checkpoint |
| `get_timeline()` | public | Walk lineage, collect events, replay from root |
| `replay_branch()` | public | Delegates to `get_timeline()`, returns replay result |
| `compare_branches()` | public | Replay both, compute char distance |
| `_validate_event_payload()` | private | Per-type payload validation with defaults |
| `_apply_event()` | private | Seeded RNG + type-specific text transformation |
| `_lineage()` | private | Walk parent pointers to root, return reversed list |
| `_lineage_event_count()` | private | Sum event counts across lineage |
| `_next_event_index()` | private | MAX(event_index) + 1 for a branch |
| `_compress_snapshot()` | private | zlib + base64 encoding |
| `_simple_distance()` | private | Char-by-char comparison |

### 5.2 RemixService Method Map

| Method | Visibility | Purpose |
|--------|-----------|---------|
| `remix()` | public | Resolve texts, apply strategy, delegate to EvolutionService |
| `_resolve_text()` | private | Get text from document or branch |
| `_branch_root_doc()` | private | Find root_document_id for a branch |
| `_apply_strategy()` | private | Dispatch to strategy method |
| `_interleave()` | private | Alternate words from two sources |
| `_thematic_blend()` | private | Shuffle sentences from both sources |
| `_temporal_layer()` | private | Overlay paragraphs with temporal markers |
| `_glyph_collide()` | private | Position-by-position glyph comparison |

### 5.3 RNG Determinism Chain

```
evolve_branch(event_type, event_payload={seed: N})
  -> _apply_event(text, event_type, event_payload)
     -> seed_input = f"{event_type}:{N}:{sha256(text)}"
     -> rng_seed = int(sha256(seed_input), 16) % 2^32
     -> rng = random.Random(rng_seed)
     -> all randomness drawn from rng (mutations, vowel removal, etc.)
```

For remix:
```
RemixService.remix(strategy, seed)
  -> seed_input = f"remix:{strategy}:{seed}:{sha256(source)}:{sha256(target)}"
  -> rng = random.Random(int(sha256(seed_input), 16) % 2^32)
  -> strategy method uses rng
```

---

## 6. P1 Stories: As-Built Hardening

### S03-01: Natural Drift Coverage

**What exists:**
- `TestExpandedNaturalDrift` in `test_arc4n.py` tests NATURAL_MAP size, key entries, determinism, and applies new mappings.

**What needs hardening:**
1. Individual mapping verification: parametrized test for all 25 NATURAL_MAP entries with known input/output.
2. Empty text edge case.
3. Case-insensitive verification: confirm "TH" -> "THORN" and "th" -> "thorn".
4. Double-replacement chain: text containing "ni" (->gn) then "gn" (->n) to verify ordering behavior.
5. Text with no matching patterns passes through unchanged.

### S03-02: Synthetic Mutation Coverage

**What exists:**
- No dedicated synthetic mutation unit tests. Integration coverage via `test_branch_replay_and_compare`.

**What needs hardening:**
1. `mutation_rate=0.0`: zero mutations expected.
2. `mutation_rate=1.0`: all alphabetic words mutated.
3. Invalid `mutation_rate` (-0.1, 1.5): verify ValueError.
4. Empty text: verify empty output.
5. Single-word text: verify mutation/no-mutation based on RNG.
6. Determinism: same seed + same text -> same output.

### S03-03: Phase Shift Coverage

**What exists:**
- `TestPhaseShiftAcceleration` tests expansion default, acceleration, compression vowel removal, rebirth SONG-BIRTH.

**What needs hardening:**
1. Peak phase with intensity <= 1.5 (no MYTHIC insertion, just uppercase).
2. Peak phase with intensity > 1.5 (MYTHIC insertion verified).
3. Invalid phase value: verify ValueError.
4. Acceleration edge cases: 0.0 (minimum intensity clamped to 0.2), very large (capped at 5.0).
5. Empty text through all 4 phases.
6. Determinism across all phases.

### S03-04: Glyph Fusion Coverage

**What exists:**
- No unit tests for glyph_fusion.

**What needs hardening:**
1. Simple fusion: "AE" in "AEGIS" -> fused glyph in "fused+GIS".
2. Case sensitivity: "ae" != "AE".
3. Multiple occurrences: count all fusions.
4. No occurrences: fusions=0, text unchanged.
5. Empty left/right/fused: verify ValueError.
6. Empty text: verify empty output.

### S03-05: Branching Mechanics

**What exists:**
- Integration tests create branches via API. No isolated tests for lineage, version, or mode.

**What needs hardening:**
1. Root branch (no parent): `branch_version=1`, `parent_branch_id=null`.
2. Child branch: `branch_version=parent+1`, `root_document_id` inherited.
3. Grandchild branch: depth=3 lineage walking.
4. Nonexistent parent: ValueError.
5. Missing root_document_id (no parent): ValueError.
6. Nonexistent root_document_id: ValueError.
7. Branch name auto-generation: `"branch-{event_type}"`.
8. Branch mode uppercase: lowercase input -> uppercase stored.

### S03-06: Event Recording & Hash Determinism

**What exists:**
- Determinism tested for natural_drift only.

**What needs hardening:**
1. Verify `event_hash` is correctly computed as `sha256(branch_id:event_index:event_type:json(payload):text_hash)`.
2. Verify `payload_schema_version = "v2"`.
3. Verify `result_snapshot.preview` is <= 500 chars.
4. Verify `event_index` starts at 1 and increments per branch.

### S03-07: Optimistic Concurrency

**What exists:**
- No tests.

**What needs hardening:**
1. Correct `expected_parent_event_index` passes.
2. Incorrect `expected_parent_event_index` raises ValueError with "Optimistic concurrency violation".
3. Omitted `expected_parent_event_index` skips check.

### S03-08: Auto-Checkpointing

**What exists:**
- No tests.

**What needs hardening:**
1. Create 10 sequential branches. Verify a BranchCheckpoint exists at event_index=10.
2. Verify checkpoint `snapshot_compressed` can be decompressed back to valid JSON matching the state.
3. Verify no checkpoint at event_index=9 or 11.
4. Verify `snapshot_hash` matches sha256 of the branch text at that point.

### S03-09: Replay & Timeline

**What exists:**
- `test_branch_replay_and_compare` tests basic replay + compare.

**What needs hardening:**
1. Replay a branch with 3+ events and verify `event_count` matches.
2. Timeline returns events in correct order (root ancestor first).
3. Replay produces text_hash matching the branch's `state_snapshot.text_hash`.
4. Timeline for nonexistent branch returns 404.

### S03-10: Branch Comparison

**What exists:**
- `test_branch_replay_and_compare` asserts "distance" key exists.

**What needs hardening:**
1. Compare identical branches: distance=0, same=True.
2. Compare completely different branches: distance > 0, same=False.
3. Verify distance calculation: known text pairs with computed expected distance.
4. Compare nonexistent branch returns 404.

### S03-11: Remix Strategies (hardening)

**What exists:**
- `TestRemixStrategies` tests 4 strategies at unit level. `TestRemixAPI` tests API level.

**What needs hardening:**
1. Interleave with unequal-length sources.
2. Thematic_blend: verify sentence count in output.
3. Temporal_layer: verify "[temporal overlay]" markers present.
4. Glyph_collide: verify output length == max(source, target) up to 2000.
5. Remix with empty source or target: verify ValueError.
6. Remix with branch sources (not just documents).

### S03-12: API Route Enforcement

**What exists:**
- Auth required tests for remix. Basic evolve/replay/compare via integration.

**What needs hardening:**
1. `POST /evolve/branch` with viewer key -> 403.
2. `POST /evolve/branch` with no key -> 401.
3. `POST /evolve/branch` in RAW mode enforcement.
4. `GET /branches` limit param boundaries (0 -> validation error, 1001 -> validation error).
5. Timeline/replay/compare with nonexistent branch -> 404.
6. Remix with viewer key -> 403.

---

## 7. P2 Stories: Reverse Drift & Multi-Evolve

### S03-13: Reverse Drift Event Type

**Goal:** Add `reverse_drift` as a supported event type that applies `REVERSE_NATURAL_MAP` substitutions.

**Approach:**
1. Add `"reverse_drift"` case in `_validate_event_payload()`: default `seed=0`.
2. Add `"reverse_drift"` case in `_apply_event()`: iterate `REVERSE_NATURAL_MAP` with `re.sub(old, new, text, flags=re.IGNORECASE)`.
3. Return `DriftResult` with `{event: "reverse_drift", reversals, before_chars, after_chars}`.

**Files touched:**
- `src/nexus_babel/services/evolution.py` (add cases in two methods)
- `tests/test_evolution.py` (new tests)

**Risks:**
- Some reverse mappings are ambiguous: `"f"` could be `"ph"` or just `"f"`. The reverse map will over-apply, converting legitimate `"f"` to `"ph"`. This is by design (documented as lossy).

### S03-14: Multi-Evolve Batch Endpoint

**Goal:** Accept an ordered list of events and apply them sequentially, returning all intermediate branch IDs.

**Approach:**
1. Add `MultiEvolveRequest` and `MultiEvolveResponse` to `schemas.py`.
2. Add `multi_evolve()` to `EvolutionService` that loops `evolve_branch()` calls, threading `parent_branch_id` from each result.
3. Add `POST /api/v1/evolve/multi` route.
4. Wrap entire batch in a single DB transaction (commit all or rollback).

**Files touched:**
- `src/nexus_babel/schemas.py`
- `src/nexus_babel/services/evolution.py`
- `src/nexus_babel/api/routes.py`
- `tests/test_evolution.py`

### S03-15: Checkpoint-Accelerated Replay

**Goal:** Use `BranchCheckpoint` to accelerate `get_timeline()` for deep lineages.

**Approach:**
1. In `get_timeline()`, before replaying from root, check for the most recent `BranchCheckpoint` in the lineage.
2. If found, decompress the checkpoint, start replay from that point.
3. Only replay events after the checkpoint's `event_index`.
4. Fallback to full replay if checkpoint is missing or corrupt.

**Files touched:**
- `src/nexus_babel/services/evolution.py` (modify `get_timeline()`)
- `tests/test_evolution.py` (benchmark test comparing full vs checkpointed replay)

---

## 8. P3 Stories: Phase State & Branch Merging

### S03-16: Phase State Manager

**Goal:** Track per-branch phase state with automatic transitions.

**Approach:**
1. Add `PhaseStateManager` class (new file or in `evolution.py`).
2. After each `evolve_branch()`, evaluate transition conditions:
   - expansion -> peak: current word count > `2 * original_word_count`
   - peak -> compression: N peak events (configurable, default 3)
   - compression -> rebirth: vowel ratio < 0.1
   - rebirth -> expansion: after SONG-BIRTH emission
3. Store phase state in `Branch.state_snapshot.phase_history`.
4. If automatic transition fires, emit an additional `phase_shift` event.

**Files touched:**
- `src/nexus_babel/services/evolution.py` or `src/nexus_babel/services/phase_manager.py` (new)
- `tests/test_phase_manager.py` (new)

### S03-17: Branch Merging

**Goal:** Merge two divergent branches.

**Approach:**
1. Find lowest common ancestor (LCA) by walking both lineages and finding the intersection.
2. Replay both branches and the LCA to their current states.
3. Three-way merge: identify segments that changed in left vs right vs both.
4. For text merging, implement strategies: `left_wins`, `right_wins`, `interleave`, `manual` (returns conflict markers).
5. Create a new branch with `parent_branch_ids=[left, right]` (schema extension needed -- currently single parent).
6. Record merge as a new event type `"merge"`.

**Files touched:**
- `src/nexus_babel/services/evolution.py`
- `src/nexus_babel/models.py` (optional: multi-parent support)
- `src/nexus_babel/schemas.py`
- `src/nexus_babel/api/routes.py`
- `tests/test_evolution.py`

**Risks:**
- Single-parent model limits merge representation. A merge event could reference the second parent in `event_payload` instead of modifying the Branch schema.

---

## 9. P4 Stories: Sung-Language & Visualization

### S03-18: Sung-Language Emergence

**Goal:** After multiple rebirth cycles, produce musical syllabic structures.

**Approach:**
1. Track rebirth count per branch lineage.
2. After 3+ rebirth events, apply singability transform:
   - Identify harsh consonant clusters (3+ consonants without vowels).
   - Insert vowel bridges (schwa /SCHWA/ sound by default).
   - Apply rhythmic pattern to word spacing.
3. Tag output with musical metadata: `{rhythm: "iambic", tempo_hint: "andante"}`.

### S03-19: Evolution Visualization

**Goal:** Interactive timeline UI in `/app/timeline`.

**Approach:**
1. Frontend: React + D3.js timeline visualization.
2. Backend: Add `GET /api/v1/branches/{id}/visualization` endpoint returning graph data.
3. Features: horizontal timeline, text diff at each node, phase coloring, branch tree, scrub replay.

---

## 10. Dependency Graph

```
S03-01 (natural drift tests)  ────┐
S03-02 (synthetic mutation tests) ─┤
S03-03 (phase shift tests)  ──────┤
S03-04 (glyph fusion tests)  ─────┤
S03-05 (branching mechanics)  ─────┤
S03-06 (event hash tests)  ────────┤──> P1 complete
S03-07 (optimistic concurrency)  ──┤
S03-08 (checkpointing tests)  ─────┤
S03-09 (replay & timeline)  ───────┤
S03-10 (comparison tests)  ────────┤
S03-11 (remix hardening)  ─────────┤
S03-12 (API enforcement)  ─────────┘
                                    |
                                    v
S03-13 (reverse drift)  ──────────┐
S03-14 (multi-evolve)  ───────────┤──> P2 complete
S03-15 (checkpoint replay)  ──────┘
                                    |
                                    v
S03-16 (phase state manager)  ────┐
S03-17 (branch merging)  ─────────┘──> P3 complete
                                    |
                                    v
S03-18 (sung-language)  ──────────┐
S03-19 (visualization)  ──────────┘──> P4 complete
```

P1 stories are independent of each other and can be parallelized.
P2 stories are independent of each other; all depend on P1 completion.
P3 stories: S03-16 depends on S03-03 (phase tests); S03-17 depends on S03-09 (replay).
P4 stories depend on P3.

---

## 11. Testing Strategy

### Unit Tests (per story)

| Story | Test File | Scope |
|-------|-----------|-------|
| S03-01 | `tests/test_evolution.py` | All 25 NATURAL_MAP entries, edge cases |
| S03-02 | `tests/test_evolution.py` | Mutation rate boundaries, determinism |
| S03-03 | `tests/test_evolution.py` | All 4 phases, acceleration, edge cases |
| S03-04 | `tests/test_evolution.py` | Glyph fusion all paths |
| S03-05 | `tests/test_evolution.py` | Branching depth, version, mode, errors |
| S03-06 | `tests/test_evolution.py` | Event hash, schema version, snapshot |
| S03-07 | `tests/test_evolution.py` | Concurrency pass/fail/omit |
| S03-08 | `tests/test_evolution.py` | Checkpoint creation, decompression |
| S03-09 | `tests/test_evolution.py` | Replay correctness, timeline ordering |
| S03-10 | `tests/test_evolution.py` | Distance calculation, same/different |
| S03-11 | `tests/test_remix.py` | Strategy edge cases, empty text |
| S03-12 | `tests/test_evolution_api.py` | Auth, errors, mode enforcement |
| S03-13 | `tests/test_evolution.py` | Reverse drift, lossiness |
| S03-14 | `tests/test_evolution.py` | Multi-evolve batch |
| S03-15 | `tests/test_evolution.py` | Checkpoint-accelerated replay |

### Integration Tests

- Existing `test_wave2.py::test_branch_replay_and_compare` covers the E2E happy path.
- Existing `test_arc4n.py::TestRemixAPI` covers remix via API.
- New `tests/test_evolution_api.py` for comprehensive API-level coverage.

### Performance Tests

- `tests/test_evolution.py::test_evolution_performance_100kb` -- evolve a 100KB document, assert < 200ms. Mark `@pytest.mark.slow`.
- `tests/test_evolution.py::test_replay_performance_100_events` -- replay a 100-event lineage, assert < 2s. Mark `@pytest.mark.slow`.

---

## 12. Migration Notes

### Database

No new migrations required for P1. The `branches`, `branch_events`, and `branch_checkpoints` tables are already created in `20260218_0001_initial` and `20260218_0002_wave2_alpha`.

P2 `multi_evolve` and `reverse_drift` use existing tables with new event_type values.

P3 branch merging may require a migration if multi-parent support is added to the Branch model (new `merge_parent_branch_id` column or a junction table).

### Backward Compatibility

- P1 is test-only; no code changes.
- P2 adds new event types and endpoints; existing branches and events are unaffected.
- P3 extends `state_snapshot` JSON schema (additive); old branches without `phase_history` continue to work.

---

## 13. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Deep lineage replay is O(n) events | Slow timeline for long chains | P2 checkpoint-accelerated replay; cap lineage display at 100 events |
| Natural drift double-replacement chains | Unexpected text output | Document ordering behavior; add integration test for chain |
| Reverse drift over-application (`f`->`ph`) | Corrupts legitimate text | Document as lossy; add "conservative" mode that only reverses unique mappings |
| Branch comparison on 500-char preview only | Misses divergence in long texts | Document limitation; P3 adds full-text comparison option |
| Checkpoint compression of large texts | Memory spike during zlib | Stream compression for texts > 1MB; current texts are < 100KB |
| Phase state auto-transition in hot loops | Runaway event creation | Rate-limit auto-transitions to 1 per evolve_branch call |
| Concurrent checkpointing at same event_index | Unique constraint violation | The unique constraint `(branch_id, event_index)` prevents duplicates; catch IntegrityError |
