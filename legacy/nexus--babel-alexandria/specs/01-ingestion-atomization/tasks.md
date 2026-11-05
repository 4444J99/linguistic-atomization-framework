# Ingestion & Atomization -- Task List

## Phase 1: Setup

### T-SETUP-001: Create domain test file [P]

Create `tests/test_ingestion_atomization.py` with domain-specific fixtures and imports. Reuse `conftest.py` fixtures (`client`, `auth_headers`, `sample_corpus`). Add extended corpus fixtures for edge cases (Unicode filenames, large text, multi-page PDF, MP3/FLAC stubs).

**Files**: `tests/test_ingestion_atomization.py`, `tests/conftest.py`
**Acceptance**: File exists, `pytest tests/test_ingestion_atomization.py -v` passes with 0 tests collected (skeleton).

### T-SETUP-002: Verify existing test coverage baseline [P]

Run `pytest tests/test_mvp.py -v` and document which ingestion tests pass. Identify any regressions. This establishes the baseline for all subsequent work.

**Files**: `tests/test_mvp.py`
**Acceptance**: All 13 MVP tests pass. Coverage report for `services/ingestion.py`, `services/text_utils.py`, `services/glyph_data.py`, `services/canonicalization.py` captured.

### T-SETUP-003: Add ruff and mypy configuration [P]

No linter or type checker is configured in `pyproject.toml`. Add `[tool.ruff]` and `[tool.mypy]` sections targeting `src/nexus_babel/services/ingestion.py`, `text_utils.py`, `glyph_data.py`, `canonicalization.py`.

**Files**: `pyproject.toml`
**Acceptance**: `ruff check src/nexus_babel/services/ingestion.py src/nexus_babel/services/text_utils.py src/nexus_babel/services/glyph_data.py src/nexus_babel/services/canonicalization.py` passes. `mypy` type-checks the same files with 0 errors.

---

## Phase 2: Foundational -- Schema & Migration Prerequisites

### T-FOUND-001: Add `atom_filename` column to Atom model [Story: US-015]

Add `atom_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)` to the `Atom` model in `models.py`. This column will store the deterministic canonical filename once the naming helper is implemented.

**Files**: `src/nexus_babel/models.py`
**Acceptance**: Column defined. Migration not yet created (see T-FOUND-002).

### T-FOUND-002: Create Alembic migration for atom_filename [Story: US-015]

Generate Alembic migration `20260223_0003_atom_filename` adding `atom_filename` column to `atoms` table. Verify upgrade and downgrade both work on SQLite and PostgreSQL.

**Files**: `alembic/versions/20260223_0003_atom_filename.py`
**Acceptance**: `make db-upgrade` applies cleanly. `alembic downgrade -1` removes the column.

### T-FOUND-003: Add `atom_track` field to Document provenance [Story: US-014]

Define the track preset mapping in `text_utils.py`:
```python
ATOM_TRACK_PRESETS = {
    "literary": ["word", "sentence", "paragraph"],
    "glyphic_seed": ["glyph-seed", "syllable"],
    "full": ATOM_LEVELS,  # default
}
```
No DB migration needed -- track name is stored in the existing `provenance` JSON field.

**Files**: `src/nexus_babel/services/text_utils.py`
**Acceptance**: Import works, `ATOM_TRACK_PRESETS` accessible.

---

## Phase 3: User Stories -- P1 Verification & Hardening

### T-P1-001: Add explicit atomization unit tests [Story: US-002] [P]

Test `atomize_text_rich()` directly:
- Verify 5 levels returned with correct keys
- Verify glyph-seed objects are `GlyphSeed` instances with all 8 fields populated
- Verify whitespace is excluded from glyph-seeds
- Verify syllable count >= word count (each word produces >=1 syllable)
- Verify sentence/paragraph splitting on known input

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-002: Add syllabification edge case tests [Story: US-002] [P]

Test `syllabify()` with:
- Empty string -> `[]`
- Single character -> `["a"]`
- Two characters -> `["ab"]`
- All-consonant word -> `["nth"]` (single syllable)
- All-vowel word -> `["oui"]`
- Long compound word -> verify split count
- Unicode word (accented chars) -> at least 1 syllable returned
- Known English words: "hello" -> `["hel", "lo"]`, "beautiful" -> verify 3 syllables

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=8 tests, all pass.

### T-P1-003: Add glyph metadata completeness tests [Story: US-003] [P]

Test all 26 letters (A-Z) have:
- Non-empty `phoneme_hint` for both upper and lower case
- Non-empty `historic_forms` list
- Non-empty `visual_mutations` list
- Non-empty `thematic_tags` list (3-5 items)
- Exactly 3 `future_seeds` items

