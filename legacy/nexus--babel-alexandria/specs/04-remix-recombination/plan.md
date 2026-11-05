# Remix & Recombination -- Implementation Plan

## Technical Context

| Component | Version / Stack |
|-----------|----------------|
| Language | Python >=3.11 |
| Web framework | FastAPI (uvicorn) |
| ORM | SQLAlchemy 2.0 (`mapped_column` style) |
| Migrations | Alembic (SQLite default, PostgreSQL via docker) |
| Schema validation | Pydantic v2 + `pydantic-settings` |
| Testing | pytest + `FastAPI.TestClient`, isolated SQLite per test via `tmp_path` |
| Graph store | Neo4j (`neo4j` Python driver) + `LocalGraphCache` fallback |
| Settings | `pydantic-settings`, `NEXUS_` prefix, `.env` file |
| Docker | `docker-compose.yml` for PostgreSQL + Neo4j |
| RNG | Python `random.Random` seeded from SHA256 hash |

## Project Structure

Files directly relevant to the remix-recombination domain:

```
src/nexus_babel/
  main.py                           # create_app() — wires RemixService onto app.state.remix_service
  config.py                         # Settings (no remix-specific config yet)
  db.py                             # DBManager wrapper
  models.py                         # Branch, BranchEvent (used by remix); proposed: RemixArtifact, RemixSourceLink
  schemas.py                        # RemixRequest, RemixResponse, RemixStrategy literal type
  api/
    routes.py                       # POST /api/v1/remix endpoint; proposed: GET /remix/{id}, GET /remix
  services/
    remix.py                        # RemixService: remix(), _resolve_text(), _apply_strategy(), 4 strategy methods
    evolution.py                    # EvolutionService.evolve_branch() — called by RemixService; handles "remix" event_type
    governance.py                   # GovernanceService.evaluate() — proposed integration for remix governance traces
    auth.py                         # API key auth, role hierarchy, mode enforcement

tests/
  conftest.py                       # test_settings, client, auth_headers, sample_corpus fixtures
  test_arc4n.py                     # TestRemixStrategies, TestRemixAPI classes (existing remix tests)

alembic/
  versions/
    20260218_0001_initial.py        # Initial schema (Branch, BranchEvent, etc.)
    20260218_0002_wave2_alpha.py    # Wave-2 additions (BranchCheckpoint, etc.)
    # Proposed: 20260223_0003_remix_artifacts.py

docs/
  alexandria_babel/
    AB-PLAN-01_Build_Tickets.md     # AB01-T005, AB01-T006, AB01-T007 — remix planning tickets
```

## Data Models

### Branch (ORM: `models.py:110-124`) -- Existing

The branch entity is created by every remix. One new branch per remix call.

```
branches
  id                  VARCHAR(36) PK    -- uuid4
  parent_branch_id    VARCHAR(36) FK    -- -> branches.id (source branch if remix from branch)
  root_document_id    VARCHAR(36) FK    -- -> documents.id (source document or branch's root doc)
  name                VARCHAR(256)      -- auto: "branch-remix"
  mode                VARCHAR(16)       -- 'PUBLIC'|'RAW', from RemixRequest.mode
  created_by          VARCHAR(128)      -- nullable (not currently set by remix)
  state_snapshot      JSON              -- {current_text, phase: "expansion", text_hash}
  branch_version      INTEGER           -- parent.branch_version + 1, or 1 if no parent
  created_at          DATETIME(tz)
```

**Remix-specific state_snapshot**:
```json
{
  "current_text": "interleaved words from both documents...",
  "phase": "expansion",
  "text_hash": "sha256-of-remixed-text"
}
```

### BranchEvent (ORM: `models.py:127-141`) -- Existing

Stores the full remix operation as a replayable event.

```
branch_events
  id                      VARCHAR(36) PK    -- uuid4
  branch_id               VARCHAR(36) FK    -- -> branches.id
  event_index             INTEGER           -- sequential (1 for the first event on a new branch)
  event_type              VARCHAR(64)       -- "remix"
  event_payload           JSON              -- full remix metadata (see below)
  payload_schema_version  VARCHAR(16)       -- "v2"
  event_hash              VARCHAR(128)      -- sha256(branch_id:index:type:payload:text_hash)
  diff_summary            JSON              -- {event, strategy, before_chars, after_chars}
  result_snapshot         JSON              -- {text_hash, preview (first 500 chars)}
  created_at              DATETIME(tz)
```

