# Ingestion & Atomization -- Implementation Plan

## Technical Context

| Component | Version / Stack |
|-----------|----------------|
| Language | Python >=3.11 |
| Web framework | FastAPI (uvicorn) |
| ORM | SQLAlchemy 2.0 (`mapped_column` style) |
| Migrations | Alembic (SQLite default, PostgreSQL via docker) |
| Schema validation | Pydantic v2 + `pydantic-settings` |
| Testing | pytest + `FastAPI.TestClient`, isolated SQLite per test via `tmp_path` |
| PDF parsing | pypdf (`PdfReader`) |
| Image metadata | Pillow (optional, graceful fallback) |
| Audio metadata | `wave` stdlib (WAV only) |
| Graph store | Neo4j (`neo4j` Python driver) + `LocalGraphCache` fallback |
| Settings | `pydantic-settings`, `NEXUS_` prefix, `.env` file |
| Docker | `docker-compose.yml` for PostgreSQL + Neo4j |

## Project Structure

Files directly relevant to the ingestion-atomization domain:

```
src/nexus_babel/
  main.py                           # create_app() factory, lifespan handler (seeds API keys + policies)
  config.py                         # Settings (corpus_root, object_storage_root, bootstrap keys, etc.)
  db.py                             # DBManager wrapper for engine + sessionmaker
  models.py                         # Document, Atom, IngestJob, DocumentVariant, ProjectionLedger
  schemas.py                        # GlyphSeed, IngestBatchRequest/Response, IngestFileStatus, IngestJobResponse
  api/
    routes.py                       # POST /ingest/batch, GET /ingest/jobs/{id}, POST /corpus/seed, GET /corpus/seeds
  services/
    ingestion.py                    # IngestionService.ingest_batch(), get_job_status(), all private helpers
    text_utils.py                   # atomize_text(), atomize_text_rich(), syllabify(), sha256_file(), has_conflict_markers()
    glyph_data.py                   # PHONEME_HINTS, HISTORIC_FORMS, VISUAL_MUTATIONS, THEMATIC_TAGS, GLYPH_POOL
    canonicalization.py             # apply_canonicalization(), collect_current_corpus_paths()
    hypergraph.py                   # HypergraphProjector, LocalGraphCache
    seed_corpus.py                  # SeedCorpusService, SEED_REGISTRY

scripts/
  ingest_corpus.py                  # CLI corpus ingestion script

tests/
  conftest.py                       # test_settings, client, auth_headers, sample_corpus fixtures
  test_mvp.py                       # Core integration tests (ingestion, conflict, hypergraph, canonicalization, multimodal)

alembic/
  versions/
    20260218_0001_initial.py        # Initial schema
    20260218_0002_wave2_alpha.py    # Wave-2 additions

docs/
  corpus/                           # Seed text source documents
  alexandria_babel/
    AB-PLAN-01_Build_Tickets.md     # Planning tickets for this domain
```

## Data Models

### Document (ORM: `models.py:30-51`)

The central entity. One row per ingested file. Path is unique and stored as resolved absolute path.

```
documents
  id              VARCHAR(36) PK    -- uuid4
  path            VARCHAR(1024) UQ  -- resolved absolute path, indexed
  title           VARCHAR(512)      -- filename
  modality        VARCHAR(32)       -- 'text'|'pdf'|'image'|'audio'|'binary', indexed
  checksum        VARCHAR(128)      -- SHA256 hex digest, indexed
  size_bytes      INTEGER           -- stat().st_size
  ingested        BOOLEAN           -- True after successful processing
  ingest_status   VARCHAR(32)       -- state machine: pending -> parsed -> ingested|unchanged|conflict
  conflict_flag   BOOLEAN           -- True if merge markers detected
  conflict_reason VARCHAR(256)      -- human-readable reason
  provenance      JSON              -- extracted_text, segments, checksum, raw_storage_path, cross_modal_links, hypergraph
  modality_status JSON              -- {modality: 'complete'|'partial'|'failed'}
  provider_summary JSON             -- {ingestion_provider, projection_provider}
  atom_count      INTEGER           -- len(atoms) after atomization
  graph_projected_atom_count INTEGER -- atoms projected to hypergraph
  graph_projection_status VARCHAR(32) -- 'pending'|'complete'|'partial'|'failed'
  created_at      DATETIME(tz)
  updated_at      DATETIME(tz)
```

