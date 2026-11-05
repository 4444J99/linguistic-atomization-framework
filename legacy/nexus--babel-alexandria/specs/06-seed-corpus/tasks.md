# Seed Corpus -- Task List

## Phase 1: Setup

### T-SETUP-001: Create domain test file [P]

Create `tests/test_seed_corpus.py` with domain-specific fixtures and imports. Reuse `conftest.py` fixtures (`client`, `auth_headers`, `test_settings`). Add a `seed_corpus_service` fixture that creates a `SeedCorpusService` with `tmp_path / "seeds"` as `seeds_dir`. Add a mock download fixture to avoid network calls in tests.

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: File exists, `pytest tests/test_seed_corpus.py -v` passes with 0 tests collected (skeleton). Mock download fixture patches `urllib.request.urlretrieve`.

### T-SETUP-002: Verify existing seed corpus test coverage baseline [P]

Run `pytest tests/test_mvp.py -v` and document which tests exercise seed corpus functionality (if any). Check `test_ingestion_atomization.py` T-P1-010 (seed registry tests from spec 01) for overlap. Establish the baseline for all subsequent work.

**Files**: `tests/test_mvp.py`, `tests/test_ingestion_atomization.py` (if exists)
**Acceptance**: Baseline documented. Any existing seed corpus tests pass.

### T-SETUP-003: Audit SeedText dataclass usage [P]

Verify that the `SeedText` dataclass (`seed_corpus.py:12-18`) is dead code. Confirm no imports or instantiations exist anywhere in the codebase. Document the finding for T-P2-001.

**Files**: `src/nexus_babel/services/seed_corpus.py`
**Acceptance**: Dead code status confirmed. Decision recorded: wire it in (T-P2-001) or remove it.

---

## Phase 2: Foundational -- P1 Verification & Hardening

### T-P1-001: Add seed registry listing tests [Story: US-001] [P]

Test `GET /api/v1/corpus/seeds`:
- Returns exactly 5 entries
- Each entry has all required fields: `title`, `author`, `language`, `source_url`, `local_path`, `atomization_status`
- All entries have `atomization_status="not_provisioned"` when no files exist
- All entries have `language="English"`
- All `source_url` values match the Gutenberg URL pattern `https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt`
- Titles match expected: The Odyssey, The Divine Comedy, Leaves of Grass, Ulysses, Frankenstein
- Authors match expected: Homer, Dante Alighieri, Walt Whitman, James Joyce, Mary Shelley

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-002: Add seed registry role enforcement tests [Story: US-001, US-004] [P]

Test auth enforcement for both endpoints:
- `GET /corpus/seeds` with viewer key -> 200
- `GET /corpus/seeds` with no key -> 401
- `POST /corpus/seed` with admin key -> proceeds (mock download)
- `POST /corpus/seed` with operator key -> 403
- `POST /corpus/seed` with researcher key -> 403
- `POST /corpus/seed` with viewer key -> 403
- `POST /corpus/seed` with no key -> 401

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=7 tests, all pass.

### T-P1-003: Add provisioning tests with mocked download [Story: US-002] [P]

Test `provision_seed_text()` directly on the service (bypass API):
- Valid title (case-insensitive: "the odyssey", "THE ODYSSEY", "The Odyssey") -> provisions successfully
- Unknown title -> raises `ValueError`
- Provisioned text has correct local_path under `seeds_dir`
- Mock download called with correct URL and destination path

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=4 tests, all pass.

### T-P1-004: Add idempotent provisioning tests [Story: US-005] [P]

Test:
- First provisioning -> `status="provisioned"`, download called once
- Second provisioning of same title -> `status="already_provisioned"`, download NOT called
- `list_seed_texts()` shows `atomization_status="provisioned"` after provisioning
- `local_path` is non-null after provisioning

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=4 tests, all pass.

### T-P1-005: Add filename sanitization tests [Story: US-006] [P]

Test `_local_path_for()` for all 5 registry titles:
- `"The Odyssey"` -> `the_odyssey.txt`
- `"The Divine Comedy"` -> `the_divine_comedy.txt`
- `"Leaves of Grass"` -> `leaves_of_grass.txt`
- `"Ulysses"` -> `ulysses.txt`
- `"Frankenstein"` -> `frankenstein.txt`

