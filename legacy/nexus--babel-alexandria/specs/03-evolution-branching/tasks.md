# 03 -- Evolution & Branching: Tasks

> **Domain:** 03-evolution-branching
> **Status:** Draft
> **Last updated:** 2026-02-23
> **Plan reference:** `specs/03-evolution-branching/plan.md`

---

## Legend

- `[P]` = Can be parallelized with other `[P]` tasks in the same story
- `[S]` = Sequential; depends on prior task completion
- `[Story X]` = Story dependency (must complete before this task starts)

---

## P1: As-Built Hardening

### S03-01: Natural Drift Coverage

- [ ] **T01-01** [P] Create `tests/test_evolution.py` with shared fixtures: `EvolutionService` instance, a helper `_make_doc_and_branch()` that inserts a `Document` with known `extracted_text` and returns `(session, doc_id)` using an isolated SQLite test database.
  - File: `tests/test_evolution.py`
  - AC: Fixtures yield a working `EvolutionService` and a session factory. No DB leaks between tests.

- [ ] **T01-02** [P] Write parametrized test `test_natural_map_individual_entries` that tests each of the 25 `NATURAL_MAP` entries individually. For each `(old, new)` pair, feed a short text containing only `old` and assert `new` appears in output.
  - File: `tests/test_evolution.py`
  - AC: 25 parametrized cases. Each asserts the specific substitution occurred. E.g., input `"the"` -> output contains `"þe"`.

- [ ] **T01-03** [P] Write test `test_natural_drift_case_insensitive` that feeds text with uppercase patterns (`"THE KNIGHT"`) and verifies drift applies (`"þE"` or similar from `re.IGNORECASE`).
  - File: `tests/test_evolution.py`
  - AC: Both `"th"` and `"TH"` patterns are replaced.

- [ ] **T01-04** [P] Write test `test_natural_drift_empty_text` verifying empty input produces empty output with `diff_summary.replacements == 0`.
  - File: `tests/test_evolution.py`
  - AC: `output_text == ""`, `diff_summary["replacements"] == 0`.

- [ ] **T01-05** [P] Write test `test_natural_drift_no_matching_patterns` with text like `"a b c d"` that has no NATURAL_MAP patterns. Verify output == input.
  - File: `tests/test_evolution.py`
  - AC: `output_text == "a b c d"`, `replacements == 0`.

- [ ] **T01-06** [P] Write test `test_natural_drift_double_replacement_chain` with text containing `"ni"` which maps to `"gn"`, and `"gn"` maps to `"n"`. Verify the double-replacement behavior (document dict ordering).
  - File: `tests/test_evolution.py`
  - AC: Input `"night"` produces output where `"ni"` is first replaced by `"gn"`, then `"gn"` is replaced by `"n"`. Exact output documented and asserted.

- [ ] **T01-07** [P] Write test `test_natural_drift_diff_summary_shape` verifying `diff_summary` contains exactly `{event, replacements, before_chars, after_chars}` with correct types.
  - File: `tests/test_evolution.py`
  - AC: All 4 keys present. `event == "natural_drift"`, `replacements` is int >= 0, `before_chars` and `after_chars` are ints.

### S03-02: Synthetic Mutation Coverage

- [ ] **T02-01** [P] Write test `test_synthetic_mutation_rate_zero` with `mutation_rate=0.0`. Verify zero mutations, output equals input.
  - File: `tests/test_evolution.py`
  - AC: `diff_summary["mutations"] == 0`, `output_text == input_text`.

- [ ] **T02-02** [P] Write test `test_synthetic_mutation_rate_one` with `mutation_rate=1.0`. Verify all alphabetic words are replaced with GLYPH_POOL glyphs.
  - File: `tests/test_evolution.py`
  - AC: No original alphabetic words remain in output. All replacements are from `GLYPH_POOL`.

- [ ] **T02-03** [P] Write parametrized test `test_synthetic_mutation_invalid_rate` with rates `[-0.1, 1.5, 2.0, -1.0]`. Verify `ValueError` for each.
  - File: `tests/test_evolution.py`
  - AC: `pytest.raises(ValueError, match="mutation_rate must be between")` for each.

- [ ] **T02-04** [P] Write test `test_synthetic_mutation_empty_text` verifying empty output with `mutations=0`.
  - File: `tests/test_evolution.py`
  - AC: `output_text == ""`, `mutations == 0`.

- [ ] **T02-05** [P] Write test `test_synthetic_mutation_deterministic` verifying same seed + same text produces identical output across 3 calls.
  - File: `tests/test_evolution.py`
  - AC: All 3 outputs identical.