Test non-Latin characters return graceful defaults (empty lists, None phoneme).

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: 26+2 tests, all pass.

### T-P1-004: Add conflict detection edge case tests [Story: US-004] [P]

Test `has_conflict_markers()` with:
- Standard `<<<<<<<` marker -> True
- `=======` marker -> True
- `>>>>>>>` marker -> True
- `|||||||` marker -> True
- Markers not at line start (indented) -> False
- Markers inside code blocks -> True (known limitation, document)
- Clean YAML -> False
- Empty string -> False

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=8 tests, all pass.

### T-P1-005: Add checksum and deduplication tests [Story: US-005]

Test:
- Same file path + same content -> `unchanged` on second ingest
- Same file path + different content -> re-ingested (atoms rebuilt)
- `force=true` -> re-ingested even with same checksum
- `sha256_file()` on known content produces expected hash

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=4 tests, all pass.

### T-P1-006: Add projection ledger verification tests [Story: US-006]

Test:
- After ingestion, `ProjectionLedger` rows exist for every atom
- Status is `"projected"` when hypergraph succeeds (local cache)
- `atom_count == graph_projected_atom_count` on the document

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=3 tests, all pass.

### T-P1-007: Add canonicalization isolation tests [Story: US-007]

Test:
- Two files with same stem, different extensions -> sibling variants created
- Three files with same stem -> pairwise variants (6 rows for 3 docs)
- Files with different stems -> no variant links
- `_normalize_stem()` on edge cases: hyphens, underscores, special chars, Unicode

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-008: Add cross-modal linking tests [Story: US-008]

Test:
- `sample.md` + `sample.png` -> cross_modal_links in both provenances
- `sample.md` + `sample.wav` -> links include audio modality
- `doc_a.md` + `doc_b.png` (different stems) -> no cross-modal links
- Verify link structure includes `target_document_id`, `target_modality`, anchors

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=4 tests, all pass.

### T-P1-009: Add modality detection tests [P]

Test `_detect_modality()` (or equivalent) for every supported extension:
- `.md`, `.txt`, `.yaml`, `.yml` -> `"text"`
- `.pdf` -> `"pdf"`
- `.png`, `.jpg`, `.jpeg`, `.webp` -> `"image"`
- `.wav`, `.mp3`, `.flac` -> `"audio"`
- `.docx`, `.unknown` -> `"binary"`

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=12 tests, all pass.

### T-P1-010: Add seed corpus registry tests [Story: US-011]

Test:
- `GET /api/v1/corpus/seeds` returns 5 entries with correct titles and authors
- All entries have valid Gutenberg URLs
- `atomization_status` is `"not_provisioned"` for unprovisioned seeds
- Invalid seed title in `POST /corpus/seed` returns error

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=4 tests, all pass.

### T-P1-011: Add path traversal security tests [Story: US-013] [P]

Test:
- Absolute path outside corpus_root -> 400
- Relative path with `../` escaping -> 400
- Symlink pointing outside corpus_root -> 400 (if applicable)
- Path within corpus_root -> accepted

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=3 tests, all pass.

---

## Phase 4: User Stories -- P2 Completion

### T-P2-001: Implement dual atomization track presets [Story: US-014]

Add `atom_tracks` key to `parse_options` in `IngestBatchRequest`. Accept a list of track names (`["literary", "glyphic_seed"]`) or `["full"]` (default). Map track names to `atom_levels` via `ATOM_TRACK_PRESETS` (T-FOUND-003). Persist selected track(s) in `document.provenance["atom_track"]`.

**Files**: `src/nexus_babel/services/ingestion.py`, `src/nexus_babel/schemas.py`
**Acceptance**: API accepts `atom_tracks`, response provenance includes track name, atom counts differ by track.

### T-P2-002: Add dual track integration tests [Story: US-014]

Test:
- `atom_tracks=["literary"]` -> only word/sentence/paragraph atoms created
- `atom_tracks=["glyphic_seed"]` -> only glyph-seed/syllable atoms created
- `atom_tracks=["literary", "glyphic_seed"]` -> same as `["full"]` (all 5 levels)
- Default (no `atom_tracks`) -> all 5 levels
- Invalid track name -> 400 error
- Provenance records the track name

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=6 tests, all pass.

### T-P2-003: Implement deterministic atom filename helper [Story: US-015]

Add `generate_atom_filename(document_title, atom_level, ordinal, token_preview, schema_version="v1") -> str` to `text_utils.py`.

Format: `{TITLE}_{LEVEL}_{ORDINAL:06d}_{TOKEN}.txt`
- `TITLE`: Uppercase, spaces -> underscores, non-alphanumeric stripped
- `LEVEL`: Uppercase level name (`GLYPH_SEED`, `SYLLABLE`, `WORD`, `SENTENCE`, `PARAGRAPH`)
- `ORDINAL`: 6-digit zero-padded
- `TOKEN`: First 20 chars of content, normalized (alphanumeric + underscore only), truncated

