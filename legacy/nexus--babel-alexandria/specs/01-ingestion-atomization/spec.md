# Ingestion & Atomization -- Specification

## Overview

The Ingestion & Atomization domain is the foundational data pipeline of Nexus Babel Alexandria. It transforms multi-modal source documents (text, PDF, image, audio) into a 5-level atomic hierarchy -- glyph-seed, syllable, word, sentence, paragraph -- where each level is independently addressable, searchable, and remixable. The glyph-seed level carries rich metadata (IPA phonemes, historic script ancestors, visual/typographic mutations, thematic tags, evolution targets) that powers the ARC4N Living Digital Canon's temporal evolution spiral.

This domain also encompasses checksummed deduplication, conflict detection (git merge markers), object storage for raw payloads, hypergraph projection of atoms, canonicalization of sibling document representations, and cross-modal linking between text and media files sharing a common stem. The ingestion pipeline is the sole entry point for all corpus material and must guarantee provenance traceability from raw file to individual atom.

## User Stories

### P1 -- As-Built (Verified)

#### US-001: Multi-modal file ingestion

> As an **operator**, I want to ingest a batch of files from the corpus root so that each file is parsed according to its modality and stored as a `Document` with full provenance.

**Given** a set of file paths within `corpus_root` and an operator API key
**When** I `POST /api/v1/ingest/batch` with `source_paths`, `modalities`, and `parse_options`
**Then** each file is:
- Resolved against `corpus_root` (path traversal rejected -- `ingestion.py:228-241`)
- Detected by modality from extension (`ingestion.py:243-253`, `TEXT_EXT`, `PDF_EXT`, `IMAGE_EXT`, `AUDIO_EXT`)
- SHA256 checksummed (`text_utils.py:29-34`)
- Skipped if checksum matches existing document and `force` is false (`ingestion.py:75-83`)
- Raw payload copied to `object_storage_root/{checksum}{ext}` (`ingestion.py:416-423`)
- Upserted as a `Document` row with `path`, `modality`, `checksum`, `size_bytes`, `provenance` JSON (`ingestion.py:316-364`)
- Result returned with per-file status (`ingested`, `unchanged`, `conflict`, `error`, `skipped`)

**Code evidence:** `test_mvp.py:88-110` (`test_ingestion_completeness`), `test_mvp.py:224-243` (`test_multimodal_linkage`).

#### US-002: 5-level atomization with rich glyph-seed metadata

> As an **operator**, I want ingested text documents to be atomized into glyph-seeds, syllables, words, sentences, and paragraphs so that each level is stored as an `Atom` row with appropriate metadata.

**Given** a text document with `atomize=true` in `parse_options`
**When** ingestion completes
**Then**:
- `atomize_text_rich()` produces 5 levels (`text_utils.py:141-156`)
- Glyph-seed level produces `GlyphSeed` Pydantic objects with `character`, `unicode_name`, `phoneme_hint`, `historic_forms`, `visual_mutations`, `thematic_tags`, `future_seeds`, `position` (`text_utils.py:95-120`, `schemas.py:14-25`)
- Whitespace characters are excluded from glyph-seeds (`text_utils.py:101`)
- Syllabification uses consonant-vowel heuristic splitting (`text_utils.py:41-92`)
- Words extracted via `[\w'-]+` regex (`text_utils.py:19`)
- Sentences split on `[.!?]\s+` or newlines (`text_utils.py:20`)
- Paragraphs split on `\n\s*\n+` (`text_utils.py:21`)
- Each atom stored with `atom_level`, `ordinal`, `content`, `atom_metadata` (length), and `metadata_json` (full `GlyphSeed.model_dump()` for glyph-seed level, `None` otherwise) (`ingestion.py:366-414`)
- Previous atoms for the document are deleted before re-creation (`ingestion.py:367-368`)

**Code evidence:** `test_mvp.py:88-110` verifies `atoms_created > 0` and `atom_count == graph_projected_atom_count`.

#### US-003: Glyph-seed metadata lookup

> As a **researcher**, I want each glyph-seed to carry its phoneme hint, historic script forms, visual mutations, thematic tags, and future evolution seeds so that downstream evolution and remix engines have rich material to work with.

