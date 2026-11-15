# 07 -- Hypergraph: Specification

> **Domain:** 07-hypergraph
> **Status:** Draft
> **Last updated:** 2026-02-23
> **Source of truth:** `src/nexus_babel/services/hypergraph.py`, `src/nexus_babel/api/routes.py`

---

## 1. Overview

The Hypergraph domain is the graph projection and query layer of the ARC4N Living Digital Canon. It maintains a dual-write knowledge graph that mirrors the relational database's Document-Atom hierarchy into a graph structure suitable for traversal, relationship discovery, and integrity verification. Every ingested document and its atoms are projected as nodes connected by `CONTAINS` edges, with writes going to both an always-available in-memory `LocalGraphCache` and an optional Neo4j graph database when configured.

This domain provides two primary capabilities: (1) graph projection during ingestion -- transforming relational Document/Atom records into graph nodes and edges, tracked per-atom via a `ProjectionLedger`; and (2) graph querying and integrity verification -- enabling callers to traverse the graph by document or node ID, filter by relationship type, and verify that projected graph counts match the relational source of truth. The system gracefully degrades: when Neo4j is unavailable, all operations fall back to the local cache, and projection failures during ingestion are non-fatal (documents are still saved with `graph_projection_status="failed"`).

The vision extends this foundation with atom-to-atom relationships (PRECEDES, SIMILAR_TO), multi-hop traversals, semantic similarity edges based on embeddings, temporal graph modeling of evolution branch events, graph-based analytical measures (centrality, community detection), graph export in standard formats (GraphML, RDF, JSON-LD), a projection retry queue for failed atoms, and persistent local cache to survive application restarts.

---

## 2. User Stories

### P1 -- As-Built (Verified)

#### US-001: Dual-write graph projection during ingestion

> As the **system**, I want every ingested document and its atoms projected into both the local graph cache and Neo4j (when configured) so that graph queries are available immediately after ingestion with graceful fallback.

**Given** a successfully ingested document with atoms
**When** `HypergraphProjector.project_document()` is called (`hypergraph.py:35-82`)
**Then**:
- Stale local projections for the document are cleared via `_clear_local_projection()` (`hypergraph.py:84-89`)
- A `doc:{document_id}` node is created in `LocalGraphCache.nodes` with label "Document" and document payload properties (`hypergraph.py:38`)
- For each atom, an `atom:{atom_id}` node is created in `LocalGraphCache.nodes` with label "Atom" and atom properties (`hypergraph.py:42-44`)
- A `CONTAINS` edge is created from `doc:{document_id}` to each `atom:{atom_id}` with `atom_level` metadata (`hypergraph.py:45-52`)
- If Neo4j driver is configured (`self._driver is not None`):
  - Old atoms for the document are DETACH DELETEd via Cypher (`hypergraph.py:56-63`)
  - The document node is MERGEd (upserted) with properties (`hypergraph.py:64-68`)
  - Atoms are MERGEd in batches of `PROJECTION_CHUNK_SIZE=500` with CONTAINS relationships (`hypergraph.py:69-80`)
- Returns `{"document_node_id": "doc:{id}", "atom_node_ids": ["atom:{id}", ...]}` (`hypergraph.py:82`)

**Code evidence:** `test_mvp.py:132-143` (`test_hypergraph_integrity`), `test_mvp.py:300-328` (`test_integrity_persists_across_restart`).

#### US-002: Local graph cache as always-available fallback

> As the **system**, I want an in-memory graph cache that is always populated regardless of Neo4j availability so that graph queries never fail due to infrastructure dependencies.

**Given** a `HypergraphProjector` initialized without Neo4j credentials (`neo4j_uri=None`)
**When** documents are projected
**Then**:
- `enabled` property returns `False` (`hypergraph.py:28-29`)
- `LocalGraphCache` still receives all nodes and edges (`hypergraph.py:38-52`)
- No Neo4j operations are attempted (`hypergraph.py:54` conditional)
- Query operations fall through to local cache lookup (`hypergraph.py:145-162`)
- Integrity checks return with `neo4j_verified=False` and `None` for Neo4j counts (`hypergraph.py:101-109`)

**Code evidence:** `conftest.py:22-24` sets `neo4j_uri=None`, all integration tests run against local cache only.

#### US-003: Graph integrity verification

> As a **viewer**, I want to verify that the graph projection for a document is consistent with the relational database so that I can detect projection drift or failures.