Collision handling: If duplicate filename exists in the same document, append `_2`, `_3`, etc.

**Files**: `src/nexus_babel/services/text_utils.py`
**Acceptance**: Function exists, unit-tested.

### T-P2-004: Add atom filename unit tests [Story: US-015] [P]

Test:
- Basic word: `generate_atom_filename("The Odyssey", "word", 1, "Sing")` -> `"THE_ODYSSEY_WORD_000001_Sing.txt"` <!-- allow-secret -->
- Unicode token: accented characters stripped/normalized <!-- allow-secret -->
- Punctuation in token: stripped to alphanumeric <!-- allow-secret -->
- Long token: truncated to 20 chars <!-- allow-secret -->
- Same input always produces same output (determinism)
- Sentence level with long preview
- Glyph-seed level with single character

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=7 tests, all pass.

### T-P2-005: Wire atom filename into ingestion pipeline [Story: US-015]

In `_create_atoms()`, call `generate_atom_filename()` and set `atom.atom_filename`. Include `atom_filename_schema_version: "v1"` in `document.provenance`.

**Files**: `src/nexus_babel/services/ingestion.py`
**Acceptance**: After ingestion, every atom has a non-null `atom_filename`. Filenames are deterministic across re-ingestion.

### T-P2-006: Add configurable corpus skip patterns [Story: US-016]

Move the hardcoded skip dirs (`{".git", ".venv", "__pycache__", "object_storage", ".pytest_cache"}`) in `collect_current_corpus_paths()` to a `Settings` field `corpus_skip_dirs`. Default to the current set. Allow override via `NEXUS_CORPUS_SKIP_DIRS` env var.

**Files**: `src/nexus_babel/services/canonicalization.py`, `src/nexus_babel/config.py`
**Acceptance**: Custom skip dirs respected. Default behavior unchanged.

---

## Phase 5: User Stories -- P3 Vision

### T-P3-001: Create atom library export script [Story: US-017]

Create `scripts/export_atom_library.py` that:
1. Connects to the database
2. For each ingested document, creates `{export_root}/{TITLE}/{LEVEL}/` directories
3. Writes each atom as `{atom_filename}` containing the atom content
4. Writes `manifest.json` per document with: `document_id`, `checksum`, `atom_count_by_level`, `export_schema_version`, `created_at`
5. Supports `--document-id` filter and `--export-root` argument
6. Idempotent: skips atoms whose files already exist with matching content

**Files**: `scripts/export_atom_library.py`
**Acceptance**: Script runs, produces filesystem tree, manifest is valid JSON, re-run is idempotent.

### T-P3-002: Add export script tests [Story: US-017]

Test:
- Export of a single document produces correct tree structure
- Manifest atom counts match database
- Re-export is idempotent (no file changes)
- Missing document ID returns error

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: >=4 tests, all pass.

### T-P3-003: Implement ingestion profiles [Story: US-018]

Add `profiles/` directory with YAML profile definitions:
```yaml
# profiles/arc4n-seed.yaml
name: arc4n-seed
description: "ARC4N seed corpus from Project Gutenberg"
seed_titles:
  - "The Odyssey"
  - "Leaves of Grass"
  - "Frankenstein"
atom_tracks: ["full"]
parse_options:
  atomize: true
  force: false
```

Update `scripts/ingest_corpus.py` to accept `--profile <name>` and load the profile. Profile name is recorded in the IngestJob's `request_payload`.

**Files**: `scripts/ingest_corpus.py`, `profiles/arc4n-seed.yaml`
**Acceptance**: `python scripts/ingest_corpus.py --profile arc4n-seed` provisions and ingests the listed seeds.

### T-P3-004: Add image OCR stub integration point [Story: US-020]

Refactor `_extract_image_metadata()` to call an optional `ocr_provider` from the plugin registry. Default provider returns empty spans. Interface: `ocr_provider.extract(path: Path) -> list[dict]` where each dict has `text`, `bbox`, `confidence`.

**Files**: `src/nexus_babel/services/ingestion.py`
**Acceptance**: Plugin point exists. Default behavior unchanged. OCR results, when available, would be stored in `segments.ocr_spans` and concatenated as `extracted_text` for atomization.

### T-P3-005: Add audio transcription stub integration point [Story: US-020]

Refactor `_extract_audio_metadata()` to call an optional `asr_provider` from the plugin registry. Default provider returns empty transcription. Interface: `asr_provider.transcribe(path: Path) -> list[dict]` where each dict has `start`, `end`, `text`, `speaker`, `confidence`.

