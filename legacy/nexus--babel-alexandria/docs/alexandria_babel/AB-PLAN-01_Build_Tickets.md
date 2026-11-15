# AB-PLAN-01 Build Tickets

Scope:
- Plan bucket: `AB-PLAN-01` (Corpus Atomization + Remix Library)
- Source authorities:
  - `~/Workspace/organvm-i-theoria/nexus--babel-alexandria-/0469-arc4n-seed-texts-and-atomization-2.md`
  - `~/Workspace/organvm-i-theoria/nexus--babel-alexandria-/Nexus_Bable-Alexandria.md`

## Priority Queue

| Ticket ID | Title | Priority | Dependencies |
|---|---|---|---|
| `AB01-T001` | Seed Corpus Registry + Profiles | P0 | None |
| `AB01-T002` | Dual Atomization Tracks | P0 | AB01-T001 |
| `AB01-T003` | Deterministic Atom Filename Schema | P0 | AB01-T002 |
| `AB01-T004` | Atom Library Export Pipeline | P1 | AB01-T003 |
| `AB01-T005` | Remix Composer API + Service | P1 | AB01-T002 |
| `AB01-T006` | Remix Persistence + Retrieval | P1 | AB01-T005 |
| `AB01-T007` | User Break-Off Timeline Hook | P1 | AB01-T005 |
| `AB01-T008` | Cartridge + Thread Plan Scaffold Sync | P2 | AB01-T004 |
| `AB01-T009` | AB-PLAN-01 Test + Contract Suite | P0 | AB01-T001..AB01-T008 |

---

## `AB01-T001` Seed Corpus Registry + Profiles

Objective:
- Materialize the pilot seed-text corpus contract and ingestion profiles for repeatable runs.

Source references:
- `0469-arc4n-seed-texts-and-atomization-2.md:46`
- `0469-arc4n-seed-texts-and-atomization-2.md:1109`

File-level owners:
- `src/nexus_babel/config.py` owner: `platform-config`
- `scripts/ingest_corpus.py` owner: `ops-tooling`
- `docs/alexandria_babel/seed_corpus_registry.yaml` owner: `corpus-curation`
- `tests/test_mvp.py` owner: `qa`

Implementation tasks:
1. Add seed registry file for canonical corpus list and profile metadata.
2. Add `ingest_profile` support to ingestion script.
3. Validate profile existence and source path normalization.

Acceptance criteria:
1. `python scripts/ingest_corpus.py --profile arc4n-seed` runs without manual path arguments.
2. Invalid profile returns non-zero exit with clear error.
3. Registry profile used is included in ingest job metadata.

---

## `AB01-T002` Dual Atomization Tracks

Objective:
- Implement explicit atomization tracks: literary track and glyphic seed track.

Source references:
- `0469-arc4n-seed-texts-and-atomization-2.md:338`
- `0469-arc4n-seed-texts-and-atomization-2.md:340`

File-level owners:
- `src/nexus_babel/services/ingestion.py` owner: `ingestion-core`
- `src/nexus_babel/services/text_utils.py` owner: `atomization-core`
- `src/nexus_babel/schemas.py` owner: `api-core`
- `tests/test_mvp.py` owner: `qa`

Implementation tasks:
1. Add `atom_tracks` parse option with named presets.
2. Track-level validation and defaults.
3. Persist track selection in document provenance.

Acceptance criteria:
1. API accepts `atom_tracks=["literary","glyphic_seed"]`.
2. Response provenance records track names and active atom levels.
3. Atom counts differ predictably by track selection.

---

## `AB01-T003` Deterministic Atom Filename Schema

Objective:
- Provide canonical atom file naming for durable parsing and remix reproducibility.

Source references:
- `0469-arc4n-seed-texts-and-atomization-2.md:211`
- `0469-arc4n-seed-texts-and-atomization-2.md:104`

File-level owners:
- `src/nexus_babel/services/text_utils.py` owner: `atomization-core`
- `src/nexus_babel/services/ingestion.py` owner: `ingestion-core`
- `tests/test_mvp.py` owner: `qa`

Implementation tasks:
1. Add deterministic naming helper (`TEXT_WORD_000001_token.txt` style).
2. Apply naming in export and artifact generation paths.
3. Include token normalization rules and collision handling.

Acceptance criteria:
1. Same input corpus yields identical filenames across runs.
2. Naming helper is unit-tested for punctuation, Unicode, and duplicates.
3. Export metadata includes generated filename schema version.

---

## `AB01-T004` Atom Library Export Pipeline

Objective:
- Export ingested atoms into a navigable archive tree suitable for manual and scripted remix.

Source references:
- `0469-arc4n-seed-texts-and-atomization-2.md:176`
- `0469-arc4n-seed-texts-and-atomization-2.md:1277`

File-level owners:
- `scripts/export_atom_library.py` owner: `ops-tooling`
- `src/nexus_babel/services/ingestion.py` owner: `ingestion-core`
- `src/nexus_babel/models.py` owner: `data-model`
- `tests/test_ab_plan_01.py` owner: `qa`

Implementation tasks:
1. Add export script generating `/ARC4N/SEED_TEXTS/<TEXT>/<LEVEL>/` trees.
2. Write manifest per document with atom IDs and source lineage.
3. Support idempotent overwrite mode.