- [ ] **T02-06** [P] Write test `test_synthetic_mutation_default_rate` verifying that omitting `mutation_rate` defaults to 0.08.
  - File: `tests/test_evolution.py`
  - AC: Validated payload has `mutation_rate == 0.08`.

- [ ] **T02-07** [P] Write test `test_synthetic_mutation_diff_summary_shape` verifying `{event, mutations, before_chars, after_chars}`.
  - File: `tests/test_evolution.py`
  - AC: `event == "synthetic_mutation"`, all ints.

### S03-03: Phase Shift Coverage

- [ ] **T03-01** [P] Write test `test_phase_shift_expansion_inserts_mythic` verifying "mythic" is inserted into expanded text.
  - File: `tests/test_evolution.py`
  - AC: `"mythic" in output_text.lower()`.

- [ ] **T03-02** [P] Write test `test_phase_shift_peak_uppercase` verifying peak phase uppercases entire text when intensity <= 1.5.
  - File: `tests/test_evolution.py`
  - AC: `output_text == input_text.upper()` (no MYTHIC insertions at default acceleration=1.0).

- [ ] **T03-03** [P] Write test `test_phase_shift_peak_high_intensity_mythic` with `acceleration=3.0` verifying "MYTHIC" is inserted alongside uppercase.
  - File: `tests/test_evolution.py`
  - AC: `"MYTHIC" in output_text`, `output_text == output_text.upper()` (all uppercase).

- [ ] **T03-04** [P] Write test `test_phase_shift_compression_vowel_removal` verifying vowel count decreases after compression.
  - File: `tests/test_evolution.py`
  - AC: Vowel count in output < vowel count in input.

- [ ] **T03-05** [P] Write test `test_phase_shift_rebirth_song_birth` verifying `"SONG-BIRTH"` is appended and vowels are removed.
  - File: `tests/test_evolution.py`
  - AC: `"SONG-BIRTH" in output_text`, vowel count in output (excluding SONG-BIRTH suffix) < input.

- [ ] **T03-06** [P] Write parametrized test `test_phase_shift_invalid_phase` with phases `["unknown", "EXPANSION", "   ", ""]`. Verify ValueError for each.
  - File: `tests/test_evolution.py`
  - AC: `pytest.raises(ValueError, match="phase must be one of")`.

- [ ] **T03-07** [P] Write test `test_phase_shift_acceleration_capping` verifying intensity is capped at 5.0 for expansion/peak and floored at 0.2 for compression/rebirth.
  - File: `tests/test_evolution.py`
  - AC: With acceleration=100.0: expansion intensity <= 5.0, compression intensity >= 0.2. Values visible in `diff_summary["intensity"]`.

- [ ] **T03-08** [P] Write test `test_phase_shift_diff_summary_shape` verifying `{event, phase, acceleration, intensity, before_chars, after_chars}`.
  - File: `tests/test_evolution.py`
  - AC: All 6 keys present with correct types.

- [ ] **T03-09** [P] Write test `test_phase_shift_deterministic` with fixed seed across all 4 phases. Verify repeated calls produce identical outputs.
  - File: `tests/test_evolution.py`
  - AC: For each phase, 2 identical calls produce identical output_text.

### S03-04: Glyph Fusion Coverage

- [ ] **T04-01** [P] Write test `test_glyph_fusion_basic` with text `"AEGIS"`, `left="A"`, `right="E"`, `fused="AE"`. Verify `"AE"` replaces `"AE"` and fusions count is correct.
  - File: `tests/test_evolution.py`
  - AC: `output_text` contains `"AE"` where `"AE"` was, `diff_summary["fusions"] >= 1`.

- [ ] **T04-02** [P] Write test `test_glyph_fusion_case_sensitive` verifying `left="a"`, `right="e"` does NOT match `"AE"` in text.
  - File: `tests/test_evolution.py`
  - AC: `diff_summary["fusions"] == 0` when text only contains uppercase `"AE"`.

- [ ] **T04-03** [P] Write test `test_glyph_fusion_multiple_occurrences` with text containing 3 instances of the pair. Verify `fusions == 3`.
  - File: `tests/test_evolution.py`
  - AC: `diff_summary["fusions"] == 3`.

- [ ] **T04-04** [P] Write test `test_glyph_fusion_no_match` with text that does not contain the pair. Verify `fusions == 0`, output unchanged.
  - File: `tests/test_evolution.py`
  - AC: `output_text == input_text`, `fusions == 0`.

