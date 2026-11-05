# AB-PLAN-02 Build Tickets

Scope:
- Plan bucket: `AB-PLAN-02` (Evolution + Glyphic Engines)
- Execution source of truth: `specs/03-evolution-branching/tasks.md`
- Tracker posture: hybrid (spec task completion + Alexandria artifact reflection)

## Milestone Status (2026-02-25)

- `S03-13 Reverse Drift Event Type`: `Implemented`
- `S03-14 Multi-Evolve Batch Endpoint`: `Implemented`
- `S03-15 Checkpoint-Accelerated Replay`: `Implemented (benchmark marked slow / non-gating)`
- `S03-19 T19-01 Visualization Endpoint`: `Implemented (backend graph endpoint)`
- `S03-17 Branch Merging`: `Implemented (v1 merge primitives + API)`

## Completed This Wave

| Ticket ID | Title | Status | Evidence |
|---|---|---|---|
| `AB02-T013` | Reverse Drift Event Support | Implemented | `src/nexus_babel/services/evolution.py`, `tests/test_evolution.py`, `tests/test_evolution_api.py` |
| `AB02-T014` | Multi-Evolve Batch Orchestration API | Implemented | `src/nexus_babel/schemas.py`, `src/nexus_babel/api/routes/branches.py`, `tests/test_evolution_api.py` |
| `AB02-T015A` | Checkpoint-Accelerated Replay (Service + Correctness Test) | Implemented | `src/nexus_babel/services/evolution.py`, `tests/test_evolution_api.py` |
| `AB02-T015B` | Checkpoint Replay Benchmark (Slow, Non-Gating) | Implemented | `tests/test_evolution_api.py` (`@pytest.mark.slow`) |
| `AB02-T019A` | Branch Visualization Graph Endpoint (Backend) | Implemented | `src/nexus_babel/api/routes/branches.py`, `tests/test_evolution_api.py` |
| `AB02-T017` | Branch Merge Primitives + API | Implemented | `src/nexus_babel/services/evolution.py`, `src/nexus_babel/api/routes/branches.py`, `tests/test_evolution_api.py` |
| `AB02-T014C` | OpenAPI Contract Snapshot Update | Implemented | `tests/snapshots/openapi_contract_normalized.json`, `tests/test_openapi_contract_snapshot.py` |

## Next Queue

| Ticket ID | Title | Priority | Spec Anchor |
|---|---|---|---|
| `AB02-T017B` | Merge Provenance/Conflict Semantics (optional hardening) | P2 | `S03-17 follow-up` |
| `AB02-T019B` | Visualization merge-edge enrichment for secondary parent links | P2 | `S03-19 follow-up` |

## Acceptance Evidence (Milestone 1)

1. `reverse_drift` is accepted by `POST /api/v1/evolve/branch` and returns `diff_summary.event = "reverse_drift"`.
2. `POST /api/v1/evolve/multi` creates chained branches in one transaction and returns `branch_ids`, `event_ids`, `final_branch_id`, `event_count`, `final_text_hash`, and `final_preview`.
3. Empty event lists fail with `400` and preserve `detail`.
4. Batch rollback on failure leaves no partial branch/event rows from the failed batch.
5. Normalized OpenAPI contract snapshot includes the additive `/api/v1/evolve/multi` operation.