**State machine** for `ingest_status`:
```
pending -> parsed -> ingested               (happy path)
                  -> ingested_with_warnings  (projection failed)
       -> conflict                          (merge markers detected)
       -> unchanged                         (checksum match, skip)
```

### Atom (ORM: `models.py:76-88`)

One row per atomic unit. Cascade-deleted with parent document.

```
atoms
  id              VARCHAR(36) PK    -- uuid4
  document_id     VARCHAR(36) FK    -- -> documents.id ON DELETE CASCADE, indexed
  atom_level      VARCHAR(32)       -- 'glyph-seed'|'syllable'|'word'|'sentence'|'paragraph', indexed
  ordinal         INTEGER           -- 1-indexed position within level
  content         TEXT              -- atom text content
  atom_metadata   JSON              -- {"length": N}
  metadata_json   JSON NULLABLE     -- GlyphSeed dict for glyph-seed level; NULL otherwise
  created_at      DATETIME(tz)
```

**GlyphSeed schema** (stored in `metadata_json` for `atom_level='glyph-seed'`):
```python
class GlyphSeed(BaseModel):
    character: str            # single character
    unicode_name: str         # unicodedata.name() or U+XXXX
    phoneme_hint: str | None  # IPA from PHONEME_HINTS
    historic_forms: list[str] # Greek/Hebrew/Phoenician ancestors
    visual_mutations: list[str] # typographic alternates
    thematic_tags: list[str]  # symbolic associations
    future_seeds: list[str]   # 3 items from GLYPH_POOL
    position: int             # 0-indexed position (excluding whitespace)
```

### IngestJob (ORM: `models.py:18-27`)

One row per `ingest_batch` call. Tracks overall batch status.

```
ingest_jobs
  id              VARCHAR(36) PK
  status          VARCHAR(32)       -- 'pending'|'running'|'completed'|'completed_with_errors'
  request_payload JSON              -- {source_paths, modalities, parse_options}
  result_summary  JSON              -- {files, documents_ingested, atoms_created, ...}
  errors          JSON              -- list of error strings
  created_at      DATETIME(tz)
  updated_at      DATETIME(tz)
```

### DocumentVariant (ORM: `models.py:55-73`)

Links sibling representations and semantic equivalences. Unique constraint on `(document_id, variant_group, variant_type, related_document_id)`.

```
document_variants
  id                  VARCHAR(36) PK
  document_id         VARCHAR(36) FK  -- -> documents.id ON DELETE CASCADE
  variant_group       VARCHAR(128)    -- 'sibling::{stem}' or 'rlos_spec_v1_equivalent'
  variant_type        VARCHAR(64)     -- 'sibling_representation' or 'semantic_equivalence'
  related_document_id VARCHAR(36) FK  -- -> documents.id ON DELETE SET NULL (nullable)
  created_at          DATETIME(tz)
```

### ProjectionLedger (ORM: `models.py:277-291`)

Per-atom projection tracking. Unique constraint on `(document_id, atom_id)`.

```
projection_ledger
  id              VARCHAR(36) PK
  document_id     VARCHAR(36) FK    -- -> documents.id ON DELETE CASCADE
  atom_id         VARCHAR(36)       -- atom UUID (not FK for flexibility)
  status          VARCHAR(32)       -- 'pending'|'projected'|'failed'
  attempt_count   INTEGER           -- retry counter
  last_error      VARCHAR(512)      -- error message
  created_at      DATETIME(tz)
  updated_at      DATETIME(tz)
```

