# 07 -- Hypergraph: Task List

> **Domain:** 07-hypergraph
> **Status:** Draft
> **Last updated:** 2026-02-23
> **Source of truth:** `specs/07-hypergraph/spec.md`, `specs/07-hypergraph/plan.md`

---

## Phase 1: Setup

### T-SETUP-001: Create domain test file [P]

Create `tests/test_hypergraph.py` with domain-specific fixtures and imports. Reuse `conftest.py` fixtures (`client`, `auth_headers`, `sample_corpus`). Add helper function `_ingest_and_get_doc_id(client, corpus_path, headers) -> str` to streamline ingestion + doc ID extraction for graph tests.

**Files**: `tests/test_hypergraph.py`
**Acceptance**: File exists, `pytest tests/test_hypergraph.py -v` passes with 0 tests collected (skeleton).

### T-SETUP-002: Verify existing test coverage baseline [P]

Run existing hypergraph-related tests and document results:
- `pytest tests/test_mvp.py::test_hypergraph_integrity -v`
- `pytest tests/test_mvp.py::test_integrity_persists_across_restart -v`
- `pytest tests/test_wave2.py::test_hypergraph_query_and_audit_decisions -v`

Identify coverage gaps in `services/hypergraph.py` and the hypergraph-related routes.

**Files**: `tests/test_mvp.py`, `tests/test_wave2.py`
**Acceptance**: All 3 existing tests pass. Coverage report for `services/hypergraph.py` captured.

### T-SETUP-003: Add Neo4j mock infrastructure [P]

Create a `tests/mocks/neo4j_mock.py` module that provides a mock Neo4j driver, session, and result set. This enables testing Neo4j code paths without an actual Neo4j instance. The mock should:
- Track all Cypher queries executed with their parameters
- Return configurable result records for `integrity_for_document()` queries
- Support the `session.run().single()` and `session.run().data()` patterns used in `hypergraph.py`

**Files**: `tests/mocks/__init__.py`, `tests/mocks/neo4j_mock.py`
**Acceptance**: Mock imports work. Mock driver can be injected into `HypergraphProjector.__init__()` in tests.

---

## Phase 2: Foundational -- LocalGraphCache Improvements

### T-FOUND-001: Add adjacency list index to LocalGraphCache [Story: Performance]

Add an `adjacency: dict[str, list[int]]` field to `LocalGraphCache` that maps each node ID to the indices of its edges in the `edges` list. Update `project_document()` to maintain this index on insert, and `_clear_local_projection()` to use it for `O(1)` node lookup instead of `O(total_edges)` scan. Maintain backward compatibility -- `edges` list remains the source of truth.

**Files**: `src/nexus_babel/services/hypergraph.py`
**Acceptance**: `_clear_local_projection()` uses adjacency index. `query()` uses adjacency index for edge lookup. Existing tests pass without modification.

### T-FOUND-002: Add node count and edge count helpers to LocalGraphCache

Add `document_count() -> int`, `atom_count() -> int`, `edge_count() -> int`, and `node_count_for_document(doc_node_id: str) -> int` methods to `LocalGraphCache`. These support cache-level integrity checking (as opposed to the current DB-driven integrity check).

**Files**: `src/nexus_babel/services/hypergraph.py`
**Acceptance**: Methods return correct counts. Unit-tested directly.

### T-FOUND-003: Add lazy import for neo4j package

Wrap the `from neo4j import Driver, GraphDatabase` at the top of `hypergraph.py` in a try/except. If the `neo4j` package is not installed, set sentinel values so the module loads without error. `HypergraphProjector.__init__()` already guards against `None` URI, so the lazy import just prevents startup crashes when the neo4j pip package is absent.

**Files**: `src/nexus_babel/services/hypergraph.py`
**Acceptance**: Application starts when `neo4j` pip package is not installed. `enabled` returns `False`. All local cache operations work. Import error logged as warning.

---