- [ ] **T04-05** [P] Write parametrized test `test_glyph_fusion_empty_params` for empty `left`, empty `right`, and empty `fused`. Verify ValueError for each.
  - File: `tests/test_evolution.py`
  - AC: `pytest.raises(ValueError, match="non-empty")`.

- [ ] **T04-06** [P] Write test `test_glyph_fusion_empty_text` verifying empty output with `fusions=0`.
  - File: `tests/test_evolution.py`
  - AC: `output_text == ""`, `fusions == 0`.

- [ ] **T04-07** [P] Write test `test_glyph_fusion_diff_summary_shape` verifying `{event, fusions, pair, fused, before_chars, after_chars}`.
  - File: `tests/test_evolution.py`
  - AC: All 6 keys present. `pair == "AE"`, `fused == "AE"`.

### S03-05: Branching Mechanics

- [ ] **T05-01** [P] Write integration test `test_root_branch_creation` that creates a branch from a root document via `evolve_branch()`. Verify `parent_branch_id=None`, `branch_version=1`, `root_document_id` matches, `name="branch-natural_drift"`.
  - File: `tests/test_evolution.py`
  - AC: All branch fields match expected values.

- [ ] **T05-02** [P] Write integration test `test_child_branch_inherits_root_doc` that creates a parent branch then a child branch. Verify child has `root_document_id` inherited from parent, `branch_version=parent+1`.
  - File: `tests/test_evolution.py`
  - AC: `child.root_document_id == parent.root_document_id`, `child.branch_version == 2`.

- [ ] **T05-03** [S] [Story T05-02] Write integration test `test_grandchild_lineage_depth_3` that creates root -> child -> grandchild. Verify `_lineage()` returns 3 branches in correct order (root first).
  - File: `tests/test_evolution.py`
  - AC: Lineage length is 3. First element is root (no parent), last is grandchild.

- [ ] **T05-04** [P] Write test `test_nonexistent_parent_branch_raises` with a fake UUID as `parent_branch_id`. Verify ValueError.
  - File: `tests/test_evolution.py`
  - AC: `pytest.raises(ValueError, match="Parent branch .* not found")`.

- [ ] **T05-05** [P] Write test `test_missing_root_document_raises` with neither `parent_branch_id` nor `root_document_id`. Verify ValueError.
  - File: `tests/test_evolution.py`
  - AC: `pytest.raises(ValueError, match="root_document_id is required")`.

- [ ] **T05-06** [P] Write test `test_nonexistent_root_document_raises` with a fake UUID as `root_document_id`. Verify ValueError.
  - File: `tests/test_evolution.py`
  - AC: `pytest.raises(ValueError, match="Root document .* not found")`.

- [ ] **T05-07** [P] Write test `test_branch_mode_stored_uppercase` that creates a branch with `mode="public"` (lowercase). Verify `Branch.mode == "PUBLIC"`.
  - File: `tests/test_evolution.py`
  - AC: Stored mode is uppercase regardless of input case.

### S03-06: Event Recording & Hash Determinism

- [ ] **T06-01** [P] Write test `test_event_hash_determinism` that creates two branches from the same document with identical event type/payload. Verify the two `BranchEvent.event_hash` values are different (because `branch_id` differs in the hash input).
  - File: `tests/test_evolution.py`
  - AC: `event1.event_hash != event2.event_hash` (different branch IDs).

- [ ] **T06-02** [P] Write test `test_event_hash_computation` that manually computes `sha256(branch_id:event_index:event_type:json(payload):text_hash)` and compares to the stored `event_hash`.
  - File: `tests/test_evolution.py`
  - AC: Manually computed hash matches `event.event_hash` exactly.

- [ ] **T06-03** [P] Write test `test_payload_schema_version_is_v2` verifying every created `BranchEvent` has `payload_schema_version == "v2"`.
  - File: `tests/test_evolution.py`
  - AC: `event.payload_schema_version == "v2"`.

- [ ] **T06-04** [P] Write test `test_result_snapshot_preview_truncated` with text > 500 chars. Verify `result_snapshot["preview"]` is exactly 500 chars.
  - File: `tests/test_evolution.py`
  - AC: `len(event.result_snapshot["preview"]) == 500`.

- [ ] **T06-05** [P] Write test `test_event_index_sequential` that creates 3 events on the same branch lineage. Verify event indices are 1, 1, 1 (one per branch, since each evolve creates a new branch).
  - File: `tests/test_evolution.py`
  - AC: Each BranchEvent in the lineage has `event_index == 1` (since each branch gets its own events).