Also test edge cases:
- Title with apostrophe (e.g., `"Shakespeare's Sonnets"`) -> `shakespeares_sonnets.txt`
- Title with multiple spaces -> collapsed to single underscores
- Empty string -> `.txt` (degenerate case, document behavior)

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=8 tests, all pass.

### T-P1-006: Add seeds directory auto-creation tests [Story: US-007] [P]

Test:
- `SeedCorpusService(seeds_dir=tmp_path / "new" / "nested" / "seeds")` creates all parent directories
- Initializing with an existing directory does not raise
- After init, `seeds_dir.is_dir()` returns `True`

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=3 tests, all pass.

### T-P1-007: Add provisioning API integration tests [Story: US-002, US-003] [P]

Test `POST /api/v1/corpus/seed` via TestClient with mocked download:
- Valid title -> 200, response has `title`, `status="provisioned"`, `local_path` (non-null)
- Unknown title -> 400, detail includes "Unknown seed text"
- Verify `document_id` is returned (non-null) when auto-ingestion succeeds
- Verify the provisioned file is ingested as a `Document` (check via `GET /api/v1/documents`)

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=4 tests, all pass.

### T-P1-008: Add case-insensitive title lookup tests [Story: US-002] [P]

Test `_find_entry()` with various case permutations:
- `"the odyssey"` -> matches
- `"THE ODYSSEY"` -> matches
- `"The Odyssey"` -> matches (exact)
- `"tHe OdYsSeY"` -> matches
- `"The Odysse"` (partial) -> None
- `""` (empty) -> None
- `"  The Odyssey  "` (leading/trailing whitespace) -> None (not trimmed -- document this behavior)

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=7 tests, all pass.

---

## Phase 3: P2 Enhancements

### T-P2-001: Wire SeedText dataclass into service [Story: US-008]

Replace raw dict usage in `SeedCorpusService` with `SeedText` dataclass instances:
1. Convert `SEED_REGISTRY` entries to `SeedText` objects at module load or in `__init__`
2. Update `list_seed_texts()` to work with `SeedText` instances
3. Update `provision_seed_text()` to accept and return typed data
4. Keep API-facing return values as dicts for backward compatibility (or convert from dataclass)
5. Decision: if removing the dataclass is preferred (simpler), remove it instead and update US-008 as "resolved by removal"

**Files**: `src/nexus_babel/services/seed_corpus.py`
**Acceptance**: Either (a) `SeedText` is used throughout and tests pass, or (b) `SeedText` is removed and dead code eliminated. No mixed state.

### T-P2-002: Add document-aware status tracking [Story: US-009]

Enhance `list_seed_texts()` to accept an optional `Session` parameter and query the `Document` table:
1. For each seed, check if a `Document` exists with `path` matching the expected `local_path`
2. If document exists and `ingested=True` and `atom_count > 0`, set `atomization_status="atomized"`
3. If document exists and `ingested=True` but `atom_count == 0`, set `atomization_status="ingested"`
4. If file exists but no document, keep `atomization_status="provisioned"`
5. If no file, keep `atomization_status="not_provisioned"`
6. Update `SeedTextEntry` schema to accept the new status values (backward compatible -- existing values still valid)

**Files**: `src/nexus_babel/services/seed_corpus.py`, `src/nexus_babel/schemas.py`, `src/nexus_babel/api/routes.py`
**Acceptance**: After provisioning + ingestion, `GET /corpus/seeds` shows `atomization_status="atomized"` for that text.

### T-P2-003: Add document-aware status tests [Story: US-009] [P]

Test:
- Unprovisionied seed -> `"not_provisioned"`
- Provisioned but not ingested (file exists, no Document row) -> `"provisioned"`
- Provisioned and ingested (Document exists, atoms exist) -> `"atomized"`
- Session parameter is optional; without it, falls back to filesystem-only check

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=4 tests, all pass.

### T-P2-004: Add robust download with timeout and atomic write [Story: US-014]

Replace `urllib.request.urlretrieve` with a safer download implementation:
1. Use `urllib.request.urlopen(url, timeout=timeout)` with configurable timeout (default 30s)
2. Write to a `.tmp` file alongside the final destination
3. On successful download, `os.rename(tmp_path, final_path)` for atomic move
4. On failure, clean up the `.tmp` file
5. Add `download_timeout` parameter to `Settings` (default 30) via `NEXUS_DOWNLOAD_TIMEOUT`
6. Optionally accept timeout in `provision_seed_text()` method signature