## Phase 3: P1 Verification & Hardening

### T-P1-001: Add LocalGraphCache unit tests [Story: US-002] [P]

Test `LocalGraphCache` directly (not through API):
- New cache has empty nodes and edges
- Adding a document node and atom nodes populates correctly
- `_clear_local_projection()` removes document node, its atom nodes, and all CONTAINS edges
- `_clear_local_projection()` does not remove nodes/edges belonging to other documents
- Adding the same document twice (without clear) appends duplicate nodes

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-002: Add project_document unit tests [Story: US-001] [P]

Test `HypergraphProjector.project_document()` (local cache mode, no Neo4j):
- Projects a document with 0 atoms: only doc node created, no atom nodes or edges
- Projects a document with 3 atoms: doc node + 3 atom nodes + 3 CONTAINS edges
- Each CONTAINS edge has correct `from`, `to`, `type`, and `metadata.atom_level`
- Node IDs follow `doc:{id}` and `atom:{id}` format
- Return value contains correct `document_node_id` and `atom_node_ids`
- Re-projecting same document clears old data first (node count does not double)

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=6 tests, all pass.

### T-P1-003: Add project_document Neo4j path tests [Story: US-001] [P]

Using the Neo4j mock from T-SETUP-003, test the Neo4j write path:
- When Neo4j is enabled, DETACH DELETE Cypher query is executed for the document
- MERGE query is executed for the document node with correct properties
- Atoms are chunked into batches of PROJECTION_CHUNK_SIZE=500
- For 1200 atoms: 3 UNWIND queries (500 + 500 + 200)
- For exactly 500 atoms: 1 UNWIND query
- For 0 atoms: no UNWIND queries (only DETACH DELETE + MERGE)
- All Cypher queries receive correct parameters

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=6 tests, all pass.

### T-P1-004: Add integrity verification unit tests [Story: US-003] [P]

Test `integrity_for_document()`:
- Document with `atom_count=10`, `graph_projected_atom_count=10`, `graph_projection_status="complete"` -> `consistent=True`
- Document with `atom_count=10`, `graph_projected_atom_count=8`, `graph_projection_status="partial"` -> `consistent=False`
- Document with `atom_count=10`, `graph_projected_atom_count=10`, `graph_projection_status="failed"` -> `consistent=False`
- Document with `atom_count=0`, `graph_projected_atom_count=0`, `graph_projection_status="complete"` -> `consistent=True`
- With Neo4j mock returning matching counts -> `neo4j_verified=True`, `consistent=True`
- With Neo4j mock returning mismatched counts -> `consistent=False` even if local counts match

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=6 tests, all pass.

### T-P1-005: Add integrity API endpoint tests [Story: US-003] [P]

Test `GET /api/v1/hypergraph/documents/{id}/integrity` via TestClient:
- Valid document after ingestion -> 200 with `consistent=True`
- Non-existent document ID -> 404
- No auth header -> 401
- Viewer role -> 200 (access granted)
- Response contains all expected fields: `document_id`, `document_nodes`, `atom_nodes`, `contains_edges`, `expected_atom_nodes`, `projection_status`, `neo4j_verified`, `consistent`

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=5 tests, all pass.

### T-P1-006: Add query API endpoint tests [Story: US-004] [P]

Test `GET /api/v1/hypergraph/query` via TestClient:
- Query by `document_id` after ingestion -> `source="local_cache"`, nodes include doc + atoms, edges are CONTAINS type
- Query by `document_id` with `relationship_type=CONTAINS` -> same result (CONTAINS is the only type)
- Query by `document_id` with `relationship_type=UNKNOWN` -> `source="local_cache"` but 0 edges (node still found, just no matching edges)
- Query with `limit=2` -> at most 2 edges returned
- Query with no parameters -> `source="empty"`, 0 nodes, 0 edges
- Query with non-existent `document_id` -> `source="empty"` (node `doc:nonexistent` not in local cache)
- Query with `node_id=doc:{id}` directly -> same as querying by document_id
- Query with `node_id=atom:{id}` -> returns that atom and its connected doc node
- No auth header -> 401
- Viewer role -> 200 (access granted)

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=10 tests, all pass.

