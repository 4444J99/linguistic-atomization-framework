# 07 -- Hypergraph: Implementation Plan

> **Domain:** 07-hypergraph
> **Status:** Draft
> **Last updated:** 2026-02-23
> **Source of truth:** `src/nexus_babel/services/hypergraph.py`

---

## Technical Context

| Component | Version / Stack |
|-----------|----------------|
| Language | Python >=3.11 |
| Web framework | FastAPI (uvicorn) |
| ORM | SQLAlchemy 2.0 (`mapped_column` style) |
| Migrations | Alembic (SQLite default, PostgreSQL via docker) |
| Graph database | Neo4j (`neo4j` Python driver, optional) |
| In-memory graph | `LocalGraphCache` (dataclass with dict nodes + list edges) |
| Testing | pytest + `FastAPI.TestClient`, isolated SQLite per test via `tmp_path` |
| Settings | `pydantic-settings`, `NEXUS_` prefix, `.env` file |
| Docker | `docker-compose.yml` for PostgreSQL + Neo4j |

---

## Project Structure

Files directly relevant to the hypergraph domain:

```
src/nexus_babel/
  main.py                           # create_app() -- wires HypergraphProjector onto app.state.hypergraph
  config.py                         # Settings: neo4j_uri, neo4j_username, neo4j_password
  models.py                         # ProjectionLedger, Document (graph_projected_atom_count, graph_projection_status)
  api/
    routes.py                       # GET /hypergraph/query, GET /hypergraph/documents/{id}/integrity
  services/
    hypergraph.py                   # HypergraphProjector, LocalGraphCache, PROJECTION_CHUNK_SIZE
    ingestion.py                    # Calls project_document(), _update_projection_ledger(), creates ProjectionLedger rows

tests/
  conftest.py                       # test_settings (neo4j_uri=None), client, auth_headers
  test_mvp.py                       # test_hypergraph_integrity, test_integrity_persists_across_restart
  test_wave2.py                     # test_hypergraph_query_and_audit_decisions

alembic/
  versions/
    20260218_0001_initial.py        # Initial schema (includes projection_ledger table)
    20260218_0002_wave2_alpha.py    # Wave-2 additions

docker-compose.yml                  # Neo4j service definition
```

---

## Data Models

### ProjectionLedger (ORM: `models.py:277-291`)

Per-atom projection tracking. One row per atom per document. Unique constraint prevents duplicate tracking rows.

```
projection_ledger
  id              VARCHAR(36) PK    -- uuid4
  document_id     VARCHAR(36) FK    -- -> documents.id ON DELETE CASCADE, indexed
  atom_id         VARCHAR(36)       -- atom UUID (not FK for flexibility), indexed
  status          VARCHAR(32)       -- 'pending'|'projected'|'failed', indexed
  attempt_count   INTEGER           -- incremented on each projection attempt
  last_error      VARCHAR(512)      -- error message from most recent failure (nullable)
  created_at      DATETIME(tz)
  updated_at      DATETIME(tz)

UNIQUE(document_id, atom_id) -- uq_projection_ledger_document_atom
```

**State machine** for `status`:
```
pending -> projected    (successful projection to local cache + optional Neo4j)
pending -> failed       (projection threw exception)
failed  -> projected    (future: retry succeeds)
failed  -> failed       (future: retry fails again, attempt_count increments)
```

### Document -- Graph-Relevant Fields (ORM: `models.py:46-48`)

```
documents (partial -- graph-specific fields only)
  graph_projected_atom_count  INTEGER     -- count of atoms in graph (local cache + Neo4j)
  graph_projection_status     VARCHAR(32) -- 'pending'|'complete'|'partial'|'failed'
```

**State machine** for `graph_projection_status`:
```
pending  -> complete    (all atoms projected successfully)
pending  -> partial     (some atoms projected, count mismatch)
pending  -> failed      (projection threw exception)
complete -> pending     (re-ingestion resets before re-projection)
```

### LocalGraphCache (dataclass: `hypergraph.py:14-17`)

In-memory only. Not persisted. Lost on restart.

```
nodes: dict[str, dict[str, Any]]
  Key format: "doc:{uuid}" or "atom:{uuid}"
  Value: {"label": "Document"|"Atom", ...properties}

edges: list[dict[str, Any]]
  Each: {"type": "CONTAINS", "from": "doc:{uuid}", "to": "atom:{uuid}", "metadata": {"atom_level": "word"}}
```