**Files**: `src/nexus_babel/services/seed_corpus.py`, `src/nexus_babel/config.py`
**Acceptance**: Download uses timeout. Interrupted downloads do not leave partial files at the final path. Existing behavior preserved for happy path.

### T-P2-005: Add download timeout and atomic write tests [Story: US-014] [P]

Test:
- Successful download produces file at expected path (mock)
- Timeout triggers cleanup of `.tmp` file
- Network error triggers cleanup of `.tmp` file
- No partial file remains after failed download
- Existing file is not overwritten on download failure

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=5 tests, all pass.

### T-P2-006: Add title whitespace trimming to `_find_entry()` [Story: US-002]

Trim leading/trailing whitespace from the input title in `_find_entry()` before comparison. This is a minor robustness improvement to handle accidental whitespace in API requests.

**Files**: `src/nexus_babel/services/seed_corpus.py`
**Acceptance**: `"  The Odyssey  "` matches `"The Odyssey"`. T-P1-008 whitespace test updated to expect match.

---

## Phase 4: P3 -- YAML Registry & Profiles

### T-P3-001: Create YAML seed registry file [Story: US-010]

Create `docs/alexandria_babel/seed_corpus_registry.yaml` with the 5 current seed texts in a structured YAML format:
```yaml
schema_version: "1.0"
seeds:
  - title: "The Odyssey"
    author: "Homer"
    language: "English"
    source_url: "https://www.gutenberg.org/cache/epub/1727/pg1727.txt"
    expected_checksum: null
    tags: ["epic", "classical", "greek"]
```

**Files**: `docs/alexandria_babel/seed_corpus_registry.yaml`
**Acceptance**: Valid YAML. All 5 texts present. `schema_version` key exists.

### T-P3-002: Add YAML registry loader to SeedCorpusService [Story: US-010]

Update `SeedCorpusService.__init__()` to accept an optional `registry_path: Path | None` parameter:
1. If `registry_path` is provided and the file exists, load registry from YAML
2. If not, fall back to hardcoded `SEED_REGISTRY`
3. Validate loaded entries have required fields (`title`, `author`, `language`, `source_url`)
4. Update `main.py` to pass `registry_path=settings.seed_registry_path` (new Settings field, default `None`)

**Files**: `src/nexus_babel/services/seed_corpus.py`, `src/nexus_babel/config.py`, `src/nexus_babel/main.py`
**Acceptance**: Service loads from YAML when path is set. Falls back to hardcoded when not. Tests pass with both modes.

### T-P3-003: Add YAML registry tests [Story: US-010] [P]

Test:
- Valid YAML file loads correctly, `list_seed_texts()` returns entries from YAML
- Invalid YAML (missing required field) raises validation error at init
- Missing YAML file falls back to hardcoded registry
- YAML with extra entries (6+ texts) works correctly
- YAML with `schema_version: "1.0"` is accepted; unknown version raises warning

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=5 tests, all pass.

### T-P3-004: Create ingestion profile schema and loader [Story: US-011]

Define ingestion profile YAML schema and add a loader:
1. Create `profiles/arc4n-seed.yaml` with seed titles, atom tracks, and parse options
2. Add `load_profile(name: str, profiles_dir: Path) -> dict` function
3. Profile schema: `name`, `description`, `seed_titles` (list), `atom_tracks` (list), `parse_options` (dict)
4. Validate profile structure at load time

**Files**: `profiles/arc4n-seed.yaml`, `src/nexus_babel/services/seed_corpus.py` (or new `src/nexus_babel/services/profiles.py`)
**Acceptance**: `load_profile("arc4n-seed", profiles_dir)` returns valid profile dict.

### T-P3-005: Add `--profile` flag to ingestion script [Story: US-011]

Update `scripts/ingest_corpus.py`:
1. Add `argparse` with `--profile` argument
2. Load profile from `profiles/{name}.yaml`
3. Provision seed texts listed in the profile (if not already provisioned)
4. Ingest using profile's `parse_options` and `atom_tracks`
5. Record profile name in the IngestJob's `request_payload`

**Files**: `scripts/ingest_corpus.py`
**Acceptance**: `python scripts/ingest_corpus.py --profile arc4n-seed` provisions and ingests listed seeds. Invalid profile name exits with non-zero and clear error.