### T-P1-007: Add projection ledger tracking tests [Story: US-005]

Test via integration (ingest a document and verify ledger):
- After ingesting a text document, `ProjectionLedger` rows exist for every atom
- Each row has `status="projected"` and `attempt_count=1`
- The unique constraint on `(document_id, atom_id)` prevents duplicates
- Total ledger rows match `document.atom_count`

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=4 tests, all pass.

### T-P1-008: Add stale projection cleanup tests [Story: US-007] [P]

Test `_clear_local_projection()` edge cases:
- Clear a document that does not exist in the cache -> no error, no change
- Clear a document with 0 atoms -> doc node removed, no atom nodes to clean
- Clear a document with atoms -> all atoms and edges removed, other documents' atoms untouched
- After clear, re-projection creates fresh nodes (verified by checking node count)

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=4 tests, all pass.

### T-P1-009: Add projection failure fallback test [Story: US-006]

Create a test that forces `project_document()` to raise an exception (e.g., by monkeypatching or by injecting a broken `HypergraphProjector`) and verify that:
- The document is still saved to the database
- `graph_projection_status` is `"failed"`
- `ProjectionLedger` rows have `status="failed"` with `last_error` populated
- The batch response includes a warning but does not return an error status
- The document's `ingested` field is still True (or `ingest_status="ingested_with_warnings"`)

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=3 tests, all pass. This covers the `# pragma: no cover` path.

### T-P1-010: Add lifecycle management test [Story: US-008] [P]

Test `HypergraphProjector` lifecycle:
- `close()` without Neo4j driver -> no error
- `close()` with Neo4j mock driver -> `driver.close()` called
- `enabled` returns `False` when URI is None
- `enabled` returns `True` when URI, username, and password are all provided (with mock)

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=4 tests, all pass.

---

## Phase 4: P2 Completion

### T-P2-001: Implement projection retry mechanism [Story: US-009]

Add a `retry_failed_projections(session, max_retries=3)` method to `HypergraphProjector` that:
1. Queries `ProjectionLedger` for `status="failed" AND attempt_count < max_retries`
2. Groups failed atoms by `document_id`
3. For each document: loads the document and its atoms from the database, calls `project_document()`
4. Updates ledger rows to `status="projected"` or `status="failed"` (with incremented `attempt_count`)
5. Returns a summary: `{"documents_retried": N, "atoms_retried": N, "atoms_recovered": N, "atoms_still_failed": N}`

**Files**: `src/nexus_babel/services/hypergraph.py`, `src/nexus_babel/services/ingestion.py`
**Acceptance**: Method exists. Retry succeeds for atoms that failed due to transient errors. Retry stops at max_retries.

### T-P2-002: Add projection retry tests [Story: US-009] [P]

Test:
- Retry with 0 failed atoms -> no-op, summary all zeros
- Retry with failed atoms (mock transient failure then success) -> atoms recover, ledger updated
- Retry with atoms at max_retries -> no retry attempted, atoms remain failed
- Retry increments `attempt_count` on each attempt
- Retry updates `last_error` with new error message on re-failure

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=5 tests, all pass.

### T-P2-003: Implement local cache startup hydration [Story: US-010]

Add a `hydrate_from_database(session)` method to `HypergraphProjector` that:
1. Queries all documents with `graph_projection_status="complete"`
2. For each document: loads its atoms from the database
3. Calls `project_document()` to populate the local cache (skipping Neo4j writes)
4. Returns count of documents and atoms hydrated

Call this method during the application lifespan startup (`main.py`, after `create_all` and before yield).

