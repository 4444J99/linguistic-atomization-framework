# Seed Corpus -- Implementation Plan

## Technical Context

| Component | Version / Stack |
|-----------|----------------|
| Language | Python >=3.11 |
| Web framework | FastAPI (uvicorn) |
| ORM | SQLAlchemy 2.0 (`mapped_column` style) |
| Migrations | Alembic (SQLite default, PostgreSQL via docker) |
| Schema validation | Pydantic v2 + `pydantic-settings` |
| Testing | pytest + `FastAPI.TestClient`, isolated SQLite per test via `tmp_path` |
| HTTP downloads | `urllib.request.urlretrieve` (stdlib, no timeout) |
| Settings | `pydantic-settings`, `NEXUS_` prefix, `.env` file |
| Docker | `docker-compose.yml` for PostgreSQL + Neo4j |

## Project Structure

Files directly relevant to the seed corpus domain:

```
src/nexus_babel/
  main.py                           # create_app() factory; wires SeedCorpusService(seeds_dir=corpus_root/"seeds")
  config.py                         # Settings (corpus_root, bootstrap keys)
  schemas.py                        # SeedTextEntry, SeedTextListResponse, SeedProvisionRequest, SeedProvisionResponse
  api/
    routes.py                       # GET /corpus/seeds, POST /corpus/seed (with auto-ingestion)
  services/
    seed_corpus.py                  # SeedCorpusService, SEED_REGISTRY, SeedText dataclass

scripts/
  ingest_corpus.py                  # CLI ingestion script (no profile support yet)

tests/
  conftest.py                       # test_settings, client, auth_headers, sample_corpus fixtures
  test_mvp.py                       # T-P1-010 in 01-ingestion-atomization covers seed registry listing

docs/
  alexandria_babel/
    AB-PLAN-01_Build_Tickets.md     # AB01-T001: Seed Corpus Registry + Profiles
```

## Data Models

### SeedText Dataclass (`seed_corpus.py:12-18`)

An internal data structure for seed text metadata. Currently defined but not used at runtime.

```python
@dataclass
class SeedText:
    title: str                          # "The Odyssey"
    author: str                         # "Homer"
    language: str                       # "English"
    source_url: str                     # "https://www.gutenberg.org/cache/epub/1727/pg1727.txt"
    local_path: Path | None = None      # Path to downloaded file, or None
    atomization_status: str = "not_provisioned"  # "provisioned" | "not_provisioned"
```

### SEED_REGISTRY (`seed_corpus.py:21-52`)

A module-level constant: `list[dict[str, Any]]` with 5 entries. Each dict has keys: `title`, `author`, `language`, `source_url`. No `local_path` or `atomization_status` -- those are computed at runtime by `list_seed_texts()`.

```python
SEED_REGISTRY: list[dict[str, Any]] = [
    {"title": "The Odyssey",       "author": "Homer",            "language": "English", "source_url": "https://www.gutenberg.org/cache/epub/1727/pg1727.txt"},
    {"title": "The Divine Comedy", "author": "Dante Alighieri",  "language": "English", "source_url": "https://www.gutenberg.org/cache/epub/8800/pg8800.txt"},
    {"title": "Leaves of Grass",   "author": "Walt Whitman",     "language": "English", "source_url": "https://www.gutenberg.org/cache/epub/1322/pg1322.txt"},
    {"title": "Ulysses",           "author": "James Joyce",      "language": "English", "source_url": "https://www.gutenberg.org/cache/epub/4300/pg4300.txt"},
    {"title": "Frankenstein",      "author": "Mary Shelley",     "language": "English", "source_url": "https://www.gutenberg.org/cache/epub/84/pg84.txt"},
]
```

### Document (downstream, `models.py:30-51`)

Seed texts become `Document` rows via auto-ingestion in the provisioning route. Relevant subset:

```
documents
  id              VARCHAR(36) PK    -- uuid4
  path            VARCHAR(1024) UQ  -- resolved path to seeds_dir/{safe_name}.txt
  title           VARCHAR(512)      -- filename (e.g., "the_odyssey.txt")
  modality        VARCHAR(32)       -- always "text" for seed texts
  checksum        VARCHAR(128)      -- SHA256 of downloaded file
  size_bytes      INTEGER           -- stat().st_size
  ingested        BOOLEAN           -- True after successful processing
  ingest_status   VARCHAR(32)       -- "ingested" after successful atomization
  atom_count      INTEGER           -- total atoms across all 5 levels
  provenance      JSON              -- extracted_text, segments, checksum, etc.
  created_at      DATETIME(tz)
  updated_at      DATETIME(tz)
```

### Proposed: Seed Registry YAML (P3 -- AB01-T001)