**Remix event_payload structure** (schema version v2):
```json
{
  "seed": 42,
  "strategy": "interleave",
  "remixed_text": "one alpha two beta three gamma",
  "source_document_id": "uuid-or-null",
  "target_document_id": "uuid-or-null",
  "source_branch_id": "uuid-or-null",
  "target_branch_id": "uuid-or-null"
}
```

### RemixArtifact -- Proposed (AB01-T006)

First-class remix entity for persistence and retrieval. One row per remix operation.

```
remix_artifacts
  id                      VARCHAR(36) PK    -- uuid4
  strategy                VARCHAR(64)       -- 'interleave'|'thematic_blend'|'temporal_layer'|'glyph_collide'
  seed                    INTEGER           -- RNG seed
  remixed_text            TEXT              -- full remixed output
  text_hash               VARCHAR(128)      -- SHA256 of remixed_text, indexed
  rng_seed_hex            VARCHAR(128)      -- full derived RNG seed hex for replay verification
  mode                    VARCHAR(16)       -- 'PUBLIC'|'RAW'
  branch_id               VARCHAR(36) FK    -- -> branches.id, nullable (null when create_branch=false)
  branch_event_id         VARCHAR(36) FK    -- -> branch_events.id, nullable
  governance_decision_id  VARCHAR(36) FK    -- -> policy_decisions.id, nullable
  created_by              VARCHAR(128)      -- API key owner from auth context
  metadata                JSON              -- extensible: {atom_levels, custom_tags, notes}
  created_at              DATETIME(tz)
  updated_at              DATETIME(tz)
```

**Indexes**: `text_hash` (for dedup lookups), `strategy` (for filtered listings), `branch_id` (for join queries).

### RemixSourceLink -- Proposed (AB01-T006)

Join table linking a remix to its source and target documents/branches. Exactly 2 rows per remix (one `source`, one `target`).

```
remix_source_links
  id                  VARCHAR(36) PK    -- uuid4
  remix_artifact_id   VARCHAR(36) FK    -- -> remix_artifacts.id ON DELETE CASCADE
  role                VARCHAR(16)       -- 'source'|'target'
  document_id         VARCHAR(36) FK    -- -> documents.id, nullable
  branch_id           VARCHAR(36) FK    -- -> branches.id, nullable
  resolved_text_hash  VARCHAR(128)      -- SHA256 of the text resolved from this source at remix time
  resolved_text_len   INTEGER           -- length of resolved text
  created_at          DATETIME(tz)
```

**Unique constraint**: `(remix_artifact_id, role)` -- one source and one target per remix.

### GovernanceDecision linkage -- Proposed (AB01-T006)

No new model needed. The existing `PolicyDecision` model (`models.py:157-168`) is reused. The `governance_decision_id` FK on `RemixArtifact` links to `policy_decisions.id`. The governance evaluation is performed on the `remixed_text` before persisting the artifact.

## API Contracts

### POST /api/v1/remix -- Existing

**Auth**: operator (minimum)
**Request** (`RemixRequest`):
```json
{
  "source_document_id": "uuid",
  "source_branch_id": null,
  "target_document_id": "uuid",
  "target_branch_id": null,
  "strategy": "interleave",
  "seed": 42,
  "mode": "PUBLIC"
}
```

- `source_document_id` / `source_branch_id`: Exactly one should be provided for the source side. If both are provided, branch takes priority.
- `target_document_id` / `target_branch_id`: Same as above for target side.
- `strategy`: One of `"interleave"`, `"thematic_blend"`, `"temporal_layer"`, `"glyph_collide"`.
- `seed`: Integer RNG seed (default 0). Same seed + same inputs = same output.
- `mode`: Governance mode. `"PUBLIC"` is default. `"RAW"` requires researcher+ role with raw_mode_enabled.

**Response** (`RemixResponse`):
```json
{
  "new_branch_id": "uuid",
  "event_id": "uuid",
  "strategy": "interleave",
  "diff_summary": {
    "event": "remix",
    "strategy": "interleave",
    "before_chars": 94,
    "after_chars": 187
  }
}
```

**Error cases**:
- 400: Both source and target resolve to empty text; unknown strategy
- 401: Missing or invalid API key
- 403: Insufficient role (viewer cannot remix); mode not allowed (RAW without authorization)

### POST /api/v1/remix -- Proposed Extension (AB01-T006, AB01-T007)