**Given** a character `'A'`
**When** the glyph-seed is constructed
**Then**:
- `phoneme_hint` = `"/eɪ/"` (uppercase) or `"/æ/"` (lowercase) (`glyph_data.py:11-37`)
- `historic_forms` = `["A", "aleph", "phoenician_aleph"]` style ancestors from Greek, Hebrew, Phoenician (`glyph_data.py:40-67`)
- `visual_mutations` = `["lambda", "@", "4", "delta"]` style typographic alternates (`glyph_data.py:70-97`)
- `thematic_tags` = `["beginning", "alpha", "apex", "air", "ascent"]` (`glyph_data.py:100-127`)
- `future_seeds` = 3 items from `GLYPH_POOL` based on deterministic index (`glyph_data.py:154-163`)
- Lookup is case-insensitive for `historic_forms`, `visual_mutations`, `thematic_tags` (uppercased key) but case-sensitive for `phoneme_hint`

**Code evidence:** Static data in `glyph_data.py`. Covered indirectly through ingestion tests that verify `atom_count > 0`.

#### US-004: Conflict marker detection

> As an **operator**, I want files containing git merge conflict markers to be flagged rather than ingested, so that corrupted files do not contaminate the corpus.

**Given** a text file containing `<<<<<<<`, `=======`, `>>>>>>>`, or `|||||||` at line start
**When** the file is ingested
**Then**:
- `has_conflict_markers()` returns `True` (`text_utils.py:37-38`, regex `CONFLICT_MARKER` at line 22)
- The document is saved with `conflict_flag=True`, `conflict_reason="Conflict markers detected"`, `ingested=False`, `ingest_status="conflict"` (`ingestion.py:94-97, 126-130`)
- The file status in the batch response is `"conflict"` with the reason
- Analysis on a conflicted document returns HTTP 409 (`routes.py:150-154`)

**Code evidence:** `test_mvp.py:112-129` (`test_conflict_hygiene_and_analyze_409`).

#### US-005: Checksum-based deduplication

> As an **operator**, I want unchanged files to be skipped on re-ingestion so that repeated runs are fast and idempotent.

**Given** a file that was previously ingested with the same SHA256 checksum
**When** re-ingested without `force=true`
**Then**:
- The document's `ingest_status` is set to `"unchanged"` (`ingestion.py:76-83`)
- The file status in the batch response is `"unchanged"`
- No new atoms are created
- `documents_unchanged` counter increments

**Code evidence:** `ingestion.py:74-83`. The `force_reingest` option (`ingestion.py:45`) overrides this behavior.

#### US-006: Hypergraph projection during ingestion

> As the **system**, I want every ingested document and its atoms projected into the hypergraph so that graph queries are available immediately after ingestion.

**Given** a successfully ingested document with atoms
**When** ingestion completes
**Then**:
- `HypergraphProjector.project_document()` is called with document payload and atom list (`ingestion.py:142-154`)
- A `doc:{id}` node and `atom:{id}` nodes are created in `LocalGraphCache` (always) and Neo4j (when configured) (`hypergraph.py:35-82`)
- `CONTAINS` edges link document node to each atom node
- `ProjectionLedger` rows track per-atom projection status (`ingestion.py:396-413`)
- `graph_projected_atom_count` and `graph_projection_status` are updated on the document
- If projection fails, the document is still saved with `graph_projection_status="failed"` and a warning (`ingestion.py:151-155`)

**Code evidence:** `test_mvp.py:132-143` (`test_hypergraph_integrity`), `test_mvp.py:300-328` (`test_integrity_persists_across_restart`).

#### US-007: Canonicalization of sibling representations

> As the **system**, I want documents with the same normalized stem but different extensions to be linked as sibling representations so that variant relationships are discoverable.

**Given** files `sample.md` and `sample.pdf` both ingested
**When** `apply_canonicalization()` runs after each batch (`ingestion.py:190`)
**Then**:
- Both documents get `DocumentVariant` rows with `variant_type="sibling_representation"` and `variant_group="sibling::{stem}"` (`canonicalization.py:46-66`)
- Each document links to the other via `related_document_id`
- Re-ingestion produces identical variant edges (deterministic rematerialization -- all variants deleted and rebuilt each time) (`canonicalization.py:31`)
- Known RLOS semantic equivalence groups are also linked (`canonicalization.py:34-44`)