```yaml
# docs/alexandria_babel/seed_corpus_registry.yaml
schema_version: "1.0"
seeds:
  - title: "The Odyssey"
    author: "Homer"
    language: "English"
    source_url: "https://www.gutenberg.org/cache/epub/1727/pg1727.txt"
    expected_checksum: null  # to be computed after first download
    tags: ["epic", "classical", "greek"]
    profiles: ["arc4n-seed", "classical"]
  - title: "The Divine Comedy"
    author: "Dante Alighieri"
    language: "English"
    source_url: "https://www.gutenberg.org/cache/epub/8800/pg8800.txt"
    expected_checksum: null
    tags: ["epic", "medieval", "italian"]
    profiles: ["arc4n-seed", "medieval"]
  # ... 3 more entries
```

### Proposed: Ingestion Profile YAML (P3 -- AB01-T001)

```yaml
# profiles/arc4n-seed.yaml
name: "arc4n-seed"
description: "ARC4N seed corpus from Project Gutenberg"
seed_titles:
  - "The Odyssey"
  - "Leaves of Grass"
atom_tracks: ["full"]
parse_options:
  atomize: true
  force: false
```

## API Contracts

### GET /api/v1/corpus/seeds

**Auth**: viewer (minimum)
**Response** (`SeedTextListResponse`):
```json
{
  "seeds": [
    {
      "title": "The Odyssey",
      "author": "Homer",
      "language": "English",
      "source_url": "https://www.gutenberg.org/cache/epub/1727/pg1727.txt",
      "local_path": null,
      "atomization_status": "not_provisioned"
    },
    {
      "title": "The Divine Comedy",
      "author": "Dante Alighieri",
      "language": "English",
      "source_url": "https://www.gutenberg.org/cache/epub/8800/pg8800.txt",
      "local_path": null,
      "atomization_status": "not_provisioned"
    },
    {
      "title": "Leaves of Grass",
      "author": "Walt Whitman",
      "language": "English",
      "source_url": "https://www.gutenberg.org/cache/epub/1322/pg1322.txt",
      "local_path": null,
      "atomization_status": "not_provisioned"
    },
    {
      "title": "Ulysses",
      "author": "James Joyce",
      "language": "English",
      "source_url": "https://www.gutenberg.org/cache/epub/4300/pg4300.txt",
      "local_path": null,
      "atomization_status": "not_provisioned"
    },
    {
      "title": "Frankenstein",
      "author": "Mary Shelley",
      "language": "English",
      "source_url": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
      "local_path": null,
      "atomization_status": "not_provisioned"
    }
  ]
}
```

**After provisioning "The Odyssey"**:
```json
{
  "seeds": [
    {
      "title": "The Odyssey",
      "author": "Homer",
      "language": "English",
      "source_url": "https://www.gutenberg.org/cache/epub/1727/pg1727.txt",
      "local_path": "/path/to/corpus/seeds/the_odyssey.txt",
      "atomization_status": "provisioned"
    }
  ]
}
```

**Error cases**:
- 401: Missing/invalid API key
- 403: No API key provided (unauthenticated)

### POST /api/v1/corpus/seed

**Auth**: admin
**Request** (`SeedProvisionRequest`):
```json
{
  "title": "The Odyssey"
}
```