### Neo4j Schema (when configured)

```cypher
(:Document {id: STRING, path: STRING, modality: STRING, checksum: STRING})
  -[:CONTAINS]->
(:Atom {id: STRING, document_id: STRING, atom_level: STRING, ordinal: INT, content: STRING})
```

No constraints or indexes are created programmatically. Neo4j's default behavior handles MERGE by property matching.

---

## API Contracts

### GET /api/v1/hypergraph/query

**Auth**: viewer (minimum)
**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `document_id` | string | No | None | Filter by document UUID |
| `node_id` | string | No | None | Query a specific node (e.g., `doc:uuid` or `atom:uuid`) |
| `relationship_type` | string | No | None | Filter edges by type (e.g., `CONTAINS`); case-insensitive |
| `limit` | integer | No | 100 | Max edges returned (1-1000) |

At least one of `document_id` or `node_id` should be provided for meaningful results. If `node_id` is absent, `document_id` is used to construct `doc:{document_id}`.

**Response** (local cache hit):
```json
{
  "source": "local_cache",
  "nodes": [
    {"id": "doc:abc-123", "label": "Document", "path": "/corpus/sample.md", "modality": "text", "checksum": "sha256..."},
    {"id": "atom:def-456", "label": "Atom", "document_id": "abc-123", "atom_level": "word", "ordinal": 1, "content": "Sing"},
    {"id": "atom:ghi-789", "label": "Atom", "document_id": "abc-123", "atom_level": "word", "ordinal": 2, "content": "O"}
  ],
  "edges": [
    {"type": "CONTAINS", "from": "doc:abc-123", "to": "atom:def-456", "metadata": {"atom_level": "word"}},
    {"type": "CONTAINS", "from": "doc:abc-123", "to": "atom:ghi-789", "metadata": {"atom_level": "word"}}
  ],
  "count": {"nodes": 3, "edges": 2}
}
```

**Response** (Neo4j fallback):
```json
{
  "source": "neo4j",
  "nodes": [
    {"id": "doc:abc-123"},
    {"id": "atom:def-456"}
  ],
  "edges": [
    {"type": "CONTAINS", "from": "doc:abc-123", "to": "atom:def-456"}
  ],
  "count": {"nodes": 2, "edges": 1}
}
```

**Response** (empty -- no data found):
```json
{
  "source": "empty",
  "nodes": [],
  "edges": [],
  "count": {"nodes": 0, "edges": 0}
}
```

**Error cases**:
- 401: Missing/invalid API key
- 403: Insufficient role

### GET /api/v1/hypergraph/documents/{document_id}/integrity

**Auth**: viewer (minimum)
**Path Parameters**: `document_id` (string, UUID)

**Response** (local cache only, consistent):
```json
{
  "document_id": "abc-123",
  "document_nodes": 1,
  "atom_nodes": 47,
  "contains_edges": 47,
  "expected_atom_nodes": 47,
  "projection_status": "complete",
  "neo4j_verified": false,
  "neo4j_document_nodes": null,
  "neo4j_atom_nodes": null,
  "neo4j_contains_edges": null,
  "consistent": true
}
```

**Response** (with Neo4j, inconsistent):
```json
{
  "document_id": "abc-123",
  "document_nodes": 1,
  "atom_nodes": 47,
  "contains_edges": 47,
  "expected_atom_nodes": 50,
  "projection_status": "partial",
  "neo4j_verified": true,
  "neo4j_document_nodes": 1,
  "neo4j_atom_nodes": 45,
  "neo4j_contains_edges": 45,
  "consistent": false
}
```

**Error cases**:
- 401: Missing/invalid API key
- 403: Insufficient role
- 404: Document not found

---

## Service Architecture

### HypergraphProjector (`hypergraph.py`)

The central graph service. Instantiated once per application in `create_app()` (`main.py:58`). Injected with Neo4j connection parameters from `Settings`. Stored on `app.state.hypergraph`. Passed to `IngestionService` and `JobService` constructors.

**Initialization flow:**

```
create_app()
  -> HypergraphProjector(uri, username, password)    # main.py:58
     -> if all 3 non-None: GraphDatabase.driver()    # hypergraph.py:24-25
     -> self.local = LocalGraphCache()                # hypergraph.py:23
  -> IngestionService(settings, hypergraph)           # main.py:66
  -> JobService(..., hypergraph)                      # main.py:69-75
```