## API Contracts

### POST /api/v1/ingest/batch

**Auth**: operator (minimum)
**Request** (`IngestBatchRequest`):
```json
{
  "source_paths": ["path/to/file.md", "path/to/file.pdf"],
  "modalities": ["text", "pdf"],
  "parse_options": {
    "atomize": true,
    "atom_levels": ["glyph-seed", "syllable", "word", "sentence", "paragraph"],
    "force": false
  }
}
```

- `source_paths`: Relative to `corpus_root` or absolute (must be within `corpus_root`). Empty = full corpus scan.
- `modalities`: Filter by modality. Empty = all modalities.
- `parse_options.atomize`: Enable/disable atomization (default `true`).
- `parse_options.atom_levels`: Subset of 5 levels to produce (default all 5).
- `parse_options.force`: Force re-ingestion even if checksum unchanged (default `false`).

**Response** (`IngestBatchResponse`):
```json
{
  "ingest_job_id": "uuid",
  "documents_ingested": 3,
  "documents_unchanged": 0,
  "atoms_created": 1547,
  "provenance_digest": "sha256-of-all-checksums",
  "ingest_scope": "partial",
  "warnings": []
}
```

**Error cases**:
- 400: Path escapes `corpus_root`
- 401: Missing/invalid API key
- 403: Insufficient role (viewer cannot ingest)

### GET /api/v1/ingest/jobs/{job_id}

**Auth**: viewer (minimum)
**Response** (`IngestJobResponse`):
```json
{
  "ingest_job_id": "uuid",
  "status": "completed",
  "files": [
    {"path": "/abs/path/file.md", "status": "ingested", "document_id": "uuid", "error": null},
    {"path": "/abs/path/conflict.yaml", "status": "conflict", "document_id": "uuid", "error": "Conflict markers detected"}
  ],
  "errors": [],
  "documents_ingested": 1,
  "documents_unchanged": 0,
  "atoms_created": 523,
  "provenance_digest": "sha256",
  "ingest_scope": "partial",
  "warnings": []
}
```

### POST /api/v1/corpus/seed

**Auth**: admin
**Request** (`SeedProvisionRequest`):
```json
{"title": "The Odyssey"}
```

**Response** (`SeedProvisionResponse`):
```json
{
  "title": "The Odyssey",
  "status": "provisioned",
  "local_path": "/path/to/seeds/the_odyssey.txt",
  "document_id": "uuid"
}
```

### GET /api/v1/corpus/seeds

**Auth**: viewer
**Response** (`SeedTextListResponse`):
```json
{
  "seeds": [
    {
      "title": "The Odyssey",
      "author": "Homer",
      "language": "English",
      "source_url": "https://www.gutenberg.org/...",
      "local_path": "/path/or/null",
      "atomization_status": "provisioned"
    }
  ]
}
```

## Service Architecture

### IngestionService (`ingestion.py`)

The central service class. Injected with `Settings` and `HypergraphProjector`.

**`ingest_batch()` flow:**

```
1. Determine scope: partial (explicit paths) or full (corpus scan)
2. Resolve paths against corpus_root (reject traversal)
3. FOR each path:
   a. Validate file exists
   b. Detect modality from extension
   c. Apply modality filter (skip if not in requested modalities)
   d. SHA256 checksum
   e. Check for existing document with same path + checksum (skip if unchanged)
   f. Copy raw payload to object_storage
   g. Extract text/metadata by modality:
      - text: read_text() + derive_text_segments()
      - pdf: PdfReader extract_text() + page_count
      - image: stat + optional PIL dimensions + caption_candidate
      - audio: stat + wave metadata (WAV only)
   h. Check for conflict markers (text only)
   i. Upsert Document row
   j. If no conflict and atomize enabled: create atoms via atomize_text_rich()
   k. Project document + atoms to hypergraph
   l. Update projection ledger
   m. Set provenance, modality_status, provider_summary
4. apply_canonicalization() -- link sibling representations
5. _apply_cross_modal_links() -- link text <-> media by stem
6. Compute provenance digest (SHA256 of sorted checksums)
7. Finalize IngestJob status
```