**Response -- first provision** (`SeedProvisionResponse`):
```json
{
  "title": "The Odyssey",
  "status": "provisioned",
  "local_path": "/path/to/corpus/seeds/the_odyssey.txt",
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response -- already provisioned**:
```json
{
  "title": "The Odyssey",
  "status": "already_provisioned",
  "local_path": "/path/to/corpus/seeds/the_odyssey.txt",
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response -- unknown title**:
```json
{
  "detail": "Unknown seed text: Nonexistent Book"
}
```
HTTP 400

**Error cases**:
- 400: Unknown title / download failure / ingestion failure
- 401: Missing/invalid API key
- 403: Non-admin role

### Proposed: POST /api/v1/corpus/seed/batch (P3)

**Auth**: admin
**Request**:
```json
{
  "titles": ["The Odyssey", "Leaves of Grass", "Frankenstein"]
}
```

**Response**:
```json
{
  "results": [
    {"title": "The Odyssey", "status": "provisioned", "local_path": "...", "document_id": "..."},
    {"title": "Leaves of Grass", "status": "already_provisioned", "local_path": "...", "document_id": "..."},
    {"title": "Frankenstein", "status": "provisioned", "local_path": "...", "document_id": "..."}
  ],
  "summary": {
    "provisioned": 2,
    "already_provisioned": 1,
    "failed": 0
  }
}
```

### Proposed: GET /api/v1/corpus/seeds/health (P3)

**Auth**: operator
**Response**:
```json
{
  "total_seeds": 5,
  "provisioned": 3,
  "not_provisioned": 2,
  "ingested": 2,
  "atomized": 2,
  "total_atoms": 523000,
  "atoms_by_level": {
    "glyph-seed": 380000,
    "syllable": 62000,
    "word": 55000,
    "sentence": 15000,
    "paragraph": 11000
  },
  "seed_health": [
    {
      "title": "The Odyssey",
      "file_exists": true,
      "file_size_bytes": 726528,
      "checksum_valid": true,
      "document_id": "...",
      "atom_count": 98000,
      "last_ingested_at": "2026-02-20T10:30:00Z"
    }
  ]
}
```

## Service Architecture

### SeedCorpusService (`seed_corpus.py`)

The service class managing the seed text lifecycle. Stateless except for the `seeds_dir` path.

**`__init__(seeds_dir: Path)`**:
```
1. Store seeds_dir
2. mkdir(parents=True, exist_ok=True) on seeds_dir
```

**`list_seed_texts() -> list[dict]`**:
```
1. FOR each entry in SEED_REGISTRY:
   a. Compute local_path via _local_path_for(title)
   b. Check if local_path.exists()
   c. Build result dict with all fields
   d. Set atomization_status = "provisioned" if exists, "not_provisioned" if not
   e. Set local_path = str(path) if exists, None if not
2. Return result list
```

**`provision_seed_text(title: str) -> dict`**:
```
1. Find entry by case-insensitive title match via _find_entry()
2. If not found, raise ValueError
3. Compute local_path via _local_path_for(entry["title"])
4. If local_path.exists():
   a. Return {title, status="already_provisioned", local_path}
5. Download via _download(source_url, local_path)
6. Return {title, status="provisioned", local_path}
```

**`_find_entry(title: str) -> dict | None`**:
```
1. Lowercase the input title
2. Iterate SEED_REGISTRY
3. Return first entry where entry["title"].lower() == title_lower
4. Return None if no match
```

**`_local_path_for(title: str) -> Path`**:
```
1. safe_name = title.lower().replace(" ", "_").replace("'", "")
2. Return seeds_dir / f"{safe_name}.txt"
```

**`_download(url: str, dest: Path) -> None`**:
```
1. urllib.request.urlretrieve(url, str(dest))
   -- No timeout
   -- No retry
   -- No checksum verification
   -- No partial file cleanup on failure
```

### Route Integration (`routes.py:638-680`)

**`GET /corpus/seeds`** (viewer):
```
1. Call seed_corpus_service.list_seed_texts()
2. Map each dict to SeedTextEntry
3. Return SeedTextListResponse(seeds=[...])
```

**`POST /corpus/seed`** (admin):
```
1. Call seed_corpus_service.provision_seed_text(payload.title)
2. If local_path exists and status in ("provisioned", "already_provisioned"):
   a. Call ingestion_service.ingest_batch(session, [local_path], ["text"], {})
   b. Commit session
   c. Extract document_id from ingest_result["files"][0]["document_id"]
3. Return SeedProvisionResponse(title, status, local_path, document_id)
4. On exception: rollback, raise HTTPException 400
```

### App Wiring (`main.py:68`)

```python
app.state.seed_corpus_service = SeedCorpusService(seeds_dir=settings.corpus_root / "seeds")
```

The `seeds_dir` is always `{corpus_root}/seeds`. The `corpus_root` defaults to `Path.cwd()` but is overridden in tests to `tmp_path`.

### Proposed: Enhanced SeedCorpusService (P2/P3)

```python
class SeedCorpusService:
    def __init__(self, seeds_dir: Path, registry_path: Path | None = None):
        self.seeds_dir = seeds_dir
        self.seeds_dir.mkdir(parents=True, exist_ok=True)
        self.registry = self._load_registry(registry_path)

    def _load_registry(self, path: Path | None) -> list[dict]:
        if path and path.exists():
            return yaml.safe_load(path.read_text())["seeds"]
        return SEED_REGISTRY  # fallback to hardcoded

    def list_seed_texts(self, session: Session | None = None) -> list[dict]:
        # Enhanced: check Document table for ingestion status
        ...

    def provision_seed_text(self, title: str, timeout: int = 30) -> dict:
        # Enhanced: timeout, retry, checksum verification
        ...

    def provision_batch(self, titles: list[str]) -> list[dict]:
        # New: batch provisioning
        ...

    def health_check(self, session: Session) -> dict:
        # New: corpus health with atom counts
        ...
```

## Research Notes

### Dependencies

| Dependency | Used For | Required? |
|------------|----------|-----------|
| `urllib.request` | Gutenberg downloads | Yes (stdlib) |
| `pathlib` | Filesystem operations | Yes (stdlib) |
| `pydantic` | Schema validation | Yes |
| `fastapi` | API routing | Yes |
| `sqlalchemy` | Database (for auto-ingestion) | Yes |

### Complexity / Performance Considerations

- **Download latency**: Project Gutenberg serves from CDN. Typical download times: Frankenstein (~442KB) ~1-2s, Ulysses (~1.5MB) ~3-5s, all 5 texts ~10-15s total. No timeout means the request thread is blocked for the full duration.
- **Auto-ingestion cost**: After download, the text goes through the full ingestion pipeline (SHA256, text extraction, 5-level atomization, hypergraph projection). For Ulysses (~265K words, ~1.5M characters), atomization produces ~1.2M glyph-seed atoms. This is the dominant cost -- roughly 30-60s for large texts on local dev.
- **Memory during provisioning**: The download is written directly to disk via `urlretrieve` (streaming), so memory usage is minimal. The auto-ingestion step reads the entire file into memory via `read_text()`, which is ~1.5MB for the largest text (manageable).
- **Filesystem atomicity**: `urlretrieve` is not atomic -- if interrupted, a partial file remains. The existence check (`local_path.exists()`) would then short-circuit subsequent provisioning attempts, leaving a corrupted file.
- **Concurrent provisioning**: No locking. Two simultaneous provisions of the same title could race on download and file write. Mitigation: File-level advisory locks or a "downloading" sentinel file.

### Known Risks

1. **No download timeout**: `urllib.request.urlretrieve` blocks indefinitely. If Gutenberg is unreachable, the API request hangs until the connection times out at the TCP level (potentially minutes). Mitigation: Use `urllib.request.urlopen` with `timeout` parameter, then read-write in chunks.
2. **No download retry**: A single transient network failure aborts provisioning with an unhandled exception. The HTTP 400 error message exposes the raw exception string. Mitigation: Retry loop with exponential backoff (2, 10, 30 seconds, matching the job retry backoff pattern).
3. **Partial file corruption**: An interrupted download leaves a partial file that blocks re-download. Mitigation: Download to a `.tmp` file, then `os.rename()` to the final path atomically. Only the final rename indicates success.
4. **SeedText dataclass dead code**: The `SeedText` dataclass is defined but never used, creating confusion about the data model. Mitigation: Either use it throughout the service or remove it.
5. **No document-level status tracking**: The `atomization_status` is purely filesystem-based and does not reflect whether the seed text has been ingested as a `Document` with atoms. A provisioned-but-not-ingested text appears the same as a fully atomized one. Mitigation: Add a `Session` parameter to `list_seed_texts()` and query the `Document` table by path.
6. **Filename sanitization gaps**: `_local_path_for()` only handles spaces and apostrophes. Titles with colons, slashes, or Unicode could produce invalid filenames. Mitigation: Use a more robust sanitization (e.g., `re.sub(r'[^\w\-]', '_', title.lower())`).
7. **Auto-ingestion document_id extraction fragility**: The route extracts `document_id` from `ingest_result.get("files", [])`. If the ingestion succeeds but returns no `files` key (e.g., all files unchanged), `doc_id` is `None`. Mitigation: Also check `documents_ingested` count and query by path if needed.

### Future Architecture Considerations

- **YAML registry** (AB01-T001): The registry file should live in `docs/alexandria_babel/seed_corpus_registry.yaml` and be loaded at service init. The service should fall back to the hardcoded `SEED_REGISTRY` if the YAML file does not exist, ensuring backward compatibility during migration. The YAML schema should include `schema_version` for future evolution.
- **Ingestion profiles** (AB01-T001): Profile YAML files should live in a `profiles/` directory at the repo root. The ingestion script should accept `--profile <name>` and resolve the profile by filename (`profiles/{name}.yaml`). Profile metadata (name, seed_titles, parse_options) should be recorded in the `IngestJob.request_payload` JSON for provenance.
- **CLI provisioning**: A `scripts/provision_corpus.py` or `python -m nexus_babel.cli provision --title "The Odyssey"` entrypoint would be cleaner than API-only provisioning. The CLI should reuse `SeedCorpusService` directly without starting the FastAPI app.
- **Enhanced status tracking**: A three-tier status model -- `not_provisioned` -> `provisioned` -> `ingested` (with optional `atomized` substatus) -- would require the service to accept a database session and query `Document` rows by path. This adds a dependency on the ORM that the current service does not have.
- **Batch provisioning**: A batch endpoint should provision sequentially (to avoid concurrent download issues) and return per-title results. Failures on individual titles should not abort the entire batch.
- **Health endpoint**: Should aggregate data from both the filesystem (file existence, size) and database (document rows, atom counts) to provide a comprehensive corpus health view.