### S03-07: Optimistic Concurrency

- [ ] **T07-01** [P] Write integration test `test_optimistic_concurrency_passes` that creates a parent branch, counts its lineage events, then evolves with `expected_parent_event_index=correct_count`. Verify success.
  - File: `tests/test_evolution.py`
  - AC: No exception raised. New branch created.

- [ ] **T07-02** [P] Write integration test `test_optimistic_concurrency_violation` that creates a parent branch, then evolves with `expected_parent_event_index=999`. Verify ValueError with "Optimistic concurrency violation".
  - File: `tests/test_evolution.py`
  - AC: `pytest.raises(ValueError, match="Optimistic concurrency violation")`.

- [ ] **T07-03** [P] Write test `test_optimistic_concurrency_omitted` verifying that omitting `expected_parent_event_index` from payload skips the check entirely.
  - File: `tests/test_evolution.py`
  - AC: No exception regardless of actual lineage count.

### S03-08: Auto-Checkpointing

- [ ] **T08-01** [S] Write integration test `test_checkpoint_created_at_10th_event` that creates a chain of 10 sequential branches (each parenting the next). Verify a `BranchCheckpoint` exists with `event_index=10`.
  - File: `tests/test_evolution.py`
  - AC: Exactly 1 checkpoint at lineage event 10. Query `BranchCheckpoint` table confirms.

- [ ] **T08-02** [S] [Story T08-01] Write test `test_checkpoint_not_at_9_or_11` verifying no checkpoints at lineage event counts 9 and 11 (only at multiples of 10).
  - File: `tests/test_evolution.py`
  - AC: After 9 events, 0 checkpoints. After 11 events, 1 checkpoint (at 10).

- [ ] **T08-03** [S] [Story T08-01] Write test `test_checkpoint_decompression_roundtrip` that reads the checkpoint's `snapshot_compressed`, decompresses via `base64.b64decode()` + `zlib.decompress()` + `json.loads()`, and verifies the result matches the branch's `state_snapshot`.
  - File: `tests/test_evolution.py`
  - AC: Decompressed JSON equals the branch's `state_snapshot` at checkpoint time.

- [ ] **T08-04** [S] [Story T08-01] Write test `test_checkpoint_hash_matches_text` verifying `BranchCheckpoint.snapshot_hash` equals `sha256(current_text)` of the branch at that event.
  - File: `tests/test_evolution.py`
  - AC: `checkpoint.snapshot_hash == sha256(branch.state_snapshot["current_text"])`.

### S03-09: Replay & Timeline

- [ ] **T09-01** [P] Write integration test `test_replay_event_count_matches` that creates 3 sequential branches and replays the last one. Verify `event_count == 3`.
  - File: `tests/test_evolution.py`
  - AC: `replay["event_count"] == 3`.

- [ ] **T09-02** [P] Write integration test `test_timeline_event_order` that creates a chain of 3 branches with different event types. Get timeline for the last branch. Verify events are ordered root-first.
  - File: `tests/test_evolution.py`
  - AC: `events[0]` is from the root branch, `events[2]` is from the leaf branch. Event types match creation order.

- [ ] **T09-03** [P] Write integration test `test_replay_hash_matches_state` that replays a branch and verifies `text_hash` matches the branch's `state_snapshot.text_hash`.
  - File: `tests/test_evolution.py`
  - AC: `replay["text_hash"] == branch.state_snapshot["text_hash"]`.

- [ ] **T09-04** [P] Write test `test_timeline_nonexistent_branch` verifying ValueError for a fake branch ID.
  - File: `tests/test_evolution.py`
  - AC: `pytest.raises(ValueError, match="Branch .* not found")`.

- [ ] **T09-05** [P] Write integration test `test_replay_determinism` that replays the same branch twice and verifies identical `text_hash` both times.
  - File: `tests/test_evolution.py`
  - AC: Both replays produce identical `text_hash` and `preview`.

### S03-10: Branch Comparison

- [ ] **T10-01** [P] Write integration test `test_compare_identical_branches` that creates two branches with the same event type, seed, and root document. Compare them. Verify `distance == 0`, `same == True`.
  - File: `tests/test_evolution.py`
  - AC: `distance == 0`, `same == True`, `left_hash == right_hash`.

- [ ] **T10-02** [P] Write integration test `test_compare_different_branches` that creates two branches with different event types from the same root. Verify `distance > 0`, `same == False`.
  - File: `tests/test_evolution.py`
  - AC: `distance > 0`, `same == False`, `left_hash != right_hash`.