### T-P3-006: Add ingestion profile tests [Story: US-011] [P]

Test:
- Valid profile loads correctly
- Invalid profile name returns error
- Profile with unknown seed title fails provisioning step
- Profile parse_options are passed to ingest_batch
- Profile name is recorded in IngestJob request_payload

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=5 tests, all pass.

### T-P3-007: Add CLI provisioning script [Story: US-012]

Create `scripts/provision_corpus.py`:
1. Accept `--title "The Odyssey"` for single provisioning
2. Accept `--all` to provision all registry texts
3. Accept `--profile <name>` to provision texts from a profile
4. Use `SeedCorpusService` directly (no FastAPI app needed for provisioning)
5. Print provisioning results in a table format
6. Exit 0 on success, 1 on any failure

**Files**: `scripts/provision_corpus.py`
**Acceptance**: `python scripts/provision_corpus.py --title "The Odyssey"` provisions the text. `--all` provisions all 5.

### T-P3-008: Add batch provisioning endpoint [Story: US-013]

Add `POST /api/v1/corpus/seed/batch` (admin):
1. Accept `{"titles": ["The Odyssey", "Leaves of Grass"]}` request
2. Provision each title sequentially
3. Auto-ingest each successfully provisioned text
4. Return per-title results and summary counts
5. Individual failures do not abort the batch

**Files**: `src/nexus_babel/api/routes.py`, `src/nexus_babel/schemas.py`, `src/nexus_babel/services/seed_corpus.py`
**Acceptance**: Batch provisioning returns per-title results. One failure does not block others.

### T-P3-009: Add batch provisioning tests [Story: US-013] [P]

Test:
- Batch of 2 valid titles -> both provisioned
- Batch with 1 valid + 1 invalid -> valid provisioned, invalid reported as error
- Batch of already-provisioned titles -> all "already_provisioned"
- Empty titles list -> 400 or empty results
- Admin-only enforcement -> non-admin gets 403

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=5 tests, all pass.

### T-P3-010: Add checksum verification after download [Story: US-015]

1. Add `expected_checksum` field to registry entries (nullable, initially null for all)
2. After download, compute SHA256 of the downloaded file
3. If `expected_checksum` is set and does not match, delete the file and raise an error
4. If `expected_checksum` is null, log the computed checksum for future use
5. Add a `scripts/compute_seed_checksums.py` utility to populate the registry

**Files**: `src/nexus_babel/services/seed_corpus.py`, `docs/alexandria_babel/seed_corpus_registry.yaml` (if YAML registry exists)
**Acceptance**: Checksum mismatch prevents provisioning. Matching checksum succeeds. Null checksum bypasses check.

---

## Phase 5: P3 -- Corpus Health & Expansion

### T-P3-011: Add corpus health endpoint [Story: US-019, US-020]

Add `GET /api/v1/corpus/seeds/health` (operator):
1. Aggregate: total_seeds, provisioned, not_provisioned, ingested, atomized
2. Per-seed: file_exists, file_size_bytes, checksum_valid (if expected_checksum set), document_id, atom_count, last_ingested_at
3. Aggregate atom counts by level from the `Atom` table for all seed documents

**Files**: `src/nexus_babel/api/routes.py`, `src/nexus_babel/services/seed_corpus.py`, `src/nexus_babel/schemas.py`
**Acceptance**: Endpoint returns health data matching actual corpus state.

### T-P3-012: Add corpus health tests [Story: US-019, US-020] [P]

Test:
- Empty corpus -> all counts zero, all "not_provisioned"
- One provisioned + ingested text -> correct counts, atoms_by_level populated
- Health endpoint requires operator role

**Files**: `tests/test_seed_corpus.py`
**Acceptance**: >=3 tests, all pass.

### T-P3-013: Add corpus expansion support [Story: US-016]

Add `POST /api/v1/corpus/seeds/register` (admin):
1. Accept `{title, author, language, source_url}` to add a new entry to the runtime registry
2. If YAML registry is used, persist the new entry back to the YAML file
3. If hardcoded registry, store in an in-memory extension list (persists until restart)
4. Validate: title must be unique, source_url must be reachable (HEAD request)