**`project_document()` flow:**

```
1. Clear stale local projection:
   a. Find all edges from doc_node_id with type=CONTAINS
   b. Collect target atom_ids from those edges
   c. Remove those edges from self.local.edges
   d. Remove atom nodes from self.local.nodes
   e. Remove doc node from self.local.nodes

2. Create local projection:
   a. Add doc node: self.local.nodes["doc:{id}"] = {label: "Document", ...payload}
   b. For each atom:
      - Add atom node: self.local.nodes["atom:{atom.id}"] = {label: "Atom", ...atom}
      - Add CONTAINS edge: {type, from, to, metadata: {atom_level}}

3. If Neo4j enabled:
   a. MATCH + DETACH DELETE old atoms for document
   b. MERGE document node, SET properties
   c. For each chunk of 500 atoms:
      - UNWIND atoms, MERGE atom nodes, SET properties
      - MATCH document, MERGE CONTAINS relationship

4. Return {document_node_id, atom_node_ids}
```

**`integrity_for_document()` flow:**

```
1. Compute base result from Document model fields:
   - expected = document.atom_count
   - projected = document.graph_projected_atom_count
   - consistent = (status == "complete") AND (expected == projected)

2. If Neo4j available:
   a. MATCH (d:Document {id})-[r:CONTAINS]->(a:Atom)
   b. COUNT DISTINCT d, a, r
   c. Extend consistent check with Neo4j counts

3. Return full integrity dict
```

**`query()` resolution flow:**

```
1. Normalize relationship_type to uppercase (or None)
2. Resolve target_node:
   - Use node_id if provided
   - Else use "doc:{document_id}" if document_id provided
   - Else None

3. Attempt local cache:
   - If target_node in self.local.nodes:
     Filter edges, collect connected nodes, return source="local_cache"

4. Attempt Neo4j:
   - If driver exists AND document_id:
     Cypher MATCH (d:Document {id})-[r]->(n) LIMIT
     Post-filter by relationship_type
     Return source="neo4j"

5. Return source="empty"
```

### Integration with IngestionService (`ingestion.py`)

The ingestion service orchestrates graph projection as part of the document ingestion lifecycle:

```
ingest_batch()
  -> for each file:
     -> _create_atoms()                         # Creates Atom + ProjectionLedger rows
     -> try:
          hypergraph.project_document()          # Dual-write to graph
          doc.graph_projected_atom_count = N
          doc.graph_projection_status = "complete"|"partial"
          _update_projection_ledger(status="projected")
        except:
          doc.graph_projection_status = "failed"
          _update_projection_ledger(status="failed", error=str(exc))
          warnings.append(...)
```

Key integration points:
- `ingestion.py:29-31`: IngestionService constructor receives `HypergraphProjector`
- `ingestion.py:142-155`: `project_document()` call with try/except
- `ingestion.py:393-399`: `ProjectionLedger` row creation during `_create_atoms()`
- `ingestion.py:459-480`: `_update_projection_ledger()` updates status + attempt_count

### Integration with JobService (`main.py:69-75`)

The `JobService` receives the `HypergraphProjector` for potential use in async job execution. Currently, the job service does not directly call hypergraph methods -- it delegates to `IngestionService` which handles projection internally.

---

## Research Notes

### Dependencies

| Dependency | Used For | Required? |
|------------|----------|-----------|
| `neo4j` | Neo4j Python driver for graph database writes/reads | No (import at module level but driver only instantiated when URI provided) |
| `sqlalchemy` | ORM for ProjectionLedger, Document model fields | Yes |

### Neo4j Driver Import

The `neo4j` package is imported at the top of `hypergraph.py` (`from neo4j import Driver, GraphDatabase`). This means the `neo4j` pip package must be installed even when Neo4j is not configured. If the package is missing, the import fails and the entire application fails to start. This could be mitigated with a lazy import.

### Complexity / Performance Considerations

- **Local cache memory**: Each atom node is a dict entry with ~5-6 keys. Each edge is a dict with 4 keys. For a large document with 100K atoms: ~100K node dicts + ~100K edge dicts. Estimated ~50-80MB per large document. For 5 seed texts, total could reach 400MB+.

- **Local cache `_clear_local_projection()` performance**: Uses list comprehension to filter `self.local.edges`, which is `O(total_edges)` for every re-projection. With millions of edges, this becomes slow. Consider switching to a dict-of-lists keyed by `from` node for `O(atoms_per_doc)` cleanup.