- [ ] **T10-03** [P] Write unit test `test_simple_distance_calculation` that calls `_simple_distance()` directly with known strings. E.g., `("abc", "axc")` -> distance=1, `("abc", "abcde")` -> distance=2.
  - File: `tests/test_evolution.py`
  - AC: Exact distance values match hand-computed expectations.

- [ ] **T10-04** [P] Write unit test `test_simple_distance_empty_strings` verifying `_simple_distance("", "") == 0` and `_simple_distance("abc", "") == 3`.
  - File: `tests/test_evolution.py`
  - AC: Exact values.

### S03-11: Remix Strategy Hardening

- [ ] **T11-01** [P] Write unit test `test_interleave_unequal_lengths` with source=3 words, target=5 words. Verify all 8 words appear in output.
  - File: `tests/test_remix.py` (new)
  - AC: Output contains all source words and all target words. Length is 8 space-separated tokens.

- [ ] **T11-02** [P] Write unit test `test_thematic_blend_output_sentence_count` verifying output has `max(len(source_sentences), len(target_sentences))` sentences.
  - File: `tests/test_remix.py`
  - AC: Sentence count in output matches expected max.

- [ ] **T11-03** [P] Write unit test `test_temporal_layer_overlay_markers` verifying `"[temporal overlay]"` appears in output.
  - File: `tests/test_remix.py`
  - AC: At least one `"[temporal overlay]"` prefix in output.

- [ ] **T11-04** [P] Write unit test `test_glyph_collide_output_length` verifying output length equals `min(max(len(source), len(target)), 2000)` non-space characters.
  - File: `tests/test_remix.py`
  - AC: Exact character count matches formula.

- [ ] **T11-05** [P] Write unit test `test_glyph_collide_cap_2000` with two 3000-character inputs. Verify output is exactly 2000 non-space characters.
  - File: `tests/test_remix.py`
  - AC: `len(output) == 2000`.

- [ ] **T11-06** [P] Write unit test `test_remix_empty_source_raises` verifying `ValueError("Both source and target must resolve")` when source text is empty.
  - File: `tests/test_remix.py`
  - AC: `pytest.raises(ValueError, match="non-empty text")`.

- [ ] **T11-07** [P] Write unit test `test_remix_unknown_strategy_raises` with `strategy="unknown"`. Verify `ValueError`.
  - File: `tests/test_remix.py`
  - AC: `pytest.raises(ValueError, match="Unknown remix strategy")`.

- [ ] **T11-08** [P] Write unit test `test_remix_all_strategies_deterministic` verifying all 4 strategies produce identical output for identical inputs and seeds across 2 calls.
  - File: `tests/test_remix.py`
  - AC: For each strategy, two calls with same inputs produce identical output.

### S03-12: API Route Enforcement

- [ ] **T12-01** [P] Create `tests/test_evolution_api.py` with fixtures inheriting from `conftest.py` (`client`, `auth_headers`, `sample_corpus`).
  - File: `tests/test_evolution_api.py`
  - AC: File created, fixtures imported, basic structure in place.

- [ ] **T12-02** [P] Write test `test_evolve_branch_requires_operator` via `POST /api/v1/evolve/branch` with viewer key. Verify 403.
  - File: `tests/test_evolution_api.py`
  - AC: `resp.status_code == 403`.

- [ ] **T12-03** [P] Write test `test_evolve_branch_requires_auth` with no API key. Verify 401.
  - File: `tests/test_evolution_api.py`
  - AC: `resp.status_code == 401`.

- [ ] **T12-04** [P] Write test `test_evolve_branch_raw_mode_enforcement` with operator key (no raw access) and `mode="RAW"`. Verify 403.
  - File: `tests/test_evolution_api.py`
  - AC: `resp.status_code == 403`, detail mentions mode.

- [ ] **T12-05** [P] Write test `test_evolve_branch_invalid_event_type` with `event_type="invalid"`. Verify 400.
  - File: `tests/test_evolution_api.py`
  - AC: `resp.status_code == 400`, detail mentions "Unsupported event_type".

- [ ] **T12-06** [P] Write test `test_evolve_branch_invalid_mutation_rate` with `mutation_rate=5.0`. Verify 400.
  - File: `tests/test_evolution_api.py`
  - AC: `resp.status_code == 400`, detail mentions "mutation_rate".

- [ ] **T12-07** [P] Write test `test_branches_list_limit_param` verifying `limit=2` returns at most 2 branches.
  - File: `tests/test_evolution_api.py`
  - AC: `len(resp.json()["branches"]) <= 2`.