**Files**: `src/nexus_babel/services/hypergraph.py`, `src/nexus_babel/main.py`
**Acceptance**: After restart, graph queries return `source="local_cache"` for previously ingested documents. Hydration time for 100 documents with 1K atoms each is <5 seconds.

### T-P2-004: Add local cache hydration tests [Story: US-010]

Test:
- Hydrate with 0 documents -> empty cache, no errors
- Hydrate with 1 document (5 atoms) -> local cache contains doc node + 5 atom nodes + 5 edges
- Hydrate skips documents with `graph_projection_status="failed"`
- After hydration, `query(document_id=...)` returns `source="local_cache"` (not empty)
- Hydration is idempotent: calling twice does not create duplicate nodes

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=5 tests, all pass.

### T-P2-005: Add query result pagination [Story: FR-033]

Add optional `offset` query parameter to `GET /api/v1/hypergraph/query` (default 0). In the local cache path, apply offset before limit to the edge list. In the Neo4j path, add `SKIP $offset` to the Cypher query. Include `total_count` (pre-limit) in the response alongside the existing `count` (post-limit).

**Files**: `src/nexus_babel/services/hypergraph.py`, `src/nexus_babel/api/routes.py`
**Acceptance**: `offset=0&limit=10` returns first 10 edges. `offset=10&limit=10` returns next 10. `total_count` reflects the unfiltered count. Existing tests pass.

### T-P2-006: Add query pagination tests [P]

Test:
- Query with `limit=5` on a document with 20 atoms -> 5 edges, `total_count=20`
- Query with `offset=5&limit=5` -> next 5 edges
- Query with `offset=100` on a document with 10 atoms -> 0 edges (past end)
- Default query (no offset) -> same as `offset=0`

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=4 tests, all pass.

### T-P2-007: Clean up orphan ProjectionLedger rows on re-ingestion

In `_create_atoms()` (`ingestion.py`), add a `DELETE FROM projection_ledger WHERE document_id = :doc_id` before creating new ledger rows. This prevents orphan rows when atoms are deleted and re-created with new UUIDs.

**Files**: `src/nexus_babel/services/ingestion.py`
**Acceptance**: After re-ingestion, `ProjectionLedger` rows match current atom IDs. No orphan rows remain. Existing tests pass.

### T-P2-008: Add orphan ledger cleanup tests

Test:
- Ingest document -> verify N ledger rows
- Re-ingest same document -> verify N ledger rows (not 2N)
- Old atom IDs are not present in the ledger after re-ingestion
- New atom IDs are present with `status="projected"`

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=3 tests, all pass.

---

## Phase 5: P3 Vision

### T-P3-001: Add atom-to-atom PRECEDES edges [Story: US-011]

During `project_document()`, for atoms within the same level and document, create `PRECEDES` edges from `atom:{ordinal-1}` to `atom:{ordinal}`. Store in both local cache and Neo4j. Update `_clear_local_projection()` to also remove PRECEDES edges.

**Files**: `src/nexus_babel/services/hypergraph.py`
**Acceptance**: After ingestion, atoms within a level are linked by PRECEDES edges. `query()` with `relationship_type=PRECEDES` returns sequential edges.

### T-P3-002: Add atom-to-atom PRECEDES tests [P]

Test:
- 3 atoms in a level -> 2 PRECEDES edges: atom1->atom2, atom2->atom3
- Single atom -> 0 PRECEDES edges
- PRECEDES edges do not cross atom levels
- `_clear_local_projection()` removes PRECEDES edges

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=4 tests, all pass.

### T-P3-003: Add multi-hop query support [Story: US-012]

Add `hops` query parameter (default 1, max 5) to `GET /api/v1/hypergraph/query`. In local cache: implement BFS with depth tracking up to `hops` depth. In Neo4j: use variable-length path `MATCH p = (n)-[*1..{hops}]->(m)`.

