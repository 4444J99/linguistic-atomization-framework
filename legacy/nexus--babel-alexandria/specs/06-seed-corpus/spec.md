# Seed Corpus -- Specification

## Overview

The Seed Corpus domain manages the canonical text registry, Project Gutenberg provisioning, corpus directory lifecycle, and ingestion profiles for Nexus Babel Alexandria. It provides the foundational literary material that feeds the ARC4N Living Digital Canon -- the five seed texts (Homer's Odyssey, Dante's Divine Comedy, Whitman's Leaves of Grass, Joyce's Ulysses, Shelley's Frankenstein) represent the pilot corpus from which all downstream atomization, evolution, remix, and scholarly analysis flows.

The domain currently consists of a hardcoded Python registry with 5 canonical texts, a provisioning service that downloads texts from Project Gutenberg to a local `seeds/` directory, and two API endpoints: one for listing the registry with provisioning status, and one for admin-only provisioning + auto-ingestion. The registry is the entry point for all corpus material -- a text must be registered and provisioned before it can be atomized, evolved, or remixed. The vision extends this to a YAML-based registry, named ingestion profiles, CLI-driven provisioning, batch operations, corpus versioning, and language-specific profiles.

## User Stories

### P1 -- As-Built (Verified)

#### US-001: List seed text registry

> As a **viewer**, I want to see the full registry of canonical seed texts with their provisioning status so that I can understand what corpus material is available and what still needs to be downloaded.

**Given** the application is running with default configuration
**When** I `GET /api/v1/corpus/seeds` with a viewer API key
**Then**:
- The response contains a `seeds` list with exactly 5 entries (`seed_corpus.py:62-74`)
- Each entry includes `title`, `author`, `language`, `source_url`, `local_path` (nullable), and `atomization_status` (`schemas.py:244-250`)
- `atomization_status` is `"provisioned"` if the local file exists at `seeds_dir/{safe_name}.txt`, otherwise `"not_provisioned"` (`seed_corpus.py:67-71`)
- `local_path` is the string representation of the local file path if provisioned, `None` otherwise (`seed_corpus.py:72`)
- The 5 entries are: The Odyssey (Homer), The Divine Comedy (Dante Alighieri), Leaves of Grass (Walt Whitman), Ulysses (James Joyce), Frankenstein (Mary Shelley) (`seed_corpus.py:21-52`)
- All entries have `language: "English"` (all are English translations) (`seed_corpus.py:26, 32, 38, 44, 50`)
- All `source_url` values point to `https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt` (`seed_corpus.py:27, 33, 39, 45, 51`)
- Viewer role is sufficient (no operator or admin required) (`routes.py:638`)

**Code evidence:** `seed_corpus.py:60-75` (`list_seed_texts`), `routes.py:638-641`.

#### US-002: Provision a seed text

> As an **admin**, I want to provision a canonical seed text by title so that it is downloaded from Project Gutenberg and made available for ingestion.

**Given** a seed title matching the registry (case-insensitive)
**When** I `POST /api/v1/corpus/seed` with `{"title": "The Odyssey"}` and an admin API key
**Then**:
- The title is matched case-insensitively against `SEED_REGISTRY` entries (`seed_corpus.py:98-102`)
- If no match is found, a `ValueError` is raised with `"Unknown seed text: {title}"` and the API returns HTTP 400 (`seed_corpus.py:79-80`, `routes.py:677-678`)
- The local path is computed as `seeds_dir/{safe_name}.txt` where `safe_name` = `title.lower().replace(" ", "_").replace("'", "")` (`seed_corpus.py:104-106`)
- If the file already exists, returns `{"title": ..., "status": "already_provisioned", "local_path": ...}` (`seed_corpus.py:83-88`)
- If the file does not exist, `urllib.request.urlretrieve(url, dest)` downloads it (`seed_corpus.py:108-109`)
- On successful download, returns `{"title": ..., "status": "provisioned", "local_path": ...}` (`seed_corpus.py:91-95`)
- The `seeds_dir` is created with `mkdir(parents=True, exist_ok=True)` in `__init__` (`seed_corpus.py:57-58`)

**Code evidence:** `seed_corpus.py:77-95` (`provision_seed_text`), `seed_corpus.py:104-109` (path generation and download).

#### US-003: Auto-ingestion after provisioning

> As an **admin**, I want a provisioned seed text to be automatically ingested through the standard pipeline so that it becomes a `Document` with atoms, hypergraph projection, and full provenance in a single API call.

**Given** a seed text has been provisioned (status `"provisioned"` or `"already_provisioned"`)
**When** the `POST /api/v1/corpus/seed` route completes provisioning
**Then**:
- If `local_path` exists and `status` is `"provisioned"` or `"already_provisioned"`, the route calls `ingestion_service.ingest_batch()` with `source_paths=[str(local_path)]`, `modalities=["text"]`, `parse_options={}` (`routes.py:660-666`)
- The ingestion produces a `Document` row with atoms, hypergraph projection, and full provenance (standard pipeline behavior)
- The `document_id` from the first file in the ingest result is included in the response (`routes.py:667-669`)
- If ingestion fails (exception), the entire operation rolls back and returns HTTP 400 (`routes.py:677-678`)
- The response schema is `SeedProvisionResponse`: `title`, `status`, `local_path` (nullable), `document_id` (nullable) (`schemas.py:261-265`)

**Code evidence:** `routes.py:644-680` (`provision_seed_text` route).

#### US-004: Admin-only provisioning

> As the **system**, I want seed text provisioning to be restricted to admin users so that corpus composition changes require the highest privilege level.

**Given** a non-admin user (viewer, operator, or researcher)
**When** they attempt `POST /api/v1/corpus/seed`
**Then**:
- The `_require_auth("admin")` dependency rejects with HTTP 403 (`routes.py:648`)
- Only users with the `admin` role can provision (role hierarchy: viewer < operator < researcher < admin)

**Code evidence:** `routes.py:648` (`Depends(_require_auth("admin"))`).

#### US-005: Idempotent provisioning

> As an **admin**, I want re-provisioning an already-downloaded seed text to skip the download and return `"already_provisioned"` so that repeated calls are safe and fast.

**Given** a seed text whose local file already exists
**When** `POST /api/v1/corpus/seed` is called with that title
**Then**:
- `local_path.exists()` returns `True` (`seed_corpus.py:83`)
- The download is skipped
- The response `status` is `"already_provisioned"` (`seed_corpus.py:85`)
- Auto-ingestion still runs (the file is re-ingested, which itself is idempotent via checksum dedup in the ingestion pipeline) (`routes.py:655-669`)

**Code evidence:** `seed_corpus.py:82-88` (existence check short-circuit).

#### US-006: Filename sanitization

> As the **system**, I want seed text filenames to be predictably sanitized so that local paths are safe, consistent, and filesystem-friendly.

**Given** a seed text title
**When** `_local_path_for()` generates the filename
**Then**:
- Title is lowercased (`seed_corpus.py:105`)
- Spaces are replaced with underscores (`seed_corpus.py:105`)
- Apostrophes are removed (`seed_corpus.py:105`)
- `.txt` extension is appended (`seed_corpus.py:106`)
- The path is under `seeds_dir` (`seed_corpus.py:106`)
- Examples:
  - `"The Odyssey"` -> `the_odyssey.txt`
  - `"Leaves of Grass"` -> `leaves_of_grass.txt`
  - `"The Divine Comedy"` -> `the_divine_comedy.txt`
  - `"Ulysses"` -> `ulysses.txt`
  - `"Frankenstein"` -> `frankenstein.txt`

**Code evidence:** `seed_corpus.py:104-106` (`_local_path_for`).

#### US-007: Seeds directory auto-creation

> As the **system**, I want the seeds directory to be created automatically when the service initializes so that provisioning works without manual filesystem setup.

**Given** the application starts with `corpus_root` set to a valid path
**When** `SeedCorpusService.__init__()` runs
**Then**:
- `seeds_dir` is set to `corpus_root / "seeds"` (`main.py:68`)
- `seeds_dir.mkdir(parents=True, exist_ok=True)` creates the directory (and parents) if they do not exist (`seed_corpus.py:58`)
- If the directory already exists, no error is raised (`exist_ok=True`)

**Code evidence:** `seed_corpus.py:56-58`, `main.py:68`.

### P2 -- Partially Built

#### US-008: Seed text as SeedText dataclass

> As a **developer**, I want seed text metadata encapsulated in a typed dataclass so that the registry and provisioning service have a well-defined internal model.

**Current state**: The `SeedText` dataclass is defined (`seed_corpus.py:12-18`) with fields: `title`, `author`, `language`, `source_url`, `local_path` (default `None`), `atomization_status` (default `"not_provisioned"`). However, the dataclass is never instantiated -- `SEED_REGISTRY` is a list of plain dicts (`seed_corpus.py:21-52`), and all service methods return plain dicts. The `SeedText` dataclass exists as dead code.

**Gap**: The dataclass is defined but unused. The service should instantiate `SeedText` objects from registry entries and use them internally for type safety and IDE support.

#### US-009: Provisioned-to-atomized status tracking

> As a **viewer**, I want to distinguish between "downloaded but not ingested" and "downloaded and atomized" seed texts so that I can see the full pipeline status.

**Current state**: The `atomization_status` field has only two values: `"provisioned"` (file exists) and `"not_provisioned"` (file does not exist) (`seed_corpus.py:71`). There is no check for whether the seed text has been ingested as a `Document` or whether atomization has completed. A provisioned text that has not yet been ingested shows the same status as one that has been fully atomized.

**Gap**: No lookup against the `Document` table to determine actual ingestion/atomization status. The `atomization_status` is purely filesystem-based.

### P3+ -- Vision

#### US-010: YAML-based seed registry

> As a **corpus curator**, I want the seed text registry to live in a YAML file (`docs/alexandria_babel/seed_corpus_registry.yaml`) so that the registry can be version-controlled, edited by non-programmers, extended without code changes, and referenced from ingestion profiles.

**Current state**: The registry is a hardcoded Python list in `seed_corpus.py:21-52`. Adding or modifying seed texts requires code changes, tests, and redeployment.

**Vision ref:** AB01-T001 -- Seed Corpus Registry + Profiles.

#### US-011: Ingestion profiles

> As an **operator**, I want to run `python scripts/ingest_corpus.py --profile arc4n-seed` so that repeatable ingestion configurations are stored as named profiles with seed title lists, atom track presets, and parse options.

**Current state**: The ingestion script (`scripts/ingest_corpus.py`) is a minimal 28-line script that ingests the entire `corpus_root` with no profile support (`scripts/ingest_corpus.py:10-28`). There is no `--profile` CLI argument, no profile definition files, and no profile metadata in ingest job provenance.

**Vision ref:** AB01-T001 -- Seed Corpus Registry + Profiles.

#### US-012: CLI provisioning

> As an **operator**, I want a CLI command to provision seed texts without using the API so that provisioning can be done in CI/CD pipelines, local development setup, and batch scripts.

**Current state**: Provisioning is only available via the API endpoint `POST /api/v1/corpus/seed`. There is no CLI entrypoint in `scripts/` or `__main__` for provisioning. The only scripted path is the ingestion script which does not provision seeds.

#### US-013: Batch provisioning

> As an **admin**, I want to provision all seed texts in a single API call or CLI invocation so that initial corpus setup is a one-step operation.

**Current state**: `POST /api/v1/corpus/seed` accepts only a single `title` string (`schemas.py:257-258`). Provisioning all 5 texts requires 5 separate API calls. There is no batch provisioning endpoint or CLI flag.

#### US-014: Download timeout and retry

> As the **system**, I want seed text downloads to have a configurable timeout and retry with backoff so that transient network failures do not leave the corpus in a partially provisioned state.

**Current state**: `urllib.request.urlretrieve(url, dest)` is called with no timeout, no retry, and no error handling beyond the exception propagating up (`seed_corpus.py:108-109`). A slow or failing Gutenberg server will block the request indefinitely.

#### US-015: Checksum verification after download

> As the **system**, I want downloaded seed texts to be verified against a known checksum so that corrupted or incomplete downloads are detected and rejected.

**Current state**: No checksum verification exists for downloaded files. The provisioning service stores the file as-is from Gutenberg with no integrity check. The ingestion pipeline will SHA256 checksum the file after provisioning, but the provisioning step itself has no expected-checksum validation.

#### US-016: Corpus expansion API

> As an **admin**, I want to add new seed texts to the registry via an API endpoint so that the corpus can grow beyond the initial 5 texts without code changes.

**Current state**: The registry is a hardcoded Python list. There is no API endpoint for adding, removing, or modifying registry entries. All 5 texts are English translations from Project Gutenberg.

#### US-017: Original-language texts

> As a **researcher**, I want seed texts available in their original languages (Homeric Greek, Italian, English, French) so that linguistic analysis operates on authentic source material, not just translations.

**Current state**: All 5 registry entries have `"language": "English"`. The Gutenberg URLs point to English translations. No original-language variants are registered.

#### US-018: Corpus versioning and immutable snapshots

> As a **knowledge operator**, I want to create immutable snapshots of the corpus at specific points in time so that scholarly references are stable and reproducible.

**Current state**: No corpus versioning mechanism exists. Seed texts are mutable files on disk. Re-provisioning overwrites the existing file if the download content has changed (unlikely for Gutenberg, but possible).

#### US-019: Seed text health checks

> As a **knowledge operator**, I want periodic health checks that verify seed text integrity (file exists, checksum matches, Gutenberg URL is reachable) so that corpus degradation is detected early.

**Current state**: No health check mechanism exists. A deleted or corrupted seed file would only be noticed when `list_seed_texts()` reports it as `"not_provisioned"`.

#### US-020: Corpus statistics dashboard

> As a **viewer**, I want to see aggregate corpus statistics (total texts, total atoms, atoms per level, provisioning status breakdown) so that corpus health is visible at a glance.

**Current state**: `GET /api/v1/corpus/seeds` lists individual seed texts but provides no aggregate statistics. The `/metrics` endpoint tracks HTTP request counts but no corpus-level metrics.

#### US-021: Language-specific ingestion profiles

> As a **researcher**, I want language-specific ingestion profiles that configure syllabification rules, glyph metadata lookups, and analysis layers appropriate for the source language so that non-English texts are processed correctly.

**Current state**: All syllabification and glyph metadata is English/Latin-biased. There are no language-specific profiles or configuration hooks.

## Functional Requirements

### Seed Registry

- **FR-001** [MUST] The system MUST maintain a registry of canonical seed texts with `title`, `author`, `language`, and `source_url` for each entry. Implemented: `seed_corpus.py:21-52` (`SEED_REGISTRY` list of dicts).
- **FR-002** [MUST] The registry MUST include exactly 5 texts: The Odyssey (Homer), The Divine Comedy (Dante Alighieri), Leaves of Grass (Walt Whitman), Ulysses (James Joyce), Frankenstein (Mary Shelley). Implemented: `seed_corpus.py:22-51`.
- **FR-003** [MUST] All registry entries MUST include a valid Project Gutenberg URL in the format `https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt`. Implemented: `seed_corpus.py:27, 33, 39, 45, 51`.
- **FR-004** [MUST] `GET /api/v1/corpus/seeds` MUST return all registry entries with `title`, `author`, `language`, `source_url`, `local_path` (nullable), and `atomization_status`. Implemented: `routes.py:638-641`, `schemas.py:244-253`.
- **FR-005** [MUST] The seeds listing endpoint MUST require `viewer` role minimum. Implemented: `routes.py:638`.
- **FR-006** [SHOULD] The registry SHOULD be stored in a YAML file rather than hardcoded in Python. Not yet implemented (AB01-T001).
- **FR-007** [SHOULD] The registry SHOULD support adding custom entries beyond the initial 5. Not yet implemented.
- **FR-008** [MAY] The registry MAY include expected checksums for download verification. Not yet implemented.

### Provisioning

- **FR-009** [MUST] `POST /api/v1/corpus/seed` MUST accept a `title` string and provision the matching seed text. Implemented: `routes.py:644-680`, `schemas.py:257-258`.
- **FR-010** [MUST] The provisioning endpoint MUST require `admin` role. Implemented: `routes.py:648`.
- **FR-011** [MUST] Title matching MUST be case-insensitive. Implemented: `seed_corpus.py:98-99`.
- **FR-012** [MUST] Unknown titles MUST raise a `ValueError` resulting in HTTP 400. Implemented: `seed_corpus.py:79-80`, `routes.py:677-678`.
- **FR-013** [MUST] Already-provisioned texts MUST return `status: "already_provisioned"` without re-downloading. Implemented: `seed_corpus.py:82-88`.
- **FR-014** [MUST] Provisioning MUST download the text from the registry's `source_url` to `seeds_dir/{safe_name}.txt`. Implemented: `seed_corpus.py:90, 108-109`.
- **FR-015** [MUST] After successful provisioning, the system MUST auto-ingest the text through the standard ingestion pipeline. Implemented: `routes.py:655-669`.
- **FR-016** [MUST] The provisioning response MUST include `title`, `status`, `local_path` (nullable), and `document_id` (nullable). Implemented: `schemas.py:261-265`.
- **FR-017** [SHOULD] Downloads SHOULD have a configurable timeout. Not yet implemented (`urlretrieve` has no timeout).
- **FR-018** [SHOULD] Downloads SHOULD retry with exponential backoff on transient failure. Not yet implemented.
- **FR-019** [SHOULD] Downloaded files SHOULD be checksum-verified against expected values. Not yet implemented.
- **FR-020** [SHOULD] The system SHOULD support batch provisioning of multiple titles in a single request. Not yet implemented.
- **FR-021** [MAY] The system MAY provide a CLI entrypoint for provisioning outside the API. Not yet implemented.

### Filename Management

- **FR-022** [MUST] Local filenames MUST be generated by lowercasing the title, replacing spaces with underscores, removing apostrophes, and appending `.txt`. Implemented: `seed_corpus.py:104-106`.
- **FR-023** [MUST] The `seeds_dir` MUST be auto-created with `parents=True, exist_ok=True` at service initialization. Implemented: `seed_corpus.py:57-58`.
- **FR-024** [SHOULD] Filename sanitization SHOULD handle additional special characters beyond spaces and apostrophes (e.g., colons, slashes, Unicode). Not yet implemented -- only spaces and apostrophes are handled.

### Status Tracking

- **FR-025** [MUST] `atomization_status` MUST be `"provisioned"` when the local file exists and `"not_provisioned"` otherwise. Implemented: `seed_corpus.py:71`.
- **FR-026** [SHOULD] `atomization_status` SHOULD distinguish between `"provisioned"` (downloaded only), `"ingested"` (Document created), and `"atomized"` (atoms generated). Not yet implemented -- status is binary based on file existence.
- **FR-027** [MAY] The system MAY track provisioning history (timestamps, download duration, source URL at time of download). Not yet implemented.

### Ingestion Profiles

- **FR-028** [SHOULD] The system SHOULD support named ingestion profiles defined in YAML files with seed title lists, atom track presets, and parse options. Not yet implemented (AB01-T001).
- **FR-029** [SHOULD] The ingestion script SHOULD accept a `--profile` CLI argument that loads a named profile. Not yet implemented (AB01-T001).
- **FR-030** [SHOULD] Profile metadata SHOULD be recorded in the IngestJob's `request_payload` for provenance. Not yet implemented (AB01-T001).
- **FR-031** [MAY] The system MAY validate profile definitions against a schema at load time. Not yet implemented.
- **FR-032** [MAY] The system MAY support language-specific profiles with syllabification and glyph metadata overrides. Not yet implemented.

### Corpus Health

- **FR-033** [MAY] The system MAY provide a health check endpoint that verifies seed text integrity (file exists, checksum matches). Not yet implemented.
- **FR-034** [MAY] The system MAY expose aggregate corpus statistics (total texts, provisioning breakdown, atom counts by level). Not yet implemented.
- **FR-035** [MAY] The system MAY support immutable corpus snapshots with version identifiers. Not yet implemented.

## Key Entities

### SeedText Dataclass (`seed_corpus.py:12-18`)

| Field | Type | Purpose |
|-------|------|---------|
| `title` | str | Canonical text title |
| `author` | str | Author name |
| `language` | str | Language code (currently all `"English"`) |
| `source_url` | str | Project Gutenberg download URL |
| `local_path` | Path \| None | Local filesystem path (populated after provisioning) |
| `atomization_status` | str | `"not_provisioned"` (default) or `"provisioned"` |

Note: This dataclass is defined but never instantiated. The service operates on plain dicts from `SEED_REGISTRY`.

### SEED_REGISTRY (`seed_corpus.py:21-52`)

| # | Title | Author | Language | Gutenberg ID |
|---|-------|--------|----------|--------------|
| 1 | The Odyssey | Homer | English | 1727 |
| 2 | The Divine Comedy | Dante Alighieri | English | 8800 |
| 3 | Leaves of Grass | Walt Whitman | English | 1322 |
| 4 | Ulysses | James Joyce | English | 4300 |
| 5 | Frankenstein | Mary Shelley | English | 84 |

### SeedTextEntry (Pydantic schema, `schemas.py:244-250`)

| Field | Type | Purpose |
|-------|------|---------|
| `title` | str | Seed text title |
| `author` | str | Author name |
| `language` | str | Language |
| `source_url` | str | Gutenberg URL |
| `local_path` | str \| None | Local path if provisioned |
| `atomization_status` | str | `"provisioned"` or `"not_provisioned"` |

### SeedTextListResponse (Pydantic schema, `schemas.py:253-254`)

| Field | Type | Purpose |
|-------|------|---------|
| `seeds` | list[SeedTextEntry] | Full registry listing |

### SeedProvisionRequest (Pydantic schema, `schemas.py:257-258`)

| Field | Type | Purpose |
|-------|------|---------|
| `title` | str | Title to provision |

### SeedProvisionResponse (Pydantic schema, `schemas.py:261-265`)

| Field | Type | Purpose |
|-------|------|---------|
| `title` | str | Provisioned text title |
| `status` | str | `"provisioned"`, `"already_provisioned"`, or error |
| `local_path` | str \| None | Local path after download |
| `document_id` | str \| None | Document ID after auto-ingestion |

### Document (downstream, `models.py:30-51`)

Provisioned seed texts become `Document` rows via auto-ingestion. The `Document` entity is defined in the ingestion-atomization domain (spec 01). Key fields for seed corpus context:
- `path`: Resolved absolute path to `seeds_dir/{safe_name}.txt`
- `title`: Filename of the seed text
- `modality`: `"text"` (all seed texts are plain text)
- `checksum`: SHA256 of the downloaded file
- `ingested`: `True` after successful processing
- `atom_count`: Total atoms created across all 5 levels

## Edge Cases

### Covered by existing tests

- Invalid seed title returns HTTP 400 (transitively via `ValueError` in `seed_corpus.py:79-80`, caught by `routes.py:677-678`)
- Admin-only enforcement -- non-admin roles cannot provision (transitively via `_require_auth("admin")` in `routes.py:648`)
- Viewer can list seeds (transitively via `_require_auth("viewer")` in `routes.py:638`)

### Not covered / known gaps

- **Network failure during download**: `urllib.request.urlretrieve` has no timeout, retry, or error recovery. A network failure mid-download may leave a partial file at `dest` which would then be considered "provisioned" on the next call since `local_path.exists()` would return `True`. No cleanup of partial files is implemented.
- **Partial file left on disk**: If a download is interrupted, the partial file remains and prevents re-download (the existence check in `seed_corpus.py:83` would short-circuit). No content validation is performed.
- **Gutenberg URL changes**: If Project Gutenberg changes its URL scheme or removes a text, provisioning would fail with an unhandled `urllib.error.URLError` or `HTTPError`.
- **Disk space exhaustion**: No check for available disk space before downloading. Ulysses is ~1.5MB, the full 5-text corpus is ~4MB.
- **Concurrent provisioning**: Two simultaneous `POST /corpus/seed` requests for the same title could race on the download, potentially producing a corrupted file if `urlretrieve` is not atomic.
- **Case variations in title**: The case-insensitive lookup handles "the odyssey" and "THE ODYSSEY", but no test verifies this. Titles with leading/trailing whitespace are not trimmed.
- **Unicode in titles**: If a future seed text has a title with Unicode characters (e.g., accented letters), `_local_path_for()` only handles spaces and apostrophes. Other special characters would pass through to the filename.
- **SeedText dataclass unused**: The `SeedText` dataclass is defined but never instantiated. All service methods return plain dicts, which means no runtime type validation occurs on registry entries.
- **Auto-ingestion failure on already-provisioned text**: When `status="already_provisioned"`, auto-ingestion still runs (`routes.py:655`). If ingestion raises an exception, the route returns HTTP 400, which may confuse the caller since the seed was already provisioned successfully.
- **`document_id` extraction from ingest result**: The route accesses `ingest_result.get("files", [])` then `files[0].get("document_id")` (`routes.py:667-669`). If `files` is empty or `document_id` is not present, `doc_id` remains `None` without error, which may silently hide ingestion failures.
- **Empty file download**: If Gutenberg returns an empty response, the provisioned file would be 0 bytes. Ingestion would proceed with empty text, producing zero atoms.
- **Seeds directory permissions**: The `mkdir(parents=True, exist_ok=True)` call does not set explicit permissions. On shared systems, the created directory may have undesirable permissions.

## Success Criteria

1. **Registry completeness**: All 5 canonical seed texts are present in the registry with correct titles, authors, languages, and valid Gutenberg URLs.
2. **Provisioning correctness**: A valid title provisions the text, an invalid title returns an error, and an already-provisioned title is idempotent.
3. **Auto-ingestion integration**: Successfully provisioned texts are automatically ingested, producing a `Document` row with atoms and a `document_id` in the response.
4. **Role enforcement**: Only admin users can provision. Viewers can list. Other roles are correctly rejected.
5. **Filename safety**: All generated filenames are filesystem-friendly: lowercase, underscores, no special characters, predictable mapping from title to path.
6. **Status accuracy**: `atomization_status` correctly reflects whether the local file exists.
7. **Directory lifecycle**: The seeds directory is auto-created on service initialization. No manual setup required.
8. **API contract compliance**: Both endpoints return the documented Pydantic response schemas. Error responses include descriptive messages.
9. **Performance baseline**: Provisioning and auto-ingestion of a single seed text (e.g., Frankenstein at ~442KB) completes within 30 seconds on local dev (including download and atomization). Listing all seeds completes in <50ms.