**Code evidence:** `test_mvp.py:146-180` (`test_canonicalization_stability_under_partial_reingestion`).

#### US-008: Cross-modal linking

> As the **system**, I want text and media files sharing the same stem to be linked so that cross-modal navigation is possible.

**Given** files `sample.md`, `sample.png`, and `sample.wav` ingested together
**When** `_apply_cross_modal_links()` runs (`ingestion.py:191`)
**Then**:
- Text documents gain `cross_modal_links` in their provenance JSON pointing to media documents (`ingestion.py:498-510`)
- Media documents gain reverse `cross_modal_links` pointing to text documents (`ingestion.py:511-521`)
- Links include `target_document_id`, `target_modality`, and anchor information

**Code evidence:** `test_mvp.py:224-243` (`test_multimodal_linkage`).

#### US-009: PDF text extraction

> As an **operator**, I want PDF files to have their text content extracted and atomized just like text files.

**Given** a `.pdf` file
**When** ingested
**Then**:
- `pypdf.PdfReader` extracts text from all pages (`ingestion.py:255-260`)
- `page_count` and `char_count` are recorded in segments (`ingestion.py:103-108`)
- Extracted text is atomized through the same 5-level pipeline

**Code evidence:** `test_mvp.py:88-110` includes `sample_corpus["pdf"]` in the batch.

#### US-010: Image and audio metadata extraction

> As an **operator**, I want image and audio files to have their metadata extracted even when no text content is available.

**Given** an image (`.png`, `.jpg`, `.jpeg`, `.webp`) or audio (`.wav`, `.mp3`, `.flac`) file
**When** ingested
**Then**:
- **Image**: `filename`, `size_bytes`, `caption_candidate` (from stem), `embedding_ref`, optional `width`/`height`/`mode` via PIL (`ingestion.py:266-281`)
- **Audio (WAV)**: `sample_rate`, `channels`, `duration_seconds`, `transcription_segments` (placeholder), `prosody_summary` (placeholder) via `wave` stdlib (`ingestion.py:283-314`)
- No atomization occurs for image/audio (no `extracted_text`)

**Code evidence:** `test_mvp.py:224-243` verifies `segments` exist for image and audio docs.

#### US-011: Seed corpus registry and provisioning

> As an **admin**, I want to provision canonical seed texts from Project Gutenberg so that the ARC4N corpus has foundational literary material.

**Given** a seed title matching the registry (The Odyssey, The Divine Comedy, Leaves of Grass, Ulysses, Frankenstein)
**When** `POST /api/v1/corpus/seed` is called with the title
**Then**:
- The text is downloaded from Gutenberg to `seeds_dir/{safe_name}.txt` (`seed_corpus.py:108-109`)
- The file is then ingested via the standard pipeline (`routes.py:658-669`)
- `GET /api/v1/corpus/seeds` lists all registry entries with provisioning status (`seed_corpus.py:60-75`)

**Code evidence:** `seed_corpus.py:21-52` (SEED_REGISTRY), `routes.py:638-680`.

#### US-012: Ingest job tracking

> As a **viewer**, I want to check the status of an ingestion job so that I can monitor progress and review results.

**Given** a completed ingestion batch producing an `IngestJob`
**When** `GET /api/v1/ingest/jobs/{id}` is called
**Then**:
- Returns `ingest_job_id`, `status`, per-file statuses, `documents_ingested`, `atoms_created`, `documents_unchanged`, `provenance_digest`, `ingest_scope`, `warnings`, `errors` (`ingestion.py:209-226`, `schemas.py:50-60`)

**Code evidence:** `test_mvp.py:35-37` (job status check in `_ingest` helper).

#### US-013: Path traversal prevention

> As the **system**, I want to reject any source paths that escape the `corpus_root` so that ingestion cannot access arbitrary filesystem locations.

**Given** a source path that resolves outside `corpus_root`
**When** `POST /api/v1/ingest/batch` is called
**Then**:
- `_resolve_path()` raises `ValueError("Path escapes corpus_root...")` (`ingestion.py:228-234`)
- The API returns HTTP 400

**Code evidence:** `test_mvp.py:76-85` (`test_ingest_path_traversal_rejection`).

### P2 -- Partially Built

#### US-014: Dual atomization tracks (literary vs. glyphic seed)