**Files**: `src/nexus_babel/services/hypergraph.py`, `src/nexus_babel/api/routes.py`
**Acceptance**: `hops=1` returns direct neighbors (existing behavior). `hops=2` returns neighbors' neighbors. `hops=0` returns just the target node.

### T-P3-004: Add multi-hop query tests [P]

Test:
- `hops=1` on a document -> returns atoms (1 hop)
- `hops=2` on a document with PRECEDES edges -> returns atoms + their PRECEDES neighbors (2 hops)
- `hops=0` on a document -> returns just the document node
- `hops=5` with no long chains -> returns all reachable nodes (capped by graph structure, not depth)

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=4 tests, all pass.

### T-P3-005: Add graph export endpoint [Story: US-016]

Add `GET /api/v1/hypergraph/export` with parameters:
- `format` (required): `graphml`, `json_ld`, `rdf_turtle`
- `document_id` (optional): filter to a single document subgraph
- Use `networkx` as intermediary: build DiGraph from local cache, serialize to requested format

**Files**: `src/nexus_babel/services/hypergraph.py`, `src/nexus_babel/api/routes.py`
**Acceptance**: GraphML export validates as XML. JSON-LD contains `@context`. All node and edge data preserved in export.

### T-P3-006: Add graph export tests [P]

Test:
- Export GraphML for a single document -> valid XML with node and edge elements
- Export JSON-LD -> valid JSON with `@graph` array
- Export with non-existent document_id -> empty graph (or 404)
- Export without document_id -> full graph exported

**Files**: `tests/test_hypergraph.py`
**Acceptance**: >=4 tests, all pass.

### T-P3-007: Add Neo4j index creation on startup [Story: Performance]

During application lifespan startup (after `create_all`), if Neo4j is enabled, execute:
- `CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.id)`
- `CREATE INDEX IF NOT EXISTS FOR (a:Atom) ON (a.id)`

**Files**: `src/nexus_babel/services/hypergraph.py`, `src/nexus_babel/main.py`
**Acceptance**: Indexes exist in Neo4j after startup. MERGE operations are faster on indexed properties.

### T-P3-008: Add temporal graph for evolution branches [Story: US-015]

Extend `project_document()` pattern with a new method `project_branch(branch, events)` that creates:
- `Branch` node with `DERIVED_FROM` edge to root `Document` node
- `BranchEvent` nodes with `EVOLVED_BY` edges to `Branch`
- `NEXT_EVENT` edges between sequential events

Call this from `EvolutionService.evolve_branch()` after creating the branch and event.

**Files**: `src/nexus_babel/services/hypergraph.py`, `src/nexus_babel/services/evolution.py`
**Acceptance**: After evolution, branch and event nodes exist in the graph. Timeline queries can traverse `NEXT_EVENT` edges.

---

## Phase 6: Cross-Cutting

### T-CROSS-001: Wire hypergraph domain tests into CI [P]

Update `.github/workflows/ci-minimal.yml` to run `pytest tests/test_hypergraph.py tests/test_mvp.py tests/test_wave2.py -v` as part of the pipeline. Ensure the test environment does not require the `neo4j` pip package (tests should pass with mock or without it).

**Files**: `.github/workflows/ci-minimal.yml`
**Acceptance**: CI runs the hypergraph test suite and fails on regression.

### T-CROSS-002: Add performance benchmark for graph projection

Create `scripts/benchmark_graph_projection.py` that:
1. Creates documents with 100, 1K, 10K, and 100K atoms
2. Times `project_document()` for each size
3. Times `query()` for each projected document
4. Times `_clear_local_projection()` for each size
5. Prints summary table: `atoms | project_ms | query_ms | clear_ms`

**Files**: `scripts/benchmark_graph_projection.py`
**Acceptance**: Script runs end-to-end. Baseline captured. 10K atoms projects in <5s. 100K atoms projects in <60s.

### T-CROSS-003: Add concurrent projection safety test