- [ ] **T12-08** [P] Write test `test_timeline_nonexistent_branch_404` via `GET /api/v1/branches/fake-uuid/timeline`. Verify 404.
  - File: `tests/test_evolution_api.py`
  - AC: `resp.status_code == 404`.

- [ ] **T12-09** [P] Write test `test_replay_nonexistent_branch_404` via `POST /api/v1/branches/fake-uuid/replay`. Verify 404.
  - File: `tests/test_evolution_api.py`
  - AC: `resp.status_code == 404`.

- [ ] **T12-10** [P] Write test `test_compare_nonexistent_branch_404` via `GET /api/v1/branches/fake-uuid/compare/other-fake`. Verify 404.
  - File: `tests/test_evolution_api.py`
  - AC: `resp.status_code == 404`.

- [ ] **T12-11** [P] Write test `test_remix_requires_operator` via `POST /api/v1/remix` with viewer key. Verify 403.
  - File: `tests/test_evolution_api.py`
  - AC: `resp.status_code == 403`.

- [ ] **T12-12** [P] Write full happy-path integration test `test_evolve_timeline_replay_compare_flow` that:
  1. Ingests a document
  2. Creates branch A (natural_drift)
  3. Creates branch B from branch A (synthetic_mutation)
  4. Gets timeline for B (verify 2 events)
  5. Replays B (verify event_count=2)
  6. Creates branch C (phase_shift from same root)
  7. Compares B vs C (verify distance > 0)
  - File: `tests/test_evolution_api.py`
  - AC: All assertions pass. Full lifecycle covered.

---

## P2: Reverse Drift & Multi-Evolve

### S03-13: Reverse Drift Event Type

- [x] **T13-01** [P] Add `"reverse_drift"` case to `_validate_event_payload()`: accept `{seed}` with default `seed=0`.
  - File: `src/nexus_babel/services/evolution.py`
  - AC: `_validate_event_payload("reverse_drift", {})` returns `{"seed": 0}`. Unknown event type still raises ValueError.

- [x] **T13-02** [S] [Story T13-01] Add `"reverse_drift"` case to `_apply_event()`: iterate `REVERSE_NATURAL_MAP`, apply `re.sub(old, new, text, flags=re.IGNORECASE)` for each entry. Return `DriftResult` with `{event: "reverse_drift", reversals, before_chars, after_chars}`.
  - File: `src/nexus_babel/services/evolution.py`
  - AC: `_apply_event("fis", "reverse_drift", {"seed": 0}).output_text` contains `"phs"` (reverse of `"ph"->"f"` is `"f"->"ph"`). Count of replacements tracked.

- [x] **T13-03** [S] [Story T13-02] Write test `test_reverse_drift_basic` applying `reverse_drift` to text that was previously natural-drifted. Verify at least some original patterns are restored.
  - File: `tests/test_evolution.py`
  - AC: Apply natural_drift to `"the"` (produces `"THORN e"`), then reverse_drift -> contains `"th"`.

- [x] **T13-04** [P] Write test `test_reverse_drift_lossy` demonstrating that reverse drift is lossy: text containing legitimate `"f"` gets converted to `"ph"`.
  - File: `tests/test_evolution.py`
  - AC: Input `"fun"` -> output `"phun"`. Documented as expected behavior.

- [x] **T13-05** [P] Write test `test_reverse_drift_12_entries` verifying all 12 `REVERSE_NATURAL_MAP` entries are applied.
  - File: `tests/test_evolution.py`
  - AC: Parametrized test for each reverse mapping. 12 cases.

### S03-14: Multi-Evolve Batch Endpoint

- [x] **T14-01** [P] Add `MultiEvolveRequest` and `MultiEvolveResponse` schemas to `schemas.py`.
  - File: `src/nexus_babel/schemas.py`
  - AC: Both models importable. Request has `root_document_id`, `parent_branch_id`, `events` (list), `mode`. Response has `branch_ids`, `final_branch_id`, `event_count`, `final_text_hash`, `final_preview`.

- [x] **T14-02** [S] [Story T14-01] Add `multi_evolve()` method to `EvolutionService` that loops through `events`, calling `evolve_branch()` for each, threading `parent_branch_id` from the result of each call.
  - File: `src/nexus_babel/services/evolution.py`
  - AC: Returns list of `(Branch, BranchEvent)` tuples. Each successive call uses previous branch as parent.