> As an **operator**, I want to select between a "literary" track (word/sentence/paragraph) and a "glyphic seed" track (glyph-seed/syllable) so that ingestion can be tuned to the analysis purpose.

**Current state**: The `parse_options` dict accepts `atom_levels` to filter which of the 5 levels are produced (`ingestion.py:43`), but there are no named track presets (e.g., `"literary"`, `"glyphic_seed"`). Track selection is not persisted in document provenance.

**Gap**: No `atom_tracks` parse option, no named presets, no provenance recording of track selection.

**Vision ref:** AB01-T002 -- Dual Atomization Tracks.

#### US-015: Deterministic atom filename schema

> As an **operator**, I want each atom to have a canonical filename (e.g., `ODYSSEY_WORD_0001_Sing.txt`) so that exported atoms are parseable and remix-reproducible.

**Current state**: Atoms have `document_id`, `atom_level`, `ordinal`, and `content` but no deterministic filename. The `ordinal` field provides sequencing but the naming convention from AB-PLAN-01 (e.g., `TEXT_LEVEL_ORDINAL_Token.txt`) is not implemented.

**Gap**: No naming helper in `text_utils.py`, no filename field on `Atom` model, no collision handling.

**Vision ref:** AB01-T003 -- Deterministic Atom Filename Schema.

#### US-016: Full-scope ingestion

> As an **operator**, I want to ingest all supported files under `corpus_root` when no `source_paths` are provided so that the entire corpus can be processed in one call.

**Current state**: When `source_paths` is empty, `collect_current_corpus_paths()` recursively finds all supported files under `corpus_root`, skipping `.git`, `.venv`, `__pycache__`, `object_storage`, `.pytest_cache` and dotfiles (`canonicalization.py:69-96`). The `ingest_scope` is set to `"full"` (`ingestion.py:40`).

**Gap**: No progress reporting for large full-scope runs. No parallelism or streaming. No configurable skip patterns beyond the hardcoded set.

### P3+ -- Vision

#### US-017: Atom library export pipeline

> As an **operator**, I want to export atomized documents into a navigable filesystem tree (`/ARC4N/SEED_TEXTS/<TEXT>/<LEVEL>/`) with per-document manifests so that atoms are accessible outside the database.

**Vision ref:** AB01-T004 -- Atom Library Export Pipeline.

#### US-018: Ingestion profiles

> As an **operator**, I want to run `python scripts/ingest_corpus.py --profile arc4n-seed` so that repeatable ingestion configurations are stored as named profiles.

**Vision ref:** AB01-T001 -- Seed Corpus Registry + Profiles.

#### US-019: Cartridge and thread plan scaffold sync

> As a **knowledge operator**, I want ingestion to synchronize with cartridge and thread plan scaffolding so that newly ingested corpus material is reflected in the ARC4N artifact index.

**Vision ref:** AB01-T008 -- Cartridge + Thread Plan Scaffold Sync.

#### US-020: OCR for images and transcription for audio

> As an **operator**, I want image OCR and audio transcription to produce text that can be atomized, not just metadata placeholders.

**Current state**: Image ingestion produces an empty `ocr_spans` list and audio produces empty `transcription_segments` text. No OCR or ASR integration exists.

#### US-021: Streaming/progress reporting for large ingestion jobs

> As an **operator**, I want ingestion of large corpora to report progress incrementally rather than blocking until completion.

**Current state**: `ingest_batch` is synchronous and returns only after all files are processed. The async job system exists but is not integrated with the ingestion pipeline for progress streaming.

## Functional Requirements

### Ingestion Pipeline