**Given** an ingested document with `atom_count` and `graph_projected_atom_count` fields
**When** `GET /api/v1/hypergraph/documents/{id}/integrity` is called (`routes.py:367-376`)
**Then** `integrity_for_document()` (`hypergraph.py:91-130`) returns:
- `document_id`: The document UUID
- `document_nodes`: Always 1 (the document itself)
- `atom_nodes`: Value of `graph_projected_atom_count` from the document
- `contains_edges`: Same as `atom_nodes` (1:1 with atoms)
- `expected_atom_nodes`: Value of `atom_count` from the document
- `projection_status`: Value of `graph_projection_status` from the document
- `consistent`: `True` only when `projection_status == "complete"` AND `expected == projected` (`hypergraph.py:105`)
- If Neo4j is available: additionally queries Neo4j for `document_nodes`, `atom_nodes`, `contains_edges` counts, sets `neo4j_verified=True`, and extends `consistent` to require Neo4j counts match expected (`hypergraph.py:111-130`)
- If Neo4j unavailable: `neo4j_verified=False`, Neo4j counts are `None` (`hypergraph.py:108-109`)

**Code evidence:** `test_mvp.py:132-143` (`test_hypergraph_integrity`), `test_mvp.py:300-328` (`test_integrity_persists_across_restart`).

#### US-004: Graph query by document or node

> As a **viewer**, I want to query the graph by document ID, node ID, or relationship type so that I can explore the document-atom graph structure.

**Given** an ingested document projected into the graph
**When** `GET /api/v1/hypergraph/query` is called with optional `document_id`, `node_id`, `relationship_type`, `limit` parameters (`routes.py:613-626`)
**Then** `query()` (`hypergraph.py:132-191`) resolves the target node and returns results from the first available source:

1. **Local cache hit** (`hypergraph.py:145-162`): If `node_id` (or `doc:{document_id}`) is found in `self.local.nodes`:
   - Filters edges where target node is either `from` or `to`, optionally filtered by uppercased `relationship_type` (`hypergraph.py:146-151`)
   - Applies `limit` to edge count (`hypergraph.py:151`)
   - Collects all connected node IDs from matching edges (`hypergraph.py:152-155`)
   - Returns `{"source": "local_cache", "nodes": [...], "edges": [...], "count": {"nodes": N, "edges": N}}`

2. **Neo4j fallback** (`hypergraph.py:164-189`): If local cache misses but Neo4j driver exists and `document_id` is provided:
   - Runs `MATCH (d:Document {id: $id})-[r]->(n) RETURN ... LIMIT $limit` Cypher query (`hypergraph.py:166-172`)
   - Post-filters by `relationship_type` if specified (`hypergraph.py:178`)
   - Returns `{"source": "neo4j", "nodes": [...], "edges": [...], "count": {"nodes": N, "edges": N}}`

3. **Empty** (`hypergraph.py:191`): If neither source has data, returns `{"source": "empty", "nodes": [], "edges": [], "count": {"nodes": 0, "edges": 0}}`

**Code evidence:** `test_wave2.py:132-136` (`test_hypergraph_query_and_audit_decisions`).

#### US-005: Projection ledger per-atom tracking

> As the **system**, I want every atom's projection status tracked in a `ProjectionLedger` so that failed projections are identifiable and retryable.

**Given** atoms created during ingestion
**When** `_create_atoms()` runs in `ingestion.py:370-414`
**Then**:
- A `ProjectionLedger` row is created for each atom with `status="pending"`, `attempt_count=0` (`ingestion.py:393-399`)
- After successful projection, `_update_projection_ledger()` sets `status="projected"` and increments `attempt_count` (`ingestion.py:150, 459-480`)
- After failed projection, `_update_projection_ledger()` sets `status="failed"`, increments `attempt_count`, and records `last_error` (`ingestion.py:154, 459-480`)
- `ProjectionLedger` has a unique constraint on `(document_id, atom_id)` (`models.py:289-291`)

**Code evidence:** Implicitly tested via integrity checks in `test_mvp.py:132-143` which verify `graph_projected_atom_count` matches `atom_count`.

#### US-006: Non-fatal projection failure

> As the **system**, I want graph projection failures to be non-fatal so that document ingestion succeeds even when the graph store is degraded.