- [x] **T14-03** [S] [Story T14-02] Add `POST /api/v1/evolve/multi` route in `routes.py` with `operator` auth.
  - File: `src/nexus_babel/api/routes.py`
  - AC: Route registered, accepts `MultiEvolveRequest`, returns `MultiEvolveResponse`.

- [x] **T14-04** [S] [Story T14-03] Write integration test `test_multi_evolve_chain` that submits 4 events in a batch. Verify 4 branch IDs returned, `final_branch_id` is the last, `event_count == 4`.
  - File: `tests/test_evolution.py`
  - AC: All assertions pass. Final preview is the result of all 4 transformations applied sequentially.

- [x] **T14-05** [P] Write test `test_multi_evolve_empty_events_raises` with empty events list. Verify 400 or ValueError.
  - File: `tests/test_evolution.py`
  - AC: Error raised for empty event list.

- [x] **T14-06** [P] Write test `test_multi_evolve_rollback_on_failure` where the 3rd event has an invalid payload. Verify no branches are created (transaction rollback).
  - File: `tests/test_evolution.py`
  - AC: After failed call, no new branches exist in DB.

### S03-15: Checkpoint-Accelerated Replay

- [x] **T15-01** [P] Modify `get_timeline()` to check for the most recent `BranchCheckpoint` in the lineage before replaying from root.
  - File: `src/nexus_babel/services/evolution.py`
  - AC: When a checkpoint exists, replay starts from checkpoint state. When no checkpoint exists, full replay from root (backward compatible).

- [x] **T15-02** [S] [Story T15-01] Write test `test_checkpoint_accelerated_replay_correctness` that creates 20 sequential branches (checkpoint at 10 and 20), replays the 20th, and verifies the result matches a full replay from root.
  - File: `tests/test_evolution.py`
  - AC: Checkpointed replay `text_hash` == full replay `text_hash`.

- [x] **T15-03** [S] [Story T15-01] Write benchmark test `test_checkpoint_replay_faster_than_full` comparing replay time for a 50-event lineage with and without checkpoint acceleration.
  - File: `tests/test_evolution.py`
  - AC: Checkpointed replay is faster. Mark `@pytest.mark.slow`.

---

## P3: Phase State & Branch Merging

### S03-16: Phase State Manager

- [ ] **T16-01** [P] Design `PhaseStateManager` class that evaluates phase transition conditions based on `state_snapshot` metrics.
  - File: `src/nexus_babel/services/phase_manager.py` (new)
  - AC: Class with `evaluate_transition(branch, current_phase) -> Optional[str]` method.

- [ ] **T16-02** [S] [Story T16-01] Implement transition rules: expansion->peak (word_count > 2x original), peak->compression (after N peak events), compression->rebirth (vowel_ratio < 0.1), rebirth->expansion (after SONG-BIRTH).
  - File: `src/nexus_babel/services/phase_manager.py`
  - AC: Each transition fires under correct conditions. Unit tests for each transition.

- [ ] **T16-03** [S] [Story T16-02] Integrate `PhaseStateManager` into `evolve_branch()`: after applying event, evaluate transition and optionally auto-emit a `phase_shift` event.
  - File: `src/nexus_babel/services/evolution.py`
  - AC: When auto-transition fires, a second BranchEvent is created with `event_type="phase_shift"`. Rate-limited to 1 auto-transition per call.

- [ ] **T16-04** [S] [Story T16-03] Write integration test `test_auto_phase_transition` that evolves a branch through expansion (adding many words) until it auto-transitions to peak.
  - File: `tests/test_phase_manager.py` (new)
  - AC: After sufficient expansion events, the branch's phase automatically shifts to "peak".

### S03-17: Branch Merging

- [x] **T17-01** [P] Implement `_find_lca(session, left_branch, right_branch)` that finds the lowest common ancestor by walking both lineages and finding the intersection.
  - File: `src/nexus_babel/services/evolution.py`
  - AC: Returns the LCA Branch or None if branches share no common ancestor.

- [x] **T17-02** [S] [Story T17-01] Implement `merge_branches(session, left_id, right_id, strategy)` that replays both branches, applies merge strategy (`left_wins`, `right_wins`, `interleave`), creates a new branch.
  - File: `src/nexus_babel/services/evolution.py`
  - AC: New branch created with `event_type="merge"`. Both parent IDs referenced in `event_payload`.

- [x] **T17-03** [S] [Story T17-02] Add `POST /api/v1/branches/merge` route with operator auth.
  - File: `src/nexus_babel/api/routes.py`
  - AC: Route accepts `{left_branch_id, right_branch_id, strategy, mode}`, returns new branch info.