**Files**: `src/nexus_babel/services/ingestion.py`
**Acceptance**: Plugin point exists. Default behavior unchanged. Transcription results, when available, would be stored in `segments.transcription_segments` and concatenated as `extracted_text` for atomization.

### T-P3-006: Integrate ingestion with async job system [Story: US-021]

Add `execution_mode` to `IngestBatchRequest` (`"sync"` default, `"async"` optional). When `"async"`, submit an `ingest` job to the `Job` queue. The worker calls `ingest_batch()` and updates the job. Progress can be polled via `GET /api/v1/jobs/{id}`.

**Files**: `src/nexus_babel/services/ingestion.py`, `src/nexus_babel/api/routes.py`, `src/nexus_babel/schemas.py`, `src/nexus_babel/worker.py`
**Acceptance**: Async ingestion submits job, worker processes it, final status available via job endpoint.

---

## Phase 6: Cross-Cutting

### T-CROSS-001: Wire ingestion domain tests into CI [P]

Update `.github/workflows/ci-minimal.yml` to run `pytest tests/test_ingestion_atomization.py tests/test_mvp.py -v` as part of the pipeline. Ensure the CI environment has all required dependencies (`pypdf`, etc.).

**Files**: `.github/workflows/ci-minimal.yml`
**Acceptance**: CI runs the test suite and fails on regression.

### T-CROSS-002: Add performance benchmark for seed corpus ingestion

Create `scripts/benchmark_ingestion.py` that:
1. Provisions all 5 seed texts
2. Ingests each, recording wall time and atom counts
3. Prints summary table: `title | file_size | atoms | duration_s`
4. Asserts total duration < 120s on local dev (baseline)

**Files**: `scripts/benchmark_ingestion.py`
**Acceptance**: Script runs end-to-end. Baseline captured.

### T-CROSS-003: Add concurrent ingestion safety test

Test that two simultaneous `ingest_batch` calls for the same file do not produce duplicate atoms or corrupt the document. This may require advisory locking or a serial queue.

**Files**: `tests/test_ingestion_atomization.py`
**Acceptance**: Concurrent ingestion either serializes correctly or returns a clear error. No data corruption.

### T-CROSS-004: Add bulk insert optimization for large documents

Profile `_create_atoms()` for a large text (>100K atoms). If `session.add_all()` + `flush()` is slow, switch to `session.execute(insert(Atom), atom_dicts)` for bulk insert. Benchmark before and after.

**Files**: `src/nexus_babel/services/ingestion.py`
**Acceptance**: Ingestion of a 100K-atom document completes in <10s on local dev.

### T-CROSS-005: Update CLAUDE.md with domain spec references

Add a section to the project CLAUDE.md pointing to the new `specs/01-ingestion-atomization/` directory and summarizing the domain's P1/P2/P3 scope.

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
  T-FOUND-003 ── (no deps, can run in parallel with T-FOUND-001)
  T-FOUND-001 -> T-FOUND-002

Phase 3 (P1 Verification) -- all can run in parallel [P]
  T-P1-001 through T-P1-011 (depend on T-SETUP-001)

Phase 4 (P2 Completion)
  T-FOUND-003 -> T-P2-001 -> T-P2-002
  T-FOUND-001 -> T-FOUND-002 -> T-P2-003 -> T-P2-004
                                          -> T-P2-005 (depends on T-P2-003 + T-FOUND-002)
  T-P2-006 (independent)

Phase 5 (P3 Vision)
  T-P2-005 -> T-P3-001 -> T-P3-002
  T-P3-003 (depends on T-P1-010)
  T-P3-004, T-P3-005 (independent)
  T-P3-006 (depends on T-P1-005)

Phase 6 (Cross-Cutting)
  T-CROSS-001 (depends on Phase 3 completion)
  T-CROSS-002 (depends on T-P1-010)
  T-CROSS-003 (depends on T-P1-005)
  T-CROSS-004 (depends on T-P1-001)
  T-CROSS-005 (no deps)
```

## Summary

| Phase | Tasks | Parallel | Scope |
|-------|-------|----------|-------|
| Phase 1: Setup | 3 | All [P] | Test infrastructure, baseline verification |
| Phase 2: Foundational | 3 | Partial | Schema additions, track presets |
| Phase 3: P1 Verification | 11 | All [P] | Harden existing as-built behavior |
| Phase 4: P2 Completion | 6 | Partial | Dual tracks, deterministic filenames, skip patterns |
| Phase 5: P3 Vision | 6 | Partial | Export pipeline, profiles, OCR/ASR stubs, async |
| Phase 6: Cross-Cutting | 5 | Partial | CI, benchmarks, concurrency, optimization |
| **Total** | **34** | | |