**Given** an ingestion in progress where `project_document()` raises an exception
**When** the exception is caught (`ingestion.py:151-155`)
**Then**:
- The document is still saved with `graph_projection_status="failed"` (`ingestion.py:153`)
- A warning is appended to the batch warnings list (`ingestion.py:155`)
- Projection ledger rows are updated to `status="failed"` with the error message (`ingestion.py:154`)
- The overall batch can still complete with status `completed` or `completed_with_errors` (`ingestion.py:203-206`)
- The document's `ingest_status` becomes `"ingested_with_warnings"` (`ingestion.py:170-173`)

**Code evidence:** The `except Exception as graph_exc` block in `ingestion.py:151` is marked `# pragma: no cover` indicating this fallback path is not covered by existing tests.

#### US-007: Stale projection cleanup on re-ingestion

> As the **system**, I want stale graph projections to be cleared when a document is re-ingested so that the graph always reflects the current state.

**Given** a document that was previously projected and is now being re-ingested
**When** `project_document()` is called again (`hypergraph.py:35-82`)
**Then**:
- `_clear_local_projection()` removes the old `doc:{id}` node, all atom nodes connected via `CONTAINS` edges, and the edges themselves from `LocalGraphCache` (`hypergraph.py:84-89`)
- If Neo4j is enabled: old atoms are DETACH DELETEd and the document node is re-MERGEd (`hypergraph.py:56-68`)
- New atom nodes and edges are created fresh

**Code evidence:** Implicit in the re-ingestion flow; not directly tested in isolation.

#### US-008: HypergraphProjector lifecycle management

> As the **system**, I want the `HypergraphProjector` to properly manage its Neo4j driver lifecycle so that connections are cleaned up on shutdown.

**Given** an application with an active `HypergraphProjector`
**When** the application lifespan exits (`main.py:52`)
**Then**:
- `close()` is called on the `HypergraphProjector` (`hypergraph.py:31-33`)
- If Neo4j driver exists, `self._driver.close()` is called
- If no driver, `close()` is a no-op

**Code evidence:** `main.py:52` calls `app.state.hypergraph.close()` in the lifespan yield cleanup.

### P2 -- Partially Built

#### US-009: Projection retry for failed atoms

> As the **system**, I want failed atom projections to be retried so that transient graph store failures do not permanently block projection.

**Current state**: The `ProjectionLedger` model has `attempt_count` and `last_error` fields (`models.py:284-286`), and `_update_projection_ledger()` increments `attempt_count` on each attempt (`ingestion.py:479`). However, there is no mechanism to re-attempt failed projections -- failed atoms stay in `status="failed"` permanently.

**Gap**: No retry worker or cron job that queries `ProjectionLedger` for `status="failed"` and re-attempts projection. No configurable retry limit or backoff strategy for projection attempts.

#### US-010: Local cache persistence across restarts

> As the **system**, I want the local graph cache to survive application restarts so that graph queries work immediately after startup without requiring re-ingestion.

**Current state**: `LocalGraphCache` is an in-memory `dataclass` with `dict` and `list` fields (`hypergraph.py:14-17`). On application restart, the cache is empty. The `test_integrity_persists_across_restart` test (`test_mvp.py:300-328`) verifies that integrity data persists (via the database `graph_projected_atom_count` field), but the actual local cache nodes/edges are lost.

**Gap**: No serialization/deserialization of `LocalGraphCache` to disk. No startup hydration from the database. Graph queries after restart return `"source": "empty"` unless Neo4j is configured.

### P3+ -- Vision

#### US-011: Atom-to-atom relationships

> As a **researcher**, I want atoms to have relationships beyond Document-CONTAINS-Atom (e.g., PRECEDES, SIMILAR_TO, REFERENCES) so that inter-atom navigation and analysis is possible.

**Current state**: Only `CONTAINS` edges from Document to Atom exist. Atoms have ordinals within their level, but no explicit ordering edges or semantic similarity edges.

**Vision**: `Atom-PRECEDES->Atom` edges for sequential ordering within a level. `Atom-SIMILAR_TO->Atom` edges based on embedding cosine similarity. `Atom-REFERENCES->Atom` for citation or thematic cross-links across documents.

#### US-012: Multi-hop graph traversals

> As a **researcher**, I want to perform multi-hop queries (e.g., "find all atoms 2 hops from this atom") so that I can discover indirect relationships in the knowledge graph.

**Current state**: `query()` only returns directly connected nodes (1-hop). No Cypher variable-length path queries or local cache BFS/DFS.