**Key helpers:**
- `_resolve_path()`: Resolves relative/absolute paths, rejects traversal
- `_detect_modality()`: Extension -> modality string
- `_extract_pdf_text()`: pypdf page iteration
- `_extract_image_metadata()`: stat + optional PIL
- `_extract_audio_metadata()`: wave module (WAV) or basic stat
- `_upsert_document()`: SELECT by path, create or update
- `_create_atoms()`: Deletes old atoms, calls `atomize_text_rich()`, creates Atom + ProjectionLedger rows
- `_store_raw_payload()`: Copy to `{checksum}{ext}` in object storage
- `_derive_text_segments()`: Paragraphs, heading candidates, citation markers
- `_derive_modality_status()`: Complete/partial/pending per modality
- `_update_projection_ledger()`: Set status + increment attempt count
- `_apply_cross_modal_links()`: Group updated docs by stem, link text <-> media

### Atomization Functions (`text_utils.py`)

Two entry points:
- `atomize_text(text) -> dict[str, list[str]]`: Fast path, plain strings for all levels
- `atomize_text_rich(text) -> dict[str, Any]`: Full path with `GlyphSeed` objects at level 0

Both share the same word/sentence/paragraph splitting logic. The rich path additionally calls `atomize_glyphs_rich()` which iterates characters, skips whitespace, looks up metadata from `glyph_data.py`.

**Syllabification algorithm** (`syllabify()`):
1. Words of length <=2 return as-is
2. Iterate characters; on vowel, consume consecutive vowels
3. Look ahead for consonant cluster before next vowel
4. If >=2 consonants before next vowel, keep all but last in current syllable
5. Split; start new syllable
6. Trailing single consonant merges into previous syllable

### Glyph Data (`glyph_data.py`)

Pure static data module. No runtime dependencies. Five lookup dicts keyed on single characters:
- `PHONEME_HINTS`: 52 entries (A-Z upper + lower), IPA strings
- `HISTORIC_FORMS`: 26 entries (A-Z upper), lists of ancestor glyphs
- `VISUAL_MUTATIONS`: 26 entries, lists of typographic alternates
- `THEMATIC_TAGS`: 26 entries, lists of symbolic associations (3-5 per letter)
- `GLYPH_POOL`: 24 extended glyphs for evolution targets

`get_future_seeds(char)` maps character to 3 pool items via `(ord(char.upper()) - ord('A')) % len(GLYPH_POOL)`.

### Canonicalization (`canonicalization.py`)

**`apply_canonicalization(session)`:**
1. Load all ingested documents
2. Delete all existing `DocumentVariant` rows (full rematerialization)
3. Check for RLOS semantic equivalence (hardcoded path substring match)
4. Group all documents by `_normalize_stem(path)` (lowercase, non-alphanumeric -> hyphens)
5. For groups with 2+ docs, create bidirectional `sibling_representation` links

**`collect_current_corpus_paths(root)`:**
Recursively finds all files under `root` with supported extensions, skipping `.git`, `.venv`, `__pycache__`, `object_storage`, `.pytest_cache`, and dotfiles. Returns sorted list.

### HypergraphProjector (`hypergraph.py`)

Dual-write architecture:
- **Always**: Writes to `LocalGraphCache` (in-memory `dict[str, dict]` nodes + `list[dict]` edges)
- **When configured**: Also writes to Neo4j via Cypher queries

`project_document()` clears prior local projection for the document, then creates `doc:` node + `atom:` nodes + `CONTAINS` edges. Neo4j writes use `MERGE` for idempotency and chunk atoms in batches of 500.

`integrity_for_document()` compares `atom_count` vs `graph_projected_atom_count` and optionally queries Neo4j for verification.