**Additional request fields**:
```json
{
  "source_document_id": "uuid",
  "target_document_id": "uuid",
  "strategy": "thematic_blend",
  "seed": 42,
  "mode": "PUBLIC",
  "create_branch": true,
  "persist_artifact": true
}
```

- `create_branch`: Boolean, default `true` (backward compatible). When `false`, no branch/event is created; only the artifact is persisted.
- `persist_artifact`: Boolean, default `true`. When `true`, a `RemixArtifact` row is created with source links and optional governance trace.

**Extended response**:
```json
{
  "remix_artifact_id": "uuid",
  "new_branch_id": "uuid-or-null",
  "event_id": "uuid-or-null",
  "strategy": "thematic_blend",
  "text_hash": "sha256-hex",
  "governance_decision_id": "uuid-or-null",
  "diff_summary": {
    "event": "remix",
    "strategy": "thematic_blend",
    "before_chars": 94,
    "after_chars": 142
  }
}
```

### GET /api/v1/remix/{remix_id} -- Proposed (AB01-T006)

**Auth**: viewer (minimum)
**Response**:
```json
{
  "remix_artifact_id": "uuid",
  "strategy": "interleave",
  "seed": 42,
  "text_hash": "sha256-hex",
  "text_preview": "first 500 characters of remixed text...",
  "mode": "PUBLIC",
  "branch_id": "uuid-or-null",
  "branch_event_id": "uuid-or-null",
  "governance_decision_id": "uuid-or-null",
  "created_by": "dev-operator",
  "created_at": "2026-02-23T12:00:00Z",
  "source_links": [
    {
      "role": "source",
      "document_id": "uuid-or-null",
      "branch_id": "uuid-or-null",
      "resolved_text_hash": "sha256-hex",
      "resolved_text_len": 1523
    },
    {
      "role": "target",
      "document_id": "uuid-or-null",
      "branch_id": "uuid-or-null",
      "resolved_text_hash": "sha256-hex",
      "resolved_text_len": 892
    }
  ]
}
```

**Error cases**:
- 404: Remix artifact not found
- 401/403: Auth/role

### GET /api/v1/remix -- Proposed (AB01-T006)

**Auth**: viewer (minimum)
**Query params**: `limit` (default 100, max 1000), `strategy` (optional filter), `mode` (optional filter)
**Response**:
```json
{
  "remixes": [
    {
      "remix_artifact_id": "uuid",
      "strategy": "interleave",
      "seed": 42,
      "text_hash": "sha256-hex",
      "mode": "PUBLIC",
      "branch_id": "uuid-or-null",
      "created_by": "dev-operator",
      "created_at": "2026-02-23T12:00:00Z"
    }
  ]
}
```

## Service Architecture

### RemixService (`remix.py`)

The core service class. Injected with `EvolutionService`. Currently handles the complete remix lifecycle.

**`remix()` flow:**

```
1. Resolve source text:
   a. If source_branch_id: branch.state_snapshot.current_text
   b. Else if source_document_id: document.provenance.extracted_text
2. Resolve target text (same logic)
3. Validate both texts are non-empty
4. Derive RNG seed:
   a. seed_input = f"remix:{strategy}:{seed}:{sha256(source_text)}:{sha256(target_text)}"
   b. rng = Random(int(sha256(seed_input)) % 2^32)
5. Apply strategy:
   a. interleave: split \S+, alternate words
   b. thematic_blend: split [.!?]+, combine, shuffle, truncate
   c. temporal_layer: split \n\s*\n, interleave with 70% overlay
   d. glyph_collide: character-level, 50/50 random, cap 2000
6. Determine root_document_id:
   a. If source_document_id: use it
   b. Elif source_branch_id: lookup branch.root_document_id
7. Delegate to EvolutionService.evolve_branch():
   a. event_type = "remix"
   b. event_payload = {seed, strategy, remixed_text, source/target IDs}
   c. mode = request mode
8. Return (Branch, BranchEvent) tuple
```

**Key methods:**
- `remix()`: Main entry point. Orchestrates text resolution, strategy application, and branch creation.
- `_resolve_text(session, document_id, branch_id)`: Resolves text from branch or document. Returns empty string if neither found.
- `_branch_root_doc(session, branch_id)`: Helper to look up a branch's `root_document_id`.
- `_apply_strategy(source, target, strategy, rng)`: Routes to the appropriate strategy method.
- `_interleave(source, target)`: Word-level alternation. No RNG needed.
- `_thematic_blend(source, target, rng)`: Sentence-level shuffle.
- `_temporal_layer(source, target, rng)`: Paragraph-level overlay with 70% inclusion.
- `_glyph_collide(source, target, rng)`: Character-level collision, 2000-char cap.

