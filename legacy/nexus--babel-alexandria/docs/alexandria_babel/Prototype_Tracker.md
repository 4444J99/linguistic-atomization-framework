# ARC4N Prototype Tracker

Source scope:
- `~/Workspace/organvm-i-theoria/nexus--babel-alexandria-/0469-arc4n-seed-texts-and-atomization-2.md`
- `~/Workspace/organvm-i-theoria/nexus--babel-alexandria-/Nexus_Bable-Alexandria.md`

Legend:
- `Implemented`: Present in code/docs artifacts now.
- `Planned`: Captured in explicit plan bucket and backlog.

| Prototype / System | Status | Evidence / Plan Anchor |
|---|---|---|
| Natural Drift Algorithm (NDA) | Implemented | `src/nexus_babel/services/evolution.py` (`natural_drift`) |
| Synthetic Mutation Engine (SDA) | Implemented | `src/nexus_babel/services/evolution.py` (`synthetic_mutation`) |
| Phase Cycle Engine (Expansion/Peak/Compression/Rebirth) | Implemented | `src/nexus_babel/services/evolution.py` (`phase_shift`) |
| Glyph Fusion Engine | Implemented | `src/nexus_babel/services/evolution.py` (`glyph_fusion`) |
| Branch Replay + Compare | Implemented | `src/nexus_babel/api/routes.py` (`/branches/{id}/replay`, `/compare`) |
| Reverse Drift Event Type | Implemented | `src/nexus_babel/services/evolution.py` (`reverse_drift`), `tests/test_evolution.py` |
| Multi-Evolve Batch Endpoint | Implemented | `src/nexus_babel/api/routes/branches.py` (`POST /api/v1/evolve/multi`), `tests/test_evolution_api.py` |
| Checkpoint-Accelerated Replay | Implemented (benchmark non-gating) | `src/nexus_babel/services/evolution.py` (`get_timeline` checkpoint path), `tests/test_evolution_api.py` |
| Evolution Visualization Graph Endpoint | Implemented | `src/nexus_babel/api/routes/branches.py` (`GET /api/v1/branches/{id}/visualization`), `tests/test_evolution_api.py` |
| Branch Merge Primitives + API | Implemented | `src/nexus_babel/services/evolution.py` (`_find_lca`, `merge_branches`), `src/nexus_babel/api/routes/branches.py` (`POST /api/v1/branches/merge`) |
| Cartridge Master Index | Planned | `AB-PLAN-04 Governance + Artifact Ops` |
| UX Explorer Thread Scaffolds | Planned | `AB-PLAN-03 Explorer UX + Interaction` |
| Academic Outreach Thread Scaffolds | Planned | `AB-PLAN-05 Academic + Funding` |
| Funding Thread Scaffolds | Planned | `AB-PLAN-05 Academic + Funding` |
| Temporal Spiral Map Prototype | Planned | `AB-PLAN-02 Evolution + Glyphic Engines` |
| Songbirth / Sung-language Prototype | Planned | `AB-PLAN-06 Mythic + Cultural Layer` |
| Prototype Tracker Artifact | Implemented | `docs/alexandria_babel/Prototype_Tracker.md` |
| Protocol Tracker Artifact | Implemented | `docs/alexandria_babel/Protocol_Tracker.md` |
| Save Receipt Workflow | Implemented | `docs/alexandria_babel/Save_Receipt_2026-02-18.md` |

## Active Plan Buckets

- `AB-PLAN-01 Corpus Atomization + Remix Library`
- `AB-PLAN-02 Evolution + Glyphic Engines`
- `AB-PLAN-03 Explorer UX + Interaction`
- `AB-PLAN-04 Governance + Artifact Ops`
- `AB-PLAN-05 Academic + Funding`
- `AB-PLAN-06 Mythic + Cultural Layer`