### SeedCorpusService (`seed_corpus.py`)

Manages the 5 canonical seed texts. Downloads from Project Gutenberg via `urllib.request.urlretrieve`. Files stored as `{seeds_dir}/{safe_name}.txt`. Idempotent -- skips download if file exists.

## Research Notes

### Dependencies

| Dependency | Used For | Required? |
|------------|----------|-----------|
| `pypdf` | PDF text extraction | Yes (for PDF modality) |
| `Pillow` (PIL) | Image dimensions | No (graceful fallback to None) |
| `neo4j` | Graph database driver | No (falls back to LocalGraphCache) |
| `pydantic` | Schema validation | Yes |
| `pydantic-settings` | Config management | Yes |
| `sqlalchemy` | ORM | Yes |
| `alembic` | Migrations | Yes (for schema changes) |

### Complexity / Performance Considerations

- **Memory**: `atomize_text_rich()` creates a `GlyphSeed` Pydantic object per non-whitespace character. For Ulysses (~265K words, ~1.5M characters), this produces ~1.2M GlyphSeed objects in memory. Each carries 7 fields. Estimated memory: ~200-400MB for a single large text.
- **Database writes**: Atom creation for a large text generates >1M INSERT statements. Currently uses `session.add_all()` in a single flush. Consider bulk insert for performance.
- **Hypergraph**: `LocalGraphCache` is an in-memory dict. For 5 seed texts, expect ~5M atom nodes and edges. Memory footprint grows linearly.
- **Canonicalization**: Full rematerialization (delete all + rebuild) is safe but potentially slow with many documents. The `O(n^2)` pairwise linking within stem groups is bounded by typical group sizes (2-5 variants).

### Known Risks

1. **Concurrent ingestion**: No row-level locking on Document upsert. Two concurrent calls processing the same file could produce duplicate atoms or corrupt provenance. Mitigation: Advisory lock or serial queue.
2. **Large file text extraction**: `path.read_text()` loads entire file into memory. For multi-GB text files this will OOM. Mitigation: Streaming extraction with chunk-based atomization.
3. **Syllabification accuracy**: The CV-heuristic is English-biased and produces incorrect splits for many non-English words, compound words, and unusual phonotactics. Mitigation: Accept as "good enough" for deterministic replay; offer plugin point for language-specific syllabifiers.
4. **Neo4j chunking**: 500-atom chunks may be too small for large documents (>1M atoms). Each chunk is a separate transaction. Mitigation: Tune `PROJECTION_CHUNK_SIZE` based on Neo4j cluster capacity.
5. **PIL optional dependency**: Tests do not verify the PIL-absent fallback path. The `conftest.py` sample PNG is minimal and may not trigger actual PIL processing if PIL happens to be installed.
6. **Seed corpus download**: `urllib.request.urlretrieve` has no timeout and no retry. Large Gutenberg texts (Ulysses is ~1.5MB) could hang indefinitely. Mitigation: Add timeout and retry with backoff.

### Future Architecture Considerations

- **Atom filename schema** (AB01-T003): Should be a pure function `(document_title, atom_level, ordinal, token_preview) -> filename` in `text_utils.py`. Must handle Unicode normalization, punctuation stripping, and collision suffixing. Consider adding an `atom_filename` column to the `Atom` model.
- **Dual tracks** (AB01-T002): Can be implemented as a mapping from track name to `atom_levels` subset: `{"literary": ["word", "sentence", "paragraph"], "glyphic_seed": ["glyph-seed", "syllable"]}`. Store track name in `document.provenance.atom_track`.
- **Export pipeline** (AB01-T004): Should be a standalone script (not API endpoint) that reads from the database and writes to a configurable export root. Manifest should be JSON with document ID, checksum, per-level atom counts, and schema version.
- **Async ingestion**: Could integrate with the existing `Job` system. Submit ingestion as an async job, worker calls `ingest_batch`, progress updates via job status polling.