### EvolutionService integration (`evolution.py`)

RemixService delegates branch creation to EvolutionService. The evolution service handles remix events as follows:

**Validation** (`_validate_event_payload`, line 286-289):
- Sets defaults: `seed=0`, `strategy="interleave"`
- No other validation (remix payload is pre-built by RemixService)

**Application** (`_apply_event`, line 377-381):
- For `event_type="remix"`, returns `event_payload.remixed_text` directly
- Does NOT recompute the remix -- the text is pre-computed by RemixService
- `diff_summary` includes `event`, `strategy`, `before_chars`, `after_chars`

**Branch creation** (`evolve_branch`, lines 76-157):
- Creates new `Branch` with `name="branch-remix"`, `mode` from request
- Creates `BranchEvent` with `event_type="remix"`, full payload, event hash
- Optional: creates `BranchCheckpoint` every 10 events in the lineage

### Proposed: Extended RemixService (AB01-T006, AB01-T007)

```
remix() flow — extended:

1-5. Same as current (resolve, validate, derive RNG, apply strategy)
6.   Optionally evaluate governance:
     a. Call GovernanceService.evaluate(session, remixed_text, mode)
     b. If PUBLIC mode blocks, raise HTTPException (or flag artifact)
     c. Store governance_decision_id
7.   Persist RemixArtifact:
     a. Create RemixArtifact row with strategy, seed, text, hash, mode, governance_decision_id
     b. Create 2 RemixSourceLink rows (source + target) with resolved_text_hash
8.   Conditionally create branch:
     a. If create_branch=True: call EvolutionService.evolve_branch()
     b. Update RemixArtifact with branch_id and branch_event_id
     c. Include remix_artifact_id in BranchEvent.event_payload
     d. If create_branch=False: skip branch creation
9.   Return extended response with remix_artifact_id, optional branch IDs
```

### Route layer (`routes.py:683-716`)

The remix endpoint handles session management, mode enforcement, service delegation, and response mapping.

```python
@router.post("/remix", response_model=RemixResponse)
def remix(
    payload: RemixRequest,
    request: Request,
    auth_context: AuthContext = Depends(_require_auth("operator")),
) -> RemixResponse:
    # 1. Open session
    # 2. Enforce mode
    # 3. Call remix_service.remix()
    # 4. Commit
    # 5. Return response
```

**Transaction boundary**: The route opens a session, calls `remix_service.remix()`, commits, and returns. Errors trigger rollback. The session is always closed in `finally`.

### Governance integration -- Proposed

For P2, the remix route (or RemixService) should call `GovernanceService.evaluate()` on the `remixed_text` after strategy application but before persistence. This creates a `PolicyDecision` row and an `AuditLog` entry. The `PolicyDecision.id` is stored as `governance_decision_id` on the `RemixArtifact`.

In PUBLIC mode, if governance blocks the remix (policy hits >= hard_block_threshold), the remix should either:
- (a) Reject with HTTP 422 and include the policy hits in the error detail, or
- (b) Persist the artifact with `governance_blocked=True` flag and return a warning

In RAW mode, governance always allows but flags terms. The decision trace is attached regardless.

## Research Notes

### Dependencies

| Dependency | Used For | Required? |
|------------|----------|-----------|
| `sqlalchemy` | ORM for Branch, BranchEvent, proposed RemixArtifact | Yes |
| `pydantic` | RemixRequest/Response schema validation | Yes |
| `hashlib` | SHA256 for RNG seeding and text hashing | Yes (stdlib) |
| `random` | Seeded RNG for stochastic strategies | Yes (stdlib) |
| `re` | Text splitting regex for all 4 strategies | Yes (stdlib) |
| `alembic` | Migrations for proposed new tables | Yes (for schema changes) |

### Complexity / Performance Considerations