- **Neo4j chunking**: 500 atoms per Cypher UNWIND. Each chunk is a separate `neo_session.run()` call within the same session. For a 100K-atom document, this is 200 Cypher transactions. Consider using explicit transactions for batching.

- **Neo4j DETACH DELETE**: The cleanup query `MATCH (d:Document {id})-[r:CONTAINS]->(a:Atom) DELETE r ... DETACH DELETE atom` can be slow for documents with many atoms. Consider adding an index on `Document.id` in Neo4j.

- **Query edge filtering**: Local cache query filters edges by iterating the entire edge list (`hypergraph.py:146-151`). No index structure exists. For millions of edges, this is `O(total_edges)`. Consider an adjacency list structure.

- **Integrity check is database-driven**: `integrity_for_document()` reads `atom_count` and `graph_projected_atom_count` from the Document model, not from the actual local cache node/edge counts. This means integrity checks do not detect local cache corruption (e.g., missing nodes due to a bug in `_clear_local_projection()`).

### Known Risks

1. **Neo4j import failure**: The `neo4j` package is imported unconditionally. If not installed, the application crashes at startup even without Neo4j configuration. Mitigation: Lazy import with try/except.

2. **Local cache is not thread-safe**: `LocalGraphCache` uses a plain `dict` and `list` with no locking. Concurrent API requests could produce read/write races on the cache. Mitigation: Read-only after projection (queries do not mutate), but concurrent ingestions could race on `_clear_local_projection()`.

3. **Neo4j partial failure**: If Neo4j connection drops between DETACH DELETE and atom MERGE, the document's atoms are deleted from Neo4j but not re-created. The system will report `graph_projection_status="complete"` because the local cache projection succeeded. Mitigation: Wrap Neo4j operations in an explicit transaction and roll back on partial failure.

4. **Orphan ProjectionLedger rows**: When a document is re-ingested, old atoms are deleted (`DELETE FROM atoms WHERE document_id = ...`) and new ones created with new UUIDs. Old `ProjectionLedger` rows with stale `atom_id` values are not cleaned up because `atom_id` is not a FK. Mitigation: Delete ledger rows for the document before re-creating atoms, or cascade through a proper FK.

5. **No Neo4j indexes**: No constraints or indexes are created on Neo4j labels/properties. `MERGE` operations on large graphs without indexes are slow. Mitigation: Add Neo4j index creation during application startup (e.g., `CREATE INDEX ON :Document(id)`, `CREATE INDEX ON :Atom(id)`).

6. **Edge list memory growth**: `self.local.edges` is an append-only list (except during `_clear_local_projection()`). With many documents, the list grows monotonically. Consider periodic compaction or a more efficient data structure.

### Future Architecture Considerations

- **Persistent local cache** (US-010): Could serialize `LocalGraphCache` to a SQLite table or JSON file on shutdown and reload on startup. Alternatively, hydrate from the database by querying all Documents + Atoms with `graph_projection_status="complete"` and rebuilding the cache.

- **Projection retry queue** (US-009): Could use the existing `Job` system: a periodic worker queries `ProjectionLedger` for `status="failed" AND attempt_count < max_retries`, submits retry jobs. Each retry calls `project_document()` for the affected document.

- **Adjacency list optimization**: Replace `edges: list[dict]` with `adjacency: dict[str, list[dict]]` keyed by node ID. This enables `O(1)` lookup for edges from a specific node instead of `O(total_edges)` scan.

- **Atom-to-atom edges** (US-011): Could be added as new edge types in both `LocalGraphCache` and Neo4j. Requires changes to `_clear_local_projection()` to preserve non-CONTAINS edges, and to `query()` to handle multi-type traversals.

- **Graph export** (US-016): Could use `networkx` as an intermediary: build an `nx.DiGraph` from `LocalGraphCache`, then export via `nx.write_graphml()`, `nx.readwrite.json_graph`, or custom RDF serialization. Alternatively, export directly from Neo4j using APOC procedures.

- **Neo4j lazy import**: Wrap the `neo4j` import in a try/except at the top of `hypergraph.py`. If the package is not installed, set `Driver = None` and `GraphDatabase = None`. The `__init__` method already checks `if uri and username and password` before using `GraphDatabase.driver()`, so the lazy import just prevents startup crashes.