- [x] **T17-04** [S] [Story T17-03] Write integration test `test_branch_merge_interleave` that creates two divergent branches from the same root, merges them with `interleave` strategy, and verifies the result contains text from both.
  - File: `tests/test_evolution.py`
  - AC: Merged text contains words/phrases from both left and right branches.

---

## P4: Sung-Language & Visualization

### S03-18: Sung-Language Emergence

- [ ] **T18-01** [P] Implement singability analysis: detect harsh consonant clusters (3+ consonants without vowels), compute consonant-density and vowel-ratio metrics.
  - File: `src/nexus_babel/services/evolution.py` or `src/nexus_babel/services/sung_language.py` (new)
  - AC: `analyze_singability(text)` returns `{consonant_clusters, vowel_ratio, singability_score}`.

- [ ] **T18-02** [S] [Story T18-01] Implement vowel bridge insertion: add schwa-like vowels between harsh consonant clusters to improve singability.
  - File: `src/nexus_babel/services/sung_language.py`
  - AC: Text with consonant cluster "strng" becomes "stureng" or similar.

- [ ] **T18-03** [S] [Story T18-02] Implement rhythmic pattern application: iambic, trochaic, dactylic patterns applied via word-spacing and syllable emphasis markers.
  - File: `src/nexus_babel/services/sung_language.py`
  - AC: Output includes rhythmic markers. Pattern is configurable.

- [ ] **T18-04** [S] [Story T18-03] Integrate sung-language transform into rebirth phase: after 3+ rebirth events in a lineage, automatically apply singability transform.
  - File: `src/nexus_babel/services/evolution.py`
  - AC: Third rebirth event in a lineage produces sung-language output. Test with 4-event chain.

### S03-19: Evolution Visualization

- [x] **T19-01** [P] Add `GET /api/v1/branches/{id}/visualization` endpoint returning graph data (nodes=events, edges=parent links, metadata=phase/type).
  - File: `src/nexus_babel/api/routes.py`
  - AC: Response is a JSON graph structure compatible with D3.js force layout.

- [ ] **T19-02** [S] [Story T19-01] Implement `/app/timeline` frontend view: React component that fetches visualization data and renders a horizontal timeline with D3.js.
  - File: Frontend files (TBD)
  - AC: Timeline renders with event nodes, text diff previews, phase coloring.

- [ ] **T19-03** [S] [Story T19-02] Add branch tree visualization showing parent-child relationships across multiple branches.
  - File: Frontend files (TBD)
  - AC: Tree layout shows all branches from a root document with their lineage.

---

## Summary

| Priority | Stories | Tasks | Status |
|----------|---------|-------|--------|
| P1 | S03-01 through S03-12 | 72 tasks | Not started |
| P2 | S03-13 through S03-15 | 14 tasks | Not started |
| P3 | S03-16, S03-17 | 8 tasks | Not started |
| P4 | S03-18, S03-19 | 7 tasks | Not started |
| **Total** | **19 stories** | **101 tasks** | |

### Parallel Execution Groups (P1)

All P1 stories are independent. Within each story, tasks marked `[P]` can be parallelized:

- **Batch 1 (all [P] tasks):** T01-01 through T01-07, T02-01 through T02-07, T03-01 through T03-09, T04-01 through T04-07, T05-01/02/04/05/06/07, T06-01 through T06-05, T07-01 through T07-03, T08-01 (standalone), T09-01 through T09-05, T10-01 through T10-04, T11-01 through T11-08, T12-01 through T12-12
- **Batch 2 (sequential tasks):** T05-03 (depends on T05-02), T08-02 through T08-04 (depend on T08-01)
- **Batch 3 (P2 sequential chains):** T13-01 -> T13-02 -> T13-03, T14-01 -> T14-02 -> T14-03 -> T14-04, T15-01 -> T15-02 -> T15-03

### Critical Path

```
P1 Batch 1 (parallel)
  |
  v
P1 Batch 2 (sequential)
  |
  v
P2 (reverse drift + multi-evolve + checkpoint replay, partially parallel)
  |
  v
P3 (phase state + merge, partially parallel)
  |
  v
P4 (sung-language + visualization)
```

Estimated P1 effort: 72 tasks, ~8-12 hours with parallelization.
Estimated P2 effort: 14 tasks, ~4-6 hours.
Estimated P3 effort: 8 tasks, ~4-6 hours.
Estimated P4 effort: 7 tasks, ~6-10 hours (frontend work).