**Vision**: Query parameter `hops` (default 1, max configurable). Local cache BFS with depth tracking. Neo4j `MATCH p = (n)-[*1..N]->(m)` queries.

#### US-013: Semantic similarity edges

> As a **researcher**, I want the system to compute embedding-based similarity between atoms and create SIMILAR_TO edges so that semantically related content is discoverable via the graph.

**Current state**: No embedding computation or storage. No similarity edges.

**Vision**: Integration with embedding provider (e.g., sentence-transformers, OpenAI embeddings). Similarity computed at word/sentence level. Edges created above a configurable cosine threshold. Stored in both local cache and Neo4j.

#### US-014: Cross-document relationship discovery

> As a **researcher**, I want the graph to surface cross-document connections (shared entities, thematic links) so that the corpus is navigable as a unified knowledge graph.

**Current state**: Documents are isolated subgraphs (each document's atoms connect only to that document). Cross-document links exist only in `DocumentVariant` (sibling representations) and `provenance.cross_modal_links`, not in the graph.

**Vision**: Shared entity extraction → entity nodes shared across documents. Thematic clustering → thematic group nodes. Evolution lineage → branch-document edges.

#### US-015: Temporal graph for evolution events

> As a **researcher**, I want evolution branch events to be represented as graph edges so that the temporal evolution of texts is navigable via graph queries.

**Current state**: Branch events are stored in `BranchEvent` rows. No graph representation of branches or evolution events.

**Vision**: `Branch` nodes connected to `Document` via `DERIVED_FROM` edges. `BranchEvent` nodes connected to `Branch` via `EVOLVED_BY` edges. Temporal ordering via `NEXT_EVENT` edges.

#### US-016: Graph export in standard formats

> As a **researcher**, I want to export the graph in GraphML, RDF, or JSON-LD so that it can be analyzed in external graph tools (Gephi, Neo4j Desktop, SPARQL endpoints).

**Current state**: No export functionality. The only way to access graph data is via the query API.

**Vision**: `GET /api/v1/hypergraph/export?format=graphml&document_id=...` endpoint. Supported formats: GraphML, JSON-LD, RDF/Turtle. Optional filtering by document or subgraph.

#### US-017: Graph-based analysis measures

> As a **researcher**, I want centrality, community detection, and other graph analytics computed over the document-atom graph so that structurally important atoms are identifiable.

**Current state**: No analytical measures computed.

**Vision**: Degree centrality, betweenness centrality, PageRank on atom nodes. Community detection (Louvain, label propagation). Results stored as node properties and queryable via API.

#### US-018: Graph visualization API

> As a **viewer**, I want a visualization endpoint that returns graph data in a format suitable for rendering (e.g., force-directed layout coordinates) so that the frontend can display interactive graph views.

**Current state**: The `/app/hypergraph` view exists (`main.py:103-108`) but renders a generic HTML shell. No API endpoint provides visualization-ready data.

**Vision**: `GET /api/v1/hypergraph/visualize?document_id=...` returning nodes with x/y coordinates, edge lists, and styling metadata (color by atom level, size by centrality).

---

## 3. Functional Requirements

### Graph Projection

- **FR-001** [MUST] The system MUST project every ingested document as a `doc:{document_id}` node in `LocalGraphCache` with label "Document" and payload properties (path, modality, checksum). Implemented: `hypergraph.py:38`.
- **FR-002** [MUST] The system MUST project every atom as an `atom:{atom_id}` node in `LocalGraphCache` with label "Atom" and atom properties (id, document_id, atom_level, ordinal, content). Implemented: `hypergraph.py:42-44`.
- **FR-003** [MUST] The system MUST create a `CONTAINS` edge from the document node to each atom node with `atom_level` metadata. Implemented: `hypergraph.py:45-52`.
- **FR-004** [MUST] When Neo4j is configured (URI, username, password all non-None), the system MUST also write to Neo4j using MERGE for idempotent upserts. Implemented: `hypergraph.py:54-80`.
- **FR-005** [MUST] Neo4j atom projection MUST use chunked batches of `PROJECTION_CHUNK_SIZE` (500) to avoid transaction size limits. Implemented: `hypergraph.py:69-80`, constant at `hypergraph.py:11`.
- **FR-006** [MUST] Before projecting, the system MUST clear stale local projections for the document by removing old atom nodes and edges. Implemented: `hypergraph.py:37, 84-89`.
- **FR-007** [MUST] Before projecting to Neo4j, the system MUST DETACH DELETE old atom nodes for the document. Implemented: `hypergraph.py:56-63`.
- **FR-008** [MUST] The `project_document()` return value MUST include `document_node_id` and `atom_node_ids`. Implemented: `hypergraph.py:82`.

### Projection Tracking

- **FR-009** [MUST] A `ProjectionLedger` row MUST be created for every atom during ingestion with `status="pending"` and `attempt_count=0`. Implemented: `ingestion.py:393-399`.
- **FR-010** [MUST] After successful projection, ledger rows MUST be updated to `status="projected"` with `attempt_count` incremented. Implemented: `ingestion.py:150, 459-480`.
- **FR-011** [MUST] After failed projection, ledger rows MUST be updated to `status="failed"` with `attempt_count` incremented and `last_error` recorded. Implemented: `ingestion.py:154, 459-480`.
- **FR-012** [MUST] The `ProjectionLedger` MUST enforce a unique constraint on `(document_id, atom_id)`. Implemented: `models.py:289-291`.
- **FR-013** [MUST] The `Document` model MUST track `graph_projected_atom_count` (Integer) and `graph_projection_status` (pending/complete/partial/failed). Implemented: `models.py:47-48`.

### Graceful Degradation

- **FR-014** [MUST] Graph projection failure MUST NOT prevent document save. The document MUST be saved with `graph_projection_status="failed"` and a warning appended to the batch. Implemented: `ingestion.py:151-155`.
- **FR-015** [MUST] When Neo4j is not configured, `HypergraphProjector.enabled` MUST return `False` and all Neo4j-specific operations MUST be skipped. Implemented: `hypergraph.py:24-25, 28-29, 54`.
- **FR-016** [MUST] `close()` MUST be safe to call regardless of whether Neo4j is configured. Implemented: `hypergraph.py:31-33`.

### Integrity Verification

- **FR-017** [MUST] `GET /api/v1/hypergraph/documents/{id}/integrity` MUST return a consistency report comparing relational `atom_count` vs `graph_projected_atom_count`. Implemented: `routes.py:367-376`, `hypergraph.py:91-130`.
- **FR-018** [MUST] The integrity response MUST include `document_id`, `document_nodes`, `atom_nodes`, `contains_edges`, `expected_atom_nodes`, `projection_status`, `neo4j_verified`, `neo4j_document_nodes`, `neo4j_atom_nodes`, `neo4j_contains_edges`, and `consistent` (boolean). Implemented: `hypergraph.py:94-106, 123-130`.
- **FR-019** [MUST] `consistent` MUST be `True` only when `projection_status == "complete"` AND `expected_atom_nodes == atom_nodes`. Implemented: `hypergraph.py:105`.
- **FR-020** [MUST] When Neo4j is available, `consistent` MUST additionally require `neo4j_document_nodes == 1`, `neo4j_atom_nodes == expected`, and `neo4j_contains_edges == expected`. Implemented: `hypergraph.py:129`.
- **FR-021** [MUST] If the document ID is not found, the endpoint MUST return HTTP 404. Implemented: `routes.py:372-373`.

### Graph Query

- **FR-022** [MUST] `GET /api/v1/hypergraph/query` MUST accept optional `document_id`, `node_id`, `relationship_type`, and `limit` (1-1000, default 100) query parameters. Implemented: `routes.py:613-626`.
- **FR-023** [MUST] The query MUST first attempt to resolve from `LocalGraphCache` using `node_id` or `doc:{document_id}`. Implemented: `hypergraph.py:141-162`.
- **FR-024** [MUST] If `relationship_type` is provided, edges MUST be filtered by uppercased type string. Implemented: `hypergraph.py:140, 146-151`.
- **FR-025** [MUST] The query response MUST include `source` (local_cache/neo4j/empty), `nodes`, `edges`, and `count` (nodes + edges). Implemented: `hypergraph.py:157-162, 184-189, 191`.
- **FR-026** [MUST] If local cache misses and Neo4j is available with a `document_id`, the query MUST fall back to a Neo4j Cypher query. Implemented: `hypergraph.py:164-189`.
- **FR-027** [MUST] If neither source yields results, the query MUST return `source: "empty"` with empty arrays. Implemented: `hypergraph.py:191`.
- **FR-028** [MUST] The `limit` parameter MUST cap the number of edges returned from local cache and rows returned from Neo4j. Implemented: `hypergraph.py:151, 169`.

### Auth

- **FR-029** [MUST] The query endpoint MUST require minimum `viewer` role authentication. Implemented: `routes.py:613`.
- **FR-030** [MUST] The integrity endpoint MUST require minimum `viewer` role authentication. Implemented: `routes.py:367`.

### Future

- **FR-031** [SHOULD] The system SHOULD provide a projection retry mechanism for atoms with `status="failed"` in the ledger. Not yet implemented.
- **FR-032** [SHOULD] The `LocalGraphCache` SHOULD be hydrated from the database on startup so that graph queries work after restart without Neo4j. Not yet implemented.
- **FR-033** [SHOULD] The query endpoint SHOULD support pagination (offset/cursor) for large result sets. Not yet implemented.
- **FR-034** [SHOULD] The system SHOULD support atom-to-atom relationships (PRECEDES, SIMILAR_TO) beyond Document-CONTAINS-Atom. Not yet implemented.
- **FR-035** [SHOULD] The system SHOULD support multi-hop traversal queries with configurable depth. Not yet implemented.
- **FR-036** [MAY] The system MAY compute and store graph analytics (centrality, community detection) on atom nodes. Not yet implemented.
- **FR-037** [MAY] The system MAY export the graph in GraphML, RDF/Turtle, or JSON-LD formats. Not yet implemented.
- **FR-038** [MAY] The system MAY provide a visualization-ready API endpoint with layout coordinates. Not yet implemented.
- **FR-039** [MAY] The system MAY project evolution branch events into the graph as temporal edges. Not yet implemented.

---

## 4. Key Entities

### HypergraphProjector (`hypergraph.py:20-191`)

The central service class. Manages dual-write to `LocalGraphCache` and Neo4j.

| Attribute | Type | Purpose |
|-----------|------|---------|
| `_driver` | `Driver \| None` | Neo4j Python driver (None when unconfigured) |
| `local` | `LocalGraphCache` | Always-available in-memory graph |

| Method | Purpose |
|--------|---------|
| `enabled` | Property: `True` if Neo4j driver exists |
| `project_document(document_id, document_payload, atoms)` | Project document + atoms to both stores |
| `_clear_local_projection(doc_node_id)` | Remove stale nodes/edges from local cache |
| `integrity_for_document(document)` | Compare DB counts vs graph counts |
| `query(document_id, node_id, relationship_type, limit)` | Query graph from local cache or Neo4j |
| `close()` | Clean up Neo4j driver |

### LocalGraphCache (`hypergraph.py:14-17`)

| Field | Type | Purpose |
|-------|------|---------|
| `nodes` | `dict[str, dict[str, Any]]` | Node ID -> properties dict. Keys are `doc:{uuid}` or `atom:{uuid}` |
| `edges` | `list[dict[str, Any]]` | Each edge: `{"type": str, "from": str, "to": str, "metadata": dict}` |

### ProjectionLedger (`models.py:277-291`)

| Field | Type | Purpose |
|-------|------|---------|
| `id` | String(36) PK | UUID |
| `document_id` | FK -> documents | Parent document (CASCADE delete) |
| `atom_id` | String(36) | Atom UUID (not a FK -- flexible) |
| `status` | String(32) | `pending` / `projected` / `failed` |
| `attempt_count` | Integer | Number of projection attempts |
| `last_error` | String(512) nullable | Error message from last failure |
| `created_at` | DateTime(tz) | Row creation time |
| `updated_at` | DateTime(tz) | Last update time |

Unique constraint: `(document_id, atom_id)` -- `uq_projection_ledger_document_atom`.

### Document -- Graph-Relevant Fields (`models.py:46-48`)

| Field | Type | Purpose |
|-------|------|---------|
| `graph_projected_atom_count` | Integer | Count of atoms successfully projected to graph |
| `graph_projection_status` | String(32) | `pending` / `complete` / `partial` / `failed` |

### Graph Node Schema

**Document Node** (`doc:{uuid}`):
```json
{
  "label": "Document",
  "path": "/abs/path/to/file.md",
  "modality": "text",
  "checksum": "sha256hex..."
}
```

**Atom Node** (`atom:{uuid}`):
```json
{
  "label": "Atom",
  "id": "uuid",
  "document_id": "uuid",
  "atom_level": "word",
  "ordinal": 1,
  "content": "Sing"
}
```

**CONTAINS Edge**:
```json
{
  "type": "CONTAINS",
  "from": "doc:uuid",
  "to": "atom:uuid",
  "metadata": {"atom_level": "word"}
}
```

---

## 5. Edge Cases

### Covered by tests

- **Integrity with local cache only** (`test_mvp.py:132-143`): Integrity check returns `consistent=True` when `atom_count == graph_projected_atom_count` and no Neo4j is configured.
- **Integrity persists across restart** (`test_mvp.py:300-328`): Database-stored counts survive restart; integrity check works against a fresh app instance (though local cache is empty, the DB counts provide the answer).
- **Query with empty graph** (`test_wave2.py:132-136`): Query returns nodes for a document that has been projected.
- **No auth on query returns 401** (implicit via `_require_auth("viewer")` dependency on routes).

### Not covered / known gaps

- **Neo4j integration testing**: All tests run with `neo4j_uri=None`. No integration test verifies actual Neo4j writes, reads, or the DETACH DELETE + MERGE flow. The Neo4j code path is untested in CI.
- **Chunked projection for large documents**: `PROJECTION_CHUNK_SIZE=500` batching is not tested with documents having >500 atoms. Boundary conditions (exactly 500, 501, 999, 1000 atoms) are untested.
- **Stale projection cleanup correctness**: `_clear_local_projection()` removes edges where `edge["from"] == doc_node_id` but does not handle atoms that are also referenced by other edges (future atom-to-atom edges). Currently safe because only `CONTAINS` edges exist.
- **Concurrent projection**: Two simultaneous calls to `project_document()` for the same document could interleave `_clear_local_projection` and node creation, producing an inconsistent local cache state. No locking exists.
- **Local cache memory pressure**: For the 5 seed texts (>1M atoms each for large texts), the local cache could hold >5M node entries and >5M edge entries. No memory bound or eviction strategy exists.
- **Neo4j connection failure mid-projection**: If the Neo4j connection drops after DETACH DELETE but before atom MERGE, the document will have 0 atoms in Neo4j but `graph_projection_status="complete"` based on local cache success.
- **Node ID collision**: Node IDs use `doc:{uuid}` and `atom:{uuid}` prefixes. If a UUID accidentally collides across documents (astronomically unlikely), nodes would be overwritten.
- **Query with node_id not in local cache and no document_id**: Falls through to empty result even if the node exists in Neo4j, because the Neo4j fallback only triggers when `document_id` is provided (`hypergraph.py:164`).
- **Relationship type case sensitivity**: The `query()` method uppercases the `relationship_type` filter (`hypergraph.py:140`), but Neo4j edges are stored with uppercase types. If a custom relationship type were added in mixed case, the filter would mismatch.
- **ProjectionLedger rows not deleted on re-ingestion**: When atoms are deleted and re-created during re-ingestion, old `ProjectionLedger` rows remain (atom IDs change, but old rows persist with stale atom IDs). The unique constraint prevents collision, but orphan rows accumulate.
- **No test for projection failure fallback**: The `except Exception as graph_exc` path in `ingestion.py:151` is marked `# pragma: no cover`.

---

## 6. Success Criteria

1. **Dual-write correctness**: After ingestion, `doc:{id}` and all `atom:{id}` nodes exist in `LocalGraphCache` with correct properties. `CONTAINS` edges correctly link them. When Neo4j is configured, the same data exists there.
2. **Integrity consistency**: For every successfully ingested document, `GET /hypergraph/documents/{id}/integrity` returns `consistent: true` with `atom_nodes == expected_atom_nodes`.
3. **Query completeness**: For every projected document, `GET /hypergraph/query?document_id={id}` returns at least one document node and all its atom nodes (within the limit).
4. **Graceful degradation**: When Neo4j is unavailable, all graph operations succeed via the local cache. No errors are surfaced to the API caller.
5. **Non-fatal projection**: When `project_document()` throws, the document is still saved, the batch completes, and the projection status correctly reflects the failure.
6. **Projection ledger accuracy**: Every atom has exactly one `ProjectionLedger` row with the correct status reflecting the actual projection outcome.
7. **Stale cleanup**: Re-ingesting a document clears old graph data before creating new projections, preventing ghost nodes or edges.
8. **Performance**: Projection of a 10K-atom document completes within 5 seconds (local cache). Neo4j projection of 10K atoms in 500-atom chunks completes within 30 seconds.
9. **Restart resilience**: After restart, integrity checks still return correct results based on database counts, even though the local cache is empty.