Acceptance criteria:
1. Export tree exists and matches atom counts in SQL.
2. Re-running export with same checksum is idempotent.
3. Manifest includes document id, checksum, and atom-level counts.

---

## `AB01-T005` Remix Composer API + Service

Objective:
- Implement first-class remix generation from atom pools (word/sentence blend).

Source references:
- `0469-arc4n-seed-texts-and-atomization-2.md:46`
- `0469-arc4n-seed-texts-and-atomization-2.md:177`

File-level owners:
- `src/nexus_babel/services/remix.py` owner: `remix-core`
- `src/nexus_babel/api/routes.py` owner: `api-core`
- `src/nexus_babel/schemas.py` owner: `api-core`
- `tests/test_ab_plan_01.py` owner: `qa`

Implementation tasks:
1. Add remix service with deterministic seed control.
2. Add `POST /api/v1/remix/compose` endpoint.
3. Support selection by source documents and atom levels.

Acceptance criteria:
1. Endpoint returns remix text + source atom references.
2. Same request + seed returns identical output.
3. Invalid source IDs fail with 404 and actionable error.

---

## `AB01-T006` Remix Persistence + Retrieval

Objective:
- Persist remix outputs as first-class artifacts with lineage and governance-ready metadata.

Source references:
- `0469-arc4n-seed-texts-and-atomization-2.md:190`
- `0469-arc4n-seed-texts-and-atomization-2.md:1254`

File-level owners:
- `src/nexus_babel/models.py` owner: `data-model`
- `alembic/versions/*` owner: `data-model`
- `src/nexus_babel/api/routes.py` owner: `api-core`
- `tests/test_wave2.py` owner: `qa`

Implementation tasks:
1. Add remix artifact tables and source-link join table.
2. Add retrieval endpoints (`GET /api/v1/remix/{id}`, `GET /api/v1/remix`).
3. Include governance decision trace snapshot for each remix.

Acceptance criteria:
1. Remix artifact and source links are persisted transactionally.
2. Retrieval endpoint returns full lineage graph references.
3. Migration applies cleanly and downgrade path exists.

---

## `AB01-T007` User Break-Off Timeline Hook

Objective:
- Turn remix or exploration actions into optional branch-off points for personalized evolution tracks.

Source references:
- `0469-arc4n-seed-texts-and-atomization-2.md:975`
- `0469-arc4n-seed-texts-and-atomization-2.md:1543`

File-level owners:
- `src/nexus_babel/services/evolution.py` owner: `evolution-core`
- `src/nexus_babel/services/remix.py` owner: `remix-core`
- `src/nexus_babel/api/routes.py` owner: `api-core`
- `tests/test_wave2.py` owner: `qa`

Implementation tasks:
1. Add `create_branch=true` option in remix compose request.
2. Emit branch event containing remix payload hash.
3. Link remix artifact id in branch event payload.

Acceptance criteria:
1. Branch is created when option is enabled and omitted otherwise.
2. Timeline replay shows remix event with stable hash.
3. Compare endpoint detects divergence across different remix seeds.

---

## `AB01-T008` Cartridge + Thread Plan Scaffold Sync

Objective:
- Materialize thread-cartridge scaffolding into repository-backed artifacts and keep index synchronized.

Source references:
- `0469-arc4n-seed-texts-and-atomization-2.md:1277`
- `0469-arc4n-seed-texts-and-atomization-2.md:1278`

File-level owners:
- `docs/alexandria_babel/` owner: `knowledge-ops`
- `scripts/alexandria_babel_alignment.py` owner: `knowledge-ops`
- `tests/test_ab_plan_01.py` owner: `qa`

Implementation tasks:
1. Add cartridge index generator command.
2. Add thread-plan templates for UX, academic, funding.
3. Add consistency check in alignment script for required scaffold files.

Acceptance criteria:
1. Running scaffold command regenerates missing templates.
2. Index includes all cartridge files with updated timestamps.
3. CI check fails if required scaffold artifact is missing.

---

## `AB01-T009` AB-PLAN-01 Test + Contract Suite

Objective:
- Add dedicated tests to gate AB-PLAN-01 behavior and keep tickets implementation-safe.

Source references:
- `Nexus_Bable-Alexandria.md:504`
- `Nexus_Bable-Alexandria.md:814`

File-level owners:
- `tests/test_ab_plan_01.py` owner: `qa`
- `tests/conftest.py` owner: `qa`
- `.github/workflows/ci-minimal.yml` owner: `devex`

Implementation tasks:
1. Create `tests/test_ab_plan_01.py` for tickets T001-T008 contracts.
2. Add fixture helpers for seed registry and remix artifacts.
3. Wire tests into CI workflow.

Acceptance criteria:
1. New test suite runs in CI and local `pytest -q`.
2. Each ticket has at least one explicit contract test.
3. CI fails on contract regression for AB-PLAN-01 endpoints and exports.

---

## Ready-to-Execute Order

1. Implement `AB01-T001`, `AB01-T002`, `AB01-T003`.
2. Implement `AB01-T004`, `AB01-T005`, `AB01-T006`.
3. Implement `AB01-T007`, `AB01-T008`.
4. Finalize `AB01-T009` and enforce in CI.