**Files**: `src/nexus_babel/api/routes.py`, `src/nexus_babel/services/seed_corpus.py`, `src/nexus_babel/schemas.py`
**Acceptance**: New text registered, appears in `GET /corpus/seeds`, can be provisioned.

---

## Phase 6: Cross-Cutting

### T-CROSS-001: Wire seed corpus tests into CI [P]

Update `.github/workflows/ci-minimal.yml` to run `pytest tests/test_seed_corpus.py -v` as part of the pipeline. Ensure mock download fixtures prevent network calls in CI.

**Files**: `.github/workflows/ci-minimal.yml`
**Acceptance**: CI runs the test suite and fails on regression. No network calls in CI.

### T-CROSS-002: Add seed corpus provisioning benchmark

Create a benchmark that (with mocked downloads) provisions and ingests all 5 seed texts, measuring:
- Time per text (provision + ingest)
- Total atoms per text
- Memory peak during largest text (Ulysses)
- Summary table output

**Files**: `scripts/benchmark_seed_corpus.py`
**Acceptance**: Script runs end-to-end with mock data. Baseline captured.

### T-CROSS-003: Reconcile with spec 01 T-P1-010

Spec 01 (ingestion-atomization) tasks.md defines T-P1-010 "Add seed corpus registry tests" which overlaps with this domain. Reconcile by:
1. Moving seed-corpus-specific tests from `test_ingestion_atomization.py` to `test_seed_corpus.py`
2. Keeping ingestion-pipeline-centric tests (e.g., "seed text produces correct atom counts") in the ingestion domain
3. Cross-referencing both specs

**Files**: `tests/test_seed_corpus.py`, `tests/test_ingestion_atomization.py`, `specs/01-ingestion-atomization/tasks.md`
**Acceptance**: No duplicate test coverage. Clear domain boundaries. Both test files pass.

### T-CROSS-004: Update CLAUDE.md with domain spec references

Add a section to the project CLAUDE.md pointing to the new `specs/06-seed-corpus/` directory and summarizing the domain's P1/P2/P3 scope.

**Files**: `CLAUDE.md`
**Acceptance**: CLAUDE.md references the spec files.

---

## Task Dependency Graph

```
Phase 1 (Setup)
  T-SETUP-001 ─┐
  T-SETUP-002 ─┤── All can run in parallel [P]
  T-SETUP-003 ─┘

Phase 2 (P1 Verification) -- all can run in parallel [P]
  T-P1-001 through T-P1-008 (depend on T-SETUP-001)

Phase 3 (P2 Enhancements)
  T-SETUP-003 -> T-P2-001
  T-P1-001 + T-P1-007 -> T-P2-002 -> T-P2-003
  T-P1-003 -> T-P2-004 -> T-P2-005
  T-P1-008 -> T-P2-006

Phase 4 (P3 Registry & Profiles)
  T-P3-001 -> T-P3-002 -> T-P3-003
  T-P3-004 -> T-P3-005 -> T-P3-006
  T-P3-007 (depends on T-P2-004)
  T-P3-008 -> T-P3-009 (depends on T-P2-004)
  T-P3-002 -> T-P3-010 (depends on T-P2-004)

Phase 5 (Corpus Health & Expansion)
  T-P2-002 -> T-P3-011 -> T-P3-012
  T-P3-002 -> T-P3-013 (depends on T-P3-011)

Phase 6 (Cross-Cutting)
  T-CROSS-001 (depends on Phase 2 completion)
  T-CROSS-002 (depends on T-P1-007)
  T-CROSS-003 (depends on T-P1-001)
  T-CROSS-004 (no deps)
```

## Summary

| Phase | Tasks | Parallel | Scope |
|-------|-------|----------|-------|
| Phase 1: Setup | 3 | All [P] | Test infrastructure, baseline verification, dead code audit |
| Phase 2: P1 Verification | 8 | All [P] | Harden existing as-built behavior with thorough tests |
| Phase 3: P2 Enhancements | 6 | Partial | SeedText dataclass wiring, status tracking, robust downloads |
| Phase 4: P3 Registry & Profiles | 10 | Partial | YAML registry, ingestion profiles, CLI, batch, checksums |
| Phase 5: Corpus Health & Expansion | 3 | Partial | Health endpoint, corpus expansion API |
| Phase 6: Cross-Cutting | 4 | Partial | CI, benchmarks, spec reconciliation |
| **Total** | **34** | | |