Test that two simultaneous calls to `project_document()` for different documents do not interfere. Test that two calls for the SAME document produce a consistent final state (one wins, no partial interleaving).

**Files**: `tests/test_hypergraph.py`
**Acceptance**: Concurrent projection of different documents -> both fully projected. Same document -> final state is consistent (either first or second projection wins completely).

### T-CROSS-004: Add Neo4j integration test (docker-only)

Create `tests/test_hypergraph_neo4j.py` marked with `@pytest.mark.neo4j` (skipped unless `NEXUS_NEO4J_URI` env var is set). Test:
- `project_document()` writes to Neo4j
- `integrity_for_document()` returns `neo4j_verified=True` with correct counts
- `query()` can fall through to Neo4j when local cache is empty
- `close()` disconnects cleanly

**Files**: `tests/test_hypergraph_neo4j.py`
**Acceptance**: Tests pass when run with `docker compose up -d` and `NEXUS_NEO4J_URI` set. Tests skip gracefully in CI without Neo4j.

### T-CROSS-005: Update CLAUDE.md with domain spec references

Add a section to the project CLAUDE.md pointing to the `specs/07-hypergraph/` directory and summarizing the domain's P1/P2/P3 scope.

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
  T-FOUND-001 ── (independent)
  T-FOUND-002 ── (independent, can parallel with T-FOUND-001)
  T-FOUND-003 ── (independent, can parallel with T-FOUND-001, T-FOUND-002)

Phase 3 (P1 Verification)
  T-SETUP-001 -> T-P1-001 through T-P1-010
  T-SETUP-003 -> T-P1-003 (Neo4j mock needed)
  T-SETUP-003 -> T-P1-004 (Neo4j mock for Neo4j-verified case)
  T-P1-001 through T-P1-010 can mostly run in parallel [P]
  Exception: T-P1-009 depends on understanding ingestion flow (no hard dependency)

Phase 4 (P2 Completion)
  T-P1-009 -> T-P2-001 (retry builds on failure path)
  T-P2-001 -> T-P2-002
  T-P1-002 -> T-P2-003 (hydration uses project_document)
  T-P2-003 -> T-P2-004
  T-P1-006 -> T-P2-005 (pagination extends query)
  T-P2-005 -> T-P2-006
  T-P1-007 -> T-P2-007 (orphan cleanup relates to ledger)
  T-P2-007 -> T-P2-008

Phase 5 (P3 Vision)
  T-P1-002 -> T-P3-001 (extends project_document)
  T-P3-001 -> T-P3-002
  T-P1-006 -> T-P3-003 (extends query)
  T-P3-003 -> T-P3-004
  T-P1-006 -> T-P3-005 (new route alongside query)
  T-P3-005 -> T-P3-006
  T-P3-007 (independent, Neo4j only)
  T-P3-001 -> T-P3-008 (extends graph model)

Phase 6 (Cross-Cutting)
  T-CROSS-001 (depends on Phase 3 completion)
  T-CROSS-002 (depends on T-P1-002)
  T-CROSS-003 (depends on T-P1-002)
  T-CROSS-004 (depends on T-SETUP-003, T-P1-003)
  T-CROSS-005 (no deps)
```

---

## Summary

| Phase | Tasks | Parallel | Scope |
|-------|-------|----------|-------|
| Phase 1: Setup | 3 | All [P] | Test infrastructure, baseline, mock creation |
| Phase 2: Foundational | 3 | All [P] | Cache optimization, lazy import |
| Phase 3: P1 Verification | 10 | Most [P] | Harden all as-built behavior, cover untested paths |
| Phase 4: P2 Completion | 8 | Partial | Retry queue, cache hydration, pagination, orphan cleanup |
| Phase 5: P3 Vision | 8 | Partial | Atom-to-atom edges, multi-hop, export, temporal graph |
| Phase 6: Cross-Cutting | 5 | Partial | CI, benchmarks, concurrency, Neo4j integration |
| **Total** | **37** | | |