- **FR-001** [MUST] The system MUST accept `POST /api/v1/ingest/batch` with `source_paths` (list of strings), `modalities` (list of strings for filtering), and `parse_options` (dict). Implemented: `routes.py:87-111`, `schemas.py:27-30`.
- **FR-002** [MUST] Source paths MUST be resolved against `corpus_root` and rejected if they escape it. Implemented: `ingestion.py:228-241`.
- **FR-003** [MUST] Modality MUST be detected from file extension: `.md/.txt/.yaml/.yml` = text, `.pdf` = pdf, `.png/.jpg/.jpeg/.webp` = image, `.wav/.mp3/.flac` = audio. Implemented: `ingestion.py:22-25, 243-253`.
- **FR-004** [MUST] Each file MUST be SHA256 checksummed before processing. Implemented: `text_utils.py:29-34`.
- **FR-005** [MUST] Files with unchanged checksums MUST be skipped unless `force=true` in `parse_options`. Implemented: `ingestion.py:74-83`.
- **FR-006** [MUST] Raw file payloads MUST be copied to `object_storage_root/{checksum}{ext}`. Implemented: `ingestion.py:416-423`.
- **FR-007** [MUST] Text files containing git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`, `|||||||`) MUST be flagged with `conflict_flag=True` and NOT marked as ingested. Implemented: `text_utils.py:22, 37-38`, `ingestion.py:94-97, 126-130`.
- **FR-008** [MUST] The batch response MUST include per-file status, `documents_ingested`, `documents_unchanged`, `atoms_created`, `provenance_digest`, `ingest_scope`, `warnings`, and `errors`. Implemented: `ingestion.py:194-207`.
- **FR-009** [MUST] An `IngestJob` row MUST be created for every batch with status `running` -> `completed` or `completed_with_errors`. Implemented: `ingestion.py:47-49, 203-206`.
- **FR-010** [MUST] `GET /api/v1/ingest/jobs/{id}` MUST return the full job status. Implemented: `routes.py:114-134`.

### Atomization

- **FR-011** [MUST] When `atomize=true` (default), text content MUST be decomposed into exactly 5 levels: `glyph-seed`, `syllable`, `word`, `sentence`, `paragraph`. Implemented: `text_utils.py:24, 141-156`.
- **FR-012** [MUST] Glyph-seeds MUST be `GlyphSeed` objects with `character`, `unicode_name`, `phoneme_hint`, `historic_forms`, `visual_mutations`, `thematic_tags`, `future_seeds`, `position`. Implemented: `schemas.py:14-25`, `text_utils.py:95-120`.
- **FR-013** [MUST] Whitespace characters MUST be excluded from glyph-seed output. Implemented: `text_utils.py:101`.
- **FR-014** [MUST] Glyph-seed `metadata_json` MUST store the full `GlyphSeed.model_dump()`. Other levels MUST have `metadata_json=None`. Implemented: `ingestion.py:377-382`.
- **FR-015** [MUST] Syllabification MUST use the deterministic consonant-vowel heuristic in `syllabify()`. Implemented: `text_utils.py:41-92`.
- **FR-016** [MUST] Word tokenization MUST use the `[\w'-]+` Unicode regex. Implemented: `text_utils.py:19`.
- **FR-017** [MUST] Re-ingestion of a document MUST delete all prior atoms before re-creating. Implemented: `ingestion.py:367-368`.
- **FR-018** [SHOULD] The system SHOULD support `atom_levels` in `parse_options` to produce only a subset of the 5 levels. Implemented: `ingestion.py:43, 373`.
- **FR-019** [SHOULD] The system SHOULD provide named atomization track presets (`literary`, `glyphic_seed`). Not yet implemented (AB01-T002).
- **FR-020** [SHOULD] Each atom SHOULD have a deterministic canonical filename for export. Not yet implemented (AB01-T003).

### Glyph Metadata

- **FR-021** [MUST] IPA phoneme hints MUST cover all 26 Latin letters (upper and lower case). Implemented: `glyph_data.py:10-37`.
- **FR-022** [MUST] Historic forms MUST include Greek, Hebrew, and (where applicable) Phoenician ancestors for A-Z. Implemented: `glyph_data.py:40-67`.
- **FR-023** [MUST] Visual mutations MUST include typographic alternates for A-Z. Implemented: `glyph_data.py:70-97`.
- **FR-024** [MUST] Thematic tags MUST include 3-5 symbolic associations per letter. Implemented: `glyph_data.py:100-127`.
- **FR-025** [MUST] Future seeds MUST return 3 items from `GLYPH_POOL` using deterministic index mapping. Implemented: `glyph_data.py:154-163`.
- **FR-026** [SHOULD] Glyph metadata SHOULD be extensible to cover Unicode characters beyond Latin A-Z. Currently returns empty lists for non-Latin characters.

### Hypergraph Projection

- **FR-027** [MUST] Every ingested document MUST be projected as a `doc:{id}` node in the local graph cache. Implemented: `hypergraph.py:36-38`.
- **FR-028** [MUST] Every atom MUST be projected as an `atom:{id}` node with a `CONTAINS` edge from its document node. Implemented: `hypergraph.py:40-52`.
- **FR-029** [MUST] Projection MUST also write to Neo4j when the driver is configured. Implemented: `hypergraph.py:54-81`.
- **FR-030** [MUST] `ProjectionLedger` rows MUST track projection status per atom. Implemented: `ingestion.py:396-413, 459-480`.
- **FR-031** [MUST] Projection failure MUST NOT prevent document save; the document MUST be saved with `graph_projection_status="failed"`. Implemented: `ingestion.py:151-155`.

### Canonicalization

- **FR-032** [MUST] After each batch, `apply_canonicalization()` MUST link documents with the same normalized stem as `sibling_representation` variants. Implemented: `canonicalization.py:47-66`.
- **FR-033** [MUST] Canonicalization MUST be deterministic: all `DocumentVariant` rows are deleted and rebuilt from scratch. Implemented: `canonicalization.py:31`.
- **FR-034** [MUST] Known semantic equivalence groups (RLOS spec variants) MUST be linked as `semantic_equivalence`. Implemented: `canonicalization.py:34-44`.

### Cross-Modal

- **FR-035** [MUST] Text and media documents sharing the same stem MUST be linked via `cross_modal_links` in provenance. Implemented: `ingestion.py:482-521`.
- **FR-036** [SHOULD] Cross-modal links SHOULD include anchor information (text span, image region, audio time range). Implemented with stub anchors: `ingestion.py:503-507`.

### Seed Corpus

- **FR-037** [MUST] The seed registry MUST include The Odyssey, The Divine Comedy, Leaves of Grass, Ulysses, and Frankenstein with Gutenberg URLs. Implemented: `seed_corpus.py:21-52`.
- **FR-038** [MUST] `POST /api/v1/corpus/seed` MUST download the text and trigger ingestion. Implemented: `routes.py:644-680`.
- **FR-039** [MUST] Already-provisioned seeds MUST not be re-downloaded. Implemented: `seed_corpus.py:83-88`.
- **FR-040** [SHOULD] The system SHOULD support adding custom seed texts beyond the hardcoded registry. Not yet implemented.

### Export

- **FR-041** [MAY] The system MAY export atomized documents as a filesystem tree with manifests. Not yet implemented (AB01-T004).
- **FR-042** [MAY] Exported atoms MAY use the deterministic filename schema. Not yet implemented (AB01-T003).

## Key Entities

### Document (`models.py:30-51`)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `path` | String(1024) UNIQUE | Resolved absolute path |
| `title` | String(512) | Filename |
| `modality` | String(32) | `text`, `pdf`, `image`, `audio`, `binary` |
| `checksum` | String(128) | SHA256 of source file |
| `size_bytes` | Integer | File size |
| `ingested` | Boolean | True if successfully processed |
| `ingest_status` | String(32) | `pending`, `parsed`, `ingested`, `unchanged`, `conflict`, `ingested_with_warnings` |
| `conflict_flag` | Boolean | True if conflict markers detected |
| `conflict_reason` | String(256) | Reason text |
| `provenance` | JSON | Extracted text, segments, checksums, raw storage path, cross-modal links |
| `modality_status` | JSON | Per-modality completion (`complete`, `partial`, `failed`) |
| `provider_summary` | JSON | Ingestion and projection provider names |
| `atom_count` | Integer | Total atoms created |
| `graph_projected_atom_count` | Integer | Atoms successfully projected |
| `graph_projection_status` | String(32) | `pending`, `complete`, `partial`, `failed` |

### Atom (`models.py:76-88`)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `document_id` | FK -> documents | Parent document |
| `atom_level` | String(32) | `glyph-seed`, `syllable`, `word`, `sentence`, `paragraph` |
| `ordinal` | Integer | Position within level (1-indexed) |
| `content` | Text | Atom text content (single char for glyph-seeds) |
| `atom_metadata` | JSON | `{"length": N}` |
| `metadata_json` | JSON nullable | Full `GlyphSeed` dict for glyph-seed level; `None` otherwise |

### IngestJob (`models.py:18-27`)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `status` | String(32) | `pending`, `running`, `completed`, `completed_with_errors` |
| `request_payload` | JSON | Original request parameters |
| `result_summary` | JSON | Full result including per-file statuses |
| `errors` | JSON | Error list |

### DocumentVariant (`models.py:55-73`)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `document_id` | FK -> documents | Source document |
| `variant_group` | String(128) | Group identifier (`sibling::{stem}`, `rlos_spec_v1_equivalent`) |
| `variant_type` | String(64) | `sibling_representation`, `semantic_equivalence` |
| `related_document_id` | FK -> documents | Linked document |

### ProjectionLedger (`models.py:277-291`)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `document_id` | FK -> documents | Parent document |
| `atom_id` | String(36) | Atom UUID |
| `status` | String(32) | `pending`, `projected`, `failed` |
| `attempt_count` | Integer | Retry counter |
| `last_error` | String(512) | Error message if failed |

## Edge Cases

### Covered by tests

- Path traversal outside `corpus_root` (`test_ingest_path_traversal_rejection`)
- File not found in batch (`ingestion.py:62-65`)
- Conflict markers in YAML files (`test_conflict_hygiene_and_analyze_409`)
- Analysis blocked on conflicted documents (HTTP 409)
- Canonicalization stability under partial re-ingestion (`test_canonicalization_stability_under_partial_reingestion`)
- Multi-modal linkage by stem matching (`test_multimodal_linkage`)
- Integrity persistence across app restart (`test_integrity_persists_across_restart`)
- Empty PDF (blank page produces empty text -- `conftest.py:62-66`)
- Minimal valid PNG and WAV fixtures (`conftest.py:69-83`)

### Not covered / known gaps

- **Unicode in filenames**: Paths with Unicode characters are supported (quoting convention) but no dedicated test exists for Unicode stems in canonicalization.
- **Large file handling**: No test for files larger than available memory. The `sha256_file` reads in 8KB chunks but `path.read_text()` for text files reads entirely into memory.
- **Concurrent ingestion**: No locking mechanism if two concurrent `ingest_batch` calls process the same file. The upsert uses `select` then `add`/update which is not atomic.
- **Binary files**: Files with unrecognized extensions are classified as `"binary"` modality but no specific handling exists (no text extraction, no metadata).
- **MP3/FLAC audio**: Only WAV has metadata extraction (`wave` module). MP3 and FLAC produce only `filename` and `size_bytes`.
- **PIL not installed**: Image metadata gracefully degrades to `width=None, height=None` but this is not tested.
- **Neo4j projection chunking**: Atoms are projected in chunks of 500 (`PROJECTION_CHUNK_SIZE`). No test for documents with >500 atoms.
- **Syllabification edge cases**: Single-character words, all-consonant words, and non-Latin Unicode words are handled minimally (return `[word]` as fallback).
- **Empty text extraction from PDF**: PDFs with images-only produce empty text. Atoms are not created, but the document is marked as ingested.

## Success Criteria

1. **Ingestion completeness**: Every supported file type (text, YAML, PDF, PNG, JPG, WEBP, WAV, MP3, FLAC) is accepted and produces a `Document` row with correct modality and provenance.
2. **Atomization correctness**: Text documents produce atoms at all 5 levels. Glyph-seed atoms carry full `GlyphSeed` metadata. Atom counts match between SQL and hypergraph.
3. **Determinism**: Re-ingesting the same file with the same checksum produces `unchanged` status. Canonicalization yields identical variant edges across runs.
4. **Conflict safety**: No conflicted document is marked as `ingested=True`. Analysis is blocked on conflicted documents.
5. **Provenance traceability**: Every document has `checksum`, `raw_storage_path`, `segments`, and `hypergraph` references in its provenance JSON.
6. **Path security**: No source path outside `corpus_root` is accepted.
7. **Graph consistency**: `atom_count == graph_projected_atom_count` when `graph_projection_status == "complete"`. Integrity endpoint confirms consistency.
8. **Cross-modal linking**: Text and media files with matching stems are linked bidirectionally.
9. **Performance baseline**: Ingestion of the 5 seed texts (Odyssey, Divine Comedy, Leaves of Grass, Ulysses, Frankenstein) completes within reasonable time and produces >100K atoms total.