- **interleave**: O(n) where n = max(source_words, target_words). Two regex passes + one join. Memory: one list per text. For two 100K-word texts, ~200K strings in memory. Fast.
- **thematic_blend**: O(n log n) due to shuffle (n = total sentences). Regex split + random shuffle + join. For typical literary texts (~5K sentences each), trivial.
- **temporal_layer**: O(n) where n = max(paragraphs). Regex split + interleave with RNG check. Memory proportional to paragraph count. Fast.
- **glyph_collide**: O(min(max_glyphs, 2000)). Character iteration capped at 2000. This is the only strategy with a hard output cap. Always fast regardless of input size.
- **Text storage in event_payload**: The full `remixed_text` is stored in `BranchEvent.event_payload` as JSON. For two large documents (e.g., Ulysses at ~265K words), the interleave output could be ~500K words. Stored as a JSON string field, this is ~3MB per event. SQLite handles this fine; PostgreSQL JSONB compression helps. For very large texts, consider storing text in a separate blob and referencing it.
- **RNG seed derivation**: Two SHA256 calls (one for source text, one for target text) plus one for the combined seed string. For a 1.5MB text, SHA256 takes ~2ms. Negligible.

### Known Risks

1. **No size limits on remix output**: `interleave`, `thematic_blend`, and `temporal_layer` have no output cap. Two 10MB texts could produce a ~20MB interleave stored in a JSON field. Mitigation: Add `max_output_chars` parameter or enforce a system-wide cap.
2. **remixed_text stored in event_payload**: Full text stored as JSON nested inside `BranchEvent.event_payload`. This duplicates storage (also in `Branch.state_snapshot.current_text`). Mitigation: For P2 `RemixArtifact`, store text only once and reference it.
3. **No governance on remix output**: Currently, mode enforcement only checks auth access. The remixed text is not evaluated against governance policies. A remix could produce text containing blocked terms by combining innocuous source material. Mitigation: Add `GovernanceService.evaluate()` call in P2.
4. **Silent failure on missing documents**: `_resolve_text()` returns `""` for nonexistent document/branch IDs. Combined with the `ValueError` check, this produces a generic error. Mitigation: Add explicit existence checks with 404 responses.
5. **No replay verification**: While the evolution service can replay branches, there is no test verifying that replaying a remix branch produces the same text hash as the original. The evolution service returns `event_payload.remixed_text` directly during replay, so this should work, but it is not explicitly tested.
6. **CJK and whitespace-free languages**: `interleave` uses `\S+` which treats CJK text as single "words". `temporal_layer` paragraph splitting works for any language. `thematic_blend` sentence splitting on `[.!?]` misses CJK sentence-end markers. Mitigation: Accept as English-biased; add locale parameter in P3.
7. **Concurrent remix to same parent branch**: Two concurrent remix calls with the same `source_branch_id` would both create child branches with `branch_version = parent.branch_version + 1`, producing version collisions. Not dangerous (versions are informational) but confusing. Mitigation: Consider unique constraint or atomic increment.
8. **glyph_collide 2000-char cap**: The cap is hardcoded. For very short texts, the cap is irrelevant. For long texts, the output is silently truncated to 2000 chars with no warning. Mitigation: Return cap info in `diff_summary`; make cap configurable.

### Future Architecture Considerations

- **Atom-pool remix** (AB01-T005): Instead of resolving full text and splitting with regex, query `Atom` rows from the database filtered by `atom_level` and `document_id`. The `_interleave` strategy would alternate `Atom.content` at the word level; `_thematic_blend` would work at the sentence level with thematic tags from `Atom.metadata_json`. This requires a new `_resolve_atoms(session, document_id, branch_id, atom_level)` method.
- **Remix artifact deduplication**: Two identical remixes (same strategy, same seed, same source texts) produce the same `text_hash`. The `RemixArtifact.text_hash` index enables quick lookup. Consider returning existing artifact instead of creating a duplicate.
- **Hypergraph projection of remixes**: Remix artifacts could be projected as nodes in the hypergraph with `REMIXED_FROM` edges to source document/branch nodes. This enables graph queries for lineage visualization.
- **Remix chains**: A remix output can be used as input to another remix. The current architecture supports this (remix creates a branch, branch text can be resolved). For P3, consider a `remix_chain_id` field grouping related remixes.
- **Strategy extensibility**: The `_apply_strategy()` router is a simple if-chain. For P3, consider a plugin-style strategy registry where custom strategies can be registered.
- **Async remix with progress**: For large texts, glyph_collide is fast (2000-char cap) but interleave on two novels could be slow due to branch/event creation overhead. Integrating with the `JobService` would allow progress polling and cancellation.
